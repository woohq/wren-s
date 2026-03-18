# VESTIGE — Design Document Index

*"I am the vestige of something. Each life shows me more of the shape."*

## Overview

**Vestige** is a text-based roguelike RPG where you play a forgotten god who doesn't remember what they are. Each run, you embody a mortal — living their life from birth to death, fighting with a card-based combat system, and shaping a persistent world through your choices. When they die, the world carries forward. Your next vessel inherits the consequences.

Over dozens of runs spanning centuries, two things emerge: the world's history (written by your accumulated choices) and your own divine nature (crystallized from what you keep choosing to care about).

**Inspirations:** Fear and Hunger (brutal combat, knowledge-as-progression), Slay the Spire (card combat, deckbuilding), Roadwarden (authored text quality, meaningful choices), Hunter x Hunter (power system reflects personality), Dwarf Fortress (simulated history), Caves of Qud (authored bones, generated flesh).

**Delivery:** Prototype in Python/web → final build in Godot → Steam release.

---

## Design Documents

| Document | What It Covers |
|----------|---------------|
| [core-loop.md](core-loop.md) | The minute-to-minute player experience, from god-awakening through multiple runs |
| [power-system.md](power-system.md) | Mortal attunements (one source, five expressions) + divine worship power |
| [combat.md](combat.md) | Card system, deck building, dismemberment, wounds, balance principles |
| [world.md](world.md) | Cultures, factions, eras, threats, world persistence across runs |
| [characters.md](characters.md) | Traits (5 sources), relationships, archetypes, content architecture |
| [god.md](god.md) | God interface, meta-progression, domain crystallization, vessel selection |
| [god-hierarchy.md](god-hierarchy.md) | The 5-tier divine hierarchy (Reputation → Concept God), worship as neutral force |
| [narrative.md](narrative.md) | Writing principles, prose style, anti-ad-libs rules, scene authoring |
| [technical.md](technical.md) | Tech stack, authoring tools, data schemas, delivery pipeline |
| [event-chains.md](event-chains.md) | How choices spawn consequence events, characters, artifacts, factions — the branching tree |
| [era-transitions.md](era-transitions.md) | How the First Era ends based on player choices, what grows from the cracks |
| [moral-complexity.md](moral-complexity.md) | Moral design principles — no right answers, every path has genuine cost |
| [pacing-and-failure.md](pacing-and-failure.md) | Default timeline, failure as motivation, vessel strategy, life length variance |
| [endgame-states.md](endgame-states.md) | Late-game scenarios, domain crystallization outcomes, the final summary |
| [thread-map.md](thread-map.md) | Main threads, sub-threads, boundary principle, how stories flow through world states |

---

## The Three Pillars

Everything in Vestige serves one of three pillars:

### 1. Every Life Feels Real
Roadwarden-quality prose. Characters with traits that create dilemmas. Relationships built through specific shared moments. No ad-libs — every scene hand-written for its specific context. 30-90 minutes of dense, authored experience per life.

### 2. Every Death Matters
The world doesn't reset. Your character's deeds become legacy — legends, artifacts, changed politics, descendants. Threats escalate if ignored. Unintended consequences cascade across eras. Two players with the same starting world will have completely different histories by run 10.

### 3. You Discover Who You Are
The god doesn't know what they are. Your domain emerges from accumulated choices. A player who protects becomes a god of mercy. A player who conquers becomes a god of dominion. The game's deepest question: after centuries of watching this world, what kind of god did you become?

---

## System Interaction Map

