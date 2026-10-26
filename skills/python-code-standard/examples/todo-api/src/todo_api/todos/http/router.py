from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from todo_api.shared.pagination import PageRequest
from todo_api.todos.application.ports import TodoListQuery
from todo_api.todos.application.use_cases.complete_todo import CompleteTodoCommand
from todo_api.todos.application.use_cases.create_todo import CreateTodoCommand
from todo_api.todos.application.use_cases.delete_todo import DeleteTodoCommand
from todo_api.todos.application.use_cases.get_todo import GetTodoQuery
from todo_api.todos.application.use_cases.reopen_todo import ReopenTodoCommand
from todo_api.todos.application.use_cases.update_todo import UpdateTodoCommand
from todo_api.todos.domain.todo import TodoItem
from todo_api.todos.http.dependencies import (
    CompleteHandler,
    CreateHandler,
    DeleteHandler,
    GetHandler,
    ListHandler,
    ReopenHandler,
    UpdateHandler,
)
from todo_api.todos.http.schemas import (
    CreateTodoRequest,
    ListTodosParams,
    TodoPageResponse,
    TodoResponse,
    UpdateTodoRequest,
)
from todo_api.web.auth import CurrentOwner
from todo_api.web.etag import expected_version, format_etag
from todo_api.web.problems import PROBLEM_JSON, ProblemResponse
from todo_api.web.rate_limit import limit_writes
from todo_api.web.strict_json import StrictJsonRoute

PREFIX = "/v1/todos"


def _problems(*statuses: int) -> dict[int | str, dict[str, Any]]:
    return {code: {"model": ProblemResponse, "content": {PROBLEM_JSON: {}}} for code in (401, 403, 422, *statuses)}


router = APIRouter(prefix=PREFIX, tags=["todos"], route_class=StrictJsonRoute, responses=_problems())
writes = [Depends(limit_writes)]
ExpectedVersion = Annotated[int, Depends(expected_version)]


def _respond(response: Response, todo: TodoItem) -> TodoResponse:
    response.headers["ETag"] = format_etag(todo.version)
    return TodoResponse.from_domain(todo)


@router.post("", status_code=status.HTTP_201_CREATED, dependencies=writes, responses=_problems(400, 413, 415, 429))
async def create_todo(
    body: CreateTodoRequest, owner: CurrentOwner, handler: CreateHandler, response: Response
) -> TodoResponse:
    todo = await handler.handle(CreateTodoCommand(owner, body.to_draft()))
    response.headers["Location"] = f"{PREFIX}/{todo.id}"
    return _respond(response, todo)


@router.get("")
async def list_todos(
    params: Annotated[ListTodosParams, Query()], owner: CurrentOwner, handler: ListHandler
) -> TodoPageResponse:
    query = TodoListQuery(
        owner_id=owner,
        status=params.status,
        search=params.q,
        sort=params.to_sort(),
        page=PageRequest(limit=params.limit, offset=params.offset),
    )
    return TodoPageResponse.from_page(await handler.handle(query))


@router.get("/{todo_id}", responses=_problems(404))
async def get_todo(todo_id: UUID, owner: CurrentOwner, handler: GetHandler, response: Response) -> TodoResponse:
    return _respond(response, await handler.handle(GetTodoQuery(owner, todo_id)))


@router.patch("/{todo_id}", dependencies=writes, responses=_problems(400, 404, 412, 413, 415, 428, 429))
async def update_todo(
    todo_id: UUID,
    body: UpdateTodoRequest,
    version: ExpectedVersion,
    owner: CurrentOwner,
    handler: UpdateHandler,
    response: Response,
) -> TodoResponse:
    todo = await handler.handle(UpdateTodoCommand(owner, todo_id, version, body.to_changes()))
    return _respond(response, todo)


@router.post("/{todo_id}/complete", dependencies=writes, responses=_problems(400, 404, 412, 428, 429))
async def complete_todo(
    todo_id: UUID, version: ExpectedVersion, owner: CurrentOwner, handler: CompleteHandler, response: Response
) -> TodoResponse:
    return _respond(response, await handler.handle(CompleteTodoCommand(owner, todo_id, version)))


@router.post("/{todo_id}/reopen", dependencies=writes, responses=_problems(400, 404, 412, 428, 429))
async def reopen_todo(
    todo_id: UUID, version: ExpectedVersion, owner: CurrentOwner, handler: ReopenHandler, response: Response
) -> TodoResponse:
    return _respond(response, await handler.handle(ReopenTodoCommand(owner, todo_id, version)))


@router.delete(
    "/{todo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=writes,
    responses=_problems(400, 404, 412, 428, 429),
)
async def delete_todo(todo_id: UUID, version: ExpectedVersion, owner: CurrentOwner, handler: DeleteHandler) -> None:
    await handler.handle(DeleteTodoCommand(owner, todo_id, version))
