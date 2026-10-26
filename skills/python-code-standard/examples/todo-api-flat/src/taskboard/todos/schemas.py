from datetime import date, datetime
from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from taskboard.shared.pagination import DEFAULT_LIMIT, MAX_LIMIT, MAX_OFFSET, Page, PageRequest
from taskboard.shared.patch import UNSET
from taskboard.todos.domain import TodoChanges, TodoDraft, TodoItem, TodoPriority, TodoStatus
from taskboard.todos.ports import TodoListQuery, TodoSort, TodoSortField
from taskboard.web.strict_json import InputModel


class CamelInput(InputModel):
    model_config = ConfigDict(alias_generator=to_camel)


class OutputModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, validate_by_name=True, serialize_by_alias=True, frozen=True)


class CreateTodoRequest(CamelInput):
    title: str
    description: str | None = None
    due_date: date | None = None
    priority: TodoPriority | None = None

    def to_draft(self) -> TodoDraft:
        return TodoDraft(title=self.title, description=self.description, due_date=self.due_date, priority=self.priority)


class UpdateTodoRequest(CamelInput):
    """Absent field = keep; `null` = clear. `model_fields_set` tells the two apart."""

    title: str | None = None
    description: str | None = None
    due_date: date | None = None
    priority: TodoPriority | None = None

    def to_changes(self) -> TodoChanges:
        sent = self.model_fields_set
        return TodoChanges(
            title=self.title if "title" in sent else UNSET,
            description=self.description if "description" in sent else UNSET,
            due_date=self.due_date if "due_date" in sent else UNSET,
            priority=self.priority if "priority" in sent else UNSET,
        )


_SORTS: dict[str, TodoSort] = {
    "createdAt": TodoSort(TodoSortField.CREATED_AT, descending=False),
    "-createdAt": TodoSort(TodoSortField.CREATED_AT, descending=True),
    "dueDate": TodoSort(TodoSortField.DUE_DATE, descending=False),
    "-dueDate": TodoSort(TodoSortField.DUE_DATE, descending=True),
}


class ListTodosParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: TodoStatus | None = None
    q: str | None = Field(default=None, min_length=1, max_length=200, pattern=r"^[^\x00]*$")
    sort: Literal["createdAt", "-createdAt", "dueDate", "-dueDate"] = "-createdAt"
    limit: int = Field(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT)
    offset: int = Field(default=0, ge=0, le=MAX_OFFSET)

    def to_query(self, owner_id: str) -> TodoListQuery:
        return TodoListQuery(
            owner_id=owner_id,
            status=self.status,
            search=self.q,
            sort=_SORTS[self.sort],
            page=PageRequest(limit=self.limit, offset=self.offset),
        )


class TodoResponse(OutputModel):
    id: UUID
    title: str
    description: str | None
    due_date: date | None
    priority: TodoPriority | None
    status: TodoStatus
    completed_at: datetime | None
    version: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, todo: TodoItem) -> Self:
        return cls(
            id=todo.id,
            title=todo.title,
            description=todo.description,
            due_date=todo.due_date,
            priority=todo.priority,
            status=todo.status,
            completed_at=todo.completed_at,
            version=todo.version,
            created_at=todo.created_at,
            updated_at=todo.updated_at,
        )


class TodoPageResponse(OutputModel):
    items: list[TodoResponse]
    total: int
    limit: int
    offset: int

    @classmethod
    def from_page(cls, page: Page[TodoItem]) -> Self:
        return cls(
            items=[TodoResponse.from_domain(todo) for todo in page.items],
            total=page.total,
            limit=page.limit,
            offset=page.offset,
        )
