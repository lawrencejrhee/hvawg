"""SIM 6 -- effect of R21's parasitics (series L, element-to-housing C, self-C) on the
V2 class-A output stage at +/-150 V.

Generates one netlist per (case, analysis) as sim6_<case>_{tran,loop}.cir, runs each as its
own LTspice -b process (hard timeout + CPU-idle hang watchdog, kills only its own PID tree),
measures from the .raw with numpy (raw deleted afterwards) and cross-checks against the
.meas values in the .log.  Results -> sim6_results.json, progress -> sim6_progress.txt.

usage:  python sim6_run.py [all|validate|baseline|<case-name> ...] [--jobs N] [--keep-raw]
"""
import os, re, sys, json, time, math, subprocess, itertools
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import psutil

OUT = os.path.dirname(os.path.abspath(__file__))
LT = r"C:\Users\lawre\AppData\Local\Programs\ADI\LTspice\LTspice.exe"
MOD = "C:/Users/lawre/OneDrive/Desktop/pister_project/hvawg/simulations/LM8261.MOD"
TIMEOUT = 240          # s, hard limit per netlist
HANG = 60              # s without CPU progress -> treated as hung and killed
RESULTS = os.path.join(OUT, "sim6_results.json")
PROGRESS = os.path.join(OUT, "sim6_progress.txt")

# ----------------------------------------------------------------------------------------
# operating points (board values).  Id = I(R21) - I(R31+scope);  I(R22) = Id + Vgs/R28
# ----------------------------------------------------------------------------------------
HV, R21, R22, R28, RLOAD = 150.0, 10e3, 75.0, 100e3, 4.7e3 + 10e6


def vin_for(vout):
    ir21 = (HV - vout) / R21
    idr = ir21 - vout / RLOAD
    vgs = 3.5 + math.sqrt(max(idr, 0.0))          # IRF730_APPROX: Kp=2, Vto=3.5
    return R22 * (idr + vgs / R28)


VIN = {k: round(vin_for(v), 5) for k, v in
       dict(p140=140.0, p100=100.0, mid=0.0, m100=-100.0, m140=-140.0).items()}
VC = round((VIN["p140"] + VIN["m140"]) / 2, 5)     # sine centre
ASIN = round((VIN["m140"] - VIN["p140"]) / 2, 5)   # sine amplitude (DC-equivalent +/-140 V)

# time plan of the combined transient (s)
T = dict(sine=(0, 60e-6), sine_meas=(20e-6, 60e-6),
         to_m100=60e-6, rise=90e-6, fall=140e-6, to_mid=190e-6,
         zero=(240e-6, 440e-6), sstep_dn=440e-6, sstep_up=480e-6,
         to_m140=520e-6, to_p140=580e-6, end=640e-6)
EDGE = 5e-9


def pwl():
    pts = [(0, VC), (T["to_m100"], VC), (T["to_m100"] + EDGE, VIN["m100"]),
           (T["rise"], VIN["m100"]), (T["rise"] + EDGE, VIN["p100"]),
           (T["fall"], VIN["p100"]), (T["fall"] + EDGE, VIN["m100"]),
           (T["to_mid"], VIN["m100"]), (T["to_mid"] + EDGE, VIN["mid"]),
           (T["sstep_dn"], VIN["mid"]), (T["sstep_dn"] + EDGE, VIN["mid"] + 0.05),
           (T["sstep_up"], VIN["mid"] + 0.05), (T["sstep_up"] + EDGE, VIN["mid"]),
           (T["to_m140"], VIN["mid"]), (T["to_m140"] + EDGE, VIN["m140"]),
           (T["to_p140"], VIN["m140"]), (T["to_p140"] + EDGE, VIN["p140"]),
           (T["end"], VIN["p140"])]
    return "PWL(" + " ".join(f"{t:.9g} {v:.6g}" for t, v in pts) + ")"


# ----------------------------------------------------------------------------------------
# cases
# ----------------------------------------------------------------------------------------
LS = ["0", "1u", "10u", "50u", "200u"]
CS = ["0", "10p", "30p", "60p", "100p"]


def si(s):
    if s == "0":
        return 0.0
    m = {"p": 1e-12, "n": 1e-9, "u": 1e-6, "m": 1e-3}
    return float(s[:-1]) * m[s[-1]] if s[-1] in m else float(s)


