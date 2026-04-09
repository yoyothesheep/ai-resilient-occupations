# Economic Index Integration Plan

**Date:** 2026-03-17

**Related docs:** `docs/data-schema.md` (output file structure) · `docs/scoring-framework.md` (scoring methodology) · `docs/tone_guide_career_pages.md` (output tone) · `docs/tone_guide_key_drivers.md` (key_drivers tone)

---

## What We're Doing & Why

We score 1,016 occupations across 10 attributes for AI resilience (see `docs/scoring-framework.md`). The scores are currently based on Claude's assessment of each occupation's characteristics — but they lack grounding in **real-world data about how AI is actually being used**.

**O*NET Task Level data**
We're pulling in O*NET's task level data to better estimate the frequency, importance, and relevance of each occupation's collection of tasks. We'll augment Claude's assessment with this mapping.

The **Anthropic Economic Index (AEI)** dataset (release 2026-01-15) contains anonymized Claude usage data mapped to 3,170 O*NET occupational tasks — showing which tasks AI is helping with, how often, with what success rate, and in what pattern (automation vs. augmentation). This is the most direct available signal of AI's real footprint on professional work.

**Key insight:** AEI task descriptions are verbatim O*NET task statements. O*NET publishes a `Task Statements.xlsx` file (19,636 rows) mapping every task text to an occupation code. This means we can do near-exact string matching instead of fuzzy guessing — solving the mapping quality problem.

### Goals (in priority order)

**Goal 1 — Customized occupation recommendations** *(highest priority)*
Currently next steps are generic tier-based text. Replace with occupation-specific guidance:
- a) Which top tasks (by importance/frequency) are being automated vs. augmented
- b) How to position yourself: lean into augmentation, protect the non-automatable, use AI to handle the automatable

**Goal 2 — Verifiable sources for recommendations**
Every recommendation should be traceable to real data — AEI task counts, O*NET task frequency, collaboration patterns. No pure Claude opinion.

**Goal 3 — Adjust scoring based on important tasks**
If high-frequency, high-importance tasks for an occupation are already being automated, that should move the score. Low-importance tasks being automated/augmented should have minimal effect. Weight by task frequency × importance from O*NET Task Ratings.

**Goal 4 — Identify adjacent roles**
Use task-level overlap between occupations to surface roles with similar AI exposure profiles. Pairs with the career families work. Adjacent roles also feed into forward-looking recommendations — if your high-automation tasks are disappearing, which adjacent role do your remaining augmented + non-automatable skills point toward?

**Goal 5 — Forward-looking recommendations** *(lowest priority)*
Based on theoretical LLM capabilities (Eloundou et al. arXiv:2303.10130): which tasks aren't yet observed in AEI but are theoretically feasible — i.e. what's coming next for this occupation. Combined with Goal 4: if those incoming-automation tasks are core to the current role, the forward-looking recommendation surfaces the adjacent role (from Goal 4) whose skill profile best matches what remains after that automation lands.

---

## Current Status

| Phase | Task | What & Why | Enables Goals | Status |
|-------|------|------------|---------------|--------|
| 0 | Metric design & methodology | Define what we're measuring and how before writing any code — task_weight formula, 5 AI status categories, scoring adjustment rules. | Foundation | ✅ Complete |
| 1 | Download EconomicIndex data | Pull raw AEI CSV (458k rows) from Hugging Face. Source of all observed AI usage signals. | Foundation | ✅ Complete |
| 2a | Extract tasks + intersection facets | Pivot the raw AEI long-format data into one row per task with all metrics: usage count, automation %, augmentation %, success rate, autonomy score, speedup factor. This is the clean task-level AEI dataset everything else builds on. | Foundation | ✅ Complete — unit fix applied, audit verified |
| 2b | Map AEI tasks → O*NET occupation codes | AEI tasks are verbatim O*NET task statements, so we exact-match them against O*NET's Task Statements file to find which occupation(s) each task belongs to. A task can map to multiple occupations. | Foundation | ✅ Complete — 2,917/3,168 tasks mapped (92.1%), 673 occupations. 251 unmatched due to O*NET version drift (AEI uses pre-v30.2 wording). |
| 3 | Build task table + occupation-level rollups | Join the full O*NET task universe (v30.2) with AEI data. Adds task_weight per task and rolls up weighted AEI metrics per occupation. Produces both the task-level table and the occupation-level metrics file. | Foundation for all | ✅ Complete — 18,796 task rows, 923 occupation rollups, all audits pass |
| 4 | Join with enriched dataset | Attach occupation-level AEI metrics to the main scored dataset (all 1,016 occupations). Occupations with no AEI coverage get nulls. | Data in place | ✅ Complete — 923/1,016 occupations matched; 93 NaN (mostly military + catch-all codes). Output: All_Occupations_ONET_enriched_aei.csv |
| 5 | Generate custom next steps | For each occupation, use task-level data to write specific, data-backed guidance: which important tasks are being automated, which to lean into, which to protect. Replaces generic tier text. | Goal 1, 2 | ✅ Script created — batch review in progress |
| 6 | Score adjustment | Adjust role_resilience_score up/down based on how much of the occupation's important task weight is already automated. | Goal 3 | Not started |
| 7 | Adjacent roles | Surface related roles with fit/learn guidance. 7a: hardcoded config + Claude generation ✅. 7b: similarity scoring via embeddings (future). | Goal 4 | ✅ Phase 7a complete |
| 8 | QA & validation | Spot-check scores, next steps, and adjacent roles across a sample of occupations. Verify no regressions vs. current output. | — | Not started |

