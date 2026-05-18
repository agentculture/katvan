"""Backward-compatibility shim.

The real definitions live at :mod:`katvan._errors`. This module exists so
existing imports (``from katvan.cli._errors import ...``) keep working.
"""
from katvan._errors import (
    EXIT_ENV_ERROR,
    EXIT_INTERNAL_ERROR,
    EXIT_SUCCESS,
    EXIT_USER_ERROR,
    KatvanError,
)

__all__ = [
    "EXIT_ENV_ERROR",
    "EXIT_INTERNAL_ERROR",
    "EXIT_SUCCESS",
    "EXIT_USER_ERROR",
    "KatvanError",
]
