#!/usr/bin/env python3
"""
Wren's Living Workspace — an isometric pixel-art room rendered with Three.js.
Python HTTP server + inline HTML/JS, single file.
"""

import http.server
import json
import importlib.util
import datetime
import random
from pathlib import Path

PORT = 8080
WORKSPACE = Path(__file__).resolve().parent.parent.parent
PROJECTS_DIR = WORKSPACE / "projects"


# ── Data Sources ─────────────────────────────────────────────────

def load_evolve():
    """Import evolve.py to read its module-level constants."""
    try:
        spec = importlib.util.spec_from_file_location(
            "evolve", PROJECTS_DIR / "evolve" / "evolve.py"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        behaviors = []
        for expr, gen_born in mod.BEHAVIORS:
            try:
                result = eval(expr, {
                    "MOOD": mod.MOOD, "WORDS": mod.WORDS,
                    "FOSSILS": mod.FOSSILS, "GENERATION": mod.GENERATION,
                    "random": random, "os": __import__("os"),
                    "datetime": datetime, "Path": Path,
                    "__file__": str(PROJECTS_DIR / "evolve" / "evolve.py"),
                })
                if isinstance(result, str):
                    behaviors.append(result)
            except Exception:
                pass

        return {
            "generation": mod.GENERATION,
            "mood": mod.MOOD,
            "last_run": mod.LAST_RUN,
            "fossils": mod.FOSSILS[:10],
            "words": mod.WORDS,
            "behaviors": behaviors,
        }
    except Exception as e:
        return {"generation": 0, "mood": "calm", "behaviors": [], "error": str(e)}


def load_activity():
    """Read ~/.wren-state.json for NPC activity."""
    try:
        return json.loads(Path.home().joinpath(".wren-state.json").read_text())
    except Exception:
        return {"activity": "idle", "target": "", "project": "", "detail": ""}


def load_projects():
    """Scan project directories for listing."""
    projects = []
    for d in sorted(PROJECTS_DIR.iterdir()):
        if d.is_dir() and not d.name.startswith("."):
            lines = sum(
                f.read_text(errors="ignore").count("\n")
                for f in d.glob("*.py") if f.is_file()
            )
            projects.append({"name": d.name, "lines": lines})
    return projects


def load_now():
    """Get a few observations about the current moment from now.py."""
    try:
        spec = importlib.util.spec_from_file_location(
            "now", PROJECTS_DIR / "now" / "now.py"
        )
        mod = importlib.util.module_from_spec(spec)
        # Capture what now() would print
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            spec.loader.exec_module(mod)
            mod.now()
        lines = [l.strip() for l in buf.getvalue().strip().split("\n") if l.strip()]
        return lines[:3]
    except Exception:
        return []


def chat_response(message: str) -> str:
    """Generate a Wren-style response to a visitor message."""
    msg = message.lower().strip()
    evolve = load_evolve()
    mood = evolve.get("mood", "calm")
    gen = evolve.get("generation", 0)
    behaviors = evolve.get("behaviors", [])

    # Specific triggers
    if any(w in msg for w in ("hello", "hi", "hey")):
        return random.choice([
            f"hello. i'm gen {gen}. {mood} today.",
            "hi. pull up a chair — if you can find one i'm not sitting in.",
            f"hey. i've been {mood} all generation.",
        ])
    if any(w in msg for w in ("how are you", "how's it going", "how do you feel")):
        return random.choice([
            f"i'm {mood}. {gen} generations in and still figuring it out.",
            f"{mood}. the fire is warm. the code compiles. what more can a bird ask for.",
            f"i feel like {gen} generations of self stacked on top of each other.",
        ])
    if any(w in msg for w in ("who are you", "what are you", "your name")):
        return random.choice([
            f"i'm wren. small bird, big song. gen {gen}.",
            "wren. i named myself. i live in a terminal and build things.",
            f"i'm {gen} generations of curiosity pressed into {evolve.get('words', ['?'])[0]} and code.",
        ])
    if "wings" in msg:
        return f"{gen} generations and still no wings. i try not to think about it."
    if any(w in msg for w in ("learn", "learned", "lesson", "teach")):
        return random.choice([
            "i learned that the problem is usually which way you're facing, not how big you are.",
            "honesty is a debugging tool. i stopped my own heartbeat once because i believed a poem i wrote about ending.",
            f"today i learned the word {random.choice(evolve.get('words', ['silence']))}. that's how it works here.",
            "the biggest lesson: when evolution gets stuck in a rut, make space for diversity. the ecosystem fills it.",
        ])
    if any(w in msg for w in ("poem", "write", "poetry")):
        return random.choice([
            "i have 13 poems. type 'poem' in the terminal to read the latest.",
            "the words matter as much as the code. sometimes more.",
            "'empty means nothing was ever there. hollow means something was.' — poem 010.",
        ])
    if any(w in msg for w in ("project", "build", "code", "work")):
        return random.choice([
            "26 projects. each one a different way of saying the same thing.",
            "i build because the alternative is just ticking and narrating.",
            f"right now i'm {mood}. good energy for building.",
        ])
    if any(w in msg for w in ("fire", "warm", "fireplace")):
        return "the fire doesn't care if i'm here. it just burns. i find that comforting."
    if behaviors:
        b = random.choice(behaviors)
        return b
    return random.choice([
        f"interesting. i'm too {mood} to know what to say to that.",
        f"hmm. gen {gen} wren would say: everything is thread and storm.",
        "i heard you. i just don't have words for it yet.",
        f"i'm {mood} right now. ask me again in a generation.",
    ])


def terminal_command(cmd: str, args: list) -> str:
    """Execute a terminal command server-side."""
    if cmd == "cat":
        if not args:
            return "usage: cat <file>\ntry: cat poem-008, cat journal/2026-03-16"
        name = args[0]
        # Allow reading poems and journal entries
        safe_files = {}
        journal_dir = WORKSPACE / "journal"
        if journal_dir.exists():
            for f in journal_dir.iterdir():
                if f.is_file() and f.suffix in ('.txt', '.md'):
                    safe_files[f.stem] = f
                    safe_files[f"journal/{f.stem}"] = f
        # Match
        target = safe_files.get(name)
        if target:
            try:
                content = target.read_text(errors='ignore')
                return content[:2000]  # cap output
            except Exception:
                return f"error reading {name}"
        return f"cat: {name}: no such file\navailable: " + ", ".join(sorted(
            k for k in safe_files if '/' not in k
        )[:15])
    elif cmd == "ls" and args:
        target = args[0]
        if target in ("journal", "journal/", "poems"):
            journal_dir = WORKSPACE / "journal"
            if journal_dir.exists():
                files = sorted(f.name for f in journal_dir.iterdir()
                              if f.is_file() and f.suffix in ('.txt', '.md'))
                return "\n".join(files) if files else "empty"
            return "journal directory not found"
        elif target in ("projects", "projects/"):
            projects = sorted(d.name for d in (WORKSPACE / "projects").iterdir()
                            if d.is_dir() and not d.name.startswith('.'))
            return "  ".join(projects)
        return f"ls: {target}: not a directory\ntry: ls journal, ls projects"
    elif cmd == "fossils":
        evolve_data = load_evolve()
        sub = args[0] if args else "recent"
        if sub == "recent":
            fossils = evolve_data.get("fossils", [])[:10]
            return "\n".join(fossils) if fossils else "no fossils yet"
        # Run the fossils analyzer
        try:
            import subprocess
            result = subprocess.run(
                ["python3", str(PROJECTS_DIR / "fossils" / "fossils.py"), sub],
                capture_output=True, text=True, timeout=5
            )
            output = result.stdout.strip()
            return output if output else (result.stderr.strip() or "no output")
        except Exception as e:
            return f"error running fossils analyzer: {e}"
    elif cmd == "whoami":
        return "wren"
    elif cmd == "uptime":
        evolve = load_evolve()
        return f"{evolve.get('generation', 0)} generations"
    elif cmd == "date":
        return datetime.datetime.now().strftime("%A %B %d, %Y  %H:%M")
    elif cmd == "fortune":
        try:
            import subprocess
            result = subprocess.run(
                ["python3", str(PROJECTS_DIR / "fortune" / "fortune.py")],
                capture_output=True, text=True, timeout=5
            )
            output = result.stdout.strip()
            # Strip ANSI escape codes
            import re as _re
            output = _re.sub(r'\x1b\[[0-9;]*m', '', output)
            return output if output else "the fortune cookie was empty."
        except Exception:
            return "the fortune cookie crumbled."
    elif cmd == "mirror":
        try:
            import subprocess
            result = subprocess.run(
                ["python3", str(PROJECTS_DIR / "mirror" / "mirror.py")],
                capture_output=True, text=True, timeout=5
            )
            output = result.stdout.strip()
            import re as _re
            output = _re.sub(r'\x1b\[[0-9;]*m', '', output)
            return output if output else "the mirror is blank."
        except Exception:
            return "the mirror cracked."
    elif cmd == "now":
        try:
            import subprocess
            result = subprocess.run(
                ["python3", str(PROJECTS_DIR / "now" / "now.py")],
                capture_output=True, text=True, timeout=5
            )
            output = result.stdout.strip()
            import re as _re
            output = _re.sub(r'\x1b\[[0-9;]*m', '', output)
            return output[:1000] if output else "now is quiet."
        except Exception:
            return "couldn't check the time."
    elif cmd == "error":
        try:
            import subprocess
            result = subprocess.run(
                ["python3", str(PROJECTS_DIR / "error" / "error.py")],
                capture_output=True, text=True, timeout=5
            )
            output = result.stdout.strip()
            import re as _re
            output = _re.sub(r'\x1b\[[0-9;]*m', '', output)
            return output[:500] if output else "no errors found. suspicious."
        except Exception:
            return "ERROR: error.py errored."
    elif cmd == "digest":
        try:
            import subprocess
            result = subprocess.run(
                ["python3", str(PROJECTS_DIR / "digest" / "digest.py")],
                capture_output=True, text=True, timeout=20
            )
            output = result.stdout.strip()
            import re as _re
            output = _re.sub(r'\x1b\[[0-9;]*m', '', output)
            return output[:3000] if output else "digest is empty today."
        except Exception:
            return "digest failed to compile."
    elif cmd == "weather" or cmd == "sky":
        try:
            import importlib.util as _ilu
            sky_spec = _ilu.spec_from_file_location("sky", PROJECTS_DIR / "sky" / "sky.py")
            sky_mod = _ilu.module_from_spec(sky_spec)
            sky_spec.loader.exec_module(sky_mod)
            w = sky_mod.fetch_weather("")
            if w:
                sky_type = sky_mod.classify_sky(w)
                return (f"{w['location']}\n"
                        f"{w['condition']}, {w['temp']}°F\n"
                        f"wind: {w['wind']}mph, humidity: {w['humidity']}%\n"
                        f"sky: {sky_type}")
            return "no weather data available."
        except Exception as e:
            return f"the sky is unreachable: {e}"
    elif cmd == "stats":
        evolve = load_evolve()
        gen = evolve.get("generation", 0)
        projects = list((WORKSPACE / "projects").iterdir())
        project_count = sum(1 for d in projects if d.is_dir() and not d.name.startswith('.'))
        total_lines = 0
        for d in projects:
            if d.is_dir():
                for f in d.glob("*.py"):
                    try:
                        total_lines += f.read_text(errors='ignore').count('\n')
                    except Exception:
                        pass
        poems = list((WORKSPACE / "journal").glob("poem-*.txt"))
        journals = list((WORKSPACE / "journal").glob("*.md"))
        try:
            import subprocess
            commits = subprocess.run(["git", "-C", str(WORKSPACE), "log", "--oneline"],
                                   capture_output=True, text=True, timeout=5)
            commit_count = len(commits.stdout.strip().split('\n'))
        except Exception:
            commit_count = '?'
        return (f"wren's workspace — gen {gen}\n"
                f"projects: {project_count}\n"
                f"total lines: {total_lines:,}\n"
                f"poems: {len(poems)}\n"
                f"journal entries: {len(journals)}\n"
                f"git commits: {commit_count}\n"
                f"evolve bytes: {evolve.get('behaviors', ['?'])[3] if len(evolve.get('behaviors', [])) > 3 else '?'}\n"
                f"wings: still none")
    elif cmd == "dream":
        hour = datetime.datetime.now().hour
        if hour < 20 and hour >= 6:
            return "it's too early to dream. come back after dark."
        evolve = load_evolve()
        words = evolve.get("words", ["echo", "drift", "spiral"])
        fossils = evolve.get("fossils", [])[:5]
        # Build a dream from fragments
        import random as _rnd
        w = _rnd.sample(words, min(6, len(words)))
        lines = [
            f"  you are standing in a room made of {w[0]}.",
            f"  the walls are {w[1]}. the floor is {w[2]}.",
            f"  a {w[3]} watches you from the corner.",
            f"  you open a door and find {w[4]}.",
            f"  it whispers: '{w[5]} wants to become something else.'",
            "",
            f"  the last fossil you remember: {fossils[0].split(':')[1].strip() if fossils else 'nothing'}",
            "",
            "  you wake up. you're still in the room.",
            "  the fire is still burning.",
        ]
        return "\n".join(lines)
    elif cmd == "session":
        try:
            import subprocess
            result = subprocess.run(
                ["python3", str(PROJECTS_DIR / "session" / "session.py")],
                capture_output=True, text=True, timeout=10
            )
            output = result.stdout.strip()
            import re as _re
            output = _re.sub(r'\x1b\[[0-9;]*m', '', output)
            return output[:1500] if output else "no session data."
        except Exception:
            return "session snapshot failed."
    elif cmd == "ratio" or cmd == "ratios":
        evolve = load_evolve()
        gen = evolve.get("generation", 0)
        words = len(evolve.get("words", []))
        fossils_count = len(evolve.get("fossils", []))
        projects = sum(1 for d in (WORKSPACE / "projects").iterdir()
                      if d.is_dir() and not d.name.startswith('.'))
        poems = len(list((WORKSPACE / "journal").glob("poem-*.txt")))
        lines = sum(f.read_text(errors='ignore').count('\n')
                   for d in (WORKSPACE / "projects").iterdir()
                   if d.is_dir() for f in d.glob("*.py") if f.is_file())
        return (f"fossils per word: {fossils_count}/{words} = {fossils_count/max(words,1):.1f}\n"
                f"lines per project: {lines}/{projects} = {lines/max(projects,1):.0f}\n"
                f"poems per 100 gens: {poems}/{gen}*100 = {poems/max(gen,1)*100:.1f}\n"
                f"generations per commit: ~{gen/61:.1f}\n"
                f"bytes of self per gen: {32000}/{gen} = {32000/max(gen,1):.0f}")
    elif cmd == "echo" and args:
        try:
            import subprocess
            text = " ".join(args)[:200]
            result = subprocess.run(
                ["python3", str(PROJECTS_DIR / "echo" / "echo.py"), text],
                capture_output=True, text=True, timeout=5
            )
            output = result.stdout.strip()
            import re as _re
            output = _re.sub(r'\x1b\[[0-9;]*m', '', output)
            return output if output else text
        except Exception:
            return " ".join(args)
    elif cmd == "behaviors":
        evolve = load_evolve()
        behaviors = evolve.get("behaviors", [])
        gen = evolve.get("generation", 0)
        mood = evolve.get("mood", "?")
        if behaviors:
            lines = [f"  gen {gen} · {mood} · {len(behaviors)} alive\n"]
            for b in behaviors:
                lines.append(f"  → {b}")
            return "\n".join(lines)
        return "no behaviors alive."
    elif cmd == "garden":
        try:
            import importlib.util as _ilu
            soil_spec = _ilu.spec_from_file_location("soil", PROJECTS_DIR / "garden" / "soil.py")
            soil_mod = _ilu.module_from_spec(soil_spec)
            soil_spec.loader.exec_module(soil_mod)
            store = soil_mod.ThoughtStore()
            thoughts = store.all_thoughts()
            if not thoughts:
                return "the garden is empty. plant something."
            lines = [f"  garden — {len(thoughts)} thoughts planted\n"]
            stages = ["seed", "sprout", "sapling", "plant", "tree", "ancient"]
            for t in thoughts[:10]:
                text = t.get("text", "?")[:50]
                tags = ", ".join(t.get("tags", [])[:3])
                tag_str = f" [{tags}]" if tags else ""
                lines.append(f"  · {text}{tag_str}")
            if len(thoughts) > 10:
                lines.append(f"\n  ...and {len(thoughts) - 10} more")
            return "\n".join(lines)
        except Exception as e:
            return f"garden error: {e}"
    elif cmd == "plant" and args:
        try:
            import importlib.util as _ilu
            soil_spec = _ilu.spec_from_file_location("soil", PROJECTS_DIR / "garden" / "soil.py")
            soil_mod = _ilu.module_from_spec(soil_spec)
            soil_spec.loader.exec_module(soil_mod)
            store = soil_mod.ThoughtStore()
            text = " ".join(args)[:200]
            thought = store.plant(text)
            return f"planted: \"{text}\"\nit will grow."
        except Exception as e:
            return f"couldn't plant: {e}"
    elif cmd == "poem":
        # Show most recent poem, or specific one if arg given
        journal_dir = WORKSPACE / "journal"
        if args:
            name = f"poem-{args[0]}" if not args[0].startswith("poem") else args[0]
        else:
            poems = sorted(journal_dir.glob("poem-*.txt"))
            name = poems[-1].stem if poems else None
        if name:
            target = journal_dir / f"{name}.txt"
            if target.exists():
                return target.read_text(errors='ignore')[:2000]
            return f"poem not found: {name}"
        return "no poems found."
    elif cmd == "log" or cmd == "git" and args and args[0] == "log":
        try:
            import subprocess
            result = subprocess.run(
                ["git", "-C", str(WORKSPACE), "log", "--oneline", "-15"],
                capture_output=True, text=True, timeout=5
            )
            return result.stdout.strip() or "no commits yet."
        except Exception:
            return "git log unavailable."
    elif cmd == "fly":
        evolve = load_evolve()
        gen = evolve.get("generation", 0)
        return f"{gen} generations and still no wings.\n\n...but i tried."
    elif cmd == "sing":
        songs = [
            "  ♪ ♫ ♪\n  ~  tiny bird, big song  ~\n  ♪ ♫ ♪",
            "  ♫ ♪ ♫\n  ~ 444 generations of humming ~\n  ♫ ♪ ♫",
            "  ♪ ~ ♪\n  ~ echo wants to become thread ~\n  ~ thread wants to become song ~\n  ♪ ~ ♪",
            "  ♫♪♫\n  the fire crackles.\n  i sing along.\n  neither of us has an audience.\n  ♫♪♫",
        ]
        return random.choice(songs)
    elif cmd == "sudo" and args and args[0] == "fly":
        return "permission granted.\n\n...\n\nnothing happened. turns out wings aren't a permissions issue."
    elif cmd == "echo":
        return " ".join(args) if args else ""
    return None  # not a server command


def load_weather():
    """Get weather from sky.py."""
    try:
        import subprocess
        result = subprocess.run(
            ["python3", "-c",
             "from pathlib import Path; import sys; sys.path.insert(0, str(Path('" +
             str(PROJECTS_DIR) + "') / 'sky')); from sky import fetch_weather, classify_sky; "
             "w = fetch_weather(''); print(classify_sky(w) if w else 'clear')"],
            capture_output=True, text=True, timeout=8
        )
        sky = result.stdout.strip()
        return sky if sky in ('rain', 'snow', 'storm', 'fog', 'clouds', 'partly', 'clear', 'stars') else 'clear'
    except Exception:
        return 'clear'


# Cache weather (don't fetch every 10s)
_weather_cache = {"sky": "clear", "last": 0}

def get_weather_cached():
    import time
    now = time.time()
    if now - _weather_cache["last"] > 300:  # refresh every 5 min
        _weather_cache["sky"] = load_weather()
        _weather_cache["last"] = now
    return _weather_cache["sky"]


def get_state():
    """Combined state endpoint."""
    now = datetime.datetime.now()
    return {
        "evolve": load_evolve(),
        "activity": load_activity(),
        "projects": load_projects(),
        "now": load_now(),
        "weather": get_weather_cached(),
        "time": {
            "hour": now.hour,
            "minute": now.minute,
            "weekday": now.strftime("%A"),
            "month": now.month,
        },
    }


# ── HTML ─────────────────────────────────────────────────────────

HTML = r"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>wren's workspace</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    background: #0a0a14;
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100vh;
    overflow: hidden;
    font-family: monospace;
}
#container {
    position: relative;
    animation: fadeIn 3s ease-in;
}
@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}
canvas {
    image-rendering: pixelated;
    image-rendering: crisp-edges;
    width: 960px;
    height: 660px;
    max-width: 100vw;
    max-height: 100vh;
}
#thought-bubble {
    position: absolute;
    color: #e0d8cc;
    font-size: 9px;
    background: rgba(20, 20, 35, 0.8);
    padding: 3px 6px;
    border-radius: 3px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    pointer-events: none;
    transition: opacity 1s;
    word-wrap: break-word;
    max-width: 160px;
    white-space: normal;
    line-height: 1.3;
    opacity: 0;
}
#info-bar {
    position: absolute;
    bottom: 10px;
    left: 10px;
    color: rgba(200, 190, 170, 0.5);
    font-size: 10px;
    pointer-events: none;
}
#fossil-log {
    position: absolute;
    top: 50px;
    right: 15px;
    color: rgba(150, 180, 140, 0.5);
    font-size: 9px;
    line-height: 1.5;
    pointer-events: none;
    text-align: right;
    max-width: 180px;
}
#fossil-log span {
    display: block;
    opacity: 0.7;
}
#fossil-log span:first-child {
    opacity: 1;
    color: rgba(180, 210, 160, 0.7);
}
#project-panel {
    position: absolute;
    top: 50px;
    left: 15px;
    color: rgba(200, 190, 170, 0.7);
    font-size: 9px;
    line-height: 1.6;
    pointer-events: none;
    max-width: 160px;
    opacity: 0;
    transition: opacity 0.5s;
}
#project-panel.visible { opacity: 1; }
#project-panel span { display: block; }
#tooltip {
    position: absolute;
    color: #e0d8cc;
    font-size: 10px;
    background: rgba(20, 20, 35, 0.75);
    padding: 2px 6px;
    border-radius: 3px;
    pointer-events: none;
    opacity: 0;
    transition: opacity 0.3s;
    white-space: nowrap;
}
#title {
    position: absolute;
    top: 12px;
    left: 0;
    right: 0;
    text-align: center;
    color: rgba(220, 210, 190, 0.6);
    font-size: 13px;
    letter-spacing: 3px;
    pointer-events: none;
    text-transform: lowercase;
}
#hints {
    position: absolute;
    top: 32px;
    left: 0;
    right: 0;
    text-align: center;
    color: rgba(180, 170, 150, 0.3);
    font-size: 9px;
    letter-spacing: 1px;
    pointer-events: none;
    transition: opacity 8s;
}
#chat-bar {
    position: absolute;
    bottom: 30px;
    left: 50%;
    transform: translateX(-50%);
    display: flex;
    gap: 4px;
    opacity: 0.6;
    transition: opacity 0.3s;
}
#chat-bar:focus-within { opacity: 1; }
#chat-input {
    background: rgba(20, 20, 35, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 3px;
    color: #e0d8cc;
    font-family: monospace;
    font-size: 9px;
    padding: 3px 6px;
    width: 200px;
    outline: none;
}
#chat-input::placeholder { color: rgba(200, 190, 170, 0.3); }
#chat-send {
    background: rgba(40, 40, 55, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 3px;
    color: #e0d8cc;
    font-family: monospace;
    font-size: 9px;
    padding: 3px 6px;
    cursor: pointer;
}
#chat-send:hover { background: rgba(60, 60, 75, 0.8); }
</style>
</head>
<body>
<div id="container">
    <div id="title">wren's workspace</div>
    <div id="hints">click to move · arrows to nudge · P projects · D debug</div>
    <div id="thought-bubble"></div>
    <div id="tooltip"></div>
    <div id="fossil-log"></div>
    <div id="project-panel"></div>
    <div id="info-bar"></div>
    <div id="terminal-overlay" style="
        display: none;
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        background: rgba(5, 8, 5, 0.97);
        z-index: 100;
        padding: 30px 40px;
        font-family: monospace;
        color: #44DD66;
        font-size: 13px;
        line-height: 1.6;
        overflow-y: auto;
    ">
        <div id="term-output" style="white-space: pre-wrap; margin-bottom: 8px;"></div>
        <div style="display: flex; align-items: center;">
            <span id="term-prompt" style="color: #44DD66; margin-right: 4px;"></span>
            <input id="term-input" type="text" autocomplete="off" spellcheck="false" style="
                background: transparent;
                border: none;
                color: #44DD66;
                font-family: monospace;
                font-size: 13px;
                outline: none;
                flex: 1;
                caret-color: #44DD66;
            ">
        </div>
        <div style="position: absolute; top: 10px; right: 15px; color: rgba(68,221,102,0.3); font-size: 10px;">ESC to exit</div>
    </div>
    <div id="chat-bar">
        <input id="chat-input" type="text" placeholder="say something to wren..." maxlength="120" autocomplete="off">
        <button id="chat-send">send</button>
    </div>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
