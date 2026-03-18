"""Data layer for a visual thought garden.

Stores "thoughts" (notes/ideas) positioned in 2D space, extracts keywords,
computes semantic connections between thoughts, and handles layout.

Storage lives at ~/.garden/garden.json as a JSON array of thought dicts.
"""

from __future__ import annotations

import math
import random
import string
from datetime import datetime
from pathlib import Path
import sys

# Import shared utilities from sibling projects
_proj = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_proj / "dash"))
sys.path.insert(0, str(_proj / "erasure"))

from data import _read_json, _write_json, _short_id, _ensure_dir

# ---------------------------------------------------------------------------
# Stop words — common words to skip when extracting keywords.
# Copied from erasure.py to avoid importing it (has argparse side effects).
# ---------------------------------------------------------------------------

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
    "all", "been", "there", "here", "out", "now", "new", "like",
    "one", "two", "don", "doesn", "didn", "won", "wasn", "aren",
    "make", "made", "let", "know", "see", "take", "give", "use",
}


# ---------------------------------------------------------------------------
# Keyword extraction
# ---------------------------------------------------------------------------

def extract_keywords(text: str) -> list[str]:
    """Extract meaningful words from text.

    Lowercase, strip punctuation, filter out SKIP_WORDS and words shorter
    than 3 characters. Returns unique words sorted alphabetically.
    """
    stripped = text.lower().translate(str.maketrans("", "", string.punctuation))
    words = stripped.split()
    seen: set[str] = set()
    keywords: list[str] = []
    for w in words:
        if len(w) >= 3 and w not in SKIP_WORDS and w not in seen:
            seen.add(w)
            keywords.append(w)
    return sorted(keywords)


# ---------------------------------------------------------------------------
# Connection computation
# ---------------------------------------------------------------------------

def compute_connections(thoughts: list[dict]) -> list[tuple[str, str, float]]:
    """Compute keyword-overlap connections between all thought pairs.

    For each pair:
      - strength = len(shared_keywords) / min(len(kw_a), len(kw_b))
      - +0.3 for each shared tag
      - Only pairs with strength >= 0.15 are returned.

    Returns list of (id_a, id_b, strength) sorted by strength descending.
    """
    connections: list[tuple[str, str, float]] = []

    for i in range(len(thoughts)):
        for j in range(i + 1, len(thoughts)):
            a, b = thoughts[i], thoughts[j]
            kw_a = set(a.get("keywords", []))
            kw_b = set(b.get("keywords", []))

            strength = 0.0
            if kw_a and kw_b:
                shared = kw_a & kw_b
                strength = len(shared) / min(len(kw_a), len(kw_b))

            # Tag overlap bonus
            tags_a = set(a.get("tags", []))
            tags_b = set(b.get("tags", []))
            shared_tags = tags_a & tags_b
            strength += 0.3 * len(shared_tags)

            if strength >= 0.15:
                connections.append((a["id"], b["id"], round(strength, 4)))

    connections.sort(key=lambda c: c[2], reverse=True)
    return connections


# ---------------------------------------------------------------------------
# Position computation
# ---------------------------------------------------------------------------

def compute_position(
    new_thought: dict,
    existing: list[dict],
    width: float = 100,
    height: float = 50,
) -> tuple[float, float]:
    """Place a new thought near related thoughts in the garden.

    1. Compute keyword overlap with each existing thought.
    2. Find top 3 most related.
    3. If related exist: position = weighted centroid + random offset (radius 4-8).
    4. If no related: random position avoiding collisions (min 3 cells from others).
    5. Clamp to (2, width-2) and (2, height-2).
    """
    new_kw = set(new_thought.get("keywords", []))

    # Score each existing thought by keyword overlap
    scored: list[tuple[dict, float]] = []
    for t in existing:
        t_kw = set(t.get("keywords", []))
        if new_kw and t_kw:
            shared = new_kw & t_kw
            overlap = len(shared) / min(len(new_kw), len(t_kw))
            if overlap > 0:
                scored.append((t, overlap))

    scored.sort(key=lambda s: s[1], reverse=True)
    top = scored[:3]

    if top:
        # Weighted centroid of top related thoughts
        total_weight = sum(s for _, s in top)
        cx = sum(t["x"] * s for t, s in top) / total_weight
        cy = sum(t["y"] * s for t, s in top) / total_weight

        # Random offset at radius 4-8
        angle = random.uniform(0, 2 * math.pi)
        radius = random.uniform(4, 8)
        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)
    else:
        # Random position avoiding collisions
        for _ in range(50):
            x = random.uniform(2, width - 2)
            y = random.uniform(2, height - 2)
            if all(
                math.hypot(x - t["x"], y - t["y"]) >= 3
                for t in existing
            ):
                break

    # Clamp to valid bounds
    x = max(2.0, min(width - 2, x))
    y = max(2.0, min(height - 2, y))

    return (round(x, 2), round(y, 2))


