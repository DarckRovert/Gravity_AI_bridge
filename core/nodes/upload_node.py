"""
Gravity Workflow Node: UploadYouTube / UploadTikTok
Sube un video a YouTube o TikTok usando los uploaders del proyecto.
"""

from core.workflow_engine import GravityNode, registry
from core.logger import log


@registry.register
class UploadYouTubeNode(GravityNode):
    NODE_TYPE = "UploadYouTube"
    DESCRIPTION = "Sube un video a YouTube con título, descripción y tags SEO."
    INPUT_SCHEMA = {
        "video_path": "VIDEO",
        "title": "TEXT",
        "description": "TEXT",    # opcional
        "tags": "TEXT",           # opcional, CSV
        "thumbnail_path": "IMAGE",  # opcional
    }
    OUTPUT_SCHEMA = {
        "video_id": "TEXT",
        "url": "TEXT",
        "success": "BOOL",
    }

    def execute(self, inputs: dict) -> dict:
        from core.youtube_uploader import upload_video

        video_path: str = inputs.get("video_path", "")
        title: str = inputs.get("title") or self.config.get("title") or "Video Gravity AI"
        description: str = inputs.get("description") or self.config.get("description") or ""
        tags_raw: str = inputs.get("tags") or self.config.get("tags") or ""
        tags = [t.strip() for t in tags_raw.split(",") if t.strip()] if tags_raw else []
        thumbnail_path: str = inputs.get("thumbnail_path") or ""

        log.info(f"[UploadYouTubeNode] Subiendo a YouTube: {title[:60]}")

        try:
            result = upload_video(
                video_path=video_path,
                title=title,
                description=description,
                tags=tags,
                thumbnail_path=thumbnail_path or None,
            )
            video_id = result.get("video_id", "")
            return {
                "video_id": video_id,
                "url": f"https://youtu.be/{video_id}" if video_id else "",
                "success": bool(video_id),
            }
        except Exception as exc:
            log.error(f"[UploadYouTubeNode] Error: {exc}")
            return {"video_id": "", "url": "", "success": False}


@registry.register
class UploadTikTokNode(GravityNode):
    NODE_TYPE = "UploadTikTok"
    DESCRIPTION = "Sube un video a TikTok usando el stealth uploader de Gravity."
    INPUT_SCHEMA = {
        "video_path": "VIDEO",
        "caption": "TEXT",
        "hashtags": "TEXT",   # opcional, CSV
    }
    OUTPUT_SCHEMA = {
        "success": "BOOL",
        "message": "TEXT",
    }

    def execute(self, inputs: dict) -> dict:
        from core.stealth_uploader import upload_to_tiktok

        video_path: str = inputs.get("video_path", "")
        caption: str = inputs.get("caption") or self.config.get("caption") or ""
        hashtags_raw: str = inputs.get("hashtags") or self.config.get("hashtags") or ""

        log.info(f"[UploadTikTokNode] Subiendo a TikTok: {caption[:60]}")

        try:
            result = upload_to_tiktok(
                video_path=video_path,
                caption=caption,
                hashtags=hashtags_raw,
            )
            return {
                "success": result.get("success", False),
                "message": result.get("message", ""),
            }
        except Exception as exc:
            log.error(f"[UploadTikTokNode] Error: {exc}")
            return {"success": False, "message": str(exc)}
