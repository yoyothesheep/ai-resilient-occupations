# From Emerging Roles to Scoring Pipeline

Integration guide: how to move validated emerging roles into the main AI resilience scoring system.

## Workflow

```
emerging_roles_findings.jsonl
         ↓ (curator picks high-confidence role)
emerging_roles_pipeline_candidates.csv (readiness: ready_for_enrichment)
         ↓ (gather task/salary/education data)
data/input/emerging_roles/<role_title>/
         ↓ (run enrichment + scoring)
data/output/ai_resilience_scores.csv (add new rows)
         ↓ (export occupation cards)
data/output/occupation_cards.jsonl (new entry)
         ↓ (manual: create TSX career page)
../ai-resilient-occupations-site/src/data/careers/<slug>.tsx
```

## Step-by-Step Integration

### Step 1: Identify Candidate Role
From `WEEKLY_EMERGING_ROLES_REPORT_YYYY-MM-DD.md` or `emerging_roles_findings.jsonl`:

**Criteria for pipeline readiness:**
- Confidence score ≥ 0.80
- Job posting count 100+ in past 3 months
- Multi-company adoption (3+ different companies)
- Clear, distinct role definition (not a rename)
- Ready to harvest enrichment data

**Example:** Context Engineer
```json
{
  "role_title": "Context Engineer",
  "confidence": 0.85,
  "job_posting_count_3m": 187,
  "companies_hiring": ["Anthropic", "Google DeepMind", "Hugging Face", "Meta"],
  "ready_for_pipeline": true
}
```

### Step 2: Create Input Directory
```bash
mkdir -p data/input/emerging_roles/context-engineer
cd data/input/emerging_roles/context-engineer
```

### Step 3: Enrich with Task & Metadata Data
Create files for task enrichment:

**`tasks.csv`** — Core job tasks
```csv
task_id,task_statement,importance_level,frequency
1,Design and optimize context window strategies for LLMs,4,very_frequent
2,Develop techniques for efficient token usage and context compression,4,very_frequent
3,Evaluate and benchmark context approaches against baselines,3,frequent
4,Collaborate with alignment teams on context robustness,3,frequent
5,Document best practices and create tools for internal teams,2,occasional
```

**`metadata.csv`** — Role metadata
```csv
role_title,job_zone,typical_entry_education,salary_median,annual_openings_estimate,growth_rate_3y
Context Engineer,4,bachelor,185000,250,0.35
```

Where:
- `job_zone`: O*NET Job Zone (1-5; 4 = requires significant preparation)
- `typical_entry_education`: associate, bachelor, master (or none)
- `salary_median`: Annual median from job postings (BLS + Glassdoor)
- `annual_openings_estimate`: Job posting count / 4 (rough quarterly average)
- `growth_rate_3y`: Estimated 3-year growth (e.g., 0.35 = 35% growth)

**`examples.csv`** — Actual job posting examples
```csv
company,posting_title,posting_url,posting_date,snippet
Anthropic,Context Engineer,https://careers.anthropic.com/...,2026-03-01,Responsible for designing and optimizing context window strategies...
Google DeepMind,Senior Context Engineer,https://google.com/careers/...,2026-02-15,Lead context research across alignment team...
Hugging Face,Context Optimization Engineer,https://huggingface.co/...,2026-03-20,Build tools for efficient context utilization...
```

### Step 4: Run Enrichment
```bash
# Merge emerging role data into main enriched dataset
python3 scripts/enrich_onet.py --emerging context-engineer

# Output: data/intermediate/All_Occupations_ONET_enriched.csv (updated with new role)
```

### Step 5: Score & Rank
```bash
# Score new role alongside existing occupations
python3 scripts/score_occupations.py

# Output: data/output/ai_resilience_scores.csv (includes Context Engineer with score)
```

### Step 6: Generate Occupation Cards
```bash
# Export structured data for career pages
python3 scripts/generate_occupation_cards.py --include-emerging

# Output: data/output/occupation_cards.jsonl (new entry for context-engineer)
```

