# XAUUSD for Opus 5.5

Test project: a clone of the `xau-mt5-v2` skill (taken 2026-11-11), run on Claude Opus 5.5 to see how it performs before Fable 5.2 stops being included on the user's plan (2026-11-16 PT).

- The skill is `/xau-opus`, in `.claude/skills/xau-opus/`. The original `~/.claude/skills/xau-mt5-v2` stays untouched; change only this copy.
- `.claude/settings.json` pins this project to `claude-opus-5-5`.
- The scripts attach to the user's running MT5 terminal: a REAL Exness account. `place_pair.py` without `--dry-run` sends real orders.
- Separated from the original on 2026-11-11 at the user's request, so the two cannot interfere. They still share the one account, but this skill has its own magic number (1055; the original uses 1000), its own drawing file (`levels_opus_<SYMBOL>.csv`) and its own indicator (`XAU_Levels_Opus`, dashed lines, object prefix `LVO_`). `--replace` and `--cancel` from here touch only magic-1055 orders. `snapshot.py` tags the original's orders `xau-mt5`; while one is pending, this skill places nothing. The original was not changed, so it sees this skill's orders as `manual` and also places nothing.
- `XAU_Levels_Opus.ex5` is compiled into the terminal's `MQL5\Indicators` and attached to the XAUUSDm M15 chart (2026-11-11). `draw.py` still prints `NOT CONFIRMED` even though the dashed lines show; check with a screenshot.
- The user chose (2026-11-11) to keep the guards: the two skills block each other on the shared account, and the user removes the other skill's orders by hand when they want `/xau-opus` to place.
- Orders sent from here carry the comment `xau-opus sell` / `xau-opus buy`; the original's carry `xau-mt5-v2 ...`. That is how to tell them apart in MT5 history.
- For a comparison run that sends nothing: `/xau-opus analyse only`.

## Where things stand (written 2026-11-11, before the chat was cleared)

**What the user wants:** keep trading the gold bracket skill after Fable 5.2 leaves their Pro plan (included until 2026-11-16 23:59 PT, about 14:59 on 17 Nov Laos time; capped at 50% of weekly limits; afterwards usage credits only). From then on Opus 5.5 runs the skill alone, so this copy must give Opus everything it needs to read the market as carefully as Fable did.

**Decisions the user made in that chat**
- The analysis stays discretionary and follows current market conditions. No rulebook, no fixed setups, no script that decides for the model. The user objected when rule-like helpers were proposed.
- Scripts may add facts and arithmetic only; they report, they never veto. The existing guards in `place_pair.py` stay as they are.
- Work happens in this copy. Test with `--dry-run` or `/xau-opus analyse only`.

**Proposed work, in order (the user has not yet said "start" on any of it)**
1. `snapshot.py`: print ready-made key levels (equal highs/lows, prior day and week extremes, session opens, round numbers, each with distance from price) and the expiry of pending orders.
2. New `check_plan.py`, report-only: for each side's entry and SL, show SL distance, risk in $ and % of equity, spacing, and the levels sitting inside the $10 path.
3. `draw.py`: it printed `NOT CONFIRMED` on 2026-11-11 although the lines were on the chart, and the sell SL was off-screen. Make confirmation reliable.
4. A run journal (CSV): time, model, each side's entry/SL/reasons, filled or not, TP/SL outcome. This is the only way to compare Fable and Opus with numbers; no win/loss record exists yet.
5. Before 16 Nov: run Opus here with `/xau-opus analyse only` on the same market Fable reads with `/xau-mt5-v2`, compare, and tighten `SKILL.md` where Opus misreads or skips a step.

**Done 2026-11-11:** first Opus run (`analyse only`) compared with Fable's bracket of the same day. Opus leaned on M15 momentum where Fable let H4/H1 decide, so at the user's request `SKILL.md` step 3 gained "How to weigh the read" (Fable's way of weighing: picture first, H4/H1 decide direction, with-trend side close, counter-trend side far beyond liquidity, one structure per stop). `XAU_Levels_Opus` is now attached to the XAUUSDm M15 chart; `draw.py` still prints `NOT CONFIRMED` while the lines show.

**Not done:** the `model` value in `.claude/settings.json` is unverified (check with `/model`). `D:\ANS\Claude\XAUUSD` (old indicator, backtest data, tools) was not copied. No git repo in this folder.

**Live state at the time of writing:** equity $120, no position, one bracket pending from `/xau-mt5-v2`: sell limit 978927483 at 4066.5 (SL 4081.2, TP 4056.5) and buy limit 978927484 at 4022.5 (SL 4011.8, TP 4032.5), both expiring 17:39 Laos time on 2026-11-11. Run `snapshot.py` for the current truth.

**Changed 2026-11-11 (evening, user approved):** default and ceiling lot is now 0.03 (`place_pair.py` defaults and `SKILL.md`). New `scripts/watch.py`: one-cancels-other (cancels the remaining magic-1055 side as soon as one fills) and follows the position to TP/SL; it runs as a background process and works only while it runs (lock file `watch_<SYMBOL>.pid`). `SKILL.md` gained step 6 Watch. `$10`-style text in `SKILL.md` was rewritten as `10 USD` because skill arguments were being substituted into `$N` (the `$10` target showed as a word from the user's arguments). The 20%/30% risk guards were kept: at 0.03 lot and ~120 USD equity they allow about 8 USD of stop per side and about 12 USD for both sides together, so a two-sided bracket rarely fits.
