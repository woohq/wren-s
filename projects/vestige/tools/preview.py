#!/usr/bin/env python3
"""
Vestige — Life Previewer
by Wren

Assembles a complete life from authored content and outputs it
as readable text. No combat, no cards, no game engine — just
the story of a life, front to back.

Shows: whether pacing works, whether voices stay consistent,
where the dead spots are, how transitions feel.

Usage:
    python3 preview.py blacksmith_s_child thornwall --traits brave,stubborn
    python3 preview.py orphan_of_war thornwall --traits cautious,perceptive
    python3 preview.py wanderer_s_child the_wander --traits curious
    python3 preview.py --list    (show available archetypes + places)
    python3 preview.py --random  (random character)
"""

import json
import sys
import random
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

# --- Colors ---
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"
CYAN = "\033[36m"
YELLOW = "\033[33m"
GREEN = "\033[32m"
MAGENTA = "\033[35m"
RED = "\033[31m"

# --- Data Loading ---

def load_all(subdir):
    """Load all JSON files from a data subdirectory (recursive)."""
    path = DATA_DIR / subdir
    entities = {}
    if not path.exists():
        return entities
    for f in sorted(path.rglob("*.json")):
        try:
            data = json.loads(f.read_text())
            entities[data.get("id", f.stem)] = data
        except (json.JSONDecodeError, KeyError):
            pass
    return entities


def load_world():
    """Load entire world state."""
    return {
        "archetypes": load_all("archetypes"),
        "traits": load_all("traits"),
        "cultures": load_all("cultures"),
        "places": load_all("places"),
        "factions": load_all("factions"),
        "gods": load_all("gods"),
        "events": load_all("events"),
        "scenes": load_all("scenes"),
        "characters": load_all("characters"),
        "creatures": load_all("creatures"),
        "artifacts": load_all("artifacts"),
        "eras": load_all("eras"),
        "threats": load_all("threats"),
    }


# --- Event Filtering ---

def event_matches(event, context):
    """Check if an event matches the current life context."""
    # Age filter
    if context.get("age") and event.get("age") not in [context["age"], "any"]:
        return False

    # Archetype filter
    arch_filter = event.get("archetype_filter", ["any"])
    if isinstance(arch_filter, str):
        arch_filter = [arch_filter]
    if "any" not in arch_filter and context.get("archetype") not in arch_filter:
        return False

    # Trait requires_any
    req = event.get("trait_requires_any", [])
    if req and not any(t in context.get("traits", []) for t in req):
        return False

    # Trait excludes
    excl = event.get("trait_excludes", [])
    if excl and any(t in context.get("traits", []) for t in excl):
        return False

    # Faction present
    fac = event.get("faction_present", [])
    if fac and not any(f in context.get("factions", []) for f in fac):
        return False

    return True


def scene_matches(scene, context):
    """Check if a scene matches the current context."""
    arch_filter = scene.get("archetype_filter", ["any"])
    if isinstance(arch_filter, str):
        arch_filter = [arch_filter]
    if "any" not in arch_filter and context.get("archetype") not in arch_filter:
        return False
    return True


# --- Life Assembly ---

