from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from taskboard.todos.dependencies import Todos
from taskboard.todos.domain import TodoItem
from taskboard.todos.schemas import (
    CreateTodoRequest,
    ListTodosParams,
    TodoPageResponse,
    TodoResponse,
    UpdateTodoRequest,
)
from taskboard.web.auth import CurrentOwner
from taskboard.web.etag import expected_version, format_etag
from taskboard.web.problems import PROBLEM_JSON, ProblemResponse
from taskboard.web.rate_limit import limit_writes
from taskboard.web.strict_json import StrictJsonRoute

PREFIX = "/v1/todos"


def _problems(*statuses: int) -> dict[int | str, dict[str, Any]]:
    return {code: {"model": ProblemResponse, "content": {PROBLEM_JSON: {}}} for code in (401, 403, 422, *statuses)}


router = APIRouter(prefix=PREFIX, tags=["todos"], route_class=StrictJsonRoute, responses=_problems())
writes = [Depends(limit_writes)]
ExpectedVersion = Annotated[int, Depends(expected_version)]
WRITE_PROBLEMS = (400, 404, 412, 428, 429)


def _respond(response: Response, todo: TodoItem) -> TodoResponse:
    response.headers["ETag"] = format_etag(todo.version)
    return TodoResponse.from_domain(todo)


@router.post("", status_code=status.HTTP_201_CREATED, dependencies=writes, responses=_problems(400, 413, 415, 429))
async def create_todo(body: CreateTodoRequest, owner: CurrentOwner, todos: Todos, response: Response) -> TodoResponse:
    todo = await todos.create(owner, body.to_draft())
    response.headers["Location"] = f"{PREFIX}/{todo.id}"
    return _respond(response, todo)


@router.get("")
async def list_todos(
    params: Annotated[ListTodosParams, Query()], owner: CurrentOwner, todos: Todos
) -> TodoPageResponse:
    return TodoPageResponse.from_page(await todos.list(params.to_query(owner)))


@router.get("/{todo_id}", responses=_problems(404))
async def get_todo(todo_id: UUID, owner: CurrentOwner, todos: Todos, response: Response) -> TodoResponse:
    return _respond(response, await todos.get(owner, todo_id))


@router.patch("/{todo_id}", dependencies=writes, responses=_problems(*WRITE_PROBLEMS, 413, 415))
async def update_todo(
    todo_id: UUID,
    body: UpdateTodoRequest,
    version: ExpectedVersion,
    owner: CurrentOwner,
    todos: Todos,
    response: Response,
) -> TodoResponse:
    return _respond(response, await todos.update(owner, todo_id, version, body.to_changes()))


@router.post("/{todo_id}/complete", dependencies=writes, responses=_problems(*WRITE_PROBLEMS))
async def complete_todo(
    todo_id: UUID, version: ExpectedVersion, owner: CurrentOwner, todos: Todos, response: Response
) -> TodoResponse:
    return _respond(response, await todos.complete(owner, todo_id, version))


@router.post("/{todo_id}/reopen", dependencies=writes, responses=_problems(*WRITE_PROBLEMS))
async def reopen_todo(
    todo_id: UUID, version: ExpectedVersion, owner: CurrentOwner, todos: Todos, response: Response
) -> TodoResponse:
    return _respond(response, await todos.reopen(owner, todo_id, version))


@router.delete(
    "/{todo_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=writes, responses=_problems(*WRITE_PROBLEMS)
)
async def delete_todo(todo_id: UUID, version: ExpectedVersion, owner: CurrentOwner, todos: Todos) -> None:
    await todos.delete(owner, todo_id, version)
