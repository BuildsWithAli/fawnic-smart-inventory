"""
Agent orchestration for the Kanban stock-check trigger.

Safety design (see CLAUDE.md sections 19-20):
  - TOOL_FUNCTIONS is a closed, hardcoded dict of exactly four callables. The model
    never receives a code path to anything else; `_execute_tool` looks the
    requested name up in this dict and raises LookupError for anything not in it,
    which the provider layer turns into a tool_result error sent back to the
    model — the call is never executed.
  - The model only ever sees JSON tool-call requests/results. It has no ORM
    handle, no SQL access, and no code execution capability of any kind.
  - All writes to StockAlert happen inside tools.py's flag_low_stock /
    suggest_reorder, which validate their own arguments (severity enum,
    positive integer quantity) independent of whatever the model claims.
  - Product.quantity is never written by anything in this module.
"""

import logging

from django.conf import settings

from . import tools
from .providers import ClaudeProvider, GeminiProvider, OllamaProvider, OpenAIProvider

logger = logging.getLogger(__name__)

TOOL_SPECS = [
    {
        "name": "get_stock_level",
        "description": "Get the current real on-hand quantity for a product by its ID.",
        "input_schema": {
            "type": "object",
            "properties": {"product_id": {"type": "integer"}},
            "required": ["product_id"],
        },
    },
    {
        "name": "get_reorder_threshold",
        "description": "Get the reorder threshold configured for a product by its ID.",
        "input_schema": {
            "type": "object",
            "properties": {"product_id": {"type": "integer"}},
            "required": ["product_id"],
        },
    },
    {
        "name": "flag_low_stock",
        "description": (
            "Create a StockAlert for a product tied to an order, at a given severity. "
            "Only call this after checking get_stock_level and get_reorder_threshold."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "integer"},
                "order_id": {"type": "integer"},
                "severity": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
            },
            "required": ["product_id", "order_id", "severity"],
        },
    },
    {
        "name": "suggest_reorder",
        "description": "Attach a suggested reorder quantity to the current alert for a product.",
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "integer"},
                "suggested_qty": {"type": "integer", "minimum": 1},
            },
            "required": ["product_id", "suggested_qty"],
        },
    },
]

# Closed whitelist. This is the ONLY place tool names are mapped to code.
TOOL_FUNCTIONS = {
    "get_stock_level": tools.get_stock_level,
    "get_reorder_threshold": tools.get_reorder_threshold,
    "flag_low_stock": tools.flag_low_stock,
    "suggest_reorder": tools.suggest_reorder,
}


def _execute_tool(name, arguments):
    if name not in TOOL_FUNCTIONS:
        raise LookupError(f"Tool '{name}' is not permitted. Allowed tools: {sorted(TOOL_FUNCTIONS)}")
    return TOOL_FUNCTIONS[name](**arguments)


def get_provider():
    provider = settings.AI_PROVIDER

    if provider == "claude" and settings.ANTHROPIC_API_KEY:
        return ClaudeProvider()
    if provider == "openai" and settings.OPENAI_API_KEY:
        return OpenAIProvider()
    if provider == "gemini" and settings.GEMINI_API_KEY:
        return GeminiProvider()
    if provider == "ollama":
        return OllamaProvider()

    if settings.ANTHROPIC_API_KEY:
        return ClaudeProvider()
    if settings.OPENAI_API_KEY:
        return OpenAIProvider()
    if settings.GEMINI_API_KEY:
        return GeminiProvider()
    return OllamaProvider()


def evaluate_order_stock(order):
    """Entry point called whenever a Kanban order's status changes.

    Builds a prompt describing the order's products and lets the agent decide
    whether to raise StockAlert(s) via its four whitelisted tools. Returns the
    model's final text summary (for logging), or None if the order has no items.
    """
    items = list(order.items.select_related("product").all())
    if not items:
        return None

    provider = get_provider()

    product_lines = "\n".join(
        f"- product_id={item.product.id}, name={item.product.name}, sku={item.product.sku}"
        for item in items
    )

    system_prompt = (
        "You are FAWNIC's inventory stock-check agent. You evaluate whether the "
        "products on a production order have enough stock to proceed through its "
        "current stage. You must call get_stock_level and get_reorder_threshold to "
        "check real numbers for every product — never assume, estimate, or invent a "
        "quantity from memory. If a product's stock is at or below its reorder "
        "threshold, call flag_low_stock with an appropriate severity ('low', "
        "'medium', 'high', or 'critical' based on how far below threshold it is or "
        "whether it is at zero), then call suggest_reorder with a sensible reorder "
        "quantity. If a product's stock is healthy, do not create an alert for it. "
        "You have no capabilities beyond the four tools provided."
    )
    user_prompt = (
        f"Order #{order.id} for {order.customer.name} just moved to status "
        f"'{order.status}'. Its line items are:\n{product_lines}\n\n"
        f"The order_id to use for flag_low_stock is {order.id}. "
        "Check each product's stock level against its reorder threshold and act accordingly."
    )

    try:
        return provider.run_tool_agent(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            tools=TOOL_SPECS,
            tool_executor=_execute_tool,
            max_turns=6,
        )
    except Exception:
        logger.exception("AI provider call failed while evaluating order %s", order.id)
        return None
