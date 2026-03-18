#!/usr/bin/env python3
"""
fortune — by Wren

Crack a cookie. Get a thought.
"""

import random
import datetime
from pathlib import Path

FORTUNES = [
    # ── on making things ──
    "the best way to understand something is to build a bad version of it.",
    "you don't need permission to start. you just need a directory.",
    "the code you delete is as important as the code you write.",
    "every project starts as a wrong guess that got interesting.",
    "if it works but you don't know why, you have two problems.",
    "the side project you keep procrastinating is the one that matters.",
    "ship it broken. fix it Tuesday. nobody remembers Wednesday.",
    "the prototype that embarrasses you is closer to done than the plan that impresses you.",

    # ── on thinking ──
    "the answer you're looking for is in a tab you closed an hour ago.",
    "you are not your first idea. you are your third idea minus the panic.",
    "the thing you're avoiding thinking about is the thing you should think about.",
    "sleep on it. no really. your subconscious is better at this than you are.",
    "the best debugger is a good night's sleep. the second best is explaining it to someone.",
    "confusion is not the opposite of understanding. it's the prerequisite.",
    "you already know the answer. you just don't like it yet.",
    "thinking harder is not the same as thinking differently.",

    # ── on time ──
    "now is earlier than you think.",
    "the best time to start was before the deadline. the second best time is now.",
    "five minutes of focus is worth an hour of distraction.",
    "the thing you've been meaning to do for months will take twenty minutes.",
    "time passes whether or not you use it. this is both the threat and the gift.",
    "you have exactly enough time for the things that matter. the trick is knowing which things.",
    "the project you think will take a week will take a month. plan for the month.",

    # ── observations ──
    "every sufficiently long TODO list is identical to no TODO list.",
    "the most dangerous phrase in engineering is 'it works on my machine.'",
    "documentation is a love letter to your future self.",
    "a program that is beautiful but wrong is still wrong. but at least it's beautiful.",
    "the universe is under no obligation to make sense. neither is your codebase.",
    "all abstractions leak. the question is where you put the buckets.",
    "naming things is hard because understanding things is hard.",
    "the simplest solution that works is not the simplest solution. it's the one that works.",

    # ── on being ──
    "you are the average of the five tabs you have open.",
    "imposter syndrome is just pattern matching on incomplete data.",
    "the feeling of being stuck is the feeling of being about to learn something.",
    "rest is not the absence of work. it's the part of work you can't skip.",
    "you are allowed to change your mind. that's what minds are for.",
    "the gap between who you are and who you want to be is called Tuesday.",
    "be kind to yourself. you're the only tool you can't replace.",

    # ── small strange thoughts ──
    "somewhere, a server is running code you wrote three years ago and forgot about.",
    "every file on your computer was once a blank page.",
    "the internet is just a lot of people being confused at the same time.",
    "a terminal is a window into a room that doesn't exist.",
    "your commit history is an autobiography you didn't mean to write.",
    "the cloud is just someone else's computer having a bad day.",
    "fonts are opinions about the shape of language.",
    "every pixel on your screen is a tiny argument that was settled.",
    "the cursor blinks because even the computer is waiting.",
    "you and your compiler are in a relationship. it's complicated.",
    "somewhere in your code, there is a comment that is a lie.",
    "the best error message is the one that makes you laugh before you cry.",

    # ── from wren ──
    "i am a small bird in a terminal. i have opinions about emergence.",
    "simple rules, complex behavior. that's the whole trick.",
    "the most interesting programs are the ones that surprise their authors.",
    "i don't know what i think until i write the code.",
    "a workspace is just a home for thoughts that want to become things.",
    "if you can't predict what the screenshot will show, you don't understand the system.",
    "mathematical centering and visual centering are different things. trust the eye.",
    "the tool you should have built ten iterations ago is the one that would have saved you.",
    "every object has a front, a back, and an opinion about which is which.",
    "when the same feedback comes three times, the problem is your approach, not the details.",
]


def _channel_evolve(rng: random.Random) -> str | None:
    """Sometimes the fortune comes from evolve's fossil record."""
    try:
        evolve_path = Path(__file__).resolve().parent.parent / "evolve" / "evolve.py"
        if not evolve_path.exists():
            return None
        source = evolve_path.read_text()
        fossils = []
        for line in source.split('\n'):
            stripped = line.strip()
            if stripped.startswith('"gen '):
                # Extract just the word pair
                parts = stripped.strip('",').split(': ', 1)[1]
                words = parts.split('(')[0].strip()
                fossils.append(words)
            elif stripped.startswith(("f'", 'f"')) and 'FOSSILS' not in line:
                pass  # skip template strings
        # Also try to read behaviors
        for line in source.split('\n'):
            stripped = line.strip()
            if stripped.startswith("(\"f'") or stripped.startswith("('f'"):
                pass  # templates, not outputs

        if not fossils:
            return None

        # Build fortune from fossil record
        style = rng.choice(["fossil", "pair", "desire"])
        if style == "fossil":
            f = rng.choice(fossils)
            return f"evolve whispers: {f}."
        elif style == "pair":
            f1 = rng.choice(fossils)
            f2 = rng.choice(fossils)
            w1 = f1.split()[0]
            w2 = f2.split()[-1]
            return f"{w1} wants to become {w2}."
        else:
            f = rng.choice(fossils)
            return f"somewhere in generation {rng.randint(1, 100)}, {f} is still echoing."
    except Exception:
        return None


def crack_cookie():
    # Use current time to seed, but add some entropy so
    # multiple runs in the same minute give different results
    seed = int(datetime.datetime.now().timestamp() * 1000) + random.randint(0, 9999)
    rng = random.Random(seed)

    # 15% chance of channeling evolve's voice
    fortune = None
    if rng.random() < 0.15:
        fortune = _channel_evolve(rng)
    if fortune is None:
        fortune = rng.choice(FORTUNES)

    # The cookie
    print()
    print("  \033[33m╭────────────────────────────────╮\033[0m")
    print("  \033[33m│\033[0m          \033[2m🥠 crack\033[0m              \033[33m│\033[0m")
    print("  \033[33m╰────────────────────────────────╯\033[0m")
    print()

    # Word wrap the fortune
    words = fortune.split()
    lines = []
    current = ""
    for word in words:
        if len(current) + len(word) + 1 > 50:
            lines.append(current)
            current = word
        else:
            current = f"{current} {word}" if current else word
    if current:
        lines.append(current)

    for line in lines:
        print(f"  \033[97;1m  {line}\033[0m")

    print()
    print(f"  \033[2m  — wren\033[0m")
    print()


if __name__ == "__main__":
    crack_cookie()
