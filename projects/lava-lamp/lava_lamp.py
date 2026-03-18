#!/usr/bin/env python3
"""
Lava Lamp — a terminal metaball visualizer by Wren

Soft blobs of color drift, merge, and split in a hypnotic display.
Uses metaball field calculations to produce smooth, organic shapes
rendered with unicode density characters and terminal colors.

Controls:
  q / Ctrl-C  — quit
  space       — pause / resume
  a           — add a blob
  d           — remove a blob
  c           — cycle color scheme
  r           — reset
"""

import curses
import random
import time
import math

# Density ramps — characters ordered by visual weight
RAMPS = [
    " ·∙•●█",           # dots
    " ░▒▓█▓▒",          # blocks
    " .:-=+*#%@",       # ascii classic
    " ⠁⠃⠇⡇⣇⣧⣷⣿",      # braille
]

# Color schemes: each is a list of curses color pairs to use
SCHEME_NAMES = ["aurora", "ember", "ocean", "vapor"]


class Blob:
    def __init__(self, x: float, y: float, radius: float):
        self.x = x
        self.y = y
        self.radius = radius
        self.vx = random.uniform(-0.3, 0.3)
        self.vy = random.uniform(-0.15, 0.15)
        # Gentle oscillation
        self.phase = random.uniform(0, math.tau)
        self.freq = random.uniform(0.01, 0.03)
        self.amp_x = random.uniform(0.05, 0.2)
        self.amp_y = random.uniform(0.02, 0.1)

    def update(self, width: float, height: float, t: float):
        # Base velocity + sinusoidal drift
        self.x += self.vx + math.sin(self.phase + t * self.freq) * self.amp_x
        self.y += self.vy + math.cos(self.phase + t * self.freq * 0.7) * self.amp_y

        # Soft bounce off walls
        margin = self.radius * 0.5
        if self.x < margin:
            self.vx = abs(self.vx) * 0.8
            self.x = margin
        elif self.x > width - margin:
            self.vx = -abs(self.vx) * 0.8
            self.x = width - margin

        if self.y < margin:
            self.vy = abs(self.vy) * 0.8
            self.y = margin
        elif self.y > height - margin:
            self.vy = -abs(self.vy) * 0.8
            self.y = height - margin

        # Gravity-like pull toward center (lava lamp convection)
        cx, cy = width / 2, height / 2
        self.vx += (cx - self.x) * 0.0003
        self.vy += (cy - self.y) * 0.0003

        # Speed limit
        speed = math.sqrt(self.vx ** 2 + self.vy ** 2)
        max_speed = 0.4
        if speed > max_speed:
            self.vx = self.vx / speed * max_speed
            self.vy = self.vy / speed * max_speed

        # Gentle radius pulsing
        self.radius += math.sin(t * 0.05 + self.phase) * 0.02


def field_value(x: float, y: float, blobs: list[Blob]) -> float:
    """Calculate metaball field strength at a point."""
    total = 0.0
    for blob in blobs:
        dx = x - blob.x
        dy = (y - blob.y) * 2.0  # compensate for terminal char aspect ratio
        dist_sq = dx * dx + dy * dy
        if dist_sq < 0.01:
            dist_sq = 0.01
        total += (blob.radius * blob.radius) / dist_sq
    return total


def nearest_blob_idx(x: float, y: float, blobs: list[Blob]) -> int:
    """Return index of the nearest blob (for coloring)."""
    best = 0
    best_contrib = 0.0
    for i, blob in enumerate(blobs):
        dx = x - blob.x
        dy = (y - blob.y) * 2.0
        dist_sq = dx * dx + dy * dy
        if dist_sq < 0.01:
            dist_sq = 0.01
        contrib = (blob.radius * blob.radius) / dist_sq
        if contrib > best_contrib:
            best_contrib = contrib
            best = i
    return best


