from __future__ import annotations

import json
from contextlib import contextmanager
from collections.abc import Iterator
from typing import Any
from uuid import uuid4

import httpx

from app.core.config import settings


class DockerManagerUnavailable(RuntimeError):
    """Raised when the internal Docker Agent cannot be reached."""


class DockerManagerRemoteError(RuntimeError):
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


class DockerManagerClient:
    def __init__(self, base_url: str | None = None, token: str | None = None, timeout: float | None = None):
        self.base_url = (base_url or settings.docker_manager_url).rstrip("/")
        self.token = settings.docker_manager_token if token is None else token
        self.timeout = timeout or settings.docker_manager_timeout_seconds

    def request(self, method: str, path: str, params: dict[str, Any] | None = None, json: Any = None) -> dict[str, Any]:
        try:
            response = httpx.request(
                method,
                self._url(path),
                params=params,
                json=json,
                headers=self._headers(),
                timeout=self.timeout,
            )
        except (httpx.TimeoutException, httpx.RequestError) as exc:
            raise DockerManagerUnavailable("Docker 管理服务暂不可用") from exc
        return self._decode(response)

    @contextmanager
    def stream_logs(self, container_id: str, params: dict[str, Any] | None = None) -> Iterator[str]:
        try:
            with httpx.stream(
                "GET",
                self._url(f"/internal/v1/containers/{container_id}/logs/stream"),
                params=params,
                headers=self._headers(),
                timeout=self.timeout,
            ) as response:
                if response.is_error:
                    self._decode(response)
                yield response.iter_lines()
        except (DockerManagerUnavailable, DockerManagerRemoteError):
            raise
        except (httpx.TimeoutException, httpx.RequestError) as exc:
            raise DockerManagerUnavailable("Docker 管理服务暂不可用") from exc

    def _headers(self) -> dict[str, str]:
        return {
            "X-Docker-Manager-Token": self.token,
            "X-Request-ID": str(uuid4()),
        }

    def _url(self, path: str) -> str:
        return f"{self.base_url}/{path.lstrip('/')}"

    @staticmethod
    def _decode(response: httpx.Response) -> dict[str, Any]:
        if response.is_error:
            try:
                payload = response.json()
                message = payload.get("detail") or payload.get("msg") or response.text
            except (ValueError, json.JSONDecodeError):
                message = response.text or "Docker Agent 请求失败"
            raise DockerManagerRemoteError(response.status_code, str(message))
        try:
            return response.json()
        except ValueError as exc:
            raise DockerManagerRemoteError(502, "Docker Agent 返回了无效响应") from exc
