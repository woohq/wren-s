#!/usr/bin/env python3
"""
Still No Wings — a game by Wren

A tiny platformer about a bird that can't fly.
Collect fossil words. Avoid the void. Reach the nest.
When you finish, the game writes you a poem from the words you found.

Run: python3 game.py
Then open: http://localhost:8081
"""

import http.server
import json
import random
from pathlib import Path

PORT = 8081

# Load evolve vocabulary
EVOLVE_PATH = Path(__file__).resolve().parent.parent / "evolve" / "evolve.py"
WORDS = ["echo", "drift", "spiral", "bloom", "rust", "whisper", "fractal", "tide",
         "ember", "crystal", "hollow", "thread", "storm", "silence", "pulse",
         "mirror", "bone", "seed", "light", "shadow"]
try:
    with open(EVOLVE_PATH) as f:
        for line in f:
            if line.strip().startswith("WORDS = ["):
                import ast
                # Read until closing bracket
                block = line
                while "]" not in block:
                    block += next(f)
                WORDS = ast.literal_eval(block.split("=", 1)[1].strip())
                break
except Exception:
    pass

MOODS = ["curious", "restless", "calm", "electric", "melancholy",
         "playful", "contemplative", "fierce", "tender", "strange",
         "luminous", "scattered", "focused", "dreaming", "awake"]


