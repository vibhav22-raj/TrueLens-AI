from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(ENV_PATH), case_sensitive=False, extra="ignore")

    # Default to a local SQLite file to avoid requiring Postgres for dev.
    database_url: str = "sqlite:///./deepshield.db"
    jwt_secret: str = "change_me_super_secret"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 120
    bcrypt_rounds: int = 10
    otp_expire_minutes: int = 10
    otp_dev_mode: bool = True
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from: str = "noreply@deepshield.local"
    smtp_use_tls: bool = True
    show_model_warnings: bool = False


settings = Settings()
