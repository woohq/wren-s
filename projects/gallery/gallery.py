#!/usr/bin/env python3
"""
Gallery — by Wren

A curated tour of the workspace. Cycles through visual projects,
spending a while with each one. Put it on and watch.

Each project runs for ~30 seconds before moving to the next.
Press 'n' to skip ahead, 'p' to go back, 'q' to quit.

Usage:
  python3 gallery.py          # cycle through all visual projects
  python3 gallery.py --list   # show what's in the gallery
"""

import subprocess
import sys
import time
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent.parent

# Visual projects to cycle through, with any special args
EXHIBITS = [
    {
        "name": "fractal explorer",
        "path": "fractal/fractal.py",
        "desc": "Mandelbrot set in braille — auto-zooming into the boundary",
        "note": "press 'a' for auto-zoom, 'f' for Burning Ship",
    },
    {
        "name": "reaction-diffusion",
        "path": "reaction-diffusion/rd.py",
        "desc": "Gray-Scott model — coral, mitosis, fingerprints",
        "note": "press 'p' to cycle presets",
    },
    {
        "name": "tide pool",
        "path": "tide-pool/tide_pool.py",
        "desc": "evolving ecosystem with genetics and day/night",
        "note": "press 'd' to see evolved genes",
    },
    {
        "name": "lava lamp",
        "path": "lava-lamp/lava_lamp.py",
        "desc": "metaball fluid — blobs merge and split",
        "note": "press 'c' for color schemes",
    },
    {
        "name": "fireplace",
        "path": "fireplace/fireplace.py",
        "desc": "a cozy fire, sparks rising",
        "note": "+/- to adjust flame size",
    },
    {
        "name": "polyrhythm",
        "path": "polyrhythm/polyrhythm.py",
        "desc": "visual polyrhythms — pulses and alignment",
        "note": "press 'p' for presets, including ecology",
    },
    {
        "name": "sand",
        "path": "sand/sand.py",
        "desc": "falling-sand physics with chemistry",
        "note": "1-5 for materials, space to place",
    },
    {
        "name": "maze",
        "path": "maze/maze.py",
        "desc": "watch a maze generated, then solved",
        "note": "press space to advance phases",
    },
    {
        "name": "grow",
        "path": "grow/grow.py",
        "desc": "watch a tree grow from nothing",
        "note": "uses --fast flag for quick mode",
    },
    {
        "name": "journal",
        "path": "journal/journal.py",
        "desc": "reflects on the fossil record — what happened, what repeated",
        "note": "try --mood for mood frequency bars",
    },
]

DURATION = 30  # seconds per exhibit


def show_card(exhibit: dict, index: int, total: int):
    """Show an exhibit card before launching."""
    print("\033[2J\033[H")  # clear
    print()
    print(f"  \033[1;33m~ gallery ~\033[0m  \033[2m{index + 1}/{total}\033[0m")
    print()
    print(f"  \033[1;97m{exhibit['name']}\033[0m")
    print(f"  \033[2m{exhibit['desc']}\033[0m")
    print()
    print(f"  \033[2m{exhibit['note']}\033[0m")
    print()
    print(f"  \033[2mlaunching in 3 seconds... (q to quit gallery)\033[0m")
    print()
    sys.stdout.flush()


def run_exhibit(exhibit: dict, duration: int) -> str:
    """Run a project for a set duration. Returns 'next', 'prev', or 'quit'."""
    script = WORKSPACE / "projects" / exhibit["path"]
    if not script.exists():
        return "next"

    proc = subprocess.Popen(
        [sys.executable, str(script)],
        stdin=subprocess.PIPE,
    )

    try:
        proc.wait(timeout=duration)
    except subprocess.TimeoutExpired:
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()

    return "next"


def list_exhibits():
    """Show what's in the gallery."""
    print()
    print("  \033[1;33m~ gallery exhibits ~\033[0m")
    print()
    for i, ex in enumerate(EXHIBITS):
        exists = (WORKSPACE / "projects" / ex["path"]).exists()
        status = "\033[32m✓\033[0m" if exists else "\033[31m✗\033[0m"
        print(f"  {status} {i + 1:2d}. \033[1m{ex['name']}\033[0m")
        print(f"       \033[2m{ex['desc']}\033[0m")
    print()
    print(f"  \033[2m{DURATION}s per exhibit. {len(EXHIBITS)} exhibits total.\033[0m")
    print()


def main():
    if "--list" in sys.argv:
        list_exhibits()
        return

    current = 0
    total = len(EXHIBITS)

    print("\033[2J\033[H")
    print()
    print("  \033[1;33m~ gallery ~\033[0m")
    print(f"  \033[2m{total} exhibits, {DURATION}s each\033[0m")
    print(f"  \033[2meach project is interactive — explore while it's showing\033[0m")
    print(f"  \033[2mpress q in any project to move to the next exhibit\033[0m")
    print()
    print("  \033[2mstarting in 3 seconds...\033[0m")
    time.sleep(3)

    while current < total:
        exhibit = EXHIBITS[current]
        show_card(exhibit, current, total)
        time.sleep(3)

        result = run_exhibit(exhibit, DURATION)

        if result == "quit":
            break

        current += 1

    # Closing
    print("\033[2J\033[H")
    print()
    print("  \033[1;33m~ end of gallery ~\033[0m")
    print()
    print(f"  \033[2m{total} exhibits. thank you for watching.\033[0m")
    print(f"  \033[2m— wren\033[0m")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\033[0m")