def case(L="0", C="0", h="gnd", P="0", CL="10p", tag=""):
    name = f"L{L}_C{C}_{h}_P{P}_CL{CL}"
    return dict(name=name, L=L, C=C, housing=h, Cpar=P, Cload=CL, group=tag)


def all_cases():
    cs = []
    for L, C in itertools.product(LS, CS):                     # full grid, grounded, CL 10p
        cs.append(case(L, C, "gnd", "0", "10p", "grid"))
    for L, C in [("0", "30p"), ("0", "100p"), ("50u", "60p"), ("200u", "30p"), ("200u", "100p")]:
        cs.append(case(L, C, "flt", "0", "10p", "floating"))
    for P in ["1p", "3p"]:
        for L, C in [("0", "0"), ("200u", "0"), ("0", "100p"), ("200u", "100p")]:
            cs.append(case(L, C, "gnd", P, "10p", "cpar"))
    cs.append(case("200u", "100p", "flt", "3p", "10p", "cpar"))
    for L, C, h, P in [("0", "0", "gnd", "0"), ("200u", "0", "gnd", "0"), ("0", "100p", "gnd", "0"),
                       ("200u", "100p", "gnd", "0"), ("200u", "100p", "flt", "0"),
                       ("200u", "100p", "gnd", "3p")]:
        cs.append(case(L, C, h, P, "30p", "cload30"))
    # extensions (added after the main grid): where does inductance start to matter, and
    # where exactly does a grounded Ccase cross the 10 % rise/fall limit?
    for L in ["500u", "1m", "2m", "5m"]:
        for C in ["0", "30p"]:
            cs.append(case(L, C, "gnd", "0", "10p", "l_ext"))
    for L in ["0", "200u"]:
        for C in ["15p", "20p"]:
            cs.append(case(L, C, "gnd", "0", "10p", "c_fine"))
    for C in ["5p", "10p", "15p", "20p"]:
        cs.append(case("0", C, "gnd", "0", "30p", "c_fine"))
    return cs


# ----------------------------------------------------------------------------------------
# netlist generation
# ----------------------------------------------------------------------------------------
MODELS = f"""* --- models (copied verbatim from sim2_classA_v2_irf730.cir; Cz = 45p nominal) ---
.param Cz=45p
.model DZ12 D(Is=1e-14 Rs=5 BV=12 Ibv=5m Cjo={{Cz}} M=0.4 Vj=0.75)
* IRF730 is NOT in LTspice's library. APPROXIMATION built from typical datasheet values (see sim2).
.model IRF730_APPROX VDMOS(Rg=2 Vto=3.5 Kp=2 Lambda=0.003 Rd=0.7 Rs=0.05 Rb=0.2 Cgdmax=0.8n Cgdmin=50p A=1 Cgs=620p Cjo=640p M=0.5 Vj=0.7 Is=20p BV=400 IBV=250u ksubthres=0.1 mfg=approximation Vds=400 Ron=1 Qg=38n)
.include {MOD}
"""


def r21_block(c):
    """R21 = 10k as a 5-section T ladder: each section n(k-1) -[1k]-[L/10]- m_k -[1k]-[L/10]- n(k),
    Ccase/5 from m_k to the housing node.  n0 = PHV, n5 = TP5.  Cpar end-to-end PHV-TP5."""
    L, C = si(c["L"]), si(c["C"])
    hous = "0" if c["housing"] == "gnd" else "HOUS"
    lines = [f"* --- R21 parasitic model: L={c['L']} Ccase={c['C']} housing={c['housing']} "
             f"Cpar={c['Cpar']} (10k total, 5 T-sections of 2 x 1k) ---"]
    for k in range(1, 6):
        a = "PHV" if k == 1 else f"N{k-1}"
        b = "TP5" if k == 5 else f"N{k}"
        m = f"M{k}"
        if L > 0:
            lines += [f"R21_{k}a {a} XA{k} 1k", f"L21_{k}a XA{k} {m} {L/10:.6g}",
                      f"R21_{k}b {m} XB{k} 1k", f"L21_{k}b XB{k} {b} {L/10:.6g}"]
        else:
            lines += [f"R21_{k}a {a} {m} 1k", f"R21_{k}b {m} {b} 1k"]
        if C > 0:
            lines.append(f"CC21_{k} {m} {hous} {C/5:.6g}")
    if c["housing"] == "flt":
        lines += ["* floating housing: 1G to +HV and 1G to GND (DC-defined, AC-floating)",
                  "RH1 HOUS PHV 1G", "RH2 HOUS 0 1G"]
    if si(c["Cpar"]) > 0:
        lines.append(f"CP21 PHV TP5 {c['Cpar']}")
    return "\n".join(lines)


