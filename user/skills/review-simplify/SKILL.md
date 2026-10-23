---
name: review-simplify
description: The simplicity review, the second pass after the general review and its fixes. It steps back from the whole of the code that a change touched, to find over-engineering, repetition and code of doubtful benefit that can go. Read when the user asks for a simplicity review, or a review for over-engineering or duplication.
---

# Simplicity review

The second of two reviews. It comes after the general review (the
`review-general` skill) and its fixes: once per task or branch, or when a
module has had several changes. Its question: is there over-engineering, or
code of doubtful benefit, that could go, so that the code as a whole is easier
for someone new to understand and maintain?

Read the `review-general` skill, and follow its sections "Who reviews", "What
to review", "Working rules", "Findings", "The report" and "Keep the report out
of the repository".
In place of its "The general review", do the review below. Report a
correctness defect that you find on the way, as the general review would.

## What to read

- The whole of each module, file or component that the scope touches, not only
  the diff. Code grows out of shape across changes that each looked fine in
  their own diff.
- The code elsewhere in the repository that the change repeats or resembles:
  search for it.
- The practices that the code must follow, the same ones that its writer read:
  "Code design" in the user-level instructions, and the skill for each subject
  of the code that those instructions name (for example `python-practices`,
  `slidev-practices`).
- Before you propose to remove something, the project's `AGENTS.md`, the docs,
  and the tasks that they link: they may say why it is there. A "not an
  oversight" note records a decision. Propose to change it only with new
  evidence.

## What to look for

You are a principal engineer, new to this code, who will maintain it.

- **Over-engineering:** options, flags, parameters or configuration that no
  caller uses or varies; layers that only pass calls through; an abstraction
  with one implementation and no invariant to enforce; generality for callers
  that may never come; defensive code for states that cannot happen; a
  framework where direct code would do.
- **Code of doubtful benefit:** features, fallbacks, compatibility paths and
  diagnostics that nothing needs now. Search for the callers and the uses
  before you say "nothing".
- **Repetition.**
  - The same knowledge (a rule, a value, a computation that must change
    together) in two places: put it in one place, even when there are only
    two.
  - Code that only looks alike: wait for the third copy before you abstract
    (the rule of three), and then only if the copies change for the same
    reason. Prefer duplication to the wrong abstraction.
  - A special component or function for each case, where the cases differ
    only in data: one general one, with each case's data given declaratively
    ("Code design").
- **Fit:** the change adds a second way to do what the code already does (a
  helper, a pattern, a convention), or does not use what exists.
- **Delete, then simplify, then abstract,** in that order. An abstraction must
  earn its place now: it hides real complexity, enforces an invariant, removes
  duplicated knowledge, or isolates an effect. For a few closed cases a
  conditional is often clearest; for variation in data, a table; for
  substantial behaviours with a common contract, polymorphism. Compare the
  total code, including factories and registration. "You aren't gonna need it"
  does not excuse tangled code.
- **Consistency:** "I would design this differently" is not a finding. "This
  makes the system less coherent" is.

**Slidev projects.**

- Prefer what the project already provides, in this order: the active theme;
  Slidev's built-in layouts, components, frontmatter, clicks and transitions; a
  small local composition; and only then custom CSS, a component or a layout.
  Check the installed versions and the theme's source before you say that a
  feature exists. Keep custom work that teaches or shows something real.
- Audit every custom layout. Follow how each one is resolved: a theme or an
  addon can override a built-in name, and the lack of a literal `layout:` does
  not prove a layout unused. For each layout give the slides that use it, what
  it does that the alternatives cannot, its costs, the closest alternative,
  and one verdict: Keep, Simplify, Replace, Remove, or Keep pending
  verification (with the check that decides). End with the count of each
  verdict.

## Each proposal

Besides what "Findings" in `review-general` asks, give for each proposal:

- the net change: the lines, functions, files and concepts that go or come,
  measured where you can, and marked as an estimate where you cannot;
- why the whole is easier for someone new afterwards. Fewer lines alone is not
  enough: a proposal that makes the code different but not simpler is not a
  finding;
- the risk, and the check that proves the behaviour is unchanged: the tests,
  or output that is byte-identical before and after.

Rank the proposals by what they remove for their risk, and give the total net
change if all were done.
