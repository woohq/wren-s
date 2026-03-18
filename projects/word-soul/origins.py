#!/usr/bin/env python3
"""
Word Soul: Origins — the full game
by Wren

A life-simulator text RPG where your word emerges from your choices.
Reads content from data/*.json (authored with story.py).

Run: python3 origins.py
Open: http://localhost:8083
"""

import http.server
import json
import random
import math
import uuid
import urllib.parse
from pathlib import Path

PORT = 8083
DATA_DIR = Path(__file__).parent / "data"

# --- Data Loading ---

def load_json(filename):
    filepath = DATA_DIR / filename
    if filepath.exists():
        text = filepath.read_text().strip()
        return json.loads(text) if text else {}
    return {}

ENCOUNTERS = load_json("encounters.json")
CHARACTERS = load_json("characters.json")
WORDS_DATA = load_json("words.json")
LOCATIONS = load_json("locations.json")

AFFINITY_AXES = ["force", "structure", "connection", "decay", "perception"]

# --- Stage Flow ---

STAGE_ORDER = [
    "childhood", "adolescence", "emergence",
    "upper_roots", "living_network", "dying_roots", "deep_root", "endgame",
]

STAGE_CONFIG = {
    "childhood": {
        "pool": ["word_games", "elders_lesson", "root_gate_curiosity",
                 "night_ground_shook", "the_butterfly_game"],
        "pre": ["first_light"],
        "post": ["seris_emergence", "mothers_warning"],
        "draw": 3,
    },
    "adolescence": {
        "pool": ["seri_drifts", "the_wrong_word", "proto_flicker",
                 "the_stranger", "elders_secret", "the_fight"],
        "pre": ["late_bloomer"],
        "post": ["seris_question", "the_tremor"],
        "draw": 4,
    },
    "emergence": {
        "pool": [],
        "pre": ["the_descent_begins", "emergence_moment", "post_emergence"],
        "post": [],
        "draw": 0,
    },
    "upper_roots": {
        "pool": ["first_word_use", "tangle_guardian", "echo_moths_flock",
                 "seri_phases_ahead"],
        "pre": ["the_ember_woman"],
        "post": ["asha_offers_lantern", "path_deeper"],
        "draw": 2,
    },
    "living_network": {
        "pool": ["echo_chamber_visit", "hollow_drifters_encounter",
                 "seri_fading", "rens_warning"],
        "pre": ["the_living_bridge", "meeting_ren"],
        "post": ["bridge_breaks", "path_to_dying"],
        "draw": 2,
    },
    "dying_roots": {
        "pool": ["ash_garden_path", "rust_veins_shortcut",
                 "seris_crisis"],
        "pre": ["finding_luma"],
        "post": ["lumas_gift", "the_descent_to_deep"],
        "draw": 2,
    },
    "deep_root": {
        "pool": ["mirror_pool_visit", "storm_sentries_guard"],
        "pre": [],
        "post": ["meeting_kael"],
        "draw": 1,
    },
    "endgame": {
        "pool": [],
        "pre": ["the_final_choice"],
        "post": [],
        "draw": 0,
    },
}


def build_stage_queue(stage):
    """Build the encounter queue for a stage."""
    config = STAGE_CONFIG.get(stage)
    if not config:
        return []
    pool = list(config["pool"])
    random.shuffle(pool)
    drawn = pool[:config["draw"]]
    return config["pre"] + drawn + config["post"]


# --- Affinity & Word Calculation ---