def stage(c, gate_lines, r22=75, r18=True, sim2=False):
    rails = ("V3 PHV 0 150\nV_neg NHV 0 -150" if sim2 else
             "* rails: ideal source + 1 ohm source R + C26/C27 4.7u (1 ohm ESR)\n"
             "V3 PHV0 0 150\nRP PHV0 PHV 1\nC26 PHV C26E 4.7u\nRC26 C26E 0 1\n"
             "V_neg NHV0 0 -150\nRN NHV0 NHV 1\nC27 NHV C27E 4.7u\nRC27 C27E 0 1")
    r21 = "R2 PHV TP5 10k" if sim2 else r21_block(c)
    return f"""XU7 IN SRC VCC NHV OA LM8261
{gate_lines}
M1 TP5 G SRC SRC IRF730_APPROX
R22 SRC NHV {r22}
* --- V2 gate protection (R28 100k G-S, D4 BZT52C12 cathode on G via 1 ohm)
R28 G SRC 100k
RZS G DK 1
D4 SRC DK DZ12
{"R18 G NHV 1Meg" if r18 else "* R18 omitted (sim2 reproduction)"}
{r21}
* --- R31 4.7k to TP6, scope 10Meg || Cload at TP6
R31 TP5 TP6 4.7k
C1 TP6 0 {c['Cload']}
RSCOPE TP6 0 10Meg
{rails}
* floating 12 V op-amp supply referenced to -HV (as sim2)
V1 N12 NHV 12
R1 N12 VCC 1
"""


HDR = """* SIM 6 -- R21 parasitics vs the V2 class-A output stage at +/-150 V   (generated by sim6_run.py)
* Stage = sim2_classA_v2_irf730.cir (VAR=3: R28/D4 + R31 + scope at TP6, Rg1 = 1 ohm) with BOARD values:
*   R22 = 75 ohm (sim2 kept 50), R18 1M gate -> -HV added (board part), rails +/-150 V with 1 ohm
*   source R + C26/C27, cshunt removed (it would add 1 pF per ladder node and bias the Ccase sweep).
* U7 +IN driven by an ideal source referenced to -HV (as sim2): I(R22) = V(IN,NHV)/75.
"""


def tran_netlist(c):
    has_hous = c["housing"] == "flt"
    return HDR + f"""* CASE {c['name']}   analysis = combined transient
* 0-60u   : 100 kHz sine, DC-equivalent +/-140 V at TP5 (6 cycles, measured 20-60u)
* 60u     : -> -100 V;  90u: step to +100 V (rise);  140u: step to -100 V (fall)
* 190u    : -> 0 V (mid);  240-440u: zero-input window (200 us after 50 us settling)
* 440u    : +50 mV small step (~ -6.7 V at TP5); 480u: back
* 520u    : -> -140 V DC (R21 power);  580u: -> +140 V;  end 640u.  Input edges 5 ns.
.param VC={VC} ASIN={ASIN}
V2S INS INM SINE(0 {{ASIN}} 100k 0 0 0 6)
V2P INM NHV {pwl()}
RIN INS IN 1
{stage(c, 'Rg1 OA G 1')}
{r21_block_save(c, has_hous)}
* initial guess for the op-amp + VDMOS operating point at t=0 (input = VC); without it the L=1u
* ladders with Ccase > 0 stalled in LTspice's source stepping (>240 s).  Changes only the start of
* the DC search, not the (unique) DC solution -- verified identical on the ideal baseline.
.nodeset V(IN)={{-150+VC}} V(SRC)={{-150+VC}} V(G)={{-146.5+VC+sqrt(VC/75)}} V(OA)={{-146.5+VC+sqrt(VC/75)}} V(TP5)={{150-VC/75*1e4}} V(TP6)={{150-VC/75*1e4}} V(VCC)=-138
.tran 0 {T['end']:.9g} 0 5n
.options method=gear plotwinsize=0 gminsteps=500 itl4=500
* ---- cross-check .meas (the numbers in sim6_results.json are computed from the .raw) ----
.meas tran s_tp5_max max V(TP5) from 20u to 60u
.meas tran s_tp5_min min V(TP5) from 20u to 60u
.meas tran s_tp5_pp pp V(TP5) from 20u to 60u
.meas tran s_tp6_pp pp V(TP6) from 20u to 60u
.meas tran lo1 avg V(TP5) from 85u to 90u
.meas tran hi1 avg V(TP5) from 135u to 140u
.meas tran tr10 when V(TP5)=-80 td=90u rise=1
.meas tran tr90 when V(TP5)=80 td=90u rise=1
.meas tran trise param tr90-tr10
.meas tran tf90 when V(TP5)=80 td=140u fall=1
.meas tran tf10 when V(TP5)=-80 td=140u fall=1
.meas tran tfall param tf10-tf90
.meas tran z_pp pp V(TP5) from 240u to 440u
.meas tran z_avg avg V(TP5) from 240u to 440u
.meas tran p_0v avg I(R21_1a)*(V(PHV)-V(TP5)) from 400u to 440u
.meas tran v_m140 avg V(TP5) from 560u to 580u
.meas tran p_m140 avg I(R21_1a)*(V(PHV)-V(TP5)) from 560u to 580u
.end
"""


