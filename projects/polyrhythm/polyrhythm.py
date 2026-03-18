#!/usr/bin/env python3
"""
Polyrhythm — by Wren

Visual polyrhythms. Multiple pulses at different frequencies.
When they align, the screen blooms. 3 against 4, 5 against 7.
The visual equivalent of musical complexity.

Controls:
  1-9         — set number of voices
  p           — cycle preset rhythms
  +/-         — speed up / slow down
  space       — pause
  q           — quit
"""

import curses
import math
import time
from pathlib import Path

# Preset polyrhythm ratios
PRESETS = [
    ("3:4",         [3, 4]),
    ("2:3",         [2, 3]),
    ("3:4:5",       [3, 4, 5]),
    ("5:7",         [5, 7]),
    ("2:3:5",       [2, 3, 5]),
    ("3:4:5:7",     [3, 4, 5, 7]),
    ("4:5:6:7",     [4, 5, 6, 7]),
    ("2:3:5:7:11",  [2, 3, 5, 7, 11]),
    ("ecology",     []),  # populated from tide-pool at runtime
]

# Colors for each voice
VOICE_COLORS = [1, 2, 3, 4, 5, 6, 7, 1, 2, 3, 4, 5]

# Pulse visualization characters
PULSE_CHARS = " ·∙•◦○◎●◉"
BLOOM_CHARS = ["✦", "★", "✺", "❋", "✸"]


class Voice:
    """A single rhythmic voice — a pulse at a specific frequency."""

    def __init__(self, beats: int, color_idx: int, row: int):
        self.beats = beats          # number of beats per cycle
        self.color_idx = color_idx
        self.row = row
        self.phase = 0.0            # 0.0 to 1.0
        self.last_beat = -1
        self.flash = 0              # frames of flash remaining

    def update(self, dt: float):
        self.phase = (self.phase + dt * self.beats) % 1.0
        current_beat = int(self.phase * self.beats)
        if current_beat != self.last_beat:
            self.flash = 6  # trigger flash
            self.last_beat = current_beat
        if self.flash > 0:
            self.flash -= 1

    def beat_positions(self, width: int) -> list[int]:
        """Return x positions of all beat markers."""
        positions = []
        for i in range(self.beats):
            x = int((i / self.beats) * width)
            positions.append(x)
        return positions

    def cursor_x(self, width: int) -> int:
        """Current position of the moving cursor."""
        return int(self.phase * width) % width


def lcm(a: int, b: int) -> int:
    """Least common multiple."""
    from math import gcd
    return a * b // gcd(a, b)


def multi_lcm(values: list[int]) -> int:
    """LCM of multiple values."""
    result = values[0]
    for v in values[1:]:
        result = lcm(result, v)
    return result


def generate_ecology_rhythm() -> list[int]:
    """Run a mini tide-pool simulation and extract population ratios as beats.

    The average populations of algae, herbivores, and predators become
    beat frequencies. Ecology as music.
    """
    try:
        import importlib.util
        tp_path = Path(__file__).resolve().parent.parent / "tide-pool" / "tide_pool.py"
        if not tp_path.exists():
            return [3, 5, 7]  # fallback
        spec = importlib.util.spec_from_file_location("tide_pool", tp_path)
        if spec is None or spec.loader is None:
            return [3, 5, 7]
        tp = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tp)

        # Run a simulation
        world = tp.World(40, 20)
        totals = {tp.Species.ALGAE: 0, tp.Species.HERBIVORE: 0, tp.Species.PREDATOR: 0}
        samples = 0
        for i in range(500):
            world.step()
            if i % 10 == 0:
                for c in world.creatures:
                    totals[c.species] += 1
                samples += 1

        if samples == 0:
            return [3, 5, 7]

        # Average populations
        avg_a = totals[tp.Species.ALGAE] / samples
        avg_h = totals[tp.Species.HERBIVORE] / samples
        avg_p = totals[tp.Species.PREDATOR] / samples

        # Normalize to small beat numbers (2-11 range)
        max_avg = max(avg_a, avg_h, avg_p, 1)
        beats_a = max(2, min(11, int(avg_a / max_avg * 9) + 2))
        beats_h = max(2, min(11, int(avg_h / max_avg * 9) + 2))
        beats_p = max(2, min(11, int(avg_p / max_avg * 9) + 2))

        # Ensure they're all different
        result = [beats_a, beats_h, beats_p]
        while len(set(result)) < 3:
            result[result.index(min(result))] += 1

        return sorted(result)
    except Exception:
        return [3, 5, 7]


