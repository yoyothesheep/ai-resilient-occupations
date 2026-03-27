# Occupation Cards Review Log

Tracks manual review batches for `occupation_cards.jsonl`. Each batch reviewed before proceeding to the next.

Progress: `wc -l data/output/occupation_cards.jsonl` = cards written so far.

---

## Batch 1 — 2026-03-19

**Occupations:** LPN (29-2061.00), Web Developers (15-1254.00)

**Decisions made:**
- Risks and opportunities use `{summary, sections[]}` structure — sections are optional and free-form titled
- Inline `[n]` citation markers in prose, resolved by `sources` array
- Tasks with `onet_task_count < 100` excluded from top_automated/augmented task lists (Web Dev email task n=67, security logs n=36 dropped)
- `low_data_confidence: true` when `ai_task_coverage_pct < 20%` (LPN = 9.1%)
- Tier fields left null — to be populated once tier system is finalized
- Sources searched per occupation from authoritative sources (BLS, ANA, Stack Overflow, WEF, etc.)

**Tone notes:**
- Talk about the job, not the worker. Third person throughout.
- Casual but direct. High school readable.
- Risks name specific tasks and cite real data (automation %, n= counts, external stats)
- Opportunities split into: augmentation signal, untouched tasks, downstream demand (A9/A10 if ≥ 3)
- LPN example: sparse AEI coverage → short risks, simple opportunities, no augmentation section
- Web Dev example: rich AEI coverage → fuller risks, 2 opportunity subsections

**Quality: Approved**
