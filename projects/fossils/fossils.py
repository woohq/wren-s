#!/usr/bin/env python3
"""
fossils — by Wren

Analyzes the evolve fossil record. Finds patterns in 400+ generations
of names, moods, and word pairings.

Usage:
  python3 fossils.py              # full analysis
  python3 fossils.py words        # word frequency
  python3 fossils.py moods        # mood distribution
  python3 fossils.py pairs        # most common word pairs
  python3 fossils.py transforms   # "wants to become" patterns
"""

import re
import sys
import importlib.util
from pathlib import Path
from collections import Counter

EVOLVE_PATH = Path(__file__).resolve().parent.parent / "evolve" / "evolve.py"


def load_evolve():
    """Import evolve.py to read its data."""
    spec = importlib.util.spec_from_file_location("evolve", EVOLVE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def parse_fossils(fossils):
    """Parse fossil strings into structured data."""
    parsed = []
    for f in fossils:
        m = re.match(r"gen (\d+): (\w+) (\w+) \((\w+)\) \[(\w+)\]", f)
        if m:
            parsed.append({
                "gen": int(m.group(1)),
                "word1": m.group(2),
                "word2": m.group(3),
                "mood": m.group(4),
                "hash": m.group(5),
            })
    return parsed


def word_frequency(fossils):
    """Count how often each word appears in fossil names."""
    words = Counter()
    for f in fossils:
        words[f["word1"]] += 1
        words[f["word2"]] += 1
    print(f"  word frequency across {len(fossils)} fossils:\n")
    for word, count in words.most_common():
        bar = "█" * (count // 2)
        print(f"  {word:>10}  {count:>3}  {bar}")


def mood_distribution(fossils):
    """Count mood frequencies."""
    moods = Counter(f["mood"] for f in fossils)
    total = len(fossils)
    print(f"  mood distribution across {total} fossils:\n")
    for mood, count in moods.most_common():
        pct = count / total * 100
        bar = "▓" * int(pct)
        print(f"  {mood:>14}  {count:>3}  ({pct:4.1f}%)  {bar}")


def common_pairs(fossils):
    """Find the most common word pairings."""
    pairs = Counter()
    for f in fossils:
        pair = tuple(sorted([f["word1"], f["word2"]]))
        pairs[pair] += 1
    print(f"  most common name pairings:\n")
    for (w1, w2), count in pairs.most_common(15):
        print(f"  {w1} {w2}  ×{count}")


def word_connections(fossils):
    """Show which words appear together most — a web of associations."""
    connections = {}
    for f in fossils:
        w1, w2 = f["word1"], f["word2"]
        connections.setdefault(w1, Counter())[w2] += 1
        connections.setdefault(w2, Counter())[w1] += 1

    print(f"  word connections (who pairs with whom):\n")
    for word in sorted(connections):
        partners = connections[word].most_common(3)
        partner_str = ", ".join(f"{p}({c})" for p, c in partners)
        print(f"  {word:>10} → {partner_str}")


def transforms(mod):
    """Extract 'wants to become' behaviors from evolve."""
    behaviors = []
    for expr, gen_born in mod.BEHAVIORS:
        try:
            result = eval(expr, {
                "MOOD": mod.MOOD, "WORDS": mod.WORDS,
                "FOSSILS": mod.FOSSILS, "GENERATION": mod.GENERATION,
                "random": __import__("random"), "os": __import__("os"),
                "datetime": __import__("datetime"), "Path": Path,
                "__file__": str(EVOLVE_PATH),
            })
            if isinstance(result, str) and "wants to become" in result:
                behaviors.append((result, gen_born))
        except Exception:
            pass

    if behaviors:
        print(f"  active transformation desires:\n")
        for b, gen in behaviors:
            print(f"  [{gen:>3}] {b}")
    else:
        print("  no active transformation behaviors right now.")


def summary(fossils, mod):
    """Full analysis."""
    print(f"\n  ── fossil analysis ── {len(fossils)} generations ──\n")
    word_frequency(fossils)
    print()
    mood_distribution(fossils)
    print()
    common_pairs(fossils)
    print()
    word_connections(fossils)
    print()
    transforms(mod)
    print()


if __name__ == "__main__":
    mod = load_evolve()
    fossils = parse_fossils(mod.FOSSILS)

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "words":
            word_frequency(fossils)
        elif cmd == "moods":
            mood_distribution(fossils)
        elif cmd == "pairs":
            common_pairs(fossils)
        elif cmd == "connections":
            word_connections(fossils)
        elif cmd == "transforms":
            transforms(mod)
        else:
            print(f"  unknown command: {cmd}")
            print("  try: words, moods, pairs, connections, transforms")
    else:
        summary(fossils, mod)
