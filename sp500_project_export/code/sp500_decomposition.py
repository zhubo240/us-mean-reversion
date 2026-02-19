"""
S&P 500 三层回报分解与均值回归验证

三层结构：
  Level 3: 公司级别 → Level 2: GICS 行业 → Level 1: 总量
每年分解：
  总回报 = 价格回报 + 股息率
  价格回报 = 盈利增长 + PE 扩张
验证：Σ公司 = Σ行业 = 总量

数据来源：Compustat 年度财务 + CCM Link + S&P 500 成分股
分析区间：1985-2024 (GICS 覆盖 >93%)
"""
import csv
import os
import json
from collections import defaultdict

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'crsp_compustat')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

GICS_SECTORS = {
    '10': 'Energy', '15': 'Materials', '20': 'Industrials',
    '25': 'Cons Disc', '30': 'Cons Staples', '35': 'Health Care',
    '40': 'Financials', '45': 'Info Tech', '50': 'Telecom',
    '55': 'Utilities', '60': 'Real Estate',
}

START_YEAR = 1985
END_YEAR = 2024

# ── 数据加载工具 ──────────────────────────────────────────

def safe_float(val):
    try:
        return float(val) if val and val.strip() else None
    except ValueError:
        return None

def load_csv(filename):
    with open(os.path.join(DATA_DIR, filename), 'r') as f:
        return list(csv.DictReader(f))

def build_permno_to_gvkey(ccm_rows):
    mapping = {}
    for r in ccm_rows:
        permno = r['LPERMNO']
        gvkey = r['gvkey']
        linkdt = r['LINKDT']
        linkenddt = r['LINKENDDT'] if r['LINKENDDT'] != 'E' else '2099-12-31'
        priority = {'P': 0, 'C': 1, 'J': 2, 'N': 3}.get(r['LINKPRIM'], 4)
        if permno not in mapping:
            mapping[permno] = []
        mapping[permno].append((gvkey, linkdt, linkenddt, priority))
    for permno in mapping:
        mapping[permno].sort(key=lambda x: x[3])
    return mapping

def get_gvkey(mapping, permno, year):
    if permno not in mapping:
        return None
    year_str = f"{year}-06-30"
    for gvkey, linkdt, linkenddt, _ in mapping[permno]:
        if linkdt <= year_str and linkenddt >= year_str:
            return gvkey
    return mapping[permno][0][0] if mapping[permno] else None

def build_sp500_by_year(sp500_rows):
    yearly = defaultdict(set)
    for r in sp500_rows:
        permno = r['permno']
        s = int(r['start'][:4])
        e = int(r['ending'][:4])
        for year in range(max(s, START_YEAR - 1), min(e, END_YEAR) + 1):
            yearly[year].add(permno)
    return yearly

def build_compustat_lookup(rows):
    lookup = {}
    for r in rows:
        gvkey = r['gvkey']
        if not r['datadate']:
            continue
        year = int(r['datadate'][:4])
        month = int(r['datadate'][5:7])
        fy = year if month >= 6 else year - 1
        key = (gvkey, fy)
        if key not in lookup or r['datadate'] > lookup[key]['datadate']:
            lookup[key] = r
    return lookup

# ── Level 3: 公司级别记录 ────────────────────────────────

