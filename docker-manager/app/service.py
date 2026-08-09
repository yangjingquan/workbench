from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime
from typing import Any, Iterable, Iterator

from .schemas import CONTAINER_ACTIONS, SERVICE_ACTIONS, DockerActionError, DockerEngineError, DockerNotFoundError

try:  # The Agent image installs docker-py; local unit tests can use fakes without it.
    from docker.errors import APIError, DockerException, NotFound
except ImportError:  # pragma: no cover - exercised only when the optional SDK is absent.
    class DockerException(Exception):
        pass

    class APIError(DockerException):
        pass

    class NotFound(DockerException):
        pass


TIMESTAMP_PREFIX = re.compile(rb"^(\d{4}-\d{2}-\d{2}T[^ ]+) ?")


class DockerService:
    def __init__(self, client: Any):
        self.client = client

    def list_overview(self) -> dict[str, Any]:
        try:
            containers = self._list_containers()
            projects = self.list_projects()
        except DockerException as exc:
            raise DockerEngineError(str(exc)) from exc

        running = sum(item["state"] == "running" for item in containers)
        abnormal = sum(item["health"] == "unhealthy" or item["state"] in {"dead", "restarting"} for item in containers)
        resources = {
            "cpu_percent": round(sum(item["resources"]["cpu_percent"] for item in containers), 2),
            "memory_usage_bytes": sum(item["resources"]["memory_usage_bytes"] for item in containers),
            "memory_limit_bytes": sum(item["resources"]["memory_limit_bytes"] for item in containers),
        }
        return {
            "engine": {"status": "online", "version": self._engine_version()},
            "container_count": len(containers),
            "running_count": running,
            "stopped_count": len(containers) - running,
            "abnormal_count": abnormal,
            "project_count": len(projects),
            "resources": resources,
        }

    def list_projects(self) -> list[dict[str, Any]]:
        groups: dict[str, dict[str, Any]] = defaultdict(lambda: {"name": "", "containers": [], "services": {}})
        for container in self._list_containers():
            summary = self._summary(container)
            project = summary["project"] or "独立容器"
            group = groups[project]
            group["name"] = project
            group["containers"].append(summary)
            service = summary["service"] or summary["name"]
            group["services"].setdefault(service, []).append(summary)

        result = []
        for project_name, group in sorted(groups.items()):
            services = [
                {
                    "name": service_name,
                    "containers": containers,
                    "running_count": sum(item["state"] == "running" for item in containers),
                    "abnormal_count": sum(item["health"] == "unhealthy" or item["state"] in {"dead", "restarting"} for item in containers),
                }
                for service_name, containers in sorted(group["services"].items())
            ]
            result.append({"name": project_name, "container_count": len(group["containers"]), "services": services})
        return result

    def list_containers(self, filters: dict[str, str] | None = None) -> list[dict[str, Any]]:
        filters = filters or {}
        result = []
        for container in self._list_containers():
            summary = self._summary(container)
            if filters.get("project") and summary["project"] != filters["project"]:
                continue
            if filters.get("service") and summary["service"] != filters["service"]:
                continue
            if filters.get("state") and summary["state"] != filters["state"]:
                continue
            if filters.get("health") and summary["health"] != filters["health"]:
                continue
            keyword = filters.get("keyword", "").strip().lower()
            if keyword and keyword not in f'{summary["name"]} {summary["image"]}'.lower():
                continue
            result.append(summary)
        return sorted(result, key=lambda item: (item["project"], item["name"]))

    def get_container(self, container_id: str) -> dict[str, Any]:
        return self._summary(self._get_container(container_id), include_details=True)

    def get_logs(self, container_id: str, tail: int = 200, since: int | None = None, until: int | None = None) -> dict[str, Any]:
        container = self._get_container(container_id)
        try:
            raw = container.logs(stdout=True, stderr=True, timestamps=True, tail=tail, since=since, until=until, demux=True)
        except DockerException as exc:
            raise DockerEngineError(str(exc)) from exc
        return {"container_id": container.id, "lines": list(self._decode_log_chunks(raw))}

    def stream_logs(self, container_id: str, tail: int = 200, since: int | None = None, until: int | None = None) -> Iterator[dict[str, str]]:
        container = self._get_container(container_id)
        try:
            chunks = container.logs(
                stdout=True,
                stderr=True,
                timestamps=True,
                tail=tail,
                since=since,
                until=until,
                demux=True,
                stream=True,
                follow=True,
            )
            yield from self._decode_log_chunks(chunks)
        except DockerException as exc:
            raise DockerEngineError(str(exc)) from exc

    def container_action(self, container_id: str, action: str) -> dict[str, Any]:
        if action not in CONTAINER_ACTIONS:
            raise DockerActionError(f"不支持的 Docker 操作：{action}")
        container = self._get_container(container_id)
        try:
            getattr(container, action)()
            state = self._summary(container, include_details=False)
        except (AttributeError, APIError, DockerException) as exc:
            raise DockerEngineError(str(exc)) from exc
        return {"action": action, "changed": True, "container": state}

    def service_action(self, project: str, service: str, action: str) -> dict[str, Any]:
        if action not in SERVICE_ACTIONS:
            raise DockerActionError(f"不支持的服务操作：{action}")
        items = []
        for container in self._list_containers():
            labels = getattr(container, "labels", {}) or {}
            if labels.get("com.docker.compose.project") != project or labels.get("com.docker.compose.service") != service:
                continue
            try:
                getattr(container, action)()
                items.append({"id": container.id, "name": container.name, "result": "success", "container": self._summary(container, include_details=False)})
            except (AttributeError, APIError, DockerException) as exc:
                items.append({"id": container.id, "name": container.name, "result": "failed", "error": str(exc)})
        return {"project": project, "service": service, "action": action, "items": items}

    def _list_containers(self) -> list[Any]:
        try:
            return list(self.client.containers.list(all=True))
        except DockerException as exc:
            raise DockerEngineError(str(exc)) from exc

    def _get_container(self, container_id: str) -> Any:
        try:
            return self.client.containers.get(container_id)
        except NotFound as exc:
            raise DockerNotFoundError(f"容器不存在：{container_id}") from exc
        except DockerException as exc:
            raise DockerEngineError(str(exc)) from exc

    def _engine_version(self) -> str | None:
        try:
            return self.client.version().get("Version")
        except DockerException:
            return None

    def _summary(self, container: Any, include_details: bool = False) -> dict[str, Any]:
        attrs = getattr(container, "attrs", {}) or {}
        state_attrs = attrs.get("State", {}) or {}
        status = getattr(container, "status", None) or state_attrs.get("Status", "unknown")
        state = status if status in {"running", "exited", "paused", "restarting", "dead", "created"} else "unknown"
        health = ((state_attrs.get("Health") or {}).get("Status") or "none")
        if health not in {"healthy", "unhealthy", "starting", "none"}:
            health = "none"
        labels = getattr(container, "labels", None) or attrs.get("Config", {}).get("Labels", {}) or {}
        summary: dict[str, Any] = {
            "id": getattr(container, "id", ""),
            "name": str(getattr(container, "name", "")).lstrip("/"),
            "project": labels.get("com.docker.compose.project", ""),
            "service": labels.get("com.docker.compose.service", ""),
            "image": (attrs.get("Config") or {}).get("Image", ""),
            "state": state,
            "status_text": getattr(container, "status", status),
            "health": health,
            "started_at": state_attrs.get("StartedAt"),
            "finished_at": state_attrs.get("FinishedAt"),
            "restart_count": int((attrs.get("HostConfig") or {}).get("RestartCount", 0) or 0),
            "ports": self._ports((attrs.get("NetworkSettings") or {}).get("Ports") or {}),
            "resources": self._stats(container, state),
        }
        if include_details:
            summary.update(
                {
                    "command": (attrs.get("Config") or {}).get("Cmd") or [],
                    "entrypoint": (attrs.get("Config") or {}).get("Entrypoint") or [],
                    "mounts": attrs.get("Mounts") or [],
                    "networks": sorted(((attrs.get("NetworkSettings") or {}).get("Networks") or {}).keys()),
                    "environment_names": [str(item).split("=", 1)[0] for item in (attrs.get("Config") or {}).get("Env", [])],
                }
            )
        return summary

    @staticmethod
    def _ports(ports: dict[str, Any]) -> list[dict[str, Any]]:
        result = []
        for private, bindings in ports.items():
            for binding in bindings or [{}]:
                result.append(
                    {
                        "private": private,
                        "public": binding.get("HostPort"),
                        "host_ip": binding.get("HostIp"),
                    }
                )
        return result

    @staticmethod
    def _stats(container: Any, state: str) -> dict[str, float | int]:
        empty = {"cpu_percent": 0.0, "memory_usage_bytes": 0, "memory_limit_bytes": 0, "memory_percent": 0.0}
        if state != "running":
            return empty
        try:
            stats = container.stats(stream=False)
            memory = stats.get("memory_stats", {})
            usage = int(memory.get("usage", 0) or 0)
            limit = int(memory.get("limit", 0) or 0)
            cpu = stats.get("cpu_stats", {})
            previous = stats.get("precpu_stats", {})
            cpu_delta = (cpu.get("cpu_usage", {}).get("total_usage", 0) or 0) - (previous.get("cpu_usage", {}).get("total_usage", 0) or 0)
            system_delta = (cpu.get("system_cpu_usage", 0) or 0) - (previous.get("system_cpu_usage", 0) or 0)
            online_cpus = cpu.get("online_cpus") or len(cpu.get("cpu_usage", {}).get("percpu_usage", []) or []) or 1
            cpu_percent = (cpu_delta / system_delta) * online_cpus * 100 if system_delta > 0 else 0.0
            return {
                "cpu_percent": round(cpu_percent, 2),
                "memory_usage_bytes": usage,
                "memory_limit_bytes": limit,
                "memory_percent": round((usage / limit) * 100, 2) if limit else 0.0,
            }
        except Exception:
            return empty

    @staticmethod
    def _decode_log_chunks(chunks: Iterable[Any]) -> Iterator[dict[str, str]]:
        for chunk in chunks or []:
            if isinstance(chunk, tuple):
                stdout, stderr = chunk
                stream = "stdout" if stdout is not None else "stderr"
                payload = stdout if stdout is not None else stderr
            else:
                stream = "stdout"
                payload = chunk
            if not payload:
                continue
            raw = payload if isinstance(payload, bytes) else str(payload).encode()
            for line in raw.splitlines():
                match = TIMESTAMP_PREFIX.match(line)
                timestamp = match.group(1).decode(errors="replace") if match else ""
                message = line[match.end() :] if match else line
                yield {"timestamp": timestamp, "stream": stream, "message": message.decode(errors="replace")}
