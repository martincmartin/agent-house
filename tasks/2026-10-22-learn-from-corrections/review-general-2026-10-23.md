# General review: bug reflection plan

## Scope

- Kind: review of a proposed workflow and skill, before implementation.
- Worktree: `/Users/martin/Develop/agent-house/work1`.
- TASK_DIR: `tasks/2026-10-22-bug-reflection/`.
- Target: the complete, untracked `PLAN.md`, lines 1–220.
- Base and head: `f414ed48148fbeb3e9b22e1cb159fc3e258a33b5`.
  No commit range was reviewed. The untracked plan was included.
- Read first: root `AGENTS.md`, `user/AGENTS.md`, the task's
  `README.md`, and `PLAN.md`.
- Supporting sources: `docs/README.md`, `docs/harnesses.md`,
  root `README.md`, the earlier instruction-trimming task's `PLAN.md`,
  the general review skill, and `tools/check`.

The review changes no repository file or Git state.

## What is good

The plan separates reflection from the decision to add a permanent rule.
The ladder prefers design changes and checks before instruction growth.
A bounded watchlist can preserve uncertain cases without a fixed taxonomy.
The six examples make the intended comparison clear.

The earlier trimming task's
[`PLAN.md`](/Users/martin/Develop/agent-house/work1/tasks/2026-10-21-trim-user-agents-md/PLAN.md:21)
explains why an explicit loading trigger matters.
[`user/AGENTS.md`](/Users/martin/Develop/agent-house/work1/user/AGENTS.md:44)
requires indexes that name when to read a document.
The new findings concern gaps between those rules, the chosen workflow,
and its proposed text.

## Findings

### 1. P2: Add the milestone trigger to the always-loaded text

Location: `tasks/2026-10-22-bug-reflection/PLAN.md:150–152`.

The proposed trigger loads the skill after a bug fix. It does not load it
when a task ends, a talk is tagged, or a release is made.
Those events appear only inside the proposed skill and its description.
Decision 1 requires both immediate reflection and milestone comparison.

A fresh session that completes a task without fixing a bug has no explicit
always-loaded instruction to perform the milestone review.
Under the plan's own loading constraint, that half of the workflow is unreliable.

A skill description can help discovery. However, the cited trimming task
treats that as weaker than an explicit trigger.

Smallest fix: add the milestone events to the proposed always-loaded trigger.
Keep the procedure inside the skill.
This adds a short trigger instead of duplicating the procedure.

Confirmation: walk through a fresh session that ends a task without a bug fix.
The always-loaded text must require the milestone review.
I checked the current text by reading; this case lacks that requirement.

### 2. P2: Compare earlier entries before sorting the new bug

Location: `tasks/2026-10-22-bug-reflection/PLAN.md:176–184`.

Only the “Not sure” branch reads the watchlist.
A bug classified as recurrent goes straight to a new lesson.
A bug classified as ordinary gets no comparison.

Suppose an earlier production-test mismatch remains uncertain on the list.
A later mismatch has a cheap check, so the proposed criteria classify it as
“It will come back.”
The later fix skips the old entry, even though the two cases can justify
the broader lesson shown by examples 1–3.
The earlier entry also remains unresolved.

Restricting reads to uncertain bugs saves work. However, the list already has
an intended limit of about 20 entries.
The restriction removes an important chance to find the pattern.

Smallest fix: compare the new bug with existing entries before choosing its group.
Then make the lesson and remove entries that the lesson addresses.
Continue to add only uncertain, unmatched bugs.

Confirmation: use one earlier uncertain entry and a related new bug with a cheap check.
The process must compare them before taking the recurrent branch.
I traced this case through the proposed steps; the current branch skips comparison.

### 3. P2: Require a useful shared cause before deleting a matched entry

Location: `tasks/2026-10-22-bug-reflection/PLAN.md:182–184`.

The instruction accepts likeness “in any way.”
It then requires a lesson and deletion of the earlier entry.
The milestone procedure also asks for groups without defining a sufficient match.

The plan's lint-disable and prerender cases both concern validation.
That resemblance alone does not establish one cause or a prevention measure
that addresses both.
The current wording permits deletion after such a superficial match.

Broad comparison is valuable because fixed classes can hide connections.
That does not require accepting every resemblance as evidence of recurrence.

Smallest fix: require a stated shared cause or gap in checks.
Explain how the proposed lesson addresses both cases.
If that link remains uncertain, retain the entry.

Confirmation: compare the lint-disable and prerender cases using only
“both concern validation.”
That alone must not justify promotion and deletion.
Then confirm that a supported comparison of examples 1–3 can still qualify.
I checked these cases by reading; the current wording accepts the weaker match.

### 4. P2: Define how readers consult both local and shared watchlists

Location: `tasks/2026-10-22-bug-reflection/PLAN.md:203–206`.

The skill names the project's watchlist “or” agent-house's watchlist.
Its procedures refer to “the watchlist.”
It does not require comparison with both sources or explain how another
project locates the shared file.

Storage scope is useful: project-specific incidents and general incidents
belong in different places.
Read scope is different.
A project incident can share a general cause with an entry stored in agent-house.
Reading only the local list prevents that comparison.

The installed skills can provide a route to their source repository.
However, [`docs/harnesses.md`](/Users/martin/Develop/agent-house/work1/docs/harnesses.md:24)
describes links for individual skills and agents, rather than shared project docs.
The proposed text gives no route from the installed skill to the shared list.

Smallest fix: separate where to store an entry from which lists to read.
Require comparison with both existing lists and define how to locate the shared file.
If it is unavailable, state what to report and where to retain the local evidence.
Any shared-file update must follow agent-house's worktree rule.

Keeping “or” is shorter, but leaves general patterns split between projects.

Confirmation: start in another project with a local list and a related shared entry.
The instructions must identify both files and require comparison.
Also check the case where the shared checkout is unavailable.
I checked the documented paths and procedure; neither case has a complete instruction.

## Older problems

No older defect is asserted.
The loading constraint and separate project documentation are existing rules.
The findings concern how this proposal uses them.

## Ranking and alternatives

Preferred approach: keep Decision 1 D, Decision 2 B, and Decision 3 A,
with the four corrections above.

Rank the corrections in finding order:

1. Add the milestone trigger. Without it, one chosen review stage lacks reliable loading.
2. Compare before sorting. This closes a direct gap in detecting recurrence.
3. Require an explained match. This prevents premature deletion of useful evidence.
4. Define access to both lists. This makes the shared storage choice usable across projects.

A fixed count still needs consistent comparison between incidents.
An unlimited log preserves more history but increases reading and maintenance.
Neither alternative fixes the loading or matching gaps by itself.
The bounded watchlist remains the better fit for the stated context limit.

## Limits and checks

- This is a text and workflow review, not an implementation review.
- I read the applicable instructions again before writing the analysis.
- I traced the four cases above through the proposed steps.
  These are manual reasoning checks, not executed agent trials.
- `git diff --check` emitted no diagnostics.
  That command does not include untracked files.
- A separate `git diff --no-index --check /dev/null` check of the plan
  emitted no whitespace diagnostics. It returned 1 for the differing files.
- I read `tools/check`. It checks the installer and converter, so it cannot
  settle the workflow questions. I did not run it.
- I did not verify the six incident reports against the Slidev repository,
  deployment logs, or source commits.
- No token cost, reflection time, or recurrence rate was measured.
- The four harnesses were not exercised. No proposed skill exists yet.

