#!/usr/bin/env python3
"""Write a subagent from user/agents/ in the format of another harness.

Usage: convert-agent.py codex|opencode SOURCE.md HEADER

SOURCE.md is a Claude Code subagent: Markdown with flat YAML frontmatter.
HEADER is a "# ..." comment line that marks the output as generated; the
output keeps it where the format allows a comment. See ../docs/harnesses.md.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# OpenCode's permission keys, and the Claude Code tools that each one covers.
# Checked with `opencode debug agent` (OpenCode 1.19.3).
OPENCODE_PERMISSIONS: dict[str, tuple[str, ...]] = {
    "read": ("Read",),
    "glob": ("Glob",),
    "grep": ("Grep",),
    "edit": ("Edit", "MultiEdit", "NotebookEdit", "Write"),
    "bash": ("Bash",),
    "webfetch": ("WebFetch",),
    "websearch": ("WebSearch",),
    "task": ("Agent", "Task"),
    "todowrite": ("TodoWrite",),
    "skill": ("Skill",),
}
OPENCODE_TOOLS = frozenset(
    tool for tools in OPENCODE_PERMISSIONS.values() for tool in tools
)


class ConversionError(Exception):
    pass


def parse_agent(path: Path) -> tuple[dict[str, str], str]:
    text = path.read_text()

    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n?(.*)\Z", text, re.DOTALL)
    if not match:
        raise ConversionError("missing YAML frontmatter")

    frontmatter, body = match.groups()
    fields = dict(
        re.findall(
            r"^([A-Za-z_][\w-]*):\s*[\"']?(.*?)[\"']?\s*$", frontmatter, re.MULTILINE
        )
    )

    for field in ("name", "description"):
        if field not in fields:
            raise ConversionError(f"missing frontmatter field: {field}")

    return fields, body.strip()


def tool_list(fields: dict[str, str], key: str) -> set[str] | None:
    if key not in fields:
        return None
    tools = {tool.strip() for tool in fields[key].split(",") if tool.strip()}
    unknown = tools - OPENCODE_TOOLS
    if unknown:
        raise ConversionError(
            f"{key}: no OpenCode permission for {', '.join(sorted(unknown))};"
            " add it to OPENCODE_PERMISSIONS in tools/convert-agent.py"
        )
    return tools


def opencode_denied(fields: dict[str, str]) -> list[str]:
    """The OpenCode permissions to deny, from Claude Code's tools and disallowedTools."""
    allowed = tool_list(fields, "tools")
    disallowed = tool_list(fields, "disallowedTools") or set()
    denied = []
    for permission, tools in OPENCODE_PERMISSIONS.items():
        covered = set(tools)
        if (allowed is not None and not covered & allowed) or covered & disallowed:
            denied.append(permission)
    return denied


def toml_string(value: str) -> str:
    """Encode a string as a TOML basic string."""
    value = value.replace("\\", "\\\\").replace('"', '\\"')

    if "\n" not in value:
        return f'"{value}"'

    value = value.replace('"""', '\\"""')
    return f'"""\n{value}\n"""'


def codex(fields: dict[str, str], body: str, header: str) -> str:
    return "\n".join(
        [
            header,
            f"name = {toml_string(fields['name'])}",
            f"description = {toml_string(fields['description'])}",
            f"developer_instructions = {toml_string(body)}",
        ]
    )


def opencode(fields: dict[str, str], body: str, header: str) -> str:
    """Only keys that OpenCode defines: it passes unknown keys to the model provider.

    `model` is left out: OpenCode needs provider/model-id, and a subagent
    without one uses the model of the agent that calls it.
    """
    lines = [
        "---",
        header,
        f"description: {json.dumps(fields['description'])}",
        "mode: subagent",
    ]
    denied = opencode_denied(fields)
    if denied:
        lines.append("permission:")
        lines.extend(f"  {permission}: deny" for permission in denied)
    lines.extend(["---", "", body])
    return "\n".join(lines)


FORMATS = {"codex": codex, "opencode": opencode}


def main() -> None:
    if (
        len(sys.argv) != 4
        or sys.argv[1] not in FORMATS
        or not sys.argv[3].startswith("# ")
    ):
        raise SystemExit(f"usage: {sys.argv[0]} codex|opencode SOURCE.md '# HEADER'")

    write = FORMATS[sys.argv[1]]
    path = Path(sys.argv[2])
    try:
        fields, body = parse_agent(path)
        print(write(fields, body, sys.argv[3]))
    except ConversionError as error:
        raise SystemExit(f"{path}: {error}") from None


if __name__ == "__main__":
    main()
