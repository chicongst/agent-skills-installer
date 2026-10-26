from uuid import UUID

from todo_api.shared.errors import DomainError, ErrorKind


class TodoValidationError(DomainError):
    def __init__(self, field: str | None, message: str) -> None:
        """`field` is the aggregate attribute name (snake_case); None means the request as a whole."""
        super().__init__(ErrorKind.VALIDATION, "VALIDATION_FAILED", message, field=field)


class TodoNotFoundError(DomainError):
    def __init__(self, todo_id: UUID) -> None:
        super().__init__(ErrorKind.NOT_FOUND, "TODO_NOT_FOUND", f"Todo {todo_id} was not found.")


class VersionMismatchError(DomainError):
    def __init__(self, current_version: int) -> None:
        super().__init__(
            ErrorKind.VERSION_MISMATCH,
            "VERSION_MISMATCH",
            "Todo was modified by someone else; reload and retry.",
            details={"current_version": current_version},
        )
