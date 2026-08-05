#!/usr/bin/env python3
"""Fetch delayed quotes for the page's tickers and write live.json.

Runs on a GitHub Actions runner every ~10 minutes during US market hours. Server-side on
purpose: browsers can't call quote APIs directly (CORS), and putting an API key in a
public page would leak it. This uses Yahoo's public chart endpoint, which needs no key.

Quotes may be delayed up to 15 minutes; the page says so. Output is display-ready strings
so the page's JS stays dumb: it swaps text, it does not do finance.
"""
import json
import time
import pathlib
import urllib.parse
import urllib.request

OUT = pathlib.Path(__file__).resolve().parent.parent / "live.json"

# key -> (yahoo symbol, formatter)
def _idx(v):   return format(v, ",.2f")            # 7,741.20
def _usd(v):   return "$" + format(v, ",.2f")      # $724.10
def _vix(v):   return format(v, ".2f")
def _yld(v):   return format(v, ".2f") + "%"

TICKERS = {
    "spx":   ("^GSPC", _idx),
    "ndx":   ("^NDX",  _idx),
    "dow":   ("^DJI",  _idx),
    "vix":   ("^VIX",  _vix),
    "us10y": ("^TNX",  None),   # special: divide by 10
    "us30y": ("^TYX",  None),
    "qqq":   ("QQQ",   _usd),
    "nvda":  ("NVDA",  _usd),
    "soxl":  ("SOXL",  _usd),
    "cost":  ("COST",  _usd),
}


def fetch(symbol):
    url = ("https://query1.finance.yahoo.com/v8/finance/chart/"
           + urllib.parse.quote(symbol) + "?interval=1d&range=1d")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        meta = json.load(r)["chart"]["result"][0]["meta"]
    return float(meta["regularMarketPrice"]), float(meta.get("chartPreviousClose") or meta.get("previousClose") or 0)


def main():
    quotes = {}
    for key, (sym, fmt) in TICKERS.items():
        try:
            price, prev = fetch(sym)
            if key in ("us10y", "us30y"):
                # Yahoo's chart meta returns ^TNX/^TYX already in percent (4.62, 5.17) —
                # NOT the CBOE x10 convention. Verified against raw responses; a /10 here
                # once produced "0.46%" on the page.
                disp = _yld(price)
            else:
                disp = fmt(price)
            q = {"v": disp}
            if prev > 0:
                pct = (price / prev - 1) * 100
                q["d"] = round(pct, 2)
                q["s"] = ("+" if pct >= 0 else "−") + format(abs(pct), ".2f") + "%"
            quotes[key] = q
            time.sleep(0.4)   # be polite
        except Exception as e:               # partial data beats no data
            print("skip %s: %s" % (key, e))

    if len(quotes) < 5:
        raise SystemExit("too few quotes fetched (%d) — not writing" % len(quotes))

    OUT.write_text(json.dumps({
        "t": int(time.time()),
        "quotes": quotes,
    }, separators=(",", ":")), encoding="utf-8")
    print("wrote %s with %d quotes" % (OUT.name, len(quotes)))


if __name__ == "__main__":
    main()
