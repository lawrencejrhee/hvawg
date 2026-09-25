* HVAWG SIM 3 -- shared models + level-shifter subcircuit (U6 + Q3 driving TP4)
* Included by sim3_levelshift*.cir.  Do not run on its own.
*
* MODELS / ASSUMPTIONS
*   U6  : LM8261 vendor macro-model ../LM8261.MOD (+IN -IN VCC VEE OUT), included unmodified, +/-12 V.
*   Q3  : IRF9610 is NOT in the LTspice 24.1.7 library -> VDMOS APPROXIMATION from the datasheet
*         (-200 V, Vth -2..-4 V -> Vto=-3, Rds(on) ~3 ohm, Ciss ~170p, Crss 8..120p).
*         Same card as Sim 1 (v2_dc_levelshift_output.cir) so the two sims agree.
*   D5  : BZT52C12 datasheet-typical: DZ12, Cjo={Cz} (45p nominal / 100p worst case), stepped.
*   TP3 : U8 output (monitor_out) = ideal source V_HV*1.11k/111.11k with 1 ohm output R.
*         (U8 itself, R30, C14/C15 are outside this sim.)
*   RV1 : R_RV1_total (R26 + RV1 rheostat) = 3.6k, the ideal-op-amp centering value at R_bottom=1.11k.
*   DAC : Thevenin source V_DAC through R11 = 2.7k (same as Sim 1) into U6 +IN.
*   TP4 : R17 = 2.7k to -HV, R19 absent (DNP), 5 pF node capacitance (U7 +IN + JP4 + trace + TP).
*   V1 board: no R29, no D5 (modelled as 1G so the netlist is identical).
*   V2 board: R29 = 100k gate-source, D5 cathode = Q3 source, anode = Q3 gate.

.include ../LM8261.MOD
.model IRF9610_APPROX VDMOS(pchan Vto=-3.0 Kp=0.6 Lambda=0.003 Rd=2.2 Rs=0.5 Rb=0.5 Cgdmax=120p Cgdmin=8p Cgs=155p Cjo=60p Is=1e-12 ksubthres=0.1 mfg=approximation Vds=-200 Ron=3 Qg=11n)
.model DZ12 D(Is=1e-14 Rs=5 BV=12 Ibv=5m Cjo={Cz} M=0.4 Vj=0.75)

* Ports: dacin = ideal DAC voltage (before R11); s = Q3 source; fb = U6 -IN (tie to s
*   externally through a 0 V source, or through an AC injection source for loop gain);
*   probes (1 V = 1 A): iq3 = Q3 drain current (source->drain, >0 = conducting),
*   id5 = D5 current (>0 = zener BREAKDOWN, <0 = forward), irv = current TP3 -> S through RV1,
*   ir29 = current S -> gate through R29; tp4r = V(TP4) - V(-HV); vgs = V(gate) - V(source).
.subckt LS3 dacin tp4 tp4r s fb g iq3 id5 irv ir29 vgs params: hvp=50 v2p=1
Vhn  hvn0 0 {-hvp}
Rhn  hvn0 hvn 1
Vp12 vp12 0 12
Vm12 vm12 0 -12
Vtp3 tp3i 0 {hvp*1110/111110}
Rtp3 tp3i tp3 1
Rrv1 tp3 srv 3.6k
Virv srv s 0
R11  dacin dac 2.7k
XU6  dac fb vp12 vm12 g LM8261
MQ3  dq3 g s IRF9610_APPROX
Viq3 dq3 tp4 0
R17  tp4 hvn 2.7k
Ctp4 tp4 hvn 5p
R29  s n29 {if(v2p,100k,1G)}
V29  n29 g 0
D5   g n5 DZ12
Rz5  n5 d5m {if(v2p,1,1G)}
Vd5  d5m s 0
Biq3  iq3  0 V=I(Viq3)
Bid5  id5  0 V=-I(Vd5)
Birv  irv  0 V=I(Virv)
Bir29 ir29 0 V=I(V29)
Btp4r tp4r 0 V=V(tp4)-V(hvn)
Bvgs  vgs  0 V=V(g)-V(s)
.ends LS3
