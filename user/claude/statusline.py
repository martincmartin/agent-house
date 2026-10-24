"""Claude Code status line.

The first line: model, effort, (git branch), session cost, context tokens,
prompt cache (time until cold, misses, tokens that a cold cache re-sends), and
the 5-hour and 7-day rate limits, each with its pace and the time until it
resets. The second line: a bar under each rate limit, in eighths of a cell.

Claude Code sends the session's data as JSON on stdin
(https://code.claude.com/docs/en/statusline). A field that is absent is left
out: rate_limits comes only on Pro and Max plans, after the first response;
effort only for a model that supports it; prompt_cache after the first
response. The context's tokens are unknown (context_window.current_usage is
null) before the first response, and again after /compact until the next one:
then total_input_tokens is 0, and the line shows "ctx ?".

Run it with -I, so that a module in the project's directory cannot shadow the
standard library: `python3 -I statusline.py`. It needs Python 3.10 or later.
How to turn it on: docs/statusline.md in agent-house.
"""

import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

RESET = "\033[0m"
DIM = "\033[2m"
CYAN = "\033[0;36m"
MAGENTA = "\033[0;35m"
GREEN = "\033[0;32m"
YELLOW = "\033[0;33m"
RED = "\033[1;31m"
# The background of a bar's empty part: the terminal's bright black.
TRACK = "\033[100m"
# 1/8 to 7/8 of a cell, filled from the left.
EIGHTHS = "▏▎▍▌▋▊▉"
# The braille pattern with no dots: one blank cell. Claude Code removes the
# spaces at the start of a status line, but not this.
BLANK = "\u2800"

FIVE_HOURS = 5 * 3600
SEVEN_DAYS = 7 * 86400


@dataclass(frozen=True)
class Config:
    """The numbers that a user can tune."""

    # A rate-limit window is over pace when its use is ahead of the part of
    # the window that has passed, and more than this percentage. The floor
    # hides the mark early in a window, when a few requests are ahead of the
    # short time that has passed.
    pace_min_used: int = 10
    # Seconds: in its last seconds, the prompt cache turns yellow and shows
    # the tokens that the next request re-sends if it goes cold.
    cache_warning: int = 300
    # Cells: the width of a rate limit's bar. Each cell has 8 steps. 16 is
    # the widest a window's text can be ("7d 100%▲ ↻23h59m"), so the bar
    # reaches at least to the end of its text.
    bar_width: int = 16


DEFAULT_CONFIG = Config()


@dataclass(frozen=True)
class Span:
    """Text in one style: an SGR escape, or "" for none. Each character that
    the status line uses is one terminal cell wide, so a span's width is its
    length."""

    text: str
    style: str = ""


SEPARATOR = Span(" · ", DIM)


def render(spans: list[Span]) -> str:
    return "".join(
        f"{span.style}{span.text}{RESET}" if span.style else span.text for span in spans
    )


def width(spans: list[Span]) -> int:
    return sum(len(span.text) for span in spans)


@dataclass(frozen=True)
class RateWindow:
    used_percentage: float
    resets_at: int | None


@dataclass(frozen=True)
class PromptCache:
    warm: bool
    expires_at: int | None
    misses: int | None
    miss_causes: list[str]
    recache_tokens_if_cold: int | None


