# General review — 2026-10-22

## Scope

- Review kind: general review of the existing repository.
- Repository and worktree: `/Users/martin/Develop/agent-house/work1`, branch `work1`.
- Snapshot: `f5dee8e05b7ff81a7e9e83f3648c009f45068531`.
  Base and head are this same commit; this is a snapshot review, not a commit-range review.
- Scope: all 15 tracked files outside `tasks/`, including the empty `user/agents/.gitkeep`.
  All nine Markdown files were read.
- Uncommitted changes: included in scope; none existed when the review started.
- TASK_DIR: none. The user excluded `tasks/`; no task files were read or changed.
- Intent: check correctness, structure, and hygiene against the documented installation and conversion contracts.
- Read first: `AGENTS.md`, `user/AGENTS.md`, `docs/README.md`, and
  [docs/harnesses.md](docs/harnesses.md).
  Also read the requested review skill at
  `/Users/martin/Develop/agent-house/main/user/skills/review-general/SKILL.md`
  and `/Users/martin/.agents/skills/python-practices/SKILL.md`.
  The repository copies of both skills were also reviewed.

[README.md](README.md) requires error reports and status 1 for unexpected conditions.
[docs/harnesses.md](docs/harnesses.md) requires checks for stale generated files, even without source agents.
The new evidence below shows six cases where installation returns status 0 despite incomplete checks or unusable configuration.

## What is good

The installer protects existing files and checks destination ownership before replacement.
Generated files use a temporary file and rename, which protects the previous output after a failed write.

The converter rejects unsupported frontmatter before it emits output.
The capability table keeps permission translations together.
The tests cover silent repeat runs, ownership conflicts, conversion failures, and both required compatibility versions.

## Findings

### 1. P2 — Check source directories before glob expansion

**Location:** `install:270` and `install:279`.

**Evidence:** Both discovery loops use globs with `nullglob` enabled.
Neither loop checks whether its source directory can be read and searched.
An unreadable directory therefore produces the same empty array as a valid empty directory.

In a temporary repository copy, I set `user/skills/` to mode `000`.
With a fresh temporary home, `install --harness claude` returned status 0 and no error.
It installed none of the four skills.
I repeated the test with unreadable `user/agents/`; that run also returned status 0 and no error.
Both cases ran as the normal user, not root.

**Consequence:** Installation can report success while it omits configuration that it could not inspect.
The caller cannot distinguish a complete installation from a failed source scan.

**Alternative and smallest fix:** Empty source directories are valid, so rejecting empty arrays would break a supported case.
Before each glob, check that the source is a directory with read and search access.
If the check fails, report it once and skip only that source category.
Do not create or repair source directories during validation.

Leaving this unchanged hides an access failure behind a successful exit.
The small precondition check preserves valid empty directories and independent installation work.

**Confirmation:** Add non-root tests for unreadable source skills and agents directories.
Require status 1, a source-specific error, and continued installation of independent configuration.
Keep the existing empty-agent, no-Python case successful and silent on its second run.
The failure reproductions ran; tests for a fix did not run because this review changes no source.

### 2. P2 — Validate source files before creating links

**Location:** `install:235` and `install:281`.

**Evidence:** The instruction link has no source-file check.
The agent discovery loop accepts every name ending in `.md`, regardless of its file type or whether its target exists.

I reproduced three cases in temporary repository copies and fresh homes:

| Source condition | Command | Observed result |
| --- | --- | --- |
| `user/AGENTS.md` missing | `install --harness claude` | Status 0; dangling `CLAUDE.md` link |
| `user/agents/broken.md` is a dangling link | `install --harness claude` | Status 0; dangling installed agent link |
| `user/agents/broken.md` is a directory | `install --harness claude` | Status 0; installed agent resolves to a directory |

All three runs had empty stderr.
Destination checks occur before these new links exist, so they do not detect the newly created dangling links.

**Consequence:** A successful first installation can leave the harness without readable instructions or a usable agent file.
Codex and OpenCode conversion errors do not protect Claude-only or Pi-only installations.

**Alternative and smallest fix:** Linking without parsing is appropriate for Claude Code and Pi.
It does not require accepting missing sources or directories as files.
Check that the instruction source and each `.md` source resolve to readable regular files.
Keep valid source symlinks if they meet those checks.
Report each invalid source once and skip only the links or conversions that depend on it.

