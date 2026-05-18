"""Unified CLI entry point for katvan.

Top-level globals (``learn``, ``explain``) live under
:mod:`katvan.cli._commands` and are registered here. Per-noun groups
(``overview``, ``pull``, ``doctor`` — landing in a later release) will
register via their own ``register()`` functions following the same pattern.

Error propagation contract
--------------------------
Every handler raises :class:`katvan.cli._errors.KatvanError` on failure; the
top-level ``main()`` catches it via :func:`_dispatch` and routes through
:mod:`katvan.cli._output`. Unknown exceptions are wrapped into a
``KatvanError`` so no Python traceback leaks to stderr.

Argparse errors (unknown verb, missing required arg) also route through our
structured format — ``_KatvanArgumentParser`` overrides ``.error()``. The
subparsers are built with ``parser_class=_KatvanArgumentParser`` so subparser
errors follow the same path. Whether the error is emitted as text or JSON
depends on whether ``--json`` appears in the raw argv (:func:`main` sets
``_KatvanArgumentParser._json_hint`` before ``parse_args``).
"""

from __future__ import annotations

import argparse
import sys

from katvan import __version__
from katvan.cli._commands import doctor as _doctor_cmd
from katvan.cli._commands import explain as _explain_cmd
from katvan.cli._commands import gsc as _gsc_cmd
from katvan.cli._commands import learn as _learn_cmd
from katvan.cli._commands import overview as _overview_cmd
from katvan.cli._commands import pull as _pull_cmd
from katvan.cli._errors import EXIT_INTERNAL_ERROR, EXIT_USER_ERROR, KatvanError
from katvan.cli._output import emit_error


class _KatvanArgumentParser(argparse.ArgumentParser):
    """ArgumentParser that routes errors through :func:`emit_error`.

    Argparse's default error handler writes ``prog: error: <msg>`` to stderr
    and exits with code 2. That skips our KatvanError plumbing and — crucially
    — produces no ``hint:`` line, which would make katvan itself fail the
    rubric's error-propagation bundle. This subclass emits our structured
    error format instead and exits with :attr:`EXIT_USER_ERROR`.

    JSON mode: parse-time errors happen before ``args.json`` is populated, so
    we rely on a class-level ``_json_hint`` that :func:`main` pre-populates
    by scanning the raw argv for ``--json`` / ``--json=…``. Best-effort and
    shared across all subparser instances (argparse's subparser factory
    produces instances of the class but doesn't thread state).
    """

    _json_hint: bool = False

    def error(self, message: str) -> None:  # type: ignore[override]
        err = KatvanError(
            code=EXIT_USER_ERROR,
            message=message,
            remediation=f"run '{self.prog} --help' to see valid arguments",
        )
        emit_error(err, json_mode=type(self)._json_hint)
        raise SystemExit(err.code)


def _argv_has_json(argv: list[str] | None) -> bool:
    tokens = argv if argv is not None else sys.argv[1:]
    return any(t == "--json" or t.startswith("--json=") for t in tokens)


def _build_parser() -> argparse.ArgumentParser:
    parser = _KatvanArgumentParser(
        prog="katvan",
        description="katvan — maintain sibling-repo docs on the culture.dev site",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    # parser_class propagates to every subparser so their .error() routes
    # through _KatvanArgumentParser too. Without this, a bogus subcommand arg
    # would hit argparse's default error path (no hint: line, wrong code).
    sub = parser.add_subparsers(dest="command", parser_class=_KatvanArgumentParser)

    # Globals (top-level, not nested under a noun).
    _learn_cmd.register(sub)
    _explain_cmd.register(sub)
    _overview_cmd.register(sub)
    _pull_cmd.register(sub)
    _doctor_cmd.register(sub)
    _gsc_cmd.register(sub)

    return parser


def _dispatch(args: argparse.Namespace) -> int:
    """Invoke the registered handler and translate exceptions to exit codes.

    Handler protocol: a handler may return ``None`` (treated as success,
    exit 0) or an ``int`` (used directly as the exit code). Failures MUST
    raise :class:`KatvanError`; any other exception is wrapped into one so no
    Python traceback leaks.
    """
    json_mode = bool(getattr(args, "json", False))
    try:
        rc = args.func(args)
    except KatvanError as err:
        emit_error(err, json_mode=json_mode)
        return err.code
    except Exception as err:  # noqa: BLE001 - last-resort; wrap and route cleanly
        wrapped = KatvanError(
            code=EXIT_INTERNAL_ERROR,
            message=f"unexpected: {err.__class__.__name__}: {err}",
            remediation="file a bug at https://github.com/agentculture/katvan/issues",
        )
        emit_error(wrapped, json_mode=json_mode)
        return wrapped.code
    return rc if rc is not None else 0


def main(argv: list[str] | None = None) -> int:
    # Pre-parse peek so argparse-level errors honour --json.
    _KatvanArgumentParser._json_hint = _argv_has_json(argv)
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    return _dispatch(args)


if __name__ == "__main__":
    sys.exit(main())
