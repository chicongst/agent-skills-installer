import re
from typing import Annotated

from fastapi import Header

from taskboard.web.problems import ProblemError

_STRONG = re.compile(r'^"([1-9][0-9]{0,9})"$')


def format_etag(version: int) -> str:
    return f'"{version}"'


def expected_version(if_match: Annotated[str | None, Header(alias="If-Match")] = None) -> int:
    """Writes require the version the client last read. Missing or `*` → 428, weak → 412, malformed → 400."""
    value = (if_match or "").strip()
    if not value or value == "*":
        raise ProblemError(428, 'Send If-Match with the ETag you last read, e.g. If-Match: "3".')
    if value.startswith("W/"):
        raise ProblemError(412, "Weak ETags cannot be used for writes.")
    match = _STRONG.match(value)
    if match is None:
        raise ProblemError(400, 'If-Match must be a quoted version, e.g. "3".', code="INVALID_IF_MATCH")
    return int(match.group(1))
