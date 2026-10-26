from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from pydantic import SecretStr

from todo_api.settings import AuthSettings, MemoryStorage, PostgresStorage, Settings

ISSUER = "https://issuer.test"
AUDIENCE = "todo-api"


@dataclass(frozen=True)
class SigningKey:
    private: rsa.RSAPrivateKey
    public_file: Path

    def token(self, subject: str | None, *, lifetime: timedelta = timedelta(minutes=5), **claims: Any) -> str:
        now = datetime.now(UTC)  # noqa: TID251
        payload: dict[str, Any] = {"iss": ISSUER, "aud": AUDIENCE, "iat": now, "exp": now + lifetime, **claims}
        if subject is not None:
            payload["sub"] = subject
        return jwt.encode(payload, self.private, algorithm="RS256")


@pytest.fixture(scope="session")
def signing_key(tmp_path_factory: pytest.TempPathFactory) -> SigningKey:
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_file = tmp_path_factory.mktemp("jwt") / "public.pem"
    public_file.write_bytes(
        private.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
    )
    return SigningKey(private, public_file)


type SettingsFactory = Callable[..., Settings]


@pytest.fixture(scope="session")
def make_settings(signing_key: SigningKey) -> SettingsFactory:
    def make(*, database_url: str | None = None, **overrides: Any) -> Settings:
        storage = (
            PostgresStorage(driver="postgres", database_url=SecretStr(database_url))
            if database_url
            else MemoryStorage(driver="memory")
        )
        return Settings(
            environment="test",
            storage=storage,
            auth=AuthSettings(issuer=ISSUER, audience=AUDIENCE, public_key_file=signing_key.public_file),
            log_format="console",
            **overrides,
        )

    return make
