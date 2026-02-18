#!/usr/bin/env python3
"""
Score and rank all occupations using the Anthropic API.

Loads occupations from CSV, batches them, scores via Claude API, computes a
composite final ranking, and writes results to CSV sorted by ranking.
Supports resuming interrupted runs.

Usage:
    python3 scripts/score_occupations.py

Requirements:
    pip install anthropic
    export ANTHROPIC_API_KEY="sk-ant-v1-..."

Output:
    data/output/ai_resilience_scores.csv  — all occupations + scores + ranking
    data/output/score_log.txt             — progress log (for resuming)
"""

import anthropic
import csv
import json
import math
import os
import re
import time

# ── Configuration ────────────────────────────────────────────────────────────
ONET_CSV       = "data/input/All_Occupations_ONET.csv"
SKILL_MD       = "docs/scoring-framework.md"
OUTPUT_CSV     = "data/output/ai_resilience_scores.csv"
LOG_FILE       = "data/output/score_log.txt"
BATCH_SIZE     = 10      # Occupations per API call
SLEEP_SEC      = 2       # Pause between batches (rate limit buffer)
START_BATCH    = 0       # Change to resume from specific batch
MODEL          = "claude-haiku-4-5-20251001"
MAX_TOKENS     = 16000

SCORE_COLUMNS = [
    "Job Zone", "Code", "Occupation", "Data-level", "url",
    "Median Wage", "Projected Growth", "Projected Job Openings",
    "ai_proof_score", "key_drivers"
]

# ── Ranking configuration ────────────────────────────────────────────────────
W_RESILIENCE = 0.50
W_GROWTH     = 0.30
W_OPENINGS   = 0.20

GROWTH_MAP = {
    "Decline (-1% or lower)": 0.0,
    "Little or no change": 0.2,
    "Slower than average (1% to 2%)": 0.4,
    "Average (3% to 4%)": 0.6,
    "Faster than average (5% to 6%)": 0.8,
    "Much faster than average (7% or higher)": 1.0,
}

# ── Helper functions ──────────────────────────────────────────────────────────
def load_skill(path: str) -> str:
    with open(path, "r") as f:
        return f.read()

