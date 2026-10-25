# agent-house

The instructions, skills and subagents that apply to all my work, for every
coding agent: Claude Code (CLI, VS Code and cloud sessions), Codex, OpenCode and
Pi. Project-specific rules stay in each project's own `AGENTS.md`.

- `user/AGENTS.md`: the user-level instructions
- `user/skills/`: one directory for each skill, with its `SKILL.md`
- `user/agents/`: one file for each subagent, in Claude Code's format. A code
  review is a skill (`review-general`, then `review-simplify`), not a subagent:
  this is not an oversight (`tasks/2026-10-21-review-without-subagent/`)
- `user/<harness>/`: files for one harness only, linked to the same path in its
  directory. `user/claude/statusline.py` is the Claude Code status line
  ([`statusline.md`](docs/statusline.md)), and the `statusline-legend` skill
  says what each part of it means
- `plugins/`: Claude Code plugins, which Claude Code reads from this checkout
  (`.claude-plugin/marketplace.json` lists them). `plugins/status-band/` draws
  the status line's gauges above the prompt in the VS Code panel
  ([`status-band.md`](docs/status-band.md))
- `install`: links `user/` to where each harness reads it, converts the
  subagents, and installs the plugins
- `tools/`: `convert-agent.py` and `install-plugins.py` (used by `install`),
  `test-install`, `check`, which runs every check before a commit, and
  `update-prices.ts` and `update-plugin-types`, which update a file that the
  status band reads ([`status-band.md`](docs/status-band.md))
- `docs/` ([`README.md`](docs/README.md)): where each harness reads what, and
  why; the status line and the VS Code status band
- `tasks/`: one directory for each decision: its options, evidence and inputs
- `AGENTS.md`: the rules for working on this repo. No harness gets it as
  user-level instructions.

## Install

```bash
./install                    # all four harnesses
./install --harness claude   # one harness; repeat the flag for more
./install --no-plugins       # no Claude Code plugins
```

`install` makes links that point into this checkout, so an edit here reaches
every harness at once. Run it again after you add or remove a skill, a subagent
or a file in `user/<harness>/`. It is idempotent: when everything is already
correct, it prints nothing and exits with status 0. It never removes or replaces
anything that it did not write. The only files that it rewrites are the
subagents that it generated, when their source changed. For Claude Code, it also
adds this checkout as a plugin marketplace and installs each plugin in it, with
Claude Code's own `claude plugin` commands; that needs the `claude` command.
`--no-plugins` skips this step. When something is not as expected (a link to
somewhere else, a real file, a dangling link), it reports it, goes on with the
rest, and exits with status 1. Look into each report, fix it, and run `install`
again.

### A laptop

`~/init-files/install-me` clones this repo to `~/Develop/agent-house/main` if it
is not there, and then runs `install`.

### Claude Code cloud sessions

A cloud session gets nothing from your laptop's `~/.claude`. In each cloud
environment, at [claude.ai/code](https://claude.ai/code), put this in the
**Setup script** field:

```bash
git clone --depth 1 https://github.com/martincmartin/agent-house.git ~/agent-house
~/agent-house/install --harness claude --no-plugins
```

The script passes `--no-plugins`: a cloud session has no VS Code panel for the
status band to draw in.

The setup script runs before Claude Code starts. The environment keeps the
result for about seven days and reuses it, so a change here can take that long
to reach new cloud sessions. To get it sooner, edit the setup script (an added
blank line is enough): the next session runs it again.

To check, run `/context` in a cloud session: `/root/.claude/CLAUDE.md` must be
under **Memory files**.

## Check a change

Run `tools/check` ("Before you commit" in [`AGENTS.md`](AGENTS.md)).