Example card from JSONL:
```json
{
  "slug": "context-engineer",
  "title": "Context Engineer",
  "score": 82,
  "salary": 185000,
  "openings": 250,
  "growth": 35,
  "description": "Engineers optimizing how AI models use their context windows for maximum utility.",
  "jobTitles": ["Context Engineer", "Context Optimization Engineer", "Senior Context Engineer"],
  "keyDrivers": "Context Engineers are in high demand as language models scale to 200k+ token contexts. The role sits at the intersection of model optimization and product needs, with strong growth across frontier labs and enterprise AI. Salary and openings both trending upward.",
  "tasks": [...],
  "sources": [...]
}
```

### Step 7: Create Career Page (Next.js Site)

In the **site repo** (`../ai-resilient-occupations-site/`):

**1. Create data file:** `src/data/careers/context-engineer.tsx`

```tsx
import { CareerData, TaskRow, Source } from "@/types";

export const contextEngineerData: CareerData = {
  title: "Context Engineer",
  score: 82,
  salary: "$185,000",
  openings: "250+ annually",
  growth: "35% (3-year)",
  description: "Engineers optimizing how AI models utilize context windows for maximum efficiency and utility.",

  jobTitles: [
    "Context Engineer",
    "Context Optimization Engineer",
    "Senior Context Engineer",
    "Context Specialist",
    "LLM Context Engineer",
    "Context Research Engineer"
  ],

  keyDrivers: <>
    Context Engineers are critical as language models scale to 200k+ token contexts. The role sits at the intersection of model optimization and product strategy, demanding both deep technical knowledge and product intuition. Strong adoption across frontier AI labs (Anthropic, Google DeepMind, Meta) signals sustained demand. Salary growth outpacing software engineering median, with 35% projected growth over 3 years driven by model scaling and enterprise AI deployment.
  </>,

  risks: {
    stat: "64%",
    statLabel: "of tasks automatable by 2030",
    statColor: "#d97706",
    body: <>
      Routine context optimization and benchmarking tasks are prime candidates for automation. As models grow larger and context strategies mature into standard patterns, the routine diagnostic work risks commoditization. However, research and novel context approaches remain difficult to automate.
    </>
  },

  opportunities: {
    stat: "18%",
    statLabel: "faster salary growth than median",
    statColor: "#10b981",
    body: <>
      Emerging nature of the role means salary inflation as supply of qualified engineers lags demand. Companies are willing to pay premiums for experienced context researchers. Cross-functional nature (research, product, engineering) creates promotion pathways into leadership roles.
    </>
  },

  howToAdapt: {
    alreadyIn: <>
      If you are already a software engineer or ML engineer: move into context-focused projects on your current team. Study LLM APIs deeply (Anthropic, OpenAI, HuggingFace). Build side projects optimizing context usage. Join open research communities (HuggingFace, arXiv) tracking context papers.
    </>,
    thinkingOf: <>
      If you are considering the transition: start with prompt engineering or RAG (retrieval-augmented generation) projects to understand context constraints. Build strong foundations in Python, ML fundamentals, and LLM architecture. Contribute to open-source projects like llama-index or LangChain that work with context.
    </>
  },

  taskData: [
    {
      task: "Design context window optimization strategies",
      resilience: 4.2,
      automationRisk: 0.65,
      source: "src-1"
    },
    {
      task: "Develop efficient token usage and compression techniques",
      resilience: 4.5,
      automationRisk: 0.45,
      source: "src-1"
    },
    {
      task: "Benchmark context approaches against baselines",
      resilience: 3.8,
      automationRisk: 0.72,
      source: "src-1"
    },
    {
      task: "Collaborate with alignment teams on context robustness",
      resilience: 4.6,
      automationRisk: 0.20,
      source: "src-1"
    },
    {
      task: "Document best practices and create internal tools",
      resilience: 3.5,
      automationRisk: 0.55,
      source: "src-1"
    }
  ] as TaskRow[],

  careerCluster: [
    {
      title: "Senior Context Engineer",
      score: 4.3,
      description: "Leadership-track role; lead context research initiatives, mentor junior engineers, shape company context strategy.",
      sourceName: "Career trajectory analysis",
      sourceTitle: "Typical progression in frontier labs",
      sourceDate: "Mar 2026"
    },
    {
      title: "LLM Research Engineer",
      score: 4.1,
      description: "Shift to research-heavy focus; publish papers, collaborate with academia, explore novel context approaches.",
      sourceName: "Research lab data",
      sourceTitle: "Emerging research roles in AI",
      sourceDate: "Mar 2026"
    },
    {
      title: "AI Product Manager",
      score: 3.9,
      description: "Transition to product side; define features around context, lead customer partnerships, shape product vision.",
      sourceName: "Product team progression",
      sourceTitle: "Cross-functional career paths",
      sourceDate: "Mar 2026"
    }
  ],

  sources: [
    {
      id: "src-1",
      name: "Anthropic",
      title: "Context Engineer role documentation",
      date: "Mar 2026",
      url: "https://careers.anthropic.com/jobs/context-engineer"
    },
    {
      id: "src-2",
      name: "LinkedIn Salary Data",
      title: "Context Engineer compensation survey",
      date: "Mar 2026",
      url: "https://linkedin.com/salary/context-engineer"
    },
    {
      id: "src-3",
      name: "BLS + Job Board Analysis",
      title: "Job opening trends 2026",
      date: "Mar 2026",
      url: "https://www.bls.gov"
    }
  ]
};
```

