These are the bringup notes for the V1 boards (A-D, fabbed before the V2 revision). For V2 boards use BRINGUP-V2.md.

The rest of this file is the older bringup procedure, kept as it was. The "v2" in its title is the second version of the procedure, not the V2 board. Some of it is now out of date: V2 J9 is no longer on a tab (it sits in an edge notch), and the gerbers in jlcpcb/ have been regenerated since.

# Bringup Procedure v2 (draft)

Updated staged bringup for the HVAWG board. Supersedes the README "Bringup notes"
for careful/first-article bringup. Key differences from v1: no floating opamp
inputs, staged HV ramps, much tighter current limits, and a defined shutdown
order.

## Quick reference at ±50 V rails (current lab setup)

The procedure below is written for the ±120 V design rails. Current bringup
runs at **±50 V** (E3612A = +HV, E3641A = −HV, triple-output = ±12 V with its
⊥/COM terminal as board GND, floating 12 V on the −100+12V pin: V1 J9 pin 7, V2 J9 pin 8). Scaled expectations:

| Quantity | ±120 V (as written) | ±50 V (current setup) |
|---|---|---|
| TP3 (RV2 = 1.11 kΩ) | ~1.20 V | ~0.50 V |
| TP3 (max possible, RV2 = 4.7 kΩ) | ~4.9 V | ~2.05 V |
| Centered R21 current | 12 mA | 5 mA |
| Initial HV current limit (Phase 4) | 25 mA | ~10 mA |
| Full-scale AC current limit | 35–40 mA | ~15–20 mA |
| Max output swing | ~±118 V | ~±49 V |

### ⚠️ J9 PINOUT DEPENDS ON THE BOARD REVISION — CHECK WHICH BOARD YOU HAVE

**V1 boards (A–D, fabbed before the V2 safety revision)** have a 2.54 mm
8-pin header J9. Count from the square pad:

| V1 J9 pin | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|
| Net | GND | GND | +12V | −12V | GND | +100V (+HV) | −100+12V (floating) | −100V (−HV) |

**V2 boards (safety revision, 2026-09-23)** have a 3.50 mm pluggable
terminal block J9 on the tab at the top edge. **The pin order is DIFFERENT.**
Pin numbers are printed on the silkscreen:

| V2 J9 pin | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|
| Net | GND | +12V | −12V | GND | +100V (+HV) | GND | −100V (−HV) | −100+12V (floating) |

Never reuse a V1 wiring harness on a V2 board. The V2 daisy-chain sockets
also changed (J5/J6: 1 +100V, 2 GND, 3 −100V, 4 −100+12V; J7/J8 are
7-pin: 1 OUT1, 2 GND, 3 OUT2, 4 GND, 5 OUT3, 6 GND, 7 OUT4), so V1 cables
don't fit V2 boards either.

Supply wiring reminders (lessons learned the hard way). The pin numbers below are
**V1 / V2**:
- Every supply connects via its **(+)/(−) output terminals**. The green ⏚
  earth post is NOT an output — using it leaves the rail floating (this
  caused a phantom "TP3 stuck at 6.8 V" reading that looked like a dead U8).
- Triple-output supplies with a ⊥/COM terminal: ⊥ **is** the ground — wire
  ⊥ → board GND, +terminal → +12V (V1 pin 3 / V2 pin 2), −terminal → −12V
  (V1 pin 4 / V2 pin 3). No "flip" needed.
- +HV supply: (+) → +100V (V1 pin 6 / V2 pin 5), (−) → board GND.
- −HV supply: (+) → board GND, (−) → −100V (V1 pin 8 / V2 pin 7).
- Floating 12 V: (−) → −100V (V1 pin 8 / V2 pin 7), (+) → −100+12V (V1 pin 7 /
  V2 pin 8). Must be an isolated output. Third LED confirms it.
