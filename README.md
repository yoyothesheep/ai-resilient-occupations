# AI-Resilient Occupations Scoring

A framework for identifying which jobs are resilient to AI displacement, scored across 10 key attributes that measure both defensive protections (why AI can't take over) and offensive opportunities (how AI can amplify expertise).

Final output is [hosted at this site](https://ai-proof-careers.com).


## Project Structure

```
.
├── README.md                          # This file
├── CLAUDE.md                          # Development instructions & pipeline reference
├── requirements.txt                   # Python dependencies
├── docs/
│   ├── 10-attributes.md              # The 10 attributes that drive resilience
│   ├── scoring-framework.md          # Complete scoring rubric & calculation logic
│   ├── career_page_spec.md           # Career page component specification
│   ├── tone_guide_career_pages.md    # Tone guide for career page prose
│   └── tone_guide_key_drivers.md     # Tone guide for key drivers text
├── data/
│   ├── input/
│   │   ├── All_Occupations_ONET.csv       # O*NET occupation data (raw)
│   │   ├── Employment Projections.csv     # BLS 2024-2034 employment projections
│   │   ├── SimpleJobTitles_altPathurl_*.csv  # SOC → AltPath URL + simplified titles
│   │   ├── anthropic/                     # Anthropic Economic Index data (not committed)
│   │   └── onet_db/                       # O*NET 30.2 Database files (Excel)
│   │       ├── Occupation Data.xlsx
│   │       ├── Sample of Reported Titles.xlsx
│   │       ├── Education Training and Experience.xlsx
│   │       ├── ETE Categories.xlsx
│   │       ├── Task Statements.xlsx       # 19,636 task statements mapped to occupation codes
│   │       └── Task Ratings.xlsx          # Task importance/frequency ratings
│   ├── intermediate/
│   │   └── All_Occupations_ONET_enriched.csv  # Enriched input for scoring
│   ├── output/
│   │   ├── ai_resilience_scores.csv       # Scored & ranked occupations (all 1,016)
│   │   └── occupation_cards.jsonl         # Per-occupation career page data
│   ├── career_clusters/                   # Adjacent roles & emerging roles data
│   │   ├── clusters.csv                   # Career cluster definitions
│   │   ├── cluster_branches.csv           # Cluster branch groupings
│   │   ├── cluster_roles.csv              # Individual roles within clusters
│   │   └── emerging_roles.csv             # AI-adjacent emerging career roles
│   ├── tiers_and_next_steps/              # Tier assignments & career guidance
│   └── top_no_degree_careers/             # Curated subset: top careers requiring no bachelor's
│       ├── ENRICHMENT_INSTRUCTIONS.md
│       ├── ai_resilience_scores-associates-5.5.csv
│       └── ai_resilience_scores-associates-5.5-enriched.csv
└── scripts/
    ├── enrich_onet.py                # Step 1: Enrich O*NET data with wages, education, projections
    ├── score_occupations.py          # Step 2: Score all occupations via Claude API
    ├── build_task_table.py           # Build task-level table with AEI metrics
    ├── generate_next_steps.py        # Generate tier assignments, next steps, career page data
    ├── adjacent_roles.py             # Generate adjacent/lateral career moves per occupation
    ├── generate_emerging_roles.py    # Generate emerging AI-adjacent roles
    ├── download_onet.py              # Download & manage O*NET database versions
    ├── download_economic_index.py    # Download Anthropic Economic Index from HuggingFace
    ├── patch_task_data.py            # Patch task data in career page files
    ├── test_scoring.py               # Quick test with 3 occupations
    └── test_enrichment.py            # Test enrichment pipeline
```

## Quick Start

### Prerequisites

Get your API key from [Anthropic Console](https://console.anthropic.com):
1. Go to Settings → API Keys
2. Create a new API key
3. Copy it (starts with `sk-ant-v1-`)

Install dependencies:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Set the environment variable:
```bash
export ANTHROPIC_API_KEY="sk-ant-v1-..."
```

Or add to `~/.zshrc` for persistence:
```bash
echo 'export ANTHROPIC_API_KEY="sk-ant-v1-..."' >> ~/.zshrc
source ~/.zshrc
```

### Full Pipeline

```bash
# Step 1: Enrich O*NET data
python3 scripts/enrich_onet.py

# Step 2: Score all occupations
python3 scripts/score_occupations.py

# Step 3: Build task table with AEI metrics
python3 scripts/build_task_table.py

# Step 4: Generate tiers, next steps, and career page data
python3 scripts/generate_next_steps.py

# Step 5: Generate adjacent roles & career clusters
python3 scripts/adjacent_roles.py

# Step 6: Generate emerging roles
python3 scripts/generate_emerging_roles.py
```

**Output:** `data/output/occupation_cards.jsonl` is the bridge between this pipeline and the [site repo](https://github.com/your-org/ai-resilient-occupations-site). Each `.tsx` career page embeds data from the corresponding card.

### Input Data

- **`data/input/All_Occupations_ONET.csv`** — downloaded from [O*NET Online — All Occupations](https://www.onetonline.org/find/all)
- **`data/input/Employment Projections.csv`** — BLS 2024-2034 employment projections from [data.bls.gov](https://data.bls.gov/projections/occupationProj)
- **`data/input/SimpleJobTitles_altPathurl_*.csv`** — maps SOC codes to AltPath URLs and simplified job titles
- **`data/input/onet_db/`** — O*NET 30.2 Database files (Excel), from [onetcenter.org](https://www.onetcenter.org/database.html). Licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
  - `Occupation Data.xlsx` — occupation codes, titles, and descriptions
  - `Sample of Reported Titles.xlsx` — real-world job titles mapped to occupations
  - `Education Training and Experience.xlsx` — education level requirements with survey percentages
  - `ETE Categories.xlsx` — category-to-label mapping for education levels
  - `Task Statements.xlsx` — task statements with O*NET-SOC codes; used to map AEI tasks to occupations
  - `Task Ratings.xlsx` — task importance and frequency ratings
- **`data/input/anthropic/`** — Anthropic Economic Index data (auto-downloaded from [HuggingFace](https://huggingface.co/datasets/Anthropic/EconomicIndex), release 2026-01-15). **Not committed to git.** To download:
  ```bash
  python3 scripts/download_economic_index.py
  ```
  Licensed under [CC BY](https://creativecommons.org/licenses/by/4.0/) (data) and [MIT](https://opensource.org/licenses/MIT) (code).

### Updating Source Data

**O*NET Database:**
```bash
python3 scripts/download_onet.py --check     # Check for newer version
python3 scripts/download_onet.py --version XX.Y  # Download & back up
python3 scripts/download_onet.py --sync      # Sync occupation list
```

**Anthropic Economic Index:** Check [HuggingFace](https://huggingface.co/datasets/Anthropic/EconomicIndex) for new releases, download to `data/input/anthropic/`, update `AEI_FILE` in `scripts/build_task_table.py`, and rerun the pipeline.

**BLS Employment Projections:** Download from [BLS](https://www.bls.gov/emp/tables/occupational-projections-and-characteristics.htm), replace `data/input/Employment Projections.csv` keeping the same column names, and rerun enrichment + scoring.

### Testing

Test the scoring pipeline with 3 sample occupations:
```bash
python3 scripts/test_scoring.py
```


## The Scoring Framework

### 10 Attributes

**Defensive (65% weight):** Why AI can't take over
- **A1** — Physical Presence & Dexterity Required
- **A2** — Trust is the Core Product
- **A3** — Novel, Ambiguous Judgment in High-Stakes Situations
- **A4** — Legal or Ethical Accountability
- **A5** — Deep Contextual Knowledge Built Over Time
- **A6** — Political & Interpersonal Navigation
- **A7** — Creative Work with a Genuine Point of View
- **A8** — Work That Requires Being Changed by the Experience

**Offensive (35% weight):** How AI amplifies these roles
- **A9** — Expertise Underutilized Due to Administrative/Volume Constraints
- **A10** — Downstream of Bottlenecks / Manages AI Systems

### AI-Proof Score (1.0-5.0)

```
Defensive Score = weighted average of A1-A8 (with attribute-specific weights)
Offensive Score = average of A9-A10
role_resilience_score  = (Defensive x 0.65) + (Offensive x 0.35)
```

**Special Rules:**
- **Ceiling Rule:** If A1 + A3 + A4 all <= 2, cap score at 2.5
- **Floor Rule:** If A9 or A10 scores 5, minimum score is 3.0

### Final Ranking (0.0-1.0)

The `final_ranking` is a weighted composite that combines the AI-proof score with labor market signals:

| Input | Weight | Normalization |
|-------|--------|---------------|
| `role_resilience_score` | 50% | Linear scale: `(score - 1) / 4` |
| Growth | 30% | See below |
| `Projected Job Openings` | 20% | Log-transform + min-max scale |

**Growth normalization** uses the best available data per occupation:
1. **`Employment Change, 2024-2034`** (preferred) — numeric percent change from BLS. Sign-preserving log transform applied, then min-max scaled to 0-1.
2. **`Projected Growth`** (fallback) — scraped category string from O*NET, mapped ordinally: Decline=0, Little/none=0.2, Slower=0.4, Average=0.6, Faster=0.8, Much faster=1.0.

See `docs/scoring-framework.md` for complete rubrics and calculation details.

## Output Format

### Main Dataset (`data/output/ai_resilience_scores.csv`)

| Column | Description |
|--------|-------------|
| `Job Zone` | O*NET Job Zone (1-5, reflects preparation level) |
| `Code` | O*NET/SOC occupation code |
| `Occupation` | Occupation title |
| `Data-level` | Indicates if row is a broad or detailed O*NET occupation |
| `url` | O*NET Online URL for the occupation |
| `Median Wage` | Wage string scraped from O*NET (e.g. "$39.27 hourly, $81,680 annual") |
| `Projected Growth` | Growth category scraped from O*NET |
| `Employment Change, 2024-2034` | Numeric BLS percent change; empty for specialty subcodes |
| `Projected Job Openings` | Projected openings 2024-2034 |
| `Education` | Top 2 education levels with survey percentages |
| `Top Education Level` | Education level with highest reporting percentage |
| `Top Education Rate` | Reporting percentage for top education level |
| `Sample Job Titles` | Real-world job titles for this occupation |
| `Job Description` | Short description of the role |
| `role_resilience_score` | 1.0-5.0 AI resilience score |
| `final_ranking` | 0.0-1.0 composite ranking (higher = better) |
| `key_drivers` | 2-3 sentence explanation of the score |
| `altpath url` | AltPath.org career page URL |
| `altpath simple title` | Plain-language job title |

### Occupation Cards (`data/output/occupation_cards.jsonl`)

One JSON object per line, per occupation. Contains all data needed to generate a career page: score, salary, growth, task-level AI data (automation/augmentation rates from Anthropic Economic Index), adjacent roles, emerging roles, how-to-adapt guidance, and sourced quotes.

### Top No-Degree Careers Subset (`data/top_no_degree_careers/`)

Filtered to `role_resilience_score >= 5.5` and `Top Education Level <= associate's`. The enriched file adds 10-year earnings projections, difficulty scores, training pathways, and job market analysis. See `data/top_no_degree_careers/ENRICHMENT_INSTRUCTIONS.md` for full schema.

## Configuration

Edit `scripts/score_occupations.py` to adjust:
- `BATCH_SIZE` — occupations per API call (default: 10)
- `SLEEP_SEC` — delay between batches (default: 2s)
- `START_BATCH` — resume from a specific batch number
- `MODEL` — Claude model to use (default: claude-opus-4-6)

## References

Framework synthesized from:
- Andrew Ng on task automation & institutional knowledge
- Yann LeCun on trust in human relationships
- Francois Chollet on genuine reasoning vs. pattern matching
- Jensen Huang on "HR for AI" roles
- Satya Nadella on human-AI collaboration
- Daron Acemoglu on task boundaries & automation risk