@dataclass(frozen=True)
class Session:
    """The fields of Claude Code's input that the status line shows."""

    model: str
    model_id: str
    effort: str | None
    directory: str | None
    cost_usd: float | None
    # None while Claude Code does not know the count.
    context_tokens: int | None
    context_window_size: int | None
    cache: PromptCache | None
    five_hour: RateWindow | None
    seven_day: RateWindow | None

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "Session":
        model = data.get("model") or {}
        effort = data.get("effort") or {}
        workspace = data.get("workspace") or {}
        cost = data.get("cost") or {}
        context = data.get("context_window") or {}
        cache = data.get("prompt_cache")
        limits = data.get("rate_limits") or {}
        return cls(
            model=model.get("display_name") or "",
            model_id=model.get("id") or "",
            effort=effort.get("level"),
            directory=workspace.get("current_dir") or data.get("cwd"),
            cost_usd=cost.get("total_cost_usd"),
            context_tokens=(
                context.get("total_input_tokens")
                if context.get("current_usage") is not None
                else None
            ),
            context_window_size=context.get("context_window_size"),
            cache=_prompt_cache(cache)
            if cache and cache.get("warm") is not None
            else None,
            five_hour=_rate_window(limits.get("five_hour")),
            seven_day=_rate_window(limits.get("seven_day")),
        )


def _prompt_cache(data: dict[str, Any]) -> PromptCache:
    last_miss = data.get("last_miss_cause") or {}
    return PromptCache(
        warm=data["warm"],
        expires_at=data.get("expires_at"),
        misses=data.get("misses"),
        miss_causes=last_miss.get("causes") or [],
        recache_tokens_if_cold=data.get("recache_tokens_if_cold"),
    )


def _rate_window(data: dict[str, Any] | None) -> RateWindow | None:
    if not data or data.get("used_percentage") is None:
        return None
    return RateWindow(
        used_percentage=data["used_percentage"], resets_at=data.get("resets_at")
    )


def colour_of(value: int, limit: int) -> str:
    """Green below half of `limit`, yellow below 80%, red from 80%."""
    if value * 100 >= limit * 80:
        return RED
    if value * 2 >= limit:
        return YELLOW
    return GREEN


def tokens(count: int) -> str:
    """A token count as 412k or 1M."""
    if count >= 1_000_000 and count % 1_000_000 == 0:
        return f"{count // 1_000_000}M"
    return f"{(count + 500) // 1000}k"


def until(moment: int, now: int) -> str:
    """The time from `now` until `moment`, in epoch seconds: 3d4h, 2h05m or 12m."""
    left = max(moment - now, 0)
    days, hours, minutes = left // 86400, left % 86400 // 3600, left % 3600 // 60
    if days:
        return f"{days}d{hours}h"
    if hours:
        return f"{hours}h{minutes:02d}m"
    return f"{minutes}m"


def window(
    name: str, length: int, limit: RateWindow, now: int, config: Config
) -> list[Span]:
    """A rate-limit window: "5h 64%▲ ↻2h05m". ▲ marks a use ahead of the time
    that has passed in the window, which runs out before it resets."""
    used = round(limit.used_percentage)
    spans = [Span(f"{name} "), Span(f"{used}%", colour_of(used, 100))]
    if limit.resets_at is None:
        return spans
    passed = 100 - max(limit.resets_at - now, 0) * 100 // length
    if used > config.pace_min_used and used > passed:
        spans.append(Span("▲", RED))
    return [*spans, Span(" "), Span(f"↻{until(limit.resets_at, now)}", DIM)]


def bar(limit: RateWindow, config: Config) -> Span:
    """A bar of `config.bar_width` cells, filled to the window's use, in
    eighths of a cell."""
    fraction = min(max(limit.used_percentage / 100, 0.0), 1.0)
    full, rest = divmod(round(fraction * config.bar_width * 8), 8)
    text = "█" * full + (EIGHTHS[rest - 1] if rest else "")
    colour = colour_of(round(limit.used_percentage), 100)
    return Span(text.ljust(config.bar_width), colour + TRACK)


