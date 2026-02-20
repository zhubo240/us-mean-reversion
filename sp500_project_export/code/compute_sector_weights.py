#!/usr/bin/env python3
"""
Compute annual S&P 500 industry sector weights using CRSP monthly data.
For each December, finds S&P 500 constituents, computes market cap weights by sector.
Uses csv reader for memory efficiency (crsp_monthly.csv is ~369MB).
"""

import csv
import json
import sys
import time
from collections import defaultdict

# Paths
CRSP_PATH = "/Users/bozhu/.openclaw/workspace-us-mean-reversion/sp500_project_export/data/crsp_compustat/crsp_monthly.csv"
CONSTITUENTS_PATH = "/Users/bozhu/.openclaw/workspace-us-mean-reversion/sp500_project_export/data/crsp_compustat/sp500_constituents.csv"
OUTPUT_PATH = "/Users/bozhu/.openclaw/workspace-us-mean-reversion/sp500_project_export/data/sp500_sector_weights.json"


def classify_sic(sic_code):
    """Map SIC code to major sector (expanded to minimize 'Other')."""
    s = sic_code
    # Technology: computers, electronics, semiconductors, software, internet
    if (3570 <= s <= 3579 or 3600 <= s <= 3699 or 7370 <= s <= 7379
            or 3674 <= s <= 3699 or 3812 <= s <= 3812
            or 5045 <= s <= 5045 or 5065 <= s <= 5065):
        return "Technology"
    # Healthcare: pharma, medical devices, health services
    if (2830 <= s <= 2836 or 2840 <= s <= 2844
            or 3841 <= s <= 3851 or s == 5912
            or 8000 <= s <= 8099 or 2860 <= s <= 2869):
        return "Healthcare"
    # Financials: banks, insurance, real estate, investment
    if 6000 <= s <= 6799:
        return "Financials"
    # Energy: oil, gas, coal, pipelines
    if (1000 <= s <= 1499 or 2900 <= s <= 2999
            or 4610 <= s <= 4619 or 5171 <= s <= 5172):
        return "Energy"
    # Consumer Staples: food, beverages, tobacco, household products, supermarkets, drugstores
    if (2000 <= s <= 2199 or 2040 <= s <= 2099
            or 5400 <= s <= 5499 or 5900 <= s <= 5999
            or 5140 <= s <= 5149 or 5180 <= s <= 5182):
        return "Consumer Staples"
    # Consumer Discretionary: retail, autos, restaurants, hotels, media, entertainment, apparel
    if (5200 <= s <= 5399 or 5500 <= s <= 5799
            or 5600 <= s <= 5699 or 5700 <= s <= 5736
            or 7000 <= s <= 7299 or 7800 <= s <= 7999
            or 2700 <= s <= 2799 or 2710 <= s <= 2741
            or 3711 <= s <= 3716 or 3720 <= s <= 3728
            or 3140 <= s <= 3199
            or 5810 <= s <= 5813
            or 3944 <= s <= 3949 or 7900 <= s <= 7999):
        return "Consumer Discretionary"
    # Industrials: machinery, aerospace, defense, construction, transportation, conglomerates
    if (3400 <= s <= 3569 or 3700 <= s <= 3799 or 3800 <= s <= 3839
            or 3900 <= s <= 3999
            or 4000 <= s <= 4599  # rail, trucking, air transport, freight, pipelines
            or 1500 <= s <= 1799  # construction
            or 8700 <= s <= 8799  # engineering services
            or 3000 <= s <= 3099  # rubber & plastics (industrial)
            or 3100 <= s <= 3139  # leather (old industrial)
            or 9995 <= s <= 9999  # conglomerates
            ):
        return "Industrials"
    # Utilities
    if 4900 <= s <= 4999:
        return "Utilities"
    # Telecom: telephone, cable, wireless, internet services
    if 4800 <= s <= 4899:
        return "Telecom"
    # Materials: chemicals, paper, metals, glass, mining
    if (2200 <= s <= 2499 or 2600 <= s <= 2699
            or 2800 <= s <= 2829 or 3200 <= s <= 3399):
        return "Materials"
    return "Other"