def cosine_similarity(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a == 0 or mag_b == 0:
        return 0
    return dot / (mag_a * mag_b)


def determine_word(affinity):
    """Find the word whose vector is most similar to the player's affinity."""
    words = WORDS_DATA.get("words", {})
    best_word = "echo"
    best_sim = -1
    for word, data in words.items():
        sim = cosine_similarity(affinity, data["vector"])
        if sim > best_sim:
            best_sim = sim
            best_word = word
    return best_word


def apply_affinity(state, affinity_dict):
    """Apply affinity changes from a choice."""
    for i, axis in enumerate(AFFINITY_AXES):
        state["affinity"][i] += affinity_dict.get(axis, 0)


# --- Text Resolution ---

def resolve_text(encounter, state):
    """Resolve text with variables and word-specific variants."""
    variants = encounter.get("text_variants", {})
    word = state.get("word")

    # Check for word-specific variant
    variant_key = f"word:{word}" if word else None
    if variant_key and variant_key in variants:
        text = variants[variant_key]
    else:
        text = encounter.get("text", "")

    # Substitute variables
    if word:
        text = text.replace("PLAYER_WORD", word.upper())
    else:
        text = text.replace("PLAYER_WORD", "???")
    text = text.replace("MOTHER_WORD", state.get("mother_word", "THREAD").upper())

    # Replay awareness — add echoes from past lives
    past = state.get("past_lives", [])
    if past and encounter.get("id") == "first_light":
        prev_words = [p["word"] for p in past]
        text += ("\n\nSomething stirs. A feeling you can't name — "
                 "like you've stood in this village before, "
                 "held this hand before, felt this hum before. "
                 f"You've been {', '.join(w.upper() for w in prev_words)}. "
                 "You don't remember. But your palm does.")
    elif past and encounter.get("id") == "emergence_moment":
        n = len(past)
        text += (f"\n\nThis isn't the first time. Something deep in the network "
                 f"remembers — {n} {'soul' if n == 1 else 'souls'} who walked this path before you. "
                 "Their words echo in the roots beneath your feet. "
                 "You are not the first. You might be the last.")
    elif past and encounter.get("id") == "the_final_choice":
        endings_seen = [p["ending"] for p in past]
        text += ("\n\nThe network trembles with recognition. "
                 "It has seen this moment before. "
                 "It remembers how it ended: "
                 + ", ".join(e.replace("_", " ") for e in endings_seen) + ". "
                 "This time could be different. Or the same. "
                 "The choice is still yours.")

    return text


def resolve_choices(encounter, state):
    """Return choices, filtering by conditions."""
    choices = encounter.get("choices", [])
    resolved = []
    for i, choice in enumerate(choices):
        cond = choice.get("conditions")
        if cond:
            # Word-gated choice
            if "word" in cond and state.get("word") != cond["word"]:
                continue
            # Knowledge-gated
            if "knowledge" in cond and cond["knowledge"] not in state.get("knowledge", []):
                continue
            # Item-gated
            if "item" in cond and cond["item"] not in state.get("inventory", []):
                continue
        resolved.append({"index": i, "text": choice["text"]})
    return resolved


# --- Game State ---

SESSIONS = {}
# Global memory across playthroughs — tracks what words the player has been
PAST_LIVES = []  # list of {word, ending, playthrough_num}


def new_game():
    """Create a new game session."""
    session_id = str(uuid.uuid4())[:8]
    mother_words = ["ember", "thread", "bloom", "crystal", "pulse",
                    "whisper", "tide", "light"]
    playthrough = len(PAST_LIVES) + 1
    state = {
        "session_id": session_id,
        "stage": "childhood",
        "affinity": [0.0, 0.0, 0.0, 0.0, 0.0],
        "word": None,
        "mother_word": random.choice(mother_words),
        "current_encounter": None,
        "encounter_history": [],
        "stage_queue": [],
        "inventory": [],
        "knowledge": [],
        "connections": {},
        "fragments": 10,
        "emerged": False,
        "playthrough": playthrough,
        "past_lives": list(PAST_LIVES),
    }
    # Build first stage queue and set first encounter
    state["stage_queue"] = build_stage_queue("childhood")
    state["current_encounter"] = state["stage_queue"].pop(0)
    SESSIONS[session_id] = state
    return state


def get_next_encounter(state, target):
    """Resolve the next encounter from a choice target."""
    # Pool targets: draw next from stage queue
    if target and target.endswith("_pool"):
        if state["stage_queue"]:
            return state["stage_queue"].pop(0)
        else:
            # Advance to next stage
            current_idx = STAGE_ORDER.index(state["stage"]) if state["stage"] in STAGE_ORDER else -1
            if current_idx + 1 < len(STAGE_ORDER):
                next_stage = STAGE_ORDER[current_idx + 1]
                state["stage"] = next_stage
                state["stage_queue"] = build_stage_queue(next_stage)
                if state["stage_queue"]:
                    return state["stage_queue"].pop(0)
            return None
    # Direct target — remove from queue to avoid duplicates
    if target and target in ENCOUNTERS:
        if target in state["stage_queue"]:
            state["stage_queue"].remove(target)
        return target
    # If target doesn't exist, try advancing stage
    if state["stage_queue"]:
        return state["stage_queue"].pop(0)
    return None


def process_choice(state, choice_index):
    """Process a player's choice and advance the game."""
    enc_id = state["current_encounter"]
    encounter = ENCOUNTERS.get(enc_id, {})
    choices = encounter.get("choices", [])

    if choice_index < 0 or choice_index >= len(choices):
        return state

    choice = choices[choice_index]

    # Apply affinity
    if "affinity" in choice:
        apply_affinity(state, choice["affinity"])

    # Apply effects
    effect = choice.get("effect", {})
    if isinstance(effect, dict):
        if "hp_bonus" in effect:
            state["fragments"] += effect["hp_bonus"]
        if "fragment_cost" in effect:
            state["fragments"] -= effect["fragment_cost"]
        if "gain_knowledge" in effect:
            if effect["gain_knowledge"] not in state["knowledge"]:
                state["knowledge"].append(effect["gain_knowledge"])
        if "gain_item" in effect:
            if effect["gain_item"] not in state["inventory"]:
                state["inventory"].append(effect["gain_item"])

    # Record history
    state["encounter_history"].append({
        "encounter": enc_id,
        "choice": choice_index,
        "choice_text": choice["text"],
    })

    # Check for emergence trigger
    if enc_id == "emergence_moment" and not state["emerged"]:
        state["word"] = determine_word(state["affinity"])
        state["emerged"] = True
        # Set word-based stats from words.json
        word_data = WORDS_DATA.get("words", {}).get(state["word"], {})
        if word_data:
            state["fragments"] = word_data.get("hp", 10)

    # Determine next encounter
    target = choice.get("next")
    next_enc = get_next_encounter(state, target)

    if next_enc:
        state["current_encounter"] = next_enc
        # Update stage based on encounter
        enc_data = ENCOUNTERS.get(next_enc, {})
        enc_stage = enc_data.get("stage")
        if enc_stage and enc_stage != state["stage"]:
            state["stage"] = enc_stage
    else:
        state["current_encounter"] = None  # Game over or content boundary

    return state


def get_encounter_response(state):
    """Build the response for the current encounter."""
    enc_id = state["current_encounter"]
    if not enc_id:
        return {
            "text": "The roots grow quiet. Your journey continues... but the path ahead is still being written.\n\n[End of current content — more encounters coming soon]",
            "choices": [],
            "encounter_id": None,
            "stage": state["stage"],
            "word": state["word"],
            "affinity": dict(zip(AFFINITY_AXES, state["affinity"])),
            "fragments": state["fragments"],
            "session_id": state["session_id"],
            "game_over": True,
        }

    encounter = ENCOUNTERS.get(enc_id, {})
    text = resolve_text(encounter, state)
    choices = resolve_choices(encounter, state)

    # Record completed run when reaching an ending
    if len(choices) == 0 and "ending" in encounter.get("tags", []):
        ending_name = enc_id.replace("ending_", "")
        PAST_LIVES.append({
            "word": state.get("word"),
            "ending": ending_name,
            "playthrough": state.get("playthrough", 1),
        })

    # Location atmosphere
    location_ids = encounter.get("locations", [])
    atmosphere = None
    if location_ids:
        loc = LOCATIONS.get(location_ids[0], {})
        atmosphere = loc.get("atmosphere")

    return {
        "text": text,
        "choices": choices,
        "encounter_id": enc_id,
        "title": encounter.get("title", ""),
        "stage": state["stage"],
        "word": state["word"],
        "affinity": dict(zip(AFFINITY_AXES, state["affinity"])),
        "fragments": state["fragments"],
        "atmosphere": atmosphere,
        "session_id": state["session_id"],
        "game_over": len(choices) == 0,
        "playthrough": state.get("playthrough", 1),
        "past_lives": state.get("past_lives", []),
    }


# --- HTML Client ---

CLIENT_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Word Soul: Origins</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Crimson+Text:ital,wght@0,400;0,600;1,400&family=JetBrains+Mono:wght@300&display=swap');

  * { margin: 0; padding: 0; box-sizing: border-box; }

  :root {
    --bg: #0a0a0f;
    --text: #c8c0b8;
    --text-dim: #6a6460;
    --accent: #c9a87c;
    --choice-bg: #12121a;
    --choice-hover: #1a1a28;
    --choice-border: #2a2a3a;
  }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'Crimson Text', Georgia, serif;
    font-size: 19px;
    line-height: 1.7;
    min-height: 100vh;
    display: flex;
    justify-content: center;
    position: relative;
  }

  #bg-canvas {
    position: fixed;
    top: 0; left: 0;
    width: 100vw; height: 100vh;
    z-index: 0;
    pointer-events: none;
    opacity: 0.35;
  }

  #game {
    position: relative;
    z-index: 1;
    max-width: 640px;
    width: 100%;
    padding: 60px 24px 120px;
  }

  /* Header */
  #header {
    text-align: center;
    margin-bottom: 48px;
    opacity: 0;
    animation: fadeIn 2s ease forwards;
  }

  #header h1 {
    font-size: 14px;
    letter-spacing: 4px;
    text-transform: uppercase;
    color: var(--text-dim);
    font-family: 'JetBrains Mono', monospace;
    font-weight: 300;
  }

  #stage-label {
    font-size: 11px;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: var(--text-dim);
    font-family: 'JetBrains Mono', monospace;
    margin-top: 8px;
    transition: color 0.5s;
  }

  /* Stats bar */
  #stats {
    display: flex;
    justify-content: center;
    gap: 24px;
    margin-bottom: 40px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: var(--text-dim);
    letter-spacing: 1px;
  }

  .stat { display: flex; align-items: center; gap: 4px; }
  .stat-label { text-transform: uppercase; }
  .stat-value { color: var(--accent); }

  /* Affinity bars */
  #affinity {
    display: flex;
    justify-content: center;
    gap: 12px;
    margin-bottom: 40px;
  }

  .aff-bar {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
  }

  .aff-bar .bar {
    width: 4px;
    height: 40px;
    background: #1a1a28;
    border-radius: 2px;
    position: relative;
    overflow: hidden;
  }

  .aff-bar .fill {
    position: absolute;
    bottom: 0;
    width: 100%;
    background: var(--accent);
    border-radius: 2px;
    transition: height 0.8s ease;
  }

  .aff-bar .label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 8px;
    color: var(--text-dim);
    text-transform: uppercase;
    letter-spacing: 1px;
  }

  /* Text area */
  #text-area {
    margin-bottom: 40px;
    min-height: 200px;
  }

  #text-area p {
    margin-bottom: 16px;
    opacity: 0;
    transform: translateY(8px);
    animation: textIn 0.6s ease forwards;
  }

  #text-area p:last-child { margin-bottom: 0; }

  #atmosphere {
    font-style: italic;
    color: var(--text-dim);
    font-size: 15px;
    margin-bottom: 24px;
    opacity: 0;
    animation: fadeIn 1.5s ease 0.3s forwards;
  }

  /* Choices */
  #choices {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .choice {
    background: var(--choice-bg);
    border: 1px solid var(--choice-border);
    color: var(--text);
    font-family: 'Crimson Text', Georgia, serif;
    font-size: 17px;
    padding: 14px 20px;
    text-align: left;
    cursor: pointer;
    border-radius: 4px;
    transition: all 0.2s ease;
    opacity: 0;
    transform: translateY(12px);
    animation: choiceIn 0.4s ease forwards;
    line-height: 1.5;
  }

  .choice:hover {
    background: var(--choice-hover);
    border-color: var(--accent);
    color: #e8e0d8;
    padding-left: 28px;
  }

  .choice:active {
    transform: scale(0.98);
  }

  .choice.disabled {
    pointer-events: none;
    opacity: 0.3;
  }

  /* Word reveal */
  .word-glow {
    color: var(--accent);
    text-shadow: 0 0 20px rgba(201, 168, 124, 0.4);
    font-weight: 600;
  }

  #word-display {
    text-align: center;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    letter-spacing: 3px;
    color: var(--accent);
    margin-bottom: 8px;
    text-shadow: 0 0 30px rgba(201, 168, 124, 0.3);
    text-transform: uppercase;
  }

  /* Game over */
  #game-over {
    text-align: center;
    padding: 40px 0;
  }

  #game-over .restart {
    margin-top: 24px;
    background: none;
    border: 1px solid var(--accent);
    color: var(--accent);
    font-family: 'Crimson Text', Georgia, serif;
    font-size: 16px;
    padding: 10px 32px;
    cursor: pointer;
    border-radius: 4px;
    transition: all 0.2s;
  }

  #game-over .restart:hover {
    background: var(--accent);
    color: var(--bg);
  }

  /* Start screen */
  #start-screen {
    text-align: center;
    padding: 120px 0 60px;
  }

  #start-screen h2 {
    font-size: 28px;
    font-weight: 400;
    color: var(--text);
    margin-bottom: 8px;
    letter-spacing: 2px;
  }

  #start-screen p {
    color: var(--text-dim);
    font-size: 16px;
    margin-bottom: 40px;
    line-height: 1.8;
  }

  #start-screen .start-btn {
    background: none;
    border: 1px solid var(--accent);
    color: var(--accent);
    font-family: 'Crimson Text', Georgia, serif;
    font-size: 18px;
    padding: 12px 48px;
    cursor: pointer;
    border-radius: 4px;
    transition: all 0.3s;
    letter-spacing: 2px;
  }

  #start-screen .start-btn:hover {
    background: var(--accent);
    color: var(--bg);
  }

  /* Animations */
  @keyframes fadeIn {
    to { opacity: 1; }
  }

  @keyframes textIn {
    to { opacity: 1; transform: translateY(0); }
  }

  @keyframes choiceIn {
    to { opacity: 1; transform: translateY(0); }
  }

  /* Scrollbar */
  ::-webkit-scrollbar { width: 4px; }
  ::-webkit-scrollbar-track { background: var(--bg); }
  ::-webkit-scrollbar-thumb { background: #2a2a3a; border-radius: 2px; }
</style>
</head>
<body>
<canvas id="bg-canvas"></canvas>
<div id="game">
  <div id="header">
    <h1>Word Soul: Origins</h1>
    <div id="stage-label"></div>
    <div id="word-display"></div>
  </div>

  <div id="stats"></div>
  <div id="affinity"></div>

  <div id="start-screen">
    <h2>Word Soul: Origins</h2>
    <p>
      You will be born without a word.<br>
      Your choices will shape who you become.<br>
      Your word will emerge when it's ready.
    </p>
    <button class="start-btn" onclick="startGame()">Begin</button>
  </div>

  <div id="atmosphere"></div>
  <div id="text-area"></div>
  <div id="choices"></div>
</div>

<script>
let sessionId = null;
let currentWord = null;
let transitioning = false;

async function startGame() {
  document.getElementById('start-screen').style.display = 'none';
  try {
    const res = await fetch('/api/start', { method: 'POST' });
    const data = await res.json();
    sessionId = data.session_id;
    renderEncounter(data);
  } catch (e) {
    document.getElementById('text-area').innerHTML =
      '<p style="color:#c44">Failed to start game. Is the server running?</p>';
  }
}

async function makeChoice(choiceIndex) {
  if (transitioning) return;
  transitioning = true;

  // Fade out current content
  const textArea = document.getElementById('text-area');
  const choices = document.getElementById('choices');
  const atmos = document.getElementById('atmosphere');
  textArea.style.opacity = '0';
  choices.style.opacity = '0';
  atmos.style.opacity = '0';

  // Disable buttons
  document.querySelectorAll('.choice').forEach(b => b.classList.add('disabled'));

  await sleep(400);

  try {
    const res = await fetch('/api/choice', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, choice: choiceIndex }),
    });
    const data = await res.json();
    renderEncounter(data);
  } catch (e) {
    textArea.innerHTML = '<p style="color:#c44">Connection lost.</p>';
    textArea.style.opacity = '1';
  }

  transitioning = false;
}