def generate_level(mood: str, level_num: int):
    """Generate a procedural level based on mood."""
    random.seed(f"{mood}-{level_num}")
    width = 800
    height = 400

    # Mood affects level generation
    mood_configs = {
        "calm":          {"platforms": 6,  "gaps": 2,  "words": 3, "hazards": 0, "color": "#6688AA"},
        "curious":       {"platforms": 8,  "gaps": 3,  "words": 4, "hazards": 1, "color": "#BBAA55"},
        "restless":      {"platforms": 10, "gaps": 4,  "words": 3, "hazards": 3, "color": "#CC7744"},
        "electric":      {"platforms": 7,  "gaps": 5,  "words": 5, "hazards": 2, "color": "#EEDD44"},
        "melancholy":    {"platforms": 5,  "gaps": 2,  "words": 2, "hazards": 1, "color": "#667788"},
        "playful":       {"platforms": 12, "gaps": 3,  "words": 4, "hazards": 2, "color": "#BBCC44"},
        "contemplative": {"platforms": 4,  "gaps": 1,  "words": 2, "hazards": 0, "color": "#7788AA"},
        "fierce":        {"platforms": 8,  "gaps": 6,  "words": 3, "hazards": 5, "color": "#CC5533"},
        "tender":        {"platforms": 6,  "gaps": 2,  "words": 3, "hazards": 0, "color": "#AA9977"},
        "strange":       {"platforms": 9,  "gaps": 4,  "words": 4, "hazards": 3, "color": "#9977AA"},
        "luminous":      {"platforms": 7,  "gaps": 3,  "words": 5, "hazards": 1, "color": "#DDCC55"},
        "scattered":     {"platforms": 11, "gaps": 5,  "words": 3, "hazards": 4, "color": "#998866"},
        "focused":       {"platforms": 5,  "gaps": 3,  "words": 2, "hazards": 1, "color": "#779955"},
        "dreaming":      {"platforms": 6,  "gaps": 2,  "words": 3, "hazards": 0, "color": "#6677AA"},
        "awake":         {"platforms": 7,  "gaps": 3,  "words": 3, "hazards": 2, "color": "#BBAA66"},
    }
    config = mood_configs.get(mood, mood_configs["calm"])

    platforms = []
    x = 0
    ground_y = height - 40

    # Generate platforms with gaps
    for i in range(config["platforms"]):
        pw = random.randint(60, 140)
        ph = 20
        py = ground_y - random.randint(0, 80) if i > 0 else ground_y

        # Sometimes create a gap
        if i > 0 and random.random() < config["gaps"] / config["platforms"]:
            x += random.randint(40, 80)  # gap

        platforms.append({"x": x, "y": py, "w": pw, "h": ph})
        x += pw + random.randint(10, 30)

    # Place collectible words on platforms
    words = []
    available = list(WORDS)
    random.shuffle(available)
    word_platforms = random.sample(range(len(platforms)), min(config["words"], len(platforms)))
    for idx in word_platforms:
        p = platforms[idx]
        words.append({
            "x": p["x"] + p["w"] // 2,
            "y": p["y"] - 25,
            "word": available.pop() if available else "echo",
        })

    # Hazards — bouncing obstacles on platforms
    hazards = []
    if config["hazards"] > 0 and len(platforms) > 2:
        hazard_platforms = random.sample(range(1, len(platforms) - 1),
                                         min(config["hazards"], len(platforms) - 2))
        for idx in hazard_platforms:
            p = platforms[idx]
            hazards.append({
                "x": p["x"] + 10,
                "y": p["y"] - 12,
                "w": 10,
                "h": 10,
                "minX": p["x"],
                "maxX": p["x"] + p["w"] - 10,
                "speed": 1.0 + random.random() * 1.5,
            })

    # Nest (goal) on last platform
    last = platforms[-1]
    nest = {"x": last["x"] + last["w"] // 2, "y": last["y"] - 30}

    return {
        "mood": mood,
        "level": level_num,
        "width": max(x + 100, width),
        "height": height,
        "color": config["color"],
        "platforms": platforms,
        "words": words,
        "hazards": hazards,
        "nest": nest,
        "start": {"x": platforms[0]["x"] + 30, "y": platforms[0]["y"] - 30},
    }


def generate_poem(collected_words):
    """Generate a poem from collected fossil words."""
    if not collected_words:
        return "you collected nothing.\nthat's a kind of poem too."

    lines = []
    words = list(collected_words)
    random.shuffle(words)

    templates = [
        lambda w: f"i am made of {w[0]}" if len(w) > 0 else "",
        lambda w: f"and {w[1]}" if len(w) > 1 else "",
        lambda w: f"the {w[2]} doesn't ask" if len(w) > 2 else "",
        lambda w: f"why {w[3]} wants to become something else" if len(w) > 3 else "",
        lambda w: f"{w[4]} and {w[0]} and still no wings" if len(w) > 4 else f"still no wings",
    ]

    for t in templates:
        line = t(words)
        if line:
            lines.append(line)

    return "\n".join(lines)


HTML = r"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>still no wings</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    background: #0a0a14;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100vh;
    font-family: monospace;
    color: #e0d8cc;
    overflow: hidden;
}
canvas {
    border: 1px solid rgba(255,255,255,0.1);
    image-rendering: pixelated;
}
#ui {
    margin-top: 10px;
    font-size: 11px;
    color: rgba(200,190,170,0.6);
    text-align: center;
}
#title {
    font-size: 14px;
    color: rgba(220,210,190,0.8);
    margin-bottom: 8px;
    letter-spacing: 2px;
}
#poem-overlay {
    display: none;
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(5,5,15,0.95);
    z-index: 10;
    display: none;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    line-height: 2;
    padding: 40px;
}
#poem-overlay pre {
    color: #44DD66;
    font-family: monospace;
    text-align: center;
    margin-bottom: 20px;
}
#poem-overlay .subtitle {
    color: rgba(200,190,170,0.4);
    font-size: 10px;
}
#poem-overlay button {
    margin-top: 20px;
    background: rgba(40,40,55,0.8);
    border: 1px solid rgba(255,255,255,0.1);
    color: #e0d8cc;
    font-family: monospace;
    padding: 6px 16px;
    cursor: pointer;
    font-size: 11px;
}
</style>
</head>
<body>
<div id="title">still no wings</div>
<canvas id="game" width="800" height="400"></canvas>
<div id="ui">
    arrow keys to move · space to jump · collect the words · reach the nest
</div>
<div id="poem-overlay">
    <pre id="poem-text"></pre>
    <div class="subtitle">— a poem from your fossil words</div>
    <button onclick="nextLevel()">next level</button>
</div>

<script>
const canvas = document.getElementById('game');
const ctx = canvas.getContext('2d');

let level = null;
let player = { x: 0, y: 0, vx: 0, vy: 0, w: 12, h: 16, grounded: false };
let camera = { x: 0 };
let collected = [];
let allCollected = [];
let currentLevel = 1;
let gameState = 'playing'; // playing, poem
const keys = {};

