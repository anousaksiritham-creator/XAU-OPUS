# xau-opus

A Claude Code skill for gold (XAUUSD) on a running MetaTrader 5 terminal. It reads live price action, draws the plan on the chart, and places a **bracket**: one Sell Limit above price and one Buy Limit below, sent together, each with a 1000-point ($10.00) target and its own structural stop.

Standalone: it needs nothing from the `xau-mt5` / `xau-mt5-v2` skills and never touches their orders or drawings. Its orders carry magic 1055 (theirs: 1000), and it draws through its own indicator `XAU_Levels_Opus` and its own file `levels_opus_<SYMBOL>.csv`. They still share one account: a pending order or open position from the other skills makes this one place nothing until it is gone.

> This skill sends real orders with no confirmation question. Trading leveraged gold can lose the whole account. Use a demo account until you trust it.

## Install

1. Copy this folder to `<project>/.claude/skills/xau-opus`.
2. `pip install MetaTrader5` (Windows, Python 3.12).
3. Open MT5 and log in. Compile `indicator/XAU_Levels_Opus.mq5` into `MQL5\Indicators` and attach it to the chart once, following `ATTACH-INDICATOR.md`.

## Use

In Claude Code type `/xau-opus`. Optional free-text arguments: a symbol (default `XAUUSDm`), a lot per order (default and ceiling 0.03), `analyse only`.

## Contract

| Item | Value |
|---|---|
| Orders | Sell Limit above and Buy Limit below; a fill on one side cancels the other (watch.py) |
| Target | 1000 points = $10.00 of price from each entry |
| Stop | Structural, at most $15 per side |
| Spacing | Sell entry more than $10 above buy entry |
| Size | 0.03 lot per order |
| Risk caps | 20% of equity per side, 30% with both stops hit |
| Order life | 8 hours, shorter before a tier-1 US release or the daily close |

A side with no clean plan is dropped, so a run can end with two orders, one, or none. After one side fills, `scripts/watch.py` cancels the other side (one cancels the other) and follows the trade to TP or SL; this works only while the watcher process runs.

While orders are pending, Claude re-reads the chart every 15 minutes on the exact quarter-hour (`scripts/wait_quarter.py`) and replaces the orders at once when the structure changes, or cancels them when the setup is gone.

## Files

- `SKILL.md`: the steps Claude follows.
- `scripts/snapshot.py`: market and account snapshot.
- `scripts/draw.py`: writes levels for the `XAU_Levels_Opus` indicator and confirms the redraw.
- `scripts/place_pair.py`: guarded order placement (`--dry-run`, `--replace`, `--cancel`).
- `scripts/watch.py`: one-cancels-other after a fill, follows the position to TP/SL.
- `scripts/wait_quarter.py`: sleeps until the next :00/:15/:30/:45 and exits, to wake the session for a re-read.
- `scripts/screenshot.ps1`: screenshot and click helper for attaching the indicator.
- `indicator/XAU_Levels_Opus.mq5`: draws the levels on the chart (dashed lines).
