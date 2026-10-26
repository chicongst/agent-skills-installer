from pathlib import Path
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, PostgresDsn, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class MemoryStorage(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    driver: Literal["memory"]


class PostgresStorage(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    driver: Literal["postgres"]
    database_url: SecretStr
    pool_size: int = Field(default=10, ge=1)
    max_overflow: int = Field(default=10, ge=0)
    pool_timeout_seconds: float = Field(default=5, gt=0)
    connect_timeout_seconds: float = Field(default=5, gt=0)
    statement_timeout_seconds: float = Field(default=10, gt=0)

    @model_validator(mode="after")
    def _url_is_postgres(self) -> Self:
        PostgresDsn(self.database_url.get_secret_value())
        return self


type StorageSettings = Annotated[MemoryStorage | PostgresStorage, Field(discriminator="driver")]

type TokenAlgorithm = Literal["RS256", "PS256", "ES256", "EdDSA"]


class AuthSettings(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    issuer: str = Field(min_length=1)
    audience: str = Field(min_length=1)
    jwks_url: HttpUrl | None = None
    public_key_file: Path | None = None
    algorithms: tuple[TokenAlgorithm, ...] = Field(default=("RS256",), min_length=1)

    @model_validator(mode="after")
    def _exactly_one_key_source(self) -> Self:
        if (self.jwks_url is None) == (self.public_key_file is None):
            msg = "Set exactly one of TODO_AUTH__JWKS_URL or TODO_AUTH__PUBLIC_KEY_FILE."
            raise ValueError(msg)
        if self.public_key_file is not None and not self.public_key_file.is_file():
            msg = f"TODO_AUTH__PUBLIC_KEY_FILE does not exist: {self.public_key_file}"
            raise ValueError(msg)
        return self


class Settings(BaseSettings):
    """Loaded once at startup from real environment variables only (development: `uv run --env-file .env ...`).
    Storage and auth have no defaults; `environment` defaults to the strictest value.
    """

    model_config = SettingsConfigDict(
        env_prefix="TODO_",
        env_nested_delimiter="__",
        env_file=None,
        extra="forbid",
        frozen=True,
    )

    environment: Literal["development", "test", "production"] = "production"
    storage: StorageSettings
    auth: AuthSettings
    log_format: Literal["json", "console"] = "json"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    write_rate_limit: str = "60/minute"
    max_body_bytes: int = Field(default=1_048_576, gt=0)
    readiness_timeout_seconds: float = Field(default=0.8, gt=0)
    docs_enabled: bool = False

    @model_validator(mode="after")
    def _production_is_durable_and_closed(self) -> Self:
        if self.environment == "production":
            if isinstance(self.storage, MemoryStorage):
                msg = "TODO_STORAGE__DRIVER=memory is not allowed when TODO_ENVIRONMENT=production."
                raise ValueError(msg)
            if self.docs_enabled:
                msg = "TODO_DOCS_ENABLED is not allowed when TODO_ENVIRONMENT=production."
                raise ValueError(msg)
        return self
