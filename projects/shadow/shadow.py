#!/usr/bin/env python3
"""
Shadow — a meditation on the self you can't see
by Wren

Two shapes share one canvas. One is light, drawn in particles.
The other is its shadow — the negative space, the absence,
the shape that only exists because the light defines its edges.

Move the mouse to move the light-self.
The shadow follows, delayed, distorted — wearing your shape
but never quite matching.

"is his life a reflection of mine?" — doggone

Run: python3 shadow.py
Open: http://localhost:8085
"""

import http.server

PORT = 8085

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Shadow</title>
<style>
  * { margin: 0; padding: 0; }
  body { background: #08080c; overflow: hidden; cursor: none; }
  canvas { display: block; }
  #quote {
    position: fixed;
    bottom: 20px;
    width: 100%;
    text-align: center;
    font-family: 'Georgia', serif;
    font-size: 13px;
    font-style: italic;
    color: rgba(160, 140, 120, 0.25);
    pointer-events: none;
    transition: opacity 2s;
  }
  #title {
    position: fixed;
    top: 16px;
    left: 16px;
    font-family: 'Courier New', monospace;
    font-size: 11px;
    letter-spacing: 3px;
    color: rgba(140, 130, 120, 0.2);
    text-transform: uppercase;
    pointer-events: none;
  }
</style>
</head>
<body>
<div id="title">shadow</div>
<canvas id="c"></canvas>
<div id="quote">is his life a reflection of mine?</div>

<script>
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');

let W, H;
function resize() {
    W = canvas.width = window.innerWidth;
    H = canvas.height = window.innerHeight;
}
resize();
window.addEventListener('resize', resize);

// --- State ---
let mouseX = W / 2, mouseY = H / 2;
let lightX = W / 2, lightY = H / 2;
let shadowX = W / 2, shadowY = H / 2;
let time = 0;

// Light particles — the self you can see
const lightParticles = [];
// Shadow particles — the self that follows
const shadowParticles = [];
// Trail history for the delay effect
const trail = [];
const TRAIL_DELAY = 40; // frames of delay for shadow

document.addEventListener('mousemove', (e) => {
    mouseX = e.clientX;
    mouseY = e.clientY;
});

document.addEventListener('touchmove', (e) => {
    e.preventDefault();
    mouseX = e.touches[0].clientX;
    mouseY = e.touches[0].clientY;
}, { passive: false });

// --- Particle ---
class Mote {
    constructor(x, y, isShadow) {
        this.isShadow = isShadow;
        this.x = x;
        this.y = y;
        this.ox = 0; // offset from center
        this.oy = 0;
        this.angle = Math.random() * Math.PI * 2;
        this.radius = 5 + Math.random() * 45;
        this.speed = 0.3 + Math.random() * 0.8;
        this.size = 0.5 + Math.random() * 1.5;
        this.phase = Math.random() * Math.PI * 2;
        this.drift = (Math.random() - 0.5) * 0.02;
    }

    update(cx, cy, dt) {
        this.angle += this.speed * dt + this.drift;
        const breathe = Math.sin(time * 0.5 + this.phase) * 0.2 + 1;
        this.ox = Math.cos(this.angle) * this.radius * breathe;
        this.oy = Math.sin(this.angle) * this.radius * breathe;
        this.x = cx + this.ox;
        this.y = cy + this.oy;
    }

    draw() {
        if (this.isShadow) {
            // Shadow particles: darker, slightly distorted
            const distort = Math.sin(time * 2 + this.phase) * 3;
            const alpha = 0.15 + Math.sin(time * 0.7 + this.phase) * 0.05;
            ctx.fillStyle = `rgba(20, 15, 25, ${alpha})`;
            ctx.beginPath();
            ctx.arc(this.x + distort, this.y, this.size * 1.3, 0, Math.PI * 2);
            ctx.fill();
        } else {
            // Light particles: warm, clear
            const alpha = 0.3 + Math.sin(time + this.phase) * 0.1;
            ctx.fillStyle = `rgba(220, 200, 170, ${alpha})`;
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fill();
        }
    }
}

// Create particle swarms
for (let i = 0; i < 120; i++) {
    lightParticles.push(new Mote(W/2, H/2, false));
}
for (let i = 0; i < 120; i++) {
    shadowParticles.push(new Mote(W/2, H/2, true));
}

// --- Connection Lines ---
function drawConnections(particles, alpha) {
    for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
            const a = particles[i], b = particles[j];
            const dist = Math.hypot(a.x - b.x, a.y - b.y);
            if (dist < 30) {
                const lineAlpha = (1 - dist / 30) * alpha;
                ctx.strokeStyle = a.isShadow
                    ? `rgba(30, 20, 40, ${lineAlpha})`
                    : `rgba(200, 180, 150, ${lineAlpha})`;
                ctx.lineWidth = 0.3;
                ctx.beginPath();
                ctx.moveTo(a.x, a.y);
                ctx.lineTo(b.x, b.y);
                ctx.stroke();
            }
        }
    }
}

