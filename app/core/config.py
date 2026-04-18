from functools import lru_cache
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_sqlite_url() -> str:
    local_path = Path.home() / "AppData" / "Local" / "EV_Nation" / "ev_nation.db"
    return f"sqlite:///{local_path.as_posix()}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    project_name: str = "EV Nation API"
    api_v1_prefix: str = "/api/v1"
    database_url: str = _default_sqlite_url()
    database_echo: bool = False
    database_connect_timeout_seconds: int = 5
    whatsapp_number: str | None = None
    secret_key: str = "change-me"
    access_token_expire_minutes: int = 60
    admin_cookie_name: str = "evn_admin_token"
    bootstrap_admin_email: str = "admin@evnation.local"
    bootstrap_admin_password: str = "Admin12345"
    bootstrap_admin_full_name: str | None = "Local Admin"
    media_dir: str = str(_PROJECT_ROOT / "media")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
