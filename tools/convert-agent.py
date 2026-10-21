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
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Capability:
    """Something a subagent can be kept from doing.

    claude_tools are the Claude Code tools that do it, opencode_permission is
    OpenCode's permission key for it, and action says it in an instruction,
    for Codex, which has no per-agent permissions.
    """

    claude_tools: tuple[str, ...]
    opencode_permission: str
    action: str


# OpenCode's keys were checked with `opencode debug agent` (OpenCode 1.19.3).
CAPABILITIES = (
    Capability(("Read",), "read", "read files"),
    Capability(("Glob",), "glob", "find files by name"),
    Capability(("Grep",), "grep", "search file contents"),
    Capability(
        ("Edit", "MultiEdit", "NotebookEdit", "Write"), "edit", "edit or write files"
    ),
    Capability(("Bash",), "bash", "run shell commands"),
    Capability(("WebFetch",), "webfetch", "fetch web pages"),
    Capability(("WebSearch",), "websearch", "search the web"),
    Capability(("Agent", "Task"), "task", "start subagents"),
    Capability(("TodoWrite",), "todowrite", "use the todo list"),
    Capability(("Skill",), "skill", "use skills"),
)
KNOWN_TOOLS = frozenset(
    tool for capability in CAPABILITIES for tool in capability.claude_tools
)


class ConversionError(Exception):
    pass


def scalar_text(value: str) -> str:
    """Read the supported single-line YAML strings; reject other syntax."""
    if re.fullmatch(r"'(?:[^']|'')*'", value):
        return value[1:-1].replace("''", "'")
    if re.fullmatch(r'"[^"\\]*"', value):
        return value[1:-1]
    if (
        not value
        or value[0] in "-+0123456789.~?:,[]{}#&*!|>'\"%@`"
        or value.lower()
        in {"true", "false", "null", "yes", "no", "on", "off", "y", "n"}
        or re.search(r":(?:\s|$)|\s#", value)
    ):
        raise ConversionError("unsupported YAML value; use a single-line string")
    return value


def parse_agent(path: Path) -> tuple[dict[str, str], str]:
    text = path.read_text()

    match = re.match(r"\A---[ \t]*\n(.*?)\n---[ \t]*(?:\n|\Z)(.*)\Z", text, re.DOTALL)
    if not match:
        raise ConversionError("missing YAML frontmatter")

    frontmatter, body = match.groups()
    fields: dict[str, str] = {}
    for line_number, line in enumerate(frontmatter.splitlines(), start=2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        field_match = re.fullmatch(r"([A-Za-z_][\w-]*)[ \t]*:[ \t]+(.*)", line)
        if not field_match:
            raise ConversionError(f"line {line_number}: unsupported YAML field")
        key, value = field_match.groups()
        if key in fields:
            raise ConversionError(f"line {line_number}: duplicate field: {key}")
        try:
            fields[key] = scalar_text(value.rstrip())
        except ConversionError as error:
            raise ConversionError(f"line {line_number}: {key}: {error}") from None

    for field in ("name", "description"):
        if field not in fields:
            raise ConversionError(f"missing frontmatter field: {field}")

    return fields, body.strip()


def tool_list(fields: dict[str, str], key: str) -> set[str] | None:
    if key not in fields:
        return None
    tools = {tool.strip() for tool in fields[key].split(",") if tool.strip()}
    unknown = tools - KNOWN_TOOLS
    if unknown:
        raise ConversionError(
            f"{key}: unknown tool {', '.join(sorted(unknown))};"
            " add it to CAPABILITIES in tools/convert-agent.py"
        )
    return tools


def denied_capabilities(fields: dict[str, str]) -> list[Capability]:
    """What the subagent may not do, from Claude Code's tools and disallowedTools."""
    allowed = tool_list(fields, "tools")
    disallowed = tool_list(fields, "disallowedTools") or set()
    denied = []
    for capability in CAPABILITIES:
        covered = set(capability.claude_tools)
        if (allowed is not None and not covered & allowed) or covered & disallowed:
            denied.append(capability)
    return denied


def toml_string(value: str) -> str:
    """Encode a string as a TOML basic string."""
    value = value.replace("\\", "\\\\").replace('"', '\\"')

    if "\n" not in value:
        return f'"{value}"'

    value = value.replace('"""', '\\"""')
    return f'"""\n{value}\n"""'


def codex(fields: dict[str, str], body: str, header: str) -> str:
    """Codex has no per-agent permissions: a custom agent runs in the sandbox of
    the session that starts it. So the limits become an instruction.
    """
    denied = denied_capabilities(fields)
    if denied:
        actions = [capability.action for capability in denied]
        listed = (
            ", ".join(actions[:-1]) + (" or " if len(actions) > 1 else "") + actions[-1]
        )
        body += f"\n\nDo not {listed}."
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
    denied = denied_capabilities(fields)
    if denied:
        lines.append("permission:")
        lines.extend(
            f"  {capability.opencode_permission}: deny" for capability in denied
        )
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
