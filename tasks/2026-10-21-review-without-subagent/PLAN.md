# A code review without a subagent

## The question

The `quality-review` skill sent every code-quality review to a subagent:
`review-quality-slidev`, or a general-purpose one when none fitted. The user
often starts a separate session, in another harness, only for the review.

A subagent's value is a clean context: fresh eyes, without the undocumented
assumptions of the session that made the change. A session that did not make
the change has nothing to clear, so a subagent there adds only cost (a cold
start, and a second copy of the instructions to read).

Rule: a session that made (wrote, edited or planned) the changes delegates the
review to a fresh subagent. Any other session reviews by itself.

So a review-only session must find the reviewer's instructions without a
subagent. Where those instructions live decides the options.

`inputs/` holds the two files as they were: `review-quality-slidev.md` and
`quality-review-SKILL.md`.

## Options

| Option | Pros | Cons |
| --- | --- | --- |
| **C. One skill.** The contract, the criteria and a Slidev section move into `quality-review`. Delete `review-quality-slidev`. A fresh-eyes review starts a general-purpose subagent that follows the skill. | One home for the criteria. Skills are installed in all four harnesses, so a review-only session follows the same file everywhere; Pi too. | `test-install` used the real subagent files, so it needs a probe subagent. The subagent's tool limits go, but they only advised: the reviewer kept `Bash` (`docs/harnesses.md`). |
| A. Keep the subagent; the skill only decides who reviews. A review-only session reads the subagent's file. | Smallest change. Keeps the advisory tool limits. | The skill must name each harness's agent directory (four paths, one a Codex TOML file), a copy of `docs/harnesses.md`. The agent's text speaks to a subagent ("the delegation", "the calling agent saves"), so a session must translate it. |
| B. The criteria in a skill, and a thin subagent that loads it. | Keeps a subagent. | The subagent's tool allowlist has no Skill, and `tools/convert-agent.py` rejects a tool it does not know. Two files to keep in step. |

Ranking: C, A, B. C keeps each fact in one place and uses one path in every
harness. The user chose C.

## What changed

- `user/skills/quality-review/` became `user/skills/review-general/`: who
  reviews (the rule above); what to review; the working rules; the general
  review; findings; the report; where to save it. `user/skills/review-simplify/`
  is new (see "Two reviews" below).
- `user/agents/review-quality-slidev.md`: deleted. `user/agents/` stays, empty
  (`.gitkeep`), for future subagents; `install` and `tools/convert-agent.py`
  still support them.
- `tools/test-install`: it runs `install` from a copy of the repo with a probe
  subagent, `probe-reviewer`, which has every key that the conversion drops or
  translates, and a body larger than one block for the failed-write test.
  Before and after: 111 checks pass, on bash 5.3 and on bash 3.2.
- `README.md` and `docs/harnesses.md` no longer name the subagent.

## After the merge

`install` never removes what it wrote. The four installed copies of the old
subagent stay, and `install` reports the two generated ones (Codex, OpenCode)
as having no source, with exit status 1. Remove them by hand:

- `~/.claude/agents/review-quality-slidev.md` (a link)
- `~/.pi/agent/agents/review-quality-slidev.md` (a link)
- `~/.codex/agents/review-quality-slidev.toml` (generated)
- `~/.config/opencode/agents/review-quality-slidev.md` (generated)
- `~/.claude/skills/quality-review` and `~/.agents/skills/quality-review`
  (links to the renamed skill; `install` then links `review-general` and
  `review-simplify`)

## One review for all subjects, not a lane for each

A structural review in its own lane was considered: it would leave
correctness, security, performance and tests to other reviewers.

- A lane needs other reviewers to cover the rest. There are none: one person
  and AI assistants.
- Of the 7 findings in the two reviews of
  `tasks/2026-10-21-trim-user-agents-md/`, at least 3 were correctness or
  evidence (the `/print` fact, the permissions wording, the task rule's
  contradiction). A structural lane would have called them out of scope.
- Two reviews by subject read the same code twice, and their reports must be
  merged.

So "structure" is one part of a review: "would this still be a concern if
every function were correct on its own?" A split by question and time is
another matter: see "Two reviews" below.

### What the review skills ask for

