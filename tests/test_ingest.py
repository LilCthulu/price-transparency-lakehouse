"""Link selection against saved page snapshots. Never touches the network."""
from dataclasses import replace
from pathlib import Path

import pytest

from pipeline.sources import load_sources, select_link, strip_query

PAGES = Path(__file__).parent / "fixtures" / "pages"
SOURCES = load_sources()


def page(system: str) -> str:
    return (PAGES / f"{system}.html").read_text(encoding="utf-8", errors="replace")


def test_twelve_unique_sources():
    assert len(SOURCES) == 12
    assert len({s.source_id for s in SOURCES}) == 12


@pytest.mark.parametrize("source", SOURCES, ids=lambda s: s.source_id)
def test_exactly_one_link_of_expected_format(source):
    result = select_link(source, page(source.system))
    assert result.error is None
    assert strip_query(result.file_url).endswith(f".{source.format}")


def test_west_does_not_pick_up_midtown():
    west = next(s for s in SOURCES if s.source_id == "ascension_west")
    assert "620347580-1629025648" in select_link(west, page("ascension")).file_url


def test_midtown_does_not_pick_up_west():
    # Same file name stem as West; only the label and the second number in the name tell them apart.
    midtown = next(s for s in SOURCES if s.source_id == "ascension_midtown")
    assert "620347580-1780778969" in select_link(midtown, page("ascension")).file_url


def test_rutherford_duplicate_anchor_is_one_link():
    # The page lists the same file under Rutherford and Rutherford Westlawn.
    r = next(s for s in SOURCES if s.source_id == "ascension_rutherford")
    assert "620475842_saint-thomas-rutherford-hospital" in select_link(r, page("ascension")).file_url


def test_broken_pattern_records_error_instead_of_crashing():
    bad = replace(SOURCES[0], pattern="^no such hospital$")
    result = select_link(bad, page(bad.system))
    assert result.file_url is None
    assert "found 0" in result.error


def test_ambiguous_pattern_records_error():
    west = next(s for s in SOURCES if s.source_id == "ascension_west")
    result = select_link(replace(west, match_on="href", pattern="saint-thomas-west-hospital"), page("ascension"))
    assert result.file_url is None
    assert "found 2" in result.error


def test_strip_query_removes_token():
    assert strip_query("https://x.net/a.json?si=p&sig=secret") == "https://x.net/a.json"
