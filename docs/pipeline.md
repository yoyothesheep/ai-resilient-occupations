# Data Pipeline

**Site:** ai-proof-careers.com | **Repo:** ai-resilient-occupations-data

Scores 1,016 O*NET occupations for AI resilience. Generates career page data for the Next.js site at `../ai-resilient-occupations-site`.

Related docs: `docs/scoring-framework.md` · `docs/data-schema.md` · `docs/tone_guide_career_pages.md`

---

## Two Tracks

### Track A — Baseline (full corpus, run on data updates)

Runs on every O*NET release, BLS update, or AEI release. Produces complete scored dataset.

```bash
python3 scripts/enrich_onet.py        # Stage 1
python3 scripts/score_occupations.py  # Stage 2 (can run in parallel with Stage 3)
python3 scripts/build_task_table.py   # Stage 3 (can run after Stage 1)
```

### Track B — Career page enrichment (per-cluster, on demand)

Expensive (API calls). Run per cluster when building new career/industry pages. Not run on full corpus.

```bash
# 1. Populate cluster files (use career-clusters skill)
# 2. Generate emerging roles + merge job title aliases
python3 scripts/generate_emerging_roles.py --cluster <cluster_id>
python3 scripts/generate_emerging_job_titles.py
# 3. Generate occupation cards
python3 scripts/generate_next_steps.py --cluster <cluster_id>   # initial cards
python3 scripts/adjacent_roles.py --cluster <cluster_id>        # add careerCluster
python3 scripts/generate_emerging_roles.py --cluster <cluster_id> --update-cards  # add emergingCareers
```

---

## Stage Reference

### Stage 1 — Enrich
**Script:** `scripts/enrich_onet.py`  
**Reads:** `data/input/All_Occupations_ONET.csv`, `data/input/onet_db/*.xlsx`, `data/input/Employment Projections.csv`, `data/input/SimpleJobTitles_altPathurl_*.csv`, `data/intermediate/onet_scrape_cache.json`  
**Writes:** `data/intermediate/All_Occupations_ONET_enriched.csv`, `data/intermediate/onet_scrape_cache.json`  
**Owns:** wages, education, BLS growth, job titles, descriptions, AltPath URLs, simple title. Scrape cache is resumable — only fetches missing/new occupations.

### Stage 2 — Score
**Script:** `scripts/score_occupations.py`  
**Reads:** `data/intermediate/All_Occupations_ONET_enriched.csv`, `docs/scoring-framework.md`  
**Writes:** `data/output/ai_resilience_scores.csv`, `data/output/score_log.txt`  
**Owns:** A1–A10 attribute scores, `role_resilience_score` (1.0–5.0), `final_ranking` (0.0–1.0), `key_drivers`. Already-scored codes are skipped; use `--rerank` to merge new enrichment without API calls.

### Stage 3 — Build Task Table
**Script:** `scripts/build_task_table.py`  
**Reads:** `data/input/onet_db/Task Statements.xlsx`, `data/input/onet_db/Task Ratings.xlsx`, `data/intermediate/economic_index_tasks_raw.csv`, `data/intermediate/economic_index_tasks_mapped.csv`  
**Writes:** `data/intermediate/onet_economic_index_task_table.csv` (18,796 rows), `data/intermediate/onet_economic_index_metrics.csv` (923 occupation rollups)  
**Owns:** task-level AEI metrics. Re-run when AEI data updates.

#### Task weight formula

`task_weight = freq_score × importance_score`

- **freq_score** — from `Task Ratings.xlsx`, Scale "Frequency of Task" (FT), categories 1–7 (1=Yearly or less → 7=Hourly or more). Computed as `sum(category × pct_respondents)` across all 7 categories.
- **importance_score** — from `Task Ratings.xlsx`, Scale "Importance" (IM), 1–5, `Data Value` directly.
- 845 tasks across 86 occupations use `mean_fallback` (occupation mean rated weight, or global mean 16.97 if entirely unrated). `weight_source` column flags these.

#### Task table schema (`onet_economic_index_task_table.csv`)

| Column | Description |
|---|---|
| `onet_code` | O*NET-SOC code |
| `task_id` | O*NET task ID |
| `task_text` | Full task description |
| `freq_score` | Weighted avg frequency (1–7). Null for 29 occupations missing Task Ratings (new in v30.2). |
| `importance_score` | Task importance (1–5). Null for same 29 occupations. |
| `task_weight` | `freq_score × importance_score` if rated; occupation mean rated weight if unrated. Never null. |
| `weight_source` | `rated` or `mean_fallback` |
| `in_aei` | Whether task appears in AEI observed data |
| `match_type` | `exact`, `fuzzy`, or null (not in AEI) |
| `onet_task_count` | Claude conversations involving this task (global, 1 week) |
| `onet_task_pct` | % of all Claude conversations this task represents |
| `automation_pct` | % of classifiable usage showing automation patterns (directive + feedback_loop) |
| `augmentation_pct` | % showing augmentation patterns (learning + task_iteration + validation) |
| `task_success_pct` | % of conversations where AI successfully completed the task |
| `ai_autonomy_mean` | Mean AI autonomy score 1–5 (higher = more delegation) |
| `speedup_factor` | `(human_only_time_hours × 60) / human_with_ai_time_minutes`. Median ~11.5x globally. **Note:** human_only_time is in hours, human_with_ai_time is in minutes — confirmed in aei_v4_appendix.pdf. |

