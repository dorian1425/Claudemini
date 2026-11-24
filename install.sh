#!/bin/bash
# Claudemini installer (macOS / Linux). Re-runnable; never overwrites a file
# you already have without making a .bak copy first.
#
#   ./install.sh            install everything
#   ./install.sh --dry-run  print what would happen
set -euo pipefail

REPO="$(cd "$(dirname "$0")" && pwd)"
DRY=0; [ "${1:-}" = "--dry-run" ] && DRY=1
BIN="$HOME/.local/bin"
GEM_SKILLS="$HOME/.gemini/config/skills"
MCP_DIR="$HOME/.claudemini/gemini-mcp-tool"
MODEL="${CLAUDEMINI_MODEL:-gemini-4-neon-high}"

say() { printf '\033[1m==> %s\033[0m\n' "$*"; }
run() { if [ $DRY = 1 ]; then echo "    $*"; else eval "$@"; fi; }
backup() { [ -e "$1" ] && run "cp -R \"$1\" \"$1.bak.$(date +%Y%m%d%H%M%S)\"" || true; }

need() { command -v "$1" >/dev/null || { echo "missing: $1 — $2" >&2; exit 1; }; }
need node "install Node.js 18+"
need git  "install git"
need claude "install Claude Code: https://claude.com/claude-code"
[ -x "$BIN/agy" ] || command -v agy >/dev/null || {
  echo "missing: agy — run: curl -fsSL https://antigravity.google/cli/install.sh | bash, then run agy once to sign in" >&2; exit 1; }
AGY="$(command -v agy || echo "$BIN/agy")"

say "1/5 gemini-mcp-tool (pinned + PR #108 model fix) -> $MCP_DIR"
if [ ! -d "$MCP_DIR" ]; then
  run "git clone -q https://github.com/jamubc/gemini-mcp-tool.git \"$MCP_DIR\""
  run "git -C \"$MCP_DIR\" checkout -q 588e73d"
  run "git -C \"$MCP_DIR\" apply \"$REPO/patches/gemini-mcp-tool-pr108.diff\""
fi
run "(cd \"$MCP_DIR\" && npm ci --ignore-scripts --silent && npm run build --silent)"

say "2/5 register MCP server 'gemini-cli' in Claude Code (user scope)"
run "claude mcp remove gemini-cli -s user >/dev/null 2>&1 || true"
run "claude mcp add --scope user gemini-cli -e GEMINI_MCP_BACKEND=agy -e AGY_CLI_PATH=\"$AGY\" -e GEMINI_DELEGATED=1 -- node \"$MCP_DIR/dist/index.js\""

say "3/5 Claude rules -> ~/.claude/CLAUDE.md"
mkdir -p "$HOME/.claude"
if [ -f "$HOME/.claude/CLAUDE.md" ] && grep -q "# Delegating to Gemini" "$HOME/.claude/CLAUDE.md"; then
  echo "    already present, skipped"
else
  backup "$HOME/.claude/CLAUDE.md"
  run "sed 's/gemini-4-neon-high/$MODEL/g' \"$REPO/claude/CLAUDE.md\" >> \"$HOME/.claude/CLAUDE.md\""
fi

say "4/5 ask-claude command + Gemini rules + permission"
run "mkdir -p \"$BIN\" \"$GEM_SKILLS/ask-claude\" \"$HOME/.gemini/antigravity-cli\""
run "install -m 755 \"$REPO/bin/ask-claude\" \"$BIN/ask-claude\""
run "sed 's|__ASK_CLAUDE__|$BIN/ask-claude|g' \"$REPO/gemini/skills/ask-claude/SKILL.md\" > \"$GEM_SKILLS/ask-claude/SKILL.md\""
if [ -f "$HOME/.gemini/GEMINI.md" ] && grep -q "## Working with Claude" "$HOME/.gemini/GEMINI.md"; then
  echo "    GEMINI.md already has the rules, skipped"
else
  backup "$HOME/.gemini/GEMINI.md"
  run "cat \"$REPO/gemini/GEMINI.md\" >> \"$HOME/.gemini/GEMINI.md\""
fi
SETTINGS="$HOME/.gemini/antigravity-cli/settings.json"
if [ -f "$SETTINGS" ]; then
  backup "$SETTINGS"
  run "node -e 'const f=process.argv[1],fs=require(\"fs\");const j=JSON.parse(fs.readFileSync(f));j.permissions=j.permissions||{};const a=j.permissions.allow=j.permissions.allow||[];if(!a.includes(\"command(ask-claude)\"))a.push(\"command(ask-claude)\");fs.writeFileSync(f,JSON.stringify(j,null,2)+\"\\n\")' \"$SETTINGS\""
else
  run "cp \"$REPO/gemini/settings.json\" \"$SETTINGS\""
fi

say "5/5 check"
run "claude mcp get gemini-cli | sed -n 1,3p"
run "rc=0; GEMINI_DELEGATED=1 \"$BIN/ask-claude\" hi >/dev/null 2>&1 || rc=\$?; [ \$rc = 3 ] && echo '    loop guard OK' || echo '    loop guard FAILED (rc=\$rc)'"
echo
echo "Done. Open a NEW Claude Code session and try: 'use gemini to summarize this directory'"
echo "In agy or the Antigravity app, try: 'ask Claude to review …'"