def cache_part(cache: PromptCache, now: int, config: Config) -> list[Span]:
    """The time until the cache goes cold, yellow in its last minutes, or
    "cold". In its last minutes, or when cold, the tokens that the next
    request re-sends. Then its misses, with the last one's cause."""
    spans = [Span("cache ")]
    if cache.warm and cache.expires_at is not None and cache.expires_at > now:
        left = cache.expires_at - now
        colour = YELLOW if left < config.cache_warning else GREEN
        spans.append(Span(until(cache.expires_at, now), colour))
    else:
        left = 0
        spans.append(Span("cold", RED))
    if cache.recache_tokens_if_cold is not None and left < config.cache_warning:
        spans += [Span(" "), Span(f"({tokens(cache.recache_tokens_if_cold)})", DIM)]
    if cache.misses:
        spans += [Span(" "), Span(f"✗{cache.misses}", YELLOW)]
        if cache.miss_causes:
            spans += [Span(" "), Span(",".join(cache.miss_causes), DIM)]
    return spans


def compact_window(settings: dict[str, Any], model_id: str) -> int | None:
    """The model's auto-compact window in settings.json (modelSettings), for
    its id without a "[1m]" suffix."""
    model_settings = settings.get("modelSettings") or {}
    window_size = (model_settings.get(model_id.split("[")[0]) or {}).get(
        "autoCompactWindow"
    )
    return window_size if isinstance(window_size, int) else None


def status_line(
    session: Session,
    branch: str | None,
    compact_limit: int | None,
    now: int,
    config: Config = DEFAULT_CONFIG,
) -> str:
    """The first line, and when there are rate limits, a second line with a
    bar under each one."""
    head = [Span(session.model, CYAN)]
    if session.effort:
        head += [Span(" "), Span(session.effort, MAGENTA)]
    if branch:
        head += [Span(" "), Span(f"({branch})", RED)]
    parts = [head]
    if session.cost_usd is not None:
        parts.append([Span(f"${session.cost_usd:.2f}")])
    if session.context_tokens is not None:
        # Coloured against the auto-compact window, else the context window.
        limit = compact_limit or session.context_window_size
        colour = colour_of(session.context_tokens, limit) if limit else ""
        parts.append([Span("ctx "), Span(tokens(session.context_tokens), colour)])
    elif session.context_window_size is not None:
        parts.append([Span("ctx "), Span("?", DIM)])
    if session.cache is not None:
        parts.append(cache_part(session.cache, now, config))
    # Each bar starts in the column of its window, which is padded to the
    # bar's width, so that the next bar does not overlap it.
    bars: list[Span] = []
    for name, length, rate_limit in (
        ("5h", FIVE_HOURS, session.five_hour),
        ("7d", SEVEN_DAYS, session.seven_day),
    ):
        if rate_limit is None:
            continue
        column = sum(width(part) + len(SEPARATOR.text) for part in parts)
        bars += [Span(BLANK * (column - width(bars))), bar(rate_limit, config)]
        part = window(name, length, rate_limit, now, config)
        parts.append([*part, Span(" " * (config.bar_width - width(part)))])
    first = render(
        [
            span
            for index, part in enumerate(parts)
            for span in ([SEPARATOR] if index else []) + part
        ]
    )
    return f"{first.rstrip()}\n{render(bars)}" if bars else first.rstrip()


def git_branch(directory: str | None) -> str | None:
    """The branch checked out in `directory`, or the short commit when HEAD is
    detached; None outside a repository."""
    where = ["-C", directory] if directory else []
    for query in (
        ["symbolic-ref", "--short", "HEAD"],
        ["rev-parse", "--short", "HEAD"],
    ):
        result = subprocess.run(
            ["git", "--no-optional-locks", *where, *query],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    return None


def read_settings() -> dict[str, Any]:
    path = (
        Path(os.environ.get("CLAUDE_CONFIG_DIR", "~/.claude")).expanduser()
        / "settings.json"
    )
    try:
        settings = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {}
    return settings if isinstance(settings, dict) else {}


def main() -> None:
    session = Session.from_json(json.load(sys.stdin))
    print(
        status_line(
            session,
            branch=git_branch(session.directory),
            compact_limit=compact_window(read_settings(), session.model_id),
            now=int(time.time()),
        )
    )


if __name__ == "__main__":
    main()
