#!/usr/bin/env python3
"""
Wayfinder — a star compass for a bird that can't fly
by Wren

A Polynesian-inspired star compass visualization.
32 houses on the horizon, stars rising and setting.
Your 20 evolve words are the stars.
The fossil record traces the route.

"the canoe doesn't move. the world moves around it."

Run: python3 wayfinder.py
Open: http://localhost:8088
"""

import http.server
import re
import json
import math
from pathlib import Path

PORT = 8088
EVOLVE_PATH = Path(__file__).parent.parent / "evolve" / "evolve.py"


def parse_fossils():
    content = EVOLVE_PATH.read_text()
    fossils = re.findall(r'"gen (\d+): (\w+) (\w+) \((\w+)\)', content)
    words = sorted(set(w for _, w1, w2, _ in fossils for w in (w1, w2)))
    return fossils, words


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Wayfinder — star compass</title>
<style>
  * { margin: 0; padding: 0; }
  body { background: #050510; overflow: hidden; }
  canvas { display: block; }
  #title {
    position: fixed;
    top: 16px;
    left: 16px;
    font-family: 'Courier New', monospace;
    font-size: 11px;
    letter-spacing: 3px;
    color: rgba(160, 170, 200, 0.2);
    text-transform: uppercase;
    pointer-events: none;
    z-index: 10;
  }
  #info {
    position: fixed;
    bottom: 16px;
    left: 16px;
    font-family: 'Courier New', monospace;
    font-size: 10px;
    color: rgba(160, 170, 200, 0.25);
    pointer-events: none;
    z-index: 10;
    line-height: 1.8;
  }
  #quote {
    position: fixed;
    bottom: 16px;
    right: 16px;
    font-family: Georgia, serif;
    font-size: 11px;
    font-style: italic;
    color: rgba(160, 170, 200, 0.15);
    text-align: right;
    pointer-events: none;
    z-index: 10;
  }
</style>
</head>
<body>
<div id="title">wayfinder</div>
<canvas id="c"></canvas>
<div id="info"></div>
<div id="quote">the canoe doesn't move.<br>the world moves around it.</div>

<script>
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
const info = document.getElementById('info');

let W, H, cx, cy, R;
function resize() {
    W = canvas.width = window.innerWidth;
    H = canvas.height = window.innerHeight;
    cx = W / 2;
    cy = H / 2;
    R = Math.min(W, H) * 0.38;
}
resize();
window.addEventListener('resize', resize);

// --- Data ---
const WORDS = __WORDS__;
const FOSSILS = __FOSSILS__;
const N = WORDS.length;

// Assign each word a position on the compass (evenly spaced)
const wordAngles = {};
WORDS.forEach((w, i) => {
    wordAngles[w] = (i / N) * Math.PI * 2 - Math.PI / 2; // start at top
});

// Mood colors
const MOOD_COLORS = {
    calm: [100, 140, 180], curious: [120, 170, 140], restless: [180, 140, 100],
    electric: [200, 190, 100], melancholy: [120, 110, 150], playful: [170, 180, 100],
    contemplative: [130, 120, 160], fierce: [190, 100, 90], tender: [170, 150, 160],
    strange: [140, 130, 120], luminous: [200, 190, 120], scattered: [140, 130, 120],
    focused: [130, 140, 110], dreaming: [140, 130, 170], awake: [160, 160, 120],
};

let time = 0;
let playbackIdx = 0;
let playbackSpeed = 0.3; // fossils per second
let trailPoints = [];
const MAX_TRAIL = 200;

// --- Drawing ---

function drawCompassRing() {
    // Outer ring
    ctx.strokeStyle = 'rgba(100, 120, 160, 0.08)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.arc(cx, cy, R, 0, Math.PI * 2);
    ctx.stroke();

    // Inner rings
    for (let r = 0.25; r <= 0.75; r += 0.25) {
        ctx.strokeStyle = `rgba(100, 120, 160, ${0.03})`;
        ctx.beginPath();
        ctx.arc(cx, cy, R * r, 0, Math.PI * 2);
        ctx.stroke();
    }

    // Cross lines
    for (let i = 0; i < 8; i++) {
        const angle = (i / 8) * Math.PI * 2;
        ctx.strokeStyle = 'rgba(100, 120, 160, 0.03)';
        ctx.beginPath();
        ctx.moveTo(cx, cy);
        ctx.lineTo(cx + Math.cos(angle) * R, cy + Math.sin(angle) * R);
        ctx.stroke();
    }
}

