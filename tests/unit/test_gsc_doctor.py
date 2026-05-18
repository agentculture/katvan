"""Tests for :mod:`katvan.gsc.doctor`."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from katvan.gsc.doctor import run_doctor

FIX = Path(__file__).resolve().parent.parent / "fixtures" / "gsc"


def _client_with_inspect_responses(by_url: dict[str, dict]) -> MagicMock:
    """Return a MagicMock whose .urlInspection().index().inspect(...).execute()
    returns the payload keyed by the inspectionUrl in the request body."""
    client = MagicMock()
    chain = client.urlInspection.return_value.index.return_value.inspect

    def fake_inspect(body: dict) -> MagicMock:
        execute = MagicMock()
        execute.execute.return_value = by_url[body["inspectionUrl"]]
        return execute

    chain.side_effect = fake_inspect
    return client


def test_run_doctor_all_pass_returns_empty_problems() -> None:
    passes = json.loads((FIX / "url-inspection-pass.json").read_text())
    urls = ["https://culture.dev/", "https://culture.dev/agex/"]
    client = _client_with_inspect_responses({u: passes for u in urls})
    with patch(
        "katvan.gsc.doctor.fetch_sitemap_urls", return_value=urls
    ):
        report = run_doctor(client, site_url="https://culture.dev/")
    assert report["summary"]["total"] == 2
    assert report["summary"]["problems"] == 0
    assert report["summary"]["errors"] == 0
    assert report["problems"] == []
    assert report["errors"] == []


def test_run_doctor_records_inspection_failures_in_errors_list() -> None:
    """One URL's inspect call raises — partial report still returns."""
    passes = json.loads((FIX / "url-inspection-pass.json").read_text())
    urls = ["https://culture.dev/", "https://culture.dev/boom/"]

    client = MagicMock()
    chain = client.urlInspection.return_value.index.return_value.inspect

    def fake_inspect(body: dict) -> MagicMock:
        execute = MagicMock()
        if body["inspectionUrl"] == urls[1]:
            execute.execute.side_effect = RuntimeError("quota exceeded")
        else:
            execute.execute.return_value = passes
        return execute

    chain.side_effect = fake_inspect

    with patch("katvan.gsc.doctor.fetch_sitemap_urls", return_value=urls):
        report = run_doctor(client, site_url="https://culture.dev/")

    assert report["summary"]["total"] == 2
    assert report["summary"]["problems"] == 0
    assert report["summary"]["errors"] == 1
    assert report["errors"][0]["url"] == urls[1]
    assert "quota exceeded" in report["errors"][0]["error"]


def test_run_doctor_groups_problems_by_class() -> None:
    passes = json.loads((FIX / "url-inspection-pass.json").read_text())
    not_indexed = json.loads((FIX / "url-inspection-not-indexed.json").read_text())
    crawl_err = json.loads((FIX / "url-inspection-crawl-error.json").read_text())
    urls = [
        "https://culture.dev/",
        "https://culture.dev/missing/",
        "https://culture.dev/broken/",
    ]
    responses = {
        urls[0]: passes,
        urls[1]: not_indexed,
        urls[2]: crawl_err,
    }
    client = _client_with_inspect_responses(responses)
    with patch("katvan.gsc.doctor.fetch_sitemap_urls", return_value=urls):
        report = run_doctor(client, site_url="https://culture.dev/")

    assert report["summary"]["total"] == 3
    assert report["summary"]["problems"] == 2
    problem_urls = {p["url"] for p in report["problems"]}
    assert urls[1] in problem_urls
    assert urls[2] in problem_urls
    # not_indexed: verdict != PASS → tagged not_indexed.
    # crawl_err:  verdict != PASS AND pageFetchState != SUCCESSFUL → tagged both.
    crawl_problem = next(p for p in report["problems"] if p["url"] == urls[2])
    assert "not_indexed" in crawl_problem["classes"]
    assert "crawl_errors" in crawl_problem["classes"]