def r21_block_save(c, has_hous):
    sv = "V(TP5) V(TP6) V(G) V(SRC) V(OA) V(IN) V(NHV) V(PHV) V(M3) I(R21_1a) I(R21_5b)"
    if has_hous:
        sv += " V(HOUS)"
    return ".save " + sv


def loop_netlist(c):
    return HDR + f"""* CASE {c['name']}   analysis = loop gain of the U7 loop (Middlebrook double injection)
* Loop broken between U7 output (OA) and Rg1: Vinj (voltage injection, OB = OA + vinj),
* Iinj (current injection into OB), Vmeas (0 V, current into the gate side).
*   k=0: Tv = -V(OA)/V(OB)            k=1: Ti = I(Vinj)/I(Vmeas)
*   T = (Tv*Ti - 1)/(Tv + Ti + 2)   (post-processed in sim6_run.py)
* Operating points: VDC -> TP5 = +140 / 0 / -140 V.
.param k=0 VDC={VIN['mid']}
V2P INS NHV {{VDC}}
RIN INS IN 1
Vinj OB OA 0 AC {{1-k}}
Iinj 0 OB 0 AC {{k}}
Vmeas OB OBL 0
{stage(c, 'Rg1 OBL G 1')}
* initial guess for the (hard) op-amp + VDMOS operating point, per VDC step
.nodeset V(IN)={{-150+VDC}} V(SRC)={{-150+VDC}} V(G)={{-146.5+VDC+sqrt(VDC/75)}} V(OA)={{-146.5+VDC+sqrt(VDC/75)}} V(OB)={{-146.5+VDC+sqrt(VDC/75)}} V(OBL)={{-146.5+VDC+sqrt(VDC/75)}} V(TP5)={{150-VDC/75*1e4}} V(TP6)={{150-VDC/75*1e4}} V(VCC)=-138
.save V(OA) V(OB) I(Vinj) I(Vmeas) V(TP5)
.step param k list 0 1
.step param VDC list {VIN['p140']} {VIN['mid']} {VIN['m140']}
.ac dec 40 1k 300Meg
.options gminsteps=500 itl4=500
.end
"""


def sim2_validation_netlist():
    c = case("0", "0", "gnd", "0", "10p")
    return f"""* SIM 6 validation: sim2_classA_v2_irf730.cir VAR=3 Cload=10p Cz=45p rebuilt by sim6_run.py
* (R22=50, ideal rails, no R18, single R2 10k, cshunt=1e-12, SINE(0.75 0.75 100k)).
* Expected from sim2_classA_v2_irf730.log step 4: tp5_pp 278.64, tp6_pp 278.22, tp5_max 141.69, tp5_min -136.95
V2 IN NHV SINE(0.75 0.75 100k)
{stage(c, 'Rg1 OA G 1', r22=50, r18=False, sim2=True)}
.tran 0 50u 30u 5n
.options method=gear plotwinsize=0 gminsteps=500 cshunt=1e-12 itl4=500
.meas tran tp5_max max V(TP5)
.meas tran tp5_min min V(TP5)
.meas tran tp5_pp pp V(TP5)
.meas tran tp6_pp pp V(TP6)
{MODELS}.end
"""


