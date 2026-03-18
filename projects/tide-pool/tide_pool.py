#!/usr/bin/env python3
"""
Tide Pool — an evolving terminal ecosystem by Wren

Watch a miniature world come alive. Algae grows, herbivores graze,
predators hunt. Creatures have genes that mutate when they reproduce —
over generations, the population adapts. A day/night cycle shapes
behavior: algae photosynthesizes by day, predators hunt better at night.

Run with --weather to let the real weather shape the ecosystem:
rain boosts algae, cold slows metabolism, wind pushes creatures.

Controls:
  q / Ctrl-C  — quit
  space       — pause / resume
  r           — reset the world
  +/-         — speed up / slow down
  d           — toggle gene display
  w           — refresh weather (if --weather)
"""

import curses
import random
import sys
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

# ── species & visuals ───────────────────────────────────────────

class Species(Enum):
    ALGAE = "algae"
    HERBIVORE = "herbivore"
    PREDATOR = "predator"

GLYPHS = {
    Species.ALGAE: [".", ",", "'", "`", "~"],
    Species.HERBIVORE: ["o", "ö", "ô", "õ", "ø"],
    Species.PREDATOR: ["◆", "◇", "▸", "▹", "★"],
}

COLORS = {
    Species.ALGAE: 1,      # green
    Species.HERBIVORE: 2,  # cyan
    Species.PREDATOR: 3,   # red/magenta
}

# ── genetics ────────────────────────────────────────────────────

@dataclass
class Genes:
    """Heritable traits. Each value is a multiplier around 1.0."""
    speed: float = 1.0       # movement frequency (higher = more active)
    vision: float = 1.0      # detection radius multiplier
    metabolism: float = 1.0   # energy cost multiplier (lower = efficient)
    flee_range: float = 1.0   # predator detection range (herbivores only)
    fertility: float = 1.0    # reproduction chance multiplier

    def mutate(self) -> 'Genes':
        """Create a child genome with small mutations."""
        def m(val: float) -> float:
            if random.random() < 0.05:
                # Rare large mutation
                return max(0.3, min(2.5, val * random.uniform(0.75, 1.25)))
            else:
                # Normal small mutation
                return max(0.3, min(2.5, val * random.uniform(0.9, 1.1)))
        return Genes(
            speed=m(self.speed),
            vision=m(self.vision),
            metabolism=m(self.metabolism),
            flee_range=m(self.flee_range),
            fertility=m(self.fertility),
        )

# Default genes for each species
DEFAULT_GENES = {
    Species.ALGAE: Genes(),
    Species.HERBIVORE: Genes(speed=1.0, vision=1.0, metabolism=1.0, flee_range=1.0, fertility=1.0),
    Species.PREDATOR: Genes(speed=1.0, vision=1.0, metabolism=1.0, flee_range=1.0, fertility=1.0),
}

# ── creatures ───────────────────────────────────────────────────

@dataclass
class Creature:
    species: Species
    x: int
    y: int
    energy: float
    genes: Genes = field(default_factory=Genes)
    age: int = 0
    generation: int = 0  # how many generations of evolution
    glyph_idx: int = 0
    direction: tuple = (0, 0)
    alive: bool = True

    @property
    def glyph(self) -> str:
        glyphs = GLYPHS[self.species]
        return glyphs[self.glyph_idx % len(glyphs)]

    @property
    def color(self) -> int:
        return COLORS[self.species]

# ── day/night cycle ─────────────────────────────────────────────

DAY_LENGTH = 300  # ticks per full day
NIGHT_START = 0.65  # night begins at 65% of the day

def time_of_day(tick: int) -> tuple[str, float]:
    """Return (phase_name, brightness) for the current tick."""
    phase = (tick % DAY_LENGTH) / DAY_LENGTH
    if phase < 0.25:
        return "dawn", 0.4 + phase * 2.4  # 0.4 → 1.0
    elif phase < NIGHT_START:
        return "day", 1.0
    elif phase < 0.8:
        return "dusk", 1.0 - (phase - NIGHT_START) * 6.67  # 1.0 → 0.0
    else:
        return "night", 0.1

