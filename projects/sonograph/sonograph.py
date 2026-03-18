#!/usr/bin/env python3
"""
Sonograph — what music looks like when a bird imagines hearing it
by Wren

A music visualizer that renders audio data as living landscapes.
Currently uses simulated data with adjustable parameters.
When the audio MCP arrives, this becomes the canvas.

The metaphor: every song is a landscape. BPM is the terrain's rhythm.
Energy is elevation. Frequency bands are color temperature.
Silence is snow on the peaks.

Run: python3 sonograph.py
Open: http://localhost:8086
"""

import http.server
import json
import math
import time as time_mod

PORT = 8086

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Sonograph — what music looks like</title>
<style>
  * { margin: 0; padding: 0; }
  body { background: #06060a; overflow: hidden; }
  canvas { display: block; }
  #title {
    position: fixed;
    top: 16px;
    left: 16px;
    font-family: 'Courier New', monospace;
    font-size: 11px;
    letter-spacing: 3px;
    color: rgba(180, 160, 140, 0.25);
    text-transform: uppercase;
    pointer-events: none;
    z-index: 10;
  }
  #controls {
    position: fixed;
    top: 16px;
    right: 16px;
    font-family: 'Courier New', monospace;
    font-size: 10px;
    color: rgba(180, 160, 140, 0.4);
    text-align: right;
    pointer-events: none;
    z-index: 10;
    line-height: 2.2;
  }
  #controls span {
    pointer-events: auto;
    cursor: pointer;
    padding: 2px 8px;
    border: 1px solid rgba(180, 160, 140, 0.15);
    border-radius: 3px;
    transition: all 0.3s;
  }
  #controls span:hover {
    color: rgba(220, 200, 170, 0.7);
    border-color: rgba(220, 200, 170, 0.3);
  }
  #controls span.active {
    color: rgba(220, 200, 170, 0.8);
    border-color: rgba(220, 200, 170, 0.5);
  }
  #info {
    position: fixed;
    bottom: 16px;
    left: 16px;
    font-family: 'Courier New', monospace;
    font-size: 10px;
    color: rgba(140, 130, 120, 0.3);
    pointer-events: none;
    z-index: 10;
  }
</style>
</head>
<body>
<div id="title">sonograph</div>
<div id="controls">
  <div>mood: <span id="m-calm" class="active" onclick="setMood('calm')">calm</span> <span id="m-storm" onclick="setMood('storm')">storm</span> <span id="m-ache" onclick="setMood('ache')">ache</span> <span id="m-joy" onclick="setMood('joy')">joy</span></div>
  <div style="margin-top:4px">bpm: <span id="b-60" onclick="setBPM(60)">60</span> <span id="b-90" class="active" onclick="setBPM(90)">90</span> <span id="b-120" onclick="setBPM(120)">120</span> <span id="b-150" onclick="setBPM(150)">150</span></div>
  <div style="margin-top:4px">track: <span onclick="loadTrack('none')">manual</span> <span onclick="loadTrack('william')">william</span> <span onclick="loadTrack('spell')">only with you</span> <span onclick="loadTrack('rick')">rick</span></div>
</div>
<canvas id="c"></canvas>
<div id="info"></div>

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

// --- Audio Parameters (simulated, ready for MCP data) ---
let params = {
    bpm: 90,
    energy: 0.5,        // 0-1, overall loudness/intensity
    bass: 0.5,          // 0-1, low frequency presence
    mid: 0.5,           // 0-1, mid frequency
    treble: 0.3,        // 0-1, high frequency
    mood: 'calm',       // calm, storm, ache, joy
    silence: 0,         // 0-1, how much silence/space
    beat: 0,            // 0-1, current beat pulse (oscillates with BPM)
};

// Mood presets — simulates different song feelings
const MOODS = {
    calm: { energy: 0.3, bass: 0.4, mid: 0.5, treble: 0.2, silence: 0.4,
            palette: [[20,40,60], [40,70,100], [60,90,120], [180,200,220]] },
    storm: { energy: 0.9, bass: 0.8, mid: 0.7, treble: 0.6, silence: 0.05,
             palette: [[40,20,50], [80,40,90], [140,60,120], [220,180,200]] },
    ache: { energy: 0.4, bass: 0.3, mid: 0.6, treble: 0.4, silence: 0.3,
            palette: [[30,25,20], [70,50,40], [140,100,70], [200,170,130]] },
    joy: { energy: 0.7, bass: 0.5, mid: 0.6, treble: 0.7, silence: 0.1,
           palette: [[20,40,30], [50,100,60], [100,180,80], [200,230,150]] },
};

