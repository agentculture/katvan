"""Real unit tests for :mod:`katvan.frontmatter`.

The librarian skill's ``_frontmatter.py`` never had unit tests — porting it
into katvan is the chance to lock its behaviour down. These tests exercise
the non-clobbering merge, title/permalink/nav_order derivation, the
byte-for-byte body guarantee (incl. CRLF), and the malformed-opener warning.
"""

from __future__ import annotations

import io
import subprocess
import sys

import pytest

from katvan.frontmatter import (
    build_permalink,
    derive_nav_order,
    derive_title,
    inject,
    main,
    parse_frontmatter_keys,
    render_value,
    split_frontmatter,
)

# --- inject(): the non-clobbering merge ------------------------------------


def test_inject_adds_defaults_to_bare_doc() -> None:
    text = "# Hello World\n\nSome body text.\n"
    out, warnings = inject(text, repo="ghafi", rel_path="guides/intro.md")
    assert warnings == []
    assert out.startswith("---\n")
    assert "title: Hello World" in out
    assert "sites: [culture]" in out
    assert "permalink: /ghafi/guides/intro/" in out
    # Body preserved verbatim after the closing fence.
    assert out.endswith("\n# Hello World\n\nSome body text.\n")


def test_inject_does_not_clobber_existing_keys() -> None:
    text = (
        "---\n"
        "title: Custom Title\n"
        "sites: [culture, agentirc]\n"
        "permalink: /custom/path/\n"
        "---\n"
        "# Different H1\n\nbody\n"
    )
    out, warnings = inject(text, repo="ghafi", rel_path="x.md")
    assert warnings == []
    # Existing values survive verbatim; no derived overrides appended.
    assert "title: Custom Title" in out
    assert "sites: [culture, agentirc]" in out
    assert "permalink: /custom/path/" in out
    assert "Different H1" not in out.split("---\n")[1]  # not in frontmatter
    assert out.count("title:") == 1
    assert out.count("permalink:") == 1
    assert out.count("sites:") == 1


def test_inject_no_h1_omits_title() -> None:
    text = "Just a paragraph, no heading.\n"
    out, warnings = inject(text, repo="zehut", rel_path="notes.md")
    assert warnings == []
    assert "title:" not in out.split("\n---\n")[0]
    # sites + permalink still injected.
    assert "sites: [culture]" in out
    assert "permalink: /zehut/notes/" in out


def test_inject_nav_order_from_numeric_prefix() -> None:
    text = "# Chapter\n\nbody\n"
    out, _ = inject(text, repo="ghafi", rel_path="03-chapter.md")
    assert "nav_order: 3" in out


def test_inject_no_nav_order_without_numeric_prefix() -> None:
    text = "# Chapter\n\nbody\n"
    out, _ = inject(text, repo="ghafi", rel_path="chapter.md")
    assert "nav_order:" not in out


def test_inject_body_is_byte_for_byte_with_crlf() -> None:
    # CRLF body must survive untouched — split/join would normalise it.
    body = "# Title\r\n\r\nLine one\r\nLine two\r\n"
    text = "---\r\ntitle: keep\r\n---\r\n" + body
    out, warnings = inject(text, repo="ghafi", rel_path="x.md")
    assert warnings == []
    assert out.endswith(body)


def test_inject_malformed_opener_warns_and_treats_as_body() -> None:
    text = "---\ntitle: no closing fence\n\n# Heading\n\nbody\n"
    out, warnings = inject(text, repo="ghafi", rel_path="broken.md")
    assert len(warnings) == 1
    assert "no closing fence" in warnings[0]
    assert "broken.md" in warnings[0]
    # Whole input treated as body — original text appears verbatim after fence.
    assert out.endswith(text)


# --- the individual derivation helpers -------------------------------------


def test_split_frontmatter_no_block() -> None:
    fm, body, warning = split_frontmatter("just body\n")
    assert fm == []
    assert body == "just body\n"
    assert warning is None


def test_split_frontmatter_extracts_block() -> None:
    fm, body, warning = split_frontmatter("---\nkey: val\n---\nbody here\n")
    assert fm == ["key: val"]
    assert body == "body here\n"
    assert warning is None


def test_parse_frontmatter_keys_shallow() -> None:
    lines = ["title: x", "  nested: y", "- listitem", "# comment", "sites: [a]"]
    assert parse_frontmatter_keys(lines) == {"title", "sites"}


def test_derive_title_first_h1_only() -> None:
    assert derive_title("# First\n\n# Second\n") == "First"
    assert derive_title("no heading here\n") is None


def test_derive_nav_order_strips_leading_zeros() -> None:
    assert derive_nav_order("01-intro.md") == 1
    assert derive_nav_order("10_advanced.md") == 10
    assert derive_nav_order("plain.md") is None


def test_build_permalink_trailing_slash() -> None:
    assert build_permalink("ghafi", "guides/intro.md") == "/ghafi/guides/intro/"
    assert build_permalink("ghafi", "index.md") == "/ghafi/index/"


def test_render_value_quotes_risky_titles() -> None:
    assert render_value("title", "Plain Title") == "title: Plain Title"
    assert render_value("title", "Has: colon").startswith('title: "Has: colon"')
    assert render_value("sites", ["culture", "agentirc"]) == "sites: [culture, agentirc]"
    assert render_value("nav_order", 4) == "nav_order: 4"


# --- the module CLI shim still works ---------------------------------------


def test_module_cli_roundtrips_via_stdin() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "katvan.frontmatter", "--repo", "ghafi", "--rel-path", "x.md"],
        input="# Hi\n\nbody\n",
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout.startswith("---\n")
    assert "title: Hi" in result.stdout
    assert result.stdout.endswith("\n# Hi\n\nbody\n")


# --- in-process main() tests (no subprocess, so pytest-cov instruments) ---


def test_main_function_roundtrips_stdin_to_stdout(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO("# Hi\n\nbody\n"))
    rc = main(["--repo", "ghafi", "--rel-path", "x.md"])
    assert rc == 0
    captured = capsys.readouterr()
    assert captured.out.startswith("---\n")
    assert "title: Hi" in captured.out
    assert captured.out.endswith("\n# Hi\n\nbody\n")
    assert captured.err == ""


def test_main_function_warns_to_stderr_on_malformed_opener(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO("---\ntitle: no close\n\nbody\n"))
    rc = main(["--repo", "ghafi", "--rel-path", "bad.md"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "no closing fence" in captured.err
    assert "bad.md" in captured.err


def test_main_function_requires_repo_argument() -> None:
    with pytest.raises(SystemExit):
        main(["--rel-path", "x.md"])


def test_module_cli_warns_on_malformed_opener_to_stderr() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "katvan.frontmatter", "--repo", "ghafi", "--rel-path", "bad.md"],
        input="---\ntitle: no close\n\nbody\n",
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "no closing fence" in result.stderr
    assert "bad.md" in result.stderr
