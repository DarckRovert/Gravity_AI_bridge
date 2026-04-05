"""
╔══════════════════════════════════════════════════════════════╗
║     GRAVITY AI — PROVIDER REGISTRY V7.0                      ║
║     Auto-discovery + hot-reload de todos los plugins        ║
╚══════════════════════════════════════════════════════════════╝
"""

import os
import importlib.util
import importlib
import threading
import time

from providers.base import ProviderPlugin, ProviderResult

_BASE   = os.path.dirname(os.path.dirname(__file__))   # F:\Gravity_AI_bridge
_LOCK   = threading.Lock()


class ProviderRegistry:
    """
    Auto-discovers all ProviderPlugin subclasses in providers/local/ and
    providers/cloud/ by importing every file matching *_provider.py or
    *_cloud.py. Maintains a singleton instance cache per class name.

    Usage:
        plugins   = ProviderRegistry.get_all_plugins()
        ollama    = ProviderRegistry.get_by_name("Ollama")
        cloud_all = ProviderRegistry.get_cloud_plugins()
    """

    _plugin_classes:   dict[str, type]          = {}   # name → class
    _instances:        dict[str, ProviderPlugin] = {}   # name → instance
    _discovered:       bool                      = False
    _last_discover_ts: float                     = 0.0
    _REDISCOVER_SECS:  float                     = 60.0  # hot-reload interval

    # ── Discovery ─────────────────────────────────────────────────────────────

    @classmethod
    def discover(cls, force: bool = False) -> None:
        """
        Scans providers/local/ and providers/cloud/ for plugin files.
        Thread-safe. Hot-reloads if called again after _REDISCOVER_SECS.
        """
        now = time.time()
        if not force and cls._discovered and (now - cls._last_discover_ts) < cls._REDISCOVER_SECS:
            return

        with _LOCK:
            # Double-checked locking
            now = time.time()
            if not force and cls._discovered and (now - cls._last_discover_ts) < cls._REDISCOVER_SECS:
                return

            new_classes: dict[str, type] = {}

            for category in ("local", "cloud"):
                cat_dir = os.path.join(_BASE, "providers", category)
                if not os.path.isdir(cat_dir):
                    continue
                for fname in sorted(os.listdir(cat_dir)):
                    if not (fname.endswith("_provider.py") or fname.endswith("_cloud.py")):
                        continue
                    if fname.startswith("_"):
                        continue   # skip _base_*.py helpers
                    module_name = f"providers.{category}.{fname[:-3]}"
                    fpath       = os.path.join(cat_dir, fname)
                    try:
                        spec   = importlib.util.spec_from_file_location(module_name, fpath)
                        mod    = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(mod)
                        for attr_name in dir(mod):
                            attr = getattr(mod, attr_name)
                            if (
                                isinstance(attr, type)
                                and issubclass(attr, ProviderPlugin)
                                and attr is not ProviderPlugin
                                and getattr(attr, "name", "")
                            ):
                                new_classes[attr.name] = attr
                    except Exception as exc:
                        # Individual bad plugin must not crash the registry
                        print(f"[Registry] Failed to load {fname}: {exc}")

            cls._plugin_classes   = new_classes
            cls._discovered       = True
            cls._last_discover_ts = now

            # Invalidate cached instances for classes that changed
            for name in list(cls._instances.keys()):
                if name not in cls._plugin_classes:
                    del cls._instances[name]

    # ── Instance access ───────────────────────────────────────────────────────

    @classmethod
    def _get_instance(cls, name: str) -> ProviderPlugin | None:
        if name not in cls._instances:
            plug_cls = cls._plugin_classes.get(name)
            if plug_cls is None:
                return None
            try:
                cls._instances[name] = plug_cls()
            except Exception:
                return None
        return cls._instances[name]

    @classmethod
    def get_all_plugins(cls) -> list[ProviderPlugin]:
        cls.discover()
        result = []
        for name in cls._plugin_classes:
            inst = cls._get_instance(name)
            if inst is not None:
                result.append(inst)
        return result

    @classmethod
    def get_local_plugins(cls) -> list[ProviderPlugin]:
        return [p for p in cls.get_all_plugins() if p.category == "local"]

    @classmethod
    def get_cloud_plugins(cls) -> list[ProviderPlugin]:
        return [p for p in cls.get_all_plugins() if p.category == "cloud"]

    @classmethod
    def get_by_name(cls, name: str) -> ProviderPlugin | None:
        cls.discover()
        # Case-insensitive lookup
        for n, _ in cls._plugin_classes.items():
            if n.lower() == name.lower():
                return cls._get_instance(n)
        return None

    @classmethod
    def get_names(cls) -> list[str]:
        cls.discover()
        return list(cls._plugin_classes.keys())

    @classmethod
    def reload(cls) -> None:
        """Force re-discovery (hot-reload)."""
        cls.discover(force=True)

    # ── Parallel health scan ──────────────────────────────────────────────────

    @classmethod
    def scan_all_health(cls) -> list[ProviderResult]:
        """
        Scans ALL plugins in parallel and returns a list of ProviderResults.
        Cloud providers that have no key configured are marked unhealthy
        without making network requests.
        """
        from concurrent.futures import ThreadPoolExecutor
        cls.discover()
        plugins = cls.get_all_plugins()

        def _safe_check(plugin: ProviderPlugin) -> ProviderResult:
            try:
                return plugin.check_health()
            except Exception as e:
                r           = plugin._make_result()
                r.is_healthy = False
                return r

        with ThreadPoolExecutor(max_workers=min(len(plugins), 20)) as ex:
            results = list(ex.map(_safe_check, plugins))

        return results


if __name__ == "__main__":
    print("Provider Registry V7.0 — Discovery test\n")
    ProviderRegistry.discover(force=True)
    names = ProviderRegistry.get_names()
    print(f"  Discovered {len(names)} plugin(s): {', '.join(names)}\n")
    results = ProviderRegistry.scan_all_health()
    for r in results:
        tag = "✅" if r.is_healthy else "🔴"
        print(f"  {tag}  {r.name:<18} {r.url} | {r.model_count}M")