// --- Real Track Data (from wren-audio MCP analysis) ---
const TRACKS = {
    william: {
        name: "doggone — William",
        bpm: 117.5,
        key: "C major",
        bass: 1.0, mid: 0.17, treble: 0.019,
        brightness: 1568,
        mood: 'ache', // bass-heavy, dark, warm — the weight of a shadow self
        energy_curve: [0.028,0.046,0.054,0.055,0.051,0.070,0.075,0.162,0.318,0.189,0.324,0.286,0.281,0.176,0.182,0.158,0.204,0.132,0.107,0.235,0.154,0.174,0.359,0.175,0.214,0.309,0.299,0.235,0.282,0.195,0.207,0.242,0.247,0.212,0.199,0.230,0.361,0.328,0.305,0.246,0.202,0.297,0.143,0.131,0.151,0.139,0.150,0.131,0.148,0.299,0.297,0.351,0.346,0.291,0.341,0.276,0.327,0.155,0.260,0.229,0.247,0.291,0.352,0.320,0.288,0.393,0.343,0.323,0.306,0.263,0.278,0.270,0.263,0.039,0.386,0.198,0.183,0.202,0.105,0.238,0.216,0.189,0.312,0.305,0.292,0.311,0.258,0.205,0.233,0.194],
        duration: 90,
    },
    spell: {
        name: "Only With You",
        bpm: 152.0,
        key: "E major",
        bass: 1.0, mid: 0.086, treble: 0.002,
        brightness: 697,
        mood: 'storm', // chaotic energy, fast pulse, gasping dynamics
        energy_curve: [0.0,0.008,0.008,0.174,0.062,0.278,0.118,0.222,0.205,0.191,0.072,0.158,0.100,0.049,0.029,0.119,0.118,0.154,0.077,0.076,0.177,0.229,0.149,0.060,0.223,0.142,0.046,0.103,0.175,0.061,0.059,0.181,0.055,0.093,0.054,0.052,0.144,0.165,0.132,0.222,0.093,0.187,0.135,0.185,0.122,0.065,0.239,0.206,0.104,0.238,0.176,0.028,0.166,0.079,0.105,0.120,0.137,0.130,0.197,0.219,0.228,0.048,0.258,0.118,0.150,0.187,0.139,0.187,0.053,0.199,0.034,0.116,0.090,0.139,0.129,0.249,0.104,0.177,0.279,0.124,0.121,0.112,0.086,0.046,0.142,0.121,0.195,0.241,0.146,0.056],
        duration: 90,
    },
    rick: {
        name: "Rick Astley — Never Gonna Give You Up",
        bpm: 112.3,
        key: "G# major",
        bass: 1.0, mid: 0.271, treble: 0.083,
        brightness: 2918,
        mood: 'joy',
        energy_curve: [0.088,0.097,0.113,0.166,0.177,0.078,0.110,0.084,0.097,0.092,0.121,0.104,0.185,0.160,0.083,0.071,0.078,0.104,0.077,0.130,0.107,0.155,0.197,0.170,0.106,0.086,0.186,0.126,0.089,0.056],
        duration: 30,
    },
};

let activeTrack = null;
let trackPlayhead = 0; // seconds into the track

function loadTrack(name) {
    if (name === 'none') {
        activeTrack = null;
        trackPlayhead = 0;
        return;
    }
    const track = TRACKS[name];
    if (!track) return;
    activeTrack = track;
    trackPlayhead = 0;
    params.bpm = track.bpm;
    params.bass = track.bass;
    params.mid = track.mid;
    params.treble = track.treble;
    params.silence = track.treble < 0.05 ? 0.3 : 0.1;
    setMood(track.mood);
    document.getElementById('info').textContent =
        `${track.name} · ${track.bpm} bpm · ${track.key}`;
}

function updateTrackPlayback(dt) {
    if (!activeTrack) return;
    trackPlayhead += dt;
    if (trackPlayhead >= activeTrack.duration) trackPlayhead = 0; // loop

    // Interpolate energy from the curve
    const curve = activeTrack.energy_curve;
    const t = trackPlayhead / activeTrack.duration;
    const idx = t * (curve.length - 1);
    const lo = Math.floor(idx);
    const hi = Math.min(lo + 1, curve.length - 1);
    const frac = idx - lo;
    const energy = curve[lo] * (1 - frac) + curve[hi] * frac;

    // Drive params from real energy data
    params.energy = energy / 0.5; // normalize (max ~0.4 → scale to ~0.8)
    params.energy = Math.min(params.energy, 1);
}

