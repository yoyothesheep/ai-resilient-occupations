# Emerging Roles Research - Quick Start

## What This Does

Automated weekly discovery of AI-related occupations not yet in O*NET that show strong job market signals.

## Key Files

| File | Purpose | Owner |
|------|---------|-------|
| `EMERGING_ROLES_RESEARCH_GUIDE.md` (root) | Full framework, cluster definitions, research prompts | Reference |
| `EMERGING_ROLES_SOURCES.csv` | Master source inventory by cluster | Update quarterly |
| `emerging_roles_findings_YYYY-MM-DD.jsonl` | Weekly research output (one JSON per role) | Auto-generated |
| `WEEKLY_EMERGING_ROLES_REPORT_YYYY-MM-DD.md` | Markdown summary; findings + next steps | Auto-generated |
| `emerging_roles_pipeline_candidates.csv` | Roles ready for enrichment/scoring | Manual curation |
| `emerging_roles_findings_SAMPLE.jsonl` | Example output format | Reference |

## Automated Workflow

**Scheduled Task:** `emerging-roles-research`
- **When:** Every Monday at 9 AM
- **Rotation:** 3 clusters per week (AI Eng → AI Infra → Data)
- **Output:** Findings JSONL + Weekly Report
- **Duration:** ~30 min per run

### What Happens Each Monday

1. Task reads `EMERGING_ROLES_RESEARCH_GUIDE.md` for cluster definitions
2. On a 6-week rotation, scans 2 clusters per week + secondary sources:
   - **Week 1:** AI Engineering & Alignment + Applied AI
   - **Week 2:** AI Infrastructure + Design & AI
   - **Week 3:** Data & Annotation + Product Management
   - **Week 4:** Marketing & Growth + Law & Compliance
   - **Weeks 5-6:** Deep-dives and cross-cluster validation
3. Scans primary sources from `EMERGING_ROLES_SOURCES.csv` for selected clusters
4. Validates job posting counts (50+ = exploratory; 100+ = emerging; multi-company = strong)
5. Writes findings to `emerging_roles_findings_YYYY-MM-DD.jsonl`
6. Generates `WEEKLY_EMERGING_ROLES_REPORT_YYYY-MM-DD.md`
7. Identifies pipeline candidates

You'll get a notification when the task completes.

## Manual Checkpoints

### Monthly (end of month)
- Review 4 weeks of findings
- Consolidate variant titles into role families
- Update `EMERGING_ROLES_SOURCES.csv` with hit rates
- Archive deprecated roles
- Update `emerging_roles_pipeline_candidates.csv`

### Quarterly (every 3 months)
- Select 3-5 pipeline candidates for deep enrichment
- Pull task statements, salary data, education
- Prepare for scoring pipeline integration
- Draft career page content

## Running Custom Research

Want to research emerging roles between scheduled runs?

```bash
# In the Scheduled tasks sidebar, find "emerging-roles-research"
# Click "Run now" to trigger immediately
```

## Integration with Scoring Pipeline

When a role is ready to score:

1. Add to `emerging_roles_pipeline_candidates.csv` with `readiness_stage: ready_for_enrichment`
2. Create `data/input/emerging_roles/<role_title>.csv` with enrichment data (tasks, salary, education)
3. Run `python3 scripts/score_occupations.py --emerging` to score
4. Output goes to `data/output/ai_resilience_scores.csv`
5. Generate `.tsx` career page from `data/output/occupation_cards.jsonl`

## Key Definitions

**Signal Strength:**
- `strong` — 100+ postings, 3+ months, multi-company
- `emerging` — 50-100 postings, 2-3 companies, 2 months history
- `weak` — <50 postings, 1 company, early-stage

**Confidence Score:**
- 0.80+ — Ready for pipeline
- 0.60-0.79 — Monitor for 2-4 weeks
- <0.60 — Exploratory; revisit monthly

**Readiness Stage:**
- `ready_for_enrichment` — Validated, 80+ confidence
- `monitoring` — Good signals but need more data
- `exploratory` — Weak signals; mark for review

## Troubleshooting

**No findings generated?**
- Check if sources are live (some careers pages go down)
- Verify LinkedIn searches still return results
- Check `EMERGING_ROLES_SOURCES.csv` for dead URLs

**Too many false positives?**
- Tighten the 100+ posting threshold per cluster
- Add more companies to validation (1 company = weak signal)
- Review sample role definitions in guide

**Source needs updating?**
- Edit `EMERGING_ROLES_SOURCES.csv` directly
- Mark old sources as `status: archived`
- Test new sources for 2 weeks before promoting to primary

## Questions?

Refer to `EMERGING_ROLES_RESEARCH_GUIDE.md` for full methodology, cluster definitions, and source curation rationale.

