---
name: statusline-legend
description: What each part of the Claude Code status line means, for this user's own status line (agent-house's statusline.py) and its VS Code version (the status band plugin above the prompt) - the gauges, their bars, colours and widths, the pace mark, cache misses, and what each part of the cost breakdown counts. Read when the user asks what something in their status line or status band means. Claude Code only.
---

# The status line: what each part means

This is the legend of the status line that `~/.claude/statusline.py` prints.
That file is a link into the agent-house repo
(`user/claude/statusline.py`). The rest of its documentation (how to turn it
on, its tests, the facts about Claude Code's input) is in agent-house's
`docs/statusline.md`: find the repo with `readlink ~/.claude/statusline.py`.
When this legend and the script disagree, the script is right: read it, and
tell the user.

Two lines, for example (the costs are from a real session, on 2026-10-24):

```text
cache 42m ✗2 ttl1h · ctx 123k  · 5h 40% ↻2h05m   · 7d 84%▲ ↻3d4h    · Opus 5.5 high (main) ~/Develop/stem/watches
█████▍               ██▎         ████████▊         ████████▊████▌     $25.01 = read 10.94 · write 6.13 (miss 0.55) · out 3.64 · think 2.21 · other 2.08
```

On the left, a column for each gauge: its text, over a bar. On the right, the
session: the model, its effort, the git branch and the working directory, over
the session's cost and what it was spent on.

## The gauges

- **The prompt cache:** the time until it goes cold, or `cold`. In its last
  minutes, and when cold, the tokens that the next request writes again, in
  parentheses. Then `✗` and the session's cache misses, with short names for
  the last miss's causes when Claude Code gives them (`SHORT_CAUSES` in the
  script; a cause with no short name keeps its own). The bar is the part of
  the cache's lifetime (`ttl`) that has passed: empty after a request, and
  full when the cache goes cold.
- **The context, in tokens,** against the model's `autoCompactWindow` in
  `settings.json` (`modelSettings`), else against the context window. `ctx ?`
  means that Claude Code does not know the count yet (before the first
  response, and after `/compact` until the next one); then the bar is empty.
- **The 5-hour and 7-day rate limits:** the percentage used, and the time until
  each resets (`↻`). The bar is solid to the lower of the use and the part of
  the window that has passed, and shaded (greyer) between the two. In a green
  bar, the shade is budget that you have not used; in a yellow or red one, it
  is use beyond pace. `▲` marks a use ahead of pace.

## Colours

A colour means that a gauge needs your attention:

- **A rate limit** is green on or behind pace, however much is used, and below
  a floor of use (`pace_min_used`). It is yellow ahead of pace: at the average
  rate so far, it runs out before it resets. It is red when, at that rate, it
  runs out within a part of the window (`alert_within`: 0.1 is 30 minutes of
  5 hours, or 17 hours of 7 days). Without a reset time, it is coloured as the
  context is.
- **The context** is green below 50% of its limit, yellow from 50%, and red
  from 80%.
- **The cache** is yellow in its last minutes (`cache_warning`), and red when
  cold.

## Bars and widths

The bars fill in eighths of a cell, with Unicode's left eighth blocks (`▏` to
`▉`), the finest step of a bar in plain text. Where two colours meet in a
cell, the block is the first colour on the second as its background. The empty
part of a bar is the track, in the terminal's bright black, and its end is
100%. The bars' colours are 256-colour (`OK`, `WARN` and `ALERT`), because a
shade needs a second green, yellow and red.

Each bar is at least as wide as the widest text of its gauge, and the text is
padded to it, so the columns do not move when the text changes: cache 18
cells ("cache cold (1000k)"), context 9 ("ctx 1000k"), 5h 15 ("5h 100%▲
↻4h59m"), 7d 16 ("7d 100%▲ ↻23h59m"). These are `CACHE_WIDTH` and the others
in the script, where a test checks each one. The cache's column grows when its
text is longer, with its misses.

## The cost breakdown

The total is Claude Code's `cost.total_cost_usd`, the same as `/usage`'s
"Total cost": the session's tokens at list price. The parts are summed from
the token usage of each response in the session's transcript and in its
subagents' transcripts, at the list prices in `prices.json`, beside the script:

- **read:** cache reads. Each request reads the whole context from the cache,
  so this part grows with the context's size times the number of requests.
- **write:** cache writes, at 1.25 times the input price for the 5-minute
  cache and 2 times for the 1-hour one. Each new token of the conversation is
  written once. `(miss …)` is the part that cache misses wrote again
  (`prompt_cache.miss_recache_tokens`): after a miss, the whole context is
  written again.
- **out** and **think:** output tokens. Thinking is billed as output; the API
  reports it apart.
- **in:** input that is not cached. Claude Code marks the prompt for caching,
  so a miss is billed as a cache write, not as input. Only the few tokens after
  the last cache marker of each request are uncached input, so this part is
  usually too small to show.
- **other:** the part of the total that the transcripts do not explain:
  requests that write no transcript (compactions, prompt suggestions, and the
  Haiku calls that WebFetch and WebSearch make), and responses that are not
  priced (a model that is not in `prices.json`, or fast mode). The status line
  cannot split it: compare the transcripts with `/usage`'s "Usage by model".
  agent-house's `docs/statusline.md` has one session's measurement.

A part under half a cent is not shown.

## The VS Code status band

In the VS Code panel, the plugin `status-band` (agent-house's
`plugins/status-band/`, `docs/status-band.md`) draws the same gauges above the
prompt box, with the same colours and pace rules. It differs in these ways:

- **The layout:** a column for each gauge (cache, ctx, 5h, 7d), its text over
  a thin bar with round ends, then a row with the cost and its parts. The
  bars are SVG, so the eighths and the widths above apply to the CLI line
  only.
- **The cache:** the time until it goes cold, from the main transcript's last
  response and the lifetime of the cache entries that the last writer wrote.
  It can be a few seconds late. It shows no tokens to re-send and no misses
  (`✗`), and the cost has no `(miss …)`: a plugin does not get these numbers.
- **The context** shows its limit (`ctx 231k/500k`): the smaller of the
  context window and the model's `autoCompactWindow`.
- **A rate limit** shows its percentage as Claude Code gives it, to one
  decimal (`23.5%`).
- **It refreshes** each 10 seconds, and when Claude Code reports a change.
- **The prices:** once a day, it reads Anthropic's pricing page. When
  `prices.json` differs from it, a yellow line names each difference
  (`claude-sonnet-5-5 cache_read 0.2 → 0.1`, `new claude-opus-6`,
  `gone claude-opus-4`). agent-house's `tools/update-prices.ts` updates the
  file. When it cannot read the page, a dim line says why.
