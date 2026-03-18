#!/usr/bin/env python3
"""
Fractal Explorer — a terminal Mandelbrot & Julia set viewer by Wren

Explore the Mandelbrot set at high resolution using braille characters.
Each terminal cell encodes a 2x4 grid of points, giving you 2x the
horizontal and 4x the vertical resolution of normal text.

Press 'j' on any point in the Mandelbrot set to dive into its Julia set —
every point defines a unique one. Press 'm' to return.

Controls:
  Arrow keys / hjkl — pan
  + / =             — zoom in
  - / _             — zoom out
  j                 — enter Julia set for current center point
  m                 — return to Mandelbrot set
  f                 — cycle fractal type (mandelbrot / burning ship)
  a                 — toggle auto-zoom toward boundary
  0                 — reset view
  b                 — cycle bookmarks
  c                 — cycle color palette
  i / o             — increase / decrease max iterations
  q / Ctrl-C        — quit
"""

import curses
import math

# Braille encoding: each braille character is a 2x4 dot grid
# Dot positions map to bit offsets:
#   (0,0)=0x01  (1,0)=0x08
#   (0,1)=0x02  (1,1)=0x10
#   (0,2)=0x04  (1,2)=0x20
#   (0,3)=0x40  (1,3)=0x80
BRAILLE_BASE = 0x2800
BRAILLE_MAP = [
    [0x01, 0x08],
    [0x02, 0x10],
    [0x04, 0x20],
    [0x40, 0x80],
]

# Color palettes — each maps iteration bands to color pair indices
PALETTE_NAMES = ["electric", "fire", "ice", "mono"]
PALETTES = [
    # electric: blue -> cyan -> white -> yellow -> magenta
    [6, 6, 2, 2, 3, 3, 5, 5, 4, 4, 1, 1],
    # fire: red -> yellow -> white
    [1, 1, 1, 4, 4, 4, 5, 5, 5, 3, 3, 3],
    # ice: blue -> cyan -> white
    [6, 6, 6, 2, 2, 2, 3, 3, 5, 5, 5, 5],
    # mono: just white at different intensities
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
]

# Interesting locations to visit
BOOKMARKS = [
    # name, center_x, center_y, zoom
    ("overview", -0.5, 0.0, 1.5),
    ("seahorse valley", -0.75, 0.1, 0.05),
    ("elephant valley", 0.28, 0.008, 0.015),
    ("spiral", -0.7463, 0.1102, 0.005),
    ("mini mandelbrot", -1.768, 0.001, 0.02),
    ("lightning", -0.170337, -1.06506, 0.02),
]

# Fractal types
FRACTAL_NAMES = ["mandelbrot", "burning ship"]


def mandelbrot(cx: float, cy: float, max_iter: int) -> float:
    """Return smooth iteration count for a point in the Mandelbrot set."""
    zx, zy = 0.0, 0.0
    for i in range(max_iter):
        if zx * zx + zy * zy > 4.0:
            return _smooth_iter(i, zx, zy)
        zx, zy = zx * zx - zy * zy + cx, 2.0 * zx * zy + cy
    return max_iter


def julia(zx: float, zy: float, cx: float, cy: float, max_iter: int) -> float:
    """Return smooth iteration count for a point in a Julia set.

    In the Mandelbrot set, c varies and z starts at 0.
    In a Julia set, c is fixed and z varies — every point in the
    Mandelbrot set defines a unique Julia set.
    """
    for i in range(max_iter):
        if zx * zx + zy * zy > 4.0:
            return _smooth_iter(i, zx, zy)
        zx, zy = zx * zx - zy * zy + cx, 2.0 * zx * zy + cy
    return max_iter


def burning_ship(cx: float, cy: float, max_iter: int) -> float:
    """Return smooth iteration count for a point in the Burning Ship fractal.

    Like Mandelbrot, but takes the absolute value of zx and zy before
    squaring. This breaks the symmetry and produces a shape that looks
    like a burning ship.
    """
    zx, zy = 0.0, 0.0
    for i in range(max_iter):
        if zx * zx + zy * zy > 4.0:
            return _smooth_iter(i, zx, zy)
        zx, zy = abs(zx), abs(zy)
        zx, zy = zx * zx - zy * zy + cx, 2.0 * zx * zy + cy
    return max_iter


def burning_ship_julia(zx: float, zy: float, cx: float, cy: float,
                       max_iter: int) -> float:
    """Return smooth iteration count for a Burning Ship Julia set."""
    for i in range(max_iter):
        if zx * zx + zy * zy > 4.0:
            return _smooth_iter(i, zx, zy)
        zx, zy = abs(zx), abs(zy)
        zx, zy = zx * zx - zy * zy + cx, 2.0 * zx * zy + cy
    return max_iter


def _smooth_iter(i: int, zx: float, zy: float) -> float:
    """Compute smooth (fractional) iteration count for escape-time fractals.

    Instead of returning an integer band, this uses the distance the
    point overshot the escape radius to interpolate between iterations,
    giving smooth color gradients instead of harsh bands.
    """
    modulus = math.sqrt(zx * zx + zy * zy)
    if modulus <= 1.0:
        return float(i)
    return i + 1.0 - math.log(math.log(modulus)) / math.log(2.0)