# ---------------------------------------------------------------------------
# Growth stage
# ---------------------------------------------------------------------------

def growth_stage(planted_at: str) -> int:
    """Return growth stage 0-4 based on how old a thought is.

    0 (seed):    < 1 hour
    1 (sprout):  1 hour - 1 day
    2 (sapling): 1 - 3 days
    3 (plant):   3 - 7 days
    4 (flower):  7+ days
    """
    planted = datetime.fromisoformat(planted_at)
    age_hours = (datetime.now() - planted).total_seconds() / 3600

    if age_hours < 1:
        return 0
    elif age_hours < 24:
        return 1
    elif age_hours < 72:
        return 2
    elif age_hours < 168:
        return 3
    else:
        return 4


# ---------------------------------------------------------------------------
# Text import — extract key sentences from prose
# ---------------------------------------------------------------------------

def import_text(text: str, max_thoughts: int = 20) -> list[str]:
    """Extract the most interesting sentences from a block of text.

    Splits text into sentences, scores each by keyword richness
    (how many non-stop-words it contains), and returns the top N.
    Short sentences and sentences with only stop words are filtered out.
    """
    import re

    # Split into sentences
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 15]

    if not sentences:
        return []

    # Score each sentence by keyword density
    scored = []
    for sent in sentences:
        words = extract_keywords(sent)
        if len(words) >= 2:  # need at least 2 meaningful words
            # Score: number of keywords, bonus for longer sentences
            score = len(words) + len(sent) * 0.01
            scored.append((score, sent))

    # Sort by score, take top N
    scored.sort(key=lambda x: -x[0])
    return [sent for _, sent in scored[:max_thoughts]]


# ---------------------------------------------------------------------------
# ThoughtStore
# ---------------------------------------------------------------------------

class ThoughtStore:
    """Storage for garden thoughts in ~/.garden/garden.json."""

    def __init__(self) -> None:
        self._path = Path.home() / ".garden" / "garden.json"
        _ensure_dir(self._path.parent)

    def _load(self) -> list[dict]:
        """Load all thoughts from disk."""
        data = _read_json(self._path)
        return data if isinstance(data, list) else []

    def _save(self, thoughts: list[dict]) -> None:
        """Save all thoughts to disk."""
        _write_json(self._path, thoughts)

    def plant(
        self,
        text: str,
        tags: list[str] | None = None,
        garden_width: float = 100,
        garden_height: float = 50,
    ) -> dict:
        """Plant a new thought. Computes keywords and position automatically.

        Returns the new thought dict.
        """
        if tags is None:
            tags = []

        keywords = extract_keywords(text)
        thought: dict = {
            "id": _short_id(),
            "text": text,
            "tags": list(tags),
            "planted_at": datetime.now().isoformat(),
            "x": 0.0,
            "y": 0.0,
            "keywords": keywords,
        }

        existing = self._load()
        x, y = compute_position(thought, existing, garden_width, garden_height)
        thought["x"] = x
        thought["y"] = y

        existing.append(thought)
        self._save(existing)
        return thought

    def all_thoughts(self) -> list[dict]:
        """Return all thoughts."""
        return self._load()

    def get(self, thought_id: str) -> dict | None:
        """Return a single thought by id, or None."""
        for t in self._load():
            if t["id"] == thought_id:
                return t
        return None

    def search(self, query: str) -> list[dict]:
        """Search thoughts by text content and tags (case-insensitive)."""
        q = query.lower()
        results: list[dict] = []
        for t in self._load():
            if q in t.get("text", "").lower():
                results.append(t)
            elif any(q in tag.lower() for tag in t.get("tags", [])):
                results.append(t)
        return results

    def remove(self, thought_id: str) -> None:
        """Remove a thought by id."""
        thoughts = [t for t in self._load() if t["id"] != thought_id]
        self._save(thoughts)
