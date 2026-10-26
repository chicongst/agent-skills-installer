import asyncio
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any

import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from taskboard.shared.identity import OWNER_ID_MAX_LENGTH
from taskboard.web.problems import ProblemError

_BEARER = HTTPBearer(auto_error=False, description="JWT access token; `sub` identifies the owner.")
_CHALLENGE = {"WWW-Authenticate": "Bearer"}


@dataclass(frozen=True, slots=True, kw_only=True)
class TokenSettings:
    issuer: str
    audience: str
    algorithms: Sequence[str]
    jwks_url: str | None = None
    public_key_file: Path | None = None


class TokenVerifier:
    """Verifies signature, `exp`, `iss` and `aud` with an explicit algorithm list. JWKS keys are cached by PyJWT."""

    def __init__(self, settings: TokenSettings) -> None:
        self._settings = settings
        self._jwks = jwt.PyJWKClient(settings.jwks_url, cache_keys=True, timeout=5) if settings.jwks_url else None
        self._static_key = settings.public_key_file.read_text() if settings.public_key_file else None

    async def verify(self, token: str) -> dict[str, Any]:
        key = await self._signing_key(token)
        claims: dict[str, Any] = jwt.decode(
            token,
            key,
            algorithms=list(self._settings.algorithms),
            audience=self._settings.audience,
            issuer=self._settings.issuer,
            leeway=30,
            options={"require": ["exp", "iss", "aud"]},
        )
        return claims

    async def _signing_key(self, token: str) -> Any:
        if self._jwks is not None:
            signing_key = await asyncio.to_thread(self._jwks.get_signing_key_from_jwt, token)
            return signing_key.key
        return self._static_key


async def current_owner(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_BEARER)],
) -> str:
    """Authenticated subject. No or bad token → 401; a valid token without a usable `sub` → 403.
    `sub` must be non-blank, unpadded and fit the owner column, so one user never maps to two owners.
    """
    if credentials is None:
        raise ProblemError(401, "A bearer token is required.", headers=_CHALLENGE)
    verifier: TokenVerifier = request.app.state.token_verifier
    try:
        claims = await verifier.verify(credentials.credentials)
    except jwt.PyJWTError as error:
        raise ProblemError(401, "The bearer token is invalid or expired.", headers=_CHALLENGE) from error
    subject = claims.get("sub")
    if (
        not isinstance(subject, str)
        or not subject
        or subject != subject.strip()
        or len(subject) > OWNER_ID_MAX_LENGTH
        or "\x00" in subject
    ):
        raise ProblemError(403, "The token does not identify a user.")
    return subject


CurrentOwner = Annotated[str, Depends(current_owner)]