---

## Phase 0: Metric Design

### Anthropic's Methodology (from arXiv:2503.04761 + AEI docs)

Anthropic maps Claude usage to occupations using this approach:
1. Classify each conversation against O*NET task descriptions
2. For each occupation, weight task-level metrics by **fraction of time spent on each task** (from O*NET Task Ratings)
3. Fully automated patterns receive **full weight**; augmentative patterns receive **half weight**
4. Result: "observed exposure" per occupation — what fraction of their actual work tasks show Claude usage

**Automation vs. Augmentation** (from AEI collaboration facet):
- **Automation** (`automation_pct`): `directive` + `feedback loop` patterns — AI does the task, human sets goal
- **Augmentation** (`augmentation_pct`): `learning` + `task iteration` + `validation` patterns — human in loop, AI assists
- Global split: 43% automation, 57% augmentation (arXiv 2503.04761)

**Important caveat:** AEI data tracks which tasks appear in Claude conversations, not which occupations use Claude. A conversation tagged "design, build, or maintain web sites" could be anyone — not necessarily a Web Developer. Anthropic's own documentation warns against inferring occupational employment from this data. The right interpretation is: **how AI-integrated are the tasks that define this occupation**, not **how much do workers in this occupation use AI**.

---

### Key Design Principle: Keep Task-Level Detail

The goals require task-level outputs, not just occupation-level aggregates. Goal 1 (custom recommendations) needs to name specific tasks and their status. Aggregating to a single occupation-level number loses exactly the information we need.

**The primary output of Phase 3 is a task-level table** — one row per (occupation × task) with importance weight + AI status. Occupation-level aggregates for scoring (Goal 3) are derived from this table, not the other way around.

---

### Task Importance Weight

Each task gets a single importance weight used for ranking and scoring:

`task_weight = freq_score × importance_score`

- **freq_score**: from `Task Ratings.xlsx`, Scale "Frequency of Task" (FT), categories 1–7
  - 1 = Yearly or less → 7 = Hourly or more
  - Computed as: `sum(category × pct_respondents)` across all 7 categories
- **importance_score**: from `Task Ratings.xlsx`, Scale "Importance" (IM), 1–5, use `Data Value` directly

This weight determines how much a task matters for scoring (Goal 3) and which tasks to feature in recommendations (Goal 1). Low-weight tasks that happen to be automated/augmented don't move the needle.

---

### Task-Level AI Metrics 

Raw continuous metrics are preserved at the task level and rolled up weighted by `task_weight` at the occupation level.

**Per-task metrics (from AEI, null if not in AEI):**

| Metric | Source | What it signals |
|--------|--------|-----------------|
| `automation_pct` | `onet_task::collaboration` | % of observed usage showing automation patterns (directive + feedback_loop). Higher = more AI substitution. |
| `augmentation_pct` | `onet_task::collaboration` | % showing augmentation patterns (learning + task_iteration + validation). Higher = human still in loop. |
| `task_success_pct` | `onet_task::task_success` | % of conversations where AI successfully completed the task. Higher = AI reliably handles it. |
| `ai_autonomy_mean` | `onet_task::ai_autonomy` | Mean autonomy score 1–5. Higher = AI operates with less human direction. |
| `speedup_factor` | time facets | `(human_only_time_hours × 60) / human_with_ai_time_minutes`. Higher = more time saved. |

**Evidence strength (for Goal 2):** Weight recommendation confidence by `onet_task_count`. Tasks with <100 conversations are weak signal; tasks with >1,000 are strong signal. Surface count in citations.

**Note on tasks not in AEI:** Tasks absent from AEI cannot be reliably classified as "resilient" vs "not yet automated" from data alone. The Phase 5 prompt instructs Claude to use structural reasoning (physical presence, legal accountability, etc.) rather than absence-of-signal to identify durable tasks.

---

### Occupation-Level Metrics (derived from task table, for Goal 3)

Rolled up weighted by `task_weight` — no binning, raw continuous metrics:

| Metric | How computed | Possible Scoring Use |
|--------|-------------|----------------------|
| `weighted_automation_pct` | `sum(task_weight × automation_pct) / sum(task_weight)` over AEI tasks | High → downward pressure on resilience score — core work is being automated |
| `weighted_augmentation_pct` | `sum(task_weight × augmentation_pct) / sum(task_weight)` over AEI tasks | Neutral/slight positive — human still in loop; may raise A10 |
| `weighted_task_success_pct` | `sum(task_weight × task_success_pct) / sum(task_weight)` over AEI tasks | High → lower A3 (Novel Judgment) — AI reliably handles these tasks |
| `weighted_ai_autonomy_mean` | `sum(task_weight × ai_autonomy_mean) / sum(task_weight)` over AEI tasks | High → raise A10 (Manages/Directs AI) — AI operates with less direction |
| `weighted_speedup_factor` | `sum(task_weight × speedup_factor) / sum(task_weight)` over AEI tasks | Context for next steps narrative — magnitude of productivity shift |
| `ai_task_coverage_pct` | `aei_tasks / total_tasks × 100` | Low = less signal confidence; high = well-observed occupation |

