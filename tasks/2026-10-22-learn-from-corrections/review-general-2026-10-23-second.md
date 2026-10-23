# General review: learn from each correction

## Scope

- Kind: review of a named plan and its proposed workflow, before implementation.
- Repository and worktree: `/Users/martin/Develop/agent-house/work1`, branch `work1`.
- TASK_DIR: `tasks/2026-10-22-learn-from-corrections/`.
- Target: the complete, untracked `PLAN.md`, lines 1–428.
- Base and head: `f414ed48148fbeb3e9b22e1cb159fc3e258a33b5`.
  No commit range was reviewed. The untracked plan was included.
- Target SHA-256: `609a40f5e29b7493eca3112e8fcfea996755f779bf013d4eeaeabd60d09c08af`.
- Read first: the invoked `review-general` skill, root `AGENTS.md`,
  `user/AGENTS.md`, the task's `PLAN.md` and `README.md`.
- Supporting sources: `docs/README.md`, `docs/harnesses.md`, root `README.md`,
  `install`, `tools/check`, and `user/skills/python-practices/SKILL.md`.
- Historical sources: the task's first review and the instruction-trimming
  task's plan, README, transcript scanner and scan results.
- External supporting file:
  `/Users/martin/Develop/slidev/stem/work1/docs/talks.md`.
  I read this cited document for context. I did not review that worktree.

The report is the only file this review writes. No repository file or Git
state changed.

## What is good

The plan covers design and documentation corrections as well as bugs.
It separates reflection from the decision to add a permanent rule.
The ladder prefers prevention through design, then checks, then scoped rules.
It also checks whether an existing rule failed before adding another rule.

Comparison happens before classification. A match needs a shared cause and
one lesson that addresses both cases. These requirements reduce false matches.

The plan addresses all four earlier findings in its proposed text.
It adds milestone triggers, compares before sorting, requires a shared cause,
and gives readers a path to both lists.
Description-only triggering remains an experiment, and the plan proposes a follow-up check.

The applicable documentation supports keeping the procedure in a skill:

- [user/AGENTS.md](/Users/martin/Develop/agent-house/work1/user/AGENTS.md:44)
  separates loading triggers from document contents.
- [docs/harnesses.md](/Users/martin/Develop/agent-house/work1/docs/harnesses.md:24)
  explains the links for individual skills.
- [The trimming task](/Users/martin/Develop/agent-house/work1/tasks/2026-10-21-trim-user-agents-md/PLAN.md:21)
  gives the earlier evidence about skill loading.

The new findings concern the milestone review's inputs and first use.
They do not repeat the earlier loading and matching findings.

## Findings

### 1. P2: Define the first milestone when no tag exists

Location: `tasks/2026-10-22-learn-from-corrections/PLAN.md:365`.

The milestone procedure uses the saved commit. Without one, it starts at
the last tag. It gives no fallback when neither exists.
The watchlist format also lacks an initialization rule.

This checkout provides a concrete first-use case: it has 17 reachable commits
and no tags. `git tag --list` returned no output.
A first milestone review here cannot select its history range from the proposed instructions.
An agent must invent a starting point or stop for clarification.
This affects the explicit user-request trigger, which does not require an earlier release.

**Strongest reason to keep it:** a tagged talk usually has an obvious starting
point. The existing fallback is short and suits that case.
However, the skill also applies to other projects and first releases.

**Smallest fix:** treat absent watchlists as empty. If neither a saved commit
nor a tag exists, review the reachable history through `HEAD`.
Create the project's milestone header after that review completes.
State the selected range to the user.

This adds a defined first-use path. Leaving the text unchanged makes first use
in an untagged project depend on an undocumented choice.

**Confirmation:** trace a repository with commits, no tags and no watchlist.
The procedure must select a range, complete comparison and initialize its header.
I verified the checkout's commit count and absence of tags.
The workflow trace was a reading check; no proposed skill was executed.

### 2. P2: Include uncommitted corrections in a requested milestone review

Location: `tasks/2026-10-22-learn-from-corrections/PLAN.md:365`.

