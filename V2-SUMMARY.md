# HVAWG V2: status, simulation results, decisions and remaining work

For: Yichen. Date: 2026-09-24. Status: the V2 design files and gerbers were committed on 2026-09-25 (61018b9).

TL;DR: Your items 1-9 are implemented and verified in the KiCad files, and the JLCPCB gerbers are regenerated from the final board. V2 also includes:
- a high-voltage safety revision (sections 2.6 and 2.7)
- R21 moved onto the board and laid flat in a Wakefield 272-AB heatsink (section 2.8)
- a re-layout: a plain 207 x 58.8mm rectangle with J9 in a small edge notch, new silkscreen, and U4B/U8B tied off (section 2.9)
- Sims 6 and 7: R21 parasitics and a coverage audit of every final value (section 2.10)
- the resolved decisions in section 3: R29 = 1Mohm, SMD test pads for TP9-TP12, J9 at 3.50mm, no BSS126, R21 flat, and R30 as a 2W 2512

LTSpice checks show the V2 values are correct as long as R19/R23 stay unpopulated.

Details below.

## 1. What was implemented

| #   | Your item                                                 | Implementation                                                                                                    | Status                                                                        |
|-----|-----------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| 1   | Fix the Q3 (IRF9610) S/D swap                             | Schematic pin map fixed, pad nets swapped, copper rerouted                                                        | Done, committed in 225dc5d                                                    |
| 2   | RV1 as a rheostat + 3.3k series                           | RV1 = 1k (wiper tied to pin 3), R26 = 3.3k                                                                        | Done                                                                          |
| 3   | RV2 as a rheostat + 820ohm series                         | RV2 = 1k (wiper tied to pin 3), R27 = 820 to GND                                                                  | Done                                                                          |
| 4   | Gate-source resistor + zener on the FETs                  | Q1: R28 100k + D4 BZT52C12 (K to G). Q3: R29 1Mohm (was 100k; changed per Sims 1/3/5) + D5 BZT52C12 (K to S)      | Done                                                                          |
| 5   | 10k between the divider tap and U8                        | R30 in series with U8 pin 3. Only U8's input sits behind it. First 10k, now 22k 2W 2512 (sections 2.5, 2.7, 2.10) | Done, see the R30 finding in section 2.5                                      |
| 6   | Test points on the Q3/Q1 gates and sources and U7's rails | TP7/TP8 = Q3 G/S, TP9/TP10 = Q1 G/S, TP11/TP12 = -100+12V / -100V                                                 | Done. TP9-TP12 are SMD 1.5mm diameter pads 1.5-5.8mm from the pins they probe |
| 7   | TP6 after the series R; keep TP5 before it                | TP5 on the amp side, TP6 on the new net output_post                                                               | Done                                                                          |
| 8   | Empty pads for an R+C test load                           | R32 (1206) + C32 (first 0603, now 1206 pads; section 2.7), both DNP, from TP5 to GND                              | Done, see decision 4 in section 3 for where it attaches                       |
| 9   | Series output resistor on board                           | R31 = 4.7k (first 1206, now 2512 for voltage and fault margin; section 2.7)                                       | Done                                                                          |

The JP8-JP11 output selectors now sit on output_post, after R31.

Six existing nets were renamed automatically by KiCad because the new parts changed the alphabetical naming. Connectivity is unchanged:

| Old name     | New name       |
|--------------|----------------|
| Net-(Q1-G)   | Net-(D4-K)     |
| Net-(Q1-S)   | Net-(D4-A)     |
| Net-(Q3-G)   | Net-(D5-A)     |
| Net-(Q3-S)   | Net-(D5-K)     |
| Net-(JP10-A) | Net-(Q1-D)     |
| Divider tap  | Net-(C14-Pad1) |

### Verification of the design files

The figures in this subsection and in section 1b are from that stage. The current board's check results are in section 2.8.

- Netlist: every item has the intended connectivity, and exactly 13 nets changed membership. All 260 of 260 pin-to-net assignments match between the schematic and the board.
- ERC: no new errors. There are actually two fewer: the unconnected RV1/RV2 pin 3 errors are gone because of the rheostat ties.
- DRC (after the connector fix in section 1b): 0 errors, 0 unconnected, 0 clearance/short errors, 0 silkscreen overlaps, 0 silkscreen over copper. What remains are pre-existing warnings only:
  - 8 silk_edge_clearance: R21/Q1 graphics, which intentionally hang past the board edge for heatsinking.
  - 37 lib_footprint_mismatch: the KiCad 9 library versions differ from the ones on the board. These were intentionally not "updated", to avoid changing pads on parts that work.
  - 29 footprint_symbol_mismatch: exclude-from-BOM flag differences.
  - For comparison, the original design had 5 errors and 91 warnings, and the first V2 version had 5 errors and 165 warnings.
- Gerbers: regenerated and installed in jlcpcb/.
  - Every drill-hole change is accounted for (PTH holes went from 125 to 132 overall). The V2 parts added 7 new Keystone test points (TP6-TP12). The connector fix moved connector pins and TP8 and changed some vias.
  - A second export matches the installed files byte-for-byte except timestamps.

### 1b. Connector spacing fix (the 5 DRC errors)

The original design had 5 courtyard-overlap errors: the daisy-chain and power connectors sat flush against each other. Since only V2 boards will be stacked, they were spread apart by the smallest amounts that clear them:

| Part                          | Move                         | Notes                                    |
|-------------------------------|------------------------------|------------------------------------------|
| J1-J4, J7, J8                 | none                         | Daisy-chain pins unchanged               |
| J5 + J6 (HV daisy-chain pair) | +1.27mm in x, both identical | Every mating pair still lines up exactly |
| J9 (bench power input)        | +1.27mm in y                 | Pinout unchanged                         |
| J10 (GND pin)                 | +1.27mm in x                 |                                          |
| TP8, R31                      | +0.5mm / +0.25mm in x        | Moved to make room                       |

- Assembly note: J3+J5 and J4+J6 used to form one continuous 8-pin row, and J7+J10 a 5-pin row. Each connector now needs its own header strip.
- HV clearances improved. The closest +HV to -HV copper went from 0.47mm to 0.84mm. All rerouted copper keeps at least 0.8mm between the HV rails and at least 0.5mm from HV to anything else.
- Every pad kept its net.
- The schematic is untouched.

## 2. Findings from the simulations

The netlists are in simulations/v2/ (the logs come from running them and are not committed). There is no LTSpice model for the IRF9610 or IRF730, so datasheet-based VDMOS approximations were used. The comparisons are more trustworthy than the absolute numbers. The LM8261 uses the vendor model, unchanged.

### 2.1 Your RV1/RV2 values are correct when R19/R23 are not fitted (Sim 1)

