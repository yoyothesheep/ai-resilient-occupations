#!/usr/bin/env python3
"""
Generate career page content for each occupation.

For each occupation, produces: risks, opportunities, howToAdapt, sources.
Passes through: score, salary, openings, growth, jobTitles, keyDrivers, taskData.

Run interactively: the script prints a prompt, you paste it into Claude,
then paste the JSON response back. The career page data is saved to occupation_cards.jsonl.

Usage:
    python3 scripts/generate_next_steps.py --code 15-1254.00
    python3 scripts/generate_next_steps.py --batch 3   # next 3 unprocessed

Output:
    data/output/occupation_cards.jsonl  — one JSON object per line
"""

import argparse
import csv
import json
import os
import re
import sys
import urllib.request
import urllib.error
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────────────
SCORES_CSV    = "data/output/ai_resilience_scores.csv"
TASK_TABLE    = "data/intermediate/onet_economic_index_task_table.csv"
OCC_METRICS   = "data/intermediate/onet_economic_index_metrics.csv"
SCORE_LOG     = "data/output/score_log.txt"
TONE_GUIDE    = "docs/tone_guide_career_pages.md"
CAREER_SPEC   = "docs/career_page_spec.md"
OUTPUT_JSONL  = "data/output/occupation_cards.jsonl"

TOP_N_TASKS   = 10   # tasks to include in taskData

# ── Loaders ───────────────────────────────────────────────────────────────────

def load_scores() -> dict:
    """Load scores CSV keyed by onet_code."""
    with open(SCORES_CSV, newline="", encoding="utf-8") as f:
        return {r["Code"]: r for r in csv.DictReader(f)}


