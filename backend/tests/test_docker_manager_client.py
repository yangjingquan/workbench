import httpx
import pytest

from app.core.config import settings
from app.services.docker_manager import DockerManagerClient, DockerManagerRemoteError, DockerManagerUnavailable


class FakeResponse:
    def __init__(self, status_code, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload
        self.text = text
        self.is_error = status_code >= 400

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload

    def iter_lines(self):
        return iter(["data: {\"message\": \"ok\"}", ""])


def test_client_sends_internal_token_and_returns_json(monkeypatch):
    seen = {}

    def fake_request(method, url, **kwargs):
        seen.update(method=method, url=url, headers=kwargs["headers"])
        return FakeResponse(200, {"containers": []})

    monkeypatch.setattr(settings, "docker_manager_token", "test-token")
    monkeypatch.setattr(httpx, "request", fake_request)
    result = DockerManagerClient().request("GET", "/internal/v1/containers")

    assert result == {"containers": []}
    assert seen["url"].endswith("/internal/v1/containers")
    assert seen["headers"]["X-Docker-Manager-Token"] == "test-token"
    assert seen["headers"]["X-Request-ID"]


def test_client_maps_connection_failure_to_unavailable(monkeypatch):
    def fail(*args, **kwargs):
        raise httpx.ConnectError("agent offline")

    monkeypatch.setattr(httpx, "request", fail)
    with pytest.raises(DockerManagerUnavailable):
        DockerManagerClient().request("GET", "/internal/v1/overview")


def test_client_maps_remote_error(monkeypatch):
    monkeypatch.setattr(httpx, "request", lambda *args, **kwargs: FakeResponse(404, {"detail": "容器不存在"}))

    with pytest.raises(DockerManagerRemoteError) as error:
        DockerManagerClient().request("GET", "/internal/v1/containers/missing")

    assert error.value.status_code == 404
    assert str(error.value) == "容器不存在"


def test_client_forwards_sse_lines(monkeypatch):
    class FakeStream:
        def __enter__(self): return FakeResponse(200, {})
        def __exit__(self, *args): return False

    monkeypatch.setattr(httpx, "stream", lambda *args, **kwargs: FakeStream())
    with DockerManagerClient(token="test-token").stream_logs("abc") as lines:
        assert list(lines) == ['data: {"message": "ok"}', ""]
