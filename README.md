# spiegel-mcp 📰

mcp-name: io.github.mohammad-abbasi-sh/spiegel-mcp

Unofficial **read-only** MCP server for **[spiegel.de](https://www.spiegel.de)** — DER SPIEGEL, Germany's biggest news magazine — via its official RSS feeds. Top headlines, news by section (13 Ressorts), keyword search, latest videos and article text. No key, no login.

> Built by Mohammad Abbasi as part of the "Germany MCP factory" (Sepehr-style pipeline). Not affiliated with spiegel.de or DER SPIEGEL.

## For AI agents

Add to your MCP client config (stdio):

```json
{
  "mcpServers": {
    "spiegel": {
      "command": "uvx",
      "args": ["spiegel-mcp==0.1.0"]
    }
  }
}
```

Or run locally: `python -m spiegel_mcp.server` (needs `mcp<2`, `httpx`).

## Tools

| Tool | Description |
|------|-------------|
| `spiegel_headlines` | Top headlines (Schlagzeilen), newest first — `limit` 1..50 |
| `spiegel_news_by_section` | Newest news of one section — `section`: "politik", "ausland", "wirtschaft", "panorama", "sport", "kultur", "netzwelt", "wissenschaft", "geschichte", "gesundheit", "karriere", "mobilitaet" or "stil" (German names work too), `limit` 1..50 |
| `spiegel_search_news` | Search news by keyword (title + description) — `query` (e.g. "Ronaldo"), `limit` 1..50 |
| `spiegel_get_article` | Text of one article: headline, description, publish date, author, body — `url` (a spiegel.de article link). Free articles return the full body; SPIEGEL+ (paywalled) articles return `paywalled: true` with only the freely available summary/teaser |
| `spiegel_latest_videos` | Latest SPIEGEL videos (SPIEGEL TV and video reports), newest first — `limit` 1..50 |
| `spiegel_health` | Reachability probe (ok / blocked / error) — one polite request |

Example output (`spiegel_headlines`, `limit` 2):

```json
{"feed_title": "DER SPIEGEL - Schlagzeilen", "total_results": 30, "count": 2,
 "items": [
  {"title": "Vanessa Emde: Die frühen Gedichte der Skandal-Linken",
   "link": "https://www.spiegel.de/politik/deutschland/vanessa-emde-die-fruehen-gedichte-der-skandal-linken-a-33089a48-bd29-4ed2-b624-03370da8e383#ref=rss",
   "description": "Vanessa Emde, die israelfeindliche Aktivistin aus Neukölln, dominiert seit Wochen die Berliner Koalitionsgespräche. Früher inszenierte sie am Theater und schrieb Lyrik. Was verrät ihr Werk über sie?",
   "published": "2026-11-15T10:10:00+00:00", "category": "Politik"},
  {"title": "Nations League: Portugal ehrt Ronaldo und verliert deutlich gegen Dänemark",
   "link": "https://www.spiegel.de/sport/fussball/nations-league-portugal-ehrt-ronaldo-und-verliert-deutlich-gegen-daenemark-a-0d14c2bb-debd-45e8-9406-5a9bbc7a123a#ref=rss",
   "description": "Ohne ihn läuft es nicht: Im ersten Spiel nach dem Rücktritt von Cristiano Ronaldo aus dem Nationalteam geht Portugal unter. ...",
   "published": "2026-11-15T09:55:00+00:00", "category": "Sport"},
  ...]}
```

Notes:
- The server reads the **official RSS feeds** (Schlagzeilen, 13 section feeds, video feed — each verified live 2026-11-15 with 20–30 items). Search filters the headlines feed plus all 13 section feeds client-side (the site search page needs a session/consent flow), de-duplicated by link, newest first.
- `spiegel_get_article` reads the NewsArticle JSON-LD (headline, publish date, author) plus the `<article>` paragraphs of the page. Only `www.spiegel.de` URLs are fetched.
- **Paywall honesty:** many SPIEGEL articles are SPIEGEL+ — their server-rendered pages carry no body text at all. For those, the tool returns `paywalled: true`, the headline, the teaser/description and a note — never fabricated text. Free articles return the full body (verified live: sport 497 words, panorama 479, wirtschaft 353).
- Data: spiegel.de public RSS feeds — no key, no login, read-only.

## Development

```bash
python3 -m venv .venv && .venv/bin/pip install "mcp<2" httpx pytest
.venv/bin/pip install -e .
.venv/bin/python -m pytest tests/ -q
```

- `tests/test_domain.py` — offline, parses real captured RSS feeds + two article pages (free + paywalled)
- `tests/test_live.py` — cautious live requests against spiegel.de

Tests: 36/36 green (28 offline + 8 live, 2026-11-15).

## License

[PolyForm Noncommercial 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0/) — free for personal and non-commercial use; commercial use needs a separate license (see LICENSE).

---

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
