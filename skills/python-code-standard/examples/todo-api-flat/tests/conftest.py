import uuid
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx2
import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import FastAPI

from taskboard.main import create_app
from taskboard.settings import AuthSettings, MemoryStorage, Settings

ISSUER = "https://issuer.test"
AUDIENCE = "taskboard"


@dataclass(frozen=True)
class SigningKey:
    private: rsa.RSAPrivateKey
    public_file: Path

    def token(self, subject: str | None, *, lifetime: timedelta = timedelta(minutes=5), **claims: Any) -> str:
        now = datetime.now(UTC)  # noqa: TID251 -- token expiry is checked by PyJWT against the real clock
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
    def make(**overrides: Any) -> Settings:
        return Settings(
            environment="test",
            storage=MemoryStorage(driver="memory"),
            auth=AuthSettings(issuer=ISSUER, audience=AUDIENCE, public_key_file=signing_key.public_file),
            log_format="console",
            **overrides,
        )

    return make


@dataclass
class Api:
    client: httpx2.AsyncClient
    app: FastAPI
    signing_key: SigningKey
    owner: str

    def auth(self, owner: str | None = None) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.signing_key.token(owner or self.owner)}"}

    async def send(
        self,
        method: str,
        url: str,
        *,
        json: Any = None,
        content: str | bytes | None = None,
        if_match: str | None = None,
        owner: str | None = None,
        anonymous: bool = False,
        headers: dict[str, str] | None = None,
    ) -> httpx2.Response:
        all_headers = {} if anonymous else self.auth(owner)
        if if_match is not None:
            all_headers["If-Match"] = if_match
        if content is not None:
            all_headers["Content-Type"] = "application/json"
        all_headers |= headers or {}
        return await self.client.request(method, url, json=json, content=content, headers=all_headers)

    async def create(self, **body: Any) -> str:
        response = await self.send("POST", "/v1/todos", json={"title": "Buy milk", **body})
        assert response.status_code == 201, response.text
        return response.headers["Location"]


async def open_api(app: FastAPI, signing_key: SigningKey) -> AsyncIterator[Api]:
    async with (
        app.router.lifespan_context(app),
        httpx2.AsyncClient(
            transport=httpx2.ASGITransport(app=app, raise_app_exceptions=False), base_url="http://test"
        ) as client,
    ):
        yield Api(client=client, app=app, signing_key=signing_key, owner=f"user-{uuid.uuid4().hex}")


@pytest.fixture(params=["memory"])
async def api(
    request: pytest.FixtureRequest, make_settings: SettingsFactory, signing_key: SigningKey
) -> AsyncIterator[Api]:
    """One param per storage backend; a database adapter adds its param here and the whole contract runs on it."""
    assert request.param == "memory"
    async for api in open_api(create_app(make_settings()), signing_key):
        yield api
