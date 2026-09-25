* HVAWG SIM 7 -- level-shifter subcircuit (U6 + Q3 driving TP4), FINAL V2 values.
* Copy of sim3_levelshift_common.inc with: R29 = parameter (final 1 Meg; Sim 3 used 100k except
*   the _isolate run), D5 always fitted, TP3 = HV * 1110/111110 (RV2 nominal, R_bottom = 1.11k),
*   R_RV1_total = parameter RRV (R26 3.3k + RV1 rheostat; 3.6k = centring value), Q3 Vto param.
* Included by sim7_ls_*.cir.  Do not run on its own.
.include ../LM8261.MOD
.model IRF9610_APPROX VDMOS(pchan Vto={VTQ3} Kp=0.6 Lambda=0.003 Rd=2.2 Rs=0.5 Rb=0.5 Cgdmax=120p Cgdmin=8p Cgs=155p Cjo=60p Is=1e-12 ksubthres=0.1 mfg=approximation Vds=-200 Ron=3 Qg=11n)
.model DZ12 D(Is=1e-14 Rs=5 BV=12 Ibv=5m Cjo={Cz} M=0.4 Vj=0.75)

* Ports as LS3 in sim3_levelshift_common.inc
.subckt LS7 dacin tp4 tp4r s fb g iq3 id5 irv ir29 vgs params: hvp=150 r29v=1Meg rrv=3.6k
Vhn  hvn0 0 {-hvp}
Rhn  hvn0 hvn 1
Vp12 vp12a 0 12
Rp12 vp12a vp12 1
Vm12 vm12a 0 -12
Rm12 vm12a vm12 1
Vtp3 tp3i 0 {hvp*1110/111110}
Rtp3 tp3i tp3 1
Rrv1 tp3 srv {rrv}
Virv srv s 0
R11  dacin dac 2.7k
XU6  dac fb vp12 vm12 g LM8261
MQ3  dq3 g s IRF9610_APPROX
Viq3 dq3 tp4 0
R17  tp4 hvn 2.7k
Ctp4 tp4 hvn 5p
R29  s n29 {r29v}
V29  n29 g 0
D5   g n5 DZ12
Rz5  n5 d5m 1
Vd5  d5m s 0
Biq3  iq3  0 V=I(Viq3)
Bid5  id5  0 V=-I(Vd5)
Birv  irv  0 V=I(Virv)
Bir29 ir29 0 V=I(V29)
Btp4r tp4r 0 V=V(tp4)-V(hvn)
Bvgs  vgs  0 V=V(g)-V(s)
.ends LS7
