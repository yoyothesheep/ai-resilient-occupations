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
      - 'Unpaid Training Years': float (e.g. 0, 0.5, 1, 2)
      - 'Training Cost ($)': int
      - 'Median Annual Wage ($)': int
      - 'Yr1 ($)' .. 'Yr10 ($)': int (ladder: manually set; linear: auto-filled based on unpaid years)

    For linear careers, auto-fills Yr1–Yr10 via interpolation before summing.
    Returns: updated row with Yr1–Yr10, 10-Year Net Earnings, and Calculation string.
    """
    calc_type = row.get('Calculation Type', 'ladder')
    median = int(row.get('Median Annual Wage ($)', 0))
    training = int(row.get('Training Cost ($)', 0))
    unpaid_str = str(row.get('Unpaid Training Years', '0') or '0')
    unpaid = float(unpaid_str)

    if calc_type == 'linear':
        full_unpaid = int(unpaid)
        fractional_unpaid = unpaid - full_unpaid

        start_year = full_unpaid + 1
        start_salary_str = row.get(f'Yr{start_year} ($)', '0')
        start_salary_str = str(start_salary_str).replace(',', '').replace('$', '').strip()
        start_salary = int(float(start_salary_str)) if start_salary_str else 0

        for i in range(1, start_year):
            row[f'Yr{i} ($)'] = '0'

        years_to_grow = 10 - start_year
        for i in range(start_year, 11):
            if years_to_grow > 0:
                val = start_salary + (median - start_salary) * (i - start_year) / years_to_grow
            else:
                val = start_salary
            
            if i == start_year and fractional_unpaid > 0:
                val = val * (1 - fractional_unpaid)
                
            row[f'Yr{i} ($)'] = str(round(val))

    yr_vals = [int(float(str(row.get(f'Yr{i+1} ($)', 0)).replace(',', '').replace('$', ''))) for i in range(10)]
    total = sum(yr_vals) - training
    row['10-Year Net Earnings ($)'] = str(total)

    if calc_type == 'linear':
        row['10-Year Net Earnings Calculation'] = (
            f'Linear: (${start_salary:,} up to ${median:,}) over {10 - unpaid:g} yrs − ${training:,} training = ${total:,}'
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
        if row.get('Calculation Type'):
            calc_e10(row)
            updated += 1

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Processed {updated}/{len(rows)} rows → {output_path}")


if __name__ == '__main__':
    main()
