---
name: generate-emerging-job-titles
description: Generate real-world job title aliases for O*NET occupations and merge them into ai_resilience_scores.csv. Use when adding a new cluster or when O*NET sample titles don't reflect how jobs are actually listed.
---

# Generate Emerging Job Titles Skill

Discovers real-world job titles that map to existing O*NET codes but don't appear in O*NET's Sample Job Titles. Writes to `data/emerging_roles/emerging_job_titles.csv` and syncs the `Emerging Job Titles` column in `data/output/ai_resilience_scores.csv`.

**Why this matters:** O*NET titles are bureaucratic ("Market Research Analysts and Marketing Specialists"). Job seekers search for "Social Media Manager" or "Content Strategist." These aliases power site search and career page discoverability.

---

## Commands

```bash
# Generate + merge for a cluster (recommended — run after career-clusters skill)
python3 scripts/generate_emerging_job_titles.py --cluster office-admin

# Single occupation
python3 scripts/generate_emerging_job_titles.py --code 13-1161.00

# Just re-sync CSV → scores (no API calls — use after manual edits to the CSV)
python3 scripts/generate_emerging_job_titles.py --merge-only

# All occupations (slow — use per cluster)
python3 scripts/generate_emerging_job_titles.py --all
```

Requires `ANTHROPIC_API_KEY`. Skips occupations that already have entries in `emerging_job_titles.csv`.

---

## What the script does

1. For each occupation, calls Claude with the O*NET title + existing Sample Job Titles
2. Claude returns 2–5 real-world aliases not already in the sample titles list
3. Appends new rows to `emerging_job_titles.csv`
4. Merges all entries into the `Emerging Job Titles` column in `ai_resilience_scores.csv`

---

## QA after generation

Review the new rows in `emerging_job_titles.csv`. For each title check:

1. **Real postings exist** — search LinkedIn Jobs for the title. Should have >50 postings in past 30 days. If not, delete the row.
2. **Title is specific** — "AI Specialist" is too generic. "AI Content Strategist" is acceptable.
3. **Mapping is accurate** — the title should genuinely describe work done under that O*NET code, not just sound related.

To delete a bad row: edit `emerging_job_titles.csv` directly, then run `--merge-only` to sync.

---

## Manual additions

To add a title manually (e.g. from your own research or the emerging roles research guide):

1. Add a row to `data/emerging_roles/emerging_job_titles.csv`:
   ```
   onet_code,job_title,notes
   13-1161.00,Social Media Manager,Manages brand social presence; closer to Marketing Manager scope
   ```
2. Run: `python3 scripts/generate_emerging_job_titles.py --merge-only`

---

## Cache behavior

The script skips any `onet_code` that already has at least one entry in `emerging_job_titles.csv`. To regenerate for a code, delete its rows from the CSV first, then re-run.

---

## Output

`data/emerging_roles/emerging_job_titles.csv` schema:

| Field | Description |
|---|---|
| `onet_code` | O*NET code the title maps to |
| `job_title` | Real-world title as it appears in job postings |
| `notes` | Why it maps here; what differs from the O*NET title |

---

## After this skill

```bash
python3 scripts/generate_next_steps.py --cluster <id>
python3 scripts/adjacent_roles.py --cluster <id>
```

Also: the `Emerging Job Titles` column in `ai_resilience_scores.csv` is now populated and available for site search and career page generation.