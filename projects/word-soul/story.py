#!/usr/bin/env python3
"""
Word Soul: Origins — World Authoring System
by Wren

A CLI tool for building and managing the Word Soul universe.
Creates and maintains characters, creatures, locations, items, and encounters
with automatic bidirectional references.

Usage:
    python3 story.py <entity_type> <action> [args]
    python3 story.py link <type> <entity_id> <encounter_id>
    python3 story.py search <query> [--type <type>] [--tag <tag>]
    python3 story.py validate
    python3 story.py graph [stage]
    python3 story.py stats

Entity types: character, creature, location, item, encounter
Actions: add, view, list, edit, delete

Examples:
    story.py character add                          # interactive
    story.py character add --name Asha --word ember  # inline
    story.py character view asha
    story.py character list --word ember
    story.py encounter list childhood
    story.py link character asha ember_junction_1
    story.py search "ember" --type character
    story.py search --tag core
    story.py validate
    story.py stats
"""

import json
import sys
import re
import textwrap
from pathlib import Path
from datetime import datetime

# --- Paths ---
DATA_DIR = Path(__file__).parent / "data"

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
    "character": CYAN,
    "creature": RED,
    "location": GREEN,
    "item": YELLOW,
    "encounter": MAGENTA,
}

# --- Schemas ---
# Each entity type: file, required fields, optional fields, display name
SCHEMAS = {
    "character": {
        "file": "characters.json",
        "required": {"name": "Name", "word": "Word"},
        "optional": {
            "role": "Role (mentor/companion/antagonist/guide/npc)",
            "age": "Age",
            "want": "Want (what they desire)",
            "fear": "Fear (what they dread)",
            "contradiction": "Contradiction (where they're hypocritical)",
            "backstory": "Backstory",
            "why_helps": "Why they help the player",
            "tags": "Tags",
        },
        "display": "Character",
    },
    "creature": {
        "file": "creatures.json",
        "required": {"name": "Name", "description": "Description"},
        "optional": {
            "behavior": "Behavior pattern",
            "hp": "HP",
            "atk": "Attack",
            "speed": "Speed (slow/medium/fast)",
            "habitat": "Habitat zones",
            "danger_level": "Danger level (low/medium/high/extreme)",
            "word_affinity": "Word affinities",
            "drops": "Item drops",
            "tags": "Tags",
        },
        "display": "Creature",
    },
    "location": {
        "file": "locations.json",
        "required": {"name": "Name", "region": "Region (village/upper_roots/living_network/dying_roots/deep_root)"},
        "optional": {
            "description": "Description",
            "atmosphere": "Atmosphere (sights, sounds, smells)",
            "connections": "Connected location IDs",
            "inhabitants": "Inhabitant entity IDs",
            "resources": "Available resources",
            "danger_level": "Danger level (safe/low/medium/high/extreme)",
            "tags": "Tags",
        },
        "display": "Location",
    },
    "item": {
        "file": "items.json",
        "required": {"name": "Name", "type": "Type (weapon/armor/key_item/consumable/material/artifact)"},
        "optional": {
            "description": "Description",
            "rarity": "Rarity (common/uncommon/rare/unique)",
            "word_affinity": "Word affinities",
            "effect": "Effect description",
            "stats": "Stat modifiers (e.g. hp+2, atk+1)",
            "tags": "Tags",
        },
        "display": "Item",
    },
    "encounter": {
        "file": "encounters.json",
        "required": {"title": "Title", "stage": "Stage"},
        "optional": {
            "text": "Narration text",
            "tags": "Tags",
        },
        "display": "Encounter",
        "stages": [
            "childhood", "adolescence", "emergence",
            "upper_roots", "living_network", "dying_roots", "deep_root",
            "endgame",
        ],
    },
}

# Fields stored as lists (comma-separated input)
LIST_FIELDS = {
    "tags", "habitat", "word_affinity", "drops", "connections",
    "inhabitants", "resources", "stats",
}

# --- Utility ---

def make_id(name):
    """Generate a slug ID from a name."""
    return re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')


def load_data(entity_type):
    """Load JSON data for an entity type."""
    filepath = DATA_DIR / SCHEMAS[entity_type]["file"]
    if filepath.exists():
        text = filepath.read_text().strip()
        if text:
            return json.loads(text)
    return {}


def save_data(entity_type, data):
    """Save JSON data for an entity type."""
    filepath = DATA_DIR / SCHEMAS[entity_type]["file"]
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


# --- WorldDB ---

