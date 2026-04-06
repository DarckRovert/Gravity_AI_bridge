"""
╔══════════════════════════════════════════════════════════════╗
║     GRAVITY AI — PROVIDER BASE CLASSES V7.1                  ║
║     ProviderResult + ProviderPlugin ABC                      ║
╚══════════════════════════════════════════════════════════════╝
All providers (local and cloud) implement ProviderPlugin.
"""

from abc import ABC, abstractmethod
from typing import Generator, Optional


# ── Unified scan result ───────────────────────────────────────────────────────

class ProviderResult:
    """
    Unified representation of a provider scan result.
    Backwards-compatible with V6 ProviderResult used by provider_scanner.py.
    """
    __slots__ = (
        "name", "url", "protocol", "category",
        "is_healthy", "models", "active_model", "response_ms",
        "supports_vision", "supports_function_calling", "max_context",
        "requires_key", "key_configured",
    )

    def __init__(self, name: str, url: str, protocol: str, category: str = "local"):
        self.name                     = name
        self.url                      = url
        self.protocol                 = protocol
        self.category                 = category  # "local" | "cloud"
        self.is_healthy               = False
        self.models: list[dict]       = []        # [{"name": str, "size": int}]
        self.active_model: str | None = None
        self.response_ms: int         = 0
        self.supports_vision          = False
        self.supports_function_calling = False
        self.max_context              = 131072
        self.requires_key             = False
        self.key_configured           = False

    # ── Backwards-compat properties (used by health_check.py, watchdog) ──────
    @property
    def model_count(self) -> int:
        return len(self.models)

    @property
    def port(self) -> int:
        try:
            return int(self.url.rstrip("/").split(":")[-1])
        except Exception:
            return 0

    def __repr__(self) -> str:
        status = "✅" if self.is_healthy else "🔴"
        return (f"ProviderResult({status} {self.name} | {self.url} | "
                f"{self.model_count}M | {self.response_ms}ms)")


# ── Abstract Plugin Base ──────────────────────────────────────────────────────

class ProviderPlugin(ABC):
    """
    Abstract base class for all Gravity AI provider plugins.

    Subclasses must set class-level attributes and implement the three
    abstract methods below. Everything else has sensible defaults.
    """

    # ── Class-level metadata (set these in every subclass) ───────────────────
    name:                    str  = ""       # "Ollama", "OpenAI", "Groq" …
    protocol:                str  = "openai" # wire protocol
    category:                str  = "local"  # "local" | "cloud"
    default_port:            int  = 0        # 0 → cloud / no fixed port
    requires_key:            bool = False
    supports_vision:         bool = False
    supports_function_calling: bool = False
    default_context:         int  = 131072

    # ── Abstract interface ────────────────────────────────────────────────────

    @abstractmethod
    def check_health(self) -> ProviderResult:
        """
        Probe this provider. Return a populated ProviderResult.
        Must be fast (< 2s); use short timeouts.
        """

    @abstractmethod
    def chat_stream(
        self,
        messages: list[dict],
        model:    str,
        options:  dict,
    ) -> Generator[str, None, None]:
        """
        Streaming chat.
        Yields raw content string chunks (NOT SSE-formatted).
        The consumer (ask_deepseek / bridge_server) handles SSE.
        """

    @abstractmethod
    def chat_complete(
        self,
        messages: list[dict],
        model:    str,
        options:  dict,
    ) -> str:
        """
        Non-streaming chat. Returns the full response as a string.
        """

    # ── Optional overrides ────────────────────────────────────────────────────

    def chat_stream_with_images(
        self,
        messages:    list[dict],
        model:       str,
        options:     dict,
        image_paths: list[str],
    ) -> Generator[str, None, None]:
        """
        Vision-capable streaming. Default falls back to text-only.
        Override in providers that support vision.
        """
        yield from self.chat_stream(messages, model, options)

    def load_model(self, model_name: str) -> bool:
        """
        Trigger a model load/warm-up (for engines like Lemonade).
        Returns True if the load was initiated successfully.
        Default: no-op, return True.
        """
        return True

    def get_cost_per_million_tokens(self, model: str) -> dict:
        """
        Token pricing in USD per 1 million tokens.
        Returns {"input": 0.0, "output": 0.0}.
        Local providers always return 0.0.
        """
        return {"input": 0.0, "output": 0.0}

    def get_display_name(self) -> str:
        return self.name

    def is_cloud(self) -> bool:
        return self.category == "cloud"

    def is_local(self) -> bool:
        return self.category == "local"

    # ── Helper: build a base ProviderResult for this plugin ──────────────────

    def _make_result(self, url: str = "") -> ProviderResult:
        r = ProviderResult(
            name     = self.name,
            url      = url or (f"http://localhost:{self.default_port}" if self.default_port else ""),
            protocol = self.protocol,
            category = self.category,
        )
        r.supports_vision              = self.supports_vision
        r.supports_function_calling    = self.supports_function_calling
        r.max_context                  = self.default_context
        r.requires_key                 = self.requires_key
        return r
