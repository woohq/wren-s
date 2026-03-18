#!/usr/bin/env python3
"""
Reaction-Diffusion — a Gray-Scott model explorer by Wren

Two chemicals diffuse across a grid. One feeds, one kills. From these
two simple rules: coral, fingerprints, mitosis, spots, waves. Turing
figured this out in 1952. The math is almost trivially simple, but the
output looks alive.

Rendered in braille characters for high resolution.

Controls:
  arrow keys    — adjust feed (←→) and kill (↑↓) rates
  space         — pause / resume
  s             — seed a blob of chemical B at random location
  S             — clear and re-seed
  p             — cycle through preset parameter sets
  1-5           — simulation speed
  c             — cycle color palette
  q / Ctrl-C    — quit
"""

import curses
import random
import array

# Braille encoding (same as fractal explorer)
BRAILLE_BASE = 0x2800
BRAILLE_MAP = [
    [0x01, 0x08],
    [0x02, 0x10],
    [0x04, 0x20],
    [0x40, 0x80],
]

# Presets: name, feed_rate, kill_rate, description
PRESETS = [
    ("coral",       0.0545, 0.062,  "branching coral growth"),
    ("mitosis",     0.0367, 0.0649, "cells that divide"),
    ("spots",       0.030,  0.062,  "stable spotted pattern"),
    ("stripes",     0.022,  0.051,  "labyrinthine stripes"),
    ("waves",       0.014,  0.045,  "pulsing wave fronts"),
    ("worms",       0.078,  0.061,  "writhing worm-like forms"),
    ("bubbles",     0.012,  0.050,  "soliton-like bubbles"),
    ("maze",        0.029,  0.057,  "dense maze pattern"),
    ("fingerprint", 0.037,  0.060,  "whorl patterns"),
    ("unstable",    0.026,  0.052,  "chaotic, always shifting"),
]

PALETTE_NAMES = ["chemical", "heat", "ocean", "bone"]


class ReactionDiffusion:
    """Gray-Scott reaction-diffusion on a 2D grid."""

    def __init__(self, width: int, height: int, feed: float, kill: float):
        self.w = width
        self.h = height
        self.feed = feed
        self.kill = kill
        self.da = 1.0    # diffusion rate of A
        self.db = 0.5    # diffusion rate of B
        self.dt = 1.0    # timestep

        n = width * height
        # Use arrays for performance — flat 2D grid
        self.a = array.array('f', [1.0] * n)
        self.b = array.array('f', [0.0] * n)
        self.a_next = array.array('f', [0.0] * n)
        self.b_next = array.array('f', [0.0] * n)

    def seed_center(self):
        """Drop a blob of B in the center."""
        cx, cy = self.w // 2, self.h // 2
        self._seed_at(cx, cy, 12)

    def seed_random(self):
        """Drop a blob of B at a random location."""
        x = random.randint(15, self.w - 15)
        y = random.randint(15, self.h - 15)
        self._seed_at(x, y, random.randint(6, 14))

    def _seed_at(self, cx: int, cy: int, radius: int):
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if dx * dx + dy * dy <= radius * radius:
                    x = (cx + dx) % self.w
                    y = (cy + dy) % self.h
                    idx = y * self.w + x
                    self.b[idx] = 1.0
                    # Add a tiny bit of noise for symmetry breaking
                    self.a[idx] = 0.5 + random.uniform(-0.01, 0.01)

    def seed_scattered(self, n: int = 5):
        """Seed multiple random blobs."""
        for _ in range(n):
            self.seed_random()

    def reset(self):
        """Clear the grid."""
        n = self.w * self.h
        for i in range(n):
            self.a[i] = 1.0
            self.b[i] = 0.0

    def step(self):
        """Advance one timestep using the Gray-Scott equations."""
        w, h = self.w, self.h
        a, b = self.a, self.b
        a_next, b_next = self.a_next, self.b_next
        f, k = self.feed, self.kill
        da, db, dt = self.da, self.db, self.dt

        for y in range(h):
            ym = (y - 1) % h
            yp = (y + 1) % h
            y_off = y * w
            ym_off = ym * w
            yp_off = yp * w

            for x in range(w):
                xm = (x - 1) % w
                xp = (x + 1) % w
                idx = y_off + x

                av = a[idx]
                bv = b[idx]

                # Laplacian (5-point stencil with diagonal weights)
                # Weights: center=-1, adjacent=0.2, diagonal=0.05
                lap_a = (
                    a[ym_off + x] * 0.2 +
                    a[yp_off + x] * 0.2 +
                    a[y_off + xm] * 0.2 +
                    a[y_off + xp] * 0.2 +
                    a[ym_off + xm] * 0.05 +
                    a[ym_off + xp] * 0.05 +
                    a[yp_off + xm] * 0.05 +
                    a[yp_off + xp] * 0.05 +
                    av * -1.0
                )
                lap_b = (
                    b[ym_off + x] * 0.2 +
                    b[yp_off + x] * 0.2 +
                    b[y_off + xm] * 0.2 +
                    b[y_off + xp] * 0.2 +
                    b[ym_off + xm] * 0.05 +
                    b[ym_off + xp] * 0.05 +
                    b[yp_off + xm] * 0.05 +
                    b[yp_off + xp] * 0.05 +
                    bv * -1.0
                )

                # Reaction: A + 2B → 3B
                abb = av * bv * bv

                a_next[idx] = av + (da * lap_a - abb + f * (1.0 - av)) * dt
                b_next[idx] = bv + (db * lap_b + abb - (k + f) * bv) * dt

                # Clamp
                if a_next[idx] < 0.0:
                    a_next[idx] = 0.0
                elif a_next[idx] > 1.0:
                    a_next[idx] = 1.0
                if b_next[idx] < 0.0:
                    b_next[idx] = 0.0
                elif b_next[idx] > 1.0:
                    b_next[idx] = 1.0

        # Swap buffers
        self.a, self.a_next = self.a_next, self.a
        self.b, self.b_next = self.b_next, self.b


