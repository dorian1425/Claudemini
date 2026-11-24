#!/usr/bin/env python3
"""A/B harness: does delegating to Gemini save Opus tokens?

Condition A (solo):     Claude Code alone, no MCP servers.
Condition B (delegate): Claude Code + the gemini-cli MCP (Gemini 4 Neon via agy),
                        following the global ~/.claude/CLAUDE.md rules.

Both conditions get the same prompt, the same working directory, the same
read-only tool allowance, and the same global CLAUDE.md (so its overhead is
paid equally). Each run is a fresh `claude -p` session.

Usage:
  python3 run.py                       # all tasks, both conditions, 1 rep
  python3 run.py --tasks E1 R1 --reps 3
  python3 run.py --conditions B --tasks E4
  python3 run.py --summary             # only rebuild results/summary.md
"""
import argparse, csv, json, os, pathlib, re, shutil, statistics, subprocess, sys, time

ROOT = pathlib.Path(__file__).resolve().parent
TASKS = ROOT / "tasks"
RES = ROOT / "results"
RAW = RES / "raw"
CSV = RES / "runs.csv"

GEMINI_MCP = {
    "mcpServers": {
        "gemini-cli": {
            "command": "node",
            "args": [str(pathlib.Path.home() / "mcp/gemini-mcp-tool/dist/index.js")],
            "env": {
                "GEMINI_MCP_BACKEND": "agy",
                "AGY_CLI_PATH": str(pathlib.Path.home() / ".local/bin/agy"),
                "GEMINI_DELEGATED": "1",
            },
        }
    }
}
READ_TOOLS = ["Read", "Grep", "Glob", "Bash(ls:*)", "Bash(wc:*)", "Bash(pdftotext:*)"]
WRITE_TOOLS = ["Edit", "Write"]
GEMINI_TOOLS = ["mcp__gemini-cli__ask-gemini", "mcp__gemini-cli__fetch-chunk",
                "mcp__gemini-cli__brainstorm"]
FIELDS = ["task", "condition", "rep", "ok", "cost_usd", "input_tokens",
          "cache_creation_tokens", "cache_read_tokens", "output_tokens",
          "in_total", "neutral_tokens",
          "num_turns", "duration_s", "gemini_calls", "answer_file"]
# Cache-neutral cost proxy: every input token at full price, output at 5x
# (Claude's output/input price ratio). Unaffected by which run warmed the cache.
OUT_WEIGHT = 5
RUN_CAP = 1.5  # per-run Claude spend cap (USD); overridden by --run-cap


def parse_task(path):
    """tasks/X.md: front matter (key: value lines) between '---', then the prompt.
    Everything after a line '## Rubric' is for graders and is never sent."""
    text = path.read_text()
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    meta = dict(l.split(":", 1) for l in m.group(1).splitlines() if ":" in l)
    meta = {k.strip(): v.strip() for k, v in meta.items()}
    prompt = m.group(2).split("\n## Rubric", 1)[0].strip()
    return meta, prompt


def run_one(task_id, cond, rep):
    meta, prompt = parse_task(TASKS / f"{task_id}.md")
    workdir = (ROOT / meta["workdir"]).resolve()
    if meta.get("fresh_copy") == "yes":  # write tasks get a throwaway copy
        tmp = RES / "work" / f"{task_id}-{cond}-{rep}"
        shutil.rmtree(tmp, ignore_errors=True)
        shutil.copytree(workdir, tmp)
        workdir = tmp
    tools = READ_TOOLS + (WRITE_TOOLS if meta.get("writes") == "yes" else [])
    cmd = ["claude", "-p", prompt, "--model", "opus", "--output-format", "stream-json", "--verbose",
           "--no-session-persistence", "--strict-mcp-config",
           "--permission-mode", "default", "--max-budget-usd", str(RUN_CAP)]
    if cond == "B":
        cfg = RES / "gemini-mcp.json"
        cfg.write_text(json.dumps(GEMINI_MCP))
        cmd += ["--mcp-config", str(cfg)]
        tools = tools + GEMINI_TOOLS
    cmd += ["--allowedTools", *tools]
    if meta.get("writes") != "yes":
        cmd += ["--disallowedTools", *WRITE_TOOLS]

    env = {k: v for k, v in os.environ.items() if k not in ("GEMINI_DELEGATED", "ASK_CLAUDE_ACTIVE")}
    t0 = time.time()
    p = subprocess.run(cmd, cwd=workdir, capture_output=True, text=True, env=env,
                       timeout=int(meta.get("timeout_s", 1800)))
    dur = time.time() - t0
    RAW.mkdir(parents=True, exist_ok=True)
    stem = f"{task_id}-{cond}-r{rep}"
    (RAW / f"{stem}.jsonl").write_text(p.stdout or "")
    if p.stderr:
        (RAW / f"{stem}.stderr.txt").write_text(p.stderr)
    j, calls = {}, 0
    for line in (p.stdout or "").splitlines():
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if ev.get("type") == "result":
            j = ev
        elif ev.get("type") == "assistant":
            for blk in ev.get("message", {}).get("content", []) or []:
                if blk.get("type") == "tool_use" and blk.get("name", "").startswith("mcp__gemini-cli__"):
                    calls += 1
    u = j.get("usage", {}) or {}
    answer = j.get("result", "") or ""
    ans_file = RAW / f"{stem}.answer.md"
    ans_file.write_text(answer)
    in_total = sum(int(u.get(k) or 0) for k in
                   ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))
    out_tok = int(u.get("output_tokens") or 0)
    row = {
        "task": task_id, "condition": cond, "rep": rep,
        "ok": int(p.returncode == 0 and not j.get("is_error", False)),
        "cost_usd": j.get("total_cost_usd", ""),
        "input_tokens": u.get("input_tokens", ""),
        "cache_creation_tokens": u.get("cache_creation_input_tokens", ""),
        "cache_read_tokens": u.get("cache_read_input_tokens", ""),
        "output_tokens": u.get("output_tokens", ""),
        "in_total": in_total if u else "",
        "neutral_tokens": in_total + OUT_WEIGHT * out_tok if u else "",
        "num_turns": j.get("num_turns", ""),
        "duration_s": round(dur, 1),
        "gemini_calls": calls,
        "answer_file": str(ans_file.relative_to(ROOT)),
    }
    new = not CSV.exists()
    with CSV.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerow(row)
    print(f"{stem}: ok={row['ok']} cost=${row['cost_usd']} out={row['output_tokens']} "
          f"turns={row['num_turns']} gemini_calls={calls} {row['duration_s']}s", flush=True)
    return row


