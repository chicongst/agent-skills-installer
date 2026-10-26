"""The HTTP contract. Every test runs once per storage backend through the parametrised `api` fixture."""

import asyncio
from datetime import timedelta
from typing import Any

import httpx2
import pytest

from tests.conftest import Api


def problem_code(response: httpx2.Response) -> str:
    assert response.headers["content-type"] == "application/problem+json"
    code: str = response.json()["code"]
    return code


async def test_post_valid_todo_returns_201_with_location_and_etag(api: Api) -> None:
    response = await api.send(
        "POST",
        "/v1/todos",
        json={"title": "Buy milk", "description": "2 litres", "priority": "high", "dueDate": "2026-03-01"},
    )

    body = response.json()
    assert response.status_code == 201
    assert response.headers["Location"] == f"/v1/todos/{body['id']}"
    assert response.headers["ETag"] == '"1"'
    assert (body["description"], body["priority"], body["dueDate"]) == ("2 litres", "high", "2026-03-01")
    assert (body["status"], body["version"], body["completedAt"]) == ("open", 1, None)


async def test_post_title_only_leaves_optional_fields_null(api: Api) -> None:
    body = (await api.send("POST", "/v1/todos", json={"title": "Just a title"})).json()

    assert (body["description"], body["dueDate"], body["priority"]) == (None, None, None)


@pytest.mark.parametrize(
    "body",
    [
        '{"title":"x","dueDate":"2026-02-30"}',
        '{"title":"x","dueDate":0}',
        '{"title":"x","dueDate":"2026-01-02T00:00:00"}',
        '{"title":"x","priority":"urgent"}',
        '{"title":"x","priority":1}',
        '{"title":"x","priority":"High"}',
        '{"title":123}',
        '{"title":"x","status":"done"}',
        '{"title":"x","due_date":"2026-01-02"}',
        '{"description":"no title"}',
        "[]",
    ],
)
async def test_post_invalid_body_returns_422_with_field_errors(api: Api, body: str) -> None:
    response = await api.send("POST", "/v1/todos", content=body)

    assert response.status_code == 422
    assert problem_code(response) == "VALIDATION_FAILED"
    assert response.json()["errors"]


@pytest.mark.parametrize("body", ["{bad json", ""])
async def test_post_malformed_json_returns_400(api: Api, body: str) -> None:
    response = await api.send("POST", "/v1/todos", content=body)

    assert response.status_code == 400
    assert problem_code(response) == "MALFORMED_JSON"


@pytest.mark.parametrize("body", [b'\xef\xbb\xbf{"title":"x"}', b'{"title":"a\\ud800b"}', b"[" * 300 + b"]" * 300])
async def test_post_json_python_accepts_but_pydantic_rejects_returns_400(api: Api, body: bytes) -> None:
    response = await api.send("POST", "/v1/todos", content=body)

    assert response.status_code == 400
    assert problem_code(response) == "MALFORMED_JSON"


async def test_post_unknown_snake_case_key_is_reported_as_sent(api: Api) -> None:
    response = await api.send("POST", "/v1/todos", content='{"title":"a","due_date":"2026-01-01"}')

    assert response.status_code == 422
    assert "due_date" in response.json()["errors"]


async def test_anonymous_write_is_refused_before_the_body_is_read(api: Api) -> None:
    response = await api.send("POST", "/v1/todos", content='{"x":1}', anonymous=True)

    assert response.status_code == 401
    assert "errors" not in response.json()


async def test_post_duplicate_key_returns_400_duplicate_key(api: Api) -> None:
    response = await api.send("POST", "/v1/todos", content='{"title":"a","title":"b"}')

    assert response.status_code == 400
    assert problem_code(response) == "DUPLICATE_KEY"


async def test_post_non_json_content_type_returns_415(api: Api) -> None:
    response = await api.send("POST", "/v1/todos", content='{"title":"x"}', headers={"Content-Type": "text/plain"})

    assert response.status_code == 415
    assert problem_code(response) == "UNSUPPORTED_MEDIA_TYPE"


