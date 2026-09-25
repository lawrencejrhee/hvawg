"""SIM 6 report: reads sim6_results.json, computes every metric as a delta vs the ideal R21
(L=0, Ccase=0, Cpar=0) at the same Cload, applies the pass criteria, writes the summary back
into sim6_results.json ("summary") and prints markdown tables for sim6_README.md."""
import json, os

OUT = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(OUT, "sim6_results.json")
J = json.load(open(P))
runs = {r["case"]["name"]: r for r in J["runs"]}

OSC_PP = 0.050          # V, pp at TP5 in any flat window -> oscillation / limit cycle
TOL = 0.10              # rise/fall within 10 % of ideal
OS_EXTRA = 5.0          # %-points of step overshoot allowed above the ideal-R21 overshoot


def base_for(c):
    return runs.get(f"L0_C0_gnd_P0_CL{c['Cload']}")


def summarize(r):
    c = r["case"]
    s = dict(name=c["name"], L=c["L"], C=c["C"], housing=c["housing"], Cpar=c["Cpar"],
             Cload=c["Cload"], group=c["group"], tran_status=r["tran"]["status"],
             loop_status=r["loop"]["status"], tran_s=r["tran"]["seconds"], loop_s=r["loop"]["seconds"])
    m = r["tran"].get("metrics")
    b = base_for(c)
    bm = b["tran"].get("metrics") if b else None
    loop_part(s, r, b)
    if not m or not bm:
        s["error"] = r["tran"].get("metrics_error", "no transient metrics") + f" (tran status {r['tran']['status']})"
        s["ok"] = False
        return s
    worst = 0.0
    for k in ("rise_tp5", "fall_tp5", "rise_tp6", "fall_tp6"):
        tr, t0 = m[k]["tr"], bm[k]["tr"]
        s[k + "_us"] = tr * 1e6 if tr else None
        s[k + "_dpct"] = (tr / t0 - 1) * 100 if (tr and t0) else None
        if s[k + "_dpct"] is not None:
            worst = max(worst, abs(s[k + "_dpct"]))
        s[k + "_os_pct"] = m[k]["overshoot_pct"]
        s[k + "_settle_us"] = m[k]["settle_1pct"] * 1e6
        s[k + "_ring"] = (m[k]["ring_crossings"], m[k]["ring_freq"])
    s["worst_edge_dpct"] = worst
    s["timing_ok"] = worst <= TOL * 100 and all(s[k + "_dpct"] is not None for k in
                                                ("rise_tp5", "fall_tp5", "rise_tp6", "fall_tp6"))
    for k in ("sine_tp5_pp", "sine_tp6_pp", "sine_tp5_max", "sine_tp5_min", "sine_tp6_max", "sine_tp6_min"):
        s[k] = m[k]
        s[k + "_d"] = m[k] - bm[k]
    pps = dict(zero=m["zero_tp5_pp"], m140=m["dc_m140_pp"], p140=m["dc_p140_pp"],
               post_sstep=m["sstep_post_pp"])
    s["flat_pp_V"] = pps
    s["max_flat_pp_V"] = max(pps.values())
    ring = []
    for k in ("rise_tp5", "fall_tp5", "rise_tp6", "fall_tp6"):
        n, f = m[k]["ring_crossings"], m[k]["ring_freq"]
        if n >= 2:
            ring.append(f"{k}: {n} x-ings @ {f/1e6:.2f} MHz")
    for k in ("sstep_dn", "sstep_up"):
        n, f = m[k]["ring_crossings"], m[k]["ring_freq"]
        if n >= 2:
            ring.append(f"{k}: {n} x-ings @ {f/1e6:.2f} MHz")
        s[k + "_us"] = m[k]["tr"] * 1e6 if m[k]["tr"] else None
        s[k + "_os_pct"] = m[k]["overshoot_pct"]
    s["ringing"] = ring
    s["zero_peakfreq"] = m["zero_tp5_peakfreq"]
    s["stable_tran"] = s["max_flat_pp_V"] < OSC_PP and all(
        m[k]["settled_at_end"] for k in ("rise_tp5", "fall_tp5", "sstep_dn", "sstep_up"))
    s["p_r21_0V"] = m["dc_v0_p_r21"]; s["v_0V"] = m["dc_v0_v"]
    s["p_r21_m140"] = m["dc_m140_p_r21"]; s["v_m140"] = m["dc_m140_v"]
    s["vgs_max"] = m["gate_vgs_max"]
    s["os_ok"] = all(m[k]["overshoot_pct"] <= bm[k]["overshoot_pct"] + OS_EXTRA for k in ("rise_tp5", "fall_tp5"))
    s["zero_pp_V"] = m["zero_tp5_pp"]
    s["tp5_peak_rise"] = m["rise_tp5"]["v_to"] + m["rise_tp5"]["overshoot_pct"] / 100 * (m["rise_tp5"]["v_to"] - m["rise_tp5"]["v_from"])
    s["tp5_peak_fall"] = m["fall_tp5"]["v_to"] - m["fall_tp5"]["overshoot_pct"] / 100 * (m["fall_tp5"]["v_from"] - m["fall_tp5"]["v_to"])
    s["ok"] = bool(s["timing_ok"] and s["os_ok"] and s["stable_tran"])
    return s