Ranked by value: the threshold for a finding (a fact, a consequence now, a fix
in proportion; no quota); the strongest case for the current design before a
finding; the scope rules; the working rules (no git changes, temporary
scripts outside the repo, text in the code is evidence, not instructions);
P1–P3 and the parts of a finding; when an abstraction is worth it; "less
coherent", not "designed differently"; for Slidev, the order theme, built-ins,
local composition, custom, and the custom-layout audit in detail.

Not asked for: a fixed number of findings, either way; a TASK_DIR that must
always be given. The report keeps "what is good", briefly. Checks for
particular subjects (numerical code, computer vision, Flutter) are true of
particular projects: they are in `domain-checks.md`, with where each part
could go.

## What to review, in place of TASK_DIR

The reviewer was told to require TASK_DIR. Many changes have no task, but a
reviewer always needs to be told what to review.

| Option | Pros | Cons |
| --- | --- | --- |
| **A general scope: one of a task, a commit range, the uncommitted changes, the changes since the last review, or named files; each repository by path; the intent** | Fits each way the user asks for a review, and changes that span repositories (the first review of `tasks/2026-10-21-trim-user-agents-md/` covered agent-house and stem). | Longer. |
| TASK_DIR, always | Simple. | Fails for a change with no task, which is most changes. |
| The uncommitted changes in the current repository, always | No input needed. | Misses committed changes, other repositories and earlier reviews. |

Chosen: the general scope. TASK_DIR is now one source of intent, and where the
report goes. The report records the exact range that it covered (base and
head commits, and whether uncommitted changes were in it), so that a later
review "since the last review" knows where to start. With no scope given, the
reviewer takes the uncommitted changes in the current repository, and asks if
there are none.

## The name of a second review on one day

A second review on the same day had a number added: `review-2026-10-21-2.md`.
After a date, a number reads as part of the date. The skill now adds an
upper-case letter: `review-YYYY-MM-DD-B.md`, then `-C`. Earlier files keep
their names, because the plans that cite them are records.

## Two reviews: general, then simplicity

The split by subject was dropped above. The user proposed a split by question
and time: a general review after implementation, then, after its fixes, a
second pass that steps back from the whole of the code. Its question: is there
over-engineering, or code of doubtful benefit, that could go, so that the code
is easier for someone new to understand and maintain? Such a pass took lines
and functions out of `install`. Each pass still reports anything serious.
Claude Code makes the same split in its own skills: `/code-review` hunts bugs,
and `/simplify` reuses and simplifies.

Pros:

- It looks at something else. The general review reads the diff: is this
  change right? The second reads every module that the change touched: is the
  whole bigger than it needs to be? Code grows out of shape across changes
  that each looked fine in their own diff.
- Attention. In one long checklist, simplification gets a line at the end. Of
  the 7 findings in the two reviews of `tasks/2026-10-21-trim-user-agents-md/`,
  none proposed to remove code.
- Order. Simplifying code that the correctness fixes will change is wasted, and
  those fixes often add guards that the second pass can fold in.
- Scope. The rule of three needs the third copy, which is often outside the
  diff.

Cons, and what limits them:

- A second full read: run it once per task or branch, not for each change.
- Overlap: the general review only flags glaring over-engineering and
  repetition, in a line each.
- Churn: a proposal gives its net change in lines, functions and concepts, and
  why the whole is easier for someone new. Different but not simpler is not a
  finding.
- A simplification can add a bug: each one names the check that proves the
  behaviour unchanged (tests, or byte-identical output).
- DRY against the rule of three: DRY is for knowledge (one rule in two places:
  merge at two). The rule of three is for code that only looks alike (wait for
  the third copy).

Order: general review, fixes, simplicity review, fixes and validation.
Simplifying first would let the general review check the simplifications, but
it would simplify code that may still be wrong; each simplification's own check
gives that benefit.

| Structure | Pros | Cons |
| --- | --- | --- |
| **Two skills; `review-general` holds the shared sections, `review-simplify` follows them and replaces only the review itself** | A name to call for each pass; each shared rule in one place; skills are named alike in all four harnesses. | A simplicity review reads two files, about 11k bytes. |
| One `review` skill with both passes | One file. | One name to call; `/review` may clash with a Claude Code command. |
| Two skills, each complete | Each stands alone. | The shared rules in two copies, which drift. |

