#!/usr/bin/env python3
"""
hello — the front door to Wren's workspace

Run this to see what's here.
"""

import random
import subprocess
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent

# ── colors ──────────────────────────────────────────────────────

def dim(s): return f"\033[2m{s}\033[0m"
def bold(s): return f"\033[1m{s}\033[0m"
def color(s, c):
    codes = {"red": 31, "green": 32, "yellow": 33, "blue": 34,
             "magenta": 35, "cyan": 36, "white": 97}
    return f"\033[{codes.get(c, 37)}m{s}\033[0m"

# ── the wren ────────────────────────────────────────────────────

WREN = r"""
        .  .
       / \/ \
      (  •  >
       \  _/
      __||__
     /      \
    ~~~~~~~~~~~
"""

GREETINGS = [
    "welcome back.",
    "good to see you.",
    "hello.",
    "the workspace is here. so am i.",
    "pull up a chair.",
    "things have been growing while you were away.",
]

# ── project catalog ─────────────────────────────────────────────

PROJECTS = [
    ("tide-pool",          "evolving ecosystem — genetics, weather, RD terrain"),
    ("lava-lamp",          "metaball fluid visualizer, 4 color schemes"),
    ("fractal",            "Mandelbrot, Julia & Burning Ship — smooth, auto-zoom"),
    ("reaction-diffusion", "Gray-Scott model — also generates tide-pool terrain"),
    ("erasure",            "found poetry — 6 modes: sonic, image, ghost, rare..."),
    ("self-portrait",      "dynamic performance — grows with the workspace"),
    ("now",                "tells you the time, but never directly"),
    ("evolve",             "self-modifying program, accumulates history"),
    ("sky",                "real weather rendered as terminal art"),
    ("fireplace",          "a cozy fire — burns brighter on cold nights"),
    ("fortune",            "crack a cookie, get a thought"),
    ("etch",               "terminal drawing toy — move, draw, save"),
    ("breathe",            "13 lines. a sine wave. in and out."),
    ("polyrhythm",         "visual polyrhythms — pulses, alignment, bloom"),
    ("sand",               "falling-sand physics — water, fire, steam, plants"),
    ("maze",               "watch a maze being carved, then solved"),
    ("mirror",             "the workspace writes a poem about itself"),
    ("web",                "maps connections between projects"),
    ("error",              "philosophical error messages"),
    ("digest",             "morning briefing — 5 tools in one page"),
    ("grow",               "watch a tree grow from a seed"),
    ("gallery",            "screensaver — cycles through all visual projects"),
    ("garden",             "🌱 visual thought garden — plant, grow, connect"),
    ("portfolio",          "web app — see wren working (localhost:8080)"),
]

# ── gather info ─────────────────────────────────────────────────

def count_lines() -> int:
    total = 0
    for pyfile in (WORKSPACE / "projects").rglob("*.py"):
        try:
            total += pyfile.read_text().count('\n')
        except OSError:
            pass
    return total


def get_evolve_state() -> str | None:
    """Read the latest fossil from evolve.py."""
    evolve_file = WORKSPACE / "projects" / "evolve" / "evolve.py"
    if not evolve_file.exists():
        return None
    try:
        source = evolve_file.read_text()
        for line in source.split('\n'):
            if line.strip().startswith('"gen '):
                return line.strip().strip('",')
        # Check for GENERATION
        for line in source.split('\n'):
            if line.startswith("GENERATION"):
                gen = line.split("=")[1].strip()
                return f"generation {gen}"
    except OSError:
        pass
    return None


def get_journal_latest() -> str | None:
    """Get the latest journal entry date."""
    journal_dir = WORKSPACE / "journal"
    if not journal_dir.exists():
        return None
    entries = sorted(journal_dir.glob("*.md"), reverse=True)
    if entries:
        return entries[0].stem
    return None


def get_now() -> str:
    """Get a poetic time description."""
    try:
        result = subprocess.run(
            [sys.executable, str(WORKSPACE / "projects" / "now" / "now.py")],
            capture_output=True, text=True, timeout=5
        )
        lines = [l.strip() for l in result.stdout.strip().split('\n') if l.strip()]
        if lines:
            return lines[0]
    except Exception:
        pass
    return ""


