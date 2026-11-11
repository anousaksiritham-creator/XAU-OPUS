# Attaching XAU_Levels_Opus to a chart

Needed once per chart (a new chart, another symbol, or after the indicator was removed). Changing timeframe on the same chart keeps it.

`XAU_Levels_Opus` is this skill's own indicator (dashed lines, file `levels_opus_<SYMBOL>.csv`). `XAU_Levels` (solid lines) belongs to the `xau-mt5` skills: leave it on the chart, the two do not interfere.

Source: `indicator/XAU_Levels_Opus.mq5` beside this file, installed in the terminal's `MQL5\Indicators\XAU_Levels_Opus.ex5`. If the `.ex5` is missing, copy the `.mq5` there and compile:
`"C:\Program Files\MetaTrader 5\MetaEditor64.exe" /compile:"<mq5>" /log:"<log>"` (log is UTF-16; read the `Result:` line).

GUI steps, driven with `scripts/screenshot.ps1` (`-act click|dbl|rclick|keys|shot -x -y -keys`, screenshot saved to `scripts/s.png`; add `-crop "x,y,w,h"`). Take a screenshot before every click and read coordinates from it; the window moves between sessions.

1. Click the target chart so it is the active one (title bar shows `[SYMBOL,TF]`).
2. `View` menu → `Navigator`.
3. In Navigator, if `XAU_Levels_Opus` is absent under `Indicators`: right-click `Indicators` → `Refresh`.
4. Double-click `XAU_Levels_Opus` → click `OK` in the dialog.
5. Close Navigator (its `x`).
6. Rerun `draw.py`; done on `CONFIRMED on chart`.

Menus scroll with arrow keys sent through `-act keys` (`{UP}` from the top wraps to the end); the mouse wheel and hovering do not scroll them.
