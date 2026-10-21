# agent-house

This file is for work on this repo. The user-level instructions are in
`user/AGENTS.md`, and `install` links them, with the skills and subagents, to
where each coding agent reads them (`README.md`).

## Read before you act

Before you…

- change `install` or `tools/convert-agent.py`, add a harness, move a link, or
  add a subagent key: `docs/harnesses.md`
- add, rename or remove a doc: `docs/README.md`

## Rules

- **Everything in `user/` reaches all four harnesses:** Claude Code, Codex,
  OpenCode and Pi. Keep it neutral. If a rule or a skill is true for one
  harness only, say so in the text.
- **Subagents in `user/agents/` use Claude Code's format.** `install` converts
  them for Codex and OpenCode. Do not remove a key from a subagent because one
  harness rejects it: drop or translate it in `tools/convert-agent.py`.
- **`install` is idempotent.** When everything is already correct, it prints
  nothing and exits with status 0. `~/init-files/install-me` runs it, and is
  run again after a later step fails, so a correct setup must never stop it.
- **`install` never removes or replaces anything that it did not write.** It
  rewrites only the subagents that it generated, through a temporary file, so
  a failed write leaves the old file. Files that it does not own (the
  harnesses' own files, and the user's own skills and subagents) are ordinary.
- **When something is not as expected, `install` reports it,** skips only what
  depends on it, and exits with status 1. Do not make it guess what the user
  meant.
- **`install` must work with bash 3.2** (macOS `/bin/bash`): no associative
  arrays, no `mapfile`, no `${var,,}`.
- **The repo is public.** Put no secrets or licence keys in it.

## Before you commit

```bash
tools/test-install bash
tools/test-install /bin/bash               # macOS: bash 3.2
uvx ruff check tools/convert-agent.py
uvx ruff format --check tools/convert-agent.py
uvx mypy --strict tools/convert-agent.py
```

When you change how `install` treats a case, add a check for it to
`tools/test-install`.
