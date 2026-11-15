"""Live tests — hit the real spiegel.de RSS feeds and article pages.
Cautious: few requests.

Run:  pytest tests/test_live.py -v
Skip: pytest -m "not live"  (or set SPIEGEL_SKIP_LIVE=1)
"""
import json
import os
import pathlib
import sys
import unittest

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from spiegel_mcp import server as srv

pytestmark = pytest.mark.live
SKIP = os.environ.get("SPIEGEL_SKIP_LIVE") == "1"


@pytest.mark.skipif(SKIP, reason="SPIEGEL_SKIP_LIVE=1")
class TestLive(unittest.TestCase):
    def test_headlines_live(self):
        out = json.loads(srv.spiegel_headlines(limit=3))
        self.assertNotIn("error", out)
        self.assertGreaterEqual(out["count"], 1)
        self.assertTrue(all(i["title"] and i["link"] for i in out["items"]))
        print(f"\nLIVE headlines: {out['count']} items, first: {out['items'][0]['title']}")

    def test_section_live(self):
        out = json.loads(srv.spiegel_news_by_section("ausland", limit=3))
        self.assertNotIn("error", out)
        self.assertGreaterEqual(out["count"], 1)
        print(f"\nLIVE ausland: {out['items'][0]['title']}")

    def test_all_sections_live(self):
        # Every section feed must answer with at least one item.
        from spiegel_mcp import domain as dom
        for s in dom.SECTIONS:
            out = json.loads(srv.spiegel_news_by_section(s["section"], limit=1))
            self.assertNotIn("error", out, f"section {s['section']}")
            self.assertGreaterEqual(out["count"], 1, f"section {s['section']}")
        print(f"\nLIVE all {len(dom.SECTIONS)} sections OK")

    def test_search_live(self):
        out = json.loads(srv.spiegel_search_news("Berlin", limit=3))
        self.assertNotIn("error", out)
        self.assertGreaterEqual(out["count"], 1)
        self.assertTrue(all(
            "berlin" in (i["title"] + i["description"]).casefold()
            for i in out["items"]
        ))
        print(f"\nLIVE search 'Berlin': {out['total_results']} hits")

    def test_get_article_live(self):
        head = json.loads(srv.spiegel_headlines(limit=5))
        url = head["items"][0]["link"]
        out = json.loads(srv.spiegel_get_article(url))
        self.assertNotIn("error", out)
        self.assertTrue(out["headline"])
        # Free article: full body; paywalled: teaser + flag, never fake text.
        if out["paywalled"]:
            self.assertTrue(out["description"])
            print(f"\nLIVE article (paywalled): {out['headline']}")
        else:
            self.assertGreater(out["body_chars"], 200)
            print(f"\nLIVE article: {out['headline']} ({out['body_chars']} chars)")

    def test_get_free_article_live(self):
        # A sport article is free more often than not; accept either
        # outcome, but the result must be honest about it.
        out = json.loads(srv.spiegel_news_by_section("sport", limit=5))
        self.assertNotIn("error", out)
        art = json.loads(srv.spiegel_get_article(out["items"][0]["link"]))
        self.assertNotIn("error", art)
        self.assertTrue(art["headline"])
        if not art["paywalled"]:
            self.assertGreater(art["body_chars"], 200)
        print(f"\nLIVE sport article: paywalled={art['paywalled']}, "
              f"{art['body_chars']} chars")

    def test_videos_live(self):
        out = json.loads(srv.spiegel_latest_videos(limit=3))
        self.assertNotIn("error", out)
        self.assertGreaterEqual(out["count"], 1)
        self.assertTrue(all(i["link"].startswith("https://www.spiegel.de/") for i in out["items"]))
        print(f"\nLIVE videos: {out['items'][0]['title']}")

    def test_health_live(self):
        out = json.loads(srv.spiegel_health())
        self.assertEqual(out["status"], "ok")
        self.assertEqual(out["http_status"], 200)
