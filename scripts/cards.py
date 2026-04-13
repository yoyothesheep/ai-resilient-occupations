"""Shared utility for loading and saving per-file occupation cards.

Cards live in data/output/cards/{onet_code}.json.
Falls back to the legacy data/output/occupation_cards.jsonl if the cards dir is empty.
"""

from pathlib import Path
import json

CARDS_DIR = Path("data/output/cards")
LEGACY_JSONL = Path("data/output/occupation_cards.jsonl")


def load_cards() -> dict:
    """Load all per-file cards as dict[onet_code -> card].

    Falls back to the legacy JSONL if the cards directory is empty or missing.
    """
    cards = {}
    if CARDS_DIR.is_dir():
        for p in sorted(CARDS_DIR.glob("*.json")):
            try:
                card = json.loads(p.read_text(encoding="utf-8"))
                cards[card["onet_code"]] = card
            except (json.JSONDecodeError, KeyError):
                pass

    if not cards and LEGACY_JSONL.exists():
        with open(LEGACY_JSONL, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        card = json.loads(line)
                        cards[card["onet_code"]] = card
                    except (json.JSONDecodeError, KeyError):
                        pass

    return cards


def save_cards(cards: dict):
    """Write each card to its own file in CARDS_DIR.

    Asserts that cards is a dict[str, dict] to prevent the naming-collision bug
    where save_jsonl was called with an emerging-roles dict instead of a cards dict.
    """
    assert isinstance(cards, dict), \
        f"save_cards expects dict[str, dict], got {type(cards).__name__}"
    assert all(isinstance(k, str) for k in cards), \
        "save_cards: all keys must be onet_code strings"

    CARDS_DIR.mkdir(parents=True, exist_ok=True)
    for onet_code, card in cards.items():
        (CARDS_DIR / f"{onet_code}.json").write_text(
            json.dumps(card, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


def save_card(card: dict):
    """Write a single card to its own file. Used by append_career_page."""
    assert isinstance(card, dict) and "onet_code" in card, \
        "save_card expects a card dict with an onet_code key"
    CARDS_DIR.mkdir(parents=True, exist_ok=True)
    onet_code = card["onet_code"]
    (CARDS_DIR / f"{onet_code}.json").write_text(
        json.dumps(card, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def load_existing_codes() -> set:
    """Return set of onet_codes already saved as individual card files."""
    if CARDS_DIR.is_dir():
        return {p.stem for p in CARDS_DIR.glob("*.json")}
    return set(load_cards().keys())
