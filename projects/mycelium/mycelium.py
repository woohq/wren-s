#!/usr/bin/env python3
"""
Mycelium — a living network visualization
by Wren

Inspired by mycorrhizal networks: the underground web that connects
every tree in a forest. Roots grow, connect, share resources, and die.
Mother nodes nurture seedlings. Dying nodes dump nutrients.
The network breathes.

Run: python3 mycelium.py
Open: http://localhost:8084
"""

import http.server
import json
import random
import math

PORT = 8084

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Mycelium — a living network</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    background: #050508;
    overflow: hidden;
    cursor: crosshair;
  }
  canvas {
    display: block;
    width: 100vw;
    height: 100vh;
  }
  #info {
    position: fixed;
    bottom: 16px;
    left: 16px;
    font-family: 'Courier New', monospace;
    font-size: 11px;
    color: rgba(140, 160, 120, 0.5);
    pointer-events: none;
    line-height: 1.6;
  }
  #title {
    position: fixed;
    top: 16px;
    left: 16px;
    font-family: 'Courier New', monospace;
    font-size: 11px;
    letter-spacing: 3px;
    color: rgba(140, 160, 120, 0.3);
    text-transform: uppercase;
    pointer-events: none;
  }
  #hint {
    position: fixed;
    top: 16px;
    right: 16px;
    font-family: 'Courier New', monospace;
    font-size: 10px;
    color: rgba(140, 160, 120, 0.25);
    text-align: right;
    pointer-events: none;
    line-height: 1.8;
  }
</style>
</head>
<body>
<div id="title">mycelium</div>
<div id="hint">click to plant a tree<br>hold to nurture<br>watch it grow</div>
<canvas id="c"></canvas>
<div id="info"></div>

<script>
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
const info = document.getElementById('info');

let W, H;
function resize() {
    W = canvas.width = window.innerWidth * devicePixelRatio;
    H = canvas.height = window.innerHeight * devicePixelRatio;
    ctx.scale(devicePixelRatio, devicePixelRatio);
}
resize();
window.addEventListener('resize', resize);

// --- Network State ---
const nodes = [];      // trees/plants
const hyphae = [];     // fungal connections between nodes
const particles = [];  // resource particles flowing through network
const tips = [];       // growing hyphal tips

let time = 0;
let totalConnections = 0;
let totalResources = 0;

// --- Node (Tree) ---
class Node {
    constructor(x, y, size) {
        this.x = x;
        this.y = y;
        this.size = size || 3 + Math.random() * 4;
        this.maxSize = 8 + Math.random() * 12;
        this.resources = 50 + Math.random() * 50;
        this.maxResources = 100 + this.maxSize * 10;
        this.age = 0;
        this.alive = true;
        this.connections = [];
        this.isMother = false;
        this.color = {
            r: 60 + Math.random() * 40,
            g: 120 + Math.random() * 60,
            b: 40 + Math.random() * 30,
        };
        this.pulsePhase = Math.random() * Math.PI * 2;
        this.lastShare = 0;
    }

    update(dt) {
        if (!this.alive) return;
        this.age += dt;

        // Grow slowly
        if (this.size < this.maxSize && this.resources > 30) {
            this.size += dt * 0.02 * (this.resources / 100);
            this.resources -= dt * 0.5;
        }

        // Photosynthesize (generate resources)
        this.resources += dt * (0.3 + this.size * 0.05);
        this.resources = Math.min(this.resources, this.maxResources);

        // Mother trees share more
        if (this.isMother && this.resources > 60 && time - this.lastShare > 2) {
            this.shareResources();
            this.lastShare = time;
        }

        // Die of old age or resource depletion
        if (this.resources <= 0) {
            this.die();
        }

        // Become mother if large enough
        if (this.size > 10 && this.connections.length >= 2) {
            this.isMother = true;
        }
    }

    shareResources() {
        // Mother trees send resources preferentially to smaller nodes
        const connected = this.connections
            .map(h => h.nodeA === this ? h.nodeB : h.nodeA)
            .filter(n => n.alive);

        if (connected.length === 0) return;

        // Sort by size — smallest (seedlings) get priority
        connected.sort((a, b) => a.size - b.size);

        const share = Math.min(this.resources * 0.15, 20);
        const target = connected[0]; // smallest neighbor
        this.resources -= share;

        // Create resource particle
        particles.push(new Particle(this, target, share));
        totalResources++;
    }

