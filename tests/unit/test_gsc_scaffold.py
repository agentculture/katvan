"""Scaffold sanity: the gsc package imports and exposes its public surface."""
from __future__ import annotations


def test_gsc_package_imports() -> None:
    import katvan.gsc  # noqa: F401


def test_googleapiclient_dependency_available() -> None:
    import googleapiclient.discovery  # noqa: F401
    from google.oauth2 import service_account  # noqa: F401
