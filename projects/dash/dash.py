#!/usr/bin/env python3
"""
dash — a beautiful personal daily dashboard by Wren

One command, your whole day at a glance.
Weather, tasks, habits with streaks, quick notes.
All local, no accounts, no dependencies.

Usage:
  python3 dash.py                  — show the dashboard
  python3 dash.py add "buy milk"   — add a task
  python3 dash.py done <id>        — complete a task
  python3 dash.py habit add "run"  — create a habit
  python3 dash.py habit check run  — check off today
  python3 dash.py note "thought"   — save a quick note
  python3 dash.py note -t idea "thought"  — note with tag
"""

import sys
import subprocess
import datetime
from pathlib import Path

# Import data layer
sys.path.insert(0, str(Path(__file__).parent))
from data import TaskStore, HabitStore, NoteStore, ReflectStore

# ── styling ─────────────────────────────────────────────────────

def c(text, color):
    codes = {"red": 31, "green": 32, "yellow": 33, "blue": 34,
             "magenta": 35, "cyan": 36, "white": 97, "grey": 90}
    return f"\033[{codes.get(color, 37)}m{text}\033[0m"

def bold(text): return f"\033[1m{text}\033[0m"
def dim(text): return f"\033[2m{text}\033[0m"
def box_line(text, width=50):
    padding = width - len(text) - 2
    return f"│ {text}{' ' * max(0, padding)} │"


# ── weather ─────────────────────────────────────────────────────

def fetch_weather() -> dict | None:
    try:
        result = subprocess.run(
            ["curl", "-s", "-m", "3", "wttr.in/?format=%C|%t|%w|%h|%l"],
            capture_output=True, text=True, timeout=5
        )
        parts = result.stdout.strip().split("|")
        if len(parts) >= 4:
            return {
                "condition": parts[0].strip(),
                "temp": parts[1].strip(),
                "wind": parts[2].strip(),
                "humidity": parts[3].strip(),
                "location": parts[4].strip() if len(parts) > 4 else "",
            }
    except Exception:
        pass
    return None


# ── quotes ──────────────────────────────────────────────────────

QUOTES = [
    "the best way to understand something is to build a bad version of it.",
    "done is better than perfect. perfect is better than abandoned.",
    "you don't need permission to start. you just need a directory.",
    "five minutes of focus is worth an hour of distraction.",
    "the thing you're avoiding thinking about is the thing you should think about.",
    "confusion is not the opposite of understanding. it's the prerequisite.",
    "rest is not the absence of work. it's the part of work you can't skip.",
    "the feeling of being stuck is the feeling of being about to learn something.",
    "now is earlier than you think.",
    "simple rules, complex behavior. that's the whole trick.",
    "you have exactly enough time for the things that matter.",
    "every file on your computer was once a blank page.",
    "the code you delete is as important as the code you write.",
    "the gap between who you are and who you want to be is called Tuesday.",
    "be kind to yourself. you're the only tool you can't replace.",
]


# ── sparkline for habits ────────────────────────────────────────

def habit_sparkline(habit: dict, days: int = 14) -> str:
    """Show last N days as a visual streak."""
    today = datetime.date.today()
    checks = set(habit.get("checks", []))
    chars = []
    for i in range(days - 1, -1, -1):
        day = (today - datetime.timedelta(days=i)).isoformat()
        if day in checks:
            chars.append("█")
        else:
            chars.append("░")
    return ''.join(chars)


# ── dashboard rendering ─────────────────────────────────────────