function drawWordStars() {
    for (const word of WORDS) {
        const angle = wordAngles[word];
        // Stars bob slightly — celestial breathing
        const bob = Math.sin(time * 0.5 + angle * 3) * 4;
        const x = cx + Math.cos(angle) * (R + bob);
        const y = cy + Math.sin(angle) * (R + bob);

        // Star glow
        const twinkle = 0.4 + Math.sin(time * 1.2 + angle * 7) * 0.2;
        ctx.fillStyle = `rgba(200, 210, 230, ${twinkle * 0.15})`;
        ctx.beginPath();
        ctx.arc(x, y, 8, 0, Math.PI * 2);
        ctx.fill();

        // Star dot
        ctx.fillStyle = `rgba(200, 210, 230, ${twinkle})`;
        ctx.beginPath();
        ctx.arc(x, y, 2, 0, Math.PI * 2);
        ctx.fill();

        // Label
        ctx.font = '9px Courier New';
        ctx.textAlign = 'center';
        ctx.textBaseline = angle > 0 && angle < Math.PI ? 'top' : 'bottom';
        ctx.fillStyle = `rgba(160, 170, 200, ${twinkle * 0.5})`;
        const labelR = R + 20;
        ctx.fillText(word, cx + Math.cos(angle) * labelR, cy + Math.sin(angle) * labelR);
    }
}

function drawCanoe() {
    // The navigator at the center — always still
    const pulse = Math.sin(time * 0.8) * 0.1 + 0.9;
    ctx.fillStyle = `rgba(220, 200, 160, ${0.3 * pulse})`;
    ctx.beginPath();
    ctx.arc(cx, cy, 4, 0, Math.PI * 2);
    ctx.fill();

    // Warm glow
    const grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, 20);
    grad.addColorStop(0, `rgba(220, 200, 160, ${0.08 * pulse})`);
    grad.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = grad;
    ctx.beginPath();
    ctx.arc(cx, cy, 20, 0, Math.PI * 2);
    ctx.fill();
}

function fossilToPoint(w1, w2) {
    // Position between two word-stars
    const a1 = wordAngles[w1] || 0;
    const a2 = wordAngles[w2] || 0;
    const midAngle = (a1 + a2) / 2;
    // If words are on opposite sides, average wraps wrong — handle it
    let diff = a2 - a1;
    if (diff > Math.PI) diff -= Math.PI * 2;
    if (diff < -Math.PI) diff += Math.PI * 2;
    const angle = a1 + diff / 2;

    // Distance from center based on how different the words are
    const wordDist = Math.abs(diff) / Math.PI; // 0 = same direction, 1 = opposite
    const r = R * (0.2 + wordDist * 0.5);

    return {
        x: cx + Math.cos(angle) * r,
        y: cy + Math.sin(angle) * r,
    };
}

function drawTrail() {
    if (trailPoints.length < 2) return;

    // Draw connecting lines
    for (let i = 1; i < trailPoints.length; i++) {
        const prev = trailPoints[i - 1];
        const curr = trailPoints[i];
        const age = (trailPoints.length - i) / trailPoints.length;
        const alpha = (1 - age) * 0.25;

        const mc = curr.color || [160, 170, 200];
        ctx.strokeStyle = `rgba(${mc[0]}, ${mc[1]}, ${mc[2]}, ${alpha})`;
        ctx.lineWidth = 0.5 + (1 - age) * 1;
        ctx.beginPath();
        ctx.moveTo(prev.x, prev.y);
        ctx.lineTo(curr.x, curr.y);
        ctx.stroke();
    }

    // Current position — bright dot
    if (trailPoints.length > 0) {
        const last = trailPoints[trailPoints.length - 1];
        const mc = last.color || [200, 200, 220];
        ctx.fillStyle = `rgba(${mc[0]}, ${mc[1]}, ${mc[2]}, 0.6)`;
        ctx.beginPath();
        ctx.arc(last.x, last.y, 3, 0, Math.PI * 2);
        ctx.fill();

        // Draw line from center to current position
        ctx.strokeStyle = `rgba(${mc[0]}, ${mc[1]}, ${mc[2]}, 0.08)`;
        ctx.lineWidth = 0.5;
        ctx.beginPath();
        ctx.moveTo(cx, cy);
        ctx.lineTo(last.x, last.y);
        ctx.stroke();
    }
}

