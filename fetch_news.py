"""
The Newspaper - Checkpoint 1: fetch news
Pulls global market news (Finnhub) + Indian markets/economy news (RSS),
keeps the last 24 hours, prints headlines, and saves news.json.

Setup:
    pip install requests feedparser
    export FINNHUB_API_KEY="your_key_here"      # Mac/Linux
    setx FINNHUB_API_KEY "your_key_here"        # Windows (reopen terminal)

Run:
    python fetch_news.py
"""

import os
import re
import json
import time
import datetime as dt

import requests
import feedparser

FINNHUB_KEY = os.environ.get("FINNHUB_API_KEY")
MAX_AGE_HOURS = 24
PER_SECTION = 12

# Indian sources (feed URLs can change; swap in new ones if a feed returns 0 items)
INDIA_FEEDS = {
    "Economic Times - Markets": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "Mint - Markets": "https://www.livemint.com/rss/markets",
    "Mint - Economy": "https://www.livemint.com/rss/economy",
    "Moneycontrol - Business": "https://www.moneycontrol.com/rss/business.xml",
}


def is_recent(ts: float) -> bool:
    return (time.time() - ts) <= MAX_AGE_HOURS * 3600


# ---- Finance & economy filter -------------------------------------------
# Only stories whose headline or summary match one of these topics are kept.
# Add or remove words to tune what appears in your paper.
FILTER_ON = True
FINANCE_TERMS = [
    r"stocks?", r"shares?", r"markets?", r"sensex", r"nifty", r"equit(?:y|ies)",
    r"bonds?", r"yields?", r"treasur(?:y|ies)", r"fed(?!\s+up)", r"federal reserve",
    r"rbi", r"central bank\w*", r"ecb", r"boe", r"boj", r"mpc", r"repo",
    r"rates?", r"interest", r"inflation", r"cpi", r"gdp", r"econom\w*",
    r"recession", r"tariffs?", r"trade deficit", r"currenc(?:y|ies)", r"rupee",
    r"dollar", r"euro", r"yen", r"forex", r"fx", r"oil", r"crude", r"brent",
    r"gold", r"silver", r"commodit(?:y|ies)", r"earnings", r"profits?",
    r"revenues?", r"margins?", r"ipo", r"funds?", r"bank\w*", r"invest\w*",
    r"fiscal", r"budget", r"tax\w*", r"gst", r"imf", r"world bank", r"merger",
    r"acquisitions?", r"dividends?", r"crypto\w*", r"bitcoin", r"rally", r"index",
    r"nasdaq", r"s&p", r"dow", r"ftse", r"nikkei", r"hang seng", r"sebi",
    r"fpis?", r"fiis?", r"diis?", r"credit", r"debt", r"loans?", r"payrolls?",
    r"unemployment", r"pmi", r"exports?", r"imports?", r"manufacturing",
    r"fixed income", r"gilts?", r"g-?secs?", r"debentures?", r"ncds?", r"sovereign", r"coupon", r"bunds?", r"jgbs?", r"t-bills?", r"sukuk", r"morning bid", r"valuations?", r"analysts?", r"brokerage", r"target price", r"upper circuit",
]
FINANCE_RE = re.compile(r"\b(?:" + "|".join(FINANCE_TERMS) + r")\b", re.IGNORECASE)


def is_finance(headline: str, summary: str = "") -> bool:
    if not FILTER_ON:
        return True
    return bool(FINANCE_RE.search(f"{headline} {summary}"))


def fetch_finnhub_general() -> list[dict]:
    if not FINNHUB_KEY:
        raise SystemExit("Set the FINNHUB_API_KEY environment variable first.")
    r = requests.get(
        "https://finnhub.io/api/v1/news",
        params={"category": "general", "token": FINNHUB_KEY},
        timeout=20,
    )
    r.raise_for_status()
    items = []
    for a in r.json():
        if not is_recent(a.get("datetime", 0)):
            continue
        if not is_finance(a.get("headline", ""), a.get("summary", "")):
            continue
        items.append({
            "headline": a.get("headline", "").strip(),
            "summary": a.get("summary", "").strip(),
            "source": a.get("source", ""),
            "url": a.get("url", ""),
            "image": a.get("image", ""),
            "ts": a.get("datetime", 0),
        })
    items.sort(key=lambda x: x["ts"], reverse=True)
    return items[:PER_SECTION]


CURRENCIES = [
    ("USD", "US Dollar"), ("EUR", "Euro"), ("GBP", "British Pound"),
    ("JPY", "Japanese Yen"), ("AUD", "Australian Dollar"), ("CAD", "Canadian Dollar"),
    ("CHF", "Swiss Franc"), ("SGD", "Singapore Dollar"), ("AED", "UAE Dirham"),
    ("CNY", "Chinese Yuan"),
]