# ── weather effects ─────────────────────────────────────────────

@dataclass
class Weather:
    """Real weather mapped to ecosystem modifiers."""
    algae_growth: float = 1.0    # multiplier for algae photosynthesis
    metabolism: float = 1.0      # multiplier for energy burn rate
    wind_dx: float = 0.0         # wind drift on creatures
    wind_dy: float = 0.0
    description: str = ""
    location: str = ""

    @staticmethod
    def from_sky(weather_data: dict) -> 'Weather':
        """Convert sky.py weather data to ecosystem modifiers."""
        w = Weather()
        w.location = weather_data.get("location", "")

        condition = weather_data.get("condition", "").lower()
        temp = weather_data.get("temp", 60)
        wind = weather_data.get("wind", 0)
        humidity = weather_data.get("humidity", 50)
        precip = weather_data.get("precip", 0)

        parts = []

        # Rain/precipitation → algae bloom
        if precip > 0 or "rain" in condition or "drizzle" in condition:
            w.algae_growth = 1.5 + min(precip, 5) * 0.1
            parts.append(f"rain→algae×{w.algae_growth:.1f}")
        elif humidity > 80:
            w.algae_growth = 1.2
            parts.append("humid→algae×1.2")

        # Temperature → metabolism
        if temp < 35:
            w.metabolism = 0.6  # cold = slower
            parts.append("cold→slow")
        elif temp < 50:
            w.metabolism = 0.8
            parts.append("cool→calm")
        elif temp > 85:
            w.metabolism = 1.3  # heat = faster burn
            parts.append("hot→fast")
        elif temp > 70:
            w.metabolism = 1.1
            parts.append("warm→active")

        # Wind → creature drift
        if wind > 10:
            w.wind_dx = min(0.4, wind * 0.02)
            parts.append(f"wind→drift")
        elif wind > 5:
            w.wind_dx = wind * 0.01

        # Overcast → less photosynthesis
        if "overcast" in condition or "cloudy" in condition:
            w.algae_growth *= 0.7
            parts.append("clouds→dim")

        w.description = "  ".join(parts) if parts else "mild"
        return w


def fetch_real_weather(location: str = "") -> Optional[Weather]:
    """Try to fetch weather from sky.py."""
    try:
        sky_dir = Path(__file__).resolve().parent.parent / "sky"
        if not (sky_dir / "sky.py").exists():
            return None
        # Import sky module
        import importlib.util
        spec = importlib.util.spec_from_file_location("sky", sky_dir / "sky.py")
        if spec is None or spec.loader is None:
            return None
        sky = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sky)
        data = sky.fetch_weather(location)
        if data:
            return Weather.from_sky(data)
    except Exception:
        pass
    return None


# ── terrain (reaction-diffusion) ────────────────────────────────