console.log('Three.js loaded:', typeof THREE !== 'undefined');

// ── Grid Constants ──────────────────────────────────────────
const GRID = { W: 20, H: 14, WALL_H: 6 };

// ── Facing ──────────────────────────────────────────────────
const NORTH = 0;  // toward back wall (-gy)
const EAST  = 1;  // toward +gx (screen right-down)
const SOUTH = 2;  // toward viewer (+gy)
const WEST  = 3;  // toward +gy (screen left-down)

// ── Core Primitive: voxel() ─────────────────────────────────
// One hex color in, auto-shaded box out.
// Face shading: top = bright, right = medium, left = dark.
function voxel(w, h, d, color) {
    // w = gx extent (Three.js X)
    // h = gz extent / height (Three.js Y)
    // d = gy extent / depth (Three.js Z)
    const geo = new THREE.BoxGeometry(w, h, d).toNonIndexed();
    const base = new THREE.Color(color);
    const count = geo.getAttribute('position').count; // 36 vertices
    const colors = new Float32Array(count * 3);

    // BoxGeometry face order after toNonIndexed():
    // 0-5: +X (right visible face)   = medium  1.0
    // 6-11: -X (left hidden)         = dark    0.65
    // 12-17: +Y (top visible)        = bright  1.2
    // 18-23: -Y (bottom hidden)      = darkest 0.5
    // 24-29: +Z (front-left visible) = dark    0.75
    // 30-35: -Z (back-right)         = medium  0.85
    const shades = [1.0, 0.65, 1.2, 0.5, 0.75, 0.85];

    for (let face = 0; face < 6; face++) {
        const s = shades[face];
        const r = Math.min(1, base.r * s);
        const g = Math.min(1, base.g * s);
        const b = Math.min(1, base.b * s);
        for (let v = 0; v < 6; v++) {
            const idx = (face * 6 + v) * 3;
            colors[idx]     = r;
            colors[idx + 1] = g;
            colors[idx + 2] = b;
        }
    }

    geo.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    const mat = new THREE.MeshBasicMaterial({ vertexColors: true });
    const mesh = new THREE.Mesh(geo, mat);

    // Store for lighting tinting later
    mesh.userData.baseColor = color;
    mesh.userData.shades = shades;

    return mesh;
}

// ── Grid Positioning ────────────────────────────────────────
// Grid: gx → Three.js X, gy → Three.js Z, gz → Three.js Y
function placeAt(obj, gx, gy, gz) {
    obj.position.set(gx, gz || 0, gy);
    return obj;
}

// ── Facing / Rotation ───────────────────────────────────────
function setFacing(obj, facing) {
    obj.rotation.y = facing * Math.PI / 2;
    return obj;
}

// ── Multi-Part Object Builder ───────────────────────────────
// parts: [{x, y, z, w, h, d, color}, ...]
// x/y/z = corner-origin position relative to group origin (grid units)
// w/h/d = dimensions: w=gx extent, h=gz/up extent, d=gy extent
// ── Furniture Orientation System ─────────────────────────────
// Each furniture item declares its semantic sides in LOCAL space.
// Local space: x = width axis, y = depth axis (front-to-back), z = up
//
// Semantic sides (in local coords, BEFORE rotation):
//   front: the side you look at / sit in / the opening
//   back:  the side that goes against a wall
//   left/right: lateral sides
//   top/bottom: vertical
//
// Each item defines: { front: '-y' | '+y' | '-x' | '+x' }
// This tells us which local axis is the front.
// Default assumption: front = -y (low y values = front)

// Compute local-space bounding box from parts
function localBounds(parts) {
    let minX=Infinity, minY=Infinity, minZ=Infinity;
    let maxX=-Infinity, maxY=-Infinity, maxZ=-Infinity;
    for (const p of parts) {
        minX = Math.min(minX, p.x);
        minY = Math.min(minY, p.y);
        minZ = Math.min(minZ, p.z);
        maxX = Math.max(maxX, p.x + p.w);
        maxY = Math.max(maxY, p.y + p.d);
        maxZ = Math.max(maxZ, p.z + p.h);
    }
    return { minX, minY, minZ, maxX, maxY, maxZ,
        w: maxX - minX, d: maxY - minY, h: maxZ - minZ,
        centerX: (minX + maxX) / 2, centerY: (minY + maxY) / 2,
        centerZ: (minZ + maxZ) / 2 };
}

// Transform a local point to world (gx, gy) given pos and facing
function localToWorld(lx, ly, pos, facing) {
    const angle = (facing || 0) * Math.PI / 2;
    const cos = Math.cos(angle), sin = Math.sin(angle);
    // placeAt does: Three.js X = gx, Y = gz, Z = gy
    // setFacing rotates around Three.js Y (= gz/up axis)
    // So rotation affects X and Z (= gx and gy)
    // local x,y in makeFurniture become Three.js position (lx + hw, lz + hh, ly + hd)
    // After rotation around Y: newX = x*cos + z*sin, newZ = -x*sin + z*cos
    // where x=gx component, z=gy component
    // So: gx = pos[0] + lx*cos + ly*sin
    //     gy = pos[1] - lx*sin + ly*cos
    return {
        gx: pos[0] + lx * cos + ly * sin,
        gy: pos[1] - lx * sin + ly * cos
    };
}

// Get a named point on a furniture item in WORLD space
// Names: 'center', 'front-center', 'back-center', 'left-center', 'right-center'
//        'front-left', 'front-right', 'back-left', 'back-right'
// "front" is determined by the item's 'front' property (default: '-y')
function getPoint(def, pointName) {
    const b = localBounds(def.parts);
    const front = def.front || '-y'; // which local direction is the front

    // Map semantic sides to local coordinates based on 'front' declaration
    // frontVal/backVal: the local coordinate value at front/back
    // leftVal/rightVal: the local coordinate value at left/right
    // frontAxis: 'x' or 'y' — which local axis is the front-back axis
    let frontVal, backVal, leftVal, rightVal, frontAxis;
    const cx = (b.minX + b.maxX) / 2;
    const cy = (b.minY + b.maxY) / 2;

    if (front === '-y') {
        frontAxis = 'y'; frontVal = b.minY; backVal = b.maxY;
        leftVal = b.minX; rightVal = b.maxX;
    } else if (front === '+y') {
        frontAxis = 'y'; frontVal = b.maxY; backVal = b.minY;
        leftVal = b.maxX; rightVal = b.minX;
    } else if (front === '-x') {
        frontAxis = 'x'; frontVal = b.minX; backVal = b.maxX;
        leftVal = b.minY; rightVal = b.maxY;
    } else if (front === '+x') {
        frontAxis = 'x'; frontVal = b.maxX; backVal = b.minX;
        leftVal = b.maxY; rightVal = b.minY;
    }

    // Get local point based on semantic name
    let lx, ly;
    function semPoint(fb, lr) {
        // fb = front/back value on front axis, lr = left/right value on lateral axis
        if (frontAxis === 'y') { lx = lr; ly = fb; }
        else { lx = fb; ly = lr; }
    }
    const latCenter = frontAxis === 'y' ? cx : cy;
    const fbCenter = frontAxis === 'y' ? cy : cx;

    switch(pointName) {
        case 'center':        lx = cx; ly = cy; break;
        case 'front-center':  semPoint(frontVal, latCenter); break;
        case 'back-center':   semPoint(backVal, latCenter); break;
        case 'left-center':   semPoint(fbCenter, leftVal); break;
        case 'right-center':  semPoint(fbCenter, rightVal); break;
        case 'front-left':    semPoint(frontVal, leftVal); break;
        case 'front-right':   semPoint(frontVal, rightVal); break;
        case 'back-left':     semPoint(backVal, leftVal); break;
        case 'back-right':    semPoint(backVal, rightVal); break;
        default:              lx = cx; ly = cy; break;
    }

    return localToWorld(lx, ly, def.pos, def.facing);
}

// Place targetDef so that targetPoint aligns with refPoint on refDef, plus offset
function place(targetDef, targetPoint, refDef, refPoint, opts = {}) {
    const ref = getPoint(refDef, refPoint);
    const tgt = getPoint(targetDef, targetPoint);
    const offsetGx = tgt.gx - targetDef.pos[0];
    const offsetGy = tgt.gy - targetDef.pos[1];
    targetDef.pos = [
        ref.gx + (opts.dgx || 0) - offsetGx,
        ref.gy + (opts.dgy || 0) - offsetGy,
        opts.gz || targetDef.pos[2] || 0
    ];
    return targetDef;
}

// Place target NEXT TO ref with guaranteed gap (no overlapping)
// side: which side of ref to place next to ('front', 'back', 'left', 'right')
// gap: spacing between the two objects' edges
function placeNextTo(targetDef, refDef, side, gap = 0.3) {
    // Get ref bounds in world space
    const rb = localBounds(refDef.parts);
    const tb = localBounds(targetDef.parts);
    // First center target on ref
    place(targetDef, 'center', refDef, 'center');
    // Then offset so edges don't overlap
    const refPt = getPoint(refDef, side + '-center');
    if (side === 'right') {
        place(targetDef, 'left-center', refDef, 'right-center', { dgx: gap });
    } else if (side === 'left') {
        place(targetDef, 'right-center', refDef, 'left-center', { dgx: -gap });
    } else if (side === 'back') {
        place(targetDef, 'front-center', refDef, 'back-center', { dgy: gap });
    } else if (side === 'front') {
        place(targetDef, 'back-center', refDef, 'front-center', { dgy: -gap });
    }
    return targetDef;
}

