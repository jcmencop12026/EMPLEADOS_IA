from pathlib import Path
from typing import Literal

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"

AppEnv = Literal["dev", "test", "prod"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(ROOT_DIR / ".env"), extra="ignore")

    app_name: str = "Enterprise AI OS"
    app_version: str = "0.2.0-b1"
    app_env: AppEnv = "dev"
    database_url: str = f"sqlite:///{(DATA_DIR / 'enterprise_ai_os.db').as_posix()}"
    jwt_secret: str = "change-me-in-env-local-dev-only"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 12
    cors_origins: str = "http://127.0.0.1:5180,http://localhost:5180"
    enable_api_docs: bool | None = None
    bootstrap_admin_username: str = "admin"
    bootstrap_admin_password: str = "Admin2026*"
    bootstrap_org_name: str = "Empresa demo"
    backup_dir: str = str(DATA_DIR / "backups")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def api_docs_enabled(self) -> bool:
        if self.enable_api_docs is not None:
            return self.enable_api_docs
        return self.app_env != "prod"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