def load_task_table() -> dict:
    """Load task table keyed by onet_code → list of task rows."""
    table: dict[str, list] = {}
    with open(TASK_TABLE, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            code = row["onet_code"]
            table.setdefault(code, []).append(row)
    return table


def load_occ_metrics() -> dict:
    """Load occupation-level AEI metrics keyed by onet_code."""
    with open(OCC_METRICS, newline="", encoding="utf-8") as f:
        return {r["onet_code"]: r for r in csv.DictReader(f)}


def load_a_scores(log_path: str) -> dict:
    """
    Parse score_log.txt to extract A1-A10 per occupation.
    Returns dict: onet_code -> {a1: int, ..., a10: int}
    """
    a_scores: dict[str, dict] = {}
    pattern_occ = re.compile(r"^\s+(.+?)\s+\((\d{2}-\d{4}\.\d{2})\)")
    pattern_attr = re.compile(r"^\s+A(\d+)\s+.+?:\s+(\d+)")
    current_code = None

    with open(log_path, encoding="utf-8") as f:
        for line in f:
            m = pattern_occ.match(line)
            if m:
                current_code = m.group(2)
                a_scores[current_code] = {}
                continue
            if current_code:
                m2 = pattern_attr.match(line)
                if m2:
                    a_scores[current_code][f"a{m2.group(1)}"] = int(m2.group(2))
    return a_scores


def load_existing_codes() -> set:
    """Return set of onet_codes already in occupation_cards.jsonl."""
    if not os.path.exists(OUTPUT_JSONL):
        return set()
    codes = set()
    with open(OUTPUT_JSONL, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    codes.add(json.loads(line)["onet_code"])
                except (json.JSONDecodeError, KeyError):
                    pass
    return codes


def load_text(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


# ── Task data builder ─────────────────────────────────────────────────────────

def build_task_data(onet_code: str, task_rows: list) -> list:
    """
    Top N tasks by task_weight. Returns list of taskData dicts.
    AEI fields are None when not in AEI.
    Short labels are applied later from the interactive JSON response.
    """

    def safe_float(val):
        try:
            return round(float(val), 1) if val not in ("", None) else None
        except (ValueError, TypeError):
            return None

    def safe_int(val):
        try:
            return int(float(val)) if val not in ("", None) else None
        except (ValueError, TypeError):
            return None

    sorted_rows = sorted(
        task_rows,
        key=lambda r: float(r["task_weight"]) if r["task_weight"] else 0,
        reverse=True
    )[:TOP_N_TASKS]

    result = []
    for r in sorted_rows:
        n = safe_int(r.get("onet_task_count"))
        has_signal = r.get("in_aei", "").lower() == "true" and n is not None
        result.append({
            "task":    r["task_text"],
            "full":    r["task_text"],
            "weight":  round(float(r["task_weight"]), 1) if r.get("task_weight") else None,
            "auto":    safe_float(r.get("automation_pct"))    if has_signal else None,
            "aug":     safe_float(r.get("augmentation_pct"))  if has_signal else None,
            "success": safe_float(r.get("task_success_pct"))  if has_signal else None,
            "n":       n if has_signal else None,
        })
    return result


# ── Prompt builder ────────────────────────────────────────────────────────────

def build_prompt(occ: dict, tasks: list, metrics: dict, a_scores: dict,
                 tone_guide: str, career_spec: str) -> str:
    code = occ["Code"]
    title = occ["Occupation"]
    score = occ.get("role_resilience_score", "?")
    final_ranking = occ.get("final_ranking", "")

    a = a_scores.get(code, {})
    a_block = "\n".join(
        f"  A{i}: {a.get(f'a{i}', '?')}" for i in range(1, 11)
    )

    m = metrics.get(code, {})
    coverage = m.get("ai_task_coverage_pct", "unknown")
    w_auto   = m.get("weighted_automation_pct", "unknown")
    w_aug    = m.get("weighted_augmentation_pct", "unknown")

    task_lines = []
    for t in tasks:
        if t["n"] is not None:
            task_lines.append(
                f"  - {t['full']}\n"
                f"    weight={t.get('weight','?')} | auto={t['auto']}% aug={t['aug']}% "
                f"success={t['success']}% n={t['n']}"
            )
        else:
            task_lines.append(f"  - {t['full']}\n    weight=? | no AEI data")

    task_block = "\n".join(task_lines)

    # Build common names line from sample job titles
    sample_titles = occ.get("Sample Job Titles", "").strip()
    if sample_titles:
        common_names_line = f"Also known as: {sample_titles}\n"
    else:
        common_names_line = ""

    return f"""You are generating career page content for ai-proof-careers.com.

Below are your style rules. Follow them exactly.

=== TONE GUIDE ===
{tone_guide}

=== CAREER PAGE SPEC ===
{career_spec}

=== OCCUPATION DATA ===
Title: {title}
{common_names_line}O*NET Code: {code}
Role Resilience Score: {score} / 5.0
Final Ranking: {final_ranking} (0–1 scale)

Attribute Scores (1–5):
{a_block}

AEI Coverage: {coverage}% of tasks observed in AI usage data
Weighted automation %: {w_auto}
Weighted augmentation %: {w_aug}

Top tasks by importance × frequency (with AEI data where available):
{task_block}

=== YOUR TASK ===

Search for 1–2 authoritative sources about AI's impact on this occupation ({title}). When searching, use the common job titles listed above, not the formal O*NET name. Prefer sources published within the last 2 years, ranked by credibility for a tech-worker audience:
1. Big cloud/AI providers: Google Cloud research, AWS reports, GitHub Octoverse, Anthropic, Microsoft
2. Practitioner surveys: Stack Overflow Developer Survey, CNCF Annual Survey, Linux Foundation
3. Think tanks / govt: WEF Future of Jobs, BLS, McKinsey, NBER, MIT
Avoid: Gartner, IDC, Forrester (paywalls, URL rot), vendor blogs, Forbes contributors, undated content, sources older than 2 years.
Note: BLS salary, openings, and growth data is already included above from our downloaded dataset — cite it as a source without fetching it.
Only include sources whose URLs you are confident actually resolve — do not invent or guess URLs.

Then generate the following JSON object. All prose must follow the tone guide.

{{
  "onet_code": "{code}",
  "taskIntro": "1-2 sentences describing how AI activity is distributed across this role's tasks. Keep it pattern-level — do not repeat task names or percentages that are already visible in the task table. CRITICAL ACCURACY RULE: only describe a category of work as having 'no AI activity' if every task in that category explicitly shows null automation and null augmentation in the task data above. If any task in that category has a non-null automation or augmentation rate, do not claim the category is unaffected. Framing rules: (1) If most top-weight tasks have no AEI signal, write: 'The highest-weight tasks in this role have no AI activity recorded. [Note what signal does exist lower in the list.]' (2) If AI activity is concentrated in lower-weight support tasks while high-weight core tasks are untouched, write: 'AI is most active in the [support/documentation/etc] work. The core [type of work] has no AI activity recorded.' (3) If top-weight tasks themselves show high automation, describe the pattern directly. Plain prose, no em dashes, no marketing language. Talk about the job not the worker.",
  "risks": {{
    "body": "2–3 sentences. Risks means risks to job prospects — specifically from AI automating tasks or reducing demand for this role. Include relevant industry hiring trends. Do NOT frame workforce shortages as risks — a shortage drives up demand and is good for workers, not bad. Inline citations like [1] where sourced.",
    "stat": "A single standout number from risks body if a strong one exists, else null. Only use a stat if it directly quantifies AI automation impact or AI-driven job loss/reduction. Do NOT use employment growth rate — slow growth is not a risk. E.g. '25%'",
    "statLabel": "Short phrase describing the stat, else null. E.g. 'drop in entry-level tech hiring (2024)'"
  }},
  "opportunities": {{
    "body": "2–3 sentences. Lead with strongest augmentation or durability signal. Inline citations like [1].",
    "stat": "Single standout number if strong one exists, else null",
    "statLabel": "Short phrase describing what the stat measures, else null. 5–8 words max. Complete the sentence naturally after the number — e.g. '66%' + 'of developers report X'. Do NOT include a year or date in parentheses — mention it in the body instead."
  }},
  "howToAdapt": {{
    "alreadyIn": "3–4 sentences structured in two parts. Part 1 (immediate): one concrete action to take now. Part 2 (6-month): where to build depth over time — the areas AI handles worst for this specific role. Inline citations. Do NOT use em dashes.",
    "thinkingOf": "3–4 sentences for someone considering entering this field. Concrete portfolio or credential advice specific to this role — not generic 'learn AI tools' advice. Do NOT repeat statistics already cited in the risks section. Inline citations. Do NOT use em dashes.",
    "quotes": [
      {{
        "persona": "alreadyIn",
        "quote": "A quote about HOW to adapt in this role — a specific skill shift, tool adoption, or strategic move. Must reinforce the alreadyIn advice above. Must come from sources[]. NOT a generic job market stat or growth projection.",
        "attribution": "Person's name and title, or publication name if unattributed",
        "sourceId": "src-N"
      }},
      {{
        "persona": "alreadyIn",
        "quote": "A SECOND quote covering a DIFFERENT adaptation angle than the first (e.g. first = tool adoption, second = skill shift). Omit entirely if no meaningfully different second angle exists.",
        "attribution": "...",
        "sourceId": "src-N"
      }},
      {{
        "persona": "thinkingOf",
        "quote": "A quote about HOW to enter or position yourself in this field — credentials, portfolio approach, or entry strategy. NOT a generic growth stat.",
        "attribution": "...",
        "sourceId": "src-N"
      }},
      {{
        "persona": "thinkingOf",
        "quote": "A SECOND quote covering a DIFFERENT entry angle than the first. Omit if no meaningfully different second angle exists.",
        "attribution": "...",
        "sourceId": "src-N"
      }}
    ]
  }},
  "taskLabels": {{
    "Full task text here...": "3-5 word short label. Verb + object style. Use / for combined verbs (Write/analyze programs). Condense, don't truncate — capture the meaning, not the first N words."
  }},
  "sources": [
    {{"id": "src-1", "name": "Publisher name", "title": "Article or report title", "date": "Mon YYYY", "url": "https://..."}}
  ]
}}

Rules:
- All [n] inline citations must resolve to an entry in sources
- stat and statLabel must come from the prose — do not add a stat not mentioned in body
- Do not use "lean into", "AI is taking over", or other prohibited phrases from the tone guide
- Quotes: each must be about adaptation or entry strategy, not generic job market stats. All 4 must cover different topics. A growth projection alone is not an adaptation quote — only use it if the quote also says what to DO about it. Do not use static credential requirements ("typically need a bachelor's degree") — these are timeless facts, not adaptation advice. Every quote must pass this test: "Would this quote have been different 5 years ago?" If no, it's too generic.
- Respond ONLY with the JSON object, no other text
"""


# ── Interactive (inline) generation ──────────────────────────────────────────

def generate_career_page_interactive(prompt: str) -> dict:
    """Print the prompt and read the JSON response from stdin."""
    print("\n" + "="*80)
    print("PROMPT — paste this into your Claude conversation:")
    print("="*80)
    print(prompt)
    print("="*80)
    print("\nPaste the JSON response below, then press Enter + Ctrl-D (or Ctrl-Z on Windows):")
    text = sys.stdin.read().strip()
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*", "", text)
    return json.loads(text)



# ── Pass-through builder ──────────────────────────────────────────────────────

def build_passthrough(occ: dict, task_data: list) -> dict:
    """Build all pass-through fields from enriched data."""
    final_ranking = float(occ.get("final_ranking", 0) or 0)

    # Format growth: prefer numeric Employment Change if available
    growth_raw = occ.get("Employment Change, 2024-2034", "").strip()
    if growth_raw:
        try:
            pct = float(growth_raw)
            growth = f"+{pct:.0f}%" if pct >= 0 else f"{pct:.0f}%"
        except ValueError:
            growth = occ.get("Projected Growth", "")
    else:
        growth = occ.get("Projected Growth", "")

    # Format openings with comma separator
    openings_raw = occ.get("Projected Job Openings", "").replace(",", "").strip()
    try:
        openings = f"{int(openings_raw):,}"
    except ValueError:
        openings = occ.get("Projected Job Openings", "")

    # Parse job titles: merge single-word segments back onto the previous title
    # (e.g. "Air Traffic Control Specialist, Terminal" is one title, not two)
    raw_titles = [t.strip() for t in occ.get("Sample Job Titles", "").split(",") if t.strip()]
    titles = []
    for seg in raw_titles:
        if titles and " " not in seg:
            titles[-1] = titles[-1] + ", " + seg
        else:
            titles.append(seg)

    # Extract annual salary only (e.g. "$69.51 hourly, $144,580 annual" → "$144,580")
    wage_raw = occ.get("Median Wage", "")
    annual_match = re.search(r"(\$[\d,]+)\s+annual", wage_raw)
    salary = annual_match.group(1) if annual_match else wage_raw

    return {
        "score":      round(final_ranking * 100),
        "salary":     salary,
        "openings":   openings,
        "growth":     growth,
        "jobTitles":  titles,
        "keyDrivers": occ.get("key_drivers", ""),
        "taskData":   task_data,
    }


# ── Sanitizer ─────────────────────────────────────────────────────────────────

def sanitize(obj):
    """Recursively replace em-dashes with commas and normalize comma spacing in all string values."""
    if isinstance(obj, str):
        s = obj.replace("\u2014", ",")
        s = re.sub(r"\s*,\s*(?=[a-zA-Z])", ", ", s)  # normalize: word, word (not digits — avoids breaking "16,800")
        return s
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize(item) for item in obj]
    return obj


# ── URL + date validation ──────────────────────────────────────────────────────

_SOFT_404_PHRASES = [
    "currently being developed",
    "page not found",
    "404",
    "no longer available",
    "has been removed",
    "content not found",
    "doesn't exist",
    "does not exist",
    "we couldn't find",
    "we could not find",
]


def check_url(url: str) -> bool:
    """Return True if URL is reachable and not a soft 404, False otherwise."""
    if not url:
        return False
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        resp = urllib.request.urlopen(req, timeout=10)
        if not (200 <= resp.status < 300):
            return False
        snippet = resp.read(4096).decode("utf-8", errors="replace").lower()
        for phrase in _SOFT_404_PHRASES:
            if phrase in snippet:
                return False
        return True
    except Exception:
        return False


def validate_sources(sources: list) -> list:
    """Check each source URL and date; warn and clear dead URLs; warn on old dates."""
    cutoff_year = datetime.now().year - 2
    for s in sources:
        url = s.get("url", "")
        if url and not check_url(url):
            print(f"  ⚠ Dead URL cleared: {url}")
            s["url"] = ""
        date_str = s.get("date", "")
        if date_str:
            try:
                pub_date = datetime.strptime(date_str, "%b %Y")
                if pub_date.year < cutoff_year:
                    print(f"  ⚠ Source older than 2 years: {date_str} — {s.get('title', s.get('name', ''))}")
            except ValueError:
                pass
    return sources


# ── Writer ────────────────────────────────────────────────────────────────────

def append_career_page(card: dict):
    os.makedirs(os.path.dirname(OUTPUT_JSONL), exist_ok=True)
    # Load existing, replace if code already present, else append
    cards = {}
    if os.path.exists(OUTPUT_JSONL):
        decoder = json.JSONDecoder()
        content = open(OUTPUT_JSONL, encoding="utf-8").read().strip()
        pos = 0
        while pos < len(content):
            cf = content[pos:].lstrip()
            if not cf:
                break
            skip = len(content[pos:]) - len(cf)
            obj, end = decoder.raw_decode(cf)
            cards[obj["onet_code"]] = obj
            pos += skip + end
    replaced = card["onet_code"] in cards
    cards[card["onet_code"]] = card
    with open(OUTPUT_JSONL, "w", encoding="utf-8") as f:
        for c in cards.values():
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    action = "Replaced" if replaced else "Written"
    print(f"  ✓ {action} in {OUTPUT_JSONL}")


# ── Main ──────────────────────────────────────────────────────────────────────

def process_occupation(code: str, scores: dict, task_table: dict, occ_metrics: dict,
                       a_scores: dict, tone_guide: str, career_spec: str,
                       print_prompt_only: bool = False):
    occ = scores.get(code)
    if not occ:
        print(f"  ✗ Code {code} not found in scores CSV")
        return

    print(f"\n── {occ['Occupation']} ({code})")

    tasks = build_task_data(code, task_table.get(code, []))
    prompt = build_prompt(occ, tasks, occ_metrics, a_scores, tone_guide, career_spec)

    if print_prompt_only:
        print("\n" + "="*80)
        print(prompt)
        print("="*80)
        return

    generated = generate_career_page_interactive(prompt)

    # Apply short labels from the interactive response
    task_labels = generated.pop("taskLabels", {})
    for t in tasks:
        if t["full"] in task_labels:
            t["task"] = task_labels[t["full"]]

    # Validate source URLs and dates
    if "sources" in generated:
        print("  Validating sources...")
        validate_sources(generated["sources"])

    passthrough = build_passthrough(occ, tasks)

    card = {
        "onet_code": code,
        "title":     occ["Occupation"],
        **passthrough,
        **generated,
    }

    # Pretty-print for review
    print("\n  Generated content:")
    print(f"  risks.stat:   {generated.get('risks', {}).get('stat')} — {generated.get('risks', {}).get('statLabel')}")
    print(f"  opps.stat:    {generated.get('opportunities', {}).get('stat')} — {generated.get('opportunities', {}).get('statLabel')}")
    print(f"  sources:      {len(generated.get('sources', []))} found")
    for s in generated.get("sources", []):
        print(f"    [{s['id']}] {s['name']}")
    print(f"\n  taskIntro:\n    {generated.get('taskIntro', '')}")
    print(f"\n  risks.body:\n    {generated.get('risks', {}).get('body', '')}")
    print(f"\n  opportunities.body:\n    {generated.get('opportunities', {}).get('body', '')}")
    print(f"\n  howToAdapt.alreadyIn:\n    {generated.get('howToAdapt', {}).get('alreadyIn', '')}")
    print(f"\n  howToAdapt.thinkingOf:\n    {generated.get('howToAdapt', {}).get('thinkingOf', '')}")

    append_career_page(sanitize(card))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--code",  help="Single O*NET code to process, e.g. 15-1254.00")
    parser.add_argument("--batch", type=int, default=1, help="Number of unprocessed occupations to run")
    parser.add_argument("--print-prompt", action="store_true", help="Print the prompt and exit (for use with Claude.ai)")
    parser.add_argument("--force", action="store_true", help="Regenerate even if already in JSONL")
    args = parser.parse_args()

    print("Loading data...")
    scores      = load_scores()
    task_table  = load_task_table()
    occ_metrics = load_occ_metrics()
    a_scores    = load_a_scores(SCORE_LOG)
    existing    = load_existing_codes()
    tone_guide  = load_text(TONE_GUIDE)
    career_spec = load_text(CAREER_SPEC)

    if args.code:
        if args.code in existing and not args.print_prompt and not args.force:
            print(f"  Already processed: {args.code}. Use --force to regenerate.")
            return
        process_occupation(args.code, scores, task_table, occ_metrics,
                           a_scores, tone_guide, career_spec,
                           print_prompt_only=args.print_prompt)
    else:
        # Batch mode: next N unprocessed, scored occupations
        candidates = [
            r["Code"] for r in csv.DictReader(open(SCORES_CSV))
            if r["Code"] not in existing
            and r.get("role_resilience_score")
            and r.get("Data-level") == "Y"
        ]
        to_run = candidates[:args.batch]
        print(f"Batch mode: {len(to_run)} occupations (of {len(candidates)} remaining)")
        for code in to_run:
            process_occupation(code, scores, task_table, occ_metrics,
                               a_scores, tone_guide, career_spec,
                               print_prompt_only=args.print_prompt)

    print("\n✓ Done")


if __name__ == "__main__":
    main()