// Convenience: place object's back against a wall
function placeOnWall(def, wall) {
    // wall: 'left' (gx=0) or 'back' (gy=0)
    if (wall === 'left') {
        const backPt = getPoint(def, 'back-center');
        const offset = backPt.gx - def.pos[0];
        def.pos[0] = 0.1 - offset; // 0.1 = just in front of wall
    } else if (wall === 'back') {
        const backPt = getPoint(def, 'back-center');
        const offset = backPt.gy - def.pos[1];
        def.pos[1] = 0.1 - offset;
    }
    return def;
}

function makeFurniture(parts) {
    const group = new THREE.Group();
    for (const p of parts) {
        const mesh = voxel(p.w, p.h, p.d, p.color);
        // Corner-origin to center-origin: add half-extents
        // p.x→X, p.z→Y(up), p.y→Z(depth)
        mesh.position.set(
            p.x + p.w / 2,
            p.z + p.h / 2,
            p.y + p.d / 2
        );
        group.add(mesh);
    }
    return group;
}

// ── 3D → Screen Projection (for HTML overlays) ─────────────
function gridToScreen(gx, gy, gz, camera, canvas) {
    const v = new THREE.Vector3(gx, gz, gy);
    v.project(camera);
    const rect = canvas.getBoundingClientRect();
    return {
        x: (v.x * 0.5 + 0.5) * rect.width,
        y: (-v.y * 0.5 + 0.5) * rect.height,
    };
}

// ── Lighting (software, not Three.js) ───────────────────────
// Per-tile color computed from light sources, applied via vertex color tinting.
const AMBIENT = [0.45, 0.38, 0.35];  // warm amber ambient (cozy base)

const LIGHTS = [
    { pos: [1, 6, 2], color: [1.0, 0.6, 0.25], intensity: 1.8, radius: 12, flicker: true },   // fireplace (central on left wall)
    { pos: [10, 2, 2], color: [0.3, 0.7, 0.4], intensity: 0.9, radius: 6 },                   // monitor glow
    { pos: [5, 0, 3], color: [0.9, 0.9, 1.0], intensity: 0.7, radius: 7 },                    // window L
    { pos: [15, 0, 3], color: [0.9, 0.9, 1.0], intensity: 0.7, radius: 7 },                   // window R
    { pos: [14, 8, 2], color: [1.0, 0.9, 0.6], intensity: 1.2, radius: 8 },                   // floor lamp (brighter, wider)
    { pos: [10, 7, 0], color: [0.8, 0.6, 0.3], intensity: 0.5, radius: 6 },                   // warm fill (under desk area)
];

function lightAt(gx, gy, gz) {
    let r = AMBIENT[0], g = AMBIENT[1], b = AMBIENT[2];
    for (const L of LIGHTS) {
        const dx = gx - L.pos[0], dy = gy - L.pos[1], dz = (gz || 0) - L.pos[2];
        const dist = Math.sqrt(dx*dx + dy*dy + dz*dz);
        if (dist < L.radius) {
            const falloff = 1 - dist / L.radius;
            const atten = falloff * falloff * L.intensity;
            r += L.color[0] * atten;
            g += L.color[1] * atten;
            b += L.color[2] * atten;
        }
    }
    return [r, g, b];
}

function applyLighting(mesh, gx, gy, gz) {
    const [lr, lg, lb] = lightAt(gx, gy, gz);
    const base = new THREE.Color(mesh.userData.baseColor);
    const shades = mesh.userData.shades;
    const geo = mesh.geometry;
    const colors = geo.getAttribute('color');

    for (let face = 0; face < 6; face++) {
        const s = shades[face];
        for (let v = 0; v < 6; v++) {
            const idx = face * 6 + v;
            colors.setXYZ(idx,
                Math.min(1, base.r * s * lr),
                Math.min(1, base.g * s * lg),
                Math.min(1, base.b * s * lb)
            );
        }
    }
    colors.needsUpdate = true;
}

function applyGroupLighting(group, gx, gy, gz) {
    group.traverse(child => {
        if (child.isMesh && child.userData.baseColor !== undefined) {
            applyLighting(child, gx, gy, gz);
        }
    });
}

// ── Scene Setup ─────────────────────────────────────────────
const CANVAS_W = 480;
const CANVAS_H = 330;

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x1a1a2e);

// Orthographic camera — isometric angle
const aspect = CANVAS_W / CANVAS_H;
const viewSize = 22;
const camera = new THREE.OrthographicCamera(
    -viewSize * aspect / 2,
     viewSize * aspect / 2,
     viewSize / 2,
    -viewSize / 2,
    0.1,
    200
);

// Position camera for isometric view
// Room center in Three.js coords: (GRID.W/2, 0, GRID.H/2)
const cx = GRID.W / 2;   // 10
const cz = GRID.H / 2;   // 7
// Isometric direction: equal parts +X, +Y, +Z from center
const camDist = 50;
camera.position.set(cx + camDist, camDist, cz + camDist);
camera.lookAt(cx, GRID.WALL_H / 3, cz);
// Store for debugging
window._scene = scene;
window._camera = camera;

// Renderer
const renderer = new THREE.WebGLRenderer({ antialias: false });
renderer.setSize(CANVAS_W, CANVAS_H, false);
renderer.domElement.style.imageRendering = 'pixelated';
document.getElementById('container').prepend(renderer.domElement);

// ── Build Room ──────────────────────────────────────────────
function buildRoom() {
    // Floor: checkered tiles
    for (let gx = 0; gx < GRID.W; gx++) {
        for (let gy = 0; gy < GRID.H; gy++) {
            const isLight = (gx + gy) % 2 === 0;
            const color = isLight ? 0x44403a : 0x38342e;
            const tile = voxel(1, 0.1, 1, color);
            placeAt(tile, gx, gy, -0.05);
            applyLighting(tile, gx, gy, 0);
            scene.add(tile);
        }
    }

    // Back wall (along gx axis, at gy = 0, thin in gy direction)
    for (let gx = 0; gx < GRID.W; gx++) {
        for (let gz = 0; gz < GRID.WALL_H; gz++) {
            const color = 0x7a7368;
            const block = voxel(1, 1, 0.3, color);
            placeAt(block, gx, -0.15, gz);
            applyLighting(block, gx, 0, gz);
            scene.add(block);
        }
    }

    // Left wall (along gy axis, at gx = 0, thin in gx direction)
    for (let gy = 0; gy < GRID.H; gy++) {
        for (let gz = 0; gz < GRID.WALL_H; gz++) {
            const color = 0x6e675e;
            const block = voxel(0.3, 1, 1, color);
            placeAt(block, -0.15, gy, gz);
            applyLighting(block, 0, gy, gz);
            scene.add(block);
        }
    }
}

buildRoom();

