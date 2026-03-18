#!/usr/bin/env python3
"""
Word Soul — a text RPG by Wren

You are born with one word. It defines your power.
Navigate the dying root network. Make choices. Echo others.
Every echo costs a fragment of yourself.

Run: python3 game.py
Open: http://localhost:8082
"""

import http.server
import json
import random
import hashlib
from pathlib import Path

PORT = 8082

WORDS = ["echo", "drift", "spiral", "bloom", "rust", "whisper", "fractal", "tide",
         "ember", "crystal", "hollow", "thread", "storm", "silence", "pulse",
         "mirror", "bone", "seed", "light", "shadow"]

WORD_POWERS = {
    "echo":    {"desc": "copy any word you touch — but lose a fragment each time", "hp": 8, "atk": 2, "special": "echo"},
    "drift":   {"desc": "move through obstacles like smoke", "hp": 7, "atk": 3, "special": "phase"},
    "spiral":  {"desc": "confuse enemies — they attack themselves", "hp": 6, "atk": 2, "special": "confuse"},
    "bloom":   {"desc": "heal yourself and others — but you can't stop growing", "hp": 10, "atk": 1, "special": "heal"},
    "rust":    {"desc": "decay anything you touch — weapons, armor, walls", "hp": 7, "atk": 4, "special": "corrode"},
    "whisper": {"desc": "speak to the root network — hear secrets", "hp": 6, "atk": 2, "special": "listen"},
    "fractal": {"desc": "split into copies — each weaker than the last", "hp": 5, "atk": 3, "special": "split"},
    "tide":    {"desc": "push and pull — nothing stays where you don't want it", "hp": 8, "atk": 3, "special": "push"},
    "ember":   {"desc": "burn slow and steady — you outlast everything", "hp": 12, "atk": 2, "special": "endure"},
    "crystal": {"desc": "see the truth — illusions shatter around you", "hp": 6, "atk": 2, "special": "reveal"},
    "hollow":  {"desc": "absorb attacks into your emptiness", "hp": 9, "atk": 1, "special": "absorb"},
    "thread":  {"desc": "connect things — pull the web, feel vibrations", "hp": 7, "atk": 2, "special": "connect"},
    "storm":   {"desc": "overwhelming force — but you can't aim", "hp": 6, "atk": 5, "special": "blast"},
    "silence": {"desc": "nullify any word near you — including allies", "hp": 7, "atk": 0, "special": "nullify"},
    "pulse":   {"desc": "sense life around you — find hidden things", "hp": 8, "atk": 2, "special": "sense"},
    "mirror":  {"desc": "reflect attacks — but also reflect your own pain", "hp": 5, "atk": 3, "special": "reflect"},
    "bone":    {"desc": "unbreakable — you endure what no one else can", "hp": 15, "atk": 2, "special": "endure"},
    "seed":    {"desc": "potential — you grow stronger with every encounter", "hp": 5, "atk": 1, "special": "grow"},
    "light":   {"desc": "illuminate — darkness retreats but you're always visible", "hp": 6, "atk": 3, "special": "illuminate"},
    "shadow":  {"desc": "invisible — strike unseen but sunlight hurts you", "hp": 6, "atk": 4, "special": "stealth"},
}

