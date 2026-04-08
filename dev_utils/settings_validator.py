"""
╔══════════════════════════════════════════════════════════╗
║     GRAVITY AI SETTINGS VALIDATOR V6.0                   ║
║     Schema validation + auto-repair for _settings.json   ║
╚══════════════════════════════════════════════════════════╝
"""

# ── Top-level field schema ────────────────────────────────────────────────────
SCHEMA = {
    "provider":          {"type": str,   "max_len": 64,  "default": "ollama"},
    "api_url":           {"type": str,   "max_len": 256, "default": "http://localhost:11434"},
    "last_model":        {"type": str,   "max_len": 128, "default": "deepseek-r1:8b"},
    "mode":              {"type": str,   "max_len": 32,  "default": "auditor",
                          "allowed": ["auditor", "coder", "creativo", "revisor"]},
    "agent_language":    {"type": str,   "max_len": 8,   "default": "en"},
    "user_language":     {"type": str,   "max_len": 8,   "default": "es"},
    "bridge_port":       {"type": int,                   "default": 7860},
    "model_locked":      {"type": bool,                  "default": False},
    "locked_model":      {"type": str,   "max_len": 128, "default": ""},
    "provider_protocol": {"type": str,   "max_len": 32,  "default": "ollama"},
}

# ── advanced_params sub-schema ────────────────────────────────────────────────
ADVANCED_SCHEMA = {
    "num_ctx":           {"type": int,   "default": 131072, "min": 2048,  "max": 524288},
    "temperature":       {"type": float, "default": 0.6,    "min": 0.0,   "max": 2.0},
    "top_p":             {"type": float, "default": 0.9,    "min": 0.0,   "max": 1.0},
    "warning_threshold": {"type": float, "default": 0.85,   "min": 0.5,   "max": 0.99},
    "streaming":         {"type": bool,  "default": True},
    "auto_compress":     {"type": bool,  "default": True},
}


def validate_and_repair(data: dict) -> tuple:
    """
    Validates and auto-repairs a _settings.json data dict against the schema.

    Returns:
        (repaired_data, repairs_list)
        - repaired_data: the corrected dict (mutated in place and returned)
        - repairs_list:  list of human-readable repair descriptions
    """
    repairs = []

    # ── Top-level fields ──────────────────────────────────────────────────────
    for key, spec in SCHEMA.items():
        val = data.get(key)
        expected_type = spec["type"]
        default = spec["default"]

        if key not in data:
            data[key] = default
            repairs.append(f"Added missing field '{key}' = {default!r}")
            continue

        # bool check must come before int because isinstance(True, int) is True in Python
        if expected_type == bool:
            if not isinstance(val, bool):
                try:
                    data[key] = bool(val)
                except Exception:
                    data[key] = default
                repairs.append(f"Fixed type of '{key}' → {data[key]!r}")
            continue

        if not isinstance(val, expected_type):
            data[key] = default
            repairs.append(
                f"Fixed type of '{key}' (was {type(val).__name__}) → {default!r}"
            )
            continue

        # String max-length guard (catches corrupted fields like 'mode' with 10k chars)
        if expected_type == str and "max_len" in spec and len(val) > spec["max_len"]:
            preview = val[:40].replace("\n", " ")
            data[key] = default
            repairs.append(
                f"Repaired corrupted '{key}' (len={len(val)}, preview='{preview}...') "
                f"→ {default!r}"
            )
            continue

        # Allowed-values guard
        if "allowed" in spec and val not in spec["allowed"]:
            data[key] = default
            repairs.append(
                f"Fixed invalid value '{key}'={val!r} (not in {spec['allowed']}) → {default!r}"
            )

    # ── advanced_params ───────────────────────────────────────────────────────
    adv = data.get("advanced_params")

    if not isinstance(adv, dict):
        data["advanced_params"] = {k: v["default"] for k, v in ADVANCED_SCHEMA.items()}
        repairs.append("Replaced corrupted 'advanced_params' with full defaults")
    else:
        for key, spec in ADVANCED_SCHEMA.items():
            val = adv.get(key)
            expected_type = spec["type"]
            default = spec["default"]

            if val is None:
                adv[key] = default
                repairs.append(f"Added missing advanced_param '{key}' = {default!r}")
                continue

            # bool before int
            if expected_type == bool:
                if not isinstance(val, bool):
                    try:
                        adv[key] = bool(val)
                    except Exception:
                        adv[key] = default
                    repairs.append(f"Fixed type of advanced_param '{key}'")
                continue

            if not isinstance(val, expected_type):
                try:
                    adv[key] = expected_type(val)
                    repairs.append(
                        f"Coerced type of advanced_param '{key}' to {expected_type.__name__}"
                    )
                except Exception:
                    adv[key] = default
                    repairs.append(
                        f"Fixed type of advanced_param '{key}' → {default!r}"
                    )
                continue

            # Numeric range check
            if "min" in spec and isinstance(adv[key], (int, float)):
                if adv[key] < spec["min"]:
                    adv[key] = default
                    repairs.append(
                        f"Fixed out-of-range advanced_param '{key}' (below min {spec['min']}) "
                        f"→ {default!r}"
                    )
                elif adv[key] > spec["max"]:
                    adv[key] = default
                    repairs.append(
                        f"Fixed out-of-range advanced_param '{key}' (above max {spec['max']}) "
                        f"→ {default!r}"
                    )

        data["advanced_params"] = adv

    return data, repairs


if __name__ == "__main__":
    import json, os

    settings_path = os.path.join(os.path.dirname(__file__), "_settings.json")
    try:
        with open(settings_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading settings: {e}")
        data = {}

    repaired, repairs = validate_and_repair(data)

    if repairs:
        print(f"\n⚠  {len(repairs)} repair(s) made:")
        for r in repairs:
            print(f"  → {r}")
        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(repaired, f, indent=4, ensure_ascii=False)
        print("\n✓ Repaired settings saved.")
    else:
        print("\n✓ Settings schema is valid. No repairs needed.")
