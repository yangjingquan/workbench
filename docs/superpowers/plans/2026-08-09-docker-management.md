# Docker Service Management Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a single-server Docker management console to Workbench with live container/service status, logs, lifecycle actions, and audited mutations.

**Architecture:** A new `docker-manager` FastAPI service is the only container that mounts `/var/run/docker.sock`. The existing Workbench FastAPI authenticates the administrator, validates actions, proxies requests to the Agent over `workbench-internal`, and records mutations in MySQL. The Vue page consumes only Workbench API routes and uses an authenticated fetch stream for live logs.

**Tech Stack:** Python 3.12, FastAPI 0.115.6, Docker SDK for Python, httpx, SQLAlchemy 2, MySQL 8, Vue 3, Element Plus, Axios, Vite, Docker Compose.

## Global Constraints

- Manage exactly one Docker Engine on the existing server; do not introduce multi-host configuration.
- `docker-manager` is the only service that mounts `/var/run/docker.sock`.
- The Agent has no published host port and accepts only the shared internal token.
- Browser code never receives the Agent URL or Agent token.
- Supported container actions are exactly `start`, `stop`, `restart`, `pause`, `unpause`, `kill`, and `remove`.
- Supported Compose service actions are `start`, `stop`, and `restart`, executed against the containers matching the project/service labels.
- Protected containers can be viewed, logged, started, stopped, and restarted, but cannot be removed through the UI.
- Do not expose arbitrary host shell commands or arbitrary `docker exec`.
- Container inventory and Docker logs are live data; only control operations are persisted.
- Destructive actions require a second confirmation and exact container-name entry in the Workbench API request.
- Existing Workbench API, web, MySQL container, networks, volumes, and business data must remain compatible.

## File Map

### Docker Agent

- Create `docker-manager/requirements.txt`: pinned runtime and test dependencies for the isolated Agent.
- Create `docker-manager/Dockerfile`: build the Agent image without exposing a host port.
- Create `docker-manager/app/schemas.py`: normalized Agent response models and action constants.
- Create `docker-manager/app/service.py`: Docker SDK discovery, status mapping, log reading, and lifecycle operations.
- Create `docker-manager/app/main.py`: internal-token-protected Agent HTTP routes and SSE log streaming.
- Create `docker-manager/tests/test_service.py`: Docker SDK behavior tests using fakes.
- Create `docker-manager/tests/test_api.py`: token, endpoint, action, and stream contract tests.

### Workbench Backend

- Modify `backend/app/core/config.py`: Agent URL, token, timeout, and protected-container settings.
- Create `backend/app/services/__init__.py`: backend service package marker.
- Create `backend/app/services/docker_manager.py`: synchronous HTTP client for Agent requests and log streams.
- Modify `backend/app/models/models.py`: `DockerOperationLog` SQLAlchemy model.
- Modify `backend/app/models/__init__.py`: export the audit model.
- Modify `backend/app/api/docker_routes.py`: authenticated Docker API proxy routes, confirmation, action validation, and audit writes.
- Modify `backend/app/main.py`: include the Docker router.
- Modify `backend/sql/init.sql`: explicit idempotent audit-table DDL.
- Create `backend/tests/test_docker_manager_client.py`: Agent client request/stream/error tests.
- Create `backend/tests/test_docker_routes.py`: auth, confirmation, protection, proxy, batch result, and audit tests.
- Create `backend/tests/test_docker_compose_contract.py`: Compose security and socket-boundary contract tests.
- Create `backend/tests/test_docker_e2e_contract.py`: documentation and acceptance-flow contract test.

### Deployment

- Modify `docker-compose.yml`: add the internal `docker-manager` service and backend environment variables.
- Modify `backend/.env.example`: document local Agent settings.
- Modify `deploy/.env.example`: document production Agent settings.
- Modify `deploy/README.md`: document the socket boundary, health check, and rollback behavior.

### Frontend