def write(name, text):
    path = os.path.join(OUT, name + ".cir")
    open(path, "w", encoding="utf-8").write(text)
    return path


def make_files(c):
    t = tran_netlist(c).replace(".end\n", MODELS + ".end\n")
    lp = loop_netlist(c).replace(".end\n", MODELS + ".end\n")
    return (write(f"sim6_{c['name']}_tran", t), write(f"sim6_{c['name']}_loop", lp))


# ----------------------------------------------------------------------------------------
# LTspice runner with timeout + hang watchdog
# ----------------------------------------------------------------------------------------
def kill_tree(pid):
    try:
        p = psutil.Process(pid)
        for ch in p.children(recursive=True):
            ch.kill()
        p.kill()
    except psutil.NoSuchProcess:
        pass


def read_log(path):
    raw = open(path, "rb").read()
    return raw.decode("utf-16-le", errors="ignore") if b"\x00" in raw[:200] else raw.decode("latin-1")


MEAS_RE = re.compile(r"^(\w+):\s.*?=\s*([-+\d.eE]+)", re.M)


def run_lt(path):
    base = path[:-4]
    for ext in (".log", ".raw", ".op.raw"):
        try:
            os.remove(base + ext)
        except FileNotFoundError:
            pass
    t0 = time.time()
    p = subprocess.Popen([LT, "-b", path], cwd=OUT)
    try:
        ps = psutil.Process(p.pid)
    except psutil.NoSuchProcess:
        ps = None
    last_cpu, last_change, status = -1.0, t0, None
    while status is None:
        try:
            rc = p.wait(timeout=2)
            status = "ok" if rc == 0 else f"EXIT CODE {rc}"
            break
        except subprocess.TimeoutExpired:
            pass
        now = time.time()
        if now - t0 > TIMEOUT:
            kill_tree(p.pid); p.wait(); status = "TIMEOUT"; break
        try:
            cpu = sum(ps.cpu_times()[:2]) if ps else 0.0
        except psutil.NoSuchProcess:
            continue
        if cpu > last_cpu + 0.05:
            last_cpu, last_change = cpu, now
        elif now - last_change > HANG:
            kill_tree(p.pid); p.wait(); status = "HANG"
    dt = time.time() - t0
    log, meas, fails, errs = base + ".log", {}, [], []
    if os.path.exists(log) and os.path.getmtime(log) >= t0 - 1:
        txt = read_log(log)
        meas = {k.lower(): float(v) for k, v in MEAS_RE.findall(txt)}
        meas.pop("options", None)
        fails = re.findall(r"Measurement \"?(\w+)\"? FAIL", txt, re.I)
        errs = [l for l in txt.splitlines() if re.search(r"error|singular|too small|abort", l, re.I)]
    elif status == "ok":
        status = "NO FRESH LOG"
    raw = base + ".raw"
    if status == "ok" and not (os.path.exists(raw) and os.path.getmtime(raw) >= t0 - 1):
        status = "NO FRESH RAW"
    return dict(status=status, seconds=round(dt, 1), meas=meas, meas_fail=fails, log_errors=errs[:5])


# ----------------------------------------------------------------------------------------
# raw reader
# ----------------------------------------------------------------------------------------
def read_raw(path):
    data = open(path, "rb").read()
    mk = "Binary:\n".encode("utf-16-le")
    i = data.find(mk)
    if i < 0:
        raise ValueError("no Binary: section")
    hdr = data[:i].decode("utf-16-le")
    body = data[i + len(mk):]
    flags = re.search(r"Flags:\s*(.*)", hdr).group(1)
    nv = int(re.search(r"No\. Variables:\s*(\d+)", hdr).group(1))
    npnt = int(re.search(r"No\. Points:\s*(\d+)", hdr).group(1))
    vs = hdr.split("Variables:")[-1].strip().splitlines()
    names = [ln.strip().split()[1] for ln in vs[:nv]]
    if "complex" in flags:
        arr = np.frombuffer(body, dtype="<c16", count=npnt * nv).reshape(npnt, nv)
        return {n.lower(): arr[:, j] for j, n in enumerate(names)}, flags
    if "double" in flags:
        arr = np.frombuffer(body, dtype="<f8", count=npnt * nv).reshape(npnt, nv)
        return {n.lower(): arr[:, j] for j, n in enumerate(names)}, flags
    dt = np.dtype([("t", "<f8")] + [(f"v{j}", "<f4") for j in range(1, nv)])
    arr = np.frombuffer(body, dtype=dt, count=npnt)
    out = {names[0].lower(): np.abs(arr["t"])}
    for j in range(1, nv):
        out[names[j].lower()] = arr[f"v{j}"].astype(np.float64)
    return out, flags