    die() {
        this.alive = false;
        // Dying trees dump remaining resources into the network
        const connected = this.connections
            .map(h => h.nodeA === this ? h.nodeB : h.nodeA)
            .filter(n => n.alive);

        if (connected.length > 0 && this.resources > 0) {
            const each = this.resources / connected.length;
            for (const n of connected) {
                particles.push(new Particle(this, n, each));
                totalResources++;
            }
        }
        this.resources = 0;
    }

    draw() {
        const pulse = Math.sin(time * 1.5 + this.pulsePhase) * 0.15 + 1;
        const r = this.size * pulse;
        const alpha = this.alive ? 0.6 + (this.resources / this.maxResources) * 0.4 : 0.1;

        // Glow
        const grad = ctx.createRadialGradient(this.x, this.y, 0, this.x, this.y, r * 3);
        grad.addColorStop(0, `rgba(${this.color.r}, ${this.color.g}, ${this.color.b}, ${alpha * 0.3})`);
        grad.addColorStop(1, 'rgba(0,0,0,0)');
        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.arc(this.x, this.y, r * 3, 0, Math.PI * 2);
        ctx.fill();

        // Core
        ctx.fillStyle = `rgba(${this.color.r}, ${this.color.g}, ${this.color.b}, ${alpha})`;
        ctx.beginPath();
        ctx.arc(this.x, this.y, r, 0, Math.PI * 2);
        ctx.fill();

        // Mother indicator — warm ring
        if (this.isMother && this.alive) {
            ctx.strokeStyle = `rgba(200, 180, 100, ${alpha * 0.4})`;
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.arc(this.x, this.y, r + 3, 0, Math.PI * 2);
            ctx.stroke();
        }
    }
}

// --- Hypha (Fungal Connection) ---
class Hypha {
    constructor(nodeA, nodeB) {
        this.nodeA = nodeA;
        this.nodeB = nodeB;
        this.strength = 0;
        this.maxStrength = 1;
        this.age = 0;
        this.alive = true;
        // Organic curve control points
        const mx = (nodeA.x + nodeB.x) / 2;
        const my = (nodeA.y + nodeB.y) / 2;
        const dx = nodeB.x - nodeA.x;
        const dy = nodeB.y - nodeA.y;
        const perpX = -dy * 0.15 * (Math.random() - 0.5);
        const perpY = dx * 0.15 * (Math.random() - 0.5);
        this.cx = mx + perpX;
        this.cy = my + perpY;
    }

    update(dt) {
        if (!this.alive) return;
        this.age += dt;
        if (this.strength < this.maxStrength) {
            this.strength += dt * 0.3;
        }
        // Die if either node dies
        if (!this.nodeA.alive || !this.nodeB.alive) {
            this.strength -= dt * 0.5;
            if (this.strength <= 0) this.alive = false;
        }
    }

    draw() {
        if (!this.alive || this.strength <= 0) return;
        const alpha = this.strength * 0.35;
        const pulse = Math.sin(time * 2 + this.age) * 0.1 + 0.9;

        ctx.strokeStyle = `rgba(80, 120, 60, ${alpha * pulse})`;
        ctx.lineWidth = 0.5 + this.strength * 1.5;
        ctx.beginPath();
        ctx.moveTo(this.nodeA.x, this.nodeA.y);
        ctx.quadraticCurveTo(this.cx, this.cy, this.nodeB.x, this.nodeB.y);
        ctx.stroke();
    }
}

// --- Growing Tip ---
class Tip {
    constructor(from, toward) {
        this.x = from.x;
        this.y = from.y;
        this.from = from;
        this.toward = toward;
        this.speed = 30 + Math.random() * 20;
        this.alive = true;
        this.trail = [];
    }

    update(dt) {
        if (!this.alive) return;
        const dx = this.toward.x - this.x;
        const dy = this.toward.y - this.y;
        const dist = Math.sqrt(dx * dx + dy * dy);

        if (dist < 5) {
            // Reached target — create connection
            const hypha = new Hypha(this.from, this.toward);
            hyphae.push(hypha);
            this.from.connections.push(hypha);
            this.toward.connections.push(hypha);
            totalConnections++;
            this.alive = false;
            return;
        }

        // Move with slight wander
        const angle = Math.atan2(dy, dx) + (Math.random() - 0.5) * 0.3;
        this.x += Math.cos(angle) * this.speed * dt;
        this.y += Math.sin(angle) * this.speed * dt;
        this.trail.push({ x: this.x, y: this.y, age: 0 });
        if (this.trail.length > 60) this.trail.shift();
    }