- Modify `frontend/src/api/http.js`: add JSON Docker API methods.
- Create `frontend/src/api/dockerStream.js`: authenticated SSE parsing for live container logs.
- Modify `frontend/src/router/index.js`: add `/docker` route.
- Modify `frontend/src/layouts/AppLayout.vue`: add Docker navigation for desktop and mobile.
- Create `frontend/src/pages/Docker.vue`: overview, service/container views, details, actions, and logs.
- Modify `frontend/src/styles.css`: responsive Docker page styles using existing design tokens.
- Create `frontend/src/pages/dockerContract.test.js`: page and navigation contract checks.

---

### Task 1: Build the Docker Agent domain service

**Files:**
- Create: `docker-manager/requirements.txt`
- Create: `docker-manager/Dockerfile`
- Create: `docker-manager/app/__init__.py`
- Create: `docker-manager/app/schemas.py`
- Create: `docker-manager/app/service.py`
- Test: `docker-manager/tests/test_service.py`

**Interfaces:**
- Consumes: Docker SDK client objects with `containers.list`, `containers.get`, `container.stats`, and `container.logs` methods.
- Produces: `DockerService.list_overview()`, `list_projects()`, `list_containers(filters)`, `get_container(container_id)`, `get_logs(container_id, tail, since, until)`, `stream_logs(container_id, tail, since, until)`, `container_action(container_id, action)`, and `service_action(project, service, action)`.
- Canonical container state values are `running`, `exited`, `paused`, `restarting`, `dead`, `created`, and `unknown`.
- Canonical health values are `healthy`, `unhealthy`, `starting`, and `none`.

- [ ] **Step 1: Write the failing normalization tests**

```python
def test_container_summary_maps_compose_labels_and_health():
    container = FakeContainer(
        id="abc123",
        name="api-1",
        status="running",
        labels={
            "com.docker.compose.project": "shop",
            "com.docker.compose.service": "api",
        },
        attrs={
            "State": {
                "Status": "running",
                "StartedAt": "2026-08-09T01:02:03Z",
                "Health": {"Status": "healthy"},
            },
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
```

Define `FakeContainer` with `id`, `name`, `status`, `labels`, `attrs`, `start`, `stop`, `restart`, `pause`, `unpause`, `kill`, `remove`, `stats`, and `logs` attributes/methods, and define `FakeDockerClient.containers.list()` and `.get()` in the same test module. The fakes must record invoked actions and return the fixture container so the tests do not require a Docker daemon.

- [ ] **Step 2: Run the focused tests to verify they fail**

Run: `cd docker-manager && pytest -q tests/test_service.py`

Expected: FAIL because `DockerService` and the action constants do not exist.

- [ ] **Step 3: Implement the normalized domain service**

Create the Agent dependency files with these contents:

```text
# docker-manager/requirements.txt
fastapi==0.115.6
uvicorn[standard]==0.34.0
docker==7.1.0
pytest==8.3.4
httpx==0.28.1
```

```dockerfile
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY docker-manager/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY docker-manager/app /app/app
EXPOSE 9100
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9100"]
```

Implement `DockerService` with these rules:

```python
CONTAINER_ACTIONS = {"start", "stop", "restart", "pause", "unpause", "kill", "remove"}
SERVICE_ACTIONS = {"start", "stop", "restart"}

def list_containers(self, filters: dict[str, str] | None = None) -> list[dict]: ...
def service_action(self, project: str, service: str, action: str) -> dict: ...
```

Use container labels for `project` and `service`, use `container.attrs` for timestamps/image/restart count/ports/mounts/networks, and use `stats(stream=False)` only for running containers. When stats are unavailable, return zero-valued resource fields and keep the container status usable. Resolve `container.logs(..., demux=True)` into `{timestamp, stream, message}` entries; preserve stdout/stderr and strip only the Docker timestamp prefix from the message.

`service_action` must select containers whose Compose project and service labels exactly match the path parameters, execute the requested lifecycle method one container at a time, and return `{project, service, action, items}` with one result per target.