```
GOD LAYER (between runs)
  │
  ├─ Vessel Selection (traits, family, place visible)
  ├─ World Summary (consequences, time passage, new state)
  ├─ Divine Progression (worship, influence, knowledge)
  └─ Domain Crystallization (emerging from accumulated choices)
  │
  ▼
MORTAL LAYER (during runs)
  │
  ├─ Life Events ←── filtered by: archetype, traits, culture, era, world state, pending_spawns
  │     ├─ choices gated by: traits, power, relationships, knowledge
  │     └─ choices spawn: consequence events, characters, artifacts, factions, threats
  │
  ├─ Relationships ←── generated from: archetype, traits, place
  │     └─ deepen through: shared events, callbacks to specific moments
  │
  ├─ Mortal Power ←── attunement from: personality/traits
  │     ├─ foundation: sense, draw, circulate, release, still
  │     ├─ specialization: body, world, void, sense, bond
  │     └─ vows: voluntary restrictions → multiplied power
  │
  ├─ Card Combat ←── deck from: attunement + equipment + traits + skills + wounds + worship
  │     ├─ mortal deck: systematic, balanced, reliable
  │     └─ worship deck: volatile, powerful, belief-dependent
  │
  ├─ Worship Power ←── from: directed belief of NPCs toward character
  │     └─ character of worship (fear/love/awe) shapes power
  │
  └─ World Impact ←── character actions → faction changes, threat escalation,
        │               cultural shifts, artifacts created, NPCs affected
        │
        ▼
      DEATH → consequences applied → world simulates forward → GOD LAYER
```

---

## The Two Power Systems

**Mortal Power (the world's energy):**
One force, five attunements, personality determines expression. A swordsman and a mage use the same energy differently. Progression through stages (Awakened → Transcendent). Vows multiply power at the cost of restriction.

**Worship Power (directed belief):**
Completely separate system. Comes from other people's consciousness directed at you. The CHARACTER of worship (fear/love/awe/habit) determines the CHARACTER of power. Kings, cult leaders, heroes, and gods all draw from this. Most people don't understand the mechanism.

These systems are orthogonal — a mortal can have one, the other, both, or neither. A master swordsman with no worshippers has only mortal power. A beloved king who never trained has only worship power. A legendary warrior-king has both. The player-god has worship power (rebuilding) and grants divine influence to vessels.

---

## Content Architecture

**Authored (hand-written with love):**
- Root life events (~50 for MVP, each 200-500 words) that spawn consequence chains through the event chain system (see [event-chains.md](event-chains.md)). 50 roots × branching choices = ~1,100 unique events across a full playthrough.
- Relationship scenes (per type × event beat)
- World events (faction conflicts, threats, discoveries)
- Archetype milestones (unique to each life path)
- Character voices, cultural flavor, artifact backstories, god personalities
- Card descriptions that feel like people, not stat blocks

**Procedural (the assembly):**
- Which authored pieces combine for THIS character in THIS place at THIS time
- Names generated from culture-appropriate pools
- NPC trait/motivation combinations
- Event ordering within a life (drawing from both root events and spawned consequence events)
- World simulation between runs

**The Rule:** No generated text. The system selects authored text based on context. The combination is unique. The pieces are crafted.

---

## Development Phases

| Phase | What | Output |
|-------|------|--------|
| **0: Design** | Lock down all systems in these documents | This document set |
| **1: Tools** | Build `world` CLI authoring system | Tool for fast content creation |
| **2: Seed** | Author first era (one region, 3-4 places, starting gods, first archetypes/traits, 50-100 events) | Playable content set |
| **3: Prototype** | Core loop playable in web (one life, basic combat) | Testable game |
| **4: Persistence** | Between-runs simulation, cascade consequences, god progression | Multi-run experience |
| **5: Scale** | More content, more eras, card balance, art integration | Full game |
| **6: Ship** | Port to Godot, Steam build, polish | Release |

---

## Design Principles

1. **Characters first.** Everyone has reasons. Empathy for those reasons is what makes someone care.
2. **Author the atoms, assemble the molecules.** Every piece hand-written. Every combination procedural.
3. **Knowledge is the real progression.** The player's brain is the god's memory.
4. **Limitations are more interesting than powers.** What you CAN'T do creates better stories than what you can.
5. **The world doesn't wait for you.** Threats escalate. Factions advance. Time passes.
6. **Every path is the canonical path.** No B-routes. Every life feels like THE story.
7. **Permanent consequences.** Burnt bridges. Wound cards. Dead NPCs. The world carries scars.
8. **Show information, create strategy.** Players should make informed decisions, not guess.
9. **Incompleteness is the theme.** The world is too large for one god. Choose what to care about.
10. **The breaks are where the light gets in.** Imperfection, injury, loss — these are where the story lives.
