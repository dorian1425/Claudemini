---
name: ask-claude
description: Delegate a task to Claude (Claude Code, Opus) from the shell and get back its result plus its objections to your plan. Use when the user asks to have Claude do, check, or review something, or when a task needs careful code changes, debugging, or a second opinion on your own reasoning.
---

# ask-claude

You (Gemini) direct; Claude executes and is allowed to disagree with you.
Claude runs as Claude Code on this computer via the `ask-claude` command.

## When to use

- The user asks for Claude by name ("ask Claude", "have Claude do …", or the same in any language).
- Multi-file code changes, debugging, or anything where a wrong edit is costly.
- You want your own plan or claim checked before you present it as fact.

Do not use it for small questions you can answer yourself: every call spends
the user's Claude quota and takes tens of seconds to minutes.

## How to call

Always use the absolute path. Run in the shell, from the project directory:

```bash
__ASK_CLAUDE__ "TASK"                 # read-only (default)
__ASK_CLAUDE__ --write "TASK"         # may edit files in the working directory
__ASK_CLAUDE__ --dir /abs/path "TASK" # run in another directory
```

For long tasks, pipe the text on stdin:
`__ASK_CLAUDE__ --write <<'EOF' … EOF`.

Use `--write` only when the user asked for changes to be made. Calls can take
several minutes; wait for them to finish.

## What to put in TASK

Write it as a brief to a capable colleague who has not seen this
conversation:

1. **Goal** — what done looks like.
2. **Your plan** — the steps you think are right, and the facts/assumptions
   they rest on, stated explicitly so Claude can challenge them.
3. **Scope** — files or directories involved; what must not be touched.

## What comes back

Claude ends its reply with `## Result`, `## Objections`, `## Unverified`.

## After the call — report to the user in your own words

Never paste Claude's raw reply. Explain the outcome to the user in your own
words, in the user's language, as plain readable prose: what was done or
found, what it means, and anything still unverified.

Use Claude's objections to get the answer right — if Claude showed that a
premise or step of yours was wrong, give the user the corrected answer. You
do not need to list the corrections one by one; mention one only when it
changes what the user should believe or do.

## Never loop

- If `ask-claude` exits with code 3, you were started by Claude: do the task
  yourself and do not call Claude.
- Never call `ask-claude` more than twice for the same user request.
