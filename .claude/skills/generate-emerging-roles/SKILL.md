---
name: generate-emerging-roles
description: Generate, QA, and update emerging AI-adjacent career roles for an occupation or cluster. Covers running the script, verifying job postings are real, and deciding when to regenerate vs. use cache.
---

# Generate Emerging Roles Skill

Generates AI-native career pivot paths for occupations based on automation risk tier. Writes to `data/emerging_roles/emerging_roles.csv` and updates `occupation_cards.jsonl`.

## Risk tier → role count

| `role_resilience_score` | Tier | Roles generated |
|---|---|---|
| ≤ 2.5 | Fragile / Volatile | 4 |
| 2.5–4.0 | Moderate | 2 |
| > 4.0 | Solid / Strong | 0 (skip) |

---

## Step 1 — Run the script

```bash
# Single occupation
python3 scripts/generate_emerging_roles.py --code 43-4051.00

# Full cluster
python3 scripts/generate_emerging_roles.py --cluster office-admin

# All occupations (slow — use per cluster instead)
python3 scripts/generate_emerging_roles.py --all
```

The script:
1. Looks up `role_resilience_score` → determines N
2. Checks `data/emerging_roles/emerging_roles.csv` for cached rows — uses them if found
3. Otherwise calls Claude API: generates N candidates with `title`, `description`, `core_tools`, `stat`, `search_query`
4. Calls Claude again per candidate: generates `fit` + `steps`
5. Constructs job search URLs from title:
   - LinkedIn: `https://www.linkedin.com/jobs/search/?keywords=<encoded_title>`
   - Indeed: `https://www.indeed.com/jobs?q=<encoded_title>`
   - TrueUp: `https://www.trueup.io/search?q=<encoded_title>`
6. Writes rows to `emerging_roles.csv`
7. Updates `emergingCareers` in `occupation_cards.jsonl`

---

## Step 2 — QA each generated role

For every role produced, verify:

**1. Is this a real job title with active postings?**

Search LinkedIn Jobs for the title. If fewer than ~50 postings in past 30 days across the US, the title is either too niche, too early, or made up. Flag it.

**2. Does the title match the occupation's actual skill set?**

The role must be reachable from the source occupation — shared tools, tasks, or domain. A Data Entry Clerk → "AI Trainer" is plausible. A Data Entry Clerk → "ML Research Scientist" is not.

**3. Is the stat credible and sourced?**

The `stat_text` must come from a real, named source (`stat_source`, `stat_url`). Check that the URL resolves and the stat is actually in the article. If not, replace the stat — do not leave a dead link or misattributed claim.

**4. Are the steps concrete?**

`steps_json` must name specific tools, courses, or certifications — not "learn Python" or "gain experience." Each step should be actionable within 3–6 months.

---

## Step 3 — Handle failures

**Role has no real job postings:**
Delete the row from `emerging_roles.csv` and regenerate for that occupation with `--code XX-XXXX.XX`. The script will call Claude fresh (no cache hit) and produce a new candidate. Repeat until you have N roles with verified postings.

**Stat URL is dead:**
Find a replacement stat from an authoritative source (LinkedIn Economic Graph, Stack Overflow Developer Survey, WEF Future of Jobs, BLS, professional association reports). Update `stat_text`, `stat_source`, `stat_title`, `stat_date`, `stat_url` in the CSV row directly, then re-run `generate_emerging_job_titles.py` and the `--update-cards` step to propagate.

**Role is too generic (e.g. "AI Specialist"):**
Edit the `emerging_title` in the CSV to be more specific (e.g. "AI-Assisted Data Coordinator"), update `description` and `search_query` accordingly. Re-check job postings.

---

## Step 4 — Propagate to occupation cards

After QA:

```bash
python3 scripts/generate_emerging_roles.py --cluster <id> --update-cards
```

This reads `emerging_roles.csv` and writes `emergingCareers` into the relevant entries in `occupation_cards.jsonl`. Run this after any edits to the CSV.

---

## Output fields per row

| Field | Description |
|---|---|
| `onet_code` | Source occupation O*NET code |
| `emerging_title` | Job title as it appears in real postings |
| `description` | 2–3 sentences: what the role does, who it's for |
| `core_tools` | Comma-separated tools/technologies (3–5) |
| `stat_text` | One-sentence stat with number (e.g. "AI-assisted roles grew 38%...") |
| `stat_source` | Publisher name |
| `stat_title` | Article or report title |
| `stat_date` | Month + year (e.g. "Jan 2024") |
| `stat_url` | Direct URL — must resolve |
| `search_query` | Suggested job board search string (quoted title + year) |
| `job_search_url` | Auto-constructed LinkedIn URL |
| `fit` | One sentence: why this occupation's skills transfer |
| `steps_json` | JSON array of 2–3 concrete steps |
| `experience_level` | 1=Entry, 2=Mid, 3=Senior, 4=Lead, 5=Executive |

---

## Cache behavior

The script checks `emerging_roles.csv` before calling the API. If a row exists for `(onet_code, emerging_title)`, it reuses it. To force regeneration, delete the relevant rows from the CSV first.

---

## After this skill

Once emerging roles are verified:

```bash
python3 scripts/generate_emerging_job_titles.py   # Sync Emerging Job Titles column in scores CSV
python3 scripts/generate_next_steps.py --cluster <id>  # Stage 6a: occupation cards
python3 scripts/adjacent_roles.py --cluster <id>        # Stage 6b: careerCluster
```