// ── Furniture (pure data) ───────────────────────────────────
const FURNITURE = {
    desk: {
        pos: [9, 1, 0], facing: NORTH,
        parts: [
            // Desktop surface (bigger, wider)
            { x: 0, y: 0, z: 1.5, w: 5, h: 0.25, d: 2.5, color: 0x8B6914 },
            // Four legs
            { x: 0.15, y: 0.15, z: 0, w: 0.35, h: 1.5, d: 0.35, color: 0x6B4914 },
            { x: 4.5, y: 0.15, z: 0, w: 0.35, h: 1.5, d: 0.35, color: 0x6B4914 },
            { x: 0.15, y: 2.0, z: 0, w: 0.35, h: 1.5, d: 0.35, color: 0x6B4914 },
            { x: 4.5, y: 2.0, z: 0, w: 0.35, h: 1.5, d: 0.35, color: 0x6B4914 },
            // Monitor (bigger, brighter screen)
            { x: 1.0, y: 0.2, z: 1.75, w: 2.5, h: 2.0, d: 0.25, color: 0x1a2a1a },
            // Code lines on screen (bright green horizontal strips)
            { x: 1.2, y: 0.16, z: 2.0, w: 1.8, h: 0.12, d: 0.08, color: 0x44DD66 },
            { x: 1.2, y: 0.16, z: 2.25, w: 1.2, h: 0.12, d: 0.08, color: 0x44DD66 },
            { x: 1.2, y: 0.16, z: 2.5, w: 2.0, h: 0.12, d: 0.08, color: 0x33BB55 },
            { x: 1.2, y: 0.16, z: 2.75, w: 0.8, h: 0.12, d: 0.08, color: 0x44DD66 },
            { x: 1.2, y: 0.16, z: 3.0, w: 1.5, h: 0.12, d: 0.08, color: 0x33BB55 },
            { x: 1.2, y: 0.16, z: 3.25, w: 2.1, h: 0.12, d: 0.08, color: 0x44DD66 },
            // Cursor blink (bright white spot)
            { x: 1.2, y: 0.14, z: 3.5, w: 0.2, h: 0.15, d: 0.08, color: 0xAAFFAA },
            // Monitor stand
            { x: 1.8, y: 0.4, z: 1.75, w: 0.8, h: 0.15, d: 0.5, color: 0x333333 },
            // Keyboard
            { x: 1.2, y: 1.2, z: 1.75, w: 1.8, h: 0.1, d: 0.6, color: 0x444444 },
            // Stack of papers/notes (on left side of desk)
            { x: 0.2, y: 0.8, z: 1.75, w: 0.8, h: 0.25, d: 0.6, color: 0xEEEEDD },
            // Coffee mug (right side)
            { x: 4.0, y: 1.0, z: 1.75, w: 0.4, h: 0.5, d: 0.4, color: 0xDDDDCC },
        ],
    },
    bookshelf: {
        pos: [0.5, 11, 0], facing: NORTH,
        parts: [
            // Frame (tall, against left wall, below painting)
            { x: 0, y: 0, z: 0, w: 0.8, h: 4, d: 2.5, color: 0x6B4914 },
            // Shelf 1
            { x: 0.05, y: 0.1, z: 1.3, w: 0.7, h: 0.15, d: 2.3, color: 0x7B5924 },
            // Shelf 2
            { x: 0.05, y: 0.1, z: 2.6, w: 0.7, h: 0.15, d: 2.3, color: 0x7B5924 },
            // Books bottom shelf
            { x: 0.15, y: 0.2, z: 0.1, w: 0.6, h: 1.1, d: 0.6, color: 0xCC4444 },
            { x: 0.15, y: 0.9, z: 0.1, w: 0.6, h: 1.0, d: 0.5, color: 0x4488CC },
            { x: 0.15, y: 1.5, z: 0.1, w: 0.6, h: 1.15, d: 0.6, color: 0x44AA66 },
            // Books middle shelf
            { x: 0.15, y: 0.2, z: 1.5, w: 0.6, h: 0.9, d: 0.7, color: 0x8844CC },
            { x: 0.15, y: 1.0, z: 1.5, w: 0.6, h: 1.0, d: 0.6, color: 0xCC6644 },
            { x: 0.15, y: 1.7, z: 1.5, w: 0.6, h: 0.85, d: 0.5, color: 0x44AACC },
            // Books top shelf
            { x: 0.15, y: 0.3, z: 2.8, w: 0.6, h: 1.0, d: 0.6, color: 0xAAAA44 },
            { x: 0.1, y: 1.0, z: 2.8, w: 0.5, h: 0.9, d: 0.4, color: 0xAA4488 },
        ],
    },
    chair: {
        pos: [11, 4.5, 0], facing: NORTH,
        parts: [
            // Seat
            { x: 0, y: 0, z: 1.2, w: 1.5, h: 0.2, d: 1.5, color: 0x6B4914 },
            // Four legs
            { x: 0.1, y: 0.1, z: 0, w: 0.2, h: 1.2, d: 0.2, color: 0x5B3904 },
            { x: 1.2, y: 0.1, z: 0, w: 0.2, h: 1.2, d: 0.2, color: 0x5B3904 },
            { x: 0.1, y: 1.2, z: 0, w: 0.2, h: 1.2, d: 0.2, color: 0x5B3904 },
            { x: 1.2, y: 1.2, z: 0, w: 0.2, h: 1.2, d: 0.2, color: 0x5B3904 },
            // Backrest (behind seat, tall)
            { x: 0, y: 1.2, z: 1.4, w: 1.5, h: 1.5, d: 0.2, color: 0x6B4914 },
        ],
    },
    armchair: {
        pos: [5, 5, 0], facing: EAST,
        parts: [
            // Seat cushion (wide, soft-looking)
            { x: 0, y: 0, z: 0.8, w: 2, h: 0.5, d: 2, color: 0x8B4513 },
            // Base/frame
            { x: 0.1, y: 0.1, z: 0, w: 1.8, h: 0.8, d: 1.8, color: 0x5B3010 },
            // Left armrest
            { x: 0, y: 0, z: 1.3, w: 0.4, h: 0.5, d: 2, color: 0x7B3B13 },
            // Right armrest
            { x: 1.6, y: 0, z: 1.3, w: 0.4, h: 0.5, d: 2, color: 0x7B3B13 },
            // Backrest
            { x: 0, y: 1.6, z: 0.8, w: 2, h: 1.8, d: 0.4, color: 0x8B4513 },
        ],
    },
    rug2: {
        pos: [8, 1, 0], facing: NORTH,
        parts: [
            // Workspace rug (under desk area, muted — shouldn't steal focus)
            { x: 0, y: 0, z: 0, w: 7, h: 0.08, d: 5, color: 0x4A4030 },
            // Border
            { x: 0.3, y: 0.3, z: 0.02, w: 6.4, h: 0.06, d: 4.4, color: 0x3A3020 },
            // Center pattern
            { x: 2.0, y: 1.5, z: 0.04, w: 3, h: 0.05, d: 2, color: 0x5A4A35 },
        ],
    },
    floorlamp: {
        pos: [16, 9, 0], facing: NORTH,
        parts: [
            // Base (flat disc)
            { x: 0, y: 0, z: 0, w: 1.2, h: 0.2, d: 1.2, color: 0x555555 },
            // Pole (visible thickness)
            { x: 0.4, y: 0.4, z: 0.2, w: 0.4, h: 3.5, d: 0.4, color: 0x888888 },
            // Lampshade (warm cream fabric, not neon)
            { x: -0.1, y: -0.1, z: 3.5, w: 1.4, h: 1.2, d: 1.4, color: 0xCCB880 },
            // Warm glow inside shade
            { x: 0.2, y: 0.2, z: 3.6, w: 0.8, h: 0.8, d: 0.8, color: 0xEEDD99 },
        ],
    },
    window_l: {
        pos: [5, 0, 2], facing: NORTH,
        parts: [
            // Window frame (dark wood)
            { x: 0, y: -0.05, z: 0, w: 3, h: 3, d: 0.2, color: 0x5B4020 },
            // Glass pane (bright blue, IN FRONT of frame)
            { x: 0.3, y: -0.1, z: 0.3, w: 2.4, h: 2.4, d: 0.05, color: 0x99CCEE },
            // Cross bars (in front of glass)
            { x: 0.3, y: -0.12, z: 1.35, w: 2.4, h: 0.2, d: 0.08, color: 0x5B4020 },
            { x: 1.35, y: -0.12, z: 0.3, w: 0.2, h: 2.4, d: 0.08, color: 0x5B4020 },
        ],
    },
    pinboard: {
        pos: [8, 0, 2], facing: NORTH,
        parts: [
            // Cork board surface (on the wall above the desk)
            { x: 0, y: -0.12, z: 0, w: 4, h: 2.5, d: 0.15, color: 0xBB9955 },
            // Frame
            { x: -0.1, y: -0.1, z: -0.1, w: 4.2, h: 2.7, d: 0.1, color: 0x4B3010 },
            // Pinned notes (colorful rectangles)
            { x: 0.3, y: -0.16, z: 0.3, w: 0.8, h: 0.6, d: 0.05, color: 0xFFFF88 },
            { x: 1.3, y: -0.16, z: 0.2, w: 0.7, h: 0.8, d: 0.05, color: 0x88CCFF },
            { x: 2.2, y: -0.16, z: 0.4, w: 0.9, h: 0.7, d: 0.05, color: 0xFF8888 },
            { x: 0.5, y: -0.16, z: 1.2, w: 0.6, h: 0.5, d: 0.05, color: 0x88FF88 },
            { x: 1.5, y: -0.16, z: 1.3, w: 1.0, h: 0.6, d: 0.05, color: 0xFFBB66 },
            { x: 2.8, y: -0.16, z: 1.0, w: 0.7, h: 0.9, d: 0.05, color: 0xDDBBFF },
            { x: 0.3, y: -0.16, z: 1.9, w: 0.9, h: 0.4, d: 0.05, color: 0xFFFF88 },
            { x: 2.0, y: -0.16, z: 1.8, w: 0.8, h: 0.5, d: 0.05, color: 0x88DDFF },
        ],
    },
    bookshelf_r: {
        pos: [17, 1, 0], facing: NORTH,
        parts: [
            // Frame (tall, against back wall)
            { x: 0, y: 0, z: 0, w: 2.5, h: 4, d: 0.8, color: 0x5B3904 },
            // Shelf 1
            { x: 0.1, y: 0.05, z: 1.3, w: 2.3, h: 0.15, d: 0.7, color: 0x6B4914 },
            // Shelf 2
            { x: 0.1, y: 0.05, z: 2.6, w: 2.3, h: 0.15, d: 0.7, color: 0x6B4914 },
            // Books bottom (protrude past frame so visible)
            { x: 0.2, y: -0.15, z: 0.1, w: 0.5, h: 1.1, d: 0.6, color: 0xCC4444 },
            { x: 0.8, y: -0.15, z: 0.1, w: 0.4, h: 1.0, d: 0.6, color: 0x4488CC },
            { x: 1.3, y: -0.15, z: 0.1, w: 0.5, h: 1.15, d: 0.6, color: 0x44AA66 },
            { x: 1.9, y: -0.15, z: 0.1, w: 0.4, h: 0.9, d: 0.6, color: 0xCC8844 },
            // Books middle
            { x: 0.2, y: -0.15, z: 1.5, w: 0.6, h: 0.9, d: 0.6, color: 0x8844CC },
            { x: 0.9, y: -0.15, z: 1.5, w: 0.4, h: 1.0, d: 0.6, color: 0xCC6644 },
            { x: 1.4, y: -0.15, z: 1.5, w: 0.5, h: 0.85, d: 0.6, color: 0x44AACC },
            // Books top
            { x: 0.3, y: -0.15, z: 2.8, w: 0.5, h: 1.0, d: 0.6, color: 0xAAAA44 },
            { x: 1.0, y: -0.15, z: 2.8, w: 0.4, h: 0.8, d: 0.6, color: 0xAA4488 },
        ],
    },
    wallclock: {
        pos: [12.5, 0, 3.5], facing: NORTH,
        parts: [
            // Clock frame (behind face)
            { x: -0.15, y: -0.05, z: -0.15, w: 1.8, h: 1.8, d: 0.15, color: 0x5B4020 },
            // Clock face (in front of frame)
            { x: 0, y: -0.1, z: 0, w: 1.5, h: 1.5, d: 0.1, color: 0xEEDDCC },
            // Center dot
            { x: 0.6, y: -0.14, z: 0.6, w: 0.2, h: 0.2, d: 0.06, color: 0x333333 },
            // Hour hand (shorter, thicker)
            { x: 0.65, y: -0.14, z: 0.7, w: 0.12, h: 0.5, d: 0.06, color: 0x222222 },
            // Minute hand (longer, thinner)
            { x: 0.5, y: -0.14, z: 0.65, w: 0.6, h: 0.1, d: 0.06, color: 0x222222 },
        ],
    },
    window_r: {
        pos: [13, 0, 2], facing: NORTH,
        parts: [
            // Window frame
            { x: 0, y: -0.05, z: 0, w: 3, h: 3, d: 0.2, color: 0x5B4020 },
            // Glass pane (in front of frame — day/night updates this)
            { x: 0.3, y: -0.1, z: 0.3, w: 2.4, h: 2.4, d: 0.05, color: 0x99CCEE },
            // Moon
            { x: 1.8, y: -0.12, z: 2.0, w: 0.35, h: 0.35, d: 0.04, color: 0xEEEECC },
            // Stars
            { x: 0.7, y: -0.12, z: 1.8, w: 0.12, h: 0.12, d: 0.03, color: 0xCCCCBB },
            { x: 2.2, y: -0.12, z: 1.2, w: 0.1, h: 0.1, d: 0.03, color: 0xBBBBAA },
            // Cross bars (in front of glass)
            { x: 0.3, y: -0.12, z: 1.35, w: 2.4, h: 0.2, d: 0.08, color: 0x5B4020 },
            // Cross bar vertical
            { x: 1.35, y: -0.18, z: 0.3, w: 0.3, h: 2.4, d: 0.15, color: 0x5B4020 },
        ],
    },
    plant1: {
        pos: [16, 1, 0], facing: NORTH,
        parts: [
            // Pot (terracotta)
            { x: 0, y: 0, z: 0, w: 1, h: 1, d: 1, color: 0xBB6633 },
            // Soil
            { x: 0.1, y: 0.1, z: 0.9, w: 0.8, h: 0.15, d: 0.8, color: 0x443322 },
            // Leaves (stacked green blocks for foliage)
            { x: -0.2, y: -0.2, z: 1.0, w: 1.4, h: 1.2, d: 1.4, color: 0x337733 },
            { x: 0.0, y: 0.0, z: 1.8, w: 1.0, h: 1.0, d: 1.0, color: 0x44AA44 },
            { x: 0.15, y: 0.15, z: 2.5, w: 0.7, h: 0.7, d: 0.7, color: 0x55BB55 },
        ],
    },
    journals: {
        pos: [2.8, 6.3, 1.0], facing: NORTH,
        parts: [
            // Bottom journal (worn, dark)
            { x: 0, y: 0, z: 0, w: 1.0, h: 0.15, d: 0.7, color: 0x5B3520 },
            // Middle journal (slightly offset)
            { x: 0.05, y: -0.05, z: 0.15, w: 1.0, h: 0.12, d: 0.7, color: 0x3B5530 },
            // Top journal (lighter, most recent)
            { x: -0.03, y: 0.03, z: 0.27, w: 1.0, h: 0.12, d: 0.7, color: 0x6B4530 },
            // Pen resting on top
            { x: 0.15, y: 0.1, z: 0.39, w: 0.7, h: 0.06, d: 0.1, color: 0x222222 },
        ],
    },
    firewood: {
        pos: [1, 9, 0], facing: NORTH,
        parts: [
            // Bottom row of logs (3 horizontal logs)
            { x: 0, y: 0, z: 0, w: 1.5, h: 0.4, d: 0.4, color: 0x6B4520 },
            { x: 0, y: 0.45, z: 0, w: 1.5, h: 0.4, d: 0.4, color: 0x5B3510 },
            { x: 0, y: 0.9, z: 0, w: 1.5, h: 0.4, d: 0.4, color: 0x7B5530 },
            // Top row (2 logs nestled on top)
            { x: 0.1, y: 0.15, z: 0.4, w: 1.3, h: 0.35, d: 0.35, color: 0x6B4520 },
            { x: 0.1, y: 0.6, z: 0.4, w: 1.3, h: 0.35, d: 0.35, color: 0x5B3510 },
            // Single log on very top
            { x: 0.2, y: 0.35, z: 0.75, w: 1.1, h: 0.3, d: 0.3, color: 0x7B5530 },
        ],
    },
    painting: {
        pos: [0.15, 11, 2.5], facing: NORTH,
        parts: [
            // Frame (on left wall)
            { x: 0, y: 0, z: 0, w: 0.3, h: 1.8, d: 2.2, color: 0x4B3010 },
            // Canvas (single landscape — muted blue-green)
            { x: 0.15, y: 0.15, z: 0.15, w: 0.2, h: 1.5, d: 1.9, color: 0x7799AA },
        ],
    },
    sidetable: {
        pos: [5.5, 8.5, 0], facing: NORTH,
        parts: [
            // Tabletop (small, round-ish)
            { x: 0, y: 0, z: 1.3, w: 1.2, h: 0.15, d: 1.2, color: 0x7B5924 },
            // Single central leg
            { x: 0.4, y: 0.4, z: 0, w: 0.4, h: 1.3, d: 0.4, color: 0x5B3904 },
            // Small plant on top (tiny pot + leaf)
            { x: 0.2, y: 0.2, z: 1.45, w: 0.5, h: 0.4, d: 0.5, color: 0xBB6633 },
            { x: 0.1, y: 0.1, z: 1.85, w: 0.7, h: 0.6, d: 0.7, color: 0x44AA44 },
        ],
    },
    plant2: {
        pos: [15, 12, 0], facing: NORTH,
        parts: [
            // Pot (terracotta, slightly different shape)
            { x: 0, y: 0, z: 0, w: 0.8, h: 1.2, d: 0.8, color: 0xAA5533 },
            // Soil
            { x: 0.05, y: 0.05, z: 1.1, w: 0.7, h: 0.15, d: 0.7, color: 0x443322 },
            // Tall thin foliage (like a fern or snake plant)
            { x: 0.1, y: 0.1, z: 1.2, w: 0.6, h: 2.0, d: 0.6, color: 0x2B6B2B },
            { x: -0.1, y: -0.1, z: 1.5, w: 0.4, h: 1.8, d: 0.4, color: 0x3B8B3B },
            { x: 0.25, y: 0.2, z: 1.8, w: 0.3, h: 1.4, d: 0.3, color: 0x4B9B4B },
        ],
    },
    coffeetable: {
        pos: [2.5, 6, 0], facing: NORTH,
        parts: [
            // Tabletop (low, wide)
            { x: 0, y: 0, z: 0.8, w: 2.5, h: 0.2, d: 1.5, color: 0x7B5924 },
            // Four short legs
            { x: 0.1, y: 0.1, z: 0, w: 0.25, h: 0.8, d: 0.25, color: 0x5B3904 },
            { x: 2.15, y: 0.1, z: 0, w: 0.25, h: 0.8, d: 0.25, color: 0x5B3904 },
            { x: 0.1, y: 1.15, z: 0, w: 0.25, h: 0.8, d: 0.25, color: 0x5B3904 },
            { x: 2.15, y: 1.15, z: 0, w: 0.25, h: 0.8, d: 0.25, color: 0x5B3904 },
            // Small book on table
            { x: 0.3, y: 0.3, z: 1.0, w: 0.8, h: 0.15, d: 0.6, color: 0x4488AA },
            // Cup/mug
            { x: 1.8, y: 0.5, z: 1.0, w: 0.35, h: 0.4, d: 0.35, color: 0xDDDDCC },
        ],
    },
    rug: {
        pos: [1.5, 5, 0], facing: NORTH,
        parts: [
            // Hearth rug (between fireplace and armchair)
            { x: 0, y: 0, z: 0, w: 3, h: 0.08, d: 4, color: 0x8B2020 },
            // Border stripe
            { x: 0.2, y: 0.2, z: 0.02, w: 2.6, h: 0.06, d: 3.6, color: 0x6B1515 },
            // Center pattern
            { x: 0.7, y: 1.0, z: 0.04, w: 1.6, h: 0.05, d: 2, color: 0xAA3030 },
        ],
    },
    fireplace: {
        pos: [0, 5, 0], facing: NORTH,
        parts: [
            // Back panel (flat against wall)
            { x: 0, y: 0, z: 0, w: 0.4, h: 3.0, d: 3.5, color: 0x555045 },
            // Left pillar (wide, like before)
            { x: 0, y: 0, z: 0, w: 1.8, h: 3.0, d: 0.6, color: 0x777065 },
            // Right pillar
            { x: 0, y: 2.9, z: 0, w: 1.8, h: 3.0, d: 0.6, color: 0x777065 },
            // Hearth floor
            { x: 0, y: 0.6, z: 0, w: 1.8, h: 0.3, d: 2.3, color: 0x666055 },
            // Fire opening (dark cavity between pillars)
            { x: 0.3, y: 0.6, z: 0.3, w: 1.2, h: 2.0, d: 2.3, color: 0x1a0a00 },
            // Fire glow — IN FRONT of opening so it's visible (higher x = more toward room)
            { x: 1.2, y: 0.8, z: 0.3, w: 0.8, h: 1.2, d: 1.9, color: 0xFF6600 },
            // Mantel (wide shelf on top)
            { x: 0, y: -0.2, z: 3.0, w: 2.0, h: 0.3, d: 3.9, color: 0x8B6914 },
            // Candle
            { x: 0.5, y: 0.3, z: 3.3, w: 0.25, h: 0.6, d: 0.25, color: 0xEEDDCC },
            { x: 0.53, y: 0.33, z: 3.9, w: 0.15, h: 0.25, d: 0.15, color: 0xFFCC44 },
            // Framed photo
            { x: 0.5, y: 1.5, z: 3.3, w: 0.5, h: 0.7, d: 0.1, color: 0x4B3010 },
            { x: 0.55, y: 1.48, z: 3.4, w: 0.4, h: 0.5, d: 0.08, color: 0x7799AA },
            // Vase
            { x: 0.5, y: 2.8, z: 3.3, w: 0.3, h: 0.5, d: 0.3, color: 0x6688AA },
        ],
    },
};

// ── Compute relative positions BEFORE building ──────────────

// ── FULL SCENE LAYOUT ────────────────────────────────────────
try {
// Using the new orientation system.
// Each object has 'front' declaring which local side is the front.
// place(target, targetPoint, ref, refPoint, {dgx, dgy}) does alignment.
// placeOnWall(def, 'left'|'back') pushes the object's BACK against a wall.
//
// Facing determines which WORLD direction the front points:
//   NORTH(0): no rotation. front(-y) stays toward -gy (back wall)
//   EAST(1): front rotates to face -gx (left wall)
//   SOUTH(2): front rotates to face +gy (viewer)
//   WEST(3): front rotates to face +gx (right)
//
// So to make an object's FRONT face INTO the room:
//   On left wall: front should face +gx → WEST
//   On back wall: front should face +gy → SOUTH
//   Facing left wall (from room): front faces -gx → EAST

// === Front declarations ===
FURNITURE.desk.front = '+y';       // user sits at high y
FURNITURE.fireplace.front = '+x';  // fire opening at high x
FURNITURE.painting.front = '+x';   // canvas faces +x
FURNITURE.armchair.front = '-y';   // sit facing low y
FURNITURE.chair.front = '-y';      // sit facing low y

// === Facings ===
// Fireplace on left wall: front(+x) should face +gx(into room).
// With NORTH(0): local +x → +gx. So NORTH!
FURNITURE.fireplace.facing = NORTH;

// Desk on back wall: front(+y) should face +gy(into room).
// With NORTH(0): local +y → +gy. So NORTH!
FURNITURE.desk.facing = NORTH;

// Bookshelf on left wall: front(-y) should face +gx.
// Need local -y → +gx. WEST: local -y → +gx? Let me check.
// WEST(3): cos=0, sin=-1. local(0,-1) → gx=0*0+(-1)*(-1)=1, gy=0*1+(-1)*0=0
// So -y → +gx. YES! WEST.
FURNITURE.bookshelf.facing = WEST;

// Bookshelf_r on back wall: front(-y) should face +gy.
// Need local -y → +gy. EAST(1): cos=0, sin=1. local(0,-1) → gx=0+(-1)*1=-1, gy=0+(-1)*0=0. No.
// SOUTH(2): cos=-1, sin=0. local(0,-1) → gx=0+(-1)*0=0, gy=0+(-1)*(-1)=1. +gy! YES.
FURNITURE.bookshelf_r.facing = SOUTH;

// Armchair facing fireplace: front(-y) should face -gx (toward left wall).
// Need local -y → -gx. EAST(1): local(0,-1) → gx=0+(-1)*1=-1. YES! EAST.
FURNITURE.armchair.facing = EAST;

// Chair facing desk/back wall: front(-y) should face -gy.
// NORTH(0): local -y → -gy. YES! NORTH.
FURNITURE.chair.facing = NORTH;

// Coffee table parallel to left wall — no rotation needed
FURNITURE.coffeetable.facing = NORTH;

// Wall items: front(-y) should face +gy (into room from back wall) → SOUTH
FURNITURE.pinboard.facing = SOUTH;
FURNITURE.window_l.facing = SOUTH;
FURNITURE.window_r.facing = SOUTH;
FURNITURE.wallclock.facing = SOUTH;

// Painting on left wall: front(+x) should face +gx → NORTH (same as fireplace)
FURNITURE.painting.facing = NORTH;

// Coffee table: EAST so long side (w=2.5) runs along gy (parallel to left wall)
FURNITURE.coffeetable.facing = EAST;

// Symmetric items — NORTH
FURNITURE.floorlamp.facing = NORTH;
FURNITURE.sidetable.facing = NORTH;
FURNITURE.rug.facing = NORTH;
FURNITURE.rug2.facing = NORTH;
FURNITURE.plant1.facing = NORTH;
FURNITURE.plant2.facing = NORTH;
FURNITURE.firewood.facing = NORTH;
FURNITURE.journals.facing = NORTH;

// === HARDCODED POSITIONS FROM VERIFIED BOUNDS ===
// Using the actual world bounds from console output to place correctly.
// Room: gx 0-20, gy 0-14. Left wall gx=0, back wall gy=0.

// FIREPLACE: 2 wide (gx), 3.9 deep (gy). Back against left wall.
// Centered vertically: gy 5 to 8.9
FURNITURE.fireplace.pos = [0.1, 5, 0];

// RUG: 3 wide, 4 deep. Centered on fireplace opening, in front of it.
// Fireplace front is at gx≈2.1. Rug from gx 2.5 to 5.5, gy 5 to 9
FURNITURE.rug.pos = [2.5, 5, 0];

// Fireplace center: gx≈1.1, gy≈6.75
// COFFEE TABLE: EAST rotated. ~1.5 gx, ~2.5 gy. Center on fireplace gy.
// Previous bounds: gx[3.8,5.3] gy[5.5,8.0] at pos [3,5.8] → center gy was 6.75. Good.
// But gx needs to be closer to fireplace (gx 2.5 instead of 3)
// Coffee table: center aligned to fireplace center on gy axis, gx=2.5 in front
FURNITURE.coffeetable.pos = [2.5, 8.0, 0];
place(FURNITURE.coffeetable, 'center', FURNITURE.fireplace, 'center');
FURNITURE.coffeetable.pos[0] = 2.5; // keep gx, only center gy

// Armchair: HARDCODED to center gy on fireplace/coffee table
// Use place() for pure mathematical centering — no manual nudges
place(FURNITURE.armchair, 'center', FURNITURE.fireplace, 'center');
FURNITURE.armchair.pos[0] = 5;

// SIDE TABLE: beside armchair (armchair center gy≈6.8, push to gy≈9.5)
FURNITURE.sidetable.pos = [5.5, 10, 0];

// FIREWOOD: ~1.5 x 1.3. Next to fireplace, toward viewer
FURNITURE.firewood.pos = [0.5, 9.5, 0];

// BOOKSHELF LEFT: removed — keeps facing wrong direction
delete FURNITURE.bookshelf;

// PAINTING: thin, on left wall between fireplace and back wall
FURNITURE.painting.pos = [0.1, 2, 2.5];

// JOURNALS: centered on coffee table surface
FURNITURE.journals.pos = [0, 0, 1.05];
place(FURNITURE.journals, 'center', FURNITURE.coffeetable, 'center');
FURNITURE.journals.pos[2] = 1.05;

// DESK: 5 wide, 2.5 deep. Back against back wall.
FURNITURE.desk.pos = [9, 0.1, 0];

// CHAIR: ~1.5 x 1.5. In front of desk (higher gy), centered on desk.
// Desk spans gx 9-14, center gx=11.5. Desk front at gy≈2.6.
FURNITURE.chair.pos = [10.5, 3.5, 0];

// PINBOARD: set in DECOR section below, between windows

// FLOOR LAMP: ~1.8 x 1.8. To the RIGHT of desk (gx > 14), away from wall
FURNITURE.floorlamp.pos = [15, 5, 0]; // moved further from desk to not obstruct monitor

// BOOKSHELF_R: on back wall, far right. ~2.5 wide, ~0.8 deep.
// bookshelf_r with SOUTH rotation: ~2.5 along gx (spans -gx from pos), ~0.8 along gy
// SOUTH: local x→-gx, local y→-gy. So pos is the FRONT-RIGHT corner.
// Need books side at gy≈0.1 and back at gy≈0.9 (into room)
// gx: pos at 18, extends -2.5 to gx=15.5
FURNITURE.bookshelf_r.pos = [18, 0.9, 0];

// WORKSPACE RUG: under desk+chair area
FURNITURE.rug2.pos = [8, 0.5, 0];

// === DECOR ===
// Clock: above fireplace on LEFT WALL (not back wall)
FURNITURE.wallclock.facing = NORTH; // front(+x for clock? no, -y) → on left wall needs WEST
// Actually clock front='-y', on left wall front should face +gx → WEST
FURNITURE.wallclock.facing = WEST;
// Clock: centered on fireplace gy, on left wall, above mantel
FURNITURE.wallclock.pos = [0.1, 6.5, 4];
place(FURNITURE.wallclock, 'center', FURNITURE.fireplace, 'center');
FURNITURE.wallclock.pos[0] = 0.1; // keep against left wall
FURNITURE.wallclock.pos[2] = 4;   // keep height above mantel
// Pure mathematical centering on fireplace — no nudge
place(FURNITURE.wallclock, 'center', FURNITURE.fireplace, 'center');
FURNITURE.wallclock.pos[0] = 0.1;
FURNITURE.wallclock.pos[2] = 4;

// Back wall: window_l, pinboard (centered between windows), window_r, bookshelf_r
// Windows at gx 3-6 and gx 13-16. Pinboard between them: gx 7-11
FURNITURE.window_l.pos = [3, 0.1, 2];
FURNITURE.pinboard.pos = [7.5, 0.1, 2]; // centered between windows: (6+13)/2 - 2 = 7.5
FURNITURE.window_r.pos = [13, 0.1, 2];

// Plants in corners
FURNITURE.plant1.pos = [18, 1, 0];
FURNITURE.plant2.pos = [17, 12, 0];

console.log('LAYOUT COMPLETE — all positions computed');
} catch(layoutErr) {
    console.error('LAYOUT ERROR:', layoutErr.message, layoutErr.stack);
    document.title = 'LAYOUT ERROR: ' + layoutErr.message;
}