# ----------------------------------------------------------------------------------------
# waveform metrics
# ----------------------------------------------------------------------------------------
def win(t, v, a, b):
    m = (t >= a) & (t <= b)
    return t[m], v[m]


def avg(t, v, a, b):
    tt, vv = win(t, v, a, b)
    return float(np.trapezoid(vv, tt) / (tt[-1] - tt[0]))


def cross(t, v, lvl, t0, t1, rising):
    tt, vv = win(t, v, t0, t1)
    d = vv - lvl
    idx = np.where((d[:-1] < 0) & (d[1:] >= 0))[0] if rising else np.where((d[:-1] > 0) & (d[1:] <= 0))[0]
    if len(idx) == 0:
        return None
    j = idx[0]
    return float(tt[j] + (tt[j + 1] - tt[j]) * (lvl - vv[j]) / (vv[j + 1] - vv[j]))


def ringing(t, v, t_start, t_end, vfin, thr):
    """Hysteresis zero-crossings of (v - vfin) after t_start. Returns (n_half_cycles, freq, first
    excursion after the first crossing)."""
    tt, vv = win(t, v, t_start, t_end)
    e = vv - vfin
    state, xs = 0, []
    for j in range(len(e)):
        s = 1 if e[j] > thr else (-1 if e[j] < -thr else 0)
        if s and s != state:
            if state:
                xs.append(tt[j])
            state = s
    if len(xs) < 2:
        return len(xs), None
    hp = np.diff(xs)
    return len(xs), float(1.0 / (2 * np.mean(hp)))


def edge_metrics(t, v, t_step, t_next, v_from, v_to):
    sw = v_to - v_from
    rising = sw > 0
    t10 = cross(t, v, v_from + 0.1 * sw, t_step, t_next, rising)
    t90 = cross(t, v, v_from + 0.9 * sw, t_step, t_next, rising)
    tt, vv = win(t, v, t_step, t_next)
    ov = ((vv.max() - v_to) if rising else (v_to - vv.min())) / abs(sw) * 100
    out_band = np.where(np.abs(vv - v_to) > 0.01 * abs(sw))[0]
    settle = float(tt[out_band[-1]] - t_step) if len(out_band) else 0.0
    thr = max(5e-3, 1e-3 * abs(sw))
    nx, f = ringing(t, v, t_step, t_next, v_to, thr)
    return dict(t10=t10, t90=t90, tr=(t90 - t10) if (t10 and t90) else None,
                overshoot_pct=float(ov), settle_1pct=settle,
                settled_at_end=bool(abs(vv[-1] - v_to) <= 0.01 * abs(sw)),
                ring_crossings=nx, ring_freq=f, v_from=v_from, v_to=v_to)


def spectrum_peak(t, v, a, b):
    tt, vv = win(t, v, a, b)
    n = int((b - a) / 5e-9)
    tu = np.linspace(a, b, n)
    vu = np.interp(tu, tt, vv)
    vu = vu - vu.mean()
    sp = np.abs(np.fft.rfft(vu * np.hanning(n)))
    fr = np.fft.rfftfreq(n, 5e-9)
    j = int(np.argmax(sp[1:]) + 1)
    return float(fr[j])


