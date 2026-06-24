"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  GRAVITY AI — STEALTH UPLOADER V1.0                                          ║
║  Módulo de subida de videos sin API para TikTok e Instagram                  ║
║  Usa Playwright Stealth para emular navegación humana y publicar Reels/Shorts║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import time
import random
from core.logger import log

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USER_DATA_DIR = os.path.join(BASE_DIR, "_sessions", "social_stealth_profile")


class StealthUploader:
    def __init__(self):
        os.makedirs(USER_DATA_DIR, exist_ok=True)
        try:
            from playwright_stealth import Stealth

            self._stealth = Stealth()
        except ImportError:
            self._stealth = None
            log.warning(
                "[StealthUploader] playwright-stealth no instalado. Fallback a vanilla."
            )

    def _human_typing(self, node, selector: str, text: str):
        try:
            node.locator(selector).first.click()
            time.sleep(1)
            kb = node.keyboard if hasattr(node, "keyboard") else node.page.keyboard
            for char in text:
                if char == "\n":
                    kb.press("Enter")
                else:
                    kb.type(char)
                time.sleep(random.uniform(0.02, 0.08))
        except Exception as e:
            log.warning(f"[StealthUploader] Error tipado humano: {e}")

    def _launch_browser(self, p, mobile=False):
        kwargs = {
            "user_data_dir": USER_DATA_DIR,
            "headless": False,  # Vital para evadir detección y captchas
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
            ],
        }

        if mobile:
            # Emular iPhone para Instagram Reels
            kwargs["viewport"] = {"width": 390, "height": 844}
            kwargs["user_agent"] = (
                "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
            )
        else:
            kwargs["viewport"] = {"width": 1280, "height": 800}
            kwargs["user_agent"] = (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )

        context = p.chromium.launch_persistent_context(**kwargs)
        page = context.pages[0] if context.pages else context.new_page()
        if self._stealth:
            self._stealth.apply_stealth_sync(page)
        return context, page

    def upload_to_tiktok(self, video_path: str, caption: str) -> dict:
        log.info("[StealthUploader] Iniciando subida a TikTok via browser...")
        from playwright.sync_api import sync_playwright

        try:
            with sync_playwright() as p:
                context, page = self._launch_browser(p, mobile=False)

                # Navegar al uploader
                page.goto(
                    "https://www.tiktok.com/creator-center/upload",
                    wait_until="domcontentloaded",
                )
                time.sleep(5)

                # Check login
                if "login" in page.url or page.locator("text=Log in").count() > 0:
                    log.error(
                        "[StealthUploader] Se requiere login en TikTok. Ejecuta start_login()."
                    )
                    context.close()
                    return {"ok": False, "error": "Login requerido en TikTok."}

                # TikTok a menudo pone el uploader dentro de un iframe
                upload_frame = page
                for frame in page.frames:
                    if "creator" in frame.url or "upload" in frame.url:
                        upload_frame = frame
                        break

                # Subir archivo
                file_input = upload_frame.locator('input[type="file"][accept*="video"]')
                file_input.wait_for(state="attached", timeout=60000)
                file_input.set_input_files(video_path)

                log.info(
                    "[StealthUploader] Video adjuntado. Esperando caja de texto..."
                )
                time.sleep(5)  # Dar tiempo a que cambie la interfaz

                # Seleccionar la caja de descripción
                caption_box = upload_frame.locator(
                    '.public-DraftEditor-content, div[contenteditable="true"]'
                ).first
                caption_box.wait_for(state="visible", timeout=60000)

                # Limpiar cualquier modal u overlay (ej. joyride tutorial de TikTok)
                try:
                    page.evaluate(
                        "() => { document.querySelectorAll('.react-joyride__overlay, #react-joyride-portal, [data-test-id=\"overlay\"]').forEach(e => e.remove()); }"
                    )
                    upload_frame.evaluate(
                        "() => { document.querySelectorAll('.react-joyride__overlay, #react-joyride-portal, [data-test-id=\"overlay\"]').forEach(e => e.remove()); }"
                    )
                except Exception:
                    pass

                caption_box.click(force=True)
                page.keyboard.press("Control+A")
                page.keyboard.press("Backspace")
                self._human_typing(
                    upload_frame,
                    '.public-DraftEditor-content, div[contenteditable="true"]',
                    caption,
                )

                log.info(
                    "[StealthUploader] Descripción escrita. Buscando botón publicar..."
                )
                time.sleep(5)  # Esperar a que se habilite el botón

                # Click post
                post_btn = upload_frame.locator(
                    'button:has-text("Post"), button:has-text("Publicar")'
                ).last
                post_btn.click()

                log.info(
                    "[StealthUploader] Clic en Publicar. Esperando a que el video se suba completamente a los servidores..."
                )

                # Esperamos un indicador de éxito o simplemente damos un tiempo amplio (60s)
                # TikTok web muestra un modal de "Manage posts" o "View profile" cuando termina.
                try:
                    upload_frame.locator(
                        'text="Manage posts", text="Administrar", text="Ver perfil", text="View profile", div[class*="success"]'
                    ).first.wait_for(state="visible", timeout=120000)
                    log.info(
                        "[StealthUploader] Modal de éxito detectado. El video ha sido publicado."
                    )
                except Exception:
                    log.warning(
                        "[StealthUploader] No se detectó modal de éxito a tiempo, pero se esperó el margen de seguridad."
                    )
                    time.sleep(15)  # Tiempo de gracia extra

                context.close()
                return {"ok": True, "platform": "tiktok", "method": "stealth"}

        except Exception as e:
            log.error(f"[StealthUploader] Fallo en TikTok: {e}")
            return {"ok": False, "error": str(e)}

    def upload_to_instagram(self, video_path: str, caption: str) -> dict:
        log.info("[StealthUploader] Iniciando subida a Instagram via browser...")
        from playwright.sync_api import sync_playwright

        # Verificar que existe sesión guardada antes de intentar
        session_state = os.path.join(
            USER_DATA_DIR, "Default", "Network Persistent State"
        )
        cookies_file = os.path.join(USER_DATA_DIR, "Default", "Cookies")
        if not os.path.exists(USER_DATA_DIR) or not os.path.exists(cookies_file):
            msg = (
                "Sesión no inicializada. Ejecuta 'start_login()' primero "
                "para guardar las cookies de Instagram."
            )
            log.error(f"[StealthUploader] {msg}")
            return {"ok": False, "error": msg, "action_required": "start_login"}

        try:
            with sync_playwright() as p:
                # Instagram funciona mejor en mobile view para Reels directos
                context, page = self._launch_browser(p, mobile=True)

                # Timeout extendido a 60s + fallback a 'load'
                try:
                    page.goto(
                        "https://www.instagram.com/",
                        wait_until="domcontentloaded",
                        timeout=60000,
                    )
                except Exception:
                    log.warning(
                        "[StealthUploader] domcontentloaded timeout, reintentando con 'load'..."
                    )
                    try:
                        page.goto(
                            "https://www.instagram.com/",
                            wait_until="load",
                            timeout=90000,
                        )
                    except Exception as e2:
                        context.close()
                        return {
                            "ok": False,
                            "error": f"Instagram no responde tras 90s: {e2}. ¿Firewall o red bloqueada?",
                            "action_required": "check_network",
                        }

                time.sleep(3)

                # Detectar login requerido
                if page.locator('input[name="username"]').count() > 0:
                    log.error(
                        "[StealthUploader] Sesión de Instagram expirada. Requiere re-login."
                    )
                    context.close()
                    return {
                        "ok": False,
                        "error": "Sesión de Instagram expirada.",
                        "action_required": "start_login",
                    }

                # Cerrar modal "Add to Home Screen" si aparece
                try:
                    if page.locator('button:has-text("Cancel")').count() > 0:
                        page.locator('button:has-text("Cancel")').click()
                        time.sleep(1)
                except Exception:
                    pass

                # Intentar inyectar archivo directamente si existe el input oculto
                file_input = page.locator('input[type="file"][accept*="video"]')
                if file_input.count() > 0:
                    file_input.set_input_files(video_path)
                else:
                    # Alternativa: Click en botón de (+) Nuevo Post
                    new_post_btn = (
                        page.locator(
                            'svg[aria-label="New post"], svg[aria-label="Nueva publicación"]'
                        )
                        .locator("xpath=..")
                        .first
                    )
                    new_post_btn.wait_for(state="visible", timeout=20000)
                    with page.expect_file_chooser() as fc_info:
                        new_post_btn.click()
                    file_chooser = fc_info.value
                    file_chooser.set_files(video_path)

                log.info("[StealthUploader] Archivo subido al modal.")
                time.sleep(4)

                # Siguiente (Next)
                page.locator(
                    'button:has-text("Next"), button:has-text("Siguiente")'
                ).first.click()
                time.sleep(2)

                # Siguiente (Next) de nuevo
                page.locator(
                    'button:has-text("Next"), button:has-text("Siguiente")'
                ).first.click()
                time.sleep(2)

                # Descripción
                caption_area = page.locator(
                    'textarea[aria-label="Write a caption..."], textarea[aria-label="Escribe un pie de foto..."]'
                )
                caption_area.wait_for(state="visible", timeout=15000)
                self._human_typing(page, "textarea", caption)

                time.sleep(1)
                # Publicar
                share_btn = page.locator(
                    'button:has-text("Share"), button:has-text("Compartir")'
                ).first
                share_btn.click()

                log.info("[StealthUploader] Compartiendo. Esperando confirmación...")
                time.sleep(20)

                context.close()
                return {"ok": True, "platform": "instagram", "method": "stealth"}

        except Exception as e:
            log.error(f"[StealthUploader] Fallo en Instagram: {e}")
            return {"ok": False, "error": str(e)}


