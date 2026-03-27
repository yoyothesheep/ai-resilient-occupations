# Data Schema

Defines the structure and purpose of every output file. The CSV is the scoring index. The JSONL file is the site-facing product.

## Output file strategy

- **`ai_resilience_scores.csv`** — flat index for sorting, filtering, leaderboards. No long-form text except `key_drivers`.
- **`occupation_cards.jsonl`** — pipeline file. One JSON object per line, one occupation per line. Easy to regenerate one occupation, run in batches, and audit with grep. This is the working format during Phase 5–9.
- **`occupation_cards.json`** — site export. Converted from JSONL as a final build step. Either a single JSON array (for client-side indexing) or split into per-file by the site build process if Next.js static generation requires it.

The site should never read the CSV directly. It consumes `occupation_cards.json`.

---

## 1. `data/output/ai_resilience_scores.csv`

The main scoring index. One row per occupation. Used for sorting, filtering, leaderboards, and analysis. No long-form text beyond `key_drivers`.

| Column | Type | Description |
|--------|------|-------------|
| `Code` | string | O*NET occupation code (e.g. `29-2061.00`) |
| `Occupation` | string | Official O*NET occupation title |
| `altpath simple title` | string | Human-readable simplified title |
| `Job Zone` | int | O*NET Job Zone 1–5 (proxy for complexity) |
| `Data-level` | string | O*NET data reliability level |
| `Top Education Level` | string | Most common education level for this occupation |
| `Top Education Rate` | float | % of workers with that education level |
| `Median Wage` | float | BLS median annual wage (USD) |
| `Projected Growth` | string | BLS projected growth rate label |
| `Employment Change, 2024-2034` | int | Projected net employment change |
| `Projected Job Openings` | int | Projected annual job openings |
| `role_resilience_score` | float | AI resilience score, 1.0–5.0 (higher = more resilient) |
| `final_ranking` | float | Composite ranking, 0.0–1.0 (score 50% + growth 30% + openings 20%) |
| `key_drivers` | string | 2–3 sentence plain-English explanation of what drives the score |
| `url` | string | O*NET occupation detail URL |
| `altpath url` | string | Alternative path / simplified career page URL |
| `Sample Job Titles` | string | Common job titles for this occupation |
| `Job Description` | string | O*NET occupation description |
| `Education` | string | Full education breakdown string |

---

## 2. `data/output/occupation_cards.jsonl` → `data/output/occupation_cards.json`

Pipeline working file is `occupation_cards.jsonl` — one JSON object per line, one occupation per line. A final export step converts it to `occupation_cards.json` (single array) for the site. The site build may further split into per-file if needed by Next.js static generation.

Each occupation object contains everything the site needs to render a full career page. Fields marked with `*` are repeated from the CSV for self-contained lookup — the site should not need to cross-reference.