def assemble_life(archetype_id, place_id, trait_ids, world):
    """Assemble a complete life from available content."""
    archetype = world["archetypes"].get(archetype_id)
    place = world["places"].get(place_id)

    if not archetype:
        print(f"  {RED}Archetype '{archetype_id}' not found.{RESET}")
        return None
    if not place:
        print(f"  {RED}Place '{place_id}' not found.{RESET}")
        return None

    # Build context
    culture_id = place.get("culture", "")
    culture = world["cultures"].get(culture_id, {})
    local_factions = place.get("factions", [])
    # Add factions from culture context
    for fid, fac in world["factions"].items():
        if place_id in fac.get("territory", []):
            if fid not in local_factions:
                local_factions.append(fid)

    context = {
        "archetype": archetype_id,
        "traits": list(trait_ids),
        "place": place_id,
        "culture": culture_id,
        "factions": local_factions,
        "era": "the_first_era",
    }

    life = {
        "archetype": archetype,
        "place": place,
        "culture": culture,
        "traits": [world["traits"].get(t, {"name": t}) for t in trait_ids],
        "sections": [],
    }

    # --- Assemble by life phase ---
    for age, label in [("childhood", "CHILDHOOD"), ("adolescence", "ADOLESCENCE"), ("adulthood", "ADULTHOOD")]:
        context["age"] = age
        section = {"label": label, "events": [], "scenes": []}

        # Find matching events
        matching = []
        for eid, event in world["events"].items():
            if event_matches(event, context):
                matching.append(event)

        # Shuffle and pick (simulate pool draw)
        random.shuffle(matching)
        max_events = {"childhood": 4, "adolescence": 3, "adulthood": 4}.get(age, 3)
        drawn = matching[:max_events]
        section["events"] = drawn

        # Find matching scenes for this phase
        if age == "childhood":
            # Friend intro + mentor intro
            for scene in world["scenes"].values():
                if scene.get("scene_type") == "awakening":
                    continue
                beat = scene.get("beat", "")
                if beat == "introduction" and scene_matches(scene, context):
                    section["scenes"].append(scene)

        if age == "adolescence":
            # Awakening scene based on attunement tendency
            attunement = archetype.get("attunement_tendency", "body")
            for scene in world["scenes"].values():
                if scene.get("scene_type") == "awakening" and scene.get("attunement") == attunement:
                    section["scenes"].append(scene)
            # Friend bonding
            for scene in world["scenes"].values():
                if scene.get("beat") == "bonding" and scene_matches(scene, context):
                    section["scenes"].append(scene)

        if age == "adulthood":
            # Friend critical + mentor bonding/critical if they exist
            for scene in world["scenes"].values():
                if scene.get("beat") == "critical" and scene_matches(scene, context):
                    section["scenes"].append(scene)

        life["sections"].append(section)

    return life


# --- Display ---

def print_life(life):
    """Print a life as readable text."""
    arch = life["archetype"]
    place = life["place"]
    culture = life["culture"]
    traits = life["traits"]

    print(f"\n{'='*60}")
    print(f"{BOLD}{CYAN}  A LIFE IN VESTIGE{RESET}")
    print(f"{'='*60}")
    print(f"\n  {BOLD}Archetype:{RESET} {arch.get('name', '?')}")
    print(f"  {BOLD}Place:{RESET} {place.get('name', '?')}")
    print(f"  {BOLD}Culture:{RESET} {culture.get('name', 'unknown')}")
    print(f"  {BOLD}Traits:{RESET} {', '.join(t.get('name', '?') for t in traits)}")
    if arch.get("story_tendency"):
        print(f"  {DIM}{arch['story_tendency']}{RESET}")
    print(f"\n{'─'*60}")

    total_words = 0
    total_events = 0
    total_scenes = 0

    for section in life["sections"]:
        label = section["label"]
        events = section["events"]
        scenes = section["scenes"]

        print(f"\n{BOLD}{MAGENTA}  ── {label} ──{RESET}\n")

        if not events and not scenes:
            print(f"  {RED}[NO CONTENT for this phase]{RESET}\n")
            continue

        # Interleave scenes and events naturally
        # Scenes first (relationship intros, awakenings), then events
        for scene in scenes:
            name = scene.get("name", "?")
            text = scene.get("text", "")
            stype = scene.get("scene_type", "")
            beat = scene.get("beat", "")

            tag = f"{stype}/{beat}" if beat else stype
            print(f"  {CYAN}[{tag}] {name}{RESET}")
            print()
            for para in text.split("\n\n"):
                for line in _wrap(para, 58):
                    print(f"    {line}")
                print()

            wc = len(text.split())
            total_words += wc
            total_scenes += 1

        for event in events:
            name = event.get("name", "?")
            text = event.get("text", "")
            choices = event.get("choices", [])

            print(f"  {YELLOW}[event] {name}{RESET}")
            print()
            for para in text.split("\n\n"):
                for line in _wrap(para, 58):
                    print(f"    {line}")
                print()

            if choices:
                print(f"  {DIM}Choices:{RESET}")
                for i, choice in enumerate(choices):
                    req = choice.get("requires", {})
                    req_str = ""
                    if req:
                        req_str = f" {DIM}(requires: {json.dumps(req)}){RESET}"
                    print(f"    {DIM}[{i+1}]{RESET} {choice['text']}{req_str}")
                print()

            wc = len(text.split())
            for c in choices:
                wc += len(c.get("consequence_text", "").split())
            total_words += wc
            total_events += 1

        print(f"  {DIM}{'─'*50}{RESET}")

    # Summary
    print(f"\n{'='*60}")
    print(f"{BOLD}  LIFE SUMMARY{RESET}")
    print(f"  Events: {total_events}  |  Scenes: {total_scenes}  |  Words: ~{total_words:,}")

    gaps = []
    for section in life["sections"]:
        if not section["events"] and not section["scenes"]:
            gaps.append(section["label"])
    if gaps:
        print(f"  {RED}GAPS: {', '.join(gaps)} — needs more content{RESET}")
    else:
        print(f"  {GREEN}All phases have content.{RESET}")

    print(f"{'='*60}\n")


