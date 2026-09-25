"""SIM 7 report: re-parse every case's LTspice log (sim7_runs/*.log) with sim7_run.parse_log and
print the tables used in sim7_README.md.  Read-only apart from rewriting the 'meas' of each case
in sim7_results.json from its (fresh) log, which fixes values parsed by an earlier parser version.

Usage:  python sim7_report.py [--save] [section ...]   sections: mon out nocs osc ls chain ctran  (default all)
"""
import os, sys, json, re
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from sim7_run import parse_log, RUNS, RESULTS

R = json.load(open(RESULTS))
for name, r in R.items():
    log = os.path.join(RUNS, f"sim7_{name}.log")
    if r.get("status") == "ok" and os.path.exists(log):
        raw = open(log, "rb").read()
        txt = raw.decode("utf-16-le", errors="ignore") if b"\x00" in raw[:200] else raw.decode("latin-1")
        res, fails = parse_log(txt)
        if res:
            r["meas"], r["fails"] = res, fails
if "--save" in sys.argv:        # only when no sim7_run.py batch is running (it writes the same file)
    json.dump(R, open(RESULTS, "w"), indent=1, sort_keys=True)

sec = [a for a in sys.argv[1:] if not a.startswith("--")] or ["mon", "out", "nocs", "osc", "ls", "chain", "ctran"]


def g(n, k, fmt="{:.3g}"):
    r = R.get(n)
    if not r:
        return "--"
    v = r["meas"].get(k)
    if isinstance(v, (int, float)):
        return fmt.format(v)
    return "FAIL" if k in r.get("fails", []) else "--"


def st(n, k):
    return R.get(n, {}).get("meas", {}).get("_steps", {}).get(k, [])


if "mon" in sec:
    print("== monitor: DC faults at +HV = 150 V (4 steps: DIFF 0/1 x unpowered-rail R 1k/10k); worst case")
    for n in ("mon_fault_10k", "mon_fault_22k"):
        for c in ("v2n_p", "v2n_u", "v2w_p", "v2w_u", "i5_p", "i5_u", "v2b_p", "v2b_u"):
            i = [abs(x) for x in st(n, f"{c}_iin_150") if isinstance(x, float)]
            p = [x for x in st(n, f"{c}_pr30_150") if isinstance(x, float)]
            vr = [abs(x) for x in st(n, f"{c}_vr30_150") if isinstance(x, float)]
            print(f"  {n:14s} {c:6s} |I_U8in|max={max(i)*1e3 if i else float('nan'):8.4f} mA  "
                  f"P_R30max={max(p) if p else float('nan'):8.4f} W  |V_R30|max={max(vr) if vr else float('nan'):7.2f} V")
    print("== monitor: +/-12 V collapse with +HV = 150 V on (steps TF = 1m, 10m, 100m)")
    for n in ("mon_pd_10k", "mon_pd_22k"):
        for c in ("v2n", "v2w", "i5"):
            i = st(n, f"{c}_imax"); p = st(n, f"{c}_pr30max"); v = st(n, f"{c}_vinmax")
            print(f"  {n:12s} {c:4s} I_U8in max (mA) = {[round(x*1e3, 4) for x in i]}  P_R30 max (mW) = "
                  f"{[round(x*1e3, 3) for x in p]}  V_in max = {[round(x, 3) for x in v]}")


def out_tables(prefix, title):
    print(f"\n== {title}: 100 kHz full-swing sine")
    for n in sorted(k for k in R if k.startswith(prefix + "sine")):
        print(f"  {n:30s} TP6 {g(n,'tp6_min','{:.1f}')}..{g(n,'tp6_max','{:.1f}')} pp={g(n,'tp6_pp','{:.1f}')} "
              f"({g(n,'swing_pct','{:.1f}')}% of 2HV) THD={g(n,'thd_pct','{:.2f}')}% Vgs {g(n,'vgs_min')}..{g(n,'vgs_max')} "
              f"Iz4 max {g(n,'iz_max')} Pq1={g(n,'pq1_avg')} W")
    print(f"== {title}: zero input 12-20 us, +50 mV step at 20 us, back at 35 us, tail to 100 us")
    for n in sorted(k for k in R if k.startswith(prefix + "step")):
        print(f"  {n:34s} TP5 {g(n,'v_pre','{:.1f}')}->{g(n,'v_post','{:.1f}')} V  zero-in pp={g(n,'pp_pre')}  "
              f"ovs={g(n,'over_pct','{:.2f}')}/{g(n,'over2_pct','{:.2f}')}%  TP5 pp 60-80us={g(n,'pp5_60')} 80-100us={g(n,'pp5_80')}  "
              f"TP6 pp 80-100us={g(n,'pp6_80')}  f_ring={g(n,'fring')}")
    print(f"== {title}: U7 loop gain (break at Q1 source / U7 -IN) and closed-loop TP6 response")
    for n in sorted(k for k in R if k.startswith(prefix + "loop")):
        print(f"  {n:34s} T(1k)={g(n,'tlf_db','{:.1f}')} dB  fc={g(n,'fc_at')} Hz  PM={g(n,'pmx_deg','{:.1f}')} deg  "
              f"(last crossing {g(n,'fclast_at')} Hz, {g(n,'pmlast_deg','{:.1f}')} deg)  TP6: lf={g(n,'glf_db','{:.2f}')} dB "
              f"peak={g(n,'gpk_db','{:.2f}')} dB f-3dB={g(n,'f3db_at')}  TP5 peak={g(n,'g5pk_db','{:.2f}')} dB")