class WorldDB:
    """Manages all world data with bidirectional references."""

    def __init__(self):
        self.data = {}
        for etype in SCHEMAS:
            self.data[etype] = load_data(etype)

    def save(self, *entity_types):
        for et in entity_types:
            save_data(et, self.data[et])

    def add(self, entity_type, fields):
        """Add a new entity. Returns its ID."""
        if entity_type == "encounter":
            eid = fields.get("id") or make_id(fields.get("title", "unnamed"))
        else:
            eid = fields.get("id") or make_id(fields.get("name", "unnamed"))

        # Handle ID collision
        base_id = eid
        counter = 2
        while eid in self.data[entity_type]:
            eid = f"{base_id}_{counter}"
            counter += 1

        fields["id"] = eid
        fields["created"] = datetime.now().isoformat()[:19]

        # Entity-specific defaults
        if entity_type == "encounter":
            fields.setdefault("choices", [])
            fields.setdefault("characters", [])
            fields.setdefault("creatures", [])
            fields.setdefault("items", [])
            fields.setdefault("locations", [])
            fields.setdefault("text_variants", {})
            fields.setdefault("conditions", None)
        else:
            fields.setdefault("appearances", [])

        self.data[entity_type][eid] = fields
        self.save(entity_type)
        return eid

    def get(self, entity_type, eid):
        return self.data[entity_type].get(eid)

    def list_all(self, entity_type, **filters):
        """List entities with optional filtering."""
        results = list(self.data[entity_type].values())
        for key, value in filters.items():
            if value is None:
                continue
            filtered = []
            for e in results:
                v = e.get(key)
                if v == value:
                    filtered.append(e)
                elif isinstance(v, list) and value in v:
                    filtered.append(e)
                elif isinstance(v, str) and value.lower() in v.lower():
                    filtered.append(e)
            results = filtered
        return results

    def update(self, entity_type, eid, updates):
        """Update fields on an entity."""
        if eid not in self.data[entity_type]:
            return False
        self.data[entity_type][eid].update(updates)
        self.data[entity_type][eid]["modified"] = datetime.now().isoformat()[:19]
        self.save(entity_type)
        return True

    def delete(self, entity_type, eid):
        """Delete an entity, cleaning up all references."""
        entity = self.data[entity_type].get(eid)
        if not entity:
            return False

        if entity_type != "encounter":
            # Remove from all encounters this entity appears in
            for enc_id in entity.get("appearances", []):
                enc = self.data["encounter"].get(enc_id)
                if enc:
                    key = entity_type + "s"
                    if eid in enc.get(key, []):
                        enc[key].remove(eid)
            self.save("encounter")
        else:
            # Removing an encounter — clean up all entity backrefs
            for etype in SCHEMAS:
                if etype == "encounter":
                    continue
                for e in self.data[etype].values():
                    if eid in e.get("appearances", []):
                        e["appearances"].remove(eid)
                self.save(etype)

        del self.data[entity_type][eid]
        self.save(entity_type)
        return True

    def link(self, entity_type, eid, encounter_id):
        """Bidirectional link: entity ↔ encounter."""
        entity = self.data.get(entity_type, {}).get(eid)
        encounter = self.data.get("encounter", {}).get(encounter_id)

        if not entity:
            print(f"  {RED}Error:{RESET} {entity_type} '{eid}' not found")
            return False
        if not encounter:
            print(f"  {RED}Error:{RESET} encounter '{encounter_id}' not found")
            return False

        changed = False
        key = entity_type + "s"

        if encounter_id not in entity.get("appearances", []):
            entity.setdefault("appearances", []).append(encounter_id)
            changed = True
        if eid not in encounter.get(key, []):
            encounter.setdefault(key, []).append(eid)
            changed = True

        if changed:
            self.save(entity_type, "encounter")
        return True

    def unlink(self, entity_type, eid, encounter_id):
        """Remove bidirectional link."""
        entity = self.data.get(entity_type, {}).get(eid)
        encounter = self.data.get("encounter", {}).get(encounter_id)
        changed = False

        if entity and encounter_id in entity.get("appearances", []):
            entity["appearances"].remove(encounter_id)
            changed = True
        key = entity_type + "s"
        if encounter and eid in encounter.get(key, []):
            encounter[key].remove(eid)
            changed = True

        if changed:
            self.save(entity_type, "encounter")
        return changed

    def search(self, query="", entity_type=None, tag=None):
        """Full-text search across all or specific entity types."""
        results = []
        types = [entity_type] if entity_type else list(SCHEMAS.keys())
        q = query.lower() if query else ""

        for etype in types:
            for eid, entity in self.data.get(etype, {}).items():
                # Tag filter
                if tag and tag not in entity.get("tags", []):
                    continue

                if not q:
                    if tag:
                        results.append((etype, eid, entity))
                    continue

                # Search all text fields
                matched = False
                for key, value in entity.items():
                    if key in ("id", "created", "modified", "appearances", "choices"):
                        continue
                    if isinstance(value, str) and q in value.lower():
                        matched = True
                        break
                    elif isinstance(value, list):
                        if any(q in str(v).lower() for v in value):
                            matched = True
                            break
                    elif isinstance(value, dict):
                        if any(q in str(v).lower() for v in value.values()):
                            matched = True
                            break
                if matched:
                    results.append((etype, eid, entity))

        return results

    def validate(self):
        """Check referential integrity across all data."""
        issues = []

        # Check entity → encounter refs
        for etype in SCHEMAS:
            if etype == "encounter":
                continue
            for eid, entity in self.data.get(etype, {}).items():
                for field in SCHEMAS[etype]["required"]:
                    if not entity.get(field):
                        issues.append(f"  {etype}/{eid}: missing required '{field}'")
                for enc_id in entity.get("appearances", []):
                    enc = self.data["encounter"].get(enc_id)
                    if not enc:
                        issues.append(f"  {etype}/{eid}: references missing encounter '{enc_id}'")
                    elif eid not in enc.get(etype + "s", []):
                        issues.append(f"  {etype}/{eid}: in '{enc_id}' but encounter doesn't list it back")

        # Check encounter → entity refs
        for enc_id, enc in self.data.get("encounter", {}).items():
            for field in SCHEMAS["encounter"]["required"]:
                if not enc.get(field):
                    issues.append(f"  encounter/{enc_id}: missing required '{field}'")

            if enc.get("stage") and enc["stage"] not in SCHEMAS["encounter"]["stages"]:
                issues.append(f"  encounter/{enc_id}: invalid stage '{enc['stage']}'")

            for etype in ["character", "creature", "item", "location"]:
                for eid in enc.get(etype + "s", []):
                    entity = self.data.get(etype, {}).get(eid)
                    if not entity:
                        issues.append(f"  encounter/{enc_id}: references missing {etype} '{eid}'")
                    elif enc_id not in entity.get("appearances", []):
                        issues.append(f"  encounter/{enc_id}: lists {etype} '{eid}' but entity missing backref")

            # Check choice targets
            for i, choice in enumerate(enc.get("choices", [])):
                target = choice.get("next")
                if target and target not in self.data.get("encounter", {}):
                    issues.append(f"  encounter/{enc_id}: choice [{i}] → missing '{target}'")

            # Dead ends
            if not enc.get("choices") and "ending" not in enc.get("tags", []):
                issues.append(f"  encounter/{enc_id}: no choices (not tagged 'ending')")

        return issues

    def stats(self):
        """World overview."""
        lines = [f"\n{BOLD}=== WORD SOUL: ORIGINS — World Stats ==={RESET}\n"]

        total_enc = len(self.data.get("encounter", {}))
        for etype in SCHEMAS:
            if etype == "encounter":
                continue
            color = TYPE_COLORS[etype]
            total = len(self.data.get(etype, {}))
            linked = sum(1 for e in self.data.get(etype, {}).values()
                         if e.get("appearances"))
            lines.append(f"  {color}{SCHEMAS[etype]['display'] + 's:':<14}{RESET} "
                         f"{total} ({linked} linked to encounters)")

        # Encounter breakdown by stage
        stage_counts = {}
        for enc in self.data.get("encounter", {}).values():
            stage = enc.get("stage", "unknown")
            stage_counts[stage] = stage_counts.get(stage, 0) + 1

        stage_str = ", ".join(f"{s}: {c}" for s, c in sorted(stage_counts.items()))
        color = TYPE_COLORS["encounter"]
        lines.append(f"  {color}{'Encounters:':<14}{RESET} "
                     f"{total_enc} ({stage_str or 'none yet'})")

        issues = self.validate()
        if issues:
            lines.append(f"\n  {YELLOW}Validation: {len(issues)} issue(s) "
                         f"— run 'validate' for details{RESET}")
        else:
            lines.append(f"\n  {GREEN}Validation: all clear{RESET}")

        return "\n".join(lines)

    def graph(self, stage=None):
        """ASCII visualization of encounter flow."""
        encounters = self.data.get("encounter", {})
        if not encounters:
            return "  No encounters yet."

        lines = []
        by_stage = {}
        for eid, enc in encounters.items():
            s = enc.get("stage", "unknown")
            by_stage.setdefault(s, []).append((eid, enc))

        stages = [stage] if stage else SCHEMAS["encounter"]["stages"]

        for s in stages:
            if s not in by_stage:
                continue
            encs = by_stage[s]
            lines.append(f"\n{BOLD}=== {s.upper().replace('_', ' ')} "
                         f"({len(encs)} encounters) ==={RESET}\n")

            for eid, enc in encs:
                chars = ", ".join(enc.get("characters", [])) or DIM + "none" + RESET
                color = TYPE_COLORS["encounter"]
                lines.append(f"  {color}[{eid}]{RESET} {enc.get('title', '?')}")
                lines.append(f"    {DIM}characters: {chars}{RESET}")

                choices = enc.get("choices", [])
                for i, choice in enumerate(choices):
                    target = choice.get("next", "???")
                    cond = choice.get("conditions")
                    cond_str = f" {DIM}(requires: {json.dumps(cond)}){RESET}" if cond else ""
                    arrow = "├─" if i < len(choices) - 1 else "└─"
                    lines.append(f"    {arrow} \"{choice.get('text', '?')}\" → {target}{cond_str}")

                if not choices:
                    if "ending" in enc.get("tags", []):
                        lines.append(f"    └─ {GREEN}[ENDING]{RESET}")
                    else:
                        lines.append(f"    └─ {YELLOW}[DEAD END]{RESET}")
                lines.append("")

        return "\n".join(lines) if lines else "  No encounters for this stage."