With the op-amps enforcing their virtual shorts:
- Centered gain = (R21 / R_src) x R_load / R_RV1
- Centering requires R_RV1 = K x R_bottom / (110k + R_bottom), where K = (R21 / R_src) x R_load

| Board                       | K                        | RV1 needed to center              | Result with the V2 range (3.3-4.3kohm)                      |
|-----------------------------|--------------------------|-----------------------------------|-------------------------------------------------------------|
| R19/R23 unfitted (as built) | 10k/75 x 2.7k = 360,000  | about 3.6kohm at R_bottom = 1.11k | Centers at ±50V and ±120V, gain about 90-120                |
| R19/R23 fitted              | 10k/42.9 x 96.4 = 22,500 | about 225ohm                      | Cannot center. Output stuck near the + rail, gain about 5-7 |

- R19 and R23 must stay DNP.
- Note on BRINGUP-V2.md: an earlier draft's Phase 3 example (96.4/R_RV1, R_RV1 = 225ohm) described the fitted configuration. The current BRINGUP-V2.md uses the as-built numbers, 2.74k and about 3.65kohm. With the final values the usable gain range is about 85-110 (from the RV2 window in section 2.10 item 3).
- Output = 100 x V_DAC, independent of the rail voltage (the monitor compensation doing its job). The usable DAC swing is therefore about ±V_TP3, roughly ±0.5V at ±50V rails. A full-scale DAC (about ±1.4V) clips at both rails, which explains the clipped outputs seen on the bench at ±50V.

### 2.2 R29 = 100k breaks rail-independence (Sims 1, 3, 5), recommend 1Mohm

R29 carries V_SG / R29, about 18-38uA depending on Q3's threshold, around Q3. That current does not scale with the rail voltage, while Q3's current does (about 137uA at ±50V, about 332uA at ±120V). So a board trimmed at one rail voltage is off-center at the other.

Output offset after trimming at one rail voltage and then running at the other:

| R29   | Q3 Vth        | Trimmed at ±120V, run at ±50V | Trimmed at ±50V, run at ±120V |
|-------|---------------|-------------------------------|-------------------------------|
| 100k  | -2 / -3 / -4V | +3.6 / +5.8 / +7.9V           | -8.7 / -14.0 / -19.1V         |
| 1Mohm | -2 / -4V      | +0.2 / +0.6V                  | -0.5 / -1.5V                  |

At 100k it also degrades the level shifter (Sim 3):

| Metric                            | V1 (no R29/D5) | R29 = 100k                                | R29 = 1Mohm (+ D5) |
|-----------------------------------|----------------|-------------------------------------------|--------------------|
| THD at ±50V                       | 2.2%           | 5.3%                                      | 2.65%              |
| THD at ±120V                      | 1.3%           | 2.2%                                      | 1.55%              |
| TP4 shift                         | -              | -77mV (about +0.1V DAC-equivalent offset) | -7.7mV             |
| Usable positive DAC swing at ±50V | -              | -19%                                      | -                  |

- 1Mohm still holds Q3 off. Worst-case IRF9610 gate leakage (about 100nA) x 1Mohm is about 0.1V, far below |Vth| = 2-4V.
- It's a value change only. Same 0402 footprint, so the gerbers are unaffected.
- With 1Mohm, the nominal RV2 setting (R_bottom about 1.11k) centers at both rail voltages (RV1 about 3.57k).

### 2.3 D4/D5 zeners, R28, and R31 (Sims 2 and 3): fine with the IRF730

- Output stage at 100kHz (IRF730 as fitted, and STW11NM80):
  - V2 costs 0.3% of swing at TP6 with a 10pF load, and 0.9% with 20pF.
  - It adds a +0.3V offset, which the trim removes. (This is sim-stage wording. In the V2 procedure, RV1 is re-trimmed live at the operating rail to center the output, and RV2 sets the gain; see BRINGUP-V2.md section 4.5.)
  - Stable, with no oscillation after a step.
  - The zeners never conduct (Q1 Vgs stays within 1.6-4.5V).
- Level shifter: D5 is harmless.
  - Bandwidth stays around 20MHz.
  - Phase margin improves from about 71° to 77°.
  - It speeds up recovery from clipping (it keeps U6 out of saturation).

### 2.4 BSS126 option: rejected (2026-09-24)

The BSS126 is not used. Its SOT-23 package (about 0.36W) can't dissipate the roughly 2.2W in Q1 at ±150V, and the real part is depletion-mode, which this circuit can't turn off. Q1 stays the IRF730. The sim findings below are kept for the record.

If the output FET is ever swapped to the BSS126 (the fast, low-capacitance option from earlier sims):
- The earlier "BSS126 + 1k gate stopper" setup has a hidden limit cycle of about 0.2Vpp at about 2.8MHz. It only shows up in step/zero-input runs, not in a 100kHz sine run.
- With V2's R31 (4.7k) added, it oscillates at 10-13Vpp (about 2.2MHz, self-starting).
- A stopper of about 3.3k brings the residual down to 0.4-0.6Vpp and still reaches about ±148V.
- The datasheet says the BSS126 is depletion-mode, while the sims used an enhancement-mode approximation. D4 would then fight its turn-off. This needs a proper model before committing to the BSS126.

The sims suggested adding a series gate resistor footprint between U7's output and Q1's gate: 0ohm for the IRF730, or about 3.3k for the BSS126. This was not on the original list and has not been added (see decision 3 in section 3).

### 2.5 U8 monitor protection (Sim 4): big improvement, one remaining gap

Current into U8's input pin (NE5532 absolute max ±10mA):