```jsonc
{
  // Identity *
  "onet_code": "29-2061.00",
  "occupation_title": "Licensed Practical and Licensed Vocational Nurses",
  "simple_title": "LPN / Licensed Practical Nurse",

  // Scores *
  "role_resilience_score": 3.6,
  "final_ranking": 0.74,
  "tier": {
    "number": 3,
    "label": "..."           // tier label from tier system
  },

  // Attribute scores (from score_log.txt)
  "a_scores": {
    "A1_physical_presence": 4,
    "A2_trust_core_product": 4,
    "A3_novel_judgment": 3,
    "A4_legal_accountability": 4,
    "A5_deep_org_context": 3,
    "A6_political_navigation": 2,
    "A7_creative_pov": 1,
    "A8_changed_by_experience": 3,
    "A9_expertise_underutilized": 4,
    "A10_downstream_ai_mgmt": 4
  },

  // Labor market *
  "median_wage": 55000,
  "projected_growth": "Average",
  "annual_openings": 56000,
  "top_education_level": "Postsecondary nondegree award",

  // AEI metrics
  "ai_task_coverage_pct": 9.1,
  "weighted_automation_pct": 53.8,
  "weighted_augmentation_pct": null,
  "weighted_task_success_pct": 78.2,
  "weighted_speedup_factor": 7.7,
  "low_data_confidence": true,    // true if ai_task_coverage_pct < 20%

  // Key drivers (existing)
  "key_drivers": "...",

  // Career page content (Phase 5)
  // Inline citation markers like [1], [2] refer to entries in the sources array below.
  // sections[] is optional — present only when the content warrants named subsections.
  // Section titles are free-form and will vary by occupation (not predefined).
  "risks": {
    "summary": "Very little risk from AI. The core responsibilities — observing patients, measuring vital signs, administering medications — are done in person and require expert-level clinical judgment. AI is not expected to replace these in the near future. BLS projects 3% job growth through 2034 [1].",
    "sections": []               // optional; empty array or omitted if no subsections needed
  },
  "opportunities": {
    "summary": "AI is starting to take on the administrative and documentation side of nursing [2]. For LPNs, that means less paperwork and more time on the clinical work that defines the role.",
    "sections": [                // optional; titles are free-form
      {
        "title": "Using AI tools in clinical settings",
        "body": "Nurses who get comfortable with AI-assisted charting and remote monitoring tools early will be better positioned as these become standard [2]."
      }
    ]
  },

  // Task highlights (derived from task table)
  // tasks[]: unified list of top tasks by weight, for the "How AI Is Changing This Role" chart.
  // Includes all tasks (AEI-matched or not). Sorted by task_weight descending.
  // automation_pct and augmentation_pct are null for tasks with no AEI coverage.
  // onet_task_count < 100 tasks excluded. Suggested max: top 10 by weight.
  "tasks": [
    { "task_text": "Write supporting code for Web applications or Web sites.", "task_weight": 23.9, "automation_pct": 39.5, "augmentation_pct": 9.7 },
    { "task_text": "Design, build, or maintain Web sites...",                   "task_weight": 22.7, "automation_pct": 45.1, "augmentation_pct": 4.4 },
    { "task_text": "Back up files from Web sites to local directories...",      "task_weight": 20.1, "automation_pct": null,  "augmentation_pct": null }
  ],

  // Convenience subsets derived from tasks[] — kept for prose generation in Phase 5.
  // Do not use these for the chart; use tasks[] instead.
  "top_automated_tasks": [
    // Top tasks by weight where automation_pct > 0 and onet_task_count >= 100. Max 3.
    { "task_text": "Record food and fluid intake and output", "automation_pct": 53.8, "task_weight": 20.9 }
  ],
  "top_augmented_tasks": [
    // Top tasks by weight where augmentation_pct > 0 and onet_task_count >= 100. Max 3.
    { "task_text": "...", "augmentation_pct": 0.0, "task_weight": 0.0 }
  ],
  "untouched_high_priority_tasks": [
    // Top tasks by weight where in_aei = false. Max 3.
    { "task_text": "Observe patients, charting and reporting changes in patients' conditions...", "task_weight": 25.7 },
    { "task_text": "Measure and record patients' vital signs...", "task_weight": 24.8 },
    { "task_text": "Administer prescribed medications or start intravenous fluids...", "task_weight": 24.5 }
  ],

  // Related careers (from adjacent_roles.py)
  // Up to 6 related careers per occupation, sorted by score descending.
  "relatedCareers": [
    {
      "code":         "29-1141.00",   // O*NET code
      "title":        "Registered Nurses",
      "relationship": "progression",  // "progression" | "specialization" | "lateral" | "adjacent"
      "score":        78,             // final_ranking × 100, rounded
      "openings":     "189,100",      // annual projected openings, formatted
      "growth":       "+5%",          // employment change % or BLS label
      "fit":          "...",          // one-sentence Feynman-style explanation
      "steps":        ["NCLEX-RN exam", "LPN-to-RN bridge program (ADN or BSN)", "..."]
      // 2–3 concrete steps to make the move: credentials, courses, certs, or practical actions.
      // Anchored by curated cluster_branches.csv notes when a direct branch exists.
    }
  ],
  // relationship values:
  //   "progression"    — step up in credential, scope, or seniority (from cluster_branches or level diff)
  //   "specialization" — same level, narrower focus or specific setting
  //   "lateral"        — different track or field, similar standing
  //   "adjacent"       — shares task overlap but no direct cluster path (methods 2 or 3)

  // Sources — enumerated to match inline [n] markers in risks/opportunities prose
  "sources": [
    { "id": 1, "label": "BLS Occupational Outlook Handbook — LPN", "url": "https://www.bls.gov/ooh/healthcare/licensed-practical-and-licensed-vocational-nurses.htm" },
    { "id": 2, "label": "American Nurses Association — AI in Nursing Practice (2025)", "url": "https://ojin.nursingworld.org/table-of-contents/volume-30-2025/number-2-may-2025/artificial-intelligence-in-nursing-practice-decisional-support-clinical-integration-and-future-directions/" }
  ]
}
```

