"""
╔══════════════════════════════════════════════════════════════════════════════╗
║        GRAVITY AI — GET ROUTES MIXIN: MEDIA [Modular Sub-Router]             ║
║            Video Studio, Image Lab, Fooocus y Streaming Multimedia           ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import glob
import time
import json
import mimetypes
import urllib.parse
from core.logger import log


class GetMediaMixin:
    """Sub-mixin especializado en rutas GET para Video, Imágenes y Archivos Estáticos Multimedia."""

    def _serve_static_output(self):
        raw = urllib.parse.unquote(self.path[len("/static/output/") :])
        if not raw:
            self.send_response(403)
            self.end_headers()
            return

        BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        fooocus_out = os.path.realpath(os.path.join(BASE, "_integrations", "Fooocus", "Fooocus", "outputs"))

        filepath = None
        candidate = os.path.realpath(os.path.join(fooocus_out, raw.replace("/", os.sep)))
        if candidate.startswith(fooocus_out + os.sep) and os.path.isfile(candidate):
            filepath = candidate
        else:
            basename = os.path.basename(raw)
            if basename and os.path.sep not in basename:
                for ext in ("*.png", "*.jpg", "*.jpeg", "*.webp"):
                    matches = glob.glob(os.path.join(fooocus_out, "**", basename), recursive=True)
                    if matches:
                        filepath = os.path.realpath(matches[0])
                        if not filepath.startswith(fooocus_out + os.sep):
                            filepath = None
                        break

        if not filepath:
            self.send_response(404)
            self.end_headers()
            return

        mime, _ = mimetypes.guess_type(filepath)
        mime = mime or "application/octet-stream"

        try:
            with open(filepath, "rb") as f:
                body = f.read()
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(body)))
            self._send_cors()
            self.end_headers()
            self.wfile.write(body)
        except Exception:
            self.send_response(500)
            self.end_headers()

    def _serve_images(self):
        """Sirve lista de imagenes generadas por Fooocus."""
        try:
            BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            fooocus_out = os.path.join(BASE, "_integrations", "Fooocus", "Fooocus", "outputs")
            files = []
            if os.path.isdir(fooocus_out):
                for ext in ("*.png", "*.jpg", "*.jpeg", "*.webp"):
                    files.extend(glob.glob(os.path.join(fooocus_out, "**", ext), recursive=True))

            files.sort(key=os.path.getmtime, reverse=True)
            img_urls = []
            for f in files[:50]:
                rel = os.path.relpath(f, fooocus_out).replace(os.sep, "/")
                img_urls.append(f"/static/output/{rel}")

            resp = {"images": img_urls, "count": len(img_urls)}
            body = json.dumps(resp).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors()
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            log.error(f"Error sirviendo imagenes: {e}")
            self.send_response(500)
            self.end_headers()

    def _serve_video_status(self):
        from api.routes.handlers.video_handler import handle_video_status
        handle_video_status(self)

    def _serve_video_voices(self):
        from api.routes.handlers.video_handler import handle_video_voices
        handle_video_voices(self)

    def _serve_video_engines(self):
        from api.routes.handlers.video_handler import handle_video_engines
        handle_video_engines(self)

    def _serve_video_animations(self):
        from api.routes.handlers.video_handler import handle_video_animations
        handle_video_animations(self)

    def _serve_video_list(self):
        from api.routes.handlers.video_handler import handle_video_list
        handle_video_list(self)

    def _serve_video_stream(self):
        from api.routes.handlers.video_handler import handle_video_stream
        handle_video_stream(self)

    def _serve_video_download(self):
        from api.routes.handlers.video_handler import handle_video_download
        handle_video_download(self)

    def _serve_video_thumbnail(self):
        from api.routes.handlers.video_handler import handle_video_thumbnail
        handle_video_thumbnail(self)

    def _serve_pollinations_health(self):
        try:
            from tools.pollinations_generator import health_check
            status = health_check()
            body = json.dumps(status, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors()
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            body = json.dumps({"online": False, "message": str(e)}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors()
            self.end_headers()
            self.wfile.write(body)

    def _serve_image_lab_list(self):
        try:
            BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            lab_dir = os.path.join(BASE, "_integrations", "ImageLab")
            files = []
            if os.path.isdir(lab_dir):
                for ext in ("*.png", "*.jpg", "*.jpeg", "*.webp"):
                    files.extend(glob.glob(os.path.join(lab_dir, ext)))

            files.sort(key=os.path.getmtime, reverse=True)
            img_urls = []
            for f in files[:50]:
                basename = os.path.basename(f)
                img_urls.append({
                    "url": f"/static/imagelab/{basename}",
                    "name": basename,
                    "date": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.path.getmtime(f))),
                })

            resp = {"images": img_urls, "count": len(img_urls)}
            body = json.dumps(resp).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors()
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            body_err = json.dumps({"error": str(e)}).encode()
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self._send_cors()
            self.end_headers()
            self.wfile.write(body_err)

    def _serve_static_image_lab(self):
        raw = self.path[len("/static/imagelab/") :]
        if not raw or ".." in raw:
            self.send_response(403)
            self.end_headers()
            return

        BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        lab_dir = os.path.realpath(os.path.join(BASE, "_integrations", "ImageLab"))
        filepath = os.path.realpath(os.path.join(lab_dir, os.path.basename(raw)))

        if not filepath.startswith(lab_dir + os.sep) or not os.path.isfile(filepath):
            self.send_response(404)
            self.end_headers()
            return

        mime, _ = mimetypes.guess_type(filepath)
        mime = mime or "application/octet-stream"

        try:
            with open(filepath, "rb") as f:
                body = f.read()
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(body)))
            self._send_cors()
            self.end_headers()
            self.wfile.write(body)
        except Exception:
            self.send_response(500)
            self.end_headers()

    def _serve_video_upload_status(self):
        try:
            params = dict(urllib.parse.parse_qsl(urllib.parse.urlparse(self.path).query))
            job_id_str = params.get("job_id", "0")
            if not job_id_str.isdigit():
                self.send_response(400)
                self._send_cors()
                self.end_headers()
                self.wfile.write(json.dumps({"error": "job_id debe ser un entero"}).encode())
                return
            from core.youtube_uploader import get_upload_status
            data = get_upload_status(int(job_id_str))
            body = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors()
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_response(500)
            self._send_cors()
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
