"""Unit tests for :mod:`katvan.cli._output`."""

from __future__ import annotations

import io
import json

from katvan.cli._errors import EXIT_USER_ERROR, KatvanError
from katvan.cli._output import emit_diagnostic, emit_error, emit_result


# --- emit_result -----------------------------------------------------------


def test_emit_result_text_adds_trailing_newline() -> None:
    buf = io.StringIO()
    emit_result("hello", json_mode=False, stream=buf)
    assert buf.getvalue() == "hello\n"


def test_emit_result_text_does_not_double_newline() -> None:
    buf = io.StringIO()
    emit_result("hello\n", json_mode=False, stream=buf)
    assert buf.getvalue() == "hello\n"


def test_emit_result_json_dumps_payload() -> None:
    buf = io.StringIO()
    emit_result({"ok": True, "n": 3}, json_mode=True, stream=buf)
    payload = json.loads(buf.getvalue())
    assert payload == {"ok": True, "n": 3}
    assert buf.getvalue().endswith("\n")


# --- emit_error ------------------------------------------------------------


def test_emit_error_text_writes_error_and_hint() -> None:
    buf = io.StringIO()
    err = KatvanError(code=EXIT_USER_ERROR, message="bad input", remediation="try again")
    emit_error(err, json_mode=False, stream=buf)
    text = buf.getvalue()
    assert text == "error: bad input\nhint: try again\n"


def test_emit_error_text_skips_hint_when_no_remediation() -> None:
    buf = io.StringIO()
    err = KatvanError(code=EXIT_USER_ERROR, message="bad input")
    emit_error(err, json_mode=False, stream=buf)
    assert buf.getvalue() == "error: bad input\n"


def test_emit_error_json_writes_structured_payload() -> None:
    buf = io.StringIO()
    err = KatvanError(code=EXIT_USER_ERROR, message="bad", remediation="fix")
    emit_error(err, json_mode=True, stream=buf)
    payload = json.loads(buf.getvalue())
    assert payload == {"code": EXIT_USER_ERROR, "message": "bad", "remediation": "fix"}
    assert buf.getvalue().endswith("\n")


# --- emit_diagnostic -------------------------------------------------------


def test_emit_diagnostic_adds_trailing_newline() -> None:
    buf = io.StringIO()
    emit_diagnostic("a message", stream=buf)
    assert buf.getvalue() == "a message\n"


def test_emit_diagnostic_preserves_existing_trailing_newline() -> None:
    buf = io.StringIO()
    emit_diagnostic("already terminated\n", stream=buf)
    assert buf.getvalue() == "already terminated\n"
