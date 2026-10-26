import logging
from collections.abc import AsyncIterator

import pytest

from taskboard.main import create_app
from taskboard.todos import dependencies
from tests.conftest import Api, SettingsFactory, SigningKey, open_api


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
    assert response.json()["code"] == "PAYLOAD_TOO_LARGE"


async def test_writes_over_the_rate_limit_return_429_with_retry_after(small_api: Api) -> None:
    for _ in range(3):
        await small_api.create()

    response = await small_api.send("POST", "/v1/todos", json={"title": "One too many"})
    other_user = await small_api.send("POST", "/v1/todos", json={"title": "Fine"}, owner="user-other")

    assert response.status_code == 429
    assert response.json()["code"] == "TOO_MANY_REQUESTS"
    assert int(response.headers["Retry-After"]) >= 1
    assert other_user.status_code == 201


async def test_reads_are_not_rate_limited(small_api: Api) -> None:
    responses = [await small_api.send("GET", "/v1/todos") for _ in range(5)]

    assert {response.status_code for response in responses} == {200}


async def test_unhandled_error_returns_500_without_leaking_details(small_api: Api) -> None:
    class Broken:
        clock = None

        @property
        def todos(self) -> object:
            msg = "connection string with secret"
            raise RuntimeError(msg)

    small_api.app.dependency_overrides[dependencies._services] = Broken

    response = await small_api.send("GET", "/v1/todos")

    assert response.status_code == 500
    assert response.json()["code"] == "INTERNAL_ERROR"
    assert "secret" not in response.text


async def test_each_request_logs_one_line_with_route_template_and_status(
    small_api: Api, caplog: pytest.LogCaptureFixture
) -> None:
    url = await small_api.create()
    caplog.clear()

    with caplog.at_level(logging.INFO, logger="taskboard.http"):
        await small_api.send("GET", url)

    [record] = [r for r in caplog.records if r.getMessage() == "http.request"]
    assert (record.method, record.route, record.status) == ("GET", "/v1/todos/{todo_id}", 200)  # type: ignore[attr-defined]
    assert record.duration_ms >= 0  # type: ignore[attr-defined]
