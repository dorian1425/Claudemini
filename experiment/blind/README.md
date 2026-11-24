# Blind Readability Review

Each task has two answers (X and Y), without showing which came from Claude solo and which used Gemini.
Rate each answer's readability from 1 to 5 in scores.md, then run:

    python3 -c "import json;print(json.load(open('blind/.key.json')))"

to reveal the mapping.

The tasks were originally posed in Chinese, so the model answers in experiment/results/raw/ and experiment/blind/ are in Chinese; they are kept verbatim as recorded data.
