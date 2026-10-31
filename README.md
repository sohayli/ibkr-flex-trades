# ibkr-flex-trades

Download your **Interactive Brokers** trade executions through the **Flex Web Service** and export them to CSV —
plus a one-line win rate / expectancy / profit factor summary. One file, Python standard library only, read-only.

```bash
export IBKR_FLEX_TOKEN=...   # Flex Web Service token
export IBKR_FLEX_QUERY=...   # Query ID of an Activity Flex Query with the Trades section
python3 ibkr_flex_trades.py --out trades.csv
```

```
3 executions -> trades.csv
closing fills: 2 | win rate: 50.0% | avg win: 98.00 | avg loss: -40.00
expectancy per closing fill: 29.00 | profit factor: 2.45 | total realized: 58.00
```

Pick the date range per run instead of the one saved in the query (IBKR `p` / `fd`+`td` overrides, max 365 days) —
handy for incremental pulls with no gaps or duplicates:

```bash
python3 ibkr_flex_trades.py --days 7 --out last_week.csv
python3 ibkr_flex_trades.py --from 2026-01-01 --to 2026-06-30 --out h1.csv
```

Offline (a Flex XML you already downloaded from Client Portal):

```bash
python3 ibkr_flex_trades.py --xml examples/sample_flex.xml --out trades.csv
```

## Getting the token and query ID

1. Client Portal → **Performance & Reports → Flex Queries** → create an **Activity Flex Query**.
2. Tick the **Trades** section (Executions), format **XML**, period e.g. *Last 365 Calendar Days*.
3. **Reports → Settings → Flex Web Service** → generate a token.

Step by step, with the sections and fields to tick, how to test the query, and fixes for common errors: **[IBKR Flex Query setup guide](https://fillscope.com/guides/ibkr-flex-query/?utm_source=github&utm_medium=readme&utm_campaign=ibkr-flex-trades)**.

## Notes

- `levelOfDetail` ORDER / summary rows are skipped so partial fills are not double counted.
- P&L is IBKR's `fifoPnlRealized` in each trade's own currency; use `fxRateToBase` for mixed-currency accounts.
- Without `--days`/`--from`/`--to` the period saved in the Flex Query is used. Overrides apply only to that request.
- Flex statements are generated asynchronously; the script polls `GetStatement` until it is ready.
- The token can only read reports. Keep it out of shell history and git (use env vars).

## Want charts instead of a CSV?

[FillScope](https://fillscope.com/?utm_source=github&utm_medium=readme&utm_campaign=ibkr-flex-trades) is a trading
journal that pulls the same Flex Query automatically: equity curve, R-multiples, expectancy by setup, and your
fills drawn on TradingView charts. Free for the last 90 days of history;
[try the demo account](https://fillscope.com/api/auth/demo?utm_source=github&utm_medium=readme&utm_campaign=ibkr-flex-trades) without connecting anything.

Practising setups before you journal them? The
[Chart Workbook](https://fillscope.com/workbook?utm_source=github&utm_medium=readme&utm_campaign=ibkr-flex-trades)
is 30 technical analysis lessons with drills on real charts ($1.99 PDF).

MIT licensed.
