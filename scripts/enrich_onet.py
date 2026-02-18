#!/usr/bin/env python3
"""
Enrich O*NET occupations CSV with wage, projected growth, and projected job openings
scraped from onetonline.org.

Uses an intermediate JSON file to cache results, so the script can be resumed
if interrupted.
"""

import csv
import json
import os
import re
import time
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

INPUT_CSV = Path(__file__).parent.parent / "data" / "input" / "All_Occupations_ONET.csv"
CACHE_FILE = Path(__file__).parent.parent / "data" / "intermediate" / "onet_enrichment_cache.json"
OUTPUT_CSV = Path(__file__).parent.parent / "data" / "input" / "All_Occupations_ONET.csv"

HEADERS = {"User-Agent": "Mozilla/5.0 (research project)"}
DELAY = 1.0  # seconds between requests to be polite


class OnetPageParser(HTMLParser):
    """Extract wage, growth, and job openings from an O*NET summary page."""

    def __init__(self):
        super().__init__()
        self._in_dt = False
        self._in_dd = False
        self._current_field = None
        self._capture = False
        self._text_buf = []

        self.median_wage = None
        self.projected_growth = None
        self.projected_job_openings = None

    def handle_starttag(self, tag, attrs):
        if tag == "dt":
            self._in_dt = True
            self._text_buf = []
        elif tag == "dd" and self._current_field:
            self._in_dd = True
            self._capture = True
            self._text_buf = []

    def handle_endtag(self, tag):
        if tag == "dt":
            self._in_dt = False
            dt_text = "".join(self._text_buf).strip()
            if "Median wages" in dt_text:
                self._current_field = "wage"
            elif "Projected growth" in dt_text:
                self._current_field = "growth"
            elif "Projected job openings" in dt_text:
                self._current_field = "openings"
            else:
                self._current_field = None
        elif tag == "dd" and self._capture:
            self._in_dd = False
            self._capture = False
            dd_text = "".join(self._text_buf).strip()
            # Clean up whitespace
            dd_text = re.sub(r"\s+", " ", dd_text).strip()

            if self._current_field == "wage":
                self.median_wage = dd_text
            elif self._current_field == "growth":
                self.projected_growth = dd_text
            elif self._current_field == "openings":
                self.projected_job_openings = dd_text

            self._current_field = None

    def handle_data(self, data):
        if self._in_dt or self._capture:
            self._text_buf.append(data)


def fetch_onet_data(url: str) -> dict:
    """Fetch and parse a single O*NET occupation page."""
    req = urllib.request.Request(url, headers=HEADERS)
    resp = urllib.request.urlopen(req, timeout=30)
    html = resp.read().decode("utf-8", errors="replace")

    parser = OnetPageParser()
    parser.feed(html)

    return {
        "median_wage": parser.median_wage or "",
        "projected_growth": parser.projected_growth or "",
        "projected_job_openings": parser.projected_job_openings or "",
    }


def main():
    # Load cache
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    cache = {}
    if CACHE_FILE.exists():
        with open(CACHE_FILE) as f:
            cache = json.load(f)

    # Read input CSV
    with open(INPUT_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    total = len(rows)
    cached_count = sum(1 for r in rows if r["Code"] in cache)
    print(f"Total occupations: {total}, already cached: {cached_count}")

    # Fetch missing data
    for i, row in enumerate(rows):
        code = row["Code"]
        if code in cache:
            continue

        url = row["url"]
        print(f"[{i+1}/{total}] Fetching {code} - {row['Occupation']}...")
        try:
            data = fetch_onet_data(url)
            cache[code] = data
            print(f"  Wage: {data['median_wage']}")
            print(f"  Growth: {data['projected_growth']}")
            print(f"  Openings: {data['projected_job_openings']}")
        except Exception as e:
            print(f"  ERROR: {e}")
            cache[code] = {
                "median_wage": "",
                "projected_growth": "",
                "projected_job_openings": "",
            }

        # Save cache after each fetch
        with open(CACHE_FILE, "w") as f:
            json.dump(cache, f, indent=2)

        time.sleep(DELAY)

    # Write enriched CSV (avoid duplicating columns if already enriched)
    enrichment_cols = ["Median Wage", "Projected Growth", "Projected Job Openings"]
    existing = list(rows[0].keys())
    fieldnames = existing + [c for c in enrichment_cols if c not in existing]

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            code = row["Code"]
            enriched = cache.get(code, {})
            row["Median Wage"] = enriched.get("median_wage", "")
            row["Projected Growth"] = enriched.get("projected_growth", "")
            row["Projected Job Openings"] = enriched.get("projected_job_openings", "")
            writer.writerow(row)

    print(f"\nDone! Enriched CSV written to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