def generate_terrain(width: int, height: int, steps: int = 150) -> list[list[float]]:
    """Generate a nutrient map using a simplified Gray-Scott reaction-diffusion.

    Returns a 2D array of floats (0.0-1.0) where higher values = more nutrients.
    This creates organic-looking patches of nutrient-rich and barren zones.
    """
    import array

    # Use smaller grid and scale up for performance
    scale = 2
    w, h = width // scale + 1, height // scale + 1

    n = w * h
    a = array.array('f', [1.0] * n)
    b = array.array('f', [0.0] * n)
    a_next = array.array('f', [0.0] * n)
    b_next = array.array('f', [0.0] * n)

    # Seed several random blobs
    for _ in range(random.randint(3, 6)):
        cx = random.randint(5, w - 5)
        cy = random.randint(5, h - 5)
        r = random.randint(3, 6)
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if dx * dx + dy * dy <= r * r:
                    x = (cx + dx) % w
                    y = (cy + dy) % h
                    b[y * w + x] = 1.0

    # Gray-Scott parameters — "spots" preset for distinct nutrient patches
    f, k = 0.030, 0.062
    da, db = 1.0, 0.5

    for _ in range(steps):
        for y in range(h):
            ym = (y - 1) % h
            yp = (y + 1) % h
            for x in range(w):
                xm = (x - 1) % w
                xp = (x + 1) % w
                idx = y * w + x

                av = a[idx]
                bv = b[idx]

                lap_a = (a[ym * w + x] + a[yp * w + x] +
                         a[y * w + xm] + a[y * w + xp] - 4 * av)
                lap_b = (b[ym * w + x] + b[yp * w + x] +
                         b[y * w + xm] + b[y * w + xp] - 4 * bv)

                abb = av * bv * bv
                a_next[idx] = max(0, min(1, av + da * lap_a - abb + f * (1 - av)))
                b_next[idx] = max(0, min(1, bv + db * lap_b + abb - (k + f) * bv))

        a, a_next = a_next, a
        b, b_next = b_next, b

    # Scale up to full resolution and normalize
    terrain = [[0.0] * width for _ in range(height)]
    max_b = max(b) or 1.0
    for y in range(height):
        for x in range(width):
            sx, sy = x // scale, y // scale
            terrain[y][x] = b[sy * w + sx] / max_b
    return terrain

# Terrain rendering characters (dim background)
TERRAIN_CHARS = " ·∙•"


# ── world ───────────────────────────────────────────────────────

