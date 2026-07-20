# -*- coding: utf-8 -*-
import unittest
import time
from unittest.mock import MagicMock, patch
from providers.base import ProviderResponse, ProviderPlugin, ProviderResult
from core import provider_manager
from providers.cloud._openai_compat_cloud import OpenAICompatCloudProvider

class TestProvidersAudit(unittest.TestCase):

    def test_provider_response_dataclass(self):
        # Ok response
        r = ProviderResponse(ok=True, text="Respuesta exitosa")
        self.assertTrue(r.ok)
        self.assertTrue(bool(r))
        self.assertEqual(r.text, "Respuesta exitosa")
        self.assertEqual(r.error, "")

        # Error response
        r_err = ProviderResponse(ok=False, error="auth", detail="HTTP 401: Unauthorized")
        self.assertFalse(r_err.ok)
        self.assertFalse(bool(r_err))
        self.assertEqual(r_err.error, "auth")
        self.assertEqual(r_err.detail, "HTTP 401: Unauthorized")

    def test_complete_json_strategies(self):
        original_complete_safe = provider_manager.complete_safe

        try:
            # Estrategia 1: JSON Directo
            provider_manager.complete_safe = lambda *args, **kwargs: ProviderResponse(ok=True, text='{"status": "ok", "value": 100}')
            res = provider_manager.complete_json([], task="any")
            self.assertTrue(res["ok"])
            self.assertEqual(res["data"]["status"], "ok")
            self.assertEqual(res["data"]["value"], 100)

            # Estrategia 2: Markdown JSON codeblock
            provider_manager.complete_safe = lambda *args, **kwargs: ProviderResponse(ok=True, text='```json\n{"status": "markdown", "value": 200}\n```')
            res = provider_manager.complete_json([], task="any")
            self.assertTrue(res["ok"])
            self.assertEqual(res["data"]["status"], "markdown")
            self.assertEqual(res["data"]["value"], 200)

            # Estrategia 3: JSON embebido balanceado
            provider_manager.complete_safe = lambda *args, **kwargs: ProviderResponse(ok=True, text='Respuesta: {"status": "embedded", "value": 300} de prueba.')
            res = provider_manager.complete_json([], task="any")
            self.assertTrue(res["ok"])
            self.assertEqual(res["data"]["status"], "embedded")
            self.assertEqual(res["data"]["value"], 300)

        finally:
            provider_manager.complete_safe = original_complete_safe

    def test_cloud_provider_get_live_models_async(self):
        class DummyCloudProvider(OpenAICompatCloudProvider):
            name = "dummy"
            _base_url = "http://localhost:12345"
            _key_id = "dummy_key"
            _available_models = ["model-a", "model-b"]

        provider = DummyCloudProvider()
        
        t0 = time.time()
        models = provider._get_live_models()
        elapsed = time.time() - t0
        
        self.assertLess(elapsed, 1.0, "El probe inicial bloqueó el hilo principal")
        self.assertIn("model-a", models)
        self.assertIn("model-b", models)


if __name__ == "__main__":
    unittest.main()
