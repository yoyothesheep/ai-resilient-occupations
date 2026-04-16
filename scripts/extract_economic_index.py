#!/usr/bin/env python3
"""
Phase 2a: Extract O*NET task data + intersection facets from EconomicIndex (global level).

Outputs:
- data/intermediate/economic_index_tasks_raw.csv
  One row per unique task with usage counts, percentages, and all intersection facet metrics.

Intersection facets extracted (same source file, cluster_name uses task::subcategory format):
  - onet_task::collaboration  → automation_pct, augmentation_pct per task
  - onet_task::task_success   → task_success_pct per task
  - onet_task::ai_autonomy    → ai_autonomy_mean per task
  - onet_task::human_only_time + onet_task::human_with_ai_time → speedup_factor per task
"""

import pandas as pd
from pathlib import Path
import sys

INPUT_FILE = Path("data/input/anthropic/aei_raw_claude_ai_2026-02-05_to_2026-02-12.csv")
OUTPUT_DIR = Path("data/intermediate")

# Collaboration pattern categories
AUTOMATION_PATTERNS = {'directive', 'feedback_loop'}
AUGMENTATION_PATTERNS = {'learning', 'task_iteration', 'validation'}


def extract_base_tasks(df):
    """Extract base onet_task facet — one row per task with count and pct."""
    tasks = df[
        (df['geography'] == 'global') &
        (df['facet'] == 'onet_task')
    ].copy()
    wide = tasks.pivot_table(
        index='cluster_name',
        columns='variable',
        values='value',
        aggfunc='first'
    ).reset_index()
    wide = wide.rename(columns={'cluster_name': 'task_text'})
    print(f"  Base tasks: {len(wide):,} unique tasks")
    return wide[['task_text', 'onet_task_count', 'onet_task_pct']]


def extract_collaboration(df):
    """Extract automation_pct and augmentation_pct per task."""
    collab = df[
        (df['geography'] == 'global') &
        (df['facet'] == 'onet_task::collaboration') &
        (df['variable'] == 'onet_task_collaboration_pct')
    ].copy()

    # Parse task_text::pattern from cluster_name
    collab[['task_text', 'pattern']] = collab['cluster_name'].str.rsplit('::', n=1, expand=True)
    collab = collab[collab['pattern'].notna() & ~collab['pattern'].isin(['not_classified', 'none'])]

    automation = collab[collab['pattern'].isin(AUTOMATION_PATTERNS)].groupby('task_text')['value'].sum().rename('automation_pct')
    augmentation = collab[collab['pattern'].isin(AUGMENTATION_PATTERNS)].groupby('task_text')['value'].sum().rename('augmentation_pct')

    result = pd.concat([automation, augmentation], axis=1).reset_index()
    print(f"  Collaboration: {len(result):,} tasks with data")
    return result


def extract_task_success(df):
    """Extract task_success_pct (% of conversations where AI succeeded) per task."""
    success = df[
        (df['geography'] == 'global') &
        (df['facet'] == 'onet_task::task_success') &
        (df['variable'] == 'onet_task_task_success_pct')
    ].copy()

    success[['task_text', 'outcome']] = success['cluster_name'].str.rsplit('::', n=1, expand=True)
    yes = success[success['outcome'] == 'yes'].set_index('task_text')['value'].rename('task_success_pct')

    result = yes.reset_index()
    print(f"  Task success: {len(result):,} tasks with data")
    return result


def extract_ai_autonomy(df):
    """Extract mean AI autonomy score per task."""
    autonomy = df[
        (df['geography'] == 'global') &
        (df['facet'] == 'onet_task::ai_autonomy') &
        (df['variable'] == 'onet_task_ai_autonomy_mean')
    ].copy()
    autonomy = autonomy.rename(columns={'cluster_name': 'task_text', 'value': 'ai_autonomy_mean'})
    # Strip ::value suffix added to numeric facet cluster_names in newer AEI releases
    autonomy['task_text'] = autonomy['task_text'].str.removesuffix('::value')
    result = autonomy[['task_text', 'ai_autonomy_mean']]
    print(f"  AI autonomy: {len(result):,} tasks with data")
    return result


