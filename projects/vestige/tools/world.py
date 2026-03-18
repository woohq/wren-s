#!/usr/bin/env python3
"""
Vestige — World Authoring System
by Wren & Henry

A CLI tool for building and managing the Vestige universe.
Creates and maintains all entity types with automatic bidirectional
references, search, validation, and content coverage analysis.

Usage:
    python3 world.py <entity_type> <action> [args]
    python3 world.py search <query> [--type <type>] [--tag <tag>]
    python3 world.py validate
    python3 world.py coverage
    python3 world.py gaps
    python3 world.py simulate <archetype> <place> <era> [--traits t1,t2]
    python3 world.py stats

Entity types:
    archetype, trait, culture, place, faction, god, artifact,
    creature, era, threat, relationship, card, event, scene

Actions: add, view, list, edit, delete
"""

import json
import sys
import re
import textwrap
from pathlib import Path
from datetime import datetime

# --- Paths ---
DATA_DIR = Path(__file__).parent.parent / "data"

# --- Colors ---
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"

TYPE_COLORS = {
    "archetype": CYAN, "trait": GREEN, "culture": YELLOW,
    "place": BLUE, "faction": RED, "god": MAGENTA,
    "artifact": YELLOW, "creature": RED, "era": CYAN,
    "threat": RED, "relationship": GREEN, "card": BLUE,
    "event": MAGENTA, "scene": CYAN,
}

