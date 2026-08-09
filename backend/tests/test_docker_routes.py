from contextlib import contextmanager

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_current_user
from app.api.docker_routes import get_docker_manager_client
from app.db.session import Base, get_db
from app.main import app
from app.models import DockerOperationLog, User


class FakeAgent:
    def __init__(self):
        self.container = {"id": "abc", "name": "api-1", "state": "running", "health": "healthy"}
        self.service_result = {"project": "shop", "service": "api", "action": "restart", "items": []}
        self.requests = []

    def request(self, method, path, params=None, json=None):
        self.requests.append((method, path, params, json))
        if method == "GET" and path.endswith("/overview"):
            return {"engine": {"status": "online"}, "container_count": 1}
        if method == "GET" and path.endswith("/projects"):
            return {"projects": [{"name": "shop", "services": []}]}
        if method == "GET" and path.endswith("/containers"):
            return {"containers": [self.container]}
        if method == "GET" and "/containers/" in path:
            return self.container
        if method == "POST" and "/services/" in path:
            return self.service_result
        if method == "POST" and "/actions/" in path:
            return {"action": path.rsplit("/", 1)[-1], "changed": True, "container": self.container}
        raise AssertionError((method, path, params, json))

    @contextmanager
    def stream_logs(self, container_id, params=None):
        yield iter(["data: {\"message\": \"ok\"}", ""])


engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
Base.metadata.create_all(bind=engine)
db = TestingSession()
db.add(User(id=7, username="admin", password_hash="x", display_name="管理员"))
db.commit()
db.close()


def override_db():
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


def make_client(fake_agent):
    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = lambda: User(id=7, username="admin", password_hash="x", display_name="管理员")
    app.dependency_overrides[get_docker_manager_client] = lambda: fake_agent
    return TestClient(app)


def teardown_client():
    app.dependency_overrides.clear()
    session = TestingSession()
    session.query(DockerOperationLog).delete()
    session.commit()
    session.close()


def test_docker_overview_requires_login():
    response = TestClient(app).get("/api/docker/overview")
    assert response.status_code == 401


def test_remove_requires_exact_name_and_protected_container_cannot_be_removed():
    fake_agent = FakeAgent()
    fake_agent.container = {"id": "abc", "name": "workbench-api", "state": "running", "health": "healthy"}
    client = make_client(fake_agent)
    try:
        response = client.post("/api/docker/containers/abc/actions/remove", json={"confirm_name": "workbench-api"})
        assert response.status_code == 409
        assert "受保护" in response.json()["detail"]
        assert TestingSession().query(DockerOperationLog).count() == 1
    finally:
        teardown_client()


def test_remove_requires_exact_name():
    fake_agent = FakeAgent()
    fake_agent.container = {"id": "abc", "name": "temporary", "state": "exited"}
    client = make_client(fake_agent)
    try:
        response = client.post("/api/docker/containers/abc/actions/remove", json={"confirm_name": "wrong"})
        assert response.status_code == 400
        assert "准确" in response.json()["detail"]
    finally:
        teardown_client()


def test_service_action_returns_partial_results():
    fake_agent = FakeAgent()
    fake_agent.service_result = {
        "project": "shop",
        "service": "api",
        "action": "restart",
        "items": [{"name": "api-1", "result": "success"}, {"name": "api-2", "result": "failed", "error": "not found"}],
    }
    client = make_client(fake_agent)
    try:
        response = client.post("/api/docker/services/shop/api/actions/restart")
        assert response.status_code == 200
        assert response.json()["data"]["items"][1]["result"] == "failed"
        session = TestingSession()
        row = session.query(DockerOperationLog).order_by(DockerOperationLog.id.desc()).first()
        assert row.result == "partial"
        session.close()
    finally:
        teardown_client()


def test_log_stream_is_forwarded():
    client = make_client(FakeAgent())
    try:
        response = client.get("/api/docker/containers/abc/logs/stream")
        assert response.status_code == 200
        assert "data:" in response.text
    finally:
        teardown_client()


def test_logs_accept_empty_optional_timestamps_and_omit_them_for_agent():
    fake_agent = FakeAgent()
    client = make_client(fake_agent)
    try:
        response = client.get("/api/docker/containers/abc/logs?tail=200&since=&until=")
        assert response.status_code == 200
        assert fake_agent.requests[-1][2] == {"tail": 200}
    finally:
        teardown_client()