def build_company_records(sp500_by_year, permno_to_gvkey, compustat_lookup, gvkey_to_name):
    print("构建公司级别记录 (Level 3)...")
    records = []

    for year in range(START_YEAR, END_YEAR + 1):
        permnos = sp500_by_year.get(year, set())
        for permno in permnos:
            gvkey = get_gvkey(permno_to_gvkey, permno, year)
            if not gvkey:
                continue
            curr = compustat_lookup.get((gvkey, year))
            if not curr:
                continue
            prior = compustat_lookup.get((gvkey, year - 1))

            ni = safe_float(curr['ni'])
            csho = safe_float(curr['csho'])
            prcc_f = safe_float(curr['prcc_f'])
            epspx = safe_float(curr['epspx'])
            dvpsx_f = safe_float(curr['dvpsx_f'])
            gind = curr.get('gind', '').strip()
            sector = gind[:2] if gind and len(gind) >= 2 and gind[:2] in GICS_SECTORS else 'XX'

            ni_prior = safe_float(prior['ni']) if prior else None
            csho_prior = safe_float(prior['csho']) if prior else None
            prcc_f_prior = safe_float(prior['prcc_f']) if prior else None
            epspx_prior = safe_float(prior['epspx']) if prior else None

            mktcap = csho * prcc_f if csho and prcc_f and prcc_f > 0 else None
            mktcap_prior = csho_prior * prcc_f_prior if csho_prior and prcc_f_prior and prcc_f_prior > 0 else None

            price_ret = (prcc_f / prcc_f_prior - 1) if prcc_f and prcc_f_prior and prcc_f_prior > 0 else None

            div_yield = None
            total_div = None
            if dvpsx_f is not None and csho is not None:
                total_div = dvpsx_f * csho
                if mktcap_prior and mktcap_prior > 0:
                    div_yield = total_div / mktcap_prior

            pe = prcc_f / epspx if prcc_f and epspx and epspx > 0 else None
            pe_prior = prcc_f_prior / epspx_prior if prcc_f_prior and epspx_prior and epspx_prior > 0 else None

            records.append({
                'year': year,
                'permno': permno,
                'gvkey': gvkey,
                'name': gvkey_to_name.get(gvkey, ''),
                'sector': sector,
                'sector_name': GICS_SECTORS.get(sector, 'Unknown'),
                'ni': ni,
                'ni_prior': ni_prior,
                'mktcap': mktcap,
                'mktcap_prior': mktcap_prior,
                'total_div': total_div,
                'price_return': price_ret,
                'dividend_yield': div_yield,
                'pe': pe,
                'pe_prior': pe_prior,
            })

    print(f"  公司记录数: {len(records)} ({START_YEAR}-{END_YEAR})")
    return records

# ── Level 2: 行业汇总 ────────────────────────────────────

def aggregate_to_sectors(company_records):
    print("汇总到行业 (Level 2)...")
    buckets = defaultdict(lambda: {
        'ni': 0, 'ni_prior': 0, 'mktcap': 0, 'mktcap_prior': 0,
        'dividends': 0, 'count': 0,
        'ni_valid': 0, 'ni_prior_valid': 0,
        'mktcap_valid': 0, 'mktcap_prior_valid': 0,
    })

    for r in company_records:
        key = (r['year'], r['sector'])
        b = buckets[key]
        b['count'] += 1
        if r['ni'] is not None:
            b['ni'] += r['ni']
            b['ni_valid'] += 1
        if r['ni_prior'] is not None:
            b['ni_prior'] += r['ni_prior']
            b['ni_prior_valid'] += 1
        if r['mktcap'] is not None:
            b['mktcap'] += r['mktcap']
            b['mktcap_valid'] += 1
        if r['mktcap_prior'] is not None:
            b['mktcap_prior'] += r['mktcap_prior']
            b['mktcap_prior_valid'] += 1
        if r['total_div'] is not None:
            b['dividends'] += r['total_div']

    sector_data = {}
    for (year, sector), b in buckets.items():
        mc = b['mktcap']
        mc_p = b['mktcap_prior']
        ni = b['ni']
        ni_p = b['ni_prior']
        div = b['dividends']

        price_ret = (mc / mc_p - 1) if mc > 0 and mc_p > 0 else None
        div_yield = (div / mc_p) if mc_p > 0 and div > 0 else None
        earn_growth = (ni / ni_p - 1) if ni_p > 0 and ni > 0 else None

        pe_expansion = None
        if price_ret is not None and earn_growth is not None:
            pe_expansion = price_ret - earn_growth

        pe = mc / ni if mc > 0 and ni > 0 else None
        pe_prior = mc_p / ni_p if mc_p > 0 and ni_p > 0 else None

        sector_data[(year, sector)] = {
            'year': year,
            'sector': sector,
            'sector_name': GICS_SECTORS.get(sector, 'Unknown'),
            'count': b['count'],
            'ni': round(ni, 1),
            'ni_prior': round(ni_p, 1),
            'mktcap': round(mc, 1),
            'mktcap_prior': round(mc_p, 1),
            'dividends': round(div, 1),
            'price_return': price_ret,
            'dividend_yield': div_yield,
            'earnings_growth': earn_growth,
            'pe_expansion': pe_expansion,
            'pe': pe,
            'pe_prior': pe_prior,
        }

    return sector_data