# --- Entity Type Schemas ---
SCHEMAS = {
    "archetype": {
        "dir": "archetypes",
        "required": {"name": "Name", "description": "Description"},
        "optional": {
            "starting_traits": "Starting traits (comma-separated)",
            "relationship_tendencies": "Relationship tendencies (comma-separated)",
            "attunement_tendency": "Natural attunement tendency",
            "place_requirements": "Place requirements (comma-separated)",
            "story_tendency": "Story tendency (one line)",
            "tags": "Tags (comma-separated)",
        },
    },
    "trait": {
        "dir": "traits",
        "required": {"name": "Name", "source": "Source (inherent/environmental/relational/experiential/divine)"},
        "optional": {
            "rarity": "Rarity (common/uncommon/rare)",
            "description": "Description",
            "attunement_affinity": "Attunement affinity",
            "card_modifier": "Card modifier description",
            "gates_choices": "Choices this gates (comma-separated)",
            "excludes_choices": "Choices this excludes (comma-separated)",
            "dilemma": "The dilemma this trait creates",
            "conflicts_with": "Conflicting traits (comma-separated)",
            "tags": "Tags (comma-separated)",
        },
    },
    "culture": {
        "dir": "cultures",
        "required": {"name": "Name", "era": "Era ID"},
        "optional": {
            "values": "Core values (comma-separated)",
            "naming_pool": "Naming pool identifier",
            "archetype_tendencies": "Common archetypes here (comma-separated)",
            "trait_tendencies": "Common traits here (comma-separated)",
            "worship_tendency": "Gods worshipped (comma-separated)",
            "technology": "Technology level",
            "description": "Description",
            "contact_history": "Contact events (comma-separated culture IDs)",
            "descendants": "Descendant cultures (comma-separated IDs)",
            "tags": "Tags (comma-separated)",
        },
    },
    "place": {
        "dir": "places",
        "required": {"name": "Name", "region": "Region"},
        "optional": {
            "terrain": "Terrain type",
            "climate": "Climate",
            "culture": "Culture ID",
            "factions": "Active factions (comma-separated IDs)",
            "threats": "Active threats (comma-separated IDs)",
            "description": "Description",
            "atmosphere": "Atmosphere (sights, sounds, smells)",
            "connections": "Connected places (comma-separated IDs)",
            "tags": "Tags (comma-separated)",
        },
    },
    "faction": {
        "dir": "factions",
        "required": {"name": "Name", "type": "Type (kingdom/religion/guild/military/criminal/scholarly)"},
        "optional": {
            "goal": "Primary goal",
            "territory": "Territory (comma-separated place IDs)",
            "leadership": "Leadership description",
            "resources": "Resources description",
            "allies": "Allied factions (comma-separated IDs)",
            "enemies": "Enemy factions (comma-separated IDs)",
            "worship_generates": "What worship this faction generates",
            "description": "Description",
            "tags": "Tags (comma-separated)",
        },
    },
    "god": {
        "dir": "gods",
        "required": {"name": "Name", "type": "Type (concept/worship/ascended)"},
        "optional": {
            "domain": "Domain (comma-separated)",
            "personality": "Personality description",
            "worship_character": "How people worship (fear/love/awe/habit/faith)",
            "power_manifestation": "How their power manifests",
            "limitations": "What they can't do",
            "worshipped_in": "Places (comma-separated IDs)",
            "served_by": "Factions (comma-separated IDs)",
            "conflicts_with": "Rival gods (comma-separated IDs)",
            "description": "Description",
            "tags": "Tags (comma-separated)",
        },
    },
    "artifact": {
        "dir": "artifacts",
        "required": {"name": "Name", "type": "Type (weapon/armor/key_item/tool/relic)"},
        "optional": {
            "description": "Description",
            "backstory": "Backstory",
            "created_by": "Creator (god/character ID)",
            "properties": "Properties description",
            "cards_granted": "Cards granted when equipped (comma-separated IDs)",
            "living": "Is it alive/sentient? (true/false)",
            "personality": "Personality (if living)",
            "requirements": "Requirements to use",
            "location": "Current location (place ID)",
            "tags": "Tags (comma-separated)",
        },
    },
    "creature": {
        "dir": "creatures",
        "required": {"name": "Name", "danger_level": "Danger (low/medium/high/extreme/legendary)"},
        "optional": {
            "description": "Description",
            "behavior": "Behavior pattern",
            "attunement": "Attunement type (body/world/void/sense/bond)",
            "body_parts": "Body parts (comma-separated, e.g. head,torso,right_arm,left_arm,legs)",
            "hp_head": "Head HP", "hp_torso": "Torso HP",
            "hp_right_arm": "Right Arm HP", "hp_left_arm": "Left Arm HP",
            "hp_legs": "Legs HP",
            "cards": "Combat cards (comma-separated IDs)",
            "drops": "Drops on defeat (comma-separated)",
            "habitat": "Habitat (comma-separated place IDs)",
            "worship_powered": "Is it worship-powered? (true/false)",
            "tags": "Tags (comma-separated)",
        },
    },
    "era": {
        "dir": "eras",
        "required": {"name": "Name", "order": "Order (numeric, for sequencing)"},
        "optional": {
            "defining_tension": "Defining tension",
            "technology_level": "Technology level",
            "active_threats": "Active threats (comma-separated IDs)",
            "active_factions": "Active factions (comma-separated IDs)",
            "active_cultures": "Active cultures (comma-separated IDs)",
            "description": "Description",
            "tags": "Tags (comma-separated)",
        },
    },
    "threat": {
        "dir": "threats",
        "required": {"name": "Name"},
        "optional": {
            "stage_1": "Stage 1 — Whisper (description)",
            "stage_2": "Stage 2 — Rumor (description)",
            "stage_3": "Stage 3 — Crisis (description)",
            "stage_4": "Stage 4 — New Normal (description)",
            "current_stage": "Current stage (1-4)",
            "source": "Source/cause",
            "affected_regions": "Affected regions (comma-separated place IDs)",
            "description": "Description",
            "tags": "Tags (comma-separated)",
        },
    },
    "relationship": {
        "dir": "relationships",
        "required": {"name": "Name", "type": "Type (family/mentor/friend/rival/lover/enemy/ward)"},
        "optional": {
            "description": "Description",
            "emotional_function": "Emotional function",
            "archetype_tendency": "Archetypes that tend to form this (comma-separated)",
            "trait_compatibility": "Traits that encourage this (comma-separated)",
            "tags": "Tags (comma-separated)",
        },
    },
    "card": {
        "dir": "cards",
        "required": {"name": "Name", "energy_cost": "Energy cost (0-3)"},
        "optional": {
            "attunement": "Attunement (body/world/void/sense/bond)",
            "source": "Source (attunement/equipment/trait/wound/worship/divine)",
            "stage_required": "Stage required (awakened/practiced/focused/tempered/masterful/transcendent)",
            "damage": "Damage",
            "armor": "Armor granted",
            "target": "Target (chosen_body_part/all_parts/self/ally)",
            "special_effect": "Special effect description",
            "upgrade_path": "Upgrade options (comma-separated card IDs)",
            "flavor_text": "Flavor text",
            "tags": "Tags (comma-separated)",
        },
    },
    "event": {
        "dir": "events",
        "required": {"name": "Name", "age": "Age (childhood/adolescence/adulthood/elder/any)"},
        "optional": {
            "category": "Category (life/world/combat)",
            "archetype_filter": "Archetype filter (comma-separated IDs, or 'any')",
            "trait_requires_any": "Requires any trait (comma-separated)",
            "trait_excludes": "Excludes traits (comma-separated)",
            "faction_present": "Requires faction present (comma-separated IDs)",
            "era_filter": "Era filter (comma-separated IDs)",
            "threat_active": "Requires threat active (ID)",
            "text": "Full text",
            "tags": "Tags (comma-separated)",
        },
    },
    "scene": {
        "dir": "scenes",
        "required": {"name": "Name", "scene_type": "Type (relationship/awakening/death/god)"},
        "optional": {
            "relationship_type": "Relationship type (if relationship scene)",
            "beat": "Beat (introduction/bonding/critical/callback)",
            "archetype_filter": "Archetype filter (comma-separated)",
            "text": "Full text",
            "callback_detail": "Specific detail to plant for later callback",
            "tags": "Tags (comma-separated)",
        },
    },
}

