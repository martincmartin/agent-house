# Files for one harness

Until now, everything in `user/` reached all four harnesses (Claude Code,
Codex, OpenCode and Pi): the instructions, the skills and the subagents. A
status line is the first file that cannot be shared, because each harness
gives it a different interface. This task decides where such a file goes in
the repo, and how `install` puts it in place.

## The evidence: status lines in the four harnesses

Found on 2026-10-24, from each harness's docs and repo:

- **Claude Code** runs a command and shows what it prints. The command gets
  the session's data as JSON on stdin. `settings.json` names the command
  (`statusLine`).
- **Codex** shows only its own built-in items, chosen by ID in its config. It
  runs no script.
- **Pi** has a footer that a TypeScript extension sets (`ctx.ui.setFooter`).
- **OpenCode** has no status line command yet. A pull request for
  `statusline.command` (#52764) was open.

So one script cannot serve all four. Codex can get no equivalent, and Pi needs
TypeScript. The user decided to make the status line for Claude Code only, for
now.

## The options

### A: a tree for each harness (chosen)

`user/<harness>/<path>` is linked to `<harness directory>/<path>`. One general
rule in `install` covers every file, also later ones.

- Pro: no per-file code. The change to `install` is one function of 16 lines
  and one call of 4 lines (27 lines with comments and a blank line).
- Pro: the path in the repo says where the file goes. A reader needs no list.
- Pro: it uses the source checks and the link checks that `install` already
  has (`check_source_dir`, `check_source_file`, `prepare_dir`, `make_link`).
- Con: a feature that has a file for each of two harnesses is in two places
  (`user/claude/statusline.py`, `user/pi/extensions/statusline.ts`).
- Con: tests beside a file must not be linked, so `install` needs a rule for
  what stays in the repo (`test_*`, `__pycache__`, hidden files, `*~`).

### B: a directory for each feature

`user/statusline/` holds `claude.py`, `pi.ts` and so on, and `install` knows
where each one goes.

- Pro: the versions of one feature are together.
- Con: `install` needs code, or a mapping, for each feature: about 5 to 10
  lines each (an estimate). The target path is not visible in the repo.
- Con: it is a second kind of directory in `user/`, beside `skills/` and
  `agents/`, with a meaning of its own.

### C: a list file

A file such as `user/links.txt` gives a source and a target on each line.

- Pro: any source can go to any target, with one line.
- Con: `install` must parse it with bash 3.2: about 20 to 30 lines with its
  error reports (an estimate), and tests for its format.
- Con: each fact is in two places: the file, and its line in the list. A file
  with no line, or a line with no file, is a new kind of error.

### Ranking

1. **A**, because it needs the least code (27 lines, with no code for each new
   file), keeps each fact in one place, and reuses the checks of `install`.
2. **C**, because it is general, but it adds a format, a parser and a second
   place for each fact.
3. **B**, because it needs code for each feature, and the number of features
   only grows.

## The settings entry

The status line works only with a `statusLine` entry in
`~/.claude/settings.json`.

1. **By hand, with the entry in `docs/statusline.md` (chosen).** `install`
   never edits a file that it does not own, and Claude Code writes
   `settings.json` (permissions, `/config`).
2. **`install` adds the entry.** It must parse and write JSON in a file that
   Claude Code also writes, with bash 3.2 or Python 3.9, and decide what to do
   when an entry is already there. Rejected: it breaks the ownership rule.
3. **Link a whole `settings.json` from the repo.** Claude Code's own writes
   would then go into the repo. Rejected.

## The Python version

`AGENTS.md` asked for Python 3.9 in `tools/convert-agent.py`, because `install`
runs it before Homebrew is installed. The status line runs under Claude Code,
long after that, with Homebrew's Python. So the rule now covers only the
Python that `install` runs, and the status line needs 3.10 (`X | None` in its
dataclasses). `tools/check` lints it with `--target-version py310`.