# ── Level 1: 总量汇总 ────────────────────────────────────

def aggregate_to_total(sector_data):
    print("汇总到总量 (Level 1)...")
    yearly = defaultdict(lambda: {
        'ni': 0, 'ni_prior': 0, 'mktcap': 0, 'mktcap_prior': 0,
        'dividends': 0, 'count': 0, 'sector_count': 0,
    })

    for (year, sector), sd in sector_data.items():
        y = yearly[year]
        y['ni'] += sd['ni']
        y['ni_prior'] += sd['ni_prior']
        y['mktcap'] += sd['mktcap']
        y['mktcap_prior'] += sd['mktcap_prior']
        y['dividends'] += sd['dividends']
        y['count'] += sd['count']
        y['sector_count'] += 1

    agg_data = {}
    for year in range(START_YEAR, END_YEAR + 1):
        y = yearly.get(year)
        if not y:
            continue
        mc = y['mktcap']
        mc_p = y['mktcap_prior']
        ni = y['ni']
        ni_p = y['ni_prior']
        div = y['dividends']

        price_ret = (mc / mc_p - 1) if mc > 0 and mc_p > 0 else None
        div_yield = (div / mc_p) if mc_p > 0 and div > 0 else None
        earn_growth = (ni / ni_p - 1) if ni_p > 0 and ni > 0 else None
        pe_expansion = (price_ret - earn_growth) if price_ret is not None and earn_growth is not None else None
        pe = mc / ni if mc > 0 and ni > 0 else None

        total_ret = None
        if price_ret is not None:
            total_ret = price_ret + (div_yield or 0)

        agg_data[year] = {
            'year': year,
            'count': y['count'],
            'sector_count': y['sector_count'],
            'ni': round(ni, 1),
            'ni_prior': round(ni_p, 1),
            'mktcap': round(mc, 1),
            'mktcap_prior': round(mc_p, 1),
            'dividends': round(div, 1),
            'price_return': price_ret,
            'dividend_yield': div_yield,
            'total_return': total_ret,
            'earnings_growth': earn_growth,
            'pe_expansion': pe_expansion,
            'pe': pe,
        }

    return agg_data

# ── 行业对总量的贡献 ─────────────────────────────────────

def compute_contributions(sector_data, agg_data):
    print("计算行业贡献...")
    for (year, sector), sd in sector_data.items():
        agg = agg_data.get(year)
        if not agg or not agg['mktcap_prior'] or agg['mktcap_prior'] <= 0:
            sd['weight'] = None
            sd['contrib_price'] = None
            sd['contrib_div'] = None
            sd['contrib_earn'] = None
            sd['contrib_pe'] = None
            continue

        weight = sd['mktcap_prior'] / agg['mktcap_prior']
        sd['weight'] = weight
        sd['contrib_price'] = weight * sd['price_return'] if sd['price_return'] is not None else None
        sd['contrib_div'] = weight * sd['dividend_yield'] if sd['dividend_yield'] is not None else None
        sd['contrib_earn'] = weight * sd['earnings_growth'] if sd['earnings_growth'] is not None else None
        sd['contrib_pe'] = weight * sd['pe_expansion'] if sd['pe_expansion'] is not None else None

