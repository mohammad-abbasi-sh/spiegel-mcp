"""Domain logic: shape spiegel.de RSS feeds and article pages into
compact dicts (stdlib only).

Data source: the official spiegel.de RSS feeds
(https://www.spiegel.de/<section>/index.rss). No key, no login.
Article text comes from the <article> paragraphs of each article
page plus its NewsArticle JSON-LD (headline, publish date, author).

Paywall honesty: a large share of SPIEGEL articles are SPIEGEL+
(paywalled) — their server-rendered page carries no body text, only
subscription prompts and an AI-generated summary widget. extract_article
therefore returns ``paywalled: true`` plus the freely available teaser/
summary for those pages instead of pretending the full text was read.
Free articles return the full body (verified live 2026-11-15: sport
532 words, panorama 479, wirtschaft 353).
"""
from __future__ import annotations

import html
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

BASE = "https://www.spiegel.de"

# Ressort feeds: <section>/index.rss — all 13 verified live 2026-11-15
# (20 items each). German names accepted as aliases in normalise_section.
SECTIONS = [
    {"section": "politik", "name": "Politik", "feed": f"{BASE}/politik/index.rss"},
    {"section": "ausland", "name": "Ausland", "feed": f"{BASE}/ausland/index.rss"},
    {"section": "wirtschaft", "name": "Wirtschaft", "feed": f"{BASE}/wirtschaft/index.rss"},
    {"section": "panorama", "name": "Panorama", "feed": f"{BASE}/panorama/index.rss"},
    {"section": "sport", "name": "Sport", "feed": f"{BASE}/sport/index.rss"},
    {"section": "kultur", "name": "Kultur", "feed": f"{BASE}/kultur/index.rss"},
    {"section": "netzwelt", "name": "Netzwelt", "feed": f"{BASE}/netzwelt/index.rss"},
    {"section": "wissenschaft", "name": "Wissenschaft", "feed": f"{BASE}/wissenschaft/index.rss"},
    {"section": "geschichte", "name": "Geschichte", "feed": f"{BASE}/geschichte/index.rss"},
    {"section": "gesundheit", "name": "Gesundheit", "feed": f"{BASE}/gesundheit/index.rss"},
    {"section": "karriere", "name": "Karriere", "feed": f"{BASE}/karriere/index.rss"},
    {"section": "mobilitaet", "name": "Mobilität", "feed": f"{BASE}/mobilitaet/index.rss"},
    {"section": "stil", "name": "Stil", "feed": f"{BASE}/stil/index.rss"},
]

HEADLINES_FEED = f"{BASE}/schlagzeilen/index.rss"
VIDEOS_FEED = f"{BASE}/video/index.rss"

_SECTION_BY_KEY = {}
for _s in SECTIONS:
    _SECTION_BY_KEY[_s["section"]] = _s
    _SECTION_BY_KEY[_s["name"].lower()] = _s


def validate_limit(limit: int) -> int:
    """Clamp/validate the page size (feeds carry 20-30 items)."""
    if not 1 <= limit <= 50:
        raise ValueError(f"limit out of range: {limit} (expected 1..50)")
    return limit


def normalise_section(section: str) -> dict:
    """Canonical section entry; accepts slug ("politik") or German name."""
    key = (section or "").strip().lower()
    if not key:
        raise ValueError("section must not be empty")
    entry = _SECTION_BY_KEY.get(key)
    if entry is None:
        raise ValueError(
            f"unknown section: {section!r} "
            f"(expected one of {', '.join(s['section'] for s in SECTIONS)})"
        )
    return entry


def _text(elem, tag: str) -> str:
    child = elem.find(tag)
    if child is None or child.text is None:
        return ""
    return html.unescape(child.text).strip()