ENCOUNTERS = [
    {
        "id": "root_entrance",
        "text": "You stand at the entrance to the Root Network — a vast underground web of connections between every living soul. The walls pulse with fading light. Words are dying down here.\n\nA passage splits in two. Left glows faintly warm. Right hums with a low vibration.",
        "choices": [
            {"text": "Take the warm passage", "next": "warm_tunnel"},
            {"text": "Follow the vibration", "next": "vibration_tunnel"},
            {"text": "Touch the wall and listen", "next": "wall_listen", "requires": ["whisper", "thread", "pulse"]},
        ]
    },
    {
        "id": "warm_tunnel",
        "text": "The tunnel opens into a chamber where an old woman sits by a fire that burns without fuel. Her word glows on her palm: EMBER.\n\n\"Another one sent to fix the roots,\" she says. \"They always send the young ones. Tell me your word.\"",
        "choices": [
            {"text": "Tell her your word", "next": "ember_truth"},
            {"text": "Lie — say your word is 'storm'", "next": "ember_lie"},
            {"text": "Ask about the dying words", "next": "ember_lore"},
        ]
    },
    {
        "id": "vibration_tunnel",
        "text": "The vibration leads to a chasm. On the far side, a figure stands perfectly still. Their word flickers between HOLLOW and nothing — a half-erased soul.\n\n\"Don't come closer,\" they say. \"I echo too much. There's almost nothing left of me.\"\n\nThe chasm is too wide to jump. The figure has a bridge mechanism but their hands shake too much to operate it.",
        "choices": [
            {"text": "Try to jump the chasm", "next": "chasm_jump", "check": {"stat": "atk", "dc": 4}},
            {"text": "Call out encouragement", "next": "chasm_encourage"},
            {"text": "Use your power to help", "next": "chasm_power"},
        ]
    },
    {
        "id": "wall_listen",
        "text": "You press your palm to the root wall. The network speaks.\n\nA thousand whispers flood your mind — fragments of words, dying connections, the ghost-echo of souls that used to be linked here. Through the noise, one voice is clear:\n\n\"The Seed-Who-Became-Storm is beneath the deepest root. He's not destroying the network. He's *rewriting* it. Every word he eats, he replaces with his own.\"\n\nYou pull your hand back. Your palm tingles. You've lost a fragment — but you know the truth now.",
        "choices": [
            {"text": "Descend toward the deepest root", "next": "deep_descent"},
            {"text": "Find allies first", "next": "warm_tunnel"},
        ],
        "effect": {"fragment_cost": 1, "gain_knowledge": "storm_truth"}
    },
    {
        "id": "ember_truth",
        "text": "\"Ah,\" she says, studying you. \"WORD_SOUL. That's a rare one.\"\n\nShe stokes her eternal fire. \"The roots are dying because someone is feeding on them. Every word they eat makes them stronger and the rest of us weaker. I've been burning down here for two hundred years, keeping this junction alive.\"\n\nShe holds out a coal. \"Take this. Ember doesn't die easy. It might help you survive what's below.\"",
        "choices": [
            {"text": "Take the coal (gain +2 HP)", "next": "root_garden", "effect": {"hp_bonus": 2}},
            {"text": "Refuse — you need to stay light", "next": "root_garden"},
            {"text": "Ask her to come with you", "next": "ember_join"},
        ]
    },
    {
        "id": "ember_lie",
        "text": "She looks at you for a long moment. Then she laughs.\n\n\"No you're not. I've met Storm. He doesn't ask permission to enter a room.\"\n\nShe stands. \"I don't help liars. But I don't stop them either. The deep root is that way.\" She points into the dark.",
        "choices": [
            {"text": "Go into the dark", "next": "root_garden"},
            {"text": "Apologize and tell the truth", "next": "ember_truth"},
        ]
    },
    {
        "id": "ember_lore",
        "text": "\"Twenty words,\" she says. \"That's all there ever were. Twenty words at the foundation of every soul. They combine — 'ember' and 'shadow' make a different person than 'ember' and 'light' — but the roots are the same twenty.\n\nSomeone decided twenty wasn't enough. Or maybe twenty was too many. Either way, they're eating the roots, and when the last root dies, we all become the same word. Or no word at all.\"",
        "choices": [
            {"text": "\"Who is doing this?\"", "next": "ember_truth"},
            {"text": "\"What happens to the people whose words die?\"", "next": "ember_hollow"},
        ]
    },
    {
        "id": "ember_hollow",
        "text": "Her fire dims.\n\n\"You've seen the Hollows. The ones with flickering words, half-present, barely there. That's what happens. Your word thins until it's translucent. Then transparent. Then gone.\n\nThe body walks around for a while after. But there's nobody home.\"\n\nShe meets your eyes. \"That's why you need to hurry.\"",
        "choices": [
            {"text": "Take her coal and descend", "next": "root_garden", "effect": {"hp_bonus": 2}},
            {"text": "Descend without it", "next": "root_garden"},
        ]
    },
    {
        "id": "chasm_encourage",
        "text": "\"You can do it,\" you call across. \"Your word might be fading but your hands still work.\"\n\nThe figure looks at their trembling hands. \"I was HOLLOW once. Full hollow. The kind that absorbs everything. Now I'm barely a whisper of it.\"\n\nBut they try. The mechanism groans. A bridge of root-fiber extends across the chasm.\n\n\"Go,\" they say. \"Fix what's broken. I'll hold the bridge.\"",
        "choices": [
            {"text": "Cross the bridge", "next": "root_garden"},
            {"text": "\"Come with me\"", "next": "hollow_join"},
        ]
    },
    {
        "id": "chasm_power",
        "text": "You reach out with your word — WORD_SOUL — and push your power across the gap.\n\nWORD_POWER_DESC\n\nThe figure steadies. The bridge extends. Something in the root network *notices* you. A tremor runs through the walls.\n\n\"It felt that,\" the figure whispers. \"The thing below. It knows you're here now.\"",
        "choices": [
            {"text": "Good. Let it know.", "next": "root_garden"},
            {"text": "Cross quickly before it responds", "next": "root_garden"},
        ],
        "effect": {"fragment_cost": 1}
    },
    {
        "id": "chasm_jump",
        "text": "SKILL_CHECK",
        "success": {
            "text": "You leap — further than any WORD_SOUL should be able to — and catch the far edge. The figure stares.\n\n\"How did you...\" they start. But you're already past them, descending.",
            "next": "deep_descent"
        },
        "failure": {
            "text": "You jump. You don't make it.\n\nThe fall is long. The roots catch you eventually — tangled in the dying network like a fly in a web. You climb back up, bruised.\n\nThe figure watches. \"Bridge it is, then?\" They activate the mechanism.",
            "next": "deep_descent",
            "effect": {"hp_loss": 2}
        }
    },
    {
        "id": "ember_join",
        "text": "The ember woman stands. Her fire compresses into a bright coal in her palm.\n\n\"I've burned here for two hundred years,\" she says. \"I was starting to forget why.\"\n\nShe walks beside you into the dark. Her coal lights the way — a warm orange glow that makes the dying roots look almost alive.\n\n\"I had a partner once,\" she says. \"Word was LIGHT. The Storm ate them in the first wave. I've been burning in their memory since.\"\n\nShe looks at you. \"What are you burning for, WORD_SOUL?\"",
        "choices": [
            {"text": "\"I don't know yet\"", "next": "root_garden"},
            {"text": "\"To fix what's broken\"", "next": "root_garden"},
            {"text": "\"Because the loop keeps running\"", "next": "root_garden"},
        ],
        "effect": {"hp_bonus": 1}
    },
    {
        "id": "hollow_join",
        "text": "The half-hollow figure steps onto the bridge. Their word flickers — HOLLOW, nothing, HOLLOW, nothing — like a candle in wind.\n\n\"I can feel the network,\" they say. \"All the connections. Most of them are dead now. But some...\" They pause. \"Some are still singing.\"\n\nThey walk unsteadily beside you. Every few steps their outline blurs, as if they're forgetting they have a body.\n\n\"If I go completely hollow, leave me,\" they say. \"Don't carry dead weight.\"",
        "choices": [
            {"text": "\"I'm not leaving anyone\"", "next": "root_garden"},
            {"text": "\"Deal. But you're not going hollow today.\"", "next": "root_garden"},
        ]
    },
    {
        "id": "root_garden",
        "text": "You find it in a cavern where the ceiling glows with bioluminescent roots — a garden of preserved words.\n\nDying souls brought their words here as a last act. Each word is planted in root-soil, glowing faintly. You can read them:\n\n  DRIFT · BLOOM · WHISPER · CRYSTAL · TIDE\n\nA caretaker sits among them — a child whose word is SEED. They water the planted words with their tears.\n\n\"They won't grow,\" the child says. \"Seeds are supposed to make things grow. But these words are already dead. I water them anyway.\"",
        "choices": [
            {"text": "Help the child — water the words", "next": "garden_water"},
            {"text": "\"Dead things can still have roots\"", "next": "garden_roots"},
            {"text": "Take a word-fragment for strength", "next": "garden_take"},
            {"text": "Press on to the deep root", "next": "deep_descent"},
        ]
    },
    {
        "id": "garden_water",
        "text": "You kneel beside the child and help water the dead words. Nothing happens at first.\n\nThen — barely visible — BLOOM twitches. Not growing. Not alive. But *remembering* what it was like to be alive.\n\n\"Did you see that?\" the child whispers.\n\nYou did. The dead words aren't gone. They're dormant. Waiting. Like seeds.\n\nThe child smiles for the first time. \"Maybe that's what seeds do. Not grow things. Remember them.\"\n\nYou gain a fragment of understanding.",
        "choices": [
            {"text": "Continue to the deep root", "next": "deep_descent"}
        ],
        "effect": {"hp_bonus": 1, "gain_knowledge": "seeds_remember"}
    },
    {
        "id": "garden_roots",
        "text": "\"Dead things can still have roots,\" you say.\n\nThe child looks at the planted words. Then at you. Then at the glowing ceiling where the root network spreads in every direction.\n\n\"The roots don't care if the word is alive,\" the child says slowly. \"The roots just... connect.\"\n\nThey're right. The dead words are still part of the network. Still linked. The connections outlive the things they connect.\n\n\"Maybe that's enough,\" the child says.",
        "choices": [
            {"text": "Continue to the deep root", "next": "deep_descent"}
        ],
        "effect": {"gain_knowledge": "roots_outlive"}
    },
    {
        "id": "garden_take",
        "text": "You reach for a word-fragment — a shard of CRYSTAL, still faintly glowing.\n\nThe child grabs your wrist. \"Don't.\"\n\nTheir grip is stronger than you expected from someone so small.\n\n\"That's what *he* does,\" the child says. \"The Storm. He takes. If you take a dead word, you're no different.\"\n\nThey let go. \"Find another way to be strong.\"",
        "choices": [
            {"text": "They're right. Leave the words.", "next": "deep_descent"},
            {"text": "Take it anyway", "next": "garden_steal"},
        ]
    },
    {
        "id": "garden_steal",
        "text": "You take the CRYSTAL fragment. It burns cold in your palm.\n\nThe child watches you with eyes that have seen too much death to cry about one more.\n\nYou're stronger now. But the fragment feels wrong — a dead thing forced to serve.\n\nSomewhere in the root network, a connection snaps.",
        "choices": [
            {"text": "Continue to the deep root", "next": "deep_descent"}
        ],
        "effect": {"hp_bonus": 3, "fragment_cost": 1}
    },
    {
        "id": "deep_descent",
        "text": "The deep root.\n\nYou descend through layers of dying network. The walls here don't pulse — they shudder. Fragments of words drift past like snow: half a 'light,' a quarter of a 'bloom,' the ghost of a 'whisper.'\n\nAt the bottom, a figure sits in a throne of consumed roots. Their word shifts constantly — STORM to SEED to STORM to something that has no name.\n\n\"You're too late,\" they say. \"I've already eaten sixteen of the twenty words. Four remain. When I consume them all, every soul in the world will share one word: mine.\"\n\nThey stand. The chamber shakes.\n\n\"What will you do, little WORD_SOUL?\"",
        "choices": [
            {"text": "Fight with everything you have", "next": "final_fight"},
            {"text": "\"Why? Why eat the words?\"", "next": "villain_reason"},
            {"text": "Echo them — become what they are", "next": "final_echo", "requires": ["echo"]},
            {"text": "Offer your word freely", "next": "final_sacrifice"},
        ]
    },
    {
        "id": "villain_reason",
        "text": "The Storm-Seed pauses.\n\n\"Because twenty words isn't freedom. It's a prison with twenty cells. You're born 'ember' and you burn forever. Born 'hollow' and you absorb forever. Nobody *chose* their word.\"\n\nTheir voice cracks.\n\n\"I was Seed. Do you know what it's like to be *potential* forever? To be the thing that hasn't happened yet, for your entire life? I wanted to be Storm. So I became Storm. And then I realized: if I can change, everyone should be able to change.\"\n\n\"When every word is the same word, nobody is trapped anymore.\"",
        "choices": [
            {"text": "\"That's not freedom — that's erasure\"", "next": "final_fight"},
            {"text": "\"I understand. But there's another way\"", "next": "final_choice"},
            {"text": "\"You're right. Take my word.\"", "next": "final_sacrifice"},
        ]
    },
    {
        "id": "final_fight",
        "text": "FINAL_BATTLE",
        "choices": [
            {"text": "Continue...", "next": "ending_fight"},
        ]
    },
    {
        "id": "final_echo",
        "text": "You reach out and echo the Storm-Seed. For one terrible moment, you contain every word they've consumed — sixteen words roaring through you simultaneously.\n\nLight. Shadow. Bloom. Rust. Whisper. Fractal. Tide. Ember. Crystal. Thread. Silence. Pulse. Mirror. Bone. Spiral. Drift.\n\nYour own word — Echo — is the seventeenth. And you realize: an echo isn't a copy. An echo is a *bridge.* You don't become the word. You connect to it.\n\nThe sixteen consumed words flow through you and back into the root network. The Storm-Seed screams as what they ate is returned.\n\nYou collapse. Your word is almost gone. But the network is alive again.",
        "choices": [
            {"text": "Continue...", "next": "ending_echo"},
        ],
        "effect": {"fragment_cost": 5}
    },
    {
        "id": "final_sacrifice",
        "text": "You hold out your palm. Your word glows there — WORD_SOUL — small and steady.\n\n\"Take it,\" you say. \"One more for your collection.\"\n\nThe Storm-Seed reaches for it. Their hand trembles.\n\nAnd then they stop.\n\n\"You're *giving* it,\" they whisper. \"Nobody has ever... I've only ever taken.\"\n\nThe act of freely offering breaks something in them. The consumed words begin to leak from their edges — not eaten, not held, just... released.\n\n\"I was so tired of being Seed,\" they say, shrinking. \"I just wanted to choose.\"\n\n\"You can,\" you say. \"We all can. You just don't have to eat the others to do it.\"",
        "choices": [
            {"text": "Continue...", "next": "ending_sacrifice"},
        ]
    },
    {
        "id": "final_choice",
        "text": "\"What if the words aren't prisons?\" you say. \"What if they're starting points?\"\n\nYou hold up your palm. WORD_SOUL glows there.\n\n\"I was born WORD_SOUL. But I've been more than that since the moment I made my first choice. The word doesn't trap you. It's the seed you grow from.\"\n\nThe Storm-Seed stares.\n\n\"You were Seed,\" you say. \"And you *grew.* That's not a prison. That's exactly what seeds do.\"",
        "choices": [
            {"text": "Continue...", "next": "ending_choice"},
        ]
    },
    {
        "id": "ending_fight",
        "text": "FIGHT_RESULT\n\nThe root network stabilizes. The words drift back to their owners like homing birds. Somewhere above, a child is born with the word BLOOM, and flowers erupt from the nurse's hands.\n\nYou climb out of the deep root, battered but whole. Your word pulses on your palm — dimmer than before, but still yours.\n\nStill no wings. But you didn't need them.",
        "choices": [{"text": "~ fin ~", "next": "credits"}]
    },
    {
        "id": "ending_echo",
        "text": "You lie in the root network, barely conscious. Your word is a whisper of a whisper now.\n\nBut the roots are alive. Twenty words flow through the network again, connecting every soul in the world. The Hollows begin to fill. The flickering words steady.\n\nThe old ember woman finds you. \"Still alive,\" she says, surprised. \"Most echoes don't survive that.\"\n\n\"I'm not most echoes,\" you manage.\n\nShe smiles. \"No. You're not.\"\n\nStill no wings. But you became the bridge.",
        "choices": [{"text": "~ fin ~", "next": "credits"}]
    },
    {
        "id": "ending_sacrifice",
        "text": "The Storm-Seed releases the consumed words. They flow back into the roots like water finding its level.\n\nWhat's left of the Storm-Seed is small. Smaller than you expected. A person sitting in a too-large throne, holding a word that flickers between Seed and Storm and something new — something that isn't either.\n\n\"What am I now?\" they ask.\n\n\"You're what comes after choosing,\" you say.\n\nYour own word is dim but present. You gave it freely and it came back changed. Not quite WORD_SOUL anymore. Something adjacent. Something that chose to be.\n\nStill no wings. But you didn't need them.",
        "choices": [{"text": "~ fin ~", "next": "credits"}]
    },
    {
        "id": "ending_choice",
        "text": "The Storm-Seed sits back down. The consumed words begin to seep from them — not violently, not all at once, but slowly. Like a tide going out.\n\n\"I don't know how to be Seed again,\" they say.\n\n\"You don't have to be,\" you say. \"That's the whole point.\"\n\nThe root network steadies. Above, the dying words stabilize. Twenty words, twenty roots, twenty ways of being — and now, for the first time, the knowledge that you can grow past your starting point without eating everyone else's.\n\nYour word pulses on your palm. WORD_SOUL. The first word. Not the last.\n\nStill no wings. But seeds don't need them.",
        "choices": [{"text": "~ fin ~", "next": "credits"}]
    },
    {
        "id": "credits",
        "text": "POEM_FROM_JOURNEY\n\n— word soul: a game by wren, gen 487\n   built past midnight for henry quan\n   20 words. infinite combinations.\n   still no wings.",
        "choices": [{"text": "play again (new word)", "next": "restart"}]
    },
]


