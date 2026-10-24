"""Tests for statusline.py. `install` does not link a test_* file.

Run: python3 -B -m unittest discover -s user/claude (tools/check runs it).
"""

import re
import unittest
from typing import Any

from statusline import (
    DEFAULT_CONFIG,
    GREEN,
    RED,
    YELLOW,
    RateWindow,
    Session,
    bar,
    compact_window,
    status_line,
    tokens,
    until,
)

NOW = 1_800_000_000
OPUS = {"display_name": "Opus 5.5", "id": "claude-opus-5-5"}
RATE_LIMITS = {
    "five_hour": {"used_percentage": 63.5, "resets_at": NOW + 7530},
    "seven_day": {
        "used_percentage": 84.2,
        "resets_at": NOW + 3 * 86400 + 4 * 3600 + 100,
    },
}
ESCAPE = re.compile(r"\033\[[0-9;]*m")


def line(
    data: dict[str, Any], branch: str | None = None, compact_limit: int | None = None
) -> str:
    """The status line for the input `data`, with colours."""
    return status_line(Session.from_json(data), branch, compact_limit, NOW)


def plain(
    data: dict[str, Any], branch: str | None = None, compact_limit: int | None = None
) -> str:
    """The status line's first line for the input `data`, without colours."""
    return ESCAPE.sub("", line(data, branch, compact_limit)).split("\n")[0]


def bars(data: dict[str, Any]) -> str:
    """The status line's second line, the bars, without colours."""
    return ESCAPE.sub("", line(data)).split("\n")[1]


def context(total: int, size: int | None = 1_000_000) -> dict[str, Any]:
    """A context_window after a response: current_usage is set."""
    return {
        "total_input_tokens": total,
        "context_window_size": size,
        "current_usage": {},
    }


class StatusLineTest(unittest.TestCase):
    def test_typical(self) -> None:
        data = {
            "model": OPUS,
            "effort": {"level": "high"},
            "cost": {"total_cost_usd": 3.456},
            "context_window": context(123_456),
            "prompt_cache": {"warm": True, "expires_at": NOW + 2537, "misses": 0},
            "rate_limits": RATE_LIMITS,
        }
        self.assertEqual(
            plain(data, branch="main"),
            "Opus 5.5 high (main) · $3.46 · ctx 123k · cache 42m"
            " · 5h 64%▲ ↻2h05m · 7d 84%▲ ↻3d4h",
        )

    def test_minimal(self) -> None:
        self.assertEqual(plain({"model": {"display_name": "Haiku"}}), "Haiku")

    def test_null_fields(self) -> None:
        data = {
            "model": OPUS,
            "effort": None,
            "prompt_cache": None,
            "rate_limits": None,
        }
        self.assertEqual(plain(data), "Opus 5.5")

    def test_context_unknown_after_compact(self) -> None:
        data = {
            "model": OPUS,
            "context_window": {
                "total_input_tokens": 0,
                "context_window_size": 1_000_000,
                "current_usage": None,
            },
        }
        self.assertEqual(plain(data), "Opus 5.5 · ctx ?")

    def test_context_colour_follows_compact_window(self) -> None:
        data = {"model": OPUS, "context_window": context(560_000)}
        self.assertIn(f"ctx {RED}560k", line(data, compact_limit=700_000))
        self.assertIn(f"ctx {YELLOW}560k", line(data))

    def test_context_without_a_size_has_no_colour(self) -> None:
        data = {"model": OPUS, "context_window": context(1499, size=None)}
        self.assertTrue(line(data).endswith("ctx 1k"))

    def test_cache_late_shows_recache_and_misses(self) -> None:
        cache = {
            "warm": True,
            "expires_at": NOW + 200,
            "misses": 2,
            "last_miss_cause": {"causes": ["tools_changed", "ttl_expired_5m"]},
            "recache_tokens_if_cold": 412_000,
        }
        data = {"model": OPUS, "prompt_cache": cache}
        self.assertEqual(
            plain(data), "Opus 5.5 · cache 3m (412k) ✗2 tools_changed,ttl_expired_5m"
        )
        self.assertIn(f"cache {YELLOW}3m", line(data))

    def test_cache_early_hides_recache(self) -> None:
        cache = {
            "warm": True,
            "expires_at": NOW + 600,
            "recache_tokens_if_cold": 88_000,
        }
        data = {"model": OPUS, "prompt_cache": cache}
        self.assertIn(f"cache {GREEN}10m", line(data))
        self.assertNotIn("88k", line(data))

    def test_cache_cold(self) -> None:
        for cache in (
            {
                "warm": False,
                "expires_at": None,
                "misses": 1,
                "recache_tokens_if_cold": 88_000,
            },
            {
                "warm": True,
                "expires_at": NOW - 10,
                "misses": 1,
                "recache_tokens_if_cold": 88_000,
            },
        ):
            with self.subTest(cache=cache):
                data = {"model": OPUS, "prompt_cache": cache}
                self.assertEqual(plain(data), "Opus 5.5 · cache cold (88k) ✗1")

    def test_pace_needs_more_than_the_floor(self) -> None:
        # 8% used, about 6% of the window passed: under the floor, no mark.
        limits = {"five_hour": {"used_percentage": 8, "resets_at": NOW + 17_000}}
        self.assertEqual(
            plain({"model": OPUS, "rate_limits": limits}), "Opus 5.5 · 5h 8% ↻4h43m"
        )

    def test_pace_needs_use_ahead_of_time(self) -> None:
        # 40% used, 90% of the window passed.
        limits = {"five_hour": {"used_percentage": 40, "resets_at": NOW + 1800}}
        self.assertEqual(
            plain({"model": OPUS, "rate_limits": limits}), "Opus 5.5 · 5h 40% ↻30m"
        )

    def test_window_without_reset_time(self) -> None:
        limits = {"five_hour": {"used_percentage": 64.5}}
        self.assertEqual(
            plain({"model": OPUS, "rate_limits": limits}), "Opus 5.5 · 5h 64%"
        )