| Scenario                                 | V1 (current boards)                                    | V2                  |
|------------------------------------------|--------------------------------------------------------|---------------------|
| Worst DC fault, at 150V                  | 1.35mA (7.4x margin)                                   | 0.15mA (65x margin) |
| RV2 wiper open, powered                  | tap clamps at 12.6V, 1.25mA                            | tap 2.44V, 0mA      |
| ±12V falling in 1-10ms with +HV still on | 13-120mA (the 10uF C15 dumps through U8's clamp diode) | at most 0.19mA      |

- The last row matters for the boards we already have. Any fast ±12V shutdown with HV still up exceeds U8's input rating, and it is a plausible cause of the op-amp failures seen so far.
- NOTE: ON V1 BOARDS, STRICTLY FOLLOW THE SHUTDOWN ORDER. RAMP +HV TO 0 BEFORE TURNING OFF ±12V.
- Item 3 (rheostat tie + R27) handles the DC faults.
- Item 5 (R30) handles the power-down transient.
- Remaining gap: if the tap is shorted straight to +HV (for example, a probe slip), V2 still passes 13.7mA at 150V, and the 0402 R30 would dissipate about 1.9W and burn open.

The suggested fix was R30 = about 22k in 0805/1206 (6.2mA in that fault).
- Cost: about twice the offset from U8's input bias current (2.2mV typ, rising to about 4.5mV). This sim-stage note originally said the RV2 calibration trims it out. The current procedure treats it as a fixed drop at TP3 that does not scale with the rail, so RV1 is retrimmed at each rail setting (section 2.10 item 2, and BRINGUP-V2.md section 4.5 step 1).
- It changes the footprint, so the gerbers would need regenerating.
- Done: R30 is 22k. Sim 7 then showed that an 0805 would still dissipate 0.87-0.97W in this fault, so R30 is now a 2W 2512 (TE CRGP2512F22K; sections 2.7 and 2.10).

### 2.6 High-voltage safety audit and spacing fix (done 2026-09-23)

KiCad's DRC was not checking high-voltage spacing: the project had a single 0.2mm clearance for every net. A voltage-aware audit instead assigned each of the 54 nets its worst-case voltage at the ±150V design rails and measured every pair against IPC-2221B (bare pads A6, masked copper B4). The results:
- At ±50V (the current bench): 0 violations.
- At ±150V: 12 issues. 8 were fixed by copper edits, and the other 4 are fixed by the safety revision in section 2.7.
  - The +100V/GND spot went from 0.20mm to 0.66mm.
  - The GND pour now keeps 1.0mm from exposed HV pads (was 0.5mm).
  - Five traces were rerouted away from HV pads.
  - No parts moved, and no nets changed.
- New hvawg.kicad_dru rules file. KiCad's DRC now enforces voltage-domain clearances (HV vs LV, +HV vs -HV/output, output vs everything). The rules were tested and fire on the old board.
- Component stress audit: no part is over its rating in normal operation. The remaining physical concerns:
  - Q1 needs a heatsink above about ±125V (its tab is at the output voltage). This was the audit's first estimate. The current figures are about ±118V as the physical limit at 40°C ambient, and the bringup procedure requires Q1's bar above ±50V (section 2.8, BRINGUP-V2.md section 5).
  - Q3's tab sits at about -150V.
  - R21 dissipates up to 8.9W while the output clips at the negative rail.

### 2.7 Safety revision (approved 2026-09-23 by Lawrence, implemented and verified 2026-09-24)

Verification (figures from that stage; the current board's results are in section 2.8):
- DRC with the HV rules: 0 errors, 0 unconnected, and no remaining KNOWN_SHORTFALL exceptions (Q1/Q3/C32/TP12 are fixed at the source).
- Voltage-aware audit at ±150V: 0 violations and 0 edge failures. The tightest gap is 0.805mm against 0.8mm required, from the Q1 drain track to Q1 pin 1.
- Every pad matches the netlist, and every net change is intended.
- Gerbers regenerated. Every hole change was reconciled (PTH holes went from 132 to 146).

Where the build differs from the approved plan (needs confirmation):
- J9 is a 3.50mm pitch block (Phoenix MC 1,5/8-G-3,5), not 3.81mm. The 3.81mm body (31.9mm) doesn't fit between the J5 and J7 cable plugs (31.75mm gap). The 3.50mm part is the same family with the same rating and gives a 1.7mm gap between contacts, versus 2.0mm for 3.81mm and 0.84mm for the old header.
- The board outline grew. At first a 30.5 x 10.8mm tab on the top edge carried J9 (board 150 x 50.85mm, was 150 x 40mm). That is superseded and the tab is gone. The board is now a plain 207 x 58.8mm rectangle with J9 at the top edge between J5 and J7, in a 0.5mm edge notch (section 2.9). A mechanical check is still needed: computed from the Phoenix drawings, the J9 plug clears the J5/J7 cable plugs by about 1.9mm on each side, assuming 2.54mm pin housings centered on the pins. Verify this against the real cable plugs.
- Q1 tab warning: the front silkscreen has the short form "Q1 TAB=OUT +/-150V" (no room for the full text). The full "Q1 TAB = OUTPUT +/-150V - INSULATE" is on the back silkscreen.
- Parts moved to make room:
  - R24, R25, TP6, TP12, D3/R3, C26/C27 (+0.2mm).
  - J7/J8 now span x 182.68-197.92 (pins 1-4 unchanged; 5-7 added). J10 was deleted.
  - The old J9 header pads became vias.

The revision was approved because this is a very-high-voltage board and new boards will be stacked (connected by cables between the edge sockets).

WARNING: THE PINOUTS CHANGE, SO ALL V2 BENCH WIRING AND CABLES MUST FOLLOW THE NEW TABLE BELOW. V2 BOARDS DO NOT MATCH V1 WIRING.

Connector pinouts (option A: no two adjacent pins more than 150V apart):

| Connector                        | Old pinout                                                                       | New pinout                                                                                                                                                                 |
|----------------------------------|----------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| J5 / J6 (HV daisy-chain, 4 pins) | 1 GND, 2 +100V, 3 -100+12V, 4 -100V                                              | 1 +100V, 2 GND, 3 -100V, 4 -100+12V                                                                                                                                        |
| J7 / J8 (output bus)             | 1x04: OUT1 to OUT4 adjacent (up to 300V apart), plus J10 = GND                   | 1x07: 1 OUT1, 2 GND, 3 OUT2, 4 GND, 5 OUT3, 6 GND, 7 OUT4 (J10 removed; its GND is now in the bus)                                                                         |
| J9 (bench power input)           | 2.54mm header: 1 GND, 2 GND, 3 +12V, 4 -12V, 5 GND, 6 +100V, 7 -100+12V, 8 -100V | 3.50mm pluggable terminal block (option B; approved as 3.81mm, see above): 1 GND, 2 +12V, 3 -12V, 4 GND, 5 +100V, 6 GND, 7 -100V, 8 -100+12V. Pin 1 is the right-hand end. |

J3/J4 (±12V) are unchanged. The daisy-chain sockets stay in place; only the output-bus sockets get longer. The power-on order is unchanged.

Part and footprint changes:
- Q1 and Q3: HV variant of the TO-220 footprint with narrower pads. The gap between pads goes from 0.635mm to 0.99mm (1.55mm pads at 2.54mm pitch). The legs stay straight.
- R30: 10k 0402 changed to 22k. It was first an 0805, but Sim 7 showed the 0805 would overheat (0.87-0.97W) with the monitor tap shorted to +HV. It is now a 2W 2512, TE CRGP2512F22K (22k 1%, 500V, pulse-rated thick film; LCSC C2076055), which survives that fault at about half its rating.
- R31: 1206 changed to 2512 (1W), for output-fault robustness.
- C32 (DNP): 0603 changed to 1206 pads. If it's ever fitted, it must be rated at least 250V.
- TP12: moved in from the board edge.
- Silkscreen: HIGH VOLTAGE warnings near the HV connectors; "Q1 TAB=OUT +/-150V" at Q1 (front) and "Q1 TAB = OUTPUT +/-150V - INSULATE" (back); "TAB ~ -150V" at Q3. The full current silkscreen is listed in section 2.9.

Assembly and operation notes:
- Q1: its tab is the output (up to ±150V). Mount it alone on the right-edge bar with a Sil-Pad K-10 (rated at least 1kV) plus a Keystone 3049 nylon shoulder washer, and tie the bar to GND. Never leave the bar floating or at output potential. The bringup procedure requires the bar above ±50V (recommended at ±50V). Physically, Q1's centered dissipation needs it above about ±118V at 40°C ambient (section 2.8, BRINGUP-V2.md sections 3.6 and 5).
- R21: laid flat in its own GND-bonded heatsink, HS1 (section 2.8). There are no flying leads.
- Stacks at ±150V: plan for forced airflow, since each board dissipates 5-10W.
- Conformal coating is recommended for ±150V operation. Mask HS1 and its screws before coating.

### 2.8 R21 on the board, laid flat in its own heatsink (implemented and verified 2026-09-24)

The chassis-mount THS2510KJ on flying wires is replaced by an on-board Vishay LTO050F10001JTE3, a 10kohm TO-220 power resistor. It is the part on the BOM. The flat footprint is dimensioned for the LTO 50 only, so the earlier alternate (C&B/RESI TPAN0220F10K0K9) is dropped. Its ratings were checked against the datasheet (<https://www.vishay.com/docs/50050/lto50.pdf>):
- 500V working, versus 300V worst case across R21.
- 50W at 25°C case, 24W at 90°C, versus 8.9W worst case.
- Isolated ceramic back, 1500VRMS. Rth(j-c) 2.5°C/W; element maximum 150°C.

R21 first stood upright at the right edge (about 19.7mm tall) and shared Q1's heatsink bar. On 2026-09-24 it was laid flat (decision 7 in section 3).

- Mounting: R21 lies ceramic face down in the trough of a Wakefield 272-AB channel heatsink, reference HS1. This is the plain bolt-on version (Digi-Key 345-1043-ND), not 272-AB01/-02. HS1 is 44.45 x 36.83mm and 9.5mm tall, and it is bonded to GND. Sim 6 recommends grounding the metal that R21's element couples to (here the sink); tying it to +HV should behave the same. A floating sink would sit at an undefined potential next to ±150V copper, so HS1 must never be left floating.
- Placement: HS1's trough runs along x, left of Q1. The sink spans x 219.0-255.9, y 81.8-126.2. R21's hole is concentric with HS1 hole 1 at (232.5, 104.0); hole 2 is at (242.4, 104.0). R21's leads point left (-x) to two slotted pads at x 213.8:
  - pad 1 = output (Net-(Q1-D)), the upper pad at y 101.46
  - pad 2 = +100V, the lower pad at y 106.54
  - The pad gap is 2.48mm, against 0.8mm required at 300V.
- Board changes:
  - The right end is 57mm wider (section 2.9).
  - Q1 and its drive block (U7, D4, R15, R18, R22, R23, R28, C24, C25, TP9-TP12) moved 57.5mm right as a unit, so the gate/source loop is unchanged.
  - A masked F.Cu GND plate lies under the sink floor, stitched to the B.Cu GND pour by 12 tented holes. The footprint keeps all tracks and vias out from under the floor.
  - The long output run (Net-(Q1-D), F.Cu, 0.5mm) goes from R21's pad-1 junction up to y 88 and along it to Q1's drain via at (281.3, 96.3). It passes under HS1's upper fins, about 8mm from the floor plate. The B.Cu GND pour stays out of y 80-96.5 along it, to keep the output-node capacitance down (see "Output-node capacitance" below).
  - New footprints: Library:TO-220-2_Horizontal_LTO50 (R21) and Library:Heatsink_Wakefield_272-AB (HS1). HS1's schematic symbol is Mechanical:Heatsink_Pad_2Pin, with both pins on GND, and it is in the BOM.
- Lead forming: the LTO 50 datasheet offers no bend option, so the bend is borrowed from Vishay's LTO 100 option TB8. Its leads have the same 3.5mm shoulder and 0.6mm thickness:
  - straight for 4.2mm from the body
  - inner radius 1.2mm
  - 90° toward the ceramic side
  - outer lead face 6.0 ±0.5mm from the body
  - Form the leads in a jig, clamping each lead between the body and the bend.
- Slots: the plated slots are 1.5 x 3.0mm. They were lengthened from 1.5 x 2.8mm on 2026-09-24, because JLCPCB requires a plated slot to be at least twice as long as it is wide. The 2.6 x 4.2mm oval pads are unchanged, leaving 0.6mm of copper at the slot ends.
  - The slots let the 0.8 x 0.6mm lead move about ±1.1mm along the lead (±1.08mm nominal, about ±1.04mm at JLC's -0.08mm slot tolerance) and ±0.35mm across.
  - That travel covers the ±0.5mm bend check together with R21's own body tolerance (hole to the lead end of the body 13.0mm, from 16.2mm and 3.2mm, each ±0.3mm) and about 0.075mm of drill position: about ±0.66mm combined (RSS), about ±1.2mm worst case.
  - The worst case is covered by the M3 screw's clearance in R21's and the PCB's 3.2mm holes (about ±0.14mm each), which lets R21 shift slightly to suit its leads.
  - The slots meet JLC's rule exactly (the drill file gives 1.5011 x 3.0023mm, a ratio of 2.00). If JLC's DFM review still flags them, 1.5 x 3.1mm gives margin and leaves 0.55mm of copper at the slot ends.
- Hardware per board:
  - Hole 1 (through R21, the sink and the PCB): an M3x12 pan-head screw with a DIN 125 flat washer on R21's molded face.
  - Hole 2 (sink only): an M3x8 pan-head screw with a DIN 6797-J internal-tooth lock washer on the sink base. The teeth bite through the anodizing, and that is what bonds the sink to GND.
  - Under the board: a DIN 127 split washer and an M3 nut on each B.Cu GND ring. The nuts and screw tails stick out about 5-6mm below the board.
  - Non-silicone thermal compound (Wakefield 126) between R21's ceramic and the sink floor. No insulator is needed, because the ceramic back is isolated.
- Assembly order:
  1. Form the leads.
  2. Grease the ceramic and place R21.
  3. Screw down both holes at about 0.5-0.6Nm (estimate). The datasheet's mounting torque is about 1Nm (recommended, not a stated maximum). Use the lower figure because the FR4 is in the clamp stack.
  4. Solder last.
- Thermal envelope: these are estimates at 40°C ambient in open air, from the Wakefield catalog curve. A closed stack is worse.
  - No fan: every case up to about ±100V is fine, including sustained clipping (R21 about 3.9W). At ±150V without a fan, allow only centered sine and near-0V outputs (R21 element about 87°C, sink about 75°C), and keep any sustained DC output above about -50V. That keeps R21 at or below about 4W, the same as the accepted ±100V clipped case. In general the no-fan DC limit is +HV - 200V.
  - A DC output held lower at ±150V (R21 takes 8.4W at -140V, 8.9W clipped at the rail) needs at least 1m/s of airflow across HS1's fins. With 1m/s (about 200LFM, sink-to-air resistance about 5°C/W from the 272-AB curve) the sink stays at about 82-85°C and the R21 element at about 111-116°C at 8.4-9W, against the 150°C element limit. Without airflow the sink reaches about 107-113°C and the R21 element about 136-144°C (about 141-144°C at 9W; the catalog's table point runs about 5% hotter than its curve).
  - Headroom from the rail only prevents clipping; it does not reduce heating. An output kept 10V off the negative-rail clip (-140V) still puts 8.4W into R21. The driver's V_MAX is a clip-avoidance limit; the no-fan limit is a host-side DC limit near -50V (BRINGUP-V2.md section 4.5 step 6, and section 5).
  - The silkscreen marks the sink "HOT >100C" and "SINK = GND".
  - C24 (10uF 1206 on the floating 12V) sits about 7mm from the sink outline. The May JLC BOM part for the 10uF 1206 caps (C13585, CL31A106KBHNNNE; Samsung's "A" code is X5R) is rated to 85°C. The PCB next to a 107-113°C sink (no-fan near-rail case) can exceed that, so C24 is now an X7R (125°C) part: Samsung CL31B106KAHNNNE, 10uF ±10% 25V X7R (-55 to +125°C) 1206, LCSC C14860 (JLC extended part; JLC has no basic or preferred X7R 10uF 1206). 25V is twice the 12V floating rail. Like the X5R part it replaces, it gives less than 10uF at 12V bias, which is fine for this bulk decoupling. The schematic's C24 now carries the MPN and a Note with the LCSC number. Check its temperature during the section 5 soak in BRINGUP-V2.md.
- Q1 is now alone on the right-edge bar. The bar carries only Q1, at most 2.23W (centered output at ±150V; Sim 7), so it only needs to span board y 99-111 or so.
  - A bar of at most 10°C/W is recommended. With the IRF730's Rth(j-c) of 1.7°C/W plus about 0.5°C/W for the Sil-Pad, that puts Tj at about ambient + 27°C.
  - Up to 30°C/W still keeps Tj at or below 125°C at 40°C ambient.
  - This replaces the old spec of at most 3.5°C/W, which covered R21 plus Q1.
  - Q1 still needs a Sil-Pad K-10 plus a Keystone 3049 nylon shoulder washer, because its tab is live. Tie the bar to GND.
  - Bar height: the bar stands on the board's right edge, so it must not be taller than the clear space to the next board in a stack (the standoff length, at least 22mm; section 4), and it must not hang below the board, or it hits the neighboring board's bar. Its height is therefore limited by the spacing chosen for the stack.
  - Edge pull-in: the right board edge (x 283.0) sits 0.405mm inside the tab face of Q1's footprint model (F.Fab line at x 283.405), so a flat bar should touch the tab, not the PCB edge. At JLC's ±0.2mm routing tolerance about 0.2mm is left. Q1's pads stay 1.5mm from the edge.
  - Real parts vary. The footprint puts the tab back 3.15mm from the lead centerline, near the top of the Vishay TO-220 range (2.59-3.23mm, nominal about 2.9mm). A real IRF730's tab can therefore sit anywhere from about 0.16mm behind the edge to about 0.48mm proud, before routing tolerance. Measure Q1's lead-to-tab-back distance with calipers (the drawings are ±0.3mm). Clamp Q1 and its Sil-Pad to the bar before soldering Q1's leads. The play of the leads in their 1.1mm holes (about 0.1mm for a nominal lead, at most about 0.25mm; a rectangular lead is stopped by its corners) then lets the tab seat flat on the bar. Check with calipers on the first board that the bar touches the tab, not the PCB edge.
- Checks on the final board (custom HV rules loaded, zones refilled):
  - DRC: 0 errors, 0 unconnected, 0 silkscreen overlaps, 0 silkscreen over copper, and no exclusions. The warnings are 32 library-version mismatches, 4 silkscreen-past-edge items (Q1's outline at the heatsink edge, intentional) and 28 exclude-from-BOM parity items.
  - Voltage-aware audit at ±150V, including the board edge: 1273 pairs, 0 violations.
  - Every track bend is at least 135°.
  - ERC is unchanged.
  - The GND pour and floor plate stay at least 2.36mm from R21's pads, at least 3.1mm from the output copper added for the flat R21, and at least 4.0mm from the long output run.
  - The gerbers and production zip in jlcpcb/ were regenerated from this board and checked (section 4).
  - All of these checks were re-run after the last changes (R21's slots lengthened to 1.5 x 3.0mm; MPN and Note fields added to C24 and J9) with identical results, item for item. The netlist is unchanged node for node.
- Output-node capacitance (re-routed 2026-09-24): the output node now has 115.3mm of track (44.9mm before the flat R21).
  - The first flat layout ran the long output track 1mm wide at y 92.5, 3mm from the floor plate and the B.Cu pour. A separate check put its added copper at about 3.1pF. Together with R21's grounded case capacitance (about 3pF), that came out at +10.1% TP5 rise time at a 30pF load, just over Sim 6's 10% budget. (An earlier "+3% edge time" figure was wrong: it compared lumped copper with Sim 6's distributed case capacitance.)
  - The long run is now 0.5mm wide at y 88, with the B.Cu pour pulled back to y 80. By a 2-D field solve (the separate check's method, applied to every output-node segment), the node carries about 1.9pF more than the pre-flat board. The same method gives 2.8pF for the first flat layout.
  - The Sim 6 generator with R21's 3pF case grounded, plus the added copper lumped at TP5, gives these worst-edge changes against ideal:

    | Added copper                                 | 30pF load | 10pF load |
    |----------------------------------------------|-----------|-----------|
    | 1.9pF (field solve)                          | +5.7%     | +4.5%     |
    | 2.2pF (plus the check's 0.3pF method offset) | +6.5%     | +5.0%     |
    | 2.5pF (margin)                               | +7.8%     | +5.5%     |

    Sim 6's 10% budget is applied here to what the R21 change adds: R21's case plus the copper added over the pre-flat board, +5.7% worst at a 30pF load (first row). It does not count the output-node copper the board already had. Counting all of the output-node copper (about 4.2pF) plus R21's case against an ideal resistor, the rise at a 30pF load is about 13% slower (about 7% for the pre-flat board on the same basis).
  - R21's element-to-sink capacitance (about 3pF) is an estimate, the same as it was on the old grounded bar. Measure it on an LCR meter (section 4). With the 1.9pF of added copper, the 10% limit at a 30pF load is reached at about 6.5-7pF (5pF gives about +8%, 8pF about +11.5%). The Q1 tab on its grounded bar adds more (Sim 7 item 5). Measure the edges on the first board (section 4).
- Stack height (the stack spacing is a requirement for whoever builds the stack, not a board constraint; section 4):
  - At least 22mm clear between boards (about 23.5mm top-to-top), because the upright Q1 and Q3 stand up to 19.9mm, plus a 2mm margin. That was already true before this change.
  - HS1 (9.5mm) and R21 with its screw head (7.2mm) are well inside that. HS1's nuts and screw tails stick out about 5.7-6.0mm below the board, so the bottom board of a stack needs feet of at least 8mm.
  - Every THT lead must be trimmed to at most 2.5mm below the board.
- To verify on real parts:
  - the lead bend (6.0 ±0.5mm) with calipers
  - HS1 fin to GND under 1ohm
  - R21's element-to-back capacitance on an LCR meter, with both leads shorted to each other and measured to the sink or the ceramic back. No vendor publishes it. Sim 6 alone allows about 10-15pF, but with the added output copper the limit is about 6.5-7pF (see above).

### 2.9 Re-layout, J9 edge notch, silkscreen and U4B/U8B tie-offs (2026-09-24)

- Outline: a plain rectangle with 5mm corner radii and no tab, x 76.0-283.0, y 68.2-127.0, so 207.0 x 58.8mm.
  - The re-layout first made it 150 x 58.8mm: the top of the old J9 tab became the whole top edge, and the bottom edge moved down 8mm.
  - The flat R21 then widened the right end by 57mm.
- J9 edge notch: the top edge steps back 0.5mm (to y 68.70) over x 150.20-180.84, behind J9.
  - Why: Phoenix's mating drawing has the PCB edge flush with the header face. Right at that face the MC-ST plug's lower body already reaches below the board's underside (about 2.2mm below the PCB top, and about 3.4mm a little further out).
  - Without the notch, the board stuck out 0.30mm in front of the header face (y 68.50) and stopped the plug about 0.3mm short of seating.
  - With the notch, the edge is 0.20mm behind the header face. It stays at or behind the face even at JLC's ±0.2mm routing tolerance. The notch runs about 0.6mm past each end of the header body, and the 1mm +HV track behind J9 stays 0.70mm from the notched edge (the HV track-to-edge rule is 0.6mm).
- J9 plug: Phoenix MC 1,5/8-ST-3,5, order no. 1840421 (Mouser 651-1840421, Digi-Key 277-5715-ND, LCSC C3579977). It mates with the 1844278 header.
  - Wire it off the board with 600V-rated hookup wire (e.g. UL1015). Pin 7 carries two leads (-HV supply and floating 12V supply), crimped into one twin ferrule (e.g. Phoenix AI-TWIN 2x0,5-8 WH).
  - Never plug or unplug it live (Phoenix: not to be plugged or unplugged under voltage). It is held by friction only (about 32N).
  - Rating: the header sets it, 250V for overvoltage category II / pollution degree 2 (a lab bench). At ±150V rails no two neighboring pins are more than 150V apart, which is also within the 160V that LCSC lists for the plug. +HV (pin 5) and -HV (pin 7) are separated by the grounded pin 6.
  - WARNING: DO NOT EXCEED ±150V RAILS.
  - Wiring table and harness check: BRINGUP-V2.md section 1.5.
  - The schematic's J9 now carries the MPN (1844278) and a Note naming the mating plug 1840421 (bought separately), so a BOM generated from the schematic lists the header part number. J9's board footprint is excluded from the board BOM (one of the 28 parity items), so a board-based plugin BOM may leave J9 out. That is harmless, since J9 is hand-fitted.
- Mounting holes: H1 (81.0, 73.2), H2 (81.0, 122.0), H3 (278.0, 73.2) and H4 (278.0, 122.0).
  - They are M3, 5mm from both edges, in a 197.0 x 48.8mm pattern.
  - V1 used 140 x 30mm, so V2 boards no longer share standoff positions with V1.
  - They are not connected to GND.
- Connectors: J1/J3/J5/J7 sit on the top edge and J2/J4/J6/J8 on the bottom edge. Their x positions are unchanged, so each mating pair (J1/J2, J3/J4, J5/J6, J7/J8) still lines up. J9 sits between J5 and J7 on the top edge.
- Routing: the functional blocks were spread out for HV separation. Every track was re-made with 45° geometry: every bend is at least 135°, and branches join as 45° Y-junctions.
- Silkscreen (all text at least 1.0mm tall with at least a 0.16mm stroke):
  - "HV_AWG v2" (was "v1") at the top left, beside J1.
  - J9: pin numbers 1-8 with the net name under each pin. Pin 1 is the right-hand end: 1 GND, 2 +12V, 3 -12V, 4 GND, 5 Vhi, 6 GND, 7 Vlo, 8 Vlo+12.
  - Pin-name labels at every daisy-chain socket (new at J3-J6):
    - J1/J2: "GND ser_in/ser_out ser_clk store"
    - J3/J4: "GND GND +12V -12V"
    - J5/J6: "Vhi GND Vlo Vlo+12"
    - J7/J8: "1 G 2 G 3 G 4"
  - "HIGH VOLTAGE" beside J5, J6, J7, J8 and J9.
  - HS1: "HS1 / SINK = GND / HOT >100C" above the sink, and "SINK = GND" inside its outline, where it is visible before assembly. "HV" between R21's pads and the sink.
  - "Q1 TAB=OUT +/-150V" above Q1 (front), "Q1 TAB = OUTPUT +/-150V - INSULATE" on the back, and "TAB ~ -150V" at Q3.
  - "DC adjust" and "gain adjust" are now horizontal. "DC adjust" sits between RV2 (upper) and RV1 (lower), and "gain adjust" is below RV1.
- U4B/U8B tie-offs: the unused halves of both NE5532s are now grounded followers (pin 5, +IN, to GND; pin 7, OUT, tied to pin 6, -IN) instead of floating inputs. They are not in any signal path.
- R30 is now the 2512 at (162.2, 89.9), between RV2 and U8. C14 moved to (153.0, 88.5).

### 2.10 Sims 6 and 7 (2026-09-24)

Both are in simulations/v2/. Neither uses the cshunt option: it adds 1pF to every node, including the inside of the LM8261 macro-model, and it produced false limit cycles.

- Sim 6, R21 parasitics (sim6_README.md, sim6_results.json; 61 cases at ±150V):
  - No oscillation in any case: L from 0 to 5mH, element-to-housing capacitance from 0 to 100pF, housing grounded or floating.
  - With the housing grounded, element-to-housing capacitance up to about 15pF (10pF load) or 10pF (30pF load) keeps rise and fall within 10% of ideal.
  - Series inductance does not matter below about 0.5mH.
  - Ground the housing. Tying it to +HV should behave the same (by inspection, not simulated). A floating housing cuts the edge penalty about 4x, but it leaves metal at an undefined potential next to ±150V, so it is not recommended. HS1 is on GND.
- Sim 7, coverage audit (sim7_README.md, sim7_results.json; 196 cases): every final value in the signal and HV path is simulated and passes, at ±150V and ±50V.
  - sim7_README.md is up to date with the follow-ups below: R30 is the 22k 2512; the R30 bias drop lowers TP3; Sim 5's offsets are paired with the ±50V to ±120V change it covered; the realistic-Crss phase margin is about 20-47°, not the 50-59° once called pessimistic; and 38 cases, not 34, needed a second .op route.
  - The realistic-Crss re-check in item 4 is not in the repo (its Crss values were assumed, not read off the IRF730 curve).

Sim 7 findings:

1. R30 with the monitor tap shorted to +HV: U8 is protected (6.3-6.6mA), but R30 dissipates 0.87-0.97W. An 0805 would overheat in a sustained short and fail open (safe for U8), so R30 is now the 2W 2512.
2. Trim RV1 at the rail you will run. U8's input bias current flows through R30 and lowers TP3 by a fixed amount that does not scale with the rail: about 5mV with a typical NE5532 (0.2uA x 22k), 11-18mV with the Sim 7 model and at maximum bias. Trimmed at ±50V and run at ±150V, the output sits at -2.9 to -4.4V (-5.2V with a maximum-bias NE5532). For the pairing Sim 5 covered (±50V to ±120V), Sim 7 gives -2.0 to -3.1V against Sim 5's -0.5 to -1.5V (no R30), about 1.5V worse. The NE5532 model biases above the datasheet typical, so typical parts show somewhat less.
3. RV2 works only between about 0.2 and 0.5kohm. At either end of RV2 no RV1 setting can center the output. The bringup preset (0.29kohm) is inside the window.
4. Stability: stable with every load from 10pF to 1nF. A re-check with a realistic high-voltage IRF730 Crss gives less phase margin, about 20-47°. That is still stable, but a step can overshoot on the Q1 source current and ring at 2-3MHz for about 2us. On the bench, probe TP10 (Q1 source) and TP9 (gate) as well as TP5.
5. Q1 tab capacitance: Q1's tab on the grounded bar, through a Sil-Pad, adds roughly 20-40pF at TP5 (estimate). It was not simulated together with R21's case capacitance. Sim 6's grounded cases cover that size for stability, but it does slow the edges.

## 3. Decisions (resolved 2026-09-24 by Lawrence unless noted)

| #   | Question                                            | Decision                                                                                                                                                                                                                                        |
|-----|-----------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 1   | R29: 100k to 1Mohm?                                 | Yes, 1Mohm (done). Restores rail-independent centering and cuts level-shifter distortion (Sims 1, 3, 5). BOM value only.                                                                                                                        |
| 2   | R30: 10k 0402 to something larger?                  | Done: 22k. First 0805 (safety revision), now a 2W 2512, TE CRGP2512F22K (LCSC C2076055), after Sim 7's tap-short finding (section 2.10).                                                                                                        |
| 3   | Gate-resistor footprint for Q1 (for a BSS126 swap)? | No. The BSS126 is rejected: its SOT-23 package (about 0.36W) can't take the roughly 2.2W in Q1 at ±150V, and it is depletion-mode, so this circuit can't turn it off. Q1 stays the IRF730.                                                      |
| 4   | Test load R32/C32 at TP5 or TP6?                    | Keep at TP5. It is the only on-board way to load the amplifier stage directly during bringup. The TP6 side can be loaded externally through the output connectors.                                                                              |
| 5   | TP9-TP12 placement?                                 | Switched to SMD test pads (done): TP9 Q1 gate 5.8mm, TP10 Q1 source 4.5mm, TP11 U7 V+ 1.5mm, TP12 U7 V- 5.1mm (pad edge to pin, final board). They are bare copper pads, so they are excluded from the BOM in both the schematic and the board. |
| 6   | J9 at 3.50mm pitch instead of 3.81mm?               | Yes, 3.50mm (header Phoenix 1844278). Same family and rating; 3.81mm doesn't fit. The mating plug is the Phoenix MC 1,5/8-ST-3,5, order no. 1840421.                                                                                            |
| 7   | R21: how to mount the LTO 50?                       | Lay it flat (2026-09-24), and keep the LTO050F10001JTE3 that is on the BOM. Ceramic face down in a Wakefield 272-AB bonded to GND (section 2.8).                                                                                                |

## 4. Remaining work before ordering

- [x] Gerbers and production zip regenerated from the final board (2026-09-24) and checked.
  - Edge.Cuts is x 76-283, y 68.2-127 (207 x 58.8mm), with the J9 notch.
  - Drill hits went from 139 to 156, and every change is accounted for. HS1 adds two 3.2mm holes and 12 x 0.3mm stitching holes. R21's two round holes became two plated slots, now 1.5 x 3.0mm. Vias went from 49 to 52.
  - The zip holds the same 14 files as jlcpcb/gerber/.
  - Regenerated again after the output-run re-route (section 2.8). Only the two copper layers changed. The drill files (156 hits), masks, silkscreen, paste and Edge.Cuts are identical apart from their dates.
  - Regenerated again after R21's plated slots were lengthened from 1.5 x 2.8mm to 1.5 x 3.0mm (JLCPCB's capabilities page: a plated slot must be at least twice as long as it is wide). Only the PTH drill file (the two slot lines) and its drill map changed. All 156 holes reconcile one to one with the board, and the copper, mask, silkscreen, paste and Edge.Cuts layers are identical apart from their dates.
  - Regenerate them again after any further board change.
- [ ] Regenerate the JLC BOM/CPL with the kicad-jlcpcb-tools plugin (manual step).
  - The CSVs in jlcpcb/production_files/ date from May 2026 and do not include the V2 parts.
  - Assign LCSC part numbers for the new assembled parts (D4, D5, R26-R31). R30 = C2076055.
  - C24 changes part: use the X7R 125°C Samsung CL31B106KAHNNNE, LCSC C14860 (section 2.8), not the X5R C13585 that the May BOM assigns to it. The other 10uF 1206 caps stay C13585.
  - The schematic's C24 and J9 now carry MPN and Note fields (C24: the LCSC number; J9: header 1844278, plug 1840421 bought separately).
  - J9 is hand-fitted, like HS1. HS1 is in the KiCad BOM (it is a part to buy) but it is fitted by hand, so give it no LCSC number or exclude it in the plugin.
- [x] Silkscreen cleanup: done (0 overlaps, 0 labels over copper).
- [x] The 5 connector courtyard DRC errors: fixed (section 1b).
- [x] HV spacing: fixed (sections 2.6 and 2.7). The voltage-aware audit is at 0 violations at ±150V, and the HV rules are enforced in DRC.
- [ ] Mechanical check of J9 with the real plug and the real J5/J7 cable plugs. The computed side clearance is about 1.9mm. (J9 at 3.50mm is decided, and the tab is gone.)
- Stack spacing: a requirement for building a stack, not a board constraint. The spacing is set by the standoffs and can be chosen later. Requirements:
  - At least 22mm clear between boards (about 23.5mm top-to-top), for example 25mm M3 standoffs, because the upright Q1 and Q3 stand up to 19.9mm (Vishay TO-220 drawing maximum) and need a 2mm margin. This assumes Q1 is held to its bar by a clip; a screw through Q1's tab needs roughly 25-27mm top-to-top. This was already true before the R21 change (the old 20mm pitch left only 18.4mm).
  - Every THT lead trimmed to at most 2.5mm below the board. Untrimmed Q1/Q3 leads reach about 8mm down, up to 9.5mm. At 23.5mm top-to-top they come within 1mm of the Q1/Q3 bodies on the board below with nominal parts, and touch them with maximum-tolerance parts.
  - Feet of at least 8mm under the bottom board, because HS1's nuts and screw tails stick out about 5.7-6mm.
  - The Q1 bar no taller than the clear space between boards (and not hanging below its board), so its height is limited by the spacing chosen.
- [ ] Airflow at ±150V. Without a fan, allow only centered sine or near-0V outputs at ±150V and keep any sustained DC output above about -50V (R21 at or below about 4W, the same as the accepted ±100V clipped case; section 2.8). Anything lower, including an output held near the negative rail, needs at least 1m/s across every HS1. Headroom from the rail only prevents clipping; it does not reduce heating, so a 10V clamp from the rail is not a substitute for the fan.
- [x] R21's Note field (schematic and board) now states the full rule: at least 1m/s across HS1 for any sustained DC output below about -50V at ±150V (in general below +HV - 200V), and no fan for sine or near-0V outputs. Done 2026-09-24. It is text only. Re-checked after the edit: DRC with rules gives 0 errors, 0 unconnected and the same warnings item for item; ERC and the netlist are identical; regenerated gerbers are identical to the installed set apart from dates.
- [ ] First-board checks for the flat R21:
  - HS1 fin to GND under 1ohm.
  - R21's element-to-back capacitance on an LCR meter. The 3pF used so far is an estimate; with the added output copper the 10% edge limit at a 30pF load is about 6.5-7pF.
  - Thermocouple the sink and the R21 top with the output clipped at ±50V (about 1W), to calibrate the thermal estimates.
  - Measure the TP5 and TP6 10-90% edges for a -100V to +100V output step and compare them with Sim 6's ideal (1.25 / 1.39us rise / fall at a 10pF load; 1.50 / 1.90us at 30pF). The 10% budget was applied to what the R21 change adds (+5.7% worst at 30pF; section 2.8). Against an ideal resistor, all of the output-node copper (about 4.2pF) plus R21's case slows the edges by about 5% (rise) to 8% (fall) at 10pF, and by up to about 13% (rise) at 30pF. The pre-flat board's figure was about 7% at 30pF. The Q1 bar adds more (Sim 7 item 5).
  - Probe TP10 and TP9 for ringing after a step (BRINGUP-V2.md section 4.4 step 14). Q1's -HV return from R22 to the bulk capacitor C27 grew from about 14mm to about 73mm, and the output node now runs about 70mm further to Q1's drain. The extra 60-70nH is about 1ohm at 2-3MHz, small next to R22 (75ohm) and R21 (10k), so it is judged minor, but those are the nodes where it would show.
- [x] Hand-solder BOM (README) updated for V2: J9 header 1844278 and plug 1840421, HS1 272-AB and its hardware, R21 laid flat, R30 2512, 1k trimpots. J7/J8 take 7-position sockets and J10 is gone. The V2 cable pinouts are in section 2.7 and BRINGUP-V2.md section 6.
- [x] Pre-existing HV spacing issue (previously listed, now fixed; the coordinates are from the board before the re-layout). At (154.75, 82.32), a +100V trace was only 0.20mm from a GND trace. That is 100-150V across 0.2mm, below the IPC-2221 guideline (at least 0.4mm with solder mask), and it was inherited from the original layout. The other sub-0.5mm spots the spacing check reported are between nets within a few volts of each other near the -HV rail (U7/D4/R17 area), which is fine.
- [x] Check the new via at (214.94, 105.30), which sat against U7 pin 4 (possible solder wicking). Resolved: the re-layout removed it, and no via touches a U7 pad on the final board.
- [x] Update the README's hand-solder BOM (it listed 4.7k trimpots; V2 uses 1k): done.

## 5. Notes for the boards we already have (V1)

Bench trim procedure, corrected by Sim 1:
1. Set RV2's bottom leg to about 1.1kohm, so TP3 is about 0.5V at ±50V.
2. Start RV1 at its maximum. The output idles near +11V, which is safe.
3. With the DAC held at midscale, turn RV1 down until TP5 reads 0V. That lands around 3.65kohm (rule of thumb: RV1 is about 7.3kohm x V_TP3).

Do not preset RV1 to 1kohm. That pins the output at the negative rail with about 1W in R21.

Other notes:
- At ±50V rails, keep the DAC within about ±0.5V (about 35% of full scale). The output is 100 x V_DAC.
- The output FET fitted per the README BOM is the IRF730. The schematic's pot values (3k/1k) were stale; the physical pots are 4.7k.

## Files

- BRINGUP-V2.md: staged bringup for V2 boards, updated with the corrected presets.
- BRINGUP-V1-BOARDS.md: bringup notes for the V1 boards (fabbed before the V2 revision).
- simulations/v2/:
  - Sim 1: v2_dc_levelshift_output.cir
  - Sim 2: sim2_classA_*
  - Sim 3: sim3_levelshift*
  - Sim 4: sim4_monitor_*
  - Sim 5: sim5_*
  - Sim 6 (R21 parasitics): sim6_README.md, sim6_results.json, sim6_*
  - Sim 7 (coverage audit): sim7_README.md, sim7_results.json, sim7_*
