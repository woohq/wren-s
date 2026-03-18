# VESTIGE — Technical Architecture

*Build tools that make writing easy. The content pipeline is the game's foundation.*

---

## Tech Stack

### Phase 1-4: Prototype (Python/Web)

**Why Python:**
- Fast iteration. Wren can build and test in heartbeats.
- Proven pattern — Origins was built this way (52 encounters, working game)
- Content is JSON — engine-agnostic
- HTML/JS frontend for visual prototype

**Stack:**
- Python 3.12+ backend (stdlib HTTP server + game engine)
- JSON data files (authored content)
- HTML/JS/CSS frontend (text display, card combat UI, god interface)
- No external dependencies for the game itself

### Phase 5-6: Final Build (Godot)

**Why Godot:**
- Free, open source
- Excellent 2D support (text-heavy games, card combat, pixel art)
- Exports to Steam (Windows, Mac, Linux)
- GDScript is Python-like (smooth transition)
- Active community, good documentation

**The bridge:** All content remains in JSON. Only the rendering/UI layer changes. Zero content rewrite when porting.

---

## Data Architecture

### Everything Is an Entity

Every piece of authored content follows the same pattern:

```json
{
  "id": "burning_sermon",
  "type": "event",
  "name": "The Burning Sermon",
  "tags": ["life_event", "adult", "religious", "dramatic"],
  "filters": { ... },
  "text": { ... },
  "choices": [ ... ],
  "effects": { ... },
  "refs": { ... }
}
```

### Data Directory Structure

```
projects/vestige/
  data/
    archetypes/        — life-path templates
    traits/            — personality attributes
    cultures/          — beliefs, naming, values
    places/            — regions, settlements, dungeons
    factions/          — organizations with goals
    gods/              — deities with domains
    artifacts/         — items with backstories
    creatures/         — enemies with body parts
    eras/              — time periods
    threats/           — escalating dangers
    relationships/     — bond templates
    events/
      childhood/       — early life events
      adolescence/     — coming of age events
      adulthood/       — main life events
      world/           — world-scale events
      combat/          — fight encounters
    cards/
      body/            — Body attunement cards
      world/           — World attunement cards
      void/            — Void attunement cards
      sense/           — Sense attunement cards
      bond/            — Bond attunement cards
      equipment/       — weapon/armor cards
      wound/           — injury cards
      worship/         — worship power cards
      divine/          — god intervention cards
    scenes/
      relationships/   — relationship-type scenes (the anti-ad-libs content)
      awakenings/      — attunement awakening scenes
      deaths/          — death scenes
      god/             — god interface text
  design/              — these documents
  research.md          — compiled research
  engine/              — game engine code (when built)
  tools/               — authoring CLI
```

### Entity Schemas (key types)

**Event:**
```json
{
  "id": "burning_sermon",
  "type": "event",
  "name": "The Burning Sermon",
  "tags": ["life_event", "adult", "religious", "dramatic", "fire"],
  "filters": {
    "age": ["adult", "elder"],
    "archetype": ["priest_apprentice", "noble_bastard", null],
    "trait_requires_any": ["faithful", "doubting", "curious"],
    "trait_excludes": ["godless"],
    "faction_present": ["church_of_flame"],
    "era_tech_min": "pre-industrial",
    "threat_active": null
  },
  "text": "The cathedral is full. [Authored prose, 200-500 words]",
  "choices": [
    {
      "text": "Stand with the priest. Truth matters more than comfort.",
      "requires": {"trait": "brave"},
      "effects": {
        "faction_rep": {"church_of_flame": -20},
        "trait_gain": "heretic",
        "card_gain": "righteous_defiance",
        "relationship_change": {"priest": +15}
      },
      "consequence_text": "The congregation splits...",
      "spawns": {
        "events": [],
        "characters": [],
        "artifacts": [],
        "factions": [],
        "cultures": [],
        "threats": [],
        "world_changes": []
      }
    }
  ],
  "born_from": null,
  "refs": {
    "places": ["cathedral_of_flame"],
    "factions": ["church_of_flame"],
    "gods": ["the_flame"]
  }
}
```