# ── 验证表 ────────────────────────────────────────────────

def build_verification(company_records, sector_data, agg_data):
    print("构建验证表...")
    # Σ公司
    company_sums = defaultdict(lambda: {'ni': 0, 'mktcap': 0, 'dividends': 0})
    for r in company_records:
        cs = company_sums[r['year']]
        if r['ni'] is not None:
            cs['ni'] += r['ni']
        if r['mktcap'] is not None:
            cs['mktcap'] += r['mktcap']
        if r['total_div'] is not None:
            cs['dividends'] += r['total_div']

    # Σ行业
    sector_sums = defaultdict(lambda: {'ni': 0, 'mktcap': 0, 'dividends': 0, 'contrib_price': 0})
    for (year, sector), sd in sector_data.items():
        ss = sector_sums[year]
        ss['ni'] += sd['ni']
        ss['mktcap'] += sd['mktcap']
        ss['dividends'] += sd['dividends']
        if sd.get('contrib_price') is not None:
            ss['contrib_price'] += sd['contrib_price']

    verification = []
    for year in range(START_YEAR, END_YEAR + 1):
        agg = agg_data.get(year)
        cs = company_sums.get(year, {})
        ss = sector_sums.get(year, {})
        if not agg:
            continue

        v = {
            'year': year,
            'agg_ni': round(agg['ni'], 1),
            'sum_company_ni': round(cs.get('ni', 0), 1),
            'sum_sector_ni': round(ss.get('ni', 0), 1),
            'diff_ni': round(agg['ni'] - cs.get('ni', 0), 1),
            'agg_mktcap': round(agg['mktcap'], 1),
            'sum_company_mktcap': round(cs.get('mktcap', 0), 1),
            'sum_sector_mktcap': round(ss.get('mktcap', 0), 1),
            'diff_mktcap': round(agg['mktcap'] - cs.get('mktcap', 0), 1),
            'agg_price_return': agg.get('price_return'),
            'sum_sector_contrib_price': ss.get('contrib_price', 0),
        }
        if v['agg_price_return'] is not None:
            v['diff_return'] = round((v['agg_price_return'] - v['sum_sector_contrib_price']) * 10000, 2)  # bps
        else:
            v['diff_return'] = None
        verification.append(v)

    return verification

# ── 滚动窗口分解 ─────────────────────────────────────────

def compute_rolling(agg_data, windows=(5, 10, 20)):
    print("计算滚动窗口分解...")
    rolling = {}
    for w in windows:
        results = []
        for end_year in range(START_YEAR + w - 1, END_YEAR + 1):
            start_year = end_year - w
            # start_year 是窗口起始的前一年（作为基准）
            agg_start = agg_data.get(start_year)
            agg_end = agg_data.get(end_year)
            if not agg_start or not agg_end:
                continue
            mc_s = agg_start['mktcap']
            mc_e = agg_end['mktcap']
            ni_s = agg_start['ni']
            ni_e = agg_end['ni']

            if not mc_s or mc_s <= 0 or not mc_e or mc_e <= 0:
                continue

            ann_price = (mc_e / mc_s) ** (1/w) - 1

            ann_earn = None
            ann_pe = None
            if ni_s > 0 and ni_e > 0:
                ann_earn = (ni_e / ni_s) ** (1/w) - 1
                ann_pe = (1 + ann_price) / (1 + ann_earn) - 1

            # 平均股息率
            div_sum = 0
            div_count = 0
            for y in range(start_year + 1, end_year + 1):
                a = agg_data.get(y)
                if a and a.get('dividend_yield') is not None:
                    div_sum += a['dividend_yield']
                    div_count += 1
            avg_div = div_sum / div_count if div_count > 0 else None

            ann_total = ann_price + avg_div if avg_div is not None else ann_price

            results.append({
                'start': start_year + 1,
                'end': end_year,
                'ann_total_return': round(ann_total * 100, 2),
                'ann_price_return': round(ann_price * 100, 2),
                'ann_earnings_growth': round(ann_earn * 100, 2) if ann_earn is not None else None,
                'ann_pe_expansion': round(ann_pe * 100, 2) if ann_pe is not None else None,
                'ann_dividend_yield': round(avg_div * 100, 2) if avg_div is not None else None,
            })
        rolling[w] = results

    return rolling