def start_login():
    """Abre el navegador en modo manual para guardar la sesión."""
    from playwright.sync_api import sync_playwright

    print("\n[+] Iniciando perfil Stealth de Chrome...")
    with sync_playwright() as p:
        up = StealthUploader()
        context, page = up._launch_browser(p, mobile=False)
        print("=========================================================")
        print(">> AHORA INICIA SESIÓN MANUALMENTE EN TIKTOK E INSTAGRAM.")
        print(">> UNA VEZ QUE VEAS TU FEED, CIERRA LA VENTANA DEL NAVEGADOR.")
        print("=========================================================")

        # Abrir ambas en pestañas
        try:
            page.goto(
                "https://www.tiktok.com/login",
                wait_until="domcontentloaded",
                timeout=60000,
            )
        except Exception as e:
            print(f"[!] Aviso: TikTok tardó en cargar: {e}")

        page2 = context.new_page()
        try:
            page2.goto(
                "https://www.instagram.com/accounts/login/",
                wait_until="domcontentloaded",
                timeout=60000,
            )
        except Exception as e:
            print(f"[!] Aviso: Instagram tardó en cargar: {e}")

        # Esperar hasta que se cierren
        try:
            page.wait_for_event("close", timeout=0)
        except Exception:
            pass
        context.close()
        print("\n[+] Sesión persistida. Listo para envíos autónomos.")


if __name__ == "__main__":
    start_login()
