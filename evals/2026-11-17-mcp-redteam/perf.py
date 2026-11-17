"""Hard-core performance and robustness run for money_atlas_mcp."""
import json, math, os, random, resource, statistics as st, subprocess, sys, tempfile, time
from pathlib import Path
REPO = Path(sys.argv[1]); sys.path.insert(0, str(REPO))
from money_atlas_mcp import analytics
from money_atlas_mcp.paper import PaperLedger, RiskError
out = {}
rng = random.Random(7)

# 1) independent ATR reference (Wilder via explicit recursion on a list, written differently)
def atr_ref(h, l, c, n):
    tr = [max(h[i]-l[i], abs(h[i]-c[i-1]), abs(l[i]-c[i-1])) for i in range(1, len(c))]
    a = [None]*len(tr); a[n-1] = sum(tr[:n])/n
    for i in range(n, len(tr)): a[i] = a[i-1] + (tr[i]-a[i-1])/n
    return a[-1]
worst = 0.0
for trial in range(300):
    n = rng.randint(15, 3000); p = 100.0; bars = []
    for i in range(n):
        p *= math.exp(rng.gauss(0, 0.02)); hi = p*(1+abs(rng.gauss(0, .01))); lo = p*(1-abs(rng.gauss(0, .01)))
        bars.append({"t": str(i), "o": p, "h": hi, "l": lo, "c": p})
    a = analytics.atr(bars, 14); r = atr_ref([b["h"] for b in bars], [b["l"] for b in bars], [b["c"] for b in bars], 14)
    worst = max(worst, abs(a-r)/r)
out["atr_vs_reference_max_rel_error"] = worst

# 2) position_size property test
bad = 0
for _ in range(20000):
    acct = 10**rng.uniform(2, 8); rp = rng.uniform(0.01, 5); e = 10**rng.uniform(-2, 5); s = e*(1+rng.choice([-1, 1])*rng.uniform(1e-4, .3))
    p = analytics.position_size(acct, rp, e, s)
    if abs(p["units"]*abs(e-s) - acct*rp/100) > 1e-6*acct: bad += 1
out["position_size_property_violations_of_20000"] = bad

# 3) stdio server: latency, throughput, memory, fuzz
FX = REPO/"money_atlas_mcp/fixtures/sample.json"
env = dict(os.environ, MONEY_ATLAS_FIXTURES=str(FX), MONEY_ATLAS_HOME=tempfile.mkdtemp())
proc = subprocess.Popen([sys.executable, "-u", str(REPO/"money_atlas_mcp/server.py")], stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, env=env, bufsize=1)
def rt(msg):
    t = time.perf_counter(); proc.stdin.write(json.dumps(msg)+"\n"); proc.stdin.flush()
    line = proc.stdout.readline(); return time.perf_counter()-t, json.loads(line)
rt({"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}})
def bench(name, args, n):
    ls = []
    for i in range(n):
        d, r = rt({"jsonrpc": "2.0", "id": i+1, "method": "tools/call", "params": {"name": name, "arguments": args}})
        assert r["id"] == i+1 and "result" in r, r
        ls.append(d*1000)
    ls.sort()
    return {"n": n, "p50_ms": round(ls[n//2], 3), "p95_ms": round(ls[int(n*.95)], 3), "p99_ms": round(ls[int(n*.99)], 3),
            "throughput_per_s": round(n/ (sum(ls)/1000), 1)}
out["get_quote"] = bench("get_quote", {"symbol": "BTCUSDT"}, 5000)
out["market_snapshot_60_bars"] = bench("market_snapshot", {"symbol": "XAUUSD"}, 2000)
out["position_size"] = bench("position_size", {"account": 500000, "risk_pct": 1, "entry": 4310, "stop": 4250}, 5000)
# fuzz: random structures; every message with an id must get exactly one reply, and the server must stay alive
def junk(depth=0):
    k = rng.random()
    if depth > 2 or k < .3: return rng.choice([None, True, 0, -1, 1e308, float("nan") if False else 3.14, "x"*rng.randint(0, 50), "ทอง", []])
    if k < .6: return [junk(depth+1) for _ in range(rng.randint(0, 3))]
    return {rng.choice(["name", "arguments", "symbol", "qty", "limit", "id", "x"]): junk(depth+1) for _ in range(rng.randint(0, 4))}
names = ["get_quote", "get_candles", "get_macro_series", "market_snapshot", "position_size", "paper_propose_order", "paper_orders", "nope"]
replies = 0; t0 = time.perf_counter(); N = 20000
for i in range(N):
    m = {"jsonrpc": "2.0", "id": 100000+i, "method": rng.choice(["tools/call", "tools/call", "tools/list", "ping", "x"]),
         "params": rng.choice([{"name": rng.choice(names), "arguments": junk()}, junk()])}
    proc.stdin.write(json.dumps(m)+"\n"); proc.stdin.flush()
    r = json.loads(proc.stdout.readline()); assert r["id"] == 100000+i; replies += 1
out["fuzz"] = {"messages": N, "replies": replies, "server_alive": proc.poll() is None, "seconds": round(time.perf_counter()-t0, 2)}
rss_kb = int(open(f"/proc/{proc.pid}/status").read().split("VmHWM:")[1].split()[0])
out["server_peak_rss_mb"] = round(rss_kb/1024, 1)
proc.stdin.close(); proc.wait(timeout=10)

# 4) market_snapshot on long histories (in-process)
for n in (100, 1000, 5000):
    bars = [{"t": str(i), "o": 1, "h": 1+math.sin(i/7)+2, "l": 1+math.sin(i/7), "c": 1+math.sin(i/7)+1, "v": 1} for i in range(n)]
    t = time.perf_counter(); [analytics.snapshot({"symbol": "X", "interval": "1d", "bars": bars, "as_of": "x", "source": "s"}) for _ in range(20)]
    out[f"snapshot_{n}_bars_ms"] = round((time.perf_counter()-t)/20*1000, 2)

# 5) ledger scale and multi-process concurrency
d = Path(tempfile.mkdtemp()); led = PaperLedger(d); s = led.load(); s["limits"]["max_open_positions"] = 10**6; led.save(s)
for target in (100, 1000, 3000):
    while len(led.load()["orders"]) < target - 1: led.propose("XAUUSD", "buy", 0.01, 4300, 4260, None, "")
    t = time.perf_counter(); led.propose("XAUUSD", "buy", 0.01, 4300, 4260, None, ""); out[f"propose_at_{target}_orders_ms"] = round((time.perf_counter()-t)*1000, 2)
d2 = Path(tempfile.mkdtemp()); led2 = PaperLedger(d2); s = led2.load(); s["limits"]["max_open_positions"] = 10**6; led2.save(s)
code = f"import sys; sys.path.insert(0, {str(REPO)!r}); from money_atlas_mcp.paper import PaperLedger; from pathlib import Path\nfor _ in range(50): PaperLedger(Path({str(d2)!r})).propose('XAUUSD','buy',0.01,4300,4260,None,'')"
procs = [subprocess.Popen([sys.executable, "-c", code]) for _ in range(8)]; [p.wait() for p in procs]
out["concurrency_8_processes_x_50"] = {"expected": 400, "stored": len(PaperLedger(d2).load()["orders"]),
                                       "all_exit_0": all(p.returncode == 0 for p in procs)}
json.dump(out, open(sys.argv[2], "w"), indent=1); print(json.dumps(out, indent=1))
