# Career CSV Enrichment Instructions

## Source File
`ai_resilience_scores-associates-5.5.csv` — 77 career rows with columns: Job Zone, Code, Occupation, url, Median Wage, Projected Growth, Employment Change, Projected Job Openings, Top Education Level, Sample Job Titles, Job Description, ai_proof_score, final_ranking, key_drivers

## Output File
`ai_resilience_scores-associates-5.5-enriched.csv` — same columns plus new columns below.

---

## New Columns — Machine-Readable Inputs

These columns feed the `calc_e10()` Python function.

### Median Annual Wage ($)
Parsed from the original "Median Wage" string (e.g. `"$49.50 hourly, $102,950 annual"` → `102950`). Clean integer, no `$` or commas.

### Calculation Type
`ladder` or `linear`. Determines which formula `calc_e10()` uses.

- **ladder** — government salary schedules, union step increases, trade apprenticeships, or careers with distinct promotion milestones (e.g., police patrol → sergeant, apprentice → journeyman)
- **linear** — careers with gradual, unstructured wage growth over time


### Unpaid Training Years
Number of full-time, unpaid training/school years before earning begins. Can be `0`, `0.5` (for ~6 month programs), or an integer number of years.

**Rules:**
- **Year 1 is always the start of the path to get into the role.** Do not only start counting after graduation. (e.g., if it's a 2-year associate's degree, Yr1 and Yr2 have $0 income).
- Set whole years of full-time unpaid training to `$0`.
- If an unpaid training year is fractional (e.g. `0.5`), the first earning year is prorated (e.g. `0.5` of full starting salary).
- All tuition/program costs go into **Training Cost ($)** — do NOT subtract them from Yr columns.
- If training is paid (apprenticeships, academies) or done while working (on-the-job, part-time certs), do NOT set any years to $0

**Choosing the shortest path:** When a career has multiple entry paths (e.g., associate degree vs. certificate, formal program vs. OJT), use the **shortest path to earning** for the Yr columns. Note the chosen path in the **10-Year Net Earnings Calculation Model** field. Examples:
- Dental Assistants: OJT available in many states → 0 unpaid years (not 1yr for the certificate program)
- Forensic Science Techs: certificate path (6–12 mo) → 1 unpaid year (not 2yr for the associate)
- Computer Systems Analysts: start in IT support with certs → 0 unpaid years (not 2yr for the associate)

### Training Cost ($)
Total out-of-pocket cost to enter the career. Use the most common/affordable pathway:
- Paid apprenticeships/academies: $0
- Certifications only: cost of cert program + exam fees
- Associate degrees: community college tuition (in-state)
- Does NOT include opportunity cost of foregone earnings during training

### Yr1 $ through Yr10 $
10 individual columns with the salary used for each year of the 10-year calculation.

- **Unpaid training years**: Yr1 is ALWAYS the start of the path. Set to `0` for full years spent in full-time unpaid school/training. Earning years shift forward accordingly. For example, a 2-year associate degree career: Yr1=$0, Yr2=$0, Yr3=first-year salary, Yr4–Yr10=subsequent years.
- **Paid training / Academies**: If a career has paid training (0 unpaid years) where the academy/training wage is significantly lower than the entry-level wage, and training lasts a fraction of the year (e.g., 6 months), blend the salaries for Yr1. For example, if academy pays $40k annualized for 6 months and post-graduation pays $60k annualized for 6 months, Yr1 = $50,000.
- **Ladder careers**: Manually set each earning year based on step/promotion research. When a promotion has a range of expected timing (e.g., "3–10 years to make Sergeant"), use the midpoint (e.g., Year 6.5 → round to Year 7). If unpaid training was fractional (e.g. 0.5), calculate the prorated first-year earning manually for that year (e.g. 50% of starting salary in Yr1).
- **Linear careers**: Earning years auto-filled by `calc_e10()` using linear interpolation. You must manually input the FULL annualized starting salary in the correct `Yr` column where they begin working (e.g., `Yr1 ($)` if 0 or 0.5 unpaid training, or `Yr3 ($)` if 2 years of unpaid training). `calc_e10()` will interpolate from that full starting salary to the median over the remaining years. If unpaid training is fractional (e.g., 0.5), `calc_e10()` will automatically prorate the first earning year down.

