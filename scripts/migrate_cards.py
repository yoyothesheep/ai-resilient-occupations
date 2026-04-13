"""One-time migration: occupation_cards.jsonl → data/output/cards/{onet_code}.json

Run once before using the updated pipeline scripts:
    python scripts/migrate_cards.py

Does NOT delete the legacy file — keep it as a backup until confirmed.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from cards import load_cards, save_cards, CARDS_DIR, LEGACY_JSONL

if __name__ == "__main__":
    cards = load_cards()
    if not cards:
        print("No cards found in legacy JSONL or cards dir. Nothing to migrate.")
        sys.exit(1)

    save_cards(cards)
    count = len(list(CARDS_DIR.glob("*.json")))
    print(f"Migrated {count} cards to {CARDS_DIR}/")
    print(f"Legacy file retained at {LEGACY_JSONL} — delete manually when confirmed.")