- [ ] **Step 4: Run the focused tests to verify they pass**

Run: `cd docker-manager && pytest -q tests/test_service.py`

Expected: PASS for state mapping, health mapping, label grouping, action allowlists, idempotent actions, and batch result shape.

- [ ] **Step 5: Commit the Agent domain layer**

```bash
git add docker-manager
git commit -m "feat: add Docker manager service layer"
```

### Task 2: Expose the protected Docker Agent API

**Files:**
- Modify: `docker-manager/app/schemas.py`
- Create: `docker-manager/app/main.py`
- Test: `docker-manager/tests/test_api.py`

**Interfaces:**
- Consumes: `DockerService` from Task 1 and header `X-Docker-Manager-Token`.
- Produces: Agent routes `GET /health`, `GET /internal/v1/overview`, `GET /internal/v1/projects`, `GET /internal/v1/containers`, `GET /internal/v1/containers/{id}`, `GET /internal/v1/containers/{id}/logs`, `GET /internal/v1/containers/{id}/logs/stream`, `POST /internal/v1/containers/{id}/actions/{action}`, and `POST /internal/v1/services/{project}/{service}/actions/{action}`.
- Produces: `StreamingResponse` with media type `text/event-stream` for the log stream; each SSE event contains one JSON log entry.

- [ ] **Step 1: Write the failing API contract tests**

```python
def test_agent_rejects_missing_token(client):
    response = client.get("/internal/v1/overview")
    assert response.status_code == 401


def test_agent_returns_container_list_with_valid_token(client):
    response = client.get("/internal/v1/containers", headers={"X-Docker-Manager-Token": "test-token"})
    assert response.status_code == 200
    assert response.json()["containers"][0]["name"] == "api-1"


def test_agent_stream_is_sse(client):
    with client.stream("GET", "/internal/v1/containers/abc/logs/stream", headers={"X-Docker-Manager-Token": "test-token"}) as response:
        assert response.headers["content-type"].startswith("text/event-stream")
```

Build the `client` fixture with `fastapi.testclient.TestClient`, override the Agent's `get_docker_service` dependency with a fake service returning one `api-1` container and one `{"timestamp": "...", "stream": "stdout", "message": "ok"}` log event, and set `DOCKER_MANAGER_TOKEN=test-token` through `monkeypatch` before importing the app.

- [ ] **Step 2: Run the API tests to verify they fail**

Run: `cd docker-manager && pytest -q tests/test_api.py`

Expected: FAIL because the Agent application and routes do not exist.

- [ ] **Step 3: Implement token validation and routes**

Read `DOCKER_MANAGER_TOKEN` from the Agent environment. Return `401` for a missing or mismatched token before invoking Docker SDK. Return JSON objects without the Workbench `ok()` wrapper because the Agent is an internal protocol service. Parse `tail` as an integer between 1 and 5000, and pass optional `since`/`until` values through as Docker log timestamps. Convert domain errors to `404` for missing containers, `400` for unsupported actions, and `503` for Docker Engine failures.

Use a small dependency `require_agent_token(request: Request)` and inject one `DockerService` instance created from `docker.from_env()`. Close the Docker client on application shutdown. Stream events as `data: {json}\n\n`, and stop the generator when the client disconnects.

- [ ] **Step 4: Run the Agent tests and import smoke test**

Run: `cd docker-manager && pytest -q`; `python -c "from app.main import app; assert app.title == 'Docker Manager Agent'"`

Expected: PASS, with a healthy app import and all token/route/stream tests passing.

- [ ] **Step 5: Commit the Agent API**

```bash
git add docker-manager/app docker-manager/tests
git commit -m "feat: expose protected Docker manager API"
```

### Task 3: Add the Workbench-to-Agent client

