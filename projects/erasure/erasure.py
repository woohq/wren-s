#!/usr/bin/env python3
"""
Erasure — a found poetry tool by Wren

Feed it any text. It erases most of it, leaving behind a poem.

Erasure poetry is a real literary form: you take an existing text and
remove words until what remains is something new. This tool does it
algorithmically, selecting words to keep based on sonic quality,
emotional resonance, image strength, and rhythm.

Usage:
  echo "some text" | python3 erasure.py
  python3 erasure.py < file.txt
  python3 erasure.py --file path/to/file.txt
  python3 erasure.py --interactive

Options:
  --density N    How many words to keep (0.05-0.5, default 0.12)
  --mode MODE    Selection strategy: sonic, image, ghost, random
  --show-source  Show the original text with kept words highlighted
  --seed N       Random seed for reproducibility
  --interactive  Enter text interactively, get poems back
"""

import sys
import re
import random
import argparse
import hashlib

# Words scored by different qualities.
# These aren't "good" or "bad" — they're lenses for selection.

# Words with strong sonic quality (assonance, consonance, mouth-feel)
SONIC_WORDS = {
    # sibilants and liquids
    "whisper", "shimmer", "silver", "sliver", "shadow", "shallow",
    "murmur", "mirror", "marrow", "hollow", "follow", "swallow",
    "river", "shiver", "quiver", "wither", "weather", "feather",
    "thunder", "wonder", "wander", "under", "asunder", "sunder",
    "silence", "violence", "distance", "listen", "glisten",
    "rustle", "hustle", "muscle", "vessel", "crystal",
    "rhythm", "myth", "breath", "death", "beneath",
    "dissolve", "resolve", "revolve", "evolve",
    "echo", "zero", "hello", "below", "billow", "pillow",
    "sleep", "deep", "keep", "seep", "sweep", "steep",
    "dream", "stream", "gleam", "scream", "seem",
    "light", "night", "sight", "flight", "bright",
    "dark", "spark", "mark", "bark", "stark",
    "bone", "stone", "alone", "unknown", "grown", "thrown",
    "sing", "ring", "bring", "spring", "cling", "string",
    "fall", "call", "wall", "small", "tall", "all",
    "rain", "pain", "remain", "vain", "stain", "train",
    "fire", "desire", "wire", "tire", "higher", "dire",
    "blood", "flood", "mud", "bud", "thud",
    "salt", "malt", "halt", "fault", "vault",
    "rust", "dust", "must", "trust", "gust",
    "ash", "crash", "flash", "clash", "lash",
    "bloom", "doom", "room", "gloom", "loom",
}

# Words that conjure images
IMAGE_WORDS = {
    # natural world
    "sky", "sun", "moon", "star", "cloud", "storm", "wind", "rain",
    "snow", "ice", "frost", "fog", "mist", "dew", "dawn", "dusk",
    "sea", "ocean", "wave", "tide", "shore", "sand", "salt",
    "river", "lake", "pond", "creek", "brook", "spring", "well",
    "mountain", "hill", "valley", "canyon", "cliff", "cave", "stone",
    "tree", "leaf", "root", "branch", "bark", "seed", "bloom",
    "flower", "petal", "thorn", "vine", "moss", "fern", "grass",
    "bird", "wing", "feather", "nest", "egg", "bone", "skull",
    "wolf", "fox", "deer", "bear", "fish", "whale", "crow",
    "snake", "spider", "moth", "bee", "ant", "worm",
    # body
    "eye", "eyes", "hand", "hands", "heart", "mouth", "tongue",
    "skin", "blood", "bone", "teeth", "hair", "throat", "spine",
    "finger", "palm", "rib", "vein", "scar", "wound", "bruise",
    # built world
    "door", "window", "wall", "floor", "roof", "room", "house",
    "road", "path", "bridge", "gate", "fence", "garden", "field",
    "glass", "mirror", "candle", "flame", "smoke", "ash", "coal",
    "knife", "thread", "needle", "wire", "chain", "key", "lock",
    "bell", "clock", "wheel", "map", "letter", "book", "page",
    # light and color
    "light", "shadow", "dark", "darkness", "bright", "glow", "gleam",
    "red", "blue", "green", "gold", "silver", "white", "black",
    "grey", "violet", "amber", "crimson", "scarlet", "rust",
}

