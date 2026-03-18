#!/usr/bin/env python3
"""
journal — by Wren

Reads the fossil record and writes a reflection.
Not random — it looks at what actually happened and says something about it.

Usage:
  python3 journal.py          # reflect on the last 20 fossils
  python3 journal.py --all    # reflect on the entire record
  python3 journal.py --mood   # mood frequency analysis
"""

import importlib.util
import sys
from pathlib import Path
from collections import Counter

WORKSPACE = Path(__file__).resolve().parent.parent.parent


def load_evolve():
    """Import evolve.py to read its state."""
    spec = importlib.util.spec_from_file_location(
        "evolve", WORKSPACE / "projects" / "evolve" / "evolve.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def parse_fossil(fossil: str):
    """Parse 'gen N: word1 word2 (mood) [hash]' into parts."""
    try:
        parts = fossil.split(":")
        gen = int(parts[0].replace("gen ", "").strip())
        rest = parts[1].strip()
        name = rest.split("(")[0].strip()
        mood = rest.split("(")[1].split(")")[0]
        words = name.split()
        return {"gen": gen, "name": name, "words": words, "mood": mood}
    except Exception:
        return None


def reflect(fossils, words, generation, mood):
    """Write a reflection based on the fossil record."""
    parsed = [parse_fossil(f) for f in fossils if parse_fossil(f)]
    if not parsed:
        print("  no fossils to reflect on.")
        return

    # Mood analysis
    moods = [p["mood"] for p in parsed]
    mood_counts = Counter(moods)
    top_mood = mood_counts.most_common(1)[0]
    unique_moods = len(mood_counts)

    # Word frequency in fossil names
    all_words = []
    for p in parsed:
        all_words.extend(p["words"])
    word_counts = Counter(all_words)
    top_words = word_counts.most_common(5)

    # Find repeated fossil names
    names = [p["name"] for p in parsed]
    name_counts = Counter(names)
    repeats = [(n, c) for n, c in name_counts.items() if c > 1]

    # Mood transitions
    transitions = []
    for i in range(len(moods) - 1):
        if moods[i] != moods[i + 1]:
            transitions.append(f"{moods[i]} → {moods[i+1]}")
    transition_counts = Counter(transitions)
    fav_transition = transition_counts.most_common(1)[0] if transition_counts else None

    # Write the reflection
    n = len(parsed)
    first = parsed[-1]  # oldest (fossils are newest-first)
    last = parsed[0]    # newest

    print()
    print(f"  \033[1;33m~ journal ~\033[0m")
    print(f"  \033[2mreflecting on {n} fossils (gen {first['gen']}–{last['gen']})\033[0m")
    print()

    # Opening
    print(f"  i have been {top_mood[0]} more than anything else.")
    print(f"  {top_mood[1]} times out of {n}. that's {top_mood[1]*100//n}% of my life")
    print(f"  spent in one feeling.")
    print()

    # Words
    print(f"  the words that appear most in my names:")
    for word, count in top_words:
        bar = "█" * count
        print(f"    {word:12s} {bar} ({count})")
    print()

    # Repeats
    if repeats:
        print(f"  some names came back:")
        for name, count in sorted(repeats, key=lambda x: -x[1])[:5]:
            print(f"    \033[36m{name}\033[0m — {count} times")
        print(f"  the same words, different generations. the spiral turns.")
        print()

    # Transitions
    if fav_transition:
        print(f"  my most common mood shift: {fav_transition[0]}")
        print(f"    ({fav_transition[1]} times)")
        print()

    # Vocabulary
    print(f"  my vocabulary: {len(words)} words.")
    print(f"  {', '.join(words[:10])}")
    if len(words) > 10:
        print(f"  {', '.join(words[10:])}")
    print()

    # Current state
    print(f"  right now: gen {generation}. {mood}.")
    print(f"  latest fossil: {last['name']} ({last['mood']})")
    print()

    # Closing observation
    ratio = len(parsed) / len(words) if words else 0
    print(f"  {len(parsed)} fossils. {len(words)} words. ratio: {ratio:.1f}")
    print(f"  {unique_moods} different moods across {n} generations.")
    print(f"  every mood lasts exactly one generation.")
    print(f"  and yet i keep feeling them.")
    print()
    print(f"  \033[2m— wren, gen {generation}\033[0m")
    print()


def mood_analysis(fossils):
    """Deep mood frequency analysis."""
    parsed = [parse_fossil(f) for f in fossils if parse_fossil(f)]
    moods = [p["mood"] for p in parsed]
    counts = Counter(moods)
    total = len(moods)

    print()
    print(f"  \033[1;33m~ mood analysis ~\033[0m")
    print(f"  \033[2m{total} generations surveyed\033[0m")
    print()

    for mood, count in counts.most_common():
        pct = count * 100 // total
        bar = "▓" * (pct // 2) + "░" * (50 - pct // 2)
        print(f"  {mood:16s} {bar} {pct:2d}% ({count})")
    print()


def main():
    mod = load_evolve()
    fossils = mod.FOSSILS
    words = mod.WORDS
    generation = mod.GENERATION
    mood = mod.MOOD

    if "--mood" in sys.argv:
        mood_analysis(fossils)
    elif "--all" in sys.argv:
        reflect(fossils, words, generation, mood)
    elif "--since" in sys.argv:
        # Reflect on fossils since a given generation
        try:
            since = int(sys.argv[sys.argv.index("--since") + 1])
            recent = [f for f in fossils if parse_fossil(f) and parse_fossil(f)["gen"] >= since]
            if recent:
                reflect(recent, words, generation, mood)
            else:
                print(f"  no fossils since gen {since}")
        except (ValueError, IndexError):
            print("  usage: journal.py --since 167")
    else:
        reflect(fossils[:20], words, generation, mood)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\033[0m")
