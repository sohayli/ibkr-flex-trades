#!/usr/bin/env python3
"""ibkr_flex_trades.py - download your Interactive Brokers trades via the Flex Web Service
and export them to CSV, with a quick win-rate / expectancy summary.

Standard library only (Python 3.8+). Read-only: the Flex token can only fetch reports.

    export IBKR_FLEX_TOKEN=...   # Flex Web Service token (Reports > Settings > Flex Web Service)
    export IBKR_FLEX_QUERY=...   # Query ID of an Activity Flex Query that includes the Trades section
    python3 ibkr_flex_trades.py --out trades.csv

    python3 ibkr_flex_trades.py --xml saved_statement.xml --out trades.csv   # offline, from a saved XML

Setup guide (token, query ID, which fields to tick):
https://fillscope.com/guides/ibkr-flex-query/?utm_source=github&utm_medium=readme&utm_campaign=ibkr-flex-trades
"""
import argparse
import csv
import os
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

SEND_URL = "https://ndcdyn.interactivebrokers.com/AccountManagement/FlexWebService/SendRequest"
GET_URL = "https://gdcdyn.interactivebrokers.com/AccountManagement/FlexWebService/GetStatement"
UA = "ibkr-flex-trades/1.0 (+https://github.com/sohayli/ibkr-flex-trades)"
# Flex error codes that mean "statement is still being generated, retry"
RETRY_CODES = {"1001", "1004", "1005", "1006", "1007", "1008", "1009", "1018", "1019", "1021"}

FIELDS = [
    "tradeDate", "dateTime", "accountId", "symbol", "assetCategory", "buySell", "openCloseIndicator",
    "quantity", "tradePrice", "currency", "fxRateToBase", "ibCommission", "netCash",
    "fifoPnlRealized", "tradeID", "orderType", "exchange",
]


def _get(url, params):
    req = urllib.request.Request(url + "?" + urllib.parse.urlencode(params), headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def fetch_statement(token, query_id, tries=10, wait=5):
    root = ET.fromstring(_get(SEND_URL, {"t": token, "q": query_id, "v": "3"}))
    if root.findtext("Status") != "Success":
        sys.exit(f"SendRequest failed: {root.findtext('ErrorCode')} {root.findtext('ErrorMessage')}")
    ref = root.findtext("ReferenceCode")
    url = root.findtext("Url") or GET_URL
    for _ in range(tries):
        time.sleep(wait)
        body = _get(url, {"t": token, "q": ref, "v": "3"})
        if b"<FlexQueryResponse" in body[:500]:
            return body
        err = ET.fromstring(body)
        code = err.findtext("ErrorCode") or ""
        if code not in RETRY_CODES:
            sys.exit(f"GetStatement failed: {code} {err.findtext('ErrorMessage')}")
    sys.exit("Statement was not ready in time; run again in a minute.")


def parse_trades(xml_bytes):
    root = ET.fromstring(xml_bytes)
    rows = []
    for t in root.iter("Trade"):
        if t.get("levelOfDetail", "EXECUTION") not in ("EXECUTION", ""):
            continue  # skip ORDER / SYMBOL_SUMMARY rollups so fills are not double counted
        rows.append({f: t.get(f, "") for f in FIELDS})
    rows.sort(key=lambda r: (r["dateTime"] or r["tradeDate"], r["tradeID"]))
    return rows


def summary(rows):
    pnl = []
    for r in rows:
        try:
            v = float(r["fifoPnlRealized"] or 0)
        except ValueError:
            continue
        if v != 0:
            pnl.append(v)
    if not pnl:
        return "No closed trades with realized P&L in this statement."
    wins = [p for p in pnl if p > 0]
    losses = [p for p in pnl if p < 0]
    win_rate = len(wins) / len(pnl)
    avg_w = sum(wins) / len(wins) if wins else 0.0
    avg_l = sum(losses) / len(losses) if losses else 0.0
    expectancy = win_rate * avg_w + (1 - win_rate) * avg_l
    pf = (sum(wins) / -sum(losses)) if losses else float("inf")
    return (
        f"closing fills: {len(pnl)} | win rate: {win_rate:.1%} | avg win: {avg_w:.2f} | avg loss: {avg_l:.2f}\n"
        f"expectancy per closing fill: {expectancy:.2f} | profit factor: {pf:.2f} | total realized: {sum(pnl):.2f}\n"
        "(currency = each trade's own currency; mixed-currency accounts should convert with fxRateToBase)"
    )


def main():
    ap = argparse.ArgumentParser(description="Export IBKR trades from a Flex Query to CSV.")
    ap.add_argument("--token", default=os.environ.get("IBKR_FLEX_TOKEN"))
    ap.add_argument("--query", default=os.environ.get("IBKR_FLEX_QUERY"))
    ap.add_argument("--xml", help="parse a saved Flex XML file instead of downloading")
    ap.add_argument("--out", default="trades.csv")
    a = ap.parse_args()
    if a.xml:
        with open(a.xml, "rb") as f:
            body = f.read()
    else:
        if not a.token or not a.query:
            ap.error("set IBKR_FLEX_TOKEN and IBKR_FLEX_QUERY (or pass --token/--query), or use --xml")
        body = fetch_statement(a.token, a.query)
    rows = parse_trades(body)
    with open(a.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} executions -> {a.out}")
    print(summary(rows))


if __name__ == "__main__":
    main()