def load_occupations(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    scoreable = [
        r for r in rows
        if r["Job Zone"] not in ("n/a", "") and r["Data-level"] == "Y"
    ]
    return scoreable

def build_prompt(occupations: list[dict], skill_text: str) -> str:
    occ_list = "\n".join(
        f"{i+1}. {r['Occupation']} (O*NET: {r['Code']}, Job Zone: {r['Job Zone']})"
        for i, r in enumerate(occupations)
    )

    scoring_prompt = f"""Score the following {len(occupations)} occupations using the AI-Resilience Scoring Skill.

OCCUPATIONS TO SCORE:
{occ_list}

Respond ONLY with a valid JSON array. Each element must be:
{{
  "onet_code": "XX-XXXX.XX",
  "ai_proof_score": <1.0-5.0>,
  "key_drivers": "2-3 sentences"
}}"""

    return f"""{skill_text}

---

{scoring_prompt}"""

def write_scores_to_csv(results: list[dict], output_path: str, source_lookup: dict, append: bool = False):
    """Write scored results to CSV file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    mode = "a" if append and os.path.exists(output_path) else "w"
    write_header = mode == "w"

    with open(output_path, mode, newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=SCORE_COLUMNS)
        if write_header:
            writer.writeheader()

        for result in results:
            code = result.get("onet_code")
            src = source_lookup.get(code, {})
            writer.writerow({
                "Job Zone": src.get("Job Zone", ""),
                "Code": src.get("Code", ""),
                "Occupation": src.get("Occupation", ""),
                "Data-level": src.get("Data-level", ""),
                "url": src.get("url", ""),
                "Median Wage": src.get("Median Wage", ""),
                "Projected Growth": src.get("Projected Growth", ""),
                "Projected Job Openings": src.get("Projected Job Openings", ""),
                "ai_proof_score": result.get("ai_proof_score", result.get("final_score", "")),
                "key_drivers": result.get("key_drivers", ""),
            })

def load_scored_codes(path: str) -> set:
    if not os.path.exists(path):
        return set()
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return {row["Code"] for row in reader}

def parse_response(text: str) -> list[dict]:
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*", "", text)
    text = text.strip()
    return json.loads(text)

def log(msg: str):
    print(msg)
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(msg + "\n")

# ── Ranking ──────────────────────────────────────────────────────────────────
def compute_rankings(csv_path: str):
    """Read scored CSV, compute final_ranking, rewrite sorted by ranking."""
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        return

    # Collect log-openings for min-max normalization
    log_openings = []
    for row in rows:
        raw = row.get("Projected Job Openings", "").replace(",", "")
        if raw.isdigit() and int(raw) > 0:
            log_openings.append(math.log(int(raw)))
        else:
            log_openings.append(None)

    valid_logs = [v for v in log_openings if v is not None]
    if valid_logs:
        log_min = min(valid_logs)
        log_max = max(valid_logs)
        log_range = log_max - log_min if log_max != log_min else 1.0
    else:
        log_min = 0
        log_range = 1.0

    for i, row in enumerate(rows):
        score_str = row.get("ai_proof_score", "")
        growth_text = row.get("Projected Growth", "")
        log_val = log_openings[i]

        r_norm = (float(score_str) - 1.0) / 4.0 if score_str else None
        g_norm = GROWTH_MAP.get(growth_text)
        o_norm = (log_val - log_min) / log_range if log_val is not None else None

        # Weighted composite, gracefully handling missing data
        parts, weights = [], []
        if r_norm is not None:
            parts.append(r_norm * W_RESILIENCE)
            weights.append(W_RESILIENCE)
        if g_norm is not None:
            parts.append(g_norm * W_GROWTH)
            weights.append(W_GROWTH)
        if o_norm is not None:
            parts.append(o_norm * W_OPENINGS)
            weights.append(W_OPENINGS)

        raw_score = sum(parts) / sum(weights) * (W_RESILIENCE + W_GROWTH + W_OPENINGS) if weights else 0.0

        # Penalty: low resilience + declining → cap at 0.20
        if score_str and float(score_str) < 2.0 and growth_text == "Decline (-1% or lower)":
            raw_score = min(raw_score, 0.20)

        # Boost: high resilience + fast growth → +0.05
        if score_str and float(score_str) >= 4.0 and growth_text in (
            "Faster than average (5% to 6%)",
            "Much faster than average (7% or higher)",
        ):
            raw_score = min(raw_score + 0.05, 1.0)

        row["final_ranking"] = round(raw_score, 3)

    # Sort by final_ranking descending
    rows.sort(key=lambda r: r.get("final_ranking", 0), reverse=True)

    # Write back with final_ranking before key_drivers
    fieldnames = [c for c in SCORE_COLUMNS if c != "key_drivers"] + ["final_ranking", "key_drivers"]

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    ranked_count = sum(1 for r in rows if r.get("final_ranking", 0) > 0)
    log(f"\n📊 Ranked {ranked_count} occupations. Top 10:")
    for r in rows[:10]:
        log(f"   {r['final_ranking']}  {r.get('ai_proof_score','?'):>4}  {r['Occupation']}")

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    skill_text   = load_skill(SKILL_MD)
    occupations  = load_occupations(ONET_CSV)
    scored_codes = load_scored_codes(OUTPUT_CSV)
    source_lookup = {o["Code"]: o for o in occupations}

    try:
        client = anthropic.Anthropic()
    except anthropic.AuthenticationError:
        log("\n✗ Authentication failed. Set ANTHROPIC_API_KEY environment variable:")
        log("   export ANTHROPIC_API_KEY=\"sk-ant-v1-...\"")
        return False

    remaining = [o for o in occupations if o["Code"] not in scored_codes]
    log(f"\n📊 Scoring {len(remaining)} occupations (skipping {len(scored_codes)} already done)")

    batches = [remaining[i:i+BATCH_SIZE] for i in range(0, len(remaining), BATCH_SIZE)]
    total   = len(batches)
    log(f"📦 {total} batches × {BATCH_SIZE} occupations\n")

    write_header = not os.path.exists(OUTPUT_CSV) or len(scored_codes) == 0

    for batch_idx, batch in enumerate(batches[START_BATCH:], start=START_BATCH):
        log(f"── Batch {batch_idx+1}/{total} ({len(batch)} occupations)")
        names = [o["Occupation"] for o in batch]
        log(f"   {', '.join(names[:3])}{'...' if len(names) > 3 else ''}")

        prompt = build_prompt(batch, skill_text)

        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=skill_text,
                messages=[{"role": "user", "content": prompt}]
            )
            raw = response.content[0].text
            results = parse_response(raw)

            write_scores_to_csv(results, OUTPUT_CSV, source_lookup, append=not write_header)
            write_header = False

            scores = [r.get('ai_proof_score', r.get('final_score')) for r in results]
            log(f"   ✓ Scored {len(results)}. Range: {min(scores):.1f}–{max(scores):.1f}")

        except json.JSONDecodeError as e:
            log(f"   ✗ JSON parse error: {e}")
            log(f"   Raw response: {raw[:300]}")
            continue

        except anthropic.RateLimitError:
            log(f"   ✗ Rate limited. Waiting 30s before retry...")
            time.sleep(30)
            continue

        except Exception as e:
            log(f"   ✗ API error: {e}")
            log("   Sleeping 30s before retry...")
            time.sleep(30)
            continue

        if batch_idx < total - 1:
            time.sleep(SLEEP_SEC)

    # Compute final rankings after all scoring is done
    log("\n── Computing final rankings...")
    compute_rankings(OUTPUT_CSV)

    log(f"\n✓ Complete! Results in {OUTPUT_CSV}\n")
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