---

## 3. `data/intermediate/onet_economic_index_task_table.csv`

Full task-level table. 18,796 rows, one per O*NET task. Used to generate occupation-level metrics and task highlights in the JSON cards. Not consumed directly by the site.

| Column | Type | Description |
|--------|------|-------------|
| `onet_code` | string | O*NET occupation code |
| `task_id` | string | O*NET task identifier |
| `task_text` | string | Full task description |
| `freq_score` | float | Frequency score from O*NET Task Ratings (FT scale, weighted avg) |
| `importance_score` | float | Importance score from O*NET Task Ratings (IM scale, 1–5) |
| `task_weight` | float | `freq_score × importance_score`; fallback = occupation mean (global mean 16.97) |
| `weight_source` | string | `rated` or `mean_fallback` |
| `in_aei` | bool | Whether this task matched an AEI task |
| `match_type` | string | `exact`, `fuzzy`, or null |
| `onet_task_count` | int | Number of AEI conversations matching this task (n=) |
| `onet_task_pct` | float | % of AEI conversations for this occupation matching this task |
| `automation_pct` | float | % of matching conversations classified as automation |
| `augmentation_pct` | float | % of matching conversations classified as augmentation |
| `task_success_pct` | float | % of matching conversations where task was completed |
| `ai_autonomy_mean` | float | Mean AI autonomy rating (1–5) across matching conversations |
| `speedup_factor` | float | `(human_only_time_hours × 60) / human_with_ai_time_minutes` |

---

## 4. `data/intermediate/onet_economic_index_metrics.csv`

Occupation-level AEI rollups. 923 occupations. Weighted means over AEI-matched tasks only.

| Column | Type | Description |
|--------|------|-------------|
| `onet_code` | string | O*NET occupation code |
| `total_tasks` | int | Total O*NET tasks for this occupation |
| `aei_tasks` | int | Number of tasks matched to AEI |
| `ai_task_coverage_pct` | float | `aei_tasks / total_tasks × 100` |
| `weighted_automation_pct` | float | Weighted mean automation % across AEI tasks |
| `weighted_augmentation_pct` | float | Weighted mean augmentation % across AEI tasks |
| `weighted_task_success_pct` | float | Weighted mean task success % across AEI tasks |
| `weighted_ai_autonomy_mean` | float | Weighted mean AI autonomy score across AEI tasks |
| `weighted_speedup_factor` | float | Weighted mean speedup factor across AEI tasks |

---

## Notes

- **Low data confidence**: set `low_data_confidence: true` in JSON when `ai_task_coverage_pct < 20%`. The site should display a caveat for these occupations.
- **Null AEI metrics**: 343 occupations have no AEI coverage at all (not in O*NET v30.2 task match). Their AEI fields will be null in both CSV and JSON.
- **A-scores source**: parsed from `data/output/score_log.txt` during Phase 5 JSON generation. Not currently in the scored CSV.
- **task_weight fallback**: 845 tasks across 86 occupations had no Task Ratings in O*NET v30.2. These use occupation mean weight (global mean 16.97 for fully-unrated occupations). Tracked via `weight_source = mean_fallback`.
