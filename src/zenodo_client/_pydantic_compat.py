"""A compatibility layer for pydantic 1 and 2."""

from pydantic import __version__ as pydantic_version

__all__ = [
    "PYDANTIC_V1",
    "field_validator",
]

PYDANTIC_V1 = pydantic_version.startswith("1.")

if PYDANTIC_V1:
    from pydantic import validator as field_validator
else:
    from pydantic import field_validator
