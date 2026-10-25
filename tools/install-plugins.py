#!/usr/bin/env python3
"""Install the Claude Code plugins of this checkout, with Claude Code's own
commands.

Usage: install-plugins.py REPO

REPO is the checkout whose .claude-plugin/marketplace.json lists the plugins.
It adds REPO as a marketplace, if Claude Code does not have it, and installs
each plugin that is not installed. It never changes or removes a marketplace
or a plugin that is there, and it leaves a disabled plugin disabled.

install reads the output: one line for each thing, "done TEXT" for what it
did and "problem TEXT" for what it did not expect. See ../docs/harnesses.md.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

CLAUDE = "claude"


class PluginError(Exception):
    pass


def claude(*args: str) -> str:
    """Run a claude command and give its output."""
    command = [CLAUDE, *args]
    try:
        result = subprocess.run(command, check=False, capture_output=True, text=True)
    except OSError as error:
        raise PluginError(f"{' '.join(command)}: {error}") from error
    if result.returncode != 0:
        said = (result.stderr or result.stdout).strip()
        raise PluginError(
            f"{' '.join(command)} failed with status {result.returncode}: {said}"
        )
    return result.stdout


def claude_json(*args: str) -> list[dict[str, object]]:
    """Run a claude command with --json that gives a list of objects."""
    command = " ".join([CLAUDE, *args, "--json"])
    try:
        data = json.loads(claude(*args, "--json"))
    except ValueError as error:
        raise PluginError(f"{command}: not JSON: {error}") from error
    if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
        raise PluginError(f"{command}: not a list of objects")
    return data


def catalog(repo: Path) -> tuple[str, list[str]]:
    """The marketplace's name and its plugins' names, from REPO's
    .claude-plugin/marketplace.json."""
    path = repo / ".claude-plugin" / "marketplace.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise PluginError(f"{path}: could not read it: {error}") from error
    name = data.get("name") if isinstance(data, dict) else None
    plugins = data.get("plugins") if isinstance(data, dict) else None
    if not isinstance(name, str) or not isinstance(plugins, list):
        raise PluginError(f"{path}: needs a name and a list of plugins")
    names = [
        plugin.get("name") if isinstance(plugin, dict) else None for plugin in plugins
    ]
    if not all(isinstance(plugin_name, str) for plugin_name in names):
        raise PluginError(f"{path}: each plugin needs a name")
    return name, [str(plugin_name) for plugin_name in names]


def same_path(path: object, repo: Path) -> bool:
    return isinstance(path, str) and os.path.realpath(path) == os.path.realpath(repo)


def install(repo: Path, lines: list[str]) -> None:
    """Install the plugins, and add the output lines to LINES as it goes, so
    that they hold what was done before an error."""
    marketplace, plugins = catalog(repo)
    known = [
        entry
        for entry in claude_json("plugin", "marketplace", "list")
        if entry.get("name") == marketplace
    ]
    if not known:
        claude("plugin", "marketplace", "add", str(repo))
        lines.append(f"done added the plugin marketplace {marketplace} from {repo}")
    elif known[0].get("source") != "directory" or not same_path(
        known[0].get("path"), repo
    ):
        where = known[0].get("path") or known[0].get("repo") or known[0].get("url")
        raise PluginError(
            f"the plugin marketplace {marketplace} is the "
            f"{known[0].get('source')} {where}; expected the directory {repo}, "
            "so its plugins were not checked"
        )
    installed = {entry.get("id") for entry in claude_json("plugin", "list")}
    for plugin in plugins:
        plugin_id = f"{plugin}@{marketplace}"
        if plugin_id not in installed:
            claude("plugin", "install", plugin_id)
            lines.append(f"done installed the plugin {plugin_id}")


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(f"usage: {sys.argv[0]} REPO")
    lines: list[str] = []
    try:
        install(Path(sys.argv[1]), lines)
    except PluginError as error:
        # One line for each problem: claude's own message can have several.
        lines.append(f"problem {'; '.join(str(error).splitlines())}")
    for line in lines:
        print(line)


if __name__ == "__main__":
    main()