**Trait:**
```json
{
  "id": "brave",
  "type": "trait",
  "name": "Brave",
  "source": "inherent",
  "rarity": "common",
  "description": "Faces things head-on. Cannot look away from a challenge.",
  "mechanical": {
    "attunement_affinity": "body",
    "card_modifier": {"attack_cards": "+1 damage"},
    "gates_choices": ["charge_recklessly", "stand_ground", "face_the_threat"],
    "excludes_choices": ["hide_and_wait"],
    "dilemma": "You CAN charge in. Which means you sometimes WILL when you shouldn't."
  },
  "tags": ["personality", "physical", "combat_relevant"]
}
```

**Card:**
```json
{
  "id": "power_strike",
  "type": "card",
  "name": "Power Strike",
  "attunement": "body",
  "stage_required": "practiced",
  "energy_cost": 1,
  "effects": {
    "damage": 8,
    "target": "chosen_body_part"
  },
  "upgrade_path": {
    "heavy_blow": {"damage": 12, "self_damage": 3},
    "precise_strike": {"damage": 8, "accuracy": "+2", "crit_chance": 0.15}
  },
  "flavor_text": "You don't think about the technique anymore. Your body remembers.",
  "tags": ["attack", "body", "melee", "basic"]
}
```

**Culture:**
```json
{
  "id": "northern_clans",
  "type": "culture",
  "name": "Northern Clans",
  "era": "era_1",
  "values": ["honor", "craft", "ancestors", "endurance"],
  "naming_pool": "nordic",
  "archetype_tendencies": ["blacksmith_child", "warrior_child"],
  "trait_tendencies": ["honor_bound", "mountain_hardy", "stubborn"],
  "worship_tendency": ["ancestor_spirits", "forge_god"],
  "technology": "iron_age",
  "contact_history": [],
  "descendants": ["old_north", "bridge_folk", "exiles"]
}
```

---

## The Authoring Tool: `world` CLI

### Philosophy

The tool should make WRITING easy. Not game-design. The author thinks about prose, characters, and moments. The tool handles connections, validation, and assembly.

### Commands

```bash
# Create content
world event add              # interactive prompts
world trait add --name brave --source inherent --rarity common
world culture add --name "Northern Clans" --values honor,craft
world place add --name Thornwall --region north --culture northern_clans
world god add --name "The Flame" --domain fire,purification
world card add --name "Power Strike" --attunement body --cost 1
world scene add --type relationship --beat betrayal --archetype blacksmith

# Explore content
world search "fire"                    # full-text search
world search --type event --tag adult  # filtered search
world graph god the_flame             # all connections from The Flame
world list events --archetype warrior  # events available to warriors
world list traits --source inherent    # all inherent traits

# Validate and analyze
world validate                         # check all references, missing content
world coverage                         # how many events per archetype/age/context?
world gaps                             # where do we need more content?
world simulate blacksmith thornwall era_1  # generate a sample life, show what events would fire

# Manage connections
world link god the_flame place cathedral_of_flame "worshipped_at"
world link faction church_of_flame god the_flame "serves"
world sync                             # rebuild all bidirectional references
```

### The Simulate Command

The most important authoring tool. Run:
```bash
world simulate blacksmith_child thornwall era_1 --traits brave,stubborn
```

Output: a sample life assembled from the current content. Shows which events would fire, which relationships would form, which cards would enter the deck. **This lets us test content coverage without playing the game.**

If the simulation produces a life that feels thin or repetitive, we know exactly where to add content.

---

## The Assembly Engine

### How a Life Is Generated

1. **Vessel selected** → archetype, place, culture, era, inherent traits known
2. **Environmental traits generated** from culture + place
3. **Family generated** → NPCs from culture naming pool + trait pool
4. **Childhood event pool assembled:**
   - Filter all events where: age=childhood AND (archetype matches OR archetype=null) AND trait requirements met AND culture/era/place match
   - Draw 3-5 events from filtered pool