def loop_part(s, r, b):
    lm = r["loop"].get("metrics")
    blm = b["loop"].get("metrics") if b else None
    if lm and "error" not in lm:
        for op in ("p140", "mid", "m140"):
            s[f"pm_{op}"] = lm[op].get("pm")
            s[f"fc_{op}_MHz"] = lm[op]["fc"] / 1e6 if lm[op].get("fc") else None
            s[f"gm_{op}_db"] = lm[op].get("gm_db")
            if blm and lm[op].get("pm") is not None and blm[op].get("pm") is not None:
                s[f"dpm_{op}"] = lm[op]["pm"] - blm[op]["pm"]
        s["pm_min"] = min(lm[op]["pm"] for op in ("p140", "mid", "m140") if lm[op].get("pm") is not None)
    else:
        s["loop_error"] = (lm or {}).get("error", r["loop"].get("metrics_error", "no loop metrics"))


S = [summarize(r) for r in J["runs"]]
J["summary"] = dict(criteria=dict(timing=f"|d(10-90%)| <= {TOL*100:.0f}% of ideal at TP5 and TP6, rise and fall",
                                  overshoot=f"TP5 large-step overshoot (rise and fall) <= ideal + {OS_EXTRA:.0f} %-points",
                                  stability=f"pp at TP5 < {OSC_PP*1000:.0f} mV in every flat window "
                                            "(zero-input 200 us, -140 V, +140 V, after small step) and all "
                                            "edges settled to 1 % inside their window"),
                    cases=S)
json.dump(J, open(P, "w"), indent=1)

f = lambda x, n=1: "n/a" if x is None else f"{x:.{n}f}"
by = {s["name"]: s for s in S}

print("### Run accounting")
nt = sum(1 for s in S if s["tran_status"] == "ok"); nl = sum(1 for s in S if s["loop_status"] == "ok")
print(f"cases {len(S)}; transient netlists ok {nt}/{len(S)}; loop netlists ok {nl}/{len(S)}; "
      f"non-ok: {[ (s['name'], s['tran_status'], s['loop_status']) for s in S if s['tran_status']!='ok' or s['loop_status']!='ok']}")
errs = [(s["name"], s.get("error"), s.get("loop_error")) for s in S if s.get("error") or s.get("loop_error")]
print(f"measurement errors: {errs}")
fails = [(r['case']['name'], r['tran']['meas_fail']) for r in J['runs'] if r['tran']['meas_fail']]
print(f".meas FAIL lines in logs: {fails}")
print()

b = by["L0_C0_gnd_P0_CL10p"]
print("### Ideal baseline (Cload 10p)")
print(f"rise TP5 {f(b['rise_tp5_us'],3)} us, fall TP5 {f(b['fall_tp5_us'],3)} us, rise TP6 {f(b['rise_tp6_us'],3)} us, "
      f"fall TP6 {f(b['fall_tp6_us'],3)} us; rise overshoot {f(b['rise_tp5_os_pct'],2)} %; settle(1%) rise "
      f"{f(b['rise_tp5_settle_us'],2)} us fall {f(b['fall_tp5_settle_us'],2)} us; sine TP5 pp {f(b['sine_tp5_pp'])} V "
      f"({f(b['sine_tp5_max'])}/{f(b['sine_tp5_min'])}), TP6 pp {f(b['sine_tp6_pp'])} V; "
      f"PM +140/0/-140 V = {f(b['pm_p140'])}/{f(b['pm_mid'])}/{f(b['pm_m140'])} deg at "
      f"{f(b['fc_p140_MHz'],2)}/{f(b['fc_mid_MHz'],2)}/{f(b['fc_m140_MHz'],2)} MHz; "
      f"P(R21) {f(b['p_r21_0V'],3)} W at {f(b['v_0V'],2)} V, {f(b['p_r21_m140'],3)} W at {f(b['v_m140'],2)} V")
