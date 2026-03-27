# Emerging Roles Research System

This directory contains the data and framework for continuous discovery of emerging AI-related occupations not yet captured by O*NET or government occupational taxonomies.

## Files & Structure

- **EMERGING_ROLES_SOURCES.csv** — Master source inventory by cluster; tracks tier (primary/secondary/tertiary), last checked date, hit rate, and status
- **emerging_roles_findings_YYYY-MM-DD.jsonl** — Weekly research outputs; one JSON object per role discovery/update
- **WEEKLY_EMERGING_ROLES_REPORT_YYYY-MM-DD.md** — Markdown summaries; high-level findings, source performance, pipeline candidates
- **emerging_roles_pipeline_candidates.csv** — Roles validated and ready for enrichment/scoring pipeline integration

## Workflow

### Weekly Research (Mondays 9 AM)
Automated task: `emerging-roles-research` runs every Monday at 9 AM, rotating across all 7 career clusters on a 6-week schedule.

**Cluster Rotation (6-week cycle):**
- Week 1: AI Engineering & Alignment + Applied AI / Enterprise AI
- Week 2: AI Infrastructure & Infra-adjacent + Design & AI
- Week 3: Data, Annotation & Labeling + Product Management & AI
- Week 4: Marketing & AI Growth + Law & Compliance / AI
- Weeks 5-6: Secondary/tertiary sources + deep-dives on high-signal roles

For each cluster:
1. Scan primary sources in **EMERGING_ROLES_SOURCES.csv**
2. Capture job postings, companies, and role characteristics
3. Validate signal strength (50+ postings = exploratory; 100+ = emerging; multi-company adoption = strong)
4. Write findings to `emerging_roles_findings_YYYY-MM-DD.jsonl`
5. Generate `WEEKLY_EMERGING_ROLES_REPORT_YYYY-MM-DD.md`
6. Identify and flag pipeline candidates

### Monthly Synthesis (Manual)
- Review 4 weeks of findings
- Deduplication: merge variant titles into role families
- Trend analysis: which roles are accelerating vs. plateauing?
- Update source performance in **EMERGING_ROLES_SOURCES.csv**
- Archive deprecated roles

### Quarterly Deep-Dives (Manual)
- Select 3–5 emerging roles from "pipeline candidates"
- Pull task statements, salary data, education requirements
- Run through enrichment pipeline
- Prepare for site integration

## Output Formats

### emerging_roles_findings_YYYY-MM-DD.jsonl

Each line is a JSON object:

```json
{
  "role_title": "Context Engineer",
  "cluster": "AI Engineering & Alignment",
  "status": "emerging",
  "first_spotted": "2025-11-15",
  "last_updated": "2026-03-26",
  "signal_strength": "strong",
  "confidence": 0.85,
  "job_posting_count_3m": 187,
  "companies_hiring": ["Anthropic", "Google DeepMind", "Hugging Face"],
  "sources": [
    {
      "source_name": "Anthropic careers",
      "source_url": "https://careers.anthropic.com/jobs/context-engineer",
      "last_checked": "2026-03-26",
      "matches": 2
    },
    {
      "source_name": "LinkedIn",
      "source_url": "https://linkedin.com/...",
      "last_checked": "2026-03-26",
      "matches": 45
    }
  ],
  "example_posting": {
    "title": "Context Engineer",
    "company": "Anthropic",
    "posting_url": "https://careers.anthropic.com/jobs/context-engineer",
    "posting_date": "2026-03-01",
    "snippet": "Responsible for designing and optimizing context window strategies for large language models. Work with product teams to maximize model utility..."
  },
  "core_responsibilities": [
    "Design and optimize context window strategies",
    "Develop techniques for efficient token usage",
    "Evaluate and benchmark context approaches",
    "Collaborate with alignment and product teams"
  ],
  "typical_background": [
    "ML engineering or research background",
    "Strong Python and data handling skills",
    "Experience with LLM APIs or fine-tuning",
    "Familiarity with prompt engineering"
  ],
  "notes": "Often conflated with Prompt Engineer but distinct role. Focuses on structural/systemic context optimization rather than individual prompt crafting. Growing rapidly as models scale.",
  "ready_for_pipeline": false,
  "pipeline_readiness_notes": ""
}
```

### WEEKLY_EMERGING_ROLES_REPORT_YYYY-MM-DD.md

Template:

```markdown
# Weekly Emerging Roles Report
**Week of:** March 24–30, 2026
**Clusters Scanned:** AI Engineering & Alignment, Applied AI / Enterprise AI
**Clusters Next Week:** AI Infrastructure, Design & UX for AI

## Summary

- **Emerging roles discovered:** 5
- **Experimental roles (weak signal):** 2
- **Deprecated roles:** 0
- **Total under active tracking:** 18

## High-Confidence Emerging Roles

### Context Engineer
- **Signal strength:** Strong
- **Confidence:** 0.85
- **Job postings (3m):** ~187 across LinkedIn, Indeed, Glassdoor
- **Companies:** Anthropic (2), Google DeepMind (3), Hugging Face (1)
- **Status:** Ready for pipeline
- **Notes:** Core emerging role in frontier AI labs; distinct from Prompt Engineer

### Design Engineer (AI)
- **Signal strength:** Emerging
- **Confidence:** 0.72
- **Job postings (3m):** ~64
- **Companies:** Figma, Framer, Replit
- **Status:** Monitoring
- **Notes:** New design specialization; blurs design + engineering

## Source Performance This Week

| Cluster | Source | Tier | Hit Rate | Status |
|---------|--------|------|----------|--------|
| AI Eng | Anthropic careers | Primary | High | Active |
| AI Eng | HuggingFace Jobs | Primary | High | Active |
| Applied AI | Y Combinator Job Board | Primary | High | Active |
| Applied AI | LinkedIn searches | Primary | High | Active |

**High performers:** Anthropic careers page (2 new roles), LinkedIn searches (direct signals)
**Low performers:** None
**Sources to replace:** None this week

## Pipeline Candidates

Roles ready for enrichment/scoring:
1. Context Engineer
2. (Additional roles as applicable)

## Next Steps

- **Data pull:** Download task statements and salary data for Context Engineer by April 2
- **Enrichment:** Run Context Engineer through pipeline by April 9
- **Site prep:** Draft career page structure by April 16

## Notes

- Job title ambiguity: "Design Engineer" used across AI, traditional software, and hardware. Filtering by AI-native companies only.
- Source rotation: Next week focus Data Annotation cluster; note if any primary sources are down.
```

### emerging_roles_pipeline_candidates.csv

```csv
role_title,cluster,confidence,job_posting_count_3m,added_date,readiness_stage,priority
Context Engineer,AI Engineering & Alignment,0.85,187,2026-03-26,ready_for_enrichment,high
Design Engineer,Design & UX for AI,0.72,64,2026-03-26,monitoring,medium
Forward Deploy Engineer,AI Engineering & Alignment,0.78,145,2026-03-19,ready_for_enrichment,high
```

## Key Definitions

**Signal Strength:**
- `strong` — 100+ postings across multiple companies, 3+ month history, consistent appearance
- `emerging` — 50–100 postings, 2–3 companies, growing visibility
- `weak` / `experimental` — <50 postings, concentrated in 1–2 companies, exploratory

**Confidence Score (0.0–1.0):**
- 0.80+ — Multiple sources, high posting volume, multi-company adoption, 3+ month history
- 0.60–0.79 — 2+ sources, moderate posting volume, 1–3 companies, 1–3 months history
- <0.60 — Single source or weak signal; exploratory only

**Pipeline Readiness Stages:**
- `ready_for_enrichment` — Validated role, 80+ confidence, ready for task statement / salary research
- `monitoring` — Good signals but need more data; revisit in 2–4 weeks
- `exploratory` — Weak signals; mark for monthly review

## Extending the System

**To add a new source:**
1. Add row to `EMERGING_ROLES_SOURCES.csv` with cluster, tier (primary/secondary/tertiary), and notes
2. Test for 2 weeks (include in research scans)
3. If high hit rate, promote to primary tier; if low, archive or move to tertiary

**To add a new cluster:**
1. Define cluster characteristics (what makes a role belong here?)
2. Identify and test 8–12 sources
3. Document high-signal roles already visible in those sources
4. Add cluster section to this README and to the research guide

**To integrate with scoring pipeline:**
1. Move role from `pipeline_candidates` to the main `ai_resilience_scores.csv` workflow
2. Create O*NET mapping (or assign Job Zone + O*NET family)
3. Pull enrichment data (tasks, salary, education, examples)
4. Run `score_occupations.py` to generate resilience score
5. Create `.tsx` career page data file for the site
6. Link from `emerging_roles_findings.jsonl` with `ready_for_pipeline: true`

