---
name: xau-opus
description: Gold on the user's running MT5, two-sided - analyse live price action, draw both plans, place a Sell Limit above and a Buy Limit below (0.03 lot, 1000-point target), cancel the other side when one fills, follow the trade to TP/SL, and re-read the chart every 15 minutes on the exact quarter-hour, replacing the orders when the structure changes.
disable-model-invocation: true
---

# xau-opus · analyse, draw, place the bracket

Typing `/xau-opus` is the user's standing instruction to run every step below to the end, including sending the real limit orders of the **bracket** (one Sell Limit above price, one Buy Limit below), with no confirmation question. Reply in Lao.

Arguments (optional, free text): a symbol (default `XAUUSDm`), a lot per order (default and ceiling 0.03, set by the user on 2026-11-11; a larger lot only when the user wrote the number in this invocation, passed as `--lot X --max-lot X`), `analyse only` / `ວິເຄາະຢ່າງດຽວ` (skip step 5).

Scripts live in `scripts/` beside this file; run them with `python`. They attach to the MT5 terminal that is already open.

## The bracket contract

| Item | Value |
|---|---|
| Orders | One Sell Limit above price **and** one Buy Limit below, sent together; each is its own plan with its own stop and target |
| Target | **1000 points = 10.00 USD of price** from each entry. The script applies it |
| Stop | **Structural**, per side: beyond the swing or zone whose break proves that side wrong, plus a spread buffer; at most 15 USD |
| Spacing | Each target ends before the other entry: `sell entry - buy entry > 10 USD` |
| Size | 0.03 lot per order (1 USD of price = 3 USD of P/L). With equity near 120 USD the 20% cap allows a stop of about 8 USD per side, and the 30% cap allows about 12 USD of stop distance for both sides together |
| Order life | 8 hours (`--expire-hours`, one value for both), shortened to end before a tier-1 US release or the daily close when one is nearer |
| Exposure | One bracket at a time on the symbol. This skill's orders carry magic 1055 and the tag `skill`; orders of the `xau-mt5` skills (magic 1000) are tagged `xau-mt5` and are never touched from here |
| After a fill | **One cancels the other**: `scripts/watch.py` cancels the remaining side as soon as one side fills, then follows the position until TP or SL. It works only while its process runs; both sides filling before the cancel lands (a spike through both) is the worst case, still capped at 30% of equity by `place_pair.py` |

## Steps

### 1. Snapshot

`python scripts/snapshot.py [SYMBOL]`

Done when you hold: bid/ask and spread, account type and equity, open positions and pending orders, each with an owner tag (`skill`, `xau-mt5` or `manual`; the tag comes from the magic number, not from the MT5 order comment), the EMA/ATR table, ADR vs today's range, candles D1→M5, unfilled FVGs, swings. If MT5 is unreachable or the last tick is stale because the market is closed, report that and stop.

### 2. Existing exposure

- **Open position on the symbol** (any owner) → place nothing. Analyse and draw anyway, and report whose position it is and how it sits against the new read.
- **Pending order tagged `manual` or `xau-mt5`** → place nothing and cancel nothing; it belongs to the user or to the other skill. Analyse, draw, report whose order it is.
- **Pending order(s) tagged `skill`** → carry on; step 5 decides keep or replace.
- **None** → carry on.

### 3. Analyse — discretionary, read this tape, once per side

There is no rulebook and no fixed setup family. Work top-down (D1 → H4 → H1 → M15 → M5) and let the current regime choose the method for each side:

- **Trending** → with-trend side: pullback into the last origin of displacement (FVG, broken structure, EMA20/50 zone). Counter-trend side: only at a higher-timeframe level (D1/H4 zone, prior day or week extreme) where a reaction of 10 USD is realistic.
- **Ranging** → fade both range edges after a sweep; targets back inside.
- **After an impulse or news spike** → one side is the first pullback or retest of the broken level; the other is the exhaustion level the impulse is heading into.
- **Compression / inside days** → the edges that liquidity sits behind; smaller expectation.
- **Stretched** (today's range well beyond ADR, price far from H1 EMA20) → continuation has less fuel; set the with-move entry deeper.

Use whatever the chart offers: structure breaks, liquidity sweeps, prior day and week extremes, round numbers, session opens (Asia, London, New York in server time), volatility. Weigh them; quote the two or three that decide each side.

**How to weigh the read.** This is a way of reading, not a rulebook; the tape can overrule it, but say why when it does.

- **Picture first.** Before any level, say in one sentence what the market is doing: yesterday's move, today's range against ADR, and where price sits inside today's range. That sentence names the regime.
- **H4 and H1 decide direction; M15 and M5 time the entry.** A bounce or breakout on M15/M5 against H4/H1 is noted as the timeframe that disagrees, and it does not flip which side is with-trend. A lower-timeframe move becomes the read only after H1 structure has broken with it.
- **With-trend side close to price,** in the nearest zone where several things overlap (FVG, EMA20/50, the origin of the last displacement, broken structure). Overlap is the reason for the entry; a deeper entry chosen only for a tighter stop or a better ratio is not.
- **Counter-trend side far, at a higher-timeframe level, and beyond liquidity.** Put it past the pool that sits there (today's low or high, equal lows or highs, prior day extreme) so it fills only after that pool is swept, at an H4/D1 zone. Accept that it may not fill; an order that misses is a fine result.
- **One structure per stop.** Name the single level whose break means the idea is wrong (for a with-trend side, usually the origin of the displacement it is pulling back into) and put the stop beyond it.
- **Say the weak points** in the report: a ratio under 1, a fact the search could not confirm, a step that did not confirm.

Run one `WebSearch` (standard mode) for today's tier-1 US releases and Fed speakers with times. A release inside the order's life shortens the life to end before it, or kills the setup.

Each side is a plan of its own, complete when every line holds a number or a named level:

1. Side, with the timeframes that agree and the one that disagrees.
2. Entry: a limit price inside a named zone, on the far side of current price.
3. Stop: the structural level, its distance in $, and what a break there would mean.
4. Path to target: the 10 USD between entry and TP checked for opposing levels. A strong opposing level inside the path means move the entry deeper or drop the side.
5. Invalidation before fill: the price or event that makes the order stale.
6. Risk: $ and % of equity at the lot in use (0.03 unless the user wrote another).

Then check the bracket as a whole: spacing above 10 USD, and both stops together within 30% of equity. When the pair fails either check, keep the side the higher timeframes favour and drop the other.

**A side with no clean plan is dropped.** Drop it when the tape gives no entry with a clean 10 USD path, or when the stop needed is wider than 15 USD. The result is then a single order; with both sides dropped, or a tier-1 release too close, the result is **"ບໍ່ມີ SETUP"**, which is a full result: draw the key levels only, and in step 5 cancel stale skill orders if any exist.

### 4. Draw

`python scripts/draw.py SYMBOL "price:kind:label" ...` — kind `R` red, `S` blue, `P` gold; ASCII labels. One call carries both sides; each run replaces this skill's previous drawing. The lines are dashed and come from the `XAU_Levels_Opus` indicator; solid lines on the chart belong to the `xau-mt5` skills and stay as they are.

Draw per side: `P` entry (`SELL LIMIT 4066.0`, `BUY LIMIT 4021.0`), its SL (`SELL SL`, `BUY SL`) and TP (`SELL TP`, `BUY TP`) with the sell side's SL in `R` and TP in `S`, the buy side's SL in `S` and TP in `R`; then the two to four levels the analysis leaned on.

Done when the script prints `CONFIRMED on chart`. On `NOT CONFIRMED`, take `powershell -File scripts/screenshot.ps1 -act shot` and read `scripts/s.png`; if the dashed lines are missing, attach the `XAU_Levels_Opus` indicator following [`ATTACH-INDICATOR.md`](ATTACH-INDICATOR.md), then rerun the draw.

### 5. Place

Always `--dry-run` first, then the same command without it. Each side is `ENTRY SL`; give only the sides that survived step 3.

```
python scripts/place_pair.py --symbol SYMBOL --sell 4067.5 4082.0 --buy 4021.0 4008.5 [--expire-hours 6] [--replace]
```

- **No skill order pending** → place.
- **Skill orders pending, new bracket is the same idea on every side** (same sides, each entry within 2 USD, same stop logic) → keep them; say so.
- **Skill orders pending, anything changed** (structure, zone, a side added or dropped) → add `--replace` at once, with no question; it swaps the whole set for the new bracket. The user gave this standing approval on 2026-11-11.
- **No setup, skill orders pending and stale** → `python scripts/place_pair.py --cancel`.

The script refuses (exit 3) on an open position, a pending order that is not this skill's (manual or `xau-mt5`), a lot above the ceiling, an entry on the wrong side of price, spacing of 10 USD or less, one side's risk above 20% of equity, or both sides' risk above 30%. A refusal is final for this run: report its message verbatim rather than working around it. Exit 4 `PARTIAL` means the sell order is live and the broker rejected the buy: report both facts and leave the live order as it is. The script switches Algo Trading on for the send and restores the previous state.

Done when the script prints `PLACED` for each side sent and the `pending now:` lines show entry, SL and TP matching the plan.

### 6. Watch (one cancels the other, follow to TP/SL)

Whenever skill orders are pending or a skill position is open after step 5 (placed, kept or replaced), start the watcher with the Bash tool and `run_in_background: true`:

```
python scripts/watch.py --symbol SYMBOL
```

It cancels the other side the moment one side fills, follows the position, and exits with one final line: `DONE` (closed by TP, SL or other, with net P/L), `NO-FILL` (orders expired or cancelled), `BOTH-FILLED` (exit 5), or `TIMEOUT`. `ALREADY-WATCHING` means one is running already; that is fine. Its exit wakes the session: read its output and report the outcome in Lao. Do not poll it.

### 7. Re-read every 15 minutes, on the exact mark

The user chose (2026-11-11) a re-read every 15 minutes at exactly :00, :15, :30 and :45 local time. Cron and `/loop` jobs drift several minutes off the mark, so use the timer script instead. At the end of every run, start it with the Bash tool and `run_in_background: true` unless one is already running:

```
python scripts/wait_quarter.py 15
```

It exits with `MARK HH:MM:SS` on the mark, and that exit wakes the session. On a wake:

1. Start `wait_quarter.py` again first, so the next mark is never missed.
2. Repeat steps 1-5 on the new snapshot. Run the news `WebSearch` again only when the last one is more than 4 hours old or a release is near. Redraw only when a level changed.
3. Decide per step 5: keep (same idea), `--replace` at once (the structure or read changed: a new swing high or low, a new FVG or origin of displacement, an H1 break, a side that became clean or stopped being clean), or `--cancel` (setup gone).
4. Check that `watch.py` is running whenever skill orders or positions exist; start it if not (`ALREADY-WATCHING` is fine).
5. Report in a few Lao lines: time, price, keep / replaced / cancelled and why, the orders now live.

The watcher tracks by magic number, so a replace does not stop it. Once a position is open, `place_pair.py` places nothing; a re-read then reports how the open trade sits against the new read. Moving the stop or target of an open position is not part of this skill: say what you would change and leave it to the user. Both timers stop if the session closes or the PC sleeps.

### 8. Report (Lao, short)

Lead with the outcome: bracket placed (per side: ticket, entry, SL, TP; expiry in Laos time), one side only, kept, replaced, cancelled, or no setup. Then one table with a row per side, the two or three reasons for each side, each invalidation, the risk per side and with both stops hit in $ and %, and whether the drawing was confirmed. State plainly anything that failed or was skipped, including a dropped side and why. Say when the orders expire and whether the watcher is running: the cancel of the other side depends on it, and it stops if this session closes or the PC sleeps.