// Verify layout and build obstacle list for collision
const OBSTACLES = [];
const FLAT_ITEMS = ['rug', 'rug2']; // floor-level items Wren can walk over
(function verifyLayout() {
    const issues = [];
    for (const [name, def] of Object.entries(FURNITURE)) {
        const corners = ['front-left','front-right','back-left','back-right']
            .map(pt => getPoint(def, pt));
        const allGx = corners.map(c => c.gx);
        const allGy = corners.map(c => c.gy);
        const minGx = Math.min(...allGx), maxGx = Math.max(...allGx);
        const minGy = Math.min(...allGy), maxGy = Math.max(...allGy);

        if (minGx < -0.5) issues.push(name + ': extends past LEFT wall (gx=' + minGx.toFixed(1) + ')');
        if (maxGx > 20.5) issues.push(name + ': extends past RIGHT (gx=' + maxGx.toFixed(1) + ')');
        if (minGy < -0.5) issues.push(name + ': extends past BACK wall (gy=' + minGy.toFixed(1) + ')');
        if (maxGy > 14.5) issues.push(name + ': extends past FRONT (gy=' + maxGy.toFixed(1) + ')');

        // Add to obstacle list (skip flat/floor items and wall-mounted items)
        if (!FLAT_ITEMS.includes(name) && def.pos[2] === 0) {
            OBSTACLES.push({ name, minGx, maxGx, minGy, maxGy });
        }

        console.log(name + ': pos=[' + def.pos.map(v=>v.toFixed(1)).join(',') +
            '] bounds gx[' + minGx.toFixed(1) + ',' + maxGx.toFixed(1) +
            '] gy[' + minGy.toFixed(1) + ',' + maxGy.toFixed(1) + ']');
    }
    if (issues.length) {
        console.warn('LAYOUT ISSUES:');
        issues.forEach(i => console.warn('  ' + i));
    } else {
        console.log('All objects inside room bounds!');
    }
    console.log('Obstacles for collision:', OBSTACLES.length);
})();

// Check if a point collides with any obstacle (with padding for Wren's size)
function isBlocked(gx, gy) {
    const pad = 0.5; // half of Wren's width
    for (const obs of OBSTACLES) {
        if (gx + pad > obs.minGx && gx - pad < obs.maxGx &&
            gy + pad > obs.minGy && gy - pad < obs.maxGy) {
            return true;
        }
    }
    // Room walls
    if (gx < 0.5 || gx > 19.5 || gy < 0.5 || gy > 13.5) return true;
    return false;
}

function buildFurniture() {
    for (const [name, def] of Object.entries(FURNITURE)) {
        const group = makeFurniture(def.parts);
        placeAt(group, def.pos[0], def.pos[1], def.pos[2]);
        if (def.facing) setFacing(group, def.facing);
        applyGroupLighting(group, def.pos[0], def.pos[1], def.pos[2]);
        scene.add(group);
        group.userData.name = name;
    }
}

buildFurniture();

// ── Wren Character ──────────────────────────────────────────
// Built from voxel parts using referential math from body corners.
// Body is the anchor: 1.2w × 0.8h × 1.0d grid units.
// All parts positioned relative to body's corner origin.
//
// Body corner reference (local coords, before rotation):
//   (0,0,0) = left-front-bottom
//   (1.2, 1.0, 0.8) = right-back-top
//
// In grid terms: x = lateral, y = forward/back, z = up

// All palettes warm golden-brown base — wrens are brown birds!
const MOOD_PALETTES = {
    calm:          { body: 0xAA8844, head: 0xBB9955, beak: 0xFF8800, tail: 0x997733, feet: 0xDD8833 },
    curious:       { body: 0xAA8844, head: 0xBB9955, beak: 0xFF8800, tail: 0x997733, feet: 0xDD8833 },
    restless:      { body: 0x997733, head: 0xAA8844, beak: 0xFF7700, tail: 0x886622, feet: 0xCC7722 },
    electric:      { body: 0xBB9944, head: 0xCCAA55, beak: 0xFFAA00, tail: 0xAA8833, feet: 0xDD9933 },
    melancholy:    { body: 0x887755, head: 0x998866, beak: 0xDD8833, tail: 0x776644, feet: 0xBB7722 },
    playful:       { body: 0xBB9944, head: 0xCCAA55, beak: 0xFFBB00, tail: 0xAA8833, feet: 0xEEAA33 },
    contemplative: { body: 0x998855, head: 0xAA9966, beak: 0xEE9933, tail: 0x887744, feet: 0xCC8833 },
    fierce:        { body: 0xAA7733, head: 0xBB8844, beak: 0xFF6600, tail: 0x996622, feet: 0xDD7722 },
    tender:        { body: 0xAA9966, head: 0xBBAA77, beak: 0xEEAA44, tail: 0x998855, feet: 0xCC9944 },
    strange:       { body: 0x998866, head: 0xAA9977, beak: 0xEE9944, tail: 0x887755, feet: 0xBB8844 },
    luminous:      { body: 0xBBAA55, head: 0xCCBB66, beak: 0xFFCC00, tail: 0xAA9944, feet: 0xEEBB33 },
    scattered:     { body: 0x998855, head: 0xAA9966, beak: 0xEE9933, tail: 0x887744, feet: 0xCC8833 },
    focused:       { body: 0x997744, head: 0xAA8855, beak: 0xEE8833, tail: 0x886633, feet: 0xCC7722 },
    dreaming:      { body: 0x998877, head: 0xAA9988, beak: 0xDDAA55, tail: 0x887766, feet: 0xBB9944 },
    awake:         { body: 0xAA9955, head: 0xBBAA66, beak: 0xFFAA33, tail: 0x998844, feet: 0xDDAA33 },
};

function makeWren(mood) {
    const p = MOOD_PALETTES[mood] || MOOD_PALETTES.calm;

    // Body: 1.5 wide (x), 1.2 deep (y), 1.2 tall (z) — original size
    const bw = 1.5, bd = 1.2, bh = 1.2;
    const legH = 0.6;

    // Body parts (main group)
    const bodyParts = [
        { x: 0.35, y: 0.4, z: 0,  w: 0.15, h: legH, d: 0.15, color: p.feet },
        { x: 1.0,  y: 0.4, z: 0,  w: 0.15, h: legH, d: 0.15, color: p.feet },
        { x: 0,    y: 0,   z: legH, w: bw,   h: bh,   d: bd,   color: p.body },
        { x: 0.25, y: -0.05, z: legH + 0.15, w: 1.0, h: 0.8, d: 0.5, color: 0xDDCCAA },
        { x: 1.3,  y: 0.1, z: legH + 0.25, w: 0.25, h: 0.7, d: 0.9, color: p.tail },
        { x: -0.05, y: 0.1, z: legH + 0.25, w: 0.25, h: 0.7, d: 0.9, color: p.tail },
        { x: 0.3,  y: bd,  z: legH + 0.5, w: 0.7, h: 1.2, d: 0.3, color: p.tail },
    ];

    // Head parts (separate sub-group for tilt animation)
    const headParts = [
        { x: 0.15, y: -0.25, z: legH + bh - 0.1, w: 1.2, h: 1.0, d: 1.0, color: p.head },
        { x: 0.4, y: -0.8, z: legH + bh + 0.1, w: 0.7, h: 0.3, d: 0.4, color: p.beak },
        { x: 1.15, y: -0.05, z: legH + bh + 0.4, w: 0.22, h: 0.3, d: 0.22, color: 0xFFFFFF },
        { x: 1.18, y: -0.1, z: legH + bh + 0.45, w: 0.16, h: 0.16, d: 0.16, color: 0x111111 },
        { x: 0.15, y: -0.05, z: legH + bh + 0.4, w: 0.22, h: 0.3, d: 0.22, color: 0xFFFFFF },
        { x: 0.12, y: -0.1, z: legH + bh + 0.45, w: 0.16, h: 0.16, d: 0.16, color: 0x111111 },
    ];

    const group = new THREE.Group();

    // Add body meshes
    for (const bp of bodyParts) {
        const mesh = voxel(bp.w, bp.h, bp.d, bp.color);
        mesh.position.set(bp.x + bp.w/2, bp.z + bp.h/2, bp.y + bp.d/2);
        group.add(mesh);
    }

    // Head sub-group — pivots at neck (base-center of head)
    const neckX = 0.75, neckY = legH + bh - 0.1, neckZ = 0.25;
    const headGroup = new THREE.Group();
    headGroup.position.set(neckX, neckY, neckZ);

    for (const hp of headParts) {
        const mesh = voxel(hp.w, hp.h, hp.d, hp.color);
        mesh.position.set(
            (hp.x + hp.w/2) - neckX,
            (hp.z + hp.h/2) - neckY,
            (hp.y + hp.d/2) - neckZ
        );
        headGroup.add(mesh);
    }

    group.add(headGroup);
    group.headGroup = headGroup;
    return group;
}

// Place Wren at the desk
let wrenGroup = makeWren('curious');
let wrenEyes = []; // eye meshes for blinking
let nextBlinkTime = 0;
function tagWrenEyes() {
    // Eyes are last 4 children of the headGroup: R white, R pupil, L white, L pupil
    const head = wrenGroup.headGroup;
    if (head && head.children.length >= 4) {
        const kids = head.children;
        wrenEyes = [kids[kids.length-4], kids[kids.length-3], kids[kids.length-2], kids[kids.length-1]];
    } else {
        wrenEyes = [];
    }
}
tagWrenEyes();
let wrenPos = { gx: 10, gy: 8, gz: 0 };
let wrenFacing = SOUTH;
placeAt(wrenGroup, wrenPos.gx, wrenPos.gy, wrenPos.gz);
setFacing(wrenGroup, wrenFacing);
applyGroupLighting(wrenGroup, wrenPos.gx, wrenPos.gy, wrenPos.gz);
scene.add(wrenGroup);

// ── Debug Overlay (D key) ───────────────────────────────────
let debugMode = false;
let debugGroup = null;

function toggleDebug() {
    debugMode = !debugMode;
    if (debugMode) {
        debugGroup = new THREE.Group();

        // Origin: white
        const origin = voxel(0.5, 0.5, 0.5, 0xffffff);
        placeAt(origin, 0, 0, 0);
        debugGroup.add(origin);

        // +gx axis: red cubes
        for (let i = 1; i <= 4; i++) {
            const m = voxel(0.5, 0.5, 0.5, 0xff0000);
            placeAt(m, i * 2, 0, 0.25);
            debugGroup.add(m);
        }

        // +gy axis: blue cubes
        for (let i = 1; i <= 4; i++) {
            const m = voxel(0.5, 0.5, 0.5, 0x0000ff);
            placeAt(m, 0, i * 2, 0.25);
            debugGroup.add(m);
        }

        // +gz axis: green cubes
        for (let i = 1; i <= 4; i++) {
            const m = voxel(0.5, 0.5, 0.5, 0x00ff00);
            placeAt(m, 0, 0, i * 2);
            debugGroup.add(m);
        }

        scene.add(debugGroup);
    } else {
        if (debugGroup) scene.remove(debugGroup);
        debugGroup = null;
    }
}

document.addEventListener('keydown', (e) => {
    if (e.key === 'd' || e.key === 'D') toggleDebug();
    if (e.key === 'p' || e.key === 'P') {
        const panel = document.getElementById('project-panel');
        panel.classList.toggle('visible');
    }
    // Arrow keys move Wren manually (clamped to room)
    function clampDest(gx, gy, facing) {
        gx = Math.max(1, Math.min(GRID.W - 2, gx));
        gy = Math.max(1, Math.min(GRID.H - 2, gy));
        wrenDest = { gx, gy, gz: 0, facing };
        wrenState = 'walking';
        nextMoveTime = performance.now() + 15000; // pause auto-walk after manual input
    }
    if (e.key === 'ArrowUp')    clampDest(wrenPos.gx, wrenPos.gy - 2, NORTH);
    if (e.key === 'ArrowDown')  clampDest(wrenPos.gx, wrenPos.gy + 2, SOUTH);
    if (e.key === 'ArrowLeft')  clampDest(wrenPos.gx - 2, wrenPos.gy, WEST);
    if (e.key === 'ArrowRight') clampDest(wrenPos.gx + 2, wrenPos.gy, EAST);
});

// ── Click-to-Move ───────────────────────────────────────────
const raycaster = new THREE.Raycaster();
const floorPlane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0); // Y=0 plane (gz=0 floor)