#### General 3% Growth Rule
**In any year where salary growth is not dictated by a published schedule or specific formula, assume a 3% annual increase to match inflation.** This applies specifically to:
- Years spent in a specific role on a ladder before jumping to the next step.
- Years *after* a career has hit the BLS median, up through Year 10.
- Training/developmental phases where specific step increases aren't documented (do NOT assume $10–20K annual jumps during training).

**Big salary jumps should only occur at documented milestone events:**
- Apprentice → Journeyman (trades): typically a 25–35% jump after 4–5 year apprenticeship
- Developmental → Certified (ATC): CPC certification brings significant raise, but developmental phases have incremental checkpoint raises over 2–4 years
- Patrol → Sergeant/Detective (law enforcement): promotion brings ~$10–15K bump after 5–8 years
- Probationary → Sworn (fire/police): modest bump ($2–4K) after 6–12 month probation
- Seniority-based (flight attendants): early years see only 3–6% annual increases; pay curve steepens at year 5+

**Reference pay structures by career type:**
| Career Type | Annual Increase During Training | Milestone Jump | Time to Median (or final jump) |
|---|---|---|---|
| Government step (police, fire) | $2–4K/year (step increases) | $10–15K at promotion | 8–10 years |
| Federal GS scale (CBP) | $6–15K/year (grade promotions GL-5→GS-12) | N/A (grade-based) | 4–5 years to GS-12 (Note: GS-12 far exceeds BLS median! Use the real GS-12 salary, don't artificially cap at median) |
| Trade apprenticeship (electrical, plumbing, HVAC) | 5–10% of journeyman/year | 25–35% at journeyman | 5–7 years |
| FAA ATC (ATSPP pay bands) | $8–17K/year during developmental | $20K at CPC certification | 7–9 years |
| Airline seniority (flight attendants) | $1.5–3K/year early; $4–5K/year mid | None (smooth curve) | 10+ years |

**A Note on the BLS Median:**
If a known pay ladder (like the federal GS scale or an established union apprentice-to-journeyman timeline) dictates that a worker will make *more* than the BLS median before Year 10, **use the actual higher ladder wage**. Do not artificially cap ladder careers at the BLS median if the real-world progression pays more.

### 10-Year Net Earnings ($)
`Sum(Yr1..Yr10) - Training Cost` — computed by `calc_e10()`.

### 10-Year Net Earnings Calculation
The exact year-by-year salary timeline used to compute the 10-Year Net Earnings figure.

- **Salary schedule/ladder careers**: List each year's salary showing the step/promotion that applies. When a promotion has a range of expected timing (e.g., "3–10 years to make Sergeant"), use the midpoint (e.g., Year 6.5 → round to Year 7).
- **Linear growth careers**: State the formula: `(Year1 + Median) / 2 × 10 - Training Cost = result`.


### 10-Year Net Earnings Calculation Model
Must include **two things**:

1. **Training description**: What the training/education is, how long it takes, and the cost structure. **Explicitly classify the initial training into one of three categories and explain how it maps to the Yr($) fields:**
   - **Paid Training (Employer pays trainee):** (e.g., apprenticeships, paid academies). The trainee earns a wage from day one. Do not set unpaid years; `Yr1 ($)` reflects this starting training wage. `Training Cost ($)` is typically $0.
   - **Free Training (No cost, but unpaid):** (e.g., unpaid internships, volunteer requirements). The training is free (`Training Cost ($)` = $0), but the time spent is uncompensated. Set the appropriate `Unpaid Training Years` (e.g., `0.5`, `1`), making the initial Yr($) fields `$0` or prorated.
   - **Student Pays (Tuition/out-of-pocket):** (e.g., associate degrees, certificates). The student pays for school (`Training Cost ($)` > $0) and does not earn a wage during that time. Set the appropriate `Unpaid Training Years`, making the initial Yr($) fields `$0` or prorated.
   If the career has multiple entry paths and the shorter path was used for the Yr columns, note which path was chosen.
2. **Earnings trajectory**: For salary schedule careers, describe the ladder steps and what impacts salary (e.g., facility level for ATC, certifications for police). For linear careers, note factors that can push above/below the estimate (overtime, specialization, setting).

**Example (ATC):** "1. Paid Training (Employer pays trainee): FAA Academy in Oklahoma City (3–5 months, paid from day one). 0 unpaid years. 2. 2–3 years of developmental training (AG→D1→D2→D3) with incremental raises. CPC certification ~Year 4 brings a major pay jump to the BLS median ($144,580), and salary continues to grow on the ATSPP pay bands."

**Example (Dental Hygienist, 2yr school):** "1. Student Pays (Tuition/out-of-pocket): 2–3 year CODA-accredited dental hygiene associate degree ($15K–$30K) required before earning. 2 years of $0 earnings during school. 2. Linear growth from ~$74K (entry-level) to BLS median $94,260 over the remaining 8 years."

**Example (Dental Assistants, OJT path):** "1. Paid Training (Employer pays trainee): Many states allow on-the-job training with no formal program. 0 unpaid years. 2. Salary grows linearly from ~$42K entry-level wage to BLS median $47,300 over 10 years."

### Difficulty Score
`High`, `Medium`, or `Low`

Factors to consider:
- **Training barriers**: Competitiveness of program admission (acceptance rates), length and rigor of training, licensing/certification exam difficulty and pass rates
- Competitiveness of hiring (hiring ratios, selection processes)
- Physical demands and danger
- Lifestyle demands (travel, irregular hours, emotional toll)

### Difficulty Score Explanation
Short explanation of what makes the career easy or hard to enter and stay in. Must address the difficulty of getting accepted into and completing the required training/education. Include specific barriers (program acceptance rates, exam pass rates, age limits, physical requirements, competitive selection processes).

### How to Get There
Step-by-step training pathway with costs at each step. Include:
- Specific program names/types and duration
- Exam names and fees
- Total estimated out-of-pocket cost
- Whether employer/union/government pays for training
- Alternative pathways if they exist (e.g., military route for aircraft mechanics)

**Example (ATC):** "FAA Academy in Oklahoma City: 3–5 months, paid federal employment from day one. After graduating, you're placed at a facility for on-the-job certification — typically 2–4 more years at increasing pay. The federal government covers everything."

### Job Market
Describe prospects for getting and keeping the job:
- BLS projected growth rate
- Number of annual openings (if notable)
- Current supply/demand dynamics (shortages, competition)
- Geographic considerations
- Factors affecting job security

**Example (ATC):** "2,200 openings per year. Rigorous FAA selection with historically high training washout rates; extreme mental demands and ongoing recertification; hard age-31 start cutoff."

### Pension
Describe retirement benefits if the job has a pension. Include:
- Type (defined-benefit, defined-contribution)
- Eligibility (years of service, age)
- Which employer types offer pensions vs. 401(k) only
- Union pension funds if applicable

**Example (Police Supervisor):** "Defined-benefit pension after 20 years — many departments allow retirement at 50."

If no pension is typical, say so and note what retirement options exist (401k, self-funded).

---

## calc_e10() Python Function

```python
def calc_e10(row: dict) -> dict:
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
        start_salary = int(float(start_salary_str.replace(',', ''))) if start_salary_str else 0

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

    yr_vals = [int(float(str(row.get(f'Yr{i+1} ($)', 0)).replace(',', ''))) for i in range(10)]
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
```

### Invariant
`10-Year Net Earnings ($)` must always equal `sum(Yr1..Yr10) - Training Cost`. The function enforces this.

Note: For ladder calculations, if the median is reached before Year 10, manually apply the 3% annual growth rule for the remaining years.

### When to use each type
| Type | When | Yr1–Yr10 set by |
|------|------|-----------------|
| `ladder` | Government pay scales, union step increases, trade apprenticeships, distinct promotion milestones | Human (manual research) |
| `linear` | Gradual unstructured wage growth | `calc_e10()` auto-interpolation |

---

## Research Process (per row)

1. **Web search** the career's training pathway, entry-level salary, and pay progression
2. **Determine calculation model**: salary ladder (government/union/trades) vs. linear growth
3. **Calculate 10-year net earnings** using the appropriate model
4. **Assess difficulty** based on entry barriers, training rigor, and working conditions
5. **Write all 10 fields** with specific, factual details (exam names, program costs, certification acronyms)

## Key Principles
- Use real credential names (NBCOT, ARDMS, NREMT, ASE, NABCEP, etc.)
- Include specific exam fees and program cost ranges
- Note union vs. non-union pathways where applicable
- Mention military-to-civilian pipelines where relevant
- For salary schedules, cite the actual step names (GS-5, Step 1, Journeyman, etc.)
- Overtime, shift differentials, and tips are mentioned but NOT included in the base calculation
