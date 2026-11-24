# Experiment Report: Does Delegating to Gemini 4 Save Opus Tokens?

Date: 2026-11-24 · Claude Code (Opus 5.5) + Antigravity CLI 1.5.16 (gemini-4-neon-high) · Experiment spend: $7.08 (Claude billing equivalent)

## Conclusions

1. **Document reading saves tokens, and saves a lot.** Once the rules were written properly (v3), Claude delegated papers to Gemini on its own:
   extracting data from a 75-page paper **saved 40%**, and comparing three papers **saved 62%**, with no change in accuracy.
2. **Code reading does not save tokens.** Claude Code already relies on Grep and targeted reads. On codebase tasks, delegating vs. working solo stayed within random variance (±20%), so coding tasks stay on Opus.
3. **Rule wording decides the outcome.** With the same tools, v1 rules cost 17% more (Claude re-read the files itself after asking Gemini); v2 rules caused Claude not to delegate at all. Only v3 ("always pass document paths to Gemini and do not re-read them") produced real savings.
4. **Trade-off: slower.** Delegated tasks took 1.5–3× as long as solo runs (Gemini needed 1–2 minutes to read PDFs) and used Antigravity quota (not measured in this experiment).
5. **Writing tasks:** When the full text must be returned in the reply, delegation does not save tokens (Claude still has to output the entire text) and can only improve prose style. Whether the writing is better is pending blind review (see [experiment/blind/](experiment/blind/)).

## Experimental design

- **Condition A**: Claude Code solo, with no MCP servers.
- **Condition B**: Claude Code + gemini-cli MCP, deciding on its own whether to delegate according to `~/.claude/CLAUDE.md`.
- Both conditions had identical prompts, working directories, read-only tool permissions, and global CLAUDE.md. Each run was a fresh `claude -p` session.
- **Primary metric: "neutral tokens"** = all input tokens (fresh input + cache write + cache read) + 5 × output tokens.
  Unaffected by prompt-cache ordering. Pilot runs showed that whichever condition ran first warmed the cache for the second, shifting dollar cost by up to 2×, so dollar cost alone is not enough.
- 7 real-world tasks (see [experiment/README.md](experiment/README.md)):
  - Engineering: E1 trace the requests call chain, E2 locate a planted bug, E3 write a technical explanation, E4 rename a function (control)
  - Research: R1 compare three papers, R2 extract numbers from the 75-page GPT-3 paper, R3 write a general-audience explainer
- Ground-truth answers for R1 and R2 were verified item by item against the original papers (the WMT14 Fr→En SOTA of 45.6 initially written from memory was wrong; it should be 35.0).

The tasks were originally posed in Chinese, so the model answers in experiment/results/raw/ and experiment/blind/ are in Chinese; they are kept verbatim as recorded data.

## Results

B/A < 1 means delegation saved tokens. Each cell was run once; single runs have roughly ±20% random variance.

### Rule v3 (final): document reading

| Task | A neutral tokens | B neutral tokens | B/A | A USD | B USD | Gemini calls | Accuracy A / B | Time A / B |
|---|---|---|---|---|---|---|---|---|
| R2 75-page paper extraction | 213,976 | 127,668 | **0.60** | $0.222 | $0.190 | 1 | 9/9 · 9/9 | 34s · 107s |
| R1 three-paper comparison | 462,770 | 178,078 | **0.38** | $0.428 | $0.236 | 1 | 8/10 · 8/10 | 80s · 123s |

Forced delegation (the prompt required using Gemini, as an ideal-case reference): R2 0.59 (9/9), R1 0.29 (10/10).

Dollar cost dropped less than neutral tokens (R2 −15%, R1 −45%) because every run includes a large fixed system prompt billed at cached-input rates.

### Code tasks (across rule versions; Condition B did not delegate or gained nothing)

| Task | Rules | Gemini calls | B/A | Accuracy |
|---|---|---|---|---|
| E1 call-chain trace | v1 | 1 | 1.05 | Both 5/5 |
| E1 call-chain trace | v2 | 0 | 1.04 | Both 5/5 |
| E2 bug localization | v1 | 0 | 0.78 (noise) | Both located utils.py:556-557 |
| E4 function rename (control) | v1 | 0 | 1.25 (noise) | Both correct; Condition B properly did not delegate |

### Problems with rule v1 (deprecated)

Across all 7 tasks, combined B/A = 1.17: delegation cost 17% more. Causes:

1. **Re-reading**: On R1 and R2, Condition B asked Gemini and then read the PDFs again itself (the rules required it to "verify"), paying twice.
2. **`@file` breaks on PDFs**: gemini-mcp-tool inlines file contents directly into the prompt, truncating binary PDFs so Gemini read nothing (R2). Rule v3 switched to passing paths only.
3. **Writing tasks** (E3 1.74, R3): After Gemini wrote the text, Claude still had to output the full text in its own reply.

R1/R2/R3 data from rounds 1 and 2 are **invalid**: poppler was not installed on the machine yet, so Claude's Read tool could not open PDFs and Condition A did not actually read the papers (R1-A gave up). Those tasks were re-run after installing poppler (round 3). Raw data remain in `experiment/results/` for inspection.

### Problems with rule v2 (deprecated)

"Do not delegate if Grep can solve it" caused Claude to read PDFs itself with pdftotext + Grep. Condition B never delegated, leaving only random variance between A and B (R2 1.20, R1 0.80).

## Limitations

- Each configuration was run once. The v3 conclusion is based on 2 tasks, 1 run each; the direction is consistent and the magnitude is well beyond ±20% variance, but more repetitions are still needed.
- Only the Claude side was measured; Gemini quota usage is not included.
- Two re-runs were stopped shortly after starting (once because the rules had not been written in, once after finding PDFs could not be read). The aborted runs may have incurred small unlogged costs; total spend is still estimated to be under $8.
- Only 7 task types and PDFs ≤75 pages were tested. Larger inputs (hundreds of pages or large logs) should save more in theory, but were not tested.
- Blind readability scoring has not been done yet.

## How to reproduce

```bash
cd experiment
./setup.sh                                   # download requests and the three papers
python3 run.py --tasks R1 R2 --reps 3 --budget 10
python3 run.py --summary
```

Requires poppler from Homebrew (`brew install poppler`); otherwise Claude cannot read PDFs.