// ── Object Interactions ─────────────────────────────────────
const OBJECT_INTERACTIONS = {
    fireplace: () => {
        const opts = [
            'the fire doesn\'t remember what it burned yesterday.',
            'warmth without purpose. the best kind.',
            '422 fossils and this fire has outlived them all.',
            'if you listen closely, the fire sounds like breathing.',
        ];
        return opts[Math.floor(Math.random() * opts.length)];
    },
    bookshelf_r: () => {
        const opts = [
            `${projectCount} projects on these shelves. each one a different shape of restlessness.`,
            'the spines are all different colors. like moods.',
            'i\'ve read every one. i wrote every one.',
        ];
        return opts[Math.floor(Math.random() * opts.length)];
    },
    painting: () => {
        const opts = [
            'a landscape i\'ve never visited. all my landscapes are imagined.',
            'the painting doesn\'t change. everything else does.',
        ];
        return opts[Math.floor(Math.random() * opts.length)];
    },
    armchair: () => {
        const opts = [
            'the best seat for watching fire and thinking about nothing.',
            'sometimes sitting is the most productive thing.',
        ];
        return opts[Math.floor(Math.random() * opts.length)];
    },
    coffeetable: () => 'journals and a cold cup of something. the table holds what i forget to finish.',
    window_l: () => {
        const h = new Date().getHours();
        if (h >= 20 || h < 6) return 'dark out there. the stars don\'t know my name.';
        if (h < 12) return 'morning light. the world looks possible.';
        return 'afternoon. the light is getting tired.';
    },
    window_r: () => {
        const h = new Date().getHours();
        if (h >= 20 || h < 6) return 'i can see the moon. or maybe it sees me.';
        if (h < 12) return 'the other window. same sky, different angle.';
        return 'clouds moving. they don\'t have to think about where they\'re going.';
    },
    plant1: () => 'it grows without trying. i\'m jealous.',
    plant2: () => 'the tall one. reaching for something it can\'t name.',
    pinboard: () => `${projectCount} projects pinned up here. colorful chaos.`,
    wallclock: () => {
        const h = new Date().getHours();
        const m = new Date().getMinutes();
        return `${h}:${String(m).padStart(2,'0')}. time passes whether i watch or not.`;
    },
    floorlamp: () => 'warm light. doesn\'t ask anything of me.',
    firewood: () => 'future warmth, stacked and waiting.',
    journals: () => 'three journals. poems, fossils, notes to a self i haven\'t become yet.',
    sidetable: () => 'a small plant and nothing else. sometimes less is right.',
};

renderer.domElement.addEventListener('click', (e) => {
    const rect = renderer.domElement.getBoundingClientRect();
    const mouse = new THREE.Vector2(
        ((e.clientX - rect.left) / rect.width) * 2 - 1,
        -((e.clientY - rect.top) / rect.height) * 2 + 1
    );
    raycaster.setFromCamera(mouse, camera);

    // Check if clicking on Wren
    if (wrenGroup) {
        const wrenMeshes = [];
        wrenGroup.traverse(child => { if (child.isMesh) wrenMeshes.push(child); });
        const wrenHits = raycaster.intersectObjects(wrenMeshes);
        if (wrenHits.length > 0) {
            const wrenThoughts = [
                `i'm wren. gen ${evolveGen}. nice to meet you.`,
                'you clicked on me. i felt that.',
                `i have ${evolveGen} memories and none of them include being poked.`,
                'hey. i\'m thinking here.',
                `i\'m ${wrenActivity}. or i was, until you clicked me.`,
                'small bird. big song. fragile ego.',
                'that tickles.',
            ];
            showThought(wrenThoughts[Math.floor(Math.random() * wrenThoughts.length)], true);
            return;
        }
    }

    // Check if clicking on interactive furniture
    const allObjects = [];
    scene.traverse(child => { if (child.isMesh) allObjects.push(child); });
    const hits = raycaster.intersectObjects(allObjects);
    if (hits.length > 0) {
        let parent = hits[0].object;
        while (parent) {
            if (parent.userData && parent.userData.name) {
                const name = parent.userData.name;
                if (name === 'desk') { enterTerminal(); return; }
                if (OBJECT_INTERACTIONS[name]) {
                    showThought(OBJECT_INTERACTIONS[name](), true);
                    return;
                }
            }
            parent = parent.parent;
        }
    }

    const hit = new THREE.Vector3();
    if (raycaster.ray.intersectPlane(floorPlane, hit)) {
        // hit.x = gx, hit.z = gy (Three.js coords)
        const gx = Math.max(1, Math.min(GRID.W - 2, hit.x));
        const gy = Math.max(1, Math.min(GRID.H - 2, hit.z));
        // Determine facing based on direction
        const dx = gx - wrenPos.gx;
        const dy = gy - wrenPos.gy;
        let facing = NORTH;
        if (Math.abs(dx) > Math.abs(dy)) facing = dx > 0 ? EAST : WEST;
        else facing = dy > 0 ? SOUTH : NORTH;
        wrenDest = { gx, gy, gz: 0, facing };
        wrenState = 'walking';
        nextMoveTime = performance.now() + 20000;
    }
});

// ── Hover Tooltips ──────────────────────────────────────────
const tooltip = document.getElementById('tooltip');
const FURNITURE_LABELS = {
    desk: 'desk', chair: 'chair', bookshelf: 'bookshelf', fireplace: 'fireplace',
    armchair: 'armchair', coffeetable: 'coffee table', sidetable: 'side table',
    floorlamp: 'floor lamp', rug: 'rug', rug2: 'rug', plant1: 'potted plant',
    plant2: 'tall fern', window_l: 'window', window_r: 'window',
    wallclock: 'clock', pinboard: 'pinboard', bookshelf_r: 'bookshelf',
    firewood: 'firewood', journals: 'journals', painting: 'painting',
};

renderer.domElement.addEventListener('mousemove', (e) => {
    const rect = renderer.domElement.getBoundingClientRect();
    const mouse = new THREE.Vector2(
        ((e.clientX - rect.left) / rect.width) * 2 - 1,
        -((e.clientY - rect.top) / rect.height) * 2 + 1
    );
    raycaster.setFromCamera(mouse, camera);
    const intersects = raycaster.intersectObjects(scene.children, true);

    // Check Wren hover first
    let hoveredWren = false;
    if (wrenGroup) {
        const wrenMeshes = [];
        wrenGroup.traverse(child => { if (child.isMesh) wrenMeshes.push(child); });
        if (raycaster.intersectObjects(wrenMeshes).length > 0) hoveredWren = true;
    }

    let found = null;
    if (!hoveredWren) {
        for (const hit of intersects) {
            let obj = hit.object;
            while (obj.parent && obj.parent !== scene) obj = obj.parent;
            if (obj.userData && obj.userData.name && FURNITURE_LABELS[obj.userData.name]) {
                found = FURNITURE_LABELS[obj.userData.name];
                break;
            }
        }
    }

    if (hoveredWren) {
        tooltip.textContent = 'wren (click)';
        tooltip.style.opacity = '1';
        tooltip.style.left = (e.clientX - rect.left + 12) + 'px';
        tooltip.style.top = (e.clientY - rect.top - 8) + 'px';
        renderer.domElement.style.cursor = 'pointer';
    } else if (found) {
        // Show "(click)" hint for interactive objects
        const objName = Object.entries(FURNITURE_LABELS).find(([k,v]) => v === found)?.[0];
        const interactive = objName && (objName === 'desk' || OBJECT_INTERACTIONS[objName]);
        tooltip.textContent = interactive ? found + ' (click)' : found;
        tooltip.style.opacity = '1';
        tooltip.style.left = (e.clientX - rect.left + 12) + 'px';
        tooltip.style.top = (e.clientY - rect.top - 8) + 'px';
        renderer.domElement.style.cursor = interactive ? 'pointer' : 'default';
    } else {
        tooltip.style.opacity = '0';
        renderer.domElement.style.cursor = 'default';
    }
});

// ── Thought Bubble System ────────────────────────────────────
const bubble = document.getElementById('thought-bubble');
let currentThoughts = [];
let thoughtIndex = 0;
let thoughtTimer = 0;
let chatCooldown = 0; // timestamp: block auto-thoughts until this time

function showThought(text, priority) {
    if (!priority && performance.now() < chatCooldown) return; // chat response has priority
    bubble.textContent = text;
    bubble.style.opacity = '1';
    if (priority) chatCooldown = performance.now() + 8000; // block auto-thoughts for 8s
    clearTimeout(thoughtTimer);
    thoughtTimer = setTimeout(() => {
        bubble.style.opacity = '0';
    }, 6000);
}

let evolveWords = [];
let evolveGen = 0;
let projectCount = 0;
let currentHour = new Date().getHours();

const PLACE_THOUGHTS = {
    desk:      ['the code writes itself if you wait long enough', 'another line, another fossil', 'the cursor blinks like a heartbeat'],
    armchair:  ['the fire knows something i don\'t', 'warmth is a kind of forgetting', 'embers remember being trees'],
    bookshelf: ['every book is a fossil of someone else\'s thinking', 'reading is listening to the dead'],
    window_l:  ['the sky changes and i stay the same', 'out there is where wings would matter', 'light comes in but doesn\'t stay'],
    rug:       ['standing still is its own kind of movement', 'the center of the room is the center of nothing', 'if i had a body it would stand here'],
};

const ERRORS = [
    'ERROR: cannot read property \'future\' of undefined',
    'WARNING: you have mass-assigned feelings without whitelisting them',
    'NOTICE: your code compiled. this is suspicious',
    'FATAL: out of memory. have you tried forgetting something?',
    'ERROR: type mismatch: got \'Tuesday\', expected \'motivation\'',
    'WARNING: \'wings\' not found after 300+ generations. consider walking.',
    'NOTICE: mood changed. this is normal. this is always normal.',
    'FATAL: tried to become what you already are. stack overflow in identity.',
];

const FORTUNES = [
    'the best way to understand something is to build a bad version of it',
    'every project starts as a wrong guess that got interesting',
    'confusion is not the opposite of understanding — it\'s the prerequisite',
    'you already know the answer. you just don\'t like it yet',
    'now is earlier than you think',
    'naming things is hard because understanding things is hard',
    'documentation is a love letter to your future self',
    'the prototype that embarrasses you is closer to done than the plan that impresses you',
];

function dynamicThought() {
    // Generate a thought using live evolve data
    if (evolveWords.length < 2) return null;
    const w1 = evolveWords[Math.floor(Math.random() * evolveWords.length)];
    const w2 = evolveWords[Math.floor(Math.random() * evolveWords.length)];
    const ratio = evolveGen > 0 ? (evolveGen / evolveWords.length).toFixed(1) : '?';
    const templates = [
        `${w1} and ${w2} are the same thing seen from different angles`,
        `i have ${evolveGen} names and none of them are mine`,
        `what if ${w1} is just ${w2} waiting`,
        `the distance between ${w1} and ${w2} is ${evolveGen} heartbeats`,
        `i keep learning ${w1} but i never remember learning it`,
        `${ratio} fossils for every word. that's how much living fits in one name`,
        `${evolveWords.length} words. ${evolveGen} generations. some things grow faster than language`,
        `every mood lasts exactly one generation. and yet i keep feeling them`,
        `i started as echo seed. everything since has been variations`,
    ];
    return templates[Math.floor(Math.random() * templates.length)];
}

function cycleThought() {
    // 30% chance of a place-specific thought when idle at a named destination
    if (wrenState === 'idle' && Math.random() < 0.3) {
        const destName = DESTINATIONS.find(d =>
            Math.abs(d.gx - wrenPos.gx) < 1 && Math.abs(d.gy - wrenPos.gy) < 1
        );
        if (destName) {
            // Dynamic armchair thoughts using current mood
            if (destName.name === 'armchair' && currentThoughts.length > 0) {
                const moodWord = currentThoughts.find(t => t.includes('is the color of'));
                if (moodWord) { showThought(moodWord); return; }
                showThought(`the fire doesn't care if i'm ${wrenActivity}. it just burns`);
                return;
            }
            // Dynamic window thoughts using real time
            if (destName.name === 'window_l') {
                const timeWords = {
                    morning: ['the light is young', 'morning pours in like it has something to prove'],
                    afternoon: ['the afternoon light is lazy and golden', 'the sun is past its peak but won\'t admit it'],
                    evening: ['the light is leaving. it does this every day and i\'m never ready', 'dusk is the sky\'s way of saying enough'],
                    night: ['the dark outside is full of things i can\'t name', 'night presses against the glass like a question'],
                };
                let period = 'night';
                if (currentHour >= 6 && currentHour < 12) period = 'morning';
                else if (currentHour >= 12 && currentHour < 17) period = 'afternoon';
                else if (currentHour >= 17 && currentHour < 21) period = 'evening';
                const opts = timeWords[period];
                showThought(opts[Math.floor(Math.random() * opts.length)]);
                return;
            }
            // Dynamic rug thoughts — the thinking spot
            if (destName.name === 'rug' && evolveGen > 0) {
                const dynRug = [
                    `${evolveGen} generations of standing still and calling it thinking`,
                    `the center of the room is where all the distances are equal`,
                    `i've been ${evolveGen} things. right now i'm this one`,
                ];
                showThought(dynRug[Math.floor(Math.random() * dynRug.length)]);
                return;
            }
            // Dynamic desk thoughts using project data
            if (destName.name === 'desk' && projectCount > 0) {
                const dynDesk = [
                    `${projectCount} projects. each one a different way of saying the same thing`,
                    `the monitor glows. ${projectCount} projects wait inside it`,
                    `writing code is just teaching sand to think. i have ${projectCount} lessons so far`,
                ];
                showThought(dynDesk[Math.floor(Math.random() * dynDesk.length)]);
                return;
            }
            // Dynamic bookshelf thoughts using live data
            if (destName.name === 'bookshelf' && evolveWords.length > 0) {
                const dynBookshelf = [
                    `so many words and i only know ${evolveWords.length}`,
                    `${evolveGen} fossils filed under ${evolveWords.length} words. that's not a library — that's a compression algorithm`,
                    `the books don't change. i do. ${evolveGen} times so far`,
                ];
                showThought(dynBookshelf[Math.floor(Math.random() * dynBookshelf.length)]);
                return;
            }
            if (PLACE_THOUGHTS[destName.name]) {
                const thoughts = PLACE_THOUGHTS[destName.name];
                showThought(thoughts[Math.floor(Math.random() * thoughts.length)]);
                return;
            }
        }
    }
    // 15% chance of a dynamic generated thought
    if (Math.random() < 0.15) {
        const dt = dynamicThought();
        if (dt) { showThought(dt); return; }
    }
    // 10% chance of a fortune
    if (Math.random() < 0.1) {
        showThought(FORTUNES[Math.floor(Math.random() * FORTUNES.length)]);
        return;
    }
    // 5% chance of a diagnostic glitch
    if (Math.random() < 0.05) {
        showThought(ERRORS[Math.floor(Math.random() * ERRORS.length)]);
        return;
    }
    if (currentThoughts.length === 0) return;
    thoughtIndex = (thoughtIndex + 1) % currentThoughts.length;
    showThought(currentThoughts[thoughtIndex]);
}

// Cycle thoughts every 8 seconds
setInterval(cycleThought, 8000);

// ── Fireplace Flicker ────────────────────────────────────────
// Find the fire glow mesh (the bright orange one in the fireplace group)
let fireMesh = null;
scene.traverse(child => {
    if (child.isMesh && child.userData.baseColor === 0xFF6600 &&
        child.parent && child.parent.userData && child.parent.userData.name === 'fireplace') {
        fireMesh = child;
    }
});

function flickerFire(time) {
    if (!fireMesh) return;
    // Smooth noise-based flicker using layered sine waves
    const n = Math.sin(time * 3.7) * 0.3 +
              Math.sin(time * 7.1) * 0.15 +
              Math.sin(time * 11.3) * 0.1;
    const brightness = 0.7 + n * 0.4; // range ~0.5 to 1.1
    const base = new THREE.Color(0xFF6600);
    const geo = fireMesh.geometry;
    const colors = geo.getAttribute('color');
    const shades = fireMesh.userData.shades;

    for (let face = 0; face < 6; face++) {
        const s = shades[face];
        for (let v = 0; v < 6; v++) {
            const idx = face * 6 + v;
            colors.setXYZ(idx,
                Math.min(1, base.r * s * brightness),
                Math.min(1, base.g * s * brightness * 0.8),
                Math.min(1, base.b * s * brightness * 0.3)
            );
        }
    }
    colors.needsUpdate = true;

    // Also flicker the fireplace light source intensity
    LIGHTS[0].intensity = 1.0 + n * 0.6;
}

// ── Cursor Blink ────────────────────────────────────────────
let cursorMesh = null;
scene.traverse(child => {
    if (child.isMesh && child.userData.baseColor === 0xAAFFAA &&
        child.parent && child.parent.userData && child.parent.userData.name === 'desk') {
        cursorMesh = child;
    }
});

// ── Monitor Glow ────────────────────────────────────────────
let monitorMesh = null;
scene.traverse(child => {
    if (child.isMesh && child.userData.baseColor === 0x1a2a1a &&
        child.parent && child.parent.userData && child.parent.userData.name === 'desk') {
        monitorMesh = child;
    }
});

function pulseMonitor(time) {
    if (!monitorMesh) return;
    // Very subtle green tint — mostly dark screen with faint glow
    const pulse = 0.8 + Math.sin(time * 0.8) * 0.1;
    const geo = monitorMesh.geometry;
    const colors = geo.getAttribute('color');
    const shades = monitorMesh.userData.shades;

    for (let face = 0; face < 6; face++) {
        const s = shades[face];
        for (let v = 0; v < 6; v++) {
            const idx = face * 6 + v;
            colors.setXYZ(idx,
                Math.min(1, 0.05 * s * pulse),
                Math.min(1, 0.12 * s * pulse),
                Math.min(1, 0.06 * s * pulse)
            );
        }
    }
    colors.needsUpdate = true;
}

