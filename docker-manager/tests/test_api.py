import json

import pytest
from fastapi.testclient import TestClient

from app.main import app, get_docker_service


class FakeService:
    def list_overview(self):
        return {"engine": {"status": "online"}, "container_count": 1, "running_count": 1, "stopped_count": 0, "abnormal_count": 0, "project_count": 1, "resources": {}}

    def list_projects(self):
        return [{"name": "shop", "services": []}]

    def list_containers(self, filters):
        return [{"id": "abc", "name": "api-1", "state": "running", "health": "healthy"}]

    def get_container(self, container_id):
        return {"id": container_id, "name": "api-1", "state": "running", "health": "healthy"}

    def get_logs(self, container_id, tail=200, since=None, until=None):
        return {"container_id": container_id, "lines": [{"timestamp": "2026-08-09T01:02:03Z", "stream": "stdout", "message": "ok"}]}

    def stream_logs(self, container_id, tail=200, since=None, until=None):
        yield {"timestamp": "2026-08-09T01:02:03Z", "stream": "stdout", "message": "ok"}

    def container_action(self, container_id, action):
        return {"action": action, "changed": True, "container": {"id": container_id, "state": "running"}}

    def service_action(self, project, service, action):
        return {"project": project, "service": service, "action": action, "items": []}


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setenv("DOCKER_MANAGER_TOKEN", "test-token")
    app.dependency_overrides[get_docker_service] = lambda: FakeService()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_agent_health_is_public(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["service"] == "docker-manager"


def test_agent_rejects_missing_token(client):
    response = client.get("/internal/v1/overview")
    assert response.status_code == 401


def test_agent_returns_container_list_with_valid_token(client):
    response = client.get("/internal/v1/containers", headers={"X-Docker-Manager-Token": "test-token"})
    assert response.status_code == 200
    assert response.json()["containers"][0]["name"] == "api-1"


def test_agent_rejects_invalid_tail(client):
    response = client.get("/internal/v1/containers/abc/logs?tail=0", headers={"X-Docker-Manager-Token": "test-token"})
    assert response.status_code == 422


def test_agent_stream_is_sse(client):
    with client.stream("GET", "/internal/v1/containers/abc/logs/stream", headers={"X-Docker-Manager-Token": "test-token"}) as response:
        body = "".join(response.iter_text())
        assert response.headers["content-type"].startswith("text/event-stream")
        assert json.loads(body.split("data: ", 1)[1].split("\n", 1)[0])["message"] == "ok"