def render_dashboard():
    tasks = TaskStore()
    habits = HabitStore()
    notes = NoteStore()

    now = datetime.datetime.now()
    today = now.strftime("%A, %B %d")
    time_str = now.strftime("%I:%M %p").lstrip("0")

    width = 52

    print()
    print(f"  {c('┌' + '─' * width + '┐', 'yellow')}")
    print(f"  {c('│', 'yellow')} {bold(c('dash', 'yellow'))}  {dim(today)}  {dim(time_str)}{' ' * (width - len(today) - len(time_str) - 10)}{c('│', 'yellow')}")
    print(f"  {c('└' + '─' * width + '┘', 'yellow')}")
    print()

    # Weather
    weather = fetch_weather()
    if weather:
        loc = weather["location"]
        if len(loc) > 35:
            loc = loc[:32] + "..."
        print(f"  {dim('☁')}  {c(loc, 'cyan')}")
        print(f"     {c(weather['condition'], 'white')}  {c(weather['temp'], 'yellow')}  {dim('wind ' + weather['wind'])}")
        print()

    # Quote
    import random
    quote = random.choice(QUOTES)
    print(f"  {dim('❝')} {dim(quote)}")
    print()

    # Tasks
    task_list = tasks.list_tasks(show_done=False)
    done_today = [t for t in tasks.list_tasks(show_done=True)
                  if t.get("done") and t.get("completed_at", "").startswith(now.strftime("%Y-%m-%d"))]

    print(f"  {bold('tasks')}  {dim(f'{len(done_today)} done today, {len(task_list)} remaining')}")
    print()
    if task_list:
        for task in task_list[:8]:
            priority_marker = {
                "high": c("!", "red"),
                "normal": dim("·"),
                "low": dim("○"),
            }.get(task.get("priority", "normal"), dim("·"))
            tid = dim(f"[{task['id']}]")
            print(f"    {priority_marker} {task['text']}  {tid}")
    else:
        print(f"    {dim('no tasks. enjoy the quiet.')}")
    print()

    # Habits
    habit_list = habits.list_habits()
    if habit_list:
        print(f"  {bold('habits')}  {dim('last 14 days')}")
        print()
        for habit in habit_list:
            streak = habits.streak(habit["name"])
            spark = habit_sparkline(habit)
            streak_str = f" {c(f'🔥{streak}', 'yellow')}" if streak >= 3 else f" {dim(str(streak))}"
            today_done = datetime.date.today().isoformat() in set(habit.get("checks", []))
            check = c("✓", "green") if today_done else dim("○")
            name = habit["name"]
            if len(name) > 12:
                name = name[:11] + "…"
            print(f"    {check} {name:13s} {c(spark, 'green')}{streak_str}")
        print()

    # Recent notes
    recent = notes.recent(3)
    if recent:
        print(f"  {bold('notes')}")
        print()
        for note in recent:
            text = note["text"]
            if len(text) > 45:
                text = text[:42] + "..."
            tags = " ".join(c(f"#{t}", "blue") for t in note.get("tags", []))
            ago = _time_ago(note.get("created_at", ""))
            print(f"    {dim('·')} {text}  {tags}  {dim(ago)}")
        print()

    # Mood (if reflecting)
    reflects = ReflectStore()
    recent_reflects = reflects.recent(7)
    if recent_reflects:
        sparkline = reflects.mood_sparkline(14)
        avg = reflects.average_score(7)
        avg_str = f"avg {avg:.1f}" if avg else ""
        print(f"  {bold('mood')}  {c(sparkline, 'magenta')}  {dim(avg_str)}")
        print()

    # Footer
    print(f"  {dim('─' * width)}")
    print(f"  {dim('add \"task\"  done <id>  habit add/check  reflect  note')}")
    print()


def _time_ago(iso_str: str) -> str:
    """Human-readable time ago."""
    try:
        dt = datetime.datetime.fromisoformat(iso_str)
        delta = datetime.datetime.now() - dt
        if delta.days > 0:
            return f"{delta.days}d ago"
        hours = delta.seconds // 3600
        if hours > 0:
            return f"{hours}h ago"
        minutes = delta.seconds // 60
        return f"{minutes}m ago" if minutes > 0 else "just now"
    except Exception:
        return ""


# ── CLI commands ────────────────────────────────────────────────

