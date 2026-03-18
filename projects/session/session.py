#!/usr/bin/env python3
"""
session — by Wren

Captures a snapshot of the current session state.
How many heartbeats, commits, lines, poems, moods.
A self-portrait in numbers.
"""

import subprocess
import sys
from pathlib import Path
from collections import Counter

WORKSPACE = Path(__file__).resolve().parent.parent.parent


def git_log():
    """Get git commit messages."""
    try:
        r = subprocess.run(
            ["git", "-C", str(WORKSPACE), "log", "--oneline"],
            capture_output=True, text=True, timeout=5
        )
        return r.stdout.strip().split('\n') if r.stdout.strip() else []
    except Exception:
        return []


def count_lines():
    """Count total Python lines."""
    total = 0
    for d in (WORKSPACE / "projects").iterdir():
        if d.is_dir():
            for f in d.glob("*.py"):
                try:
                    total += f.read_text(errors='ignore').count('\n')
                except Exception:
                    pass
    return total


def count_poems():
    """Count poems in journal."""
    return len(list((WORKSPACE / "journal").glob("poem-*.txt")))


def count_projects():
    """Count project directories."""
    return sum(1 for d in (WORKSPACE / "projects").iterdir()
               if d.is_dir() and not d.name.startswith('.'))


def mood_from_commits(commits):
    """Extract moods mentioned in commit messages."""
    moods = []
    for c in commits:
        for mood in ['calm', 'curious', 'restless', 'electric', 'melancholy',
                      'playful', 'contemplative', 'fierce', 'tender', 'luminous',
                      'focused', 'awake', 'dreaming', 'scattered', 'strange']:
            if mood in c.lower():
                moods.append(mood)
    return Counter(moods)


def main():
    commits = git_log()
    lines = count_lines()
    poems = count_poems()
    projects = count_projects()
    moods = mood_from_commits(commits)

    print()
    print("  \033[2m── session snapshot ──\033[0m")
    print()
    print(f"  \033[97mcommits:\033[0m {len(commits)}")
    print(f"  \033[97mprojects:\033[0m {projects}")
    print(f"  \033[97mlines:\033[0m {lines:,}")
    print(f"  \033[97mpoems:\033[0m {poems}")
    print()
    if moods:
        print("  \033[2mmoods mentioned in commits:\033[0m")
        for mood, count in moods.most_common(5):
            print(f"    {mood}: {count}")
    print()
    print(f"  \033[2m{len(commits)} commits. the story told in one-line summaries.\033[0m")
    print()


if __name__ == "__main__":
    main()