- **Jumpers change only with power off and rails discharged** (hot-plugging
  JP4 sparked and nearly killed board #1).

## Bringup log

| Board | Status |
|---|---|
| Board A (original) | Took JP4 hot-plug spark. Output stage suspect (U7/Q1). Parked / parts donor. |
| Board B | Long bringup session: Phases 1–3 passed (TP2 sine, TP3 monitor, TP4 level shift). Phase 4 stalled on level-shifter over-current (TP4 ≈ −14.6 V, suspected RV1 ≈ 0 Ω; never confirmed fixed — swapped out mid-diagnosis). |
| Board C | On −50 V turn-on: −12 rail dragged to −24.9 V, +HV sagged to 30.7 V. Root cause: fried opamp shorting rails. Retired. |
| Board D (current) | Rails behave normally incl. −50 V. Sine does not propagate to output yet ("sine isn't kept") — needs full phased bringup: Q3 leg check, RV1/RV2 ohm-preset, jumper config, then TP2→TP4→TP5 walk. |

Hard-won rules: preset the pots by ohmmeter BEFORE first HV. On pre-V2 boards
(R19/R23 NOT fitted, 4.7k pots): RV2 bottom leg ≈ 1.1 kΩ (gives TP3 ≈ 0.5 V at
±50 V), and RV1 at its MAXIMUM (4.7 kΩ, output then idles near +11 V — safe).
Then, powered, with the DAC held at midscale, turn RV1 DOWN while watching TP5
until TP5 ≈ 0 V (≈ 3.65 kΩ; rule of thumb RV1 ≈ 7.3 kΩ × V_TP3). Gain there ≈ 97.
(An earlier version of this note said "RV1 ≈ 1.0 kΩ" — that is WRONG: LTspice
shows 1.0 kΩ pins the output at the negative rail with ~1 W in R21, and RV1 near
0 Ω is worse — level-shifter over-current that collapses rails and corrupts
everything, incl. TP2.) Keep R19/R23 unfitted: with them fitted the output cannot
be centered with these parts. The output is 100 × V_DAC regardless of rail
voltage, so at ±50 V keep the DAC within about ±0.5 V (≈35% of full scale) or
the output clips at both rails. Check Q3 legs on EVERY board before first −HV.
Verify J9 wiring against the correct revision's table above on every board
swap. On V1 boards, count from the square pad. On V2 boards, read the silkscreen
pin numbers.

Q3 ERRATA STATUS (2026-09-09): the source/drain swap is FIXED in the design
files (hvawg.kicad_sch symbol pin mapping + hvawg.kicad_pcb pad nets, copper
reroute, zone refill; verified — netlist Q3 pin2→levelshift_out / pin3→
Net-(Q3-S), DRC/ERC byte-identical to pre-fix baseline). Boards fabbed from the
fixed files take Q3 with STRAIGHT legs. All boards fabbed earlier (A–D and any
bare spares from the old fab) still REQUIRE the leg-cross. Tell revisions apart
with the 2 mA −HV ramp test. Regenerate gerbers (jlcpcb/ is stale) before any
new order.

## Phase 1 — low-voltage section only

Configuration:

- All HV supplies physically disconnected.
- JP4 open.
- DAC held at its zero-output or midscale code.
- Do not leave both U6 inputs floating as in the original README procedure.
  Either install JP3 and JP6 with DAC and monitor at 0 V, or temporarily pull
  both U6 inputs to ground through approximately 10 kΩ.

Apply ±12 V with separate current limits, initially around 40–60 mA per rail.

Verify:

- +12 V and −12 V at the IC pins;
- TP2 at the expected DC level;
- TP3 approximately 0 V with +HV absent;
- U6 pins 3 and 4 both close to 0 V;
- U4, U6, and U8 remain cool for several minutes;
- no unexpected high-frequency oscillation.

If U4 or U8 heats during this phase, the problem is independent of the HV
potentiometers and points toward rail polarity, soldering, component
orientation, unused-channel oscillation, or damage remaining elsewhere.

## Phase 2 — U8 monitor circuit isolated

Configuration:

- JP6 removed so U8 is not loaded through RV1.
- Temporarily hold U6 pin 4 near ground with about 10 kΩ so U6 does not float.
- Negative HV and output-stage supplies off.

Ramp +HV: +20 V → +60 V → +120 V.

A 2 mA current limit is sufficient for the monitor-only stage after the
hardware corrections.

Expected TP3:

    V_TP3 = V_+HV * R_RV2 / (110k + R_RV2)

For R_RV2 = 1.11 kΩ:

| +HV   | Expected TP3 |
|-------|--------------|
| 20 V  | ~0.20 V      |
| 60 V  | ~0.60 V      |
| 120 V | ~1.20 V      |

TP3 and U8 pin 3 should be nearly identical.

Initially adjust RV2 only with power off, then reapply power and remeasure.
A live sweep can be tested later after the fail-safe modifications.

NOTE: A supply current limit alone does not protect an op-amp input from
overvoltage through 110 kΩ: the dangerous fault current may be below 1 mA and
therefore never trip a 5 mA current limit.

## Phase 3 — level shifter without output stage

Configuration:

- JP3 and JP6 installed.
- JP4 open.
- DAC input fixed at 0 V.
- Floating −100+12 V supply still off.

Begin with approximately ±20 V HV rails rather than ±120 V.

Verify:

    V_U6+ ≈ V_U6− ≈ V_DAC

and:

    V_TP4 = V_−HV + (96.4 / R_RV1) * (V_TP3 − V_DAC)

At ±120 V, gain 100, R_RV1 = 225 Ω, V_DAC = 0, and V_TP3 = 1.2 V:

    V_TP4 ≈ −120 + 0.514 = −119.49 V

The corresponding Q3 current is approximately:

    I_Q3 ≈ 1.2 / 225 = 5.3 mA

Use a properly rated differential/isolated probe or a high-voltage DMM for TP4.

Ramp in stages: ±20 V → ±60 V → ±120 V.

Stop immediately if U6 pins 3 and 4 differ substantially, U6 output rails, or
Q3 heats rapidly.

## Phase 4 — output stage at reduced voltage

Power down and discharge the rails, then install JP4.

Connect the floating supply that provides 12 V above the negative rail.
Confirm the voltage between U7 pins 5 and 2 is approximately 12 V; do not
infer this solely from ground-referenced supply displays.

Start at ±20 V with no external load and zero DAC input.

Expected centered R21 current:

    I_R21 = V_+HV / 10k

| Rails  | Centered R21 current |
|--------|----------------------|
| ±20 V  | 2 mA                 |
| ±60 V  | 6 mA                 |
| ±120 V | 12 mA                |

Suitable initial HV current limits:

- 5 mA at ±20 V;
- 12 mA at ±60 V;
- 25 mA at ±120 V for zero or small-signal testing.

For full-scale AC testing, raise the limits cautiously toward roughly
35–40 mA, because the R21 current and Q3 current both rise near the negative
output extreme.

## Phase 5 — calibration

Start with:

- 100 Hz;
- 5–10% full-scale DAC amplitude;
- no external capacitive load.

Then:

1. Measure output peak-to-peak gain.
2. Adjust RV1 slightly to establish gain.
3. Adjust RV2 to center the waveform.
4. Repeat gain and centering once.
5. Increase amplitude.
6. Increase frequency.
7. Add the intended capacitive load last.

Monitor continuously:

- +12 V and −12 V currents;
- positive and negative HV currents;
- TP3;
- U6 pin-3 versus pin-4 voltage;
- TP4;
- U4/U8 temperature;
- Q3, Q1, and R21 temperature.

## Shutdown

Keep ±12 V present until +HV has been ramped to zero, so U8 is never left
with a powered divider and unpowered supply rails. Bring both HV rails to
zero under controlled conditions, discharge them, and only then turn off the
low-voltage rails.
