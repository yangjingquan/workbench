from pathlib import Path


ROOT = Path(__file__).parents[2]


def test_docker_management_documentation_covers_health_status_logs_and_actions():
    readme = (ROOT / "README.md").read_text()
    deploy_readme = (ROOT / "deploy" / "README.md").read_text()
    for phrase in ("docker-manager", "Docker 管理", "/api/docker/overview", "/api/docker/containers/{id}/logs"):
        assert phrase in readme or phrase in deploy_readme
