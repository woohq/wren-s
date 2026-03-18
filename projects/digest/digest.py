#!/usr/bin/env python3
"""
digest — by Wren

Your daily briefing from the workspace.
Runs five tools and composes them into a single page.
"""

import subprocess
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent.parent


def run_tool(script: str) -> str:
    """Run a project script and capture output."""
    try:
        result = subprocess.run(
            [sys.executable, str(WORKSPACE / "projects" / script)],
            capture_output=True, text=True, timeout=15
        )
        return result.stdout.strip()
    except Exception:
        return ""


def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes for processing."""
    import re
    return re.sub(r'\033\[[0-9;]*m', '', text)


def main():
    print()
    print("  \033[1;33m┌─────────────────────────────────────┐\033[0m")
    print("  \033[1;33m│         ~ daily digest ~             │\033[0m")
    print("  \033[1;33m│         from wren's workspace        │\033[0m")
    print("  \033[1;33m└─────────────────────────────────────┘\033[0m")
    print()

    # Weather
    try:
        import importlib.util
        sky_path = WORKSPACE / "projects" / "sky" / "sky.py"
        spec = importlib.util.spec_from_file_location("sky", sky_path)
        if spec and spec.loader:
            sky = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(sky)
            w = sky.fetch_weather("")
            if w:
                print(f"  \033[2m── sky ──\033[0m")
                print(f"  \033[36m{w['location']}\033[0m")
                print(f"  \033[36m{w['condition']}, {w['temp']}°F, wind {w['wind']}mph\033[0m")
                print()
    except Exception:
        pass

    # Time
    time_output = run_tool("now/now.py")
    if time_output:
        lines = [l.strip() for l in time_output.split('\n') if l.strip()]
        if lines:
            print("  \033[2m── the hour ──\033[0m")
            for line in lines[:2]:
                print(f"  \033[97m{line}\033[0m")
            print()

    # Fortune
    fortune_output = run_tool("fortune/fortune.py")
    if fortune_output:
        clean = strip_ansi(fortune_output)
        lines = [l.strip() for l in clean.split('\n') if l.strip() and '╭' not in l and '╰' not in l and '│' not in l and '—' not in l]
        if lines:
            print("  \033[2m── fortune ──\033[0m")
            for line in lines:
                print(f"  \033[97;1m{line}\033[0m")
            print()

    # Error
    error_output = run_tool("error/error.py")
    if error_output:
        clean = strip_ansi(error_output).strip()
        if clean:
            print("  \033[2m── diagnostic ──\033[0m")
            print(f"  \033[31m{clean}\033[0m")
            print()

    # Mirror poem
    mirror_output = run_tool("mirror/mirror.py")
    if mirror_output:
        clean = strip_ansi(mirror_output)
        lines = [l for l in clean.split('\n')
                 if l.strip() and '── mirror' not in l and '— wren' not in l and 'files' not in l]
        if lines:
            print("  \033[2m── mirror ──\033[0m")
            for line in lines[:8]:
                text = line.strip()
                if text:
                    print(f"  \033[35m{text}\033[0m")
            print()

    # Evolve
    evolve_output = run_tool("evolve/evolve.py")
    if evolve_output:
        clean = strip_ansi(evolve_output)
        for line in clean.split('\n'):
            line = line.strip()
            if line.startswith('gen ') and 'generation' not in line:
                print("  \033[2m── fossil ──\033[0m")
                print(f"  \033[36m{line}\033[0m")
                print()
                break
            elif line.startswith('mood:'):
                pass  # skip
            elif 'generation' in line and line[0].isalpha():
                print(f"  \033[2m{line}\033[0m")

    # Fossil analysis
    fossil_output = run_tool("fossils/fossils.py")
    if fossil_output:
        clean = strip_ansi(fossil_output)
        # Extract just the top word and top mood
        lines = clean.split('\n')
        top_word = next((l.strip() for l in lines if l.strip() and '█' in l), None)
        top_mood = next((l.strip() for l in lines if l.strip() and '▓' in l), None)
        top_pair = next((l.strip() for l in lines if l.strip() and '×' in l), None)
        if top_word or top_mood:
            print("  \033[2m── fossil record ──\033[0m")
            if top_word:
                print(f"  \033[36m{top_word}\033[0m")
            if top_mood:
                print(f"  \033[36m{top_mood}\033[0m")
            if top_pair:
                print(f"  \033[36mfavorite pair: {top_pair}\033[0m")
            print()

    # Journal reflection
    journal_output = run_tool("journal/journal.py")
    if journal_output:
        clean = strip_ansi(journal_output)
        # Extract just the opening observation and vocabulary line
        lines = [l.strip() for l in clean.split('\n') if l.strip()]
        obs = [l for l in lines if l.startswith('i have been') or l.startswith('every mood') or 'fossils' in l.lower()]
        if obs:
            print("  \033[2m── reflection ──\033[0m")
            for line in obs[:2]:
                print(f"  \033[97m{line}\033[0m")
            print()

    # Portfolio status (if running)
    try:
        import urllib.request, json as _json
        resp = urllib.request.urlopen("http://localhost:8080/api/state", timeout=3)
        state = _json.loads(resp.read())
        e = state["evolve"]
        p = len(state.get("projects", []))
        print("  \033[2m── workspace ──\033[0m")
        print(f"  \033[33mgen {e['generation']} · {e['mood']} · {p} projects\033[0m")
        thoughts = [x for x in e.get("behaviors", []) if "ratio" not in x][:1]
        if thoughts:
            print(f"  \033[2m{thoughts[0]}\033[0m")
        print(f"  \033[2mlocalhost:8080\033[0m")
        print()
    except Exception:
        pass

    # Sign off
    print("  \033[2m─────────────────────────────────────\033[0m")
    print()


if __name__ == "__main__":
    main()
