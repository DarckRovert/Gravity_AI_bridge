"""
╔══════════════════════════════════════════════════════════════╗
║     GRAVITY AI — BENCHMARK V7.1                              ║
║     Comparador de modelos: velocidad, calidad, costo        ║
╚══════════════════════════════════════════════════════════════╝
"""
import time
from core.provider_manager import get_plugin, scan_all

BENCHMARK_SUITE = {
    "speed": "Di solamente: 'Listo'",
    "code":  "Implementa en Python una función que calcule el n-ésimo número de Fibonacci usando memoización. Solo el código, sin explicación.",
    "reason":"Explica brevemente el problema del viajante de comercio (TSP) y cuál es su complejidad computacional.",
    "math":  "¿Cuántos ceros terminales tiene 100! (100 factorial)? Da solo el número.",
}


def run_benchmark(
    suite:      str | list[str] = "all",
    providers:  list[str] | None = None,
) -> list[dict]:
    """
    Runs benchmark suite against all available providers/models.
    Returns list of result dicts.
    suite: "all" | "speed" | "code" | "reason" | "math" | list of those
    """
    if suite == "all":
        tasks = list(BENCHMARK_SUITE.items())
    elif isinstance(suite, str):
        tasks = [(suite, BENCHMARK_SUITE.get(suite, suite))]
    else:
        tasks = [(s, BENCHMARK_SUITE.get(s, s)) for s in suite]

    results   = scan_all(force=True)
    available = [r for r in results if r.is_healthy and r.models]
    if providers:
        available = [r for r in available if r.name in providers]

    benchmark_results = []

    for r in available:
        plugin = get_plugin(r.name)
        if not plugin:
            continue
        model = r.active_model or r.models[0]["name"]

        for task_name, prompt in tasks:
            messages = [{"role": "user", "content": prompt}]
            t0       = time.time()
            ttft     = None
            chars    = 0
            error    = None
            try:
                for i, chunk in enumerate(plugin.chat_stream(messages, model, {})):
                    if i == 0:
                        ttft = round((time.time() - t0) * 1000)  # ms to first token
                    chars += len(chunk)
            except Exception as e:
                error = str(e)

            elapsed = round(time.time() - t0, 2)
            tps     = round(chars / 4 / elapsed, 1) if elapsed > 0 else 0  # rough tok/s

            benchmark_results.append({
                "provider": r.name,
                "model":    model,
                "task":     task_name,
                "ttft_ms":  ttft or 0,
                "tok_s":    tps,
                "elapsed_s": elapsed,
                "chars":    chars,
                "error":    error,
            })

    return benchmark_results


def format_results(results: list[dict]) -> str:
    """Formats benchmark results as a Markdown table."""
    if not results:
        return "Sin resultados."

    lines = ["| Provider | Model | Task | TTFT | tok/s | Time | Status |",
             "|---|---|---|---|---|---|---|"]
    for r in sorted(results, key=lambda x: (x["task"], x["tok_s"]), reverse=False):
        status = "✅" if not r["error"] else "❌"
        lines.append(
            f"| {r['provider']} | {r['model'][:30]} | {r['task']} "
            f"| {r['ttft_ms']}ms | {r['tok_s']} | {r['elapsed_s']}s | {status} |"
        )
    return "\n".join(lines)
