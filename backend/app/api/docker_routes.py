from __future__ import annotations

import time
from collections.abc import Iterator
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.api.common import ok
from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models import DockerOperationLog, User
from app.services.docker_manager import DockerManagerClient, DockerManagerRemoteError, DockerManagerUnavailable


router = APIRouter(prefix="/api/docker", tags=["docker"])
CONTAINER_ACTIONS = {"start", "stop", "restart", "pause", "unpause", "kill", "remove"}
SERVICE_ACTIONS = {"start", "stop", "restart"}
DANGEROUS_ACTIONS = {"kill", "remove"}


class DockerActionIn(BaseModel):
    confirm_name: str | None = None


def get_docker_manager_client() -> DockerManagerClient:
    return DockerManagerClient()


def _agent_error(exc: Exception) -> HTTPException:
    if isinstance(exc, DockerManagerUnavailable):
        return HTTPException(503, "Docker 管理服务暂不可用")
    if isinstance(exc, DockerManagerRemoteError):
        status = exc.status_code if 400 <= exc.status_code < 500 else 502
        return HTTPException(status, exc.message)
    return HTTPException(500, "Docker 管理接口调用失败")


def _write_audit(
    db: Session,
    user: User,
    *,
    target_type: str,
    target_id: str,
    target_name: str,
    action: str,
    result: str,
    duration_ms: int,
    error_message: str | None = None,
    request_summary: dict[str, Any] | None = None,
) -> None:
    db.add(
        DockerOperationLog(
            user_id=user.id,
            target_type=target_type,
            target_id=target_id,
            target_name=target_name,
            action=action,
            request_summary=request_summary or {},
            result=result,
            error_message=error_message,
            duration_ms=duration_ms,
        )
    )
    db.commit()


def _record_and_raise(
    db: Session,
    user: User,
    *,
    target_type: str,
    target_id: str,
    target_name: str,
    action: str,
    started: float,
    exc: HTTPException,
    request_summary: dict[str, Any] | None = None,
) -> None:
    _write_audit(
        db,
        user,
        target_type=target_type,
        target_id=target_id,
        target_name=target_name,
        action=action,
        result="rejected" if exc.status_code in {400, 409} else "failed",
        duration_ms=round((time.monotonic() - started) * 1000),
        error_message=str(exc.detail),
        request_summary=request_summary,
    )
    raise exc


