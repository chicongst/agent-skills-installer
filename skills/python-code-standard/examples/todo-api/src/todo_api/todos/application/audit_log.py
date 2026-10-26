import logging
from uuid import UUID

logger = logging.getLogger("todo_api.todos")


def todo_created(todo_id: UUID, owner_id: str) -> None:
    logger.info("todo.created", extra={"todo_id": str(todo_id), "owner_id": owner_id})


def todo_deleted(todo_id: UUID, owner_id: str) -> None:
    logger.info("todo.deleted", extra={"todo_id": str(todo_id), "owner_id": owner_id})


def version_conflict(todo_id: UUID, expected_version: int, current_version: int) -> None:
    logger.warning(
        "todo.version_conflict",
        extra={
            "todo_id": str(todo_id),
            "expected_version": expected_version,
            "current_version": current_version,
        },
    )