**Files:**
- Modify: `backend/app/core/config.py`
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/services/docker_manager.py`
- Test: `backend/tests/test_docker_manager_client.py`

**Interfaces:**
- Consumes: `settings.docker_manager_url`, `settings.docker_manager_token`, and `settings.docker_manager_timeout_seconds`.
- Produces: `DockerManagerClient.request(method, path, params=None, json=None)`, `stream_logs(container_id, params=None)`, and `DockerManagerUnavailable`.
- `request` returns decoded Agent JSON; it raises `DockerManagerUnavailable` for connection/timeouts and `DockerManagerRemoteError` with status/message for non-2xx responses.

- [ ] **Step 1: Write client tests with mocked httpx responses**

```python
def test_client_sends_internal_token_and_returns_json(monkeypatch):
    seen = {}

    def fake_request(method, url, **kwargs):
        seen.update(method=method, url=url, headers=kwargs["headers"])
        return FakeResponse(200, {"containers": []})

    monkeypatch.setattr(httpx, "request", fake_request)
    result = DockerManagerClient().request("GET", "/internal/v1/containers")

    assert result == {"containers": []}
    assert seen["url"].endswith("/internal/v1/containers")
    assert seen["headers"]["X-Docker-Manager-Token"] == settings.docker_manager_token


def test_client_maps_connection_failure_to_unavailable(monkeypatch):
    def fail(*args, **kwargs):
        raise httpx.ConnectError("agent offline")

    monkeypatch.setattr(httpx, "request", fail)
    with pytest.raises(DockerManagerUnavailable):
        DockerManagerClient().request("GET", "/internal/v1/overview")
```

Define `FakeResponse` with `status_code`, `json()`, `text`, `raise_for_status()`, and `iter_text()` members in the test module; it must model both a successful JSON response and a `503` response without requiring an HTTP server.

- [ ] **Step 2: Run the client tests to verify they fail**

Run: `cd backend && pytest -q tests/test_docker_manager_client.py`

Expected: FAIL because the settings fields and client module do not exist.

- [ ] **Step 3: Implement configuration and client behavior**

Add these settings with the listed defaults:

```python
docker_manager_url: str = "http://docker-manager:9100"
docker_manager_token: str = ""
docker_manager_timeout_seconds: float = 12.0
docker_protected_containers: str = "workbench-api,workbench-web,docker-manager,xp-mysql"
```

Expose `protected_container_names` as a trimmed non-empty set. Use `httpx.request` for JSON calls with `X-Docker-Manager-Token`, `X-Request-ID`, and the configured timeout. Use `httpx.stream("GET", ...)` for logs and yield decoded SSE chunks to the backend route. Never log the token or full response body.

- [ ] **Step 4: Run the client tests to verify they pass**

Run: `cd backend && pytest -q tests/test_docker_manager_client.py`

Expected: PASS for headers, URL construction, JSON decoding, timeout/connection mapping, non-2xx mapping, and SSE chunk forwarding.

- [ ] **Step 5: Commit the Agent client**

```bash
git add backend/app/core/config.py backend/app/services backend/tests/test_docker_manager_client.py
git commit -m "feat: add Workbench Docker manager client"
```

### Task 4: Add audited authenticated Docker routes

**Files:**
- Modify: `backend/app/models/models.py`
- Modify: `backend/app/models/__init__.py`
- Create: `backend/app/api/docker_routes.py`
- Modify: `backend/app/main.py`
- Modify: `backend/sql/init.sql`
- Test: `backend/tests/test_docker_routes.py`

**Interfaces:**
- Consumes: `DockerManagerClient` from Task 3, `get_current_user`, `get_db`, and `ok()`.
- Produces: the browser-facing routes from the design, plus `DockerActionIn(confirm_name: str | None = None)`.
- Produces: `DockerOperationLog` with `user_id`, `target_type`, `target_id`, `target_name`, `action`, `request_summary`, `result`, `error_message`, `duration_ms`, and `created_at`.

- [ ] **Step 1: Write failing route and audit tests**

```python
def test_docker_overview_requires_login(client):
    response = client.get("/api/docker/overview")
    assert response.status_code == 401


