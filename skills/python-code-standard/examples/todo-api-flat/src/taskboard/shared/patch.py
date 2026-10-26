from enum import Enum
from typing import Final, Literal


class Unset(Enum):
    """Marks a PATCH field the client did not send, as opposed to one it set to null."""

    UNSET = "UNSET"


UNSET: Final = Unset.UNSET

type Patch[T] = T | Literal[Unset.UNSET]
