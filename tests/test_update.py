import importlib.util, json, re, sys, os, tempfile, datetime as dt
TMP = tempfile.mkdtemp()
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ["STATS_TOKEN"] = "x"; os.environ["ANTHROPIC_API_KEY"] = "k"
spec = importlib.util.spec_from_file_location("u", os.path.join(ROOT, "scripts", "update.py"))
u = importlib.util.module_from_spec(spec); spec.loader.exec_module(u)
NOW, UTC = u.NOW, u.UTC
today = NOW.replace(hour=0, minute=0, second=0)
def daily(fn, ndays=500):  # {day: stars}
    return {today - dt.timedelta(days=i): fn(i) for i in range(ndays) if fn(i)}
REPOS = {  # name: (created_days_ago, forks, daily fn, desc)
  "a/rising":  (10, 50,  lambda i: [400, 300, 100, 20][i] if i < 4 else 0, "new agent framework"),
  "b/peaked":  (40, 400, lambda i: 2000 if 5 <= i <= 7 else 30, "llm toolkit"),
  "c/steady":  (900, 900, lambda i: 60, "web framework"),
  "d/oldgiant":(2000, 9000, lambda i: 150 if i < 200 else 10, "database"),
  "e1234/farm":(5, 0, lambda i: 500 if i < 2 else 0, "free download"),
}
H = {n: daily(fn, created) for n, (created, f, fn, d) in REPOS.items()}
def weeks(h):  # newest-first weekly buckets starting Sunday
    out = {}
    for day, v in h.items():
        start = day - dt.timedelta(days=(day.weekday() + 1) % 7)
        out.setdefault(start, [0]*7)[(day.weekday() + 1) % 7] += v
    return [{"week": int(k.timestamp()), "total": sum(v), "days": v} for k, v in sorted(out.items(), reverse=True)]
calls = {"hist": 0, "haiku": 0}
def fake(url, data=None, headers=None, tries=6):
    if "anthropic" in url:
        calls["haiku"] += 1
        n = len(json.loads(data)["messages"][0]["content"].split("\n"))
        return 200, {}, json.dumps({"content": [{"type": "tool_use", "input": {"labels": [{"i": j, "k": ["ai"]} for j in range(n)]}}]}).encode()
    if "graphql" in url:
        q = json.loads(data)["query"]; out = {}
        for m in re.finditer(r'r(\d+): repository\(owner:"(.*?)", name:"(.*?)"\)', q):
            n = m.group(2) + "/" + m.group(3); c, f, fn, d = REPOS[n]
            out["r" + m.group(1)] = {"nameWithOwner": n, "description": d, "primaryLanguage": {"name": "Python"}, "createdAt": u.iso(NOW - dt.timedelta(days=c)),
                "forkCount": f, "isFork": False, "isArchived": False, "isPrivate": False, "homepageUrl": "", "stargazerCount": sum(H[n].values()), "repositoryTopics": {"nodes": []}}
        return 200, {}, json.dumps({"data": out}).encode()
    if "/search/" in url:
        page = int(re.search(r"[?&]page=(\d+)", url).group(1))
        return 200, {}, json.dumps({"items": [{"full_name": n} for n in REPOS] if page == 1 else []}).encode()
    m = re.search(r"/repos/(\w+/\w+)/stargazers/history\?page=(\d+)", url)
    if m:
        calls["hist"] += 1; w = weeks(H[m.group(1)]); p = int(m.group(2))
        return 200, {"x-ratelimit-remaining": "4000"}, json.dumps(w[(p-1)*30:p*30]).encode()
    return 404, {}, b""
u.http = fake; u.time.sleep = lambda s: None
def run(argv, prev=None):
    if prev: json.dump(prev, open(os.path.join(TMP, "prev.json"), "w"))
    sys.argv = ["x", "--out", os.path.join(TMP, "d.json")] + (["--prev", os.path.join(TMP, "prev.json")] if prev else []) + argv
    u.main(); return json.load(open(os.path.join(TMP, "d.json")))
def truth(n, key):
    h = H[n]
    if key == "ytd": start = dt.datetime(today.year, 1, 1, tzinfo=UTC)
    else: start = today - dt.timedelta(days={"today":1,"3d":3,"7d":7,"14d":14,"1mo":30,"3mo":90,"1y":365}[key] - 1)
    return sum(v for d, v in h.items() if d >= start)
d1 = run(["--long", "--labels"])
names = sorted(r["n"] for r in d1["repos"])
bad = [(r["n"], k, v, truth(r["n"], k)) for r in d1["repos"] for k, v in r["g"].items() if v != truth(r["n"], k)]
hot = [r["n"] for r in sorted(d1["repos"], key=lambda r: -r["hot"])]
d7 = [r["n"] for r in sorted(d1["repos"], key=lambda r: -r["g"].get("7d", 0))]
print("hot order:", hot); print("7d order:", d7)

def check(name, ok):
    print(("ok   " if ok else "FAIL ") + name)
    if not ok: check.failed += 1
check.failed = 0
check("star-farmed spam repo is filtered", "e1234/farm" not in names)
check("every window count matches the ground truth from daily data", not bad)
check("hot score favors a repo climbing now over one that peaked last week", hot.index("a/rising") < hot.index("b/peaked"))
check("7d ranking favors the repo with the most stars gained in 7 days", d7[0] == "b/peaked")
check("labels were produced on a manual run", len(d1["labels"]) == len(names))

calls.update(hist=0, haiku=0)
d2 = run([], prev=d1)
check("scheduled run never calls Claude", calls["haiku"] == 0)
check("scheduled run carries 1y numbers over", {r["n"]: r["g"].get("1y") for r in d2["repos"]} == {r["n"]: r["g"].get("1y") for r in d1["repos"]})
check("scheduled run keeps the YTD as_of stamp", [w["as_of"] for w in d2["windows"] if w["key"] == "ytd"] == [w["as_of"] for w in d1["windows"] if w["key"] == "ytd"])
sys.exit(1 if check.failed else 0)