5. **Relationships generated** from archetype tendencies + trait compatibility
6. **Adolescence events** drawn (filtered by traits + relationships + world state)
7. **Awakening scene** selected based on attunement affinity
8. **Adulthood events** drawn (largest pool, most variety)
9. **World events** injected based on era + threat stages
10. **Death** determined by accumulated wounds, age, story circumstances

### The Filter Cascade

Every event has filters. The engine matches current context against filters:

```python
def matches(event, context):
    f = event['filters']

    # Age must match
    if context.age not in f.get('age', [context.age]):
        return False

    # Archetype: null means universal
    if f.get('archetype') and context.archetype not in f['archetype']:
        return False

    # Traits: requires_any means at least one must match
    if f.get('trait_requires_any'):
        if not any(t in context.traits for t in f['trait_requires_any']):
            return False

    # Traits: excludes means none can match
    if f.get('trait_excludes'):
        if any(t in context.traits for t in f['trait_excludes']):
            return False

    # Faction presence
    if f.get('faction_present'):
        if not any(fa in context.local_factions for fa in f['faction_present']):
            return False

    # Spawn eligibility: chain events only fire if spawned
    if event.get('born_from') and event['id'] not in context.pending_spawns:
        return False

    return True
```

The beauty: **events don't know about specific characters.** They know about CONTEXTS. An event written for "any brave adult in a region with a religious faction" will fire for hundreds of different character configurations. The authored quality is in the prose. The reusability is in the filters.

---

## World State Persistence

### Save Format

The world state is a JSON document that grows across runs:

```json
{
  "current_era": "era_3",
  "years_elapsed": 247,
  "runs_completed": 8,
  "god": {
    "worship": 340,
    "influence": 45,
    "knowledge_flags": ["scourge_source", "flame_doctrine", "northern_schism"],
    "domain_axes": {
      "mercy_justice": 0.7,
      "knowledge_action": -0.3,
      "connection_independence": 0.5,
      "creation_destruction": 0.4,
      "order_freedom": -0.1
    },
    "past_lives": [ ... ]
  },
  "factions": { ... },
  "threats": { ... },
  "cultures": { ... },
  "npcs": [ ... ],
  "artifacts": [ ... ],
  "legacy": { ... },
  "active_threads": [ ... ],
  "spent_events": [ ... ],
  "pending_spawns": [ ... ]
}
```

### Between-Runs Simulation

After each death, a simulation step runs:

```python
def advance_world(state, years):
    # 1. Apply direct consequences from the life
    apply_life_consequences(state)

    # 2. Advance faction agendas
    for faction in state.factions:
        faction.pursue_agenda(state, years)

    # 3. Escalate/resolve threats
    for threat in state.threats:
        threat.advance(state, years)

    # 4. Age NPCs
    for npc in state.npcs:
        npc.age(years)  # some die, some have children

    # 5. Cultural evolution
    for culture in state.cultures:
        culture.evolve(state, years)  # contact, schism, merging

    # 6. Technology
    check_discoveries(state, years)

    # 7. Generate new state
    generate_new_npcs(state)
    generate_new_tensions(state)

    # 8. Record legacy
    record_legacy(state)
```

For MVP, this simulation is **authored consequence chains, not emergent simulation.** Each faction has scripted "if X then Y" advancement rules. Each threat has scripted stage progressions. This is easier to control narratively and ensures quality.

Later phases can add more emergent behavior.

---

## Performance Considerations

- **Text-heavy games are lightweight.** No 3D rendering, no physics. A potato can run this.
- **JSON loading** — all data loaded at startup, held in memory. Expected total data size: <10MB even with full content.
- **Save files** — world state grows across runs but stays manageable (<1MB).
- **The bottleneck is content, not computation.** The game is limited by how much we write, not how fast it runs.
