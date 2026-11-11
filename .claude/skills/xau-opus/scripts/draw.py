"""draw.py SYMBOL "price:kind:label" ...   kind = R (red) | S (blue) | P (gold)
draw.py SYMBOL --clear

Writes MQL5\\Files\\levels_opus_<SYMBOL>.csv; the XAU_Levels_Opus indicator on the chart redraws within 5 s.
(The xau-mt5 skills use levels_<SYMBOL>.csv and the XAU_Levels indicator; the two drawings do not touch.)
Then waits for the indicator's "drew N levels" log line to confirm the chart really updated.
Exit 0 = confirmed on chart, 2 = file written but redraw not confirmed.
"""
import os
import sys
import time
from datetime import datetime

import MetaTrader5 as mt5

sym, items = sys.argv[1], sys.argv[2:]
if not mt5.initialize():
    sys.exit(f"MT5 not reachable: {mt5.last_error()}")
data = mt5.terminal_info().data_path
mt5.shutdown()

rows = []
if items != ["--clear"]:
    for it in items:
        price, kind, label = (it.split(":", 2) + ["P", ""])[:3]
        label = label.replace(";", ",").encode("ascii", "replace").decode()
        rows.append((float(price), kind.upper() or "P", label or kind))
path = os.path.join(data, "MQL5", "Files", f"levels_opus_{sym}.csv")
t0 = datetime.now()
with open(path, "w", encoding="ascii", newline="\n") as f:
    f.write("# price;label;kind(S/R/P)\n")
    for p, k, lab in sorted(rows, reverse=True):
        f.write(f"{p};{lab};{k}\n")
print(f"wrote {len(rows)} levels -> {path}")

log = os.path.join(data, "MQL5", "Logs", f"{t0:%Y%m%d}.log")
want = f"XAU_Levels_Opus ({sym},"
for _ in range(25):
    time.sleep(1)
    try:
        with open(log, encoding="utf-16-le", errors="ignore") as f:
            hits = [ln for ln in f if want in ln and "drew" in ln]
    except OSError:
        hits = []
    for ln in reversed(hits):
        parts = ln.split("\t")
        if len(parts) > 2 and parts[2][:8] >= f"{t0:%H:%M:%S}":
            print("CONFIRMED on chart:", parts[-1].strip())
            sys.exit(0)
print(f"NOT CONFIRMED: no redraw line in the MT5 log within 25 s. "
      f"The log can lag, or XAU_Levels_Opus is not attached to a {sym} chart.")
sys.exit(2)