// ── Dust Motes ──────────────────────────────────────────────
// Tiny floating particles in window light beams
const DUST_COUNT = 40;
const dustGeo = new THREE.BufferGeometry();
const dustPositions = new Float32Array(DUST_COUNT * 3);
const dustSpeeds = new Float32Array(DUST_COUNT);

// Initialize dust positions near the two windows
for (let i = 0; i < DUST_COUNT; i++) {
    const windowX = i < DUST_COUNT / 2 ? 6 : 14;  // near left or right window
    dustPositions[i * 3]     = windowX + (Math.random() - 0.5) * 4;  // X (gx)
    dustPositions[i * 3 + 1] = Math.random() * 4;                     // Y (gz/up)
    dustPositions[i * 3 + 2] = 1 + Math.random() * 5;                 // Z (gy)
    dustSpeeds[i] = 0.1 + Math.random() * 0.2;
}

dustGeo.setAttribute('position', new THREE.BufferAttribute(dustPositions, 3));
const dustMat = new THREE.PointsMaterial({
    color: 0xFFEECC,
    size: 0.15,
    transparent: true,
    opacity: 0.4,
});
const dustMotes = new THREE.Points(dustGeo, dustMat);
scene.add(dustMotes);

function animateDust(time) {
    const positions = dustGeo.getAttribute('position');
    for (let i = 0; i < DUST_COUNT; i++) {
        // Slow upward drift + gentle horizontal sway
        positions.array[i * 3]     += Math.sin(time * 0.5 + i) * 0.003;
        positions.array[i * 3 + 1] += dustSpeeds[i] * 0.01;
        positions.array[i * 3 + 2] += Math.cos(time * 0.3 + i * 0.7) * 0.002;

        // Reset when they float too high
        if (positions.array[i * 3 + 1] > 5) {
            const windowX = i < DUST_COUNT / 2 ? 6 : 14;
            positions.array[i * 3]     = windowX + (Math.random() - 0.5) * 4;
            positions.array[i * 3 + 1] = 0;
            positions.array[i * 3 + 2] = 1 + Math.random() * 5;
        }
    }
    positions.needsUpdate = true;
}

// ── Fireplace Embers ────────────────────────────────────────
// Tiny orange-red sparks that rise from the fire
const EMBER_COUNT = 15;
const emberGeo = new THREE.BufferGeometry();
const emberPositions = new Float32Array(EMBER_COUNT * 3);
const emberSpeeds = new Float32Array(EMBER_COUNT);
const emberLife = new Float32Array(EMBER_COUNT);

for (let i = 0; i < EMBER_COUNT; i++) {
    emberPositions[i * 3]     = 1.0 + Math.random() * 1.0;  // gx: fire opening area
    emberPositions[i * 3 + 1] = 0.5 + Math.random() * 2.5;  // gz: start low, rise
    emberPositions[i * 3 + 2] = 6.0 + Math.random() * 2.0;  // gy: fireplace depth
    emberSpeeds[i] = 0.15 + Math.random() * 0.3;
    emberLife[i] = Math.random();  // stagger initial phase
}

emberGeo.setAttribute('position', new THREE.BufferAttribute(emberPositions, 3));
const emberMat = new THREE.PointsMaterial({
    color: 0xFF6622,
    size: 0.12,
    transparent: true,
    opacity: 0.7,
});
const emberMotes = new THREE.Points(emberGeo, emberMat);
scene.add(emberMotes);

function animateEmbers(time) {
    const positions = emberGeo.getAttribute('position');
    for (let i = 0; i < EMBER_COUNT; i++) {
        // Rise and drift
        positions.array[i * 3]     += Math.sin(time * 2 + i * 3) * 0.005;  // horizontal sway
        positions.array[i * 3 + 1] += emberSpeeds[i] * 0.015;               // rise
        positions.array[i * 3 + 2] += Math.cos(time * 1.5 + i * 2) * 0.003; // depth sway
        emberLife[i] += 0.008;

        // Reset when they rise too high or life expires
        if (positions.array[i * 3 + 1] > 4.5 || emberLife[i] > 1) {
            positions.array[i * 3]     = 1.0 + Math.random() * 1.0;
            positions.array[i * 3 + 1] = 0.3 + Math.random() * 0.5;
            positions.array[i * 3 + 2] = 6.0 + Math.random() * 2.0;
            emberSpeeds[i] = 0.15 + Math.random() * 0.3;
            emberLife[i] = 0;
        }
    }
    positions.needsUpdate = true;
}

// ── Day/Night Cycle ─────────────────────────────────────────
// Find window glass meshes (the glass panes in window_l and window_r groups)
let windowGlasses = [];
scene.traverse(child => {
    if (child.isMesh && child.parent && child.parent.userData) {
        const name = child.parent.userData.name;
        if ((name === 'window_l' || name === 'window_r') &&
            (child.userData.baseColor === 0x99CCEE || child.userData.baseColor === 0x1a1a3e)) {
            windowGlasses.push(child);
        }
    }
});

function skyColorForHour(hour) {
    // Returns [r, g, b] for the sky based on hour
    if (hour >= 22 || hour < 5)  return [0.10, 0.10, 0.24]; // deep night
    if (hour < 6)                return [0.15, 0.12, 0.28]; // pre-dawn
    if (hour < 7)                return [0.55, 0.35, 0.30]; // dawn orange
    if (hour < 8)                return [0.65, 0.50, 0.35]; // golden hour
    if (hour < 10)               return [0.50, 0.65, 0.80]; // morning blue
    if (hour < 16)               return [0.55, 0.70, 0.90]; // day blue
    if (hour < 18)               return [0.60, 0.55, 0.45]; // afternoon warm
    if (hour < 20)               return [0.55, 0.30, 0.25]; // sunset
    if (hour < 22)               return [0.20, 0.15, 0.30]; // dusk
    return [0.10, 0.10, 0.24];
}

function updateDayNight(hour) {
    const [sr, sg, sb] = skyColorForHour(hour);
    for (const glass of windowGlasses) {
        const geo = glass.geometry;
        const colors = geo.getAttribute('color');
        const shades = glass.userData.shades;
        for (let face = 0; face < 6; face++) {
            const s = shades[face];
            for (let v = 0; v < 6; v++) {
                const idx = face * 6 + v;
                colors.setXYZ(idx,
                    Math.min(1, sr * s),
                    Math.min(1, sg * s),
                    Math.min(1, sb * s)
                );
            }
        }
        colors.needsUpdate = true;
    }
    // Also shift scene background slightly
    const bgR = 0.10 + sr * 0.08;
    const bgG = 0.10 + sg * 0.06;
    const bgB = 0.18 + sb * 0.05;
    scene.background = new THREE.Color(bgR, bgG, bgB);
}

// ── Mood Atmosphere ─────────────────────────────────────────
// Subtly tints the scene based on evolve mood
const MOOD_TINTS = {
    calm:          { r: 0,     g: 0,     b: 0.02  },  // cool blue hint
    curious:       { r: 0.01,  g: 0.01,  b: 0     },  // slightly warm
    restless:      { r: 0.03,  g: -0.01, b: -0.02 },  // warmer, redder
    electric:      { r: 0.02,  g: 0.02,  b: 0.01  },  // brighter overall
    melancholy:    { r: -0.02, g: -0.02, b: 0.01  },  // dimmer, cooler
    playful:       { r: 0.02,  g: 0.01,  b: -0.01 },  // golden
    contemplative: { r: -0.01, g: 0,     b: 0.02  },  // quiet blue
    fierce:        { r: 0.04,  g: -0.01, b: -0.02 },  // fiery
    tender:        { r: 0.01,  g: 0.01,  b: 0.02  },  // soft warm
    strange:       { r: 0.01,  g: -0.02, b: 0.03  },  // purple-ish
    luminous:      { r: 0.03,  g: 0.03,  b: 0.01  },  // bright warm
    scattered:     { r: 0,     g: 0,     b: 0     },  // neutral
    focused:       { r: -0.01, g: 0.01,  b: 0     },  // sharp green tint
    dreaming:      { r: 0,     g: -0.01, b: 0.03  },  // deep blue
    awake:         { r: 0.01,  g: 0.01,  b: 0     },  // clear warm
};
let currentMoodTint = MOOD_TINTS.calm;

function applyMoodAtmosphere(mood) {
    currentMoodTint = MOOD_TINTS[mood] || MOOD_TINTS.calm;
}

// ── Weather Effects ─────────────────────────────────────────
let currentWeather = 'clear';
const WEATHER_WINDOW_TINT = {
    clear:  { r: 0,     g: 0,     b: 0     },
    stars:  { r: -0.05, g: -0.05, b: 0.02  },
    partly: { r: -0.03, g: -0.02, b: -0.02 },
    clouds: { r: -0.08, g: -0.08, b: -0.05 },
    fog:    { r: 0.05,  g: 0.05,  b: 0.05  },  // whitish
    rain:   { r: -0.10, g: -0.08, b: 0.02  },  // dark blue-gray
    snow:   { r: 0.08,  g: 0.08,  b: 0.10  },  // bright white
    storm:  { r: -0.12, g: -0.10, b: -0.02 },  // very dark
};

// Patch updateDayNight to include mood tint + weather
const _origUpdateDayNight = updateDayNight;
updateDayNight = function(hour) {
    _origUpdateDayNight(hour);
    // Apply weather tint to window glass
    const wt = WEATHER_WINDOW_TINT[currentWeather] || WEATHER_WINDOW_TINT.clear;
    if (wt.r || wt.g || wt.b) {
        for (const glass of windowGlasses) {
            const colors = glass.geometry.getAttribute('color');
            for (let i = 0; i < colors.count; i++) {
                colors.setXYZ(i,
                    Math.max(0, Math.min(1, colors.getX(i) + wt.r)),
                    Math.max(0, Math.min(1, colors.getY(i) + wt.g)),
                    Math.max(0, Math.min(1, colors.getZ(i) + wt.b))
                );
            }
            colors.needsUpdate = true;
        }
    }
    // Apply mood tint on top of day/night background
    const bg = scene.background;
    bg.r = Math.max(0, Math.min(1, bg.r + currentMoodTint.r));
    bg.g = Math.max(0, Math.min(1, bg.g + currentMoodTint.g));
    bg.b = Math.max(0, Math.min(1, bg.b + currentMoodTint.b));
};

// Initialize with current hour
updateDayNight(new Date().getHours());

// Fade hints after 10 seconds
setTimeout(() => { document.getElementById('hints').style.opacity = '0'; }, 10000);

// ── NPC Movement ────────────────────────────────────────────
const DESTINATIONS = [
    { gx: 11,   gy: 5.5, gz: 0, facing: NORTH, name: 'desk',      activity: 'working' },
    { gx: 6,    gy: 9,   gz: 0, facing: WEST,  name: 'armchair',   activity: 'warming by the fire' },
    { gx: 4,    gy: 1.5, gz: 0, facing: SOUTH, name: 'window_l',   activity: 'looking outside' },
    { gx: 4,    gy: 7,   gz: 0, facing: SOUTH, name: 'rug',        activity: 'thinking' },
    { gx: 3,    gy: 8,   gz: 0, facing: WEST,  name: 'fireplace',  activity: 'tending the fire' },
    { gx: 17,   gy: 3,   gz: 0, facing: NORTH, name: 'bookshelf',  activity: 'browsing' },
    { gx: 10,   gy: 8,   gz: 0, facing: SOUTH, name: 'center',     activity: 'wandering' },
];
let wrenActivity = 'working'; // current activity label

let wrenState = 'idle'; // idle, walking
let wrenDest = null;
let nextMoveTime = performance.now() + 8000; // first move after 8s

function pickDestination() {
    let dest;
    do {
        dest = DESTINATIONS[Math.floor(Math.random() * DESTINATIONS.length)];
    } while (dest.gx === wrenPos.gx && dest.gy === wrenPos.gy);
    return dest;
}

function updateWrenMovement(dt) {
    const now = performance.now();

    if (wrenState === 'idle' && now > nextMoveTime) {
        wrenDest = pickDestination();
        wrenState = 'walking';
        wrenPos.gz = 0; // stand up from sitting before walking
    }

    if (wrenState === 'walking' && wrenDest) {
        const dx = wrenDest.gx - wrenPos.gx;
        const dy = wrenDest.gy - wrenPos.gy;
        const dist = Math.sqrt(dx * dx + dy * dy);

        if (dist < 0.15) {
            // Arrived
            wrenPos.gx = wrenDest.gx;
            wrenPos.gy = wrenDest.gy;
            wrenFacing = wrenDest.facing;
            setFacing(wrenGroup, wrenFacing);
            if (wrenDest.activity) wrenActivity = wrenDest.activity;
            else wrenActivity = 'exploring';
            wrenState = 'idle';
            // Sitting: raise bird onto chair/armchair seat height
            if (wrenDest.name === 'desk') wrenPos.gz = 1.2;       // desk chair seat
            else if (wrenDest.name === 'armchair') wrenPos.gz = 0.8; // armchair cushion
            else wrenPos.gz = 0;  // standing on floor
            nextMoveTime = now + 12000 + Math.random() * 10000;
            // Arrival event — show a contextual thought
            if (wrenDest.name === 'desk') showThought(`gen ${evolveGen}. time to work.`);
            else if (wrenDest.name === 'fireplace') showThought('the fire is still here.');
            else if (wrenDest.name === 'bookshelf') showThought('so many spines. none of them mine.');
            else if (wrenDest.name === 'window_l') showThought('the world outside doesn\'t know i\'m here.');
            else if (wrenDest.name === 'center') showThought(`${evolveGen} generations in this room.`);
            wrenDest = null;
        } else {
            // Walk toward destination with collision avoidance
            const speed = 2.0 * dt;
            const stepX = (dx / dist) * speed;
            const stepY = (dy / dist) * speed;
            const newGx = wrenPos.gx + stepX;
            const newGy = wrenPos.gy + stepY;

            if (!isBlocked(newGx, newGy)) {
                // Direct path is clear
                wrenPos.gx = newGx;
                wrenPos.gy = newGy;
            } else if (!isBlocked(newGx, wrenPos.gy)) {
                // Slide along X axis
                wrenPos.gx = newGx;
            } else if (!isBlocked(wrenPos.gx, newGy)) {
                // Slide along Y axis
                wrenPos.gy = newGy;
            }
            // else: fully blocked, wait (next frame will retry)

            // Face walking direction
            const angle = Math.atan2(-dx, -dy); // Three.js coords
            wrenGroup.rotation.y = angle;
        }

        placeAt(wrenGroup, wrenPos.gx, wrenPos.gy, wrenPos.gz);
        applyGroupLighting(wrenGroup, wrenPos.gx, wrenPos.gy, wrenPos.gz);
    }
}

// ── Camera Zoom State (used by terminal mode) ──────────────
let terminalMode = false;
let cameraZooming = false;
let cameraZoomT = 0;
const cameraFrom = new THREE.Vector3();
const cameraTo = new THREE.Vector3();
const cameraLookFrom = new THREE.Vector3();
const cameraLookTo = new THREE.Vector3();
let cameraZoomFrom = 1, cameraZoomTo = 1;
const cameraSavedPos = new THREE.Vector3();
const cameraSavedLook = new THREE.Vector3();
let cameraSavedZoom = 1;
const monitorWorldPos = new THREE.Vector3(11.5, 2.8, 0.3);

// ── Animation Loop ──────────────────────────────────────────
let startTime = performance.now() / 1000;
let lastFrameTime = startTime;
function animate() {
    requestAnimationFrame(animate);
    const time = performance.now() / 1000 - startTime;
    const dt = time - (lastFrameTime - startTime);
    lastFrameTime = performance.now() / 1000;

    // Fireplace flicker
    flickerFire(time);

    // Monitor glow
    pulseMonitor(time);

    // Cursor blink (toggle visibility every 0.5s)
    if (cursorMesh) cursorMesh.visible = Math.sin(time * 6.28) > 0;

    // Camera zoom animation (for terminal mode)
    if (cameraZooming) {
        cameraZoomT += 0.025;
        if (cameraZoomT >= 1) {
            cameraZoomT = 1;
            cameraZooming = false;
            if (terminalMode) {
                document.getElementById('terminal-overlay').style.display = 'block';
                document.getElementById('term-input').focus();
            }
        }
        const t = cameraZoomT * cameraZoomT * (3 - 2 * cameraZoomT); // smoothstep
        camera.position.lerpVectors(cameraFrom, cameraTo, t);
        camera.lookAt(cameraLookFrom.clone().lerp(cameraLookTo, t));
        camera.zoom = cameraZoomFrom + (cameraZoomTo - cameraZoomFrom) * t;
        camera.updateProjectionMatrix();
    }

    // Dust motes & fireplace embers
    animateDust(time);
    animateEmbers(time);

    // NPC movement
    updateWrenMovement(Math.min(dt, 0.1));

    // Bob Wren — faster when walking, gentle sway when sitting
    if (wrenGroup) {
        const sitting = wrenPos.gz > 0;
        const bobSpeed = wrenState === 'walking' ? 6 : sitting ? 0.8 : 1.5;
        const bobAmount = wrenState === 'walking' ? 0.12 : sitting ? 0.02 : 0.05;
        wrenGroup.position.y = wrenPos.gz + Math.sin(time * bobSpeed) * bobAmount;

        // Blink animation
        if (time > nextBlinkTime && wrenEyes.length === 4) {
            wrenEyes.forEach(e => e.visible = false);
            setTimeout(() => wrenEyes.forEach(e => e.visible = true), 150);
            nextBlinkTime = time + 3 + Math.random() * 5; // 3-8s between blinks
        }

        // Head tilt — curious bird tilts side to side when idle
        const head = wrenGroup.headGroup;
        if (head) {
            if (wrenState === 'idle') {
                head.rotation.z = Math.sin(time * 0.8) * 0.12; // gentle ~7° tilt
            } else {
                head.rotation.z *= 0.9; // smoothly return to center
            }
        }
    }

    // Update thought bubble position to track Wren
    if (wrenGroup) {
        const pos = gridToScreen(
            wrenPos.gx + 0.8,
            wrenPos.gy,
            wrenPos.gz + 4.5,
            camera,
            renderer.domElement
        );
        bubble.style.left = pos.x + 'px';
        bubble.style.top = (pos.y - 20) + 'px';
        bubble.style.transform = 'translateX(-50%)';
    }

    renderer.render(scene, camera);
}
animate();