# --- Display ---

def display_entity(entity_type, entity, db=None):
    """Pretty-print a single entity."""
    color = TYPE_COLORS[entity_type]
    name = entity.get("name") or entity.get("title", "?")

    print(f"\n{BOLD}{color}=== {SCHEMAS[entity_type]['display']}: {name} ==={RESET}\n")

    # Show fields
    skip = {"id", "created", "modified", "appearances", "choices",
            "text_variants", "conditions", "characters", "creatures",
            "items", "locations"}

    for key, value in entity.items():
        if key in skip:
            continue
        if isinstance(value, list) and value:
            print(f"  {BOLD}{key}:{RESET} {', '.join(str(v) for v in value)}")
        elif isinstance(value, dict) and value:
            print(f"  {BOLD}{key}:{RESET}")
            for k, v in value.items():
                print(f"    {k}: {v}")
        elif isinstance(value, str) and len(value) > 80:
            print(f"  {BOLD}{key}:{RESET}")
            for line in textwrap.wrap(value, 76):
                print(f"    {line}")
        elif value is not None and value != [] and value != {}:
            print(f"  {BOLD}{key}:{RESET} {value}")

    # Encounter-specific: linked entities
    if entity_type == "encounter":
        for etype in ["character", "creature", "item", "location"]:
            linked = entity.get(etype + "s", [])
            if linked:
                ecolor = TYPE_COLORS[etype]
                names = []
                if db:
                    for lid in linked:
                        e = db.get(etype, lid)
                        n = e.get("name", lid) if e else lid
                        names.append(n)
                else:
                    names = linked
                print(f"  {BOLD}{etype}s:{RESET} {ecolor}{', '.join(names)}{RESET}")

        # Choices
        if entity.get("choices"):
            print(f"\n  {BOLD}Choices:{RESET}")
            for i, choice in enumerate(entity["choices"]):
                target = choice.get("next", "???")
                cond = choice.get("conditions")
                cond_str = f" {DIM}[requires: {json.dumps(cond)}]{RESET}" if cond else ""
                print(f"    [{i}] \"{choice.get('text', '?')}\" → {target}{cond_str}")

        # Text variants
        if entity.get("text_variants"):
            print(f"\n  {BOLD}Text Variants:{RESET}")
            for key, text in entity["text_variants"].items():
                print(f"    {DIM}[{key}]{RESET}")
                for line in textwrap.wrap(text, 72):
                    print(f"      {line}")

    # Appearances (for non-encounter entities)
    if entity.get("appearances"):
        print(f"\n  {BOLD}Appears in:{RESET}")
        for enc_id in entity["appearances"]:
            if db:
                enc = db.get("encounter", enc_id)
                if enc:
                    stage = enc.get("stage", "?")
                    title = enc.get("title", "?")
                    print(f"    {MAGENTA}{enc_id}{RESET} [{stage}] {title}")
                else:
                    print(f"    {RED}{enc_id} (missing!){RESET}")
            else:
                print(f"    {enc_id}")

    print(f"\n  {DIM}[id: {entity['id']}] "
          f"[created: {entity.get('created', '?')}]{RESET}")
    if entity.get("modified"):
        print(f"  {DIM}[modified: {entity['modified']}]{RESET}")
    print()


