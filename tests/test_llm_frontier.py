import unittest
from pydantic import BaseModel, Field
from core.llm_frontier import chat_structured


class SampleResponse(BaseModel):
    summary: str = Field(description="Resumen de la respuesta")
    score: int = Field(description="Puntaje de 0 a 100")


class TestLLMFrontier(unittest.TestCase):
    def test_successful_validation(self):
        def mock_llm(messages):
            return '{"summary": "Excelente", "score": 95}'

        res = chat_structured(SampleResponse, mock_llm, [{"role": "user", "content": "hola"}])
        self.assertTrue(res.ok)
        self.assertEqual(res.data.summary, "Excelente")
        self.assertEqual(res.data.score, 95)
        self.assertEqual(res.attempts, 1)

    def test_auto_correction_after_bad_json(self):
        call_count = 0

        def mock_llm_flaky(messages):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return "Respuesta invalida sin json"
            return '```json\n{"summary": "Corregido", "score": 80}\n```'

        res = chat_structured(SampleResponse, mock_llm_flaky, [{"role": "user", "content": "hola"}])
        self.assertTrue(res.ok)
        self.assertEqual(res.data.summary, "Corregido")
        self.assertEqual(res.attempts, 2)

    def test_failure_after_max_attempts(self):
        def mock_llm_always_fail(messages):
            return "No json here"

        res = chat_structured(SampleResponse, mock_llm_always_fail, [{"role": "user", "content": "hola"}], max_attempts=2)
        self.assertFalse(res.ok)
        self.assertEqual(res.error, "validation_failed_after_retries")
        self.assertEqual(res.attempts, 2)


if __name__ == "__main__":
    unittest.main()