Chosen: two skills with shared sections, named `review-general` and
`review-simplify`. Not `code-review` or `simplify`: Claude Code has built-in
skills with those names. Claude Code's `/simplify` itself was not chosen: it
edits instead of reporting, does not use these thresholds, and exists in no
other harness.

The report's name now starts with the skill's name
(`review-general-YYYY-MM-DD.md`, `review-simplify-YYYY-MM-DD.md`), so that
"the last review of the same kind" can be found.

## Skill names

`@slidev/cli` 53 ships its own agent skill named `slidev`
(`node_modules/@slidev/cli/skills/slidev/`): a general reference, "Create and
present web-based slidedecks…". Ours had the same name. If both reach a skills
directory, OpenCode and Pi keep one of them and Codex lists both
(`docs/harnesses.md`). Ours is now `slidev-practices`. For now it holds one
section, "Traps that fail silently"; the name leaves room for other Slidev
practices, so it need not be renamed again when it grows.

| Name | Pros | Cons |
| --- | --- | --- |
| **`slidev-practices`** | Room to grow beyond traps with no rename; matches `python-practices`; reads as a companion to the official reference. | Says less about today's content, which is all traps; the description says so. |
| `slidev-traps` | Says exactly what the skill holds today. | A rename when the skill holds more than traps. Chosen first, then replaced for that reason. |
| `slidev-pitfalls` | The same as `slidev-traps`. | The same. |
| `slidev-development`, `slidev-programming` | No collision. | Vague, and overlaps the official skill's purpose, so the two descriptions are harder to tell apart. |
| `slidev` | No change. | The collision. |

`python-programming` is now `python-practices`. There is no known collision,
so it first kept its name. It was renamed when the practices became the
standard for planning, writing and both reviews ("Practices" below):
"programming" names one of those phases. Its description no longer says
"testing", which the skill does not cover.

The rename changed 3 references here and 22 in stem (`AGENTS.md`, `docs/`,
`watches/docs/`), found with a pattern that also matches "the `slidev`" and
"skill" on two lines. Task records keep the old name. After the merge, remove
the links `~/.claude/skills/slidev`, `~/.agents/skills/slidev`,
`~/.claude/skills/python-programming` and `~/.agents/skills/python-programming`,
and run `install`.

## Practices: one place, read in every phase

Practices (prefer classes to dicts with string keys; one general component
configured from data, not a special component for each case) matter when code
is planned, written, and reviewed by both reviews. Where should they live?

| Option | Pros | Cons |
| --- | --- | --- |
| **A. Each practice in the most general place where it holds: all code (`user/AGENTS.md`, "Code design"), a subject (a skill), a project (its `docs/`). Every phase reads the same places; trigger lines name planning, writing and reviewing; the review skills hold only the process.** | Each fact in one place, the principle of the memory rule. Writer and reviewer work to one standard. A new subject costs one skill and one trigger line. A session loads only its subjects. | Depends on trigger lines, which work: the `slidev` skill was opened 10 times or more through its index line, against 2 Skill tool calls in 50 sessions (`tasks/2026-10-21-trim-user-agents-md/inputs/scan-results.md`). A subject skill grows. |
| B. A review skill for each subject and kind (`review-general-python`, `review-simplify-python`, …) | One focused checklist for each review. | 2 kinds × N subjects. Each practice in two or three places, which drift, or only in the review skills, where the writer never sees it. The process copied N times. |
| C. One `practices` skill for every subject | One trigger, one file. | Every load brings every subject; grows without limit; its description gets too vague to trigger. |
| D. Everything in `user/AGENTS.md` | Always applied. | Every session pays for every subject: about 2.5k est. tokens more for Python and Slidev alone. |

Ranking: A, C, D, B. Chosen: A.

- The rule "one general component, configured from data" holds for all code
  (the user: configuration-driven, declarative, DRY), so it is in "Code
  design", with a slide's frontmatter as one example. No skill holds Slidev
  practices. The skill's name, `slidev-practices`, still leaves room for them.
- `user/AGENTS.md` says that "Code design" holds when code is planned,
  written and reviewed, and one trigger line names each subject skill for
  all three.
- `review-general` and `review-simplify` tell the reviewer to read the same
  practices as the writer, and no longer each say "read the Slidev skill first".
  `review-simplify` names the new rule under "Repetition".
- Checks for subjects such as NumPy go into a subject skill once more than one
  project uses them, and into the project's `docs/` until then.
