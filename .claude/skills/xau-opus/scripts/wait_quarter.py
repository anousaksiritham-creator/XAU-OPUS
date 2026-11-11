"""wait_quarter.py [MINUTES] - sleep until the next exact clock mark (default every 15 min: :00 :15 :30 :45), then exit.

Run it with the Bash tool in the background: its exit wakes the Claude session on the mark,
which then re-reads the chart (/xau-opus steps 1-5) and starts it again.
"""
import sys
import time
from datetime import datetime, timedelta

step = int(sys.argv[1]) if len(sys.argv) > 1 else 15
now = datetime.now()
nxt = now.replace(second=0, microsecond=0) + timedelta(minutes=step - now.minute % step)
print(f"now {now:%H:%M:%S}, waking at {nxt:%H:%M:%S}", flush=True)
while (left := (nxt - datetime.now()).total_seconds()) > 0:
    time.sleep(min(left, 30))
print(f"MARK {datetime.now():%H:%M:%S}", flush=True)