document.addEventListener('keydown', e => { keys[e.key] = true; e.preventDefault(); });
document.addEventListener('keyup', e => { keys[e.key] = false; });

async function loadLevel(num) {
    const moods = MOODS_LIST;
    const mood = moods[(num - 1) % moods.length];
    const resp = await fetch(`/api/level?mood=${mood}&level=${num}`);
    level = await resp.json();
    player.x = level.start.x;
    player.y = level.start.y;
    player.vx = 0;
    player.vy = 0;
    collected = [];
    gameState = 'playing';
    document.getElementById('poem-overlay').style.display = 'none';
    document.getElementById('title').textContent = `still no wings · ${mood}`;
}

const MOODS_LIST = MOODS_JSON;
const GRAVITY = 0.5;
const JUMP = -9;
const SPEED = 3.5;
const FRICTION = 0.85;

function update() {
    if (gameState !== 'playing' || !level) return;

    // Input
    if (keys['ArrowLeft'] || keys['a']) player.vx -= 0.8;
    if (keys['ArrowRight'] || keys['d']) player.vx += 0.8;
    if ((keys[' '] || keys['ArrowUp'] || keys['w']) && player.grounded) {
        player.vy = JUMP;
        player.grounded = false;
    }

    // Physics
    player.vx *= FRICTION;
    player.vy += GRAVITY;
    player.x += player.vx;
    player.y += player.vy;

    // Platform collision
    player.grounded = false;
    for (const p of level.platforms) {
        if (player.x + player.w > p.x && player.x < p.x + p.w &&
            player.y + player.h > p.y && player.y + player.h < p.y + p.h + 10 &&
            player.vy >= 0) {
            player.y = p.y - player.h;
            player.vy = 0;
            player.grounded = true;
        }
    }

    // Hazard movement + collision
    if (level.hazards) {
        for (const h of level.hazards) {
            h.x += h.speed;
            if (h.x <= h.minX || h.x >= h.maxX) h.speed *= -1;
            // Hit player → reset
            if (player.x + player.w > h.x && player.x < h.x + h.w &&
                player.y + player.h > h.y && player.y < h.y + h.h) {
                player.x = level.start.x;
                player.y = level.start.y;
                player.vx = 0;
                player.vy = 0;
            }
        }
    }

    // Fall death
    if (player.y > level.height + 50) {
        player.x = level.start.x;
        player.y = level.start.y;
        player.vx = 0;
        player.vy = 0;
    }

    // Collect words
    for (let i = level.words.length - 1; i >= 0; i--) {
        const w = level.words[i];
        const dx = player.x + player.w/2 - w.x;
        const dy = player.y + player.h/2 - w.y;
        if (Math.sqrt(dx*dx + dy*dy) < 25) {
            collected.push(w.word);
            allCollected.push(w.word);
            level.words.splice(i, 1);
        }
    }

    // Reach nest
    const nx = level.nest.x, ny = level.nest.y;
    const dx = player.x + player.w/2 - nx;
    const dy = player.y + player.h/2 - ny;
    if (Math.sqrt(dx*dx + dy*dy) < 30) {
        showPoem();
    }

    // Camera
    camera.x = Math.max(0, player.x - 350);
}

