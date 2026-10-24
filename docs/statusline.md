# The Claude Code status line

**Covers:** what `user/claude/statusline.py` shows, how to turn it on, how it
is tested, and the facts about Claude Code's input that it depends on.
**Read before** you change the status line.
**Tasks:** `tasks/2026-10-24-per-harness-files/` (why it is in
`user/claude/`, and why only Claude Code has one).

## What it shows

Two lines, for example:

```text
cache 42m ✗2 ttl1h · ctx 123k  · 5h 40% ↻2h05m   · 7d 84%▲ ↻3d4h    · Opus 5.5 high (main)
█████▍               █▋          ████████▊         ████████▊████▌     $3.46
```

On the left, a column for each gauge: its text, over a bar. On the right, the
session: the model, its effort and the git branch of the working directory,
over the session's cost.

- **The prompt cache:** the time until it goes cold, or `cold`. In its last
  minutes, and when cold, the tokens that the next request writes again, in
  parentheses. Then `✗` and the session's cache misses, with short names for
  the last miss's causes when Claude Code gives them (`SHORT_CAUSES` in
  `statusline.py`; a cause with no short name keeps its own). The bar is the
  part of the cache's lifetime (`ttl`) that has passed: empty after a request,
  and full when the cache goes cold.
- **The context, in tokens,** against the model's `autoCompactWindow` in
  `settings.json` (`modelSettings`), else against the context window. `ctx ?`
  means that Claude Code does not know the count yet; then the bar is empty.
- **The 5-hour and 7-day rate limits:** the percentage used, and the time until
  each resets. The bar is solid to the lower of the use and the part of the
  window that has passed, and shaded (greyer) between the two. In a green bar,
  the shade is budget that you have not used; in a yellow or red one, it is
  use beyond pace. `▲` marks a use ahead of pace.

**Colours** mean that a gauge needs your attention:

- **A rate limit** is green on or behind pace, however much is used, and below
  a floor of use. It is yellow ahead of pace: at the average rate so far, it
  runs out before it resets. It is red when, at that rate, it runs out within
  a part of the window (`alert_within`). Without a reset time, it is coloured
  as the context is.
- **The context** is green below 50% of its limit, yellow from 50%, and red
  from 80%.
- **The cache** is yellow in its last minutes, and red when cold.

**The bars** fill in eighths of a cell, with Unicode's left eighth blocks (`▏`
to `▉`), the finest step of a bar in plain text. Where two colours meet in a
cell, the block is the first colour on the second as its background. The empty
part of a bar is the track, in the terminal's bright black, and its end is
100%. The bars' colours are 256-colour (`OK`, `WARN` and `ALERT` in
`statusline.py`), because a shade needs a second green, yellow and red. Each
bar is at least as wide as the widest text of its gauge (`CACHE_WIDTH` and
the others; a test checks each one), and the text is padded to it, so the
columns do not move when the text changes. The cache's column grows when its
text is longer, with its misses.

`Config` in `statusline.py` holds the numbers that you can tune: the pace
floor, when a rate limit turns red, and when the cache turns yellow.

## Turn it on

`install` links the script to `~/.claude/statusline.py`. It does not edit
`~/.claude/settings.json`, because Claude Code writes that file
([`harnesses.md`](harnesses.md#files-for-one-harness)). Add this to it by
hand:

```json
"statusLine": {
  "type": "command",
  "command": "/opt/homebrew/bin/python3 -I ~/.claude/statusline.py",
  "refreshInterval": 60
}
```

- **The script needs Python 3.10 or later.** On macOS, `/usr/bin/python3` is
  3.9, so the command names Homebrew's Python. A cloud session has the script
  but not this entry, so it shows no status line.
- **`-I`** keeps a module in the project's directory from shadowing the
  standard library.
- **`refreshInterval`** runs the script again each 60 seconds, so that the
  countdowns move when no message arrives.

## Test it

`user/claude/test_statusline.py` tests the line for given inputs, at a fixed
time. `tools/check` runs it, with ruff and mypy. `install` does not link a
`test_*` file.

## Claude Code's input

Claude Code sends the session's data as JSON on stdin
([status line docs](https://code.claude.com/docs/en/statusline), read
2026-10-24). These facts are easy to get wrong:

- **After `/compact`, the context's size is not known.**
  `context_window.current_usage` is `null`, and `total_input_tokens` is `0`,
  until the next response. The script shows `ctx ?`, not `ctx 0k`. The same is
  true before the first response of a session.
- **A compaction is not a cache miss.** `prompt_cache.misses` counts requests
  that wrote again what the cache already held, with no compaction to explain
  it. Claude Code counts a compaction in `expected_rebuilds`.
- **A warm cache after `/compact` is real.** The system prompt, the tools and
  the instructions do not change, so the next request reads them from the
  cache.
- **`prompt_cache.recache_tokens_if_cold` is `null` after a compaction,** until
  the next request.
- **`rate_limits` comes only on Pro and Max plans,** after the first response.
  Each window can be absent.
- **Claude Code removes the spaces at the start of a line** that the script
  prints (seen on 2026-10-24; the docs do not say so). So the empty part of a
  bar is braille blanks (U+2800), which show as empty cells: an empty bar at
  the start of the second line keeps its place.
