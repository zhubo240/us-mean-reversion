"""
Compare CRSP vs Compustat market cap for S&P 500 constituents
"""
import csv, os

DATA = os.path.join(os.path.dirname(__file__), '..', 'data', 'crsp_compustat')

def load_csv(filename):
    with open(os.path.join(DATA, filename)) as f:
        return list(csv.DictReader(f))

def safe_float(v):
    try: return float(v)
    except: return None

# --- CRSP: December market cap per PERMNO per year ---
print("Loading CRSP monthly...")
crsp_mktcap = {}  # (permno, year) -> mktcap in $M
for row in load_csv('crsp_monthly.csv'):
    date = row.get('date', '')
    if not date: continue
    # December only
    parts = date.split('-') if '-' in date else [date[:4], date[4:6]] if len(date) >= 6 else []
    if len(parts) >= 2:
        year, month = int(parts[0]), int(parts[1])
    else:
        continue
    if month != 12: continue

    permno = row.get('PERMNO', '').strip()
    prc = safe_float(row.get('PRC'))
    shrout = safe_float(row.get('SHROUT'))
    if prc and shrout:
        mktcap = abs(prc) * shrout / 1000  # SHROUT in thousands, so mktcap in $M
        crsp_mktcap[(permno, year)] = mktcap

print(f"  CRSP December records: {len(crsp_mktcap):,}")

# --- Compustat: fiscal year-end market cap ---
print("Loading Compustat...")
comp_mktcap = {}  # (gvkey, year) -> mktcap in $M
for row in load_csv('compustat_annual.csv'):
    gvkey = row.get('gvkey', '').strip()
    datadate = row.get('datadate', '')
    prcc_f = safe_float(row.get('prcc_f'))
    csho = safe_float(row.get('csho'))
    if not datadate or not prcc_f or not csho: continue
    # datadate format: YYYY-MM-DD
    parts = datadate.split('-')
    if len(parts) != 3: continue
    year = int(parts[0])
    month = int(parts[1])
    # Fiscal years ending Jan-May: assign to prior calendar year
    if month <= 5:
        year -= 1
    comp_mktcap[(gvkey, year)] = prcc_f * csho  # already in $M

print(f"  Compustat records: {len(comp_mktcap):,}")

# --- CCM link: PERMNO -> GVKEY ---
print("Loading CCM links...")
permno_to_gvkey = {}
for row in load_csv('ccm_link_table.csv'):
    lp = row.get('LINKPRIM', '').strip()
    if lp not in ('P', 'C'): continue
    permno = row.get('LPERMNO', '').strip()
    gvkey = row.get('gvkey', '').strip()
    permno_to_gvkey[permno] = gvkey

# --- Compare ---
print("\nYear-by-year S&P 500 aggregate market cap comparison:\n")
print(f"{'Year':>6} {'CRSP ($T)':>12} {'Compustat ($T)':>14} {'Diff%':>8} {'#Match':>8} {'#CRSP':>8}")
print("-" * 62)

for year in range(1985, 2025):
    crsp_total = 0
    comp_total = 0
    matched = 0
    crsp_count = 0

    for (permno, y), cmk in crsp_mktcap.items():
        if y != year: continue
        crsp_total += cmk
        crsp_count += 1

        gvkey = permno_to_gvkey.get(permno)
        if gvkey and (gvkey, year) in comp_mktcap:
            comp_total += comp_mktcap[(gvkey, year)]
            matched += 1

    if crsp_total > 0 and comp_total > 0:
        diff_pct = (comp_total - crsp_total) / crsp_total * 100
        print(f"{year:>6} {crsp_total/1e6:>11,.2f} {comp_total/1e6:>13,.2f} {diff_pct:>+7.2f}% {matched:>8} {crsp_count:>8}")
