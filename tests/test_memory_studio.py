"""
Tests unitarios para Knowledge Graph en core.strategic_memory y el endpoint /v1/memory/graph.
"""

import io
import json

from api.routes.mixin_get import GetRoutesMixin
from api.routes.mixin_tiktok import TikTokMixin
from core.strategic_memory import get_knowledge_graph


class DummyGetHandler(GetRoutesMixin, TikTokMixin):
    def __init__(self, path: str):
        self.path = path
        self.wfile = io.BytesIO()
        self.status_code = None
        self.response_headers = {}

    def send_response(self, code: int):
        self.status_code = code

    def send_header(self, key: str, value: str):
        self.response_headers[key] = value

    def end_headers(self):
        pass

    def _send_cors(self):
        pass

    def _check_rate(self) -> bool:
        return True


def test_get_knowledge_graph_structure():
    graph = get_knowledge_graph()
    assert isinstance(graph, dict)
    assert "nodes_count" in graph
    assert "edges_count" in graph
    assert "most_central_nodes" in graph
    assert "nodes" in graph
    assert "edges" in graph
    assert isinstance(graph["nodes"], list)
    assert isinstance(graph["edges"], list)

    if graph["nodes"]:
        first_node = graph["nodes"][0]
        assert "id" in first_node
        assert "label" in first_node
        assert "type" in first_node
        assert "score" in first_node


def test_endpoint_memory_graph():
    handler = DummyGetHandler("/v1/memory/graph")
    handler.do_GET()

    assert handler.status_code == 200
    assert handler.response_headers.get("Content-Type") == "application/json"
    data = json.loads(handler.wfile.getvalue().decode("utf-8"))
    assert "nodes_count" in data
    assert "nodes" in data
    assert "edges" in data
    assert "most_central_nodes" in data