The milestone inputs are the watchlists and committed history.
`git log <commit>..` excludes staged, unstaged and untracked work.
The per-correction procedure retains only uncertain cases in a watchlist
(lines 317–324). Other current corrections therefore need not appear in either input.

The plan explicitly allows a milestone request at the end of a phase of work
(lines 127–131 and 362–363). It does not require a commit first.
A session can make several related corrections, then receive that request
before the user approves a commit.
The proposed procedure can report no groups even though the current work
contains the corrections that the user expects it to compare.

This plan itself is untracked. `git ls-files` lists no file in its task directory.
A history query for the plan cannot show its revisions, including examples 8 and 9.
`git log HEAD..HEAD -- <plan-path>` returned no output.
This confirms the input limitation; it does not measure an agent's response.

**Strongest reason to keep it:** committed history gives a stable boundary
and avoids treating unfinished work as settled evidence.
That suits a release prepared from committed work.
It does not cover the separately supported request during current work.

**Smallest fix:** include corrections from the current session and pending
changes when the user requests a milestone before a commit.
Read staged and unstaged changes and relevant untracked files.
State that the review includes pending work and which commit bounds its history.
Keep the saved marker at the latest committed revision reviewed.

Alternatively, defer the milestone until a commit exists and tell the user
that it remains pending. This is less useful for the stated request-at-any-time behavior.
Do not create a commit solely to obtain a boundary without the user's approval.

Including pending work preserves the chosen trigger. Leaving it out gives
an incomplete milestone review for a supported use case.

**Confirmation:** start with a saved milestone at `HEAD`, empty watchlists,
and two related, uncommitted corrections. Request a milestone review.
The procedure must compare those corrections or explicitly defer the review.
I traced this case through the proposed steps and checked the Git visibility limit.
I did not run an agent trial.

## Older problems

No additional older defect is asserted.
The first review's four findings are addressed in the current proposal.
Its report remains inside the task directory from that earlier review.
This review leaves it unchanged and saves its own report outside the repository.

## Ranking and alternatives

Keep the chosen combination: reflection after each significant correction,
judgment with explicit signs, and bounded watchlists.
The two findings need local changes to the milestone procedure.

Rank the recommendations as follows:

1. Define first-use history and watchlist initialization. This removes a missing
   path that the current untagged repository already demonstrates.
2. Include pending corrections in requested milestone reviews. This makes the
   procedure cover the user-request timing that the plan explicitly supports.

For finding 1, full reachable history is the simplest complete fallback.
A user-selected cutoff can reduce reading, but adds a question on first use.
Using only `HEAD` is cheaper, but silently discards earlier correction evidence.
Rank these choices: full history, explicit cutoff, then `HEAD` alone.
No history-reading time was measured.

For finding 2, including pending work best preserves the selected behavior.
Deferral gives a stable boundary but postpones the requested comparison.
Rank inclusion first, explicit deferral second.

A fixed recurrence count still needs comparable evidence across incidents.
An unlimited correction log preserves more evidence but adds continuing maintenance.
Neither alternative resolves these two history-boundary gaps by itself.

## Limits and checks

- This is a plan review. No proposed skill or watchlist implementation exists
  in the reviewed task, so runtime behavior was not tested.
- I reread the applicable instructions and cited documents before writing this analysis.
- I checked the milestone paths by reading and manual workflow traces.
- `git diff --check` emitted no diagnostics. It excludes untracked files.
- `git diff --no-index --check /dev/null <plan-path>` emitted no diagnostics.
  It returned status 1 because the compared files differ.
- I checked Git status, HEAD, the branch, tracked task files, tags and commit count.
  The task directory was untracked before and after review.
- I read `tools/check`. It validates the installer and converter, so it cannot
  settle these proposed workflow gaps. I did not run it.
- I inspected the installer's skill-linking code. I did not run `install`.
- I read the earlier transcript scanner. I did not run it or inspect private transcripts.
- I did not verify the ten correction accounts against source commits,
  deployment logs or CI runs.
- I did not test skill discovery in the four harnesses or verify their current
  external documentation. The findings do not depend on those behaviors.
- I measured no token cost, reflection time, recurrence rate or trigger recall.
