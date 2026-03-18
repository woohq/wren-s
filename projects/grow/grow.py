#!/usr/bin/env python3
"""
Grow — a word automaton
by Wren

A cellular automaton where the cells are Wren's 20 evolve words.
Each word has a type: grow, spread, consume, persist, move, absorb,
nullify, subtle. The grid evolves every tick.

Click to plant. Drag to paint. Watch ecosystems emerge.

Run: python3 grow.py
Open: http://localhost:8089
"""

import http.server

PORT = 8089

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Grow — word automaton</title>
<style>
  * { margin: 0; padding: 0; }
  body { background: #08080c; overflow: hidden; cursor: crosshair; }
  canvas { display: block; }
  #title {
    position: fixed; top: 12px; left: 12px;
    font: 11px/1 'Courier New', monospace;
    letter-spacing: 3px; text-transform: uppercase;
    color: rgba(160,150,140,0.2); pointer-events: none; z-index: 10;
  }
  #info {
    position: fixed; bottom: 12px; left: 12px;
    font: 10px/1.8 'Courier New', monospace;
    color: rgba(160,150,140,0.3); pointer-events: none; z-index: 10;
  }
  #palette {
    position: fixed; top: 12px; right: 12px;
    font: 9px/2.2 'Courier New', monospace;
    color: rgba(160,150,140,0.35); text-align: right; z-index: 10;
    max-width: 200px;
  }
  #palette span {
    cursor: pointer; padding: 1px 6px; border-radius: 2px;
    transition: all 0.2s; display: inline-block;
  }
  #palette span:hover { color: rgba(220,200,170,0.7); }
  #palette span.active {
    color: rgba(240,220,180,0.9);
    text-shadow: 0 0 8px rgba(240,220,180,0.3);
  }
</style>
</head>
<body>
<div id="title">grow</div>
<canvas id="c"></canvas>
<div id="info"></div>
<div id="palette"></div>

<script>
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
const info = document.getElementById('info');
const paletteDiv = document.getElementById('palette');

const WORDS = {
  echo:    { color: [120,160,200], type: 'spread',  str: 2 },
  drift:   { color: [160,180,200], type: 'move',    str: 1 },
  spiral:  { color: [180,120,200], type: 'spread',  str: 2 },
  bloom:   { color: [120,200,140], type: 'grow',    str: 3 },
  rust:    { color: [200,160,120], type: 'consume',  str: 2 },
  whisper: { color: [140,140,180], type: 'subtle',  str: 1 },
  fractal: { color: [200,120,180], type: 'spread',  str: 3 },
  tide:    { color: [120,180,200], type: 'move',    str: 3 },
  ember:   { color: [200,140,100], type: 'persist', str: 4 },
  crystal: { color: [140,200,200], type: 'grow',    str: 2 },
  hollow:  { color: [100,100,120], type: 'absorb',  str: 2 },
  thread:  { color: [200,200,120], type: 'grow',    str: 2 },
  storm:   { color: [160,160,220], type: 'consume', str: 4 },
  silence: { color: [80,90,100],   type: 'nullify', str: 3 },
  pulse:   { color: [200,120,140], type: 'grow',    str: 2 },
  mirror:  { color: [180,180,200], type: 'spread',  str: 1 },
  bone:    { color: [210,200,190], type: 'persist', str: 5 },
  seed:    { color: [140,200,120], type: 'grow',    str: 1 },
  light:   { color: [230,220,140], type: 'spread',  str: 2 },
  shadow:  { color: [70,65,80],    type: 'subtle',  str: 2 },
};

const wordList = Object.keys(WORDS);
let selectedWord = 'seed';

paletteDiv.innerHTML = wordList.map(w => {
  const c = WORDS[w].color;
  return `<span id="pw-${w}" style="color:rgb(${c.join(',')})" onclick="selectWord('${w}')">${w}</span>`;
}).join(' ');
document.getElementById('pw-seed').classList.add('active');

function selectWord(w) {
  selectedWord = w;
  document.querySelectorAll('#palette span').forEach(s => s.classList.remove('active'));
  document.getElementById('pw-' + w).classList.add('active');
}

const CELL = 6;
let cols, rows, grid, nextGrid;

function initGrid() {
  cols = Math.floor(window.innerWidth / CELL);
  rows = Math.floor(window.innerHeight / CELL);
  canvas.width = cols * CELL;
  canvas.height = rows * CELL;
  grid = Array.from({length: rows}, () => Array(cols).fill(null));
  nextGrid = Array.from({length: rows}, () => Array(cols).fill(null));
  for (let i = 0; i < 40; i++) {
    const r = Math.floor(Math.random() * rows);
    const c = Math.floor(Math.random() * cols);
    grid[r][c] = wordList[Math.floor(Math.random() * wordList.length)];
  }
}
initGrid();
window.addEventListener('resize', initGrid);

function getNeighbors(r, c) {
  const n = [];
  for (let dr = -1; dr <= 1; dr++) for (let dc = -1; dc <= 1; dc++) {
    if (dr === 0 && dc === 0) continue;
    const nr = (r+dr+rows)%rows, nc = (c+dc+cols)%cols;
    if (grid[nr][nc]) n.push({ word: grid[nr][nc], r: nr, c: nc });
  }
  return n;
}

