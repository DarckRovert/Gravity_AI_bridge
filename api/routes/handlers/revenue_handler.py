import json
import os
import sqlite3 as _sq3

def handle_cost(handler):
    try:
        from core.cost_tracker import CostTracker, _get_daily_limit
        over_limit, daily = CostTracker.check_limit()
        data = {
            "session_cost":    CostTracker.get_session_cost(),
            "session_tokens":  CostTracker.get_session_tokens(),
            "daily_cost":      daily,
            "daily_limit":     _get_daily_limit(),
            "over_limit":      over_limit,
            "daily_breakdown": CostTracker.get_daily_breakdown(),
        }
        body = json.dumps(data, indent=2).encode("utf-8")
        handler.send_response(200)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(body)
    except Exception as e:
        handler.send_response(500)
        handler.end_headers()
        handler.wfile.write(json.dumps({"error": str(e)}).encode())

def handle_revenue_top_jobs(handler):
    try:
        from core.revenue_tracker import get_top_jobs
        body = json.dumps(get_top_jobs(), ensure_ascii=False).encode("utf-8")
        handler.send_response(200)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(body)
    except Exception as e:
        handler.send_response(500)
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(json.dumps({"error": str(e)}).encode())

def handle_youtube_quota(handler):
    try:
        from core.youtube_uploader import get_quota_status
        body = json.dumps(get_quota_status(), ensure_ascii=False).encode("utf-8")
        handler.send_response(200)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(body)
    except Exception as e:
        handler.send_response(500)
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(json.dumps({"error": str(e)}).encode())

def handle_cost_limit(handler):
    try:
        length = int(handler.headers.get("Content-Length", 0))
        data   = json.loads(handler.rfile.read(length)) if length else {}
        limit  = float(data.get("limit_usd", 10.0))
        from core.cost_tracker import CostTracker
        CostTracker.set_daily_limit(limit)
        body = json.dumps({"ok": True, "limit_usd": limit}).encode("utf-8")
        handler.send_response(200)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(body)
    except Exception as e:
        handler.send_response(500)
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(json.dumps({"error": str(e)}).encode())

def handle_revenue_views_update(handler):
    try:
        length  = int(handler.headers.get("Content-Length", 0))
        data    = json.loads(handler.rfile.read(length)) if length else {}
        job_id  = data.get("job_id")
        views   = data.get("views", 0)
        if job_id is None:
            handler.send_response(400)
            handler._send_cors()
            handler.end_headers()
            handler.wfile.write(json.dumps({"error": "job_id requerido"}).encode())
            return
        from core.revenue_tracker import update_views
        update_views(int(job_id), int(views))
        body = json.dumps({"ok": True, "job_id": job_id, "views": views}).encode()
        handler.send_response(200)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(body)
    except Exception as e:
        handler.send_response(500)
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(json.dumps({"error": str(e)}).encode())

def handle_youtube_auth_exchange(handler):
    try:
        length = int(handler.headers.get("Content-Length", 0))
        data   = json.loads(handler.rfile.read(length)) if length else {}
        code   = data.get("code", "").strip()
        if not code:
            handler.send_response(400)
            handler._send_cors()
            handler.end_headers()
            handler.wfile.write(json.dumps({"error": "Campo 'code' requerido"}).encode())
            return
        from core.youtube_uploader import exchange_auth_code
        result = exchange_auth_code(code)
        body = json.dumps(result).encode("utf-8")
        handler.send_response(200 if result.get("ok") else 400)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(body)
    except Exception as e:
        handler.send_response(500)
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(json.dumps({"error": str(e)}).encode())

def handle_youtube_upload(handler):
    try:
        length = int(handler.headers.get("Content-Length", 0))
        data   = json.loads(handler.rfile.read(length)) if length else {}
        job_id = int(data.get("job_id", 0))
        if not job_id:
            handler.send_response(400)
            handler._send_cors()
            handler.end_headers()
            handler.wfile.write(json.dumps({"error": "job_id requerido"}).encode())
            return
        BASE_D = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        db_p   = os.path.join(BASE_D, "_video_queue.sqlite")
        conn   = _sq3.connect(db_p)
        conn.row_factory = _sq3.Row
        row = conn.execute("SELECT output_path, title, topic, thumbnail_path FROM video_jobs WHERE id=?", (job_id,)).fetchone()
        conn.close()
        if not row or not row["output_path"]:
            handler.send_response(404)
            handler._send_cors()
            handler.end_headers()
            handler.wfile.write(json.dumps({"error": f"Job #{job_id} no encontrado o sin video."}).encode())
            return
        from core.youtube_uploader import upload_job_async
        upload_job_async(
            job_id     = job_id,
            video_path = row["output_path"],
            title      = row["title"] or row["topic"] or f"Video #{job_id}",
            thumb_path = row["thumbnail_path"] or "",
        )
        body = json.dumps({"ok": True, "job_id": job_id, "message": "Upload iniciado en background."}).encode()
        handler.send_response(200)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(body)
    except Exception as e:
        handler.send_response(500)
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(json.dumps({"error": str(e)}).encode())