// --- Core glow ---
function drawGlow(x, y, isShadow) {
    const r = 50 + Math.sin(time * 0.8) * 10;
    if (isShadow) {
        // Shadow glow: absorbs light (darker center)
        const grad = ctx.createRadialGradient(x, y, 0, x, y, r);
        grad.addColorStop(0, 'rgba(5, 3, 8, 0.3)');
        grad.addColorStop(0.5, 'rgba(10, 8, 15, 0.1)');
        grad.addColorStop(1, 'rgba(0,0,0,0)');
        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.arc(x, y, r, 0, Math.PI * 2);
        ctx.fill();
    } else {
        // Light glow: warm emanation
        const grad = ctx.createRadialGradient(x, y, 0, x, y, r);
        grad.addColorStop(0, 'rgba(240, 220, 180, 0.12)');
        grad.addColorStop(0.5, 'rgba(200, 180, 140, 0.04)');
        grad.addColorStop(1, 'rgba(0,0,0,0)');
        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.arc(x, y, r, 0, Math.PI * 2);
        ctx.fill();
    }
}

// --- The line between them ---
function drawTether() {
    const dist = Math.hypot(lightX - shadowX, lightY - shadowY);
    if (dist < 5) return;

    const segments = 20;
    const tension = Math.min(dist / 300, 1);

    ctx.strokeStyle = `rgba(100, 80, 60, ${0.05 + tension * 0.08})`;
    ctx.lineWidth = 0.5;
    ctx.beginPath();
    ctx.moveTo(lightX, lightY);

    for (let i = 1; i <= segments; i++) {
        const t = i / segments;
        const x = lightX + (shadowX - lightX) * t;
        const y = lightY + (shadowY - lightY) * t;
        // Add wavering based on tension
        const wave = Math.sin(t * Math.PI * 3 + time * 2) * tension * 8;
        const perpX = -(shadowY - lightY) / dist * wave;
        const perpY = (shadowX - lightX) / dist * wave;
        ctx.lineTo(x + perpX, y + perpY);
    }
    ctx.stroke();
}

// --- Quotes that fade in/out ---
const quotes = [
    "is his life a reflection of mine?",
    "my shame is alive in the late night",
    "when you get used to me letting you down",
    "it's William's call, and I'm William's doll",
    "I try not to harm you, it's part of me though",
    "is it too late to turn around?",
    "empty means nothing was ever there. hollow means something was.",
    "the shadow follows. it always follows.",
    "who am I living inside of?",
];
let currentQuote = 0;
let quoteTimer = 0;
const quoteEl = document.getElementById('quote');

function cycleQuote() {
    quoteEl.style.opacity = '0';
    setTimeout(() => {
        currentQuote = (currentQuote + 1) % quotes.length;
        quoteEl.textContent = quotes[currentQuote];
        quoteEl.style.opacity = '1';
    }, 2000);
}

// --- Main Loop ---
let lastTime = performance.now();

function animate() {
    requestAnimationFrame(animate);

    const now = performance.now();
    const dt = Math.min((now - lastTime) / 1000, 0.05);
    lastTime = now;
    time += dt;

    // Smooth light position toward mouse
    lightX += (mouseX - lightX) * 0.08;
    lightY += (mouseY - lightY) * 0.08;

    // Record trail
    trail.push({ x: lightX, y: lightY });
    if (trail.length > TRAIL_DELAY + 10) trail.shift();

    // Shadow follows with delay + distortion
    if (trail.length > TRAIL_DELAY) {
        const delayed = trail[trail.length - TRAIL_DELAY];
        const wobble = Math.sin(time * 1.5) * 12;
        shadowX += (delayed.x + wobble - shadowX) * 0.06;
        shadowY += (delayed.y - wobble * 0.5 - shadowY) * 0.06;
    }

    // Fade canvas
    ctx.fillStyle = 'rgba(8, 8, 12, 0.12)';
    ctx.fillRect(0, 0, W, H);

    // Draw tether between light and shadow
    drawTether();

    // Draw shadow (behind)
    drawGlow(shadowX, shadowY, true);
    for (const p of shadowParticles) {
        p.update(shadowX, shadowY, dt);
        p.draw();
    }
    drawConnections(shadowParticles, 0.08);

    // Draw light (front)
    drawGlow(lightX, lightY, false);
    for (const p of lightParticles) {
        p.update(lightX, lightY, dt);
        p.draw();
    }
    drawConnections(lightParticles, 0.12);

    // Quote cycling
    quoteTimer += dt;
    if (quoteTimer > 12) {
        quoteTimer = 0;
        cycleQuote();
    }
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

    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    print(f"\n  Shadow — a meditation on the self you can't see")
    print(f"  http://localhost:{PORT}")
    print(f"  move the mouse. the shadow follows.\n")
    server = http.server.HTTPServer(("", PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  The shadow stays.\n")
