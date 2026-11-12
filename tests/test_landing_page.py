"""
Tests unitarios para la Landing Page Oficial de Gravity AI Bridge V30.2 MYTHOS.
Verifica redirección canónica, servicio HTML, servicio de CSS/JS, 404 y protección Ring 0 contra Path Traversal.
"""

import threading
import urllib.request
import urllib.error
from http.server import ThreadingHTTPServer
import pytest
from bridge_server import GravityBridgeHandler


@pytest.fixture(scope="module")
def local_test_server():
    server = ThreadingHTTPServer(("127.0.0.1", 0), GravityBridgeHandler)
    port = server.server_port
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()


def test_landing_redirect(local_test_server):
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    opener = urllib.request.build_opener(NoRedirect)
    try:
        res = opener.open(f"{local_test_server}/landing")
        status = res.status
        headers = res.headers
    except urllib.error.HTTPError as e:
        status = e.code
        headers = e.headers

    assert status == 301
    assert headers.get("Location") == "/landing/"
    assert headers.get("Content-Length") == "0"


def test_landing_redirect_query_preserved(local_test_server):
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    opener = urllib.request.build_opener(NoRedirect)
    try:
        res = opener.open(f"{local_test_server}/landing?ref=github")
        status = res.status
        headers = res.headers
    except urllib.error.HTTPError as e:
        status = e.code
        headers = e.headers

    assert status == 301
    assert headers.get("Location") == "/landing/?ref=github"
    assert headers.get("Content-Length") == "0"


def test_landing_html(local_test_server):
    res = urllib.request.urlopen(f"{local_test_server}/landing/")
    assert res.status == 200
    assert "text/html" in res.headers.get("Content-Type", "")
    content = res.read().decode("utf-8")
    assert "Gravity AI Bridge V30.2" in content
    assert '<canvas id="gravity-bg"></canvas>' in content


def test_landing_css(local_test_server):
    res = urllib.request.urlopen(f"{local_test_server}/landing/style.css")
    assert res.status == 200
    assert "text/css" in res.headers.get("Content-Type", "")
    content = res.read().decode("utf-8")
    assert len(content) > 1000


def test_landing_js(local_test_server):
    res = urllib.request.urlopen(f"{local_test_server}/landing/script.js")
    assert res.status == 200
    assert ("javascript" in res.headers.get("Content-Type", ""))
    content = res.read().decode("utf-8")
    assert len(content) > 1000


def test_landing_404(local_test_server):
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(f"{local_test_server}/landing/inexistente_12345.xyz")
    assert exc_info.value.code == 404


def test_landing_path_traversal_403(local_test_server):
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(f"{local_test_server}/landing/..%2f..%2fconfig.yaml")
    assert exc_info.value.code == 403