def display_list(entity_type, entities):
    """Display entities as a compact table."""
    if not entities:
        print(f"  No {SCHEMAS[entity_type]['display'].lower()}s found.")
        return

    color = TYPE_COLORS[entity_type]
    print(f"\n{BOLD}{color}=== {SCHEMAS[entity_type]['display']}s "
          f"({len(entities)}) ==={RESET}\n")

    for e in entities:
        eid = e["id"]
        if entity_type == "character":
            word = e.get("word", "?")
            name = e.get("name", "?")
            role = e.get("role", "")
            apps = len(e.get("appearances", []))
            print(f"  {eid:<20} [{word}] {name}"
                  f"{' — ' + role if role else ''}  "
                  f"{DIM}({apps} enc){RESET}")
        elif entity_type == "creature":
            name = e.get("name", "?")
            danger = e.get("danger_level", "?")
            apps = len(e.get("appearances", []))
            print(f"  {eid:<20} [{danger}] {name}  "
                  f"{DIM}({apps} enc){RESET}")
        elif entity_type == "location":
            name = e.get("name", "?")
            region = e.get("region", "?")
            apps = len(e.get("appearances", []))
            print(f"  {eid:<20} [{region}] {name}  "
                  f"{DIM}({apps} enc){RESET}")
        elif entity_type == "item":
            name = e.get("name", "?")
            itype = e.get("type", "?")
            rarity = e.get("rarity", "")
            apps = len(e.get("appearances", []))
            print(f"  {eid:<20} [{itype}] {name}"
                  f"{' (' + rarity + ')' if rarity else ''}  "
                  f"{DIM}({apps} enc){RESET}")
        elif entity_type == "encounter":
            title = e.get("title", "?")
            stage = e.get("stage", "?")
            n_ch = len(e.get("choices", []))
            chars = ", ".join(e.get("characters", [])) or "—"
            print(f"  {eid:<25} [{stage}] {title}  "
                  f"{DIM}({n_ch} choices, chars: {chars}){RESET}")
    print()