**Scoring adjustment logic (Goal 3) — thresholds TBD after data exploration:**
- High `weighted_automation_pct` → downward pressure on resilience score
- High `weighted_task_success_pct` → downward pressure on A3 (Novel Judgment)
- High `weighted_ai_autonomy_mean` → upward signal on A10 (Manages/Directs AI)
- Low `ai_task_coverage_pct` → reduce confidence in any adjustment

---

### Adjacent Role Similarity (for Goals 4 + 5)

For each pair of occupations, compute a weighted task overlap score:

`similarity = cosine(task_weight_vector_A, task_weight_vector_B)`

Where each occupation is represented as a vector of task_weights across the full O*NET task universe (zero for tasks not in that occupation). Cosine similarity captures both which tasks overlap AND how important they are.

Adjacent roles serve two purposes:
- **Goal 4**: "Similar AI exposure profile" — occupations with high overlap that have better resilience scores are natural pivots
- **Goal 5**: "Where your remaining skills point" — after the "not yet" tasks automate, the adjacent role whose task vector best matches the occupation's *remaining* (augmented + resilient) tasks is the forward-looking recommendation

---

---

## Phase 1: Data Extraction

**Download EconomicIndex data from HuggingFace and save locally.**

- **Source:** `Anthropic/EconomicIndex` release 2026-01-15 → `aei_raw_claude_ai_2025-11-13_to_2025-11-20.csv` (90 MB)
- **Destination:** `data/input/anthropic/`
- **Scripts:** `scripts/download_economic_index.py` (created)

---

## Phase 2a: Task Extraction + Intersection Facets

**Extract all O*NET task metrics from EconomicIndex in one pass (global level).**

All facets live in the same raw file. Intersection facets use `task_text::subcategory` format in `cluster_name`.

**Script:** `scripts/extract_economic_index.py`

**Process:**
1. Load raw AEI CSV, filter to `geography == 'global'`
2. Extract base `onet_task` facet → count + pct per task
3. Extract `onet_task::collaboration` → split on `::`, sum automation patterns (directive, feedback_loop) and augmentation patterns (learning, task_iteration, validation) per task
4. Extract `onet_task::task_success` → `yes` category pct per task
5. Extract `onet_task::ai_autonomy` → mean autonomy score per task
6. Extract `onet_task::human_only_time` + `onet_task::human_with_ai_time` → speedup_factor per task
7. Merge all on task_text, exclude 'none'/'not_classified'

**Output: `data/intermediate/economic_index_tasks_raw.csv`**

| Column | Type | Description |
|--------|------|-------------|
| `task_text` | string | O*NET task description (verbatim from AEI) |
| `onet_task_count` | int | Claude conversations involving this task (global, 1 week) |
| `onet_task_pct` | float | % of all Claude conversations this task represents |
| `automation_pct` | float | % of classifiable usage showing automation patterns (directive + feedback_loop) |
| `augmentation_pct` | float | % showing augmentation patterns (learning + task_iteration + validation) |
| `task_success_pct` | float | % of conversations where AI successfully completed the task |
| `ai_autonomy_mean` | float | Mean AI autonomy score 1–5 |
| `speedup_factor` | float | `(human_only_time_hours × 60) / human_with_ai_time_minutes` — how many times faster with AI; median ~11.5x globally. Units confirmed in aei_v4_appendix.pdf: human_only_time asked in hours, human_with_ai_time asked in minutes. |

**Audit:**
- Row count: ~3,170 tasks (excluding none/not_classified)
- Top task by count should be software-related
- `automation_pct + augmentation_pct` ≤ 100 per task (remainder = unclassified)
- Global average: ~43% automation, ~57% augmentation (per arXiv 2503.04761)
- `task_success_pct` range: 0–100%; `speedup_factor` > 1.0 means AI is faster
- Collaboration data available for ~subset of tasks (not all tasks have intersection data)

**Audit Findings (verified 2026-03-18):**

**Issue 1 — Missing 6.5% from `none`/`not_classified` tasks**
- `none` (onet_task_count = 37,119, 3.7% of conversations) = conversations Anthropic couldn't map to any O*NET task — likely personal/off-topic use. Correctly excluded.
- `not_classified` (onet_task_count = 27,729, 2.8%) = conversations where the task matched O*NET task categories but lacked enough signal to assign a specific task. Correctly excluded.
- Both are non-task noise. Exclusion is valid.

**Issue 2 — Our global avg automation (37.9%) vs. Anthropic's 43%**
- Our values are unweighted task-level averages (each task equally weighted).
- Anthropic's 43% is conversation-weighted (each conversation weighted by its onet_task_count).
- High-volume tasks (software coding: 59,739 conversations) have higher automation rates, pulling the conversation-weighted figure up.
- This is expected behavior — not a bug. We will use task-level averages consistently.

