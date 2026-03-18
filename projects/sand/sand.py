#!/usr/bin/env python3
"""
Sand — a falling-sand physics toy by Wren

Paint with particles. Sand piles. Water flows. Fire rises. Stone stays.
Plants grow. Steam evaporates. Simple rules, emergent chemistry.

Controls:
  Arrow keys / hjkl — move cursor
  SPACE / ENTER     — place particle
  1                 — sand (falls, piles)
  2                 — water (flows, fills)
  3                 — stone (solid, stays)
  4                 — fire (rises, spreads, dies)
  5                 — plant (grows upward from sand)
  6                 — eraser
  [ / ]             — smaller / bigger brush
  x                 — clear all
  g                 — toggle gravity direction
  q                 — quit

Chemistry:
  water + fire = steam (rises fast, condenses back to water)
  fire + plant = more fire (plants are flammable)
  plant grows upward when rooted in sand
"""

import curses
import random
import time

# Particle types
EMPTY = 0
SAND = 1
WATER = 2
STONE = 3
FIRE = 4
PLANT = 5
STEAM = 6

NAMES = {
    EMPTY: "eraser", SAND: "sand", WATER: "water",
    STONE: "stone", FIRE: "fire", PLANT: "plant", STEAM: "steam",
}

CHARS = {
    SAND: ["▒", "░", "▓", "▒"],
    WATER: ["~", "≈", "~", "∼"],
    STONE: ["█", "▓", "█", "▓"],
    FIRE: ["▲", "△", "♦", "✦", "*"],
    PLANT: ["⌇", "⌇", "│", "╿"],
    STEAM: [".", "·", "∙", " "],
}

PARTICLE_COLORS = {
    SAND: 1,    # yellow
    WATER: 2,   # blue
    STONE: 3,   # white
    FIRE: 4,    # red
    PLANT: 5,   # green
    STEAM: 6,   # cyan
}


