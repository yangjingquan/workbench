from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "mysql+pymysql://root:changeme_root@127.0.0.1:3306/workbench?charset=utf8mb4"
    jwt_secret_key: str = "please-change-this-in-production"
    access_token_expire_minutes: int = 1440
    cors_origins: str = "http://localhost:5173,http://localhost:5174,null"
    docker_manager_url: str = "http://docker-manager:9100"
    docker_manager_token: str = ""
    docker_manager_timeout_seconds: float = 12.0
    docker_protected_containers: str = "workbench-api,workbench-web,docker-manager,xp-mysql"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def protected_container_names(self) -> set[str]:
        return {item.strip() for item in self.docker_protected_containers.split(",") if item.strip()}


settings = Settings()
