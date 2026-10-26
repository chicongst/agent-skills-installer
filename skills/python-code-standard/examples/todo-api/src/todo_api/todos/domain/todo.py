import unicodedata
from dataclasses import dataclass, replace
from datetime import date, datetime
from enum import StrEnum
from typing import Self
from uuid import UUID

from todo_api.shared.identity import OWNER_ID_MAX_LENGTH
from todo_api.shared.patch import UNSET, Patch
from todo_api.todos.domain.errors import TodoValidationError

TITLE_MAX_LENGTH = 200
DESCRIPTION_MAX_LENGTH = 5000


class TodoStatus(StrEnum):
    OPEN = "open"
    DONE = "done"


class TodoPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True, slots=True, kw_only=True)
class TodoDraft:
    title: str
    description: str | None = None
    due_date: date | None = None
    priority: TodoPriority | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class TodoChanges:
    title: Patch[str | None] = UNSET
    description: Patch[str | None] = UNSET
    due_date: Patch[date | None] = UNSET
    priority: Patch[TodoPriority | None] = UNSET

    @property
    def is_empty(self) -> bool:
        return all(value is UNSET for value in (self.title, self.description, self.due_date, self.priority))


@dataclass(frozen=True, slots=True, kw_only=True)
class TodoItem:
    """Immutable aggregate. Build it with `create`; a real change returns a new instance with the next version,
    a change that alters nothing returns `self`, so callers can skip the write.
    """

    id: UUID
    owner_id: str
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
    def create(cls, *, todo_id: UUID, owner_id: str, draft: TodoDraft, now: datetime) -> Self:
        if not owner_id.strip() or len(owner_id) > OWNER_ID_MAX_LENGTH:
            raise TodoValidationError("owner_id", "Owner is required.")
        return cls(
            id=todo_id,
            owner_id=owner_id,
            title=_valid_title(draft.title),
            description=_valid_description(draft.description),
            due_date=draft.due_date,
            priority=draft.priority,
            status=TodoStatus.OPEN,
            completed_at=None,
            version=1,
            created_at=now,
            updated_at=now,
        )

    def apply(self, changes: TodoChanges, now: datetime) -> Self:
        if changes.is_empty:
            raise TodoValidationError(None, "At least one field must be provided.")
        candidate = replace(
            self,
            title=self.title if changes.title is UNSET else _valid_title(changes.title),
            description=self.description if changes.description is UNSET else _valid_description(changes.description),
            due_date=self.due_date if changes.due_date is UNSET else changes.due_date,
            priority=self.priority if changes.priority is UNSET else changes.priority,
        )
        if candidate == self:
            return self
        return replace(candidate, version=self.version + 1, updated_at=now)

    def complete(self, now: datetime) -> Self:
        if self.status is TodoStatus.DONE:
            return self
        return replace(self, status=TodoStatus.DONE, completed_at=now, version=self.version + 1, updated_at=now)

    def reopen(self, now: datetime) -> Self:
        if self.status is TodoStatus.OPEN:
            return self
        return replace(self, status=TodoStatus.OPEN, completed_at=None, version=self.version + 1, updated_at=now)


def _valid_title(title: str | None) -> str:
    trimmed = _clean("title", title)
    if not trimmed:
        raise TodoValidationError("title", "Title is required.")
    if len(trimmed) > TITLE_MAX_LENGTH:
        raise TodoValidationError("title", f"Title must be at most {TITLE_MAX_LENGTH} characters.")
    return trimmed


def _valid_description(description: str | None) -> str | None:
    trimmed = _clean("description", description, multiline=True)
    if len(trimmed) > DESCRIPTION_MAX_LENGTH:
        raise TodoValidationError("description", f"Description must be at most {DESCRIPTION_MAX_LENGTH} characters.")
    return trimmed or None


_ALLOWED_IN_MULTILINE = frozenset("\n\t")


def _clean(field: str, value: str | None, *, multiline: bool = False) -> str:
    """Reject control and invisible format characters (NUL breaks PostgreSQL, ESC injects terminal sequences,
    zero-width spaces make a title look blank) so every backend stores the same, displayable text.
    """
    text = (value or "").strip()
    allowed = _ALLOWED_IN_MULTILINE if multiline else frozenset()
    if any(unicodedata.category(char) in {"Cc", "Cf"} and char not in allowed for char in text):
        raise TodoValidationError(field, "Must not contain control or invisible characters.")
    return text
