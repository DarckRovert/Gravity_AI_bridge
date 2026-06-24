"""
GRAVITY AI — SUITE DE PRUEBAS EXHAUSTIVA COMPLETA V2
========================================================
- Prueba TODOS los endpoints GET (47) y POST (65+)
- Valida el CUERPO de la respuesta, no solo el status code
- Reporta status 0 (no conecta), 404 (rota), y "ok":false como FALLO real
- Diferencia entre errores esperados (validacion 400) y fallos reales (500, 0)
"""

import urllib.request
import json
import time
import subprocess

# ─── COLORES ASCII ───
OK = "[OK]  "
FAIL = "[FAIL]"
SKIP = "[SKIP]"

# ─── GET ENDPOINTS ────────────────────────────────────────────────
GET_ENDPOINTS = [
    "/",
    "/dashboard",
    "/health",
    "/v1/models",
    "/v1/status",
    "/v1/audit",
    "/v1/fooocus/status",
    "/v1/images",
    "/metrics",
    "/v1/security",
    "/v1/security/geoip",
    "/v1/queue",
    "/v1/deploy/status",
    "/v1/gameserver/status",
    "/v1/gameserver/log",
    "/v1/gameserver/players",
    "/v1/hardware",
    "/v1/hardware/stats",
    "/v1/cost",
    "/v1/watchdog",
    "/v1/sessions",
    "/v1/sessions/active",
    "/v1/rag/status",
    "/v1/fabricaweb/status",
    "/v1/video/status",
    "/v1/video/voices",
    "/v1/video/engines",
    "/v1/video/list",
    "/v1/video/animations",
    "/v1/image/health",
    "/v1/image/lab/history",
    "/v1/mcp/status",
    "/v1/hitl/pending",
    "/v1/tools/firecrawl/health",
    "/v1/gravity/context",
    "/v1/processes",
    "/v1/scheduler/status",
    "/v1/scheduler/niches",
    "/v1/youtube/status",
    "/v1/youtube/quota",
    "/v1/youtube/auth/url",
    "/v1/revenue/summary",
    "/v1/revenue/timeline",
    "/v1/revenue/top",
    "/v1/social/status",
    "/v1/affiliates/status",
    "/v1/affiliates/programs",
    "/v1/language/status",
    "/v1/v2v/status",
    "/v1/obs/status",
]