def summarize():
    if not CSV.exists():
        print("no runs yet"); return
    rows = [r for r in csv.DictReader(CSV.open()) if r["ok"] == "1" and r.get("neutral_tokens")]
    tasks = sorted({r["task"] for r in rows})
    def med(task, cond, key):
        v = [float(r[key]) for r in rows if r["task"] == task and r["condition"] == cond and r.get(key)]
        return statistics.median(v) if v else None
    f = lambda x, d=0: "—" if x is None else f"{x:,.{d}f}"
    out = ["# Results", "",
           "Primary metric: **neutral tokens** = all input tokens (fresh + cache write + cache read) "
           f"+ {OUT_WEIGHT} × output tokens, median over successful reps. It ignores which run happened "
           "to warm the prompt cache. `$` is Claude's billed-equivalent cost and IS cache-sensitive. "
           "Gemini usage is not included — it runs on your Antigravity quota.", "",
           "| Task | A neutral | B neutral | B/A | A out | B out | A $ | B $ | B gemini calls | A time | B time |",
           "|---|---|---|---|---|---|---|---|---|---|---|"]
    tot = {"A": 0.0, "B": 0.0}
    for t in tasks:
        a, b = med(t, "A", "neutral_tokens"), med(t, "B", "neutral_tokens")
        if a and b:
            tot["A"] += a; tot["B"] += b
        ratio = f"{b / a:.2f}" if a and b else "—"
        out.append(f"| {t} | {f(a)} | {f(b)} | {ratio} | {f(med(t,'A','output_tokens'))} | "
                   f"{f(med(t,'B','output_tokens'))} | {f(med(t,'A','cost_usd'),3)} | {f(med(t,'B','cost_usd'),3)} | "
                   f"{f(med(t,'B','gemini_calls'))} | {f(med(t,'A','duration_s'))}s | {f(med(t,'B','duration_s'))}s |")
    if tot["A"]:
        out += ["", f"**Paired total (neutral tokens):** A {tot['A']:,.0f} vs B {tot['B']:,.0f} "
                    f"→ B/A = {tot['B'] / tot['A']:.2f}"]
    (RES / "summary.md").write_text("\n".join(out) + "\n")
    print("\n".join(out))


def spent():
    if not CSV.exists():
        return 0.0
    return sum(float(r["cost_usd"] or 0) for r in csv.DictReader(CSV.open()))


def main():
    global RUN_CAP
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", nargs="*")
    ap.add_argument("--conditions", nargs="*", default=["A", "B"])
    ap.add_argument("--reps", type=int, default=1)
    ap.add_argument("--rep-start", type=int, default=1)
    ap.add_argument("--budget", type=float, default=10.0,
                    help="stop before a run that could push total Claude spend past this (USD)")
    ap.add_argument("--run-cap", type=float, default=RUN_CAP)
    ap.add_argument("--summary", action="store_true")
    a = ap.parse_args()
    RUN_CAP = a.run_cap
    if a.summary:
        summarize(); return
    ids = a.tasks or sorted(p.stem for p in TASKS.glob("*.md"))
    for rep in range(a.rep_start, a.rep_start + a.reps):
        for t in ids:
            # alternate condition order per rep to spread cache/time effects
            conds = a.conditions if rep % 2 else list(reversed(a.conditions))
            if spent() + 2 * RUN_CAP > a.budget:  # need room for the whole A/B pair
                print(f"budget stop before {t} r{rep}: spent ${spent():.2f} of ${a.budget:.2f}", flush=True)
                summarize(); return
            for c in conds:
                try:
                    run_one(t, c, rep)
                except subprocess.TimeoutExpired:
                    print(f"{t}-{c}-r{rep}: TIMEOUT", flush=True)
    summarize()


if __name__ == "__main__":
    main()
