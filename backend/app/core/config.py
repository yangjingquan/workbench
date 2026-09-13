from ipaddress import IPv4Network, IPv6Network, ip_network

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "mysql+pymysql://root:changeme_root@127.0.0.1:3306/workbench?charset=utf8mb4"
    jwt_secret_key: str = "please-change-this-in-production"
    access_token_expire_minutes: int = 1440
    cors_origins: str = "http://localhost:5173,http://localhost:5174,null"
    redis_url: str = ""
    trusted_proxy_cidrs: str = "127.0.0.1/32,::1/128,172.16.0.0/12"
    workbench_build_id: str = "dev"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def trusted_proxy_networks(self) -> list[IPv4Network | IPv6Network]:
        networks = []
        for value in self.trusted_proxy_cidrs.split(","):
            value = value.strip()
            if value:
                networks.append(ip_network(value, strict=False))
        return networks


settings = Settings()
