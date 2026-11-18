# spiegel-mcp 📰

mcp-name: io.github.mohammad-abbasi-sh/spiegel-mcp

Inoffizieller **Read-only**-MCP-Server für **[spiegel.de](https://www.spiegel.de)** — DER SPIEGEL, Deutschlands größtes Nachrichtenmagazin — über die offiziellen RSS-Feeds. Top-Schlagzeilen, Nachrichten nach Ressort (13 Ressorts), Stichwortsuche, neueste Videos und Artikeltexte. Kein Schlüssel, kein Login.

> Gebaut von Mohammad Abbasi im Rahmen der „Germany MCP factory" (Sepehr-Modell). Nicht mit spiegel.de oder DER SPIEGEL verbunden.

## Für KI-Agenten

Zur MCP-Client-Konfiguration hinzufügen (stdio):

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

Oder lokal starten: `python -m spiegel_mcp.server` (benötigt `mcp<2`, `httpx`).

## Tools

| Tool | Beschreibung |
|------|--------------|
| `spiegel_headlines` | Top-Schlagzeilen, neueste zuerst — `limit` 1..50 |
| `spiegel_news_by_section` | Neueste Nachrichten eines Ressorts — `section`: „politik", „ausland", „wirtschaft", „panorama", „sport", „kultur", „netzwelt", „wissenschaft", „geschichte", „gesundheit", „karriere", „mobilitaet" oder „stil" (deutsche Namen funktionieren auch), `limit` 1..50 |
| `spiegel_search_news` | Nachrichtensuche nach Stichwort (Titel + Beschreibung) — `query` (z. B. „Ronaldo"), `limit` 1..50 |
| `spiegel_get_article` | Text eines Artikels: Schlagzeile, Beschreibung, Veröffentlichungsdatum, Autor, Text — `url` (ein spiegel.de-Artikellink). Freie Artikel liefern den Volltext; SPIEGEL+-Artikel (Paywall) liefern `paywalled: true` mit nur der frei verfügbaren Zusammenfassung/dem Teaser |
| `spiegel_latest_videos` | Neueste SPIEGEL-Videos (SPIEGEL TV und Videoreportagen), neueste zuerst — `limit` 1..50 |
| `spiegel_health` | Erreichbarkeitsprüfung (ok / blocked / error) — eine höfliche Anfrage |

Beispielausgabe (`spiegel_headlines`, `limit` 2):

```json
{"feed_title": "DER SPIEGEL - Schlagzeilen", "total_results": 30, "count": 2,
 "items": [
  {"title": "Vanessa Emde: Die frühen Gedichte der Skandal-Linken",
   "link": "https://www.spiegel.de/politik/deutschland/vanessa-emde-die-fruehen-gedichte-der-skandal-linken-a-33089a48-bd29-4ed2-b624-03370da8e383#ref=rss",
   "description": "Vanessa Emde, die israelfeindliche Aktivistin aus Neukölln, dominiert seit Wochen die Berliner Koalitionsgespräche. ...",
   "published": "2026-11-15T10:10:00+00:00", "category": "Politik"},
  {"title": "Nations League: Portugal ehrt Ronaldo und verliert deutlich gegen Dänemark",
   "link": "https://www.spiegel.de/sport/fussball/nations-league-portugal-ehrt-ronaldo-und-verliert-deutlich-gegen-daenemark-a-0d14c2bb-debd-45e8-9406-5a9bbc7a123a#ref=rss",
   "description": "Ohne ihn läuft es nicht: Im ersten Spiel nach dem Rücktritt von Cristiano Ronaldo aus dem Nationalteam geht Portugal unter. ...",
   "published": "2026-11-15T09:55:00+00:00", "category": "Sport"},
  ...]}
```

Hinweise:
- Der Server liest die **offiziellen RSS-Feeds** (Schlagzeilen, 13 Ressort-Feeds, Video-Feed — alle am 15.11.2026 live geprüft, je 20–30 Einträge). Die Suche filtert den Schlagzeilen-Feed plus alle 13 Ressort-Feeds clientseitig (die Website-Suche braucht einen Session-/Consent-Flow), nach Link dedupliziert, neueste zuerst.
- `spiegel_get_article` liest das NewsArticle-JSON-LD (Schlagzeile, Veröffentlichungsdatum, Autor) plus die `<article>`-Absätze der Seite. Nur `www.spiegel.de`-URLs werden abgerufen.
- **Paywall-Ehrlichkeit:** Viele SPIEGEL-Artikel sind SPIEGEL+ — ihre serverseitig gerenderten Seiten enthalten gar keinen Artikeltext. Für diese liefert das Tool `paywalled: true`, die Schlagzeile, den Teaser/die Beschreibung und einen Hinweis — niemals erfundenen Text. Freie Artikel liefern den Volltext (live geprüft: Sport 497 Wörter, Panorama 479, Wirtschaft 353).
- Daten: öffentliche RSS-Feeds von spiegel.de — kein Schlüssel, kein Login, nur lesend.

## Entwicklung

```bash
python3 -m venv .venv && .venv/bin/pip install "mcp<2" httpx pytest
.venv/bin/pip install -e .
.venv/bin/python -m pytest tests/ -q
```

- `tests/test_domain.py` — offline, mit echten aufgezeichneten RSS-Feeds und zwei Artikelseiten (frei + Paywall)
- `tests/test_live.py` — wenige vorsichtige Live-Anfragen an spiegel.de

Tests: 36/36 grün (28 offline + 8 live, 15.11.2026).

## Lizenz

[PolyForm Noncommercial 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0/)

---

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
