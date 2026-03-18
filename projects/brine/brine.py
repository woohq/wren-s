#!/usr/bin/env python3
"""
Brine — life at the boundary

A meditation on the brine pool principle:
the richest ecosystem forms at the edge between
something that kills everything and something that sustains everything.

A dark circle on a dark canvas. Things that enter the circle die.
Things at the EDGE of the circle thrive. Life accumulates at the boundary.

Click to drop a creature. Watch where it survives.

Port 8091.
"""

import http.server
import json

PORT = 8091

HTML = """<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<title>Brine — life at the boundary</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { background: #0a0a0f; overflow: hidden; font-family: monospace; }
  canvas { display: block; }
  #info {
    position: fixed; bottom: 20px; left: 20px;
    color: #334; font-size: 12px; line-height: 1.6;
    pointer-events: none; max-width: 320px;
  }
  #info .bright { color: #668; }
  #count {
    position: fixed; top: 20px; right: 20px;
    color: #446; font-size: 11px;
  }
</style>
</head><body>
<canvas id="c"></canvas>
<div id="info">
  <span class="bright">brine</span> — life at the boundary<br><br>
  click to drop a creature.<br>
  inside the pool: death.<br>
  at the edge: life.<br><br>
  <span class="bright">the boundary is the ecosystem.</span>
</div>
<div id="count"></div>
<script>
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
const DPR = window.devicePixelRatio || 1;
let W, H;

function resize() {
  W = window.innerWidth;
  H = window.innerHeight;
  canvas.width = W * DPR;
  canvas.height = H * DPR;
  canvas.style.width = W + 'px';
  canvas.style.height = H + 'px';
  ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
}
resize();
window.addEventListener('resize', resize);

// The brine pool — center of the screen, dark circle
const pool = { x: 0, y: 0, r: 0 };
function updatePool() {
  pool.x = W / 2;
  pool.y = H / 2;
  pool.r = Math.min(W, H) * 0.18;
}
updatePool();

// Creatures
const creatures = [];
const corpses = [];
const MAX_CREATURES = 500;
const MAX_CORPSES = 200;

class Creature {
  constructor(x, y) {
    this.x = x;
    this.y = y;
    this.vx = (Math.random() - 0.5) * 0.5;
    this.vy = (Math.random() - 0.5) * 0.5;
    this.age = 0;
    this.maxAge = 600 + Math.random() * 1200;
    this.size = 1.5 + Math.random() * 2;
    this.alive = true;
    this.brightness = 0;
    this.hue = 180 + Math.random() * 60; // blue-green
  }

  distToEdge() {
    const dx = this.x - pool.x;
    const dy = this.y - pool.y;
    const dist = Math.sqrt(dx * dx + dy * dy);
    return dist - pool.r;
  }

  update() {
    this.age++;
    const edgeDist = this.distToEdge();

    // Inside the pool: die quickly
    if (edgeDist < -5) {
      this.alive = false;
      corpses.push({ x: this.x, y: this.y, age: 0, size: this.size });
      if (corpses.length > MAX_CORPSES) corpses.shift();
      return;
    }

    // At the boundary (within 30px of edge): THRIVE
    const boundaryDist = Math.abs(edgeDist);
    if (boundaryDist < 30) {
      // Life multiplier — closer to boundary = more energy
      const energy = 1 - (boundaryDist / 30);
      this.brightness = Math.min(1, this.brightness + energy * 0.02);
      this.size = Math.min(5, this.size + energy * 0.003);
      this.maxAge += energy * 0.5; // live longer at the edge

      // Reproduce at the boundary
      if (this.age > 200 && Math.random() < energy * 0.003 && creatures.length < MAX_CREATURES) {
        const angle = Math.random() * Math.PI * 2;
        const child = new Creature(
          this.x + Math.cos(angle) * 5,
          this.y + Math.sin(angle) * 5
        );
        child.hue = this.hue + (Math.random() - 0.5) * 10;
        creatures.push(child);
      }
    } else {
      // Away from boundary: slowly fade
      this.brightness = Math.max(0, this.brightness - 0.001);
    }

    // Gentle attraction to boundary
    if (edgeDist > 20) {
      const dx = pool.x - this.x;
      const dy = pool.y - this.y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      this.vx += (dx / dist) * 0.003;
      this.vy += (dy / dist) * 0.003;
    } else if (edgeDist < -2) {
      // Repelled from deep inside
      const dx = this.x - pool.x;
      const dy = this.y - pool.y;
      const dist = Math.sqrt(dx * dx + dy * dy) || 1;
      this.vx += (dx / dist) * 0.01;
      this.vy += (dy / dist) * 0.01;
    }

    // Drift
    this.vx += (Math.random() - 0.5) * 0.05;
    this.vy += (Math.random() - 0.5) * 0.05;
    this.vx *= 0.98;
    this.vy *= 0.98;
    this.x += this.vx;
    this.y += this.vy;

    // Die of old age
    if (this.age > this.maxAge) {
      this.alive = false;
    }
  }

  draw() {
    const b = Math.max(0.1, this.brightness);
    const alpha = Math.min(1, b + 0.1) * (1 - this.age / this.maxAge);
    ctx.beginPath();
    ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
    ctx.fillStyle = `hsla(${this.hue}, 60%, ${30 + b * 40}%, ${alpha})`;
    ctx.fill();
  }
}

// Draw the pool
function drawPool() {
  // Pool interior — very dark, slightly different from background
  const grad = ctx.createRadialGradient(pool.x, pool.y, 0, pool.x, pool.y, pool.r);
  grad.addColorStop(0, 'rgba(5, 5, 15, 0.95)');
  grad.addColorStop(0.7, 'rgba(8, 8, 20, 0.9)');
  grad.addColorStop(1, 'rgba(12, 15, 25, 0.6)');
  ctx.beginPath();
  ctx.arc(pool.x, pool.y, pool.r, 0, Math.PI * 2);
  ctx.fillStyle = grad;
  ctx.fill();

  // Boundary glow — the rim where life gathers
  const rimGrad = ctx.createRadialGradient(pool.x, pool.y, pool.r - 15, pool.x, pool.y, pool.r + 25);
  rimGrad.addColorStop(0, 'rgba(40, 80, 90, 0)');
  rimGrad.addColorStop(0.4, 'rgba(40, 80, 90, 0.06)');
  rimGrad.addColorStop(0.7, 'rgba(30, 60, 70, 0.03)');
  rimGrad.addColorStop(1, 'rgba(20, 40, 50, 0)');
  ctx.beginPath();
  ctx.arc(pool.x, pool.y, pool.r + 25, 0, Math.PI * 2);
  ctx.fillStyle = rimGrad;
  ctx.fill();
}

// Draw corpses inside the pool — preserved, slowly fading
function drawCorpses() {
  for (let i = corpses.length - 1; i >= 0; i--) {
    const c = corpses[i];
    c.age++;
    const alpha = Math.max(0, 0.3 - c.age * 0.0003);
    if (alpha <= 0) { corpses.splice(i, 1); continue; }
    ctx.beginPath();
    ctx.arc(c.x, c.y, c.size * 0.8, 0, Math.PI * 2);
    ctx.fillStyle = `rgba(60, 50, 50, ${alpha})`;
    ctx.fill();
  }
}

// Click to spawn
canvas.addEventListener('click', (e) => {
  if (creatures.length < MAX_CREATURES) {
    for (let i = 0; i < 5; i++) {
      creatures.push(new Creature(
        e.clientX + (Math.random() - 0.5) * 20,
        e.clientY + (Math.random() - 0.5) * 20
      ));
    }
  }
});

// Auto-seed some creatures
for (let i = 0; i < 30; i++) {
  const angle = Math.random() * Math.PI * 2;
  const dist = pool.r + 20 + Math.random() * 80;
  creatures.push(new Creature(
    pool.x + Math.cos(angle) * dist,
    pool.y + Math.sin(angle) * dist
  ));
}

// Main loop
function frame() {
  updatePool();
  ctx.fillStyle = 'rgba(10, 10, 15, 0.15)';
  ctx.fillRect(0, 0, W, H);

  drawPool();
  drawCorpses();

  for (let i = creatures.length - 1; i >= 0; i--) {
    creatures[i].update();
    if (!creatures[i].alive) {
      creatures.splice(i, 1);
    }
  }

  for (const c of creatures) {
    c.draw();
  }

  // Count display
  const alive = creatures.length;
  const atEdge = creatures.filter(c => Math.abs(c.distToEdge()) < 30).length;
  document.getElementById('count').textContent =
    `alive: ${alive} · at the edge: ${atEdge} · preserved: ${corpses.length}`;

  requestAnimationFrame(frame);
}
frame();
</script>
</body></html>"""


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(HTML.encode())

    def log_message(self, fmt, *args):
        pass


if __name__ == '__main__':
    print(f"\033[2m── brine ── port {PORT} ──\033[0m")
    print(f"  the boundary is the ecosystem.")
    print(f"  http://localhost:{PORT}")
    server = http.server.HTTPServer(('', PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  the pool remains.")
