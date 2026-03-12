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
      - 'Training Years': float — duration of training program (0, 0.5, 1, 2…)
      - 'Training Salary ($)': int — annualized wage paid during training (0 if unpaid/student)
      - 'Training Cost ($)': int — out-of-pocket cost (tuition, tools, certs)
      - 'Median Annual Wage ($)': int
      - 'Yr1 ($)' .. 'Yr10 ($)': int (ladder: manually set; linear: auto-filled)

    For linear careers, auto-fills Yr1–Yr10 via interpolation before summing.
    Returns: updated row with Yr1–Yr10, 10-Year Net Earnings, and Calculation string.
    """
    calc_type = row.get('Calculation Type', 'ladder')
    median = int(row.get('Median Annual Wage ($)', 0))
    training_cost = int(str(row.get('Training Cost ($)', 0) or 0))
    training_yrs = float(str(row.get('Training Years', '0') or '0'))
    paid_rate = int(float(str(row.get('Training Salary ($)', '0') or '0')))

    if calc_type == 'linear':
        full_training = int(training_yrs)
        frac_training = training_yrs - full_training
        start_year = full_training + 1  # first full earning year

        start_salary_str = str(row.get(f'Yr{start_year} ($)', '0')).replace(',', '').replace('$', '').strip()
        start_salary = int(float(start_salary_str)) if start_salary_str else 0

        # Fill full training years with paid_rate (0 if unpaid/student)
        for i in range(1, start_year):
            row[f'Yr{i} ($)'] = str(paid_rate)

        # Linear interpolation from start_year to year 10
        years_to_grow = 10 - start_year
        for i in range(start_year, 11):
            val = start_salary + (median - start_salary) * (i - start_year) / years_to_grow if years_to_grow > 0 else start_salary
            if i == start_year and frac_training > 0:
                # Blend: frac_training portion at paid_rate, remainder at earning rate
                val = paid_rate * frac_training + val * (1 - frac_training)
            row[f'Yr{i} ($)'] = str(round(val))

    yr_vals = [int(float(str(row.get(f'Yr{i+1} ($)', 0)).replace(',', '').replace('$', ''))) for i in range(10)]
    total = sum(yr_vals) - training_cost
    row['10-Year Net Earnings ($)'] = str(total)

    if calc_type == 'linear':
        row['10-Year Net Earnings Calculation'] = (
            f'Linear: (${start_salary:,} up to ${median:,}) over {10 - training_yrs:g} yrs − ${training_cost:,} training = ${total:,}'
        )
    else:
        parts = [f'Yr{i+1} ${v:,}' for i, v in enumerate(yr_vals)]
        row['10-Year Net Earnings Calculation'] = (
            ' + '.join(parts) + f' = ${sum(yr_vals):,} − ${training_cost:,} training = ${total:,}'
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
