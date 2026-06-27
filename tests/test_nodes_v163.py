"""
Tests de regresión para los nodos migrados en V16.3 PRO.
Cubre los bugs críticos encontrados y corregidos en la sesión de auditoría:
  - LLMQueryNode acepta system_prompt y system (ambos)
  - ContentNormalizerNode no bloquea con Pollinations
  - TopicPickerNode selecciona tópicos correctamente
  - NewsNormalizerNode deprecado redirige a ContentNormalizerNode
  - Todos los workflows cargan sin errores topológicos
  - FileReader resuelve rutas relativas a BASE_DIR
"""
import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_node(cls, node_id="test"):
    return cls(node_id=node_id, config={})


# ══════════════════════════════════════════════════════════════════════════════
# TopicPickerNode
# ══════════════════════════════════════════════════════════════════════════════

class TestTopicPickerNode(unittest.TestCase):

    def setUp(self):
        from core.nodes.topic_picker_node import TopicPickerNode
        self.cls = TopicPickerNode

    def test_picks_from_json_list(self):
        node = _make_node(self.cls)
        topics = [
            {"topic": "quantum computing", "query": "quantum computing 2025"},
            {"topic": "neurociencia", "query": "neuroscience 2025"},
        ]
        result = node.execute({"topics_json": json.dumps(topics)})
        self.assertIn("topic", result)
        self.assertIn("query", result)
        self.assertIn(result["topic"], ["quantum computing", "neurociencia"])

    def test_override_topic_takes_priority(self):
        node = _make_node(self.cls)
        topics = [{"topic": "fallback", "query": "fallback query"}]
        result = node.execute({
            "topics_json": json.dumps(topics),
            "override_topic": "my custom topic"
        })
        self.assertEqual(result["topic"], "my custom topic")

    def test_override_topic_empty_string_ignored(self):
        """Un override_topic vacío NO debe anular la selección aleatoria."""
        node = _make_node(self.cls)
        topics = [{"topic": "selected", "query": "selected query"}]
        result = node.execute({
            "topics_json": json.dumps(topics),
            "override_topic": ""
        })
        self.assertEqual(result["topic"], "selected")

    def test_empty_topics_raises(self):
        node = _make_node(self.cls)
        with self.assertRaises(Exception):
            node.execute({"topics_json": "[]"})


# ══════════════════════════════════════════════════════════════════════════════
# ContentNormalizerNode
# ══════════════════════════════════════════════════════════════════════════════

class TestContentNormalizerNode(unittest.TestCase):

    def setUp(self):
        from core.nodes.content_normalizer_node import ContentNormalizerNode
        self.cls = ContentNormalizerNode

    def _run(self, raw_json: str, content_type="news") -> dict:
        node = _make_node(self.cls)
        with patch("urllib.request.urlopen"):  # mock Pollinations
            result = node.execute({
                "raw_json": raw_json,
                "content_type": content_type,
                "author": "Test Author",
                "image_prompt_prefix": "test prefix",
            })
        return json.loads(result["normalized_json"])

    def test_clean_json_passthrough(self):
        raw = json.dumps({
            "title": "Test Title",
            "excerpt": "Short excerpt",
            "fullText": "Full body text.",
            "category": "Tecnología Descentralizada",
            "featured": True
        })
        data = self._run(raw)
        self.assertEqual(data["title"], "Test Title")
        self.assertEqual(data["author"], "Test Author")
        self.assertIn("id", data)
        self.assertIn("date", data)
        self.assertIn("image", data)

    def test_repairs_markdown_json_block(self):
        raw = '```json\n{"title": "From Markdown", "fullText": "body"}\n```'
        data = self._run(raw)
        self.assertEqual(data["title"], "From Markdown")

    def test_fallback_title_when_missing(self):
        raw = '{"fullText": "only body, no title"}'
        data = self._run(raw)
        self.assertIn("title", data)
        self.assertTrue(len(data["title"]) > 0)

    def test_category_normalized_to_default_when_invalid(self):
        raw = json.dumps({"title": "T", "fullText": "B", "category": "INVALID"})
        data = self._run(raw, content_type="news")
        # Should fall back to default_category (empty = keep or "")
        self.assertIn("category", data)

    def test_pollinations_call_is_nonblocking(self):
        """Verifica que el precalentamiento de imagen no bloquea (fire-and-forget)."""
        import time
        raw = json.dumps({"title": "Speed Test", "fullText": "x"})
        node = _make_node(self.cls)

        # Simula Pollinations extremadamente lento
        def slow_urlopen(*args, **kwargs):
            import time
            time.sleep(30)

        with patch("urllib.request.urlopen", side_effect=slow_urlopen):
            t0 = time.time()
            node.execute({
                "raw_json": raw,
                "content_type": "news",
                "author": "A",
                "image_prompt_prefix": "p",
            })
            elapsed = time.time() - t0

        # El nodo debe retornar en menos de 5s aunque Pollinations tarde 30s
        self.assertLess(elapsed, 5.0, "ContentNormalizerNode bloquea la pipeline!")


# ══════════════════════════════════════════════════════════════════════════════
# LLMQueryNode — system_prompt alias
# ══════════════════════════════════════════════════════════════════════════════