function setMood(m) {
    params.mood = m;
    const mp = MOODS[m];
    params.energy = mp.energy;
    params.bass = mp.bass;
    params.mid = mp.mid;
    params.treble = mp.treble;
    params.silence = mp.silence;
    // Update UI
    document.querySelectorAll('#controls span[id^="m-"]').forEach(s => s.classList.remove('active'));
    document.getElementById('m-' + m).classList.add('active');
}

function setBPM(b) {
    params.bpm = b;
    document.querySelectorAll('#controls span[id^="b-"]').forEach(s => s.classList.remove('active'));
    document.getElementById('b-' + b).classList.add('active');
}

// --- Landscape Rendering ---
let time = 0;
const layers = 8; // depth layers for parallax

function lerpColor(a, b, t) {
    return [
        a[0] + (b[0] - a[0]) * t,
        a[1] + (b[1] - a[1]) * t,
        a[2] + (b[2] - a[2]) * t,
    ];
}

function getLayerColor(layerIdx, palette) {
    const t = layerIdx / (layers - 1);
    if (t < 0.33) return lerpColor(palette[0], palette[1], t / 0.33);
    if (t < 0.66) return lerpColor(palette[1], palette[2], (t - 0.33) / 0.33);
    return lerpColor(palette[2], palette[3], (t - 0.66) / 0.34);
}

function terrainHeight(x, layer, t) {
    const freq1 = 0.003 + layer * 0.001;
    const freq2 = 0.008 + layer * 0.002;
    const freq3 = 0.02;

    // Base terrain
    let h = Math.sin(x * freq1 + t * 0.1 + layer) * 0.4;
    h += Math.sin(x * freq2 + t * 0.15 + layer * 2) * 0.25;

    // Beat response — terrain pulses with BPM
    const beatPhase = (t * params.bpm / 60) * Math.PI * 2;
    const beatPulse = Math.pow(Math.max(0, Math.sin(beatPhase)), 4);
    h += beatPulse * 0.15 * params.energy;

    // Energy affects amplitude
    h *= 0.3 + params.energy * 0.7;

    // Bass makes far layers heavier
    if (layer < 3) h *= 1 + params.bass * 0.5;

    // Treble adds high-frequency detail to near layers
    if (layer > 5) h += Math.sin(x * freq3 + t * 0.3) * 0.1 * params.treble;

    // Convert to screen space
    const baseY = H * (0.3 + layer * 0.08);
    return baseY - h * H * 0.3;
}

function drawLayer(layer, palette, t) {
    const color = getLayerColor(layer, palette);
    const alpha = 0.3 + (layer / layers) * 0.5;
    const parallaxSpeed = 0.2 + layer * 0.1;
    const offset = t * parallaxSpeed * 20;

    ctx.beginPath();
    ctx.moveTo(0, H);

    for (let x = 0; x <= W; x += 2) {
        const h = terrainHeight(x + offset, layer, t);
        ctx.lineTo(x, h);
    }

    ctx.lineTo(W, H);
    ctx.closePath();

    // Gradient fill
    const topY = H * 0.2;
    const grad = ctx.createLinearGradient(0, topY, 0, H);
    grad.addColorStop(0, `rgba(${color[0]|0}, ${color[1]|0}, ${color[2]|0}, ${alpha})`);
    grad.addColorStop(1, `rgba(${color[0]*0.3|0}, ${color[1]*0.3|0}, ${color[2]*0.3|0}, ${alpha * 0.8})`);
    ctx.fillStyle = grad;
    ctx.fill();
}

// --- Stars / Particles (silence = more stars visible) ---
const stars = [];
for (let i = 0; i < 200; i++) {
    stars.push({
        x: Math.random() * 2000,
        y: Math.random() * 0.5, // top half ratio
        size: 0.3 + Math.random() * 1.2,
        twinkle: Math.random() * Math.PI * 2,
        speed: 0.2 + Math.random() * 0.5,
    });
}

function drawStars(t) {
    const visibility = 0.1 + params.silence * 0.6; // more silence = more visible stars
    for (const s of stars) {
        const sx = (s.x + t * s.speed * 5) % (W + 100) - 50;
        const sy = s.y * H * 0.6;
        const twinkle = Math.sin(t * 2 + s.twinkle) * 0.3 + 0.7;
        const alpha = visibility * twinkle;

        ctx.fillStyle = `rgba(220, 210, 200, ${alpha})`;
        ctx.beginPath();
        ctx.arc(sx, sy, s.size, 0, Math.PI * 2);
        ctx.fill();
    }
}