def load_sp500_constituents():
    """
    Load S&P 500 membership as list of (permno, start_yyyymm, end_yyyymm).
    We convert dates to YYYYMM integers for fast comparison.
    """
    members = []
    with open(CONSTITUENTS_PATH, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            permno = int(row["permno"])
            # start date: YYYY-MM-DD -> YYYYMM
            start_parts = row["start"].split("-")
            start_ym = int(start_parts[0]) * 100 + int(start_parts[1])
            # end date
            end_str = row["ending"].strip()
            if end_str == "" or end_str.lower() == "na":
                end_ym = 209912  # still active, far future
            else:
                end_parts = end_str.split("-")
                end_ym = int(end_parts[0]) * 100 + int(end_parts[1])
            members.append((permno, start_ym, end_ym))
    return members


def build_membership_lookup(members):
    """
    Build a dict: permno -> list of (start_ym, end_ym) intervals.
    """
    lookup = defaultdict(list)
    for permno, start_ym, end_ym in members:
        lookup[permno].append((start_ym, end_ym))
    return dict(lookup)


def is_sp500_member(lookup, permno, yyyymm):
    """Check if permno was in S&P 500 during given YYYYMM."""
    intervals = lookup.get(permno)
    if intervals is None:
        return False
    for start_ym, end_ym in intervals:
        if start_ym <= yyyymm <= end_ym:
            return True
    return False


def main():
    t0 = time.time()

    # Step 1: Load S&P 500 constituents
    print("Loading S&P 500 constituents...")
    members = load_sp500_constituents()
    membership = build_membership_lookup(members)
    print(f"  Loaded {len(members)} membership records for {len(membership)} unique PERMNOs")

    # Step 2: Scan CRSP monthly, filter December rows for S&P 500 members
    # Accumulate: year -> sector -> total_mktcap
    sector_mktcap = defaultdict(lambda: defaultdict(float))
    # Also track counts for diagnostics
    year_counts = defaultdict(int)

    print("Scanning CRSP monthly data (December rows only)...")
    row_count = 0
    matched = 0
    skipped_no_price = 0
    skipped_no_sic = 0
    skipped_not_sp500 = 0

    with open(CRSP_PATH, "r") as f:
        reader = csv.reader(f)
        header = next(reader)
        # Build column index map
        col = {name: i for i, name in enumerate(header)}
        idx_permno = col["PERMNO"]
        idx_date = col["date"]
        idx_siccd = col["SICCD"]
        idx_prc = col["PRC"]
        idx_shrout = col["SHROUT"]

        for row in reader:
            row_count += 1
            if row_count % 1_000_000 == 0:
                elapsed = time.time() - t0
                print(f"  Processed {row_count:,} rows ({elapsed:.1f}s), {matched:,} matched so far")

            # Quick filter: only December dates (date field is YYYY-MM-DD, check month part)
            date_str = row[idx_date]
            if len(date_str) < 7:
                continue
            # Month is characters 5-6 (0-indexed)
            if date_str[5:7] != "12":
                continue

            # Parse year
            year = int(date_str[:4])

            # Parse PERMNO
            try:
                permno = int(row[idx_permno])
            except (ValueError, IndexError):
                continue

            # Check S&P 500 membership
            yyyymm = year * 100 + 12
            if not is_sp500_member(membership, permno, yyyymm):
                skipped_not_sp500 += 1
                continue

            # Parse PRC and SHROUT
            prc_str = row[idx_prc].strip()
            shrout_str = row[idx_shrout].strip()
            if prc_str == "" or shrout_str == "":
                skipped_no_price += 1
                continue

            try:
                prc = abs(float(prc_str))
                shrout = float(shrout_str)
            except ValueError:
                skipped_no_price += 1
                continue

            if prc <= 0 or shrout <= 0:
                skipped_no_price += 1
                continue

            # Parse SIC code
            sic_str = row[idx_siccd].strip()
            if sic_str == "":
                skipped_no_sic += 1
                continue
            try:
                sic_code = int(sic_str)
            except ValueError:
                skipped_no_sic += 1
                continue

            # Compute market cap (in thousands of dollars)
            mktcap = prc * shrout

            # Classify sector
            sector = classify_sic(sic_code)

            sector_mktcap[year][sector] += mktcap
            year_counts[year] += 1
            matched += 1

    elapsed = time.time() - t0
    print(f"  Done scanning. {row_count:,} total rows, {matched:,} matched.")
    print(f"  Skipped: {skipped_not_sp500:,} not S&P 500, {skipped_no_price:,} no price/shares, {skipped_no_sic:,} no SIC")
    print(f"  Time: {elapsed:.1f}s")

    # Step 3: Compute percentage weights
    print("\nComputing sector weights...")
    result = {}
    for year in sorted(sector_mktcap.keys()):
        sectors = sector_mktcap[year]
        total = sum(sectors.values())
        if total <= 0:
            continue
        weights = {}
        for sector, mktcap in sorted(sectors.items()):
            weights[sector] = round(mktcap / total * 100, 2)
        result[str(year)] = weights
        n_stocks = year_counts[year]
        top_sector = max(weights, key=weights.get)
        print(f"  {year}: {n_stocks} stocks, top sector: {top_sector} ({weights[top_sector]:.1f}%)")

    # Step 4: Save output
    with open(OUTPUT_PATH, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nSaved to {OUTPUT_PATH}")
    print(f"Years covered: {min(result.keys())} to {max(result.keys())}")
    print(f"Total time: {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
