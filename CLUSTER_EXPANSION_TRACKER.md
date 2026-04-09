# Cluster Expansion Tracker
## 5 New Clusters: Sales, Analysts, Finance, Marketing, Design

**Full plan:** `/Users/yuchen/.claude/plans/rippling-noodling-alpaca.md`

Track B runs all 5 steps per cluster before moving to the next cluster.

---

## Phase 1: Define Cluster Data ✅
All 5 clusters defined in clusters.csv, cluster_roles.csv, cluster_branches.csv.

---

## Phase 2: Track B Pipeline (per cluster)

Run all 4 steps for one cluster, then move to the next.

Order matters: generate_next_steps must run before generate_emerging_roles so the card exists
when emergingCareers is written. generate_emerging_roles also uses card context to generate
better candidates, so earlier = worse output.

```bash
source venv/bin/activate
# Step 1 (Claude generates JSON responses automatically, one --code per occupation)
python3 scripts/generate_next_steps.py --code <code>
# Step 2
python3 scripts/generate_emerging_job_titles.py --cluster <id>
# Step 3 (uses card context from step 1; writes emergingCareers into existing cards)
python3 scripts/generate_emerging_roles.py --cluster <id>
# Step 4 (run for each code in cluster — no --cluster flag)
for code in <code1> <code2> ...; do python3 scripts/adjacent_roles.py --code $code; done
```

### `sales`
- [x] 1. generate_next_steps
- [x] 2. generate_emerging_job_titles
- [x] 3. generate_emerging_roles
- [x] 4. adjacent_roles

### Note - change from interactive to API before running analysts cluster

### `analysts`
- [ ] 1. generate_next_steps
- [ ] 2. generate_emerging_job_titles
- [ ] 3. generate_emerging_roles
- [ ] 4. adjacent_roles

### `finance`
- [ ] 1. generate_next_steps
- [ ] 2. generate_emerging_job_titles
- [ ] 3. generate_emerging_roles
- [ ] 4. adjacent_roles

### `marketing`
- [ ] 1. generate_next_steps
- [ ] 2. generate_emerging_job_titles
- [ ] 3. generate_emerging_roles
- [ ] 4. adjacent_roles

### `design`
- [ ] 1. generate_next_steps
- [ ] 2. generate_emerging_job_titles
- [ ] 3. generate_emerging_roles
- [ ] 4. adjacent_roles

---

## Phase 3: Career Pages (site repo — ../ai-resilient-occupations-site)

```bash
# Generate (run from data repo)
python3 scripts/generate_career_pages.py --cluster <id>
# QA (run from site repo) — use aeo-content-writer skill
/aeo-content-writer qa --cluster <id>
```

Slug derived from `altpath simple title` in ai_resilience_scores.csv. Two files per occupation: `src/data/careers/<slug>.tsx` + `app/career/<slug>/page.tsx`.

### Sales ✅
- [x] generate
- [x] QA
- [x] insurance-sales-agent (41-3021.00)
- [x] retail-salesperson (41-2031.00)
- [x] manufacturing-sales-representative (41-4012.00)
- [x] real-estate-sales-agent (41-9022.00)
- [x] real-estate-broker (41-9021.00)
- [x] sales-engineer (41-9031.00)
- [x] sales-manager (11-2022.00)

### Analysts
- [ ] generate
- [ ] QA (aeo-content-writer)
- [ ] market-research-analyst (13-1161.00)
- [ ] budget-analyst (13-2031.00)
- [ ] management-analyst (13-1111.00)
- [ ] financial-investment-analyst (13-2051.00)
- [ ] compliance-officer (13-1041.00)
- [ ] financial-examiner (13-2061.00)

### Finance
- [ ] generate
- [ ] QA (aeo-content-writer)
- [ ] bookkeeping-accounting-clerk (43-3031.00)
- [ ] tax-preparer (13-2082.00)
- [ ] accountant-auditor (13-2011.00)
- [ ] loan-officer (13-2072.00)
- [ ] credit-analyst (13-2041.00)
- [ ] personal-financial-advisor (13-2052.00)
- [ ] financial-risk-specialist (13-2054.00)
- [ ] fraud-examiner (13-2099.04)
- [ ] financial-manager (11-3031.00)
*(13-2051.00 and 13-2061.00 shared with analysts — skip if already done)*

### Marketing
- [ ] generate
- [ ] QA (aeo-content-writer)
- [ ] search-marketing-strategist (13-1161.01)
- [ ] advertising-sales-agent (41-3011.00)
- [ ] public-relations-specialist (27-3031.00)
- [ ] writer-author (27-3043.00)
- [ ] editor (27-3041.00)
- [ ] advertising-promotions-manager (11-2011.00)
- [ ] marketing-manager (11-2021.00)
*(13-1161.00 shared with analysts — skip if already done)*

### Design
- [ ] generate
- [ ] QA (aeo-content-writer)
- [ ] graphic-designer (27-1024.00)
- [ ] special-effects-artist-animator (27-1014.00)
- [ ] merchandise-displayer (27-1026.00)
- [ ] commercial-industrial-designer (27-1021.00)
- [ ] fashion-designer (27-1022.00)
- [ ] fine-artist (27-1013.00)
- [ ] interior-designer (27-1025.00)
- [ ] set-exhibit-designer (27-1027.00)
- [ ] art-director (27-1011.00)

---

## Phase 4: Industry Pages (site repo)
Two files per cluster: `src/data/industries/<slug>.ts` + `app/industry/<slug>/page.tsx`
Reference: `src/data/industries/software-technology.ts`

- [x] sales-business-development
- [ ] business-financial-analysts
- [ ] finance-accounting
- [ ] marketing-growth
- [ ] design-creative

---

## Phase 5: QA & Deploy
- [ ] All career pages load at localhost:3000/career/<slug>
- [ ] All industry pages load at localhost:3000/industry/<slug>
- [ ] Run `publish-checklist` skill in site repo
