# VESTIGE — Combat System

*Slay the Spire's strategy. Fear and Hunger's consequences. Your character's identity expressed as a deck.*

---

## Philosophy

1. **Combat is punctuation, not the sentence.** Fights are crises within a life, not the reason the life exists.
2. **Any fight can maim or kill you.** Knowing when to RUN is a core skill.
3. **Your deck IS your character.** Look at someone's cards and you know their story — what they trained, what they lost, who they are.
4. **Risk vs reward in every decision.** Every turn presents a meaningful tradeoff.
5. **Show enough information for strategy.** Enemy intent is partially visible — enough to plan, not enough to solve.
6. **Imperfect solutions create depth.** Every card should solve part of a problem while introducing another.

---

## Core Mechanics

### Turn Structure

Each turn:
1. Draw cards from your deck (base: 5 cards)
2. See partial enemy intent (what they're LIKELY to do)
3. Spend energy to play cards (base: 3 energy per turn)
4. Unplayed cards go to discard
5. Enemy acts
6. Repeat until combat ends (victory, death, or escape)

When your draw pile is empty, shuffle your discard pile into a new draw pile. This means wound cards keep cycling back.

### Energy

Base: 3 energy per turn. Cards cost 0-3 energy.

Energy sources:
- Base allocation (3)
- Some cards generate energy
- Some attunement abilities modify energy
- Worship cards can grant bonus energy (volatile)

Energy does NOT carry over between turns. Use it or lose it.

### The Deck

Your deck is assembled from everything you are:

| Source | How Cards Enter | Permanent? |
|---|---|---|
| **Archetype base** | Start of life — Strike, Block, basic cards | Yes (can be upgraded) |
| **Attunement** | Awakening + training — Power Strike, Flame Bolt, Shadow Step, etc. | Yes (grow with proficiency) |
| **Equipment** | Picking up / equipping gear — each weapon/armor adds specific cards | While equipped |
| **Proficiency upgrades** | Training milestones — Slash → Skilled Slash → Whirlwind | Replaces previous version |
| **Trait cards** | From personality — Berserker Rage, Patient Counter, etc. | Yes (inherent to character) |
| **Vow cards** | Taking a vow — Protector's Strike (+3 vs threats to innocents) | Yes (permanent, conditional) |
| **Wound cards** | Injuries — Phantom Pain, Weakened Grip, One-Eyed | Yes (permanent, NEGATIVE) |
| **Worship cards** | Character gains worship — Dread Aura, Sheltering Light | While worshipped (volatile) |
| **Divine cards** | God spends influence — Fate's Whisper, Divine Nudge | One-use per intervention |

### Deck Size Tension

More cards = more options but less consistency. The carry-weight problem as probability:

- A lean deck (12-15 cards) draws key cards frequently. Predictable, reliable.
- A loaded deck (25-30 cards) has more tools but you might draw Phantom Pain when you need Power Strike.
- Equipment adds cards. Injuries add cards. Every addition dilutes the deck.
- **The strategic question every run:** keep the deck lean, or accumulate power at the cost of consistency?

This is the Slay the Spire principle: sometimes REMOVING a card is more powerful than adding one.

---

## Body Part Targeting (Fear and Hunger System)

### How It Works

Every combatant (player AND enemies) has targetable body parts:

**Humanoid layout:**
- **Head** — destroying it is usually fatal. Hardest to hit. Critical hits.
- **Torso** — main HP pool. Must be destroyed to kill (unless head is destroyed first).
- **Right Arm** — destroying it removes all cards that require that arm (weapon attacks, shield blocks).
- **Left Arm** — same. Losing both arms = almost no combat capability.
- **Legs** — destroying them prevents escape. Reduces dodge. Character must drag themselves.

**The targeting choice each turn:** When you play an attack card, you choose which body part to target. This creates strategic depth:

- **Go for the weapon arm** to disable their strongest attack
- **Go for the legs** to prevent them from escaping (or to enable YOUR escape)
- **Go for the head** for a quick kill (but it's harder to hit)
- **Go for the torso** as the safe, reliable damage option

### Damage and Destruction

Each body part has its own HP pool:
- Head: ~30% of total HP (but harder to hit — accuracy penalty)
- Torso: ~100% of total HP (the main health bar)
- Each arm: ~40% of total HP
- Legs: ~50% of total HP (combined — destroying one leg impairs, both cripples)

When a body part reaches 0 HP:
- **Head destroyed:** Instant death (for enemies). For the player: instant run end.
- **Torso destroyed:** Death.
- **Arm destroyed:** All cards requiring that arm are REMOVED from the deck permanently. For the rest of this run AND all future combat in this life.
- **Leg destroyed:** Movement cards removed. Escape becomes nearly impossible. Dodge cards severely penalized.

### Lasting Damage (The Fear and Hunger Principle)

**Injuries are PERMANENT for the life.** Losing an arm doesn't heal. The wound card enters your deck and stays.

| Injury | Immediate Effect | Permanent Card Added | Long-term Consequence |
|---|---|---|---|
| Arm severed | All arm-dependent cards lost | **Phantom Limb** (costs 1 energy, does nothing) | Can't use two-handed weapons, shields on that side |
| Leg severed | Movement/dodge cards lost | **Dragging** (enemy gets +1 attack against you) | Can't run from fights. Travel takes longer. |
| Eye lost | Accuracy reduced | **Blind Spot** (enemies occasionally get free hits) | Sense attunement partially compensates over time |
| Deep wound | HP max reduced | **Old Wound** (occasionally costs 1 energy for nothing when it flares) | Never fully heals. A reminder of the fight. |
| Broken bones | Temporary stat reduction | **Mending** (negative card for a period, eventually fades to **Ache**) | Healed but never quite right |

**Why this matters:** Every combat encounter is a genuine risk. Even winning costs something if you take damage. The player must constantly ask: **"Is this fight worth what it might cost me?"**

Running away is ALWAYS an option. But running has costs too — you might lose equipment, reputation, or the thing you were fighting for.

---

## Attunement in Combat

Each attunement grants a different combat identity:

### Body (the warrior)

**Card identity:** High damage, high defense, straightforward. Body cards hit hard and take hits. Low complexity, high reliability.

**Signature mechanic:** **Fortify** — spend energy to add temporary armor that persists until your next turn. Stacks with multiple Fortify cards.

**Example cards:**
| Card | Cost | Effect |
|---|---|---|
| Power Strike | 1 | Deal 8 damage to target body part |
| Iron Skin | 1 | Gain 7 armor |
| Fortify | 2 | Gain 12 armor. Retain half next turn. |
| Reckless Blow | 2 | Deal 15 damage. Take 5 damage to torso. |
| Endure | 0 | Gain 3 armor. Draw 1 card. |
| (Focused) War Cry | 1 | All attacks deal +3 this turn |
| (Masterful) Execution | 3 | Deal 25 damage to one body part. If it destroys the part, gain 2 energy. |

### World (the mage)

**Card identity:** High damage potential, area effects, environmental manipulation. Powerful but fragile — no natural armor generation.

**Signature mechanic:** **Channel** — some cards require charging (play the Channel card one turn, the effect triggers next turn). Risk: if you're interrupted before the effect triggers, the energy is wasted.

**Example cards:**
| Card | Cost | Effect |
|---|---|---|
| Flame Bolt | 1 | Deal 6 damage. Apply 2 Burn (damage over time). |
| Stone Ward | 2 | Gain 10 armor. Create 1 Rubble (can be launched for 5 damage). |
| Channel: Tempest | 2 | Next turn: deal 5 damage to ALL enemy body parts. |
| Shatter | 1 | Deal 4 damage. If target body part is below 50% HP, deal 8 instead. |
| Gust | 0 | Push enemy back. Prevents melee attacks for 1 turn. |
| (Focused) Elemental Fusion | 2 | Combine two element effects on the field for a unique result. |
| (Masterful) Cataclysm | 3 | Channel 2 turns. Then: deal 30 damage split across all body parts. |

### Void (the assassin)

**Card identity:** Low base damage, massive first-strike, evasion. The Void deck is about avoiding damage entirely and ending fights in one decisive moment.

**Signature mechanic:** **Stealth stacks.** Cards generate Stealth. At max Stealth, your next attack deals triple damage. Taking any damage resets Stealth to zero.

**Example cards:**
| Card | Cost | Effect |
|---|---|---|
| Unseen Blade | 1 | Deal 4 damage (+2 per Stealth stack). |
| Fade | 1 | Gain 3 Stealth. Gain 4 evasion (chance to dodge attacks). |
| Shadow Step | 0 | Gain 1 Stealth. Draw 1 card. |
| Expose Weakness | 1 | Target body part takes +4 damage from all sources this turn. |
| Vanish | 2 | Reset combat. Full Stealth. Enemy loses track of you. Can't be attacked for 1 turn. |
| (Focused) Death Mark | 1 | Mark one body part. All Stealth bonus damage applies only to that part, but at double. |
| (Masterful) Annihilate | All energy | Spend ALL energy and ALL Stealth. Deal damage equal to (energy × Stealth × 5) to one body part. The assassination. |

### Sense (the strategist)

**Card identity:** Information, prediction, counters. Low personal damage. High tactical value. Best paired with allies or adjacent attunement cards.

**Signature mechanic:** **Insight.** Sense cards generate Insight tokens. Spend Insight to: reveal hidden enemy intent, predict next turn's draw, or enable counter-cards.

**Example cards:**
| Card | Cost | Effect |
|---|---|---|
| Read Intent | 0 | Gain 2 Insight. Reveal one hidden enemy action. |
| Predict | 1 | Gain 3 Insight. Look at your next 3 cards. Reorder them. |
| Exploit Opening | 1 | Spend 3 Insight. Deal 10 damage to any body part (the precise strike). |
| Forewarn | 0 | Spend 2 Insight. Gain armor equal to incoming damage this turn. |
| Disrupt | 1 | Spend 4 Insight. Cancel enemy's current action. |
| (Focused) Battle Flow | 2 | Gain Insight equal to the number of enemy body parts remaining. |
| (Masterful) Prescience | 0 | Spend 6 Insight. Take an extra turn. |

### Bond (the healer/support)

**Card identity:** Healing, reinforcement, energy transfer. Low damage. High sustain. In solo combat, Bond is the weakest offensively — but in any encounter with allies or objectives, they're invaluable.

**Signature mechanic:** **Mend.** Bond cards can repair damaged body parts (restoring HP to arms, legs, torso). Cannot bring back a destroyed part, but can prevent destruction.

**Example cards:**
| Card | Cost | Effect |
|---|---|---|
| Mending Touch | 1 | Restore 8 HP to one of YOUR body parts. |
| Reinforce | 1 | Target equipment card is immune to destruction for 2 turns. |
| Share Strength | 1 | Transfer up to 5 of your armor to an ally. |
| Pain Transfer | 0 | Take 3 damage. An ally heals 5. |
| Binding | 1 | Reduce target enemy body part's attack by 3 for 2 turns. |
| (Focused) Reconstruct | 3 | Restore a body part to 50% HP. Can only be used once per combat. |
| (Masterful) Sacrifice | All HP - 1 | Fully heal one ally. You drop to 1 HP. |

---

## Enemy Design

### Enemies Use the Same System

Enemies have:
- Body parts (targetable, destroyable)
- Attunements (they use the same mortal power system)
- Intent (partially visible to the player)

**Why same system matters:** When you fight a Body-attuned bandit, you understand their power because you understand the system. You know they'll hit hard and take hits. A World-attuned mage enemy is dangerous at range — you know to close distance. A Void enemy might vanish — you know to Sense for them.

### Enemy Intent Display

**Partial visibility.** Unlike Slay the Spire's full intent, Vestige shows:

- **Clear intent:** Physical attacks (you can see them winding up)
- **Hazy intent:** Magical effects (you know something is coming, not exactly what)
- **Hidden intent:** Stealth actions, tricks, traps (no warning without Sense)

**Sense attunement reveals more.** A Sense-attuned character sees all intents clearly. Others see the base level. Invest in Sense (even as a secondary) to gain tactical advantage.

### Worship-Powered Enemies

Kings, cult leaders, high priests — enemies with Devotion have worship cards in THEIR deck too:

- A feared king has **Dread Aura** (you skip a turn from terror)
- A beloved war-hero has **Rally** (their allies get extra actions)
- A fanatical cult leader has **Zealot's Fury** (damage increases as their followers watch)

**How to counter:** Undermine their worship. If you can turn their followers against them (through story choices BEFORE combat), their worship cards weaken or vanish. The political game feeds into the combat game.

---

## The Escape System

**Running is always an option. Running always costs something.**

To escape:
1. Play an Escape card, or spend 2 energy to attempt flee
2. Success based on: legs intact? Enemy faster? Terrain?
3. If successful: combat ends. You're alive. BUT:
   - You might lose equipment (dropped in the chaos)
   - The enemy is still there (they'll be in the world, potentially stronger)
   - NPCs might judge you for fleeing
   - If you were protecting something/someone, they're now unprotected

**Leg destruction prevents escape entirely.** This is why targeting legs is both a tactical tool and a terrifying enemy action. If they go for your legs, they're saying: "You don't get to leave."

---

## Combat Consequences

### After Each Fight

- **Won cleanly:** Minimal consequences. Possible loot. Reputation gain.
- **Won with injuries:** Wound cards added permanently. Body part damage may be lasting.
- **Escaped:** Alive but diminished. The threat persists.
- **Lost (death):** Run over. God-perspective returns.
- **Lost (captured):** Worse than death in some cases. Slavery, imprisonment, torture. A whole different story branch.

### The Attrition Curve

Over a life, combat damage ACCUMULATES:
- Fight 1: Clean win. Small scratch. No wound cards.
- Fight 5: You've taken real damage. One wound card in the deck. Arm at 60%.
- Fight 10: Multiple wound cards. Missing an eye. Deck is cluttered with Phantom Pain and Old Wound.
- Fight 15: A veteran's deck — powerful skill cards buried among accumulated wounds. Every draw is a gamble between strength and suffering.

**This is the Fear and Hunger principle:** combat doesn't exist in isolation. Every fight is part of a sequence, and the sequence grinds you down.

---

## Card Upgrades and Proficiency

### How Cards Upgrade

Training or experience upgrades cards along proficiency tracks:

```
Slash (base) → Skilled Slash (+3 damage) → Precise Slash (choose body part at +accuracy)
                                         → Whirlwind (hits all body parts for reduced damage)
```

At each upgrade point, the player CHOOSES the branch. The choice reflects the character's development:
- Precise Slash = the disciplined swordsman
- Whirlwind = the aggressive fighter

### Proficiency Tracks

| Track | What Improves | Cards Affected |
|---|---|---|
| Swordsmanship | Blade-based attacks | Slash, Parry, Riposte |
| Archery | Ranged attacks | Aimed Shot, Quick Shot, Volley |
| Unarmed | Body-only attacks | Punch, Grapple, Throw |
| Elemental (per element) | Specific element spells | Fire/water/earth/air cards |
| Stealth | Void-based skills | Fade, Shadow Step, Unseen Blade |
| Medicine | Healing cards | Mending Touch, Reconstruct, Diagnose |
| Defense | Armor/block cards | Block, Iron Skin, Fortify |

Proficiency increases through USE and TRAINING:
- Using sword cards in combat gradually increases Swordsmanship
- Finding a mentor accelerates it
- A training montage event can push a proficiency to the next tier

---

## Worship Cards in Combat (The Wild Layer)

Worship cards are powerful but volatile. They appear in your deck ONLY while you're actively worshipped:

| Card | Worship Type | Cost | Effect | Disappears If... |
|---|---|---|---|---|
| Dread Aura | Fear | 1 | Enemy skips next action | You show weakness |
| Sheltering Light | Love | 1 | Block ALL damage this turn | You betray your people |
| Radiance | Awe | 0 | All attacks deal +5 this turn | You fail publicly |
| Zealot's Fury | Fanaticism | 2 | Deal 20 damage. Take 5. | Doubt spreads among followers |
| Divine Mandate | Faith | 1 | Choose: heal 10 OR deal 10 OR gain 10 armor | Followers lose faith |

**The volatility:** Worship cards can disappear MID-COMBAT if the conditions change. Fighting in front of your followers and losing badly? The awe fades. The Radiance card vanishes from your hand. You're just a person now.

---

## Balance Principles

1. **No dominant strategy.** Different enemies should challenge different builds.
2. **Every card should have at least one scenario where it's the best choice.**
3. **Running is always viable.** A build that can't escape is doomed.
4. **Wound cards create natural difficulty scaling.** The longer you survive, the harder combat becomes.
5. **The Slay the Spire rule: "at least one half of a synergy pair must work fine independently."**
6. **Single player = allow power spikes.** Let the player feel overpowered sometimes. It feels great.
7. **Data-driven iteration.** Metrics will tell us what's too strong. Playtesting tells us what FEELS right.