# --- Interactive Prompts ---

def prompt_field(label, required=False, multiline=False):
    """Prompt for a single field value."""
    suffix = "" if required else f" {DIM}(Enter to skip){RESET}"
    if multiline:
        print(f"  {label}{suffix} — enter text, blank line to finish:")
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
    """Prompt for comma-separated list."""
    value = input(f"  {label} {DIM}(comma-separated, Enter to skip){RESET}: ").strip()
    if not value:
        return []
    return [v.strip() for v in value.split(",") if v.strip()]


def interactive_add(entity_type, db):
    """Walk through adding an entity interactively."""
    schema = SCHEMAS[entity_type]
    color = TYPE_COLORS[entity_type]
    print(f"\n{color}Creating new {schema['display']}...{RESET}\n")

    fields = {}

    # Required fields
    for field, label in schema["required"].items():
        if field == "stage" and entity_type == "encounter":
            stages = schema["stages"]
            print(f"  Stages: {', '.join(stages)}")
            value = prompt_field(label, required=True)
            while value not in stages:
                print(f"  {RED}Invalid.{RESET} Choose: {', '.join(stages)}")
                value = prompt_field(label, required=True)
            fields[field] = value
        else:
            fields[field] = prompt_field(label, required=True)

    # Optional fields
    for field, label in schema["optional"].items():
        if field == "text":
            value = prompt_field(label, multiline=True)
        elif field in LIST_FIELDS or field == "tags":
            value = prompt_list(label)
        else:
            value = prompt_field(label)
        if value:
            fields[field] = value

    # Encounter-specific: choices, variants, links
    if entity_type == "encounter":
        # Text variants
        fields["text_variants"] = {}
        if input(f"\n  Add text variants? {DIM}(y/n){RESET}: ").strip().lower() == "y":
            while True:
                key = input("    Key (e.g. 'word:ember', 'knowledge:x'): ").strip()
                if not key:
                    break
                text = prompt_field("    Text", multiline=True)
                if text:
                    fields["text_variants"][key] = text
                if input(f"    Another? {DIM}(y/n){RESET}: ").strip().lower() != "y":
                    break

        # Choices
        fields["choices"] = []
        if input(f"\n  Add choices? {DIM}(y/n){RESET}: ").strip().lower() == "y":
            while True:
                text = input("    Choice text: ").strip()
                if not text:
                    break
                next_id = input("    Next encounter ID (or empty): ").strip() or None
                cond_str = input("    Conditions JSON (or empty): ").strip()
                choice = {"text": text, "next": next_id}
                if cond_str:
                    try:
                        choice["conditions"] = json.loads(cond_str)
                    except json.JSONDecodeError:
                        print(f"    {RED}Invalid JSON, skipping conditions{RESET}")
                fields["choices"].append(choice)
                if input(f"    Another? {DIM}(y/n){RESET}: ").strip().lower() != "y":
                    break

        # Link entities
        for etype in ["character", "creature", "item", "location"]:
            available = list(db.data.get(etype, {}).keys())
            if available:
                ecolor = TYPE_COLORS[etype]
                print(f"\n  Available {etype}s: {ecolor}{', '.join(available)}{RESET}")
                ids_str = input(f"  Link {etype}s (comma-separated, Enter to skip): ").strip()
                if ids_str:
                    fields[etype + "s"] = [i.strip() for i in ids_str.split(",")
                                           if i.strip()]

    return fields


