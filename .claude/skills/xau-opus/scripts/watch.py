"""watch.py - one-cancels-other and fill-to-close watch for the xau-opus bracket (magic 1055 only).

  python watch.py [--symbol XAUUSDm] [--poll 1] [--grace 90] [--max-hours 24]

While it runs:
  - as soon as a skill position exists on the symbol, every remaining skill pending order is cancelled
    (the other side of the bracket), so only one trade is ever live;
  - the open position is followed until it closes, and the close is reported as TP, SL or other.
It tracks by magic number, not ticket, so a --replace from place_pair.py does not break it.
Orders of the xau-mt5 skills (magic 1000) and manual orders are never touched.

Exit (prints one final line starting with the word shown):
  0  DONE        a skill position closed (TP / SL / other), nothing of the skill left
  0  NO-FILL     no skill order or position for --grace seconds (expired, cancelled, or none at start)
  0  TIMEOUT     --max-hours reached, orders/position left as they are
  5  BOTH-FILLED both sides filled before the cancel landed; both positions are left with their SL/TP
It needs this process to stay alive: if the PC sleeps or the process is stopped, nothing cancels the other side.
Algo Trading: switched on only for a cancel and restored to its previous state afterwards.
"""
import argparse
import ctypes
import os
import sys
import time
from ctypes import wintypes
from datetime import datetime, timedelta, timezone

import MetaTrader5 as mt5

MAGIC = 1055
LAO = timezone(timedelta(hours=7))

ap = argparse.ArgumentParser()
ap.add_argument("--symbol", default="XAUUSDm")
ap.add_argument("--poll", type=float, default=1.0, help="seconds between checks")
ap.add_argument("--grace", type=float, default=90.0, help="seconds with nothing of the skill before NO-FILL")
ap.add_argument("--max-hours", type=float, default=24.0)
ap.add_argument("--heartbeat-min", type=float, default=15.0)
a = ap.parse_args()
S = a.symbol


def log(*parts):
    print(f"[{datetime.now(LAO):%m-%d %H:%M:%S} Laos]", *parts, flush=True)


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


def cancel(orders):
    """Cancel the given orders; returns the tickets that are still pending afterwards."""
    was_on = mt5.terminal_info().trade_allowed
    if not was_on:
        toggle_algo()
    try:
        for o in orders:
            r = mt5.order_send({"action": mt5.TRADE_ACTION_REMOVE, "order": o.ticket})
            ok = r is not None and r.retcode == mt5.TRADE_RETCODE_DONE
            log("OCO cancel", o.ticket, "ok" if ok else f"FAILED {r.retcode if r else mt5.last_error()}")
    finally:
        if not was_on and mt5.terminal_info().trade_allowed:
            toggle_algo()
    left = {o.ticket for o in mt5.orders_get(symbol=S) or [] if o.magic == MAGIC}
    return [o.ticket for o in orders if o.ticket in left]


def side(p):
    return "buy" if p.type == mt5.POSITION_TYPE_BUY else "sell"


def close_report(ticket, info):
    deals = mt5.history_deals_get(position=ticket) or []
    if not deals:  # history can lag a moment behind the position list
        time.sleep(2)
        deals = mt5.history_deals_get(position=ticket) or []
    outs = [d for d in deals if d.entry in (mt5.DEAL_ENTRY_OUT, mt5.DEAL_ENTRY_OUT_BY)]
    if not outs:
        log("CLOSED", ticket, info["side"], "entry", info["entry"], "- close deal not found in history yet")
        return
    d = outs[-1]
    reason = {mt5.DEAL_REASON_TP: "TP", mt5.DEAL_REASON_SL: "SL", mt5.DEAL_REASON_SO: "STOP-OUT"}.get(
        d.reason, f"other(reason {d.reason})")
    net = sum(x.profit + x.commission + x.swap + getattr(x, "fee", 0.0) for x in deals)
    log(f"CLOSED {ticket} {info['side']} {info['volume']} entry {info['entry']} -> {d.price} "
        f"by {reason}  net {net:+.2f} {mt5.account_info().currency}")


def main():
    t_start = time.time()
    empty_since = None
    seen = {}  # position ticket -> info
    closed_any = False
    both_warned = False
    last_beat = 0.0
    log(f"watching {S} magic {MAGIC}: poll {a.poll}s, grace {a.grace}s, max {a.max_hours}h")
    while True:
        if mt5.terminal_info() is None and not mt5.initialize():
            log("MT5 not reachable, retrying:", mt5.last_error())
            time.sleep(5)
            continue
        orders = [o for o in mt5.orders_get(symbol=S) or [] if o.magic == MAGIC]
        poss = [p for p in mt5.positions_get(symbol=S) or [] if p.magic == MAGIC]

        for p in poss:
            if p.ticket not in seen:
                seen[p.ticket] = {"side": side(p), "entry": p.price_open, "volume": p.volume}
                log(f"FILLED {p.ticket} {side(p)} {p.volume} @ {p.price_open}  SL {p.sl}  TP {p.tp}")
        for t in [t for t in seen if t not in {p.ticket for p in poss}]:
            close_report(t, seen.pop(t))
            closed_any = True

        if len(poss) >= 2 and not both_warned:
            both_warned = True
            log("BOTH-FILLED: two skill positions are open; both keep their own SL/TP")
        if poss and orders:
            left = cancel(orders)
            if left:
                log("OCO cancel incomplete, will retry:", left)

        if not poss and not orders:
            if closed_any:
                log("DONE: the skill position closed and nothing of the skill is left")
                return 5 if both_warned else 0
            empty_since = empty_since or time.time()
            if time.time() - empty_since >= a.grace:
                log("NO-FILL: no skill order or position (expired, cancelled, or none) - watch ends")
                return 0
        else:
            empty_since = None

        now = time.time()
        if now - last_beat >= a.heartbeat_min * 60:
            last_beat = now
            tk = mt5.symbol_info_tick(S)
            flo = sum(p.profit for p in poss)
            log(f"beat: bid {tk.bid if tk else '?'}  pending {[o.ticket for o in orders]}  "
                f"positions {[p.ticket for p in poss]}  floating {flo:+.2f}")
        if now - t_start >= a.max_hours * 3600:
            log("TIMEOUT: max-hours reached; orders and positions left as they are")
            return 0
        time.sleep(a.poll)


def alive(pid):
    k = ctypes.windll.kernel32
    h = k.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
    if not h:
        return False
    code = wintypes.DWORD()
    k.GetExitCodeProcess(h, ctypes.byref(code))
    k.CloseHandle(h)
    return code.value == 259  # STILL_ACTIVE


LOCK = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"watch_{S}.pid")
try:
    other = int(open(LOCK).read().strip())
except (OSError, ValueError):
    other = 0
if other and other != os.getpid() and alive(other):
    print(f"ALREADY-WATCHING: watch.py pid {other} is running for {S}; not starting a second one")
    sys.exit(0)
with open(LOCK, "w") as f:
    f.write(str(os.getpid()))

if not mt5.initialize():
    sys.exit(f"MT5 not reachable: {mt5.last_error()}")
try:
    code = main()
finally:
    mt5.shutdown()
    try:
        os.remove(LOCK)
    except OSError:
        pass
sys.exit(code)