def test_remove_requires_exact_name_and_protected_container_cannot_be_removed(auth_client, fake_agent, db_session):
    fake_agent.container = {"id": "abc", "name": "workbench-api", "state": "running"}

    response = auth_client.post(
        "/api/docker/containers/abc/actions/remove",
        json={"confirm_name": "workbench-api"},
    )

    assert response.status_code == 409
    assert "受保护" in response.json()["msg"]
    assert db_session.query(DockerOperationLog).count() == 1


def test_service_action_returns_partial_results(auth_client, fake_agent):
    fake_agent.service_result = {
        "project": "shop",
        "service": "api",
        "action": "restart",
        "items": [
            {"name": "api-1", "result": "success"},
            {"name": "api-2", "result": "failed", "error": "not found"},
        ],
    }

    response = auth_client.post("/api/docker/services/shop/api/actions/restart")

    assert response.status_code == 200
    assert response.json()["data"]["items"][1]["result"] == "failed"
```

Add test fixtures in this module: `db_session` creates a temporary SQLite database with `Base.metadata.create_all`, `auth_client` overrides `get_db` and `get_current_user` with a known `User(id=7)`, and `fake_agent` overrides the route dependency with a fake client whose `request` and `stream_logs` methods return the dictionaries used above. The fixtures must use `app.dependency_overrides` and clear it in teardown.

- [ ] **Step 2: Run the route tests to verify they fail**

Run: `cd backend && pytest -q tests/test_docker_routes.py`

Expected: FAIL because the audit model, Docker router, and main-app router inclusion do not exist.

- [ ] **Step 3: Implement the audit model, schema DDL, and routes**

Define `DockerOperationLog.request_summary` as JSON and `error_message` as nullable text. Add an idempotent `CREATE TABLE IF NOT EXISTS docker_operation_log` statement to `backend/sql/init.sql` with a foreign key to `user(id)` and indexes on `user_id`, `created_at`, and `target_name`.

Create a router with prefix `/api/docker`. Every route depends on `get_current_user`. For mutating container routes, validate the action against the exact allowlist, load the target summary before removal/confirmation, reject names in `settings.protected_container_names` for `remove`, and require `confirm_name == target_name` for `kill` and `remove`. Record both successful and rejected mutation attempts with duration and a sanitized request summary. The read-only audit endpoint returns the latest 100 rows for the current user, newest first.

For the logs JSON route, validate `tail` between 1 and 5000. For the stream route, return a `StreamingResponse` that forwards only Agent SSE data and closes the Agent stream in a `finally` block. Translate client failures to `503 管理服务暂不可用`, remote 404 to 404, and remote action errors to the original 400/409 message.

- [ ] **Step 4: Run backend tests and existing regression tests**

Run: `cd backend && pytest -q`

Expected: PASS for Docker route tests plus all existing backend tests.

- [ ] **Step 5: Commit the backend proxy and audit layer**

```bash
git add backend/app backend/sql/init.sql backend/tests/test_docker_routes.py
git commit -m "feat: add audited Docker management routes"
```

### Task 5: Add the Agent to Compose with hardened deployment settings

**Files:**
- Modify: `docker-compose.yml`
- Modify: `backend/.env.example`
- Modify: `deploy/.env.example`
- Modify: `deploy/README.md`
- Test: `backend/tests/test_docker_compose_contract.py`

**Interfaces:**
- Consumes: `DOCKER_MANAGER_TOKEN`, `DOCKER_MANAGER_URL`, and `DOCKER_PROTECTED_CONTAINERS` from the deployment environment.
- Produces: an internal `docker-manager` service at `http://docker-manager:9100`, with no host port and a health check at `/health`.

- [ ] **Step 1: Add a Compose contract check**