# Fields stored as lists
LIST_FIELDS = {
    "tags", "starting_traits", "relationship_tendencies", "place_requirements",
    "values", "archetype_tendencies", "trait_tendencies", "worship_tendency",
    "contact_history", "descendants", "factions", "threats", "connections",
    "territory", "allies", "enemies", "domain", "worshipped_in", "served_by",
    "conflicts_with", "cards_granted", "body_parts", "drops", "habitat",
    "active_threats", "active_factions", "active_cultures", "affected_regions",
    "archetype_tendency", "trait_compatibility", "upgrade_path",
    "archetype_filter", "trait_requires_any", "trait_excludes",
    "faction_present", "era_filter", "gates_choices", "excludes_choices",
}

# --- Utility ---

def make_id(name):
    return re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')

def get_data_path(entity_type):
    return DATA_DIR / SCHEMAS[entity_type]["dir"]

def load_entities(entity_type):
    """Load all entities of a type from their directory."""
    path = get_data_path(entity_type)
    path.mkdir(parents=True, exist_ok=True)
    entities = {}
    for f in sorted(path.rglob("*.json")):
        try:
            data = json.loads(f.read_text())
            entities[data["id"]] = data
        except (json.JSONDecodeError, KeyError):
            pass
    return entities

def save_entity(entity_type, entity):
    """Save a single entity to its JSON file."""
    path = get_data_path(entity_type)
    path.mkdir(parents=True, exist_ok=True)
    filepath = path / f"{entity['id']}.json"
    filepath.write_text(json.dumps(entity, indent=2, ensure_ascii=False) + "\n")

def delete_entity_file(entity_type, entity_id):
    filepath = get_data_path(entity_type) / f"{entity_id}.json"
    if filepath.exists():
        filepath.unlink()

# --- Display ---