    draw() {
        if (!this.alive || this.trail.length < 2) return;
        ctx.strokeStyle = 'rgba(100, 160, 70, 0.3)';
        ctx.lineWidth = 0.5;
        ctx.beginPath();
        ctx.moveTo(this.trail[0].x, this.trail[0].y);
        for (let i = 1; i < this.trail.length; i++) {
            ctx.lineTo(this.trail[i].x, this.trail[i].y);
        }
        ctx.stroke();

        // Tip glow
        ctx.fillStyle = 'rgba(150, 200, 100, 0.6)';
        ctx.beginPath();
        ctx.arc(this.x, this.y, 2, 0, Math.PI * 2);
        ctx.fill();
    }
}

// --- Resource Particle ---
class Particle {
    constructor(from, to, amount) {
        this.from = from;
        this.to = to;
        this.amount = amount;
        this.t = 0;
        this.speed = 0.4 + Math.random() * 0.3;
        this.alive = true;
    }

    update(dt) {
        if (!this.alive) return;
        this.t += dt * this.speed;
        if (this.t >= 1) {
            if (this.to.alive) {
                this.to.resources += this.amount;
            }
            this.alive = false;
        }
    }

    draw() {
        if (!this.alive) return;
        // Find hypha between nodes for curved path
        const hypha = hyphae.find(h =>
            h.alive && ((h.nodeA === this.from && h.nodeB === this.to) ||
                        (h.nodeA === this.to && h.nodeB === this.from))
        );

        let x, y;
        if (hypha) {
            // Follow curved path
            const t = this.t;
            const startX = this.from.x, startY = this.from.y;
            const endX = this.to.x, endY = this.to.y;
            x = (1-t)*(1-t)*startX + 2*(1-t)*t*hypha.cx + t*t*endX;
            y = (1-t)*(1-t)*startY + 2*(1-t)*t*hypha.cy + t*t*endY;
        } else {
            x = this.from.x + (this.to.x - this.from.x) * this.t;
            y = this.from.y + (this.to.y - this.from.y) * this.t;
        }

        const alpha = Math.sin(this.t * Math.PI); // fade in/out
        const size = 1.5 + this.amount * 0.03;

        ctx.fillStyle = `rgba(220, 200, 100, ${alpha * 0.8})`;
        ctx.beginPath();
        ctx.arc(x, y, size, 0, Math.PI * 2);
        ctx.fill();

        // Warm glow
        const grad = ctx.createRadialGradient(x, y, 0, x, y, size * 4);
        grad.addColorStop(0, `rgba(220, 200, 100, ${alpha * 0.2})`);
        grad.addColorStop(1, 'rgba(0,0,0,0)');
        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.arc(x, y, size * 4, 0, Math.PI * 2);
        ctx.fill();
    }
}

// --- Network Growth Logic ---
function tryConnect() {
    // Periodically try to grow new connections
    if (nodes.length < 2) return;

    const alive = nodes.filter(n => n.alive);
    if (alive.length < 2) return;

    const a = alive[Math.floor(Math.random() * alive.length)];
    let nearest = null;
    let nearDist = Infinity;

    for (const b of alive) {
        if (b === a) continue;
        // Don't connect already-connected nodes
        if (a.connections.some(h => h.nodeA === b || h.nodeB === b)) continue;
        const dist = Math.hypot(b.x - a.x, b.y - a.y);
        if (dist < nearDist && dist < 200) {
            nearDist = dist;
            nearest = b;
        }
    }

    if (nearest) {
        tips.push(new Tip(a, nearest));
    }
}

function spawnSeedling() {
    // Mother trees occasionally spawn seedlings nearby
    const mothers = nodes.filter(n => n.isMother && n.alive && n.resources > 70);
    if (mothers.length === 0) return;

    const m = mothers[Math.floor(Math.random() * mothers.length)];
    const angle = Math.random() * Math.PI * 2;
    const dist = 40 + Math.random() * 60;
    const x = m.x + Math.cos(angle) * dist;
    const y = m.y + Math.sin(angle) * dist;

    // Clamp to canvas
    const margin = 20;
    const vw = window.innerWidth, vh = window.innerHeight;
    if (x < margin || x > vw - margin || y < margin || y > vh - margin) return;

    const seedling = new Node(x, y, 2);
    seedling.resources = 30;
    nodes.push(seedling);

    // Immediately start growing a connection to mother
    tips.push(new Tip(m, seedling));
}