@pytest.mark.parametrize(
    ("body", "status"),
    [
        ({"title": "x" * 200}, 201),
        ({"title": "x" * 201}, 422),
        ({"title": "x", "description": "d" * 5000}, 201),
        ({"title": "x", "description": "d" * 5001}, 422),
        ({"title": "a\u0000b"}, 422),
        ({"title": "x", "description": "nul \u0000 here"}, 422),
    ],
)
async def test_post_boundary_and_hostile_strings_return_expected_status(
    api: Api, body: dict[str, str], status: int
) -> None:
    response = await api.send("POST", "/v1/todos", json=body)

    assert response.status_code == status, response.text


async def test_post_blank_title_returns_422_for_that_field(api: Api) -> None:
    response = await api.send("POST", "/v1/todos", json={"title": "   "})

    assert response.status_code == 422
    assert list(response.json()["errors"]) == ["title"]


async def test_request_without_token_returns_401_with_challenge(api: Api) -> None:
    response = await api.send("GET", "/v1/todos", anonymous=True)

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
    assert problem_code(response) == "UNAUTHORIZED"


@pytest.mark.parametrize("claims", [{"aud": "another-api"}, {"iss": "https://evil.test"}])
async def test_request_with_wrong_audience_or_issuer_returns_401(api: Api, claims: dict[str, Any]) -> None:
    token = api.signing_key.token(api.owner, **claims)

    response = await api.client.get("/v1/todos", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
    assert problem_code(response) == "UNAUTHORIZED"


async def test_request_with_expired_token_returns_401(api: Api) -> None:
    token = api.signing_key.token(api.owner, lifetime=timedelta(minutes=-5))

    response = await api.client.get("/v1/todos", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401


@pytest.mark.parametrize("subject", [None, "", "   ", " user-alex", "u" * 129, "a\u0000b"])
async def test_request_with_unusable_subject_returns_403(api: Api, subject: str | None) -> None:
    token = api.signing_key.token(subject)

    response = await api.client.get("/v1/todos", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403
    assert problem_code(response) == "FORBIDDEN"


async def test_get_own_todo_returns_200_with_etag(api: Api) -> None:
    url = await api.create(title="Mine")

    response = await api.send("GET", url)

    assert (response.status_code, response.headers["ETag"], response.json()["title"]) == (200, '"1"', "Mine")


async def test_get_another_users_todo_returns_404(api: Api) -> None:
    url = await api.create(title="Private")

    response = await api.send("GET", url, owner="user-someone-else")

    assert response.status_code == 404
    assert problem_code(response) == "TODO_NOT_FOUND"


@pytest.mark.parametrize(("method", "suffix"), [("PATCH", ""), ("DELETE", ""), ("POST", "/complete")])
async def test_write_another_users_todo_returns_404(api: Api, method: str, suffix: str) -> None:
    url = await api.create()

    response = await api.send(
        method,
        f"{url}{suffix}",
        json={"title": "x"} if method == "PATCH" else None,
        if_match='"1"',
        owner="user-mallory",
    )

    assert response.status_code == 404
    assert problem_code(response) == "TODO_NOT_FOUND"


async def test_get_malformed_id_returns_422(api: Api) -> None:
    response = await api.send("GET", "/v1/todos/not-a-uuid")

    assert response.status_code == 422
    assert "todoId" in response.json()["errors"]


async def test_list_filters_by_status(api: Api) -> None:
    done_url = await api.create(title="Done one")
    await api.create(title="Open one")
    await api.send("POST", f"{done_url}/complete", if_match='"1"')

    done = (await api.send("GET", "/v1/todos?status=done")).json()
    still_open = (await api.send("GET", "/v1/todos?status=open")).json()

    assert [item["title"] for item in done["items"]] == ["Done one"]
    assert [item["title"] for item in still_open["items"]] == ["Open one"]


async def test_list_searches_title_case_insensitively_and_sorts_by_due_date_nulls_last(api: Api) -> None:
    await api.create(title="Milk later", dueDate="2026-03-01")
    await api.create(title="MILK soon", dueDate="2026-02-01")
    await api.create(title="Milk someday")
    await api.create(title="Bread", description="milk in the description does not match")

    page = (await api.send("GET", "/v1/todos?q=milk&sort=dueDate&limit=10")).json()

    assert page["total"] == 3
    assert [item["title"] for item in page["items"]] == ["MILK soon", "Milk later", "Milk someday"]


async def test_list_descending_due_date_still_puts_nulls_last(api: Api) -> None:
    await api.create(title="No date")
    await api.create(title="Early", dueDate="2026-02-01")
    await api.create(title="Late", dueDate="2026-03-01")

    page = (await api.send("GET", "/v1/todos?sort=-dueDate")).json()

    assert [item["title"] for item in page["items"]] == ["Late", "Early", "No date"]


async def test_list_default_sort_is_newest_created_first(api: Api) -> None:
    for number in range(3):
        await api.create(title=f"Task {number}")

    ascending = (await api.send("GET", "/v1/todos?sort=createdAt")).json()
    default = (await api.send("GET", "/v1/todos")).json()

    assert [item["title"] for item in ascending["items"]] == ["Task 0", "Task 1", "Task 2"]
    assert [item["title"] for item in default["items"]] == ["Task 2", "Task 1", "Task 0"]


async def test_list_paginates_with_total(api: Api) -> None:
    for number in range(3):
        await api.create(title=f"Task {number}")

    page = (await api.send("GET", "/v1/todos?sort=createdAt&limit=2&offset=2")).json()

    assert (page["total"], page["limit"], page["offset"]) == (3, 2, 2)
    assert [item["title"] for item in page["items"]] == ["Task 2"]


async def test_list_only_shows_the_callers_todos(api: Api) -> None:
    await api.create(title="Mine")
    await api.send("POST", "/v1/todos", json={"title": "Theirs"}, owner="user-other")

    page = (await api.send("GET", "/v1/todos")).json()

    assert [item["title"] for item in page["items"]] == ["Mine"]


@pytest.mark.parametrize("q", ["%", "_", "\\"])
async def test_list_search_treats_wildcards_literally(api: Api, q: str) -> None:
    await api.create(title=f"Literal {q} here")
    await api.create(title="Butter")

    page = (await api.client.get("/v1/todos", params={"q": q}, headers=api.auth())).json()

    assert [item["title"] for item in page["items"]] == [f"Literal {q} here"]


@pytest.mark.parametrize(
    "query",
    [
        "limit=101",
        "limit=0",
        "limit=abc",
        "offset=-1",
        "offset=10001",
        "offset=9223372036854775808",
        "status=archived",
        "sort=title",
        "q=",
        "q=%00",
        "colour=red",
    ],
)
async def test_list_invalid_query_returns_422(api: Api, query: str) -> None:
    response = await api.send("GET", f"/v1/todos?{query}")

    assert response.status_code == 422
    assert problem_code(response) == "VALIDATION_FAILED"


@pytest.mark.parametrize(
    ("if_match", "status", "code"),
    [
        (None, 428, "PRECONDITION_REQUIRED"),
        ("*", 428, "PRECONDITION_REQUIRED"),
        ('W/"1"', 412, "VERSION_MISMATCH"),
        ("1", 400, "INVALID_IF_MATCH"),
        ('"1", "2"', 400, "INVALID_IF_MATCH"),
    ],
)
async def test_write_with_unusable_if_match_is_rejected(api: Api, if_match: str | None, status: int, code: str) -> None:
    url = await api.create()

    response = await api.send("PATCH", url, json={"title": "x"}, if_match=if_match)

    assert response.status_code == status
    assert problem_code(response) == code


async def test_patch_with_stale_etag_returns_412_with_current_version(api: Api) -> None:
    url = await api.create()
    await api.send("PATCH", url, json={"title": "First"}, if_match='"1"')

    response = await api.send("PATCH", url, json={"title": "Second"}, if_match='"1"')

    assert response.status_code == 412
    assert problem_code(response) == "VERSION_MISMATCH"
    assert response.json()["currentVersion"] == 2
    assert (await api.send("GET", url)).json()["title"] == "First"


async def test_patch_ten_concurrent_writers_with_same_etag_exactly_one_wins(api: Api) -> None:
    url = await api.create()

    responses = await asyncio.gather(
        *(api.send("PATCH", url, json={"title": f"Writer {n}"}, if_match='"1"') for n in range(10))
    )

    assert sorted(response.status_code for response in responses) == [200] + [412] * 9
    assert (await api.send("GET", url)).json()["version"] == 2


async def test_patch_with_current_values_is_a_no_op(api: Api) -> None:
    url = await api.create(priority="low")

    response = await api.send("PATCH", url, json={"title": "Buy milk", "priority": "low"}, if_match='"1"')

    assert (response.status_code, response.headers["ETag"], response.json()["version"]) == (200, '"1"', 1)


async def test_patch_partial_update_changes_only_sent_fields(api: Api) -> None:
    url = await api.create(description="2 litres", priority="low", dueDate="2026-03-01")

    response = await api.send("PATCH", url, json={"description": None, "priority": "high"}, if_match='"1"')

    todo = response.json()
    assert (response.status_code, response.headers["ETag"]) == (200, '"2"')
    assert (todo["title"], todo["description"], todo["priority"], todo["dueDate"]) == (
        "Buy milk",
        None,
        "high",
        "2026-03-01",
    )


@pytest.mark.parametrize(
    ("body", "field"),
    [
        ('{"title":null}', "title"),
        ("{}", "body"),
        ('{"priority":"medium,high"}', "priority"),
        ('{"dueDate":1}', "dueDate"),
    ],
)
async def test_patch_invalid_change_reports_the_field(api: Api, body: str, field: str) -> None:
    url = await api.create()

    response = await api.send("PATCH", url, content=body, if_match='"1"')

    assert response.status_code == 422
    assert problem_code(response) == "VALIDATION_FAILED"
    assert field in response.json()["errors"]


async def test_complete_twice_second_call_is_a_no_op(api: Api) -> None:
    url = await api.create()

    first = await api.send("POST", f"{url}/complete", if_match='"1"')
    repeat = await api.send("POST", f"{url}/complete", if_match='"2"')

    assert (first.json()["status"], first.json()["completedAt"] is not None) == ("done", True)
    assert (repeat.status_code, repeat.headers["ETag"]) == (200, '"2"')


async def test_complete_without_if_match_returns_428_linking_rfc_6585(api: Api) -> None:
    url = await api.create()

    response = await api.send("POST", f"{url}/complete")

    assert response.status_code == 428
    assert "rfc6585" in response.json()["type"]


async def test_reopen_clears_completion(api: Api) -> None:
    url = await api.create()
    await api.send("POST", f"{url}/complete", if_match='"1"')

    todo = (await api.send("POST", f"{url}/reopen", if_match='"2"')).json()

    assert (todo["status"], todo["completedAt"], todo["version"]) == ("open", None, 3)


async def test_delete_with_current_version_returns_204_then_404(api: Api) -> None:
    url = await api.create()

    deleted = await api.send("DELETE", url, if_match='"1"')
    after = await api.send("GET", url)

    assert deleted.status_code == 204
    assert after.status_code == 404


async def test_delete_with_stale_version_returns_412_and_keeps_the_todo(api: Api) -> None:
    url = await api.create()

    response = await api.send("DELETE", url, if_match='"5"')

    assert (response.status_code, response.json()["currentVersion"]) == (412, 1)
    assert (await api.send("GET", url)).status_code == 200


async def test_unknown_route_returns_404_problem(api: Api) -> None:
    response = await api.send("GET", "/v1/nope")

    assert response.status_code == 404
    assert problem_code(response) == "NOT_FOUND"


async def test_wrong_method_returns_405_problem(api: Api) -> None:
    response = await api.send("PUT", "/v1/todos")

    assert response.status_code == 405
    assert problem_code(response) == "METHOD_NOT_ALLOWED"


@pytest.mark.parametrize("path", ["/health/live", "/health/ready"])
async def test_health_endpoints_are_anonymous(api: Api, path: str) -> None:
    response = await api.send("GET", path, anonymous=True)

    assert (response.status_code, response.json()) == (200, {"status": "ok"})


async def test_openapi_is_closed_by_default(api: Api) -> None:
    response = await api.send("GET", "/openapi.json", anonymous=True)

    assert response.status_code == 404