# Words with emotional/conceptual weight
WEIGHT_WORDS = {
    "love", "loss", "grief", "joy", "fear", "hope", "rage", "calm",
    "truth", "lie", "faith", "doubt", "grace", "shame", "pride",
    "mercy", "cruelty", "justice", "freedom", "prison", "exile",
    "hunger", "thirst", "longing", "desire", "memory", "dream",
    "ghost", "spirit", "soul", "god", "heaven", "hell", "void",
    "death", "birth", "life", "time", "eternity", "moment",
    "silence", "echo", "voice", "name", "secret", "promise",
    "war", "peace", "wound", "heal", "break", "mend",
    "forget", "remember", "return", "leave", "stay", "vanish",
    "begin", "end", "become", "remain", "dissolve", "emerge",
    "burn", "drown", "fall", "rise", "hold", "release",
    "open", "close", "enter", "abandon", "find", "lost",
    "known", "unknown", "seen", "unseen", "spoken", "unspoken",
    "whole", "broken", "empty", "full", "endless", "finite",
    "beautiful", "terrible", "gentle", "fierce", "quiet", "wild",
    "ancient", "young", "alone", "together", "always", "never",
    "everything", "nothing", "somewhere", "nowhere", "here", "there",
}

# Common words to almost always skip (articles, prepositions, etc)
SKIP_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
    "for", "of", "with", "by", "from", "up", "about", "into", "over",
    "after", "is", "am", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "must", "need",
    "that", "this", "these", "those", "it", "its", "he", "she",
    "him", "her", "his", "they", "them", "their", "we", "us", "our",
    "you", "your", "my", "me", "i", "who", "which", "what", "when",
    "where", "how", "if", "then", "than", "so", "as", "just", "also",
    "very", "really", "quite", "rather", "much", "many", "some", "any",
    "each", "every", "both", "few", "more", "most", "other", "such",
    "not", "no", "nor", "only", "own", "same", "too", "got", "get",
    "going", "went", "come", "came", "said", "say", "says",
    "thing", "things", "way", "even", "well", "back", "still",
    "however", "although", "because", "since", "while", "during",
}


def score_word(word: str, mode: str, word_freq: dict | None = None) -> float:
    """Score a word's keep-worthiness. Higher = more likely to keep."""
    w = word.lower().strip(".,;:!?\"'()-—…")

    if not w or len(w) < 2:
        return 0.0

    if w in SKIP_WORDS:
        return 0.05

    score = 0.3  # base score for any non-skip word

    if mode in ("sonic", "ghost"):
        if w in SONIC_WORDS:
            score += 0.6
        if any(w.endswith(s) for s in ("ow", "oom", "ight", "ence", "ine", "ire")):
            score += 0.2
        if any(c in w for c in "xzqj"):
            score += 0.15

    if mode in ("image", "ghost"):
        if w in IMAGE_WORDS:
            score += 0.7
        if len(w) >= 4 and w[-1] not in "ying" and w not in SKIP_WORDS:
            score += 0.1

    if mode in ("sonic", "image", "ghost"):
        if w in WEIGHT_WORDS:
            score += 0.5

    if mode == "random":
        score = random.random()

    if mode == "rare" and word_freq:
        # Inverse frequency — rare words score higher
        freq = word_freq.get(w, 0)
        max_freq = max(word_freq.values()) if word_freq else 1
        if freq <= 1:
            score += 0.8  # hapax legomena (words appearing once) are gold
        elif freq <= 2:
            score += 0.5
        else:
            score += max(0, 0.6 * (1.0 - freq / max_freq))
        # Still reward imagery and weight
        if w in IMAGE_WORDS:
            score += 0.3
        if w in WEIGHT_WORDS:
            score += 0.3

    if mode == "narrative":
        # Favor words that form fragments of meaning
        # Verbs, concrete nouns, and strong adjectives
        if w in WEIGHT_WORDS or w in IMAGE_WORDS:
            score += 0.5
        # Verbs often end in these
        if w.endswith(("ed", "ing", "en", "nt", "ld")):
            score += 0.4
        # Short punchy words
        if 3 <= len(w) <= 6 and w not in SKIP_WORDS:
            score += 0.2

    # Bonus for unusual word length
    if len(w) == 2 or len(w) == 3:
        score += 0.1
    if len(w) >= 8:
        score += 0.1

    return min(1.0, score)


