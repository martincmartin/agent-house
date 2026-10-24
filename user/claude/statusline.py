"""Claude Code status line, one line.

Model, effort, (git branch), session cost, context tokens, prompt cache (time
until cold, misses, tokens that a cold cache re-sends), and the 5-hour and
7-day rate limits, each with its pace and the time until it resets.

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


DEFAULT_CONFIG = Config()


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


def window(name: str, length: int, limit: RateWindow, now: int, config: Config) -> str:
    """A rate-limit window: "5h 64%▲ ↻2h05m". ▲ marks a use ahead of the time
    that has passed in the window, which runs out before it resets."""
    used = round(limit.used_percentage)
    text = f"{name} {colour_of(used, 100)}{used}%{RESET}"
    if limit.resets_at is None:
        return text
    passed = 100 - max(limit.resets_at - now, 0) * 100 // length
    if used > config.pace_min_used and used > passed:
        text += f"{RED}▲{RESET}"
    return text + f" {DIM}↻{until(limit.resets_at, now)}{RESET}"


def cache_part(cache: PromptCache, now: int, config: Config) -> str:
    """The time until the cache goes cold, yellow in its last minutes, or
    "cold". In its last minutes, or when cold, the tokens that the next
    request re-sends. Then its misses, with the last one's cause."""
    if cache.warm and cache.expires_at is not None and cache.expires_at > now:
        left = cache.expires_at - now
        colour = YELLOW if left < config.cache_warning else GREEN
        text = f"cache {colour}{until(cache.expires_at, now)}{RESET}"
    else:
        left = 0
        text = f"cache {RED}cold{RESET}"
    if cache.recache_tokens_if_cold is not None and left < config.cache_warning:
        text += f" {DIM}({tokens(cache.recache_tokens_if_cold)}){RESET}"
    if cache.misses:
        text += f" {YELLOW}✗{cache.misses}{RESET}"
        if cache.miss_causes:
            text += f" {DIM}{','.join(cache.miss_causes)}{RESET}"
    return text


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
    head = f"{CYAN}{session.model}{RESET}"
    if session.effort:
        head += f" {MAGENTA}{session.effort}{RESET}"
    if branch:
        head += f" {RED}({branch}){RESET}"
    parts = [head]
    if session.cost_usd is not None:
        parts.append(f"${session.cost_usd:.2f}")
    if session.context_tokens is not None:
        # Coloured against the auto-compact window, else the context window.
        limit = compact_limit or session.context_window_size
        colour = colour_of(session.context_tokens, limit) if limit else ""
        end = RESET if limit else ""
        parts.append(f"ctx {colour}{tokens(session.context_tokens)}{end}")
    elif session.context_window_size is not None:
        parts.append(f"ctx {DIM}?{RESET}")
    if session.cache is not None:
        parts.append(cache_part(session.cache, now, config))
    if session.five_hour is not None:
        parts.append(window("5h", FIVE_HOURS, session.five_hour, now, config))
    if session.seven_day is not None:
        parts.append(window("7d", SEVEN_DAYS, session.seven_day, now, config))
    return f" {DIM}·{RESET} ".join(parts)


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