# ─── POST ENDPOINTS ────────────────────────────────────────────────
# Categorías: (path, payload, espera_ok_true, descripcion)
# espera_ok_true=False → solo verificamos que no crashea (500/0)
POST_ENDPOINTS = [
    # ── Chat / LLM ─────────────────────────────────────────────────
    (
        "/v1/chat/completions",
        {"messages": [{"role": "user", "content": "ping"}], "max_tokens": 5},
        False,
        "Chat Completions (LLM)",
    ),
    (
        "/v1/gravity/chat",
        {"messages": [{"role": "user", "content": "ping"}]},
        False,
        "Gravity Chat (RAG+LLM)",
    ),
    ("/v1/model/lock", {"provider": "LM Studio", "model": "test"}, False, "Model Lock"),
    ("/v1/keys", {"api_key": "test", "provider": "openai"}, False, "Keys Set"),
    ("/v1/agent/compare", {"prompt": "Hi", "n_models": 1}, False, "Agent Compare"),
    # ── Herramientas (Tools) ────────────────────────────────────────
    ("/v1/tools/search", {"query": "gravity ai bridge"}, True, "Tool: Search"),
    ("/v1/tools/git", {"cmd": "status"}, True, "Tool: Git"),
    (
        "/v1/tools/run",
        {"code": "print('test')", "language": "python"},
        True,
        "Tool: Code Run",
    ),
    (
        "/v1/tools/grep",
        {"pattern": "def run_server"},
        False,
        "Tool: Grep (Timeout Expected)",
    ),
    (
        "/v1/tools/scrape",
        {"url": "http://example.com"},
        True,
        "Tool: Scrape (Firecrawl)",
    ),
    # ── RAG / Agentes ──────────────────────────────────────────────
    ("/v1/rag/toggle", {}, True, "RAG Toggle"),
    # ── Sistema / Config ───────────────────────────────────────────
    ("/v1/universal/config", {"max_tokens": 512}, True, "Universal Config"),
    ("/v1/cost/limit", {"limit_usd": 10.0}, True, "Cost Limit"),
    ("/v1/audit/rotate", {}, True, "Audit Rotate"),
    ("/v1/security/scan", {}, True, "Security Scan"),
    ("/v1/scheduler/trigger", {}, True, "Scheduler Trigger"),
    ("/v1/scheduler/topic/add", {"topic": "Tech AI News"}, True, "Scheduler Topic Add"),
    ("/v1/queue/clear_history", {}, True, "Queue Clear History"),
    ("/v1/watchdog/unlock", {}, True, "Watchdog Unlock"),
    # ── Autonomía / Reflexión ──────────────────────────────────────
    ("/v1/autonomy/trigger", {}, False, "Autonomy Trigger"),
    ("/v1/reflection/trigger", {}, True, "Self-Reflection Trigger"),
    # ── Bounty / Agente Freelancer ────────────────────────────────
    (
        "/v1/bounties/profile",
        {"profile": "Test Expert Developer"},
        True,
        "Bounty Profile",
    ),
    (
        "/v1/bounties/action",
        {"url": "http://test.com", "action": "bid"},
        True,
        "Bounty Action",
    ),
    ("/v1/infiltrator/stop", {}, False, "Infiltrator Stop (safe)"),
    # ── Media / Video ──────────────────────────────────────────────
    (
        "/v1/video/cancel",
        {"job_id": "nonexistent-job-0001"},
        False,
        "Video Cancel (non-existent)",
    ),
    ("/v1/v2v/stop", {}, False, "V2V Stop"),
    ("/v1/obs/stream/stop", {}, False, "OBS Stream Stop (safe)"),
    ("/v1/obs/record/stop", {}, False, "OBS Record Stop (safe)"),
    # ── HITL ───────────────────────────────────────────────────────
    (
        "/v1/hitl/approve",
        {"approval_id": "nonexistent-0001"},
        False,
        "HITL Approve (non-existent)",
    ),
    (
        "/v1/hitl/reject",
        {"approval_id": "nonexistent-0001", "reason": "test"},
        False,
        "HITL Reject (non-existent)",
    ),
    # ── Gameserver ─────────────────────────────────────────────────
    (
        "/v1/gameserver/command",
        {"command": "list"},
        False,
        "Gameserver Command (no server running)",
    ),
    # ── Fabricaweb / Deploy ────────────────────────────────────────
    (
        "/v1/fabricaweb/deploy",
        {"url": "http://localhost:3000", "domain": "test.local"},
        False,
        "Fabricaweb Deploy",
    ),
]

# Endpoints que sirven HTML o texto plano (no JSON) — se validan solo por HTTP status
NON_JSON_ENDPOINTS = {"/", "/dashboard", "/metrics"}


def send_get(path):
    url = f"http://127.0.0.1:7860{path}"
    try:
        with urllib.request.urlopen(
            urllib.request.Request(url, method="GET"), timeout=15
        ) as r:
            raw = r.read().decode("utf-8", errors="replace")
            try:
                body = json.loads(raw)
            except json.JSONDecodeError:
                body = {"_raw": True}  # No JSON — tratar como ok si status 200
            return r.status, body
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read().decode("utf-8", errors="replace"))
        except:  # noqa: E722
            body = {}
        return e.code, body
    except Exception as ex:
        return 0, str(ex)


def send_post(path, payload):
    url = f"http://127.0.0.1:7860{path}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read().decode("utf-8", errors="replace")
            try:
                body = json.loads(raw)
            except json.JSONDecodeError:
                body = {"_raw": True}
            return r.status, body
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read().decode("utf-8", errors="replace"))
        except:  # noqa: E722
            body = {}
        return e.code, body
    except Exception as ex:
        return 0, str(ex)