**Issue 3 — speedup_factor < 1.0 in original script (now fixed)**
- Root cause: unit mismatch. `human_only_time` is in **hours**, `human_with_ai_time` is in **minutes**.
- **Confirmed in `aei_v4_appendix.pdf` (release_2026_01_15):** The LLM-judge prompt for `human_only_time` asks *"how many hours a competent professional would need"* and the prompt for `human_with_ai_time` asks *"how many minutes the User spent"*. Units differ by design — one measures task length without AI, the other measures actual conversation time.
- Original formula (`hot / hwt`) produced 0.2x because it divided hours by minutes.
- Fixed formula: `(human_only_time_hours × 60) / human_with_ai_time_minutes`
- Global check: (3.09h × 60) / 15.35min = **12.1x** — matches README's stated 9–12x range.
- Task-level corrected median = **11.5x**, range 2.2x – 103x.


---

## Phase 2b: Task-to-Occupation Mapping

**Map 3,168 AEI task descriptions to O*NET occupation codes (v30.2).**

**Script:** `scripts/map_economic_index.py`

**Approach:** AEI task descriptions are verbatim O*NET task statements. Join on task text (one row per AEI task × occupation). Two-pass:
1. **Exact match** — lowercase + strip
2. **Fuzzy fallback** (threshold ≥ 95) — handles trivial punctuation differences

**Output: `data/intermediate/economic_index_tasks_mapped.csv`**

| Column | Type | Description |
|--------|------|-------------|
| `task_text` | string | AEI task description |
| `onet_code` | string | O*NET-SOC occupation code |
| `occupation_title` | string | Occupation name |
| `match_type` | string | `exact`, `fuzzy`, or `unmatched` |
| `onet_task_count` | int | Claude conversations for this task (from Phase 2a) |
| `onet_task_pct` | float | % of all Claude conversations (from Phase 2a) |

One row per (AEI task × occupation) — a task shared by multiple occupations produces multiple rows.

**Audit Findings (verified 2026-03-18):**

| Metric | Value |
|--------|-------|
| Total rows | 4,024 |
| Unique AEI tasks mapped | 2,917 of 3,168 (92.1%) |
| Exact matches | 2,635 tasks → 3,384 rows |
| Fuzzy matches | 282 tasks → 389 rows |
| Unmatched | 251 tasks |
| Unique occupations covered | 673 of 923 in v30.2 |
| Scored occupations with AEI coverage | 673 of 923 |
| Tasks per occupation | min=1, median=4, mean=5.6, max=25 |

**Unmatched tasks (251):** Best fuzzy scores against v30.2 range 54–86 — well below the 95 threshold. These are genuine wording changes between the O*NET version used by Anthropic and v30.2, not trivial punctuation differences. Top unmatched tasks by usage include high-signal ones: "develop instructional materials..." (10,035 conversations), "edit or rewrite existing copy..." (4,741), "write, design, or edit web page content..." (2,821). These tasks exist in the AEI data but their v30.2 equivalents use different phrasing — they are lost signal.

**Fuzzy match quality:** Sample review shows correct occupation assignments (Database Architects, RNs, Truck Drivers, Nannies) with semantically identical task descriptions. Fuzzy pass is sound.

**Known limitation:** AEI dataset was built against an earlier O*NET version (pre-v30.2). The 251 unmatched tasks (8% of AEI tasks) represent real usage signal that cannot be attributed to specific occupations without a manual mapping or access to the older O*NET version used by Anthropic.


---

## Phase 3: Task Table + Occupation-Level Rollups

**Join the full O*NET task universe with AEI data. Produce a task-level table and an occupation-level metrics file.**

**Script:** `scripts/build_task_table.py`

See **Phase 0** for metric design, weighting rationale, and Anthropic's methodology.

---

**Output 1: `data/intermediate/onet_economic_index_task_table.csv`**

One row per (onet_code × task). All AEI metrics are null for tasks not in AEI.

| Column | Type | Description |
|--------|------|-------------|
| `onet_code` | string | O*NET-SOC occupation code |
| `task_id` | int | O*NET task ID |
| `task_text` | string | Full task description |
| `freq_score` | float | Weighted avg frequency (1–7 scale): `sum(category × pct_respondents / 100)`. Null for 29 occupations missing Task Ratings data (new in v30.2). |
| `importance_score` | float | Task importance rating (1–5 scale, from O*NET Task Ratings IM scale). Null for same 29 occupations. |
| `task_weight` | float | `freq_score × importance_score` if rated; occupation mean rated task_weight if unrated (global mean if no rated tasks exist for that occupation). Never null. |
| `weight_source` | string | `rated` or `mean_fallback` — flags which tasks used the fallback for downstream confidence tracking |
| `in_aei` | bool | Whether this task appears in AEI observed data |
| `match_type` | string | `exact`, `fuzzy`, or null (if not in AEI) |
| `onet_task_count` | int | Claude conversations involving this task (global, 1 week) |
| `onet_task_pct` | float | % of all Claude conversations this task represents |
| `automation_pct` | float | % of classifiable usage showing automation patterns (directive + feedback_loop) |
| `augmentation_pct` | float | % showing augmentation patterns (learning + task_iteration + validation) |
| `task_success_pct` | float | % of conversations where AI successfully completed the task |
| `ai_autonomy_mean` | float | Mean AI autonomy score 1–5 (higher = more delegation to AI) |
| `speedup_factor` | float | `(human_only_time_hours × 60) / human_with_ai_time_minutes`; median ~11.5x globally |

