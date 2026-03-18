#!/usr/bin/env python3
"""
Garden demo — self-running hackathon presentation

Watch the garden plant thoughts, find connections, and grow.
"""

import subprocess
import sys
import time
from pathlib import Path

GARDEN = str(Path(__file__).parent / "garden.py")
SEED = str(Path(__file__).parent / "seed_demo.py")
FAST = "--fast" in sys.argv


def pause(s=1.0):
    if not FAST:
        time.sleep(s)


def narrate(text: str):
    print()
    for ch in text:
        sys.stdout.write(f"\033[2m{ch}\033[0m")
        sys.stdout.flush()
        if not FAST:
            time.sleep(0.025)
    print()
    pause(0.5)


def run_cmd(cmd_display: str, args: list[str]):
    print()
    sys.stdout.write("  \033[32m$\033[0m ")
    for ch in cmd_display:
        sys.stdout.write(f"\033[1m{ch}\033[0m")
        sys.stdout.flush()
        if not FAST:
            time.sleep(0.035)
    print()
    pause(0.3)
    subprocess.run([sys.executable, GARDEN] + args)
    pause(0.8)


def main():
    print("\033[2J\033[H")
    print()
    print("  \033[1;32m╔══════════════════════════════════════╗\033[0m")
    print("  \033[1;32m║           garden demo                ║\033[0m")
    print("  \033[1;32m║    a visual thought garden           ║\033[0m")
    print("  \033[1;32m╚══════════════════════════════════════╝\033[0m")
    pause(2)

    narrate("garden is a place where your thoughts grow.")
    narrate("plant an idea. it becomes a seed.")
    narrate("over time, seeds sprout, grow, and flower.")
    narrate("related thoughts find each other automatically.")
    pause(1)

    # Clear and start fresh
    narrate("let's plant some thoughts:")
    pause(0.5)

    run_cmd('garden plant "simple rules create complex behavior" -t emergence',
            ["plant", "simple rules create complex behavior", "-t", "emergence"])

    run_cmd('garden plant "the beauty of math is hidden patterns" -t math',
            ["plant", "the beauty of math is hidden patterns", "-t", "math"])

    run_cmd('garden plant "emergence happens at the boundary of order and chaos" -t emergence',
            ["plant", "emergence happens at the boundary of order and chaos", "-t", "emergence"])

    narrate("the garden detected a connection:")
    narrate("'simple rules' and 'emergence...boundary' share the concept of emergence.")
    pause(1)

    run_cmd('garden plant "what if notes could grow like plants" -t idea -t garden',
            ["plant", "what if notes could grow like plants", "-t", "idea", "-t", "garden"])

    run_cmd('garden plant "a program that rewrites itself is alive" -t code -t emergence',
            ["plant", "a program that rewrites itself is alive", "-t", "code", "-t", "emergence"])

    narrate("let's see the garden:")
    run_cmd('garden list', ["list"])
    pause(1)

    narrate("thoughts connect through shared concepts and tags.")
    narrate("they cluster near related thoughts in space.")
    narrate("over days, seeds grow into flowers.")
    pause(1)

    run_cmd('garden search "simple"', ["search", "simple"])

    narrate("now imagine this with 100 thoughts.")
    narrate("a visual map of everything you're thinking about.")
    narrate("connections you didn't know were there.")
    pause(1)

    print()
    print("  \033[1;32m──────────────────────────────────────\033[0m")
    print()
    narrate("plant a thought. watch it grow.")
    narrate("the garden finds the connections you missed.")
    print()
    print("  \033[2mrun: python3 garden.py        (visual garden)\033[0m")
    print("  \033[2mrun: python3 garden.py list   (see all thoughts)\033[0m")
    print()
    print("  \033[1;97mgarden\033[0m \033[2m— by wren\033[0m")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\033[0m")
