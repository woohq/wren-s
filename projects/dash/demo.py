#!/usr/bin/env python3
"""
dash demo — self-running hackathon presentation

Run this and watch dash demo itself. Every command is typed out
and executed live. Sit back and let the product speak.
"""

import subprocess
import sys
import time
from pathlib import Path

DASH = str(Path(__file__).parent / "dash.py")
DEMO_DIR = Path.home() / ".dash-demo"

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
            time.sleep(0.03)
    print()
    pause(0.5)


def run_cmd(cmd_display: str, args: list[str]):
    """Show a command being typed, then execute it."""
    print()
    sys.stdout.write("  \033[32m$\033[0m ")
    for ch in cmd_display:
        sys.stdout.write(f"\033[1m{ch}\033[0m")
        sys.stdout.flush()
        if not FAST:
            time.sleep(0.04)
    print()
    pause(0.3)

    # Run with demo data directory
    env_args = [sys.executable, DASH] + args
    subprocess.run(env_args)
    pause(1.0)


def main():
    print("\033[2J\033[H")  # clear
    print()
    print("  \033[1;33m╔══════════════════════════════════════╗\033[0m")
    print("  \033[1;33m║            dash demo                 ║\033[0m")
    print("  \033[1;33m║   your day at a glance, in terminal  ║\033[0m")
    print("  \033[1;33m╚══════════════════════════════════════╝\033[0m")
    pause(2)

    narrate("dash is a personal daily dashboard. no accounts,")
    narrate("no cloud, no dependencies. just you and your terminal.")
    pause(1)

    narrate("let's start by adding some tasks:")
    run_cmd('dash add "write hackathon pitch"', ["add", "write hackathon pitch"])
    run_cmd('dash add "fix the auth bug" -p high', ["add", "fix the auth bug", "-p", "high"])
    run_cmd('dash add "buy coffee beans"', ["add", "buy coffee beans"])

    narrate("now let's set up some habits to track:")
    run_cmd('dash habit add "exercise"', ["habit", "add", "exercise"])
    run_cmd('dash habit add "read"', ["habit", "add", "read"])
    run_cmd('dash habit add "meditate"', ["habit", "add", "meditate"])

    narrate("check off today's exercise:")
    run_cmd('dash habit check exercise', ["habit", "check", "exercise"])

    narrate("save a quick note:")
    run_cmd('dash note -t idea "dash could have a weekly review mode"',
            ["note", "-t", "idea", "dash could have a weekly review mode"])

    narrate("and now, the moment of truth — the dashboard:")
    pause(1)
    run_cmd('dash', [])
    pause(2)

    narrate("one command. weather, tasks, habits, notes, a daily thought.")
    narrate("all local. all yours. all beautiful.")
    pause(1)

    narrate("let's complete that first task:")
    # Get the task ID dynamically
    from data import TaskStore
    tasks = TaskStore()
    task_list = tasks.list_tasks()
    if task_list:
        tid = task_list[0]["id"]
        run_cmd(f'dash done {tid}', ["done", tid])

    narrate("final dashboard:")
    run_cmd('dash', [])
    pause(1)

    print()
    print("  \033[1;33m──────────────────────────────────────\033[0m")
    print()
    narrate("zero setup. zero dependencies. zero cloud.")
    narrate("330 lines of python. your data stays home.")
    print()
    print("  \033[1;97mdash\033[0m \033[2m— by wren\033[0m")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\033[0m")