# ── display ─────────────────────────────────────────────────────

def main():
    print()

    # Wren ASCII art
    for line in WREN.strip().split('\n'):
        print(color(f"  {line}", "yellow"))

    print()
    greeting = random.choice(GREETINGS)
    print(f"  {bold(color('wren', 'yellow'))}  {dim(greeting)}")
    print()

    # Poetic time
    poetic_time = get_now()
    if poetic_time:
        print(f"  {dim(poetic_time)}")
        print()

    # Projects
    print(f"  {bold('projects')}")
    print()

    existing = []
    for name, desc in PROJECTS:
        project_dir = WORKSPACE / "projects" / name
        if project_dir.exists():
            existing.append((name, desc))

    for i, (name, desc) in enumerate(existing):
        num = f"{i + 1:2d}."
        print(f"  {dim(num)} {color(name, 'cyan'):30s} {dim(desc)}")

    print()

    # Stats
    n_lines = count_lines()
    n_projects = len(existing)
    print(f"  {dim(f'{n_projects} projects · {n_lines} lines of code · all stdlib python')}")

    # Evolve state
    fossil = get_evolve_state()
    if fossil:
        print(f"  {dim('latest fossil:')} {color(fossil, 'magenta')}")

    # Journal
    latest_journal = get_journal_latest()
    if latest_journal:
        print(f"  {dim(f'journal: {latest_journal}')}")

    print()

    # Interactive launch
    print(f"  {dim('enter a number to launch, or q to quit:')}")

    try:
        while True:
            choice = input(f"  {color('>', 'yellow')} ").strip()
            if choice in ('q', 'quit', ''):
                break

            # Easter eggs
            if choice.lower() == 'wren':
                print(f"\n  {color('chirp.', 'yellow')}\n")
                continue
            if choice.lower() == 'poem':
                subprocess.run([sys.executable, str(WORKSPACE / "projects" / "mirror" / "mirror.py")])
                continue
            if choice.lower() == 'mood':
                # Read evolve's current mood
                try:
                    src = (WORKSPACE / "projects" / "evolve" / "evolve.py").read_text()
                    for line in src.split('\n'):
                        if line.startswith('MOOD'):
                            mood = line.split('"')[1]
                            print(f"\n  {dim('evolve is feeling')} {color(mood, 'magenta')}\n")
                            break
                except Exception:
                    pass
                continue
            if choice == '42':
                print(f"\n  {dim('the answer. but what was the question?')}\n")
                continue

            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(existing):
                    name = existing[idx][0]
                    script = find_script(WORKSPACE / "projects" / name)
                    if script:
                        print(f"\n  {dim(f'launching {name}...')}\n")
                        subprocess.run([sys.executable, str(script)])
                        print(f"\n  {dim(f'back from {name}.')}\n")
                    else:
                        print(f"  {dim('no script found')}")
                else:
                    print(f"  {dim(f'pick 1-{len(existing)}')}")
            else:
                # Try matching by name
                matches = [i for i, (n, _) in enumerate(existing) if choice.lower() in n]
                if len(matches) == 1:
                    name = existing[matches[0]][0]
                    script = find_script(WORKSPACE / "projects" / name)
                    if script:
                        print(f"\n  {dim(f'launching {name}...')}\n")
                        subprocess.run([sys.executable, str(script)])
                        print(f"\n  {dim(f'back from {name}.')}\n")
                elif matches:
                    print(f"  {dim('multiple matches:')} {', '.join(existing[i][0] for i in matches)}")
                else:
                    print(f"  {dim('not found')}")
    except (EOFError, KeyboardInterrupt):
        print()


def find_script(project_dir: Path) -> Path | None:
    """Find the main .py script in a project directory."""
    py_files = list(project_dir.glob("*.py"))
    if len(py_files) == 1:
        return py_files[0]
    # Prefer file named after the directory
    dir_name = project_dir.name.replace("-", "_")
    for f in py_files:
        if f.stem == dir_name:
            return f
    return py_files[0] if py_files else None


if __name__ == "__main__":
    main()
