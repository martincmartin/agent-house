# Trim `user/AGENTS.md`

The options, the decisions and both reviews are in [PLAN.md](PLAN.md).

- 2026-10-21: a code review no longer always uses a subagent. Only a session
  that made the changes starts one; any other session reviews by itself. The
  `review-quality-slidev` subagent is gone, and its criteria are in the
  `review-general` and `review-simplify` skills. See
  `tasks/2026-10-21-review-without-subagent/`.