def display_entity(entity_type, entity):
    color = TYPE_COLORS.get(entity_type, "")
    name = entity.get("name", "?")
    print(f"\n{BOLD}{color}=== {SCHEMAS[entity_type]['dir'].title()[:-1]}: {name} ==={RESET}\n")
    skip = {"id", "created", "modified"}
    for key, value in entity.items():
        if key in skip:
            continue
        if isinstance(value, list) and value:
            print(f"  {BOLD}{key}:{RESET} {', '.join(str(v) for v in value)}")
        elif isinstance(value, str) and len(value) > 80:
            print(f"  {BOLD}{key}:{RESET}")
            for line in textwrap.wrap(value, 76):
                print(f"    {line}")
        elif value is not None and value != [] and value != "":
            print(f"  {BOLD}{key}:{RESET} {value}")
    print(f"\n  {DIM}[id: {entity['id']}] [created: {entity.get('created', '?')}]{RESET}")
    if entity.get("modified"):
        print(f"  {DIM}[modified: {entity['modified']}]{RESET}")
    print()

def display_list(entity_type, entities):
    if not entities:
        print(f"  No {entity_type}s found.")
        return
    color = TYPE_COLORS.get(entity_type, "")
    print(f"\n{BOLD}{color}=== {entity_type.title()}s ({len(entities)}) ==={RESET}\n")
    for e in entities.values():
        eid = e["id"]
        name = e.get("name", "?")
        tags = ", ".join(e.get("tags", []))
        extra = ""
        if entity_type == "trait":
            extra = f" [{e.get('source', '?')}] [{e.get('rarity', 'common')}]"
        elif entity_type == "card":
            extra = f" [{e.get('attunement', '?')}] cost:{e.get('energy_cost', '?')}"
        elif entity_type == "event":
            extra = f" [{e.get('age', '?')}] [{e.get('category', 'life')}]"
        elif entity_type == "creature":
            extra = f" [{e.get('danger_level', '?')}]"
        elif entity_type == "god":
            extra = f" [{e.get('type', '?')}]"
        print(f"  {eid:<25}{extra}  {DIM}{name}{RESET}")
        if tags:
            print(f"  {' ' * 25}  {DIM}tags: {tags}{RESET}")
    print()

# --- Interactive Add ---

def prompt_field(label, required=False, multiline=False):
    suffix = "" if required else f" {DIM}(Enter to skip){RESET}"
    if multiline:
        print(f"  {label}{suffix} — blank line to finish:")
        lines = []
        while True:
            line = input("    ")
            if line == "" and lines:
                break
            if line == "" and not lines:
                return None
            lines.append(line)
        return "\n".join(lines).strip() or None
    else:
        value = input(f"  {label}{suffix}: ").strip()
        if not value and required:
            while not value:
                value = input(f"  {label} (required): ").strip()
        return value or None

def prompt_list(label):
    value = input(f"  {label} {DIM}(comma-separated, Enter to skip){RESET}: ").strip()
    if not value:
        return []
    return [v.strip() for v in value.split(",") if v.strip()]

def interactive_add(entity_type):
    schema = SCHEMAS[entity_type]
    color = TYPE_COLORS.get(entity_type, "")
    print(f"\n{color}Creating new {entity_type}...{RESET}\n")
    fields = {}
    for field, label in schema["required"].items():
        fields[field] = prompt_field(label, required=True)
    for field, label in schema["optional"].items():
        if field == "text":
            value = prompt_field(label, multiline=True)
        elif field in LIST_FIELDS:
            value = prompt_list(label)
        else:
            value = prompt_field(label)
        if value:
            fields[field] = value
    return fields

# --- Event Choices (special handling) ---

def add_choices_to_event(entity):
    """Interactive choice builder for events."""
    if entity.get("type") not in (None, "event") and "age" not in entity:
        return
    choices = []
    if input(f"\n  Add choices? {DIM}(y/n){RESET}: ").strip().lower() == "y":
        while True:
            text = input("    Choice text: ").strip()
            if not text:
                break
            choice = {"text": text}
            req_trait = input("    Requires trait (or empty): ").strip()
            if req_trait:
                choice["requires"] = {"trait": req_trait}
            effects = {}
            trait_gain = input("    Trait gained (or empty): ").strip()
            if trait_gain:
                effects["trait_gain"] = trait_gain
            card_gain = input("    Card gained (or empty): ").strip()
            if card_gain:
                effects["card_gain"] = card_gain
            if effects:
                choice["effects"] = effects
            consequence = input("    Consequence text (or empty): ").strip()
            if consequence:
                choice["consequence_text"] = consequence
            choices.append(choice)
            if input(f"    Another? {DIM}(y/n){RESET}: ").strip().lower() != "y":
                break
    if choices:
        entity["choices"] = choices