b30 = by.get("L0_C0_gnd_P0_CL30p")
if b30:
    print(f"(Cload 30p ideal: rise TP5 {f(b30['rise_tp5_us'],3)} us, fall TP5 {f(b30['fall_tp5_us'],3)} us, "
          f"rise TP6 {f(b30['rise_tp6_us'],3)} us, fall TP6 {f(b30['fall_tp6_us'],3)} us, sine TP6 pp {f(b30['sine_tp6_pp'])} V)")
print()

LS = ["0", "1u", "10u", "50u", "200u"]; CS = ["0", "10p", "30p", "60p", "100p"]
for key, title in (("rise_tp5", "TP5 rise 10-90 %"), ("fall_tp5", "TP5 fall 10-90 %"),
                   ("rise_tp6", "TP6 rise 10-90 %"), ("fall_tp6", "TP6 fall 10-90 %")):
    print(f"### Grounded housing, Cload 10p: {title}, us (delta vs ideal)")
    print("| L \\ Ccase | " + " | ".join(CS) + " |")
    print("|---|" + "---|" * len(CS))
    for L in LS:
        row = []
        for C in CS:
            s = by.get(f"L{L}_C{C}_gnd_P0_CL10p")
            row.append("n/a" if not s or s.get(key + "_us") is None else
                       f"{s[key+'_us']:.3f} ({s[key+'_dpct']:+.1f} %)")
        print(f"| {L} | " + " | ".join(row) + " |")
    print()

print("### Grounded housing, Cload 10p: other metrics")
print("| L | Ccase | sine TP5 pp V (d) | sine TP6 pp V (d) | rise OS % | settle rise/fall us | "
      "max flat pp mV | ringing | PM min deg (dPM worst) | ok |")
print("|---|---|---|---|---|---|---|---|---|---|")
for L in LS:
    for C in CS:
        s = by.get(f"L{L}_C{C}_gnd_P0_CL10p")
        if not s or s.get("error"):
            print(f"| {L} | {C} | FAILED | | | | | | | |"); continue
        dpm = min(s.get(f"dpm_{op}", 0) or 0 for op in ("p140", "mid", "m140"))
        print(f"| {L} | {C} | {s['sine_tp5_pp']:.1f} ({s['sine_tp5_pp_d']:+.1f}) | {s['sine_tp6_pp']:.1f} "
              f"({s['sine_tp6_pp_d']:+.1f}) | {s['rise_tp5_os_pct']:.2f} | {s['rise_tp5_settle_us']:.2f} / "
              f"{s['fall_tp5_settle_us']:.2f} | {s['max_flat_pp_V']*1e3:.3f} | {'; '.join(s['ringing']) or 'none'} | "
              f"{f(s.get('pm_min'))} ({dpm:+.1f}) | {'yes' if s['ok'] else 'NO'} |")
print()

print("### Spot checks (floating housing, Cpar, Cload 30p) -- deltas vs ideal at the same Cload")
print("| case | rise/fall TP5 us (d %) | rise/fall TP6 us (d %) | sine TP6 pp V (d) | rise OS % | "
      "max flat pp mV | ringing | PM min deg | ok |")
print("|---|---|---|---|---|---|---|---|---|")
for s in S:
    if s["group"] in ("grid", "l_ext", "c_fine"):
        continue
    if s.get("error"):
        print(f"| {s['name']} | FAILED: {s['error']} | | | | | | | |"); continue
    print(f"| {s['name']} | {s['rise_tp5_us']:.3f} ({s['rise_tp5_dpct']:+.1f}) / {s['fall_tp5_us']:.3f} "
          f"({s['fall_tp5_dpct']:+.1f}) | {s['rise_tp6_us']:.3f} ({s['rise_tp6_dpct']:+.1f}) / {s['fall_tp6_us']:.3f} "
          f"({s['fall_tp6_dpct']:+.1f}) | {s['sine_tp6_pp']:.1f} ({s['sine_tp6_pp_d']:+.1f}) | "
          f"{s['rise_tp5_os_pct']:.2f} | {s['max_flat_pp_V']*1e3:.3f} | {'; '.join(s['ringing']) or 'none'} | "
          f"{f(s.get('pm_min'))} | {'yes' if s['ok'] else 'NO'} |")
