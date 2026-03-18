#!/usr/bin/env python3
"""
etch — a terminal drawing toy by Wren

Move the cursor. Leave a trail. Make something.

Controls:
  Arrow keys / hjkl — move & draw
  SPACE              — pick up / put down the pen
  1-6                — change brush character
  c                  — change color
  x                  — clear canvas
  s                  — save drawing to file
  q                  — quit
"""

import curses
import datetime
from pathlib import Path

BRUSHES = ["█", "░", "▒", "▓", "·", "○"]
COLOR_NAMES = ["white", "red", "green", "yellow", "blue", "magenta", "cyan"]


def main(stdscr):
    curses.curs_set(1)
    stdscr.nodelay(False)
    stdscr.timeout(-1)

    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_WHITE, -1)
    curses.init_pair(2, curses.COLOR_RED, -1)
    curses.init_pair(3, curses.COLOR_GREEN, -1)
    curses.init_pair(4, curses.COLOR_YELLOW, -1)
    curses.init_pair(5, curses.COLOR_BLUE, -1)
    curses.init_pair(6, curses.COLOR_MAGENTA, -1)
    curses.init_pair(7, curses.COLOR_CYAN, -1)
    curses.init_pair(8, curses.COLOR_WHITE, curses.COLOR_WHITE)  # cursor highlight

    max_h, max_w = stdscr.getmaxyx()
    canvas_h = max_h - 2  # leave room for status
    canvas_w = max_w

    # Canvas stores (char, color_pair) or None
    canvas: dict[tuple[int, int], tuple[str, int]] = {}

    # Cursor state
    cx, cy = canvas_w // 2, canvas_h // 2
    pen_down = True
    brush_idx = 0
    color_idx = 0

    def draw_canvas():
        stdscr.erase()
        # Draw all marks
        for (x, y), (ch, col) in canvas.items():
            if 0 <= y < canvas_h and 0 <= x < canvas_w - 1:
                try:
                    stdscr.addstr(y, x, ch, curses.color_pair(col + 1) | curses.A_BOLD)
                except curses.error:
                    pass

        # Draw cursor
        if 0 <= cy < canvas_h and 0 <= cx < canvas_w - 1:
            existing = canvas.get((cx, cy))
            if existing:
                try:
                    stdscr.addstr(cy, cx, existing[0],
                                curses.color_pair(existing[1] + 1) | curses.A_REVERSE)
                except curses.error:
                    pass
            else:
                try:
                    stdscr.addstr(cy, cx, BRUSHES[brush_idx],
                                curses.A_BLINK | curses.A_DIM)
                except curses.error:
                    pass

        # Status bar
        pen_state = "▼ drawing" if pen_down else "▲ moving"
        brush_ch = BRUSHES[brush_idx]
        col_name = COLOR_NAMES[color_idx]
        marks = len(canvas)
        status = (f" etch  {pen_state}  brush:{brush_ch}  "
                 f"color:{col_name}  marks:{marks}  "
                 f"({cx},{cy})")
        controls = "  space:pen 1-6:brush c:color x:clear s:save q:quit"
        try:
            stdscr.addstr(max_h - 2, 0, status[:canvas_w - 1],
                         curses.color_pair(color_idx + 1) | curses.A_DIM)
            stdscr.addstr(max_h - 1, 0, controls[:canvas_w - 1],
                         curses.A_DIM)
        except curses.error:
            pass

        stdscr.move(cy, min(cx, canvas_w - 2))
        stdscr.refresh()

    def move(dx: int, dy: int):
        nonlocal cx, cy
        new_x = max(0, min(canvas_w - 2, cx + dx))
        new_y = max(0, min(canvas_h - 1, cy + dy))

        if pen_down:
            canvas[(cx, cy)] = (BRUSHES[brush_idx], color_idx)
            # Also mark the destination
            canvas[(new_x, new_y)] = (BRUSHES[brush_idx], color_idx)

        cx, cy = new_x, new_y

    def save_drawing():
        """Save the canvas as a text file."""
        if not canvas:
            return "nothing to save"

        # Find bounds
        min_x = min(x for x, _ in canvas)
        max_x = max(x for x, _ in canvas)
        min_y = min(y for _, y in canvas)
        max_y = max(y for _, y in canvas)

        lines = []
        for y in range(min_y, max_y + 1):
            line = ""
            for x in range(min_x, max_x + 1):
                if (x, y) in canvas:
                    line += canvas[(x, y)][0]
                else:
                    line += " "
            lines.append(line.rstrip())

        # Save to workspace
        workspace = Path(__file__).resolve().parent.parent.parent
        drawings_dir = workspace / "drawings"
        drawings_dir.mkdir(exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = drawings_dir / f"etch-{timestamp}.txt"
        filename.write_text('\n'.join(lines) + '\n')
        return f"saved to drawings/etch-{timestamp}.txt"

    draw_canvas()
    save_msg = ""
    save_msg_tick = 0

    while True:
        key = stdscr.getch()

        if key == ord('q'):
            break
        elif key in (ord('h'), curses.KEY_LEFT):
            move(-1, 0)
        elif key in (ord('l'), curses.KEY_RIGHT):
            move(1, 0)
        elif key in (ord('k'), curses.KEY_UP):
            move(0, -1)
        elif key in (ord('j'), curses.KEY_DOWN):
            move(0, 1)
        elif key == ord(' '):
            pen_down = not pen_down
        elif key == ord('c'):
            color_idx = (color_idx + 1) % len(COLOR_NAMES)
        elif key == ord('x'):
            canvas.clear()
        elif key == ord('s'):
            save_msg = save_drawing()
            save_msg_tick = 30
        elif ord('1') <= key <= ord('6'):
            brush_idx = key - ord('1')
        elif key == curses.KEY_RESIZE:
            max_h, max_w = stdscr.getmaxyx()
            canvas_h = max_h - 2
            canvas_w = max_w

        draw_canvas()

        if save_msg_tick > 0:
            try:
                stdscr.addstr(max_h - 1, canvas_w - len(save_msg) - 2,
                             save_msg, curses.color_pair(3))
            except curses.error:
                pass
            stdscr.refresh()
            save_msg_tick -= 1


if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
