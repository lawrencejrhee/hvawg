# HVAWG bringup procedure for V2 boards

This is the staged first-article bringup procedure for V2 boards (the safety revision, with R21 laid flat in an on-board heatsink). It keeps Yichen's five-phase structure from the V1 procedure: low voltage only, then the monitor, then the level shifter, then the output stage, then calibration. The numbers are for the V2 parts.

- Expected values come from the netlist of hvawg.kicad_sch (2026-09-24; the component values are unchanged since 2026-09-23) and hand analysis with ideal opamps. They were cross-checked against the LTSpice runs in simulations/v2/, which agree within about 1-3%.
- Locations refer to the component side, with J9's edge at the top. The board is 207 x 58.8mm. The DAC is at the left end, and the output stage (HS1 with R21, then Q1) is at the right end.
- Nothing in this procedure has been run on a V2 board yet. Anything that was derived but not measured is marked "(confirm on first board)".
- When a measurement disagrees with a table, stop and find out why before going on.

Related documents:
- README.md: circuit description.
- V2-SUMMARY.md: what changed in V2, simulation results, and decisions.
- BRINGUP-V1-BOARDS.md: the procedure, lessons and board log for V1 boards A-D.

## 0. Scope and revision check

This document applies only to V2 boards. V1 and V2 boards have different J9, J5/J6 and J7/J8 pinouts, so never use a V1 harness or cable on a V2 board.

| Feature                  | V2 board (this document)                                                                                                            | V1 board (use BRINGUP-V1-BOARDS.md)          |
|--------------------------|-------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------|
| Board                    | Plain 207 x 58.8mm rectangle; M3 holes at 197 x 48.8mm                                                                              | 150 x 40mm; holes at 140 x 30mm              |
| Bench power input J9     | 3.50mm pluggable terminal block (Phoenix MC 1,5/8-G-3,5, 1844278) on the top edge between J5 and J7, in a 0.5mm edge notch. No tab. | 2.54mm 8-pin header                          |
| Output bus J7/J8         | 7-pin sockets (OUT1, GND, OUT2, GND, OUT3, GND, OUT4)                                                                               | 4-pin sockets plus a separate J10 GND socket |
| R21 (10k power resistor) | TO-220 part (Vishay LTO 50) laid flat, ceramic face down, in a Wakefield 272-AB heatsink (HS1, on GND) left of Q1                   | Off-board resistor on flying leads           |
| Q1                       | Alone at the right edge, on its own heatsink bar                                                                                    | Right edge                                   |
| Test points              | TP1-TP8 are Keystone loops. TP9-TP12 are bare round SMD pads near Q1/U7.                                                            | TP1-TP5 only                                 |
| Q3                       | Fitted with straight legs (the S/D fix is in the design files)                                                                      | Legs crossed by hand                         |

- Silkscreen version text: boards made from the current files read "HV_AWG v2" at the top left, beside J1. V1 boards read "HV_AWG v1". Still check the features in the table.
- The J9 silkscreen shows pin numbers 1-8, with the net name under each pin. Seen from the component side with J9's edge at the top, pin 1 is the right end and pin 8 the left end. From right to left: 1 GND, 2 +12V, 3 -12V, 4 GND, 5 Vhi, 6 GND, 7 Vlo, 8 Vlo+12.

## 1. Safety first

### 1.1 Hazards on this board

- Voltages: up to ±150V to GND and 300V between the rails. Supplies set to ±50V still put 100V across the board.
- Stored energy: the 4.7uF rail capacitors (C26, C27) hold about 53mJ each at 150V.
- Supply current: the HV supplies can deliver hundreds of mA if the limit is not set (E3612A 0.25A; E3641A about 0.5-0.8A).
- WARNING: THE OUTPUT IS LIVE EVEN WHEN IT "SHOULD" BE AT 0V. Whenever Q1 is off, R21 pulls TP5, TP6, the Q1 tab and the selected J7/J8 output pin up to +HV. Q1 is off in Phases 2 and 3, in Phase 4 before the floating 12V is on, whenever the latched code is on the Q3 cutoff side (including a random power-up code), and after a fault.
- Hot surfaces: HS1 (R21's heatsink, silk "HOT >100C") and R21 on it. At ±150V with the output held near the negative rail and no airflow, the sink can reach about 110-113°C and the R21 element about 141-144°C (estimates, see section 5). HS1 is on GND, so it is not a shock hazard, but it is a burn hazard. Q1 and its bar also get warm.

Live nodes during HV phases:

| Potential | Where it appears |
|---|---|
| +HV | J9-5, J5/J6 pin 1, R12 top, R21 lower pad (pad 2), C26, R24 |
| Output (anywhere between -HV and +HV) | TP5, TP6, Q1 tab (drain), R21 upper pad (pad 1), R31, R32 pad 1 (empty), JP8-JP11, J7/J8 pins 1/3/5/7 |
| About -HV | J9-7, J9-8, J5/J6 pins 3 and 4, C27, R25, TP4, TP9-TP12, both JP4 pins, Q3 tab (drain, silk "TAB ~ -150V"), U7, D4, R17, R22, R18, R28, Q1 gate/source pins, Q3 middle pin, D3 and R3 (both ends; they sit between the J5/J6 -HV traces, left of TP8), C24, C25, R15, the R19/R23 pads |
| Low voltage (near GND) | TP1, TP2, TP3, TP7, TP8, JP3, JP6, RV1, RV2, U2, U3, U4, U6, U8, J1-J4, HS1 (GND, but hot) |

### 1.2 Working rules

- One-hand rule. With HV on, keep one hand off the bench (in a pocket or behind your back). Probe with one hand only.
- Attach clip leads with power off. Clip or solder measurement leads to HV nodes, then power up and read. Do not hunt for pins on a live board.
- WARNING: CHANGE JUMPERS ONLY WITH POWER OFF AND THE RAILS DISCHARGED, AND NEVER PLUG OR UNPLUG J9 LIVE. On V1 board A, hot-plugging JP4 drew a spark and nearly destroyed the board. This also applies to JP8-JP11, the Phase 2 10k clip, the Q1 heatsink bar and the J9 plug (Phoenix: not to be plugged or unplugged under voltage).
- Adjust RV2 only with power off. Adjust RV1 live only with an insulated plastic trim tool, one-handed. RV1 sits at low voltage, but J6, R25, D3/R3 and the J5-J6 -HV traces, about 5.5-8.5mm to its left, are at -HV.
- Set current limits before enabling any output. Use the limits given in each phase. Never run with the limit at max.
- Remove watches and rings. Keep the bench clear of loose wire and metal tools. Do not work alone whenever any HV supply is connected.
- Emergency action: switch the HV supply outputs off (both HV supplies and the floating 12V), then follow section 7.

### 1.3 Bleed-down and discharge

When the HV supplies are ramped to 0, the on-board resistors discharge the rails:

| Rail                          | Capacitance          | Bleed path                                                | Time constant | Time to go from 150V to below 5V       |
|-------------------------------|----------------------|-----------------------------------------------------------|---------------|----------------------------------------|
| +HV                           | C26 4.7uF            | R24 1M in parallel with (R12 110k + R_bottom), about 100k | about 0.5s    | about 1.6s                             |
| -HV                           | C27 4.7uF            | R25 1M (worst case, with Q1/Q3 not conducting)            | about 4.7s    | about 16s                              |
| Floating 12V (across C24/C25) | C24 10uF + C25 100nF | R15 1M, plus D3/R3 above about 2.5V                       | about 10s     | D3/R3 pull it below about 2.5V quickly |

Note that the supplies' own output capacitors also discharge into these resistors, so the real discharge can be slower.

Rule: after the supplies read 0V, wait at least 30s. Then, with a DMM, verify all of the following before touching anything or moving a jumper:
- under 5V from J9-5 (+HV) to GND
- under 5V from J9-7 (-HV) to GND
- under 5V from J9-8 (floating rail) to GND and to J9-7

Measure on the J9 plug's screw heads or wire entries (confirm on first board that the plug's screws can be reached with a probe). TP12 (-HV) and TP5 are alternative check points.

### 1.4 Probes and meters

| Rails in use            | Highest node-to-GND voltage | Scope probe                                                                                                                      | DMM                                     |
|-------------------------|-----------------------------|----------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------|
| up to ±50V              | 50V (100V between rails)    | 10x passive probe rated at least 300V (CAT II), set and used at 10x. Never use 1x.                                               | Handheld, battery powered, CAT III 600V |
| above ±50V, up to ±150V | 150V (300V between rails)   | 100x HV passive probe rated at least 1kV, or a differential probe rated at least 300V differential and at least 300V common-mode | Handheld, battery powered, CAT III 600V |

- Probe voltage ratings derate with frequency. Check the probe's derating curve before looking at signals in the 100kHz range.
- Use a 1Mohm scope input with DC coupling. Never use 50ohm: a 50ohm input at these voltages destroys the scope input or the terminator.
- WARNING: SCOPE GROUND CLIPS GO ON BOARD GND ONLY. Every channel's ground is the scope chassis, which is earthed. A ground clip on any other node shorts that node to earth.
  - Good GND points: a male header pin inserted into J4 pin 1 or 2 (both GND, in the low voltage area; insert it with power off), J1 pin 1, or J9-1 (the end terminal; never clip onto J9-4 or J9-6, which sit beside +HV).
  - The mounting holes H1-H4 are not connected to GND.
- TP4 and TP9-TP12 sit at about -HV. A probe tip may go on them with the ground clip on GND. Never clip a scope ground to them.
- For the small voltages above -HV (level shifter, Q1 gate/source), use the handheld DMM with COM on the -HV reference (TP12, or a header pin in J6 pin 3 on a standalone board), and put the red lead on the node.
  - The DMM then floats at -HV. Do not touch it or its leads while powered.
  - Attach the COM lead with power off.
  - TP9-TP12 are bare pads. Use a sprung probe tip, or solder a short insulated lead to TP12 with the board unpowered.

### 1.5 Supplies and wiring

- Use only the (+) and (-) output terminals. The green earth post on a bench supply is not an output. Wiring a rail to it leaves the rail floating; on V1 this produced a phantom "TP3 stuck at 6.8V" and "rail reads 0V".
- Triple-output supply (±12V): its COM (ground symbol) terminal is board GND. Wire COM to GND, (+) to +12V and (-) to -12V.
- +HV supply: (+) to +100V, (-) to GND.
- -HV supply: (+) to GND, (-) to -100V. This reverse-biases nothing on the board. C27's + terminal is on GND.
- Floating 12V supply: it must be an isolated output, with (-) to -100V and (+) to -100+12V. Its output-to-earth isolation rating must exceed the -HV setting. Check its manual before going above ±50V (confirm).
- The ±12V pair must never be the channel that supplies the floating 12V, because that channel's COM is GND.
- No earth straps on the -HV and floating supplies. Remove any shorting link between an output terminal and the earth/chassis post on the -HV and floating 12V supplies. Check that each output terminal reads open to the earth post before wiring. The scope and the Pico already earth GND, so a strapped (-) terminal on either supply shorts -HV to GND.

J9 wiring (V2 only). Pin 1 is at the right end.

| J9 pin | Silk label | Net      | Connect to                                                                                                                                                        |
|--------|------------|----------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 1      | GND        | GND      | ±12V supply COM                                                                                                                                                   |
| 2      | +12V       | +12V     | ±12V supply (+)                                                                                                                                                   |
| 3      | -12V       | -12V     | ±12V supply (-)                                                                                                                                                   |
| 4      | GND        | GND      | +HV supply (-)                                                                                                                                                    |
| 5      | Vhi        | +100V    | +HV supply (+)                                                                                                                                                    |
| 6      | GND        | GND      | -HV supply (+)                                                                                                                                                    |
| 7      | Vlo        | -100V    | -HV supply (-) and floating 12V supply (-). Crimp both leads into one twin ferrule (0.5mm^2, e.g. Phoenix AI-TWIN 2x0,5-8 WH); the MC-ST clamp accepts two wires. |
| 8      | Vlo+12     | -100+12V | floating 12V supply (+)                                                                                                                                           |