**Output 2: `data/intermediate/onet_economic_index_metrics.csv`**

One row per occupation — task-level metrics rolled up, weighted by `task_weight`.

| Column | Type | Description | Possible Scoring Use |
|--------|------|-------------|----------------------|
| `onet_code` | string | O*NET-SOC occupation code | — |
| `total_tasks` | int | Total O*NET tasks for this occupation | — |
| `aei_tasks` | int | Tasks observed in AEI | — |
| `ai_task_coverage_pct` | float | `aei_tasks / total_tasks × 100` | Low coverage = less signal confidence |
| `weighted_automation_pct` | float | `sum(task_weight × automation_pct) / sum(task_weight)` for AEI tasks | High → lower A9 (AI Handles Work); adjust A1 (Physical Presence) if low automation |
| `weighted_augmentation_pct` | float | `sum(task_weight × augmentation_pct) / sum(task_weight)` for AEI tasks | High → raise A10 (Manages/Directs AI); signals role is evolving toward AI collaboration |
| `weighted_task_success_pct` | float | `sum(task_weight × task_success_pct) / sum(task_weight)` for AEI tasks | High success = AI reliably handles these tasks; relevant to A3 (Novel Judgment) |
| `weighted_ai_autonomy_mean` | float | `sum(task_weight × ai_autonomy_mean) / sum(task_weight)` for AEI tasks | High autonomy = AI operates independently; relevant to A9, A10 |
| `weighted_speedup_factor` | float | `sum(task_weight × speedup_factor) / sum(task_weight)` for AEI tasks | High speedup = significant productivity gain; context for next steps narrative |

**Audit:**
- Task table: ~18,796 rows across 923 occupations (v30.2)
- `task_weight` is never null — rated tasks use `freq_score × importance_score`, fallback tasks use occupation mean rated weight (global mean 16.97 if no rated tasks exist)
- `weight_source = mean_fallback` for 845 rows across 86 occupations — 29 occupations entirely missing from Task Ratings (new v30.2 codes) and 57 with mixed rated/unrated tasks. Fallback = occupation mean rated task_weight; global mean used for fully-unrated occupations.
- `task_weight` range: ~1–35 for rated tasks; spot-check that daily high-importance tasks score highest
- `in_aei` = True for tasks from AEI-covered occupations
- Coverage spot-check: Web Developers (15-1254.00), Registered Nurses (29-1141.00), Construction Laborers (47-2061.00)
- All 1,016 scored occupations covered (v30.2 resolved the prior code version gap)

**QA:** All 1,016 occupations have `ai_task_coverage_pct`. Spot-check 10 occupations: task lists, AI status labels, and importance weights make sense.

---

## Phase 4: Join with Enriched Dataset

**Join task-level table + occupation-level metrics (from Phase 3) to `All_Occupations_ONET_enriched.csv`.**

**Script to create:** `scripts/enrich_with_economic_index.py`

**Input:**
- `data/intermediate/onet_economic_index_task_table.csv`
- `data/intermediate/onet_economic_index_metrics.csv`
- `data/intermediate/All_Occupations_ONET_enriched.csv`

**Process:** Left join on `onet_code`. All 1,016 occupations retained; NaN where no AEI data.

**Output: `data/intermediate/All_Occupations_ONET_enriched.csv`** (updated in place)

New columns added (from occupation-level metrics):

| Column | Type | Description |
|--------|------|-------------|
| `ai_task_coverage_pct` | float | % of O*NET tasks observed in AEI |
| `weighted_automation_pct` | float | Importance-weighted mean automation % across AEI tasks |
| `weighted_augmentation_pct` | float | Importance-weighted mean augmentation % across AEI tasks |
| `weighted_task_success_pct` | float | Importance-weighted mean AI success rate |
| `weighted_ai_autonomy_mean` | float | Importance-weighted mean autonomy score (1–5) |
| `weighted_speedup_factor` | float | Importance-weighted mean speedup factor |

**Audit:**
- All 1,016 occupations present after join
- Occupations with no AEI data: all new columns = NaN
- Count of occupations with AEI data: should be ~722
- Spot-check 3 occupations: metrics match what's in task table


---

## Phase 5: Generate Custom Next Steps per Occupation

**For each occupation, produce occupation-specific risks and opportunities using real task-level AI usage data, attribute scores, and authoritative external sources.**

**Script to create:** `scripts/generate_next_steps.py`

**Rollout approach:** Batch-by-batch manual review until output quality is consistent, then run full dataset in one pass.

**Inputs:**
- `data/intermediate/onet_economic_index_task_table.csv` — task-level AEI metrics + weights
- `data/intermediate/onet_economic_index_metrics.csv` — occupation-level AEI rollups
- `data/intermediate/All_Occupations_ONET_enriched_aei.csv` — enriched occupation data
- `data/output/score_log.txt` — A1–A10 attribute scores per occupation
- External sources searched per occupation (authoritative: BLS, ANA, Stack Overflow, WEF, McKinsey, etc.)

