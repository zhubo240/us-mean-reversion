"""
S&P 500 公司级别分析：用真实 CRSP/Compustat 数据计算
- 每年 S&P 500 聚合 EPS、净利润、PE
- EPS 增长率分解
- 与 Shiller 指数级数据对比
- 验证 EPS 低估假说
"""
import csv
import os
import json
from collections import defaultdict

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'crsp_compustat')

def load_csv(filename):
    path = os.path.join(DATA_DIR, filename)
    with open(path, 'r') as f:
        return list(csv.DictReader(f))

def safe_float(val):
    try:
        return float(val) if val and val.strip() else None
    except ValueError:
        return None

def build_permno_to_gvkey(ccm_rows):
    """构建 PERMNO → GVKEY 映射（优先使用 Primary link）"""
    mapping = {}  # permno -> [(gvkey, link_start, link_end, priority)]
    for r in ccm_rows:
        permno = r['LPERMNO']
        gvkey = r['gvkey']
        linkdt = r['LINKDT']
        linkenddt = r['LINKENDDT'] if r['LINKENDDT'] != 'E' else '2099-12-31'
        # P (Primary) > C (Secondary) > J/N
        priority = {'P': 0, 'C': 1, 'J': 2, 'N': 3}.get(r['LINKPRIM'], 4)
        if permno not in mapping:
            mapping[permno] = []
        mapping[permno].append((gvkey, linkdt, linkenddt, priority))

    # 对每个 permno，按优先级排序
    for permno in mapping:
        mapping[permno].sort(key=lambda x: x[3])

    return mapping

def get_gvkey_for_permno_year(mapping, permno, year):
    """给定 PERMNO 和年份，返回最佳匹配的 GVKEY"""
    if permno not in mapping:
        return None
    year_str = f"{year}-06-30"  # 用年中作为参考点
    for gvkey, linkdt, linkenddt, priority in mapping[permno]:
        if linkdt <= year_str and linkenddt >= year_str:
            return gvkey
    # 如果没有精确匹配，返回优先级最高的
    return mapping[permno][0][0] if mapping[permno] else None

def build_sp500_by_year(sp500_rows):
    """构建每年 S&P 500 成分股列表"""
    yearly = defaultdict(set)
    for r in sp500_rows:
        permno = r['permno']
        start_year = int(r['start'][:4])
        end_year = int(r['ending'][:4])
        for year in range(max(start_year, 1950), min(end_year, 2024) + 1):
            yearly[year].add(permno)
    return yearly