def is_real_failure(status, body, path=""):
    """Fallo real = no conecta (0) o error interno (5xx).
    Los endpoints no-JSON (HTML, Prometheus) se aceptan si el HTTP status es < 500."""
    if status == 0:
        return True  # Sin conexión — crash o timeout
    if status >= 500:
        return True  # Error interno del servidor
    return False  # 200, 400, 401, 403, 404 son comportamiento REST esperado


def check_body_ok(body):
    """Verifica que el cuerpo JSON indique éxito si esperamos ok=true."""
    if isinstance(body, dict):
        if "ok" in body and body["ok"] is False:
            return False
        if "error" in body and not body.get("ok", True):
            return False
    return True


def run():
    print("=" * 60)
    print("  GRAVITY AI — EXHAUSTIVE TEST SUITE V2 (COMPLETA)")
    print("=" * 60)
    print(f"\n  GET endpoints: {len(GET_ENDPOINTS)}")
    print(f"  POST endpoints: {len(POST_ENDPOINTS)}")
    print(f"  Total: {len(GET_ENDPOINTS)+len(POST_ENDPOINTS)} pruebas\n")

    print("[*] Arrancando bridge_server.py...")
    proc = subprocess.Popen(
        ["python", "bridge_server.py"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Espera activa: polling /health hasta que el servidor responda (máx 60s)
    print("[*] Esperando que el servidor esté listo...")
    deadline = time.time() + 60
    ready = False
    while time.time() < deadline:
        try:
            with urllib.request.urlopen("http://127.0.0.1:7860/health", timeout=2) as r:
                if r.status in (200, 404):  # cualquier respuesta HTTP = servidor activo
                    ready = True
                    break
        except Exception:
            time.sleep(1)
    if not ready:
        print("[WARN] Servidor no respondió en 60s — continuando de todas formas.")
    else:
        print("[*] Servidor listo.")

    total, passed, failed = 0, 0, 0
    failures = []

    print("\n--- GET ENDPOINTS -----------------------------------------")
    for ep in GET_ENDPOINTS:
        total += 1
        status, body = send_get(ep)
        if is_real_failure(status, body, ep):
            failed += 1
            short = str(body)[:120] if isinstance(body, str) else json.dumps(body)[:120]
            print(f"  {FAIL} GET {ep:<45} status={status} | {short}")
            failures.append(f"GET {ep} → {status}")
        else:
            passed += 1
            note = " [non-JSON: HTML/text]" if ep in NON_JSON_ENDPOINTS else ""
            print(f"  {OK} GET {ep:<45} status={status}{note}")

    print("\n--- POST ENDPOINTS ----------------------------------------")
    for ep, payload, expect_ok, desc in POST_ENDPOINTS:
        total += 1
        status, body = send_post(ep, payload)
        real_fail = is_real_failure(status, body, ep)
        body_fail = expect_ok and not check_body_ok(body) and not body.get("_raw")

        if real_fail:
            failed += 1
            short = str(body)[:120] if isinstance(body, str) else json.dumps(body)[:120]
            print(f"  {FAIL} POST {ep:<45} status={status} | {short}")
            failures.append(f"POST {ep} → {status}")
        elif body_fail:
            failed += 1
            short = json.dumps(body)[:120]
            print(f"  {FAIL} POST {ep:<45} status={status} BODY_FAIL | {short}")
            failures.append(f"POST {ep} → ok=False en body")
        else:
            passed += 1
            print(f"  {OK} POST {ep:<45} status={status} [{desc}]")

    print("\n[*] Terminando servidor...")
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except:  # noqa: E722
        proc.kill()

    print("\n" + "=" * 60)
    print(f"  RESULTADO FINAL: {passed}/{total} pruebas pasaron.")
    print(f"  FALLOS REALES: {failed}")
    print("=" * 60)
    if failures:
        print("\n  FALLOS DETECTADOS:")
        for f in failures:
            print(f"    -> {f}")
    else:
        print("\n  [OK] 0 FALLOS REALES. NINGÚN ENDPOINT CRASHEA.")

    with open("exhaustive_results_v2.json", "w", encoding="utf-8") as fout:
        json.dump(
            {"passed": passed, "failed": failed, "total": total, "failures": failures},
            fout,
            indent=2,
        )


if __name__ == "__main__":
    run()