def extract_speedup(df):
    """Extract speedup_factor per task.

    Unit correction: human_only_time is in HOURS, human_with_ai_time is in MINUTES.
    Formula: speedup_factor = (human_only_time_hours * 60) / human_with_ai_time_minutes
    Global check: (3.09h * 60) / 15.35min = 12.1x, matching Anthropic's stated 9-12x range.
    """
    human_raw = df[
        (df['geography'] == 'global') &
        (df['facet'] == 'onet_task::human_only_time') &
        (df['variable'] == 'onet_task_human_only_time_mean')
    ].copy()
    human_raw['task_text'] = human_raw['cluster_name'].str.removesuffix('::value')
    human = human_raw.rename(columns={'value': 'human_only_time'})[['task_text', 'human_only_time']]

    ai_raw = df[
        (df['geography'] == 'global') &
        (df['facet'] == 'onet_task::human_with_ai_time') &
        (df['variable'] == 'onet_task_human_with_ai_time_mean')
    ].copy()
    ai_raw['task_text'] = ai_raw['cluster_name'].str.removesuffix('::value')
    ai = ai_raw.rename(columns={'value': 'human_with_ai_time'})[['task_text', 'human_with_ai_time']]

    merged = human.merge(ai, on='task_text', how='inner')
    # Unit correction: human_only_time in hours → convert to minutes before dividing
    merged['speedup_factor'] = (merged['human_only_time'] * 60) / merged['human_with_ai_time'].replace(0, float('nan'))
    result = merged[['task_text', 'speedup_factor']]
    print(f"  Speedup factor: {len(result):,} tasks with data")
    return result


def main():
    print("=" * 100)
    print("PHASE 2a: EXTRACT ECONOMICINDEX TASKS + INTERSECTION FACETS (GLOBAL)")
    print("=" * 100)

    print("\nLoading raw data...")
    df = pd.read_csv(INPUT_FILE)
    print(f"  Total rows: {len(df):,}")

    print("\nExtracting facets...")
    base = extract_base_tasks(df)
    collab = extract_collaboration(df)
    success = extract_task_success(df)
    autonomy = extract_ai_autonomy(df)
    speedup = extract_speedup(df)

    # Merge all on task_text
    result = base.copy()
    for extra in [collab, success, autonomy, speedup]:
        result = result.merge(extra, on='task_text', how='left')

    # Exclude non-task rows
    result = result[~result['task_text'].isin(['none', 'not_classified'])].copy()

    print(f"\nFinal dataset: {len(result):,} tasks")
    print(f"  With collaboration data:  {result['automation_pct'].notna().sum():,}")
    print(f"  With task_success data:   {result['task_success_pct'].notna().sum():,}")
    print(f"  With ai_autonomy data:    {result['ai_autonomy_mean'].notna().sum():,}")
    print(f"  With speedup_factor data: {result['speedup_factor'].notna().sum():,}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / "economic_index_tasks_raw.csv"
    result.to_csv(output_file, index=False)
    print(f"\n✓ Saved: {output_file}")
    print(f"  Columns: {list(result.columns)}")

    print("\nTop 10 tasks by usage:")
    for _, row in result.nlargest(10, 'onet_task_count').iterrows():
        print(f"  [{int(row['onet_task_count']):>6,}]  auto={row['automation_pct']:.0f}%  aug={row['augmentation_pct']:.0f}%  {row['task_text'][:60]}" if pd.notna(row['automation_pct']) else f"  [{int(row['onet_task_count']):>6,}]  (no collab data)  {row['task_text'][:60]}")

    print("\nPhase 2a complete. Next: Phase 2b (map tasks to O*NET occupations).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
