#!/usr/bin/env python3
"""
Maze — by Wren

Watch a maze being carved, then watch it being solved.
Computation made visible.

Generation: recursive backtracking (depth-first)
Solving: A* search (finds the shortest path)

Controls:
  SPACE / ENTER — start generation / start solving / regenerate
  +/-           — speed up / slow down
  q             — quit
"""

import curses
import random
import time
import heapq
from enum import Enum

class CellState(Enum):
    WALL = 0
    PATH = 1
    VISITED = 2    # solver visited
    SOLUTION = 3   # final solution path
    START = 4
    END = 5
    FRONTIER = 6   # solver frontier (being considered)


# Characters
CHARS = {
    CellState.WALL: "█",
    CellState.PATH: " ",
    CellState.VISITED: "·",
    CellState.SOLUTION: "◆",
    CellState.START: "S",
    CellState.END: "E",
    CellState.FRONTIER: "○",
}

COLORS = {
    CellState.WALL: 1,
    CellState.PATH: 2,
    CellState.VISITED: 3,
    CellState.SOLUTION: 4,
    CellState.START: 5,
    CellState.END: 5,
    CellState.FRONTIER: 6,
}


class Maze:
    def __init__(self, width: int, height: int):
        # Ensure odd dimensions for clean maze grid
        self.w = width if width % 2 == 1 else width - 1
        self.h = height if height % 2 == 1 else height - 1
        self.grid = [[CellState.WALL] * self.w for _ in range(self.h)]
        self.start = (1, 1)
        self.end = (self.w - 2, self.h - 2)

        # Generation state
        self.gen_stack: list[tuple[int, int]] = []
        self.gen_done = False

        # Solving state
        self.solve_open: list[tuple[float, int, int, int]] = []  # (f, counter, x, y)
        self.solve_came_from: dict[tuple[int, int], tuple[int, int]] = {}
        self.solve_g_score: dict[tuple[int, int], float] = {}
        self.solve_done = False
        self.solve_started = False
        self.solve_counter = 0

    def init_generation(self):
        """Start the maze generation process."""
        sx, sy = self.start
        self.grid[sy][sx] = CellState.PATH
        self.gen_stack = [(sx, sy)]
        self.gen_done = False

    def step_generation(self, steps: int = 1) -> bool:
        """Advance maze generation by N steps. Returns True when complete."""
        for _ in range(steps):
            if not self.gen_stack:
                self.gen_done = True
                # Mark start and end
                sx, sy = self.start
                ex, ey = self.end
                self.grid[sy][sx] = CellState.START
                self.grid[ey][ex] = CellState.END
                return True

            cx, cy = self.gen_stack[-1]

            # Find unvisited neighbors (2 cells away)
            neighbors = []
            for dx, dy in [(0, -2), (0, 2), (-2, 0), (2, 0)]:
                nx, ny = cx + dx, cy + dy
                if 0 < nx < self.w - 1 and 0 < ny < self.h - 1:
                    if self.grid[ny][nx] == CellState.WALL:
                        neighbors.append((nx, ny, cx + dx // 2, cy + dy // 2))

            if neighbors:
                # Choose random neighbor
                nx, ny, wx, wy = random.choice(neighbors)
                # Carve path
                self.grid[wy][wx] = CellState.PATH
                self.grid[ny][nx] = CellState.PATH
                self.gen_stack.append((nx, ny))
            else:
                # Backtrack
                self.gen_stack.pop()

        return self.gen_done

    def init_solving(self):
        """Start A* solving."""
        sx, sy = self.start
        ex, ey = self.end
        self.solve_started = True
        self.solve_done = False
        self.solve_came_from = {}
        self.solve_g_score = {(sx, sy): 0}
        h = abs(ex - sx) + abs(ey - sy)
        self.solve_counter = 0
        self.solve_open = [(h, 0, sx, sy)]

    def step_solving(self, steps: int = 1) -> bool:
        """Advance A* by N steps. Returns True when solved."""
        ex, ey = self.end

        for _ in range(steps):
            if not self.solve_open:
                self.solve_done = True
                return True

            _, _, cx, cy = heapq.heappop(self.solve_open)

            if (cx, cy) == (ex, ey):
                # Found the end — trace back the solution
                self._trace_solution()
                self.solve_done = True
                return True

            # Mark as visited
            if self.grid[cy][cx] not in (CellState.START, CellState.END):
                self.grid[cy][cx] = CellState.VISITED

            current_g = self.solve_g_score.get((cx, cy), float('inf'))

            for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                nx, ny = cx + dx, cy + dy
                if not (0 <= nx < self.w and 0 <= ny < self.h):
                    continue
                if self.grid[ny][nx] == CellState.WALL:
                    continue

                new_g = current_g + 1
                if new_g < self.solve_g_score.get((nx, ny), float('inf')):
                    self.solve_g_score[(nx, ny)] = new_g
                    h = abs(ex - nx) + abs(ey - ny)
                    f = new_g + h
                    self.solve_counter += 1
                    heapq.heappush(self.solve_open, (f, self.solve_counter, nx, ny))
                    self.solve_came_from[(nx, ny)] = (cx, cy)

                    if self.grid[ny][nx] not in (CellState.START, CellState.END, CellState.VISITED):
                        self.grid[ny][nx] = CellState.FRONTIER

        return self.solve_done

    def _trace_solution(self):
        """Trace back from end to start, marking the solution path."""
        cx, cy = self.end
        while (cx, cy) in self.solve_came_from:
            px, py = self.solve_came_from[(cx, cy)]
            if self.grid[py][px] not in (CellState.START, CellState.END):
                self.grid[py][px] = CellState.SOLUTION
            cx, cy = px, py
        # Mark end
        ex, ey = self.end
        self.grid[ey][ex] = CellState.END


class Phase(Enum):
    WAITING = "press space to generate"
    GENERATING = "generating..."
    GEN_DONE = "press space to solve"
    SOLVING = "solving..."
    SOLVED = "press space to regenerate"


def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(20)

    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_WHITE)   # wall
    curses.init_pair(2, curses.COLOR_BLACK, -1)                   # path
    curses.init_pair(3, curses.COLOR_BLUE, -1)                    # visited
    curses.init_pair(4, curses.COLOR_YELLOW, -1)                  # solution
    curses.init_pair(5, curses.COLOR_GREEN, -1)                   # start/end
    curses.init_pair(6, curses.COLOR_CYAN, -1)                    # frontier
    curses.init_pair(7, curses.COLOR_MAGENTA, -1)                 # UI

    max_h, max_w = stdscr.getmaxyx()
    maze_h = max_h - 2
    maze_w = max_w

    maze = Maze(maze_w, maze_h)
    phase = Phase.WAITING
    speed = 5  # steps per frame
    solution_len = 0

    while True:
        key = stdscr.getch()
        if key == ord('q'):
            break
        elif key in (ord(' '), ord('\n'), curses.KEY_ENTER):
            if phase == Phase.WAITING:
                maze.init_generation()
                phase = Phase.GENERATING
            elif phase == Phase.GEN_DONE:
                maze.init_solving()
                phase = Phase.SOLVING
            elif phase == Phase.SOLVED:
                maze = Maze(maze_w, maze_h)
                maze.init_generation()
                phase = Phase.GENERATING
        elif key in (ord('+'), ord('=')):
            speed = min(50, speed + 2)
        elif key in (ord('-'), ord('_')):
            speed = max(1, speed - 1)
        elif key == curses.KEY_RESIZE:
            max_h, max_w = stdscr.getmaxyx()
            maze_h = max_h - 2
            maze_w = max_w
            maze = Maze(maze_w, maze_h)
            phase = Phase.WAITING

        # Advance
        if phase == Phase.GENERATING:
            if maze.step_generation(speed):
                phase = Phase.GEN_DONE
        elif phase == Phase.SOLVING:
            if maze.step_solving(speed):
                phase = Phase.SOLVED
                solution_len = sum(
                    1 for row in maze.grid for c in row
                    if c == CellState.SOLUTION
                ) + 2  # +start +end

        # Draw
        stdscr.erase()

        for y in range(min(maze.h, max_h - 2)):
            for x in range(min(maze.w, max_w - 1)):
                cell = maze.grid[y][x]
                ch = CHARS[cell]
                color = COLORS[cell]
                attr = curses.color_pair(color)

                if cell == CellState.WALL:
                    attr = curses.color_pair(1)
                elif cell == CellState.SOLUTION:
                    attr |= curses.A_BOLD
                elif cell == CellState.START or cell == CellState.END:
                    attr |= curses.A_BOLD
                elif cell == CellState.FRONTIER:
                    attr |= curses.A_DIM

                try:
                    stdscr.addstr(y, x, ch, attr)
                except curses.error:
                    pass

        # Generation cursor (show where we're carving)
        if phase == Phase.GENERATING and maze.gen_stack:
            gx, gy = maze.gen_stack[-1]
            if 0 <= gy < max_h - 2 and 0 <= gx < max_w - 1:
                try:
                    stdscr.addstr(gy, gx, "▪", curses.color_pair(7) | curses.A_BOLD)
                except curses.error:
                    pass

        # Status
        try:
            status = f" maze  {phase.value}  speed:{speed}"
            if phase == Phase.SOLVED:
                visited = sum(
                    1 for row in maze.grid for c in row
                    if c in (CellState.VISITED, CellState.SOLUTION)
                )
                status += f"  path:{solution_len}  explored:{visited}"
            stdscr.addstr(max_h - 1, 0, status[:max_w - 1],
                         curses.color_pair(7) | curses.A_DIM)
        except curses.error:
            pass

        stdscr.refresh()
        time.sleep(0.02)


if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