**Evidence strength:** Weight recommendation confidence by `onet_task_count`. Tasks with <100 conversations are weak signal; >1,000 are strong.

#### Occupation metrics schema (`onet_economic_index_metrics.csv`)

All weighted metrics use `sum(task_weight × metric) / sum(task_weight)` over AEI-covered tasks only.

| Column | Description | Phase 6 scoring use |
|---|---|---|
| `total_tasks` | Total O*NET tasks for occupation | — |
| `aei_tasks` | Tasks observed in AEI | — |
| `ai_task_coverage_pct` | `aei_tasks / total_tasks × 100` | Low = less signal confidence; don't overstate risk |
| `weighted_automation_pct` | Weighted mean automation % | High → downward pressure on resilience score |
| `weighted_augmentation_pct` | Weighted mean augmentation % | High → raise A10 (Manages/Directs AI) |
| `weighted_task_success_pct` | Weighted mean AI success rate | High → lower A3 (Novel Judgment) |
| `weighted_ai_autonomy_mean` | Weighted mean autonomy score (1–5) | High → raise A10; AI operates independently |
| `weighted_speedup_factor` | Weighted mean speedup factor | Context for next steps narrative — magnitude of productivity shift |

#### AEI extraction audit findings

**speedup_factor:** Original script had a unit mismatch — `human_only_time` is in hours, `human_with_ai_time` in minutes. Fixed formula: `(hours × 60) / minutes`. Corrected median = 11.5x (range 2.2x–103x), matching README's stated 9–12x range.

**Task mapping:** 2,917/3,168 tasks matched (92.1%). 251 unmatched due to O*NET version drift — AEI was built against a pre-v30.2 version. Unmatched tasks include high-signal ones (e.g. "develop instructional materials" = 10,035 conversations). Fuzzy match threshold = 95; spot-checked and sound.

**automation_pct global average:** Our task-level unweighted avg = 37.9%; Anthropic's stated 43% is conversation-weighted (high-volume software tasks have higher automation rates). Expected difference — use task-level averages consistently.

### Stage 4 — Build Career Clusters (Track B)
**Skill:** `.claude/skills/career-clusters/SKILL.md`  
**Writes:** `data/career_clusters/clusters.csv`, `data/career_clusters/cluster_roles.csv`, `data/career_clusters/cluster_branches.csv`  
**Owns:** curated career ladder topology — which occupations belong to which family, levels, and transitions (including cross-family). Run when adding a new industry group.

### Stage 5 — Emerging Roles & Job Title Aliases (Track B)
**Scripts:** `scripts/generate_emerging_roles.py`, `scripts/generate_emerging_job_titles.py`  
**Writes:** `data/emerging_roles/emerging_roles.csv` (AI-adjacent career pivots per occupation), updates `data/output/ai_resilience_scores.csv` (`Emerging Job Titles` column)  
**Owns:** emerging AI-era job titles generated per occupation based on risk tier (≤2.5 → 4 roles, 2.5–4.0 → 2 roles, >4.0 → skip). Job title aliases map real-world titles (e.g. "Social Media Manager") to existing O*NET codes.

### Stage 6 — Occupation Cards (Track B)
Three scripts write to `data/output/occupation_cards.jsonl` in sequence. Each is idempotent for its own fields.

**6a — `scripts/generate_next_steps.py`**  
Writes initial card: `score`, `salary`, `taskData`, `taskIntro`, `risks`, `opportunities`, `howToAdapt`, `sources`.  
Interactive mode (single occupation): reads prompt from stdin — paste response into Claude Code conversation.  
Batch mode (default): calls Claude API directly.

**6b — `scripts/adjacent_roles.py`**  
Adds `careerCluster` field. Three matching methods in priority order: 1) curated cluster data (`cluster_roles.csv` + `cluster_branches.csv` — branch `notes` injected as ground truth into Claude prompt), 2) Jaccard task overlap (threshold 0.15, weighted by `task_weight`), 3) SOC prefix similarity. Max 6 related careers per occupation. Per (source, target) pair, calls Claude to generate `fit` (one Feynman-style sentence) and `learn` (2–3 concrete skills/credentials).

