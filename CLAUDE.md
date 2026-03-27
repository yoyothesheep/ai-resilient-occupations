# AI-Resilient Occupations Data

Scoring framework for AI job resilience across 1,000+ O*NET occupations. Site: ai-proof-careers.com

## Project Structure

This repo is the **data pipeline**. The end product is the site at `../ai-resilient-occupations-site` (Next.js). Data flows one way: pipeline → site data files. Never edit site data files by hand when the root cause is in the pipeline.

```
ai-resilient-occupations-data/   ← you are here (pipeline + scores)
ai-resilient-occupations-site/   ← Next.js site (../ai-resilient-occupations-site)
```

### Full Pipeline (data → site)

```
enrich_onet.py
  → data/intermediate/All_Occupations_ONET_enriched.csv

score_occupations.py
  → data/output/ai_resilience_scores.csv          (all 1,016 occupations scored)

generate_next_steps.py
  → data/tiers_and_next_steps/

adjacent_roles.py
  → data/career_clusters/

generate_emerging_roles.py
  → data/career_clusters/emerging_roles.csv
  → data/output/occupation_cards.jsonl            (per-occupation career page data)

  ↓ manual step: copy/adapt into site
../ai-resilient-occupations-site/src/data/careers/<slug>.tsx   (one file per career page)
```

**Occupation cards** (`data/output/occupation_cards.jsonl`) are the bridge between pipeline and site. Each `.tsx` career page in the site embeds data from the corresponding card. When regenerating emerging roles or adjacent roles, update both the JSONL and the corresponding `.tsx` file.

## Key Files

- `data/input/` — raw O*NET + BLS source files
- `data/intermediate/All_Occupations_ONET_enriched.csv` — enriched input for scoring
- `data/output/ai_resilience_scores.csv` — final scored dataset (all occupations)
- `data/top_no_degree_careers/` — curated subset: top careers requiring ≤ associate's degree
- `scripts/score_occupations.py` — Claude API scoring pipeline
- `scripts/enrich_onet.py` — enriches O*NET data (currently being refactored)
- `docs/scoring-framework.md` — full scoring methodology and rubrics

## Pipeline

```
enrich_onet.py → [data/intermediate/] → score_occupations.py → data/output/ai_resilience_scores.csv
```

**Note: `enrich_onet.py` is currently under active refactoring — do not assume it's stable.**

### Commands

```bash
source venv/bin/activate
python3 scripts/enrich_onet.py        # Step 1: enrich (refactoring in progress)
python3 scripts/score_occupations.py  # Step 2: score all occupations
python3 scripts/test_scoring.py       # Quick test with 3 occupations
```

Requires `ANTHROPIC_API_KEY` env var.

## Scoring Summary

- **10 attributes**: A1–A8 defensive (65%), A9–A10 offensive (35%)
- **`role_resilience_score`**: 1.0–5.0
- **`final_ranking`**: 0.0–1.0 composite (score 50% + growth 30% + openings 20%)
- Special rules: ceiling cap at 2.5 if A1+A3+A4 all ≤ 2; floor at 3.0 if A9 or A10 = 5

See `docs/scoring-framework.md` for full rubric.

## Updating Source Data

### Anthropic Economic Index