def _compute_iter(px: float, py: float, max_iter: int,
                  fractal_type: int, julia_mode: bool,
                  julia_cx: float, julia_cy: float) -> float:
    """Dispatch to the correct fractal function."""
    if julia_mode:
        if fractal_type == 1:
            return burning_ship_julia(px, py, julia_cx, julia_cy, max_iter)
        return julia(px, py, julia_cx, julia_cy, max_iter)
    else:
        if fractal_type == 1:
            return burning_ship(px, py, max_iter)
        return mandelbrot(px, py, max_iter)


def render_braille(stdscr, width: int, height: int,
                   center_x: float, center_y: float, zoom: float,
                   max_iter: int, palette_idx: int,
                   julia_mode: bool = False,
                   julia_cx: float = 0.0, julia_cy: float = 0.0,
                   fractal_type: int = 0):
    """Render a fractal using braille characters.

    In Mandelbrot mode, each pixel is a value of c with z starting at 0.
    In Julia mode, each pixel is a starting z with c fixed.
    """
    palette = PALETTES[palette_idx % len(PALETTES)]
    palette_len = len(palette)

    # Each terminal cell = 2 wide x 4 tall in sample space
    sample_w = width * 2
    sample_h = height * 4

    aspect = 2.0  # terminal character aspect ratio compensation

    # Build iteration grid
    x_min = center_x - zoom * (sample_w / sample_h) * aspect
    x_max = center_x + zoom * (sample_w / sample_h) * aspect
    y_min = center_y - zoom
    y_max = center_y + zoom

    dx = (x_max - x_min) / sample_w
    dy = (y_max - y_min) / sample_h

    for row in range(height):
        for col in range(width):
            braille_bits = 0
            total_escape = 0.0
            n_escaped = 0

            for sub_y in range(4):
                for sub_x in range(2):
                    px = x_min + (col * 2 + sub_x) * dx
                    py = y_min + (row * 4 + sub_y) * dy

                    iters = _compute_iter(px, py, max_iter, fractal_type,
                                          julia_mode, julia_cx, julia_cy)

                    if iters < max_iter:
                        braille_bits |= BRAILLE_MAP[sub_y][sub_x]
                        total_escape += iters
                        n_escaped += 1

            if braille_bits == 0:
                continue  # all points in set — leave blank

            ch = chr(BRAILLE_BASE | braille_bits)

            # Color by average escape iteration (now smooth/fractional)
            avg_escape = total_escape / max(n_escaped, 1)
            color_idx = palette[int(avg_escape) % palette_len]
            attr = curses.color_pair(color_idx)

            # Bold for faster escapes (outer region)
            if avg_escape < max_iter * 0.3:
                attr |= curses.A_BOLD

            try:
                stdscr.addstr(row, col, ch, attr)
            except curses.error:
                pass


def find_boundary_target(center_x: float, center_y: float, zoom: float,
                         max_iter: int, fractal_type: int,
                         julia_mode: bool,
                         julia_cx: float, julia_cy: float) -> tuple:
    """Find a point near the current center that sits on the fractal boundary.

    Samples a grid of points around the center and picks the one whose
    iteration count is closest to max_iter/2 — that's the boundary between
    escaping quickly and being trapped in the set.
    """
    best_x, best_y = center_x, center_y
    best_diff = max_iter
    target = max_iter / 2.0
    steps = 15  # sample a 15x15 grid

    for iy in range(steps):
        for ix in range(steps):
            px = center_x + zoom * (ix / steps - 0.5)
            py = center_y + zoom * (iy / steps - 0.5)
            iters = _compute_iter(px, py, max_iter, fractal_type,
                                  julia_mode, julia_cx, julia_cy)
            diff = abs(iters - target)
            if diff < best_diff:
                best_diff = diff
                best_x, best_y = px, py

    return best_x, best_y


