"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  GRAVITY V16.0 PRO — TEST SUITE: autonomy_engine                            ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestInvariantRules(unittest.TestCase):
    def test_rules_are_immutable_list(self):
        from core.autonomy_engine import get_invariant_rules, INVARIANT_RULES
        rules = get_invariant_rules()
        self.assertIsInstance(rules, list)
        self.assertGreater(len(rules), 0)
        # Modificar la copia devuelta NO debe afectar al original
        rules.append("fake rule")
        self.assertNotIn("fake rule", INVARIANT_RULES)

    def test_rules_contain_budget_constraint(self):
        from core.autonomy_engine import get_invariant_rules
        rules = get_invariant_rules()
        budget_rule = any("$0.50" in r or "budget" in r.lower() or "gastar" in r.lower() for r in rules)
        self.assertTrue(budget_rule, "Debe existir una regla de límite de presupuesto")

    def test_rules_contain_no_delete_core(self):
        from core.autonomy_engine import get_invariant_rules
        rules = get_invariant_rules()
        core_rule = any("core/" in r or "core\\" in r for r in rules)
        self.assertTrue(core_rule, "Debe existir una regla que proteja el directorio core/")


class TestBudgetControl(unittest.TestCase):
    def setUp(self):
        import core.autonomy_engine as ae
        # Reset budget para cada test
        ae._daily_spend = 0.0
        ae._daily_spend_date = ""

    def test_budget_available_when_zero_spend(self):
        from core.autonomy_engine import _check_budget
        self.assertTrue(_check_budget(0.01))

    def test_budget_exhausted_when_exceed_limit(self):
        import core.autonomy_engine as ae
        from datetime import datetime, timezone
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        ae._daily_spend = ae.AUTONOMY_DAILY_BUDGET_USD + 0.01
        ae._daily_spend_date = today  # Mismo día — no debe resetear
        from core.autonomy_engine import _check_budget
        self.assertFalse(_check_budget(0.01))


    def test_deduct_budget_accumulates(self):
        import core.autonomy_engine as ae
        ae._daily_spend = 0.0
        from core.autonomy_engine import _deduct_budget
        _deduct_budget(0.10)
        _deduct_budget(0.15)
        self.assertAlmostEqual(ae._daily_spend, 0.25, places=4)

    def test_budget_resets_on_new_day(self):
        import core.autonomy_engine as ae
        ae._daily_spend = 0.49
        ae._daily_spend_date = "2000-01-01"  # Fecha pasada
        from core.autonomy_engine import _check_budget
        # Debe resetear el contador porque la fecha cambió
        result = _check_budget(0.01)
        self.assertTrue(result)
        self.assertAlmostEqual(ae._daily_spend, 0.0, places=4)


class TestOrient(unittest.TestCase):
    def _make_snapshot(self, **overrides):
        base = {
            "security": {"critical": 0, "warnings": 0, "score": 100},
            "api_cost":  {"daily_usd": 0.0, "limit_usd": 5.0},
            "hardware":  {"ram_pct": 50.0, "disk_free_gb": 100.0},
            "scheduler": {"enabled": True},
            "reflection": {"patches_pending": 0, "issues_found": 0},
            "revenue":   {"monthly_proj_usd": 0.0},
        }
        base.update(overrides)
        return base

    def test_normal_state(self):
        from core.autonomy_engine import _orient
        level, alerts = _orient(self._make_snapshot())
        self.assertEqual(level, "NORMAL")
        self.assertEqual(len(alerts), 0)

    def test_critical_security_alert(self):
        from core.autonomy_engine import _orient
        snap = self._make_snapshot(security={"critical": 2, "warnings": 0, "score": 30})
        level, alerts = _orient(snap)
        self.assertEqual(level, "CRÍTICO")
        self.assertTrue(any("SEGURIDAD" in a for a in alerts))

    def test_high_ram_triggers_alert(self):
        from core.autonomy_engine import _orient
        snap = self._make_snapshot(hardware={"ram_pct": 95.0, "disk_free_gb": 100.0})
        level, alerts = _orient(snap)
        self.assertIn(level, ("ALERTA", "CRÍTICO"))
        self.assertTrue(any("RAM" in a for a in alerts))

    def test_low_disk_triggers_alert(self):
        from core.autonomy_engine import _orient
        snap = self._make_snapshot(hardware={"ram_pct": 50.0, "disk_free_gb": 2.0})
        level, alerts = _orient(snap)
        self.assertIn(level, ("ALERTA", "CRÍTICO"))
        self.assertTrue(any("disco" in a.lower() or "GB" in a for a in alerts))

    def test_scheduler_disabled_triggers_opportunity(self):
        from core.autonomy_engine import _orient
        snap = self._make_snapshot(scheduler={"enabled": False})
        level, alerts = _orient(snap)
        self.assertIn(level, ("OPORTUNIDAD", "ALERTA", "CRÍTICO"))
        self.assertTrue(any("scheduler" in a.lower() or "CONTENIDO" in a for a in alerts))

    def test_api_cost_near_limit_triggers_alert(self):
        from core.autonomy_engine import _orient
        snap = self._make_snapshot(api_cost={"daily_usd": 4.95, "limit_usd": 5.0})
        level, alerts = _orient(snap)
        self.assertIn(level, ("ALERTA", "CRÍTICO"))
        self.assertTrue(any("COSTO" in a for a in alerts))


