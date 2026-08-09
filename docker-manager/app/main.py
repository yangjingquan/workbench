from __future__ import annotations

import json
import os
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from .schemas import DockerActionError, DockerEngineError, DockerNotFoundError
from .service import DockerService

try:
    import docker
except ImportError:  # pragma: no cover - the Agent image always installs docker-py.
    docker = None


app = FastAPI(title="Docker Manager Agent", version="1.0.0")
_service: DockerService | None = None


def get_docker_service() -> DockerService:
    global _service
    if _service is None:
        if docker is None:
            raise DockerEngineError("Docker SDK 未安装")
        _service = DockerService(docker.from_env())
    return _service


def require_agent_token(x_docker_manager_token: Annotated[str | None, Header()] = None) -> None:
    expected = os.getenv("DOCKER_MANAGER_TOKEN", "")
    if not expected or x_docker_manager_token != expected:
        raise HTTPException(status_code=401, detail="Agent Token 无效")


def service_dependency(service: DockerService = Depends(get_docker_service)) -> DockerService:
    return service


def _error_response(exc: Exception) -> HTTPException:
    if isinstance(exc, DockerNotFoundError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, DockerActionError):
        return HTTPException(status_code=400, detail=str(exc))
    if isinstance(exc, DockerEngineError):
        return HTTPException(status_code=503, detail=str(exc) or "Docker Engine 不可用")
    return HTTPException(status_code=500, detail="Docker Agent 内部错误")


@app.get("/health")
def health():
    return {"status": "ok", "service": "docker-manager"}


@app.get("/internal/v1/overview", dependencies=[Depends(require_agent_token)])
def overview(service: DockerService = Depends(service_dependency)):
    try:
        return service.list_overview()
    except Exception as exc:
        raise _error_response(exc) from exc


@app.get("/internal/v1/projects", dependencies=[Depends(require_agent_token)])
def projects(service: DockerService = Depends(service_dependency)):
    try:
        return {"projects": service.list_projects()}
    except Exception as exc:
        raise _error_response(exc) from exc


@app.get("/internal/v1/containers", dependencies=[Depends(require_agent_token)])
def containers(
    project: str | None = None,
    service_name: Annotated[str | None, Query(alias="service")] = None,
    state: str | None = None,
    health: str | None = None,
    keyword: str | None = None,
    service: DockerService = Depends(service_dependency),
):
    try:
        result = service.list_containers({"project": project or "", "service": service_name or "", "state": state or "", "health": health or "", "keyword": keyword or ""})
        return {"containers": result}
    except Exception as exc:
        raise _error_response(exc) from exc


@app.get("/internal/v1/containers/{container_id}", dependencies=[Depends(require_agent_token)])
def container_detail(container_id: str, service: DockerService = Depends(service_dependency)):
    try:
        return service.get_container(container_id)
    except Exception as exc:
        raise _error_response(exc) from exc


@app.get("/internal/v1/containers/{container_id}/logs", dependencies=[Depends(require_agent_token)])
def container_logs(
    container_id: str,
    tail: int = Query(default=200, ge=1, le=5000),
    since: int | None = None,
    until: int | None = None,
    service: DockerService = Depends(service_dependency),
):
    try:
        return service.get_logs(container_id, tail=tail, since=since, until=until)
    except Exception as exc:
        raise _error_response(exc) from exc


@app.get("/internal/v1/containers/{container_id}/logs/stream", dependencies=[Depends(require_agent_token)])
def container_log_stream(
    request: Request,
    container_id: str,
    tail: int = Query(default=200, ge=1, le=5000),
    since: int | None = None,
    until: int | None = None,
    service: DockerService = Depends(service_dependency),
):
    async def events() -> AsyncIterator[str]:
        try:
            for item in service.stream_logs(container_id, tail=tail, since=since, until=until):
                if await request.is_disconnected():
                    break
                yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"
        except Exception as exc:
            error = _error_response(exc)
            yield f"event: error\ndata: {json.dumps({'detail': error.detail}, ensure_ascii=False)}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.post("/internal/v1/containers/{container_id}/actions/{action}", dependencies=[Depends(require_agent_token)])
def container_action(container_id: str, action: str, service: DockerService = Depends(service_dependency)):
    try:
        return service.container_action(container_id, action)
    except Exception as exc:
        raise _error_response(exc) from exc


@app.post("/internal/v1/services/{project}/{service_name}/actions/{action}", dependencies=[Depends(require_agent_token)])
def service_action(project: str, service_name: str, action: str, service: DockerService = Depends(service_dependency)):
    try:
        return service.service_action(project, service_name, action)
    except Exception as exc:
        raise _error_response(exc) from exc
