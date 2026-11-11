"""place_pair.py - place the xau-opus bracket: a Sell Limit above price and a Buy Limit below, with guards.
Orders carry magic 1055. Orders from xau-mt5 / xau-mt5-v2 (magic 1000) are never cancelled or replaced from here.

  python place_pair.py --sell 4067.5 4082.0 --buy 4021.0 4008.5    # each: ENTRY SL; TP = entry -/+ 1000 points ($10)
  python place_pair.py --sell 4067.5 4082.0                        # one side only, when the other has no setup
  python place_pair.py ... --dry-run      # broker check only, nothing sent
  python place_pair.py ... --replace      # cancel the skill's old pending order(s) first
  python place_pair.py --cancel           # cancel the skill's pending order(s), place nothing

Guards (exit code 3 = refused, nothing sent):
  open position on the symbol; a pending order not placed by the skill; lot above --max-lot;
  an entry on the wrong side of the market; SL on the wrong side; a target that reaches past the
  other side's entry; one side's risk above --max-risk-pct; both sides' risk together above
  --max-total-risk-pct of equity.
Exit code 4 = PARTIAL: the first order is live and the second was rejected by the broker.
Algo Trading: switched on only for the send and restored to its previous state afterwards.
"""
import argparse
import ctypes
import sys
import time
from ctypes import wintypes

import MetaTrader5 as mt5

MAGIC = 1055  # xau-opus only
XAU_MT5_MAGIC = 1000  # xau-mt5 / xau-mt5-v2: their orders count as "not placed by the skill"
POINT_USD = 0.01  # the user's "point" on gold: 1000 points = $10.00 of price

ap = argparse.ArgumentParser()
ap.add_argument("--symbol", default="XAUUSDm")
ap.add_argument("--sell", nargs=2, type=float, metavar=("ENTRY", "SL"))
ap.add_argument("--buy", nargs=2, type=float, metavar=("ENTRY", "SL"))
ap.add_argument("--tp-points", type=int, default=1000)
ap.add_argument("--lot", type=float, default=0.03, help="per order")
ap.add_argument("--max-lot", type=float, default=0.03)
ap.add_argument("--max-risk-pct", type=float, default=20.0, help="one side")
ap.add_argument("--max-total-risk-pct", type=float, default=30.0, help="both stops hit")
ap.add_argument("--expire-hours", type=float, default=8.0, help="0 = good till cancelled")
ap.add_argument("--comment", default="xau-opus")
ap.add_argument("--dry-run", action="store_true")
ap.add_argument("--replace", action="store_true")
ap.add_argument("--cancel", action="store_true")
a = ap.parse_args()


def refuse(msg):
    print("REFUSED:", msg)
    raise SystemExit(3)


def toggle_algo():
    u = ctypes.windll.user32
    found = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    def cb(h, _):
        c = ctypes.create_unicode_buffer(256)
        u.GetClassNameW(h, c, 256)
        if c.value.startswith("MetaQuotes::MetaTrader::5"):
            found.append(h)
        return True

    u.EnumWindows(cb, 0)
    if found:
        u.PostMessageW(found[0], 0x0111, 32851, 0)  # WM_COMMAND: the Algo Trading button
        time.sleep(1.5)


def with_algo(fn):
    was_on = mt5.terminal_info().trade_allowed
    if not was_on:
        toggle_algo()
        if not mt5.terminal_info().trade_allowed:
            refuse("could not switch Algo Trading on; enable it in MT5 and run again")
    try:
        return fn()
    finally:
        if not was_on and mt5.terminal_info().trade_allowed:
            toggle_algo()
        print("algo_trading now:", mt5.terminal_info().trade_allowed, "(before:", was_on, ")")


def cancel_mine(orders):
    for o in orders:
        r = mt5.order_send({"action": mt5.TRADE_ACTION_REMOVE, "order": o.ticket})
        print("cancel", o.ticket, r.retcode if r else mt5.last_error())
        if r is None or r.retcode != mt5.TRADE_RETCODE_DONE:
            refuse(f"could not cancel {o.ticket}")


def show_pending(S):
    names = {mt5.ORDER_TYPE_SELL_LIMIT: "sell_limit", mt5.ORDER_TYPE_BUY_LIMIT: "buy_limit"}
    tags = {MAGIC: "skill", XAU_MT5_MAGIC: "xau-mt5"}
    for o in mt5.orders_get(symbol=S) or []:
        print("pending now:", o.ticket, names.get(o.type, o.type), o.volume_current, o.price_open,
              "SL", o.sl, "TP", o.tp, tags.get(o.magic, "manual"))


