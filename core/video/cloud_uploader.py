"""
Gravity AI — Cloud Object Storage Uploader (Cloudflare R2 / AWS S3 / Supabase / Custom CDN)
Sube automáticamente los videos MP4 generados por los reporteros al almacenamiento CDN en la nube
para no saturar ni romper el repositorio de Git con archivos pesados.
"""

import os
import json
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("gravity")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def _load_storage_config() -> Dict[str, Any]:
    """Carga la configuración de almacenamiento en la nube desde config.yaml o _settings.json."""
    config = {}
    try:
        import yaml
        cfg_path = os.path.join(BASE_DIR, "config.yaml")
        if os.path.exists(cfg_path):
            with open(cfg_path, "r", encoding="utf-8") as f:
                raw = yaml.safe_load(f) or {}
                config = raw.get("object_storage", {})
    except Exception:
        pass

    # Intentar leer overrides desde _settings.json o KeyManager
    try:
        from core.key_manager import KeyManager
        r2_account = KeyManager.get_key("r2_account_id") or config.get("account_id", "")
        r2_access = KeyManager.get_key("r2_access_key_id") or config.get("access_key_id", "")
        r2_secret = KeyManager.get_key("r2_secret_access_key") or config.get("secret_access_key", "")
        r2_bucket = KeyManager.get_key("r2_bucket") or config.get("bucket", "gravity-media")
        r2_domain = KeyManager.get_key("r2_public_domain") or config.get("public_domain", "")

        if r2_account:
            config["account_id"] = r2_account
        if r2_access:
            config["access_key_id"] = r2_access
        if r2_secret:
            config["secret_access_key"] = r2_secret
        if r2_bucket:
            config["bucket"] = r2_bucket
        if r2_domain:
            config["public_domain"] = r2_domain
    except Exception:
        pass

    return config

def upload_video_to_cdn(file_path: str, filename_override: Optional[str] = None) -> Optional[str]:
    """
    Sube un archivo de video MP4 a Cloudflare R2 / AWS S3 y devuelve su URL pública en el CDN.
    Si no hay credenciales configuradas, devuelve None y registra una advertencia.
    """
    if not file_path or not os.path.exists(file_path):
        logger.warning(f"[CloudUploader] El archivo no existe: {file_path}")
        return None

    cfg = _load_storage_config()
    account_id = cfg.get("account_id", "").strip()
    access_key = cfg.get("access_key_id", "").strip()
    secret_key = cfg.get("secret_access_key", "").strip()
    bucket = cfg.get("bucket", "gravity-media").strip()
    public_domain = cfg.get("public_domain", "").strip().rstrip("/")

    filename = filename_override or os.path.basename(file_path)

    # 1. Intento de subida con boto3 (compatible con Cloudflare R2 y S3)
    if access_key and secret_key:
        try:
            import boto3
            from botocore.config import Config

            endpoint_url = (
                f"https://{account_id}.r2.cloudflarestorage.com"
                if account_id
                else cfg.get("endpoint_url")
            )

            s3_client = boto3.client(
                "s3",
                endpoint_url=endpoint_url,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                config=Config(signature_version="s3v4"),
                region_name="auto"
            )

            content_type = "video/mp4" if filename.endswith(".mp4") else "image/jpeg"
            logger.info(f"[CloudUploader] Subiendo {filename} a CDN ({bucket})...")

            s3_client.upload_file(
                file_path,
                bucket,
                filename,
                ExtraArgs={"ContentType": content_type}
            )

            if public_domain:
                public_url = f"{public_domain}/{filename}"
            elif account_id:
                public_url = f"https://pub-{account_id[:8]}.r2.dev/{filename}"
            else:
                public_url = f"https://{bucket}.s3.amazonaws.com/{filename}"

            logger.info(f"[CloudUploader] ✓ Video subido exitosamente a CDN: {public_url}")
            return public_url

        except Exception as e:
            logger.error(f"[CloudUploader] Error subiendo con boto3: {e}")

    logger.info(
        f"[CloudUploader] Cloudflare R2 / S3 no configurado en config.yaml (_settings.json). "
        f"El video se mantiene en almacenamiento local: {file_path}"
    )
    return None

def patch_json_with_video(title: str, video_url: str):
    """
    Busca en los JSON de noticias, ensayos y ciencia del portal React
    el artículo con el título más similar y le inyecta la URL del video.
    """
    if not video_url or not title:
        return
        
    portal_data_paths = [
        os.path.join(BASE_DIR, "..", "gravity-news-portal", "src", "data", "news.json"),
        os.path.join(BASE_DIR, "..", "gravity-news-portal", "src", "data", "essays.json"),
        os.path.join(BASE_DIR, "..", "gravity-news-portal", "src", "data", "science.json")
    ]
    
    # Normalizar titulo para búsqueda parcial
    normalized_title = title.lower().replace("resumen de noticia:", "").strip()
    
    for json_path in portal_data_paths:
        if not os.path.exists(json_path):
            continue
            
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            updated = False
            for item in data:
                # Comparamos títulos (puede haber truncamiento por eso se usa 'in')
                item_title = item.get("title", "").lower()
                if item_title and (item_title in normalized_title or normalized_title in item_title or normalized_title[:30] in item_title):
                    item["videoUrl"] = video_url
                    updated = True
                    logger.info(f"[CloudUploader] ✓ Enlazado video {video_url} al artículo: '{item.get('title')}' en {os.path.basename(json_path)}")
                    break
                    
            if updated:
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                return  # Si lo encontramos, no seguimos buscando
                
        except Exception as e:
            logger.error(f"[CloudUploader] Error parcheando {json_path}: {e}")