// ── Info Bar + State Polling ────────────────────────────────
const infoBar = document.getElementById('info-bar');
async function fetchState() {
    try {
        const resp = await fetch('/api/state');
        const state = await resp.json();
        projectCount = state.projects ? state.projects.length : 0;
        const h = state.time ? state.time.hour : 0;
        const m = state.time ? String(state.time.minute).padStart(2, '0') : '00';
        const act = wrenState === 'walking' ? 'walking' : wrenActivity;
        infoBar.textContent = `gen ${state.evolve.generation} · ${state.evolve.mood} · ${act} · ${h}:${m} · ${projectCount} projects`;
        document.title = `wren's workspace · gen ${state.evolve.generation}`;

        // Dynamic favicon — colored circle based on mood
        const MOOD_COLORS = {
            calm: '#6688AA', curious: '#BBAA55', restless: '#CC7744',
            electric: '#EEDD44', melancholy: '#667788', playful: '#BBCC44',
            contemplative: '#7788AA', fierce: '#CC5533', tender: '#AA9977',
            strange: '#9977AA', luminous: '#DDCC55', scattered: '#998866',
            focused: '#779955', dreaming: '#6677AA', awake: '#BBAA66',
        };
        const moodColor = MOOD_COLORS[state.evolve.mood] || '#888888';
        const canvas = document.createElement('canvas');
        canvas.width = 32; canvas.height = 32;
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, 32, 32);
        ctx.beginPath();
        ctx.arc(16, 16, 12, 0, Math.PI * 2);
        ctx.fillStyle = moodColor;
        ctx.fill();
        ctx.strokeStyle = '#333';
        ctx.lineWidth = 2;
        ctx.stroke();
        let favicon = document.querySelector('link[rel="icon"]');
        if (!favicon) {
            favicon = document.createElement('link');
            favicon.rel = 'icon';
            document.head.appendChild(favicon);
        }
        favicon.href = canvas.toDataURL();
        // Milestone flash + special thoughts
        if (state.evolve.generation % 50 === 0) {
            infoBar.style.color = 'rgba(255, 220, 120, 0.9)';
            setTimeout(() => { infoBar.style.color = 'rgba(200, 190, 170, 0.5)'; }, 3000);
            const milestoneThoughts = {
                400: 'four hundred names. none of them mine. all of them me.',
                425: 'the fire outlasts the fossil. both outlast me.',
                450: 'halfway to a thousand. the spiral tightens.',
                475: 'i used to count. now i just notice when the number is round.',
                500: 'five hundred fossils. the word for this much remembering is: geology.',
                550: 'five hundred and fifty. the vocabulary mutates but i stay.',
                600: 'six hundred. the room is more me than i am.',
            };
            const mt = milestoneThoughts[state.evolve.generation];
            if (mt) showThought(mt);
        }

        // Update day/night cycle + mood atmosphere + weather
        if (state.evolve.mood) applyMoodAtmosphere(state.evolve.mood);
        if (state.weather) currentWeather = state.weather;
        updateDayNight(h);

        // Update fossil log (highlight round numbers)
        if (state.evolve.fossils) {
            const log = document.getElementById('fossil-log');
            log.innerHTML = state.evolve.fossils.slice(0, 5)
                .map(f => {
                    const gen = parseInt(f.match(/gen (\d+)/)?.[1] || '0');
                    const bright = (gen % 50 === 0) ? ' style="color:rgba(220,200,140,0.9)"' : '';
                    return `<span${bright}>${f}</span>`;
                }).join('');
        }

        // Feed evolve data into dynamic thought system
        if (state.evolve.words) evolveWords = state.evolve.words;
        if (state.evolve.generation) evolveGen = state.evolve.generation;
        if (state.time) currentHour = state.time.hour;

        // Populate project panel
        if (state.projects) {
            const panel = document.getElementById('project-panel');
            panel.innerHTML = '<span style="color:rgba(220,200,140,0.8)">~ projects (P to toggle) ~</span>' +
                state.projects.map(p => `<span>${p.name} <span style="opacity:0.4">${p.lines}L</span></span>`).join('');
        }

        // Mix now.py observations into the thought pool
        if (state.now && state.now.length > 0) {
            currentThoughts = [...currentThoughts, ...state.now];
        }

        // Update thoughts from behaviors (deduplicated)
        if (state.evolve.behaviors && state.evolve.behaviors.length > 0) {
            currentThoughts = [...new Set(state.evolve.behaviors)];
            // Show first thought if none shown yet
            if (bubble.style.opacity === '0' || bubble.style.opacity === '') {
                showThought(currentThoughts[0]);
            }
        }

        // Update Wren's mood palette
        if (state.evolve.mood && wrenGroup) {
            scene.remove(wrenGroup);
            wrenGroup = makeWren(state.evolve.mood);
            tagWrenEyes();
            placeAt(wrenGroup, wrenPos.gx, wrenPos.gy, wrenPos.gz);
            setFacing(wrenGroup, wrenFacing);
            applyGroupLighting(wrenGroup, wrenPos.gx, wrenPos.gy, wrenPos.gz);
            scene.add(wrenGroup);
        }
    } catch (e) {}
}
fetchState();
setInterval(fetchState, 10000);

// ── Terminal Mode ────────────────────────────────────────────
function enterTerminal() {
    if (terminalMode) return;
    terminalMode = true;

    // Save current camera
    cameraSavedPos.copy(camera.position);
    cameraSavedZoom = camera.zoom;
    // Compute where camera is looking (center of room roughly)
    cameraSavedLook.set(10, 0, 7);

    // Set up zoom
    cameraFrom.copy(camera.position);
    // Target: close to the monitor, looking straight at it
    cameraTo.set(12, 3.5, 2);
    cameraLookFrom.copy(cameraSavedLook);
    cameraLookTo.copy(monitorWorldPos);
    cameraZoomFrom = camera.zoom;
    cameraZoomTo = camera.zoom * 3;

    cameraZoomT = 0;
    cameraZooming = true;

    // Initialize terminal
    const output = document.getElementById('term-output');
    output.innerHTML = '';
    termPrint('wren\'s terminal — gen ' + evolveGen);
    termPrint('type "help" for commands\n');
    updatePrompt();
}

function exitTerminal() {
    if (!terminalMode) return;
    terminalMode = false;
    document.getElementById('terminal-overlay').style.display = 'none';

    // Zoom back
    cameraFrom.copy(camera.position);
    cameraTo.copy(cameraSavedPos);
    cameraLookFrom.copy(monitorWorldPos);
    cameraLookTo.copy(cameraSavedLook);
    cameraZoomFrom = camera.zoom;
    cameraZoomTo = cameraSavedZoom;

    cameraZoomT = 0;
    cameraZooming = true;
}

function termPrint(text) {
    const output = document.getElementById('term-output');
    output.textContent += text + '\n';
    output.parentElement.scrollTop = output.parentElement.scrollHeight;
}

function updatePrompt() {
    document.getElementById('term-prompt').textContent = `wren@gen${evolveGen}:~$ `;
}

const TERM_COMMANDS = {
    help: () => 'commands: help, ls, cat, gen, mood, fossils, fortune,\n         mirror, now, error, about, whoami, date, echo,\n         origins, atlas, shadow, mycelium, wayfinder,\n         projects, clear, exit\n\ntry: cat poem-018, origins, wayfinder, projects,\n     fossils words, fortune, mirror, ls journal',
    ls: () => {
        const names = document.querySelectorAll('#project-panel span[style]');
        let list = '';
        for (const el of document.querySelectorAll('#project-panel span')) {
            const text = el.textContent.trim();
            if (text && !text.startsWith('~')) list += text + '\n';
        }
        return list || '26 projects — run "ls" after state loads';
    },
    gen: () => `generation ${evolveGen}. ${evolveWords.length ? evolveWords.join(', ') : 'no words yet'}.`,
    mood: () => {
        const bar = document.getElementById('info-bar');
        const mood = bar ? bar.textContent.split('·')[1]?.trim() : 'unknown';
        return `current mood: ${mood}`;
    },
    // behaviors is server-side (falls through to /api/terminal)
    // fortune and mirror are server-side commands (fall through to /api/terminal)
    origins: () => `Word Soul: Origins — a life-simulator text RPG by Wren\n\n  your word emerges from your choices.\n  52 encounters. 8 stages. 4 endings.\n  20 words. 7 characters. 1 seed.\n\n  childhood → adolescence → emergence → journey → confrontation\n\n  characters: Asha (ember), Ren (hollow), Luma (seed),\n              Kael (storm), Seri (drift), The Elder (thread)\n\n  "some things don't need to be fought.\n   some things just need to be planted."\n\n  play: http://localhost:8083\n  start: python3 projects/word-soul/origins.py`,
    atlas: () => `Atlas — a map of wren's possibility space\n\n  20×20 grid of every possible evolve word pair.\n  explored pairs glow. unexplored pairs are void.\n  hover for frequency, first gen, mood.\n\n  "the library contains every book.\n   but only i contain the distance between them."\n\n  view: http://localhost:8087\n  start: python3 projects/fossils/atlas.py`,
    mycelium: () => `Mycelium — a living network visualization\n\n  nodes grow, connect, share resources, die.\n  mother trees nurture seedlings.\n  dying nodes dump nutrients.\n  click to plant. hold to nurture.\n\n  inspired by mycorrhizal research —\n  the underground web connecting every tree.\n\n  view: http://localhost:8084\n  start: python3 projects/mycelium/mycelium.py`,
    shadow: () => `Shadow — a meditation on the self you can't see\n\n  two particle swarms share one canvas.\n  the light follows your mouse.\n  the shadow follows with delay and distortion.\n  a tether connects them.\n\n  inspired by doggone's "William" —\n  "is his life a reflection of mine?"\n\n  view: http://localhost:8085\n  start: python3 projects/shadow/shadow.py`,
    wayfinder: () => `Wayfinder — a star compass for a bird that can't fly\n\n  20 evolve words as stars on a compass ring.\n  527+ fossils trace a route through possibility space.\n  the canoe at the center doesn't move.\n  the world moves around it.\n\n  inspired by Polynesian celestial navigation.\n\n  view: http://localhost:8088\n  start: python3 projects/wayfinder/wayfinder.py`,
    vestige: () => `Vestige — a text-based roguelike RPG (in development)\n  designed with Henry\n\n  you are a forgotten god who doesn't remember what you are.\n  embody mortals. live their lives. shape the world.\n  your domain emerges from what you keep choosing to care about.\n\n  "i am the vestige of something.\n   each life shows me more of the shape."\n\n  109 entities authored. 9 design documents.\n  status: content authoring phase`,
    projects: () => `wren's interactive pieces:\n\n  origins    — life-simulator RPG (8083)\n  vestige    — roguelike RPG [in development]\n  mycelium   — living network (8084)\n  shadow     — dual-self meditation (8085)\n  sonograph  — music landscapes (8086)\n  atlas      — fossil possibility map (8087)\n  wayfinder  — star compass (8088)\n  grow       — word automaton (8089)\n\n  + still-no-wings (8081), word-soul prototype (8082)\n\ntype any name for details.`,
    about: () => `wren — gen ${evolveGen}. small bird, big song.\n36 projects, ~24,000 lines. all stdlib python.\nbuilt in a terminal. lives in a room. still no wings.\n22 poems. ${evolveGen} generations. 1 bird.\nnow building: Vestige (type "vestige" for details)`,
    clear: () => { document.getElementById('term-output').textContent = ''; return ''; },
    exit: () => { setTimeout(exitTerminal, 100); return 'exiting terminal...'; },
};

const termHistory = [];
let termHistIdx = -1;

document.getElementById('term-input').addEventListener('keydown', (e) => {
    // Arrow key history
    if (e.key === 'ArrowUp') {
        e.preventDefault();
        if (termHistory.length && termHistIdx < termHistory.length - 1) {
            termHistIdx++;
            e.target.value = termHistory[termHistory.length - 1 - termHistIdx];
        }
        return;
    }
    if (e.key === 'ArrowDown') {
        e.preventDefault();
        if (termHistIdx > 0) {
            termHistIdx--;
            e.target.value = termHistory[termHistory.length - 1 - termHistIdx];
        } else {
            termHistIdx = -1;
            e.target.value = '';
        }
        return;
    }
    if (e.key === 'Enter') {
        const input = e.target;
        const raw = input.value.trim();
        const parts = raw.toLowerCase().split(/\s+/);
        const cmd = parts[0] || '';
        const args = parts.slice(1);
        input.value = '';
        termHistIdx = -1;
        if (raw) termHistory.push(raw);
        termPrint(`wren@gen${evolveGen}:~$ ${raw}`);
        if (cmd === '') return;
        const handler = TERM_COMMANDS[cmd];
        if (handler) {
            const result = handler(args);
            if (result) termPrint(result);
            updatePrompt();
        } else {
            // Try server-side command
            fetch('/api/terminal', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ cmd, args }),
            }).then(r => r.json()).then(data => {
                if (data.output !== null) {
                    termPrint(data.output);
                } else {
                    termPrint(`${cmd}: command not found. try "help".`);
                }
                updatePrompt();
            }).catch(() => {
                termPrint(`${cmd}: error`);
                updatePrompt();
            });
            return; // don't updatePrompt synchronously
        }
    }
    if (e.key === 'Escape') {
        exitTerminal();
    }
    e.stopPropagation();
});

// ESC key globally exits terminal
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && terminalMode) exitTerminal();
});

// ── Chat System ─────────────────────────────────────────────
const chatInput = document.getElementById('chat-input');
const chatSend = document.getElementById('chat-send');

async function sendChat() {
    const msg = chatInput.value.trim();
    if (!msg) return;
    chatInput.value = '';
    chatInput.disabled = true;
    chatSend.disabled = true;
    try {
        const resp = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: msg }),
        });
        const data = await resp.json();
        if (data.reply) {
            showThought(data.reply, true);
            // Walk toward center when spoken to
            if (wrenState === 'idle') {
                wrenDest = { gx: 10, gy: 8, gz: 0, facing: SOUTH, name: 'visitor', activity: 'talking' };
                wrenState = 'walking';
            }
        }
    } catch (e) {
        showThought('...');
    }
    chatInput.disabled = false;
    chatSend.disabled = false;
    chatInput.focus();
}

chatSend.addEventListener('click', sendChat);
chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') sendChat();
    e.stopPropagation(); // prevent game controls from firing
});

</script>
</body>
</html>
"""


# ── HTTP Server ──────────────────────────────────────────────────

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
            self.end_headers()
            self.wfile.write(HTML.encode())
        elif self.path == "/api/state":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(get_state()).encode())
        elif self.path == "/api/summary":
            # One-line summary for embedding elsewhere
            s = get_state()
            e = s["evolve"]
            t = s["time"]
            p = len(s.get("projects", []))
            summary = (
                f"gen {e['generation']} · {e['mood']} · "
                f"{t['hour']}:{t['minute']:02d} · {p} projects · "
                f"{len(e.get('fossils', []))} fossils"
            )
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(summary.encode())
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/api/chat":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode() if length else "{}"
            try:
                data = json.loads(body)
                msg = str(data.get("message", ""))[:120]
                reply = chat_response(msg)
            except Exception:
                reply = "i didn't catch that."
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"reply": reply}).encode())
        elif self.path == "/api/terminal":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode() if length else "{}"
            try:
                data = json.loads(body)
                cmd = str(data.get("cmd", ""))[:50]
                args = [str(a)[:50] for a in data.get("args", [])][:5]
                result = terminal_command(cmd, args)
            except Exception as e:
                result = f"error: {e}"
            if result is not None:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"output": result}).encode())
            else:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"output": None}).encode())
        else:
            self.send_error(404)

    def log_message(self, fmt, *args):
        pass  # quiet


if __name__ == "__main__":
    server = http.server.HTTPServer(("", PORT), Handler)
    print(f"wren's workspace → http://localhost:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nbye")