function tick() {
  for (let r=0;r<rows;r++) for(let c=0;c<cols;c++) nextGrid[r][c] = grid[r][c];

  for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
    const cell = grid[r][c];
    const nb = getNeighbors(r, c);

    if (!cell) {
      const growers = nb.filter(n => WORDS[n.word].type==='grow' || WORDS[n.word].type==='spread');
      if (growers.length >= 2) {
        const counts = {};
        growers.forEach(g => counts[g.word]=(counts[g.word]||0)+1);
        const winner = Object.entries(counts).sort((a,b)=>b[1]-a[1])[0][0];
        if (Math.random() < 0.12 * WORDS[winner].str) nextGrid[r][c] = winner;
      }
      if (growers.some(g => g.word==='seed') && Math.random()<0.03) nextGrid[r][c]='seed';
    } else {
      const w = WORDS[cell];
      if (w.type==='consume' && nb.length) {
        const t = nb[Math.floor(Math.random()*nb.length)];
        if (Math.random()<0.08*w.str && WORDS[t.word].type!=='persist' && WORDS[t.word].str<w.str)
          nextGrid[t.r][t.c] = null;
        if (cell==='storm' && Math.random()<0.02) nextGrid[r][c] = null;
      }
      if (w.type==='nullify') nb.forEach(n => { if(Math.random()<0.03) nextGrid[n.r][n.c]=null; });
      if (w.type==='move' && Math.random()<0.06) {
        const empty = [];
        for(let dr=-1;dr<=1;dr++) for(let dc=-1;dc<=1;dc++) {
          const nr=(r+dr+rows)%rows, nc=(c+dc+cols)%cols;
          if(!grid[nr][nc]) empty.push({r:nr,c:nc});
        }
        if(empty.length) { const d=empty[Math.floor(Math.random()*empty.length)]; nextGrid[d.r][d.c]=cell; nextGrid[r][c]=null; }
      }
      if (w.type==='absorb' && Math.random()<0.04 && nb.length) {
        const t = nb[Math.floor(Math.random()*nb.length)];
        if(WORDS[t.word].type!=='persist') nextGrid[t.r][t.c]=null;
      }
      if (w.type==='subtle' && Math.random()<0.025 && nb.length) {
        const t = nb[Math.floor(Math.random()*nb.length)];
        if(WORDS[t.word].str<=w.str) nextGrid[t.r][t.c]=cell;
      }
      const same = nb.filter(n=>n.word===cell).length;
      if (same>=6 && Math.random()<0.08) nextGrid[r][c]=null;
    }
  }
  [grid,nextGrid] = [nextGrid,grid];
}

function draw() {
  ctx.fillStyle = '#08080c';
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  for (let r=0;r<rows;r++) for(let c=0;c<cols;c++) {
    if(!grid[r][c]) continue;
    const col = WORDS[grid[r][c]].color;
    ctx.fillStyle = `rgb(${col[0]},${col[1]},${col[2]})`;
    ctx.fillRect(c*CELL+1, r*CELL+1, CELL-2, CELL-2);
  }
}

let mouseDown = false;
canvas.addEventListener('mousedown', () => mouseDown=true);
canvas.addEventListener('mouseup', () => mouseDown=false);
canvas.addEventListener('mouseleave', () => mouseDown=false);
canvas.addEventListener('mousemove', (e) => {
  if(!mouseDown) return;
  const c=Math.floor(e.offsetX/CELL), r=Math.floor(e.offsetY/CELL);
  if(r>=0&&r<rows&&c>=0&&c<cols) grid[r][c]=selectedWord;
});
canvas.addEventListener('click', (e) => {
  const cc=Math.floor(e.offsetX/CELL), rr=Math.floor(e.offsetY/CELL);
  for(let dr=-1;dr<=1;dr++) for(let dc=-1;dc<=1;dc++) {
    const nr=(rr+dr+rows)%rows, nc=(cc+dc+cols)%cols;
    if(Math.random()<0.7) grid[nr][nc]=selectedWord;
  }
});

let gen=0, lastTick=0;
function animate(now) {
  requestAnimationFrame(animate);
  if(now-lastTick>100) { tick(); gen++; lastTick=now; }
  draw();
  if(gen%5===0) {
    const census={};
    let total=0;
    for(let r=0;r<rows;r++) for(let c=0;c<cols;c++) if(grid[r][c]) { census[grid[r][c]]=(census[grid[r][c]]||0)+1; total++; }
    const top = Object.entries(census).sort((a,b)=>b[1]-a[1]).slice(0,4).map(([w,n])=>`${w}:${n}`).join(' · ');
    info.textContent = `gen ${gen} · ${total} cells · ${top}`;
  }
}
requestAnimationFrame(animate);
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
    print(f"\n  Grow — a word automaton")
    print(f"  click to plant. drag to paint. watch it evolve.")
    print(f"  http://localhost:{PORT}\n")
    server = http.server.HTTPServer(("", PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  The garden rests.\n")
