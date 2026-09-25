"""Host-side PD controller for the HVAWG 4-channel HV driver.

Computes a desired output VOLTAGE per channel from a measured height/position
and streams setpoints to the Pico (which clamps, calibrates, and drives the HV).

Run on the PC. The Pico runs pico_test_script/main.py.
Wire your sensor read into read_heights().
"""

import serial
import time

PORT = "COM5"          # <-- set to your Pico's serial port
DT = 0.005             # control period (s). 5ms = 200Hz. USB-CDC jitter dominates;
                       # for a true deterministic kHz loop, move PD onto the Pico.
N = 4


class PD:
    """PD with a low-passed derivative (raw D on a noisy sensor is unusable)."""
    def __init__(self, kp, kd, dt, d_alpha=0.2):
        self.kp, self.kd, self.dt, self.a = kp, kd, dt, d_alpha
        self.prev_e = None
        self.df = 0.0

    def step(self, setpoint, measured):
        e = setpoint - measured
        d = 0.0 if self.prev_e is None else (e - self.prev_e) / self.dt
        self.df = self.a * d + (1 - self.a) * self.df    # filter the D term
        self.prev_e = e
        return self.kp * e + self.kd * self.df           # -> desired VOLTS


def read_heights():
    """Return [h0, h1, h2, h3] from your sensor. STUB -- wire this up."""
    return [0.0] * N


def main():
    pico = serial.Serial(PORT, 115200, timeout=0.01)   # baud irrelevant for USB-CDC
    pd = [PD(kp=2.0, kd=0.05, dt=DT) for _ in range(N)]
    setpoint = [0.0] * N                                # target heights

    def send(volts):
        pico.write(("%.3f,%.3f,%.3f,%.3f\n" % tuple(volts)).encode())

    next_t = time.perf_counter()
    try:
        while True:
            next_t += DT
            h = read_heights()
            v = [pd[ch].step(setpoint[ch], h[ch]) for ch in range(N)]   # volts
            send(v)                                     # Pico clamps to +/-V_MAX
            # (optional) read back "ok,c0,c1,c2,c3" for logging:
            # print(pico.readline().decode().strip())
            time.sleep(max(0.0, next_t - time.perf_counter()))
    except KeyboardInterrupt:
        pico.write(b"z\n")                              # panic stop on exit
        pico.close()


if __name__ == "__main__":
    main()
