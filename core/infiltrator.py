import os
import time
import random
import threading
from core.logger import log

_infiltrator_state = {
    "running": False,
    "current_url": None,
    "status_msg": "Apagado",
    "last_screenshot": None,
    "task_queue": [],
}


class InfiltratorManager:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.thread = None

        # Guardaremos el perfil de Chrome en la carpeta _sessions
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.user_data_dir = os.path.join(
            BASE_DIR, "_sessions", "chrome_stealth_profile"
        )
        os.makedirs(self.user_data_dir, exist_ok=True)

    def _human_typing(self, selector, text):
        """Escribe texto simulando retrasos humanos entre teclas."""
        if not self.page:
            return
        self.page.focus(selector)
        for char in text:
            self.page.keyboard.type(char)
            time.sleep(random.uniform(0.05, 0.15))

    def _human_scroll(self):
        """Simula scroll orgánico para no parecer un bot estático."""
        if not self.page:
            return
        scrolls = random.randint(1, 4)
        for _ in range(scrolls):
            direction = random.choice([1, -1])
            amount = random.randint(100, 600) * direction
            self.page.mouse.wheel(0, amount)
            time.sleep(random.uniform(0.5, 2.0))

    def _human_mouse_move(self):
        """Mueve el mouse a un punto aleatorio."""
        if not self.page:
            return
        try:
            viewport = self.page.viewport_size
            if not viewport:
                return
            x = random.randint(0, viewport["width"])
            y = random.randint(0, viewport["height"])
            self.page.mouse.move(x, y, steps=random.randint(5, 15))
        except Exception:
            pass

    def queue_task(self, task_dict):
        global _infiltrator_state
        _infiltrator_state["task_queue"].append(task_dict)
        return True, "Tarea encolada en el Infiltrador."

    def start_infiltration(self, target_url):
        global _infiltrator_state
        if _infiltrator_state["running"]:
            return False, "El infiltrador ya está en ejecución."

        _infiltrator_state["running"] = True
        _infiltrator_state["last_screenshot"] = None
        _infiltrator_state["status_msg"] = (
            f"Iniciando infiltración hacia {target_url}..."
        )

        self.thread = threading.Thread(
            target=self._infiltration_loop, args=(target_url,), daemon=True
        )
        self.thread.start()
        return True, "Infiltrador iniciado."

    def stop_infiltration(self):
        global _infiltrator_state
        _infiltrator_state["running"] = False
        if self.thread and self.thread.is_alive():
            _infiltrator_state["status_msg"] = "Deteniendo..."
            return True, "Infiltrador deteniéndose (espera un par de segundos)."
        else:
            _infiltrator_state["status_msg"] = "Apagado"
            return True, "Infiltrador detenido."

    def _infiltration_loop(self, target_url):
        global _infiltrator_state
        from playwright.sync_api import sync_playwright
        from playwright_stealth import Stealth

        try:
            self.playwright = sync_playwright().start()

            # Usar persistent context para mantener cookies (sesión logueada)
            _infiltrator_state["status_msg"] = "Lanzando Chrome en modo Stealth..."
            self.context = self.playwright.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                headless=False,  # Importante: False para poder hacer login manual la primera vez o evadir mejor
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-infobars",
                    "--start-maximized",
                ],
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            )

            self.page = (
                self.context.pages[0] if self.context.pages else self.context.new_page()
            )

            # Aplicar stealth evasivo
            Stealth().apply_stealth_sync(self.page)

            _infiltrator_state["status_msg"] = f"Navegando a {target_url}..."
            self.page.goto(target_url, wait_until="domcontentloaded")
            _infiltrator_state["current_url"] = self.page.url

            # Bucle de mantenimiento y emulación humana
            while _infiltrator_state["running"]:
                _infiltrator_state["current_url"] = self.page.url

                if _infiltrator_state["task_queue"]:
                    task = _infiltrator_state["task_queue"].pop(0)
                    self._execute_task(task)
                    continue

                _infiltrator_state["status_msg"] = (
                    f"Monitoreando orgánicamente: {self.page.url}"
                )

                # Acciones aleatorias para mantener viva la sesión sin parecer bot
                sleep_time = int(random.uniform(5.0, 15.0))
                for _ in range(sleep_time):
                    if not _infiltrator_state["running"]:
                        break
                    time.sleep(1)

                if not _infiltrator_state["running"]:
                    break

                action = random.choice(["scroll", "mouse", "wait"])
                if action == "scroll":
                    self._human_scroll()
                elif action == "mouse":
                    self._human_mouse_move()

                # Tomar un screenshot para el dashboard
                try:
                    screenshot_bytes = self.page.screenshot(quality=60, type="jpeg")
                    import base64

                    _infiltrator_state["last_screenshot"] = (
                        "data:image/jpeg;base64,"
                        + base64.b64encode(screenshot_bytes).decode("utf-8")
                    )
                except Exception:
                    pass

        except Exception as e:
            if "has been closed" in str(e) or not _infiltrator_state["running"]:
                pass  # Es esperado si el usuario o el sistema cerró el navegador forzosamente
            else:
                log.error(f"[Infiltrator] Error en la rutina principal: {e}")
                _infiltrator_state["status_msg"] = f"Error: {str(e)}"
        finally:
            _infiltrator_state["running"] = False
            try:
                if self.context:
                    self.context.close()
                if self.playwright:
                    self.playwright.stop()
            except Exception:
                pass
            
            if _infiltrator_state["status_msg"] == "Deteniendo..." or not _infiltrator_state["status_msg"].startswith("Error"):
                _infiltrator_state["status_msg"] = "Apagado"
                
            log.info("[Infiltrator] Rutina terminada.")

    def _execute_task(self, task):
        global _infiltrator_state
        try:
            if task["type"] == "freelancer_bid":
                url = task["url"]
                proposal = task["proposal"]
                _infiltrator_state["status_msg"] = f"Aplicando a oferta: {url}"
                self.page.goto(url, wait_until="domcontentloaded")
                time.sleep(random.uniform(3, 6))

                # Intentar localizar el campo de propuesta
                # Freelancer usa textareas, intentaremos localizar la primera razonable o buscar por placeholder
                try:
                    textarea = self.page.locator("textarea").first
                    # Esperar máximo 10 segundos para no bloquear el bot eternamente
                    textarea.wait_for(state="visible", timeout=10000)
                    textarea.scroll_into_view_if_needed()
                    # Usar force=True por si hay banners o popups bloqueando el clic
                    textarea.click(force=True)
                    time.sleep(0.5)
                    self.page.keyboard.type(proposal, delay=15)  # Tipeo humano
                    _infiltrator_state["status_msg"] = (
                        "Propuesta escrita. Enviando (Full Auto-Pilot)..."
                    )

                    try:
                        time.sleep(2)
                        # Buscar botón de enviar (Place Bid o Submit)
                        for btn_text in [
                            "Place Bid",
                            "Submit Proposal",
                            "Enviar Oferta",
                            "Submit",
                        ]:
                            btn = self.page.locator(
                                f"button:has-text('{btn_text}')"
                            ).first
                            if btn:
                                try:
                                    btn.wait_for(state="visible", timeout=2000)
                                    btn.scroll_into_view_if_needed()
                                    btn.click(force=True)
                                    _infiltrator_state["status_msg"] = (
                                        f"¡Oferta enviada exitosamente ({btn_text})!"
                                    )
                                    log.info(
                                        f"[Infiltrator] 💸 Oferta enviada automáticamente a {url}"
                                    )
                                    break
                                except Exception:
                                    pass
                    except Exception as e:
                        log.error(
                            f"[Infiltrator] Error al clickear el botón de enviar: {e}"
                        )
                except Exception as e:
                    if "Timeout" in str(e):
                        log.warning(
                            "[Infiltrator] No se encontró la caja de texto en la oferta (Posiblemente cerró, no cumples los requisitos, o requiere relogueo). Saltando..."
                        )
                    else:
                        log.error(f"[Infiltrator] Error al escribir propuesta: {e}")

                time.sleep(3)
        except Exception as e:
            log.error(f"[Infiltrator] Error ejecutando tarea {task}: {e}")


manager = InfiltratorManager()


def start():
    pass  # Inicialización dummy requerida por el service_loader


def get_status():
    global _infiltrator_state
    return _infiltrator_state


def start_job(url):
    return manager.start_infiltration(url)


def stop_job():
    return manager.stop_infiltration()