Create a shell-independent Python test at `backend/tests/test_docker_compose_contract.py` that loads `docker-compose.yml` as text and asserts the service has the socket mount, `workbench-internal` network, no `ports:` entry, `read_only: true`, `security_opt` containing `no-new-privileges:true`, and `cap_drop` containing `ALL`.

- [ ] **Step 2: Run the contract test to verify it fails**

Run: `cd backend && pytest -q tests/test_docker_compose_contract.py`

Expected: FAIL because `docker-manager` is not yet present in Compose.

- [ ] **Step 3: Implement the Compose and environment changes**

Add this service shape to `docker-compose.yml`:

```yaml
  docker-manager:
    build:
      context: .
      dockerfile: docker-manager/Dockerfile
    image: workbench-docker-manager:latest
    container_name: docker-manager
    restart: unless-stopped
    environment:
      DOCKER_MANAGER_TOKEN: ${DOCKER_MANAGER_TOKEN}
    read_only: true
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    tmpfs:
      - /tmp
    mem_limit: 256m
    pids_limit: 128
    expose:
      - "9100"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    networks:
      - workbench-internal
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:9100/health')"]
      interval: 30s
      timeout: 5s
      retries: 3
```

Add `DOCKER_MANAGER_URL`, `DOCKER_MANAGER_TOKEN`, and `DOCKER_PROTECTED_CONTAINERS` to `workbench-api.environment`. Add the same token and protected-name examples to both environment example files. Document that the socket mount is the only privileged boundary, the Agent has no host port, `docker compose config` must pass before deployment, and rollback leaves existing containers and volumes untouched.

- [ ] **Step 4: Run Compose and regression validation**

Run: `docker compose config`; `cd backend && pytest -q`

Expected: Compose renders successfully, the Agent service has no published ports, and all backend tests pass.

- [ ] **Step 5: Commit the deployment wiring**

```bash
git add docker-compose.yml backend/.env.example deploy/.env.example deploy/README.md backend/tests/test_docker_compose_contract.py
git commit -m "feat: deploy hardened Docker manager Agent"
```

### Task 6: Add frontend API, route, and navigation contracts

**Files:**
- Modify: `frontend/src/api/http.js`
- Create: `frontend/src/api/dockerStream.js`
- Modify: `frontend/src/router/index.js`
- Modify: `frontend/src/layouts/AppLayout.vue`
- Test: `frontend/src/pages/dockerContract.test.js`
- Test: `frontend/src/pages/dockerContract.test.js`

**Interfaces:**
- Consumes: the FastAPI routes from Task 4 and the existing `http` Axios interceptor.
- Produces: API methods `dockerOverview`, `dockerProjects`, `dockerContainers`, `dockerContainer`, `dockerLogs`, `dockerAction`, `dockerServiceAction`, and `dockerAuditLogs`.
- Produces: `streamDockerLogs(containerId, params, onEvent, signal)` that sends the stored JWT as `Authorization: Bearer ...`, parses SSE `data:` records, calls `onEvent(parsedRecord)`, and aborts cleanly.

- [ ] **Step 1: Write frontend contract tests**

```javascript
test('router and AppLayout expose Docker management', () => {
  const routerSource = readFileSync(new URL('../router/index.js', import.meta.url), 'utf8')
  const layoutSource = readFileSync(new URL('../layouts/AppLayout.vue', import.meta.url), 'utf8')
  assert.match(routerSource, /path: 'docker'/)
  assert.match(routerSource, /Docker\.vue/)
  assert.match(layoutSource, /to="\/docker"/)
  assert.match(layoutSource, /Docker 管理/)
})

test('Docker API surface includes lifecycle and log methods', () => {
  const source = readFileSync(new URL('../api/http.js', import.meta.url), 'utf8')
  assert.match(source, /dockerOverview/)
  assert.match(source, /dockerAction/)
  assert.match(source, /dockerServiceAction/)
  assert.match(source, /dockerAuditLogs/)
})
```

- [ ] **Step 2: Run the contract test to verify it fails**

