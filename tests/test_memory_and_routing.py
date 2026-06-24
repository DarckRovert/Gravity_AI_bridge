import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Asegurar path de importación
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from providers.local.native_provider import NativeLlamaProvider
from core.provider_manager import _score_model, ProviderResult


class TestMemoryAndRouting(unittest.TestCase):

    def test_task_routing_scoring(self):
        # 1. Mock de ProviderResult
        r = ProviderResult(
            name="Native Llama",
            url="native://llama",
            protocol="llama.cpp",
            category="local",
        )
        r.is_healthy = True
        r.active_model = None

        # 2. Verificar scoring de Vision
        score_llava = _score_model(r, "llava-phi-3-mini-int4.gguf", "vision")
        score_nomic = _score_model(r, "nomic-embed-text-v1.5.f16.gguf", "vision")
        self.assertGreater(
            score_llava,
            score_nomic,
            "La tarea vision debe favorecer masivamente a llava sobre nomic",
        )

        # 3. Verificar scoring de Embedding
        score_nomic_embed = _score_model(
            r, "nomic-embed-text-v1.5.f16.gguf", "embedding"
        )
        score_llava_embed = _score_model(r, "llava-phi-3-mini-int4.gguf", "embedding")
        self.assertGreater(
            score_nomic_embed,
            score_llava_embed,
            "La tarea embedding debe favorecer masivamente a nomic sobre llava",
        )

        # 4. Verificar penalización de nomic en chats comunes
        score_nomic_chat = _score_model(r, "nomic-embed-text-v1.5.f16.gguf", "code")
        self.assertLess(
            score_nomic_chat,
            0.0,
            "Nomic debe estar penalizado severamente en chats comunes como code",
        )

        # 5. Verificar que code favorece a Qwen2.5-Coder
        score_qwen = _score_model(r, "Qwen2.5-Coder-7B-Instruct-Q5_K_M.gguf", "code")
        score_hermes = _score_model(r, "Hermes-3-Llama-3.1-8B-Q5_K_M.gguf", "code")
        self.assertGreater(
            score_qwen,
            score_hermes,
            "La tarea code debe favorecer a Qwen-Coder sobre Hermes",
        )

    @patch("psutil.virtual_memory")
    @patch("os.path.getsize")
    @patch("llama_cpp.Llama")
    def test_proactive_memory_eviction(
        self, mock_llama, mock_getsize, mock_virtual_memory
    ):
        # Configurar mocks
        mock_getsize.return_value = 5 * 1024 * 1024 * 1024  # 5 GB de modelo

        # Simular RAM disponible muy baja (ej. 2 GB libres)
        mock_virtual_memory.return_value = MagicMock(
            available=2 * 1024 * 1024 * 1024, percent=90.0
        )

        provider = NativeLlamaProvider()

        # Simulamos que tenemos un modelo inactivo cargado
        provider._instances["old_model.gguf"] = {
            "instance": MagicMock(),
            "last_used": 10.0,
        }

        # Intentamos cargar un nuevo modelo "new_model.gguf"
        # Con 2 GB libres y un modelo de 5 GB requerido (+1 GB buffer = 6 GB necesarios),
        # debe gatillarse la liberación proactiva de old_model.gguf
        with patch("os.path.exists", return_value=True):
            provider._load_model("new_model.gguf", {"num_ctx": 4096})

        # Verificar que old_model.gguf fue desalojado
        self.assertNotIn(
            "old_model.gguf",
            provider._instances,
            "El modelo antiguo debió ser desalojado para liberar RAM",
        )
        self.assertIn(
            "new_model.gguf", provider._instances, "El nuevo modelo debió ser cargado"
        )


if __name__ == "__main__":
    unittest.main()
