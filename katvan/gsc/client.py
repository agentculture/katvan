"""Service-account auth and thin GSC API client wrapper.

Single source of truth for:

* The OAuth scope (read-only).
* Credentials loading from ``$KATVAN_GSC_CREDENTIALS``.
* The verified-property URL (``$KATVAN_GSC_SITE`` or the culture.dev default).
* Building the ``searchconsole v1`` discovery client.

All env-var problems raise :class:`KatvanError` with ``EXIT_ENV_ERROR`` so the
top-level dispatcher prints a clean ``error: … / hint: …`` pair instead of a
Python traceback.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable, TypeVar

from google.oauth2 import service_account
from googleapiclient import discovery
from googleapiclient.errors import HttpError

from katvan._errors import EXIT_ENV_ERROR, KatvanError

T = TypeVar("T")

SCOPE = "https://www.googleapis.com/auth/webmasters.readonly"
DEFAULT_SITE_URL = "https://culture.dev/"
_SETUP_HINT = "see docs/gsc-setup.md for the one-time setup steps"


def site_url() -> str:
    """Return the verified-property URL (env override or default).

    Always normalised to a trailing slash so consumers can do prefix
    matching without worrying about substring host confusion
    (e.g. ``https://culture.dev`` accepting ``https://culture.dev.evil.com/``).
    """
    raw = os.environ.get("KATVAN_GSC_SITE", DEFAULT_SITE_URL)
    return raw if raw.endswith("/") else raw + "/"


def build_client() -> Any:
    """Return a ``googleapiclient`` Resource for the Search Console v1 API.

    Raises :class:`KatvanError` (``EXIT_ENV_ERROR``) when the credentials env
    var is unset or the file is unreadable.
    """
    path_str = os.environ.get("KATVAN_GSC_CREDENTIALS")
    if not path_str:
        raise KatvanError(
            code=EXIT_ENV_ERROR,
            message="KATVAN_GSC_CREDENTIALS env var is not set",
            remediation=_SETUP_HINT,
        )
    if not Path(path_str).is_file():
        raise KatvanError(
            code=EXIT_ENV_ERROR,
            message=f"KATVAN_GSC_CREDENTIALS file not found: {path_str}",
            remediation=_SETUP_HINT,
        )
    creds = service_account.Credentials.from_service_account_file(
        path_str, scopes=[SCOPE]
    )
    return discovery.build(
        "searchconsole",
        "v1",
        credentials=creds,
        cache_discovery=False,
    )


def call_with_translation(action: Callable[[], T]) -> T:
    """Invoke a googleapiclient call and translate HttpError to KatvanError.

    401/403 -> EXIT_ENV_ERROR, "check the SA is granted on the GSC property"
    429    -> EXIT_ENV_ERROR, "rate-limited by GSC; retry later"
    other  -> EXIT_ENV_ERROR with the upstream message preserved

    We classify all HttpErrors as env-errors rather than internal: by the
    time we hit one, the credentials worked but the API call didn't, which
    almost always points at GSC-side configuration (property grant, quota,
    URL not under the property). Genuine internal bugs raise non-HttpError
    exceptions and continue to fall through to the dispatcher's
    EXIT_INTERNAL_ERROR path.
    """
    try:
        return action()
    except HttpError as exc:
        status = getattr(getattr(exc, "resp", None), "status", None)
        if status in (401, 403):
            raise KatvanError(
                code=EXIT_ENV_ERROR,
                message=f"GSC API rejected the request (HTTP {status})",
                remediation=(
                    "ensure the service account email is added as a user on the GSC "
                    "property; see docs/gsc-setup.md"
                ),
            ) from exc
        if status == 429:
            raise KatvanError(
                code=EXIT_ENV_ERROR,
                message="GSC API rate-limited the request (HTTP 429)",
                remediation="retry later or reduce request frequency",
            ) from exc
        raise KatvanError(
            code=EXIT_ENV_ERROR,
            message=f"GSC API error (HTTP {status or '?'}): {exc}",
            remediation="check GSC property configuration; see docs/gsc-setup.md",
        ) from exc
