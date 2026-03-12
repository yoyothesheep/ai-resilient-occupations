"""
Fix 5 occupations whose 10-year earnings models started at mid-level pay.
All now start from absolute entry-level per ENRICHMENT_INSTRUCTIONS.md.
"""
import csv, os

FIXES = {
    "15-1299.08": {  # Computer Systems Engineers/Architects — BLS median $108,970
        "Calculation Type": "ladder",
        "Unpaid Training Years": "0",
        "Training Cost ($)": "2000",
        "Yr1 ($)": "45000",   # IT help desk, CompTIA A+
        "Yr2 ($)": "48000",   # Tier II support, Network+
        "Yr3 ($)": "55000",   # Junior Systems Admin, Security+
        "Yr4 ($)": "63000",   # Systems Admin, AWS Associate
        "Yr5 ($)": "72000",   # Senior Sysadmin / Systems Engineer
        "Yr6 ($)": "82000",   # Senior Engineer, AWS Professional/TOGAF
        "Yr7 ($)": "90000",   # Solutions Architect entry
        "Yr8 ($)": "96000",   # Architect, enterprise experience
        "Yr9 ($)": "102000",  # Senior Architect
        "Yr10 ($)": "108970", # BLS median
        "10-Year Net Earnings ($)": "759970",
        "10-Year Net Earnings Calculation": "Yr1 $45,000 + Yr2 $48,000 + Yr3 $55,000 + Yr4 $63,000 + Yr5 $72,000 + Yr6 $82,000 + Yr7 $90,000 + Yr8 $96,000 + Yr9 $102,000 + Yr10 $108,970 = $761,970 − $2,000 training = $759,970",
        "10-Year Net Earnings Calculation Model": "1. Paid Training (Employer pays trainee): Start in IT support/help desk with CompTIA A+ cert. 0 unpaid years; ~$2,000 for cert exam fees (A+, Network+, Security+, AWS) earned while working. Canonical IT/Systems Family path — mapped from day one of the IT support career.\n2. Yr1–2: IT Help Desk (~$45k–$48k), earning CompTIA A+ and Network+. Yr3–4: Junior Systems Admin after Security+ and cloud fundamentals (~$55k–$63k). Yr5–6: Systems Engineer with AWS Professional/Azure or TOGAF certifications (~$72k–$82k). Yr7–10: Solutions Architect track growing to the BLS median ($108,970). Salary varies by cloud platform depth, industry vertical, and consulting vs. in-house.",
        "Difficulty Score": "High",
        "Difficulty Score Explanation": "No degree strictly required, but the certification stack (A+, Network+, Security+, AWS/Azure Professional, TOGAF) is lengthy and self-directed — each exam requires significant study time. The entry path from help desk to architect takes 6–8 years of consistent advancement; stalling at systems admin is common. Roles require both deep technical knowledge and the ability to communicate architecture decisions to non-technical stakeholders.",
        "How to Get There": "Start in IT help desk or support technician role — no degree required. Earn CompTIA A+ (~$300 exam) as the entry ticket. Add Network+ and Security+ over Years 2–3 (~$300 each). Transition into systems admin by gaining hands-on server/cloud exposure. Pursue AWS Solutions Architect Associate (~$300) or Azure equivalent to move into engineer roles. TOGAF enterprise architecture certification (~$495) unlocks senior architect titles. Total cert cost: ~$1,500–$2,000 over 5–7 years.",
    },

    "15-1211.00": {  # Computer Systems Analysts — BLS median $103,790
        "Calculation Type": "ladder",
        "Unpaid Training Years": "0",
        "Training Cost ($)": "2000",
        "Yr1 ($)": "45000",   # IT help desk/support
        "Yr2 ($)": "48000",   # Tier II support, ITIL Foundation
        "Yr3 ($)": "55000",   # Junior Systems Analyst
        "Yr4 ($)": "64000",   # Systems Analyst
        "Yr5 ($)": "74000",   # Senior Analyst
        "Yr6 ($)": "82000",   # Lead Analyst / IT Business Analyst
        "Yr7 ($)": "88000",   # Senior systems analyst
        "Yr8 ($)": "93000",   # Principal analyst
        "Yr9 ($)": "98000",
        "Yr10 ($)": "103790", # BLS median
        "10-Year Net Earnings ($)": "748790",
        "10-Year Net Earnings Calculation": "Yr1 $45,000 + Yr2 $48,000 + Yr3 $55,000 + Yr4 $64,000 + Yr5 $74,000 + Yr6 $82,000 + Yr7 $88,000 + Yr8 $93,000 + Yr9 $98,000 + Yr10 $103,790 = $750,790 − $2,000 training = $748,790",
        "10-Year Net Earnings Calculation Model": "1. Paid Training (Employer pays trainee): Start in IT support/help desk — 0 unpaid years. ~$2,000 for CompTIA A+/Network+ and ITIL Foundation exam fees earned while working. Canonical IT/Systems Family path — mapped from day one of the IT support career.\n2. Yr1–2: IT Help Desk (~$45k–$48k). Yr3–4: Junior Systems Analyst after ITIL Foundation and business-systems exposure (~$55k–$64k). Yr5–7: Systems Analyst → Senior Analyst, specializing in ERP, CRM, or infrastructure integrations (~$74k–$88k). Yr8–10: Principal/lead analyst growing to the BLS median ($103,790). High-demand platform specialization (SAP, Salesforce, ServiceNow) can push well above median.",
        "Difficulty Score": "Medium",
        "Difficulty Score Explanation": "No formal degree required but requires bridging both IT technical skills and business process knowledge — a combination many help-desk workers struggle to develop without deliberate effort. ITIL certification is widely required. Moving from support to analyst typically takes 2–4 years; advancement beyond that depends on ability to translate between technical and business stakeholders. No competitive exam or physical barriers.",
        "How to Get There": "Start in IT help desk or support technician role. Earn CompTIA A+ (~$300) to get hired. Within 1–2 years, add ITIL Foundation certification (~$400 exam) to bridge into analyst work — this is the key differentiator. Gain exposure to business systems (ERP, CRM, ticketing). Target junior analyst or business systems analyst roles at 2–3 years. PMP or Six Sigma Green Belt (~$400–$600) accelerates path to lead analyst. Total cert cost: ~$1,500–$2,000.",
    },

    "33-3021.00": {  # Detectives and Criminal Investigators — BLS median $93,580
        "Calculation Type": "ladder",
        "Unpaid Training Years": "0",
        "Training Cost ($)": "0",
        "Yr1 ($)": "60000",  # Patrol officer Yr1 (blended academy + probationary patrol)
        "Yr2 ($)": "62500",  # Step increase
        "Yr3 ($)": "65000",
        "Yr4 ($)": "67500",
        "Yr5 ($)": "70000",
        "Yr6 ($)": "72500",  # Patrol, testing for detective
        "Yr7 ($)": "85000",  # Detective promotion (~$12.5k bump at Yr7, midpoint of 5–8yr range)
        "Yr8 ($)": "87550",  # 3% growth
        "Yr9 ($)": "90177",  # 3%
        "Yr10 ($)": "93580", # BLS median (~3.8%, close enough)
        "10-Year Net Earnings ($)": "753807",
        "10-Year Net Earnings Calculation": "Yr1 $60,000 + Yr2 $62,500 + Yr3 $65,000 + Yr4 $67,500 + Yr5 $70,000 + Yr6 $72,500 + Yr7 $85,000 + Yr8 $87,550 + Yr9 $90,177 + Yr10 $93,580 = $753,807 − $0 training = $753,807",
        "10-Year Net Earnings Calculation Model": "1. Paid Training (Employer pays trainee): Police academy (~6 months, paid from day one — ~$40k–$50k annualized during academy, blending to ~$60k first full year). 0 unpaid years, $0 cost — department covers all training. Canonical Police Family path — mapped from day one of the patrol officer career.\n2. Yr1–6: Patrol officer with municipal step increases (~$60k → $72.5k, ~$2,500/year). Yr7: Promoted to detective via competitive exam or appointment (midpoint of 5–8 year range), ~$12.5k bump to $85k. Yr8–10: Detective salary grows ~3%/year toward the BLS median ($93,580). Pay varies by assignment (homicide, narcotics, cybercrime) and department size.",
        "Difficulty Score": "High",
        "Difficulty Score Explanation": "Entry itself is competitive — police academies require passing written exams, physical fitness tests (timed runs, push-ups, sit-ups), a comprehensive background investigation, and a psychological evaluation; failure rates at any stage are significant. Academy washout rates vary by department. Beyond entry, earning a detective shield requires 5–8 years of exemplary patrol performance and passing competitive promotional exams or departmental selection boards — only a fraction of patrol officers advance.",
        "How to Get There": "Pass written civil service exam, physical fitness test (POPAT or similar), background investigation, polygraph, and psychological evaluation — each is a separate elimination round. Complete 5–6 month paid police academy. Serve 1–2 year probationary period on patrol. Build 5–8 years of strong patrol record (arrests, case clearance, no disciplinary issues). Apply for detective bureau via written promotional exam or supervisor appointment. Some departments require completion of detective investigation courses (e.g., Reid Technique, FDLE certifications). No out-of-pocket cost — department pays for all training.",
    },

    "33-2021.00": {  # Fire Inspectors and Investigators — BLS median $78,060
        "Calculation Type": "ladder",
        "Unpaid Training Years": "0",
        "Training Cost ($)": "0",
        "Yr1 ($)": "45000",  # Firefighter Yr1 (blended academy + probationary)
        "Yr2 ($)": "47000",  # Step increase
        "Yr3 ($)": "49000",
        "Yr4 ($)": "51000",
        "Yr5 ($)": "53000",
        "Yr6 ($)": "55000",  # Senior firefighter, pursuing NFPA inspector certs
        "Yr7 ($)": "72000",  # Inspector/Investigator promotion (~$17k specialty bump + grade reclassification)
        "Yr8 ($)": "74160",  # 3%
        "Yr9 ($)": "76385",  # 3%
        "Yr10 ($)": "78060", # BLS median (~2.2%, close enough)
        "10-Year Net Earnings ($)": "600605",
        "10-Year Net Earnings Calculation": "Yr1 $45,000 + Yr2 $47,000 + Yr3 $49,000 + Yr4 $51,000 + Yr5 $53,000 + Yr6 $55,000 + Yr7 $72,000 + Yr8 $74,160 + Yr9 $76,385 + Yr10 $78,060 = $600,605 − $0 training = $600,605",
        "10-Year Net Earnings Calculation Model": "1. Paid Training (Employer pays trainee): Firefighter academy (~4–6 months, paid from day one — ~$40k annualized during academy, blending to ~$45k first full year). 0 unpaid years, $0 cost. Canonical Fire Family path — mapped from day one of the firefighter career.\n2. Yr1–6: Firefighter with annual step increases (~$45k → $55k). During Yr5–6, complete NFPA 1031 Inspector I/II and NFPA 921 fire investigation coursework while on active duty (department-funded). Yr7: Promoted to fire inspector or investigator — specialty reclassification brings a ~$17k bump to ~$72k. Yr8–10: Inspector salary grows ~3%/year toward the BLS median ($78,060).",
        "Difficulty Score": "Medium",
        "Difficulty Score Explanation": "Entry as a firefighter is moderately competitive — requires passing written exam, Candidate Physical Ability Test (CPAT), background check, and medical clearance; CPAT is physically demanding and many candidates fail. After several years on the job, the inspector promotion is competitive within the department and requires earning NFPA 1031 certifications. The inspector role itself demands meticulous knowledge of fire codes, building construction, and legal documentation for arson investigations.",
        "How to Get There": "Apply to a municipal fire department. Pass written civil service exam, Candidate Physical Ability Test (CPAT — ~$150 registration fee, prep is physical training), medical exam, and background check. Complete a 4–6 month paid firefighter academy ($0 cost). After 1-year probation and several years of active firefighting, pursue inspector track: complete NFPA 1031 Inspector I and Inspector II (department typically covers coursework costs). Add NFPA 921 fire investigation training for investigator roles. Some departments accept direct-hire inspectors from building/fire safety backgrounds, but the firefighter pathway is most common.",
    },

    "11-3051.00": {  # Industrial Production Managers — BLS median $121,440
        "Calculation Type": "ladder",
        "Unpaid Training Years": "0",
        "Training Cost ($)": "0",
        "Yr1 ($)": "35000",   # Entry production worker/line operator
        "Yr2 ($)": "36000",   # ~3%
        "Yr3 ($)": "40000",   # Promoted to team lead
        "Yr4 ($)": "44000",   # Team lead with experience
        "Yr5 ($)": "52000",   # First-line supervisor
        "Yr6 ($)": "58000",   # Supervisor, multi-shift
        "Yr7 ($)": "70000",   # Shift manager / senior supervisor
        "Yr8 ($)": "85000",   # Area manager / junior production manager
        "Yr9 ($)": "102000",  # Production manager, mid-sized facility
        "Yr10 ($)": "121440", # BLS median, large-facility manager
        "10-Year Net Earnings ($)": "643440",
        "10-Year Net Earnings Calculation": "Yr1 $35,000 + Yr2 $36,000 + Yr3 $40,000 + Yr4 $44,000 + Yr5 $52,000 + Yr6 $58,000 + Yr7 $70,000 + Yr8 $85,000 + Yr9 $102,000 + Yr10 $121,440 = $643,440 − $0 training = $643,440",
        "10-Year Net Earnings Calculation Model": "1. Paid Training (Employer pays trainee): Start as an entry-level production worker or machine operator. On-the-job training from day one — 0 unpaid years, $0 cost. OSHA 10 certification often provided free by employer. Canonical Industrial Production Family path — mapped from day one on the production floor.\n2. Yr1–2: Production worker/line operator (~$35k–$36k), learning machinery, safety, and quality protocols. Yr3–4: Team lead or line lead after demonstrating reliability (~$40k–$44k). Yr5–6: First-line production supervisor, managing a crew (~$52k–$58k). Yr7: Shift manager or senior supervisor (~$70k). Yr8–10: Area manager to production manager at progressively larger facilities (~$85k–$121k). Salary acceleration at Yr8+ reflects facility-size premiums; automotive, aerospace, and pharma manufacturers pay significantly above median.",
        "Difficulty Score": "Medium",
        "Difficulty Score Explanation": "No formal education barriers at entry — production worker roles are widely accessible. The challenge is the long climb: moving from floor worker to manager requires 7–10 years of consistent performance, reliability under pressure, and demonstrated ability to manage people and production targets. Physical demands are moderate (standing, machinery operation). Management roles require navigating labor relations, safety compliance (OSHA), and production scheduling. Lean/Six Sigma certifications are increasingly expected at manager level.",
        "How to Get There": "Apply directly for a production worker, machine operator, or assembly line role at a manufacturing plant — no degree required. Earn OSHA 10 certification (often free through employer). Move into team lead by Yr2–3 by showing consistency. Pursue first-line supervisor role by Yr4–5. An optional Six Sigma Yellow Belt or Green Belt certification (~$200–$500 self-study) signals readiness for management and can compress the timeline. At large manufacturers (automotive OEMs, defense contractors, food processors), formal internal leadership development programs accelerate the path to production manager.",
    },
}

src = "data/top_no_degree_careers/ai_resilience_scores-associates-5.5-enriched.csv"
tmp = src + ".tmp"

with open(src, newline='', encoding='utf-8') as fin, \
     open(tmp, 'w', newline='', encoding='utf-8') as fout:
    reader = csv.DictReader(fin)
    writer = csv.DictWriter(fout, fieldnames=reader.fieldnames)
    writer.writeheader()
    for row in reader:
        if row['Code'] in FIXES:
            row.update(FIXES[row['Code']])
        writer.writerow(row)

os.replace(tmp, src)
print("Done. Updated 5 rows.")