**File:** `data/input/anthropic/aei_raw_claude_ai_*.csv`
**Source:** [Hugging Face — Anthropic/EconomicIndex](https://huggingface.co/datasets/Anthropic/EconomicIndex)

When a new release is available:
1. Download the new CSV from Hugging Face and place it in `data/input/anthropic/`
2. Update the filename reference in `scripts/build_task_table.py` (look for `AEI_FILE`)
3. Rerun the task table build: `python3 scripts/build_task_table.py`
4. Rerun enrichment and scoring: `python3 scripts/enrich_onet.py && python3 scripts/score_occupations.py`
5. Update the date/version note in `data/input/anthropic/README_ECONOMIC_INDEX.md`

The current file covers **2025-11-13 to 2025-11-20** (release 2026-01-15). New releases are periodic — check Hugging Face for updates.

### BLS Employment Projections

**File:** `data/input/Employment Projections.csv`
**Source:** [BLS Occupational Outlook — Employment Projections](https://www.bls.gov/emp/tables/occupational-projections-and-characteristics.htm)

BLS publishes a new 10-year projection cycle every two years (next: 2025–2035, expected late 2025 or 2026). When updated:
1. Download the Excel table from BLS and export to CSV
2. Replace `data/input/Employment Projections.csv` — **keep the same column names** (the pipeline depends on: `Occupation Code`, `Employment Change, 2024-2034`, `Occupational Openings, 2024-2034 Annual Average`, `Median Annual Wage 2024`, `Typical Entry-Level Education`)
3. Update column name references in `scripts/enrich_onet.py` if BLS renamed any columns (check the header row)
4. Rerun the full pipeline

### O*NET Database

**Files:** `data/input/onet_db/*.xlsx` (Task Statements, Task Ratings, Occupation Data, Education Training and Experience, Sample of Reported Titles)
**Current version in use:** O*NET 30.2 (February 2026)
**Source:** [O*NET Resource Center — Database](https://www.onetcenter.org/database.html) · [Release history](https://www.onetcenter.org/db_releases.html)
**Download script:** `python3 scripts/download_onet.py --version 30.2` (backs up existing files automatically)

O*NET releases ~4 times a year (Feb, May, Aug, Nov). When updated:
1. Run `python3 scripts/download_onet.py --check` to see if a newer version is available
2. Run `python3 scripts/download_onet.py --version XX.Y` to download and back up
3. Run `python3 scripts/download_onet.py --sync` to update `All_Occupations_ONET.csv` with new/removed codes
   - New codes are added with their Job Zone; they'll be enriched and scored in subsequent steps
   - Removed codes are kept so their scores aren't lost; enrichment falls back to the scrape cache
4. Rerun enrichment (scrapes new codes, updates cache): `python3 scripts/enrich_onet.py`
5. Score new codes and rerank all: `python3 scripts/score_occupations.py`
   - Already-scored codes are skipped; only new codes get API calls
   - `--rerank` flag merges existing scores with fresh enrichment data (no API calls)

## Active Work

See `ECONOMIC_INDEX_INTEGRATION_PLAN.md` for the current multi-phase project integrating Anthropic Economic Index task-level data into scoring and career page generation.

## Career Page Data Format

A career page requires **two files**:

1. **Data file:** `../ai-resilient-occupations-site/src/data/careers/<slug>.tsx` — exports the `CareerData` object
2. **Route file:** `../ai-resilient-occupations-site/app/career/<slug>/page.tsx` — registers the Next.js route

Without the route file the page 404s. Template for the route file:
```tsx
import CareerDetailPage from "@/components/CareerDetailPage";
import { myOccupationData } from "@/data/careers/my-occupation";

export default function MyOccupationPage() {
  return <CareerDetailPage data={myOccupationData} />;
}
```

When generating or updating `.tsx` career data files in `../ai-resilient-occupations-site/src/data/careers/`, follow these conventions exactly. The layout component (`CareerDetailPage.tsx`) drives all rendering — the data file only supplies content.

### CareerData fields

- `title`, `score` (0–100), `salary`, `openings`, `growth` — header stats
- `description` — one concise sentence shown in the page header. Not a paragraph.
- `jobTitles[]` — 3–6 example titles, shown as rectangular chips
- `keyDrivers: ReactNode` — 2–4 sentences explaining why the role got this score. No em dashes.
- `risks: { stat, statLabel, statColor, body: ReactNode }` — `stat` is a short number or %, `statLabel` is a brief phrase (5–8 words max) that sits inline beside the number on one line. Keep it short.
- `opportunities: { stat, statLabel, statColor, body: ReactNode }` — same structure
- `howToAdapt: { alreadyIn: ReactNode, thinkingOf: ReactNode }`
- `taskData: TaskRow[]` — include all tasks; nulls are fine and filtered by the layout
- `careerCluster?: CareerClusterNode[]` — `score` is 1.0–5.0 scale
- `sources: Source[]` — see source conventions below

### Source conventions

`Source` fields: `id` (e.g. `"src-1"`), `name` (publisher), `title` (article title), `date` (e.g. `"Dec 2025"`), `url`.

- Use `id` as the anchor target for inline footnotes: `<sup><a href="#src-1">[1]</a></sup>`
- Career map `CareerClusterNode.stat` also needs `sourceName`, `sourceTitle`, `sourceDate` — the layout merges these into the unified numbered sources list automatically
- **Verify every URL resolves before generating the file.** Dead links must be replaced, not left in.
- Never use em dashes (`—`) anywhere — use a hyphen (`-`) or rewrite the sentence

### Page title & meta description

Each career page must have a custom `usePageMeta` title and description.

**Title template:** `[Job Title] Career Guide: AI Risk, Salary & Next Steps`

**Meta description template:** `[Job Title] scores [score]/100 on AI resilience — [tier label] territory. See which tasks AI already automates, how salaries are holding, and which adjacent roles offer better protection.`

Tier labels: Strong (65+), Solid (50–64), Shifting (35–49), Exposed (20–34), Risky (0–19). Use lowercase in the description.

### Style rules

- No em dashes anywhere in data files
- Prose fields (`body`, `keyDrivers`, `fit`, `steps`) use plain sentences — no marketing language
- `steps[]` are concrete and actionable (specific course names, tools, certifications — not "learn Python")
- `stat` + `statLabel` in risks/opportunities must come from a cited source in `sources[]`

---

## Working Principles

- **Always make fixes generalizable.** When fixing a data or formatting issue for one occupation, fix it in the script so it applies to all. Never patch individual records manually when the root cause is in the pipeline.

## generate_next_steps.py Workflow

`generate_next_steps.py` is interactive: it prints a prompt and reads JSON from stdin. When running it, **paste the prompt output directly into this Claude Code conversation and respond with JSON here**. Do not launch a separate Claude.ai tab or spawn an API agent. Claude Code IS Claude — respond to the prompt inline, write the JSON to `data/output/occupation_cards.jsonl` directly.

## Top No-Degree Careers Sub-Dataset

Subset filtered to `role_resilience_score ≥ 5.5` and `Top Education Level ≤ associate's`.

- Base: `data/top_no_degree_careers/ai_resilience_scores-associates-5.5.csv`
- Enriched: `data/top_no_degree_careers/ai_resilience_scores-associates-5.5-enriched.csv`
- Schema + methodology: `data/top_no_degree_careers/ENRICHMENT_INSTRUCTIONS.md`
