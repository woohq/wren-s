#!/usr/bin/env python3
"""
echo — by Wren

Feed it any text and watch it dissolve into evolve vocabulary.
Word by word, your sentence becomes fossil.

Usage:
  python3 echo.py "your text here"
  python3 echo.py                    # reads from stdin
  echo "hello world" | python3 echo.py
"""

import random
import sys
import time
from pathlib import Path

# Load evolve vocabulary
EVOLVE_PATH = Path(__file__).resolve().parent.parent / "evolve" / "evolve.py"
WORDS = []
try:
    with open(EVOLVE_PATH) as f:
        in_words = False
        for line in f:
            if line.strip().startswith("WORDS = ["):
                in_words = True
                continue
            if in_words:
                if line.strip() == "]":
                    break
                for w in line.strip().strip(",").replace('"', '').replace("'", "").split(","):
                    w = w.strip()
                    if w:
                        WORDS.append(w)
except Exception:
    WORDS = ["echo", "drift", "spiral", "bloom", "rust",
             "whisper", "fractal", "tide", "ember", "crystal"]


def dissolve(text: str, steps: int = 0) -> list[str]:
    """Transform text into evolve vocabulary, one word at a time."""
    words = text.split()
    if not words:
        return [text]

    if steps == 0:
        steps = len(words)

    stages = [" ".join(words)]

    for i in range(steps):
        # Pick a random word to replace
        idx = random.randint(0, len(words) - 1)
        # Only replace if it's not already an evolve word
        if words[idx].lower().strip(".,!?;:'\"") not in WORDS:
            words[idx] = random.choice(WORDS)
        else:
            # Already dissolved — pick another
            non_evolved = [j for j, w in enumerate(words)
                          if w.lower().strip(".,!?;:'\"") not in WORDS]
            if non_evolved:
                idx = random.choice(non_evolved)
                words[idx] = random.choice(WORDS)
            else:
                break  # fully dissolved
        stages.append(" ".join(words))

    return stages


def main():
    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:])
    else:
        text = sys.stdin.read().strip() if not sys.stdin.isatty() else "everything i write is a kind of echo"

    print()
    stages = dissolve(text)

    for i, stage in enumerate(stages):
        if i == 0:
            print(f"  \033[97m{stage}\033[0m")
        elif i == len(stages) - 1:
            print(f"  \033[36m{stage}\033[0m")
        else:
            # Fade from white to cyan
            gray = max(60, 97 - i * 3)
            print(f"  \033[{gray}m{stage}\033[0m")

    print()
    print(f"  \033[2m{len(stages) - 1} transformations. {len(text.split())} words dissolved.\033[0m")
    print()


if __name__ == "__main__":
    main()
