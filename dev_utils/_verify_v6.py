"""Gravity AI V6.0 — verification tests (no external deps beyond stdlib)."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

errors = []

# ── BUG-02: SettingsManager.heal() no lanza NameError ─────────────────────────
try:
    from ask_deepseek import SettingsManager
    s = SettingsManager()
    result = s.heal()
    assert isinstance(result, dict), "heal() debe retornar dict"
    print("[OK] BUG-02: SettingsManager.heal() sin NameError")
except Exception as e:
    errors.append(f"BUG-02 FAIL: {e}")
    print(f"[ERR] BUG-02: {e}")

# ── BUG-01: mode no contiene código corrupto ──────────────────────────────────
try:
    mode = s.data["mode"]
    assert len(mode) < 50, f"mode corrupto: {len(mode)} chars"
    print(f"[OK] BUG-01: mode = {mode!r} ({len(mode)} chars)")
except Exception as e:
    errors.append(f"BUG-01 FAIL: {e}")
    print(f"[ERR] BUG-01: {e}")

# ── BUG-03: warning_threshold = 0.85 ─────────────────────────────────────────
try:
    wt = s.data["advanced_params"]["warning_threshold"]
    assert wt == 0.85, f"esperado 0.85, got {wt}"
    print(f"[OK] BUG-03: warning_threshold = {wt}")
except Exception as e:
    errors.append(f"BUG-03 FAIL: {e}")
    print(f"[ERR] BUG-03: {e}")

# ── FEAT-11: model_locked fields exist and work ────────────────────────────────
try:
    assert "model_locked" in s.data
    assert "locked_model" in s.data
    s.lock_model("test-model:7b")
    assert s.data["model_locked"] == True
    assert s.data["locked_model"] == "test-model:7b"
    s.unlock_model()
    assert s.data["model_locked"] == False
    assert s.data["locked_model"] == ""
    print("[OK] FEAT-11: lock_model / unlock_model correctos")
except Exception as e:
    errors.append(f"FEAT-11 FAIL: {e}")
    print(f"[ERR] FEAT-11: {e}")

# ── BUG-07: model_selector tarea 'any' no fuerza switch ───────────────────────
try:
    import model_selector
    model_selector.set_active_model("deepseek-r1:32b")
    m, did = model_selector.get_optimal_model(
        text="hola como estas",
        protocol="ollama",
        provider_name="Ollama",
        available_models=["deepseek-r1:32b", "qwen2.5-coder:14b"],
    )
    assert not did, f"switch inesperado en tarea 'any': {m}"
    print(f"[OK] BUG-07: tarea 'any' no fuerza switch (modelo={m})")
except Exception as e:
    errors.append(f"BUG-07 FAIL: {e}")
    print(f"[ERR] BUG-07: {e}")

# ── BUG-06: deduplicacion en model_selector cache ─────────────────────────────
try:
    import model_selector as ms
    ms._available_models_cache = {}
    ms.update_available_models("LM Studio", ["model-a", "model-b"])
    ms.update_available_models("LM Studio", ["model-b", "model-c"])
    cache = ms._available_models_cache["LM Studio"]
    assert len(cache) == len(set(cache)), f"Duplicados: {cache}"
    assert "model-b" in cache
    print(f"[OK] BUG-06: deduplicacion en cache OK ({cache})")
except Exception as e:
    errors.append(f"BUG-06 FAIL: {e}")
    print(f"[ERR] BUG-06: {e}")

# ── FEAT-15: knowledge con timestamps ─────────────────────────────────────────
try:
    from ask_deepseek import MemoryManager
    mm = MemoryManager()
    count_before = len(mm.knowledge)
    added = mm.learn("Test rule for V6.0 verification")
    if added:
        last = mm.knowledge[-1]
        assert isinstance(last, dict), "regla debe ser dict"
        assert "rule"   in last
        assert "added"  in last
        assert "source" in last
        print(f"[OK] FEAT-15: knowledge con formato dict: {last}")
        mm.forget_rule(len(mm.knowledge) - 1)  # cleanup
    else:
        print("[OK] FEAT-15: regla ya existia (skip)")
except Exception as e:
    errors.append(f"FEAT-15 FAIL: {e}")
    print(f"[ERR] FEAT-15: {e}")

# ── BUG-12: estimacion adaptativa de tokens ───────────────────────────────────
try:
    mm2 = MemoryManager()
    mm2.history = [{"role": "user", "content": "```python\ndef foo(): pass\n```"}]
    est_code = mm2.get_estimated_tokens("system")
    mm2.history = [{"role": "user", "content": "hola como estas que tal todo bien"}]
    est_text = mm2.get_estimated_tokens("system")
    # Smaller divisor (3.0 for code) → MORE estimated tokens for same char count → correct
    assert est_code > est_text, f"code({est_code}) debe ser > text({est_text}) para mismo len"
    print(f"[OK] BUG-12: tokens adaptativos code={est_code} > text={est_text} (divisor 3 vs 4)")
except Exception as e:
    errors.append(f"BUG-12 FAIL: {e}")
    print(f"[ERR] BUG-12: {e}")

# ── settings_validator: detecta corrupcion ────────────────────────────────────
try:
    from settings_validator import validate_and_repair
    corrupted = {"mode": "A" * 5000, "advanced_params": {}}
    repaired, repairs = validate_and_repair(corrupted)
    assert repaired["mode"] == "auditor"
    assert any("mode" in r for r in repairs)
    print(f"[OK] FEAT-01: settings_validator repara corrupcion ({len(repairs)} reparaciones)")
except Exception as e:
    errors.append(f"FEAT-01 FAIL: {e}")
    print(f"[ERR] FEAT-01: {e}")

print()
if errors:
    print(f"RESULTADO: {len(errors)} test(s) fallaron:")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
else:
    print(f"RESULTADO: Todos los tests pasaron. [V6.0 verificado]")
    sys.exit(0)
