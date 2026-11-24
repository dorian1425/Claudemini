# Claudemini

Two-way collaboration between **Claude Code (Opus)** and local **Antigravity (Gemini 4)**:

- **Claude → Gemini**: Claude delegates read-heavy, short-answer tasks and long-form writing to Gemini 4 Neon to save Opus tokens and produce more readable prose.
- **Gemini → Claude**: When chatting with Gemini in Antigravity (desktop or the `agy` CLI), Gemini can delegate careful code edits and debugging to Claude. Claude points out flaws in Gemini's plan, and Gemini explains the results back to you in its own words.
- **No infinite loops**: Both directions are guarded by environment variables, and the guards have been tested.

> **Measured results**: On papers and long documents, Opus token usage drops by 40–62% with no loss in accuracy. On code reading, it does not save tokens, so the rules keep coding tasks on Opus. See [REPORT.md](REPORT.md).

## How it works

```
You ──► Claude Code (Opus)
          │  decides whether to delegate via ~/.claude/CLAUDE.md
          ▼
        gemini-cli MCP (gemini-mcp-tool + PR#108 patch)
          │  env GEMINI_DELEGATED=1
          ▼
        agy  --model gemini-4-neon-high  -p "..."
          ✗  Gemini here cannot call back to Claude (ask-claude refuses, exit code 3)

You ──► Antigravity / agy (Gemini 4)
          │  via ~/.gemini/GEMINI.md + ask-claude skill
          ▼
        ask-claude  (read-only by default; --write allows edits in the current directory)
          │  env ASK_CLAUDE_ACTIVE=1, --strict-mcp-config (no Gemini tools)
          ▼
        claude -p --model opus  → ends reply with Result / Objections / Unverified
          ✗  Claude here has no Gemini tools; even if it runs agy itself, any call back is refused
```

## Installation

Prerequisites: macOS or Linux, Node.js 18+, git, a signed-in Claude Code installation, poppler (`brew install poppler`; without it, Claude cannot read PDFs), and Antigravity CLI:

```bash
curl -fsSL https://antigravity.google/cli/install.sh | bash
```

```bash
agy            # run once and sign in to your Google account
```

Then:

```bash
git clone https://github.com/dorian1425/Claudemini.git && cd Claudemini
./install.sh --dry-run   # preview what it will do
./install.sh
```

The installer is additive: existing `~/.claude/CLAUDE.md`, `~/.gemini/GEMINI.md`, and agy's `settings.json` are backed up to `*.bak.<timestamp>` before appending, rather than overwritten. To pick a different model: `CLAUDEMINI_MODEL=gemini-4-carbon-high ./install.sh`.

## Usage

**In Claude Code** (start a new session):

- "Use Gemini to read src and summarize what each module does in 10 bullet points or fewer."
- "Have Gemini write a README to docs/README.md based on these points."

**In Antigravity desktop or `agy`**:

- "Have Claude check the average function in stats.py for edge cases."
- "Have Claude refactor this function for me." (Gemini will pass `--write`.)

The first time the desktop app invokes `ask-claude`, it prompts you to approve the command. Choose "Always allow".

## Repository layout

| Path | Contents |
|---|---|
| `claude/CLAUDE.md` | Rules for when and how Claude delegates to Gemini |
| `gemini/GEMINI.md` | Global rules for Gemini (working with Claude and writing style) |
| `gemini/skills/ask-claude/` | Skill for Gemini to invoke Claude |
| `gemini/settings.json` | Allowlists only `ask-claude` in agy unattended mode |
| `bin/ask-claude` | Gemini → Claude bridge command (including loop guards) |
| `patches/gemini-mcp-tool-pr108.diff` | Patch so gemini-mcp-tool forwards `--model` to agy |
| `experiment/` | Token-savings A/B experiment: tasks, rubrics, runner script, and raw answers |
| `REPORT.md` | Experiment report |

## Dependencies

- [Antigravity CLI](https://antigravity.google/) (Google): runs Gemini 4 locally; install it yourself.
- [gemini-mcp-tool](https://github.com/jamubc/gemini-mcp-tool) (MIT): MCP server that lets Claude Code call `agy`; fetched by `install.sh` at commit `588e73d` and patched with `patches/gemini-mcp-tool-pr108.diff`.

## Security notes

- In unattended mode, `agy` runs tools **without a sandbox** using your own user permissions. `CLAUDE.md` instructs Claude to tell Gemini not to modify files on read-only tasks, but that is only an instruction, not enforced isolation.
- `ask-claude` disables Claude's file-writing tools by default. With `--write`, it auto-approves edits only within the current directory and rejects any other command that requires approval.
- Anything delegated to Gemini is sent to Google. Do not let Claude send secrets or private data to Gemini (this is stated in the rules).

## Uninstall

```bash
claude mcp remove gemini-cli -s user
rm -rf ~/.claudemini ~/.local/bin/ask-claude ~/.gemini/config/skills/ask-claude
```

Then manually remove the "# Delegating to Gemini" section from `~/.claude/CLAUDE.md` and the "## Working with Claude" section from `~/.gemini/GEMINI.md`.
