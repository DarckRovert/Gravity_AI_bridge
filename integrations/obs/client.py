"""
╔══════════════════════════════════════════════════════════════════════════════╗
║               GRAVITY OBS CLIENT — integrations/obs/client.py                ║
║  Total control of OBS Studio: scenes, inputs, audio, streaming, recording   ║
╚══════════════════════════════════════════════════════════════════════════════╗
"""

import threading
import time
from core.logger import log

import logging

try:
    import obsws_python as obs

    OBS_AVAILABLE = True
    logging.getLogger("obsws_python").setLevel(logging.CRITICAL)
except ImportError:
    obs = None
    OBS_AVAILABLE = False

_DEFAULT_HOST = "127.0.0.1"
_DEFAULT_PORT = 4455
_DEFAULT_PASSWORD = "JZe2JTFSolWLni2i"
_RECONNECT_SECS = 10


class OBSClient:
    """Singleton thread-safe for OBS WebSocket v5."""

    _instance = None
    _init_lock = threading.Lock()

    def __new__(cls):
        with cls._init_lock:
            if cls._instance is None:
                inst = super().__new__(cls)
                inst._setup()
                cls._instance = inst
        return cls._instance

    def _setup(self):
        self._lock = threading.Lock()
        self._client = None
        self._connected = False
        self._enabled = False
        self._host = _DEFAULT_HOST
        self._port = _DEFAULT_PORT
        self._password = _DEFAULT_PASSWORD
        self._obs_version = ""
        self._ws_version = ""
        self._streaming = False
        self._recording = False
        self._current_scene = ""
        self._last_conn_error = False
        t = threading.Thread(
            target=self._reconnect_loop, daemon=True, name="OBSReconnectLoop"
        )
        t.start()
        log.info("[OBSClient] Integration driver initialized.")

    def configure(self, host: str, port: int, password: str):
        with self._lock:
            self._host = host
            self._port = port
            self._password = password
            self._enabled = True

    def connect(self) -> dict:
        if not OBS_AVAILABLE:
            return {
                "ok": False,
                "error": "obsws-python not installed. pip install obsws-python",
            }

        with self._lock:
            host = self._host
            port = self._port
            password = self._password
            if self._client is not None:
                try:
                    self._client.base_client.ws.close()
                except Exception:
                    pass
                self._client = None
                self._connected = False

        try:
            client = obs.ReqClient(host=host, port=port, password=password, timeout=5)
            ver = client.get_version()
            obs_version = ver.obs_version
            ws_version = ver.obs_web_socket_version

            with self._lock:
                self._client = client
                self._obs_version = obs_version
                self._ws_version = ws_version
                self._connected = True
                self._last_conn_error = False
                self._refresh_locked()

            log.info(f"[OBSClient] Connected to OBS {obs_version}")
            return {
                "ok": True,
                "obs_version": obs_version,
                "ws_version": ws_version,
                "host": host,
                "port": port,
            }
        except Exception as e:
            with self._lock:
                self._connected = False
                self._client = None
                show_warn = not getattr(self, "_last_conn_error", False)
                self._last_conn_error = True

            if show_warn:
                log.warning(
                    f"[OBSClient] Connection failed: {e} (Suppressing further identical warnings)"
                )
            return {"ok": False, "error": str(e)}

    def disconnect(self):
        with self._lock:
            if self._client:
                try:
                    self._client.base_client.ws.close()
                except Exception:
                    pass
            self._client = None
            self._connected = False
            self._enabled = False

    def is_connected(self) -> bool:
        return self._connected

    def _reconnect_loop(self):
        time.sleep(5)
        current_backoff = _RECONNECT_SECS
        max_backoff = 300
        while True:
            with self._lock:
                should_reconnect = self._enabled and not self._connected
            if should_reconnect and OBS_AVAILABLE:
                res = self.connect()
                if res.get("ok"):
                    current_backoff = _RECONNECT_SECS
                else:
                    current_backoff = min(current_backoff * 2, max_backoff)
            else:
                current_backoff = _RECONNECT_SECS
            time.sleep(current_backoff)

    def _refresh_locked(self):
        try:
            st = self._client.get_stream_status()
            self._streaming = st.output_active
        except Exception:
            pass
        try:
            rt = self._client.get_record_status()
            self._recording = rt.output_active
        except Exception:
            pass
        try:
            sc = self._client.get_current_program_scene()
            self._current_scene = sc.current_program_scene_name
        except Exception:
            pass

    def _req(self, fn, *args, **kwargs):
        if not self._connected or self._client is None:
            raise ConnectionError("OBS not connected")
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            if any(
                k in str(e).lower()
                for k in ("connection", "closed", "timeout", "broken")
            ):
                self._connected = False
                self._client = None
            raise

    def get_status(self) -> dict:
        with self._lock:
            if not self._connected:
                return {
                    "connected": False,
                    "host": self._host,
                    "port": self._port,
                    "obs_version": "",
                    "ws_version": "",
                    "streaming": False,
                    "recording": False,
                    "current_scene": "",
                }
            try:
                self._refresh_locked()
            except Exception:
                pass
            return {
                "connected": True,
                "host": self._host,
                "port": self._port,
                "obs_version": self._obs_version,
                "ws_version": self._ws_version,
                "streaming": self._streaming,
                "recording": self._recording,
                "current_scene": self._current_scene,
            }

    def get_scenes(self) -> list:
        with self._lock:
            resp = self._req(self._client.get_scene_list)
            return [
                {
                    "name": s["sceneName"],
                    "uuid": s.get("sceneUuid", ""),
                    "index": s.get("sceneIndex", i),
                }
                for i, s in enumerate(resp.scenes)
            ]

    def get_current_scene(self) -> str:
        with self._lock:
            return self._req(
                self._client.get_current_program_scene
            ).current_program_scene_name

    def switch_scene(self, scene_name: str) -> dict:
        with self._lock:
            self._req(self._client.set_current_program_scene, scene_name)
            self._current_scene = scene_name
            return {"ok": True, "scene_name": scene_name}

    def get_scene_items(self, scene_name: str) -> list:
        with self._lock:
            resp = self._req(self._client.get_scene_item_list, scene_name)
            return [
                {
                    "scene_item_id": it["sceneItemId"],
                    "source_name": it["sourceName"],
                    "source_type": it.get("inputKind", it.get("sourceType", "")),
                    "enabled": it["sceneItemEnabled"],
                    "index": it.get("sceneItemIndex", 0),
                }
                for it in resp.scene_items
            ]

    def set_item_visible(self, scene_name: str, item_id: int, visible: bool) -> dict:
        with self._lock:
            self._req(
                self._client.set_scene_item_enabled,
                scene_name=scene_name,
                item_id=item_id,
                enabled=visible,
            )
            return {
                "ok": True,
                "scene_name": scene_name,
                "item_id": item_id,
                "visible": visible,
            }

    def toggle_item_visible(self, scene_name: str, item_id: int) -> dict:
        with self._lock:
            cur = self._req(
                self._client.get_scene_item_enabled, scene_name, item_id
            ).scene_item_enabled
            self._req(
                self._client.set_scene_item_enabled,
                scene_name=scene_name,
                item_id=item_id,
                enabled=not cur,
            )
            return {
                "ok": True,
                "scene_name": scene_name,
                "item_id": item_id,
                "visible": not cur,
            }

    def get_inputs(self) -> list:
        AUDIO_KINDS = {
            "wasapi_input_capture",
            "wasapi_output_capture",
            "wasapi_process_output_capture",
            "pulse_input_capture",
            "pulse_output_capture",
            "coreaudio_input_capture",
            "coreaudio_output_capture",
            "ffmpeg_source",
            "browser_source",
            "vlc_source",
            "dshow_input",
            "ndi_source",
        }
        with self._lock:
            resp = self._req(self._client.get_input_list)
            inputs = []
            for inp in resp.inputs:
                name = inp["inputName"]
                kind = inp.get("inputKind", "")
                entry = {
                    "input_name": name,
                    "kind": kind,
                    "muted": False,
                    "volume_db": 0.0,
                }
                if kind in AUDIO_KINDS:
                    try:
                        entry["muted"] = self._client.get_input_mute(name).input_muted
                        entry["volume_db"] = round(
                            self._client.get_input_volume(name).input_volume_db, 1
                        )
                    except Exception:
                        pass
                inputs.append(entry)
            return inputs

    def toggle_mute(self, input_name: str) -> dict:
        with self._lock:
            self._req(self._client.toggle_input_mute, input_name)
            muted = self._req(self._client.get_input_mute, input_name).input_muted
            return {"ok": True, "input_name": input_name, "muted": muted}

    def set_volume(self, input_name: str, volume_db: float) -> dict:
        with self._lock:
            self._req(self._client.set_input_volume, input_name, vol_db=volume_db)
            return {"ok": True, "input_name": input_name, "volume_db": volume_db}

    def create_browser_source(
        self,
        scene_name: str,
        input_name: str,
        url: str,
        width: int = 400,
        height: int = 300,
        x: int = 0,
        y: int = 0,
    ) -> dict:
        with self._lock:
            resp = self._req(
                self._client.create_input,
                sceneName=scene_name,
                inputName=input_name,
                inputKind="browser_source",
                inputSettings={
                    "url": url,
                    "width": width,
                    "height": height,
                    "css": "body { background-color: rgba(0,0,0,0); margin: 0; }",
                    "fps": 30,
                    "shutdown": False,
                },
                sceneItemEnabled=True,
            )
            sid = resp.scene_item_id
            if x != 0 or y != 0:
                try:
                    self._client.set_scene_item_transform(
                        scene_name=scene_name,
                        item_id=sid,
                        transform={
                            "positionX": float(x),
                            "positionY": float(y),
                            "boundsWidth": float(width),
                            "boundsHeight": float(height),
                        },
                    )
                except Exception as e:
                    log.warning(f"[OBSClient] Transform error: {e}")
            return {
                "ok": True,
                "scene_name": scene_name,
                "input_name": input_name,
                "scene_item_id": sid,
                "url": url,
                "width": width,
                "height": height,
            }

    def update_browser_source_url(self, input_name: str, new_url: str) -> dict:
        with self._lock:
            self._req(
                self._client.set_input_settings,
                name=input_name,
                settings={"url": new_url},
                overlay=True,
            )
            try:
                self._client.press_input_properties_button(input_name, "refreshnocache")
            except Exception:
                pass
            return {"ok": True, "input_name": input_name, "url": new_url}

    def refresh_browser_source(self, input_name: str) -> dict:
        with self._lock:
            try:
                self._req(
                    self._client.press_input_properties_button,
                    input_name,
                    "refreshnocache",
                )
            except Exception as e:
                return {"ok": False, "error": str(e)}
            return {"ok": True, "input_name": input_name}

    def remove_input(self, input_name: str) -> dict:
        with self._lock:
            self._req(self._client.remove_input, input_name)
            return {"ok": True, "input_name": input_name}

    def get_stream_status(self) -> dict:
        with self._lock:
            st = self._req(self._client.get_stream_status)
            rt = self._req(self._client.get_record_status)
            return {
                "streaming": st.output_active,
                "recording": rt.output_active,
                "stream_timecode": getattr(st, "output_timecode", ""),
                "record_timecode": getattr(rt, "output_timecode", ""),
                "stream_bytes": getattr(st, "output_bytes", 0),
                "record_bytes": getattr(rt, "output_bytes", 0),
            }

    def start_stream(self) -> dict:
        with self._lock:
            self._req(self._client.start_stream)
            self._streaming = True
            return {"ok": True, "action": "start_stream"}

    def stop_stream(self) -> dict:
        with self._lock:
            if not self._connected or self._client is None:
                return {"ok": False, "error": "OBS not connected"}
            self._req(self._client.stop_stream)
            self._streaming = False
            return {"ok": True, "action": "stop_stream"}

    def toggle_stream(self) -> dict:
        with self._lock:
            self._req(self._client.toggle_stream)
            try:
                self._streaming = self._req(
                    self._client.get_stream_status
                ).output_active
            except Exception:
                self._streaming = not self._streaming
            return {"ok": True, "streaming": self._streaming}

    def start_record(self) -> dict:
        with self._lock:
            self._req(self._client.start_record)
            self._recording = True
            return {"ok": True, "action": "start_record"}

    def stop_record(self) -> dict:
        with self._lock:
            if not self._connected or self._client is None:
                return {"ok": False, "error": "OBS not connected"}
            self._req(self._client.stop_record)
            self._recording = False
            return {"ok": True, "action": "stop_record"}

    def toggle_record(self) -> dict:
        with self._lock:
            self._req(self._client.toggle_record)
            try:
                self._recording = self._req(
                    self._client.get_record_status
                ).output_active
            except Exception:
                self._recording = not self._recording
            return {"ok": True, "recording": self._recording}


# ── Global Singleton instance ──────────────────────────────────────────────────
_obs = OBSClient()


def auto_connect_if_configured():
    try:
        from core.config_manager import config

        cfg = config.get("obs_websocket", {})
        if not cfg.get("enabled", False):
            return
        password = cfg.get("password", "")
        if not password:
            try:
                from core.key_manager import KeyManager

                password = (
                    KeyManager.get_key("obs_websocket_password") or _DEFAULT_PASSWORD
                )
            except Exception:
                password = _DEFAULT_PASSWORD

        _obs.configure(
            host=cfg.get("host", _DEFAULT_HOST),
            port=int(cfg.get("port", _DEFAULT_PORT)),
            password=password,
        )
        _obs.connect()
        # Logging handled internally by connect() to prevent spam
    except Exception as e:
        log.warning(f"[OBSClient] auto_connect error: {e}")


def get_client() -> OBSClient:
    return _obs
