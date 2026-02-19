"""
S&P 500 GICS 行业分析：
1. 各行业盈利、市值、PE 年度变化
2. 行业权重变迁
3. 行业对总盈利增长的贡献分解
4. 行业 PE 均值回归分析
5. 替换原 French 5 行业数据

数据：CRSP/Compustat 公司级别数据 (1962-2024)
GICS 覆盖率：1980+ >90%，主要分析聚焦 1980-2024
"""
import csv
import os
import json
from collections import defaultdict

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'crsp_compustat')

GICS_SECTORS = {
    '10': 'Energy',
    '15': 'Materials',
    '20': 'Industrials',
    '25': 'Cons Disc',
    '30': 'Cons Staples',
    '35': 'Health Care',
    '40': 'Financials',
    '45': 'Info Tech',
    '50': 'Telecom',
    '55': 'Utilities',
    '60': 'Real Estate',
}

def safe_float(val):
    try:
        return float(val) if val and val.strip() else None
    except ValueError:
        return None

def load_csv(filename):
    path = os.path.join(DATA_DIR, filename)
    with open(path, 'r') as f:
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
        start_year = int(r['start'][:4])
        end_year = int(r['ending'][:4])
        for year in range(max(start_year, 1962), min(end_year, 2024) + 1):
            yearly[year].add(permno)
    return yearly

def build_compustat_lookup(compustat_rows):
    lookup = {}
    for r in compustat_rows:
        gvkey = r['gvkey']
        if not r['datadate']:
            continue
        year = int(r['datadate'][:4])
        month = int(r['datadate'][5:7])
        fiscal_year = year if month >= 6 else year - 1
        key = (gvkey, fiscal_year)
        if key not in lookup or r['datadate'] > lookup[key]['datadate']:
            lookup[key] = r
    return lookup