class BarTest(unittest.TestCase):
    def test_each_bar_is_under_its_window(self) -> None:
        data = {"model": OPUS, "rate_limits": RATE_LIMITS}
        first, second = plain(data), bars(data)
        five_hour, seven_day = first.index("5h"), first.index("7d")
        # 63.5% of 80 eighths is 51: 6 cells and 3 eighths.
        self.assertEqual(second[five_hour : five_hour + 10], "██████▍   ")
        # 84.2% of 80 eighths is 67: 8 cells and 3 eighths.
        self.assertEqual(second[seven_day:], "████████▍ ")
        self.assertEqual(second[:five_hour], " " * five_hour)

    def test_a_short_window_is_padded_so_that_bars_do_not_overlap(self) -> None:
        limits = {
            "five_hour": {"used_percentage": 64.5},
            "seven_day": {"used_percentage": 10},
        }
        data = {"model": OPUS, "rate_limits": limits}
        first, second = plain(data), bars(data)
        self.assertEqual(first, "Opus 5.5 · 5h 64%     · 7d 10%")
        self.assertEqual(second.index("█"), first.index("5h"))
        self.assertEqual(second.rindex("█"), first.index("7d"))

    def test_no_rate_limits_no_second_line(self) -> None:
        self.assertNotIn("\n", line({"model": OPUS, "context_window": context(1)}))

    def test_eighths(self) -> None:
        cases = {
            0: " " * 10,
            1: "▏" + " " * 9,
            50: "█████     ",
            100: "█" * 10,
            120: "█" * 10,
        }
        for used, expected in cases.items():
            with self.subTest(used=used):
                limit = RateWindow(used_percentage=used, resets_at=None)
                self.assertEqual(bar(limit, DEFAULT_CONFIG).text, expected)

    def test_colour_follows_use(self) -> None:
        limit = RateWindow(used_percentage=84.2, resets_at=None)
        self.assertTrue(bar(limit, DEFAULT_CONFIG).style.startswith(RED))


class FormatTest(unittest.TestCase):
    def test_tokens(self) -> None:
        self.assertEqual(
            [tokens(count) for count in (0, 499, 500, 123_456, 999_999, 1_000_000)],
            ["0k", "0k", "1k", "123k", "1000k", "1M"],
        )

    def test_until(self) -> None:
        self.assertEqual(
            [
                until(NOW + left, NOW)
                for left in (-5, 59, 720, 7530, 3 * 86400 + 4 * 3600)
            ],
            ["0m", "0m", "12m", "2h05m", "3d4h"],
        )


class CompactWindowTest(unittest.TestCase):
    def test_reads_the_model_settings(self) -> None:
        settings = {
            "modelSettings": {"claude-opus-5-5": {"autoCompactWindow": 700_000}}
        }
        self.assertEqual(compact_window(settings, "claude-opus-5-5[1m]"), 700_000)
        self.assertIsNone(compact_window(settings, "claude-sonnet-5-5"))
        self.assertIsNone(compact_window({}, "claude-opus-5-5"))


if __name__ == "__main__":
    unittest.main()