class World:
    def __init__(self, width: int, height: int):
        self.w = width
        self.h = height
        self.grid = [[EMPTY] * width for _ in range(height)]
        self.age = [[0] * width for _ in range(height)]  # for fire/animation
        self.tick = 0
        self.gravity_down = True

    def get(self, x: int, y: int) -> int:
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.grid[y][x]
        return STONE  # walls are solid

    def set(self, x: int, y: int, val: int):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.grid[y][x] = val
            self.age[y][x] = 0

    def swap(self, x1: int, y1: int, x2: int, y2: int):
        if (0 <= x1 < self.w and 0 <= y1 < self.h and
            0 <= x2 < self.w and 0 <= y2 < self.h):
            self.grid[y1][x1], self.grid[y2][x2] = self.grid[y2][x2], self.grid[y1][x1]
            self.age[y1][x1], self.age[y2][x2] = self.age[y2][x2], self.age[y1][x1]

    def clear(self):
        for y in range(self.h):
            for x in range(self.w):
                self.grid[y][x] = EMPTY
                self.age[y][x] = 0

    def step(self):
        self.tick += 1
        dy = 1 if self.gravity_down else -1

        # Process bottom-up for falling, top-down for rising
        if self.gravity_down:
            y_range = range(self.h - 2, -1, -1)
        else:
            y_range = range(1, self.h)

        # Track which cells have been updated this tick
        moved = set()

        for y in y_range:
            # Randomize x order to prevent bias
            x_order = list(range(self.w))
            random.shuffle(x_order)

            for x in x_order:
                if (x, y) in moved:
                    continue

                cell = self.grid[y][x]
                if cell == EMPTY:
                    continue

                self.age[y][x] += 1

                if cell == SAND:
                    self._step_sand(x, y, dy, moved)
                elif cell == WATER:
                    self._step_water(x, y, dy, moved)
                elif cell == FIRE:
                    self._step_fire(x, y, moved)
                elif cell == PLANT:
                    self._step_plant(x, y, moved)
                elif cell == STEAM:
                    self._step_steam(x, y, moved)
                # STONE doesn't move

    def _step_sand(self, x: int, y: int, dy: int, moved: set):
        below = y + dy
        # Fall straight down
        if self.get(x, below) == EMPTY:
            self.swap(x, y, x, below)
            moved.add((x, below))
        # Fall through water
        elif self.get(x, below) == WATER:
            self.swap(x, y, x, below)
            moved.add((x, below))
        # Slide diagonally
        elif random.random() < 0.5:
            if self.get(x - 1, below) in (EMPTY, WATER):
                self.swap(x, y, x - 1, below)
                moved.add((x - 1, below))
            elif self.get(x + 1, below) in (EMPTY, WATER):
                self.swap(x, y, x + 1, below)
                moved.add((x + 1, below))
        else:
            if self.get(x + 1, below) in (EMPTY, WATER):
                self.swap(x, y, x + 1, below)
                moved.add((x + 1, below))
            elif self.get(x - 1, below) in (EMPTY, WATER):
                self.swap(x, y, x - 1, below)
                moved.add((x - 1, below))

    def _step_water(self, x: int, y: int, dy: int, moved: set):
        below = y + dy
        # Fall
        if self.get(x, below) == EMPTY:
            self.swap(x, y, x, below)
            moved.add((x, below))
        # Spread sideways
        else:
            dirs = [-1, 1]
            random.shuffle(dirs)
            for dx in dirs:
                if self.get(x + dx, y) == EMPTY:
                    self.swap(x, y, x + dx, y)
                    moved.add((x + dx, y))
                    break
                elif self.get(x + dx, below) == EMPTY:
                    self.swap(x, y, x + dx, below)
                    moved.add((x + dx, below))
                    break

        # Erosion — water slowly dissolves adjacent sand
        if random.random() < 0.008:
            for edx, edy in [(-1, 0), (1, 0), (0, 1), (0, -1)]:
                ex, ey = x + edx, y + edy
                if self.get(ex, ey) == SAND:
                    if 0 <= ex < self.w and 0 <= ey < self.h:
                        self.grid[ey][ex] = WATER
                        self.age[ey][ex] = 0
                        break  # erode one grain per tick max

    def _step_fire(self, x: int, y: int, moved: set):
        age = self.age[y][x]

        # Fire dies after a while
        if age > random.randint(15, 40):
            self.grid[y][x] = EMPTY
            return

        # Fire rises (opposite of gravity)
        above = y - 1
        if above >= 0 and self.get(x, above) == EMPTY:
            if random.random() < 0.6:
                self.swap(x, y, x, above)
                moved.add((x, above))
                return

        # Fire drifts sideways
        dx = random.choice([-1, 0, 0, 1])
        if self.get(x + dx, above if above >= 0 else y) == EMPTY and above >= 0:
            self.swap(x, y, x + dx, above)
            moved.add((x + dx, above))
        elif dx != 0 and self.get(x + dx, y) == EMPTY:
            self.swap(x, y, x + dx, y)
            moved.add((x + dx, y))

        # Chemistry: fire + water → steam, fire + plant → more fire
        for fdx, fdy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            fx, fy = x + fdx, y + fdy
            neighbor = self.get(fx, fy)
            if neighbor == WATER:
                # Water + fire → steam!
                self.grid[y][x] = STEAM
                self.age[y][x] = 0
                if 0 <= fy < self.h and 0 <= fx < self.w:
                    self.grid[fy][fx] = STEAM
                    self.age[fy][fx] = 0
                return
            elif neighbor == PLANT:
                # Plants are flammable
                if random.random() < 0.3:
                    if 0 <= fy < self.h and 0 <= fx < self.w:
                        self.grid[fy][fx] = FIRE
                        self.age[fy][fx] = 0

    def _step_plant(self, x: int, y: int, moved: set):
        """Plants grow upward when rooted in sand. Flammable."""
        age = self.age[y][x]

        # Check if rooted (sand or other plant below)
        below = self.get(x, y + 1)
        rooted = below in (SAND, PLANT, STONE)

        if not rooted:
            # Unrooted plants fall like sand
            if self.get(x, y + 1) == EMPTY:
                self.swap(x, y, x, y + 1)
                moved.add((x, y + 1))
            return

        # Grow upward occasionally
        if age > 5 and random.random() < 0.03 and y > 0:
            above = self.get(x, y - 1)
            if above == EMPTY:
                self.grid[y - 1][x] = PLANT
                self.age[y - 1][x] = 0
            # Branch sideways occasionally
            elif random.random() < 0.3:
                dx = random.choice([-1, 1])
                if self.get(x + dx, y - 1) == EMPTY:
                    if 0 <= x + dx < self.w and y - 1 >= 0:
                        self.grid[y - 1][x + dx] = PLANT
                        self.age[y - 1][x + dx] = 0

    def _step_steam(self, x: int, y: int, moved: set):
        """Steam rises fast and eventually condenses back to water."""
        age = self.age[y][x]

        # Condense back to water after a while
        if age > random.randint(30, 60):
            self.grid[y][x] = WATER
            self.age[y][x] = 0
            return

        # Rise quickly
        above = y - 1
        if above >= 0 and self.get(x, above) == EMPTY:
            self.swap(x, y, x, above)
            moved.add((x, above))
        else:
            # Drift sideways
            dx = random.choice([-1, 1])
            if self.get(x + dx, y) == EMPTY:
                self.swap(x, y, x + dx, y)
                moved.add((x + dx, y))
            elif above >= 0 and self.get(x + dx, above) == EMPTY:
                self.swap(x, y, x + dx, above)
                moved.add((x + dx, above))

    def count(self) -> dict:
        counts = {SAND: 0, WATER: 0, STONE: 0, FIRE: 0, PLANT: 0, STEAM: 0}
        for row in self.grid:
            for cell in row:
                if cell in counts:
                    counts[cell] += 1
        return counts


