# agent-house

This file is for work on this repo. The user-level instructions are in
`user/AGENTS.md`, and `install` links them, with the skills and subagents, to
where each coding agent reads them (`README.md`).

## Read before you act

Before you…

- change `install` or `tools/convert-agent.py`, add a harness, move a link,
  add a subagent key, or add a file to `user/<harness>/`: `docs/harnesses.md`
- change the Claude Code status line (`user/claude/statusline.py`):
  `docs/statusline.md`
- change the VS Code status band (`plugins/status-band/`) or the repo's plugin
  list (`.claude-plugin/marketplace.json`): `docs/status-band.md`
- change `user/claude/prices.json`, `tools/update-prices.ts` or
  `tools/update-plugin-types`: `docs/status-band.md`
- add, rename or remove a doc: `docs/README.md`

## Rules

- **Do not edit or commit in the checkout that `install` linked** (on a
  laptop, `~/Develop/agent-house/main`). Every harness reads its files, and
  Claude Code runs the plugins in `plugins/` from it, so a change there is
  live at once, also a change that is not finished. Work in a
  worktree on a branch, run `tools/check`, and then fast-forward `main` in that
  checkout. The one exception is the status line (`user/claude/statusline.py`,
  its tests and `docs/statusline.md`): edit it in that checkout, so that the
  user sees each edit live. A broken edit there breaks only the status line.
  Run `tools/check` before you commit, and then bring the other branches up to
  `main`.
- **Everything in `user/` reaches all four harnesses** (Claude Code, Codex,
  OpenCode and Pi), **except `user/<harness>/`** (`claude`, `codex`,
  `opencode`, `pi`). Keep the shared files neutral. If a rule or a skill is
  true for one harness only, say so in the text. Put a file in
  `user/<harness>/` only when the harnesses' interfaces differ too much for
  one shared file, as for a status line. `install` links each file there to
  the same path in that harness's directory (`docs/harnesses.md`).
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
- **The Python that `install` runs must work with Python 3.9** (macOS
  `/usr/bin/python3`): `~/init-files/install-me` runs `install` before it
  installs Homebrew. Today that is `tools/convert-agent.py` and
  `tools/install-plugins.py`. No `match`, no `X | Y` outside annotations, and
  no library call that is new in 3.10 or later. The Python that a harness runs
  needs only the Python that runs it: `user/claude/statusline.py` needs 3.10
  (`docs/statusline.md`).
- **The repo is public.** Put no secrets or licence keys in it.

## Before you commit

```bash
tools/check
```

It runs `tools/test-install` with bash, and again with bash 3.2 and Python 3.9
(on macOS). It runs ruff and mypy on the Python that `install` runs and on the
Python in `user/claude/`, and the tests there (`test_*.py`). For the status
band, it runs `claude plugin validate`, `claude plugin test` and `tsc`, and
`tsc` on `tools/update-prices.ts` (`docs/status-band.md`).

When you change how `install` treats a case, add a check for it to
`tools/test-install`.