def _iso(date_text: str) -> str | None:
    if not date_text:
        return None
    try:
        dt = parsedate_to_datetime(date_text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    except (TypeError, ValueError):
        return None


def compact_item(item: ET.Element) -> dict:
    """One RSS <item>, compact: title, link, description, publish time,
    section category."""
    return {
        "title": _text(item, "title"),
        "link": _text(item, "link"),
        "description": _text(item, "description"),
        "published": _iso(_text(item, "pubDate")),
        "category": _text(item, "category"),
    }


def parse_rss(xml_text: str) -> dict:
    """Parse one spiegel.de RSS feed into {feed_title, count, items}.

    Raises ValueError on malformed XML or a non-RSS document (e.g. a
    403 error page saved as text).
    """
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        raise ValueError(f"invalid RSS XML: {e}") from e
    channel = root.find("channel")
    if channel is None:
        raise ValueError("unexpected RSS shape: no <channel> element")
    items = [compact_item(it) for it in channel.findall("item")]
    return {
        "feed_title": _text(channel, "title"),
        "count": len(items),
        "items": items,
    }


def search_items(items: list, query: str) -> list:
    """Case-insensitive substring match over title + description.

    The site search page needs a session/consent flow, so search filters
    the fetched feeds client-side.
    """
    q = (query or "").strip().casefold()
    if not q:
        raise ValueError("query must not be empty")
    return [
        it for it in items
        if q in (it.get("title") or "").casefold()
        or q in (it.get("description") or "").casefold()
    ]


_LD_JSON_RE = re.compile(
    r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>',
    re.S | re.I,
)
_TITLE_RE = re.compile(r"<title>(.*?)</title>", re.S | re.I)
_META_DESC_RE = re.compile(
    r'<meta\s+name="description"\s+content="([^"]*)"', re.S | re.I
)
_ARTICLE_RE = re.compile(r"<article[^>]*>(.*?)</article>", re.S | re.I)
_PARA_RE = re.compile(r"<p[^>]*>(.*?)</p>", re.S | re.I)
_TAG_RE = re.compile(r"<[^>]+>")

# Paragraphs inside <article> that are UI/boilerplate, not article text:
# subscription prompts, the AI-summary widget, photo credits, script noise.
_BOILERPLATE = (
    "digital-abo",
    "print-abo",
    "itunes-account",
    "automatisch erstellt mit ki",
    "war die zusammenfassung hilfreich",
)


def _clean_para(raw: str) -> str:
    text = _TAG_RE.sub("", raw)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _is_boilerplate(text: str) -> bool:
    low = text.casefold()
    if low.startswith("foto:") or low.startswith("bild:"):
        return True
    if "typeof(event)" in low:
        return True
    return any(marker in low for marker in _BOILERPLATE)


def _news_article_node(page_html: str) -> dict:
    """The NewsArticle node of the page's JSON-LD (@graph list or dict)."""
    match = _LD_JSON_RE.search(page_html)
    if not match:
        return {}
    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError:
        return {}
    nodes = data if isinstance(data, list) else [data]
    for node in nodes:
        if isinstance(node, dict) and node.get("@type") == "NewsArticle":
            return node
    return {}


def extract_article(page_html: str) -> dict:
    """Headline, description, author, publish date and body text of one
    spiegel.de article page.

    Headline/author/date come from the NewsArticle JSON-LD; description
    from the meta description; body from the <article> paragraphs with
    subscription/AI-summary/photo boilerplate removed.

    SPIEGEL+ (paywalled) articles carry no body text in the SSR page:
    when the filtered body is under 100 words and the page shows the
    paywall prompts, ``paywalled`` is true and ``body`` holds only the
    freely available summary/teaser. Raises ValueError when the page
    has neither JSON-LD nor an <article> block (not an article page).
    """
    node = _news_article_node(page_html)
    title_m = _TITLE_RE.search(page_html)
    title = html.unescape(title_m.group(1)).strip() if title_m else ""
    title = re.sub(r"\s+", " ", title)
    if title.endswith(" - DER SPIEGEL"):
        title = title[: -len(" - DER SPIEGEL")]
    headline = (node.get("headline") or "").strip() or title

    meta_m = _META_DESC_RE.search(page_html)
    description = html.unescape(meta_m.group(1)).strip() if meta_m else ""
    if not description:
        description = (node.get("description") or "").strip()

    author = node.get("author")
    if isinstance(author, dict):
        author = author.get("name") or ""
    elif not isinstance(author, str):
        author = ""

    article_m = _ARTICLE_RE.search(page_html)
    article_block = article_m.group(1) if article_m else ""
    if not node and not article_block:
        raise ValueError(
            "no JSON-LD data and no <article> block on this page "
            "(not a spiegel.de article page?)"
        )
    paras = [
        _clean_para(p)
        for p in _PARA_RE.findall(article_block)
    ]
    body_paras = [p for p in paras if p and not _is_boilerplate(p)]
    body = "\n\n".join(body_paras)
    words = len(body.split())
    paywalled = words < 100 and (
        "SPIEGEL+" in article_block or "Digital-Abo" in article_block
    )
    return {
        "headline": headline,
        "description": description,
        "published": node.get("datePublished") or "",
        "modified": node.get("dateModified") or "",
        "author": author or "",
        "body": body,
        "body_chars": len(body),
        "body_words": words,
        "paywalled": paywalled,
        "note": (
            "Full text is behind the SPIEGEL+ paywall; the text above "
            "is only the freely available summary/teaser."
            if paywalled
            else ""
        ),
    }