# ── 均值回归统计 ──────────────────────────────────────────

def compute_mean_reversion(rolling):
    print("计算均值回归统计...")
    stats = {}
    for w, results in rolling.items():
        totals = [r['ann_total_return'] for r in results if r['ann_total_return'] is not None]
        if not totals:
            continue
        mean = sum(totals) / len(totals)
        std = (sum((t - mean)**2 for t in totals) / len(totals)) ** 0.5
        stats[w] = {
            'window': w,
            'samples': len(totals),
            'mean': round(mean, 2),
            'std': round(std, 2),
            'min': round(min(totals), 2),
            'max': round(max(totals), 2),
            'range': round(max(totals) - min(totals), 2),
        }
    return stats

# ── Top Contributors ─────────────────────────────────────

def find_top_contributors(company_records, n=10):
    print("找 Top Contributors...")
    by_year = defaultdict(list)
    for r in company_records:
        by_year[r['year']].append(r)

    top = []
    for year in range(START_YEAR, END_YEAR + 1):
        recs = by_year.get(year, [])

        # Top earnings change
        earn_changes = []
        for r in recs:
            if r['ni'] is not None and r['ni_prior'] is not None:
                earn_changes.append({
                    'name': r['name'], 'sector': r['sector_name'],
                    'change': r['ni'] - r['ni_prior'],
                    'ni': r['ni'], 'ni_prior': r['ni_prior'],
                })
        earn_changes.sort(key=lambda x: abs(x['change']), reverse=True)

        # Top PE movers (by market cap impact)
        pe_movers = []
        for r in recs:
            if r['pe'] is not None and r['pe_prior'] is not None and r['mktcap'] is not None:
                pe_change = r['pe'] - r['pe_prior']
                pe_movers.append({
                    'name': r['name'], 'sector': r['sector_name'],
                    'pe_change': pe_change,
                    'pe': r['pe'], 'pe_prior': r['pe_prior'],
                    'mktcap': r['mktcap'],
                })
        pe_movers.sort(key=lambda x: abs(x['pe_change'] * x['mktcap']), reverse=True)

        top.append({
            'year': year,
            'top_earnings': earn_changes[:n],
            'top_pe': pe_movers[:n],
        })

    return top

# ── 主流程 ────────────────────────────────────────────────

