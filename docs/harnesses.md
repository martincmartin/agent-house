# Where each harness reads its user-level configuration

**Covers:** the directory, instruction file, skills and subagents that `install`
sets up for each harness, and the facts that decided each one.
**Read before** you change `install` or `tools/convert-agent.py`, add a harness,
or move a link.

The paths below are the defaults. `install` honours each harness's own override
variable. The text says how each fact was found. Harnesses change their search
paths often, so check again before you rely on an old fact.

| Harness     | Directory (override)                     | Instructions | Skills              | Subagents                                          |
| ----------- | ---------------------------------------- | ------------ | ------------------- | -------------------------------------------------- |
| Claude Code | `~/.claude` (`CLAUDE_CONFIG_DIR`)        | `CLAUDE.md`  | `~/.claude/skills/` | `agents/<name>.md`, linked                         |
| Codex       | `~/.codex` (`CODEX_HOME`)                | `AGENTS.md`  | `~/.agents/skills/` | `agents/<name>.toml`, generated                    |
| OpenCode    | `~/.config/opencode` (`XDG_CONFIG_HOME`) | `AGENTS.md`  | `~/.agents/skills/` | `agents/<name>.md`, generated                      |
| Pi          | `~/.pi/agent` (`PI_CODING_AGENT_DIR`)    | `AGENTS.md`  | `~/.agents/skills/` | `agents/<name>.md`, linked (no built-in subagents) |

`install` links each skill and each subagent one by one. It does not link a
whole `skills/` or `agents/` directory. This is not an oversight: the harnesses
write their own files there (Codex `skills/.system/`, Claude Code
`skills/synced/`).

## Skills: one shared directory, and Claude Code's own

Codex, OpenCode and Pi all read `~/.agents/skills`, the path of the Agent
Skills standard. Claude Code does not, so it gets `~/.claude/skills`. This
gives each harness one copy of each skill:

- **Codex** reads `~/.agents/skills` and `~/.codex/skills`, and lists a skill
  that is in both twice (codex-cli 0.163.0, `codex debug prompt-input`,
  2026-10-21). Its docs name only `~/.agents/skills`.
- **OpenCode** reads `~/.agents/skills`, `~/.config/opencode/skills` and
  `~/.claude/skills`, and keeps one skill for each name: the `~/.agents` copy
  wins (OpenCode 1.19.3, `opencode debug skill`, 2026-10-21). It also loads the
  claude.ai skills in `~/.claude/skills/synced/`, which name tools that only
  Claude Code has. `OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1` turns off
  `~/.claude/skills` ([rules docs](https://opencode.ai/docs/rules/)).
- **Pi** reads `~/.agents/skills` and `~/.pi/agent/skills`, and keeps the first
  skill of each name, with a warning
  ([skills docs](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/skills.md),
  2026-10-21; not tested, because Pi lists its skills only through a model).

So `install` reports a link to one of our skills in `~/.codex/skills`,
`~/.config/opencode/skills` or `~/.pi/agent/skills`: that is the old layout,
and Codex and Pi would see the skill twice.

Codex and OpenCode both load a skill with Claude Code's own keys
(`disable-model-invocation`, `paths`, `allowed-tools`, `model`,
`argument-hint`), with no warning (2026-10-21). This was a test of loading,
not of use with a model. If a harness ever rejects a skill key, give that skill
a generated variant, as for subagents.

## Subagents: Claude Code's format, converted

There is no shared format. The files in `user/agents/` are Claude Code
subagents. `install` links them for Claude Code and Pi, and
`tools/convert-agent.py` writes them for Codex and OpenCode. A comment in the
first two lines of a generated file names its source. `install` reports a file
with that name that it did not write, or whose source is gone, and leaves it.

- **The limits** come from Claude Code's `tools` (an allowlist) and
  `disallowedTools`. `CAPABILITIES` in `tools/convert-agent.py` lists each
  thing that a subagent can be kept from doing, with its Claude Code tools and
  its OpenCode permission. A tool that the list does not know is an error: add
  it to the list.
- **Codex** reads TOML: `name`, `description`, `developer_instructions`. It has
  no per-agent permissions. A custom agent runs in the sandbox of the session
  that starts it, and its `sandbox_mode` does not override that
  ([subagents docs](https://learn.chatgpt.com/docs/agent-configuration/subagents),
  2026-10-21). So the limits become the last sentence of
  `developer_instructions` ("Do not edit or write files, …"). Nothing enforces
  it.
- **OpenCode** gives `tools:` and `model:` other meanings: `tools` is a map of
  tool to `true` or `false` (and deprecated for `permission:`), and `model` is
  `provider/model-id`. It passes keys that it does not know to the model
  provider as options, and a strict provider can refuse them
  ([agents docs](https://opencode.ai/docs/agents/)). So the OpenCode copy has
  only `description`, `mode: subagent` and `permission:`. `model` is left out:
  then the subagent uses the model of the agent that calls it.
- **OpenCode's `permission:`** enforces the limits. This OpenCode calls its
  shell permission `bash`, and its `edit` covers editing and writing files
  (checked with `opencode debug agent`, 2026-10-21).
- **The limits block tools, not actions,** in every harness. A subagent that
  keeps its shell (`review-quality-slidev` keeps `Bash`, to read and run
  checks) can still write files and use the network through it. So "do not
  write files" is an instruction there, not a guarantee. For a hard limit, use
  the sandbox of the session that starts the subagent.

## Claude Code

- **The instructions are `CLAUDE.md`, not `AGENTS.md`.** Claude Code reads
  `~/.claude/CLAUDE.md` as user instructions in every session, also in the cloud.
  It reads an `AGENTS.md` only in the working directory and the directories
  above it, and only when no `CLAUDE.md` is there. A `~/.claude/AGENTS.md` loads
  only because `$HOME` is above most working directories. Then it is a project
  file, and a repo with a `CLAUDE.md` turns it off. So `install` reports a
  `~/.claude/AGENTS.md` as a problem. Checked in the
  [memory docs](https://code.claude.com/docs/en/memory#agents-md), 2026-10-21.
- **Cloud sessions** get nothing from your laptop's `~/.claude`. The cloud
  environment's setup script runs `install --harness claude` before Claude Code
  starts ([README](../README.md#claude-code-cloud-sessions)). Checked in the
  [cloud environment docs](https://code.claude.com/docs/en/cloud-environments#what-carries-over-from-your-setup),
  2026-10-21.
- **`skills/synced/`** holds the skills of your claude.ai account. Claude Code
  writes it. Do not name a skill `synced`.