Leaving this unchanged makes success depend on which harnesses the user selects.
The file checks make source validation consistent without adding YAML parsing to linked harnesses.

**Confirmation:** Add tests for all three cases above, plus an unreadable source file.
Require status 1, no new unusable link, and continued installation of unrelated valid sources.
The three failure reproductions ran; tests for a fix did not run.

### 3. P2 — Preserve header-read failures during stale-file checks

**Location:** `install:169` and `install:220`.

**Evidence:** `generated_source` ends its read pipeline with `|| true`.
This suppresses a failed `head` read as well as the expected absence of a matching marker.
The stale-file loop receives an empty source string and continues without reporting a problem through `report`.

I created a generated `gone.toml` with the exact ownership header and a missing source.
I set that generated file to mode `000`, then ran `install --harness codex` with no source agents.
The command printed `head: .../gone.toml: Permission denied` but returned status 0.
It did not issue the installer problem summary.

**Consequence:** A stale-file audit can fail while its caller receives success.
This contradicts the documented stale-file check and prevents callers from using exit status to detect incomplete validation.
The file remains untouched; this reproduction did not show data loss.

**Alternative and smallest fix:** A readable file without an ownership marker must remain an ordinary user file.
An unreadable file is a different result: ownership could not be checked.
Separate the header read from marker matching and return a failure for read errors.
Have each caller handle that failure, call `report`, and continue safely.
Keep reporting in the caller; a counter changed inside command substitution would not reach the parent shell.

Leaving this unchanged hides an incomplete ownership check.
Explicit read failure preserves ordinary unowned files and the existing checks for directories, links, and FIFOs.

**Confirmation:** Add a non-root test with an unreadable stale generated file for each output format.
Require status 1, a clear read error, an unchanged file, and continued checks of other entries.
Retain the tests for readable unowned files and non-regular entries.
The Codex failure reproduction ran; the OpenCode case and tests for a fix did not run.
Both formats use the same helper and stale-file loop.

## Older problems

All three findings concern code already present at the reviewed commit.
This snapshot review has no change baseline, so it does not assign a regression date.
No additional historical findings are claimed, and `tasks/` remains excluded.

## Ranking

1. **Check source directories.** One inaccessible skills directory silently omits all four current skills.
   This has the widest demonstrated effect and needs only a small validation step.
2. **Validate source files.** Three demonstrated cases create unusable configuration while returning success.
   File checks preserve the existing link-based design.
3. **Preserve header-read failures.** This closes an incomplete audit with a successful exit.
   Rank it third because the unreadable file already produces a command-level error and remains untouched.

For all three, prefer explicit validation and status 1 over a warning with status 0.
Warnings alone cannot enforce the documented contract for callers.
Automatic repair would require assumptions about source content or file ownership.

## Limits and validation

- Read all tracked source, tools, configuration, and documentation outside `tasks/`.
  Reviewed the shipped skills as documents; did not apply them to external projects.
- Ran `tools/check` with temporary Ruff and mypy cache paths and `UV_OFFLINE=1`: passed.
  Ruff lint, Ruff format, and strict mypy passed.
  Both installer test runs passed with Bash 3.2.57 and Python 3.9.6.
- The first sandboxed check could not write the uv cache lock.
  Its installer tests passed, but its three uv checks failed for that environment restriction.
  The offline rerun with cache access passed in full.
- Ran the installer tests with Bash 5.3.20 and Python 3.9.6: passed.
- Ran the installer tests with Bash 5.3.20 and Python 3.15.0: passed.
  This run also passed TOML parsing, which Python 3.9 skips because it has no `tomllib`.
- Ran six targeted failure reproductions in temporary copies and temporary homes.
  The source remained unchanged. Each reproduction returned status 0 as described above.
- Checked four relative Markdown link targets: none were missing.
  Did not inspect the contents of any task link or fetch external documentation.
- Ran `git diff --check` before saving this report: passed.
- Did not run live harness sessions or verify current upstream discovery and permission behavior.
  Those statements received a review for local consistency only.
- No fixes, commits, rebases, installations into the real home, or other Git state changes were made.
  This report is the only file added to the worktree.
