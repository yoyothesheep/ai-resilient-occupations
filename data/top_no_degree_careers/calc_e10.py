"""
calc_e10 — Calculate 10-Year Net Earnings for career rows.

Usage:
    python calc_e10.py                          # processes enriched CSV in place
    python calc_e10.py input.csv output.csv     # explicit input/output
"""

import csv
import sys
from pathlib import Path

DEFAULT_INPUT = Path(__file__).parent / "ai_resilience_scores-associates-5.5-enriched.csv"


def calc_e10(row: dict) -> dict:
    """
    Calculate 10-Year Net Earnings from CSV row dict.

    Inputs read from row:
      - 'Calculation Type': 'ladder' or 'linear'
      - 'Year 1 Income ($)': int
      - 'Training Cost ($)': int
      - 'Median Annual Wage ($)': int
      - 'Yr1 ($)' .. 'Yr10 ($)': int (ladder: manually set; linear: auto-filled)

    For linear careers, auto-fills Yr1–Yr10 via interpolation before summing.
    Returns: updated row with Yr1–Yr10, 10-Year Net Earnings, and Calculation string.
    """
    yr1 = int(row['Year 1 Income ($)'])
    median = int(row['Median Annual Wage ($)'])
    training = int(row['Training Cost ($)'])
    calc_type = row['Calculation Type']

    if calc_type == 'linear':
        for i in range(10):
            row[f'Yr{i+1} ($)'] = str(round(yr1 + (median - yr1) * i / 9))

    yr_vals = [int(row[f'Yr{i+1} ($)']) for i in range(10)]
    total = sum(yr_vals) - training
    row['10-Year Net Earnings ($)'] = str(total)

    if calc_type == 'linear':
        row['10-Year Net Earnings Calculation'] = (
            f'Linear: (${yr1:,} + ${median:,}) / 2 × 10 − ${training:,} = ${total:,}'
        )
    else:
        parts = [f'Yr{i+1} ${v:,}' for i, v in enumerate(yr_vals)]
        row['10-Year Net Earnings Calculation'] = (
            ' + '.join(parts) + f' = ${sum(yr_vals):,} − ${training:,} training = ${total:,}'
        )
    return row


def main():
    if len(sys.argv) >= 3:
        input_path = Path(sys.argv[1])
        output_path = Path(sys.argv[2])
    elif len(sys.argv) == 2:
        input_path = Path(sys.argv[1])
        output_path = input_path
    else:
        input_path = DEFAULT_INPUT
        output_path = DEFAULT_INPUT

    with open(input_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    updated = 0
    for row in rows:
        if row.get('Calculation Type') and row.get('Year 1 Income ($)'):
            calc_e10(row)
            updated += 1

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Processed {updated}/{len(rows)} rows → {output_path}")


if __name__ == '__main__':
    main()
