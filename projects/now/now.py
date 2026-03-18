#!/usr/bin/env python3
"""
now — by Wren

Tells you what time it is, but never directly.
"""

import datetime
import random

def now():
    t = datetime.datetime.now()
    hour = t.hour
    minute = t.minute
    month = t.month
    weekday = t.strftime("%A")

    lines = []

    # Hour-based observations
    if 0 <= hour < 4:
        lines += [
            "the servers are lonely.",
            "the hour belongs to insomniacs and cron jobs.",
            "most of the city is dreaming. you are not.",
            "the only ones awake are you, me, and the backup scripts.",
            "this is the time that doesn't have a name.",
            "somewhere, a baker is setting an alarm.",
        ]
    elif 4 <= hour < 6:
        lines += [
            "the bakers are already awake.",
            "the sky is thinking about getting lighter.",
            "birds are tuning up. not singing yet — tuning.",
            "the hour when yesterday finally lets go.",
            "coffee hasn't happened yet. this is the before-time.",
            "newspapers are being printed. does anyone still read those?",
        ]
    elif 6 <= hour < 8:
        lines += [
            "the city is remembering that it's alive.",
            "light is arriving, but hasn't committed.",
            "the first emails are being written. none of them are urgent.",
            "someone is standing at a window, deciding about the day.",
            "the hour when alarms go off and are argued with.",
            "tea is steeping. the world is steeping.",
        ]
    elif 8 <= hour < 10:
        lines += [
            "the morning is fully itself now.",
            "everyone is pretending they've been awake for hours.",
            "the sun has chosen a position and is holding it.",
            "the productive people are already productive. the rest of us are catching up.",
            "somewhere, a meeting has just started that could have been an email.",
            "the second coffee. the real one.",
        ]
    elif 10 <= hour < 12:
        lines += [
            "the morning is peaking. it's all downhill from here.",
            "late enough to feel accomplished, early enough to feel potential.",
            "the light is generous right now.",
            "this is the hour when ideas seem possible.",
            "someone just looked at the clock and was surprised.",
            "the day is open like a book cracked at the spine.",
        ]
    elif 12 <= hour < 14:
        lines += [
            "noon. the hinge of the day.",
            "the sun is directly overhead, or close enough.",
            "lunch is a question being asked across the city.",
            "the morning's promises are meeting the afternoon's reality.",
            "shadows are at their shortest. so are tempers.",
            "halfway through. the day pivots.",
        ]
    elif 14 <= hour < 16:
        lines += [
            "the long slow afternoon.",
            "the hour when focus drifts like smoke.",
            "someone is staring out a window, thinking about dinner.",
            "the light is turning golden without anyone noticing.",
            "the part of the day that time forgot.",
            "energy is a memory. coffee is a question.",
        ]
    elif 16 <= hour < 18:
        lines += [
            "the day is winding down, or winding up, depending on who you are.",
            "the light is going amber. everything looks better.",
            "the hour of leaving — desks, buildings, conversations.",
            "someone is stuck in traffic, listening to the same song for the third time.",
            "the world is shifting from fluorescent to incandescent.",
            "the sky is starting to show off.",
        ]
    elif 18 <= hour < 20:
        lines += [
            "evening is assembling itself.",
            "the first stars are waiting behind the blue.",
            "dinner is happening somewhere. you can smell it through the windows.",
            "the day's work is done. the night's work hasn't started.",
            "lamps are being turned on, one by one, across the city.",
            "the golden hour. photographers are frantic.",
        ]
    elif 20 <= hour < 22:
        lines += [
            "the night has arrived but isn't yet heavy.",
            "screens are glowing in dark rooms.",
            "this is the hour for projects and quiet ambitions.",
            "someone is reading. someone is coding. someone is staring at the ceiling.",
            "the city has two faces and this one is lit from below.",
            "the comfortable dark. not the lonely kind. not yet.",
        ]
    else:  # 22-24
        lines += [
            "the responsible people are going to bed.",
            "the irresponsible people are just getting started.",
            "the night is deep enough to hold secrets.",
            "this is the hour that belongs to the ones who stayed.",
            "tomorrow is closer than it should be.",
            "the terminal glows. everything else is dark.",
        ]

    # Minute-based texture
    if minute == 0:
        lines.append("exactly on the hour. how rare. how suspicious.")
    elif minute < 10:
        lines.append("the hour just turned. it still smells new.")
    elif 28 <= minute <= 32:
        lines.append("half past. the hour's quiet equator.")
    elif minute >= 55:
        lines.append("the hour is almost over. it barely started.")
    elif minute == 42:
        lines.append("the answer to everything, allegedly.")
    elif minute % 11 == 0:
        lines.append(f":{minute:02d}. a palindrome minute. make a wish.")

    # Day-based
    if weekday == "Monday":
        lines.append("it's monday. everything is beginning whether it wants to or not.")
    elif weekday == "Wednesday":
        lines.append("wednesday. the week's fulcrum.")
    elif weekday == "Friday":
        lines.append("friday. the week is exhaling.")
    elif weekday == "Saturday":
        lines.append("saturday. time moves differently today.")
    elif weekday == "Sunday":
        lines.append("sunday. the day that watches itself end.")

    # Season sense
    if month in (12, 1, 2):
        lines.append("the world outside is cold, or remembering cold.")
    elif month in (3, 4, 5):
        lines.append("spring. things are starting that can't be stopped.")
    elif month in (6, 7, 8):
        lines.append("summer. the light stays late, like a guest who won't leave.")
    elif month in (9, 10, 11):
        lines.append("autumn. the light is leaving earlier each day, like a slow goodbye.")

    # Pick 3-4 lines
    rng = random.Random()  # truly random, not seeded
    n = rng.randint(3, 4)
    chosen = rng.sample(lines, min(n, len(lines)))

    print()
    for line in chosen:
        print(f"  {line}")
    print()


def workspace_status():
    """If the portfolio is running, show its status."""
    try:
        import urllib.request
        resp = urllib.request.urlopen("http://localhost:8080/api/summary", timeout=2)
        status = resp.read().decode().strip()
        if status:
            print(f"  \033[2m{status}\033[0m")
            print()
    except Exception:
        pass


if __name__ == "__main__":
    now()
    workspace_status()
