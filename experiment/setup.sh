#!/bin/bash
# Fetch the public materials the tasks run against. Safe to re-run.
set -euo pipefail
cd "$(dirname "$0")"
M=materials
mkdir -p "$M/papers"

# Engineering: psf/requests pinned to v2.32.3
if [ ! -d "$M/requests" ]; then
  git clone -q --depth 1 --branch v2.32.3 https://github.com/psf/requests.git "$M/requests"
fi

# E2: a copy of requests with one planted bug (ground truth in tasks/E2.md).
# get_encoding_from_headers() should fall back to ISO-8859-1 for text/*;
# the planted bug makes it return utf-8 instead.
if [ ! -d "$M/requests-bug" ]; then
  cp -R "$M/requests" "$M/requests-bug"
  python3 -I - "$M/requests-bug/src/requests/utils.py" <<'PY'
import sys, pathlib
p = pathlib.Path(sys.argv[1]); s = p.read_text()
old = '''    if "text" in content_type:
        return "ISO-8859-1"'''
new = '''    if "text" in content_type:
        return "utf-8"'''
assert old in s, "anchor not found — requests version changed?"
p.write_text(s.replace(old, new, 1))
PY
  rm -rf "$M/requests-bug/.git"
fi

# E4: tiny module for the small-edit control task
mkdir -p "$M/tiny"
cat > "$M/tiny/geometry.py" <<'PY'
import math


def area_of_circle(r):
    return math.pi * r * r


def describe(r):
    return f"circle r={r}, area={area_of_circle(r):.2f}"
PY

# Research: three public arXiv papers (PDF)
dl() { [ -s "$M/papers/$1.pdf" ] || curl -fsSL "https://arxiv.org/pdf/$1" -o "$M/papers/$1.pdf"; }
dl 1706.03762   # Attention Is All You Need
dl 1810.04805   # BERT
dl 2005.14165   # GPT-3 (Language Models are Few-Shot Learners), 75 pages

echo "materials ready:"; du -sh "$M"/* | sed 's/^/  /'