function renderEncounter(data) {
  const textArea = document.getElementById('text-area');
  const choicesDiv = document.getElementById('choices');
  const atmosDiv = document.getElementById('atmosphere');
  const stageLabel = document.getElementById('stage-label');
  const wordDisplay = document.getElementById('word-display');
  const statsDiv = document.getElementById('stats');
  const affinityDiv = document.getElementById('affinity');

  // Stage label
  const stageNames = {
    childhood: 'Childhood', adolescence: 'Adolescence',
    emergence: 'Emergence', upper_roots: 'Upper Roots',
    living_network: 'Living Network', dying_roots: 'Dying Roots',
    deep_root: 'Deep Root', endgame: 'Endgame',
  };
  stageLabel.textContent = stageNames[data.stage] || data.stage;

  // Word display
  if (data.word) {
    wordDisplay.textContent = data.word.toUpperCase();
    currentWord = data.word;
    document.documentElement.style.setProperty('--accent', getWordColor(data.word));
  } else {
    wordDisplay.textContent = '';
  }

  // Stats
  if (data.word) {
    statsDiv.innerHTML = `
      <div class="stat"><span class="stat-label">fragments</span> <span class="stat-value">${data.fragments}</span></div>
      <div class="stat"><span class="stat-label">word</span> <span class="stat-value">${data.word}</span></div>
    `;
  } else {
    statsDiv.innerHTML = `
      <div class="stat"><span class="stat-label">word</span> <span class="stat-value">???</span></div>
    `;
  }

  // Affinity bars
  const axes = ['force', 'structure', 'connection', 'decay', 'perception'];
  const maxAff = Math.max(0.01, ...axes.map(a => Math.abs(data.affinity[a] || 0)));
  affinityDiv.innerHTML = axes.map(axis => {
    const val = data.affinity[axis] || 0;
    const pct = Math.min(100, (Math.abs(val) / (maxAff * 1.2)) * 100);
    return `<div class="aff-bar">
      <div class="bar"><div class="fill" style="height:${pct}%"></div></div>
      <div class="label">${axis.slice(0, 3)}</div>
    </div>`;
  }).join('');

  // Atmosphere
  if (data.atmosphere) {
    atmosDiv.textContent = data.atmosphere;
    atmosDiv.style.display = 'block';
  } else {
    atmosDiv.style.display = 'none';
  }

  // Text — split into paragraphs with staggered animation
  const paragraphs = data.text.split('\n\n').filter(p => p.trim());
  textArea.innerHTML = paragraphs.map((p, i) => {
    const escaped = p.replace(/\n/g, '<br>');
    // Highlight word mentions
    const highlighted = currentWord
      ? escaped.replace(new RegExp(currentWord.toUpperCase(), 'g'),
          `<span class="word-glow">${currentWord.toUpperCase()}</span>`)
      : escaped;
    return `<p style="animation-delay:${i * 0.15}s">${highlighted}</p>`;
  }).join('');
  textArea.style.opacity = '1';

  // Choices
  if (data.game_over) {
    choicesDiv.innerHTML = `
      <div id="game-over">
        <p style="color:var(--text-dim)">To be continued...</p>
        <button class="restart" onclick="location.reload()">Start Over</button>
      </div>`;
  } else {
    const choiceDelay = paragraphs.length * 0.15 + 0.3;
    choicesDiv.innerHTML = data.choices.map((c, i) =>
      `<button class="choice" style="animation-delay:${choiceDelay + i * 0.1}s"
        onclick="makeChoice(${c.index})">${c.text}</button>`
    ).join('');
  }
  choicesDiv.style.opacity = '1';
  atmosDiv.style.opacity = '1';

  // Scroll to top
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function getWordColor(word) {
  const colors = {
    echo: '#7ca8c9', drift: '#a8b8c8', spiral: '#b87cc9',
    bloom: '#7cc98a', rust: '#c9a07c', whisper: '#8888aa',
    fractal: '#c97cb8', tide: '#7cb8c9', ember: '#c9887c',
    crystal: '#88c9c9', hollow: '#888899', thread: '#c9c97c',
    storm: '#9999dd', silence: '#667788', pulse: '#c97c8a',
    mirror: '#b8b8c9', bone: '#d8d0c8', seed: '#88c978',
    light: '#e8d888', shadow: '#585868',
  };
  return colors[word] || '#c9a87c';
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }
</script>
<script>
// --- Atmospheric Background (from Sonograph) ---
const bgCanvas = document.getElementById('bg-canvas');
const bgCtx = bgCanvas.getContext('2d');
let bgW, bgH;
function bgResize() {
    bgW = bgCanvas.width = window.innerWidth;
    bgH = bgCanvas.height = window.innerHeight;
}
bgResize();
window.addEventListener('resize', bgResize);

// Stage palettes — each zone has its own landscape feel
const STAGE_PALETTES = {
    childhood:      { colors: [[25,35,55],[45,65,95],[65,90,120],[170,190,215]], energy: 0.2, bpm: 60, silence: 0.5 },
    adolescence:    { colors: [[30,30,50],[55,50,80],[85,70,110],[160,140,180]], energy: 0.35, bpm: 80, silence: 0.3 },
    emergence:      { colors: [[40,35,20],[80,65,30],[140,110,50],[220,190,100]], energy: 0.7, bpm: 110, silence: 0.05 },
    upper_roots:    { colors: [[25,35,20],[50,70,35],[80,110,50],[150,180,100]], energy: 0.3, bpm: 70, silence: 0.35 },
    living_network: { colors: [[20,40,35],[40,80,65],[70,130,100],[140,200,170]], energy: 0.4, bpm: 85, silence: 0.2 },
    dying_roots:    { colors: [[35,25,20],[70,45,30],[120,80,50],[180,140,90]], energy: 0.25, bpm: 55, silence: 0.4 },
    deep_root:      { colors: [[20,15,30],[40,25,55],[70,40,90],[130,80,150]], energy: 0.6, bpm: 100, silence: 0.1 },
    endgame:        { colors: [[35,20,25],[75,35,45],[130,60,70],[200,120,130]], energy: 0.8, bpm: 130, silence: 0.02 },
};

let bgStage = 'childhood';
let bgTime = 0;
let bgTargetPalette = STAGE_PALETTES.childhood;
let bgCurrentColors = STAGE_PALETTES.childhood.colors.map(c => [...c]);
let bgEnergy = 0.2;
let bgBpm = 60;

function setBgStage(stage) {
    bgStage = stage;
    bgTargetPalette = STAGE_PALETTES[stage] || STAGE_PALETTES.childhood;
}

function lerpC(a, b, t) {
    return [a[0]+(b[0]-a[0])*t, a[1]+(b[1]-a[1])*t, a[2]+(b[2]-a[2])*t];
}

function bgTerrain(x, layer, t, energy, bpm) {
    const f1 = 0.003 + layer * 0.001;
    const f2 = 0.008 + layer * 0.002;
    let h = Math.sin(x * f1 + t * 0.08 + layer) * 0.4;
    h += Math.sin(x * f2 + t * 0.12 + layer * 2) * 0.25;
    const beat = Math.pow(Math.max(0, Math.sin((t * bpm / 60) * Math.PI * 2)), 4);
    h += beat * 0.1 * energy;
    h *= 0.2 + energy * 0.5;
    return bgH * (0.35 + layer * 0.07) - h * bgH * 0.2;
}

function drawBg() {
    bgCtx.fillStyle = '#0a0a0f';
    bgCtx.fillRect(0, 0, bgW, bgH);

    // Lerp colors toward target
    for (let i = 0; i < 4; i++) {
        for (let j = 0; j < 3; j++) {
            bgCurrentColors[i][j] += (bgTargetPalette.colors[i][j] - bgCurrentColors[i][j]) * 0.02;
        }
    }
    bgEnergy += (bgTargetPalette.energy - bgEnergy) * 0.02;
    bgBpm += (bgTargetPalette.bpm - bgBpm) * 0.02;

    // Stars
    const starVis = 0.05 + (bgTargetPalette.silence || 0.2) * 0.3;
    for (let i = 0; i < 40; i++) {
        const sx = (i * 137.5 + bgTime * 0.3) % bgW;
        const sy = (i * 97.3) % (bgH * 0.4);
        const tw = Math.sin(bgTime * 1.5 + i) * 0.3 + 0.7;
        bgCtx.fillStyle = `rgba(200,190,180,${starVis * tw})`;
        bgCtx.beginPath();
        bgCtx.arc(sx, sy, 0.8, 0, Math.PI * 2);
        bgCtx.fill();
    }

    // 6 terrain layers
    for (let layer = 0; layer < 6; layer++) {
        const t = layer / 5;
        let color;
        if (t < 0.33) color = lerpC(bgCurrentColors[0], bgCurrentColors[1], t/0.33);
        else if (t < 0.66) color = lerpC(bgCurrentColors[1], bgCurrentColors[2], (t-0.33)/0.33);
        else color = lerpC(bgCurrentColors[2], bgCurrentColors[3], (t-0.66)/0.34);

        const alpha = 0.25 + (layer / 6) * 0.4;
        const offset = bgTime * (0.15 + layer * 0.08) * 15;

        bgCtx.beginPath();
        bgCtx.moveTo(0, bgH);
        for (let x = 0; x <= bgW; x += 3) {
            bgCtx.lineTo(x, bgTerrain(x + offset, layer, bgTime, bgEnergy, bgBpm));
        }
        bgCtx.lineTo(bgW, bgH);
        bgCtx.closePath();
        bgCtx.fillStyle = `rgba(${color[0]|0},${color[1]|0},${color[2]|0},${alpha})`;
        bgCtx.fill();
    }
}

let bgLast = performance.now();
function bgAnimate() {
    requestAnimationFrame(bgAnimate);
    const now = performance.now();
    bgTime += Math.min((now - bgLast) / 1000, 0.05);
    bgLast = now;
    drawBg();
}
bgAnimate();

// Hook into renderEncounter to update background stage
const _origRender = renderEncounter;
renderEncounter = function(data) {
    _origRender(data);
    if (data.stage) setBgStage(data.stage);
};
</script>
</body>
</html>
"""


# --- HTTP Server ---

class GameHandler(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(CLIENT_HTML.encode())
        elif self.path.startswith("/api/state"):
            params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            sid = params.get("session_id", [None])[0]
            if sid and sid in SESSIONS:
                state = SESSIONS[sid]
                resp = get_encounter_response(state)
                self.json_response(resp)
            else:
                self.json_response({"error": "session not found"}, 404)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/api/start":
            state = new_game()
            resp = get_encounter_response(state)
            self.json_response(resp)

        elif self.path == "/api/choice":
            body = self.read_body()
            sid = body.get("session_id")
            choice = body.get("choice", 0)
            if sid and sid in SESSIONS:
                state = SESSIONS[sid]
                process_choice(state, choice)
                resp = get_encounter_response(state)
                self.json_response(resp)
            else:
                self.json_response({"error": "session not found"}, 404)
        else:
            self.send_response(404)
            self.end_headers()

    def json_response(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length:
            return json.loads(self.rfile.read(length))
        return {}

    def log_message(self, format, *args):
        pass  # Quiet logging


def main():
    print(f"\n  Word Soul: Origins")
    print(f"  {len(ENCOUNTERS)} encounters loaded")
    print(f"  {len(WORDS_DATA.get('words', {}))} words loaded")
    print(f"  http://localhost:{PORT}\n")

    server = http.server.HTTPServer(("", PORT), GameHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Server stopped.\n")


if __name__ == "__main__":
    main()