def _wrap(text, width):
    """Simple word wrap."""
    words = text.split()
    lines = []
    current = []
    length = 0
    for word in words:
        if length + len(word) + 1 > width and current:
            lines.append(" ".join(current))
            current = [word]
            length = len(word)
        else:
            current.append(word)
            length += len(word) + 1
    if current:
        lines.append(" ".join(current))
    return lines or [""]


# --- CLI ---

def main():
    if len(sys.argv) < 2:
        print(f"\n{BOLD}Vestige Life Previewer{RESET}")
        print(f"\n  Usage:")
        print(f"    preview.py <archetype> <place> [--traits t1,t2,...]")
        print(f"    preview.py --list")
        print(f"    preview.py --random")
        return

    world = load_world()

    if sys.argv[1] == "--list":
        print(f"\n{BOLD}Available:{RESET}\n")
        print(f"  {CYAN}Archetypes:{RESET}")
        for aid, a in world["archetypes"].items():
            att = a.get("attunement_tendency", "?")
            print(f"    {aid:<25} [{att}] {a.get('name', '?')}")
        print(f"\n  {YELLOW}Places:{RESET}")
        for pid, p in world["places"].items():
            culture = p.get("culture", "none")
            print(f"    {pid:<25} [{culture}] {p.get('name', '?')}")
        print(f"\n  {GREEN}Traits:{RESET}")
        for tid, t in world["traits"].items():
            print(f"    {tid:<25} [{t.get('source','?')}] {t.get('name','?')}")
        print()
        return

    if sys.argv[1] == "--random":
        arch = random.choice(list(world["archetypes"].keys()))
        place = random.choice(list(world["places"].keys()))
        all_traits = list(world["traits"].keys())
        traits = random.sample(all_traits, min(3, len(all_traits)))
        print(f"  {DIM}Random: {arch} in {place} with {', '.join(traits)}{RESET}")
        life = assemble_life(arch, place, traits, world)
        if life:
            print_life(life)
        return

    archetype = sys.argv[1]
    place = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else "thornwall"

    traits = []
    for i, arg in enumerate(sys.argv):
        if arg == "--traits" and i + 1 < len(sys.argv):
            traits = [t.strip() for t in sys.argv[i + 1].split(",")]

    if not traits:
        # Default traits from archetype tendency
        arch_data = world["archetypes"].get(archetype, {})
        trait_tendencies = arch_data.get("starting_traits", [])
        if isinstance(trait_tendencies, str):
            trait_tendencies = [t.strip() for t in trait_tendencies.split(",")]
        # Also add a personality trait
        traits = trait_tendencies[:2] + ["brave"]

    life = assemble_life(archetype, place, traits, world)
    if life:
        print_life(life)


if __name__ == "__main__":
    main()