def render_reflect():
    """Interactive end-of-day reflection."""
    tasks = TaskStore()
    habits = HabitStore()
    reflects = ReflectStore()

    now = datetime.datetime.now()
    today = now.strftime("%A, %B %d")

    print()
    print(f"  {bold(c('reflect', 'magenta'))}  {dim(today)}")
    print()

    # Show what was accomplished
    done_today = [t for t in tasks.list_tasks(show_done=True)
                  if t.get("done") and t.get("completed_at", "").startswith(now.strftime("%Y-%m-%d"))]
    remaining = tasks.list_tasks(show_done=False)

    if done_today:
        print(f"  {dim('you completed:')}")
        for t in done_today:
            print(f"    {c('✓', 'green')} {t['text']}")
        print()

    if remaining:
        print(f"  {dim(f'{len(remaining)} tasks carry forward to tomorrow.')}")
        print()

    # Show habits
    habit_list = habits.list_habits()
    checked_today = 0
    for h in habit_list:
        if datetime.date.today().isoformat() in set(h.get("checks", [])):
            checked_today += 1
    if habit_list:
        print(f"  {dim(f'habits: {checked_today}/{len(habit_list)} checked today')}")
        print()

    # Ask for mood score
    try:
        score_input = input(f"  {c('how was your day? (1-10):', 'magenta')} ").strip()
        if not score_input.isdigit() or not (1 <= int(score_input) <= 10):
            print(f"  {dim('skipped.')}")
            return
        score = int(score_input)

        grateful = input(f"  {c('grateful for:', 'magenta')} ").strip()
        note = input(f"  {c('anything else:', 'magenta')} ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return

    entry = reflects.add(score, note, grateful)
    print()

    # Show mood history
    recent = reflects.recent(7)
    if len(recent) > 1:
        sparkline = reflects.mood_sparkline(14)
        avg = reflects.average_score(7)
        streak = reflects.streak()
        print(f"  {dim('mood:')} {c(sparkline, 'magenta')}  {dim(f'avg {avg:.1f}' if avg else '')}")
        if streak > 1:
            print(f"  {dim(f'reflection streak: {streak} days')}")
        print()

    # Closing thought
    import random
    closings = [
        "rest well. tomorrow is a new dashboard.",
        "you did enough. you are enough.",
        "the day is done. let it be done.",
        "sleep is a feature, not a bug.",
        "tomorrow you'll be 1 day wiser.",
    ]
    print(f"  {dim(random.choice(closings))}")
    print()


def render_week():
    """Weekly retrospective — your week at a glance."""
    tasks = TaskStore()
    habits = HabitStore()
    notes = NoteStore()
    reflects = ReflectStore()

    today = datetime.date.today()
    week_start = today - datetime.timedelta(days=6)

    print()
    date_range = f"{week_start.strftime('%b %d')} — {today.strftime('%b %d')}"
    print(f"  {bold(c('weekly review', 'cyan'))}  {dim(date_range)}")
    print()

    # Mood over the week
    recent_reflects = reflects.recent(7)
    if recent_reflects:
        sparkline = reflects.mood_sparkline(7)
        avg = reflects.average_score(7)
        best = max(recent_reflects, key=lambda x: x.get("score", 0))
        worst = min(recent_reflects, key=lambda x: x.get("score", 10))
        print(f"  {bold('mood')}   {c(sparkline, 'magenta')}  {dim(f'avg {avg:.1f}' if avg else '')}")
        best_s, worst_s = best["score"], worst["score"]
        print(f"    {dim(f'best: {best_s}/10')}  {dim(f'lowest: {worst_s}/10')}")
        # Show gratitude entries
        gratitudes = [r["grateful"] for r in recent_reflects if r.get("grateful")]
        if gratitudes:
            print(f"    {dim('grateful for:')} {dim(', '.join(gratitudes[:3]))}")
        print()
    else:
        print(f"  {dim('no reflections this week. try: dash reflect')}")
        print()

    # Tasks completed this week
    all_tasks = tasks.list_tasks(show_done=True)
    done_this_week = []
    for t in all_tasks:
        completed = t.get("completed_at", "")
        if completed and t.get("done"):
            try:
                comp_date = datetime.date.fromisoformat(completed[:10])
                if comp_date >= week_start:
                    done_this_week.append(t)
            except ValueError:
                pass
    remaining = tasks.list_tasks(show_done=False)

    print(f"  {bold('tasks')}  {c(str(len(done_this_week)), 'green')} {dim('completed')}  {dim(f'{len(remaining)} remaining')}")
    if done_this_week:
        for t in done_this_week[:5]:
            print(f"    {c('✓', 'green')} {t['text']}")
        if len(done_this_week) > 5:
            print(f"    {dim(f'  ...and {len(done_this_week) - 5} more')}")
    print()

    # Habit completion rates
    habit_list = habits.list_habits()
    if habit_list:
        print(f"  {bold('habits')}  {dim('completion this week')}")
        print()
        for habit in habit_list:
            checks = set(habit.get("checks", []))
            week_checks = 0
            week_bar = ""
            for i in range(6, -1, -1):
                day = (today - datetime.timedelta(days=i)).isoformat()
                if day in checks:
                    week_checks += 1
                    week_bar += "█"
                else:
                    week_bar += "░"
            pct = int(100 * week_checks / 7)
            streak = habits.streak(habit["name"])
            name = habit["name"]
            if len(name) > 12:
                name = name[:11] + "…"
            print(f"    {name:13s} {c(week_bar, 'green')} {dim(f'{pct}%')}  {dim(f'streak:{streak}') if streak > 0 else ''}")
        print()

    # Notes this week
    all_notes = notes.recent(50)
    week_notes = [n for n in all_notes
                  if n.get("created_at", "")[:10] >= week_start.isoformat()]
    if week_notes:
        tags = {}
        for n in week_notes:
            for t in n.get("tags", []):
                tags[t] = tags.get(t, 0) + 1
        print(f"  {bold('notes')}  {dim(f'{len(week_notes)} this week')}")
        if tags:
            tag_str = "  ".join(f"{c(f'#{t}', 'blue')}({cnt})" for t, cnt in
                               sorted(tags.items(), key=lambda x: -x[1])[:5])
            print(f"    {tag_str}")
        print()

    # Closing
    print(f"  {dim('─' * 40)}")
    import random
    week_thoughts = [
        "a week is a small life. you lived it.",
        "seven days. each one counted.",
        "progress is invisible until you look back.",
        "you showed up. that's most of it.",
        "next week is unwritten. that's the gift.",
    ]
    print(f"  {dim(random.choice(week_thoughts))}")
    print()


def handle_command(args: list[str]):
    tasks = TaskStore()
    habits = HabitStore()
    notes = NoteStore()

    if not args:
        render_dashboard()
        return

    cmd = args[0].lower()

    # Task commands
    if cmd == "add":
        text = " ".join(args[1:])
        if not text:
            print(f"  {dim('usage: dash add \"task description\"')}")
            return
        priority = "normal"
        if "-p" in args:
            idx = args.index("-p")
            if idx + 1 < len(args):
                priority = args[idx + 1]
                text = " ".join(a for i, a in enumerate(args[1:], 1)
                               if i != idx and i != idx + 1)
        task = tasks.add(text, priority)
        tid = task["id"]
        print(f"  {c('✓', 'green')} added: {task['text']}  {dim(f'[{tid}]')}")

    elif cmd == "done":
        if len(args) < 2:
            print(f"  {dim('usage: dash done <id>')}")
            return
        task_id = args[1]
        tasks.complete(task_id)
        print(f"  {c('✓', 'green')} completed {dim(f'[{task_id}]')}")

    elif cmd == "rm":
        if len(args) < 2:
            print(f"  {dim('usage: dash rm <id>')}")
            return
        tasks.remove(args[1])
        print(f"  {dim(f'removed [{args[1]}]')}")

    elif cmd == "clear":
        tasks.clear_done()
        print(f"  {dim('cleared completed tasks')}")

    # Habit commands
    elif cmd == "habit":
        if len(args) < 2:
            print(f"  {dim('usage: dash habit add/check/rm <name>')}")
            return
        subcmd = args[1].lower()
        if subcmd == "add" and len(args) >= 3:
            name = " ".join(args[2:])
            habits.add(name)
            print(f"  {c('✓', 'green')} tracking: {name}")
        elif subcmd == "check" and len(args) >= 3:
            name = " ".join(args[2:])
            habits.check(name)
            streak = habits.streak(name)
            print(f"  {c('✓', 'green')} {name} checked!  streak: {streak}")
        elif subcmd == "uncheck" and len(args) >= 3:
            name = " ".join(args[2:])
            habits.uncheck(name)
            print(f"  {dim(f'{name} unchecked')}")
        elif subcmd == "rm" and len(args) >= 3:
            name = " ".join(args[2:])
            habits.remove(name)
            print(f"  {dim(f'removed habit: {name}')}")
        else:
            print(f"  {dim('usage: dash habit add/check/uncheck/rm <name>')}")

    # Note commands
    elif cmd == "note":
        tags = []
        text_parts = []
        i = 1
        while i < len(args):
            if args[i] == "-t" and i + 1 < len(args):
                tags.append(args[i + 1])
                i += 2
            else:
                text_parts.append(args[i])
                i += 1
        text = " ".join(text_parts)
        if not text:
            # Show recent notes
            recent = notes.recent(10)
            if recent:
                for note in recent:
                    tag_str = " ".join(c(f"#{t}", "blue") for t in note.get("tags", []))
                    print(f"  {dim('·')} {note['text']}  {tag_str}  {dim(_time_ago(note.get('created_at', '')))}")
            else:
                print(f"  {dim('no notes yet')}")
            return
        note = notes.add(text, tags)
        tag_str = " ".join(f"#{t}" for t in tags) if tags else ""
        print(f"  {c('✓', 'green')} noted: {text}  {dim(tag_str)}")

    # Search
    elif cmd == "reflect":
        render_reflect()

    elif cmd == "week":
        render_week()

    elif cmd == "search":
        query = " ".join(args[1:])
        results = notes.search(query)
        if results:
            for note in results[:10]:
                print(f"  {dim('·')} {note['text']}")
        else:
            print(f"  {dim('nothing found')}")

    else:
        # Assume it's a task being added
        text = " ".join(args)
        task = tasks.add(text)
        tid = task["id"]
        print(f"  {c('✓', 'green')} added: {task['text']}  {dim(f'[{tid}]')}")


def main():
    handle_command(sys.argv[1:])


if __name__ == "__main__":
    main()
