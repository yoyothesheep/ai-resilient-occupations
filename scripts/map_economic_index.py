#!/usr/bin/env python3
"""
Phase 2b: Map AEI task descriptions to O*NET occupation codes via join.

Two-pass matching:
1. Exact match on lowercased task text
2. Fuzzy fallback (threshold >= 95) for unmatched — differences are trivially
   small (comma placement, "and" vs "or")

One AEI task can map to multiple occupations — all matches are kept.

Input:
- data/intermediate/economic_index_tasks_raw.csv
- data/input/onet_db/Task Statements.xlsx

Output:
- data/intermediate/economic_index_tasks_mapped.csv
"""

import pandas as pd
from pathlib import Path
from rapidfuzz import fuzz, process
import sys

TASKS_FILE = Path("data/intermediate/economic_index_tasks_raw.csv")
ONET_TASKS_FILE = Path("data/input/onet_db/Task Statements.xlsx")
OUTPUT_FILE = Path("data/intermediate/economic_index_tasks_mapped.csv")
FUZZY_THRESHOLD = 95


def main():
    print("=" * 100)
    print("PHASE 2b: MAP AEI TASKS TO O*NET OCCUPATION CODES")
    print("=" * 100)

    # Load AEI tasks
    aei = pd.read_csv(TASKS_FILE)
    aei['task_lower'] = aei['task_text'].str.lower().str.strip()
    print(f"\nAEI tasks to map: {len(aei):,}")

    # Load O*NET task statements
    onet = pd.read_excel(ONET_TASKS_FILE, usecols=['O*NET-SOC Code', 'Title', 'Task'])
    onet.columns = ['onet_code', 'occupation_title', 'task_text']
    onet['task_lower'] = onet['task_text'].str.lower().str.strip()
    print(f"O*NET task statements: {len(onet):,} ({onet['onet_code'].nunique():,} occupations)")

    # --- Pass 1: exact match ---
    print("\nPass 1: Exact match...")
    merged_exact = aei.merge(
        onet[['task_lower', 'onet_code', 'occupation_title']],
        on='task_lower',
        how='left'
    )
    matched = merged_exact[merged_exact['onet_code'].notna()].copy()
    matched['match_type'] = 'exact'

    unmatched_tasks = aei[~aei['task_lower'].isin(onet['task_lower'])].copy()
    print(f"  Matched:   {matched['task_text'].nunique():,} tasks ({len(matched):,} rows)")
    print(f"  Unmatched: {len(unmatched_tasks):,} tasks")

    # --- Pass 2: fuzzy fallback on unmatched ---
    fuzzy_rows = []
    still_unmatched = []

    if len(unmatched_tasks) > 0:
        print(f"\nPass 2: Fuzzy match on {len(unmatched_tasks)} unmatched (threshold: {FUZZY_THRESHOLD})...")
        onet_task_list = onet['task_lower'].tolist()

        for i, (_, row) in enumerate(unmatched_tasks.iterrows()):
            task = row['task_lower']
            result = process.extractOne(task, onet_task_list, scorer=fuzz.ratio)

            if result and result[1] >= FUZZY_THRESHOLD:
                matched_text = result[0]
                # Get all O*NET rows with this task text (may be multiple occupations)
                matches = onet[onet['task_lower'] == matched_text]
                for _, onet_row in matches.iterrows():
                    fuzzy_rows.append({
                        'task_text': row['task_text'],
                        'onet_code': onet_row['onet_code'],
                        'occupation_title': onet_row['occupation_title'],
                        'match_type': 'fuzzy',
                        'onet_task_count': row['onet_task_count'],
                        'onet_task_pct': row['onet_task_pct'],
                    })
            else:
                still_unmatched.append({
                    'task_text': row['task_text'],
                    'onet_code': None,
                    'occupation_title': None,
                    'match_type': 'unmatched',
                    'onet_task_count': row['onet_task_count'],
                    'onet_task_pct': row['onet_task_pct'],
                })

            if (i + 1) % 50 == 0:
                print(f"  {i + 1}/{len(unmatched_tasks)}...")

        print(f"  Fuzzy matched:  {len(set(r['task_text'] for r in fuzzy_rows)):,} tasks ({len(fuzzy_rows):,} rows)")
        print(f"  Still unmatched: {len(still_unmatched):,} tasks")

    # Combine all results
    matched = matched.drop(columns=['task_lower'])
    fuzzy_df = pd.DataFrame(fuzzy_rows) if fuzzy_rows else pd.DataFrame()
    unmatched_df = pd.DataFrame(still_unmatched) if still_unmatched else pd.DataFrame()

    final = pd.concat([matched, fuzzy_df, unmatched_df], ignore_index=True)

    # Summary
    print(f"\nFinal results:")
    print(f"  Exact matches:    {len(final[final['match_type']=='exact']['task_text'].unique()):,} tasks")
    print(f"  Fuzzy matches:    {len(final[final['match_type']=='fuzzy']['task_text'].unique()):,} tasks")
    print(f"  Unmatched:        {len(final[final['match_type']=='unmatched']):,} tasks")
    print(f"  Occupations:      {final['onet_code'].nunique():,}")
    print(f"  Total rows:       {len(final):,}")

    # Save
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    final.to_csv(OUTPUT_FILE, index=False)
    print(f"\n✓ Saved: {OUTPUT_FILE}")

    # Show remaining unmatched
    if still_unmatched:
        print(f"\nStill unmatched after fuzzy pass:")
        for r in sorted(still_unmatched, key=lambda x: -x['onet_task_count'])[:20]:
            print(f"  [{int(r['onet_task_count']):>5,}]  {r['task_text'][:80]}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
