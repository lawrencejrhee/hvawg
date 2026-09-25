# HVAWG 4-channel driver for Raspberry Pi Pico / Pico 2 (MicroPython)
#
# Drives up to 4 daisy-chained boards (4x 74HC595 -> 4x DAC0808) as one 32-bit
# shift chain, converting a commanded HV OUTPUT VOLTAGE per channel into the
# right 8-bit DAC code using per-board calibration.
#
# Wiring (Pico -> J1 input header of the FIRST / nearest board):
#   GP3 -> J1 pin 2  serial_in    (SPI0 MOSI / TX)
#   GP2 -> J1 pin 3  shift_clock  (SPI0 SCK)
#   GP5 -> J1 pin 4  store_clock  (manual GPIO latch, broadcast to all boards)
#   GND -> J1 pin 1  GND          (mandatory common ground)
# Each board's serial_out (74HC595 QH'/pin 9) -> next board's serial_in.
# shift_clock and store_clock are broadcast to every board.
#
# Logic levels: you have ALREADY confirmed 3.3V drive works on this board
# (the DAC sine appeared at TP2 driven by the Pico). The README also states
# 3.3V/5V inputs both work. (Datasheet VIH at VCC=5V is 3.5V, so it's
# technically marginal -- but it's empirically fine here.)

from machine import Pin, SPI
import time

# ---------- PER-CHANNEL CALIBRATION (MEASURE THESE PER BOARD) ----------
# Model is the linear fit of the HV OUTPUT (TP5) vs DAC code, at the ACTUAL
# rails you run (you're at +/-50V):
#         V_out = slope * code + intercept            (code 0..255)
# To command a voltage we invert it:
#         code  = round((V_target - intercept) / slope)
#
# How to get the numbers (see hardware step H2):
#   1. Trim RV2 so code 128 reads ~0V at TP5, RV1 for your full-scale.
#   2. Sweep codes (0,64,128,192,255), read TP5 with a DMM.
#   3. Least-squares fit V_out = slope*code + intercept.
#   The slope is NEGATIVE: the DAC stage inverts, so the output FALLS as the
#   code rises (code 0 -> about +125 V requested, code 128 -> ~0 V,
#   code 255 -> about -124 V). The request is clipped at the actual rails,
#   so at +/-50 V rails only codes ~77..179 are linear.
#   slope     ~= -100 * (DAC V/code) ~= -0.98 V/code (gain ~100, DAC ~2.49 Vpp)
#   intercept ~= volts at code 0 ~= +125 V (extrapolated; beyond the rails)
#   Fit only the codes that are NOT clipped at your rail voltage.
# These are PER BOARD (RV1/RV2 differ) and NOT transferable -- tag to a serial #.
# The values below are PLACEHOLDERS from the design analysis; replace them with
# your board's measured fit before trusting any commanded voltage.
CAL = [
    {"slope": -0.976, "intercept": 125.0},  # ch0 = NEAREST board (last byte shifted)
    {"slope": -0.976, "intercept": 125.0},  # ch1
    {"slope": -0.976, "intercept": 125.0},  # ch2
    {"slope": -0.976, "intercept": 125.0},  # ch3 = FARTHEST board (first byte shifted)
]


class HVAWG:
    NUM_CH     = 4
    V_MAX      = 45.0     # software clamp (V). Keep < rail (~49V) for headroom.
    TIMEOUT_MS = 100      # watchdog: no valid setpoint within this -> failsafe to 0V

    def __init__(self, data_gp=3, clock_gp=2, latch_gp=5, cal=CAL, use_spi=True):
        assert len(cal) == self.NUM_CH, "CAL must have NUM_CH entries"
        self.cal = cal
        self._latch = Pin(latch_gp, Pin.OUT, value=0)
        self._spi = None
        if use_spi:
            # 74HC595 is SPI mode 0 (idle low, sample on rising), MSB-first.
            # GP2 = SPI0 SCK, GP3 = SPI0 TX(MOSI) on RP2040/RP2350 -- required.
            self._spi = SPI(0, baudrate=4_000_000, polarity=0, phase=0,
                            bits=8, firstbit=SPI.MSB,
                            sck=Pin(clock_gp), mosi=Pin(data_gp))
        else:                                    # bit-bang fallback (slower, jittery)
            self._data  = Pin(data_gp,  Pin.OUT, value=0)
            self._clock = Pin(clock_gp, Pin.OUT, value=0)
        self._last_feed = time.ticks_ms()

    # ---- voltage -> code (invert the per-board fit; clamp in VOLTS first) ----
    def volts_to_code(self, ch, v):
        if v >  self.V_MAX: v =  self.V_MAX      # CLAMP before convert (no int wrap!)
        if v < -self.V_MAX: v = -self.V_MAX
        c = self.cal[ch]
        code = int(round((v - c["intercept"]) / c["slope"]))
        if code < 0:   code = 0                   # clip to valid DAC range
        if code > 255: code = 255
        return code

    # ---- low-level: shift all 4 bytes, then ONE atomic latch ----
    def set_codes(self, codes):
        assert len(codes) == self.NUM_CH
        # First byte shifted travels FURTHEST -> lands on the farthest board.
        # So transmit ch3 (farthest) first ... ch0 (nearest) last.
        frame = bytes(codes[i] for i in range(self.NUM_CH - 1, -1, -1))
        self._latch.value(0)                      # outputs hold previous value
        if self._spi:
            self._spi.write(frame)
        else:
            for byte in frame:
                for i in range(7, -1, -1):        # MSB first
                    self._data.value((byte >> i) & 1)
                    self._clock.value(1)          # rising edge shifts the bit
                    self._clock.value(0)
        self._latch.value(1)                      # single rising edge -> all 4 latch
        # leave latch HIGH; next call drives it low before shifting

    # ---- high-level: volts in, HV out ----
    def set_channels(self, volts):
        codes = [self.volts_to_code(ch, volts[ch]) for ch in range(self.NUM_CH)]
        self.set_codes(codes)
        return codes                              # echo applied codes for logging

    def all_zero(self):
        self.set_channels([0.0] * self.NUM_CH)

    # ---- watchdog (feed ONLY on a valid setpoint; never in the failsafe) ----
    def feed(self):
        self._last_feed = time.ticks_ms()

    def expired(self):
        return time.ticks_diff(time.ticks_ms(), self._last_feed) > self.TIMEOUT_MS
