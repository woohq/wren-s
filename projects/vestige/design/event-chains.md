# VESTIGE — Event Chain System

*Every event is a seed. Every choice grows something.*

---

## The Principle

No event exists in isolation. Every outcome spawns consequences — new events, new characters, new artifacts, new factions, new threads. By era 3, the majority of available events aren't generic encounters — they're consequences of the player's choices. The world becomes YOURS through accumulated causation.

**No event should ever repeat across a full playthrough.** Events mutate. They spawn children. The children are new events authored for that specific consequence chain.

---

## The Schema

Every choice in every event can spawn future content:

```json
{
  "text": "Stand your ground and fight.",
  "effects": {
    "trait_gain": "blooded"
  },
  "spawns": {
    "events": [
      {
        "id": "the_mans_brother",
        "delay": "years",
        "description": "The man you hit has a brother. The brother heard what happened. He's been asking about you."
      }
    ],
    "characters": [
      {
        "id": "broken_arm_bandit",
        "description": "The man whose arm you broke with a forge hammer. He survived. He remembers."
      }
    ],
    "artifacts": [],
    "factions": [],
    "threats": [],
    "world_changes": [
      "Road bandits avoid Thornwall's trade routes for a season — word spreads about the kid with the hammer."
    ]
  }
}
```

## Spawn Types

Every choice can spawn any combination of:

**Events** — new encounters that become available in future runs/eras
- `delay`: when it can fire (immediate, years, next_era, generations)
- The spawned event is a full event with its own text, choices, and spawns
- It carries a `born_from` field tracing its origin

**Characters** — new NPCs that enter the world
- The orphaned child who becomes a warrior
- The merchant who remembers your kindness
- The soldier who survived a battle you started

**Artifacts** — objects created by consequences
- The sword forged from a betrayed alliance's broken weapons
- The journal of a scholar who died researching something you discovered
- The crown of a kingdom your choices created

**Factions** — groups born from consequences
- Refugees who band together because you didn't save their village
- A cult that forms around an artifact you created
- A resistance movement against a ruler you installed

**Cultures** — (rare, major cascades only) entire ways of life born from your choices
- The mixed-culture children of a trade route you opened
- The isolationist splinter group that rejected your reforms
- The nomadic survivors of a nation you destroyed

**Threats** — dangers born from consequences
- The revenge-seeker empowered by a dark god
- The plague that spread because you chose quarantine over cure
- The power vacuum you created by removing a tyrant

**World Changes** — descriptive text about how the world shifted
- Not a specific entity — just a narrative note about what changed
- "The road is safer now" or "Thornwall's reputation grows"

---

## Chain Depth

Event chains can go deep:

```
Root Event (Era 1): The Road Between — bandits on the road
  └─ Choice: fight → spawns:
      └─ Era 1 late: "Broken Arm" — the bandit you hit recognizes you in town
          └─ Choice: confront → spawns:
              └─ Era 2: "The Bandit's Son" — his child, now grown, finds you
                  └─ Choice: mercy → spawns:
                      └─ Era 3: "The Reformed" — the son became a peacekeeper
                                because of your mercy. He names his patrol
                                after you.
                  └─ Choice: fight → spawns:
                      └─ Era 2 late: "Blood Feud" — the cycle continues.
                                A new generation of enemies.
```

Every choice at every level spawns the next link. The chain can run for the entire game — a single moment on a road when you were fourteen echoing through centuries.

---

## Authoring Workflow

When writing an event:

1. Write the scene and choices as before
2. For EACH choice, ask: "What grows from this?"
3. Write spawn stubs — not full events yet, just IDs and descriptions
4. The spawned events get authored later as full events with their own spawns
5. Use `world.py chain <event_id>` to visualize the chain from any root

The spawned events don't all need to be written immediately. Stubs are enough to plan — the full text comes when we get there. But the STRUCTURE of what spawns should be designed upfront so the chains feel intentional.

---

## The Volume Shift

This changes the content math:

**Old model:** 200 standalone events in a pool. Each life draws ~12. After ~17 lives, you've seen everything.

**New model:** 50 root events, each with 3-4 choices, each choice spawning 1-3 consequence events, each of THOSE spawning further... The tree grows exponentially. After 50 root events:

- 50 × 3 choices = 150 outcomes
- 150 × 2 average spawns = 300 consequence events
- 300 × 2 = 600 second-generation events
- Total: ~1,100 unique events from 50 roots

Most players will see maybe 10% of this tree. Every playthrough walks a unique path through the branches. Two players will NEVER have the same event history.

---

## Implementation

The world state tracks:
- `active_threads`: list of thread IDs currently in play
- `spent_events`: events that have already fired (never fire again)
- `pending_spawns`: events that have been spawned but haven't fired yet
- `spawn_conditions`: what needs to be true for a pending spawn to fire

The event filter adds a new check:
- Is this event in `pending_spawns`? → eligible
- Is this event in `spent_events`? → never eligible
- Is this a root event that hasn't been spent? → eligible
- Chain events ONLY fire if they're in pending_spawns

This means consequence events are INVISIBLE until spawned. The player can't encounter "The Bandit's Son" unless they fought the bandit AND the broken-arm follow-up fired. The world only shows you what YOUR choices created.