# --- CLI Parsing ---

def parse_cli_fields(args):
    """Parse ['--name', 'Asha', '--word', 'ember'] into dict."""
    fields = {}
    i = 0
    while i < len(args):
        if args[i].startswith("--"):
            key = args[i][2:]
            if i + 1 < len(args) and not args[i + 1].startswith("--"):
                value = args[i + 1]
                if key in LIST_FIELDS or key == "tags":
                    value = [v.strip() for v in value.split(",")]
                fields[key] = value
                i += 2
            else:
                fields[key] = True
                i += 1
        else:
            i += 1
    return fields


def print_help():
    """Print usage help."""
    print(f"""
{BOLD}Word Soul: Origins — World Authoring System{RESET}

{BOLD}Entity commands:{RESET}
  story.py character add              Create character (interactive)
  story.py character add --name X     Create character (inline)
  story.py character view <id>        View character details
  story.py character list             List all characters
  story.py character list --word X    List characters by word
  story.py character edit <id>        Edit character (interactive)
  story.py character edit <id> --X Y  Edit character field
  story.py character delete <id>      Delete character

  {DIM}Same for: creature, location, item, encounter{RESET}

{BOLD}Encounter-specific:{RESET}
  story.py encounter list childhood   List by stage
  story.py encounter edit <id> --add-choice    Add choice interactively
  story.py encounter edit <id> --add-variant   Add text variant
  story.py connect <from> <idx> <to>  Wire choice to encounter

{BOLD}Linking:{RESET}
  story.py link <type> <id> <enc_id>    Link entity ↔ encounter
  story.py unlink <type> <id> <enc_id>  Remove link

{BOLD}Search & Validate:{RESET}
  story.py search "query"               Full-text search
  story.py search --type character "X"   Search specific type
  story.py search --tag core             Search by tag
  story.py validate                      Check integrity
  story.py graph [stage]                 Encounter flow diagram
  story.py stats                         World overview
""")


# --- Main ---

