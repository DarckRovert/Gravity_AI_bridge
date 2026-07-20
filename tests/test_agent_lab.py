import unittest
from core.agent_lab import run_laboratory_evaluation


class TestAgentLab(unittest.TestCase):
    def test_laboratory_eval(self):
        def mock_agent(prompt):
            if "asesor humano" in prompt:
                return "Entendido, te paso con un humano."
            return "Respuesta procesada correctamente."

        def mock_judge(messages):
            return '{"veredicto": "verde", "score": 90, "hallazgos": []}'

        report = run_laboratory_evaluation(mock_agent, mock_judge)
        self.assertGreater(report["global_score"], 0)
        self.assertEqual(report["cases_evaluated"], 3)
        self.assertEqual(len(report["results"]), 3)


if __name__ == "__main__":
    unittest.main()
