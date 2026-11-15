"""Offline tests — parse real captured spiegel.de RSS feeds and two
article pages (one free, one SPIEGEL+ paywalled), no network."""
import json
import pathlib
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from spiegel_mcp import domain as dom
from spiegel_mcp import server as srv

FIX = pathlib.Path(__file__).resolve().parent / "fixtures"


def _rss(name):
    return dom.parse_rss((FIX / name).read_text(encoding="utf-8"))


class TestHeadlinesFixture(unittest.TestCase):
    def test_headlines_shape(self):
        out = _rss("headlines.xml")
        self.assertEqual(out["feed_title"], "DER SPIEGEL - Schlagzeilen")
        self.assertEqual(out["count"], 30)
        self.assertEqual(len(out["items"]), 30)

    def test_headlines_first_item(self):
        item = _rss("headlines.xml")["items"][0]
        self.assertEqual(
            item["title"],
            "Vanessa Emde: Die frühen Gedichte der Skandal-Linken",
        )
        self.assertTrue(item["link"].startswith("https://www.spiegel.de/politik/"))
        self.assertEqual(item["published"], "2026-11-15T10:10:00+00:00")
        self.assertEqual(item["category"], "Politik")

    def test_headlines_all_items_complete(self):
        items = _rss("headlines.xml")["items"]
        self.assertTrue(all(i["title"] and i["link"] and i["published"] for i in items))
        self.assertTrue(all(i["link"].startswith("https://www.spiegel.de/") for i in items))


class TestSectionAndVideoFixtures(unittest.TestCase):
    def test_section_politik(self):
        out = _rss("section-politik.xml")
        self.assertEqual(out["feed_title"], "DER SPIEGEL - Politik")
        self.assertEqual(out["count"], 20)
        self.assertTrue(all(i["link"].startswith("https://www.spiegel.de/") for i in out["items"]))
        self.assertTrue(all(i["description"] for i in out["items"]))

    def test_videos_feed(self):
        out = _rss("videos.xml")
        self.assertEqual(out["feed_title"], "DER SPIEGEL - Videos")
        self.assertEqual(out["count"], 20)
        self.assertTrue(all(i["link"].startswith("https://www.spiegel.de/") for i in out["items"]))


class TestParseErrors(unittest.TestCase):
    def test_malformed_xml(self):
        with self.assertRaises(ValueError):
            dom.parse_rss("<rss><channel><item>oops")

    def test_non_rss_document(self):
        with self.assertRaises(ValueError):
            dom.parse_rss("<html><head><title>403</title></head></html>")

    def test_empty_string(self):
        with self.assertRaises(ValueError):
            dom.parse_rss("")


class TestValidation(unittest.TestCase):
    def test_limit_bounds(self):
        self.assertEqual(dom.validate_limit(1), 1)
        self.assertEqual(dom.validate_limit(50), 50)
        with self.assertRaises(ValueError):
            dom.validate_limit(0)
        with self.assertRaises(ValueError):
            dom.validate_limit(51)

    def test_normalise_section(self):
        self.assertEqual(dom.normalise_section("politik")["section"], "politik")
        self.assertEqual(dom.normalise_section("Politik")["name"], "Politik")
        self.assertEqual(dom.normalise_section("MOBILITÄT")["section"], "mobilitaet")
        self.assertEqual(dom.normalise_section("Mobilität")["section"], "mobilitaet")
        with self.assertRaises(ValueError):
            dom.normalise_section("dax")
        with self.assertRaises(ValueError):
            dom.normalise_section("")

    def test_sections_all_have_feeds(self):
        self.assertEqual(len(dom.SECTIONS), 13)
        for s in dom.SECTIONS:
            self.assertTrue(s["feed"].startswith("https://www.spiegel.de/"))
            self.assertTrue(s["feed"].endswith("/index.rss"))


class TestSearch(unittest.TestCase):
    def test_search_case_insensitive(self):
        items = _rss("headlines.xml")["items"]
        self.assertEqual(len(dom.search_items(items, "Ronaldo")), 1)
        self.assertEqual(len(dom.search_items(items, "ronaldo")), 1)
        self.assertEqual(len(dom.search_items(items, "RONALDO")), 1)

    def test_search_counts(self):
        items = _rss("headlines.xml")["items"]
        self.assertEqual(len(dom.search_items(items, "Berlin")), 3)
        self.assertEqual(len(dom.search_items(items, "Trump")), 3)

    def test_search_no_hits(self):
        items = _rss("headlines.xml")["items"]
        self.assertEqual(dom.search_items(items, "zzzzqqq"), [])

    def test_search_empty_raises(self):
        with self.assertRaises(ValueError):
            dom.search_items([], "  ")