**2. Create route file:** `app/career/context-engineer/page.tsx`

```tsx
import CareerDetailPage from "@/components/CareerDetailPage";
import { contextEngineerData } from "@/data/careers/context-engineer";

export default function ContextEngineerPage() {
  return <CareerDetailPage data={contextEngineerData} />;
}
```

**3. Add page meta:**

In the `CareerDetailPage` component (or add to your page metadata system):

```tsx
// Title: "Context Engineer Career Guide: AI Risk, Salary & Next Steps"
// Meta: "Context Engineer scores 82/100 on AI resilience — strong territory. See which tasks AI already automates, how salaries are holding, and which adjacent roles offer better protection."
```

### Step 8: Link from Emerging Roles Findings

Update `data/career_clusters/emerging_roles_findings_YYYY-MM-DD.jsonl` entry for Context Engineer:

```json
{
  "role_title": "Context Engineer",
  ...
  "ready_for_pipeline": true,
  "pipeline_readiness_notes": "Integrated into scoring pipeline. Scored 82/100 (Strong). Career page live at ai-proof-careers.com/career/context-engineer"
}
```

## Validation Checklist

Before marking a role as "live":

- [ ] Confidence score ≥ 0.80
- [ ] Task enrichment data complete (5+ tasks with resilience ratings)
- [ ] Salary data cross-checked against BLS + Glassdoor + job postings
- [ ] Growth rate estimate validated (posting trends over 3 months)
- [ ] Scoring pipeline run successfully
- [ ] Career page `.tsx` file created with non-dead URLs
- [ ] Route file registered in site
- [ ] Page meta title and description follow templates
- [ ] No em dashes in data files
- [ ] All sources verified and resolving
- [ ] Career cluster connections drafted

## Timeline

Typical integration: 2-3 weeks from "ready_for_enrichment" to "live on site"

- **Week 1:** Gather enrichment data, run scoring
- **Week 2:** Create career page, validate content, test routes
- **Week 3:** Deploy to site, update emerging roles log

## Rollback

If a role scores poorly or integration reveals issues:

1. Remove from `ai_resilience_scores.csv`
2. Mark as `status: archived` in `emerging_roles_findings.jsonl` with reason
3. Note in `emerging_roles_pipeline_candidates.csv`
4. Unpublish career page (or mark as draft)
5. Document lesson learned for future roles