Run: `cd frontend && node --test src/pages/dockerContract.test.js`

Expected: FAIL because the route, navigation entry, and API methods do not exist.

- [ ] **Step 3: Implement API methods, SSE parsing, route, and navigation**

Add Axios methods with the existing `http` wrapper and use query parameters for `project`, `service`, `state`, `health`, `keyword`, `tail`, `since`, and `until`. Add a `dockerStream.js` reader that buffers incomplete SSE records, parses only `data:` lines, ignores keepalive comments, and throws the response message for non-2xx responses.

Add a `/docker` child route with title `Docker 管理`. Add a `Monitor` or `Cpu` Element Plus icon to `mainNav`, the desktop Tools section, and the mobile drawer. Keep Docker out of workspace/project context filtering because it represents the server, not Workbench business data.

- [ ] **Step 4: Run frontend contracts and build**

Run: `cd frontend && node --test src/utils/*.test.js src/layouts/*.test.js src/pages/dockerContract.test.js`; `npm run build`

Expected: PASS for all existing and Docker contracts, followed by a successful Vite production build.

- [ ] **Step 5: Commit the frontend API and navigation**

```bash
git add frontend/src/api frontend/src/router/index.js frontend/src/layouts/AppLayout.vue frontend/src/pages/dockerContract.test.js
git commit -m "feat: add Docker management navigation and API"
```

### Task 7: Implement the Docker management page

**Files:**
- Create: `frontend/src/pages/Docker.vue`
- Modify: `frontend/src/styles.css`

**Interfaces:**
- Consumes: the API methods from Task 6 and response fields from Tasks 1 and 4.
- Produces: a `/docker` page with overview metrics, service/container tabs, filters, container detail drawer, lifecycle actions, service batch actions, logs, and audit list.

- [ ] **Step 1: Write page behavior checks**

Add assertions to `frontend/src/pages/dockerContract.test.js` for the page source:

```javascript
const pageSource = readFileSync(new URL('./Docker.vue', import.meta.url), 'utf8')
assert.match(pageSource, /Docker 管理/)
assert.match(pageSource, /dockerOverview/)
assert.match(pageSource, /实时日志/)
assert.match(pageSource, /confirm_name/)
assert.match(pageSource, /streamDockerLogs/)
assert.match(pageSource, /受保护容器/)
```

- [ ] **Step 2: Run page checks to verify they fail**

Run: `cd frontend && node --test src/pages/dockerContract.test.js`

Expected: FAIL because `Docker.vue` is not present.

- [ ] **Step 3: Implement the page state and data flow**

Use the existing `<script setup>` and Element Plus patterns. Maintain `activeView` (`services` or `containers`), `overview`, `projects`, `containers`, `filters`, `selectedContainer`, `logLines`, `logFollowing`, and `loading`. Load overview/projects/containers on mount and poll every 5 seconds while the page is visible; clear the interval on unmount.

Render four stat cards for Engine status, running containers, abnormal containers, and Compose projects. Render service groups from project data and a filtered container table with status and health tags. Selecting a container opens a drawer with metadata and action buttons. Call `dockerAction` or `dockerServiceAction`, show Element Plus success/error messages, refresh the affected data, and keep partial batch results visible.

For `kill` and `remove`, open a confirmation dialog requiring the exact container name and send `{ confirm_name }`. Disable remove for protected containers and show the text `受保护容器不可删除`.

Implement the log panel with tail selector, keyword input, stdout/stderr badges, a follow toggle, and a scrollable `<pre>`. Load historical logs through `dockerLogs`; when follow is enabled, use `streamDockerLogs` with an `AbortController`, append events, cap displayed lines at 5000, and abort the stream when switching containers, closing the drawer, or unmounting.

- [ ] **Step 4: Implement responsive styles and run verification**