def tran_metrics(d):
    t = d["time"]
    tp5, tp6, g = d["v(tp5)"], d["v(tp6)"], d["v(g)"]
    r = {}
    a, b = T["sine_meas"]
    for nm, v in (("tp5", tp5), ("tp6", tp6)):
        _, vv = win(t, v, a, b)
        r[f"sine_{nm}_max"], r[f"sine_{nm}_min"] = float(vv.max()), float(vv.min())
        r[f"sine_{nm}_pp"] = float(vv.max() - vv.min())
    # large step
    for nm, v in (("tp5", tp5), ("tp6", tp6)):
        lo1 = avg(t, v, T["rise"] - 5e-6, T["rise"])
        hi = avg(t, v, T["fall"] - 5e-6, T["fall"])
        lo2 = avg(t, v, T["to_mid"] - 5e-6, T["to_mid"])
        r[f"rise_{nm}"] = edge_metrics(t, v, T["rise"], T["fall"], lo1, hi)
        r[f"fall_{nm}"] = edge_metrics(t, v, T["fall"], T["to_mid"], hi, lo2)
    # zero input window
    a, b = T["zero"]
    _, vv = win(t, tp5, a, b)
    r["zero_tp5_pp"] = float(vv.max() - vv.min())
    r["zero_tp5_avg"] = avg(t, tp5, a, b)
    _, gg = win(t, g, a, b)
    r["zero_gate_pp"] = float(gg.max() - gg.min())
    _, v6 = win(t, tp6, a, b)
    r["zero_tp6_pp"] = float(v6.max() - v6.min())
    r["zero_tp5_peakfreq"] = spectrum_peak(t, tp5, a, b) if r["zero_tp5_pp"] > 1e-3 else None
    # small step (+50 mV in -> ~ -6.7 V out) and back
    base0 = avg(t, tp5, T["sstep_dn"] - 20e-6, T["sstep_dn"])
    dn = avg(t, tp5, T["sstep_up"] - 5e-6, T["sstep_up"])
    back = avg(t, tp5, T["to_m140"] - 5e-6, T["to_m140"])
    r["sstep_dn"] = edge_metrics(t, tp5, T["sstep_dn"], T["sstep_up"], base0, dn)
    r["sstep_up"] = edge_metrics(t, tp5, T["sstep_up"], T["to_m140"], dn, back)
    _, vv = win(t, tp5, T["sstep_up"] + 20e-6, T["to_m140"])
    r["sstep_post_pp"] = float(vv.max() - vv.min())
    # DC extremes: pp (limit-cycle check) and R21 power
    ir = d["i(r21_1a)"]
    vr = d["v(phv)"] - tp5
    for key, (a, b) in dict(m140=(T["to_m140"] + 30e-6, T["to_p140"]),
                            p140=(T["to_p140"] + 30e-6, T["end"]),
                            v0=(T["zero"][1] - 40e-6, T["zero"][1])).items():
        _, vv = win(t, tp5, a, b)
        r[f"dc_{key}_v"] = avg(t, tp5, a, b)
        r[f"dc_{key}_pp"] = float(vv.max() - vv.min())
        r[f"dc_{key}_p_r21"] = avg(t, ir * vr, a, b)
    # internal ladder node and gate: max excursion across whole run
    r["gate_vgs_max"] = float(np.max(g - d["v(src)"]))
    r["gate_vgs_min"] = float(np.min(g - d["v(src)"]))
    return r


def loop_metrics(d, logtxt):
    f = np.real(d["frequency"])
    starts = [0] + [j for j in range(1, len(f)) if f[j] < f[j - 1]] + [len(f)]
    segs = [(starts[i], starts[i + 1]) for i in range(len(starts) - 1)]
    steps = re.findall(r"\.step k=(\S+) vdc=(\S+)", logtxt)
    res = {}
    labels = ["p140", "mid", "m140"]
    if len(segs) != 6:
        return dict(error=f"expected 6 AC segments, got {len(segs)}")
    for n in range(3):
        s0, s1 = segs[2 * n], segs[2 * n + 1]
        ff = f[s0[0]:s0[1]]
        tv = -d["v(oa)"][s0[0]:s0[1]] / d["v(ob)"][s0[0]:s0[1]]
        ti = d["i(vinj)"][s1[0]:s1[1]] / d["i(vmeas)"][s1[0]:s1[1]]
        tl = (tv * ti - 1) / (tv + ti + 2)
        mag = 20 * np.log10(np.abs(tl))
        ph = np.degrees(np.unwrap(np.angle(tl)))
        ph = ph - 360 * round(ph[0] / 360)
        out = dict(dc_gain_db=float(mag[0]), phase_lowf=float(ph[0]))
        j = np.where((mag[:-1] >= 0) & (mag[1:] < 0))[0]
        if len(j):
            j = j[0]
            fr = mag[j] / (mag[j] - mag[j + 1])
            fc = ff[j] * (ff[j + 1] / ff[j]) ** fr
            pc = ph[j] + fr * (ph[j + 1] - ph[j])
            out.update(fc=float(fc), pm=float(180 + pc))
            if len(np.where((mag[:-1] >= 0) & (mag[1:] < 0))[0]) > 1:
                out["multiple_crossovers"] = True
        k = np.where((ph[:-1] > -180) & (ph[1:] <= -180))[0]
        if len(k):
            k = k[0]
            out.update(f180=float(ff[k]), gm_db=float(-mag[k]))
        res[labels[n]] = out
    res["step_labels"] = steps
    return res


