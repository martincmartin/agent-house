"""Aggregate counts from recent Claude Code transcripts (counting only)."""

import collections
import glob
import json
import os
import re
import statistics
import sys
import time

root = os.path.expanduser("~/.claude/projects")
files = sorted(glob.glob(f"{root}/*/*.jsonl"), key=os.path.getmtime, reverse=True)[:50]
oldest = min(os.path.getmtime(path) for path in files)
print(f"sessions={len(files)} window_days={(time.time() - oldest) / 86400:.1f}")
print("projects:", collections.Counter(os.path.basename(os.path.dirname(p)) for p in files).most_common())

skills = collections.Counter()
slash = collections.Counter()
mcp = collections.Counter()
tools = collections.Counter()
hooks = collections.defaultdict(list)
hook_timeouts = collections.Counter()
denials = collections.Counter()
denial_kinds = collections.defaultdict(collections.Counter)
skill_files = collections.Counter()
cmd_re = re.compile(r"<command-name>/?([A-Za-z0-9_:.-]+)</command-name>")
skill_file_re = re.compile(r"skills/([A-Za-z0-9_.-]+)/SKILL\.md")

for path in files:
    tool_uses = {}
    entries = []
    with open(path, errors="replace") as handle:
        for line in handle:
            try:
                entry = json.loads(line)
            except ValueError:
                continue
            entries.append(entry)
            if entry.get("type") == "assistant":
                for block in entry.get("message", {}).get("content", []) or []:
                    if isinstance(block, dict) and block.get("type") == "tool_use":
                        name = block.get("name", "")
                        tools[name] += 1
                        tool_uses[block.get("id")] = block
                        if name == "Skill":
                            skills[str(block.get("input", {}).get("skill"))] += 1
                        # A skill file opened directly (Read, cat, sed), not
                        # through the Skill tool: one count per tool call.
                        for skill in set(skill_file_re.findall(json.dumps(block.get("input")))):
                            skill_files[skill] += 1
                        if name.startswith("mcp__"):
                            mcp["__".join(name.split("__")[:2])] += 1
            elif entry.get("type") == "user":
                content = entry.get("message", {}).get("content")
                text = content if isinstance(content, str) else json.dumps(content)
                for match in cmd_re.findall(text or ""):
                    slash[match] += 1
            elif entry.get("type") == "attachment":
                att = entry.get("attachment", {})
                if str(att.get("type", "")).startswith("hook_"):
                    key = (att.get("hookEvent"), att.get("hookName"), att.get("type"))
                    if att.get("durationMs") is not None:
                        hooks[key].append(att["durationMs"])
                    if att.get("timedOut"):
                        hook_timeouts[key] += 1
    for entry in entries:
        kind = entry.get("toolDenialKind")
        if entry.get("type") != "user" or not kind or kind in ("interrupted", "cancelled"):
            continue
        content = entry.get("message", {}).get("content") or []
        for block in content if isinstance(content, list) else []:
            if isinstance(block, dict) and block.get("type") == "tool_result":
                use = tool_uses.get(block.get("tool_use_id"))
                if not use:
                    continue
                name = use.get("name")
                if name == "Bash":
                    words = str(use.get("input", {}).get("command", "")).split()
                    key = "Bash: " + " ".join(words[:2])
                else:
                    key = name
                denials[key] += 1
                denial_kinds[key][kind] += 1

print("skills:", skills.most_common())
print("skill files opened directly:", skill_files.most_common())
print("slash:", slash.most_common())
print("mcp:", mcp.most_common())
print("top tools:", tools.most_common(25))
for key, durations in sorted(hooks.items(), key=lambda item: -len(item[1])):
    print("hook", key, "n=", len(durations), "median=", statistics.median(durations), "max=", max(durations))
print("hook timeouts:", dict(hook_timeouts))
print("denials:", sum(denials.values()))
for key, count in denials.most_common(30):
    print(f"  {count:3d} {key[:90]!r} {dict(denial_kinds[key])}")
