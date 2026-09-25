# HVAWG DAC test driver for Raspberry Pi Pico / Pico 2 (MicroPython)
#
# Drives the on-board 74HC595 shift register -> DAC0808 to produce a test
# waveform at the DAC output (board test point TP2 / JP3).
#
# Wiring (Pico GPIO  ->  board J1 serial-input header):
#   GP3  (phys pin 5)  -> J1 pin 2  serial_in
#   GP2  (phys pin 4)  -> J1 pin 3  shift_clock
#   GP5  (phys pin 7)  -> J1 pin 4  store_clock
#   GND  (phys pin 3)  -> J1 pin 1  GND   (mandatory common ground)
#
# NOTE: the 74HC595 is powered from the board's 5V rail, so its logic HIGH
# threshold is ~3.5V while the Pico drives 3.3V. This is marginal/out-of-spec.
# If TP2 looks glitchy or bits are missing, that's the likely cause.

from machine import Pin
import math
import time

# --- pin setup (GPIO numbers, not physical pin numbers) ---
DATA  = Pin(3, Pin.OUT)   # GP3 -> serial_in   (J1 pin 2)
CLOCK = Pin(2, Pin.OUT)   # GP2 -> shift_clock  (J1 pin 3)
LATCH = Pin(5, Pin.OUT)   # GP5 -> store_clock  (J1 pin 4)

CLOCK.value(0)
LATCH.value(0)


def shift_byte(value):
    """Clock one 8-bit value into the 74HC595, MSB first, then latch it."""
    LATCH.value(0)
    for i in range(7, -1, -1):          # MSB first (matches Arduino MSBFIRST)
        DATA.value((value >> i) & 1)
        CLOCK.value(1)                  # rising edge shifts the bit in
        CLOCK.value(0)
    LATCH.value(1)                      # rising edge latches to DAC outputs


def dc_test():
    """Step through fixed DC levels so you can verify the DAC with a multimeter.
    Expect TP2 to move in clean steps as each value latches."""
    for v in (0, 64, 128, 192, 255):
        shift_byte(v)
        print("DAC code =", v)
        time.sleep(2)


def sine_test():
    """Continuously output a sine. Scope TP2 -> expect ~2.8Vpp sine."""
    N = 256
    table = [int(128 + 127 * math.sin(2 * math.pi * i / N)) for i in range(N)]
    while True:
        for v in table:
            shift_byte(v)


# Run a slow DC staircase first to confirm basic function, then the sine.
# Comment out whichever you don't want.
if __name__ == "__main__":
    dc_test()      # multimeter sanity check (5 steps, ~10 s)
    sine_test()    # then free-run the sine for the scope
