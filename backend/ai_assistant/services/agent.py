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
import time
from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

from django.conf import settings

from . import tools
from .providers import ClaudeProvider, GeminiProvider, OllamaProvider, OpenAIProvider

logger = logging.getLogger(__name__)

# Hard upper bound on how long the Kanban status-change request will wait for the
# whole AI stock-check (all fallback rungs combined) before giving up. SDKs' own
# retry/backoff logic can exceed any per-request timeout they're configured with,
# so this is enforced independently in a worker thread — a slow or hanging
# provider must never block the request that persisted the order's new status.
AI_CALL_TIMEOUT_SECONDS = 45

# Per-rung ceiling. Without it, one rung burning the entire budget (an SDK
# retrying a 429 for 45s) would starve every rung behind it. Each rung gets the
# smaller of this and whatever remains of AI_CALL_TIMEOUT_SECONDS.
AI_RUNG_TIMEOUT_SECONDS = 25

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


# Outcome of evaluate_order_stock, so the caller (orders.views) can tell a
# genuine "checked, stock is fine" apart from "nothing checked at all":
#   status="skipped"     -> the order has no line items; nothing to evaluate.
#   status="ok"          -> a provider completed the check. It may or may not
#                           have raised alerts — that is the agent's decision.
#   status="unavailable" -> every provider rung errored or timed out. The order's
#                           status change was still saved, but no stock check ran;
#                           the API surfaces this so the UI isn't silently wrong.
# summary  = the model's final text (logging only) when status="ok", else None.
# provider = "ClassName:model" of the rung that answered, else None.
StockCheckResult = namedtuple("StockCheckResult", ["status", "summary", "provider"])

VALID_STOCK_CHECK_STATUSES = ("ok", "skipped", "unavailable")

# Ordered provider rungs. Each value builds a provider instance, or returns None
# when the rung isn't usable (no credentials). evaluate_order_stock advances to
# the next rung whenever one errors or times out, so a single provider/model's
# rate-limit or outage no longer silently drops the stock check. The two Gemini
# models are separate rungs: if the primary model is rate-limited, the higher-RPD
# fallback model gets a turn before we leave Gemini entirely.
def _gemini_fallback_provider():
    fallback = settings.GEMINI_FALLBACK_MODEL
    if settings.GEMINI_API_KEY and fallback and fallback != settings.GEMINI_MODEL:
        return GeminiProvider(model=fallback)
    return None


def _provider_builders():
    return {
        "claude": lambda: ClaudeProvider() if settings.ANTHROPIC_API_KEY else None,
        "openai": lambda: OpenAIProvider() if settings.OPENAI_API_KEY else None,
        "gemini": lambda: GeminiProvider() if settings.GEMINI_API_KEY else None,
        "gemini-fallback": _gemini_fallback_provider,
        "ollama": lambda: OllamaProvider(),
    }


# Rung order for a given AI_PROVIDER: the configured provider first, its Gemini
# fallback model right after it when Gemini is configured, then the rest.
def _rung_order():
    configured = settings.AI_PROVIDER
    order = [configured]
    if configured == "gemini":
        order.append("gemini-fallback")
    for key in ("claude", "openai", "gemini", "gemini-fallback", "ollama"):
        if key not in order:
            order.append(key)
    return order


def get_provider_chain():
    """Ordered list of provider instances evaluate_order_stock tries in turn."""
    builders = _provider_builders()
    chain = []
    for key in _rung_order():
        build = builders.get(key)
        if build is None:
            continue
        try:
            provider = build()
        except Exception:
            logger.exception("Could not initialise AI provider rung %r; skipping it in the fallback chain.", key)
            continue
        if provider is not None:
            chain.append(provider)
    return chain


def get_provider():
    """The single primary provider — first rung of the fallback chain.

    Retained for callers/tests that only need the configured provider; the
    Kanban stock-check path uses get_provider_chain() for model/provider failover.
    """
    chain = get_provider_chain()
    return chain[0] if chain else OllamaProvider()


def _provider_label(provider):
    model = getattr(provider, "model", None)
    return f"{type(provider).__name__}:{model}" if model else type(provider).__name__


def _run_agent_once(provider, *, system_prompt, user_prompt, timeout):
    """Run one provider's tool-agent loop in a worker thread, bounded by `timeout`.

    Raises FutureTimeoutError if the provider doesn't return in time. The worker
    thread is abandoned rather than killed — an SDK's own retry/backoff can
    outlast any per-request timeout it was handed, so the ceiling is enforced
    here instead of trusting the SDK.
    """
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(
        provider.run_tool_agent,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        tools=TOOL_SPECS,
        tool_executor=_execute_tool,
        max_turns=6,
    )
    try:
        return future.result(timeout=timeout)
    finally:
        executor.shutdown(wait=False)


def evaluate_order_stock(order):
    """Entry point called whenever a Kanban order's status changes.

    Tries each rung of get_provider_chain() until one completes, giving the agent
    a chance to raise StockAlert(s) via its four whitelisted tools. All rungs
    share a single AI_CALL_TIMEOUT_SECONDS budget so a slow rung can't stack
    timeouts and stall the status-change request. Returns a StockCheckResult.
    """
    items = list(order.items.select_related("product").all())
    if not items:
        return StockCheckResult(status="skipped", summary=None, provider=None)

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

    chain = get_provider_chain()
    deadline = time.monotonic() + AI_CALL_TIMEOUT_SECONDS

    for provider in chain:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            logger.warning(
                "AI stock-check budget (%ss) exhausted before trying %s for order %s.",
                AI_CALL_TIMEOUT_SECONDS,
                _provider_label(provider),
                order.id,
            )
            break

        label = _provider_label(provider)
        try:
            summary = _run_agent_once(
                provider,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                timeout=min(remaining, AI_RUNG_TIMEOUT_SECONDS),
            )
            return StockCheckResult(status="ok", summary=summary, provider=label)
        except FutureTimeoutError:
            logger.warning(
                "AI provider %s timed out while evaluating order %s; falling back to the next rung "
                "(the order's status change was already saved).",
                label,
                order.id,
            )
        except Exception:
            logger.exception(
                "AI provider %s failed while evaluating order %s; falling back to the next rung.",
                label,
                order.id,
            )

    logger.error(
        "Every AI provider rung failed or timed out while evaluating order %s; no stock check ran.",
        order.id,
    )
    return StockCheckResult(status="unavailable", summary=None, provider=None)