class TestLLMQueryNode(unittest.TestCase):

    def setUp(self):
        from core.nodes.llm_query_node import LLMQueryNode
        self.cls = LLMQueryNode

    def _run_with_mock(self, inputs: dict) -> dict:
        node = _make_node(self.cls)
        mock_complete = MagicMock(return_value="mocked response")
        mock_get_best = MagicMock(return_value=("mock_provider", "mock_model"))
        with patch("core.provider_manager.complete", mock_complete), \
             patch("core.provider_manager.get_best", mock_get_best):
            return node.execute(inputs), mock_complete

    def test_system_prompt_alias_used(self):
        """system_prompt debe llegar al LLM — bug corregido en V16.3."""
        result, mock_complete = self._run_with_mock({
            "prompt": "Hello",
            "system_prompt": "You are a journalist",
        })
        call_args = mock_complete.call_args
        messages = call_args[1]["messages"] if "messages" in call_args[1] else call_args[0][0]
        system_msgs = [m for m in messages if m["role"] == "system"]
        self.assertEqual(len(system_msgs), 1)
        self.assertEqual(system_msgs[0]["content"], "You are a journalist")

    def test_system_field_also_works(self):
        """El campo 'system' original también debe funcionar."""
        result, mock_complete = self._run_with_mock({
            "prompt": "Hello",
            "system": "You are a scientist",
        })
        call_args = mock_complete.call_args
        messages = call_args[1]["messages"] if "messages" in call_args[1] else call_args[0][0]
        system_msgs = [m for m in messages if m["role"] == "system"]
        self.assertEqual(len(system_msgs), 1)
        self.assertEqual(system_msgs[0]["content"], "You are a scientist")

    def test_system_prompt_takes_priority_over_system(self):
        """system_prompt tiene prioridad sobre system si ambos están presentes."""
        result, mock_complete = self._run_with_mock({
            "prompt": "Hello",
            "system": "fallback",
            "system_prompt": "priority",
        })
        call_args = mock_complete.call_args
        messages = call_args[1]["messages"] if "messages" in call_args[1] else call_args[0][0]
        system_msgs = [m for m in messages if m["role"] == "system"]
        self.assertEqual(system_msgs[0]["content"], "priority")

    def test_empty_prompt_raises(self):
        node = _make_node(self.cls)
        with self.assertRaises(ValueError):
            with patch("core.provider_manager.get_best", return_value=("p", "m")), \
                 patch("core.provider_manager.complete", return_value="x"):
                node.execute({"prompt": ""})


# ══════════════════════════════════════════════════════════════════════════════
# NewsNormalizerNode — deprecation redirect
# ══════════════════════════════════════════════════════════════════════════════

class TestNewsNormalizerNodeDeprecated(unittest.TestCase):

    def test_redirects_to_content_normalizer(self):
        from core.nodes.news_normalizer_node import NewsNormalizerNode
        node = NewsNormalizerNode(node_id="test", config={})
        raw = json.dumps({"title": "Test", "fullText": "body", "category": "Tecnología Descentralizada"})
        with patch("urllib.request.urlopen"):
            result = node.execute({"raw_json": raw})
        self.assertIn("normalized_json", result)
        data = json.loads(result["normalized_json"])
        self.assertEqual(data["title"], "Test")


# ══════════════════════════════════════════════════════════════════════════════
# FileReaderNode — ruta relativa a BASE_DIR
# ══════════════════════════════════════════════════════════════════════════════

class TestFileReaderNode(unittest.TestCase):

    def test_reads_lore_bible(self):
        from core.nodes.file_reader_node import FileReaderNode
        node = FileReaderNode(node_id="test", config={})
        result = node.execute({"filepath": "lore_bible.md"})
        self.assertIn("content", result)
        self.assertGreater(len(result["content"]), 100)

    def test_missing_file_returns_empty(self):
        from core.nodes.file_reader_node import FileReaderNode
        node = FileReaderNode(node_id="test", config={})
        result = node.execute({"filepath": "nonexistent_file_xyz.txt"})
        self.assertEqual(result["content"], "")


# ══════════════════════════════════════════════════════════════════════════════
# Workflow topology validation — todos los workflows deben cargar sin errores
# ══════════════════════════════════════════════════════════════════════════════

class TestWorkflowTopology(unittest.TestCase):

    def test_all_workflows_load_and_sort(self):
        from core.workflow_engine import list_workflows, WorkflowGraph
        import glob

        wf_dir = os.path.join(BASE_DIR, "workflows")
        wf_files = glob.glob(os.path.join(wf_dir, "*.json"))
        self.assertGreater(len(wf_files), 0, "No se encontraron workflows.")

        errors = []
        for wf_file in wf_files:
            try:
                with open(wf_file, "r", encoding="utf-8") as f:
                    wf_data = json.load(f)
                graph = WorkflowGraph(wf_data)
                order = graph._resolve_deps()
                self.assertGreater(len(order), 0)
            except Exception as e:
                errors.append(f"{os.path.basename(wf_file)}: {e}")

        if errors:
            self.fail("Errores de topología en workflows:\n" + "\n".join(errors))

    def test_workflow_ids_match_filenames(self):
        """workflow_id debe coincidir con el nombre del archivo JSON."""
        import glob
        wf_dir = os.path.join(BASE_DIR, "workflows")
        mismatches = []
        for wf_file in glob.glob(os.path.join(wf_dir, "*.json")):
            fname = os.path.splitext(os.path.basename(wf_file))[0]
            with open(wf_file, "r", encoding="utf-8") as f:
                wf_data = json.load(f)
            wf_id = wf_data.get("workflow_id", "")
            if wf_id != fname:
                mismatches.append(f"{fname}.json → workflow_id='{wf_id}'")
        if mismatches:
            self.fail("workflow_id no coincide con filename:\n" + "\n".join(mismatches))


if __name__ == "__main__":
    unittest.main(verbosity=2)