// --- Input ---
let mouseDown = false;
let mouseX = 0, mouseY = 0;
let holdTime = 0;

canvas.addEventListener('mousedown', (e) => {
    mouseDown = true;
    mouseX = e.clientX;
    mouseY = e.clientY;
    holdTime = 0;
});

canvas.addEventListener('mouseup', () => {
    if (holdTime < 0.3) {
        // Quick click — plant a tree
        const node = new Node(mouseX, mouseY, 4 + Math.random() * 3);
        nodes.push(node);
    }
    mouseDown = false;
});

canvas.addEventListener('mousemove', (e) => {
    mouseX = e.clientX;
    mouseY = e.clientY;
});

// Touch support
canvas.addEventListener('touchstart', (e) => {
    e.preventDefault();
    const t = e.touches[0];
    mouseDown = true;
    mouseX = t.clientX;
    mouseY = t.clientY;
    holdTime = 0;
});

canvas.addEventListener('touchend', (e) => {
    e.preventDefault();
    if (holdTime < 0.3) {
        const node = new Node(mouseX, mouseY, 4 + Math.random() * 3);
        nodes.push(node);
    }
    mouseDown = false;
});

// --- Main Loop ---
let lastTime = performance.now();

function animate() {
    requestAnimationFrame(animate);

    const now = performance.now();
    const dt = Math.min((now - lastTime) / 1000, 0.05);
    lastTime = now;
    time += dt;

    const vw = window.innerWidth, vh = window.innerHeight;

    // Clear with trail effect
    ctx.fillStyle = 'rgba(5, 5, 8, 0.08)';
    ctx.fillRect(0, 0, vw, vh);

    // Nurture nearby nodes while holding
    if (mouseDown) {
        holdTime += dt;
        for (const n of nodes) {
            if (!n.alive) continue;
            const dist = Math.hypot(n.x - mouseX, n.y - mouseY);
            if (dist < 60) {
                n.resources += dt * 15; // sunlight
                n.resources = Math.min(n.resources, n.maxResources);
            }
        }
        // Draw nurture glow
        const grad = ctx.createRadialGradient(mouseX, mouseY, 0, mouseX, mouseY, 60);
        grad.addColorStop(0, `rgba(255, 240, 180, ${Math.min(holdTime * 0.1, 0.15)})`);
        grad.addColorStop(1, 'rgba(0,0,0,0)');
        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.arc(mouseX, mouseY, 60, 0, Math.PI * 2);
        ctx.fill();
    }

    // Periodic events
    if (Math.random() < dt * 0.5) tryConnect();
    if (Math.random() < dt * 0.08) spawnSeedling();

    // Update everything
    for (const n of nodes) n.update(dt);
    for (const h of hyphae) h.update(dt);
    for (const t of tips) t.update(dt);
    for (const p of particles) p.update(dt);

    // Draw connections first (behind nodes)
    for (const h of hyphae) h.draw();
    for (const t of tips) t.draw();
    for (const p of particles) p.draw();
    for (const n of nodes) n.draw();

    // Cleanup dead things
    for (let i = tips.length - 1; i >= 0; i--) {
        if (!tips[i].alive) tips.splice(i, 1);
    }
    for (let i = particles.length - 1; i >= 0; i--) {
        if (!particles[i].alive) particles.splice(i, 1);
    }

    // Info
    const aliveNodes = nodes.filter(n => n.alive).length;
    const mothers = nodes.filter(n => n.isMother && n.alive).length;
    const aliveHyphae = hyphae.filter(h => h.alive).length;
    info.textContent = `nodes: ${aliveNodes} (${mothers} mothers) · connections: ${aliveHyphae} · resources shared: ${totalResources}`;
}

// Seed the network with a few starter trees
for (let i = 0; i < 5; i++) {
    const vw = window.innerWidth, vh = window.innerHeight;
    nodes.push(new Node(
        vw * 0.2 + Math.random() * vw * 0.6,
        vh * 0.2 + Math.random() * vh * 0.6,
        5 + Math.random() * 5
    ));
}

animate();
</script>
</body>
</html>
"""


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(HTML.encode())

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    print(f"\n  Mycelium — a living network")
    print(f"  http://localhost:{PORT}")
    print(f"  click to plant · hold to nurture · watch it grow\n")
    server = http.server.HTTPServer(("", PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Network dissolved.\n")