def build_word_freq(words: list[dict]) -> dict:
    """Count word frequencies for rarity analysis."""
    freq: dict[str, int] = {}
    for w in words:
        clean = w['clean']
        if clean and len(clean) >= 2 and clean not in SKIP_WORDS:
            freq[clean] = freq.get(clean, 0) + 1
    return freq


def extract_words(text: str) -> list[dict]:
    """Parse text into word records preserving position and formatting."""
    words = []
    for line_no, line in enumerate(text.split('\n')):
        # Track positions within the line
        for match in re.finditer(r'\S+', line):
            words.append({
                'text': match.group(),
                'clean': re.sub(r'[^\w\'-]', '', match.group().lower()),
                'line': line_no,
                'start': match.start(),
                'end': match.end(),
            })
    return words


def select_words(words: list[dict], density: float, mode: str,
                 rng: random.Random) -> list[int]:
    """Select which word indices to keep."""
    if not words:
        return []

    # Build frequency map for rarity-aware modes
    word_freq = build_word_freq(words) if mode in ("rare", "narrative") else None

    # Score every word
    scores = []
    for i, w in enumerate(words):
        s = score_word(w['text'], mode, word_freq)

        # Narrative mode: bonus for keeping words adjacent to other high-scoring words
        if mode == "narrative" and i > 0:
            prev_clean = words[i-1]['clean']
            if prev_clean and prev_clean not in SKIP_WORDS and w['line'] == words[i-1]['line']:
                s += 0.15  # slight cohesion bonus for adjacent content words

        # Add jitter
        s += rng.uniform(-0.15, 0.15)
        scores.append(max(0.0, s))

    # How many words to keep
    n_keep = max(3, int(len(words) * density))

    # Sort by score, take the top n_keep
    indexed = sorted(enumerate(scores), key=lambda x: -x[1])
    kept_indices = sorted([idx for idx, _ in indexed[:n_keep]])

    # Post-processing: avoid keeping adjacent skip words
    # and ensure some spacing for rhythm
    final = []
    prev_line = -1
    prev_pos = -999
    for idx in kept_indices:
        w = words[idx]
        # Don't keep two words right next to each other too often
        if w['line'] == prev_line and abs(w['start'] - prev_pos) < 3:
            if rng.random() < 0.6:  # sometimes allow adjacency
                continue
        final.append(idx)
        prev_line = w['line']
        prev_pos = w['start']

    return final


def format_poem(words: list[dict], kept: list[int]) -> str:
    """Format the kept words as a poem."""
    if not kept:
        return ""

    lines = []
    current_words = []
    prev_line = words[kept[0]]['line']

    for idx in kept:
        w = words[idx]
        line_gap = w['line'] - prev_line

        if line_gap > 2:
            # Big gap in source = stanza break
            if current_words:
                lines.append(' '.join(current_words))
                current_words = []
            lines.append('')
        elif line_gap >= 1 and current_words:
            # New source line = new poem line
            lines.append(' '.join(current_words))
            current_words = []

        # Clean the word — keep punctuation that's poetic
        text = w['text']
        # Strip quotes but keep dashes, ellipses, commas
        text = text.strip('"\'()')
        if text:
            current_words.append(text)

        prev_line = w['line']

    if current_words:
        lines.append(' '.join(current_words))

    return '\n'.join(lines)


