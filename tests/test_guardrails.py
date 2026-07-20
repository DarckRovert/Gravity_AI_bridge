import unittest
from core.guardrails import evaluate_pre_llm_guardrails


class TestGuardrails(unittest.TestCase):
    def test_stop_command(self):
        match = evaluate_pre_llm_guardrails("alto")
        self.assertTrue(match.matched)
        self.assertEqual(match.action, "stop")

    def test_reset_command(self):
        match = evaluate_pre_llm_guardrails("limpiar contexto")
        self.assertTrue(match.matched)
        self.assertEqual(match.action, "reset")

    def test_handoff_command(self):
        match = evaluate_pre_llm_guardrails("Quiero hablar con un asesor humano por favor")
        self.assertTrue(match.matched)
        self.assertEqual(match.action, "handoff")

    def test_normal_text(self):
        match = evaluate_pre_llm_guardrails("¿Cómo configuro el servidor de videos?")
        self.assertFalse(match.matched)
        self.assertEqual(match.action, "none")


if __name__ == "__main__":
    unittest.main()