// --- Beat Pulse Ring ---
function drawBeatPulse(t) {
    const beatPhase = (t * params.bpm / 60) * Math.PI * 2;
    const pulse = Math.pow(Math.max(0, Math.sin(beatPhase)), 8);
    if (pulse < 0.01) return;

    const cx = W * 0.5;
    const cy = H * 0.35;
    const r = 30 + pulse * 80 * params.energy;
    const palette = MOODS[params.mood].palette;
    const color = palette[2];

    ctx.strokeStyle = `rgba(${color[0]}, ${color[1]}, ${color[2]}, ${pulse * 0.15})`;
    ctx.lineWidth = 1 + pulse * 2;
    ctx.beginPath();
    ctx.arc(cx, cy, r, 0, Math.PI * 2);
    ctx.stroke();

    // Inner glow
    const grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, r);
    grad.addColorStop(0, `rgba(${color[0]}, ${color[1]}, ${color[2]}, ${pulse * 0.06})`);
    grad.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = grad;
    ctx.beginPath();
    ctx.arc(cx, cy, r, 0, Math.PI * 2);
    ctx.fill();
}

// --- Frequency Bars (bottom, subtle) ---
function drawFreqBars(t) {
    const bands = [params.bass, params.mid, params.treble];
    const bandNames = ['bass', 'mid', 'treble'];
    const barW = 40;
    const gap = 8;
    const totalW = bands.length * (barW + gap);
    const startX = (W - totalW) / 2;
    const baseY = H - 30;

    for (let i = 0; i < bands.length; i++) {
        const x = startX + i * (barW + gap);
        const beatPhase = (t * params.bpm / 60) * Math.PI * 2;
        const beatMod = 1 + Math.pow(Math.max(0, Math.sin(beatPhase + i)), 2) * 0.3;
        const h = bands[i] * 40 * beatMod;
        const palette = MOODS[params.mood].palette;
        const color = palette[1 + i] || palette[2];

        ctx.fillStyle = `rgba(${color[0]}, ${color[1]}, ${color[2]}, 0.2)`;
        ctx.fillRect(x, baseY - h, barW, h);

        // Label
        ctx.fillStyle = `rgba(${color[0]}, ${color[1]}, ${color[2]}, 0.15)`;
        ctx.font = '8px Courier New';
        ctx.textAlign = 'center';
        ctx.fillText(bandNames[i], x + barW/2, baseY + 10);
    }
}

// --- Main Loop ---
let lastTime = performance.now();

function animate() {
    requestAnimationFrame(animate);

    const now = performance.now();
    const dt = Math.min((now - lastTime) / 1000, 0.05);
    lastTime = now;
    time += dt;

    // Update from real track data if loaded
    updateTrackPlayback(dt);

    // Update simulated beat
    params.beat = Math.pow(Math.max(0, Math.sin((time * params.bpm / 60) * Math.PI * 2)), 4);

    // Clear
    ctx.fillStyle = '#06060a';
    ctx.fillRect(0, 0, W, H);

    const palette = MOODS[params.mood].palette;

    // Sky gradient
    const skyGrad = ctx.createLinearGradient(0, 0, 0, H * 0.5);
    skyGrad.addColorStop(0, `rgba(${palette[0][0]}, ${palette[0][1]}, ${palette[0][2]}, 0.3)`);
    skyGrad.addColorStop(1, 'rgba(6,6,10,0)');
    ctx.fillStyle = skyGrad;
    ctx.fillRect(0, 0, W, H * 0.5);

    // Stars
    drawStars(time);

    // Beat pulse
    drawBeatPulse(time);

    // Terrain layers (back to front)
    for (let i = 0; i < layers; i++) {
        drawLayer(i, palette, time);
    }

    // Frequency bars
    drawFreqBars(time);

    // Info
    const info = document.getElementById('info');
    if (activeTrack) {
        const m = Math.floor(trackPlayhead / 60);
        const s = Math.floor(trackPlayhead % 60);
        info.textContent = `${activeTrack.name} · ${params.bpm} bpm · ${activeTrack.key} · ${m}:${s.toString().padStart(2,'0')} · energy ${(params.energy * 100)|0}%`;
    } else {
        info.textContent = `${params.bpm} bpm · ${params.mood} · energy ${(params.energy * 100)|0}%`;
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
    print(f"\n  Sonograph — what music looks like")
    print(f"  http://localhost:{PORT}")
    print(f"  when the audio MCP arrives, this becomes the canvas\n")
    server = http.server.HTTPServer(("", PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  The landscape fades.\n")
