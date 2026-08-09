import pytest

from app.schemas import DockerActionError
from app.service import DockerService


class FakeContainer:
    def __init__(self, id, name, status="running", labels=None, attrs=None, log_chunks=None):
        self.id = id
        self.name = name
        self.status = status
        self.labels = labels or {}
        self.attrs = attrs or {}
        self.log_chunks = log_chunks or []
        self.actions = []

    def start(self): self.actions.append("start")
    def stop(self): self.actions.append("stop")
    def restart(self): self.actions.append("restart")
    def pause(self): self.actions.append("pause")
    def unpause(self): self.actions.append("unpause")
    def kill(self): self.actions.append("kill")
    def remove(self): self.actions.append("remove")
    def stats(self, stream=False): return {}
    def logs(self, **kwargs): return self.log_chunks


class FakeContainers:
    def __init__(self, containers): self.items = containers
    def list(self, all=True): return self.items
    def get(self, container_id): return next(item for item in self.items if item.id == container_id)


class FakeDockerClient:
    def __init__(self, containers):
        self.containers = FakeContainers(containers)

    def version(self): return {"Version": "27.0.0"}


def test_container_summary_maps_compose_labels_and_health():
    container = FakeContainer(
        id="abc123",
        name="api-1",
        status="running",
        labels={"com.docker.compose.project": "shop", "com.docker.compose.service": "api"},
        attrs={
            "State": {"Status": "running", "StartedAt": "2026-08-09T01:02:03Z", "Health": {"Status": "healthy"}},
            "Config": {"Image": "shop-api:latest"},
            "HostConfig": {"RestartCount": 2},
        },
    )

    result = DockerService(FakeDockerClient([container])).get_container("abc123")

    assert result["name"] == "api-1"
    assert result["project"] == "shop"
    assert result["service"] == "api"
    assert result["state"] == "running"
    assert result["health"] == "healthy"
    assert result["restart_count"] == 2


def test_action_allowlist_rejects_unknown_action():
    with pytest.raises(DockerActionError, match="不支持的 Docker 操作"):
        DockerService(FakeDockerClient([])).container_action("abc123", "exec")


def test_service_action_groups_exact_compose_labels_and_returns_each_result():
    api = FakeContainer("api-1", "api-1", labels={"com.docker.compose.project": "shop", "com.docker.compose.service": "api"})
    worker = FakeContainer("worker-1", "worker-1", labels={"com.docker.compose.project": "shop", "com.docker.compose.service": "worker"})

    result = DockerService(FakeDockerClient([api, worker])).service_action("shop", "api", "restart")

    assert [item["name"] for item in result["items"]] == ["api-1"]
    assert api.actions == ["restart"]
    assert worker.actions == []


def test_logs_preserve_stream_and_strip_timestamp():
    container = FakeContainer("abc", "api-1", log_chunks=[(b"2026-08-09T01:02:03Z hello\n", None), (None, b"2026-08-09T01:02:04Z error\n")])

    result = DockerService(FakeDockerClient([container])).get_logs("abc")

    assert result["lines"] == [
        {"timestamp": "2026-08-09T01:02:03Z", "stream": "stdout", "message": "hello"},
        {"timestamp": "2026-08-09T01:02:04Z", "stream": "stderr", "message": "error"},
    ]