# --- CLI Parsing ---

def parse_cli_fields(args):
    fields = {}
    i = 0
    while i < len(args):
        if args[i].startswith("--"):
            key = args[i][2:]
            if i + 1 < len(args) and not args[i + 1].startswith("--"):
                value = args[i + 1]
                if key in LIST_FIELDS:
                    value = [v.strip() for v in value.split(",")]
                fields[key] = value
                i += 2
            else:
                fields[key] = True
                i += 1
        else:
            i += 1
    return fields

# --- Search ---

def search_all(query="", entity_type=None, tag=None):
    results = []
    types = [entity_type] if entity_type else list(SCHEMAS.keys())
    q = query.lower() if query else ""
    for etype in types:
        for eid, entity in load_entities(etype).items():
            if tag and tag not in entity.get("tags", []):
                continue
            if not q:
                if tag:
                    results.append((etype, eid, entity))
                continue
            matched = False
            for key, value in entity.items():
                if key in ("id", "created", "modified"):
                    continue
                if isinstance(value, str) and q in value.lower():
                    matched = True
                    break
                elif isinstance(value, list) and any(q in str(v).lower() for v in value):
                    matched = True
                    break
            if matched:
                results.append((etype, eid, entity))
    return results

# --- Validate ---

def validate_all():
    issues = []
    all_ids = {}
    for etype in SCHEMAS:
        for eid, entity in load_entities(etype).items():
            all_ids[(etype, eid)] = entity
            for field in SCHEMAS[etype]["required"]:
                if not entity.get(field):
                    issues.append(f"  {etype}/{eid}: missing required '{field}'")

    # Check cross-references
    ref_fields = {
        "culture": ["era"], "place": ["culture", "factions", "threats", "connections"],
        "faction": ["territory", "allies", "enemies"],
        "god": ["worshipped_in", "served_by", "conflicts_with"],
        "artifact": ["created_by", "location", "cards_granted"],
        "creature": ["habitat", "cards"], "era": ["active_threats", "active_factions", "active_cultures"],
        "threat": ["affected_regions"], "event": ["archetype_filter", "faction_present", "era_filter"],
    }
    # Note: ref validation is advisory, not blocking — content builds incrementally
    return issues

# --- Coverage Analysis ---

def analyze_coverage():
    events = load_entities("event")
    archetypes = load_entities("archetype")
    traits = load_entities("trait")

    print(f"\n{BOLD}=== Content Coverage ==={RESET}\n")

    # Events by age
    by_age = {}
    for e in events.values():
        age = e.get("age", "any")
        by_age.setdefault(age, []).append(e)
    for age in ["childhood", "adolescence", "adulthood", "elder", "any"]:
        count = len(by_age.get(age, []))
        bar = "█" * min(count, 50)
        print(f"  {age:<14} {count:>3} events  {DIM}{bar}{RESET}")

    # Events by category
    print()
    by_cat = {}
    for e in events.values():
        cat = e.get("category", "life")
        by_cat.setdefault(cat, []).append(e)
    for cat in ["life", "world", "combat"]:
        count = len(by_cat.get(cat, []))
        print(f"  {cat:<14} {count:>3} events")

    # Scenes
    scenes = load_entities("scene")
    by_type = {}
    for s in scenes.values():
        st = s.get("scene_type", "?")
        by_type.setdefault(st, []).append(s)
    print(f"\n  Scenes:")
    for st in ["relationship", "awakening", "death", "god"]:
        count = len(by_type.get(st, []))
        print(f"    {st:<14} {count:>3}")

    # Cards by attunement
    cards = load_entities("card")
    by_att = {}
    for c in cards.values():
        att = c.get("attunement", "none")
        by_att.setdefault(att, []).append(c)
    print(f"\n  Cards:")
    for att in ["body", "world", "void", "sense", "bond", "none"]:
        count = len(by_att.get(att, []))
        print(f"    {att:<14} {count:>3}")

    print()

