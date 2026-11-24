# Results

Primary metric: **neutral tokens** = all input tokens (fresh + cache write + cache read) + 5 × output tokens, median over successful reps. It ignores which run happened to warm the prompt cache. `$` is Claude's billed-equivalent cost and IS cache-sensitive. Gemini usage is not included — it runs on your Antigravity quota.

| Task | A neutral | B neutral | B/A | A out | B out | A $ | B $ | B gemini calls | A time | B time |
|---|---|---|---|---|---|---|---|---|---|---|
| E1 | 196,996 | 205,334 | 1.04 | 3,242 | 3,164 | 0.239 | 0.262 | 0 | 106s | 134s |
| E2 | 162,331 | 125,905 | 0.78 | 1,450 | 1,454 | 0.369 | 0.195 | 0 | 42s | 38s |
| E3 | 129,879 | 226,617 | 1.74 | 2,474 | 4,186 | 0.194 | 0.269 | 1 | 31s | 179s |
| E4 | 160,864 | 200,441 | 1.25 | 755 | 715 | 0.360 | 0.182 | 0 | 15s | 16s |
| R1 | 247,249 | 343,036 | 1.39 | 2,635 | 4,600 | 0.234 | 0.325 | 1 | 33s | 219s |
| R1F | — | 135,677 | — | — | 2,804 | — | 0.234 | 1 | —s | 164s |
| R2 | 232,633 | 257,679 | 1.11 | 2,900 | 2,749 | 0.228 | 0.239 | 1 | 67s | 107s |
| R2F | — | 127,267 | — | — | 1,850 | — | 0.186 | 1 | —s | 141s |
| R3 | 529,599 | 416,299 | 0.79 | 7,218 | 7,826 | 0.392 | 0.411 | 3 | 335s | 1,267s |

**Paired total (neutral tokens):** A 1,659,552 vs B 1,775,310 → B/A = 1.07
