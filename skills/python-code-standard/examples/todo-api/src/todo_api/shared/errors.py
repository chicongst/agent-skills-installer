from enum import StrEnum
from typing import Any


class ErrorKind(StrEnum):
    VALIDATION = "validation"
    NOT_FOUND = "not_found"
    VERSION_MISMATCH = "version_mismatch"


class DomainError(Exception):
    """An expected business failure. The web layer maps `kind` to an HTTP status in one place."""

    def __init__(
        self,
        kind: ErrorKind,
        code: str,
        message: str,
        *,
        field: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.kind = kind
        self.code = code
        self.message = message
        self.field = field
        self.details = details or {}
