"""snapshot.py [SYMBOL] - live multi-timeframe picture of a symbol from the running MT5 terminal (read-only)."""
import sys
from datetime import datetime, timedelta, timezone

import MetaTrader5 as mt5
import numpy as np
import pandas as pd

S = sys.argv[1] if len(sys.argv) > 1 else "XAUUSDm"
MAGIC = 1055  # xau-opus
XAU_MT5_MAGIC = 1000  # the xau-mt5 / xau-mt5-v2 skills
TAGS = {MAGIC: "skill", XAU_MT5_MAGIC: "xau-mt5"}  # owner tag by magic number; anything else is manual
if not mt5.initialize():
    sys.exit(f"MT5 not reachable: {mt5.last_error()}")
mt5.symbol_select(S, True)
info, t, acc, term = mt5.symbol_info(S), mt5.symbol_info_tick(S), mt5.account_info(), mt5.terminal_info()
if info is None or t is None:
    sys.exit(f"symbol {S} not available")
srv = datetime.fromtimestamp(t.time, timezone.utc).replace(tzinfo=None)
lao = datetime.now(timezone(timedelta(hours=7))).replace(tzinfo=None)
print(f"== {S}  bid {t.bid}  ask {t.ask}  spread ${t.ask - t.bid:.2f}  digits {info.digits}")
print(f"server time of last tick {srv:%Y-%m-%d %H:%M}   Laos time now {lao:%Y-%m-%d %H:%M}")
print(f"account {acc.login} {acc.server} {'REAL' if acc.trade_mode == 2 else 'DEMO/CONTEST'}  "
      f"balance {acc.balance} equity {acc.equity} {acc.currency}  algo_trading {term.trade_allowed}")
pos = [(p.ticket, "buy" if p.type == 0 else "sell", p.volume, p.price_open, p.sl, p.tp, p.profit,
        TAGS.get(p.magic, "manual"))
       for p in mt5.positions_get(symbol=S) or []]
pend = [(o.ticket, {2: "buy_limit", 3: "sell_limit", 4: "buy_stop", 5: "sell_stop"}.get(o.type, o.type),
         o.volume_current, o.price_open, o.sl, o.tp, TAGS.get(o.magic, "manual"))
        for o in mt5.orders_get(symbol=S) or []]
print("positions:", pos or "none")
print("pending  :", pend or "none")

TF = {"D1": mt5.TIMEFRAME_D1, "H4": mt5.TIMEFRAME_H4, "H1": mt5.TIMEFRAME_H1,
      "M15": mt5.TIMEFRAME_M15, "M5": mt5.TIMEFRAME_M5}
D = {}
for k, v in TF.items():
    df = pd.DataFrame(mt5.copy_rates_from_pos(S, v, 0, 600))
    df["time"] = pd.to_datetime(df.time, unit="s")
    D[k] = df


def ema(s, n):
    return s.ewm(span=n, adjust=False).mean()


def atr(df, n=14):
    pc = df.close.shift()
    tr = np.maximum(df.high - df.low, np.maximum((df.high - pc).abs(), (df.low - pc).abs()))
    return tr.rolling(n).mean()


print("\nTF    close    ema20    ema50   ema200    atr14  ema20-slope(5 bars)")
for k, df in D.items():
    c = df.close
    e20 = ema(c, 20)
    print(f"{k:4s}{c.iloc[-1]:9.2f}{e20.iloc[-1]:9.2f}{ema(c, 50).iloc[-1]:9.2f}{ema(c, 200).iloc[-1]:9.2f}"
          f"{atr(df).iloc[-1]:9.2f}  {e20.iloc[-1] - e20.iloc[-6]:+.2f}")

d = D["D1"]
adr = (d.high - d.low).iloc[-15:-1].mean()
td, prev = d.iloc[-1], d.iloc[-2]
wk = d.iloc[-6:-1]
rng = td.high - td.low
print(f"\nADR14 {adr:.2f}  today range {rng:.2f} ({rng / adr * 100:.0f}% of ADR)  today H {td.high} L {td.low}")
print(f"prev day H {prev.high} L {prev.low} C {prev.close}   last-5-days H {wk.high.max()} L {wk.low.min()}")

cols = ["time", "open", "high", "low", "close"]
for k, n in (("D1", 8), ("H4", 12), ("H1", 24), ("M15", 32), ("M5", 24)):
    print(f"\n{k} last {n} (last row = forming bar)")
    print(D[k].tail(n)[cols].to_string(index=False))

for k in ("H4", "H1", "M15"):
    df = D[k].iloc[:-1].reset_index(drop=True)
    a = atr(df)
    print(f"\nunfilled FVG {k} (last 150 bars):")
    for i in range(max(2, len(df) - 150), len(df)):
        if df.low[i] > df.high[i - 2]:
            lo, hi, dr = df.high[i - 2], df.low[i], "bull"
        elif df.high[i] < df.low[i - 2]:
            lo, hi, dr = df.high[i], df.low[i - 2], "bear"
        else:
            continue
        if hi - lo < 0.2 * a[i]:
            continue
        after = df.iloc[i + 1:]
        if dr == "bull":
            ext = after.low.min() if len(after) else 9e9
            filled, touched = ext <= lo, ext <= hi
        else:
            ext = after.high.max() if len(after) else 0
            filled, touched = ext >= hi, ext >= lo
        if not filled:
            print(f"  {dr} {lo:.2f}-{hi:.2f} (${hi - lo:.2f}) formed {df.time[i - 1]} "
                  f"{'partly filled' if touched else 'fresh'}")

for k, n in (("H4", 60), ("H1", 120), ("M15", 96)):
    df = D[k]
    h, l = df.high.values, df.low.values
    out = []
    for i in range(len(df) - n, len(df) - 3):
        if h[i] == max(h[i - 3:i + 4]):
            out.append(f"H {df.time[i]:%m-%d %H:%M} {h[i]}")
        if l[i] == min(l[i - 3:i + 4]):
            out.append(f"L {df.time[i]:%m-%d %H:%M} {l[i]}")
    print(f"\nswings {k}: " + " | ".join(out))
mt5.shutdown()