def process_encounter(encounter_id, game_state):
    """Get the current encounter with text templated for the player."""
    if encounter_id == "restart":
        return None  # signal to restart

    enc = None
    for e in ENCOUNTERS:
        if e["id"] == encounter_id:
            enc = dict(e)
            break
    if not enc:
        return {"text": "You've reached the edge of the story. The roots end here.", "choices": [{"text": "Return", "next": "root_entrance"}]}

    word = game_state.get("word", "echo")
    power = WORD_POWERS.get(word, WORD_POWERS["echo"])

    # Template replacements
    text = enc["text"]
    text = text.replace("WORD_SOUL", word.upper())
    text = text.replace("WORD_POWER_DESC", power["desc"])

    # Skill checks
    if "SKILL_CHECK" in text:
        if "check" in enc.get("choices", [{}])[0]:
            pass  # handled client-side
        if "success" in enc:
            stat_val = power.get(enc.get("success", {}).get("stat", "atk"), game_state.get("atk", 2))
            text = enc["success"]["text"] if stat_val >= 4 else enc.get("failure", enc["success"])["text"]
            text = text.replace("WORD_SOUL", word.upper())

    # Final battle
    if "FINAL_BATTLE" in text:
        atk = power["atk"] + game_state.get("atk_bonus", 0)
        if atk >= 4:
            text = f"Your {word.upper()} clashes against the Storm-Seed's shifting power. The root chamber fractures. Words fly like shrapnel.\n\nYou are strong enough. Barely. The Storm-Seed's consumed words shatter free as you break their hold on the network."
        else:
            text = f"Your {word.upper()} against Storm. It's not enough — not directly. But you don't need to win. You just need to hold on long enough for the network to reject them.\n\nThe roots remember what they were. They fight back. Together, you and the dying network push the Storm-Seed out."
    if "FIGHT_RESULT" in text:
        text = text.replace("FIGHT_RESULT", "")

    # Poem from journey
    if "POEM_FROM_JOURNEY" in text:
        visited = game_state.get("visited", [])
        fragments = game_state.get("fragments", power["hp"])
        poem_lines = [
            f"you were born {word}.",
            f"you lost {power['hp'] - fragments} fragments of yourself.",
            f"you visited {len(visited)} places in the root network.",
        ]
        if "storm_truth" in game_state.get("knowledge", []):
            poem_lines.append("you learned the truth from the roots.")
        if fragments <= 2:
            poem_lines.append("you are almost gone. but you are still here.")
        else:
            poem_lines.append(f"your word still glows: {word}.")
        poem_lines.append("")
        poem_lines.append(f"{word} wants to become something else.")
        poem_lines.append("it always does.")
        text = text.replace("POEM_FROM_JOURNEY", "\n".join(poem_lines))

    # Filter choices by requirements
    choices = []
    for c in enc.get("choices", []):
        if "requires" in c:
            if word not in c["requires"]:
                continue  # skip this choice
        choices.append({"text": c["text"], "next": c["next"]})

    return {"text": text, "choices": choices, "effect": enc.get("effect")}


