#!/usr/bin/env python3
"""
Reformat '10-Year Net Earnings Calculation Model' to the 2-bullet format.

Sends each row's existing model text + training fields to Claude for
lightweight reformatting — no re-research, just restructuring.

Usage:
    python3 scripts/reformat_model_text.py
"""

import anthropic
import csv
import os
import re
import sys
import time
from pathlib import Path

CSV_PATH = Path("data/top_no_degree_careers/ai_resilience_scores-associates-5.5-enriched.csv")
MODEL = "claude-opus-4-6"
MAX_TOKENS = 1024
SLEEP_SEC = 0.5

SYSTEM = """You reformat career earnings model text into a strict 2-bullet format.
Preserve all facts exactly — do not add, remove, or change any numbers or claims.
Return only the 2 bullet lines, nothing else."""

def normalize_bullets(text: str) -> str | None:
    """Split response into 2 bullets and normalize to '1. ...\n2. Earnings trajectory: ...'"""
    # 1. Prefer explicit "Earnings trajectory:" — works with or without a leading newline/bullet
    m = re.search(r'(?:(?:^|\n)\s*(?:[•\-\*]|\d+\.?)\s*)?Earnings trajectory:', text, re.IGNORECASE)
    if not m:
        # 2. Fall back: any explicit "2." marker on its own line
        m = re.search(r'\n\s*(?:[•\-\*]|2\.?)\s+(?=\S)', text)
    if not m:
        return None

    bullet1_raw = text[:m.start()].strip()
    bullet2_raw = text[m.start():].strip()

    # Strip leading bullet markers from each part
    bullet1 = re.sub(r'^[\s•\-\*\d\.]+', '', bullet1_raw).strip()
    bullet2_body = re.sub(r'^[\s•\-\*\d\.]+', '', bullet2_raw).strip()

    # Ensure bullet 2 starts with "Earnings trajectory:"
    if not re.match(r'Earnings trajectory:', bullet2_body, re.IGNORECASE):
        bullet2_body = f"Earnings trajectory: {bullet2_body}"

    if not bullet1 or not bullet2_body:
        return None
    return f"1. {bullet1}\n2. {bullet2_body}"


def build_prompt(row: dict) -> str:
    return f"""Reformat this '10-Year Net Earnings Calculation Model' text into the exact 2-bullet format below.

Occupation: {row['Occupation']}
Training Years: {row['Training Years']}
Training Salary ($): {row['Training Salary ($)']}
Training Cost ($): {row['Training Cost ($)']}

Current text:
{row['10-Year Net Earnings Calculation Model']}

Required format — return exactly 2 lines:
1. [Training label]: [training description — what it is, duration, who pays, out-of-pocket cost]
2. Earnings trajectory: [salary progression — key milestones, what drives variation]

Training label rules:
- Use "Paid Training:" if the employer/department pays a wage during training (academy, apprenticeship, OJT, internal promotion path)
- Use "Student Pays:" if the candidate pays tuition upfront with no income during training

Preserve all specific numbers, credential names, and facts from the original. Be concise."""


def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    updated = 0
    for i, row in enumerate(rows):
        if not row.get("10-Year Net Earnings Calculation Model") or row["10-Year Net Earnings Calculation Model"] == "ERROR":
            continue

        # Skip rows already in 2-bullet format
        text = row["10-Year Net Earnings Calculation Model"]
        if text.strip().startswith("1. ") and "\n2. Earnings trajectory:" in text:
            continue

        print(f"[{i+1:3}] {row['Code']}  {row['Occupation'][:45]}")

        try:
            resp = client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=SYSTEM,
                messages=[{"role": "user", "content": build_prompt(row)}],
            )
            result = resp.content[0].text.strip()

            # Normalize: split on the earnings trajectory line, rebuild with "1."/"2." prefixes
            normalized = normalize_bullets(result)
            if normalized:
                row["10-Year Net Earnings Calculation Model"] = normalized
                updated += 1
            else:
                print(f"       ⚠ Could not parse 2 bullets, skipping: {result[:120]}")

        except Exception as e:
            print(f"       ERROR: {e}")

        if i < len(rows) - 1:
            time.sleep(SLEEP_SEC)

    # Write back
    tmp = str(CSV_PATH) + ".tmp"
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    import os as _os
    _os.replace(tmp, CSV_PATH)
    print(f"\nDone. {updated} rows reformatted.")


if __name__ == "__main__":
    main()