class TestParseActions(unittest.TestCase):
    def test_parse_low_risk_action(self):
        from core.autonomy_engine import _parse_actions
        plan = """ANÁLISIS: Sistema estable.
ACCIONES:
1. [BAJA] [content_scheduler] — Agregar topic "finanzas personales" al niche tech
2. [ALTA] [config.yaml] — Cambiar proveedor a OpenRouter
JUSTIFICACIÓN: Optimización de contenido."""
        actions = _parse_actions(plan)
        self.assertEqual(len(actions), 2)
        self.assertEqual(actions[0]["risk"], "BAJA")
        self.assertEqual(actions[0]["module"], "content_scheduler")
        self.assertEqual(actions[1]["risk"], "ALTA")
        self.assertEqual(actions[1]["module"], "config.yaml")

    def test_parse_empty_plan(self):
        from core.autonomy_engine import _parse_actions
        actions = _parse_actions("ANÁLISIS: Sin acciones necesarias.\nJUSTIFICACIÓN: Todo OK.")
        self.assertEqual(actions, [])

    def test_parse_no_acciones_section(self):
        from core.autonomy_engine import _parse_actions
        actions = _parse_actions("Solo texto sin estructura.")
        self.assertEqual(actions, [])


class TestTriggerCycle(unittest.TestCase):
    def test_trigger_returns_ok_when_not_running(self):
        import core.autonomy_engine as ae
        ae._state["running"] = False
        from core.autonomy_engine import trigger_cycle
        result = trigger_cycle()
        self.assertTrue(result.get("ok"))

    def test_trigger_blocked_when_already_running(self):
        import core.autonomy_engine as ae
        ae._state["running"] = True
        from core.autonomy_engine import trigger_cycle
        result = trigger_cycle()
        self.assertFalse(result.get("ok"))
        self.assertIn("error", result)
        ae._state["running"] = False  # cleanup


class TestSecurityLayers(unittest.TestCase):
    """Verifica que las capas de seguridad del engine funcionan correctamente."""

    def test_invariant_rules_cannot_be_modified_through_public_api(self):
        """Las reglas invariantes son read-only desde la API pública."""
        from core.autonomy_engine import get_invariant_rules, INVARIANT_RULES
        original_count = len(INVARIANT_RULES)
        rules_copy = get_invariant_rules()
        rules_copy.clear()
        self.assertEqual(len(INVARIANT_RULES), original_count)

    def test_budget_check_respects_daily_limit(self):
        """El engine nunca gasta más del límite diario configurado."""
        import core.autonomy_engine as ae
        from datetime import datetime, timezone
        ae._daily_spend = ae.AUTONOMY_DAILY_BUDGET_USD  # Al límite exacto
        ae._daily_spend_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        from core.autonomy_engine import _check_budget
        self.assertFalse(_check_budget(0.001))  # Ni un centavo más


if __name__ == "__main__":
    unittest.main(verbosity=2)
