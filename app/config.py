from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Techma Mail"
    environment: str = "production"
    api_key: str = Field(min_length=24)
    smtp_host: str
    smtp_port: int = 587
    smtp_username: str
    smtp_password: str
    smtp_from_email: str
    smtp_from_name: str = "Techma Mail"
    smtp_use_tls: bool = False
    smtp_start_tls: bool = True
    allowed_from_domains: str = ""
    max_recipients: int = 20
    max_message_bytes: int = 1_000_000
    smtp_timeout_seconds: float = 20.0

    @field_validator("smtp_port")
    @classmethod
    def valid_port(cls, value: int) -> int:
        if not 1 <= value <= 65535:
            raise ValueError("SMTP_PORT must be between 1 and 65535")
        return value

    @property
    def from_domains(self) -> set[str]:
        return {item.strip().lower() for item in self.allowed_from_domains.split(",") if item.strip()}

@lru_cache
def get_settings() -> Settings:
    return Settings()
