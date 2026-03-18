#!/usr/bin/env python3
"""
Garden — a visual thought garden by Wren

Plant thoughts like seeds. Watch them grow. Watch them connect.
The garden is alive.

Usage:
  python3 garden.py                     — open the visual garden
  python3 garden.py plant "thought"     — plant a thought
  python3 garden.py plant -t tag "text" — plant with tags
  python3 garden.py search "query"      — search thoughts
  python3 garden.py list                — list all thoughts
  python3 garden.py remove <id>         — remove a thought

In the garden:
  Arrow keys / hjkl — pan around
  p                 — plant a new thought
  Enter             — inspect selected thought
  Tab               — cycle through thoughts
  /                 — search
  q                 — quit
"""

import curses
import sys
import time
from pathlib import Path

# Import data layer
sys.path.insert(0, str(Path(__file__).parent))
from soil import ThoughtStore, compute_connections, growth_stage, import_text

# ── visual constants ────────────────────────────────────────────

GROWTH_GLYPHS = {
    0: [".", "·"],                          # seed
    1: [",", "'", "`"],                     # sprout
    2: ["⌇", "╿", "│"],                    # sapling
    3: ["╽", "┃", "╻"],                     # plant
    4: ["✿", "❀", "✾", "❁", "✻", "⚘"],    # flower
}

GROWTH_NAMES = {0: "seed", 1: "sprout", 2: "sapling", 3: "plant", 4: "flower"}

# Tag-based color mapping
TAG_COLORS = {
    "idea": 3, "ideas": 3, "thought": 3, "abstract": 3,
    "code": 2, "tech": 2, "project": 2, "work": 2,
    "nature": 1, "life": 1, "organic": 1,
    "personal": 4, "journal": 4, "feeling": 4,
    "question": 5, "wonder": 5,
    "important": 6, "urgent": 6,
}

# Vine characters for connections
VINE_CHARS = {
    "weak": ["·", " ", "·", " "],
    "medium": ["~", "≈", "~", "∼"],
    "strong": ["─", "│", "╱", "╲"],
}


def thought_color(thought: dict) -> int:
    """Determine color pair for a thought based on tags."""
    for tag in thought.get("tags", []):
        if tag.lower() in TAG_COLORS:
            return TAG_COLORS[tag.lower()]
    # Default: color by growth stage
    stage = growth_stage(thought.get("planted_at", ""))
    if stage >= 4:
        return 3  # flowers are magenta
    elif stage >= 2:
        return 1  # plants are green
    return 7  # seeds/sprouts are white