**6c — `scripts/generate_emerging_roles.py --update-cards`**  
Adds `emergingCareers` field from `data/emerging_roles/emerging_roles.csv`.

### Stage 7 — Publish Career Page (Track B)
**Skill:** `aeo-content-writer` in `../ai-resilient-occupations-site/.claude/skills/`  
**Requires:** Stage 6 complete for the occupation (`occupation_cards.jsonl` has entry with `careerCluster` + `emergingCareers`)  
**Writes:** two files in the site repo:
- `src/data/careers/<slug>.tsx` — CareerData object
- `app/career/<slug>/page.tsx` — Next.js route (missing = 404)

**After writing:** run `publish-checklist` skill in site repo to validate SEO, URLs, TypeScript, and sitemap before deploying.

---

## Key Files

| File | Source | Purpose |
|---|---|---|
| `data/intermediate/All_Occupations_ONET_enriched.csv` | Stage 1 | Enriched occupation data, input to scoring |
| `data/output/ai_resilience_scores.csv` | Stage 2 | All 1,016 occupations scored; main dataset |
| `data/output/score_log.txt` | Stage 2 | A1–A10 per occupation (parsed by Stage 6a) |
| `data/intermediate/onet_economic_index_task_table.csv` | Stage 3 | 18,796 task rows with AEI metrics + weights |
| `data/intermediate/onet_economic_index_metrics.csv` | Stage 3 | 923 occupation-level AEI rollups |
| `data/career_clusters/clusters.csv` | Stage 4 | Career cluster definitions |
| `data/career_clusters/cluster_roles.csv` | Stage 4 | Occupation → cluster membership + level |
| `data/career_clusters/cluster_branches.csv` | Stage 4 | From→to career transitions |
| `data/emerging_roles/emerging_roles.csv` | Stage 5 | Emerging AI-era pivot roles per occupation |
| `data/emerging_roles/emerging_job_titles.csv` | Stage 5 | Real-world job title aliases for O*NET codes |
| `data/output/occupation_cards.jsonl` | Stage 6 | Per-occupation career page data (bridge to site) |

---

## AEI Background

The **Anthropic Economic Index (AEI)** maps anonymized Claude usage to 3,170 O*NET task statements, showing which tasks AI is helping with, how often, and whether in automation or augmentation mode (43%/57% global split).

AEI tasks are verbatim O*NET task statements — enabling near-exact string matching (92.1% match rate). 251 tasks unmatched due to O*NET version drift (AEI uses pre-v30.2 wording).

**Important caveat:** AEI tracks which tasks appear in Claude conversations, not which occupations use Claude. Interpret as: *how AI-integrated are the tasks that define this occupation* — not *how much do workers use AI*.

Automation vs. augmentation classification:
- **Automation** — `directive` + `feedback loop` patterns: AI does the task
- **Augmentation** — `learning` + `task iteration` + `validation` patterns: human in loop

---

## Deferred / Future Work

| Item | Status | Notes |
|---|---|---|
| Score adjustment (Phase 6) | Deferred | Adjust `role_resilience_score` based on weighted_automation_pct. Proposal to be written to `docs/score-adjustment-proposal.md` — do not modify scores yet. |
| QA & validation (Phase 8) | Not started | Spot-check scores, next steps, adjacent roles across sample |
| Adjacent roles via embeddings (Phase 7b) | Future | Replace Jaccard with weighted cosine similarity on task text embeddings. Three signals: 1) task text similarity (primary) — embed all O*NET task texts, compute weighted cosine per occupation pair using task_weight as weights (cannot use task IDs — they're unique per occupation, must use text); 2) sample job title overlap (secondary) — shared titles are a flag, not a primary signal; 3) SOC family match (tertiary/tiebreaker). Top N by combined score → Claude generates fit + learn per pair. |
| `generate_next_steps.py` full batch mode | Partial | Interactive stdin kept as fallback; batch API mode is default |

---

## Source Data Updates

### O*NET Database
Current: v30.2 (Feb 2026). Releases ~4×/year.  
`python3 scripts/download_onet.py --check` → check for newer version  
`python3 scripts/download_onet.py --version XX.Y` → download + backup  
Then rerun Track A.

### BLS Employment Projections
Current: 2024–2034 cycle. Next: 2025–2035 (expected late 2026).  
Replace `data/input/Employment Projections.csv` — keep column names identical. Rerun Track A.

### Anthropic Economic Index
Current: 2025-11-13 to 2025-11-20 (release 2026-01-15).  
Source: [Hugging Face — Anthropic/EconomicIndex](https://huggingface.co/datasets/Anthropic/EconomicIndex)  
On new release: download CSV → update `AEI_FILE` in `scripts/build_task_table.py` → rerun Stage 3 → rerun Stage 6.