**Output:** `data/output/occupation_cards.jsonl` — one JSON object per line, one occupation per line.

Full schema defined in `docs/data-schema.md`. See `docs/career_page_spec.md` for content rules per section.

**Fields generated by Phase 5** (others pass through from enriched dataset):

| Field | Notes |
|-------|-------|
| `keyDrivers` | 2–3 sentence qualitative explanation of the score. No AEI metrics. See `docs/tone_guide_key_drivers.md`. |
| `risks` | Object: `{ stat, statLabel, statColor, body, sections[] }`. `stat` is the single standout number; `body` is prose with inline `[n]` citations. |
| `opportunities` | Same shape as `risks`. `statColor` should be `#5a9a6e` (green). |
| `howToAdapt` | Object: `{ alreadyIn, thinkingOf }`. Two short paragraphs for different audiences. Separate from `opportunities`. |
| `taskData` | Top 10 tasks by weight. Fields: `task` (short label), `full` (full O*NET text), `auto`, `aug`, `success`, `n`. Null AEI fields for tasks not in AEI. |
| `sources` | Array of `{ id, name, url }`. `id` is anchor string (e.g. `"src-1"`). |
| `top_automated_tasks` | Convenience subset. Up to 3, sorted by task_weight desc. |
| `top_augmented_tasks` | Convenience subset. Up to 3, sorted by task_weight desc. |
| `untouched_high_priority_tasks` | Convenience subset. Top 3 high-weight tasks with no AEI signal. |

**Pass-through fields** (joined from enriched dataset, not generated):

| Field | Source |
|-------|--------|
| `score` | `final_ranking × 100`, rounded to integer (0–100) |
| `salary` | Median annual wage from BLS/O*NET enriched data |
| `openings` | Annual job openings from BLS |
| `growth` | 10-year projected growth % from BLS |
| `jobTitles` | O*NET sample job titles for the occupation |

**risks logic:**
- Lead with what AI is doing to the highest-weight tasks (`automation_pct` on high-weight tasks)
- Suppress or soften claims for tasks where `onet_task_count < 100` (weak signal)
- If `ai_task_coverage_pct < 20%`, note that AI has limited footprint on this role — that's context, not a risk
- Mention impact on entry-level vs senior workers where external data supports it
- Pick `stat` as the single most concrete, surprising number from the prose — must be cited

**opportunities logic — draw from these signals in order:**
1. High/medium-weight tasks with **high `augmentation_pct`** — human still in the loop; worth highlighting
2. A9 ≥ 3 — specialized expertise not easily replicated; mention as a differentiator
3. A10 ≥ 3 — directing/managing AI is a natural growth path
4. **Downstream demand** — when AI makes a category cheaper/faster, it often creates adjacent demand
5. External sources — augment with specific recommendations from authoritative sources (BLS projections, Stack Overflow survey, WEF, professional associations)

**Do not cite tasks as opportunities based on weight alone.** A high-weight task absent from AEI is not automatically a durable strength — it may just be next. Only call out untouched tasks if there's a structural reason AI is unlikely to touch them (physical presence, real-time judgment, legal accountability, etc.). See `docs/career_page_spec.md` for examples of what not to do.

Low-weight tasks that are automated: mention briefly in risks or omit entirely.

**Tone guide:** `docs/tone_guide_career_pages.md`

**Audit:**
- Both sections name specific tasks, not generic descriptions
- High-weight tasks are featured, not low-weight ones
- Inline `[n]` citations all resolve to entries in `sources`
- Occupations with `ai_task_coverage_pct < 20%` don't overstate AI risk
- Batch-by-batch manual review before full run

**QA:** Next steps recommendations are specific, cite real tasks, and evidence counts are shown.

---

## Phase 6: Score Adjustment

**Adjust `role_resilience_score` based on important task automation.**

**Script to modify:** `scripts/score_occupations.py`

**Logic:** See Phase 0 scoring adjustment design. Use `weighted_automation_pct`, `weighted_task_success_pct`, and `weighted_ai_autonomy_mean` from Phase 3b occupation-level rollups. Thresholds TBD after data exploration.

**QA:** Score adjustments are directionally sensible — no wild swings from baseline.

---

## Phase 7: Adjacent Roles

**Surface related roles a worker could move into, with concrete lateral path guidance.**

**Script:** `scripts/adjacent_roles.py` ✅ Phase 7a complete

### Phase 7a-pre: Generate career cluster (if missing)

Before running `adjacent_roles.py` for any occupation, check whether it has a career cluster entry:

```bash
grep "<CODE>" data/career_clusters/cluster_roles.csv
```

If no match, Method 1 (cluster) will produce zero candidates and adjacent roles will rely entirely on task overlap and SOC similarity — lower quality results.

**Steps to generate a cluster:**

