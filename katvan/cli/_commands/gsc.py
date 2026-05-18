"""``katvan gsc`` — Google Search Console read-only verbs.

Subcommands:

* ``sitemaps`` — list submitted sitemaps and status.
* ``inspect <url>`` — single-URL inspection (Task 7).
* ``doctor`` — composite indexing-health audit (Task 9).

Wiring follows the existing one-file-per-verb pattern in this directory.
Subcommands dispatch through ``args.gsc_func``; the top-level ``cmd_gsc``
delegates to that handler, or prints the verb help when no subcommand is given.
"""
from __future__ import annotations

import argparse

from katvan.cli._errors import EXIT_USER_ERROR, KatvanError
from katvan.cli._output import emit_result
from katvan.gsc.client import build_client, site_url
from katvan.gsc.inspect import inspect_url
from katvan.gsc.sitemaps import list_sitemaps


# ----- subcommand handlers -----------------------------------------------------

def _cmd_sitemaps(args: argparse.Namespace) -> int:
    client = build_client()
    rows = list_sitemaps(client, site_url=site_url())
    json_mode = bool(getattr(args, "json", False))
    if json_mode:
        emit_result({"site": site_url(), "sitemaps": rows}, json_mode=True)
    else:
        if not rows:
            emit_result("(no sitemaps submitted)", json_mode=False)
        else:
            lines = []
            for row in rows:
                lines.append(
                    f"{row['path']}\t"
                    f"last_downloaded={row['last_downloaded'] or '-'}\t"
                    f"errors={row['errors']}\twarnings={row['warnings']}"
                )
            emit_result("\n".join(lines), json_mode=False)
    return 0


def _cmd_inspect(args: argparse.Namespace) -> int:
    client = build_client()
    result = inspect_url(client, url=args.url, site_url=site_url())
    json_mode = bool(getattr(args, "json", False))
    if json_mode:
        emit_result(result, json_mode=True)
    else:
        lines = [
            f"url: {result['url']}",
            f"verdict: {result['verdict']}",
            f"coverage_state: {result['coverage_state']}",
            f"last_crawl_time: {result['last_crawl_time'] or '-'}",
            f"robots_txt_state: {result['robots_txt_state']}",
            f"page_fetch_state: {result['page_fetch_state']}",
            f"google_canonical: {result['google_canonical'] or '-'}",
            f"user_canonical: {result['user_canonical'] or '-'}",
            f"mobile_usability: {result['mobile_usability'] or '-'}",
            f"rich_results: {result['rich_results'] or '-'}",
        ]
        emit_result("\n".join(lines), json_mode=False)
    return 0


# ----- top-level verb dispatch -------------------------------------------------

def cmd_gsc(args: argparse.Namespace) -> int:
    handler = getattr(args, "gsc_func", None)
    if handler is None:
        # No subcommand given. Argparse alone won't catch this because the
        # subparsers are optional (so `--help` works without crashing); we
        # raise a KatvanError instead of printing help to keep error
        # contract uniform.
        raise KatvanError(
            code=EXIT_USER_ERROR,
            message="missing gsc subcommand",
            remediation="run 'katvan gsc --help' to see subcommands",
        )
    return handler(args)


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "gsc",
        help="Google Search Console read-only verbs (sitemaps, inspect, doctor).",
    )
    p.set_defaults(func=cmd_gsc)
    p.add_argument("--json", action="store_true", help="Emit structured JSON.")

    gsub = p.add_subparsers(dest="gsc_command")

    # `sitemaps` subcommand.
    s = gsub.add_parser("sitemaps", help="List submitted sitemaps and status.")
    s.add_argument("--json", action="store_true", help="Emit structured JSON.")
    s.set_defaults(gsc_func=_cmd_sitemaps)

    # `inspect` subcommand.
    i = gsub.add_parser("inspect", help="Inspect a single URL's indexing status.")
    i.add_argument("url", help="The URL to inspect (must be under the verified property).")
    i.add_argument("--json", action="store_true", help="Emit structured JSON.")
    i.set_defaults(gsc_func=_cmd_inspect)
