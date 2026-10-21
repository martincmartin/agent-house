# agent-house

The instructions, skills and subagents that apply to all my work, for every
coding agent: Claude Code (CLI, VS Code and cloud sessions), Codex, OpenCode and
Pi. Project-specific rules stay in each project's own `AGENTS.md`.

| Path             | Holds                                                                              |
| ---------------- | ---------------------------------------------------------------------------------- |
| `user/AGENTS.md` | the user-level instructions                                                        |
| `user/skills/`   | one directory for each skill, with its `SKILL.md`                                  |
| `user/agents/`   | one file for each subagent, in Claude Code's format                                |
| `install`        | links `user/` to where each harness reads it, and converts the subagents           |
| `tools/`         | `convert-agent.py` (used by `install`) and `test-install`                          |
| `docs/`          | [`harnesses.md`](docs/harnesses.md): where each harness reads what, and why        |
| `AGENTS.md`      | the rules for working on this repo. No harness gets it as user-level instructions. |

## Install

```bash
./install                    # all four harnesses
./install --harness claude   # one harness; repeat the flag for more
```

`install` makes links that point into this checkout, so an edit here reaches
every harness at once. Run it again after you add or remove a skill or a
subagent. It is idempotent: when everything is already correct, it prints
nothing and exits with status 0. It never removes or replaces anything that it
did not write. The only files that it rewrites are the subagents that it
generated, when their source changed. When something is not as
expected (a link to somewhere else, a real file, a dangling link), it reports
it, goes on with the rest, and exits with status 1. Look into each report, fix
it, and run `install` again.

### A laptop

`~/init-files/install-me` clones this repo to `~/Develop/agent-house` if it is
not there, and then runs `install`.

### Claude Code cloud sessions

A cloud session gets nothing from your laptop's `~/.claude`. In each cloud
environment, at [claude.ai/code](https://claude.ai/code), put this in the
**Setup script** field:

```bash
git clone --depth 1 https://github.com/martincmartin/agent-house.git ~/agent-house
~/agent-house/install --harness claude
```

The setup script runs before Claude Code starts. The environment keeps the
result for about seven days and reuses it, so a change here can take that long to
reach new cloud sessions. To get it sooner, edit the setup script (an added
blank line is enough): the next session runs it again.

To check, run `/context` in a cloud session: `/root/.claude/CLAUDE.md` must be
under **Memory files**.

## Check a change

```bash
tools/test-install bash
tools/test-install /bin/bash   # macOS: install must work with bash 3.2
```
