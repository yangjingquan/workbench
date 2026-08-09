from __future__ import annotations

from typing import Final


CONTAINER_ACTIONS: Final[frozenset[str]] = frozenset(
    {"start", "stop", "restart", "pause", "unpause", "kill", "remove"}
)
SERVICE_ACTIONS: Final[frozenset[str]] = frozenset({"start", "stop", "restart"})


class DockerActionError(ValueError):
    """Raised when a caller requests an action outside the public allowlist."""


class DockerNotFoundError(LookupError):
    """Raised when a container no longer exists in the Docker Engine."""


class DockerEngineError(RuntimeError):
    """Raised when Docker cannot complete an otherwise valid operation."""
