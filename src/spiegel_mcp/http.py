"""HTTP layer for spiegel_mcp — plain httpx GETs against the official
spiegel.de RSS feeds and article pages.

No key, no login. The site search page needs a session/consent flow,
so search is done client-side over the fetched feeds instead.
"""
from __future__ import annotations

import os
import ssl
import time
from urllib.parse import urlparse

import httpx

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
TIMEOUT = 25.0
ALLOWED_HOST = "www.spiegel.de"


class SpiegelError(RuntimeError):
    pass


def _verify():
    """TLS trust store: the OS bundle when present, else httpx/certifi.

    The OS bundle matters behind MITM egress proxies (their CA is in the
    system store, not in certifi) and is the right default on Linux
    anyway; on systems without it we fall back to certifi.
    """
    for path in (
        "/etc/ssl/certs/ca-certificates.crt",
        ssl.get_default_verify_paths().openssl_cafile,
    ):
        if path and os.path.exists(path):
            return ssl.create_default_context(cafile=path)
    return True


def _client() -> httpx.Client:
    # NOTE: we read the proxy URL from the environment but never log it.
    # trust_env=False because httpx fails to parse bracketed IPv6 entries
    # (e.g. [::1]) that some environments put in no_proxy.
    proxy = os.environ.get("https_proxy") or os.environ.get("HTTPS_PROXY")
    return httpx.Client(
        headers={"User-Agent": UA, "Accept": "application/rss+xml, application/xml, text/html, */*"},
        timeout=TIMEOUT,
        proxy=proxy or None,
        trust_env=False,
        verify=_verify(),
    )


def fetch_text(url: str) -> str:
    """GET one URL and return its text. One retry on 429/5xx."""
    last_exc: Exception | None = None
    r: httpx.Response | None = None
    for attempt in range(2):
        try:
            with _client() as c:
                r = c.get(url)
        except httpx.HTTPError as e:
            last_exc = e
            if attempt == 0:
                time.sleep(1.0)
                continue
            raise SpiegelError(f"network error fetching {url}: {e}") from e
        if r.status_code in (429, 500, 502, 503):
            if attempt == 0:
                time.sleep(1.0)
                continue
        break
    assert r is not None  # loop always assigns r or raises
    if r.status_code == 403:
        raise SpiegelError(
            f"spiegel.de returned HTTP 403 for {url} (bot wall) — try again later"
        )
    if r.status_code == 429:
        raise SpiegelError(
            f"spiegel.de rate-limited the request (HTTP 429) — try again later"
        )
    if r.status_code != 200:
        raise SpiegelError(f"spiegel.de returned HTTP {r.status_code} for {url}")
    return r.text


def fetch_feed(url: str) -> str:
    """GET one RSS feed; returns the raw XML text."""
    return fetch_text(url)


def fetch_article(url: str) -> str:
    """GET one article page; only spiegel.de URLs are fetched."""
    host = (urlparse(url).netloc or "").lower()
    if host != ALLOWED_HOST:
        raise SpiegelError(
            f"only {ALLOWED_HOST} article URLs are fetched (got {host or url!r})"
        )
    return fetch_text(url)


def health_check() -> dict:
    """One polite probe of the source site.

    Returns {"status": "ok"|"blocked"|"error", "http_status": int|None,
    "url": ..., "detail": ...}. Used by the `spiegel_health` tool
    and the daily smoke CI.
    """
    url = "https://www.spiegel.de/schlagzeilen/index.rss"
    try:
        fetch_feed(url)
    except SpiegelError as e:
        msg = str(e)
        if "403" in msg:
            return {"status": "blocked", "http_status": 403, "url": url, "detail": msg}
        if "429" in msg:
            return {"status": "blocked", "http_status": 429, "url": url, "detail": msg}
        return {"status": "error", "http_status": None, "url": url, "detail": msg}
    return {"status": "ok", "http_status": 200, "url": url}
