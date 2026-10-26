import json
from collections.abc import Callable, Coroutine
from typing import Any

from fastapi import Request, Response
from fastapi.routing import APIRoute
from pydantic import BaseModel, ConfigDict, ValidationError

from taskboard.web.problems import ProblemError


class InputModel(BaseModel):
    """Base for request bodies. Unknown fields are errors; `StrictJsonRoute` adds strict types and duplicate keys."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class InvalidBodyError(Exception):
    def __init__(self, errors: dict[str, list[str]]) -> None:
        super().__init__("Request body is invalid.")
        self.errors = errors


class StrictJsonRoute(APIRoute):
    """FastAPI validates bodies in lax Python mode after `json.loads`: `true` may arrive as `"yes"`, `0` becomes
    1970-01-01, a duplicate key silently wins, and model-wide `strict=True` rejects every ISO date and enum.
    This route validates the raw bytes in strict JSON mode first. It is an extra pass, not a replacement:
    FastAPI's own validation still runs and is what rejects snake_case keys on alias models.
    """

    def get_route_handler(self) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        handler = super().get_route_handler()
        bodies = [param.field_info.annotation for param in self.dependant.body_params]
        model = bodies[0] if len(bodies) == 1 else None
        if not (isinstance(model, type) and issubclass(model, BaseModel)):
            return handler
        body_model: type[BaseModel] = model

        async def strict_handler(request: Request) -> Response:
            # FastAPI reads the body before dependencies run; refuse anonymous callers before parsing anything.
            # `CurrentOwner` still verifies the token afterwards.
            if "authorization" not in request.headers:
                raise ProblemError(401, "A bearer token is required.", headers={"WWW-Authenticate": "Bearer"})
            await validate_strict_json(request, body_model)
            return await handler(request)

        return strict_handler


async def validate_strict_json(request: Request, model: type[BaseModel]) -> None:
    media_type = request.headers.get("content-type", "").partition(";")[0].strip().lower()
    if media_type != "application/json":
        raise ProblemError(415, "Send the body as application/json.")
    raw = await request.body()
    try:
        json.loads(raw, object_pairs_hook=_reject_duplicate_keys)
    except _DuplicateKeyError as error:
        raise ProblemError(400, str(error), code="DUPLICATE_KEY") from error
    except ValueError as error:
        raise ProblemError(400, "Request body is not valid JSON.", code="MALFORMED_JSON") from error
    try:
        model.model_validate_json(raw, strict=True)
    except ValidationError as error:
        if any(item["type"] == "json_invalid" for item in error.errors()):
            # Bytes Python's json accepts but Pydantic's parser does not: BOM, lone surrogates, deep nesting.
            raise ProblemError(400, "Request body is not valid JSON.", code="MALFORMED_JSON") from error
        raise InvalidBodyError(field_errors(error)) from error


def field_errors(error: ValidationError) -> dict[str, list[str]]:
    errors: dict[str, list[str]] = {}
    for item in error.errors(include_url=False, include_input=False):
        path = ".".join(str(part) for part in item["loc"]) or "body"
        errors.setdefault(path, []).append(item["msg"])
    return errors


class _DuplicateKeyError(ValueError):
    pass


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            msg = f"Duplicate key {key!r} in the request body."
            raise _DuplicateKeyError(msg)
        result[key] = value
    return result
