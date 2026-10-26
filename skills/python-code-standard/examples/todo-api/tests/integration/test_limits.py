from collections.abc import AsyncIterator

import pytest

from tests.conftest import SettingsFactory, SigningKey
from tests.integration.conftest import Api, open_api
from todo_api.main import create_app
from todo_api.todos.http import dependencies


@pytest.fixture
async def small_api(make_settings: SettingsFactory, signing_key: SigningKey) -> AsyncIterator[Api]:
    app = create_app(make_settings(max_body_bytes=1024, write_rate_limit="3/minute"))
    async for api in open_api(app, signing_key):
        yield api


async def test_body_over_the_limit_returns_413(small_api: Api) -> None:
    response = await small_api.send("POST", "/v1/todos", json={"title": "x", "description": "a" * 2000})

    assert response.status_code == 413
    assert response.json()["code"] == "PAYLOAD_TOO_LARGE"


async def test_streamed_body_over_the_limit_returns_413(small_api: Api) -> None:
    async def chunks() -> AsyncIterator[bytes]:
        yield b'{"title":"x","description":"'
        for _ in range(4):
            yield b"a" * 400
        yield b'"}'

    response = await small_api.client.post(
        "/v1/todos", content=chunks(), headers={**small_api.auth(), "Content-Type": "application/json"}
    )

    assert response.status_code == 413


async def test_writes_over_the_rate_limit_return_429_with_retry_after(small_api: Api) -> None:
    for _ in range(3):
        await small_api.create()

    response = await small_api.send("POST", "/v1/todos", json={"title": "One too many"})
    other_user = await small_api.send("POST", "/v1/todos", json={"title": "Fine"}, owner="user-other")

    assert response.status_code == 429
    assert int(response.headers["Retry-After"]) >= 1
    assert "rfc6585" in response.json()["type"]
    assert other_user.status_code == 201


async def test_reads_are_not_rate_limited(small_api: Api) -> None:
    responses = [await small_api.send("GET", "/v1/todos") for _ in range(5)]

    assert {response.status_code for response in responses} == {200}


async def test_unhandled_error_returns_500_without_leaking_details(small_api: Api) -> None:
    class Broken:
        clock = None

        @property
        def todos(self) -> object:
            msg = "connection string postgres://secret"
            raise RuntimeError(msg)

    small_api.app.dependency_overrides[dependencies._services] = Broken

    response = await small_api.send("GET", "/v1/todos")

    assert response.status_code == 500
    assert response.json()["code"] == "INTERNAL_ERROR"
    assert "secret" not in response.text