if "out" in sec:
    out_tables("out_", "output stage WITH Sim-2 cshunt=1e-12")
if "nocs" in sec:
    out_tables("nocs_", "output stage WITHOUT cshunt (vendor LM8261 model as issued; = Sim 6 / chain)")
if "osc" in sec:
    out_tables("osc_", "oscillation follow-up (with cshunt)")

if "ls" in sec:
    print("\n== level shifter AC (R29 = 1 Meg unless noted)")
    for n in sorted(k for k in R if k.startswith("ls_ac")):
        print(f"  {n:22s} gain={g(n,'glfm_db','{:.2f}')} dB peak={g(n,'gpk_db','{:.2f}')} dB f-3dB={g(n,'f3db_at')} Hz  "
              f"T(100)={g(n,'tlf_db','{:.1f}')} dB fc={g(n,'fc_at')} Hz PM={g(n,'pmx_deg','{:.1f}')} deg (last {g(n,'pmlast_deg','{:.1f}')})")
    print("== level shifter +/-20 mV DAC steps")
    for n in sorted(k for k in R if k.startswith("ls_step")):
        print(f"  {n:22s} step {g(n,'stepa')}/{g(n,'stepb')} V  ovs {g(n,'ovsa_pct','{:.2f}')}/{g(n,'ovsb_pct','{:.2f}')}%  "
              f"residual pp {g(n,'resa_pp')}/{g(n,'resb_pp')}  pre pp {g(n,'pre_pp')}  Iq3={g(n,'iq3_0')} A  IR29={g(n,'ir29_0')} A Vgs={g(n,'vgs_0')}")
    print("== level shifter 100 kHz DAC sine")
    for n in sorted(k for k in R if k.startswith("ls_sine")):
        print(f"  {n:22s} TP4-(-HV) {g(n,'tmin')}..{g(n,'tmax')} V gain={g(n,'gain')} THD={g(n,'thd_pct','{:.2f}')}% "
              f"Iq3 {g(n,'iqmin')}..{g(n,'iqmax')} Vgs3 {g(n,'vgsmin')}..{g(n,'vgsmax')} ID5 {g(n,'id5min')}..{g(n,'id5max')} clip={g(n,'clip100pct','{:.1f}')}%")

if "chain" in sec:
    print("\n== full chain, bench trim at midscale (servo on RV1+R26; RV1 range = 3300..4300 ohm)")
    for n in sorted(k for k in R if k.startswith("chain_trim")):
        print(f"  {n:34s} Rc={g(n,'rc','{:.0f}')} TP5@RV1max={g(n,'out_rhi','{:.1f}')} @RV1min={g(n,'out_rlo','{:.1f}')} "
              f"gain={g(n,'gain','{:.1f}')} code0={g(n,'o0','{:.1f}')} code255={g(n,'o255','{:.1f}')} TP3={g(n,'tp3_c','{:.4f}')} "
              f"V_R30={g(n,'r30drop','{:.4f}')} Vgs1max={g(n,'vgs1max','{:.2f}')} ID4max={g(n,'id4max')} ID5 {g(n,'id5min')}..{g(n,'id5max')} "
              f"Pq1(mid)={g(n,'pq1_c','{:.2f}')} PR21(255)={g(n,'pr21_255','{:.2f}')}")
    print("== full chain, RV1 fixed at the value trimmed on one rail, run on another")
    for n in sorted(k for k in R if k.startswith("chain_fix")):
        print(f"  {n:38s} RV1tot={R[n]['params'].get('RFIX')} TP5(mid)={g(n,'out_c','{:.2f}')} gain={g(n,'gain','{:.1f}')} "
              f"code0={g(n,'o0','{:.1f}')} code255={g(n,'o255','{:.1f}')}")

if "ctran" in sec:
    print("\n== full chain dynamic (RV1 fixed at the trimmed value)")
    for n in sorted(k for k in R if k.startswith("ctran")):
        if "step" in n:
            print(f"  {n:22s} TP5(mid)={g(n,'out_c')} zero-in pp TP5={g(n,'pp5_zero')} TP6={g(n,'pp6_zero')} TP4={g(n,'pp4_zero')} "
                  f"step {g(n,'v_pre')}->{g(n,'v_post')} V ovs={g(n,'over_pct','{:.3f}')}/{g(n,'over2_pct','{:.3f}')}% "
                  f"TP5 pp after step={g(n,'pp5_post')} after return={g(n,'pp5_end')}  Q1-source pp {g(n,'pps1_post')}/{g(n,'pps1_end')}")
        else:
            print(f"  {n:22s} TP5 {g(n,'o_min','{:.1f}')}..{g(n,'o_max','{:.1f}')} TP6 {g(n,'o6_min','{:.1f}')}..{g(n,'o6_max','{:.1f}')} "
                  f"pp6={g(n,'o6_pp','{:.1f}')} THD6={g(n,'thd_pct','{:.2f}')}% TP4-(-HV) {g(n,'tp4r_min')}..{g(n,'tp4r_max')} "
                  f"Iq3min={g(n,'iq3_min')} Vgs1max={g(n,'vgs1_max')} ID4max={g(n,'id4max')} ID5 {g(n,'id5min')}..{g(n,'id5max')}")

bad = {n: r["status"] for n, r in R.items() if r["status"] != "ok"}
print(f"\ncases: {len(R)}   not ok: {bad if bad else 'none'}")
