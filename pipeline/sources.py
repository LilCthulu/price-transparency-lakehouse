"""Load the source config and pick each source's one file link from its saved or live page HTML."""
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit

import yaml
from bs4 import BeautifulSoup

from pipeline import settings


@dataclass(frozen=True)
class Source:
    source_id: str
    display_name: str
    system: str
    format: str
    page_url: str
    match_on: str
    pattern: str


@dataclass(frozen=True)
class LinkResult:
    source_id: str
    file_url: str | None  # full URL, may hold a token: use only for the download, never store it
    error: str | None


def load_sources(path: Path = settings.SOURCES_FILE) -> list[Source]:
    cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
    return [
        Source(
            source_id=s["source_id"],
            display_name=s["display_name"],
            system=s["system"],
            format=s["format"],
            page_url=cfg["pages"][s["system"]],
            match_on=s["match"]["field"],
            pattern=s["match"]["pattern"],
        )
        for s in cfg["sources"]
    ]


def strip_query(url: str) -> str:
    """The form safe to log or store: TriStar's query string holds a SAS token."""
    return urlunsplit(urlsplit(url)._replace(query="", fragment=""))


def select_link(source: Source, html: str) -> LinkResult:
    """Zero or several distinct matches come back as a recorded error, so one bad source cannot stop the run."""
    rx = re.compile(source.pattern)
    urls: list[str] = []
    for a in BeautifulSoup(html, "html.parser").find_all("a", href=True):
        text = a.get_text(" ", strip=True) if source.match_on == "label" else a["href"]
        url = urljoin(source.page_url, a["href"].strip())
        if rx.search(text) and url not in urls:
            urls.append(url)
    if len(urls) == 1:
        return LinkResult(source.source_id, urls[0], None)
    shown = [strip_query(u) for u in urls[:3]]
    return LinkResult(source.source_id, None, f"expected 1 link, found {len(urls)}: {shown}")