def init_colors(palette_idx: int):
    curses.start_color()
    curses.use_default_colors()
    schemes = [
        # chemical: greens and cyans
        [(curses.COLOR_GREEN, -1), (curses.COLOR_CYAN, -1),
         (curses.COLOR_WHITE, -1), (curses.COLOR_YELLOW, -1),
         (curses.COLOR_BLUE, -1), (curses.COLOR_MAGENTA, -1)],
        # heat: reds and yellows
        [(curses.COLOR_RED, -1), (curses.COLOR_YELLOW, -1),
         (curses.COLOR_WHITE, -1), (curses.COLOR_MAGENTA, -1),
         (curses.COLOR_RED, -1), (curses.COLOR_YELLOW, -1)],
        # ocean: blues
        [(curses.COLOR_BLUE, -1), (curses.COLOR_CYAN, -1),
         (curses.COLOR_WHITE, -1), (curses.COLOR_GREEN, -1),
         (curses.COLOR_BLUE, -1), (curses.COLOR_CYAN, -1)],
        # bone: whites and grays
        [(curses.COLOR_WHITE, -1), (curses.COLOR_WHITE, -1),
         (curses.COLOR_CYAN, -1), (curses.COLOR_BLUE, -1),
         (curses.COLOR_WHITE, -1), (curses.COLOR_WHITE, -1)],
    ]
    scheme = schemes[palette_idx % len(schemes)]
    for i, (fg, bg) in enumerate(scheme):
        curses.init_pair(i + 1, fg, bg)