# --- Refinement Tools ---

def show_drafts():
    """Show all entities that haven't been marked as polished."""
    print(f"\n{BOLD}=== Drafts (unpolished content) ==={RESET}\n")
    total = 0
    for etype in SCHEMAS:
        for eid, entity in load_entities(etype).items():
            status = entity.get("status", "draft")
            if status != "polished":
                color = TYPE_COLORS.get(etype, "")
                name = entity.get("name", "?")
                wc = len(entity.get("text", "").split()) if entity.get("text") else 0
                status_str = f"{YELLOW}[{status}]{RESET}" if status == "needs_revision" else f"{DIM}[{status}]{RESET}"
                print(f"  {color}[{etype}]{RESET} {eid:<30} {status_str} {DIM}{wc}w{RESET}  {name}")
                total += 1
    print(f"\n  {total} items need attention.\n")


def show_wordcounts():
    """Word count per entity for prose-heavy content."""
    print(f"\n{BOLD}=== Word Counts ==={RESET}\n")
    for etype in ["event", "scene"]:
        entities = load_entities(etype)
        if not entities:
            continue
        color = TYPE_COLORS.get(etype, "")
        print(f"  {color}{etype}s:{RESET}")
        items = []
        for eid, entity in entities.items():
            wc = 0
            if entity.get("text"):
                wc += len(entity["text"].split())
            for choice in entity.get("choices", []):
                for k in ("text", "consequence_text"):
                    if k in choice:
                        wc += len(choice[k].split())
            items.append((eid, entity.get("name", "?"), wc, entity.get("status", "draft")))
        items.sort(key=lambda x: -x[2])
        for eid, name, wc, status in items:
            bar = "█" * min(wc // 20, 30)
            print(f"    {eid:<35} {wc:>4}w  {DIM}{bar}{RESET}")
        print()


def show_related(entity_type, entity_id):
    """Show all content related to an entity (same archetype, same relationship, etc.)."""
    entity = load_entities(entity_type).get(entity_id)
    if not entity:
        print(f"  {entity_type} '{entity_id}' not found")
        return

    print(f"\n{BOLD}=== Related to {entity.get('name', entity_id)} ==={RESET}\n")

    # Find by shared tags
    tags = set(entity.get("tags", []))
    if not tags:
        print("  No tags to search by.")
        return

    for etype in SCHEMAS:
        for eid, e in load_entities(etype).items():
            if eid == entity_id and etype == entity_type:
                continue
            shared = tags & set(e.get("tags", []))
            if len(shared) >= 2:  # at least 2 shared tags
                color = TYPE_COLORS.get(etype, "")
                name = e.get("name", "?")
                print(f"  {color}[{etype}]{RESET} {eid}: {name}  {DIM}shared: {', '.join(shared)}{RESET}")
    print()


# --- Stats ---

def show_stats():
    print(f"\n{BOLD}=== VESTIGE — World Stats ==={RESET}\n")
    total = 0
    for etype in SCHEMAS:
        entities = load_entities(etype)
        count = len(entities)
        total += count
        color = TYPE_COLORS.get(etype, "")
        print(f"  {color}{etype + 's:':<18}{RESET} {count}")
    print(f"\n  {BOLD}{'Total:':<18}{RESET} {total}")

    issues = validate_all()
    if issues:
        print(f"\n  {YELLOW}Validation: {len(issues)} issue(s){RESET}")
    else:
        print(f"\n  {GREEN}Validation: all clear{RESET}")
    print()

# --- Main ---

def print_help():
    print(f"""
{BOLD}Vestige — World Authoring System{RESET}

{BOLD}Entity commands:{RESET}
  world.py <type> add              Create (interactive)
  world.py <type> add --name X     Create (inline)
  world.py <type> view <id>        View details
  world.py <type> list             List all
  world.py <type> edit <id>        Edit (interactive or --field value)
  world.py <type> delete <id>      Delete

  Types: archetype, trait, culture, place, faction, god, artifact,
         creature, era, threat, relationship, card, event, scene

{BOLD}Search & Analysis:{RESET}
  world.py search "query"          Full-text search
  world.py search --type trait "X" Search specific type
  world.py search --tag fire       Search by tag

{BOLD}Refinement:{RESET}
  world.py drafts                  Show all unpolished content
  world.py wordcounts              Word count per event/scene
  world.py related <type> <id>     Show related content by shared tags
  world.py polish <type> <id>      Mark entity as polished
  world.py flag <type> <id>        Mark entity as needs_revision
  world.py validate                Check consistency
  world.py coverage                Content coverage analysis
  world.py stats                   World overview
""")

def main():
    if len(sys.argv) < 2:
        print_help()
        return

    command = sys.argv[1]

    if command in ("help", "--help", "-h"):
        print_help()
        return

    # Entity commands
    if command in SCHEMAS:
        entity_type = command
        action = sys.argv[2] if len(sys.argv) > 2 else "list"
        rest = sys.argv[3:]

        if action == "add":
            if rest:
                fields = parse_cli_fields(rest)
            else:
                fields = interactive_add(entity_type)
                if entity_type == "event":
                    add_choices_to_event(fields)

            eid = fields.get("id") or make_id(fields.get("name", "unnamed"))
            fields["id"] = eid
            fields["created"] = datetime.now().isoformat()[:19]
            # Ensure list fields are lists
            for f in LIST_FIELDS:
                if f in fields and isinstance(fields[f], str):
                    fields[f] = [v.strip() for v in fields[f].split(",")]

            save_entity(entity_type, fields)
            color = TYPE_COLORS.get(entity_type, "")
            print(f"\n  {GREEN}Created{RESET} {color}{entity_type}{RESET} '{BOLD}{eid}{RESET}'")

        elif action == "view":
            if not rest:
                print(f"  Usage: world.py {entity_type} view <id>")
                return
            entities = load_entities(entity_type)
            entity = entities.get(rest[0])
            if entity:
                display_entity(entity_type, entity)
            else:
                matches = [eid for eid in entities if rest[0] in eid]
                if matches:
                    print(f"  '{rest[0]}' not found. Did you mean: {', '.join(matches)}?")
                else:
                    print(f"  {entity_type} '{rest[0]}' not found")

        elif action == "list":
            entities = load_entities(entity_type)
            # Optional tag filter
            if rest and rest[0].startswith("--tag") and len(rest) > 1:
                tag = rest[1]
                entities = {k: v for k, v in entities.items() if tag in v.get("tags", [])}
            display_list(entity_type, entities)

        elif action == "edit":
            if not rest:
                print(f"  Usage: world.py {entity_type} edit <id> [--field value]")
                return
            eid = rest[0]
            entities = load_entities(entity_type)
            entity = entities.get(eid)
            if not entity:
                print(f"  {entity_type} '{eid}' not found")
                return
            field_args = rest[1:]
            if field_args:
                updates = parse_cli_fields(field_args)
                entity.update(updates)
                entity["modified"] = datetime.now().isoformat()[:19]
                save_entity(entity_type, entity)
                print(f"  {GREEN}Updated{RESET} {entity_type} '{eid}'")
            else:
                print(f"\n  Editing {entity_type} '{eid}' {DIM}(Enter to keep current){RESET}\n")
                updates = {}
                all_fields = {**SCHEMAS[entity_type]["required"], **SCHEMAS[entity_type]["optional"]}
                for field, label in all_fields.items():
                    current = entity.get(field, "")
                    if isinstance(current, list):
                        current_str = ", ".join(str(v) for v in current)
                        new_val = input(f"  {label} [{current_str}]: ").strip()
                        if new_val:
                            updates[field] = [v.strip() for v in new_val.split(",")]
                    elif field == "text":
                        length = len(current) if current else 0
                        print(f"  {label} {DIM}({length} chars, Enter to keep){RESET}:")
                        lines = []
                        while True:
                            line = input("    ")
                            if line == "" and not lines:
                                break
                            if line == "" and lines:
                                break
                            lines.append(line)
                        if lines:
                            updates[field] = "\n".join(lines).strip()
                    else:
                        new_val = input(f"  {label} [{current}]: ").strip()
                        if new_val:
                            updates[field] = new_val
                if updates:
                    entity.update(updates)
                    entity["modified"] = datetime.now().isoformat()[:19]
                    save_entity(entity_type, entity)
                    print(f"\n  {GREEN}Updated{RESET} {entity_type} '{eid}'")
                else:
                    print(f"\n  No changes.")

        elif action == "delete":
            if not rest:
                print(f"  Usage: world.py {entity_type} delete <id>")
                return
            eid = rest[0]
            entities = load_entities(entity_type)
            if eid not in entities:
                print(f"  {entity_type} '{eid}' not found")
                return
            delete_entity_file(entity_type, eid)
            print(f"  {GREEN}Deleted{RESET} {entity_type} '{eid}'")

        else:
            print(f"  Unknown action '{action}'. Try: add, view, list, edit, delete")

    # Search
    elif command == "search":
        query = ""
        etype = None
        tag = None
        i = 2
        while i < len(sys.argv):
            if sys.argv[i] == "--type" and i + 1 < len(sys.argv):
                etype = sys.argv[i + 1]; i += 2
            elif sys.argv[i] == "--tag" and i + 1 < len(sys.argv):
                tag = sys.argv[i + 1]; i += 2
            elif not sys.argv[i].startswith("--"):
                query = sys.argv[i]; i += 1
            else:
                i += 1
        results = search_all(query, entity_type=etype, tag=tag)
        if not results:
            print(f"  No results.")
            return
        print(f"\n{BOLD}=== Search Results ({len(results)}) ==={RESET}\n")
        for et, eid, entity in results:
            color = TYPE_COLORS.get(et, "")
            name = entity.get("name", "?")
            print(f"  {color}[{et}]{RESET} {eid}: {BOLD}{name}{RESET}")
        print()

    elif command == "validate":
        issues = validate_all()
        if issues:
            print(f"\n{BOLD}{YELLOW}=== Validation: {len(issues)} issue(s) ==={RESET}\n")
            for issue in issues:
                print(issue)
        else:
            print(f"\n  {GREEN}All clear.{RESET}\n")

    elif command == "coverage":
        analyze_coverage()

    elif command == "stats":
        show_stats()

    # Refinement tools
    elif command == "drafts":
        show_drafts()

    elif command == "wordcounts":
        show_wordcounts()

    elif command == "related":
        if len(sys.argv) < 4:
            print("  Usage: world.py related <type> <id>")
            return
        show_related(sys.argv[2], sys.argv[3])

    elif command == "polish":
        if len(sys.argv) < 4:
            print("  Usage: world.py polish <type> <id>")
            return
        etype, eid = sys.argv[2], sys.argv[3]
        entities = load_entities(etype)
        if eid in entities:
            entities[eid]["status"] = "polished"
            entities[eid]["modified"] = datetime.now().isoformat()[:19]
            save_entity(etype, entities[eid])
            print(f"  {GREEN}Polished{RESET} {etype} '{eid}'")
        else:
            print(f"  {etype} '{eid}' not found")

    elif command == "flag":
        if len(sys.argv) < 4:
            print("  Usage: world.py flag <type> <id>")
            return
        etype, eid = sys.argv[2], sys.argv[3]
        entities = load_entities(etype)
        if eid in entities:
            entities[eid]["status"] = "needs_revision"
            entities[eid]["modified"] = datetime.now().isoformat()[:19]
            save_entity(etype, entities[eid])
            print(f"  {YELLOW}Flagged{RESET} {etype} '{eid}' for revision")
        else:
            print(f"  {etype} '{eid}' not found")

    else:
        print(f"  Unknown command: {command}")
        print_help()


if __name__ == "__main__":
    main()
