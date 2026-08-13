from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "mysql+pymysql://root:changeme_root@127.0.0.1:3306/workbench?charset=utf8mb4"
    jwt_secret_key: str = "please-change-this-in-production"
    access_token_expire_minutes: int = 1440
    cors_origins: str = "http://localhost:5173,http://localhost:5174,null"
    workbench_build_id: str = "dev"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


settings = Settings()
