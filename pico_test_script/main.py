# Pico firmware: watchdog'd 4-channel DAC server (Option C).
# The HOST computes the PD control and sends 4 setpoint voltages per update;
# the Pico clamps, calibrates, shifts all 4 bytes, latches once, and parks the
# outputs at 0V if the host goes silent.
#
# Protocol over USB serial:
#   host -> Pico : "v0,v1,v2,v3\n"  (volts; out-of-range is clamped, not rejected)
#                  "z\n"            (panic stop -> all 0V)
#   Pico -> host : "ok,c0,c1,c2,c3\n"  (codes actually latched)  or  "err,..."

import sys, select, time
from hvawg_driver import HVAWG

hv = HVAWG(use_spi=True)
hv.all_zero()

poll = select.poll()
poll.register(sys.stdin, select.POLLIN)
line = ""

def handle(cmd):
    global line
    cmd = cmd.strip()
    if cmd == "z":                          # panic stop
        hv.all_zero(); hv.feed()
        print("ok,stop"); return
    parts = cmd.split(",")
    if len(parts) != 4:
        print("err,malformed"); return
    try:
        v = [float(p) for p in parts]
    except ValueError:
        print("err,nan"); return
    codes = hv.set_channels(v)              # clamp + cal + 4-byte + single latch
    hv.feed()                              # feed watchdog ONLY on a valid setpoint
    print("ok,%d,%d,%d,%d" % tuple(codes))

while True:
    # Drain ALL characters available this tick (not one-per-poll -> no throttle).
    while poll.poll(0):                     # 0ms = non-blocking: any char ready?
        ch = sys.stdin.read(1)
        if ch == "\n":
            handle(line); line = ""
        elif ch:
            line += ch
    if hv.expired():                        # host silent -> FAILSAFE (do NOT feed)
        hv.all_zero()
    time.sleep_ms(1)                        # ~1 kHz service tick