def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(30)

    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_YELLOW, -1)   # sand
    curses.init_pair(2, curses.COLOR_BLUE, -1)     # water
    curses.init_pair(3, curses.COLOR_WHITE, -1)    # stone
    curses.init_pair(4, curses.COLOR_RED, -1)      # fire
    curses.init_pair(5, curses.COLOR_GREEN, -1)    # plant
    curses.init_pair(6, curses.COLOR_CYAN, -1)     # steam
    curses.init_pair(7, curses.COLOR_MAGENTA, -1)  # cursor
    curses.init_pair(8, curses.COLOR_WHITE, -1)    # UI

    max_h, max_w = stdscr.getmaxyx()
    world_h = max_h - 2
    world_w = max_w

    world = World(world_w, world_h)

    cx, cy = world_w // 2, world_h // 2
    brush_type = SAND
    brush_size = 1
    paused = False

    def paint(px: int, py: int):
        """Paint particles at cursor position."""
        for dy in range(-brush_size + 1, brush_size):
            for dx in range(-brush_size + 1, brush_size):
                nx, ny = px + dx, py + dy
                if 0 <= nx < world_w and 0 <= ny < world_h:
                    if brush_type == EMPTY:
                        world.set(nx, ny, EMPTY)
                    elif world.get(nx, ny) == EMPTY:
                        world.set(nx, ny, brush_type)

    while True:
        key = stdscr.getch()
        if key == ord('q'):
            break
        elif key in (ord('h'), curses.KEY_LEFT):
            cx = max(0, cx - 1)
        elif key in (ord('l'), curses.KEY_RIGHT):
            cx = min(world_w - 1, cx + 1)
        elif key in (ord('k'), curses.KEY_UP):
            cy = max(0, cy - 1)
        elif key in (ord('j'), curses.KEY_DOWN):
            cy = min(world_h - 1, cy + 1)
        elif key in (ord(' '), ord('\n'), curses.KEY_ENTER):
            paint(cx, cy)
        elif key == ord('1'):
            brush_type = SAND
        elif key == ord('2'):
            brush_type = WATER
        elif key == ord('3'):
            brush_type = STONE
        elif key == ord('4'):
            brush_type = FIRE
        elif key == ord('5'):
            brush_type = PLANT
        elif key == ord('6'):
            brush_type = EMPTY
        elif key == ord('['):
            brush_size = max(1, brush_size - 1)
        elif key == ord(']'):
            brush_size = min(5, brush_size + 1)
        elif key == ord('x'):
            world.clear()
        elif key == ord('g'):
            world.gravity_down = not world.gravity_down
        elif key == ord('p'):
            paused = not paused
        elif key == curses.KEY_RESIZE:
            max_h, max_w = stdscr.getmaxyx()
            world_h = max_h - 2
            world_w = max_w
            world = World(world_w, world_h)

        if not paused:
            world.step()

        stdscr.erase()

        # Draw particles
        for y in range(world_h):
            for x in range(world_w):
                cell = world.grid[y][x]
                if cell == EMPTY:
                    continue
                chars = CHARS[cell]
                age = world.age[y][x]
                ch = chars[age % len(chars)]
                color = PARTICLE_COLORS[cell]
                attr = curses.color_pair(color)

                if cell == FIRE:
                    # Fire flickers
                    if age < 10:
                        attr |= curses.A_BOLD
                    elif age > 25:
                        attr |= curses.A_DIM
                elif cell == SAND:
                    attr |= curses.A_DIM if age > 50 else 0
                elif cell == WATER:
                    attr |= curses.A_BOLD

                if 0 <= x < max_w - 1:
                    try:
                        stdscr.addstr(y, x, ch, attr)
                    except curses.error:
                        pass

        # Draw cursor
        for dy in range(-brush_size + 1, brush_size):
            for dx in range(-brush_size + 1, brush_size):
                nx, ny = cx + dx, cy + dy
                if 0 <= ny < world_h and 0 <= nx < max_w - 1:
                    try:
                        existing = world.grid[ny][nx]
                        if existing == EMPTY:
                            ch = "·" if brush_type != EMPTY else "×"
                            stdscr.addstr(ny, nx, ch,
                                         curses.color_pair(7) | curses.A_DIM)
                        else:
                            ch = CHARS[existing][0]
                            stdscr.addstr(ny, nx, ch,
                                         curses.color_pair(PARTICLE_COLORS[existing]) | curses.A_REVERSE)
                    except curses.error:
                        pass

        # Status bar
        counts = world.count()
        brush_name = NAMES[brush_type]
        gravity = "↓" if world.gravity_down else "↑"
        try:
            status = (f" sand  brush:{brush_name}  size:{brush_size}  "
                     f"gravity:{gravity}  "
                     f"s:{counts[SAND]} w:{counts[WATER]} "
                     f"st:{counts[STONE]} f:{counts[FIRE]} "
                     f"p:{counts[PLANT]} stm:{counts[STEAM]}")
            stdscr.addstr(max_h - 2, 0, status[:max_w - 1],
                         curses.color_pair(8) | curses.A_DIM)
            controls = " 1:sand 2:water 3:stone 4:fire 5:plant 6:erase []:size g:flip q:quit"
            stdscr.addstr(max_h - 1, 0, controls[:max_w - 1], curses.A_DIM)
        except curses.error:
            pass

        stdscr.refresh()
        time.sleep(0.03)


if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