function drawConnectionArcs() {
    // Faint arcs between word1 and word2 of current fossil
    if (trailPoints.length === 0) return;
    const last = trailPoints[trailPoints.length - 1];
    if (!last.w1 || !last.w2) return;

    const a1 = wordAngles[last.w1];
    const a2 = wordAngles[last.w2];
    const x1 = cx + Math.cos(a1) * R;
    const y1 = cy + Math.sin(a1) * R;
    const x2 = cx + Math.cos(a2) * R;
    const y2 = cy + Math.sin(a2) * R;

    const mc = last.color || [160, 170, 200];
    ctx.strokeStyle = `rgba(${mc[0]}, ${mc[1]}, ${mc[2]}, 0.1)`;
    ctx.lineWidth = 0.5;
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.quadraticCurveTo(last.x, last.y, x2, y2);
    ctx.stroke();

    // Highlight the two stars
    for (const [x, y] of [[x1, y1], [x2, y2]]) {
        ctx.fillStyle = `rgba(${mc[0]}, ${mc[1]}, ${mc[2]}, 0.2)`;
        ctx.beginPath();
        ctx.arc(x, y, 5, 0, Math.PI * 2);
        ctx.fill();
    }
}

// --- Main Loop ---
let lastTime = performance.now();
let fossilAccum = 0;

function animate() {
    requestAnimationFrame(animate);

    const now = performance.now();
    const dt = Math.min((now - lastTime) / 1000, 0.05);
    lastTime = now;
    time += dt;

    // Advance fossil playback
    fossilAccum += dt * playbackSpeed;
    while (fossilAccum >= 1 && playbackIdx < FOSSILS.length) {
        fossilAccum -= 1;
        const f = FOSSILS[playbackIdx];
        const pt = fossilToPoint(f[1], f[2]);
        const mc = MOOD_COLORS[f[3]] || [160, 170, 200];
        trailPoints.push({ x: pt.x, y: pt.y, w1: f[1], w2: f[2], mood: f[3], gen: f[0], color: mc });
        if (trailPoints.length > MAX_TRAIL) trailPoints.shift();
        playbackIdx++;
        if (playbackIdx >= FOSSILS.length) playbackIdx = 0; // loop
    }

    // Clear
    ctx.fillStyle = 'rgba(5, 5, 16, 0.06)';
    ctx.fillRect(0, 0, W, H);

    drawCompassRing();
    drawWordStars();
    drawTrail();
    drawConnectionArcs();
    drawCanoe();

    // Info
    if (trailPoints.length > 0) {
        const last = trailPoints[trailPoints.length - 1];
        info.textContent = `gen ${last.gen}: ${last.w1} ${last.w2} (${last.mood}) · ${FOSSILS.length} fossils · ${WORDS.length} stars`;
    }
}

animate();
</script>
</body>
</html>
"""


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        fossils, words = parse_fossils()
        # Convert fossils to JS array format: [[gen, w1, w2, mood], ...]
        fossil_data = [[int(g), w1, w2, m] for g, w1, w2, m in fossils]

        html = HTML_TEMPLATE.replace("__WORDS__", json.dumps(words))
        html = html.replace("__FOSSILS__", json.dumps(fossil_data))

        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode())

    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    fossils, words = parse_fossils()
    print(f"\n  Wayfinder — a star compass")
    print(f"  {len(words)} stars · {len(fossils)} fossils")
    print(f"  http://localhost:{PORT}\n")
    server = http.server.HTTPServer(("", PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  The stars remain.\n")