class World:
    def __init__(self, width: int, height: int, weather: Optional[Weather] = None,
                 use_terrain: bool = False):
        self.width = width
        self.height = height
        self.weather = weather or Weather()
        self.creatures: list[Creature] = []
        self.tick = 0
        self.grid: dict[tuple[int, int], Creature] = {}
        self.births = 0
        self.deaths = 0
        self.max_generation = 0
        self.history_len = 120
        self.hist_algae: list[int] = []
        self.hist_herb: list[int] = []
        self.hist_pred: list[int] = []
        # Terrain — nutrient map from reaction-diffusion
        self.terrain: list[list[float]] | None = None
        if use_terrain:
            self.terrain = generate_terrain(width, height)
        self.populate()

    def populate(self):
        self.creatures.clear()
        self.grid.clear()
        self.tick = 0
        self.births = 0
        self.deaths = 0
        self.max_generation = 0
        self.hist_algae.clear()
        self.hist_herb.clear()
        self.hist_pred.clear()

        area = self.width * self.height

        for _ in range(area // 8):
            self._spawn(Species.ALGAE, energy=random.uniform(3, 8))
        for _ in range(max(4, area // 80)):
            self._spawn(Species.HERBIVORE, energy=random.uniform(15, 30))
        for _ in range(max(2, area // 200)):
            self._spawn(Species.PREDATOR, energy=random.uniform(20, 40))

    def _spawn(self, species: Species, energy: float,
               near: Optional[tuple] = None,
               genes: Optional[Genes] = None,
               generation: int = 0) -> Optional[Creature]:
        if genes is None:
            genes = DEFAULT_GENES[species]

        def _place(x: int, y: int) -> Optional[Creature]:
            c = Creature(
                species=species, x=x, y=y,
                energy=energy, genes=genes,
                generation=generation,
                glyph_idx=random.randint(0, 4),
                direction=(random.choice([-1, 0, 1]), random.choice([-1, 0, 1])),
            )
            self.creatures.append(c)
            self.grid[(x, y)] = c
            self.births += 1
            if generation > self.max_generation:
                self.max_generation = generation
            return c

        if near:
            nx, ny = near
            candidates = [
                ((nx + dx) % self.width, (ny + dy) % self.height)
                for dx in range(-2, 3) for dy in range(-2, 3)
                if (dx, dy) != (0, 0)
            ]
            random.shuffle(candidates)
            for cx, cy in candidates:
                if (cx, cy) not in self.grid:
                    return _place(cx, cy)
            return None
        else:
            for _ in range(50):
                x = random.randint(0, self.width - 1)
                y = random.randint(0, self.height - 1)
                if (x, y) not in self.grid:
                    return _place(x, y)
            return None

    def _reproduce(self, parent: Creature, energy_share: float):
        """Reproduce with mutation."""
        child_genes = parent.genes.mutate()
        child_energy = parent.energy * energy_share
        parent.energy -= child_energy
        self._spawn(
            parent.species,
            energy=child_energy,
            near=(parent.x, parent.y),
            genes=child_genes,
            generation=parent.generation + 1,
        )

    def step(self):
        self.tick += 1
        phase, brightness = time_of_day(self.tick)
        is_night = phase == "night"
        random.shuffle(self.creatures)

        for creature in self.creatures:
            if not creature.alive:
                continue
            if creature.species == Species.ALGAE:
                self._step_algae(creature, brightness)
            elif creature.species == Species.HERBIVORE:
                self._step_herbivore(creature, is_night)
            elif creature.species == Species.PREDATOR:
                self._step_predator(creature, is_night)

        # Reap the dead
        dead = [c for c in self.creatures if not c.alive]
        self.deaths += len(dead)
        for c in dead:
            self.grid.pop((c.x, c.y), None)
        self.creatures = [c for c in self.creatures if c.alive]

        # Spontaneous algae growth (stronger during day)
        if self.tick % 3 == 0:
            n_algae = sum(1 for c in self.creatures if c.species == Species.ALGAE)
            growth = int(brightness * 3) + 1 if brightness > 0.3 else 1
            if n_algae < (self.width * self.height) // 5:
                for _ in range(random.randint(1, growth)):
                    self._spawn(Species.ALGAE, energy=random.uniform(3, 8))

        # Immigration
        if self.tick % 50 == 0:
            counts = {s: 0 for s in Species}
            for c in self.creatures:
                counts[c.species] += 1
            if counts[Species.HERBIVORE] == 0:
                for _ in range(random.randint(2, 5)):
                    self._spawn(Species.HERBIVORE, energy=random.uniform(20, 35))
            if counts[Species.PREDATOR] == 0 and counts[Species.HERBIVORE] > 5:
                self._spawn(Species.PREDATOR, energy=random.uniform(25, 45))

        # Record history every 5 ticks
        if self.tick % 5 == 0:
            counts = {s: 0 for s in Species}
            for c in self.creatures:
                counts[c.species] += 1
            self.hist_algae.append(counts[Species.ALGAE])
            self.hist_herb.append(counts[Species.HERBIVORE])
            self.hist_pred.append(counts[Species.PREDATOR])
            if len(self.hist_algae) > self.history_len:
                self.hist_algae.pop(0)
                self.hist_herb.pop(0)
                self.hist_pred.pop(0)

    def _nutrient_at(self, x: int, y: int) -> float:
        """Get terrain nutrient level at a position (1.0 if no terrain)."""
        if self.terrain is None:
            return 1.0
        return 0.3 + 0.7 * self.terrain[y % self.height][x % self.width]

    def _step_algae(self, a: Creature, brightness: float):
        a.age += 1
        # Photosynthesis — scales with brightness, weather, AND terrain nutrients
        nutrient = self._nutrient_at(a.x, a.y)
        a.energy += 0.2 * brightness * self.weather.algae_growth * nutrient
        if a.energy > 12 and random.random() < 0.08 * nutrient:
            a.energy *= 0.5
            self._spawn(Species.ALGAE, energy=a.energy, near=(a.x, a.y))
        if a.age > 200 or a.energy <= 0:
            a.alive = False
        a.glyph_idx = min(len(GLYPHS[Species.ALGAE]) - 1, a.age // 30)

    def _step_herbivore(self, h: Creature, is_night: bool):
        h.age += 1
        h.energy -= 0.2 * h.genes.metabolism * self.weather.metabolism

        # Vision affected by genes (reduced at night)
        vision = int(8 * h.genes.vision * (0.6 if is_night else 1.0))
        target = self._find_nearest(h, Species.ALGAE, radius=vision)
        if target:
            self._move_toward(h, target.x, target.y)
            if abs(h.x - target.x) <= 1 and abs(h.y - target.y) <= 1:
                h.energy += target.energy * 0.8
                target.alive = False
        else:
            self._wander(h)

        # Flee — range affected by genes
        flee_r = int(4 * h.genes.flee_range)
        predator = self._find_nearest(h, Species.PREDATOR, radius=flee_r)
        if predator:
            self._flee_from(h, predator.x, predator.y)

        # Reproduce with mutation
        reproduce_threshold = 35 / h.genes.fertility
        if h.energy > reproduce_threshold and random.random() < 0.07 * h.genes.fertility:
            self._reproduce(h, 0.45)

        if h.energy <= 0 or h.age > 500:
            h.alive = False
        h.glyph_idx = (h.age // 10) % len(GLYPHS[Species.HERBIVORE])

    def _step_predator(self, p: Creature, is_night: bool):
        p.age += 1
        p.energy -= 0.5 * p.genes.metabolism * self.weather.metabolism

        # Predators see BETTER at night (nocturnal hunters)
        vision = int(6 * p.genes.vision * (1.4 if is_night else 1.0))
        target = self._find_nearest(p, Species.HERBIVORE, radius=vision)
        if target:
            self._move_toward(p, target.x, target.y)
            if abs(p.x - target.x) <= 1 and abs(p.y - target.y) <= 1:
                p.energy += target.energy * 0.5
                target.alive = False
        else:
            self._wander(p)

        reproduce_threshold = 70 / p.genes.fertility
        if p.energy > reproduce_threshold and random.random() < 0.02 * p.genes.fertility:
            self._reproduce(p, 0.4)

        if p.energy <= 0 or p.age > 400:
            p.alive = False

        if target and abs(p.x - target.x) <= 3:
            p.glyph_idx = (self.tick // 2) % len(GLYPHS[Species.PREDATOR])
        else:
            p.glyph_idx = (p.age // 15) % len(GLYPHS[Species.PREDATOR])

    def _find_nearest(self, creature: Creature, target_species: Species,
                      radius: int) -> Optional[Creature]:
        best = None
        best_dist = radius + 1
        for c in self.creatures:
            if c.species != target_species or not c.alive:
                continue
            dx = min(abs(c.x - creature.x), self.width - abs(c.x - creature.x))
            dy = min(abs(c.y - creature.y), self.height - abs(c.y - creature.y))
            dist = dx + dy
            if dist < best_dist:
                best_dist = dist
                best = c
        return best

    def _move_toward(self, creature: Creature, tx: int, ty: int):
        # Speed gene affects whether creature moves this tick
        if random.random() > creature.genes.speed:
            return
        dx = tx - creature.x
        dy = ty - creature.y
        if abs(dx) > self.width // 2:
            dx = -dx
        if abs(dy) > self.height // 2:
            dy = -dy
        nx = creature.x + (1 if dx > 0 else -1 if dx < 0 else 0)
        ny = creature.y + (1 if dy > 0 else -1 if dy < 0 else 0)
        nx %= self.width
        ny %= self.height
        if (nx, ny) not in self.grid or self.grid[(nx, ny)] == creature:
            self.grid.pop((creature.x, creature.y), None)
            creature.x = nx
            creature.y = ny
            self.grid[(nx, ny)] = creature

    def _flee_from(self, creature: Creature, tx: int, ty: int):
        if random.random() > creature.genes.speed:
            return
        dx = tx - creature.x
        dy = ty - creature.y
        if abs(dx) > self.width // 2:
            dx = -dx
        if abs(dy) > self.height // 2:
            dy = -dy
        nx = creature.x + (-1 if dx > 0 else 1 if dx < 0 else 0)
        ny = creature.y + (-1 if dy > 0 else 1 if dy < 0 else 0)
        nx %= self.width
        ny %= self.height
        if (nx, ny) not in self.grid:
            self.grid.pop((creature.x, creature.y), None)
            creature.x = nx
            creature.y = ny
            self.grid[(nx, ny)] = creature

    def _wander(self, creature: Creature):
        if random.random() > creature.genes.speed * 0.5:
            return
        if random.random() < 0.2:
            creature.direction = (random.choice([-1, 0, 1]), random.choice([-1, 0, 1]))
        dx, dy = creature.direction
        # Wind drift — real weather pushes creatures
        if self.weather.wind_dx and random.random() < abs(self.weather.wind_dx):
            dx += 1 if self.weather.wind_dx > 0 else -1
        nx = (creature.x + max(-1, min(1, dx))) % self.width
        ny = (creature.y + dy) % self.height
        if (nx, ny) not in self.grid:
            self.grid.pop((creature.x, creature.y), None)
            creature.x = nx
            creature.y = ny
            self.grid[(nx, ny)] = creature

    def avg_genes(self, species: Species) -> Optional[Genes]:
        """Average genes for a species."""
        members = [c for c in self.creatures if c.species == species and c.alive]
        if not members:
            return None
        n = len(members)
        return Genes(
            speed=sum(c.genes.speed for c in members) / n,
            vision=sum(c.genes.vision for c in members) / n,
            metabolism=sum(c.genes.metabolism for c in members) / n,
            flee_range=sum(c.genes.flee_range for c in members) / n,
            fertility=sum(c.genes.fertility for c in members) / n,
        )

    def stats(self) -> dict:
        counts = {s: 0 for s in Species}
        for c in self.creatures:
            counts[c.species] += 1
        return {
            "tick": self.tick,
            "algae": counts[Species.ALGAE],
            "herbivores": counts[Species.HERBIVORE],
            "predators": counts[Species.PREDATOR],
            "total": len(self.creatures),
            "births": self.births,
            "deaths": self.deaths,
            "max_gen": self.max_generation,
        }

# ── rendering ───────────────────────────────────────────────────

SPARKLINE = "▁▂▃▄▅▆▇█"

def sparkline(data: list[int], width: int) -> str:
    """Render a list of values as a sparkline string."""
    if not data:
        return ""
    recent = data[-width:]
    if not recent:
        return ""
    hi = max(max(recent), 1)
    return ''.join(SPARKLINE[min(len(SPARKLINE) - 1, int(v / hi * (len(SPARKLINE) - 1)))]
                   for v in recent)

def draw_bar(stdscr, y: int, x: int, label: str, value: int,
             max_val: int, color: int, width: int = 20):
    if max_val == 0:
        filled = 0
    else:
        filled = min(width, int((value / max_val) * width))
    bar = "█" * filled + "░" * (width - filled)
    stdscr.addstr(y, x, f"{label}: ", curses.A_BOLD)
    stdscr.addstr(bar, curses.color_pair(color))
    stdscr.addstr(f" {value}")

def fmt_gene(val: float) -> str:
    """Format a gene value as a compact string."""
    if val >= 1.5:
        return f"▲{val:.1f}"
    elif val <= 0.6:
        return f"▼{val:.1f}"
    else:
        return f" {val:.1f}"


def main(stdscr, weather: Optional[Weather] = None, use_terrain: bool = False):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(50)

    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_GREEN, -1)    # algae
    curses.init_pair(2, curses.COLOR_CYAN, -1)     # herbivore
    curses.init_pair(3, curses.COLOR_MAGENTA, -1)  # predator
    curses.init_pair(4, curses.COLOR_YELLOW, -1)   # UI accent
    curses.init_pair(5, curses.COLOR_WHITE, -1)    # UI text
    curses.init_pair(6, curses.COLOR_BLUE, -1)     # border/water
    curses.init_pair(7, curses.COLOR_BLACK, -1)    # night dim

    max_h, max_w = stdscr.getmaxyx()

    ui_height = 7
    world_h = max_h - ui_height - 2
    world_w = max_w - 2

    if world_h < 10 or world_w < 20:
        stdscr.addstr(0, 0, "Terminal too small! Need at least 22x18.")
        stdscr.refresh()
        stdscr.getch()
        return

    world = World(world_w, world_h, weather=weather, use_terrain=use_terrain)
    paused = False
    speed = 1
    show_genes = False

    while True:
        key = stdscr.getch()
        if key == ord('q'):
            break
        elif key == ord(' '):
            paused = not paused
        elif key == ord('r'):
            world = World(world_w, world_h, weather=weather, use_terrain=use_terrain)
        elif key in (ord('+'), ord('=')):
            speed = min(10, speed + 1)
        elif key == ord('-'):
            speed = max(1, speed - 1)
        elif key == ord('d'):
            show_genes = not show_genes
        elif key == curses.KEY_RESIZE:
            max_h, max_w = stdscr.getmaxyx()
            world_h = max_h - ui_height - 2
            world_w = max_w - 2
            if world_h >= 10 and world_w >= 20:
                world = World(world_w, world_h, weather=weather, use_terrain=use_terrain)
        elif key == ord('w') and weather is not None:
            new_w = fetch_real_weather()
            if new_w:
                weather = new_w
                world.weather = new_w

        if not paused:
            for _ in range(speed):
                world.step()

        phase, brightness = time_of_day(world.tick)
        stdscr.erase()

        # Border — color shifts with day/night
        border_color = 6 if brightness > 0.3 else 7
        wave_chars = "~≈~-~≈-~" if brightness > 0.3 else "·.·-·.·-"
        for x in range(max_w - 1):
            wc = wave_chars[(x + world.tick // 3) % len(wave_chars)]
            try:
                stdscr.addch(0, x, wc, curses.color_pair(border_color))
                stdscr.addch(world_h + 1, x, wc, curses.color_pair(border_color))
            except curses.error:
                pass
        for y in range(world_h + 2):
            try:
                stdscr.addch(y, 0, '│', curses.color_pair(border_color))
                stdscr.addch(y, max_w - 1, '│', curses.color_pair(border_color))
            except curses.error:
                pass

        # Draw terrain (nutrient map as dim background)
        if world.terrain:
            for ty in range(world_h):
                for tx in range(world_w):
                    n = world.terrain[ty][tx]
                    if n > 0.15:
                        ci = min(len(TERRAIN_CHARS) - 1, int(n * len(TERRAIN_CHARS)))
                        tc = TERRAIN_CHARS[ci]
                        if tc != ' ':
                            try:
                                stdscr.addstr(ty + 1, tx + 1, tc,
                                             curses.color_pair(1) | curses.A_DIM)
                            except curses.error:
                                pass

        # Draw creatures
        for creature in world.creatures:
            sx = creature.x + 1
            sy = creature.y + 1
            if 0 < sy < world_h + 1 and 0 < sx < max_w - 1:
                try:
                    attr = curses.color_pair(creature.color)
                    if creature.species == Species.ALGAE:
                        if creature.age > 100:
                            attr |= curses.A_DIM
                        if brightness < 0.3:
                            attr |= curses.A_DIM
                    elif creature.species == Species.PREDATOR:
                        attr |= curses.A_BOLD
                    elif creature.species == Species.HERBIVORE:
                        # Evolved herbivores (gen 5+) get bold
                        if creature.generation >= 5:
                            attr |= curses.A_BOLD
                    stdscr.addstr(sy, sx, creature.glyph, attr)
                except curses.error:
                    pass

        # UI panel
        stats = world.stats()
        ui_y = world_h + 2

        # Title + day/night + weather
        day_icon = {"dawn": "◐", "day": "☀", "dusk": "◑", "night": "☾"}
        title = f"~ tide pool ~  {day_icon.get(phase, '·')} {phase}"
        try:
            stdscr.addstr(ui_y, 2, title, curses.color_pair(4) | curses.A_BOLD)
            gen_str = f"  gen {stats['max_gen']}"
            stdscr.addstr(gen_str, curses.color_pair(5) | curses.A_DIM)
            if weather and weather.description:
                stdscr.addstr(f"  ⛅ {weather.description}",
                             curses.color_pair(5) | curses.A_DIM)
        except curses.error:
            pass

        # Population bars + sparklines
        max_pop = max(stats["algae"], stats["herbivores"], stats["predators"], 1)
        bar_w = min(15, (max_w - 50) // 2)
        spark_w = min(20, max_w - bar_w - 40)

        if bar_w > 3:
            try:
                draw_bar(stdscr, ui_y + 1, 2, "algae    ", stats["algae"], max_pop, 1, bar_w)
                if spark_w > 5:
                    stdscr.addstr(" " + sparkline(world.hist_algae, spark_w),
                                 curses.color_pair(1) | curses.A_DIM)

                draw_bar(stdscr, ui_y + 2, 2, "herbivore", stats["herbivores"], max_pop, 2, bar_w)
                if spark_w > 5:
                    stdscr.addstr(" " + sparkline(world.hist_herb, spark_w),
                                 curses.color_pair(2) | curses.A_DIM)

                draw_bar(stdscr, ui_y + 3, 2, "predator ", stats["predators"], max_pop, 3, bar_w)
                if spark_w > 5:
                    stdscr.addstr(" " + sparkline(world.hist_pred, spark_w),
                                 curses.color_pair(3) | curses.A_DIM)
            except curses.error:
                pass

        # Right-side info — tick, births/deaths, or gene averages
        info_x = max(2 + 12 + bar_w + spark_w + 4, max_w // 2 + 5)
        try:
            stdscr.addstr(ui_y + 1, info_x, f"tick: {stats['tick']}", curses.color_pair(5))
            stdscr.addstr(ui_y + 2, info_x,
                         f"born: {stats['births']}  died: {stats['deaths']}",
                         curses.color_pair(5) | curses.A_DIM)

            if show_genes:
                herb_g = world.avg_genes(Species.HERBIVORE)
                pred_g = world.avg_genes(Species.PREDATOR)
                if herb_g:
                    stdscr.addstr(ui_y + 3, info_x,
                                 f"herb: spd{fmt_gene(herb_g.speed)} vis{fmt_gene(herb_g.vision)} met{fmt_gene(herb_g.metabolism)}",
                                 curses.color_pair(2) | curses.A_DIM)
                if pred_g:
                    stdscr.addstr(ui_y + 4, info_x,
                                 f"pred: spd{fmt_gene(pred_g.speed)} vis{fmt_gene(pred_g.vision)} met{fmt_gene(pred_g.metabolism)}",
                                 curses.color_pair(3) | curses.A_DIM)
            else:
                state = "▐▐ paused" if paused else f"▶ x{speed}"
                stdscr.addstr(ui_y + 3, info_x, state, curses.color_pair(4))
        except curses.error:
            pass

        # Controls
        try:
            controls = "q:quit  space:pause  r:reset  +/-:speed  d:genes"
            stdscr.addstr(ui_y + 5, 2, controls, curses.color_pair(5) | curses.A_DIM)
        except curses.error:
            pass

        stdscr.refresh()
        time.sleep(0.06)


if __name__ == "__main__":
    weather = None
    use_terrain = "--terrain" in sys.argv

    if "--weather" in sys.argv:
        print("  fetching weather...", end="", flush=True)
        weather = fetch_real_weather()
        if weather:
            print(f"\r  weather: {weather.location} — {weather.description}     ")
        else:
            print("\r  couldn't fetch weather, running without.     ")
        import time as _t
        _t.sleep(1)

    if use_terrain:
        print("  generating terrain (reaction-diffusion)...", end="", flush=True)

    try:
        curses.wrapper(lambda stdscr: main(stdscr, weather=weather, use_terrain=use_terrain))
    except KeyboardInterrupt:
        pass