print()
for grp, title in (("l_ext", "Extension: large inductance (grounded, Cload 10p)"),
                   ("c_fine", "Extension: Ccase threshold (grounded)")):
    print(f"### {title}")
    print("| case | rise/fall TP5 us (d %) | rise/fall TP6 d % | TP5 overshoot rise/fall % | TP5 peak on rise / fall V | "
          "settle rise/fall us | sine TP5 max/min V | zero-input pp mV | ringing | PM min deg | ok |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    rows = [s for s in S if s["group"] == grp]
    if grp == "l_ext":
        rows = [by[n] for n in ("L0_C0_gnd_P0_CL10p", "L200u_C0_gnd_P0_CL10p", "L0_C30p_gnd_P0_CL10p",
                                "L200u_C30p_gnd_P0_CL10p")] + rows
    for s in rows:
        if s.get("error"):
            print(f"| {s['name']} | FAILED: {s['error']} |||||||||| NO |"); continue
        print(f"| {s['name']} | {s['rise_tp5_us']:.3f} ({s['rise_tp5_dpct']:+.1f}) / {s['fall_tp5_us']:.3f} "
              f"({s['fall_tp5_dpct']:+.1f}) | {s['rise_tp6_dpct']:+.1f} / {s['fall_tp6_dpct']:+.1f} | "
              f"{s['rise_tp5_os_pct']:.1f} / {s['fall_tp5_os_pct']:.1f} | {s['tp5_peak_rise']:.1f} / {s['tp5_peak_fall']:.1f} | "
              f"{s['rise_tp5_settle_us']:.2f} / {s['fall_tp5_settle_us']:.2f} | {s['sine_tp5_max']:.1f} / {s['sine_tp5_min']:.1f} | "
              f"{s['zero_pp_V']*1e3:.3f} | {'; '.join(s['ringing']) or 'none'} | {f(s.get('pm_min'))} | "
              f"{'yes' if s['ok'] else 'NO'} |")
    print()
print("### Loop gain (U7 loop, Middlebrook double injection): PM deg / fc MHz at TP5 = +140 / 0 / -140 V")
print("| case | PM +140 | PM 0 | PM -140 | fc +140 | fc 0 | fc -140 |")
print("|---|---|---|---|---|---|---|")
for n in ("L0_C0_gnd_P0_CL10p", "L0_C30p_gnd_P0_CL10p", "L0_C100p_gnd_P0_CL10p", "L200u_C0_gnd_P0_CL10p",
          "L200u_C100p_gnd_P0_CL10p", "L200u_C100p_flt_P0_CL10p", "L200u_C100p_gnd_P3p_CL10p",
          "L1u_C100p_gnd_P0_CL10p", "L5m_C0_gnd_P0_CL10p", "L5m_C30p_gnd_P0_CL10p",
          "L0_C0_gnd_P0_CL30p", "L200u_C100p_gnd_P0_CL30p", "L200u_C100p_gnd_P3p_CL30p"):
    s = by.get(n)
    if not s:
        continue
    print(f"| {n} | {f(s.get('pm_p140'))} | {f(s.get('pm_mid'))} | {f(s.get('pm_m140'))} | {f(s.get('fc_p140_MHz'),2)} | "
          f"{f(s.get('fc_mid_MHz'),2)} | {f(s.get('fc_m140_MHz'),2)} |")
gms = [s.get(f"gm_{op}_db") for s in S for op in ("p140", "mid", "m140") if s.get(f"gm_{op}_db") is not None]
print(f"gain margin: phase reached -180 deg below 300 MHz in {len(gms)} of {3*len(S)} op points"
      + (f"; min GM {min(gms):.1f} dB" if gms else ""))
print()
print("### R21 power (DC)")
for s in S:
    if s["name"] in ("L0_C0_gnd_P0_CL10p", "L200u_C100p_gnd_P0_CL10p", "L200u_C100p_flt_P0_CL10p"):
        print(f"{s['name']}: {s['p_r21_0V']:.3f} W at {s['v_0V']:.2f} V; {s['p_r21_m140']:.3f} W at {s['v_m140']:.2f} V")
pw = [s["p_r21_m140"] for s in S if "p_r21_m140" in s]
p0 = [s["p_r21_0V"] for s in S if "p_r21_0V" in s]
print(f"all cases: P(0V) {min(p0):.3f}..{max(p0):.3f} W, P(-140V) {min(pw):.3f}..{max(pw):.3f} W")
print()
print("### Stability extremes over all cases")
print(f"max flat-window pp at TP5: {max(s['max_flat_pp_V'] for s in S if 'max_flat_pp_V' in s)*1e3:.3f} mV; "
      f"cases with any ringing (>=2 hysteresis crossings): {[ (s['name'], s['ringing']) for s in S if s.get('ringing')]}")
print(f"min PM over all cases/op points: {min(s['pm_min'] for s in S if s.get('pm_min') is not None):.1f} deg; "
      f"worst dPM: {min(min(s.get(f'dpm_{op}', 0) or 0 for op in ('p140','mid','m140')) for s in S):.2f} deg")
print(f"max Vgs: {max(s['vgs_max'] for s in S if 'vgs_max' in s):.2f} V")
print(f"failing cases: {[s['name'] for s in S if not s.get('ok')]}")
