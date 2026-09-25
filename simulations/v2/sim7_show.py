"""Print selected SIM 7 results from sim7_results.json.  Usage: python sim7_show.py <substring> [keys...]"""
import json, sys, os
R = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "sim7_results.json")))
sub = sys.argv[1] if len(sys.argv) > 1 else ""
keys = sys.argv[2:]
for name in sorted(R):
    if sub not in name:
        continue
    r = R[name]
    m = r["meas"]
    sel = {k: m[k] for k in keys if k in m} if keys else {k: v for k, v in m.items() if k != "_steps"}
    def f(v):
        return f"{v:.5g}" if isinstance(v, float) else str(v)
    print(f"{name} [{r['status']} {r['t']}s] fails={r['fails'][:6]}{' err=' + r['err'][:120] if r['err'] else ''}")
    print("   " + "  ".join(f"{k}={f(v)}" for k, v in sel.items()))