def main():
    print("=" * 80)
    print("S&P 500 三层回报分解 (1985-2024)")
    print("=" * 80)

    # 加载数据
    print("\n加载数据...")
    sp500_rows = load_csv('sp500_constituents.csv')
    ccm_rows = load_csv('ccm_link_table.csv')
    compustat_rows = load_csv('compustat_annual.csv')

    print("构建映射...")
    permno_to_gvkey = build_permno_to_gvkey(ccm_rows)
    sp500_by_year = build_sp500_by_year(sp500_rows)
    compustat_lookup = build_compustat_lookup(compustat_rows)
    gvkey_to_name = {}
    for r in ccm_rows:
        gvkey_to_name[r['gvkey']] = r['conm']

    # Level 3: 公司
    company_records = build_company_records(
        sp500_by_year, permno_to_gvkey, compustat_lookup, gvkey_to_name)

    # Level 2: 行业
    sector_data = aggregate_to_sectors(company_records)

    # Level 1: 总量
    agg_data = aggregate_to_total(sector_data)

    # 行业贡献
    compute_contributions(sector_data, agg_data)

    # 验证
    verification = build_verification(company_records, sector_data, agg_data)

    # 滚动窗口
    rolling = compute_rolling(agg_data)

    # 均值回归统计
    mr_stats = compute_mean_reversion(rolling)

    # Top Contributors
    top_contrib = find_top_contributors(company_records)

    # ── 输出 JSON ──
    print("\n保存 JSON...")

    # 压缩公司记录（只保留有效字段，四舍五入）
    company_out = []
    for r in company_records:
        company_out.append({
            'y': r['year'],
            'p': r['permno'],
            'n': r['name'],
            's': r['sector'],
            'sn': r['sector_name'],
            'ni': r['ni'],
            'ni_p': r['ni_prior'],
            'mc': round(r['mktcap'], 1) if r['mktcap'] else None,
            'mc_p': round(r['mktcap_prior'], 1) if r['mktcap_prior'] else None,
            'div': round(r['total_div'], 1) if r['total_div'] else None,
            'pr': round(r['price_return'], 4) if r['price_return'] is not None else None,
            'dy': round(r['dividend_yield'], 4) if r['dividend_yield'] is not None else None,
            'pe': round(r['pe'], 2) if r['pe'] is not None else None,
            'pe_p': round(r['pe_prior'], 2) if r['pe_prior'] is not None else None,
        })

    # 行业数据
    sector_out = []
    for (year, sector), sd in sorted(sector_data.items()):
        rec = {k: (round(v, 4) if isinstance(v, float) and v is not None else v)
               for k, v in sd.items()}
        sector_out.append(rec)

    # 总量数据
    agg_out = []
    for year in sorted(agg_data.keys()):
        ad = agg_data[year]
        rec = {k: (round(v, 4) if isinstance(v, float) and v is not None else v)
               for k, v in ad.items()}
        agg_out.append(rec)

    output = {
        'metadata': {
            'analysis_window': f'{START_YEAR}-{END_YEAR}',
            'methodology': 'Compustat fiscal-year prices; Total Return = Earnings Growth + PE Expansion + Dividend Yield',
        },
        'aggregate': agg_out,
        'sectors': sector_out,
        'companies': company_out,
        'verification': verification,
        'rolling': {str(k): v for k, v in rolling.items()},
        'mean_reversion': {str(k): v for k, v in mr_stats.items()},
        'top_contributors': top_contrib,
    }

    path = os.path.join(OUTPUT_DIR, 'sp500_3level_decomposition.json')
    with open(path, 'w') as f:
        json.dump(output, f, indent=2, default=str)
    fsize = os.path.getsize(path) / 1024 / 1024
    print(f"  已保存: sp500_3level_decomposition.json ({fsize:.1f} MB)")

    # ── 打印摘要 ──
    print("\n" + "=" * 80)
    print("摘要")
    print("=" * 80)

    print(f"\n  公司记录: {len(company_records)}")
    print(f"  行业-年: {len(sector_data)}")
    print(f"  年度数: {len(agg_data)}")

    # 验证通过率
    max_diff_ni = max(abs(v['diff_ni']) for v in verification)
    max_diff_mc = max(abs(v['diff_mktcap']) for v in verification)
    max_diff_ret = max(abs(v['diff_return']) for v in verification if v['diff_return'] is not None)
    print(f"\n  验证:")
    print(f"    Σ公司 vs 总量 盈利最大差: ${max_diff_ni}M")
    print(f"    Σ公司 vs 总量 市值最大差: ${max_diff_mc}M")
    print(f"    Σ行业贡献 vs 总量回报最大差: {max_diff_ret} bps")

    # 均值回归
    print(f"\n  均值回归:")
    for w in sorted(mr_stats.keys()):
        s = mr_stats[w]
        print(f"    {w}年窗口: 均值 {s['mean']:.2f}%, 标准差 {s['std']:.2f}%, "
              f"范围 [{s['min']:.2f}%, {s['max']:.2f}%]")

if __name__ == "__main__":
    main()
