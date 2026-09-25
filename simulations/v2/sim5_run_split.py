"""Sim 5 (finished by hand): run each R29 x Vto x x2 combination as its own netlist
with a hard timeout, so one non-converging combination cannot block the rest."""
import re, os, subprocess, time, json, itertools
from concurrent.futures import ThreadPoolExecutor

SRC = r"C:\Users\lawre\OneDrive\Desktop\pister_project\hvawg\simulations\v2\sim5_r29_sweep.cir"
MOD = "C:/Users/lawre/OneDrive/Desktop/pister_project/hvawg/simulations/LM8261.MOD"
LT = r"C:\Users\lawre\AppData\Local\Programs\ADI\LTspice\LTspice.exe"
OUT = os.path.dirname(os.path.abspath(__file__))
TIMEOUT = 120

base = open(SRC, encoding="utf-8").read()
base = base.replace(".include ../LM8261.MOD", ".include " + MOD)

R29 = ["100k", "470k", "1Meg", "2.2Meg", "1e12"]
VTO = ["-2", "-3", "-4"]
X2 = ["290", "500"]

def make(r, v, x):
    s = re.sub(r"^\.step param r29v list.*$", f".param r29v={r}", base, flags=re.M)
    s = re.sub(r"^\.step param vtq3 list.*$", f".param vtq3={v}", s, flags=re.M)
    s = re.sub(r"^\.step param x2 list.*$", f".param x2={x}", s, flags=re.M)
    name = f"r{r}_v{v.lstrip('-')}_x{x}"
    path = os.path.join(OUT, name + ".cir")
    open(path, "w", encoding="utf-8").write(s)
    return name, path

meas_re = re.compile(r"^(\w+):\s.*?=\s*([-+\d.eE]+)", re.M)

def run(job):
    name, path = job
    log = path[:-4] + ".log"
    for ext in (".log", ".raw", ".op.raw"):
        try: os.remove(path[:-4] + ext)
        except FileNotFoundError: pass
    t0 = time.time()
    p = subprocess.Popen([LT, "-b", path])
    try:
        p.wait(timeout=TIMEOUT)
        status = "ok"
    except subprocess.TimeoutExpired:
        p.kill(); p.wait()
        status = "TIMEOUT"
    dt = time.time() - t0
    res = {}
    if os.path.exists(log) and os.path.getmtime(log) >= t0:      # freshness check
        raw = open(log, "rb").read()
        txt = raw.decode("utf-16-le", errors="ignore") if b"\x00" in raw[:200] else raw.decode("latin-1")
        res = {k.lower(): float(v) for k, v in meas_re.findall(txt)}
        fails = re.findall(r"Measurement \"?(\w+)\"? FAIL", txt, re.I)
        if fails: res["_fail"] = fails
    elif status == "ok":
        status = "NO FRESH LOG"
    for ext in (".raw", ".op.raw"):
        try: os.remove(path[:-4] + ext)
        except FileNotFoundError: pass
    with open(os.path.join(OUT, "progress.txt"), "a") as f:
        f.write(f"{time.strftime('%H:%M:%S')} {name} {status} {dt:.1f}s\n")
    return name, status, round(dt, 1), res

jobs = [make(r, v, x) for r, v, x in itertools.product(R29, VTO, X2)]
with ThreadPoolExecutor(max_workers=4) as ex:
    results = list(ex.map(run, jobs))
json.dump(results, open(os.path.join(OUT, "results.json"), "w"), indent=1)
ok = sum(1 for _, s, _, r in results if s == "ok" and "rca" in r)
print(f"done: {ok}/{len(results)} runs produced centering results")