def _request(client: DockerManagerClient, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
    try:
        return client.request(method, path, **kwargs)
    except Exception as exc:
        raise _agent_error(exc) from exc


def _decorate_protection(payload: dict[str, Any]) -> dict[str, Any]:
    def decorate(container: dict[str, Any]) -> None:
        container["protected"] = container.get("name") in settings.protected_container_names

    for container in payload.get("containers", []):
        decorate(container)
    for project in payload.get("projects", []):
        for service in project.get("services", []):
            for container in service.get("containers", []):
                decorate(container)
    if payload.get("name"):
        decorate(payload)
    return payload


@router.get("/overview")
def docker_overview(client: DockerManagerClient = Depends(get_docker_manager_client), user: User = Depends(get_current_user)):
    return ok(_request(client, "GET", "/internal/v1/overview"))


@router.get("/projects")
def docker_projects(client: DockerManagerClient = Depends(get_docker_manager_client), user: User = Depends(get_current_user)):
    return ok(_decorate_protection(_request(client, "GET", "/internal/v1/projects")))


@router.get("/containers")
def docker_containers(
    project: str | None = None,
    service: str | None = None,
    state: str | None = None,
    health: str | None = None,
    keyword: str | None = None,
    client: DockerManagerClient = Depends(get_docker_manager_client),
    user: User = Depends(get_current_user),
):
    params = {key: value for key, value in {"project": project, "service": service, "state": state, "health": health, "keyword": keyword}.items() if value}
    return ok(_decorate_protection(_request(client, "GET", "/internal/v1/containers", params=params)))


@router.get("/containers/{container_id}")
def docker_container(container_id: str, client: DockerManagerClient = Depends(get_docker_manager_client), user: User = Depends(get_current_user)):
    return ok(_decorate_protection(_request(client, "GET", f"/internal/v1/containers/{container_id}")))


@router.get("/containers/{container_id}/logs")
def docker_logs(
    container_id: str,
    tail: int = Query(default=200, ge=1, le=5000),
    since: int | None = None,
    until: int | None = None,
    client: DockerManagerClient = Depends(get_docker_manager_client),
    user: User = Depends(get_current_user),
):
    return ok(_request(client, "GET", f"/internal/v1/containers/{container_id}/logs", params={"tail": tail, "since": since, "until": until}))


@router.get("/containers/{container_id}/logs/stream")
def docker_log_stream(
    container_id: str,
    tail: int = Query(default=200, ge=1, le=5000),
    since: int | None = None,
    until: int | None = None,
    client: DockerManagerClient = Depends(get_docker_manager_client),
    user: User = Depends(get_current_user),
):
    def events() -> Iterator[str]:
        try:
            with client.stream_logs(container_id, params={"tail": tail, "since": since, "until": until}) as lines:
                for line in lines:
                    yield f"{line}\n\n" if line else "\n"
        except Exception as exc:
            raise _agent_error(exc) from exc

    return StreamingResponse(events(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.get("/audit-logs")
def docker_audit_logs(
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    rows = db.scalars(select(DockerOperationLog).where(DockerOperationLog.user_id == user.id).order_by(desc(DockerOperationLog.created_at), desc(DockerOperationLog.id)).limit(limit)).all()
    return ok(
        [
            {
                "id": row.id,
                "target_type": row.target_type,
                "target_id": row.target_id,
                "target_name": row.target_name,
                "action": row.action,
                "request_summary": row.request_summary or {},
                "result": row.result,
                "error_message": row.error_message,
                "duration_ms": row.duration_ms,
                "created_at": row.created_at,
            }
            for row in rows
        ]
    )


@router.post("/containers/{container_id}/actions/{action}")
def docker_container_action(
    container_id: str,
    action: str,
    payload: DockerActionIn = Body(default=DockerActionIn()),
    db: Session = Depends(get_db),
    client: DockerManagerClient = Depends(get_docker_manager_client),
    user: User = Depends(get_current_user),
):
    started = time.monotonic()
    summary: dict[str, Any] = {}
    try:
        if action not in CONTAINER_ACTIONS:
            raise HTTPException(400, f"不支持的 Docker 操作：{action}")
        summary = _request(client, "GET", f"/internal/v1/containers/{container_id}")
        target_name = str(summary.get("name") or container_id)
        if action == "remove" and target_name in settings.protected_container_names:
            raise HTTPException(409, "受保护容器不可删除")
        if action in DANGEROUS_ACTIONS and payload.confirm_name != target_name:
            raise HTTPException(400, "危险操作需要输入准确的容器名称")
        result = _request(client, "POST", f"/internal/v1/containers/{container_id}/actions/{action}", json={})
        _write_audit(db, user, target_type="container", target_id=container_id, target_name=target_name, action=action, result="success", duration_ms=round((time.monotonic() - started) * 1000), request_summary={"confirmation_provided": bool(payload.confirm_name)})
        return ok(result, "Docker 操作已完成")
    except HTTPException as exc:
        _record_and_raise(db, user, target_type="container", target_id=container_id, target_name=str(summary.get("name") or container_id), action=action, started=started, exc=exc, request_summary={"confirmation_provided": bool(payload.confirm_name)})


@router.post("/services/{project}/{service}/actions/{action}")
def docker_service_action(
    project: str,
    service: str,
    action: str,
    db: Session = Depends(get_db),
    client: DockerManagerClient = Depends(get_docker_manager_client),
    user: User = Depends(get_current_user),
):
    started = time.monotonic()
    target_name = f"{project}/{service}"
    try:
        if action not in SERVICE_ACTIONS:
            raise HTTPException(400, f"不支持的服务操作：{action}")
        result = _request(client, "POST", f"/internal/v1/services/{project}/{service}/actions/{action}", json={})
        items = result.get("items", [])
        outcome = "partial" if any(item.get("result") == "failed" for item in items) else "success"
        _write_audit(db, user, target_type="service", target_id=target_name, target_name=target_name, action=action, result=outcome, duration_ms=round((time.monotonic() - started) * 1000), request_summary={})
        return ok(result, "服务操作已完成" if outcome == "success" else "服务操作部分失败")
    except HTTPException as exc:
        _record_and_raise(db, user, target_type="service", target_id=target_name, target_name=target_name, action=action, started=started, exc=exc)
