from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"


DEFAULT_JWT_SECRET = "change-me-in-env-local-dev-only"
DEFAULT_BOOTSTRAP_PASSWORD = "Admin2026*"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(ROOT_DIR / ".env"), extra="ignore")

    app_name: str = "Enterprise AI OS"
    app_version: str = "0.2.0-b1"
    app_env: str = "development"
    database_url: str = f"sqlite:///{(DATA_DIR / 'enterprise_ai_os.db').as_posix()}"
    jwt_secret: str = DEFAULT_JWT_SECRET
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 12
    cors_origins: str = "http://127.0.0.1:5180,http://localhost:5180"
    login_max_failed_attempts: int = 5
    login_lockout_minutes: int = 15
    allow_insecure_dev_bootstrap: bool = True
    bootstrap_admin_username: str = "admin"
    bootstrap_admin_password: str = DEFAULT_BOOTSTRAP_PASSWORD
    bootstrap_org_name: str = "Empresa demo"
    bootstrap_owner_username: str | None = None
    bootstrap_owner_password: str | None = None
    bootstrap_auditor_username: str | None = None
    bootstrap_auditor_password: str | None = None


settings = Settings()


def validate_security_settings() -> None:
    """Bloquea arranque inseguro en entornos no desarrollo."""
    env = (settings.app_env or "development").strip().lower()
    if env in {"development", "dev", "test"}:
        return
    if settings.jwt_secret == DEFAULT_JWT_SECRET or len(settings.jwt_secret) < 32:
        raise RuntimeError(
            "APP_ENV no desarrollo: configure JWT_SECRET (mín. 32 caracteres) fuera del código fuente."
        )
    if settings.allow_insecure_dev_bootstrap:
        raise RuntimeError(
            "APP_ENV no desarrollo: ALLOW_INSECURE_DEV_BOOTSTRAP debe ser false."
        )
    if settings.bootstrap_admin_password == DEFAULT_BOOTSTRAP_PASSWORD:
        raise RuntimeError(
            "APP_ENV no desarrollo: no use la contraseña bootstrap por defecto; defina BOOTSTRAP_ADMIN_PASSWORD."
        )