def main():
    if len(sys.argv) < 2:
        print_help()
        return

    command = sys.argv[1]

    if command in ("help", "--help", "-h"):
        print_help()
        return

    db = WorldDB()

    # --- Entity commands ---
    if command in SCHEMAS:
        entity_type = command
        action = sys.argv[2] if len(sys.argv) > 2 else "list"
        rest = sys.argv[3:]

        if action == "add":
            if rest:
                fields = parse_cli_fields(rest)
            else:
                fields = interactive_add(entity_type, db)

            eid = db.add(entity_type, fields)

            # Auto-link entities listed in encounter
            if entity_type == "encounter":
                for etype in ["character", "creature", "item", "location"]:
                    for linked_id in fields.get(etype + "s", []):
                        db.link(etype, linked_id, eid)

            color = TYPE_COLORS[entity_type]
            print(f"\n  {GREEN}Created{RESET} {color}{entity_type}{RESET} "
                  f"'{BOLD}{eid}{RESET}'")

        elif action == "view":
            if not rest:
                print(f"  Usage: story.py {entity_type} view <id>")
                return
            entity = db.get(entity_type, rest[0])
            if entity:
                display_entity(entity_type, entity, db)
            else:
                # Fuzzy: try partial match
                matches = [eid for eid in db.data[entity_type]
                           if rest[0] in eid]
                if matches:
                    print(f"  '{rest[0]}' not found. Did you mean: "
                          f"{', '.join(matches)}?")
                else:
                    print(f"  {entity_type} '{rest[0]}' not found")

        elif action == "list":
            filters = {}
            args_rest = list(rest)

            # Encounter stage shortcut: `encounter list childhood`
            if (entity_type == "encounter" and args_rest
                    and not args_rest[0].startswith("--")):
                filters["stage"] = args_rest.pop(0)

            # Parse --field value filters
            i = 0
            while i < len(args_rest):
                if args_rest[i].startswith("--") and i + 1 < len(args_rest):
                    filters[args_rest[i][2:]] = args_rest[i + 1]
                    i += 2
                else:
                    i += 1

            entities = db.list_all(entity_type, **filters)
            display_list(entity_type, entities)

        elif action == "edit":
            if not rest:
                print(f"  Usage: story.py {entity_type} edit <id> [--field value]")
                return

            eid = rest[0]
            entity = db.get(entity_type, eid)
            if not entity:
                print(f"  {entity_type} '{eid}' not found")
                return

            field_args = rest[1:]

            # Encounter special flags
            if "--add-choice" in field_args and entity_type == "encounter":
                text = input("  Choice text: ").strip()
                if text:
                    next_id = input("  Next encounter ID (or empty): ").strip() or None
                    cond_str = input("  Conditions JSON (or empty): ").strip()
                    choice = {"text": text, "next": next_id}
                    if cond_str:
                        try:
                            choice["conditions"] = json.loads(cond_str)
                        except json.JSONDecodeError:
                            print(f"  {RED}Invalid JSON{RESET}")
                    entity["choices"].append(choice)
                    db.save("encounter")
                    print(f"  {GREEN}Added choice to '{eid}'{RESET}")
                return

            if "--add-variant" in field_args and entity_type == "encounter":
                key = input("  Variant key (e.g. 'word:ember'): ").strip()
                if key:
                    text = prompt_field("  Text", multiline=True)
                    if text:
                        entity.setdefault("text_variants", {})[key] = text
                        db.save("encounter")
                        print(f"  {GREEN}Added variant '{key}' to '{eid}'{RESET}")
                return

            # Inline edit
            if field_args:
                updates = parse_cli_fields(field_args)
                db.update(entity_type, eid, updates)
                print(f"  {GREEN}Updated{RESET} {entity_type} '{eid}'")
            else:
                # Interactive edit
                print(f"\n  Editing {entity_type} '{eid}' "
                      f"{DIM}(Enter to keep current){RESET}\n")
                updates = {}
                all_fields = {**SCHEMAS[entity_type]["required"],
                              **SCHEMAS[entity_type]["optional"]}
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
                    db.update(entity_type, eid, updates)
                    print(f"\n  {GREEN}Updated{RESET} {entity_type} '{eid}'")
                else:
                    print(f"\n  No changes.")

        elif action == "delete":
            if not rest:
                print(f"  Usage: story.py {entity_type} delete <id> [-f]")
                return
            eid = rest[0]
            force = "-f" in rest or "--force" in rest
            entity = db.get(entity_type, eid)
            if not entity:
                print(f"  {entity_type} '{eid}' not found")
                return

            name = entity.get("name") or entity.get("title", eid)
            apps = entity.get("appearances", [])

            if apps and not force:
                print(f"  {YELLOW}Warning:{RESET} '{name}' appears in "
                      f"{len(apps)} encounter(s): {', '.join(apps)}")
                if input("  Delete anyway? (y/n): ").strip().lower() != "y":
                    print("  Cancelled.")
                    return

            db.delete(entity_type, eid)
            print(f"  {GREEN}Deleted{RESET} {entity_type} '{eid}'")

        else:
            print(f"  Unknown action '{action}'. Try: add, view, list, edit, delete")

    # --- Link / Unlink ---
    elif command == "link":
        if len(sys.argv) < 5:
            print("  Usage: story.py link <type> <entity_id> <encounter_id>")
            return
        etype, eid, enc_id = sys.argv[2], sys.argv[3], sys.argv[4]
        if etype not in ("character", "creature", "item", "location"):
            print(f"  {RED}Invalid type '{etype}'.{RESET} "
                  f"Use: character, creature, item, location")
            return
        if db.link(etype, eid, enc_id):
            color = TYPE_COLORS[etype]
            print(f"  {GREEN}Linked{RESET} {color}{etype}/{eid}{RESET} "
                  f"↔ {MAGENTA}encounter/{enc_id}{RESET}")

    elif command == "unlink":
        if len(sys.argv) < 5:
            print("  Usage: story.py unlink <type> <entity_id> <encounter_id>")
            return
        etype, eid, enc_id = sys.argv[2], sys.argv[3], sys.argv[4]
        if db.unlink(etype, eid, enc_id):
            print(f"  {GREEN}Unlinked{RESET} {etype}/{eid} ↔ encounter/{enc_id}")
        else:
            print(f"  No link found.")

    # --- Connect (wire choice to encounter) ---
    elif command == "connect":
        if len(sys.argv) < 5:
            print("  Usage: story.py connect <from_enc> <choice_idx> <to_enc>")
            return
        from_id, idx_str, to_id = sys.argv[2], sys.argv[3], sys.argv[4]
        enc = db.get("encounter", from_id)
        if not enc:
            print(f"  Encounter '{from_id}' not found")
            return
        try:
            idx = int(idx_str)
        except ValueError:
            print(f"  '{idx_str}' is not a valid choice index")
            return
        if idx < 0 or idx >= len(enc.get("choices", [])):
            print(f"  Choice index {idx} out of range "
                  f"(0-{len(enc['choices']) - 1})")
            return
        enc["choices"][idx]["next"] = to_id
        db.save("encounter")
        choice_text = enc["choices"][idx].get("text", "?")
        print(f"  {GREEN}Connected{RESET} [{from_id}] choice [{idx}] "
              f"\"{choice_text}\" → {to_id}")

    # --- Search ---
    elif command == "search":
        query = ""
        etype = None
        tag = None
        i = 2
        while i < len(sys.argv):
            if sys.argv[i] == "--type" and i + 1 < len(sys.argv):
                etype = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == "--tag" and i + 1 < len(sys.argv):
                tag = sys.argv[i + 1]
                i += 2
            elif not sys.argv[i].startswith("--"):
                query = sys.argv[i]
                i += 1
            else:
                i += 1

        results = db.search(query, entity_type=etype, tag=tag)
        if not results:
            print(f"  No results for '{query or tag}'")
            return

        print(f"\n{BOLD}=== Search Results ({len(results)}) ==={RESET}\n")
        for et, eid, entity in results:
            color = TYPE_COLORS[et]
            name = entity.get("name") or entity.get("title", "?")
            tags_str = ", ".join(entity.get("tags", []))
            print(f"  {color}[{et}]{RESET} {eid}: {BOLD}{name}{RESET}")
            if tags_str:
                print(f"    {DIM}tags: {tags_str}{RESET}")
        print()

    # --- Validate ---
    elif command == "validate":
        issues = db.validate()
        if issues:
            print(f"\n{BOLD}{YELLOW}=== Validation: "
                  f"{len(issues)} issue(s) ==={RESET}\n")
            for issue in issues:
                print(issue)
        else:
            print(f"\n  {GREEN}All clear — no issues found.{RESET}\n")

    # --- Graph ---
    elif command == "graph":
        stage = sys.argv[2] if len(sys.argv) > 2 else None
        print(db.graph(stage=stage))

    # --- Stats ---
    elif command == "stats":
        print(db.stats())

    # --- Sync (rebuild bidirectional references) ---
    elif command == "sync":
        fixed = 0
        # For each encounter, ensure all listed entities have backrefs
        for enc_id, enc in db.data.get("encounter", {}).items():
            for etype in ["character", "creature", "item", "location"]:
                for eid in enc.get(etype + "s", []):
                    entity = db.data.get(etype, {}).get(eid)
                    if entity and enc_id not in entity.get("appearances", []):
                        entity.setdefault("appearances", []).append(enc_id)
                        fixed += 1
        # For each entity, ensure all appearances still exist
        for etype in SCHEMAS:
            if etype == "encounter":
                continue
            for eid, entity in db.data.get(etype, {}).items():
                to_remove = []
                for enc_id in entity.get("appearances", []):
                    enc = db.data["encounter"].get(enc_id)
                    if not enc:
                        to_remove.append(enc_id)
                        fixed += 1
                    elif eid not in enc.get(etype + "s", []):
                        to_remove.append(enc_id)
                        fixed += 1
                for enc_id in to_remove:
                    entity["appearances"].remove(enc_id)
            db.save(etype)
        db.save("encounter")
        print(f"  {GREEN}Synced.{RESET} Fixed {fixed} reference(s).")

    else:
        print(f"  Unknown command: {command}")
        print_help()


if __name__ == "__main__":
    main()
