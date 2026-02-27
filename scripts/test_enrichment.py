#!/usr/bin/env python3
"""
Test the O*NET enrichment scraper on a sample of occupations.

Tests that the enrich_onet.py parser correctly extracts:
- Median wage
- Projected growth
- Projected job openings
- Education requirements
- Sample of reported job titles (NEW)

Usage:
    python3 scripts/test_enrichment.py

Output:
    Prints formatted results to console
    Saves enrichment data to data/output/test_enrichment.csv
"""

import csv
from pathlib import Path
from enrich_onet import fetch_onet_data

INPUT_CSV = Path(__file__).parent.parent / "data" / "input" / "All_Occupations_ONET.csv"
OUTPUT_CSV = Path(__file__).parent.parent / "data" / "output" / "test_enrichment.csv"
SAMPLE_SIZE = 3

EXPECTED_FIELDS = [
    "median_wage",
    "projected_growth",
    "projected_job_openings",
    "education_top_2",
    "top_education_level",
    "top_education_rate",
    "sample_job_titles",
]


def load_sample_occupations(n: int) -> list[dict]:
    """Load first n occupations from input CSV."""
    with open(INPUT_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [row for i, row in enumerate(reader) if i < n]


def display_result(index: int, occupation: dict, enriched_data: dict):
    """Display a single enriched result."""
    code = occupation["Code"]
    name = occupation["Occupation"]

    print(f"\n{'='*90}")
    print(f"[{index}] {code}: {name}")
    print(f"{'='*90}")

    print(f"  URL: {occupation['url']}\n")

    # Check for missing fields
    missing = [f for f in EXPECTED_FIELDS if f not in enriched_data or not enriched_data[f]]
    if missing:
        print(f"  ⚠ Missing fields: {', '.join(missing)}\n")

    # Display each field
    print(f"  Median Wage:")
    print(f"    {enriched_data.get('median_wage', 'N/A')}\n")

    print(f"  Projected Growth:")
    print(f"    {enriched_data.get('projected_growth', 'N/A')}\n")

    print(f"  Projected Job Openings:")
    print(f"    {enriched_data.get('projected_job_openings', 'N/A')}\n")

    print(f"  Education (all levels):")
    print(f"    {enriched_data.get('education_top_2', 'N/A')}\n")

    print(f"  Top Education Level:")
    print(f"    {enriched_data.get('top_education_level', 'N/A')}")
    print(f"    ({enriched_data.get('top_education_rate', '')})\n")

    print(f"  Sample Job Titles:")
    titles = enriched_data.get("sample_job_titles", "N/A")
    if titles and len(titles) > 100:
        print(f"    {titles[:97]}...\n")
    else:
        print(f"    {titles}\n")


def verify_all_fields(results: list[dict]) -> bool:
    """Verify all results have the core expected fields.

    Note: top_education_rate may be empty for occupations that use descriptive
    education format instead of percentage format.
    """
    required_fields = [
        "median_wage",
        "projected_growth",
        "projected_job_openings",
        "sample_job_titles",
    ]
    optional_fields = ["education_top_2", "top_education_level", "top_education_rate"]

    all_present = True
    for i, data in enumerate(results, 1):
        missing = [f for f in required_fields if f not in data or not data[f]]
        if missing:
            print(f"  ✗ Result {i} missing required fields: {', '.join(missing)}")
            all_present = False
        else:
            present_optional = [f for f in optional_fields if f in data and data[f]]
            print(f"  ✓ Result {i}: all required fields + {len(present_optional)}/{len(optional_fields)} optional")

    return all_present


def main():
    # Ensure output directory exists
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    print(f"\n🧪 O*NET Enrichment Test")
    print(f"Scraping {SAMPLE_SIZE} sample occupations\n")

    # Load sample occupations
    occupations = load_sample_occupations(SAMPLE_SIZE)
    if not occupations:
        print("Error: No occupations found in input CSV")
        return False

    print(f"✓ Loaded {len(occupations)} occupations:")
    for i, occ in enumerate(occupations, 1):
        print(f"  {i}. {occ['Occupation']} ({occ['Code']})")

    # Fetch enrichment data for each
    print(f"\n🔄 Fetching enrichment data...\n")
    results = []
    occupations_list = []
    for i, occ in enumerate(occupations, 1):
        code = occ["Code"]
        url = occ["url"]

        print(f"  [{i}/{len(occupations)}] Fetching {code}...", end="", flush=True)
        try:
            data = fetch_onet_data(url)
            results.append(data)
            occupations_list.append(occ)
            print(" ✓")
        except Exception as e:
            print(f" ✗ ({e})")
            return False

    # Display results
    print(f"\n✓ Successfully fetched {len(results)} occupations\n")
    for i, (occ, data) in enumerate(zip(occupations_list, results), 1):
        display_result(i, occ, data)

    # Verify all fields are present
    print(f"\n{'='*90}")
    print("VERIFICATION")
    print(f"{'='*90}\n")

    if not verify_all_fields(results):
        print("✗ Some fields are missing")
        return False

    print("✓ All expected fields present in all results!")

    # Write results to CSV (enrichment-only format, matching enrich_onet.py)
    print(f"\n{'='*90}")
    print("WRITING OUTPUT CSV")
    print(f"{'='*90}\n")

    enrichment_fieldnames = [
        "Code",
        "Median Wage",
        "Projected Growth",
        "Projected Job Openings",
        "Education",
        "Top Education Level",
        "Top Education Rate",
        "Sample Job Titles",
    ]

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=enrichment_fieldnames)
        writer.writeheader()
        for occ, enriched in zip(occupations_list, results):
            writer.writerow({
                "Code": occ["Code"],
                "Median Wage": enriched.get("median_wage", ""),
                "Projected Growth": enriched.get("projected_growth", ""),
                "Projected Job Openings": enriched.get("projected_job_openings", ""),
                "Education": enriched.get("education_top_2", ""),
                "Top Education Level": enriched.get("top_education_level", ""),
                "Top Education Rate": enriched.get("top_education_rate", ""),
                "Sample Job Titles": enriched.get("sample_job_titles", ""),
            })

    print(f"✓ Output saved to: {OUTPUT_CSV}")

    # Display CSV preview
    print(f"\n📊 CSV File Preview:")
    print(f"{'-'*90}")
    with open(OUTPUT_CSV, "r") as f:
        lines = f.readlines()
        for i, line in enumerate(lines[:4]):
            print(line.rstrip())
        if len(lines) > 4:
            print(f"... ({len(lines) - 4} more rows)")

    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
