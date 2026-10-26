from uuid import UUID

from sqlalchemy import ColumnElement, Select, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from todo_api.shared.pagination import Page
from todo_api.todos.application.ports import Missing, Stale, TodoListQuery, TodoSortField, WriteResult, Written
from todo_api.todos.domain.todo import TodoItem
from todo_api.todos.infrastructure.tables import TodoRow, to_domain, to_values


class SqlTodoRepository:
    """One short transaction per call. Writes carry `version` in the WHERE clause: no read-then-write race."""

    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = sessions

    async def add(self, todo: TodoItem) -> None:
        async with self._sessions.begin() as session:
            session.add(TodoRow(**to_values(todo)))

    async def get(self, owner_id: str, todo_id: UUID) -> TodoItem | None:
        async with self._sessions() as session:
            row = await session.scalar(select(TodoRow).where(TodoRow.id == todo_id, TodoRow.owner_id == owner_id))
            return None if row is None else to_domain(row)

    async def list(self, query: TodoListQuery) -> Page[TodoItem]:
        filters = _filters(query)
        async with self._sessions() as session:
            total = await session.scalar(select(func.count()).select_from(TodoRow).where(*filters)) or 0
            rows = await session.scalars(
                _ordered(select(TodoRow).where(*filters), query).limit(query.page.limit).offset(query.page.offset)
            )
            return Page(
                items=[to_domain(row) for row in rows],
                total=total,
                limit=query.page.limit,
                offset=query.page.offset,
            )

    async def update(self, todo: TodoItem, expected_version: int) -> WriteResult:
        async with self._sessions.begin() as session:
            written = await session.scalar(
                update(TodoRow)
                .where(TodoRow.id == todo.id, TodoRow.owner_id == todo.owner_id, TodoRow.version == expected_version)
                .values(to_values(todo))
                .returning(TodoRow.version)
            )
            return Written() if written is not None else await _miss(session, todo.owner_id, todo.id)

    async def delete(self, owner_id: str, todo_id: UUID, expected_version: int) -> WriteResult:
        async with self._sessions.begin() as session:
            deleted = await session.scalar(
                delete(TodoRow)
                .where(TodoRow.id == todo_id, TodoRow.owner_id == owner_id, TodoRow.version == expected_version)
                .returning(TodoRow.id)
            )
            return Written() if deleted is not None else await _miss(session, owner_id, todo_id)


async def _miss(session: AsyncSession, owner_id: str, todo_id: UUID) -> WriteResult:
    current = await session.scalar(select(TodoRow.version).where(TodoRow.id == todo_id, TodoRow.owner_id == owner_id))
    return Missing() if current is None else Stale(current)


def _filters(query: TodoListQuery) -> list[ColumnElement[bool]]:
    filters = [TodoRow.owner_id == query.owner_id]
    if query.status is not None:
        filters.append(TodoRow.status == query.status)
    if query.search:
        filters.append(TodoRow.title.ilike(f"%{_escape_like(query.search)}%", escape="\\"))
    return filters


def _ordered(statement: Select[TodoRow], query: TodoListQuery) -> Select[TodoRow]:
    column = TodoRow.due_date if query.sort.field is TodoSortField.DUE_DATE else TodoRow.created_at
    key = column.desc() if query.sort.descending else column.asc()
    tie = TodoRow.id.desc() if query.sort.descending else TodoRow.id.asc()
    return statement.order_by(key.nulls_last(), tie)


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