def fetch_fx() -> list[dict]:
    """Rupees per 1 unit of each currency. Tries Finnhub, then a free fallback."""
    rates = {}
    try:
        r = requests.get(
            "https://finnhub.io/api/v1/forex/rates",
            params={"base": "USD", "token": FINNHUB_KEY},
            timeout=20,
        )
        r.raise_for_status()
        rates = r.json().get("quote", {}) or {}
    except Exception as e:
        print(f"  Finnhub forex failed ({e}); trying fallback...")
    if "INR" not in rates:
        try:
            r = requests.get("https://open.er-api.com/v6/latest/USD", timeout=20)
            r.raise_for_status()
            rates = r.json().get("rates", {}) or {}
        except Exception as e:
            print(f"  Fallback forex failed ({e}).")
            return []
    if "INR" not in rates:
        return []
    out = []
    for code, name in CURRENCIES:
        if code in rates and rates[code]:
            out.append({"code": code, "name": name, "inr": rates["INR"] / rates[code]})
    return out


def fetch_india_rss() -> list[dict]:
    items = []
    for name, url in INDIA_FEEDS.items():
        feed = feedparser.parse(url)
        count = 0
        for e in feed.entries:
            parsed = e.get("published_parsed") or e.get("updated_parsed")
            if not parsed:
                continue
            ts = time.mktime(parsed)
            if not is_recent(ts):
                continue
            if not is_finance(e.get("title", ""), e.get("summary", "") or ""):
                continue
            items.append({
                "headline": e.get("title", "").strip(),
                "summary": (e.get("summary", "") or "").strip(),
                "source": name,
                "url": e.get("link", ""),
                "ts": ts,
            })
            count += 1
        print(f"  {name}: {count} recent items")
    # de-duplicate by headline, newest first
    seen, unique = set(), []
    for it in sorted(items, key=lambda x: x["ts"], reverse=True):
        key = it["headline"].lower()
        if key and key not in seen:
            seen.add(key)
            unique.append(it)
    return unique[:PER_SECTION * 2]


# ---- Fixed income & bond news (Google News search feeds) -------------------
BOND_FEEDS = {
    "india": ("Google News - India bonds",
              "https://news.google.com/rss/search?q=India+bond+yields+OR+G-sec+OR+%22corporate+bonds%22+OR+%22fixed+income%22+when:1d&hl=en-IN&gl=IN&ceid=IN:en"),
    "global": ("Google News - Global bonds",
               "https://news.google.com/rss/search?q=Treasury+yields+OR+%22bond+market%22+OR+%22fixed+income%22+OR+gilts+when:1d&hl=en-US&gl=US&ceid=US:en"),
}


def fetch_bond_news(which: str) -> list[dict]:
    label, url = BOND_FEEDS[which]
    feed = feedparser.parse(url)
    items = []
    for e in feed.entries:
        parsed = e.get("published_parsed") or e.get("updated_parsed")
        if not parsed:
            continue
        ts = time.mktime(parsed)
        title = e.get("title", "").strip()
        if not is_recent(ts) or not is_finance(title):
            continue
        pub = ""
        src = e.get("source")
        if isinstance(src, dict):
            pub = src.get("title", "")
        items.append({
            "headline": title,
            "summary": "",           # Google summaries are just related links
            "source": pub or label,
            "url": e.get("link", ""),
            "image": "",
            "ts": ts,
        })
    print(f"  {label}: {len(items)} recent items")
    return items


def merge(primary: list[dict], extra: list[dict], cap: int) -> list[dict]:
    """Combine two lists, drop duplicate headlines, newest first, keep `cap`."""
    seen, out = set(), []
    for it in sorted(primary + extra, key=lambda x: x["ts"], reverse=True):
        key = re.sub(r"\W+", "", it["headline"].lower())[:50]
        if key and key not in seen:
            seen.add(key)
            out.append(it)
    return out[:cap]


def show(title: str, items: list[dict]) -> None:
    print(f"\n=== {title} ({len(items)}) ===")
    for i, it in enumerate(items, 1):
        when = dt.datetime.fromtimestamp(it["ts"]).strftime("%d %b %H:%M")
        print(f"{i:>2}. [{when}] {it['headline']}  ({it['source']})")


def main() -> None:
    print("Fetching Finnhub global news...")
    global_news = fetch_finnhub_general()

    print("Fetching currency rates...")
    fx = fetch_fx()

    print("Fetching Indian RSS feeds...")
    india_news = fetch_india_rss()

    print("Fetching bond and fixed income news...")
    global_news = merge(global_news, fetch_bond_news("global"), PER_SECTION + 5)
    india_news = merge(india_news, fetch_bond_news("india"), PER_SECTION * 2 + 6)

    show("GLOBAL MARKETS", global_news)
    show("INDIA: MARKETS & ECONOMY", india_news)

    print("\n=== RUPEE EXCHANGE RATES ===")
    for c in fx:
        print(f"  {c['code']}  1 = Rs {c['inr']:.4f}")

    out = {
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "global": global_news,
        "india": india_news,
        "fx": fx,
    }
    with open("news.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("\nSaved news.json")


if __name__ == "__main__":
    main()