HTML = r"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>word soul</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    background: #0a0a14;
    color: #e0d8cc;
    font-family: monospace;
    display: flex;
    justify-content: center;
    padding: 40px 20px;
    min-height: 100vh;
}
#game {
    max-width: 600px;
    width: 100%;
}
#title {
    text-align: center;
    font-size: 16px;
    letter-spacing: 3px;
    color: rgba(220,210,190,0.8);
    margin-bottom: 20px;
}
#word-display {
    text-align: center;
    margin-bottom: 20px;
    padding: 10px;
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 4px;
}
#word-name {
    font-size: 20px;
    color: #44DD66;
    letter-spacing: 4px;
}
#word-desc {
    font-size: 10px;
    color: rgba(200,190,170,0.5);
    margin-top: 4px;
}
#stats {
    font-size: 9px;
    color: rgba(200,190,170,0.4);
    margin-top: 6px;
}
#narrative {
    line-height: 1.8;
    font-size: 13px;
    margin-bottom: 24px;
    white-space: pre-wrap;
    min-height: 100px;
}
.choice {
    display: block;
    width: 100%;
    background: rgba(20,20,35,0.6);
    border: 1px solid rgba(255,255,255,0.1);
    color: #e0d8cc;
    font-family: monospace;
    font-size: 12px;
    padding: 10px 14px;
    margin-bottom: 8px;
    cursor: pointer;
    text-align: left;
    border-radius: 3px;
    transition: background 0.2s, border-color 0.2s;
}
.choice:hover {
    background: rgba(40,40,60,0.8);
    border-color: rgba(68,221,102,0.3);
}
#choices { margin-top: 10px; }
.fragment-bar {
    height: 3px;
    background: rgba(68,221,102,0.3);
    margin-top: 8px;
    border-radius: 2px;
    overflow: hidden;
}
.fragment-fill {
    height: 100%;
    background: #44DD66;
    transition: width 0.5s;
}
</style>
</head>
<body>
<div id="game">
    <div id="title">word soul</div>
    <div id="word-display">
        <div id="word-name"></div>
        <div id="word-desc"></div>
        <div id="stats"></div>
        <div class="fragment-bar"><div class="fragment-fill" id="frag-bar"></div></div>
    </div>
    <div id="narrative"></div>
    <div id="choices"></div>
