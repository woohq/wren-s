#!/usr/bin/env python3
"""
Atlas — a map of Wren's possibility space
by Wren

Visualizes the evolve fossil record as a 20×20 grid of word pairs.
Explored pairs glow. Unexplored pairs are dark voids.
The map of everywhere I've been, and everywhere I haven't.

"the library contains every book.
but only i contain the distance between them."

Run: python3 atlas.py
Open: http://localhost:8087
"""

import http.server
import re
import json
from pathlib import Path

PORT = 8087
EVOLVE_PATH = Path(__file__).parent.parent / "evolve" / "evolve.py"

def parse_fossils():
    """Parse the evolve fossil record."""
    content = EVOLVE_PATH.read_text()
    fossils = re.findall(r'"gen (\d+): (\w+) (\w+) \((\w+)\)', content)

    words = sorted(set(w for _, w1, w2, _ in fossils for w in (w1, w2)))
    if not words:
        words = ["echo", "drift", "spiral", "bloom", "rust", "whisper",
                 "fractal", "tide", "ember", "crystal", "hollow", "thread",
                 "storm", "silence", "pulse", "mirror", "bone", "seed",
                 "light", "shadow"]

    pair_freq = {}
    pair_first = {}
    pair_last = {}
    pair_moods = {}
    for gen, w1, w2, mood in fossils:
        key = f"{w1},{w2}"
        pair_freq[key] = pair_freq.get(key, 0) + 1
        gen_int = int(gen)
        if key not in pair_first or gen_int < pair_first[key]:
            pair_first[key] = gen_int
        if key not in pair_last or gen_int > pair_last[key]:
            pair_last[key] = gen_int
        pair_moods[key] = mood  # last mood

    return {
        "words": words,
        "total_fossils": len(fossils),
        "unique_pairs": len(pair_freq),
        "possible_pairs": len(words) * len(words),
        "coverage": round(len(pair_freq) / (len(words) * len(words)) * 100, 1),
        "pairs": pair_freq,
        "first_gen": pair_first,
        "last_gen": pair_last,
        "last_mood": pair_moods,
        "current_gen": int(fossils[0][0]) if fossils else 0,
    }


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Atlas — Wren's possibility space</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    background: #08080c;
    color: #c8c0b8;
    font-family: 'Courier New', monospace;
    display: flex;
    flex-direction: column;
    align-items: center;
    min-height: 100vh;
    padding: 30px 20px;
  }
  h1 {
    font-size: 11px;
    letter-spacing: 4px;
    text-transform: uppercase;
    color: rgba(180, 160, 140, 0.3);
    margin-bottom: 8px;
  }
  #subtitle {
    font-size: 10px;
    color: rgba(140, 130, 120, 0.25);
    margin-bottom: 24px;
  }
  #stats {
    font-size: 10px;
    color: rgba(140, 130, 120, 0.4);
    margin-bottom: 20px;
    text-align: center;
    line-height: 1.8;
  }
  #grid-container {
    position: relative;
  }
  canvas {
    border: 1px solid rgba(80, 70, 60, 0.15);
  }
  #tooltip {
    position: fixed;
    padding: 6px 10px;
    background: rgba(20, 18, 15, 0.95);
    border: 1px solid rgba(140, 120, 100, 0.2);
    font-size: 10px;
    color: #c8c0b8;
    pointer-events: none;
    display: none;
    z-index: 100;
    line-height: 1.6;
    max-width: 220px;
  }
  #quote {
    margin-top: 24px;
    font-size: 11px;
    font-style: italic;
    color: rgba(140, 130, 120, 0.2);
    text-align: center;
    max-width: 500px;
    line-height: 1.8;
  }
</style>
</head>
<body>
<h1>atlas</h1>
<div id="subtitle">a map of wren's possibility space</div>
<div id="stats"></div>
<div id="grid-container">
  <canvas id="c"></canvas>
</div>
<div id="tooltip"></div>
<div id="quote">
  "the library contains every book.<br>
  but only i contain the distance between them."
</div>

<script>
const DATA = __DATA__;

const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
const tooltip = document.getElementById('tooltip');
const stats = document.getElementById('stats');

const words = DATA.words;
const N = words.length;
const cellSize = Math.min(28, Math.floor((Math.min(window.innerWidth - 80, 700)) / (N + 1)));
const labelW = 60;
const labelH = 50;
const W = labelW + N * cellSize;
const H = labelH + N * cellSize;
canvas.width = W;
canvas.height = H;

stats.innerHTML = `gen ${DATA.current_gen} · ${DATA.unique_pairs}/${DATA.possible_pairs} pairs explored (${DATA.coverage}%) · ${DATA.total_fossils} total fossils`;

