import os
import time
import threading
from typing import Dict, List, Any, Generator
from providers.base import ProviderPlugin, ProviderResult

_BASE = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
MODELS_DIR = os.path.join(_BASE, "models")
MAX_CONCURRENT_MODELS = 2
IDLE_TIMEOUT_SEC = 300  # 5 minutos


class NativeLlamaProvider(ProviderPlugin):
    name = "Native Llama"
    protocol = "llama.cpp"
    category = "local"
    default_port = 0
    requires_key = False
    supports_vision = False
    supports_function_calling = False
    default_context = 8192

    _instances: Dict[str, Dict[str, Any]] = (
        {}
    )  # { "model_name": {"instance": Llama, "last_used": float} }
    _inference_lock = threading.RLock()
    _watchdog_started = False

    def __init__(self):
        super().__init__()
        self._start_watchdog()

    def _start_watchdog(self):
        with self._inference_lock:
            if NativeLlamaProvider._watchdog_started:
                return
            NativeLlamaProvider._watchdog_started = True

        def watchdog_loop():
            while True:
                time.sleep(10)  # Comprueba cada 10 segundos
                now = time.time()
                try:
                    import psutil

                    has_psutil = True
                except ImportError:
                    has_psutil = False

                with self._inference_lock:
                    to_delete = []
                    # Comportamiento dinámico bajo presión de RAM
                    current_timeout = IDLE_TIMEOUT_SEC
                    if has_psutil:
                        vm = psutil.virtual_memory()
                        available_gb = vm.available / (1024**3)
                        percent_used = vm.percent
                        # Si la memoria libre es crítica (< 2.5 GB o > 88% usada), bajamos el timeout de inactividad a 15 segundos
                        if percent_used > 88.0 or available_gb < 2.5:
                            current_timeout = 15.0
                            print(
                                f"\n[Native Llama Watchdog] ¡Presión de RAM detectada! (Uso: {percent_used}%, Disponible: {available_gb:.2f} GB). Reduciendo timeout a {current_timeout}s."
                            )

                    for m_name, data in self._instances.items():
                        if now - data["last_used"] > current_timeout:
                            to_delete.append(m_name)

                    for m_name in to_delete:
                        print(
                            f"\n[Native Llama Watchdog] Modelo '{m_name}' inactivo por > {current_timeout}s. Liberando RAM."
                        )
                        del self._instances[m_name]["instance"]
                        del self._instances[m_name]
                        import gc

                        gc.collect()

        t = threading.Thread(
            target=watchdog_loop, daemon=True, name="NativeLlamaWatchdog"
        )
        t.start()

    def _get_gguf_models(self) -> List[Dict[str, Any]]:
        models = []
        if os.path.exists(MODELS_DIR):
            for f in os.listdir(MODELS_DIR):
                if f.endswith(".gguf"):
                    path = os.path.join(MODELS_DIR, f)
                    size_mb = os.path.getsize(path) // (1024 * 1024)
                    models.append({"name": f, "size": size_mb, "path": path})
        return models

    def check_health(self) -> ProviderResult:
        r = self._make_result("native://llama")
        try:
            import llama_cpp

            r.is_healthy = True
        except ImportError:
            r.is_healthy = False
            r.models = []
            return r

        ggufs = self._get_gguf_models()
        if not ggufs:
            r.is_healthy = False
            return r

        r.models = ggufs
        r.is_healthy = True
        with self._inference_lock:
            if self._instances:
                # Retornar el más reciente como active
                latest = max(self._instances.items(), key=lambda x: x[1]["last_used"])
                r.active_model = latest[0]
            else:
                r.active_model = ggufs[0]["name"] if ggufs else None
        r.response_ms = 1
        return r

    def _load_model(self, model_name: str, options: Dict[str, Any]):
        import llama_cpp

        path = os.path.join(MODELS_DIR, model_name)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Model '{model_name}' not found in {MODELS_DIR}")

        if model_name in self._instances:
            self._instances[model_name]["last_used"] = time.time()
            return  # Already loaded

        # Obtener tamaño estimado en bytes
        model_size_bytes = os.path.getsize(path)

        # Monitoreo inteligente de RAM antes de cargar
        try:
            import psutil

            has_psutil = True
        except ImportError:
            has_psutil = False

        if has_psutil:
            # Requerimos el tamaño del modelo + 1 GB de buffer
            required_free_bytes = model_size_bytes + 1_024_000_000
            available_bytes = psutil.virtual_memory().available

            while available_bytes < required_free_bytes and self._instances:
                # Evict el más antiguo cargado (LRU)
                oldest = min(self._instances.items(), key=lambda x: x[1]["last_used"])
                oldest_name = oldest[0]
                print(
                    f"\n[Native Llama] Memoria insuficiente para cargar '{model_name}' (Libre: {available_bytes/(1024**3):.2f} GB, Requerido con buffer: {required_free_bytes/(1024**3):.2f} GB). Descargando '{oldest_name}'..."
                )
                del self._instances[oldest_name]["instance"]
                del self._instances[oldest_name]
                import gc

                gc.collect()
                available_bytes = psutil.virtual_memory().available

        # Si aún supera MAX_CONCURRENT_MODELS, aplicar el límite por LRU como salvaguarda
        if len(self._instances) >= MAX_CONCURRENT_MODELS:
            oldest = min(self._instances.items(), key=lambda x: x[1]["last_used"])
            oldest_name = oldest[0]
            print(
                f"\n[Native Llama] Límite de RAM alcanzado ({MAX_CONCURRENT_MODELS}). Descargando '{oldest_name}'..."
            )
            del self._instances[oldest_name]["instance"]
            del self._instances[oldest_name]
            import gc

            gc.collect()

        print(f"\n[Native Llama] Cargando '{model_name}' en memoria...")
        ctx = options.get("num_ctx", self.default_context)
        instance = llama_cpp.Llama(
            model_path=path, n_ctx=ctx, n_gpu_layers=-1, verbose=False
        )
        self._instances[model_name] = {"instance": instance, "last_used": time.time()}

    def chat_stream(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        options: Dict[str, Any],
    ) -> Generator[str, None, None]:
        try:
            import llama_cpp
        except ImportError:
            yield "[Native Llama] Error: llama-cpp-python no está instalado. Ejecuta install_native_llm.bat"
            return

        try:
            with self._inference_lock:
                self._load_model(model, options)
                self._instances[model]["last_used"] = time.time()

                formatted_messages = []
                for m in messages:
                    formatted_messages.append(
                        {"role": m.get("role", "user"), "content": m.get("content", "")}
                    )

                stream = self._instances[model]["instance"].create_chat_completion(
                    messages=formatted_messages,
                    stream=True,
                    temperature=options.get("temperature", 0.7),
                    max_tokens=options.get("max_tokens", 4096),
                )

                for chunk in stream:
                    if "choices" in chunk and len(chunk["choices"]) > 0:
                        delta = chunk["choices"][0].get("delta", {})
                        if "content" in delta:
                            yield delta["content"]

                self._instances[model]["last_used"] = time.time()

        except Exception as e:
            yield f"[Native Llama] Error durante inferencia nativa: {e}"

    def chat_complete(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        options: Dict[str, Any],
    ) -> str:
        chunks = list(self.chat_stream(messages, model, options))
        return "".join(chunks)
