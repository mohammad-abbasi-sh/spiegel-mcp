# spiegel-mcp 📰

mcp-name: io.github.mohammad-abbasi-sh/spiegel-mcp

سرور MCP غیررسمی و **فقط‌خواندنی** برای **[spiegel.de](https://www.spiegel.de)** — اشپیگل (DER SPIEGEL)، بزرگ‌ترین مجلهٔ خبری آلمان — از طریق فیدهای رسمی RSS. تیترهای برتر، اخبار ۱۳ بخش، جست‌وجوی کلیدواژه، جدیدترین ویدیوها و متن مقاله‌ها. بدون کلید، بدون ورود.

> ساختهٔ محمد عباسی در چارچوب «کارخانهٔ MCP آلمان» (مدل سپهر). وابسته به spiegel.de یا DER SPIEGEL نیست.

## برای ایجنت‌های هوش مصنوعی

به پیکربندی MCP Client اضافه کنید (stdio):

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

یا اجرای محلی: `python -m spiegel_mcp.server` (نیازمند `mcp<2` و `httpx`).

## ابزارها

| ابزار | توضیح |
|------|-------|
| `spiegel_headlines` | تیترهای برتر (Schlagzeilen)، جدیدترین اول — `limit` بین ۱ تا ۵۰ |
| `spiegel_news_by_section` | جدیدترین اخبار یک بخش — `section`: «politik»، «ausland»، «wirtschaft»، «panorama»، «sport»، «kultur»، «netzwelt»، «wissenschaft»، «geschichte»، «gesundheit»، «karriere»، «mobilitaet» یا «stil» (نام آلمانی هم کار می‌کند)، `limit` بین ۱ تا ۵۰ |
| `spiegel_search_news` | جست‌وجوی اخبار با کلیدواژه (عنوان + توضیح) — `query` (مثلاً «Ronaldo»)، `limit` بین ۱ تا ۵۰ |
| `spiegel_get_article` | متن یک مقاله: تیتر، توضیح، تاریخ انتشار، نویسنده و متن — `url` (لینک مقالهٔ spiegel.de). مقاله‌های رایگان متن کامل را برمی‌گردانند؛ مقاله‌های SPIEGEL+ (پولی) مقدار `paywalled: true` را با فقط خلاصه/تیزر رایگان برمی‌گردانند |
| `spiegel_latest_videos` | جدیدترین ویدیوهای اشپیگل (SPIEGEL TV و گزارش‌های ویدیویی)، جدیدترین اول — `limit` بین ۱ تا ۵۰ |
| `spiegel_health` | بررسی در دسترس بودن سایت (ok / blocked / error) — یک درخواست مؤدبانه |

نمونهٔ خروجی (`spiegel_headlines` با `limit` برابر ۲):

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

نکته‌ها:
- سرور **فیدهای رسمی RSS** را می‌خواند (تیترها، ۱۳ فید بخش، فید ویدیو — همه در ۱۵ نوامبر ۲۰۲۶ به‌صورت زنده بررسی شدند، هر کدام ۲۰ تا ۳۰ مورد). جست‌وجو فید تیترها به‌علاوهٔ هر ۱۳ فید بخش را سمت کلاینت فیلتر می‌کند (جست‌وجوی سایت نیازمند نشست/رضایت است)، بدون تکرار لینک، جدیدترین اول.
- `spiegel_get_article` داده‌های NewsArticle در JSON-LD (تیتر، تاریخ انتشار، نویسنده) به‌علاوهٔ پاراگراف‌های `<article>` صفحه را می‌خواند. فقط آدرس‌های `www.spiegel.de` واکشی می‌شوند.
- **صداقت دربارهٔ پی‌وال:** بسیاری از مقاله‌های اشپیگل SPIEGEL+ هستند — صفحه‌های رندرشدهٔ سمت سرور آن‌ها اصلاً متن مقاله ندارند. برای این مقاله‌ها ابزار مقدار `paywalled: true`، تیتر، تیزر/توضیح و یک یادداشت برمی‌گرداند — هرگز متن ساختگی. مقاله‌های رایگان متن کامل را برمی‌گردانند (بررسی زنده: ورزش ۴۹۷ کلمه، پانوراما ۴۷۹، اقتصاد ۳۵۳).
- داده‌ها: فیدهای عمومی RSS سایت spiegel.de — بدون کلید، بدون ورود، فقط خواندنی.

## توسعه

```bash
python3 -m venv .venv && .venv/bin/pip install "mcp<2" httpx pytest
.venv/bin/pip install -e .
.venv/bin/python -m pytest tests/ -q
```

- `tests/test_domain.py` — آفلاین، با فیدهای RSS واقعی ضبط‌شده و دو صفحهٔ مقاله (رایگان + پولی)
- `tests/test_live.py` — چند درخواست زندهٔ محتاطانه به spiegel.de

تست‌ها: ۳۶ از ۳۶ سبز (۲۸ آفلاین + ۸ زنده، ۱۵ نوامبر ۲۰۲۶).

## مجوز

[PolyForm Noncommercial 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0/)

---

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
