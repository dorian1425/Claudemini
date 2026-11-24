# Experiment: Does Delegating to Gemini Save Opus Tokens?

## Questions to answer

1. **Does it save tokens?** On the same task, how much does Opus token usage differ between Claude solo (Condition A) and Claude delegating to Gemini 4 Neon under `~/.claude/CLAUDE.md` (Condition B)?
2. **Does quality drop?** Does delegation reduce answer accuracy?
3. **Readability:** Does delegating writing tasks make the prose easier to read?
4. **Do the rules over-delegate?** On a small task (E4), Condition B should make zero Gemini calls.

## Conditions

| | Condition A (solo) | Condition B (delegate) |
|---|---|---|
| Model | Opus, fresh `claude -p` session | Same |
| MCP | None | gemini-cli only (Gemini 4 Neon via agy) |
| Tools | Read-only tools (Read/Grep/Glob/ls/wc/pdftotext); E4 also allows file edits | Same + Gemini tools |
| Global CLAUDE.md | Loaded (same overhead for both conditions) | Loaded |
| Prompt, working directory | Identical | Identical |

Both conditions use `--strict-mcp-config` so that no other MCP servers interfere.

## Tasks (real materials)

| ID | Type | Material | Expectation |
|---|---|---|---|
| E1 | Engineering: trace codebase call chain | psf/requests v2.32.3 | Read-heavy; delegation should save tokens |
| E2 | Engineering: locate a planted bug | Copy of requests (one-line edit) | Search-heavy; may not delegate |
| E3 | Engineering: technical explanation for beginners | requests | Readability task |
| E4 | Engineering: rename a function (control) | A 10-line file | **Should not delegate**, A≈B |
| R1 | Research: three-paper comparison table | Transformer / BERT / GPT-3 PDFs | Read-heavy; delegation should save tokens |
| R2 | Research: extract numbers from a 75-page paper | GPT-3 paper | Heaviest reading; most likely to save tokens |
| R3 | Research: general-audience science explainer | Three papers | Readability task |

The `## Rubric` section at the end of each task file is the grading rubric and is not sent to the model. Ground-truth answers for R1 and R2 were verified against the original papers. `R1F` and `R2F` are forced-delegation variants used to measure the ideal case.

The tasks were originally posed in Chinese, so the model answers in experiment/results/raw/ and experiment/blind/ are in Chinese; they are kept verbatim as recorded data.

## What is measured

`run.py` records Claude's `usage` for every run:

- **Primary metric: neutral tokens** = all input tokens (fresh input + cache write + cache read) + 5 × output tokens.
  Unaffected by prompt caching. Pilot runs showed that whichever condition ran first warmed the cache for the second, shifting dollar cost by up to 2×, so dollar cost alone is not enough.
- Dollar cost (`total_cost_usd`): actual billing equivalent, but affected by cache ordering.
- Output tokens, turn count, wall-clock duration, and number of Gemini calls in Condition B.
- Gemini-side usage is not counted: it uses your Antigravity quota and does not cost Claude money.

## Noise and repetitions

In a pilot run (E2, 1 run each), Condition B **made zero Gemini calls** yet used 22% fewer neutral tokens than Condition A. That is the natural variance between two runs of the same task.
Therefore:

- Run each task at least **3 times** per condition and take the median.
- Alternate A/B order across rounds (handled automatically by the script).
- Treat a saving as real only when B/A is clearly below about 0.8 and consistent in direction across repetitions.

## Quality and readability scoring

1. **Accuracy**: Score `results/raw/*.answer.md` against each task's Rubric.
2. **Readability (E3, R3)**: Blind review. Shuffle the A and B answers for each task, strip condition labels, score each from 1 to 5 yourself, and reveal the mapping at the end.
   You can have someone else shuffle them: `ls results/raw/E3-*answer.md | sort -R`.

## How to run

```bash
./setup.sh                          # download materials (requests and three papers); safe to re-run
python3 run.py --tasks E4 --reps 1  # run the cheapest control task first to check for over-delegation
python3 run.py --reps 3             # all tasks × both conditions × 3 reps (42 runs total)
python3 run.py --summary            # regenerate results/summary.md only
```

Cost reference: measured at $0.18–0.43 per run (Opus billing equivalent). `--budget` stops when total spend could exceed the cap. Also requires `brew install poppler`; otherwise Claude cannot read PDFs.

## Output files

- `results/runs.csv`: one row per run
- `results/summary.md`: summary table
- `results/raw/`: full event stream (`.jsonl`) and final answer (`.answer.md`) for each run

## Known limitations

- Measures only Claude-side tokens; check Antigravity for Gemini usage.
- Whether Condition B delegates depends on how Claude interprets CLAUDE.md. That is what we want to test, but it also means results change with rule wording.
- Small task count (7 tasks); conclusions apply only to similar tasks.
