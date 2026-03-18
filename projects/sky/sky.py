#!/usr/bin/env python3
"""
sky — by Wren

Fetches the current weather and renders it as a terminal scene.
The real world, filtered through text.

Usage:
  python3 sky.py              # auto-detect location
  python3 sky.py "Tokyo"      # specific location
  python3 sky.py --animate    # watch the sky for a while
"""

import curses
import random
import time
import subprocess
import sys
import math


def fetch_weather(location: str = "") -> dict | None:
    """Fetch weather from wttr.in."""
    try:
        url = f"wttr.in/{location}?format=%C|%t|%w|%h|%p|%l"
        result = subprocess.run(
            ["curl", "-s", "-m", "5", url],
            capture_output=True, text=True, timeout=10
        )
        parts = result.stdout.strip().split("|")
        if len(parts) < 5:
            return None

        condition = parts[0].strip().lower()
        temp_str = parts[1].strip().replace("°F", "").replace("°C", "").replace("+", "")
        wind_str = parts[2].strip()
        humidity = parts[3].strip().replace("%", "")
        precip = parts[4].strip().replace("mm", "")
        loc = parts[5].strip() if len(parts) > 5 else location or "here"

        # Parse wind speed
        wind_speed = 0
        for ch in wind_str:
            if ch.isdigit():
                wind_speed = wind_speed * 10 + int(ch)

        return {
            "condition": condition,
            "temp": float(temp_str) if temp_str.replace("-", "").replace(".", "").isdigit() else 0,
            "wind": wind_speed,
            "humidity": int(humidity) if humidity.isdigit() else 50,
            "precip": float(precip) if precip.replace(".", "").isdigit() else 0,
            "location": loc,
            "raw": result.stdout.strip(),
        }
    except Exception:
        return None


def classify_sky(weather: dict) -> str:
    """Map weather condition to a sky type."""
    c = weather["condition"]
    if any(w in c for w in ("rain", "drizzle", "shower")):
        return "rain"
    elif any(w in c for w in ("snow", "blizzard", "sleet", "ice")):
        return "snow"
    elif any(w in c for w in ("thunder", "lightning")):
        return "storm"
    elif any(w in c for w in ("fog", "mist", "haze")):
        return "fog"
    elif any(w in c for w in ("cloud", "overcast")):
        return "clouds"
    elif any(w in c for w in ("partly", "scattered")):
        return "partly"
    elif any(w in c for w in ("clear", "sunny")):
        # Check time — clear at night means stars
        hour = time.localtime().tm_hour
        if hour >= 20 or hour < 6:
            return "stars"
        return "clear"
    else:
        return "clear"


# ── particle systems ────────────────────────────────────────────

class Particle:
    def __init__(self, x: float, y: float, vx: float = 0, vy: float = 0,
                 char: str = ".", life: float = 100):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.char = char
        self.life = life
        self.age = 0
        self.twinkle_phase = 0.0
        self.twinkle_speed = 0.1


def make_rain(width: int, height: int, intensity: float) -> list[Particle]:
    particles = []
    n = int(width * intensity * 0.3)
    for _ in range(n):
        p = Particle(
            x=random.uniform(0, width),
            y=random.uniform(-height, 0),
            vx=random.uniform(-0.5, 0.5),
            vy=random.uniform(1.0, 2.5),
            char=random.choice(["│", "╎", "┊", "·", "|"]),
            life=height * 2,
        )
        particles.append(p)
    return particles


def make_snow(width: int, height: int, intensity: float) -> list[Particle]:
    particles = []
    n = int(width * intensity * 0.2)
    for _ in range(n):
        p = Particle(
            x=random.uniform(0, width),
            y=random.uniform(-height, 0),
            vx=random.uniform(-0.3, 0.3),
            vy=random.uniform(0.2, 0.6),
            char=random.choice(["*", "·", "∙", "•", "❄", "✦", "."]),
            life=height * 4,
        )
        particles.append(p)
    return particles


def make_stars(width: int, height: int) -> list[Particle]:
    particles = []
    n = int(width * height * 0.02)
    for _ in range(n):
        p = Particle(
            x=random.uniform(0, width),
            y=random.uniform(0, height),
            char=random.choice([".", "·", "∙", "✦", "★", "*", "˙", "⋅"]),
            life=999,
        )
        # Stars twinkle
        p.twinkle_phase = random.uniform(0, math.tau)
        p.twinkle_speed = random.uniform(0.05, 0.2)
        particles.append(p)
    return particles


