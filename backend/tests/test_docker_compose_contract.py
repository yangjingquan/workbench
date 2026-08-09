from pathlib import Path
import re


COMPOSE = Path(__file__).parents[2].joinpath("docker-compose.yml").read_text()


def _service_block(name: str) -> str:
    marker = f"  {name}:\n"
    assert marker in COMPOSE
    block = COMPOSE.split(marker, 1)[1]
    next_service = re.search(r"\n  [A-Za-z0-9_-]+:\n", block)
    return block if not next_service else block[: next_service.start()]


def test_docker_manager_has_socket_boundary_and_hardening():
    block = _service_block("docker-manager")
    assert "/var/run/docker.sock:/var/run/docker.sock" in block
    assert "workbench-internal" in block
    assert "\n    ports:" not in block
    assert "read_only: true" in block
    assert "no-new-privileges:true" in block
    assert "cap_drop:" in block and "      - ALL" in block
    assert "healthcheck:" in block


def test_workbench_api_receives_agent_configuration():
    block = _service_block("workbench-api")
    assert "DOCKER_MANAGER_URL:" in block
    assert "DOCKER_MANAGER_TOKEN:" in block
    assert "DOCKER_PROTECTED_CONTAINERS:" in block
