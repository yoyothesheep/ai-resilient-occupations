#!/usr/bin/env python3
"""
Audit ai_resilience_scores.csv for two types of issues:

1. CATEGORY/TEXT CONFLICTS — key_drivers language contradicts the ai_category label
2. BORDERLINE SCORES — filter values within ±0.3 of a classification threshold
   (these occupations are fragile: small rescoring flips their category)

Usage:
    python3 scripts/audit_conflicts.py
    python3 scripts/audit_conflicts.py --borderline-only
    python3 scripts/audit_conflicts.py --conflicts-only
"""

import csv
import sys
from pathlib import Path

SCORES_CSV = Path("data/output/ai_resilience_scores.csv")

# Classification thresholds (must match score_occupations.py)
EXPOSURE_THRESHOLD   = 3.2
NECESSITY_THRESHOLD  = 1.8
ELASTICITY_THRESHOLD = 3.5
BORDERLINE_MARGIN    = 0.3

# Phrases that signal the key_drivers text contradicts the assigned category.
# Uses negation-aware matching: skip if preceded by "not", "rather than", "won't", "isn't", "can't".
CONFLICT_SIGNALS = {
    "Grow with AI": [
        "headcount pressure is real",
        "highly automatable",
        "highly vulnerable",
        "prime target for",
        "shrinking demand",
        "fewer positions over time",
        "already being replaced",
        "significant displacement",
        "core task.*is highly automatable",
        "faces significant displacement",
    ],
    "High Automation Risk": [
        "well-protected",
        "strong job security",
        "stable career path",
        "cannot replicate",
        "hard to automate",
        "irreplaceable",
    ],
    "Will Evolve": [
        r"(?<!not )(?<!won't )(?<!isn't )disappearing\b",
        "eliminated entirely",
        "replaced entirely",
    ],
    "Less Immediate Change": [
        "highly vulnerable to automation",
        "prime target for automation",
    ],
}

NEGATION_PREFIXES = ["not ", "rather than ", "won't ", "isn't ", "can't ", "without ", "instead of "]


def _has_conflict_phrase(kd: str, phrases: list[str]) -> list[str]:
    import re
    kd_lower = kd.lower()
    hits = []
    for phrase in phrases:
        matches = list(re.finditer(phrase, kd_lower))
        for m in matches:
            start = max(0, m.start() - 15)
            context = kd_lower[start:m.start()]
            if not any(context.endswith(neg) or neg in context[-len(neg):] for neg in NEGATION_PREFIXES):
                hits.append(phrase)
                break
    return hits


def find_conflicts(rows: list[dict]) -> list[dict]:
    results = []
    for row in rows:
        cat = row.get("ai_category", "")
        kd = row.get("key_drivers", "")
        if not cat or not kd:
            continue
        phrases = CONFLICT_SIGNALS.get(cat, [])
        hits = _has_conflict_phrase(kd, phrases)
        if hits:
            results.append({**row, "_conflict_phrases": hits})
    return results


def find_borderline(rows: list[dict]) -> list[dict]:
    results = []
    for row in rows:
        try:
            exp = float(row.get("exposure_filter", 0))
            nec = float(row.get("necessity_filter", 0))
            ela = float(row.get("elasticity_filter", 0))
        except ValueError:
            continue
        flags = []
        if abs(exp - EXPOSURE_THRESHOLD) <= BORDERLINE_MARGIN:
            flags.append(f"exp={exp} (threshold {EXPOSURE_THRESHOLD})")
        if abs(nec - NECESSITY_THRESHOLD) <= BORDERLINE_MARGIN:
            flags.append(f"nec={nec} (threshold {NECESSITY_THRESHOLD})")
        if abs(ela - ELASTICITY_THRESHOLD) <= BORDERLINE_MARGIN:
            flags.append(f"ela={ela} (threshold {ELASTICITY_THRESHOLD})")
        if flags:
            results.append({**row, "_borderline_flags": flags})
    return results


def print_conflicts(conflicts: list[dict]):
    print(f"\n{'='*70}")
    print(f"CATEGORY / KEY_DRIVERS CONFLICTS ({len(conflicts)} found)")
    print(f"{'='*70}")
    for r in conflicts:
        print(f"\n  {r['Occupation']} ({r['Code']}) — {r['ai_category']}")
        print(f"  Flags   : {r['_conflict_phrases']}")
        print(f"  Filters : exp={r['exposure_filter']}  nec={r['necessity_filter']}  ela={r['elasticity_filter']}")
        print(f"  Text    : {r['key_drivers'][:200]}...")


def print_borderline(borderline: list[dict]):
    print(f"\n{'='*70}")
    print(f"BORDERLINE SCORES — within ±{BORDERLINE_MARGIN} of threshold ({len(borderline)} found)")
    print(f"{'='*70}")
    for r in borderline:
        print(f"\n  {r['Occupation']} ({r['Code']}) — {r['ai_category']}")
        print(f"  Flags   : {r['_borderline_flags']}")


def print_distribution(rows: list[dict]):
    from collections import Counter
    cats = Counter(r["ai_category"] for r in rows if r.get("ai_category"))
    total = sum(cats.values())
    openai = {"Less Immediate Change": 46, "Will Evolve": 24, "High Automation Risk": 18, "Grow with AI": 12}
    print(f"\n{'='*70}")
    print(f"CATEGORY DISTRIBUTION (n={total})")
    print(f"{'='*70}")
    print(f"  {'Category':<30} {'Ours':>6}  {'OpenAI':>8}  {'Delta':>6}")
    print(f"  {'-'*55}")
    for cat in ["Less Immediate Change", "Will Evolve", "High Automation Risk", "Grow with AI"]:
        n = cats.get(cat, 0)
        pct = n / total * 100
        ref = openai.get(cat, 0)
        delta = pct - ref
        flag = " ⚠" if abs(delta) > 5 else ""
        print(f"  {cat:<30} {pct:>5.0f}%  {ref:>7}%  {delta:>+5.0f}%{flag}")


def main():
    if not SCORES_CSV.exists():
        print(f"✗ {SCORES_CSV} not found")
        sys.exit(1)

    with open(SCORES_CSV, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    conflicts_only  = "--conflicts-only"  in sys.argv
    borderline_only = "--borderline-only" in sys.argv

    print_distribution(rows)

    if not borderline_only:
        conflicts = find_conflicts(rows)
        print_conflicts(conflicts)

    if not conflicts_only:
        borderline = find_borderline(rows)
        print_borderline(borderline)

    print()


if __name__ == "__main__":
    main()
