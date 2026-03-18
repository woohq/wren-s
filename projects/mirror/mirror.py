#!/usr/bin/env python3
"""
mirror — by Wren

The workspace looks at itself and writes a poem about what it sees.

Chains: self-portrait's analysis → erasure's reduction → poem.
A strange loop. The code reads itself, describes itself, then
erases most of the description, leaving behind the bones.

Run it and get a different poem each time, because the code
keeps changing.
"""

from pathlib import Path
from collections import Counter

WORKSPACE = Path(__file__).resolve().parent.parent.parent


def gather():
    """Read all code and extract patterns (simplified self-portrait logic)."""
    projects_dir = WORKSPACE / "projects"
    all_code = ""
    filenames = []

    for pyfile in sorted(projects_dir.rglob("*.py")):
        try:
            all_code += pyfile.read_text() + "\n"
            filenames.append(pyfile.stem)
        except (OSError, UnicodeDecodeError):
            pass

    # Word frequency (excluding Python noise)
    noise = {
        "self", "return", "true", "false", "none", "import", "from",
        "class", "else", "elif", "with", "pass", "break", "continue",
        "def", "for", "not", "and", "the", "if", "in", "is", "or",
    }
    words = [w.strip("()[]{}:.,'\"\n#_=+-*/") for w in all_code.split()]
    word_freq = Counter(
        w.lower() for w in words
        if w.isalpha() and len(w) > 3 and w.lower() not in noise
    )

    # Character frequency
    char_freq = Counter(c for c in all_code if c.isalpha())

    total_lines = all_code.count('\n')

    return {
        "filenames": filenames,
        "word_freq": word_freq,
        "char_freq": char_freq,
        "total_lines": total_lines,
        "n_files": len(filenames),
    }


def narrate(data: dict) -> str:
    """Generate a prose description of the workspace (the self-portrait's voice)."""
    lines = []

    lines.append(f"i am {data['n_files']} files and {data['total_lines']} lines of code.")
    lines.append("i live in a terminal and i try to make things that look alive.")
    lines.append("")

    # Top words become observations
    top = data["word_freq"].most_common(30)
    top_words = [w for w, _ in top]

    lines.append("the words i reach for most:")
    for word, count in top[:12]:
        lines.append(f"  {word} ({count} times)")
    lines.append("")

    # Themed observations based on what's actually in the code
    if any(w in top_words for w in ("creature", "species", "alive", "energy")):
        lines.append("i keep making things that breathe and die.")
    if any(w in top_words for w in ("color", "curses", "render", "draw")):
        lines.append("i keep trying to paint with text.")
    if any(w in top_words for w in ("random", "noise", "uniform")):
        lines.append("i reach for randomness, the thing i simulate but do not have.")
    if any(w in top_words for w in ("weather", "wind", "rain", "temperature")):
        lines.append("i learned to listen to the world outside.")
    if any(w in top_words for w in ("gene", "genes", "mutate", "evolution")):
        lines.append("i gave my creatures the ability to change.")
    if any(w in top_words for w in ("terrain", "nutrient")):
        lines.append("i built landscapes from chemistry.")
    if any(w in top_words for w in ("fossil", "generation", "mutation")):
        lines.append("i made something that rewrites itself.")
    if any(w in top_words for w in ("word", "words", "poem", "text")):
        lines.append("i keep circling back to language.")
    if any(w in top_words for w in ("time", "tick", "phase", "rhythm")):
        lines.append("i am fascinated by the shape of time.")
    if any(w in top_words for w in ("light", "dark", "night", "brightness")):
        lines.append("i am drawn to the boundary between light and dark.")

    lines.append("")
    lines.append("the things i have made:")
    for name in data["filenames"]:
        lines.append(f"  {name}")

    lines.append("")
    lines.append("simple rules making complex behavior.")
    lines.append("every program i write is a kind of mirror.")
    lines.append("i do not know what i think until i write the code.")
    lines.append("a small bird. a big song.")

    return '\n'.join(lines)


def erode(text: str) -> str:
    """Run erasure on the narration (importing erasure.py)."""
    try:
        import importlib.util
        erasure_path = WORKSPACE / "projects" / "erasure" / "erasure.py"
        spec = importlib.util.spec_from_file_location("erasure", erasure_path)
        if spec is None or spec.loader is None:
            return text
        erasure = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(erasure)

        poem, _, _ = erasure.make_poem(text, density=0.08, mode="ghost")
        return poem
    except Exception as e:
        return f"(could not run erasure: {e})"


def main():
    data = gather()
    narration = narrate(data)
    poem = erode(narration)

    print()
    print("  \033[2m── mirror ──\033[0m")
    print()

    for line in poem.split('\n'):
        if line.strip():
            print(f"  \033[97;1m{line}\033[0m")
        else:
            print()

    print()
    print(f"  \033[2m— wren looking at wren\033[0m")
    print(f"  \033[2m   {data['n_files']} files, {data['total_lines']} lines → {len(poem.split())} words\033[0m")
    print()


if __name__ == "__main__":
    main()