def make_fog(width: int, height: int, density: float) -> list[Particle]:
    particles = []
    n = int(width * height * density * 0.03)
    for _ in range(n):
        p = Particle(
            x=random.uniform(0, width),
            y=random.uniform(height * 0.3, height),
            vx=random.uniform(0.1, 0.4),
            vy=random.uniform(-0.05, 0.05),
            char=random.choice(["░", "▒", "·", ".", " ", "~"]),
            life=999,
        )
        particles.append(p)
    return particles


def make_clouds(width: int, height: int, n_clouds: int = 5) -> list[dict]:
    clouds = []
    shapes = [
        ["  ._===_. ", " /       \\", "|         |", " \\_______/"],
        [" .---.", "/     \\", "\\_____/"],
        ["   ___", " _/   \\_", "/       \\", "\\_______/"],
        ["  ~-~", " /   \\", "~-----~"],
    ]
    for _ in range(n_clouds):
        clouds.append({
            "x": random.uniform(0, width),
            "y": random.randint(1, max(2, height // 3)),
            "vx": random.uniform(0.05, 0.3),
            "shape": random.choice(shapes),
        })
    return clouds


# ── rendering ───────────────────────────────────────────────────

def render_sky(stdscr, weather: dict, animate: bool):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(50)

    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_CYAN, -1)     # rain/snow
    curses.init_pair(2, curses.COLOR_YELLOW, -1)    # sun/stars
    curses.init_pair(3, curses.COLOR_WHITE, -1)     # clouds/fog
    curses.init_pair(4, curses.COLOR_BLUE, -1)      # sky
    curses.init_pair(5, curses.COLOR_MAGENTA, -1)   # storm
    curses.init_pair(6, curses.COLOR_GREEN, -1)     # ground

    max_h, max_w = stdscr.getmaxyx()
    sky_type = classify_sky(weather)
    render_h = max_h - 3  # leave room for info

    # Initialize particles based on weather
    particles: list[Particle] = []
    clouds: list[dict] = []
    ground_line = render_h - 1

    if sky_type == "rain":
        particles = make_rain(max_w, render_h, weather["precip"] + 1)
    elif sky_type == "snow":
        particles = make_snow(max_w, render_h, weather["precip"] + 1)
    elif sky_type == "stars":
        particles = make_stars(max_w, render_h)
    elif sky_type == "fog":
        particles = make_fog(max_w, render_h, weather["humidity"] / 100)
    elif sky_type in ("clouds", "partly"):
        clouds = make_clouds(max_w, render_h)
        if sky_type == "partly":
            particles = make_stars(max_w, render_h)  # stars peeking through

    if sky_type in ("storm",):
        particles = make_rain(max_w, render_h, 3.0)
        clouds = make_clouds(max_w, render_h, 8)

    tick = 0
    lightning_flash = 0
    single_frame = not animate

    while True:
        key = stdscr.getch()
        if key == ord('q') or (single_frame and tick > 0):
            break

        tick += 1
        stdscr.erase()

        # ── ground ──
        ground_chars = "___,._.-_.__.___"
        for x in range(max_w - 1):
            gc = ground_chars[(x + tick // 10) % len(ground_chars)]
            try:
                stdscr.addch(ground_line, x, gc, curses.color_pair(6) | curses.A_DIM)
            except curses.error:
                pass

        # ── sun (for clear/partly) ──
        if sky_type in ("clear", "partly"):
            sun_x = max_w // 4
            sun_y = render_h // 5
            sun_rays = [
                "    \\   |   /",
                "  --- ☀ ---",
                "    /   |   \\",
            ]
            for i, ray in enumerate(sun_rays):
                try:
                    sx = sun_x - len(ray) // 2
                    if 0 <= sun_y - 1 + i < render_h:
                        stdscr.addstr(sun_y - 1 + i, max(0, sx), ray,
                                     curses.color_pair(2) | curses.A_BOLD)
                except curses.error:
                    pass

        # ── clouds ──
        for cloud in clouds:
            cloud["x"] += cloud["vx"]
            if cloud["x"] > max_w + 20:
                cloud["x"] = -20

            for i, line in enumerate(cloud["shape"]):
                cy = int(cloud["y"]) + i
                cx = int(cloud["x"])
                if 0 <= cy < render_h:
                    try:
                        stdscr.addstr(cy, max(0, cx), line[:max_w - max(0, cx) - 1],
                                     curses.color_pair(3) | curses.A_DIM)
                    except curses.error:
                        pass

        # ── particles ──
        wind_factor = weather["wind"] * 0.05
        for p in particles:
            p.x += p.vx + wind_factor
            p.y += p.vy
            p.age += 1

            # Wrap/respawn
            if p.y > ground_line:
                if sky_type in ("rain", "storm"):
                    p.y = random.uniform(-5, 0)
                    p.x = random.uniform(0, max_w)
                elif sky_type == "snow":
                    p.y = random.uniform(-5, 0)
                    p.x = random.uniform(0, max_w)
                else:
                    continue
            if p.x < 0:
                p.x += max_w
            if p.x >= max_w:
                p.x -= max_w

            ix, iy = int(p.x), int(p.y)
            if 0 <= iy < ground_line and 0 <= ix < max_w - 1:
                attr = curses.color_pair(1)

                if sky_type == "stars":
                    # Twinkling
                    brightness = math.sin(tick * p.twinkle_speed + p.twinkle_phase)
                    if brightness > 0.3:
                        attr = curses.color_pair(2) | curses.A_BOLD
                    elif brightness > -0.2:
                        attr = curses.color_pair(2)
                    else:
                        attr = curses.color_pair(4) | curses.A_DIM
                elif sky_type in ("fog",):
                    attr = curses.color_pair(3) | curses.A_DIM
                elif sky_type == "snow":
                    attr = curses.color_pair(3) | curses.A_BOLD
                elif sky_type == "storm":
                    attr = curses.color_pair(5)

                try:
                    stdscr.addstr(iy, ix, p.char, attr)
                except curses.error:
                    pass

        # ── lightning ──
        if sky_type == "storm" and random.random() < 0.02:
            lightning_flash = 3
        if lightning_flash > 0:
            bolt_x = random.randint(max_w // 4, 3 * max_w // 4)
            y = 0
            for _ in range(render_h):
                bolt_x += random.choice([-1, 0, 0, 1])
                y += 1
                if 0 <= y < ground_line and 0 <= bolt_x < max_w - 1:
                    try:
                        ch = random.choice(["╲", "│", "╱", "⚡"])
                        stdscr.addstr(y, bolt_x, ch,
                                     curses.color_pair(2) | curses.A_BOLD)
                    except curses.error:
                        pass
            lightning_flash -= 1

        # ── info bar ──
        try:
            temp = weather["temp"]
            temp_color = 2 if temp > 75 else 1 if temp < 40 else 3

            stdscr.addstr(max_h - 3, 1,
                         f" {weather['location']}",
                         curses.color_pair(3) | curses.A_BOLD)
            stdscr.addstr(max_h - 2, 1,
                         f" {weather['condition']}  {temp}°F  "
                         f"wind {weather['wind']}mph  "
                         f"humidity {weather['humidity']}%",
                         curses.color_pair(temp_color) | curses.A_DIM)
            if animate:
                stdscr.addstr(max_h - 1, 1, " q: quit",
                             curses.A_DIM)
            else:
                stdscr.addstr(max_h - 1, 1,
                             " run with --animate for a live sky",
                             curses.A_DIM)
        except curses.error:
            pass

        stdscr.refresh()

        if single_frame:
            stdscr.timeout(-1)  # wait for keypress
            stdscr.getch()
            break

        time.sleep(0.06)


def main():
    location = ""
    animate = False

    args = sys.argv[1:]
    for arg in args:
        if arg == "--animate":
            animate = True
        else:
            location = arg

    # Fetch weather
    print("  fetching the sky...", end="", flush=True)
    weather = fetch_weather(location)
    print("\r                     \r", end="", flush=True)

    if not weather:
        print("  couldn't reach the sky. (check your connection)")
        return

    curses.wrapper(lambda stdscr: render_sky(stdscr, weather, animate))


if __name__ == "__main__":
    main()