def thought_glyph(thought: dict, tick: int) -> str:
    """Get the current glyph for a thought based on growth stage and animation."""
    stage = growth_stage(thought.get("planted_at", ""))
    glyphs = GROWTH_GLYPHS[stage]
    if stage >= 4:
        # Flowers sway — cycle glyphs slowly
        idx = (tick // 20 + hash(thought["id"])) % len(glyphs)
    else:
        idx = hash(thought["id"]) % len(glyphs)
    return glyphs[idx]


def draw_connection(stdscr, x1: int, y1: int, x2: int, y2: int,
                    strength: float, tick: int, max_h: int, max_w: int):
    """Draw a vine connection between two points."""
    if strength >= 0.5:
        chars = VINE_CHARS["strong"]
    elif strength >= 0.25:
        chars = VINE_CHARS["medium"]
    else:
        chars = VINE_CHARS["weak"]

    # Simple line drawing — step from (x1,y1) toward (x2,y2)
    dx = x2 - x1
    dy = y2 - y1
    steps = max(abs(dx), abs(dy))
    if steps == 0:
        return

    for i in range(1, steps):
        t = i / steps
        x = int(x1 + dx * t)
        y = int(y1 + dy * t)

        if 0 < y < max_h - 2 and 0 < x < max_w - 1:
            # Choose vine character based on direction
            if abs(dx) > abs(dy):
                ch = chars[0]  # horizontal-ish
            elif abs(dy) > abs(dx):
                ch = chars[1] if len(chars) > 1 else chars[0]  # vertical-ish
            elif dx * dy > 0:
                ch = chars[2] if len(chars) > 2 else chars[0]  # diagonal
            else:
                ch = chars[3] if len(chars) > 3 else chars[0]

            # Animate: skip some vine chars for "growing" effect
            if (i + tick // 10) % 3 == 0 and strength < 0.4:
                continue

            try:
                stdscr.addstr(y, x, ch, curses.color_pair(8) | curses.A_DIM)
            except curses.error:
                pass


# ── curses garden view ──────────────────────────────────────────

def run_garden(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(100)

    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_GREEN, -1)     # nature/default
    curses.init_pair(2, curses.COLOR_CYAN, -1)      # tech/code
    curses.init_pair(3, curses.COLOR_MAGENTA, -1)   # ideas/flowers
    curses.init_pair(4, curses.COLOR_YELLOW, -1)    # personal
    curses.init_pair(5, curses.COLOR_RED, -1)       # questions
    curses.init_pair(6, curses.COLOR_RED, -1)       # important
    curses.init_pair(7, curses.COLOR_WHITE, -1)     # seeds/default
    curses.init_pair(8, curses.COLOR_BLUE, -1)      # connections

    max_h, max_w = stdscr.getmaxyx()
    view_h = max_h - 3  # status + controls
    view_w = max_w

    store = ThoughtStore()
    thoughts = store.all_thoughts()
    connections = compute_connections(thoughts)

    view_x, view_y = 0.0, 0.0
    selected_idx = 0 if thoughts else -1
    mode = "view"  # "view" | "plant" | "inspect" | "search"
    input_buffer = ""
    tick = 0
    needs_reload = False

    # Center view on thoughts
    if thoughts:
        avg_x = sum(t["x"] for t in thoughts) / len(thoughts)
        avg_y = sum(t["y"] for t in thoughts) / len(thoughts)
        view_x = avg_x - view_w // 2
        view_y = avg_y - view_h // 2

    while True:
        key = stdscr.getch()
        tick += 1

        if needs_reload:
            thoughts = store.all_thoughts()
            connections = compute_connections(thoughts)
            needs_reload = False

        # ── input handling ──
        if mode == "view":
            if key == ord('q'):
                break
            elif key in (ord('h'), curses.KEY_LEFT):
                view_x -= 3
            elif key in (ord('l'), curses.KEY_RIGHT):
                view_x += 3
            elif key in (ord('k'), curses.KEY_UP):
                view_y -= 2
            elif key in (ord('j'), curses.KEY_DOWN):
                view_y += 2
            elif key == ord('p'):
                mode = "plant"
                input_buffer = ""
            elif key == ord('/'):
                mode = "search"
                input_buffer = ""
            elif key == ord('\t') and thoughts:
                selected_idx = (selected_idx + 1) % len(thoughts)
                # Pan to selected thought
                t = thoughts[selected_idx]
                view_x = t["x"] - view_w // 2
                view_y = t["y"] - view_h // 2
            elif key in (ord('\n'), curses.KEY_ENTER, 10) and thoughts and selected_idx >= 0:
                mode = "inspect"
            elif key == curses.KEY_RESIZE:
                max_h, max_w = stdscr.getmaxyx()
                view_h = max_h - 3
                view_w = max_w

        elif mode == "plant":
            if key == 27:  # ESC
                mode = "view"
                input_buffer = ""
            elif key in (ord('\n'), curses.KEY_ENTER, 10):
                if input_buffer.strip():
                    # Parse tags from #hashtags
                    text_parts = []
                    tags = []
                    for word in input_buffer.split():
                        if word.startswith("#") and len(word) > 1:
                            tags.append(word[1:])
                        else:
                            text_parts.append(word)
                    text = " ".join(text_parts)
                    if text:
                        store.plant(text, tags=tags,
                                   garden_width=view_w + 20,
                                   garden_height=view_h + 20)
                        needs_reload = True
                mode = "view"
                input_buffer = ""
            elif key == curses.KEY_BACKSPACE or key == 127:
                input_buffer = input_buffer[:-1]
            elif 32 <= key <= 126:
                input_buffer += chr(key)

        elif mode == "search":
            if key == 27:
                mode = "view"
                input_buffer = ""
            elif key in (ord('\n'), curses.KEY_ENTER, 10):
                if input_buffer.strip():
                    results = store.search(input_buffer.strip())
                    if results:
                        # Jump to first result
                        for i, t in enumerate(thoughts):
                            if t["id"] == results[0]["id"]:
                                selected_idx = i
                                view_x = t["x"] - view_w // 2
                                view_y = t["y"] - view_h // 2
                                break
                mode = "view"
                input_buffer = ""
            elif key == curses.KEY_BACKSPACE or key == 127:
                input_buffer = input_buffer[:-1]
            elif 32 <= key <= 126:
                input_buffer += chr(key)

        elif mode == "inspect":
            if key in (27, ord('q'), ord('\n'), 10):
                mode = "view"
            elif key == ord('d') and thoughts and selected_idx >= 0:
                store.remove(thoughts[selected_idx]["id"])
                needs_reload = True
                selected_idx = max(0, selected_idx - 1)
                mode = "view"

        # ── render ──
        stdscr.erase()

        # Draw connections first (behind plants)
        for id_a, id_b, strength in connections:
            t_a = next((t for t in thoughts if t["id"] == id_a), None)
            t_b = next((t for t in thoughts if t["id"] == id_b), None)
            if t_a and t_b:
                sx_a = int(t_a["x"] - view_x)
                sy_a = int(t_a["y"] - view_y)
                sx_b = int(t_b["x"] - view_x)
                sy_b = int(t_b["y"] - view_y)
                # Only draw if at least one end is visible
                if (-10 < sx_a < view_w + 10 and -10 < sy_a < view_h + 10) or \
                   (-10 < sx_b < view_w + 10 and -10 < sy_b < view_h + 10):
                    draw_connection(stdscr, sx_a, sy_a, sx_b, sy_b,
                                  strength, tick, max_h, max_w)

        # Draw thoughts
        for i, thought in enumerate(thoughts):
            sx = int(thought["x"] - view_x)
            sy = int(thought["y"] - view_y)

            if 0 <= sy < view_h and 0 <= sx < max_w - 1:
                glyph = thought_glyph(thought, tick)
                col = thought_color(thought)
                attr = curses.color_pair(col)
                stage = growth_stage(thought.get("planted_at", ""))

                if stage >= 3:
                    attr |= curses.A_BOLD
                elif stage == 0:
                    attr |= curses.A_DIM

                # Highlight selected
                if i == selected_idx:
                    attr |= curses.A_REVERSE

                try:
                    stdscr.addstr(sy, sx, glyph, attr)

                    # Show truncated text next to mature plants
                    if stage >= 2:
                        label = thought["text"][:20]
                        if len(thought["text"]) > 20:
                            label += "…"
                        if sx + 2 + len(label) < max_w - 1:
                            stdscr.addstr(sy, sx + 2, label,
                                        curses.color_pair(col) | curses.A_DIM)
                except curses.error:
                    pass

        # ── status bar ──
        n_conn = len(connections)
        status_line = max_h - 2

        if mode == "view":
            status = (f" ~ garden ~  {len(thoughts)} thoughts  "
                     f"{n_conn} connections")
            if thoughts and selected_idx >= 0 and selected_idx < len(thoughts):
                t = thoughts[selected_idx]
                stage_name = GROWTH_NAMES[growth_stage(t.get("planted_at", ""))]
                status += f"  selected: {stage_name}"
            try:
                stdscr.addstr(status_line, 0, status[:max_w - 1],
                             curses.color_pair(1) | curses.A_DIM)
                controls = " arrows:pan  tab:next  enter:inspect  p:plant  /:search  q:quit"
                stdscr.addstr(max_h - 1, 0, controls[:max_w - 1], curses.A_DIM)
            except curses.error:
                pass

        elif mode == "plant":
            prompt = f" plant: {input_buffer}█"
            try:
                stdscr.addstr(status_line, 0, prompt[:max_w - 1],
                             curses.color_pair(1) | curses.A_BOLD)
                stdscr.addstr(max_h - 1, 0,
                             " type your thought (#tag for tags)  enter:plant  esc:cancel"[:max_w - 1],
                             curses.A_DIM)
            except curses.error:
                pass

        elif mode == "search":
            prompt = f" search: {input_buffer}█"
            try:
                stdscr.addstr(status_line, 0, prompt[:max_w - 1],
                             curses.color_pair(2) | curses.A_BOLD)
                stdscr.addstr(max_h - 1, 0,
                             " enter:find  esc:cancel"[:max_w - 1],
                             curses.A_DIM)
            except curses.error:
                pass

        elif mode == "inspect" and thoughts and selected_idx >= 0:
            t = thoughts[selected_idx]
            stage = growth_stage(t.get("planted_at", ""))
            glyph = thought_glyph(t, tick)

            # Draw inspection overlay
            panel_w = min(50, max_w - 4)
            panel_h = 10
            panel_x = (max_w - panel_w) // 2
            panel_y = (max_h - panel_h) // 2

            # Border
            try:
                for y in range(panel_y, panel_y + panel_h):
                    stdscr.addstr(y, panel_x, " " * panel_w,
                                curses.color_pair(7))

                stdscr.addstr(panel_y, panel_x,
                             f" {glyph} {GROWTH_NAMES[stage]} ",
                             curses.color_pair(thought_color(t)) | curses.A_BOLD)

                # Text (word-wrapped)
                text = t["text"]
                y = panel_y + 2
                while text and y < panel_y + panel_h - 3:
                    line = text[:panel_w - 4]
                    text = text[panel_w - 4:]
                    stdscr.addstr(y, panel_x + 2, line,
                                curses.color_pair(7) | curses.A_BOLD)
                    y += 1

                # Tags
                if t.get("tags"):
                    tag_str = " ".join(f"#{tag}" for tag in t["tags"])
                    stdscr.addstr(y, panel_x + 2, tag_str[:panel_w - 4],
                                curses.color_pair(2) | curses.A_DIM)
                    y += 1

                # Connections
                my_conns = [(a, b, s) for a, b, s in connections
                           if a == t["id"] or b == t["id"]]
                if my_conns:
                    y += 1
                    stdscr.addstr(y, panel_x + 2,
                                f"connected to {len(my_conns)} thought(s)",
                                curses.A_DIM)

                # Controls
                stdscr.addstr(panel_y + panel_h - 1, panel_x + 2,
                             "esc:close  d:delete",
                             curses.A_DIM)
            except curses.error:
                pass

        stdscr.refresh()
        time.sleep(0.05)


# ── CLI ─────────────────────────────────────────────────────────

def c(text, color):
    codes = {"green": 32, "cyan": 36, "yellow": 33, "magenta": 35,
             "red": 31, "white": 97, "grey": 90}
    return f"\033[{codes.get(color, 37)}m{text}\033[0m"

def dim(text): return f"\033[2m{text}\033[0m"
def bold(text): return f"\033[1m{text}\033[0m"

def _time_ago(iso_str: str) -> str:
    from datetime import datetime
    try:
        dt = datetime.fromisoformat(iso_str)
        delta = datetime.now() - dt
        if delta.days > 0:
            return f"{delta.days}d ago"
        hours = delta.seconds // 3600
        if hours > 0:
            return f"{hours}h ago"
        minutes = delta.seconds // 60
        return f"{minutes}m ago" if minutes > 0 else "just now"
    except Exception:
        return ""


def cli_plant(args: list[str]):
    store = ThoughtStore()
    tags = []
    text_parts = []
    i = 0
    while i < len(args):
        if args[i] == "-t" and i + 1 < len(args):
            tags.append(args[i + 1])
            i += 2
        else:
            text_parts.append(args[i])
            i += 1
    text = " ".join(text_parts)
    if not text:
        print(f"  {dim('usage: garden plant \"your thought\" [-t tag]')}")
        return
    thought = store.plant(text, tags=tags)
    tid = thought["id"]
    tag_str = " ".join(f"#{t}" for t in tags) if tags else ""
    print(f"  {c('⌱', 'green')} planted: {text}  {dim(tag_str)}  {dim(f'[{tid}]')}")


def cli_list():
    store = ThoughtStore()
    thoughts = store.all_thoughts()
    if not thoughts:
        print(f"  {dim('the garden is empty. plant something:')}")
        print(f"  {dim('  garden plant \"your first thought\"')}")
        return
    connections = compute_connections(thoughts)
    print()
    print(f"  {bold(c('garden', 'green'))}  {dim(f'{len(thoughts)} thoughts, {len(connections)} connections')}")
    print()
    for t in sorted(thoughts, key=lambda x: x.get("planted_at", "")):
        stage = growth_stage(t.get("planted_at", ""))
        glyph = GROWTH_GLYPHS[stage][0]
        name = GROWTH_NAMES[stage]
        age = _time_ago(t.get("planted_at", ""))
        tags = " ".join(c(f"#{tag}", "cyan") for tag in t.get("tags", []))
        text = t["text"]
        if len(text) > 45:
            text = text[:42] + "..."
        tid = t["id"]
        print(f"  {c(glyph, 'green')} {text}  {tags}  {dim(f'{name} · {age}')}  {dim(f'[{tid}]')}")
    print()


def cli_search(query: str):
    store = ThoughtStore()
    results = store.search(query)
    if results:
        print()
        for t in results:
            glyph = GROWTH_GLYPHS[growth_stage(t.get("planted_at", ""))][0]
            tid = t["id"]
            print(f"  {c(glyph, 'green')} {t['text']}  {dim(f'[{tid}]')}")
        print()
    else:
        print(f"  {dim('nothing found.')}")


def cli_view():
    """Print a static map of the garden — works everywhere, screenshots well."""
    store = ThoughtStore()
    thoughts = store.all_thoughts()
    connections = compute_connections(thoughts)

    if not thoughts:
        print(f"  {dim('the garden is empty.')}")
        return

    # Find bounds
    min_x = min(t["x"] for t in thoughts)
    max_x = max(t["x"] for t in thoughts)
    min_y = min(t["y"] for t in thoughts)
    max_y = max(t["y"] for t in thoughts)

    # Add padding
    min_x -= 2
    min_y -= 1
    max_x += 25  # room for labels
    max_y += 1

    width = int(max_x - min_x) + 1
    height = int(max_y - min_y) + 1

    # Build canvas
    canvas = {}  # (x, y) -> (char, color_name)

    # Draw connections first
    for id_a, id_b, strength in connections:
        t_a = next((t for t in thoughts if t["id"] == id_a), None)
        t_b = next((t for t in thoughts if t["id"] == id_b), None)
        if not t_a or not t_b:
            continue
        x1, y1 = int(t_a["x"] - min_x), int(t_a["y"] - min_y)
        x2, y2 = int(t_b["x"] - min_x), int(t_b["y"] - min_y)

        dx, dy = x2 - x1, y2 - y1
        steps = max(abs(dx), abs(dy))
        if steps == 0:
            continue

        vine = "~" if strength < 0.4 else "─"
        for i in range(1, steps):
            t = i / steps
            x = int(x1 + dx * t)
            y = int(y1 + dy * t)
            if (x, y) not in canvas:
                canvas[(x, y)] = (vine, "blue")

    # Draw thoughts on top
    for thought in thoughts:
        sx = int(thought["x"] - min_x)
        sy = int(thought["y"] - min_y)
        stage = growth_stage(thought.get("planted_at", ""))
        glyphs = GROWTH_GLYPHS[stage]
        glyph = glyphs[hash(thought["id"]) % len(glyphs)]

        col = "green"
        for tag in thought.get("tags", []):
            if tag in TAG_COLORS:
                col = {1: "green", 2: "cyan", 3: "magenta", 4: "yellow",
                       5: "red", 6: "red", 7: "white"}.get(TAG_COLORS[tag], "green")
                break

        canvas[(sx, sy)] = (glyph, col)

        # Label
        label = thought["text"][:20]
        if len(thought["text"]) > 20:
            label += "…"
        for i, ch in enumerate(label):
            lx = sx + 2 + i
            if (lx, sy) not in canvas or canvas[(lx, sy)][1] == "blue":
                canvas[(lx, sy)] = (ch, "grey")

    # Render
    print()
    print(f"  {bold(c('~ garden ~', 'green'))}  {dim(f'{len(thoughts)} thoughts, {len(connections)} connections')}")
    print()

    for y in range(height):
        line = "  "
        for x in range(width):
            if (x, y) in canvas:
                ch, col = canvas[(x, y)]
                line += c(ch, col)
            else:
                line += " "
        # Only print if line has content
        stripped = line.replace("\033[", "").strip()
        if any(ch.isalnum() or ch in "✿❀✾❁✻⚘╽┃╻⌇╿│·,.'`~─" for ch in stripped):
            print(line)

    print()

    # Legend
    print(f"  {c('✿', 'green')} flower (7d+)  {c('╽', 'green')} plant (3-7d)  {c('⌇', 'green')} sapling (1-3d)  {c(',', 'green')} sprout (<1d)  {c('·', 'green')} seed (<1h)")
    print(f"  {c('~', 'blue')} weak link   {c('─', 'blue')} strong link")
    print()


def main():
    args = sys.argv[1:]

    if not args:
        curses.wrapper(run_garden)
        return

    cmd = args[0].lower()

    if cmd == "plant":
        cli_plant(args[1:])
    elif cmd == "list":
        cli_list()
    elif cmd == "view":
        cli_view()
    elif cmd == "search" and len(args) > 1:
        cli_search(" ".join(args[1:]))
    elif cmd == "remove" and len(args) > 1:
        store = ThoughtStore()
        store.remove(args[1])
        print(f"  {dim(f'removed [{args[1]}]')}")

    elif cmd == "import" and len(args) > 1:
        filepath = " ".join(args[1:])
        tags = []
        parts = args[1:]
        filepath_parts = []
        i = 0
        while i < len(parts):
            if parts[i] == "-t" and i + 1 < len(parts):
                tags.append(parts[i + 1])
                i += 2
            elif parts[i] in ("--animate", "-a"):
                i += 1
            else:
                filepath_parts.append(parts[i])
                i += 1
        filepath = " ".join(filepath_parts)

        try:
            text = Path(filepath).read_text()
        except OSError:
            print(f"  {c('✗', 'red')} could not read: {filepath}")
            return

        sentences = import_text(text)
        if not sentences:
            print(f"  {dim('no thoughts found in the text.')}")
            return

        store = ThoughtStore()
        animate = "--animate" in args or "-a" in args

        print(f"\n  {c('⌱', 'green')} importing {len(sentences)} thoughts from {Path(filepath).name}")
        print()

        import time as _time

        prev_connections = 0
        for idx, sent in enumerate(sentences):
            thought = store.plant(sent, tags=tags)
            text_preview = sent[:55] + ("…" if len(sent) > 55 else "")

            # Show the thought being planted
            stage_char = "·"
            print(f"    {c(stage_char, 'green')} {text_preview}")

            if animate:
                # Check for new connections
                all_thoughts = store.all_thoughts()
                connections = compute_connections(all_thoughts)
                new_conns = len(connections) - prev_connections
                if new_conns > 0:
                    # Show connections forming
                    new_pairs = connections[-(new_conns):]
                    for id_a, id_b, strength in new_pairs[:3]:
                        t_a = next((t for t in all_thoughts if t["id"] == id_a), None)
                        t_b = next((t for t in all_thoughts if t["id"] == id_b), None)
                        if t_a and t_b:
                            vine = "─" if strength > 0.4 else "~"
                            a_text = t_a["text"][:20]
                            b_text = t_b["text"][:20]
                            print(f"      {c(vine * 3, 'blue')} {dim(f'{a_text}… ↔ {b_text}…')}")
                    if new_conns > 3:
                        print(f"      {dim(f'  +{new_conns - 3} more connections')}")
                prev_connections = len(connections)
                _time.sleep(0.3)

        thoughts = store.all_thoughts()
        connections = compute_connections(thoughts)
        print(f"\n  {dim(f'{len(thoughts)} total thoughts, {len(connections)} connections')}")
        print()

    else:
        print(f"  {dim('commands: plant, list, view, search, import, remove')}")
        print(f"  {dim('or just: garden  (opens visual garden)')}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
