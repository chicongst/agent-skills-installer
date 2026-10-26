import uuid
from collections.abc import AsyncIterator, Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx2
import pytest
from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from testcontainers.community.postgres import PostgresContainer

from tests.conftest import SettingsFactory, SigningKey
from todo_api.main import create_app

ROOT = Path(__file__).parents[2]


@pytest.fixture(scope="session")
def postgres_url() -> Iterator[str]:
    """One container per run, migrated with the real Alembic scripts. Tests isolate by owner id, not truncation."""
    with PostgresContainer("postgres:17-alpine", driver="asyncpg") as postgres:
        url = postgres.get_connection_url()
        config = Config(ROOT / "alembic.ini")
        config.attributes["url"] = url
        with ThreadPoolExecutor(1) as thread:  # env.py calls asyncio.run; keep it off the test event loop
            thread.submit(command.upgrade, config, "head").result()
        yield url


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


@pytest.fixture(params=["memory", pytest.param("postgres", marks=pytest.mark.postgres)])
async def api(
    request: pytest.FixtureRequest, make_settings: SettingsFactory, signing_key: SigningKey
) -> AsyncIterator[Api]:
    database_url = request.getfixturevalue("postgres_url") if request.param == "postgres" else None
    async for api in open_api(create_app(make_settings(database_url=database_url)), signing_key):
        yield api