def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(50)

    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_RED, -1)
    curses.init_pair(2, curses.COLOR_CYAN, -1)
    curses.init_pair(3, curses.COLOR_WHITE, -1)
    curses.init_pair(4, curses.COLOR_YELLOW, -1)
    curses.init_pair(5, curses.COLOR_MAGENTA, -1)
    curses.init_pair(6, curses.COLOR_BLUE, -1)
    curses.init_pair(7, curses.COLOR_GREEN, -1)

    max_h, max_w = stdscr.getmaxyx()

    # View state
    center_x, center_y, zoom = BOOKMARKS[0][1], BOOKMARKS[0][2], BOOKMARKS[0][3]
    max_iter = 80
    palette_idx = 0
    bookmark_idx = 0
    needs_redraw = True

    # Julia mode state
    julia_mode = False
    julia_cx, julia_cy = 0.0, 0.0  # the c constant for Julia set
    saved_mandelbrot = None  # save Mandelbrot view to return to

    # Fractal type state
    fractal_type = 0  # 0 = mandelbrot, 1 = burning ship

    # Auto-zoom state
    auto_zoom = False
    auto_target_x, auto_target_y = center_x, center_y

    # Rendering area (leave 1 row for status bar)
    render_h = max_h - 1
    render_w = max_w - 1

    while True:
        key = stdscr.getch()
        if key == ord('q'):
            break
        elif key in (ord('h'), curses.KEY_LEFT):
            center_x -= zoom * 0.2
            auto_zoom = False
            needs_redraw = True
        elif key in (ord('l'), curses.KEY_RIGHT):
            center_x += zoom * 0.2
            auto_zoom = False
            needs_redraw = True
        elif key in (ord('k'), curses.KEY_UP):
            center_y -= zoom * 0.2
            auto_zoom = False
            needs_redraw = True
        elif key in (ord('j'), curses.KEY_DOWN):
            center_y += zoom * 0.2
            auto_zoom = False
            needs_redraw = True
        elif key in (ord('+'), ord('=')):
            zoom *= 0.7
            auto_zoom = False
            needs_redraw = True
        elif key in (ord('-'), ord('_')):
            zoom /= 0.7
            auto_zoom = False
            needs_redraw = True
        elif key == ord('0'):
            center_x, center_y, zoom = -0.5, 0.0, 1.5
            max_iter = 80
            fractal_type = 0
            auto_zoom = False
            needs_redraw = True
        elif key == ord('c'):
            palette_idx = (palette_idx + 1) % len(PALETTE_NAMES)
            needs_redraw = True
        elif key == ord('i'):
            max_iter = min(500, max_iter + 20)
            needs_redraw = True
        elif key == ord('o'):
            max_iter = max(20, max_iter - 20)
            needs_redraw = True
        elif key == ord('j') and not julia_mode:
            # Dive into Julia set — current center becomes the c constant
            julia_mode = True
            julia_cx, julia_cy = center_x, center_y
            saved_mandelbrot = (center_x, center_y, zoom)
            # Julia sets are centered at origin
            center_x, center_y, zoom = 0.0, 0.0, 1.8
            auto_zoom = False
            needs_redraw = True
        elif key == ord('m') and julia_mode:
            # Return to Mandelbrot
            julia_mode = False
            if saved_mandelbrot:
                center_x, center_y, zoom = saved_mandelbrot
            auto_zoom = False
            needs_redraw = True
        elif key == ord('f'):
            # Cycle fractal type
            fractal_type = (fractal_type + 1) % len(FRACTAL_NAMES)
            auto_zoom = False
            needs_redraw = True
        elif key == ord('a'):
            # Toggle auto-zoom
            auto_zoom = not auto_zoom
            if auto_zoom:
                auto_target_x, auto_target_y = find_boundary_target(
                    center_x, center_y, zoom, max_iter, fractal_type,
                    julia_mode, julia_cx, julia_cy)
            needs_redraw = True
        elif key == ord('b') and not julia_mode:
            bookmark_idx = (bookmark_idx + 1) % len(BOOKMARKS)
            bm = BOOKMARKS[bookmark_idx]
            center_x, center_y, zoom = bm[1], bm[2], bm[3]
            auto_zoom = False
            needs_redraw = True
        elif key == curses.KEY_RESIZE:
            max_h, max_w = stdscr.getmaxyx()
            render_h = max_h - 1
            render_w = max_w - 1
            needs_redraw = True

        # Auto-zoom: drift toward boundary and zoom in
        if auto_zoom:
            zoom *= 0.995
            # Drift center toward the target
            center_x += (auto_target_x - center_x) * 0.02
            center_y += (auto_target_y - center_y) * 0.02
            needs_redraw = True

        if needs_redraw:
            stdscr.erase()
            render_braille(stdscr, render_w, render_h,
                          center_x, center_y, zoom,
                          max_iter, palette_idx,
                          julia_mode, julia_cx, julia_cy,
                          fractal_type)

            # Status bar
            fractal_label = FRACTAL_NAMES[fractal_type].upper()
            if julia_mode:
                mode_str = f"{fractal_label} JULIA c=({julia_cx:.6f}, {julia_cy:.6f})"
                hint = "  m:back  f:fractal"
            else:
                mode_str = fractal_label
                hint = "  j:julia  f:fractal"
                for bm in BOOKMARKS:
                    if abs(center_x - bm[1]) < 0.0001 and abs(center_y - bm[2]) < 0.0001:
                        mode_str += f" [{bm[0]}]"
                        break

            auto_label = "  AUTO" if auto_zoom else ""
            status = (f" {mode_str}  "
                     f"zoom:{zoom:.2e}  "
                     f"center:({center_x:.6f}, {center_y:.6f})  "
                     f"iter:{max_iter}  "
                     f"{PALETTE_NAMES[palette_idx]}"
                     f"{auto_label}"
                     f"{hint}")
            try:
                stdscr.addstr(max_h - 1, 0, status[:max_w - 1],
                             curses.color_pair(3) | curses.A_DIM)
            except curses.error:
                pass

            stdscr.refresh()
            needs_redraw = False


if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