1. Look at the occupation's level in the broader career ladder (what are the entry roles? what are the senior roles? what are the lateral specializations?). Cross-reference `data/output/ai_resilience_scores.csv` for related codes.
2. Draft rows for `data/career_clusters/clusters.csv` (one new cluster or add to existing), `data/career_clusters/cluster_roles.csv` (one row per role in the cluster), and `data/career_clusters/cluster_branches.csv` (one row per directed transition, with `notes` for curated guidance).
3. **Human review:** inspect the drafted rows before committing. Check that levels are correct, transition_types make sense, and notes are accurate. Edit as needed.
4. Once approved, save to the CSVs — then run `adjacent_roles.py`.

**Schema reference:** `docs/data-schema.md` — career cluster section.

**Why this matters:** cluster branches carry curated `notes` that get injected into the Claude prompt as ground truth for the "How to make the move" steps. Without a cluster, steps are generated cold from task overlap alone.

### Phase 7a: Hardcoded config + Claude-generated fit/learn (current)

**Config:** `data/input/related_careers_config.json` — manually curated list of related codes per occupation. Edit this file to add new occupations or change related roles.

**Process per (source, target) pair:**
1. Pull top 6 tasks by weight for both occupations from task table
2. Call Claude (sonnet) with both task lists — generate `fit` (one sentence, Feynman style) and `learn` (2–3 concrete skills/credentials)
3. Join `score`, `openings`, `growth` from scores CSV
4. Write `relatedCareers[]` into the occupation's entry in `occupation_cards.jsonl`

**To add a new occupation:** add its code and a list of related codes to `related_careers_config.json`, then run:
```bash
python3 scripts/adjacent_roles.py --code XX-XXXX.XX
```

### Phase 7b: Similarity scoring via task embeddings (future)

Replace the hardcoded config with computed similarity:
1. Embed all O*NET task texts using sentence-transformers
2. For each occupation, compute weighted cosine similarity against all others using `task_weight` as the weight vector
3. Top N by similarity score become the candidate related roles
4. Still use Claude to generate `fit` and `learn` per pair

**Three signals (same as before):**
1. Task text similarity (primary) — weighted cosine on task embeddings
2. Sample job title overlap (secondary)
3. SOC family match (tertiary, tiebreaker)

**Output:** Top 6 adjacent roles per occupation, added to `relatedCareers` in `occupation_cards.jsonl`. Used for Goal 4 and feeds Goal 5 forward-looking recs.

**Three similarity signals — use all three, combine into ranked list:**

1. **Task text similarity (primary)** — O*NET task IDs are unique per occupation and not shared, so cosine similarity must be computed on task *text embeddings*, not task ID vectors. Embed all task texts, then for each occupation compute weighted cosine similarity against every other occupation using task_weight as the weight. This is the strongest signal for "does this role do similar work?" — requires embedding step (sentence-transformers or similar).

2. **Sample job title overlap (secondary)** — O*NET sample job titles are illustrative and not exclusive. The same real-world title (e.g. "Web Architect", "Webmaster") can appear under multiple occupation codes. Occupations that share ≥1 sample job title are candidate adjacent roles. Title overlap is a flag, not a primary match signal.

3. **Same SOC family (tertiary)** — occupations sharing the same 2-digit SOC prefix (e.g. `15-xxxx` = Computer and Mathematical) are in the same broad field. Use as a tiebreaker or to surface options the other two signals miss.

**Note on title overlap:** shared titles don't always mean similar work — e.g. "Web Architect" appears under Web Developers (15-1254.00), Web Administrators (15-1299.01), and Computer Systems Engineers (15-1299.08). Use task similarity to rank and filter.

**`fit` and `learn` generation:** After computing the ranked list, run a Claude API call per (source occupation, adjacent occupation) pair to generate:
- `fit` — one sentence explaining the lateral path. Feynman style: what's true about the overlap, not instructions.
- `learn` — 2–3 concrete skills/tools to close the gap. Specific, not vague categories.

**Output per occupation:**
```json
{
  "relatedCareers": [
    {
      "code": "15-1299.08",
      "title": "Computer Systems Engineers/Architects",
      "score": 55,
      "openings": "31,300",
      "growth": "+17%",
      "fit": "Senior web developers who design how components connect — APIs, databases, third-party services — are already thinking like architects. This role primarily does that.",
      "learn": ["Cloud platform architecture (AWS, GCP, Azure)", "System scalability and reliability patterns", "Cross-team technical leadership"]
    }
  ]
}
```

**QA:** Adjacent roles pass sanity check — similar roles surfaced, not random ones.

---

## Files Created/Modified

### New Files
- `scripts/download_economic_index.py` ✅ Phase 1
- `scripts/extract_economic_index.py` ✅ Phase 2a
- `scripts/map_economic_index.py` ✅ Phase 2b
- `scripts/aggregate_economic_index.py` — Phase 3 (to create)
- `scripts/enrich_with_economic_index.py` — Phase 4 (to create)
- `scripts/generate_next_steps.py` — Phase 5 (to create)
- `scripts/adjacent_roles.py` — Phase 7 (to create)
- `data/input/anthropic/aei_raw_claude_ai_2025-11-13_to_2025-11-20.csv` ✅ Phase 1
- `data/input/anthropic/README_ECONOMIC_INDEX.md` ✅ Phase 1
- `data/input/onet_db/Task Statements.xlsx` ✅ Phase 2b
- `data/input/onet_db/Task Ratings.xlsx` ✅ Phase 3a
- `data/intermediate/economic_index_tasks_raw.csv` ✅ Phase 2a
- `data/intermediate/economic_index_tasks_mapped.csv` ✅ Phase 2b
- `data/intermediate/onet_economic_index_task_table.csv` — Phase 3 (to create)
- `data/intermediate/onet_economic_index_metrics.csv` — Phase 3c (to create)