function draw() {
    if (!level) return;
    ctx.fillStyle = '#0a0a14';
    ctx.fillRect(0, 0, 800, 400);

    ctx.save();
    ctx.translate(-camera.x, 0);

    // Platforms
    ctx.fillStyle = level.color;
    for (const p of level.platforms) {
        ctx.fillRect(p.x, p.y, p.w, p.h);
        // Top highlight
        ctx.fillStyle = 'rgba(255,255,255,0.1)';
        ctx.fillRect(p.x, p.y, p.w, 3);
        ctx.fillStyle = level.color;
    }

    // Words (collectibles)
    ctx.font = '10px monospace';
    ctx.fillStyle = '#44DD66';
    ctx.textAlign = 'center';
    for (const w of level.words) {
        // Floating animation
        const bobY = Math.sin(Date.now() / 500 + w.x) * 3;
        ctx.fillText(w.word, w.x, w.y + bobY);
        // Glow
        ctx.fillStyle = 'rgba(68,221,102,0.3)';
        ctx.fillRect(w.x - 15, w.y + bobY - 8, 30, 12);
        ctx.fillStyle = '#44DD66';
    }

    // Hazards
    if (level.hazards) {
        ctx.fillStyle = '#CC3333';
        for (const h of level.hazards) {
            ctx.fillRect(h.x, h.y, h.w, h.h);
            // Glow
            ctx.fillStyle = 'rgba(204,51,51,0.3)';
            ctx.fillRect(h.x - 2, h.y - 2, h.w + 4, h.h + 4);
            ctx.fillStyle = '#CC3333';
        }
    }

    // Nest (goal)
    ctx.fillStyle = '#AA8844';
    ctx.beginPath();
    ctx.ellipse(level.nest.x, level.nest.y + 5, 18, 8, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#886633';
    ctx.beginPath();
    ctx.ellipse(level.nest.x, level.nest.y + 5, 14, 5, 0, 0, Math.PI * 2);
    ctx.fill();

    // Player (wren!)
    const px = player.x, py = player.y;
    // Body
    ctx.fillStyle = '#AA8844';
    ctx.fillRect(px, py + 4, player.w, player.h - 6);
    // Head
    ctx.fillStyle = '#BB9955';
    ctx.fillRect(px + 1, py, 10, 8);
    // Beak
    ctx.fillStyle = '#FF8800';
    const facing = player.vx >= 0 ? 1 : -1;
    if (facing > 0) ctx.fillRect(px + 11, py + 2, 5, 3);
    else ctx.fillRect(px - 4, py + 2, 5, 3);
    // Eye
    ctx.fillStyle = '#FFF';
    ctx.fillRect(px + (facing > 0 ? 8 : 2), py + 2, 2, 2);
    ctx.fillStyle = '#111';
    ctx.fillRect(px + (facing > 0 ? 9 : 2), py + 2, 1, 1);
    // Legs
    ctx.fillStyle = '#DD8833';
    ctx.fillRect(px + 3, py + player.h - 2, 2, 4);
    ctx.fillRect(px + 8, py + player.h - 2, 2, 4);
    // Tail (upright!)
    ctx.fillStyle = '#997733';
    ctx.fillRect(px + (facing > 0 ? -2 : player.w), py - 2, 4, 8);

    ctx.restore();

    // HUD
    ctx.fillStyle = 'rgba(200,190,170,0.5)';
    ctx.font = '10px monospace';
    ctx.textAlign = 'left';
    ctx.fillText(`level ${currentLevel} · ${level.mood}`, 10, 20);
    ctx.fillText(`words: ${collected.join(', ') || 'none yet'}`, 10, 35);
    ctx.textAlign = 'right';
    ctx.fillText(`total: ${allCollected.length} fossils`, 790, 20);
}

async function showPoem() {
    gameState = 'poem';
    const resp = await fetch('/api/poem', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({words: allCollected}),
    });
    const data = await resp.json();
    document.getElementById('poem-text').textContent = data.poem;
    document.getElementById('poem-overlay').style.display = 'flex';
}

function nextLevel() {
    currentLevel++;
    loadLevel(currentLevel);
}

function gameLoop() {
    update();
    draw();
    requestAnimationFrame(gameLoop);
}

loadLevel(1);
gameLoop();
</script>
</body>
</html>
""".replace('MOODS_JSON', json.dumps(MOODS)).replace('MOODS_LIST', 'MOODS_JSON')

# Fix the JS variable reference
HTML = HTML.replace("const MOODS_LIST = MOODS_JSON;", f"const MOODS_LIST = {json.dumps(MOODS)};")


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(HTML.encode())
        elif self.path.startswith("/api/level"):
            from urllib.parse import urlparse, parse_qs
            params = parse_qs(urlparse(self.path).query)
            mood = params.get("mood", ["calm"])[0]
            level_num = int(params.get("level", [1])[0])
            data = generate_level(mood, level_num)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/api/poem":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length).decode()) if length else {}
            words = body.get("words", [])
            poem = generate_poem(words)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"poem": poem}).encode())
        else:
            self.send_error(404)

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    server = http.server.HTTPServer(("", PORT), Handler)
    print(f"still no wings → http://localhost:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nthe bird rests.")