def analyze():
    print("加载数据...")
    sp500_rows = load_csv('sp500_constituents.csv')
    ccm_rows = load_csv('ccm_link_table.csv')
    compustat_rows = load_csv('compustat_annual.csv')

    print("构建映射...")
    permno_to_gvkey = build_permno_to_gvkey(ccm_rows)
    sp500_by_year = build_sp500_by_year(sp500_rows)
    compustat_lookup = build_compustat_lookup(compustat_rows)

    print("计算行业年度数据...")

    # 存储结构: industry_data[year][sector] = {earnings, mktcap, dividends, companies}
    industry_data = {}

    for year in range(1962, 2025):
        permnos = sp500_by_year.get(year, set())
        if not permnos:
            continue

        sectors = defaultdict(lambda: {
            'earnings': 0, 'mktcap': 0, 'dividends': 0,
            'revenue': 0, 'companies': 0, 'total_companies': 0
        })
        no_gics_count = 0

        for permno in permnos:
            gvkey = get_gvkey(permno_to_gvkey, permno, year)
            if not gvkey:
                continue
            data = compustat_lookup.get((gvkey, year))
            if not data:
                continue

            ni = safe_float(data['ni'])
            csho = safe_float(data['csho'])
            prcc_f = safe_float(data['prcc_f'])
            revt = safe_float(data['revt'])
            dvpsx_f = safe_float(data['dvpsx_f'])
            gind = data.get('gind', '').strip()

            sector = gind[:2] if gind and len(gind) >= 2 else None
            if sector not in GICS_SECTORS:
                sector = None

            if sector is None:
                no_gics_count += 1
                sector = 'XX'  # Unknown

            s = sectors[sector]
            s['total_companies'] += 1

            if ni is not None:
                s['earnings'] += ni
            if csho is not None and prcc_f is not None and prcc_f > 0:
                s['mktcap'] += csho * prcc_f
                s['companies'] += 1
            if dvpsx_f is not None and csho is not None:
                s['dividends'] += dvpsx_f * csho
            if revt is not None:
                s['revenue'] += revt

        industry_data[year] = dict(sectors)

    # =========================================
    # 1. 行业权重变迁
    # =========================================
    print("\n" + "=" * 120)
    print("1. S&P 500 行业市值权重变迁 (GICS Sector)")
    print("=" * 120)

    # 选取关键年份
    key_years = [1985, 1990, 1995, 2000, 2005, 2010, 2015, 2020, 2024]

    # 表头
    header = f"{'Sector':<16}"
    for y in key_years:
        header += f"{y:>8}"
    print(header)
    print("-" * (16 + 8 * len(key_years)))

    for sector_code in sorted(GICS_SECTORS.keys()):
        name = GICS_SECTORS[sector_code]
        row = f"{name:<16}"
        for y in key_years:
            if y not in industry_data:
                row += f"{'N/A':>8}"
                continue
            sectors = industry_data[y]
            total_mc = sum(s['mktcap'] for s in sectors.values())
            sec_mc = sectors.get(sector_code, {}).get('mktcap', 0)
            if total_mc > 0:
                weight = sec_mc / total_mc * 100
                row += f"{weight:>7.1f}%"
            else:
                row += f"{'N/A':>8}"
        print(row)

    # Unknown 行
    row = f"{'Unknown':<16}"
    for y in key_years:
        sectors = industry_data.get(y, {})
        total_mc = sum(s['mktcap'] for s in sectors.values())
        unk_mc = sectors.get('XX', {}).get('mktcap', 0)
        if total_mc > 0:
            row += f"{unk_mc/total_mc*100:>7.1f}%"
        else:
            row += f"{'N/A':>8}"
    print(row)

    # =========================================
    # 2. 行业盈利贡献
    # =========================================
    print("\n" + "=" * 120)
    print("2. S&P 500 行业盈利占比")
    print("=" * 120)

    header = f"{'Sector':<16}"
    for y in key_years:
        header += f"{y:>8}"
    print(header)
    print("-" * (16 + 8 * len(key_years)))

    for sector_code in sorted(GICS_SECTORS.keys()):
        name = GICS_SECTORS[sector_code]
        row = f"{name:<16}"
        for y in key_years:
            sectors = industry_data.get(y, {})
            total_e = sum(s['earnings'] for s in sectors.values())
            sec_e = sectors.get(sector_code, {}).get('earnings', 0)
            if total_e > 0:
                row += f"{sec_e/total_e*100:>7.1f}%"
            else:
                row += f"{'N/A':>8}"
        print(row)

    # =========================================
    # 3. 行业 PE 分析
    # =========================================
    print("\n" + "=" * 120)
    print("3. 行业 PE (市值/盈利)")
    print("=" * 120)

    header = f"{'Sector':<16}"
    for y in key_years:
        header += f"{y:>8}"
    print(header)
    print("-" * (16 + 8 * len(key_years)))

    sector_pe_history = defaultdict(list)  # sector -> [(year, pe)]

    for sector_code in sorted(GICS_SECTORS.keys()):
        name = GICS_SECTORS[sector_code]
        row = f"{name:<16}"
        for y in key_years:
            sectors = industry_data.get(y, {})
            sec = sectors.get(sector_code, {})
            mc = sec.get('mktcap', 0)
            e = sec.get('earnings', 0)
            if mc > 0 and e > 0:
                pe = mc / e
                if pe < 100:
                    row += f"{pe:>7.1f}"
                else:
                    row += f"{'  >100':>8}"
            else:
                row += f"{'N/A':>8}"
        print(row)

        # 收集完整 PE 历史
        for y in range(1980, 2025):
            sectors = industry_data.get(y, {})
            sec = sectors.get(sector_code, {})
            mc = sec.get('mktcap', 0)
            e = sec.get('earnings', 0)
            if mc > 0 and e > 0:
                pe = mc / e
                if 0 < pe < 100:
                    sector_pe_history[sector_code].append((y, pe))

    # =========================================
    # 4. 行业 PE 均值回归分析
    # =========================================
    print("\n" + "=" * 120)
    print("4. 行业 PE 均值回归分析 (1980-2024)")
    print("=" * 120)

    print(f"\n{'Sector':<16} {'均值PE':>8} {'标准差':>8} {'最小PE':>8} {'最大PE':>8} {'当前PE':>8} {'偏离均值':>8} {'回归概率':>8}")
    print("-" * 82)

    sector_stats = {}
    for sector_code in sorted(GICS_SECTORS.keys()):
        name = GICS_SECTORS[sector_code]
        history = sector_pe_history.get(sector_code, [])
        if len(history) < 10:
            continue

        pes = [pe for _, pe in history]
        mean_pe = sum(pes) / len(pes)
        std_pe = (sum((p - mean_pe)**2 for p in pes) / len(pes)) ** 0.5
        min_pe = min(pes)
        max_pe = max(pes)
        current_pe = history[-1][1]
        deviation = (current_pe - mean_pe) / std_pe

        # 回归概率：过去 PE 高于均值的年份，下一年 PE 回落的概率
        above_mean_count = 0
        revert_count = 0
        for i in range(len(history) - 1):
            y1, pe1 = history[i]
            y2, pe2 = history[i + 1]
            if pe1 > mean_pe:
                above_mean_count += 1
                if pe2 < pe1:  # 回落
                    revert_count += 1
        revert_pct = revert_count / above_mean_count * 100 if above_mean_count > 0 else 0

        sector_stats[sector_code] = {
            'name': name, 'mean_pe': mean_pe, 'std_pe': std_pe,
            'current_pe': current_pe, 'deviation': deviation,
            'revert_pct': revert_pct,
        }

        print(f"{name:<16} {mean_pe:>7.1f} {std_pe:>7.1f} {min_pe:>7.1f} {max_pe:>7.1f} "
              f"{current_pe:>7.1f} {deviation:>+7.1f}σ {revert_pct:>6.0f}%")

    # =========================================
    # 5. 行业盈利增长贡献分解
    # =========================================
    print("\n" + "=" * 120)
    print("5. 行业对 S&P 500 盈利增长的贡献分解")
    print("=" * 120)

    # 计算各行业在不同时段的盈利增长贡献
    periods = [(1985, 1995), (1995, 2005), (2005, 2015), (2015, 2024), (1985, 2024)]

    header = f"{'Sector':<16}"
    for p1, p2 in periods:
        header += f"  {p1}-{p2}"
    print(header)
    print("-" * (16 + 12 * len(periods)))

    for sector_code in sorted(GICS_SECTORS.keys()):
        name = GICS_SECTORS[sector_code]
        row = f"{name:<16}"
        for p1, p2 in periods:
            s1 = industry_data.get(p1, {}).get(sector_code, {})
            s2 = industry_data.get(p2, {}).get(sector_code, {})
            e1 = s1.get('earnings', 0)
            e2 = s2.get('earnings', 0)
            total_e1 = sum(s.get('earnings', 0) for s in industry_data.get(p1, {}).values())
            total_e2 = sum(s.get('earnings', 0) for s in industry_data.get(p2, {}).values())

            if total_e1 > 0 and total_e2 > 0:
                # 该行业的盈利变化占总盈利变化的比例
                delta_sector = e2 - e1
                delta_total = total_e2 - total_e1
                if delta_total != 0:
                    contribution = delta_sector / delta_total * 100
                    row += f"{contribution:>10.1f}%"
                else:
                    row += f"{'N/A':>11}"
            else:
                row += f"{'N/A':>11}"
        print(row)

    # =========================================
    # 6. 行业盈利 CAGR
    # =========================================
    print("\n" + "=" * 120)
    print("6. 行业盈利年化增长率 (CAGR)")
    print("=" * 120)

    header = f"{'Sector':<16}"
    for p1, p2 in periods:
        header += f"  {p1}-{p2}"
    print(header)
    print("-" * (16 + 12 * len(periods)))

    for sector_code in sorted(GICS_SECTORS.keys()):
        name = GICS_SECTORS[sector_code]
        row = f"{name:<16}"
        for p1, p2 in periods:
            s1 = industry_data.get(p1, {}).get(sector_code, {})
            s2 = industry_data.get(p2, {}).get(sector_code, {})
            e1 = s1.get('earnings', 0)
            e2 = s2.get('earnings', 0)
            n = p2 - p1
            if e1 > 0 and e2 > 0 and n > 0:
                cagr = (e2 / e1) ** (1/n) - 1
                row += f"{cagr*100:>10.1f}%"
            else:
                row += f"{'N/A':>11}"
        print(row)

    # Total
    row = f"{'S&P 500 Total':<16}"
    for p1, p2 in periods:
        te1 = sum(s.get('earnings', 0) for s in industry_data.get(p1, {}).values())
        te2 = sum(s.get('earnings', 0) for s in industry_data.get(p2, {}).values())
        n = p2 - p1
        if te1 > 0 and te2 > 0:
            cagr = (te2 / te1) ** (1/n) - 1
            row += f"{cagr*100:>10.1f}%"
        else:
            row += f"{'N/A':>11}"
    print(row)

    # =========================================
    # 7. 与 French 5 行业对比
    # =========================================
    print("\n" + "=" * 120)
    print("7. GICS → French 5 行业映射验证")
    print("=" * 120)

    # GICS to French mapping
    gics_to_french = {
        '25': 'Consumer', '30': 'Consumer',  # Consumer Disc + Staples
        '15': 'Manufacturing', '20': 'Manufacturing',  # Materials + Industrials
        '10': 'Energy',  # Energy
        '40': 'Finance', '60': 'Finance',  # Financials + Real Estate
        '35': 'Other', '45': 'Other', '50': 'Other', '55': 'Other',
    }

    french_years = [1985, 1990, 1995, 2000, 2005, 2010, 2015, 2020, 2024]

    print(f"\n市值权重 (GICS→French 5映射):")
    header = f"{'French Sector':<16}"
    for y in french_years:
        header += f"{y:>8}"
    print(header)
    print("-" * (16 + 8 * len(french_years)))

    french_names = ['Consumer', 'Manufacturing', 'Energy', 'Finance', 'Other']
    for fname in french_names:
        row = f"{fname:<16}"
        for y in french_years:
            sectors = industry_data.get(y, {})
            total_mc = sum(s['mktcap'] for s in sectors.values())
            french_mc = 0
            for sc, fn in gics_to_french.items():
                if fn == fname:
                    french_mc += sectors.get(sc, {}).get('mktcap', 0)
            if total_mc > 0:
                row += f"{french_mc/total_mc*100:>7.1f}%"
            else:
                row += f"{'N/A':>8}"
        print(row)

    # =========================================
    # 8. 综合：行业对均值回归的贡献
    # =========================================
    print("\n" + "=" * 120)
    print("8. 行业对 S&P 500 均值回归的贡献")
    print("=" * 120)
    print("""
  均值回归机制：当某行业 PE 偏高时，后续回报倾向偏低（PE 收缩）。
  如果各行业的 PE 波动方向不同（轮动），行业多样化本身就促进了指数级别的均值回归。
""")

    # 计算跨行业 PE 相关性
    # 用年度 PE 变化
    sector_pe_changes = {}
    for sector_code in sorted(GICS_SECTORS.keys()):
        history = sector_pe_history.get(sector_code, [])
        if len(history) < 20:
            continue
        changes = {}
        for i in range(1, len(history)):
            y1, pe1 = history[i-1]
            y2, pe2 = history[i]
            if y2 == y1 + 1:
                changes[y2] = pe2/pe1 - 1
        sector_pe_changes[sector_code] = changes

    # 平均跨行业相关性
    codes = sorted(sector_pe_changes.keys())
    correlations = []
    for i in range(len(codes)):
        for j in range(i+1, len(codes)):
            c1 = sector_pe_changes[codes[i]]
            c2 = sector_pe_changes[codes[j]]
            common_years = set(c1.keys()) & set(c2.keys())
            if len(common_years) < 15:
                continue
            vals1 = [c1[y] for y in sorted(common_years)]
            vals2 = [c2[y] for y in sorted(common_years)]
            mean1 = sum(vals1) / len(vals1)
            mean2 = sum(vals2) / len(vals2)
            cov = sum((v1-mean1)*(v2-mean2) for v1, v2 in zip(vals1, vals2)) / len(vals1)
            std1 = (sum((v-mean1)**2 for v in vals1) / len(vals1)) ** 0.5
            std2 = (sum((v-mean2)**2 for v in vals2) / len(vals2)) ** 0.5
            if std1 > 0 and std2 > 0:
                corr = cov / (std1 * std2)
                correlations.append((codes[i], codes[j], corr))

    if correlations:
        avg_corr = sum(c for _, _, c in correlations) / len(correlations)
        print(f"  跨行业 PE 变化相关性:")
        print(f"    平均相关系数: {avg_corr:.3f}")
        print(f"    （<0.5 = 行业轮动显著，有助于指数均值回归）")

        # 找出最不相关和最相关的行业对
        correlations.sort(key=lambda x: x[2])
        print(f"\n    最不相关（轮动最强）:")
        for c1, c2, corr in correlations[:5]:
            print(f"      {GICS_SECTORS[c1]} vs {GICS_SECTORS[c2]}: {corr:.3f}")
        print(f"    最相关（同步最强）:")
        for c1, c2, corr in correlations[-5:]:
            print(f"      {GICS_SECTORS[c1]} vs {GICS_SECTORS[c2]}: {corr:.3f}")

    # PE 均值回归贡献
    print(f"\n  各行业 PE 均值回归贡献:")
    print(f"    {'Sector':<16} {'PE均值':>8} {'当前PE':>8} {'偏离':>8} {'市值占比':>8} {'对指数PE影响':>12}")
    print("    " + "-" * 66)

    latest_year = 2024
    sectors_latest = industry_data.get(latest_year, {})
    total_mc = sum(s['mktcap'] for s in sectors_latest.values())

    for sector_code in sorted(GICS_SECTORS.keys()):
        stats = sector_stats.get(sector_code)
        if not stats:
            continue
        sec = sectors_latest.get(sector_code, {})
        mc = sec.get('mktcap', 0)
        weight = mc / total_mc if total_mc > 0 else 0

        # 如果 PE 回归均值，对指数 PE 的影响
        pe_if_revert = stats['mean_pe']
        pe_current = stats['current_pe']
        pe_impact = (pe_if_revert - pe_current) * weight

        print(f"    {stats['name']:<16} {stats['mean_pe']:>7.1f} {stats['current_pe']:>7.1f} "
              f"{stats['deviation']:>+6.1f}σ {weight*100:>7.1f}% {pe_impact:>+10.1f}")

    # 如果所有行业回归均值PE，指数PE变化
    current_agg_pe = 0
    revert_agg_pe = 0
    for sector_code in sorted(GICS_SECTORS.keys()):
        stats = sector_stats.get(sector_code)
        if not stats:
            continue
        sec = sectors_latest.get(sector_code, {})
        mc = sec.get('mktcap', 0)
        e = sec.get('earnings', 0)
        weight = mc / total_mc if total_mc > 0 else 0
        if e > 0 and mc > 0:
            current_agg_pe += mc / e * weight / weight if weight > 0 else 0

    # 更简单的方法：直接用加权平均
    total_e = sum(s.get('earnings', 0) for s in sectors_latest.values())
    if total_e > 0 and total_mc > 0:
        current_index_pe = total_mc / total_e
        print(f"\n    当前 S&P 500 聚合 PE: {current_index_pe:.1f}")

        # 如果各行业回归均值PE，指数PE应该是多少
        hypothetical_mc = 0
        for sector_code in sorted(GICS_SECTORS.keys()):
            stats = sector_stats.get(sector_code)
            sec = sectors_latest.get(sector_code, {})
            e = sec.get('earnings', 0)
            if stats and e > 0:
                hypothetical_mc += e * stats['mean_pe']
            elif e > 0:
                # 没有历史数据的行业，保持不变
                hypothetical_mc += sec.get('mktcap', 0)

        if total_e > 0:
            hypothetical_pe = hypothetical_mc / total_e
            pe_change = (hypothetical_pe / current_index_pe - 1) * 100
            print(f"    均值回归后 PE: {hypothetical_pe:.1f}")
            print(f"    PE 变化: {pe_change:+.1f}%")
            price_change = (hypothetical_pe / current_index_pe - 1) * 100
            print(f"    对应市值变化: {price_change:+.1f}% （盈利不变时）")

    # 保存行业数据为 JSON
    output = []
    for year in range(1980, 2025):
        sectors = industry_data.get(year, {})
        total_mc = sum(s['mktcap'] for s in sectors.values())
        total_e = sum(s['earnings'] for s in sectors.values())

        year_data = {'year': year, 'sectors': {}}
        for sector_code in sorted(GICS_SECTORS.keys()):
            sec = sectors.get(sector_code, {})
            mc = sec.get('mktcap', 0)
            e = sec.get('earnings', 0)
            year_data['sectors'][GICS_SECTORS[sector_code]] = {
                'weight': round(mc / total_mc * 100, 2) if total_mc > 0 else 0,
                'earnings_share': round(e / total_e * 100, 2) if total_e > 0 else 0,
                'earnings_M': round(e, 1),
                'mktcap_M': round(mc, 1),
                'pe': round(mc / e, 2) if e > 0 and mc > 0 and mc/e < 200 else None,
                'companies': sec.get('companies', 0),
            }
        output.append(year_data)

    output_path = os.path.join(DATA_DIR, '..', 'sp500_industry_analysis.json')
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"\n  行业数据已保存到: sp500_industry_analysis.json")

if __name__ == "__main__":
    analyze()
