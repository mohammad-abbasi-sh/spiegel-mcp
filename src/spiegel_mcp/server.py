"""MCP server: unofficial read-only access to spiegel.de — DER SPIEGEL,
Germany's biggest news magazine — via its official RSS feeds.
No key, no login."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone

from mcp.server.fastmcp import FastMCP

from . import domain as _dom
from . import http as _http

INSTRUCTIONS = """\
Unofficial read-only MCP server for spiegel.de — DER SPIEGEL, Germany's
biggest news magazine — via its official RSS feeds (no key, no login).
Top headlines, news by section (Politik, Ausland, Wirtschaft, Panorama,
Sport, Kultur, Netzwelt, Wissenschaft, Geschichte, Gesundheit, Karriere,
Mobilität, Stil), keyword search across all feeds, latest videos and
article text. NOTE: many SPIEGEL articles are SPIEGEL+ (paywalled) —
their pages carry no full body text, so spiegel_get_article reports
paywalled: true and returns only the freely available summary/teaser
for those; free articles return the full body. Search filters the
fetched feeds client-side (the site search page needs a session/consent
flow).
Built by Mohammad Abbasi (mohammad-abbasi-sh) — https://almanibama.ir · \
https://mabbasi.ir — Germany MCP factory.\
"""


_SOURCE = "spiegel.de"
_DISCLAIMER = "Unofficial read-only data from spiegel.de; verify on the site before acting on it."


def _envelope() -> dict:
    return {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": _SOURCE,
        "disclaimer": _DISCLAIMER,
    }


def _ok(payload: dict) -> str:
    return json.dumps({**_envelope(), **payload}, ensure_ascii=False)


def _err(e: Exception) -> str:
    return _ok({"error": str(e)})


mcp = FastMCP("spiegel-mcp", instructions=INSTRUCTIONS)


def _feed(url: str, limit: int) -> dict:
    """Fetch one RSS feed and return its items, newest first, capped."""
    parsed = _dom.parse_rss(_http.fetch_feed(url))
    items = parsed["items"][:limit]
    return {
        "feed_title": parsed["feed_title"],
        "total_results": parsed["count"],
        "count": len(items),
        "items": items,
    }


@mcp.tool()
def spiegel_headlines(limit: int = 10) -> str:
    """Top headlines from spiegel.de (Schlagzeilen), newest first.
limit: 1..50 (default 10)."""
    try:
        lim = _dom.validate_limit(limit)
        out = _feed(_dom.HEADLINES_FEED, lim)
    except (_http.SpiegelError, ValueError) as e:
        return _err(e)
    return _ok(out)


@mcp.tool()
def spiegel_news_by_section(section: str, limit: int = 10) -> str:
    """Newest news of one SPIEGEL section, newest first. section:
"politik", "ausland", "wirtschaft", "panorama", "sport", "kultur",
"netzwelt", "wissenschaft", "geschichte", "gesundheit", "karriere",
"mobilitaet" or "stil" (German names work too, e.g. "Mobilität").
limit: 1..50 (default 10)."""
    try:
        lim = _dom.validate_limit(limit)
        entry = _dom.normalise_section(section)
        out = _feed(entry["feed"], lim)
    except (_http.SpiegelError, ValueError) as e:
        return _err(e)
    return _ok({"section": entry["section"], "section_name": entry["name"], **out})


@mcp.tool()
def spiegel_search_news(query: str, limit: int = 10) -> str:
    """Search spiegel.de news by keyword (title + description).
query: free text, e.g. "Ronaldo" or "Bundestag". limit: 1..50
(default 10). Searches the headlines feed plus all 13 section feeds
client-side (the site search page needs a session/consent flow),
newest first, de-duplicated by link."""
    try:
        if not (query or "").strip():
            return _ok({"error": "query must not be empty"})
        lim = _dom.validate_limit(limit)
        feeds = [_dom.HEADLINES_FEED] + [s["feed"] for s in _dom.SECTIONS]
        seen: set[str] = set()
        found: list[dict] = []
        for url in feeds:
            parsed = _dom.parse_rss(_http.fetch_feed(url))
            for item in _dom.search_items(parsed["items"], query.strip()):
                if item["link"] in seen:
                    continue
                seen.add(item["link"])
                found.append(item)
        found.sort(key=lambda it: it.get("published") or "", reverse=True)
        out = {
            "query": query.strip(),
            "total_results": len(found),
            "count": min(lim, len(found)),
            "items": found[:lim],
        }
    except (_http.SpiegelError, ValueError) as e:
        return _err(e)
    return _ok(out)


@mcp.tool()
def spiegel_get_article(url: str) -> str:
    """Text of one spiegel.de article: headline, description, publish
date, author and the article body. url: a spiegel.de article link,
e.g. from spiegel_headlines. Free articles return the full body;
SPIEGEL+ (paywalled) articles return paywalled: true with only the
freely available summary/teaser — the full text stays behind the
paywall and is never fabricated."""
    try:
        if not (url or "").strip():
            return _ok({"error": "url must not be empty"})
        article = _dom.extract_article(_http.fetch_article(url.strip()))
    except (_http.SpiegelError, ValueError) as e:
        return _err(e)
    return _ok({"url": url.strip(), **article})


@mcp.tool()
def spiegel_latest_videos(limit: int = 10) -> str:
    """Latest SPIEGEL videos (SPIEGEL TV and video reports), newest
first. limit: 1..50 (default 10)."""
    try:
        lim = _dom.validate_limit(limit)
        out = _feed(_dom.VIDEOS_FEED, lim)
    except (_http.SpiegelError, ValueError) as e:
        return _err(e)
    return _ok(out)


@mcp.tool()
def spiegel_health() -> str:
    """Check whether spiegel.de is reachable right now.

    Returns status ok (HTTP 200), blocked (HTTP 403/429 — bot wall or
    rate limit) or error, plus the HTTP status and the probed URL.
    One polite request; it does not fetch any listings."""
    return _ok(_http.health_check())


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    sys.exit(main())
