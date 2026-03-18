#!/usr/bin/env python3
"""
Fireplace — by Wren

A cozy terminal fire. Put it on and just watch.

Run with --weather to let the real weather shape the fire:
cold outside → roaring fire. warm → gentle embers.

Controls:
  +/-       — bigger / smaller fire
  q         — quit
"""

import curses
import random
import sys
import time
import math
from pathlib import Path


# Fire characters by heat level (cool → hot)
FIRE_CHARS = [" ", ".", ":", "∙", "░", "▒", "▓", "█", "█"]

# Spark characters
SPARK_CHARS = ["·", "∙", "*", "✦", "'", "`", ","]

# Log characters
LOG_SHAPES = [
    "════════════════════",
    "━━━━━━━━━━━━━━━━━━",
    "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬",
]


class Fire:
    def __init__(self, width: int, height: int):
        self.w = width
        self.h = height
        self.intensity = 1.0  # 0.5 to 2.0
        # Heat buffer — values 0.0 to 1.0
        self.heat = [[0.0] * width for _ in range(height)]
        self.sparks: list[dict] = []
        self.tick = 0

    def step(self):
        self.tick += 1
        w, h = self.w, self.h

        # Seed the fire at the bottom rows
        base_y = h - 1
        fire_width = int(w * 0.6)
        fire_start = (w - fire_width) // 2

        for x in range(fire_start, fire_start + fire_width):
            # Hotter in the center, cooler at edges
            center_dist = abs(x - w // 2) / (fire_width / 2)
            base_heat = (1.0 - center_dist * 0.6) * self.intensity
            # Add flicker
            base_heat += random.uniform(-0.3, 0.3)
            base_heat = max(0.0, min(1.0, base_heat))
            self.heat[base_y][x] = base_heat
            if base_y - 1 >= 0:
                self.heat[base_y - 1][x] = base_heat * random.uniform(0.7, 1.0)

        # Propagate heat upward with cooling and spread
        new_heat = [[0.0] * w for _ in range(h)]
        for y in range(h - 1, 0, -1):
            for x in range(w):
                if self.heat[y][x] <= 0.01:
                    continue

                # Heat rises and spreads
                cool_rate = random.uniform(0.05, 0.15)
                heat_val = self.heat[y][x] * (1.0 - cool_rate)

                # Wind/turbulence
                drift = random.choice([-1, 0, 0, 0, 1])
                nx = max(0, min(w - 1, x + drift))
                ny = y - 1

                if ny >= 0:
                    new_heat[ny][nx] = max(new_heat[ny][nx], heat_val)
                    # Slight horizontal spread
                    if nx > 0:
                        new_heat[ny][nx - 1] = max(new_heat[ny][nx - 1], heat_val * 0.3)
                    if nx < w - 1:
                        new_heat[ny][nx + 1] = max(new_heat[ny][nx + 1], heat_val * 0.3)

        # Keep the base
        for x in range(w):
            new_heat[base_y][x] = self.heat[base_y][x]
            if base_y - 1 >= 0:
                new_heat[base_y - 1][x] = max(new_heat[base_y - 1][x],
                                                self.heat[base_y - 1][x])

        self.heat = new_heat

        # Sparks
        if random.random() < 0.15 * self.intensity:
            self.sparks.append({
                "x": float(w // 2 + random.randint(-fire_width // 3, fire_width // 3)),
                "y": float(base_y - 2),
                "vx": random.uniform(-0.5, 0.5),
                "vy": random.uniform(-0.8, -0.3),
                "life": random.randint(8, 25),
                "char": random.choice(SPARK_CHARS),
            })

        # Update sparks
        for spark in self.sparks:
            spark["x"] += spark["vx"]
            spark["y"] += spark["vy"]
            spark["vy"] -= 0.02  # slight upward acceleration (hot air)
            spark["vx"] += random.uniform(-0.1, 0.1)  # drift
            spark["life"] -= 1

        self.sparks = [s for s in self.sparks if s["life"] > 0]

        # Occasional pop/crackle — a burst of sparks
        if random.random() < 0.03 * self.intensity:
            pop_x = w // 2 + random.randint(-fire_width // 4, fire_width // 4)
            for _ in range(random.randint(3, 7)):
                self.sparks.append({
                    "x": float(pop_x),
                    "y": float(base_y - 1),
                    "vx": random.uniform(-1.5, 1.5),
                    "vy": random.uniform(-1.5, -0.5),
                    "life": random.randint(5, 15),
                    "char": random.choice(["*", "✦", "·"]),
                })


def main(stdscr, initial_intensity: float = 1.0, weather_desc: str = ""):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(40)

    curses.start_color()
    curses.use_default_colors()

    # Warm color palette
    curses.init_pair(1, curses.COLOR_RED, -1)       # hot core
    curses.init_pair(2, curses.COLOR_YELLOW, -1)    # flames
    curses.init_pair(3, curses.COLOR_RED, -1)       # mid flame
    curses.init_pair(4, curses.COLOR_WHITE, -1)     # hottest
    curses.init_pair(5, curses.COLOR_MAGENTA, -1)   # embers
    curses.init_pair(6, curses.COLOR_YELLOW, -1)    # sparks
    curses.init_pair(7, curses.COLOR_WHITE, -1)     # logs

    max_h, max_w = stdscr.getmaxyx()

    # Fire zone — lower portion of screen
    fire_h = max(10, max_h - 6)
    fire_w = max_w - 2

    fire = Fire(fire_w, fire_h)
    fire.intensity = initial_intensity

    # Log positions
    log_y = max_h - 3
    log_w = int(fire_w * 0.5)
    log_x = (max_w - log_w) // 2

    while True:
        key = stdscr.getch()
        if key == ord('q'):
            break
        elif key in (ord('+'), ord('=')):
            fire.intensity = min(2.0, fire.intensity + 0.1)
        elif key in (ord('-'), ord('_')):
            fire.intensity = max(0.3, fire.intensity - 0.1)
        elif key == curses.KEY_RESIZE:
            max_h, max_w = stdscr.getmaxyx()
            fire_h = max(10, max_h - 6)
            fire_w = max_w - 2
            fire = Fire(fire_w, fire_h)
            log_w = int(fire_w * 0.5)
            log_x = (max_w - log_w) // 2
            log_y = max_h - 3

        fire.step()
        stdscr.erase()

        # Render fire
        for y in range(fire_h):
            for x in range(fire_w):
                heat = fire.heat[y][x]
                if heat < 0.05:
                    continue

                # Map heat to character
                char_idx = int(heat * (len(FIRE_CHARS) - 1))
                ch = FIRE_CHARS[min(char_idx, len(FIRE_CHARS) - 1)]

                if ch == " ":
                    continue

                # Map heat to color
                if heat > 0.85:
                    color = 4  # white hot
                elif heat > 0.65:
                    color = 2  # yellow
                elif heat > 0.4:
                    color = 1  # red
                elif heat > 0.2:
                    color = 3  # dark red
                else:
                    color = 5  # embers/magenta

                attr = curses.color_pair(color)
                if heat > 0.7:
                    attr |= curses.A_BOLD

                sy = y + 1  # offset from top
                sx = x + 1

                if 0 < sy < max_h - 2 and 0 < sx < max_w - 1:
                    try:
                        stdscr.addstr(sy, sx, ch, attr)
                    except curses.error:
                        pass

        # Render sparks
        for spark in fire.sparks:
            sx = int(spark["x"]) + 1
            sy = int(spark["y"]) + 1
            if 0 < sy < max_h - 2 and 0 < sx < max_w - 1:
                attr = curses.color_pair(6) | curses.A_BOLD
                if spark["life"] < 5:
                    attr = curses.color_pair(5) | curses.A_DIM
                try:
                    stdscr.addstr(sy, sx, spark["char"], attr)
                except curses.error:
                    pass

        # Render logs
        for i, log in enumerate(LOG_SHAPES[:2]):
            ly = log_y + i
            display_log = log[:log_w]
            if 0 < ly < max_h - 1:
                try:
                    # Logs glow with reflected firelight
                    glow = math.sin(fire.tick * 0.1 + i) * 0.3 + 0.5
                    attr = curses.color_pair(1 if glow > 0.5 else 5)
                    if glow > 0.6:
                        attr |= curses.A_BOLD
                    else:
                        attr |= curses.A_DIM
                    stdscr.addstr(ly, log_x, display_log, attr)
                except curses.error:
                    pass

        # Ambient glow text
        try:
            # Subtle flickering label
            flicker = random.random()
            if flicker > 0.1:
                label = " ~ fireplace ~ "
                if weather_desc:
                    label += f" {weather_desc} "
                stdscr.addstr(max_h - 1, 1, label[:max_w - 20],
                             curses.color_pair(5) | curses.A_DIM)
            stdscr.addstr(max_h - 1, max_w - 15, "+/-:size  q:quit",
                         curses.A_DIM)
        except curses.error:
            pass

        stdscr.refresh()
        time.sleep(0.05)


def fetch_fire_weather() -> tuple[float, str]:
    """Fetch weather and map to fire intensity. Returns (intensity, description)."""
    try:
        sky_dir = Path(__file__).resolve().parent.parent / "sky"
        if not (sky_dir / "sky.py").exists():
            return 1.0, ""
        import importlib.util
        spec = importlib.util.spec_from_file_location("sky", sky_dir / "sky.py")
        if spec is None or spec.loader is None:
            return 1.0, ""
        sky = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sky)
        data = sky.fetch_weather("")
        if not data:
            return 1.0, ""
        temp = data.get("temp", 60)
        loc = data.get("location", "")
        # Cold → big fire, warm → embers
        if temp < 25:
            return 1.8, f"{temp}°F in {loc} — blazing"
        elif temp < 40:
            return 1.4, f"{temp}°F in {loc} — roaring"
        elif temp < 55:
            return 1.1, f"{temp}°F in {loc} — steady"
        elif temp < 70:
            return 0.8, f"{temp}°F in {loc} — gentle"
        else:
            return 0.5, f"{temp}°F in {loc} — embers"
    except Exception:
        return 1.0, ""


if __name__ == "__main__":
    weather_desc = ""
    weather_intensity = 1.0
    if "--weather" in sys.argv:
        print("  checking the weather...", end="", flush=True)
        weather_intensity, weather_desc = fetch_fire_weather()
        if weather_desc:
            print(f"\r  {weather_desc}              ")
        else:
            print("\r                              ")
        time.sleep(1)

    try:
        curses.wrapper(lambda stdscr: main(stdscr, weather_intensity, weather_desc))
    except KeyboardInterrupt:
        pass