Add `.docker-page`, `.docker-stat-grid`, `.docker-toolbar`, `.docker-table`, `.docker-detail`, `.docker-log-panel`, and mobile media-query rules using `var(--surface)`, `var(--line)`, `var(--text)`, `var(--muted)`, `var(--primary)`, `var(--green)`, `var(--orange)`, and `var(--red)`. Do not introduce a new color system. Verify that tables become horizontally scrollable and the detail drawer/log panel remain usable below 760px.

Run: `cd frontend && node --test src/utils/*.test.js src/layouts/*.test.js src/pages/dockerContract.test.js`; `npm run build`

Expected: PASS for page contracts and the production build.

- [ ] **Step 5: Commit the Docker page**

```bash
git add frontend/src/pages/Docker.vue frontend/src/styles.css frontend/src/pages/dockerContract.test.js
git commit -m "feat: add Docker management console"
```

### Task 8: Run end-to-end verification and update deployment documentation

**Files:**
- Modify: `README.md`
- Modify: `deploy/README.md`
- Create: `backend/tests/test_docker_e2e_contract.py`

**Interfaces:**
- Consumes: the complete Agent, backend proxy, Compose service, and frontend page from Tasks 1-7.
- Produces: documented deployment commands and a repeatable smoke-test contract for the seven acceptance criteria.

- [ ] **Step 1: Add the Docker smoke-test contract**

Create a test that checks the documented commands and expected routes are present:

```python
def test_docker_management_documentation_covers_health_status_logs_and_actions():
    readme = Path("README.md").read_text()
    deploy_readme = Path("deploy/README.md").read_text()
    for phrase in ("docker-manager", "Docker 管理", "/api/docker/overview", "/api/docker/containers/{id}/logs"):
        assert phrase in readme or phrase in deploy_readme
```

- [ ] **Step 2: Run the smoke-test contract before documentation changes**

Run: `cd backend && pytest -q tests/test_docker_e2e_contract.py`

Expected: FAIL because the documentation does not yet mention the Docker management flow.

- [ ] **Step 3: Document local and production verification**

Add to `README.md` the local Agent configuration, the authenticated Workbench route, and the verification sequence:

```bash
docker compose config
docker compose build docker-manager workbench-api workbench-web
docker compose up -d docker-manager workbench-api workbench-web
curl -fsS http://127.0.0.1:18082/health
```

Document that the final check must be performed in the logged-in UI: discover all containers, open a log stream, restart a non-protected test container, verify the audit row, and confirm protected-container removal is rejected. Document rollback as stopping the Agent/API image update without deleting containers, networks, volumes, or database data.

- [ ] **Step 4: Run the complete verification matrix**

Run:

```bash
cd backend && pytest -q
cd ../docker-manager && pytest -q
cd ../frontend && node --test src/utils/*.test.js src/layouts/*.test.js src/pages/dockerContract.test.js && npm run build
cd .. && docker compose config
```

Expected: all Python and Node tests pass, the frontend builds, and Compose renders without errors. If a real Docker Engine is available, additionally run the documented smoke test against a disposable non-protected container and verify its cleanup.

- [ ] **Step 5: Commit the final documentation and verification contract**

```bash
git add README.md deploy/README.md backend/tests/test_docker_e2e_contract.py
git commit -m "docs: document Docker management rollout and verification"
```

## Plan Self-Review

- Spec coverage: Agent isolation and token boundary are covered by Tasks 1-2; authenticated proxy and audit are covered by Tasks 3-4; Compose hardening is covered by Task 5; navigation, API, SSE logs, and UI are covered by Tasks 6-7; testing, deployment, and rollback are covered by Task 8.
- Placeholder scan: no `TBD`, `TODO`, or unspecified implementation steps are used; each task names files, interfaces, test commands, expected outcomes, and commit commands.
- Type consistency: the Agent action names, route paths, settings names, audit fields, API method names, and frontend stream function are consistent across tasks.
- Scope check: this remains one integrated single-server feature; multi-host management, shell access, `docker exec`, image builds, and Compose file editing remain explicit non-goals.