- Plug: Phoenix MC 1,5/8-ST-3,5, order no. 1840421 (screw clamp). It mates with the 1844278 header on the board. Sources: Mouser 651-1840421, Digi-Key 277-5715-ND, LCSC C3579977. A 3.81mm plug will not mate properly. The MC 1,5/8-ST-3,5 BD:1-8 (1900523) is the same plug with printed numbers; check that its "1" lands on J9 pin 1, the right-hand end.
- Wire: 600V rated hookup wire (e.g. UL1015), because +HV and -HV are 300V apart in the same harness. 24-20 AWG is plenty: the current is under 0.15A even when board 1 feeds a 4-board stack. The clamp takes AWG 28-16; strip 7mm and tighten to 0.22-0.25Nm (Phoenix screwdriver SZS 0,4X2,5 VDE, 1205037).
- Wire and tighten the plug off the board, then plug it in with power off and the rails discharged. Never plug or unplug J9 live. The plug is held by friction only (about 32N), so strain-relieve the harness.
- Rating: the header (1844278) sets it: 250V for overvoltage category II / pollution degree 2 (a lab bench), 160V for III/2. At ±150V rails the largest voltage between neighboring pins is 150V (pins 4-5, 5-6 and 6-7), which is also within the 160V that LCSC lists for the 1840421 plug. Pins 5 and 7 (300V apart) are separated by the grounded pin 6. Do not exceed ±150V rails.
- Label the harness "V2".

Harness verification (every new harness, and every time the harness is rewired). A mirror-image harness is easy to make, because pin 1 is at the right end; it puts HV on the ±12V and GND pins. Plug the harness into J9 with every supply switched off and its leads disconnected from the supplies. Measure the resistance from each supply-end lead to a board point:

| Supply-end lead          | Board point             | Expected                                                                                               |
|--------------------------|-------------------------|--------------------------------------------------------------------------------------------------------|
| ±12V COM                 | header pin in J4 pin 1  | under 1ohm                                                                                             |
| +12V lead                | U4 pin 8                | under 1ohm                                                                                             |
| -12V lead                | U4 pin 4                | under 1ohm                                                                                             |
| +HV (+)                  | C26 + pad / R12 top pad | under 1ohm                                                                                             |
| +HV (-) and -HV (+)      | header pin in J4 pin 1  | under 1ohm                                                                                             |
| -HV (-) and floating (-) | TP12                    | under 1ohm                                                                                             |
| floating (+)             | TP11                    | under 1ohm                                                                                             |
| floating (+)             | header pin in J4 pin 1  | must not read low (about 2Mohm via R15 + R25, creeping). A mirror-image harness reads under 1ohm here. |

Any other result: stop and rewire.

Power-on order:
1. +12V
2. -12V (apply -12V promptly after +12V; the DAC can heat up with +12V alone)
3. +HV
4. -HV
5. Floating 12V

Power-off order: see section 7. The HV rails and the floating 12V come down first, and ±12V goes off last. U8 must never see a powered HV divider while its own rails are unpowered.

## 2. Equipment

| Item | Requirement | Notes |
|---|---|---|
| ±12V supply | Triple output with COM, 0-12V, current limit adjustable down to about 40mA | Current lab: triple output, with COM used as board GND |
| +HV supply | 0 to target rail. Current limit settable from about 0.5mA up to 35mA. | Current lab: E3612A (bench at +50V; confirm its range before planning above ±50V) |
| -HV supply | Same as +HV | Current lab: E3641A (confirm its range before going above ±50V) |
| Floating 12V supply | Isolated output, 12V, at least 10mA per board. Output-to-earth isolation greater than the -HV magnitude. No output-to-earth strap (section 1.5). | Powers U7 on the -HV rail |
| Two DMMs | Handheld, battery, CAT III 600V, 10Mohm input | One stays on TP5 during Phases 4-5 |
| Oscilloscope | At least 2 channels, 1Mohm inputs | Timebase in ms/div for Pico waveforms |
| Scope probes | 10x rated at least 300V (up to ±50V); 100x HV probe rated at least 1kV, or a rated differential probe (above ±50V) | Section 1.4 |
| Pico / Pico 2 with MicroPython | pico_test_script/pico_dac_test.py, hvawg_driver.py (and main.py for host use later), Thonny or similar REPL | GP3 to J1-2 data, GP2 to J1-3 shift clock, GP5 to J1-4 store clock, GND to J1-1. These are GPIO numbers, not physical pin numbers. |
| Leads | Mini-grabbers, insulated alligator clips, single male header pins (for GND/-HV reference in sockets), a 10kohm resistor with clip leads (Phase 2) | |
| Trim tool | Insulated (plastic) trimmer screwdriver for the 3296Y pots | |
| Mating plug | Phoenix MC 1,5/8-ST-3,5, order no. 1840421 (3.50mm), 600V hookup wire, one twin ferrule for pin 7, wired per section 1.5 | |
| R21/HS1 (fitted at assembly, every board) | Wakefield 272-AB (plain) heatsink; M3x12 and M3x8 pan head screws, one DIN 125 flat washer, one DIN 6797-J internal-tooth washer, two DIN 127 split washers, two M3 nuts; non-silicone grease (Wakefield 126); a lead-forming jig | Section 3.6 |
| Q1 heatsink bar (mandatory above ±50V) | Bar of at most 10°C/W recommended (at most 30°C/W absolute at 40°C ambient), Q1 only, covering board y about 99-111 at the right edge. Sil-Pad K-10 and Keystone 3049 nylon shoulder washer for Q1. M3 hardware. A GND tie wire. Calipers. | Sections 3.6 and 5 |
| Airflow | A fan giving at least 1m/s across HS1's fins if a sustained DC output may sit below about -50V at ±150V (R21 above about 4W; in general below +HV - 200V, so never needed up to about ±100V); recommended for closed stacks at ±150V | Section 5 |
| Temperature | Thermal camera, IR thermometer or thermocouple | |
| Optional | Function generator with high-Z output mode (JP3 injection, Phase 5); insulation tester (Q1 pad and R21-to-sink checks) | |

- Supply ranges: the E3641A tops out at about 60V and the E3612A at 120V (verify against their manuals), so ±150V needs other supplies. The current ±50V bench is within both.

## 3. Pre-power inspection (board unpowered: Phase 0)

### 3.1 Revision and assembly