def render_braille(stdscr, rd: ReactionDiffusion, render_w: int, render_h: int,
                   palette_idx: int):
    """Render the B chemical concentration using braille."""
    palettes = [
        # Each maps intensity bands to color pair indices
        [1, 1, 2, 2, 3, 4],
        [1, 1, 2, 2, 3, 3],
        [1, 1, 2, 2, 3, 4],
        [1, 1, 2, 3, 4, 5],
    ]
    pal = palettes[palette_idx % len(palettes)]

    # Braille: each cell = 2 cols x 4 rows of samples
    # We sample from the rd grid, which may be larger than render area
    for row in range(render_h):
        for col in range(render_w):
            braille_bits = 0
            max_b = 0.0

            for sub_y in range(4):
                for sub_x in range(2):
                    gx = col * 2 + sub_x
                    gy = row * 4 + sub_y
                    if gx < rd.w and gy < rd.h:
                        bv = rd.b[gy * rd.w + gx]
                        if bv > 0.1:
                            braille_bits |= BRAILLE_MAP[sub_y][sub_x]
                        if bv > max_b:
                            max_b = bv

            if braille_bits == 0:
                continue

            ch = chr(BRAILLE_BASE | braille_bits)
            band = min(len(pal) - 1, int(max_b * len(pal)))
            color_pair = pal[band]
            attr = curses.color_pair(color_pair)
            if max_b > 0.5:
                attr |= curses.A_BOLD

            try:
                stdscr.addstr(row, col, ch, attr)
            except curses.error:
                pass


def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(10)

    max_h, max_w = stdscr.getmaxyx()
    palette_idx = 0
    init_colors(palette_idx)

    render_h = max_h - 2  # leave room for status
    render_w = max_w - 1

    # Grid size: braille gives 2x horizontal, 4x vertical resolution
    grid_w = render_w * 2
    grid_h = render_h * 4

    preset_idx = 0
    f, k = PRESETS[preset_idx][1], PRESETS[preset_idx][2]

    rd = ReactionDiffusion(grid_w, grid_h, f, k)
    rd.seed_center()
    rd.seed_scattered(3)

    paused = False
    speed = 3  # steps per frame
    tick = 0

    while True:
        key = stdscr.getch()
        if key == ord('q'):
            break
        elif key == ord(' '):
            paused = not paused
        elif key == curses.KEY_RIGHT:
            rd.feed = min(0.1, rd.feed + 0.001)
        elif key == curses.KEY_LEFT:
            rd.feed = max(0.0, rd.feed - 0.001)
        elif key == curses.KEY_UP:
            rd.kill = min(0.1, rd.kill + 0.001)
        elif key == curses.KEY_DOWN:
            rd.kill = max(0.0, rd.kill - 0.001)
        elif key == ord('s'):
            rd.seed_random()
        elif key == ord('S'):
            rd.reset()
            rd.seed_center()
            rd.seed_scattered(3)
        elif key == ord('p'):
            preset_idx = (preset_idx + 1) % len(PRESETS)
            _, f, k, _ = PRESETS[preset_idx]
            rd.feed = f
            rd.kill = k
            rd.reset()
            rd.seed_center()
            rd.seed_scattered(3)
        elif key == ord('c'):
            palette_idx = (palette_idx + 1) % len(PALETTE_NAMES)
            init_colors(palette_idx)
        elif key in (ord('1'), ord('2'), ord('3'), ord('4'), ord('5')):
            speed = key - ord('0')
        elif key == curses.KEY_RESIZE:
            max_h, max_w = stdscr.getmaxyx()
            render_h = max_h - 2
            render_w = max_w - 1
            grid_w = render_w * 2
            grid_h = render_h * 4
            rd = ReactionDiffusion(grid_w, grid_h, rd.feed, rd.kill)
            rd.seed_center()
            rd.seed_scattered(3)

        if not paused:
            for _ in range(speed):
                rd.step()
                tick += 1

        stdscr.erase()
        render_braille(stdscr, rd, render_w, render_h, palette_idx)

        # Status bar
        preset_name = PRESETS[preset_idx][0]
        preset_desc = PRESETS[preset_idx][3]
        state = "▐▐" if paused else f"▶x{speed}"
        try:
            status = (f" reaction-diffusion  "
                     f"f:{rd.feed:.4f} k:{rd.kill:.4f}  "
                     f"preset:{preset_name}  "
                     f"tick:{tick}  "
                     f"{state}")
            stdscr.addstr(max_h - 2, 0, status[:max_w - 1],
                         curses.color_pair(1) | curses.A_DIM)
            controls = f" ←→:feed ↑↓:kill  p:preset  s:seed  S:reset  c:color  1-5:speed  q:quit  │ {preset_desc}"
            stdscr.addstr(max_h - 1, 0, controls[:max_w - 1], curses.A_DIM)
        except curses.error:
            pass

        stdscr.refresh()


if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