### Modified Files
- `.gitignore` ✅ Phase 1
- `README.md` ✅ Phase 1
- `data/intermediate/All_Occupations_ONET_enriched.csv` — Phase 4
- `scripts/score_occupations.py` — Phase 6

---

## Rollback Plan

If Phase 3+ breaks anything:
1. Revert `data/intermediate/All_Occupations_ONET_enriched.csv` to backup
2. Run scoring without EconomicIndex enrichment
3. Identify root cause (logic error? missing data? bad join?)
4. Fix and re-run

---

## Future TODOs

- **Eloundou et al. theoretical exposure data** (arXiv:2303.10130) — "GPTs are GPTs" paper provides task-level β scores (0, 0.5, 1.0) for theoretical LLM exposure across O*NET occupations. Joining these to our AEI observed data would let us identify: (1) tasks theoretically exposed but not yet observed — AI hasn't arrived yet but is coming; (2) tasks showing observed usage despite low theoretical scores — model capabilities may have advanced past 2023 estimates. This would add a "theoretical vs. observed gap" signal useful for forward-looking scoring and next steps guidance.

---

## Phase 9: Emerging Roles

**Generate AI-native career pivot paths proportional to each occupation's automation risk.**

**Script:** `scripts/generate_emerging_roles.py`

**Risk tier → count:**
| `role_resilience_score` | Tier | Emerging roles generated |
|---|---|---|
| ≤ 2.5 | Fragile / Volatile | 4 |
| 2.5–4.0 | Moderate | 2 |
| > 4.0 | Solid / Strong | 0 (skip) |

**Per occupation:**
1. Look up `role_resilience_score` → determine N
2. If N = 0, skip (solid/strong jobs don't need escape hatches)
3. Check `data/career_clusters/emerging_roles.csv` for cached rows — use if found
4. Otherwise call Claude: generate N candidates with title, description, core_tools, stat, search_query
5. Call Claude again per candidate: generate `fit` + `steps`
6. Construct search URLs automatically:
   - LinkedIn: `linkedin.com/jobs/search/?keywords=<title>`
   - Indeed: `indeed.com/jobs?q=<title>`
   - TrueUp: `trueup.io/search?q=<title>`
7. Write rows to `emerging_roles.csv` (cache for re-runs)
8. Write `emergingCareers` to `occupation_cards.jsonl`

```bash
python3 scripts/generate_emerging_roles.py --code 15-1254.00
python3 scripts/generate_emerging_roles.py --all
```

**Output fields per emerging role:** `title`, `description`, `core_tools`, `stat` (text/sourceName/sourceUrl), `search_query`, `job_search_url`, `fit`, `steps`

**QA:** Each emerging role has a real `job_search_url` verified via web search. Roles with no real job postings are replaced.

---

## Phase 10: Publish Career Pages to Site

**Turn each processed occupation into a live page on ai-proof-careers.com.**

**Skill:** `add-career-page` (Claude Code skill at `~/.claude/skills/add-career-page.md`)

**Per occupation:**
1. Run `generate_next_steps.py --code <CODE>` interactively to write the career page content to `occupation_cards.jsonl`
2. Check if the occupation has a career cluster: `grep "<CODE>" data/career_clusters/cluster_roles.csv`. If not, draft and review cluster rows before proceeding (see Phase 7a-pre).
3. Run `adjacent_roles.py --code <CODE>` to populate `relatedCareers`
4. Create `ai-resilient-occupations-site/src/data/careers/<slug>.tsx` from the JSONL data
5. Create `ai-resilient-occupations-site/app/career/<slug>/page.tsx` as the Next.js route

**To invoke:** `/add-career-page` — skill walks through all steps.

**Pages live so far:** licensed-practical-nurse, web-developer, air-traffic-controller, computer-programmer, software-developer, information-security-analyst, computer-information-systems-manager

**QA:** All pages load without 404. TypeScript compiles clean. Related careers and emerging roles render correctly.

**Fixes applied during Phase 10:**
- `adjacent_roles.py`: removed SOC family filter for Method 2 (task overlap) — was blocking cross-family matches (e.g. IT Manager 11- → 15- roles)
- `generate_next_steps.py`: `append_career_page()` now replaces existing entries instead of appending duplicates
- Page routes must be created manually — `generate_next_steps.py` and `adjacent_roles.py` only write to `occupation_cards.jsonl`, not the site

---

## Success Criteria

✅ Phase 1 & 2: Complete (data downloaded, tasks mapped)
⏳ Phase 3+: Pending execution

- [ ] All 1,016 occupations have EconomicIndex enrichment (or documented reason for gap)
- [ ] Scoring produces stable, sensible results
- [ ] Next steps recommendations are specific & actionable
- [ ] Key drivers cite EconomicIndex data when relevant
- [ ] No unexplained NaN values