def main():
    S = a.symbol
    mt5.symbol_select(S, True)
    info, tick, acc = mt5.symbol_info(S), mt5.symbol_info_tick(S), mt5.account_info()
    orders = list(mt5.orders_get(symbol=S) or [])
    mine = [o for o in orders if o.magic == MAGIC]
    other = [o for o in orders if o.magic != MAGIC]

    if a.cancel:
        if not mine:
            print("no pending order from the skill")
        elif a.dry_run:
            print("dry-run: would cancel", [o.ticket for o in mine])
        else:
            with_algo(lambda: cancel_mine(mine))
            show_pending(S)
        return

    if not a.sell and not a.buy:
        ap.error("give --sell ENTRY SL and/or --buy ENTRY SL")
    if mt5.positions_get(symbol=S):
        refuse(f"a position is already open on {S}")
    if other:
        refuse(f"pending order(s) not placed by the skill: {[o.ticket for o in other]}")
    if mine and not a.replace:
        refuse(f"the skill already has pending order(s) {[o.ticket for o in mine]}; pass --replace to swap")
    if a.lot > a.max_lot:
        refuse(f"lot {a.lot} above max-lot {a.max_lot}")

    legs = []  # sell first, then buy
    for side, pair in (("sell", a.sell), ("buy", a.buy)):
        if not pair:
            continue
        sign = 1 if side == "buy" else -1
        entry, sl = (round(x, info.digits) for x in pair)
        tp = round(entry + sign * a.tp_points * POINT_USD, info.digits)
        if side == "sell" and not entry > tick.bid:
            refuse(f"sell limit {entry} must be above bid {tick.bid}")
        if side == "buy" and not entry < tick.ask:
            refuse(f"buy limit {entry} must be below ask {tick.ask}")
        if sign * (entry - sl) <= 0:
            refuse(f"{side} SL {sl} on the wrong side of entry {entry}")
        otype = mt5.ORDER_TYPE_BUY if side == "buy" else mt5.ORDER_TYPE_SELL
        risk = abs(mt5.order_calc_profit(otype, S, a.lot, entry, sl) or 0)
        reward = abs(mt5.order_calc_profit(otype, S, a.lot, entry, tp) or 0)
        risk_pct = risk / acc.equity * 100 if acc.equity else 999
        print(f"{side.upper()} LIMIT {S} {a.lot} @ {entry}  SL {sl} (${abs(entry - sl):.2f})  "
              f"TP {tp} (${abs(tp - entry):.2f})  risk {risk:.2f} {acc.currency} = {risk_pct:.1f}%  "
              f"reward {reward:.2f}  RR {reward / risk if risk else 0:.2f}")
        if risk_pct > a.max_risk_pct:
            refuse(f"{side} risk {risk_pct:.1f}% above max-risk-pct {a.max_risk_pct}")
        req = {"action": mt5.TRADE_ACTION_PENDING, "symbol": S, "volume": a.lot,
               "type": mt5.ORDER_TYPE_BUY_LIMIT if side == "buy" else mt5.ORDER_TYPE_SELL_LIMIT,
               "price": entry, "sl": sl, "tp": tp, "deviation": 20, "magic": MAGIC,
               "comment": f"{a.comment} {side}"[:31],
               "type_filling": mt5.ORDER_FILLING_RETURN, "type_time": mt5.ORDER_TIME_GTC}
        if a.expire_hours > 0:
            req["type_time"] = mt5.ORDER_TIME_SPECIFIED
            req["expiration"] = int(tick.time + a.expire_hours * 3600)
        legs.append({"side": side, "entry": entry, "tp": tp, "risk_pct": risk_pct, "req": req})

    if len(legs) == 2:
        s, b = legs
        if not (s["tp"] > b["entry"] and b["tp"] < s["entry"]):
            refuse(f"entries too close: sell TP {s['tp']} must stay above buy entry {b['entry']} "
                   f"and buy TP {b['tp']} below sell entry {s['entry']}")
        total = s["risk_pct"] + b["risk_pct"]
        print(f"both stops hit: {total:.1f}% of equity")
        if total > a.max_total_risk_pct:
            refuse(f"total risk {total:.1f}% above max-total-risk-pct {a.max_total_risk_pct}")
    if a.expire_hours > 0:
        print(f"expires {a.expire_hours} h after the last tick")

    def send():
        for leg in legs:  # every leg passes the broker check before anything is sent
            chk = mt5.order_check(leg["req"])
            if chk is None or chk.retcode != 0:
                refuse(f"broker check failed on {leg['side']}: "
                       f"{chk.retcode if chk else mt5.last_error()} {chk.comment if chk else ''}")
        if a.dry_run:
            print(f"DRY-RUN OK: broker check passed for {len(legs)} order(s), nothing sent")
            return
        if mine:
            cancel_mine(mine)
        placed = []
        for leg in legs:
            r = mt5.order_send(leg["req"])
            if r is None or r.retcode not in (mt5.TRADE_RETCODE_DONE, mt5.TRADE_RETCODE_PLACED):
                msg = (f"order_send failed on {leg['side']}: "
                       f"{r.retcode if r else mt5.last_error()} {r.comment if r else ''}")
                if placed:
                    print(f"PARTIAL: {msg}; still live: {placed}")
                    raise SystemExit(4)
                refuse(msg)
            placed.append(r.order)
            print("PLACED", leg["side"], "ticket", r.order)

    try:
        with_algo(send)
    finally:
        show_pending(S)


if not mt5.initialize():
    sys.exit(f"MT5 not reachable: {mt5.last_error()}")
try:
    main()
finally:
    mt5.shutdown()
