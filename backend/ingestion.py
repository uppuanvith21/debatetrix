from __future__ import annotations

import datetime as dt
import html
import re
from email.utils import parsedate_to_datetime

import requests
from bs4 import BeautifulSoup

from backend.fact_check_sources import FACT_CHECK_SOURCES, FactCheckSource

try:
    import feedparser
except ImportError:  # pragma: no cover - depends on local environment
    feedparser = None


HEADERS = {
    "User-Agent": "DebatetrixAI/1.0 (+local research dashboard; respects public feeds)",
    "Accept": "application/rss+xml, application/xml, text/html;q=0.8",
}


def _clean_text(value: str | None, limit: int = 420) -> str:
    if not value:
        return ""
    text = BeautifulSoup(value, "html.parser").get_text(" ", strip=True)
    text = html.unescape(re.sub(r"\s+", " ", text)).strip()
    return text[:limit]


def _parse_date(value: str | None) -> str:
    if not value:
        return ""
    try:
        return parsedate_to_datetime(value).strftime("%Y-%m-%d")
    except (TypeError, ValueError):
        return value[:80]


def _item_from_entry(source: FactCheckSource, entry: object) -> dict[str, object] | None:
    title = _clean_text(getattr(entry, "title", ""), 260)
    url = getattr(entry, "link", "")
    if not title or not url:
        return None
    published = getattr(entry, "published", "") or getattr(entry, "updated", "")
    return {
        "source_name": source.name,
        "source_region": source.region,
        "source_reliability": source.reliability,
        "title": title,
        "summary": _clean_text(getattr(entry, "summary", ""), 520),
        "url": url,
        "published_at": _parse_date(published),
        "tags": list(source.tags),
    }


def fetch_source_items(source: FactCheckSource, max_items: int = 8, timeout: int = 12) -> tuple[list[dict[str, object]], str]:
    if feedparser is None:
        return [], "feedparser is not installed. Run: pip install -r requirements.txt"
    if not source.feed_url:
        return [], f"{source.name}: no public feed configured; use its website/API manually."
    try:
        response = requests.get(source.feed_url, headers=HEADERS, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException as exc:
        return [], f"{source.name}: fetch failed - {exc}"

    parsed = feedparser.parse(response.content)
    items = []
    for entry in parsed.entries[:max_items]:
        item = _item_from_entry(source, entry)
        if item:
            items.append(item)
    if not items:
        return [], f"{source.name}: feed returned no parseable items."
    return items, f"{source.name}: fetched {len(items)} items."


def fetch_all_sources(region: str = "All", max_per_source: int = 8) -> tuple[list[dict[str, object]], list[str]]:
    started_at = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    items: list[dict[str, object]] = []
    logs = [f"Fetch started at {started_at}"]
    for source in FACT_CHECK_SOURCES:
        if region != "All" and source.region != region:
            continue
        fetched, message = fetch_source_items(source, max_items=max_per_source)
        items.extend(fetched)
        logs.append(message)
    logs.append(f"Total fetched items: {len(items)}")
    return items, logs