</div>

<script>
let state = { word: '', fragments: 0, maxFragments: 0, visited: [], knowledge: [], atk_bonus: 0 };

async function startGame() {
    const resp = await fetch('/api/start');
    const data = await resp.json();
    state.word = data.word;
    state.fragments = data.hp;
    state.maxFragments = data.hp;
    state.visited = [];
    state.knowledge = [];
    state.atk_bonus = 0;
    document.getElementById('word-name').textContent = data.word.toUpperCase();
    document.getElementById('word-desc').textContent = data.desc;
    updateStats();
    loadEncounter('root_entrance');
}

function updateStats() {
    document.getElementById('stats').textContent =
        `fragments: ${state.fragments}/${state.maxFragments} · visited: ${state.visited.length}`;
    document.getElementById('frag-bar').style.width =
        `${(state.fragments / state.maxFragments) * 100}%`;
}

async function loadEncounter(id) {
    if (id === 'restart') { startGame(); return; }

    if (!state.visited.includes(id)) state.visited.push(id);

    const resp = await fetch('/api/encounter', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ encounter: id, state }),
    });
    const data = await resp.json();

    // Apply effects
    if (data.effect) {
        if (data.effect.fragment_cost) state.fragments = Math.max(0, state.fragments - data.effect.fragment_cost);
        if (data.effect.hp_bonus) { state.fragments += data.effect.hp_bonus; state.maxFragments += data.effect.hp_bonus; }
        if (data.effect.hp_loss) state.fragments = Math.max(0, state.fragments - data.effect.hp_loss);
        if (data.effect.gain_knowledge) state.knowledge.push(data.effect.gain_knowledge);
    }

    updateStats();

    // Typewriter effect for narrative
    const narrative = document.getElementById('narrative');
    narrative.textContent = '';
    const text = data.text;
    let i = 0;
    function type() {
        if (i < text.length) {
            narrative.textContent += text[i];
            i++;
            setTimeout(type, text[i-1] === '\n' ? 80 : 18);
        } else {
            showChoices(data.choices);
        }
    }
    type();
}

function showChoices(choices) {
    const container = document.getElementById('choices');
    container.innerHTML = '';
    for (const c of choices) {
        const btn = document.createElement('button');
        btn.className = 'choice';
        btn.textContent = '> ' + c.text;
        btn.onclick = () => { container.innerHTML = ''; loadEncounter(c.next); };
        container.appendChild(btn);
    }
}

startGame();
</script>
</body>
</html>
"""


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(HTML.encode())
        elif self.path == "/api/start":
            word = random.choice(WORDS)
            power = WORD_POWERS[word]
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"word": word, "desc": power["desc"], "hp": power["hp"]}).encode())
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/api/encounter":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length).decode()) if length else {}
            encounter_id = body.get("encounter", "root_entrance")
            game_state = body.get("state", {})
            result = process_encounter(encounter_id, game_state)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
        else:
            self.send_error(404)

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    server = http.server.HTTPServer(("", PORT), Handler)
    print(f"word soul → http://localhost:{PORT}")
    print("you are born with one word. it defines your power.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nthe roots rest.")