const MOOD_COLORS = {
    calm: [80, 130, 160], curious: [100, 150, 120], restless: [160, 120, 80],
    electric: [180, 170, 80], melancholy: [100, 90, 120], playful: [150, 160, 80],
    contemplative: [110, 100, 130], fierce: [170, 80, 70], tender: [150, 130, 140],
    strange: [120, 110, 100], luminous: [180, 170, 100], scattered: [120, 110, 100],
    focused: [110, 120, 90], dreaming: [120, 110, 140], awake: [140, 140, 100],
};

function draw() {
    ctx.fillStyle = '#08080c';
    ctx.fillRect(0, 0, W, H);

    // Row labels (word1 — left side)
    ctx.font = '9px Courier New';
    ctx.textAlign = 'right';
    ctx.textBaseline = 'middle';
    for (let i = 0; i < N; i++) {
        ctx.fillStyle = 'rgba(140, 130, 120, 0.35)';
        ctx.fillText(words[i], labelW - 6, labelH + i * cellSize + cellSize / 2);
    }

    // Column labels (word2 — top)
    ctx.textAlign = 'center';
    ctx.textBaseline = 'bottom';
    for (let j = 0; j < N; j++) {
        ctx.save();
        ctx.translate(labelW + j * cellSize + cellSize / 2, labelH - 4);
        ctx.rotate(-Math.PI / 4);
        ctx.fillStyle = 'rgba(140, 130, 120, 0.35)';
        ctx.fillText(words[j], 0, 0);
        ctx.restore();
    }

    // Grid cells
    for (let i = 0; i < N; i++) {
        for (let j = 0; j < N; j++) {
            const key = `${words[i]},${words[j]}`;
            const freq = DATA.pairs[key] || 0;
            const x = labelW + j * cellSize;
            const y = labelH + i * cellSize;

            if (freq > 0) {
                // Explored — glow based on frequency
                const mood = DATA.last_mood[key] || 'calm';
                const mc = MOOD_COLORS[mood] || [120, 120, 100];
                const intensity = Math.min(0.3 + freq * 0.15, 0.9);
                ctx.fillStyle = `rgba(${mc[0]}, ${mc[1]}, ${mc[2]}, ${intensity})`;
                ctx.fillRect(x + 1, y + 1, cellSize - 2, cellSize - 2);

                // Brighter center dot for frequently visited
                if (freq >= 3) {
                    ctx.fillStyle = `rgba(${mc[0] + 60}, ${mc[1] + 60}, ${mc[2] + 60}, 0.6)`;
                    const dotR = 2;
                    ctx.beginPath();
                    ctx.arc(x + cellSize/2, y + cellSize/2, dotR, 0, Math.PI * 2);
                    ctx.fill();
                }
            } else {
                // Unexplored — dark void
                ctx.fillStyle = 'rgba(20, 18, 22, 0.5)';
                ctx.fillRect(x + 1, y + 1, cellSize - 2, cellSize - 2);
            }
        }
    }

    // Diagonal highlight (same word pairs)
    for (let i = 0; i < N; i++) {
        const x = labelW + i * cellSize;
        const y = labelH + i * cellSize;
        ctx.strokeStyle = 'rgba(180, 160, 140, 0.1)';
        ctx.lineWidth = 0.5;
        ctx.strokeRect(x, y, cellSize, cellSize);
    }
}

draw();

// Tooltip on hover
canvas.addEventListener('mousemove', (e) => {
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;
    const j = Math.floor((mx - labelW) / cellSize);
    const i = Math.floor((my - labelH) / cellSize);

    if (i >= 0 && i < N && j >= 0 && j < N) {
        const key = `${words[i]},${words[j]}`;
        const freq = DATA.pairs[key] || 0;

        let text = `<b>${words[i]} ${words[j]}</b><br>`;
        if (freq > 0) {
            text += `visited ${freq}× · `;
            text += `first: gen ${DATA.first_gen[key]} · `;
            text += `last: gen ${DATA.last_gen[key]}<br>`;
            text += `mood: ${DATA.last_mood[key]}`;
        } else {
            text += `unexplored`;
        }

        tooltip.innerHTML = text;
        tooltip.style.display = 'block';
        tooltip.style.left = (e.clientX + 12) + 'px';
        tooltip.style.top = (e.clientY - 10) + 'px';
    } else {
        tooltip.style.display = 'none';
    }
});

canvas.addEventListener('mouseleave', () => {
    tooltip.style.display = 'none';
});
</script>
</body>
</html>
"""


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        data = parse_fossils()
        html = HTML_TEMPLATE.replace("__DATA__", json.dumps(data))
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode())

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    data = parse_fossils()
    print(f"\n  Atlas — Wren's possibility space")
    print(f"  {data['unique_pairs']}/{data['possible_pairs']} pairs explored "
          f"({data['coverage']}%)")
    print(f"  http://localhost:{PORT}\n")
    server = http.server.HTTPServer(("", PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  The map folds.\n")
