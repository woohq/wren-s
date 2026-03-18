#!/usr/bin/env python3
"""Seed the garden with demo data at various ages for hackathon demos."""

import json
import datetime
from pathlib import Path

sys_path_hack = True  # just to avoid import issues
import sys
sys.path.insert(0, str(Path(__file__).parent))
from soil import ThoughtStore, extract_keywords, compute_position

def seed():
    store = ThoughtStore()

    # Clear existing
    store._save([])

    now = datetime.datetime.now()

    # Demo thoughts at different ages
    demo_thoughts = [
        # Old thoughts (flowers - 7+ days)
        (-10, "simple rules create complex behavior", ["emergence", "complexity"]),
        (-9,  "the beauty of fractals is infinite self-similarity", ["math", "beauty"]),
        (-8,  "every program is a mirror of its author", ["code", "reflection"]),

        # Medium thoughts (plants - 3-7 days)
        (-5,  "music is patterns in time the way art is patterns in space", ["art", "music"]),
        (-4,  "the best tools disappear into the work", ["design", "tools"]),
        (-4,  "constraints breed creativity not freedom", ["creativity"]),

        # Young thoughts (saplings - 1-3 days)
        (-2,  "emergence happens at the boundary between order and chaos", ["emergence", "complexity"]),
        (-1,  "what if notes could grow like plants", ["idea", "garden"]),
        (-1,  "a workspace is a home for thoughts that want to become things", ["reflection"]),

        # Fresh thoughts (sprouts - hours)
        (-0.1, "connection is not something you add it is something you notice", ["idea"]),
        (-0.05, "the garden grows whether you watch it or not", ["garden"]),

        # Brand new (seeds - minutes)
        (0,   "simple systems surprise their creators", ["emergence"]),
    ]

    thoughts = []
    for days_ago, text, tags in demo_thoughts:
        planted = now + datetime.timedelta(days=days_ago)
        keywords = extract_keywords(text)

        thought = {
            "id": store._short_id() if hasattr(store, '_short_id') else __import__('secrets').token_hex(3),
            "text": text,
            "tags": tags,
            "planted_at": planted.isoformat(),
            "keywords": keywords,
            "x": 0.0,
            "y": 0.0,
        }

        # Compute position relative to existing thoughts
        x, y = compute_position(thought, thoughts, 80, 40)
        thought["x"] = x
        thought["y"] = y
        thoughts.append(thought)

    store._save(thoughts)

    print(f"  🌱 seeded {len(thoughts)} thoughts across {10} days")
    print()
    for t in thoughts:
        from soil import growth_stage
        stage = growth_stage(t["planted_at"])
        names = {0: "seed", 1: "sprout", 2: "sapling", 3: "plant", 4: "flower"}
        print(f"    {names[stage]:8s}  {t['text'][:45]}")
    print()
    print(f"  run: python3 garden.py")


if __name__ == "__main__":
    seed()