def init_colors(scheme_idx: int):
    """Set up color pairs for the current scheme."""
    curses.start_color()
    curses.use_default_colors()

    schemes = [
        # aurora: greens, cyans, magentas
        [
            (curses.COLOR_GREEN, -1),
            (curses.COLOR_CYAN, -1),
            (curses.COLOR_MAGENTA, -1),
            (curses.COLOR_BLUE, -1),
            (curses.COLOR_YELLOW, -1),
            (curses.COLOR_WHITE, -1),
        ],
        # ember: reds, yellows, whites
        [
            (curses.COLOR_RED, -1),
            (curses.COLOR_YELLOW, -1),
            (curses.COLOR_WHITE, -1),
            (curses.COLOR_RED, -1),
            (curses.COLOR_YELLOW, -1),
            (curses.COLOR_MAGENTA, -1),
        ],
        # ocean: blues, cyans
        [
            (curses.COLOR_BLUE, -1),
            (curses.COLOR_CYAN, -1),
            (curses.COLOR_WHITE, -1),
            (curses.COLOR_BLUE, -1),
            (curses.COLOR_CYAN, -1),
            (curses.COLOR_GREEN, -1),
        ],
        # vapor: magentas, cyans, pinks
        [
            (curses.COLOR_MAGENTA, -1),
            (curses.COLOR_CYAN, -1),
            (curses.COLOR_BLUE, -1),
            (curses.COLOR_MAGENTA, -1),
            (curses.COLOR_WHITE, -1),
            (curses.COLOR_CYAN, -1),
        ],
    ]

    scheme = schemes[scheme_idx % len(schemes)]
    for i, (fg, bg) in enumerate(scheme):
        curses.init_pair(i + 1, fg, bg)


def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(30)

    max_h, max_w = stdscr.getmaxyx()

    scheme_idx = 0
    ramp_idx = 0
    init_colors(scheme_idx)

    # Create initial blobs
    blobs: list[Blob] = []
    n_blobs = random.randint(5, 8)
    for _ in range(n_blobs):
        blobs.append(Blob(
            x=random.uniform(5, max_w - 5),
            y=random.uniform(3, max_h - 3),
            radius=random.uniform(3, 6),
        ))

    paused = False
    t = 0.0

    while True:
        key = stdscr.getch()
        if key == ord('q'):
            break
        elif key == ord(' '):
            paused = not paused
        elif key == ord('a'):
            blobs.append(Blob(
                x=random.uniform(5, max_w - 5),
                y=random.uniform(3, max_h - 3),
                radius=random.uniform(3, 6),
            ))
        elif key == ord('d') and len(blobs) > 1:
            blobs.pop(random.randint(0, len(blobs) - 1))
        elif key == ord('c'):
            scheme_idx = (scheme_idx + 1) % len(SCHEME_NAMES)
            init_colors(scheme_idx)
        elif key == ord('t'):
            ramp_idx = (ramp_idx + 1) % len(RAMPS)
        elif key == ord('r'):
            blobs.clear()
            for _ in range(random.randint(5, 8)):
                blobs.append(Blob(
                    x=random.uniform(5, max_w - 5),
                    y=random.uniform(3, max_h - 3),
                    radius=random.uniform(3, 6),
                ))
        elif key == curses.KEY_RESIZE:
            max_h, max_w = stdscr.getmaxyx()

        if not paused:
            t += 1.0
            for blob in blobs:
                blob.update(float(max_w), float(max_h), t)

        ramp = RAMPS[ramp_idx]
        ramp_len = len(ramp)

        stdscr.erase()

        # Render the metaball field — sample every cell
        # Use step=2 for columns to improve performance (terminal chars are ~2:1)
        for row in range(max_h - 1):
            for col in range(max_w - 1):
                val = field_value(float(col), float(row), blobs)

                if val < 0.15:
                    continue  # empty space, skip for speed

                # Map field value to density character
                normalized = min(1.0, val / 2.5)
                char_idx = int(normalized * (ramp_len - 1))
                ch = ramp[char_idx]

                if ch == ' ':
                    continue

                # Color based on nearest blob
                blob_idx = nearest_blob_idx(float(col), float(row), blobs)
                color_pair = (blob_idx % 6) + 1

                # Brighter at higher density
                attr = curses.color_pair(color_pair)
                if normalized > 0.7:
                    attr |= curses.A_BOLD

                try:
                    stdscr.addstr(row, col, ch, attr)
                except curses.error:
                    pass

        # UI overlay
        try:
            status = f" ~ lava lamp ~  scheme:{SCHEME_NAMES[scheme_idx]}  blobs:{len(blobs)}  "
            if paused:
                status += "▐▐ paused"
            stdscr.addstr(max_h - 1, 0, status,
                         curses.color_pair(1) | curses.A_DIM)
            controls = "  q:quit space:pause a/d:±blob c:color t:texture r:reset"
            remaining = max_w - len(status) - 1
            if remaining > 10:
                stdscr.addstr(controls[:remaining], curses.A_DIM)
        except curses.error:
            pass

        stdscr.refresh()
        time.sleep(0.04)


if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