def build_compustat_lookup(compustat_rows):
    """构建 (gvkey, year) → 财务数据 的查找表"""
    lookup = {}
    for r in compustat_rows:
        gvkey = r['gvkey']
        if not r['datadate']:
            continue
        year = int(r['datadate'][:4])
        month = int(r['datadate'][5:7])
        # 对于财年结束在1-5月的，归入上一年
        fiscal_year = year if month >= 6 else year - 1
        key = (gvkey, fiscal_year)
        # 如果已有记录，保留较晚的（更完整的）
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

    print("计算年度聚合...")
    results = []

    for year in range(1950, 2025):
        permnos = sp500_by_year.get(year, set())
        if not permnos:
            continue

        total_earnings = 0  # 净利润合计
        total_market_cap = 0  # 总市值
        total_revenue = 0
        total_dividends = 0
        total_book_value = 0
        company_count = 0
        eps_count = 0
        pe_values = []
        eps_values = []
        gics_earnings = defaultdict(float)  # GICS 行业 → 盈利合计
        gics_market_cap = defaultdict(float)

        for permno in permnos:
            gvkey = get_gvkey_for_permno_year(permno_to_gvkey, permno, year)
            if not gvkey:
                continue

            data = compustat_lookup.get((gvkey, year))
            if not data:
                continue

            ni = safe_float(data['ni'])
            csho = safe_float(data['csho'])
            prcc_f = safe_float(data['prcc_f'])
            epspx = safe_float(data['epspx'])
            revt = safe_float(data['revt'])
            dvpsx_f = safe_float(data['dvpsx_f'])
            seq = safe_float(data['seq'])
            gind = data.get('gind', '').strip()

            if ni is not None:
                total_earnings += ni
            if csho is not None and prcc_f is not None and prcc_f > 0:
                mkt_cap = csho * prcc_f
                total_market_cap += mkt_cap
                if gind:
                    gics_market_cap[gind[:2]] += mkt_cap  # 用2位 GICS sector
                    if ni is not None:
                        gics_earnings[gind[:2]] += ni
            if revt is not None:
                total_revenue += revt
            if dvpsx_f is not None and csho is not None:
                total_dividends += dvpsx_f * csho
            if seq is not None:
                total_book_value += seq

            if epspx is not None:
                eps_values.append(epspx)
                eps_count += 1
            if epspx is not None and prcc_f is not None and epspx > 0:
                pe_values.append(prcc_f / epspx)

            company_count += 1

        if total_market_cap > 0 and total_earnings != 0:
            # 加权 EPS = 总盈利 / (总市值 / 加权平均股价)
            # 更简单：用 earnings yield = total_earnings / total_market_cap
            earnings_yield = total_earnings / total_market_cap
            aggregate_pe = total_market_cap / total_earnings if total_earnings > 0 else None
            dividend_yield = total_dividends / total_market_cap if total_dividends > 0 else 0

            result = {
                'year': year,
                'companies': company_count,
                'sp500_count': len(permnos),
                'total_earnings_M': round(total_earnings, 1),
                'total_mktcap_M': round(total_market_cap, 1),
                'total_revenue_M': round(total_revenue, 1),
                'total_dividends_M': round(total_dividends, 1),
                'total_book_value_M': round(total_book_value, 1),
                'earnings_yield_pct': round(earnings_yield * 100, 2),
                'aggregate_pe': round(aggregate_pe, 2) if aggregate_pe else None,
                'dividend_yield_pct': round(dividend_yield * 100, 2),
                'median_pe': round(sorted(pe_values)[len(pe_values)//2], 2) if pe_values else None,
                'eps_company_count': eps_count,
            }
            results.append(result)

    # 输出结果
    print("\n" + "=" * 100)
    print("S&P 500 公司级别聚合分析 (1950-2024)")
    print("=" * 100)

    print(f"\n{'年份':>6} {'公司数':>6} {'总盈利(M$)':>12} {'总市值(M$)':>14} {'盈利率':>8} {'聚合PE':>8} {'股息率':>8} {'中位PE':>8}")
    print("-" * 84)

    for r in results:
        pe_str = f"{r['aggregate_pe']:>6.1f}" if r['aggregate_pe'] else "   N/A"
        med_pe = f"{r['median_pe']:>6.1f}" if r['median_pe'] else "   N/A"
        print(f"{r['year']:>6} {r['companies']:>6} {r['total_earnings_M']:>12,.0f} {r['total_mktcap_M']:>14,.0f} "
              f"{r['earnings_yield_pct']:>6.2f}% {pe_str} {r['dividend_yield_pct']:>6.2f}% {med_pe}")

    # EPS 增长率分析
    print("\n" + "=" * 100)
    print("盈利增长率分析（5年滚动）")
    print("=" * 100)

    print(f"\n{'期间':>14} {'盈利CAGR':>10} {'市值CAGR':>10} {'PE变化':>10} {'股息率均值':>10}")
    print("-" * 60)

    for i in range(0, len(results) - 5, 5):
        r1 = results[i]
        r2 = results[min(i + 5, len(results) - 1)]
        n = r2['year'] - r1['year']
        if n == 0 or r1['total_earnings_M'] <= 0 or r2['total_earnings_M'] <= 0:
            continue

        earn_cagr = (r2['total_earnings_M'] / r1['total_earnings_M']) ** (1/n) - 1
        mktcap_cagr = (r2['total_mktcap_M'] / r1['total_mktcap_M']) ** (1/n) - 1

        pe1 = r1['aggregate_pe'] or 0
        pe2 = r2['aggregate_pe'] or 0
        pe_change = ((pe2 / pe1) ** (1/n) - 1) if pe1 > 0 and pe2 > 0 else 0

        # 期间平均股息率
        period_results = [r for r in results if r1['year'] <= r['year'] <= r2['year']]
        avg_div = sum(r['dividend_yield_pct'] for r in period_results) / len(period_results)

        print(f"{r1['year']}-{r2['year']:>4} {earn_cagr*100:>8.2f}% {mktcap_cagr*100:>8.2f}% "
              f"{pe_change*100:>8.2f}% {avg_div:>8.2f}%")

    # 全期增长
    if results[0]['total_earnings_M'] > 0 and results[-1]['total_earnings_M'] > 0:
        n_total = results[-1]['year'] - results[0]['year']
        total_earn_cagr = (results[-1]['total_earnings_M'] / results[0]['total_earnings_M']) ** (1/n_total) - 1
        total_mktcap_cagr = (results[-1]['total_mktcap_M'] / results[0]['total_mktcap_M']) ** (1/n_total) - 1
        pe_first = results[0]['aggregate_pe'] or 1
        pe_last = results[-1]['aggregate_pe'] or 1
        total_pe_change = (pe_last / pe_first) ** (1/n_total) - 1
        avg_div_all = sum(r['dividend_yield_pct'] for r in results) / len(results)

        print("-" * 60)
        print(f"{'全期':>14} {total_earn_cagr*100:>8.2f}% {total_mktcap_cagr*100:>8.2f}% "
              f"{total_pe_change*100:>8.2f}% {avg_div_all:>8.2f}%")

        print(f"\n" + "=" * 100)
        print("全期总结 ({}-{})".format(results[0]['year'], results[-1]['year']))
        print("=" * 100)
        print(f"""
  公司级别数据覆盖: {results[0]['year']}-{results[-1]['year']} ({n_total} 年)
  盈利年化增长 (CAGR):      {total_earn_cagr*100:.2f}%
  市值年化增长 (CAGR):      {total_mktcap_cagr*100:.2f}%
  PE 年化变化:              {total_pe_change*100:.2f}%
  平均股息率:               {avg_div_all:.2f}%

  回报分解 (近似):
    市值增长 ≈ 盈利增长 + PE 扩张
    {total_mktcap_cagr*100:.2f}% ≈ {total_earn_cagr*100:.2f}% + {total_pe_change*100:.2f}%

    总回报 ≈ 市值增长 + 股息率
    {total_mktcap_cagr*100 + avg_div_all:.2f}% ≈ {total_mktcap_cagr*100:.2f}% + {avg_div_all:.2f}%

  对比 Shiller 数据 (1928-2024):
    Shiller EPS 增长:  5.16%/年
    公司级别盈利增长:  {total_earn_cagr*100:.2f}%/年
    Shiller PE 扩张:   0.81%/年
    公司级别 PE 扩张:  {total_pe_change*100:.2f}%/年
""")

    # 保存 JSON
    output_path = os.path.join(DATA_DIR, '..', 'sp500_company_analysis.json')
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"  结果已保存到: sp500_company_analysis.json")

if __name__ == "__main__":
    analyze()