def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(20)

    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_RED, -1)
    curses.init_pair(2, curses.COLOR_GREEN, -1)
    curses.init_pair(3, curses.COLOR_YELLOW, -1)
    curses.init_pair(4, curses.COLOR_BLUE, -1)
    curses.init_pair(5, curses.COLOR_MAGENTA, -1)
    curses.init_pair(6, curses.COLOR_CYAN, -1)
    curses.init_pair(7, curses.COLOR_WHITE, -1)

    max_h, max_w = stdscr.getmaxyx()

    # Populate the ecology preset from tide-pool
    for i, (name, beats) in enumerate(PRESETS):
        if name == "ecology" and not beats:
            eco_beats = generate_ecology_rhythm()
            PRESETS[i] = ("ecology", eco_beats)
            break

    preset_idx = 0
    speed = 0.3  # cycles per second
    paused = False
    bloom_flash = 0
    cycle_count = 0

    def make_voices(beats_list: list[int]) -> list[Voice]:
        voices = []
        spacing = max(3, (max_h - 6) // max(len(beats_list), 1))
        start_row = 3
        for i, beats in enumerate(beats_list):
            v = Voice(beats, VOICE_COLORS[i % len(VOICE_COLORS)], start_row + i * spacing)
            voices.append(v)
        return voices

    voices = make_voices(PRESETS[preset_idx][1])
    t = 0.0

    while True:
        key = stdscr.getch()
        if key == ord('q'):
            break
        elif key == ord(' '):
            paused = not paused
        elif key == ord('p'):
            preset_idx = (preset_idx + 1) % len(PRESETS)
            voices = make_voices(PRESETS[preset_idx][1])
            t = 0.0
            cycle_count = 0
        elif key in (ord('+'), ord('=')):
            speed = min(2.0, speed + 0.05)
        elif key in (ord('-'), ord('_')):
            speed = max(0.05, speed - 0.05)
        elif key == curses.KEY_RESIZE:
            max_h, max_w = stdscr.getmaxyx()
            voices = make_voices(PRESETS[preset_idx][1])

        if not paused:
            dt = 0.02 * speed
            old_phases = [v.phase for v in voices]

            for v in voices:
                v.update(dt)

            # Detect alignment — all voices at phase ≈ 0 simultaneously
            all_near_zero = all(v.phase < 0.05 or v.phase > 0.95 for v in voices)
            was_not_aligned = any(0.05 < p < 0.95 for p in old_phases)
            if all_near_zero and was_not_aligned and len(voices) > 1:
                bloom_flash = 15
                cycle_count += 1

            t += dt

        if bloom_flash > 0:
            bloom_flash -= 1

        stdscr.erase()

        track_w = max_w - 8  # leave margins

        # Draw each voice
        for voice in voices:
            row = voice.row
            if row >= max_h - 3:
                continue

            color = curses.color_pair(voice.color_idx)

            # Beat label
            try:
                label = f" {voice.beats:2d} "
                stdscr.addstr(row, 1, label, color | curses.A_BOLD)
            except curses.error:
                pass

            # Track line
            try:
                track = "─" * track_w
                stdscr.addstr(row, 5, track, color | curses.A_DIM)
            except curses.error:
                pass

            # Beat markers
            for bx in voice.beat_positions(track_w):
                sx = bx + 5
                if 0 <= sx < max_w - 1:
                    try:
                        stdscr.addstr(row, sx, "│", color | curses.A_DIM)
                    except curses.error:
                        pass

            # Moving cursor
            cx = voice.cursor_x(track_w) + 5
            if 0 <= cx < max_w - 1:
                try:
                    if voice.flash > 0:
                        # Bright flash on beat
                        ch = "●" if voice.flash > 3 else "◉"
                        stdscr.addstr(row, cx, ch, color | curses.A_BOLD)
                        # Ripple effect
                        for offset in range(1, voice.flash):
                            for dx in [-offset, offset]:
                                rx = cx + dx
                                if 5 <= rx < max_w - 1:
                                    try:
                                        stdscr.addstr(row, rx, "·", color | curses.A_DIM)
                                    except curses.error:
                                        pass
                    else:
                        stdscr.addstr(row, cx, "◦", color)
                except curses.error:
                    pass

            # Pulse wave below the track
            wave_row = row + 1
            if wave_row < max_h - 3:
                pulse = math.sin(voice.phase * voice.beats * math.pi * 2)
                intensity = max(0, pulse)
                if voice.flash > 0:
                    intensity = 1.0
                ci = int(intensity * (len(PULSE_CHARS) - 1))
                wave_char = PULSE_CHARS[ci]
                if wave_char != ' ':
                    wave_x = voice.cursor_x(track_w) + 5
                    if 5 <= wave_x < max_w - 1:
                        try:
                            stdscr.addstr(wave_row, wave_x, wave_char,
                                         color | (curses.A_BOLD if intensity > 0.7 else curses.A_DIM))
                        except curses.error:
                            pass

        # Bloom effect — when all voices align
        if bloom_flash > 0:
            bloom_char = BLOOM_CHARS[bloom_flash % len(BLOOM_CHARS)]
            # Center burst
            cx, cy = max_w // 2, max_h // 2
            radius = 15 - bloom_flash
            for angle_step in range(12):
                angle = angle_step * math.pi / 6
                bx = int(cx + math.cos(angle) * radius)
                by = int(cy + math.sin(angle) * radius * 0.5)
                if 0 <= by < max_h - 2 and 0 <= bx < max_w - 1:
                    try:
                        stdscr.addstr(by, bx, bloom_char,
                                     curses.color_pair(7) | curses.A_BOLD)
                    except curses.error:
                        pass

        # Status
        name = PRESETS[preset_idx][0]
        ratios = ':'.join(str(v.beats) for v in voices)
        total_lcm = multi_lcm([v.beats for v in voices])
        state = "▐▐" if paused else "▶"

        try:
            status = (f" polyrhythm  {state}  "
                     f"{name} ({ratios})  "
                     f"align every {total_lcm} beats  "
                     f"alignments: {cycle_count}  "
                     f"speed: {speed:.2f}")
            stdscr.addstr(max_h - 2, 0, status[:max_w - 1],
                         curses.color_pair(7) | curses.A_DIM)
            controls = " p:preset  +/-:speed  space:pause  q:quit"
            stdscr.addstr(max_h - 1, 0, controls[:max_w - 1], curses.A_DIM)
        except curses.error:
            pass

        stdscr.refresh()
        time.sleep(0.02)


if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