- V2 confirmed per section 0: J9 block on the top edge in the notch (no tab), 7-pin J7/J8, R21 flat in HS1, "HV_AWG v2".
- Q1 = IRF730, alone at the right edge, right of U7. Its pins from top to bottom are G, D, S, and the tab faces the right edge (by the footprint it stands about 0.4mm past the board edge; a real part varies, see section 3.6). Q3 = IRF9610 in the level shifter area near the bottom edge, tab facing right. Q1 and Q3 are both TO-220, so read the part markings to make sure they are not swapped.
- Q3 legs straight. V2 boards do not take the V1 leg-cross; crossing them reverses Q3.
- R21 (LTO 50) and HS1 fitted per section 3.6. R21 lies ceramic face down in the trough, with its hole on HS1's left-hand hole. Its formed leads go into the two slotted pads left of the sink: upper pad = output, lower pad = +HV. Both screws are torqued before the leads are soldered.
- C26 and C27 polarity (both are 200V polarized electrolytics). C26: + terminal on +100V, - on GND. C27: + terminal on GND, - on -100V. Match each part's polarity mark to the silkscreen.
- R19 and R23 not fitted (the THT vertical footprints: R19 just below JP4's right pin; R23 below R22 in the output stage block, left of TP10). If they are fitted, the output cannot be centered.
- R32/C32 empty. They form a series RC from TP5 to GND (an AC load). Fit them only on purpose, and C32 must then be rated at least 250V.
- V2-only parts present with the right values. The JLC BOM is stale and does not list these, so check them against the schematic. If R29 is 100k (the old value), centering will drift with rail voltage.

  | Part     | Value / type                                                                                                     |
  |----------|------------------------------------------------------------------------------------------------------------------|
  | R26      | 3.3k                                                                                                             |
  | R27      | 820ohm                                                                                                           |
  | R28      | 100k                                                                                                             |
  | R29      | 1M                                                                                                               |
  | R30      | 22k, 2512 (TE CRGP2512F22K, 2W)                                                                                  |
  | R31      | 4.7k, 2512                                                                                                       |
  | D4, D5   | BZT52C12 (check orientation)                                                                                     |
  | RV1, RV2 | 1k 3296Y (not the V1 4.7k)                                                                                       |
  | C24      | 10uF 1206 X7R, 125°C: Samsung CL31B106KAHNNNE (LCSC C14860), not the May BOM X5R CL31A106KBHNNNE (see section 5) |

- JP1 (solder jumper just right of R4/R5, about 4.5mm below U3 pin 1) is open. Bridged, it doubles the DAC current and moves the center code to about 64.
- JP2 (solder jumper just right of R9/R10, above-left of U4) is bridged. Open, it shifts the DAC output up by about 3.75V.
- U3 (DAC0808) orientation matches a working V1 board. The schematic pin numbering is non-standard but unchanged from V1, and V1 boards produced a correct DAC sine. Do not "correct" it.
- J9 header soldered and seated. The plug slides in parallel to the board from the top edge; the edge is notched 0.5mm behind J9 so that the plug seats fully. The wire entries face out, away from the board.
- No solder bridges or flux residue around the HV pads (Q1, Q3, R21, J9, J5/J6, JP4, C26/C27). Clean off flux, which becomes a leakage path at HV.
- Every THT lead trimmed to 2.5mm or less below the board (R21's to about 1.5mm, section 3.6). Stacking needs this (section 6 step 0): an untrimmed Q1 or Q3 lead reaches about 8mm (up to 9.5mm) below the board and, at the recommended spacing, can touch the Q1/Q3 bodies on the board below.
- All removable jumpers (JP3, JP4, JP6, JP8-JP11) are out for sections 3.2 and 3.3.

### 3.2 Resistance checks (power off, jumpers out, rails discharged)

- "Red to black" means the red lead goes on the node that is more positive in operation. In this polarity every FET body diode is reverse biased. Reversed polarity reads lower, because the diodes conduct; that is not a fault.
- Readings creep while the rail capacitors charge from the meter. Read after about 30s.

| Red to black | Designed path | Expected | Stop if |
|---|---|---|---|
| J9-5 (+100V) to J9-1 (GND) | R24 1M in parallel with (R12 110k + R_bottom) | about 100kohm (about 95-105k with R12 at 5%). This is the HV divider, not a fault. | under 50k; about 1-2k means R12 is shorted |
| J9-1 (GND) to J9-7 (-100V) | R25 1M | about 1Mohm (somewhat less from IC leakage) | much less than 1M: C27/R25 fault or a -HV to GND short (this check cannot see Q3; section 4.3 Step A does) |
| J9-5 (+100V) to J9-7 (-100V) | about 100k + 1M | about 1.1Mohm | about 10k: Q1 shorted D-S |
| J9-8 (-100+12V) to J9-7 (-100V) | R15 1M in parallel with D3/R3 and the U7 supply pins | at most 1Mohm, record it | under 1k |
| TP5 to GND | R21 10k to +100V, then the divider (about 100k) | about 110kohm (TP6 about 115k) | 10k or less |
| J9-2 (+12V) to GND | IC supply pins + R1/D1, about 40uF | High and climbing (much more than 10k), record it | under 1k |
| GND to J9-3 (-12V) | IC supply pins + D2/R2, about 40uF | High and climbing, record it | under 1k |
| J9-2 (+12V) to J9-3 (-12V) | Opamp and DAC supply pins | Record it and compare between boards | under 1k (the V1 board C failure: an opamp shorted across the rails) |
| TP1 (+5V) to GND | R7-R10 (10.8k) in parallel with the DAC reference and U2/U3 VCC | at most 10.8kohm. This is naturally the lowest; record it. | under 1k |

### 3.3 Trimmer presets (power off)

The 3296Y has no marked direction for this circuit. Turn it a few turns, re-measure, and record on the record sheet which direction raises the in-circuit resistance. Watch the reading rather than counting turns.

| Trim | Meaning | Measure between | Preset | Range |
|---|---|---|---|---|
| RV2 ("DC adjust", upper trimmer) | R_bottom = RV2 + R27 (820ohm) | RV2 pin 1 to GND (e.g. J9-1). Let C15 (10uF) settle. The reading is about 0.1% low because of the R12/R24 path. | R_bottom = 1.11kohm (RV2 about 290ohm) | 0.82-1.82k (usable only about 1.02-1.32k, i.e. RV2 about 0.2-0.5kohm; Sim 7) |
| RV1 ("gain adjust", lower trimmer) | R_RV1 = R26 (3.3k) + RV1 | JP6 pin 1 (lower pin) to TP8, with JP6 out. It reads nothing else. | R_RV1 = 4.3kohm (RV1 at maximum; 4.2-4.4k with pot tolerance) | 3.3-4.3k |

- Which trimmer is which: the two trimmers sit one above the other, between the J5/J6 HV traces and U8/Q3. RV2 is the upper one (nearer J9) and RV1 the lower one (nearer the bottom edge). The "DC adjust", "RV2" and "RV1" labels all sit in the gap between them, and "gain adjust" is below RV1, so go by position, not by the nearest label.
- RV2 window: at either end of RV2 (0 or 1kohm) no RV1 setting can center the output (Sim 7). The preset (about 290ohm) is inside the usable 0.2-0.5kohm window.
- Pad positions (same for both trimmers): pin 1 = upper-left pad (toward the top edge), pin 2 = the single right-hand pad, pin 3 = lower-left pad. Pins 2 and 3 are tied together (rheostat).
- RV2 pin 1 is the divider tap (continuity to C14 pad 1). RV1 pin 1 is the R26 end; RV1 pins 2 and 3 are on TP8.
- Why these presets: R_RV1 at 4.3k is above the centering value (about 3.65k), so at first output stage power the output idles positive at about +0.15 x HV (section 4.4). The V1 failure where RV1 at about 0ohm caused level shifter over-current cannot happen on V2, because R26 keeps R_RV1 at 3.3k or more.

| Check                                                | Expected    | Stop if                 |
|------------------------------------------------------|-------------|-------------------------|
| JP6 pin 1 to TP8, RV1 at minimum (during presetting) | about 3.3k  | under 3.2k: R26 shorted |
| RV2 pin 1 to GND, RV2 at minimum                     | about 0.82k | under 0.8k: R27 shorted |

### 3.4 Jumper configuration by phase

| Phase           | JP3 (DAC to U6+) | JP6 (TP3 to R26/RV1) | JP4 (TP4 to U7+) | JP8-JP11                                        | Extra                  |
|-----------------|------------------|----------------------|------------------|-------------------------------------------------|------------------------|
| 0 inspection    | out              | out                  | out              | none                                            | -                      |
| 1 ±12V only     | in               | in                   | out              | none                                            | -                      |
| 2 +HV monitor   | in               | out                  | out              | none                                            | 10k from TP8 to GND    |
| 3 level shifter | in               | in                   | out              | none                                            | remove the 10k         |
| 4 output stage  | in               | in                   | in               | none (measure at TP5/TP6)                       | floating 12V connected |
| 5 calibration   | in               | in                   | in               | exactly one (JP8 = OUT1 for a standalone board) | -                      |

- JP3 pins: upper = dac_out, lower = U6 +in.
- JP6 pins: upper = monitor_out (TP3), lower = R26 end of the RV1 string.
- JP4 pins: left = TP4, right = U7 +in. Both pins are at -HV.
- JP8-JP11: upper pin = output_post (TP6), lower pin = OUT1-OUT4 (silk "Out Select 1 2 3 4").

### 3.5 Test point map

| TP   | Net / function                               | Where (J9 edge at the top; Q1 at the right edge)                                                                                                                            | Potential          |
|------|----------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------|
| TP1  | +5V logic rail (7805 out)                    | Far left, above-right of the bottom-left mounting hole                                                                                                                      | +5V                |
| TP2  | DAC output (dac_out)                         | Below U4, just left of JP3                                                                                                                                                  | ±1.25V             |
| TP3  | Monitor output (U8, the HV divider buffered) | Right of U8, just left of the JP8-JP11 row (2.8mm from JP8's upper pin, which is output_post)                                                                               | about 1% of +HV    |
| TP4  | Level shifter output (Q3 drain)              | Below JP6, above JP4. Right-hand one of the TP7/TP4 pair.                                                                                                                   | -HV + 0 to 1.8V    |
| TP5  | Amplifier output, before R31 (Q1 drain)      | Right of R31 (large 2512), below C26, left of R32/C32                                                                                                                       | ±HV                |
| TP6  | Output after R31 4.7k (output_post)          | Under the Out Select row, above J8                                                                                                                                          | ±HV                |
| TP7  | Q3 gate / U6 output                          | Left of TP4, same row                                                                                                                                                       | low voltage        |
| TP8  | Q3 source / U6 -in                           | Left of RV1                                                                                                                                                                 | low voltage        |
| TP9  | Q1 gate / U7 output (SMD pad)                | Right end, above R18 and up-left of Q1's gate pin. The 0.5mm output track passes 1.9mm up-right of it (under solder mask); Q1's drain pin (output potential) is 8.4mm away. | -HV + 3 to 5V      |
| TP10 | Q1 source / U7 -in (SMD pad)                 | Below and right of D4, down-left of Q1's source (bottom) pin (6.8mm from Q1's drain pin, which is at the output potential)                                                  | -HV + 75ohm x I_Q1 |
| TP11 | -100+12V (U7 V+) (SMD pad)                   | Just above U7, right of C25                                                                                                                                                 | -HV + 12V          |
| TP12 | -100V (U7 V-) (SMD pad)                      | Left of R22, below C24/C25                                                                                                                                                  | -HV                |

LEDs:
- D1 = +12V present.
- D2 = -12V present.
- D3 = floating 12V present. D3 says nothing about whether -HV itself is present.
- There is no LED for +HV, -HV or +5V. Use TP3 and TP1.

### 3.6 Heatsinks and insulation

There are two heatsinks. HS1 (R21's heatsink) is part of the assembly on every board. The Q1 bar is required before operating above ±50V and recommended at ±50V.

HS1 and R21 (Wakefield 272-AB, plain version; R21 = LTO 50 laid flat):

- Lead forming. Form R21's leads in a jig, clamping each lead between the body and the bend:
  - straight for 4.2mm from the body;
  - inner radius 1.2mm (e.g. over a 2.4mm diameter mandrel);
  - 90° toward the ceramic side, i.e. down into the board;
  - outer lead face 6.0 ±0.5mm from the body (check with calipers).

  Never bend sideways. The 1.5 x 3.0mm plated slots let the 0.8 x 0.6mm lead move about ±1.1mm along the lead (±1.08mm nominal; about ±1.04mm if JLC makes the slot 0.08mm small) and ±0.35mm across. The 6.0 ±0.5mm caliper check keeps the bend inside that. The same travel also absorbs R21's own body tolerance (its hole is 13.0mm from the lead end of the body, from 16.2 and 3.2mm, each ±0.3mm) and the drill position (about 0.075mm): about ±0.66mm combined (RSS), about ±1.2mm worst case. The worst case is covered by the M3 screw's clearance in R21's and the PCB's 3.2mm holes (about ±0.14mm each), which lets R21 shift slightly to suit its leads.
- Assembly order: form, grease, place, screw down, solder last.
  1. Put a thin layer of non-silicone grease (Wakefield 126) on R21's ceramic face.
  2. Lay R21 face down in the trough, with its hole on HS1's left-hand hole and its leads through the two slotted pads.
  3. Hole 1 (R21, sink and PCB): M3x12 pan head with a DIN 125 flat washer on R21's molded face.
  4. Hole 2 (sink only): M3x8 pan head with a DIN 6797-J internal-tooth washer on the sink base. The teeth bite through the anodizing and bond the sink to GND.
  5. Under the board, fit a DIN 127 split washer and an M3 nut on each hole's GND ring. Torque to about 0.5-0.6Nm. The LTO 50 datasheet's mounting torque is about 1Nm (a recommended value, not a stated maximum); use the lower figure here because the FR4 is in the clamp stack.
  6. Solder the leads, then trim them to about 1.5mm.
- No insulator under R21. Its ceramic back is isolated (1500V RMS).
- Insulation check (power off): R21 either lead to sink reads over 10Mohm (the DMM should read open/OL). With an insulation tester, expect over 100Mohm at 500V (optional).
- GND bond: HS1 fin to J9-1 (or a header pin in J4 pin 1) reads under 1ohm. If it reads high, the tooth washer at hole 2 is not biting through the anodizing: reseat it. HS1 must never float (Sim 6).
- The nuts and screw tails stick out about 5-6mm below the board. Put the board on feet or standoffs of at least 8mm.
- Keep wires and probe leads off the fins. The sink is hot in operation.

Q1 bar (Q1 only; required above ±50V, recommended at ±50V):

- Bar spec: at most 10°C/W recommended, at most 30°C/W absolute at 40°C ambient. Q1 dissipates at most 2.23W, at the centered output at ±150V.
- Bar fit. The bar spans board y about 99-111 at the right edge.
  - The board edge is pulled in: by the footprint model, Q1's tab face stands about 0.4mm past the PCB edge (about 0.2mm at the worst routing tolerance), so a flat bar should touch the tab, through the Sil-Pad, before it touches the PCB edge.
  - A real IRF730 varies: its tab back is 2.6-3.2mm from the lead centerline (Vishay TO-220 drawing), so the tab can sit anywhere from about 0.16mm behind the edge to about 0.48mm past it. Measure Q1's lead-to-tab-back distance with calipers.
  - Clamp Q1 and its Sil-Pad to the bar before soldering Q1's leads. The leads have about 0.1mm of play in their 1.1mm holes (at most about 0.25mm with the thinnest, narrowest leads), which lets the tab seat flat on the bar. Then check with calipers on the first board that the bar touches the tab, not the PCB edge. (The 1.1mm holes for Q1 and Q3 are unchanged from V1 and take nominal leads, but a lead at the TO-220 drawing's maximum, 1.02 x 0.61mm or 1.19mm across its diagonal, would not enter; dry-fit both before soldering.)
  - Bar height: this is limited by the chosen stack spacing. The bar must not stand taller than the clear space to the next board (the standoff length, at least 22mm; section 6 step 0) less a small margin, and must not hang below the board, or it hits the neighboring board's bar.
- Mounting hole. Q1's hole is at about board y 105.2, roughly 16mm above the board (confirm with calipers).
- Q1 insulation: Sil-Pad K-10 plus a Keystone 3049 nylon shoulder washer. The tab is the output, which reaches ±150V.
- Insulation check (power off):
  - Q1 tab (or TP5) to bar reads over 10Mohm (the DMM should read open/OL).
  - If an insulation tester is available, test Q1 tab to bar at 250V or more (optional).
- GND tie. Tie the bar to GND with a wire to J4 pin 1 (header pin) or J9-1. Check that bar to J9-1 reads under 1ohm. The mounting holes are not GND.
- Nothing metallic touches the Q3 tab, which sits at about -HV with no heatsink.

## 4. Powered bringup phases

### Common setup (every phase)

- Pico: connect J1-1 GND first, then GP3 to J1-2, GP2 to J1-3, GP5 to J1-4.
- Put pico_dac_test.py on the Pico's filesystem, not as main.py. If main.py (the serial server) is auto-running, stop it with Ctrl-C.
- Hold a code from the REPL:

  ```python
  from pico_dac_test import shift_byte
  shift_byte(128)          # latches code 128; the 74HC595 holds it until the next shift
  ```

- The 74HC595 has no reset (SRCLR is tied to +5V and OE to GND), so it powers up with a random code. After ±12V comes up, and before any HV, re-send the center code. Re-send it after any ±12V interruption.
- The 74HC595 runs on 5V and the Pico drives 3.3V. This is marginal on paper but worked on V1 boards. If TP2 shows missing bits, suspect it.
- Keep a DMM on TP5 from Phase 2 onward; it shows the HV output state at a glance.
- Record every reading on the record sheet (section 9).

### 4.1 Phase 1: low voltage section only (±12V, no HV)

Configuration:
- HV supplies and the floating supply physically disconnected from the harness (leads off at the supply).
- JP3 in, JP6 in, JP4 out, no JP8-JP11. U6's inputs are then defined: dac_out on +in, and TP3 (about 0V) via R26/RV1 on -in.
- ±12V current limit: 60mA each. Investigate any draw above about 45mA.

Steps:
1. Turn on +12V, then -12V immediately after.
2. Check that D1 and D2 are lit and D3 is dark. Record both supply currents.
3. Measure +12V and -12V at U4 or U8 pin 8 (V+) and pin 4 (V-).
4. Measure TP1.
5. Hold codes 0, 64, 128, 192 and 255 in turn, and measure TP2 with the DMM at each one. Use shift_byte(c) for each; dc_test() steps through them every 2s, which suits the scope.
6. Find the DAC center code c0: the code whose TP2 is closest to 0V. Hold c0 - 1, c0 and c0 + 1 to pick it. Nominal c0 = 128. Use c0 as "center" everywhere below.
7. Compute LSB_meas = (TP2(0) - TP2(255)) / 255.
8. Compliance check at low codes. Compare TP2(0) - TP2(64) with TP2(64) - TP2(128); both should be about 0.625V. A noticeably smaller step between 0 and 64 means the DAC0808 output compliance limit is compressing low codes (TP2 above about +0.4V; check the datasheet figure). Record it (confirm on first board). It only matters at rails where the low codes are used, i.e. above ±50V.
9. Measure TP3 and TP8.
10. Run sine_test() and scope TP2. Expect a clean sine of about 2.5Vpp centered near 0V, at tens of Hz from the bit-banged loop; measure the frequency. Use a ms/div timebase and DC coupling.
11. Let it run 5 min. Check that U4, U6, U8, U3 and U1 stay cool. V1 reference: NE5532 about 35°C, LEDs about 32°C.

Expected values:

| Point | Expected |
|---|---|
| +12V / -12V supply current | about 29mA / about 26mA (datasheet-typical estimate; confirm on first board) |
| TP1 | 5.00V (4.8-5.2V) |
| TP2 at code 0 / 64 / 128 / 192 / 255 | +1.250 / +0.625 / 0.000 / -0.625 / -1.240V. It falls as the code rises. It scales with TP1/5.00. (Derived from the netlist, not yet measured; the sims assumed ±1.4V and the README says around 2.8Vpp. Confirm on first board.) |
| TP2 step | -9.77mV per code (full scale 2.49Vpp) |
| c0 (TP2 about 0V) | 128 (midscale is about 0V, within a few tens of mV) |
| TP3 (no HV) | about 0V (about -5mV; within ±20mV) |
| TP8 | equal to TP2 for codes up to c0; about 0V for codes above c0 (see note) |
| TP7 | about TP2 + 0.6V for codes up to c0; near -12V for codes above c0 (see note) |

Note on TP7/TP8 in Phase 1: with -HV absent, Q3 has no drain supply and cannot carry current. D5 (anode on Q3's gate/TP7, cathode on Q3's source/TP8) gives U6 a second path:
- For codes below c0 (TP2 above 0V), U6 still closes its loop through D5 (forward biased): TP8 = TP2 and TP7 is about TP2 + 0.6V. About (TP2 - TP3)/R_RV1 (0.3mA at most) flows through R26/RV1 into U8's output.
- For codes above c0 (TP2 below 0V), U6 sits near -12V and TP8 is about equal to TP3, about 0V.

This is expected (confirm on first board). U6 closes its loop through Q3 only once -HV is present (Phase 3).

Go / no-go:
- Go:
  - Currents are within the limit and steady.
  - TP1 is within 4.8-5.2V.
  - TP2 is monotonic, and each of the 5 codes is within ±10% of the table after scaling by TP1/5.00.
  - c0 is within 128 ±5.
  - TP3 is within ±20mV.
  - Nothing is warm.
- A TP2 full scale near 2.8Vpp (the V1 bench value) is not a failure. Record LSB_meas and use it in sections 4.5 and 6.

Stop if:
- Either ±12V current exceeds 45mA or climbs.
- A rail at the IC pins is off by more than 0.5V.
- U4 or U8 heats up. Suspects: rail polarity, orientation, solder faults, or oscillation of the unused halves U4B/U8B. On V2 these are tied off as grounded followers (pin 5 to GND, pin 7 to pin 6), so pin 7 of U4 and U8 should read about 0V. Scope it for HF oscillation.
- TP2 is about +5V at code 0: JP2 is open.
- TP2 is about -1.25V at code 128, and full scale is about 5Vpp: JP1 is bridged.
- TP2 is flat or glitchy: see section 8.

### 4.2 Phase 2: +HV only (monitor circuit, U8)

Configuration (power off and discharged before changing anything):
- JP3 in, JP6 out, JP4 out, no JP8-JP11.
- 10kohm from TP8 to GND (holds U6 -in; the GND end on a header pin in J4 pin 1). Clip it on with power off.
- -HV supply and floating supply: outputs off at 0V, or disconnected.
- ±12V limits as in Phase 1.
- +HV current limit: 0.5mA at +20V, 1mA at +50V. If the supply cannot be set to 0.5mA, use 1mA or less.

Steps:
1. Turn on +12V, then -12V. Re-send c0.
2. Ramp +HV to +20V in steps of about 5V, watching the current.
3. Measure J9-5 (the actual rail), TP3, the +HV current, and TP5.
4. Measure the divider tap (RV2 pin 1) as well: TP3 should equal it within about 10mV. The tap is at low voltage, but R12's top end is at +HV, so place the probe one-handed.
5. Compute R_bottom = 110k x TP3 / (HV - TP3). It should agree with the ohmmeter preset (1.11k) within about ±6%, since R12 is a 5% part.
6. Ramp to +50V in steps of 10V or less (limit 1mA) and repeat the readings.
7. Check TP3/HV at 20V and at 50V. The ratios should agree within 1%.
8. Adjust RV2 only with power off (section 4.5 explains when). Re-measure after re-powering.

Expected values (R_bottom = 1.11k):

| +HV                    | TP3    | TP3 over the RV2 range (0.82-1.82k) | +HV supply current | Limit | TP5 = TP6 |
|------------------------|--------|-------------------------------------|--------------------|-------|-----------|
| +20V                   | 0.200V | 0.148-0.326V                        | 0.20mA             | 0.5mA | +20V      |
| +50V                   | 0.500V | 0.370-0.814V                        | 0.50mA             | 1mA   | +50V      |
| +150V (section 5 only) | 1.499V | 1.110-2.441V                        | 1.50mA             | 3mA   | +150V     |

- TP3 reads about 5mV below the formula, because of U8's bias current through R30 (22k).
- TP5, TP6, the Q1 tab and both R21 leads are at +HV in this phase, because Q1 is off. This is expected, and it is a shock hazard.

Go / no-go:
- Go:
  - TP3/HV is 0.0094-0.0106 at R_bottom 1.11k.
  - TP3/HV is the same at both rail settings.
  - The +HV current is within ±20% of the table.
  - U8 is cool.
  - ±12V currents are unchanged from Phase 1.

Stop if:
- TP3 does not scale with HV, or TP3 is stuck. Suspects: +HV supply floating (earth post), RV2 or R27 open, or R12 open.
- TP3 is more than 2.5% of HV.
- The +HV current is well above the table (more than 2x expected).
- U8 warms.

### 4.3 Phase 3: level shifter (Q3, U6), output stage unpowered

Configuration (power off and discharged):
- Remove the 10k from TP8. JP3 in, JP6 in, JP4 out, no JP8-JP11.
- Floating 12V: output off at 0V, or disconnected. U7 is unpowered and its +in is open with JP4 out, which is acceptable.
- -HV reference lead: attach the DMM COM to TP12 (soldered lead) or to a header pin in J6 pin 3 now, with power off.
- Limits: +HV 0.5mA at ±20V and 1mA at ±50V. -HV 2mA for the first turn-on check, then 1mA.

Step A, -HV first turn-on check (do this on every new board):
1. Turn on ±12V and re-send c0. Bring +HV to +20V and confirm TP3 = 0.200V.
2. Set the -HV limit to 2mA. Ramp -HV slowly from 0 to -20V while watching the current and voltage.
3. Pass: -HV reaches -20V with the current below 1mA. The expected current is about 0.07mA.
4. Fail: the current pins at 2mA and the voltage collapses. Switch the HV off at once. Suspect Q3 reversed (legs crossed by V1 habit), Q3 shorted D-S, or a C27/R25 fault (an R17 short instead shows TP4 - (-HV) of about 0). The 2mA limit keeps R17 within its rating.
5. After a pass, set the -HV limit to 1mA.

Step B, level shifter measurement:
1. At ±20V, hold codes 0, 64, c0, c0 + 64 (192) and 255. At each one, measure:
   - TP4 relative to -HV (DMM COM on -HV),
   - TP4 relative to GND,
   - TP7, TP8 and TP3,
   - the -HV current.
2. Cross-check at each code where Q3 conducts. The predicted TP4 - (-HV) is 2.74k x (TP3 - TP8) / R_RV1, less about 10mV. It should agree within ±10%. Here R_RV1 is the preset value from section 3.3, and TP3 - TP8 is the voltage across R26 + RV1.
3. Ramp both HV rails to ±50V in steps of 10V or less, alternating between +HV and -HV. Use limits of 1mA / 1mA, and watch both currents. Repeat step 1.
4. Optional: run a small sine (the section 4.5 snippet, A = 20 at ±50V). Scope TP4 with the probe tip on TP4 and the ground on GND. Expect a sine of about ±0.12V riding on about -49.7V DC, inverted relative to TP2. It flattens only if A exceeds about 51, where Q3 cuts off. Use DC coupling with the scope's offset. AC coupling distorts waveforms below about 10Hz.
5. Watch TP5 during this phase. It stays at +HV.

Expected values (RV1 at its preset, R_RV1 = 4.3k, ideal opamps), with TP4 given relative to -HV:

| Rails                  | code 0     | code 64    | code c0 (128) | code 192 | code 255 | TP4 vs GND at c0 | -HV current at c0 | -HV current at 255 | -HV limit |
|------------------------|------------|------------|---------------|----------|----------|------------------|-------------------|--------------------|-----------|
| ±20V                   | 0 (Q3 off) | 0 (Q3 off) | 0.127V        | 0.526V   | 0.918V   | -19.87V          | 0.07mA            | 0.36mA             | 1mA       |
| ±50V                   | 0 (Q3 off) | 0 (Q3 off) | 0.318V        | 0.717V   | 1.109V   | -49.68V          | 0.17mA            | 0.46mA             | 1mA       |
| ±150V (section 5 only) | 0.158V     | 0.557V     | 0.955V        | 1.353V   | 1.745V   | -149.05V         | 0.50mA            | 0.79mA             | 2mA       |

| Point       | Q3 conducting (TP2 below TP3)         | Q3 cut off (TP2 above TP3, i.e. codes below about c0 - TP3/LSB)              |
|-------------|---------------------------------------|------------------------------------------------------------------------------|
| TP8         | equal to TP2 within a few mV          | equal to TP2 (via D5; about (TP2 - TP3)/R_RV1, at most 0.3mA, flows into U8) |
| TP7         | TP8 - (2 to 4V), typically TP8 - 2.9V | about TP2 + 0.6V (D5 forward; U6 not saturated)                              |
| TP4 - (-HV) | table above                           | 0V                                                                           |
| +HV current | 0.20mA (±20V) / 0.50mA (±50V)         | same                                                                         |
| TP5         | +HV                                   | +HV                                                                          |

- The slope dTP4/dV_DAC is -0.64V/V at R_RV1 = 4.3k.
- Q3 dissipation is negligible at these rails (about 60mW centered even at ±150V).

Go / no-go:
- Go:
  - Step A passes.
  - TP8 = TP2 at every code (through Q3 where it conducts, through D5 where it is cut off).
  - TP4 - (-HV) matches the cross-check within ±10%.
  - The -HV current is below 0.6mA at every code (expected 0.46mA at code 255 at ±50V, 0.49mA if TP2 is 2.8Vpp).
  - Q3 and U6 are cool.
  - ±12V currents are within a few mA of Phase 1.

Stop if:
- The -HV current pins or exceeds 1mA.
- TP4 is more than 2V above -HV. On V1 board B, TP4 sat at about -14.6V with -50V rails, from level shifter over-current. On V2 this points to R26 shorted, Q3 reversed or shorted, or TP3 far too high.
- TP4 - (-HV) is about 0 at code c0 with TP7 slightly positive (about TP8 + 0.5V). Q3 is carrying no current: TP3 is missing, JP6 is not making contact, or the R26/RV1 path is open. TP7 at about +11V would mean D5 is open or missing.
- TP8 does not follow TP2 in the conducting region.
- Either ±12V rail moves when -HV is applied. On V1 board C, a fried opamp dragged -12V to -24.9V.
- Q3 warms.

### 4.4 Phase 4: output stage (U7, Q1, R21)

Configuration (power off and discharged):
- Fit JP4. JP3 and JP6 in. No JP8-JP11; measure at TP5/TP6.
- Connect the floating 12V supply: (-) to J9-7, (+) to J9-8. Set it to 12.0V with a 10mA limit, output off.
- RV1 still at the preset (4.3k) and RV2 at 1.11k.
- Limits at ±20V: +HV 5mA, -HV 5mA. At ±50V: 12mA / 12mA.
- Without the Q1 bar, stay at ±50V or below. See section 5 for the thresholds. R21 is always in HS1 (section 3.6).
- Before starting: a DMM on TP5, and a second DMM (COM on -HV) ready for TP4, TP9, TP10 and TP11.
- In Phases 4-5, measure TP4 only against -HV. A DMM or probe from TP4 to GND (10Mohm against TP4's 2.74k source) shifts TP5 by about -1.8V at ±50V (about -5.5V at ±150V).

Steps:
1. Turn on ±12V. Re-send c0.
2. Turn on +HV to +20V and confirm TP3.
3. Turn on -HV to -20V. Expected currents are as in Phase 3. TP5 reads +20V (Q1 still off).
4. Turn on the floating 12V. D3 lights.
5. Measure TP11 - TP12 = 12.0V directly, with the DMM across them. Do not infer it from the supply display.
6. Check that TP5 drops from +20V to about +3 to +5V (the RV1 preset idle), and that the +HV current rises to about 1.9mA.
7. Measure TP4, TP10 and TP9 relative to -HV, and TP5 and TP6 relative to GND. Record all supply currents.
   - TP9/TP10 are bare pads 6.8-8.4mm from Q1's drain pin, which is at the output potential. Solder short insulated leads to them with power off and read those, or use an insulated sprung tip one-handed.
8. Center. With c0 held, turn RV1 down (live, insulated tool, one hand) until TP5 = 0.0 ±0.1V.
   - This lands at R_RV1 of about 3.34-3.65k at ±20V. At ±20V, a high-threshold Q3 can put the center right at the bottom of RV1's range. Do the final trim at ±50V.
9. Direction check.
   - Hold c0 + 8: expect TP5 of about -7.8V.
   - Hold c0 - 8: expect about +7.8V.
   - The output falls as the code rises (confirm on first board).
   - Return to c0.
10. Ramp to ±50V in steps of 10V or less, alternating +HV and -HV. Raise the limits to 12mA / 12mA first. Watch TP5 and both currents at each step. Expect the output to drift by only about -1 to -3V.
11. Re-center RV1 at ±50V (TP5 = 0.0 ±0.1V).
12. Record the full table below.
13. Thermal soak: 10 min at ±50V, centered. Measure Q1, R21 (its top face), the HS1 fins, U7 and R22.
14. Ringing check. Hold c0, then step the code by a few counts, and scope TP5 and also TP10 (Q1 source) and TP9 (gate). At TP9/TP10 use the probe tip only, with the ground clip on GND; AC coupling is fine for this. A re-check of Sim 7 with a realistic IRF730 Crss gives only about 20-47° of phase margin. The stage is still stable, but a step may ring at 2-3MHz on the Q1 source current for about 2us. That ringing is acceptable. A sustained oscillation is not: stop and investigate. Repeat this check with the real output cable attached in Phase 5.
    - Layout note: with R21 laid flat, Q1's -HV return from R22 to the bulk capacitor C27 is now about 73mm long (was about 14mm), and the output node runs about 70mm further to reach Q1's drain. The extra inductance is about 1ohm at 2-3MHz, small next to R22 (75ohm), so it is judged minor, but it is one more reason to look at TP10 and TP9 here.

Expected values, centered (code c0, TP5 trimmed to 0V, no load):

| Quantity                                                              | ±20V                   | ±50V                   | ±150V (section 5 only)   |
|-----------------------------------------------------------------------|------------------------|------------------------|--------------------------|
| TP3                                                                   | 0.200V                 | 0.500V                 | 1.499V                   |
| TP2 = TP8                                                             | 0.000V                 | 0.000V                 | 0.000V                   |
| TP7 (Q3 gate)                                                         | -2 to -4V (typ -2.9V)  | -2 to -4V              | -2 to -4V                |
| TP4 - (-HV)                                                           | 0.150V                 | 0.375V                 | 1.125V                   |
| TP4 vs GND (computed; do not measure it in this phase)                | -19.85V                | -49.63V                | -148.88V                 |
| TP10 - (-HV) (TP4 plus or minus the U7 offset)                        | 0.150V                 | 0.375V                 | 1.125V                   |
| TP9 - (-HV) (Q1 gate)                                                 | 2.4 to 4.8V (typ 3.6V) | 2.6 to 5.0V (typ 3.9V) | 3.3 to 5.7V (typ 4.7V)   |
| TP11 - TP12                                                           | 12.0V                  | 12.0V                  | 12.0V                    |
| TP11 vs GND                                                           | -8.0V                  | -38.0V                 | -138.0V                  |
| TP5 / TP6                                                             | 0V / 0V                | 0V / 0V                | 0V / 0V                  |
| I_Q1 = I_R21                                                          | 2.00mA                 | 5.00mA                 | 15.0mA                   |
| I_Q3                                                                  | 55uA                   | 137uA                  | 411uA                    |
| +HV supply                                                            | 2.20mA                 | 5.50mA                 | 16.5mA                   |
| -HV supply                                                            | 2.08mA                 | 5.19mA                 | 15.6mA                   |
| Floating 12V supply                                                   | about 4.4mA            | about 4.4mA            | about 4.4mA              |
| +HV supply before trimming (RV1 at 4.3k)                              | 1.9mA                  | 4.7mA                  | 14.2mA                   |
| TP5 before trimming (RV1 at 4.3k): ideal / with R29 and bias currents | +3.0V / +3.8 to +4.9V  | +7.6V / +8.3 to +9.4V  | +22.7V / +23.4 to +24.5V |
| Q1 / R21 dissipation                                                  | 0.04W / 0.04W          | 0.25W / 0.25W          | 2.23W / 2.25W            |
| Q1 temperature rise, free air                                         | about +2.5°C           | about +15°C            | Q1 bar mandatory         |

- R21 current = +HV supply current - HV/111k - HV/1M. A symmetric sine does not change the average supply current.
- The floating 12V current is mostly D3 (about 3.3mA) and U7 (about 1mA). It returns through the floating supply's own (-) lead, so the -HV supply does not see it.

Current and thermal limits in this phase:

| Condition                | +HV current                                  | R21 dissipation | Note                                                                       |
|--------------------------|----------------------------------------------|-----------------|----------------------------------------------------------------------------|
| Centered, ±50V           | 5.5mA                                        | 0.25W           | normal                                                                     |
| Output clipped low, ±20V | about 4.2mA                                  | 0.16W           | within the 5mA limit                                                       |
| Output clipped low, ±50V | about 10.4mA                                 | about 1W        | within 12mA. HS1 gets warm (R21 top about 57°C at 40°C ambient, estimate). |
| Full-scale AC/DC sweeps  | raise the limits to 5mA (±20V) / 15mA (±50V) |                 |                                                                            |

- Q1's worst case is the centered point, because any output swing reduces its dissipation.
- R21's worst case is the most negative output.

Go / no-go:
- Go:
  - TP11 - TP12 = 12.0V.
  - The output centers within RV1's range.
  - The direction check shows about 0.98V/code with a negative sign.
  - After trimming, the ±50V centered values are within ±10% of the table. TP9 is within its range.
  - Q1 and R21 are at most about ambient + 20°C after the soak (confirm on first board).
  - ±12V currents are unchanged from Phase 1.

Stop if:
- TP5 goes toward -HV as soon as the floating 12V comes on. Check:
  - Is TP9 about 11-12V above -HV? Then U7 is driving hard: TP4 is too high, so check the Phase 3 values.
  - Is TP9 low while TP5 is still low? Then Q1 is shorted.
- TP5 stays at +HV with the floating 12V on. Check D3, TP11 - TP12, JP4 contact, and whether TP9 is about equal to TP12 (U7 dead or unpowered). Also make sure c0 is actually latched: a random power-up code can cut Q3 off.
- A supply sits at its current limit while centered.
- RV1 cannot reach center:
  - If the output is still positive at RV1 minimum (3.3k): power off, raise R_bottom (RV2) by 20-50ohm, then retry.
  - If the output is still negative at RV1 maximum (4.3k): lower RV2.
  - If the offset is large (more than about 0.3 x HV), suspect assembly first: wrong R26/R27/RV values (4.7k V1 pots), or R29 = 100k.
- Q1 or R21 heats faster than the table suggests.

### 4.5 Phase 5: trim and calibration

Configuration (power off and discharged):
- All of JP3, JP6 and JP4 in.
- Fit exactly one of JP8-JP11. Use JP8 (OUT1) for a standalone board. Leave nothing connected to J7/J8 until TP5/TP6 look right.
- Operating rails (±50V on the current bench). Limits: 12mA / 12mA small-signal, 15mA / 15mA for the sweeps and full-scale sine. Floating supply 10mA.

How the trims interact (R19/R23 unfitted, R29 = 1M):
- V_out = +HV - (K / R_RV1) x (TP3 - V_DAC), with K = 10k / 75 x 2.74k = 365k.
- Centering (V_out = 0 at c0) requires R_RV1 = K x R_bottom / (110k + R_bottom).
- Once centered, the gain equals (110k + R_bottom) / R_bottom regardless of the rails. That is 100.1 at R_bottom = 1.11k.
- In practice:
  - RV2 (power off) sets the gain.
  - RV1 (live) centers.
  - The allowed gain range is about 85-110, because centering must stay within RV1's 3.3-4.3k. In RV2 terms that is about 0.2-0.5kohm (Sim 7); at either end of RV2 the output cannot be centered.
  - The silk labels ("RV1 gain adjust", "RV2 DC adjust") follow the original README.

Steps:
1. Power up in order at the operating rails. Re-send c0. Re-center RV1 so that TP5 = 0.0 ±0.1V at c0.
   - Trim RV1 at the rail you will run, and retrim at every new rail setting. U8's input bias current through R30 (22k) lowers TP3 by a fixed amount that does not scale with the rail: about 5mV with a typical NE5532 (section 4.2), 11-18mV with the Sim 7 model and at maximum bias.
   - A board trimmed at ±50V and run at ±150V is off by about -2.9 to -4.4V (down to -5.2V with a high-bias NE5532; typical parts show somewhat less).
   - A board trimmed at ±150V and run at ±50V is off by about +0.9 to +1.4V.
   - Trimming at ±20V and running at ±150V is worse still.
2. 5-point code sweep. Hold each code and read TP5 with the DMM. Also read TP6: with no load it should be the same within 0.05%. Use the codes for your rails, offset from c0:

   | Rails                  | Codes                                         | Expected TP5                         | Peak +HV current                                     |
   |------------------------|-----------------------------------------------|--------------------------------------|------------------------------------------------------|
   | ±20V                   | c0 -16, -8, 0, +8, +16 (112/120/128/136/144)  | +15.6 / +7.8 / 0 / -7.8 / -15.6V     | 3.8mA                                                |
   | ±50V                   | c0 -40, -20, 0, +20, +40 (88/108/128/148/168) | +39.1 / +19.6 / 0 / -19.6 / -39.1V   | 9.4mA                                                |
   | ±150V (section 5 only) | 0 / 64 / 128 / 192 / 255                      | +125.1 / +62.6 / 0 / -62.6 / -124.2V | 28.9mA (Q1 bar mandatory; HS1 airflow per section 5) |

   Do not use 0/64/128/192/255 at ±20V or ±50V. Every point except the center clips there:
   - The output clips at +HV for codes of c0 - 52 or lower at ±50V (c0 - 21 or lower at ±20V), because Q3 cuts off.
   - It clips at -HV + 1.5% (-49.25V at ±50V, -19.7V at ±20V) for codes of c0 + 51 or higher (c0 + 21 or higher at ±20V).

   Snippet (Pico REPL):

   ```python
   from pico_dac_test import shift_byte
   C0 = 128                                  # your measured center code
   for d in (-40, -20, 0, 20, 40):           # use (-16,-8,0,8,16) at +/-20V
       shift_byte(C0 + d)
       input("code %d: read TP5, then Enter" % (C0 + d))
   shift_byte(C0)                            # park at center
   ```

3. Least-squares fit of V_TP5 = slope x code + intercept. This runs in the Pico REPL or on the PC:

   ```python
   codes = [88, 108, 128, 148, 168]          # the codes you used
   volts = [0.0, 0.0, 0.0, 0.0, 0.0]         # your TP5 readings
   n = len(codes); mx = sum(codes)/n; my = sum(volts)/n
   slope = sum((x-mx)*(y-my) for x, y in zip(codes, volts)) / sum((x-mx)**2 for x in codes)
   intercept = my - slope*mx
   resid = [y - (slope*x + intercept) for x, y in zip(codes, volts)]
   print(slope, intercept, max(abs(r) for r in resid))
   ```

4. Check the fit:

   | Result                     | Expected                        | Accept                                                                                              |
   |----------------------------|---------------------------------|-----------------------------------------------------------------------------------------------------|
   | slope                      | -0.978V/code                    | -0.89 to -1.07V/code. Gain ±5% (R12) and LSB ±4% (5V regulator).                                    |
   | intercept                  | about +125V (about -slope x c0) | consistent with c0                                                                                  |
   | gain G = -slope / LSB_meas | 100.1                           | 95-105                                                                                              |
   | max residual               | small                           | at most 1V at ±50V (confirm on first board). The end points nearest the clip may compress slightly. |

5. Change the gain if needed (optional; for example G = 102.4 gives exactly 1V/code at the nominal LSB):
   1. Power off and discharge.
   2. Set R_bottom = 110k / (G_target - 1), measured at RV2 pin 1 to GND. For example 1.085k for G = 102.4.
   3. Power up and re-center RV1.
   4. Repeat steps 2-4.
6. Enter the CAL into pico_test_script/hvawg_driver.py for this board's channel: `{"slope": <slope>, "intercept": <intercept>}`.
   - The values there now (slope -0.976V/code, intercept +125.0V on all four channels) are placeholders from the design analysis. They have the right sign and are close to the expected fit, but they are not this board's calibration: replace them with the measured fit before trusting any commanded voltage.
   - The driver's header comments predate this procedure: follow this section, not them. Its "Trim RV2 so code 128 reads ~0V at TP5, RV1 for your full-scale" follows the original silk labels; on V2 (R19/R23 unfitted) RV1 (live) centers and RV2 (power off) sets the gain, as above. Its "hardware step H2" does not exist in this document; the procedure is steps 1-4 here. Its "headroom" comment on V_MAX means clip avoidance (next bullet).
   - Set HVAWG.V_MAX below the clip level for your rails: about 18V at ±20V, 45V at ±50V (the current value), and at most 120V at ±150V. V_MAX is a clip-avoidance limit, not a thermal limit: keeping away from the rail does not reduce R21's heating. For ±150V without airflow across HS1, also limit any sustained DC output in the host to about -50V or above (section 5); centered sine outputs through the full range are fine (about 3W average in R21).
   - Tag the CAL with the board serial.
7. AC test. Output = +G x (V_DAC - V_DAC(c0)) = -G x LSB x (code - c0). Start small, then increase the amplitude up to A_max (table below).

   ```python
   import math
   from pico_dac_test import shift_byte
   C0 = 128; A = 5                           # start at A = 5 (about +/-4.9V out)
   table = [max(0, min(255, int(round(C0 + A*math.sin(2*math.pi*i/256))))) for i in range(256)]
   while True:
       for v in table:
           shift_byte(v)
   ```

   - Scope TP5 or TP6 with the 10x probe (section 1.4), DC coupled, ms/div timebase. Stop the loop with Ctrl-C, then run shift_byte(C0).
   - While the loop runs, a clock feedthrough "hash" at a few hundred kHz rides on the waveform. That is not the signal (section 8).
8. Optional external injection via JP3 (power off to change the jumper):
   1. Remove JP3.
   2. Connect a function generator to JP3's lower pin (U6 +in), with its ground to board GND. Connect the generator and set its output (at TP2(c0) DC, zero amplitude) before HV; with JP3 out and no source, U6 +in floats and the output goes to a random rail.
   3. Put the generator in High-Z load mode, so the displayed amplitude is real.
   4. Keep it within ±0.9 x TP3 peak around TP2(c0): at most 0.45V peak at ±50V, at most 0.18V peak at ±20V.
   5. The output is +G x (V_in - TP2(c0)), in phase with the generator.

   This is how the README frequency response was measured.
9. Increase the frequency. Add the intended capacitive load last, through J7/J8 or TP6, with power off and the rails discharged (section 7 steps 1-5). With the real cable attached, repeat the section 4.4 step 14 ringing check at TP5, TP10 and TP9.
   - Q1 tab capacitance: with Q1 on its grounded bar through the Sil-Pad, the tab adds roughly 20-40pF from TP5 to GND (estimate, not simulated). Expect somewhat slower edges with the bar fitted than without it.
10. Monitor throughout:
    - all five supply currents,
    - TP3,
    - TP4 - (-HV),
    - U4/U6/U8 temperature,
    - Q1/Q3/R21 and HS1 temperature.

DAC amplitude limit per rail (sine C0 + A x sin):

| Rails | Usable ±V_DAC (= TP3) | Counts at 9.77mV/LSB        | Linear code window     | A_max (about 90%)                                          | Start A |
|-------|-----------------------|-----------------------------|------------------------|------------------------------------------------------------|---------|
| ±20V  | ±0.200V               | ±20.5                       | c0 - 20 to c0 + 20     | 18 (16 if TP2 is 2.8Vpp)                                   | 5       |
| ±50V  | ±0.500V               | ±51.1                       | c0 - 51 to c0 + 51     | 45 (40 if TP2 is 2.8Vpp)                                   | 5       |
| ±150V | ±1.499V               | ±153 (beyond the DAC range) | 0 to 255 (no clipping) | 127 and at most min(c0, 255 - c0) (DAC-limited, ±124V out) | 13      |

- Recompute with the Phase 1 numbers: A_max = 0.9 x (TP3 - TP2(c0)) / LSB_meas, and never more than min(c0, 255 - c0). The clamp in the snippet stops a wrapped code (-1 becoming 255, or 256 becoming 0) from producing a full-swing spike, but a clamped sine is still clipped.

## 5. Raising the rails beyond ±50V

WARNING: DO NOT EXCEED ±150V. C26 and C27 are 200V parts, and R12, R24 and R25 are 200V rated.

Prerequisites before going above ±50V:
- The board has passed Phases 1-5 at ±50V.
- Q1 heatsink bar fitted and checked per section 3.6.
  - It is mandatory above ±50V in this procedure.
  - The physical limit: above about ±118V, Q1's centered dissipation alone needs the bar at 40°C ambient.
- HS1 checked per section 3.6 (fin to GND under 1ohm, R21 leads to sink open). The envelope for R21 in HS1 (estimates at 40°C ambient in open air; a closed stack is worse):
  - No fan: every case up to about ±100V, including a clipped-low output (R21 about 3.9W). At ±150V without a fan, allow only centered sine and near-0V outputs (R21 element about 87°C, sink about 75°C), and keep any sustained DC output above about -50V. That keeps R21 at or below about 4W, the same as the accepted ±100V clipped case. (In general the no-fan DC limit is +HV - 200V, e.g. about -75V at ±125V.)
  - A DC output held below that at ±150V (a command, a fault, an out-of-range code, or a wrong RV1 preset; R21 takes 8.4W at -140V and 8.9W clipped at the rail) needs at least 1m/s of airflow across HS1's fins. With 1m/s, the sink stays at about 82-85°C and the R21 element at about 111-116°C at 8.4-9W (element limit 150°C). Without it (9W), the sink reaches about 110-113°C and the R21 element about 141-144°C (the Wakefield catalog's table point runs about 5% hotter than its curve).
  - Headroom from the rail only prevents clipping; it does not reduce heating. An output kept 10V off the negative rail clip (-140V) still puts 8.4W into R21. Without a fan, the host limit that matters is the DC limit near -50V (section 4.5 step 6), not V_MAX.
- Scope: 100x HV probe (at least 1kV) or a rated differential probe. DMM: CAT III 600V.
- HV supplies and the floating supply are confirmed for the target voltage. The floating supply's isolation to earth must exceed the -HV magnitude.
- Airflow: a fan per the HS1 envelope above (at least 1m/s across HS1 for any sustained DC output below about -50V at ±150V; in general below +HV - 200V); recommended for closed stacks at ±150V (5-10W per board). Conformal coating is recommended for ±150V operation; mask HS1 and its screws first.

Procedure:
1. Raise the rails in steps: ±50V, ±75V, ±100V, ±125V, then ±150V. Within each step, change the rails 10V or less at a time, alternating +HV and -HV, with the output centered at c0.
2. Before each step, set the small-signal current limits from the table below.
3. At each step:
   - check TP3 = 0.00999 x HV,
   - check the centered currents,
   - check TP4 - (-HV) = 0.0075 x HV,
   - retrim RV1 so that TP5 = 0,
   - soak 10 min, and check the Q1, bar, R21 and HS1 temperatures, plus:
     - C27, the electrolytic closest to R21. Its courtyard is about 10mm from R21's formed leads and body (8.8mm from R21's pad 2 copper) and 10mm from the sink outline.
     - C24 (10uF 1206 on the floating 12V), about 7mm from the sink outline. It must be the X7R 125°C part (Samsung CL31B106KAHNNNE, LCSC C14860; section 3.1), not the May JLC BOM's X5R CL31A106KBHNNNE (85°C). Keep it below 125°C (V2-SUMMARY section 2.8).
4. Stop if any value departs from the table by more than about 10%, or if the bar or HS1 temperature keeps climbing.
5. Recalibrate (section 4.5) at the final operating rails. Update V_MAX, and without a fan at ±150V set the host DC limit (about -50V).

| Rails | TP3    | TP4 - (-HV), centered | +HV / -HV centered | Small-signal limit (each HV)         | Full-scale limit        | Q1 centered | R21 if clipped low | A_max                                           |
|-------|--------|-----------------------|--------------------|--------------------------------------|-------------------------|-------------|--------------------|-------------------------------------------------|
| ±75V  | 0.749V | 0.56V                 | 8.3 / 7.8mA        | 18mA                                 | 20mA                    | 0.56W       | 2.2W               | about 68                                        |
| ±100V | 0.999V | 0.75V                 | 11.0 / 10.4mA      | 22mA                                 | 25mA                    | 1.0W        | 3.9W               | about 91                                        |
| ±125V | 1.249V | 0.94V                 | 13.8 / 13.0mA      | 25mA                                 | 30mA                    | 1.55W       | 6.1W               | about 115                                       |
| ±150V | 1.499V | 1.125V                | 16.5 / 15.6mA      | 25mA (up to 30mA for nuisance trips) | 35mA (never above 40mA) | 2.23W       | 8.9W               | 127 and at most min(c0, 255 - c0) (DAC-limited) |

- Floating 12V: 10mA limit at every rail.
- Phase 2/3-style checks at these rails (monitor only, or level shifter only): use +HV limits of about 2x the TP3 divider current (3mA at +150V) and a -HV limit of 2mA.
- At ±150V with Q1 alone on a 10°C/W bar (2.23W centered):
  - the bar sits at about ambient + 22°C;
  - Q1's junction sits at about ambient + 27°C.
- R21's heat goes into HS1, not the bar. At ±150V centered (2.25W), HS1 runs at about 68°C at 40°C ambient without a fan (estimate).
- At ±150V, the 35mA full-scale limit does not catch a clipped-low fault. HS1, with airflow, is what protects R21. Without a fan, a clipped-low fault relies on the element staying just under its 150°C limit (estimate about 141-144°C).

## 6. Stacking and multi-board bringup

0. Stack spacing requirement (set by the standoffs; it can be chosen when the stack is built and is not a board constraint; see V2-SUMMARY section 4):
   - At least 22mm clear between boards (about 23.5mm top-to-top with 1.6mm boards), for example 25mm M3 standoffs. The upright Q1 and Q3 stand up to 19.9mm (Vishay TO-220 maximum), plus a 2mm margin. This assumes Q1 is held to its bar by a clip; a screw through Q1's tab needs roughly 25-27mm top-to-top.
   - Every THT lead trimmed to 2.5mm or less below the board (section 3.1). Untrimmed Q1/Q3 leads reach about 8mm (up to 9.5mm) below the board. At 23.5mm top-to-top that leaves under 1mm to the Q1/Q3 bodies on the board below with nominal parts, and maximum-tolerance parts would touch them; untrimmed leads would need about 25-27mm top-to-top to keep the 2mm margin.
   - Bottom board on feet of at least 8mm, because HS1's nuts and screw tails stick out about 5.7-6mm below it. On the boards above, the same hardware stays well clear of the HS1 below.
   - Q1 bar height is limited by the chosen spacing: each board's bar must fit within the clear space between boards (the standoff length) and must not hang below its board, so the bars do not touch.
1. Bring up each board alone first (Phases 0-5) at the stack's operating rails. Record its c0, trims and CAL.
2. Output select: exactly one of JP8-JP11 per board, different on each board. Two boards on the same OUT fight each other through their R31s.

   Suggested assignment:

   | Chain position (from the Pico) | Driver channel | Jumper | Output |
   |--------------------------------|----------------|--------|--------|
   | nearest                        | ch0            | JP8    | OUT1   |
   | 2nd                            | ch1            | JP9    | OUT2   |
   | 3rd                            | ch2            | JP10   | OUT3   |
   | 4th                            | ch3            | JP11   | OUT4   |

   Record the assignment.
3. Cables: straight-through, pin n to pin n, V2 pinouts only. Before first use, check every cable with an ohmmeter: pin n to pin n under 1ohm, adjacent pins open. The J3-J8 sockets are unkeyed 2.54mm: a cable plugged in turned 180° connects +100V to -100+12V and GND to -100V, and one shifted by a pin shorts rails together. Step 3a catches both.

   | From board n                                               | To board n+1   | Carries                                                 |
   |------------------------------------------------------------|----------------|---------------------------------------------------------|
   | J2 (serial out: GND, serial_out, shift clock, store clock) | J1 (serial in) | Data passes through each 74HC595; the clocks are bussed |
   | J4                                                         | J3             | GND, GND, +12V, -12V                                    |
   | J6                                                         | J5             | +100V, GND, -100V, -100+12V                             |
   | J8                                                         | J7             | OUT1, GND, OUT2, GND, OUT3, GND, OUT4                   |

   3a. Installed-stack check (power off, after all cables are plugged in):
   - On every board k from 2 up, the J9 header pins are exposed (J9 unplugged). On board 1, measure at the J9 plug's screw heads, with the harness disconnected from the supplies.
   - For each pin p = 1 to 8, measure board 1 J9-p to board k J9-p: under 1ohm.
   - Also measure board k J9-5 to board 1 J9-8, and board k J9-7 to board 1 J9-1: neither may read under 1kohm (a J5/J6 cable turned 180° reads under 1ohm here).
   - Check that no cable header pin is left exposed beside any socket, which would mean an offset plug.
   - Check the output bus by measuring each board's JP8-JP11 lower pins to board 1's: under 1ohm.
   - Any other result: power stays off; reseat or replace the cable and repeat.
4. Only the first board's J9 is powered. Leave the other J9 blocks unplugged, and never connect a second bench supply set. WARNING: THE UNPLUGGED J9 CONTACTS ON THE OTHER BOARDS ARE LIVE, because they share the daisy-chained rails. Never plug or unplug any J9 while the stack is powered.
5. Current limits scale with the board count N:
   - ±12V: 60mA x N (expect about 29/26mA x N).
   - HV small-signal: the per-board limit from sections 4.4 and 5, times N.
   - Floating 12V: 10mA x N.
   - -HV first turn-on in a stack (c0 latched on every board): limit 2mA + 0.1mA x N (round down to what the supply can set). Pass only if the current is at most 0.1mA x N (expected about 0.07mA per board at -20V).
   - Do not scale the 2mA check by N. One reversed or shorted Q3 draws at least about 2.8mA at -20V (-HV through R17 and R26/RV1; more if U6 also feeds it through D5). With N = 4 the total is about 3.1mA, which would pass an "under 1mA x N" test, and at -50V that board's 0402 R17 would take at least 0.13W against its 63mW rating. If the current pins at the limit or exceeds 0.1mA x N, switch HV off and split the stack to find the board.
6. Start the stack at ±20V. Turn on +12V then -12V. Before any HV, latch c0 on every board (a single-byte shift_byte does not set a stack):

   ```python
   from hvawg_driver import HVAWG
   hv = HVAWG(use_spi=True)                  # ch0 = board nearest the Pico
   hv.set_codes([c0_0, c0_1, c0_2, c0_3])    # your measured c0 per channel; 4 entries even with fewer boards
   ```

   Then turn on +HV, then -HV (with the step 5 check), then the floating 12V.
7. Cascade order check. Move one channel at a time and confirm which board responds:

   ```python
   # reuses hv from step 6
   C0 = [128, 128, 128, 128]                 # measured center codes per channel
   hv.set_codes(C0)
   for ch in range(4):
       c = list(C0); c[ch] = C0[ch] - 8      # about +7.8V on that channel only
       hv.set_codes(c)
       input("ch%d moved? check each board's TP5 / its OUT pin, then Enter" % ch)
   hv.set_codes(C0)
   ```

   - The driver always shifts 4 bytes. With fewer than 4 boards, the bytes for the missing far channels fall off the end of the chain, so ch0 is always the nearest board.
   - Pass: only the expected board's TP5, and its selected OUT pin on J7/J8, moves.
   - If a different board moves, fix the cabling or the CAL/JP mapping.
   - If no board moves, check the J2 to J1 cabling and the clocks.
8. Raise the stack's rails per section 5, with each board's Q1 on its bar above ±50V, and air moving across every HS1 if a sustained DC output may sit below about -50V at ±150V (below +HV - 200V in general). Retrim RV1 on each board at the final rails. Load each board's CAL into hvawg_driver.py in channel order.
9. When using main.py (the serial server): it parks all channels at 0V (about c0 with a correct CAL) if the host is silent for 100ms. During manual REPL testing, stop main.py first.

## 7. Shutdown procedure

1. Set every channel to its center code c0, so the output is about 0V.
2. Ramp +HV and -HV down to 0 together, in steps (at most 10-20V at a time), alternating. The output stays near 0V as they fall.
3. Switch the floating 12V off.
4. Switch the HV supply outputs off. Wait at least 30s.
5. Verify under 5V with the DMM at J9-5 to GND, J9-7 to GND and J9-8 to GND (and J9-8 to J9-7). TP12 and TP5 are alternatives.
6. Switch -12V, then +12V off (±12V always last).
7. Only now touch the board, move jumpers, or remove clip leads.

- Emergency: switch both HV outputs and the floating 12V off at once, keep ±12V on for at least 30s, then continue from step 5.
- The V2 changes (R30) protect U8 far better than V1 against a fast ±12V loss with HV up (at most 0.19mA instead of 13-120mA), but keep the order anyway.

## 8. Troubleshooting

| Symptom | Most likely cause | Check |
|---|---|---|
| A rail reads 0V or wanders at the board, but the supply display looks right | Lead on the supply's green earth post instead of an output terminal, or no return lead to GND | Wiring against the section 1.5 table; measure at the J9 plug screws vs GND |
| +12V pin reads about -38V (the LV rails far below GND) at ±50V | Triple supply COM not connected to board GND, so the LV island floats down toward -HV | Power off; check COM to J9-1 continuity. Do not connect the Pico while this is unresolved. |
| TP3 stuck (e.g. a fixed 6.8V on V1) or not tracking +HV | +HV supply floating (earth post); RV2/R27 open or at an end stop; R12 open | TP3/HV ratio; RV2 pin 1 to GND resistance (power off); J9-5 vs GND |
| TP4 far above -HV (e.g. -14V at -50V rails) with the rails sagging | Level shifter over-current. On V1: RV1 at about 0ohm. On V2 R26 prevents that, so suspect R26 shorted, Q3 reversed or shorted, R17 damaged, or TP3 far too high. | JP6 pin 1 to TP8 at least 3.3k; Q3 orientation; section 4.3 Step A |
| -HV supply pins at the 2mA limit on first turn-on | Q3 legs crossed (V1 habit) or Q3 D-S short; C27/R25 fault; in a stack, a mis-plugged J5/J6 cable | Q3 orientation; section 6 step 3a in a stack. (The section 3.2 GND to -100V check cannot see Q3; an R17 short does not over-current, it shows TP4 - (-HV) of about 0.) |
| TP5 pinned at +HV with everything powered | Q1 off: floating 12V off or reversed (D3 dark); JP4 out; U7 dead; code on the cutoff side (below c0 - TP3/LSB), or a random power-up code; JP3 out | D3; TP11 - TP12; TP9 - TP12 of about 0 means U7 is not driving; TP8 equal to TP2 and above TP3, with TP7 about TP8 + 0.6V, means Q3 is cut off; re-send c0 |
| TP5 pinned near -HV | Code too high; TP4 too high (TP3 high: RV2 too large; R_RV1 too low); Q1 shorted D-S. The V2 trim ranges are narrow, so a large offset points to assembly: wrong R26/R27/RV1/RV2 values, or R29 = 100k. | +HV current about 2HV/10k; TP9 - TP12 of about 11-12V means U7 is railed (TP4 too high); TP9 low with TP5 still low means Q1 is shorted |
| RV1 cannot bring TP5 to 0 | R_bottom outside the usable window of about 1.02-1.32k (RV2 outside about 0.2-0.5kohm; Sim 7) | Section 4.4 stop-if list: adjust RV2 by tens of ohms, with power off |
| Sine vanishes, or a rail distorts, when -HV is applied; ±12V dragged (V1 board C: -12V went to -24.9V and +HV sagged to 30.7V) | A fault drawing current: a fried opamp shorting the rails, or a reversed or shorted Q3 | Supply currents against the Phase 1 baseline; power off and measure +12V to -12V resistance (section 3.2) |
| Spark when fitting a jumper or the J9 plug | Hot-plugging (V1 board A, JP4) | Never do it. After a spark, suspect U7, Q1 and U6; repeat Phases 3-4 at ±20V. |
| No sine anywhere / TP2 flat | Pico script stopped (exception, or the main.py watchdog parked it); wrong GP pins (GP3/GP2/GP5 are GPIO numbers); Pico GND not on J1-1; ±12V off (TP1 not 5V); scope timebase in ns instead of ms; AC coupling on a Hz-range sine | REPL output; shift_byte(0) / shift_byte(255) with the DMM on TP2; scope settings |
| TP2 about +5V at code 0 | JP2 open | JP2 solder bridge |
| TP2 about -1.25V at code 128, full scale about 5Vpp | JP1 bridged | JP1 should be open |
| TP2 missing bits or steps | 3.3V drive into the 5V 74HC595 (marginal); a loose J1 wire | Staircase via dc_test() on the scope |
| Low codes compressed (the 0-64 step smaller than 64-128) | DAC0808 output compliance (TP2 above about +0.4V) (confirm on first board) | Phase 1 step 8. Only matters above ±50V. |
| "375kHz" hash on TP5 (or TP2/TP4) | Clock feedthrough from continuous bit-banging, not the signal | It disappears while a code is held; use the scope's 20MHz bandwidth limit or averaging |
| Scope readings are nonsense, or a rail shifts when the probe is attached | Probe ground clip on a node other than GND (shorts it to earth); 50ohm input; 1x probe | Ground clips on GND only; 1Mohm input; 10x or 100x probe |
| The output moves the wrong way for commanded voltages | A CAL entry with a positive slope (a typo or an old fit) in hvawg_driver.py; the shipped placeholders (-0.976 / +125.0) have the right sign but are not a board's calibration | Refit per section 4.5; the slope is negative |
| A supply drops into current limit when the output swings negative | The limit is set for the centered draw; clipped-low draws 2HV/10k | Use the full-scale limits (sections 4.4 and 5) |
| The offset changes when the rails change | RV1 trimmed at a different rail (the R29/bias current effect), or TP2(c0) not about 0 | Retrim RV1 at the operating rails; recheck c0 |
| D3 dark in Phase 4 | Floating supply off, reversed, or not connected to J9-7/J9-8 | TP11 - TP12 |
| U4 or U8 warm with ±12V only | Rail polarity, orientation, solder faults, or oscillation of the unused halves U4B/U8B. On V2 they are tied off as grounded followers (pin 5 to GND, pin 7 to pin 6), so pin 7 should sit at about 0V. | U4/U8 pin 7 about 0V DC; scope it for HF oscillation; check the pin 5/6/7 solder joints |
| HS1 fin to GND reads high or open | The internal-tooth washer at hole 2 is not biting through the anodizing, or the nuts are loose | Reseat the tooth washer and re-torque (section 3.6). Never run with HS1 floating. |
| R21 or HS1 much hotter than section 5 suggests | Output sitting near the negative rail (code, RV1 preset, fault); no airflow; poor grease contact | TP5 and the +HV current; reduce the rail or add airflow (section 5); reseat R21 with fresh grease |
| 2-3MHz ringing at TP10/TP9 after a step | Low phase margin with the real IRF730 Crss at high VDS (about 20-47°, Sim 7 re-check); cable or load capacitance | Acceptable if it dies out within a few us. A sustained oscillation is not expected: stop and investigate. |
| In a stack, the wrong board responds, or two boards fight | Chain order or cabling; duplicate JP8-JP11 selection | Section 6 step 7; one jumper per board, all different |

## 9. Per-board record sheet

Copy this section for each board and fill it in.

```
Board serial / ID: ________   Revision: V2 (J9 edge notch, 7-pin J7/J8, R21 flat in HS1)   Date: ________   Operator: ________

PHASE 0 (power off)
  Visual: Q3 straight [ ]  Q1/Q3 not swapped [ ]  C26/C27 polarity [ ]  R19/R23 empty [ ]  R32/C32 empty [ ]
          R26-R31, D4, D5 present and correct [ ]  RV1/RV2 = 1k [ ]  JP1 open [ ]  JP2 bridged [ ]
  +100V->GND ____ k   GND->-100V ____ M   +100V->-100V ____ M   -100+12V->-100V ____
  TP5->GND ____ k   +12V->GND ____   GND->-12V ____   +12V->-12V ____   TP1->GND ____ k
  RV2 preset: R_bottom (RV2 pin1->GND) ____ k      RV1 preset: R_RV1 (JP6 pin1->TP8) ____ k
  Screw direction raising R: RV1 CW / CCW     RV2 CW / CCW
  R21 lead bend (body->outer lead face) ____ mm   HS1: R21 leads->sink ____ M   fin->GND ____ ohm
  Q1 bar (if fitted): Q1 tab->bar ____ M   bar->GND ____ ohm

PHASE 1 (+/-12V)
  I(+12) ____ mA   I(-12) ____ mA   TP1 ____ V   TP3 ____ mV   TP8 ____ mV
  TP2: code 0 ____  64 ____  128 ____  192 ____  255 ____ V
  c0 = ____   TP2(c0) = ____ mV   LSB_meas = ____ mV   low-code compression? Y/N
  Temps after 5 min: U4 ____ U8 ____ U6 ____ C

PHASE 2 (+HV only, JP6 out, 10k on TP8)
  +HV 20V:  TP3 ____ V  I(+HV) ____ mA  TP5 ____ V
  +HV 50V:  TP3 ____ V  I(+HV) ____ mA  TP5 ____ V    R_bottom from TP3 = ____ k

PHASE 3 (level shifter)
  -HV first turn-on (2mA limit): reached -20V at ____ mA   PASS / FAIL
  Rails ____ : code |  TP4-(-HV) | TP4 vs GND | TP7 | TP8 | I(-HV)
               0    |            |            |     |     |
               64   |            |            |     |     |
               c0   |            |            |     |     |
               192  |            |            |     |     |
               255  |            |            |     |     |

PHASE 4 (output stage)
  TP11-TP12 ____ V   TP5 at first power (RV1 preset) ____ V   direction check c0+8 -> ____ V, c0-8 -> ____ V
  Centered @ rails ____ : TP4-(-HV) ____  TP10-(-HV) ____  TP9-(-HV) ____  TP5 ____  TP6 ____
            I(+HV) ____ mA  I(-HV) ____ mA  I(float) ____ mA  I(+12) ____  I(-12) ____
  Soak 10 min: Q1 ____ C   R21 ____ C   HS1 fins ____ C   U7 ____ C   ambient ____ C
  Ringing after a small step (TP5 / TP10 / TP9): ____ MHz, dies out in ____ us  /  none
  R_RV1 at center (power off, JP6 out, optional) ____ k

PHASE 5 (calibration) at rails ____
  codes:  ____ ____ ____ ____ ____
  TP5:    ____ ____ ____ ____ ____
  slope ____ V/code   intercept ____ V   max residual ____ V   gain G ____   A_max used ____
  CAL entered in hvawg_driver.py as channel ____   V_MAX ____   Output jumper JP__ (OUT_)

Notes / anomalies:
```

### V2 board log

| Board | Date | Rails reached | Status / notes |
|-------|------|---------------|----------------|
|       |      |               |                |

## 10. One-page bench checklist

Before power:
- [ ] V2 board (J9 in the top-edge notch, 7-pin J7/J8, R21 flat in HS1, "HV_AWG v2"). Harness is V2 (plug 1840421, pin 1 = right end, twin ferrule on pin 7) and passed the section 1.5 harness verification. No earth straps on the -HV or floating supply. In a stack: section 6 step 3a passed.
- [ ] HS1: fin to GND under 1ohm; R21 leads to sink open.
- [ ] Q3 straight legs. C26/C27 polarity. R19/R23 empty. R32/C32 empty. JP1 open, JP2 bridged. R29 = 1M, RV1/RV2 = 1k.
- [ ] Ohm checks (section 3.2): +HV to GND about 100k, GND to -HV about 1M, +HV to -HV about 1.1M, ±12V and +5V not shorted.
- [ ] Presets: R_bottom 1.11k (RV2 pin 1 to GND); R_RV1 4.3k (JP6 pin 1 to TP8, JP6 out).
- [ ] Jumpers for the phase (section 3.4). Q1 bar and insulation checked if going above ±50V.
- [ ] Current limits set before enabling outputs. Scope input at 1Mohm, grounds on GND only, probes rated.

Power on:
1. +12V
2. -12V
3. Send c0
4. +HV
5. -HV
6. Floating 12V

| Phase | Jumpers                              | Limits at ±50V                   | Key readings at ±50V                                                                           |
|-------|--------------------------------------|----------------------------------|------------------------------------------------------------------------------------------------|
| 1     | JP3, JP6 in                          | ±12V: 60mA                       | TP1 5.0V; TP2 +1.25/0/-1.24V at codes 0/128/255; c0; about 29/26mA                             |
| 2     | JP3 in, JP6 out, 10k from TP8 to GND | +HV 1mA                          | TP3 0.500V; I 0.50mA; TP5 = +50V                                                               |
| 3     | JP3, JP6 in                          | -HV 2mA check, then 1mA; +HV 1mA | -HV under 1mA at -20V; TP4 - (-HV) 0.318V at c0                                                |
| 4     | add JP4                              | 12 / 12mA, floating 10mA         | TP11 - TP12 12.0V; trim RV1 for TP5 = 0V; I 5.5 / 5.2 / 4.4mA; TP4 - (-HV) 0.375V              |
| 5     | add one of JP8-JP11                  | 15 / 15mA for sweeps             | codes c0-40/c0-20/c0+20/c0+40 give +39.1/+19.6/-19.6/-39.1V; slope about -0.98V/code; A_max 45 |

Never:
- hot-plug a jumper or the J9 plug;
- clip a scope ground anywhere but GND;
- use a 50ohm scope input;
- run above ±50V without the Q1 bar;
- hold a DC output below about -50V at ±150V (below +HV - 200V in general) without air moving across HS1;
- run with HS1 not bonded to GND;
- exceed ±150V;
- use the V1 harness;
- trust the driver's placeholder CAL.

Power off:
1. c0 on all channels.
2. Ramp ±HV to 0 together.
3. Floating 12V off.
4. Wait at least 30s; verify under 5V at J9-5, J9-7 and J9-8.
5. -12V, then +12V off.