class TestArticleExtraction(unittest.TestCase):
    def test_free_article_fixture(self):
        html_text = (FIX / "article-free.html").read_text(encoding="utf-8")
        out = dom.extract_article(html_text)
        self.assertEqual(
            out["headline"],
            "Nations League: Portugal ehrt Ronaldo – vor allem mit einer "
            "heftigen Niederlage gegen Dänemark",
        )
        self.assertEqual(out["published"], "2026-11-15T10:55:00+01:00")
        self.assertEqual(out["author"], "DER SPIEGEL")
        self.assertEqual(out["body_chars"], 3533)
        self.assertEqual(out["body_words"], 497)
        self.assertFalse(out["paywalled"])
        self.assertEqual(out["note"], "")
        self.assertTrue(out["body"].startswith("Die portugiesische"))
        self.assertTrue(out["description"].startswith("Ohne ihn läuft es nicht"))

    def test_paywalled_article_fixture(self):
        html_text = (FIX / "article-paywalled.html").read_text(encoding="utf-8")
        out = dom.extract_article(html_text)
        self.assertEqual(
            out["headline"],
            "Koalitionstheater in der Hauptstadt: Das sind die Gedichte "
            "der Skandal-Linken Vanessa Emde",
        )
        self.assertEqual(out["published"], "2026-11-15T11:10:00+01:00")
        self.assertEqual(out["author"], "Felix Dachsel")
        self.assertTrue(out["paywalled"])
        self.assertEqual(out["body_words"], 0)
        self.assertIn("SPIEGEL+ paywall", out["note"])
        # Teaser/description is still returned — never an empty result.
        self.assertTrue(out["description"].startswith("Vanessa Emde"))

    def test_article_no_data(self):
        with self.assertRaises(ValueError):
            dom.extract_article("<html><body>no data here</body></html>")


class TestServerOffline(unittest.TestCase):
    """Tool functions with the HTTP layer mocked to the fixtures."""

    def _mock_feeds(self, mapping):
        def fake_fetch(url):
            return mapping[url]
        return mock.patch.object(srv._http, "fetch_feed", side_effect=fake_fetch)

    def test_headlines_tool(self):
        xml = (FIX / "headlines.xml").read_text(encoding="utf-8")
        with self._mock_feeds({dom.HEADLINES_FEED: xml}):
            out = json.loads(srv.spiegel_headlines(limit=3))
        self.assertNotIn("error", out)
        self.assertEqual(out["count"], 3)
        self.assertEqual(out["total_results"], 30)
        self.assertEqual(out["source"], "spiegel.de")
        self.assertIn("fetched_at", out)

    def test_section_tool(self):
        xml = (FIX / "section-politik.xml").read_text(encoding="utf-8")
        with self._mock_feeds({dom.SECTIONS[0]["feed"]: xml}):
            out = json.loads(srv.spiegel_news_by_section("politik", limit=2))
        self.assertNotIn("error", out)
        self.assertEqual(out["section"], "politik")
        self.assertEqual(out["count"], 2)

    def test_section_tool_unknown(self):
        out = json.loads(srv.spiegel_news_by_section("dax", limit=2))
        self.assertIn("error", out)
        self.assertIn("unknown section", out["error"])

    def test_search_tool(self):
        xml = (FIX / "headlines.xml").read_text(encoding="utf-8")
        feeds = {dom.HEADLINES_FEED: xml}
        feeds.update({s["feed"]: xml for s in dom.SECTIONS})
        with self._mock_feeds(feeds):
            out = json.loads(srv.spiegel_search_news("Ronaldo", limit=10))
        self.assertNotIn("error", out)
        self.assertEqual(out["query"], "Ronaldo")
        self.assertEqual(out["total_results"], 1)
        self.assertEqual(out["count"], 1)

    def test_search_tool_empty_query(self):
        out = json.loads(srv.spiegel_search_news("   "))
        self.assertIn("error", out)

    def test_get_article_tool_free(self):
        html_text = (FIX / "article-free.html").read_text(encoding="utf-8")
        with mock.patch.object(srv._http, "fetch_article", return_value=html_text):
            out = json.loads(
                srv.spiegel_get_article(
                    "https://www.spiegel.de/sport/fussball/nations-league-portugal-ehrt-ronaldo-und-verliert-deutlich-gegen-daenemark-a-0d14c2bb-debd-45e8-9406-5a9bbc7a123a"
                )
            )
        self.assertNotIn("error", out)
        self.assertEqual(out["body_chars"], 3533)
        self.assertFalse(out["paywalled"])
        self.assertIn("Ronaldo", out["headline"])

    def test_get_article_tool_paywalled(self):
        html_text = (FIX / "article-paywalled.html").read_text(encoding="utf-8")
        with mock.patch.object(srv._http, "fetch_article", return_value=html_text):
            out = json.loads(
                srv.spiegel_get_article(
                    "https://www.spiegel.de/politik/deutschland/vanessa-emde-die-fruehen-gedichte-der-skandal-linken-a-33089a48-bd29-4ed2-b624-03370da8e383"
                )
            )
        self.assertNotIn("error", out)
        self.assertTrue(out["paywalled"])
        self.assertIn("SPIEGEL+ paywall", out["note"])

    def test_get_article_tool_rejects_other_hosts(self):
        out = json.loads(srv.spiegel_get_article("https://example.com/news.html"))
        self.assertIn("error", out)

    def test_videos_tool(self):
        xml = (FIX / "videos.xml").read_text(encoding="utf-8")
        with self._mock_feeds({dom.VIDEOS_FEED: xml}):
            out = json.loads(srv.spiegel_latest_videos(limit=5))
        self.assertNotIn("error", out)
        self.assertEqual(out["count"], 5)
        self.assertEqual(out["total_results"], 20)

    def test_health_tool(self):
        with mock.patch.object(srv._http, "health_check", return_value={"status": "ok", "http_status": 200, "url": dom.HEADLINES_FEED}):
            out = json.loads(srv.spiegel_health())
        self.assertEqual(out["status"], "ok")


if __name__ == "__main__":
    unittest.main()
