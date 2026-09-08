#!/usr/bin/env python3
"""Validate the high-agency skill package using only the standard library."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
SKILL = ROOT / "skills" / "high-agency" / "SKILL.md"
RESULTS_LINK = "eval/RESULTS.md"
REQUIRED_LINKS = {"assets/banner.png", RESULTS_LINK}


def fail(message: str, failures: list[str]) -> None:
    failures.append(message)


def main() -> int:
    failures: list[str] = []

    for path in (README, SKILL, ROOT / "LICENSE"):
        if not path.is_file():
            fail(f"missing required file: {path.relative_to(ROOT)}", failures)

    if failures:
        return report(failures)

    readme = README.read_text(encoding="utf-8")
    skill = SKILL.read_text(encoding="utf-8")

    frontmatter = re.match(r"\A---\n(?P<meta>.*?)\n---\n(?P<body>.*)\Z", skill, re.DOTALL)
    if not frontmatter:
        fail("SKILL.md must have complete YAML frontmatter", failures)
        body = skill
    else:
        metadata: dict[str, str] = {}
        for line in frontmatter.group("meta").splitlines():
            if ":" not in line:
                fail(f"invalid frontmatter line: {line!r}", failures)
                continue
            key, value = line.split(":", 1)
            metadata[key.strip()] = value.strip()
        if metadata.get("name") != "high-agency":
            fail("frontmatter name must be high-agency", failures)
        if len(metadata.get("description", "")) < 80:
            fail("frontmatter description must explain behavior and activation", failures)
        body = frontmatter.group("body")

    required_readme_text = (
        ".agents/skills",
        ".claude/skills",
        "$high-agency",
        "python3 scripts/check.py",
        "eval/RESULTS.md",
    )
    for expected in required_readme_text:
        if expected not in readme:
            fail(f"README.md is missing required text: {expected}", failures)

    links = re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", readme)
    for expected in REQUIRED_LINKS:
        if expected not in links:
            fail(f"README.md must link to {expected}", failures)
    for link in links:
        if re.match(r"(?:https?://|mailto:|#)", link):
            continue
        target = ROOT / link
        if target.exists():
            continue
        fail(f"broken local README link: {link}", failures)

    for label, text in (("README.md", readme), ("SKILL.md", skill)):
        if "/Users/" in text:
            fail(f"{label} contains a private absolute path", failures)

    return report(failures)


def report(failures: list[str]) -> int:
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print("PASS: high-agency package checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