# ----------------------------------------------------------------------------------------
def log_progress(msg):
    with open(PROGRESS, "a", encoding="utf-8") as fh:
        fh.write(f"{time.strftime('%H:%M:%S')} {msg}\n")


def do_case(c, keep_raw=False, only=None, prev=None):
    tpath, lpath = make_files(c)
    out = dict(prev) if prev else dict(case=c)
    out["case"] = c
    for kind, path in (("tran", tpath), ("loop", lpath)):
        if only and kind != only:
            continue
        rr = run_lt(path)
        raw = path[:-4] + ".raw"
        if rr["status"] == "ok":
            try:
                d, _ = read_raw(raw)
                if kind == "tran":
                    rr["metrics"] = tran_metrics(d)
                else:
                    rr["metrics"] = loop_metrics(d, read_log(path[:-4] + ".log"))
            except Exception as ex:           # measurement failure is reported, not hidden
                rr["metrics_error"] = f"{type(ex).__name__}: {ex}"
        if not keep_raw:
            for ext in (".raw", ".op.raw"):
                try:
                    os.remove(path[:-4] + ext)
                except FileNotFoundError:
                    pass
        out[kind] = rr
        log_progress(f"{c['name']} {kind} {rr['status']} {rr['seconds']}s"
                     + (" METRICS-ERROR " + rr["metrics_error"] if "metrics_error" in rr else ""))
    return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    jobs = 4
    for a in sys.argv[1:]:
        if a.startswith("--jobs="):
            jobs = int(a.split("=")[1])
    keep = "--keep-raw" in sys.argv
    only = None
    for a in sys.argv[1:]:
        if a.startswith("--only="):
            only = a.split("=")[1]
    if args and args[0] == "validate":
        p = write("sim6_validate_sim2", sim2_validation_netlist())
        rr = run_lt(p)
        for ext in (".raw", ".op.raw"):
            try:
                os.remove(p[:-4] + ext)
            except FileNotFoundError:
                pass
        print(json.dumps(rr, indent=1))
        return
    cases = all_cases()
    if args and args[0] == "baseline":
        cases = [c for c in cases if c["name"] == "L0_C0_gnd_P0_CL10p"]
    elif args and args[0] != "all":
        cases = [c for c in cases if c["name"] in args]
    existing = {}
    if os.path.exists(RESULTS):
        for r in json.load(open(RESULTS)).get("runs", []):
            existing[r["case"]["name"]] = r
    import threading
    lock = threading.Lock()

    def save():                                   # incremental, so a killed sweep keeps its results
        order = [c["name"] for c in all_cases()]
        runs = [existing[n] for n in order if n in existing]
        meta = dict(generated=time.strftime("%Y-%m-%d %H:%M:%S"), vin=VIN, vc=VC, asin=ASIN, timeplan=T,
                    timeout_s=TIMEOUT, hang_s=HANG)
        tmp = RESULTS + ".tmp"
        json.dump(dict(meta=meta, runs=runs), open(tmp, "w"), indent=1)
        os.replace(tmp, RESULTS)

    def job(c):
        r = do_case(c, keep, only, existing.get(c["name"]))
        with lock:
            existing[c["name"]] = r
            save()
        return r

    with ThreadPoolExecutor(max_workers=jobs) as ex:
        results = list(ex.map(job, cases))
    kinds = [only] if only else ["tran", "loop"]
    n_ok = sum(1 for r in results for k in kinds if k in r and r[k]["status"] == "ok" and "metrics" in r[k])
    print(f"this invocation: {len(results)} cases, {n_ok}/{len(kinds)*len(results)} netlists ok with metrics")


if __name__ == "__main__":
    main()
