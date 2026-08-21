"""
AIProvider abstraction. The rest of the application (agent.py, and everything
above it) only ever talks to this interface — never directly to the Anthropic,
OpenAI, Gemini, or Ollama SDKs. That keeps provider swaps and fallback logic
isolated to this one file.
"""

import json
import logging
from abc import ABC, abstractmethod

from django.conf import settings

logger = logging.getLogger(__name__)


class AIProvider(ABC):
    @abstractmethod
    def run_tool_agent(self, *, system_prompt, user_prompt, tools, tool_executor, max_turns=6):
        """Run an agentic tool-calling loop and return the model's final text reply.

        tools: list of {"name", "description", "input_schema"} JSON-schema tool specs.
        tool_executor: callable(name: str, arguments: dict) -> dict. Must raise on
            an unknown tool name or invalid arguments — the provider implementation
            reports that error back to the model as a tool_result error rather than
            crashing, so the model can see the rejection was for input validity, not
            a bug. It is this callable, defined in agent.py, that structurally limits
            the model to the four whitelisted tools; the provider never calls
            anything except this callable.
        """
        raise NotImplementedError


class ClaudeProvider(AIProvider):
    def __init__(self, model="claude-sonnet-4-5-20250929", api_key=None):
        from anthropic import Anthropic

        self.client = Anthropic(api_key=api_key or settings.ANTHROPIC_API_KEY)
        self.model = model

    def run_tool_agent(self, *, system_prompt, user_prompt, tools, tool_executor, max_turns=6):
        anthropic_tools = [
            {"name": t["name"], "description": t["description"], "input_schema": t["input_schema"]}
            for t in tools
        ]
        messages = [{"role": "user", "content": user_prompt}]

        for _ in range(max_turns):
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=system_prompt,
                messages=messages,
                tools=anthropic_tools,
            )
            messages.append({"role": "assistant", "content": response.content})

            tool_uses = [block for block in response.content if block.type == "tool_use"]
            if not tool_uses:
                text_blocks = [block.text for block in response.content if block.type == "text"]
                return "\n".join(text_blocks)

            tool_results = []
            for tool_use in tool_uses:
                try:
                    result = tool_executor(tool_use.name, tool_use.input)
                    tool_results.append(
                        {"type": "tool_result", "tool_use_id": tool_use.id, "content": json.dumps(result)}
                    )
                except Exception as exc:
                    logger.warning("Tool call rejected: %s(%s) -> %s", tool_use.name, tool_use.input, exc)
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_use.id,
                            "content": json.dumps({"error": str(exc)}),
                            "is_error": True,
                        }
                    )
            messages.append({"role": "user", "content": tool_results})

        return "Reached maximum tool-call turns without a final answer."


class OpenAIProvider(AIProvider):
    """Fallback provider. Same tool-calling contract via OpenAI's chat completions API."""

    def __init__(self, model="gpt-4o-mini", api_key=None):
        from openai import OpenAI

        self.client = OpenAI(api_key=api_key or settings.OPENAI_API_KEY)
        self.model = model

    def run_tool_agent(self, *, system_prompt, user_prompt, tools, tool_executor, max_turns=6):
        openai_tools = [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t["input_schema"],
                },
            }
            for t in tools
        ]
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        for _ in range(max_turns):
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=openai_tools,
                tool_choice="auto",
            )
            message = response.choices[0].message
            tool_calls = message.tool_calls or []

            if not tool_calls:
                return message.content or ""

            messages.append(
                {
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                        }
                        for tc in tool_calls
                    ],
                }
            )

            for tool_call in tool_calls:
                try:
                    arguments = json.loads(tool_call.function.arguments or "{}")
                    result = tool_executor(tool_call.function.name, arguments)
                    content = json.dumps(result)
                except Exception as exc:
                    logger.warning(
                        "Tool call rejected: %s(%s) -> %s",
                        tool_call.function.name,
                        tool_call.function.arguments,
                        exc,
                    )
                    content = json.dumps({"error": str(exc)})

                messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": content})

        return "Reached maximum tool-call turns without a final answer."


class OllamaProvider(AIProvider):
    """Optional local/offline dev-time provider (Ollama + Llama 3). Not required
    for the application to function — if Ollama is unreachable this raises and
    the caller (agent.get_provider) should have already fallen back before
    reaching here in a normal configuration."""

    def __init__(self, model=None, base_url=None):
        self.model = model or settings.OLLAMA_MODEL
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")

    def run_tool_agent(self, *, system_prompt, user_prompt, tools, tool_executor, max_turns=6):
        import requests

        ollama_tools = [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t["input_schema"],
                },
            }
            for t in tools
        ]
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        for _ in range(max_turns):
            resp = requests.post(
                f"{self.base_url}/api/chat",
                json={"model": self.model, "messages": messages, "tools": ollama_tools, "stream": False},
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()
            message = data.get("message", {})
            tool_calls = message.get("tool_calls") or []

            if not tool_calls:
                return message.get("content", "")

            messages.append(message)
            for tool_call in tool_calls:
                fn = tool_call.get("function", {})
                name = fn.get("name")
                arguments = fn.get("arguments") or {}
                if isinstance(arguments, str):
                    arguments = json.loads(arguments)
                try:
                    result = tool_executor(name, arguments)
                    content = json.dumps(result)
                except Exception as exc:
                    logger.warning("Tool call rejected: %s(%s) -> %s", name, arguments, exc)
                    content = json.dumps({"error": str(exc)})
                messages.append({"role": "tool", "content": content})

        return "Reached maximum tool-call turns without a final answer."


class GeminiProvider(AIProvider):
    """Fallback/alternate provider using Google's Gemini API (google-genai SDK).
    Same tool-calling contract as the other providers — the model only ever
    sees JSON tool-call requests/results via `tool_executor`."""

    def __init__(self, model="gemini-3.6-flash", api_key=None):
        from google import genai

        self.client = genai.Client(api_key=api_key or settings.GEMINI_API_KEY)
        self.model = model

    def run_tool_agent(self, *, system_prompt, user_prompt, tools, tool_executor, max_turns=6):
        from google.genai import types

        gemini_tool = types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name=t["name"],
                    description=t["description"],
                    parameters_json_schema=t["input_schema"],
                )
                for t in tools
            ]
        )
        config = types.GenerateContentConfig(system_instruction=system_prompt, tools=[gemini_tool])
        contents = [types.Content(role="user", parts=[types.Part(text=user_prompt)])]

        for _ in range(max_turns):
            response = self.client.models.generate_content(model=self.model, contents=contents, config=config)

            calls = response.function_calls or []
            if not calls:
                return response.text or ""

            contents.append(response.candidates[0].content)

            response_parts = []
            for call in calls:
                try:
                    result = tool_executor(call.name, dict(call.args or {}))
                    if not isinstance(result, dict):
                        result = {"result": result}
                    response_parts.append(types.Part.from_function_response(name=call.name, response=result))
                except Exception as exc:
                    logger.warning("Tool call rejected: %s(%s) -> %s", call.name, call.args, exc)
                    response_parts.append(
                        types.Part.from_function_response(name=call.name, response={"error": str(exc)})
                    )
            contents.append(types.Content(role="user", parts=response_parts))

        return "Reached maximum tool-call turns without a final answer."