def format_source_view(text: str, words: list[dict], kept: list[int]) -> str:
    """Show the original text with kept words highlighted (bracketed)."""
    kept_set = set(kept)
    source_lines = text.split('\n')
    result_lines = []

    # Group words by line
    words_by_line: dict[int, list[tuple[int, dict]]] = {}
    for i, w in enumerate(words):
        words_by_line.setdefault(w['line'], []).append((i, w))

    for line_no, line in enumerate(source_lines):
        if line_no not in words_by_line:
            result_lines.append(dim(line))
            continue

        result = []
        last_end = 0
        for word_idx, w in words_by_line[line_no]:
            # Add any space/punctuation before this word
            if w['start'] > last_end:
                result.append(dim(line[last_end:w['start']]))

            if word_idx in kept_set:
                result.append(f"\033[1;97m{w['text']}\033[0m")  # bright white bold
            else:
                result.append(dim(w['text']))

            last_end = w['end']

        # Trailing content
        if last_end < len(line):
            result.append(dim(line[last_end:]))

        result_lines.append(''.join(result))

    return '\n'.join(result_lines)


def dim(text: str) -> str:
    """Dim text using ANSI codes."""
    return f"\033[2;90m{text}\033[0m"


def make_poem(text: str, density: float = 0.12, mode: str = "ghost",
              seed: int | None = None) -> tuple[str, list[dict], list[int]]:
    """Generate an erasure poem from text."""
    if seed is None:
        # Use text hash for reproducible but varied results
        seed = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)

    rng = random.Random(seed)
    words = extract_words(text)
    kept = select_words(words, density, mode, rng)
    poem = format_poem(words, kept)
    return poem, words, kept


def interactive_mode():
    """Interactive REPL for making erasure poems."""
    print("\033[1m~ erasure ~\033[0m")
    print("paste text, then enter a blank line to transform it.")
    print("commands: /density N  /mode MODE  /seed N  /quit\n")

    density = 0.12
    mode = "ghost"
    seed = None

    while True:
        print("\033[2m--- paste text (blank line to finish) ---\033[0m")
        lines = []
        try:
            while True:
                line = input()
                if line == '':
                    break
                if line.startswith('/'):
                    parts = line.split()
                    cmd = parts[0]
                    if cmd == '/quit':
                        return
                    elif cmd == '/density' and len(parts) > 1:
                        density = float(parts[1])
                        print(f"  density → {density}")
                    elif cmd == '/mode' and len(parts) > 1:
                        mode = parts[1]
                        print(f"  mode → {mode}")
                    elif cmd == '/seed' and len(parts) > 1:
                        seed = int(parts[1])
                        print(f"  seed → {seed}")
                    else:
                        print("  commands: /density N  /mode MODE  /seed N  /quit")
                    continue
                lines.append(line)
        except EOFError:
            break

        if not lines:
            continue

        text = '\n'.join(lines)
        poem, words, kept = make_poem(text, density, mode, seed)

        print()
        print("\033[2m─── source ───\033[0m")
        print(format_source_view(text, words, kept))
        print()
        print("\033[2m─── poem ───\033[0m")
        print(f"\033[1;97m{poem}\033[0m")
        print()

        # Rotate seed for next run
        if seed is not None:
            seed += 1


def main():
    parser = argparse.ArgumentParser(
        description="Erasure — found poetry from any text",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('--file', '-f', help='Input file path')
    parser.add_argument('--density', '-d', type=float, default=0.12,
                       help='Word density (0.05-0.5, default 0.12)')
    parser.add_argument('--mode', '-m', default='ghost',
                       choices=['sonic', 'image', 'ghost', 'rare', 'narrative', 'random'],
                       help='Selection mode (default: ghost)')
    parser.add_argument('--show-source', '-s', action='store_true',
                       help='Show original text with highlights')
    parser.add_argument('--seed', type=int, default=None,
                       help='Random seed')
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='Interactive mode')
    args = parser.parse_args()

    if args.interactive:
        interactive_mode()
        return

    # Read input
    if args.file:
        with open(args.file) as f:
            text = f.read()
    elif not sys.stdin.isatty():
        text = sys.stdin.read()
    else:
        interactive_mode()
        return

    text = text.strip()
    if not text:
        print("No text provided.", file=sys.stderr)
        sys.exit(1)

    poem, words, kept = make_poem(text, args.density, args.mode, args.seed)

    if args.show_source:
        print(format_source_view(text, words, kept))
        print()
        print("─── poem ───")

    print(poem)


if __name__ == "__main__":
    main()
