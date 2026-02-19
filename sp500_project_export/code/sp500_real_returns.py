"""
用 CRSP 月度数据计算 S&P 500 成分股的真实年度回报
结合 Compustat 盈利数据，做精确的回报分解
验证 EPS 低估假说

修正：使用年初市值作权重（避免 winner bias）
"""
import csv
import os
import json
from collections import defaultdict

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'crsp_compustat')

def safe_float(val):
    try:
        if val and val.strip() and val.strip() not in ('C', 'B', 'A'):
            return float(val)
    except ValueError:
        pass
    return None

def load_sp500_constituents():
    """加载 S&P 500 成分股列表"""
    path = os.path.join(DATA_DIR, 'sp500_constituents.csv')
    yearly = defaultdict(set)
    with open(path, 'r') as f:
        for r in csv.DictReader(f):
            permno = r['permno']
            start_year = int(r['start'][:4])
            end_year = int(r['ending'][:4])
            for year in range(max(start_year, 1962), min(end_year, 2024) + 1):
                yearly[year].add(permno)
    return yearly

def compute_annual_returns(sp500_by_year):
    """
    用 CRSP 月度数据计算每年 S&P 500 市值加权回报
    使用年初（上年末）市值作权重
    """
    print("加载 CRSP 月度数据 (515万行)...")
    crsp_path = os.path.join(DATA_DIR, 'crsp_monthly.csv')

    all_sp500_permnos = set()
    for year, permnos in sp500_by_year.items():
        all_sp500_permnos.update(permnos)

    # 读取 CRSP 数据
    # 存储结构: monthly_data[(permno, year)] = [(month, ret, prc, shrout, dlret)]
    monthly_data = defaultdict(list)
    row_count = 0

    with open(crsp_path, 'r') as f:
        for r in csv.DictReader(f):
            row_count += 1
            if row_count % 1000000 == 0:
                print(f"  已处理 {row_count/1000000:.0f}M 行...")

            permno = r['PERMNO']
            if permno not in all_sp500_permnos:
                continue

            date = r['date']
            if not date:
                continue
            year = int(date[:4])
            month = int(date[5:7])

            if year < 1961 or year > 2024:  # 需要上一年12月数据
                continue

            ret = safe_float(r['RET'])
            prc = safe_float(r['PRC'])
            shrout = safe_float(r['SHROUT'])
            dlret = safe_float(r['DLRET'])

            if prc is not None:
                prc = abs(prc)

            monthly_data[(permno, year)].append({
                'month': month,
                'ret': ret,
                'prc': prc,
                'shrout': shrout,
                'dlret': dlret,
            })

    print(f"  总行数: {row_count}")

    # 构建年末市值查找表（用于作为下一年的权重）
    # year_end_mktcap[(permno, year)] = 12月的市值
    year_end_mktcap = {}
    for (permno, year), months in monthly_data.items():
        # 找12月数据
        dec_data = [m for m in months if m['month'] == 12]
        if dec_data:
            m = dec_data[0]
            if m['prc'] is not None and m['shrout'] is not None:
                year_end_mktcap[(permno, year)] = m['prc'] * m['shrout']

    print("\n计算年度市值加权回报（年初市值权重）...")
    yearly_results = {}

    for year in range(1962, 2025):
        permnos = sp500_by_year.get(year, set())
        if not permnos:
            continue

        stock_returns = []

        for permno in permnos:
            months = monthly_data.get((permno, year), [])
            if not months:
                continue

            months.sort(key=lambda x: x['month'])

            # 计算年度回报：连乘月度回报
            cumulative = 1.0
            valid_months = 0
            for m in months:
                ret = m['ret']
                if ret is not None:
                    cumulative *= (1.0 + ret)
                    valid_months += 1

            # 处理退市回报
            last_month = months[-1]
            if last_month['dlret'] is not None:
                cumulative *= (1.0 + last_month['dlret'])

            if valid_months < 6:
                continue

            annual_ret = cumulative - 1.0

            # 用上年末（年初）市值作权重
            beg_mktcap = year_end_mktcap.get((permno, year - 1))

            # 如果没有上年末数据，用当年1月数据
            if beg_mktcap is None:
                jan_data = [m for m in months if m['month'] == 1]
                if jan_data and jan_data[0]['prc'] is not None and jan_data[0]['shrout'] is not None:
                    beg_mktcap = jan_data[0]['prc'] * jan_data[0]['shrout']

            if beg_mktcap is not None and beg_mktcap > 0:
                stock_returns.append((permno, annual_ret, beg_mktcap))

        if not stock_returns:
            continue

        # 市值加权回报（用年初市值）
        total_beg_mktcap = sum(mc for _, _, mc in stock_returns)
        vw_return = sum(ret * mc / total_beg_mktcap for _, ret, mc in stock_returns)

        # 等权回报
        ew_return = sum(ret for _, ret, _ in stock_returns) / len(stock_returns)

        # 年末总市值（用于记录）
        total_end_mktcap = 0
        for permno, _, _ in stock_returns:
            end_mc = year_end_mktcap.get((permno, year))
            if end_mc:
                total_end_mktcap += end_mc

        yearly_results[year] = {
            'year': year,
            'stocks': len(stock_returns),
            'vw_return': vw_return,
            'ew_return': ew_return,
            'total_beg_mktcap_K': total_beg_mktcap,
            'total_end_mktcap_K': total_end_mktcap,
        }

    return yearly_results

def load_company_analysis():
    path = os.path.join(DATA_DIR, '..', 'sp500_company_analysis.json')
    with open(path) as f:
        data = json.load(f)
    return {r['year']: r for r in data}

def main():
    sp500_by_year = load_sp500_constituents()
    yearly_returns = compute_annual_returns(sp500_by_year)
    company_data = load_company_analysis()

    print("\n" + "=" * 100)
    print("S&P 500 真实年度回报 (CRSP 市值加权，年初权重) vs 盈利增长 (Compustat)")
    print("=" * 100)

    print(f"\n{'年份':>6} {'股票数':>6} {'VW回报':>10} {'EW回报':>10} {'盈利增长':>10} {'PE':>8} {'股息率':>8}")
    print("-" * 68)

    years = sorted(set(yearly_returns.keys()) & set(company_data.keys()))
    prev_earnings = None
    annual_vw = []

    for year in years:
        yr = yearly_returns[year]
        cd = company_data[year]

        earnings_growth = None
        if prev_earnings and prev_earnings > 0 and cd['total_earnings_M'] > 0:
            earnings_growth = cd['total_earnings_M'] / prev_earnings - 1
        prev_earnings = cd['total_earnings_M']

        pe_str = f"{cd['aggregate_pe']:>6.1f}" if cd['aggregate_pe'] and cd['aggregate_pe'] < 100 else "   N/A"
        eg_str = f"{earnings_growth*100:>8.2f}%" if earnings_growth is not None else "     N/A"

        annual_vw.append(yr['vw_return'])

        # 只打印关键年份
        if year in [1962, 1965, 1970, 1975, 1980, 1985, 1990, 1995, 2000, 2005, 2010, 2015, 2020, 2024]:
            print(f"{year:>6} {yr['stocks']:>6} {yr['vw_return']*100:>8.2f}% {yr['ew_return']*100:>8.2f}% "
                  f"{eg_str} {pe_str} {cd['dividend_yield_pct']:>6.2f}%")

    # 全期统计
    n = len(annual_vw)
    cumulative = 1.0
    for r in annual_vw:
        cumulative *= (1 + r)
    geo_mean = cumulative ** (1/n) - 1

    print(f"\n{'='*100}")
    print(f"CRSP 回报统计 ({years[0]}-{years[-1]}, {n} 年)")
    print(f"{'='*100}")
    print(f"  市值加权年化回报（几何平均）: {geo_mean*100:.2f}%")
    print(f"  累积倍数: {cumulative:.1f}x")

    # ====================================
    # 核心分析：EPS 低估验证
    # ====================================
    print(f"\n{'='*100}")
    print("EPS 低估假说验证：10年滚动分析")
    print(f"{'='*100}")
    print("""
  方法说明：
  - CRSP 给出真实的市值加权年回报
  - Compustat 给出公司级别的盈利变化
  - 对比 盈利增长+股息率（基本面驱动）vs CRSP回报（市场实际）
  - 差额 = PE 扩张/收缩（即市场估值变化）
  - 如果 PE 持续扩张 → 市场之前低估了盈利前景
""")

    print(f"{'期间':>14} {'CRSP回报':>10} {'盈利CAGR':>10} {'PE变化':>10} {'股息率':>8} {'基本面回报':>10} {'估值贡献':>10}")
    print("-" * 82)

    pe_contributions = []
    for start_year in range(1963, 2015):
        end_year = start_year + 10
        if start_year not in company_data or end_year not in company_data:
            continue
        if start_year not in yearly_returns:
            continue

        cd1 = company_data[start_year]
        cd2 = company_data[end_year]

        if cd1['total_earnings_M'] <= 0 or cd2['total_earnings_M'] <= 0:
            continue

        # CRSP 10年累积回报
        crsp_cum = 1.0
        valid_years = 0
        for y in range(start_year + 1, end_year + 1):
            if y in yearly_returns:
                crsp_cum *= (1 + yearly_returns[y]['vw_return'])
                valid_years += 1
        if valid_years < 8:
            continue
        crsp_annual = crsp_cum ** (1/10) - 1

        # 盈利 CAGR
        earn_cagr = (cd2['total_earnings_M'] / cd1['total_earnings_M']) ** (1/10) - 1

        # PE 变化
        pe1 = cd1['aggregate_pe']
        pe2 = cd2['aggregate_pe']
        if pe1 and pe2 and pe1 > 0 and pe2 > 0 and pe1 < 100 and pe2 < 100:
            pe_change = (pe2 / pe1) ** (1/10) - 1
        else:
            pe_change = None

        # 平均股息率
        div_sum = 0
        div_count = 0
        for y in range(start_year, end_year + 1):
            if y in company_data:
                div_sum += company_data[y]['dividend_yield_pct']
                div_count += 1
        avg_div = div_sum / div_count if div_count > 0 else 0

        # 基本面回报 = 盈利增长 + 股息
        fundamental_return = earn_cagr + avg_div / 100

        # 估值贡献 = CRSP 回报 - 基本面回报
        valuation_contribution = crsp_annual - fundamental_return

        pe_str = f"{pe_change*100:>8.2f}%" if pe_change is not None else "     N/A"

        if pe_change is not None:
            pe_contributions.append({
                'period': f"{start_year}-{end_year}",
                'crsp': crsp_annual,
                'earn_cagr': earn_cagr,
                'pe_change': pe_change,
                'avg_div': avg_div,
                'fundamental': fundamental_return,
                'valuation': valuation_contribution,
            })

        # 打印关键时段
        if start_year % 5 == 0 or start_year in [1963, 2014]:
            print(f"{start_year}-{end_year:>4} {crsp_annual*100:>8.2f}% {earn_cagr*100:>8.2f}% "
                  f"{pe_str} {avg_div:>6.2f}% {fundamental_return*100:>8.2f}% {valuation_contribution*100:>8.2f}%")

    # 统计
    if pe_contributions:
        avg_pe_change = sum(p['pe_change'] for p in pe_contributions) / len(pe_contributions)
        avg_valuation = sum(p['valuation'] for p in pe_contributions) / len(pe_contributions)
        pe_expansion_count = sum(1 for p in pe_contributions if p['pe_change'] > 0)
        avg_crsp = sum(p['crsp'] for p in pe_contributions) / len(pe_contributions)
        avg_earn = sum(p['earn_cagr'] for p in pe_contributions) / len(pe_contributions)
        avg_div = sum(p['avg_div'] for p in pe_contributions) / len(pe_contributions)
        avg_fund = sum(p['fundamental'] for p in pe_contributions) / len(pe_contributions)

        print(f"\n{'='*100}")
        print("统计总结")
        print(f"{'='*100}")
        print(f"""
  10年滚动分析 ({len(pe_contributions)} 个时段):

  平均 CRSP 回报:       {avg_crsp*100:.2f}%/年
  平均盈利 CAGR:        {avg_earn*100:.2f}%/年
  平均股息率:           {avg_div:.2f}%/年
  平均基本面回报:       {avg_fund*100:.2f}%/年
  平均 PE 变化:         {avg_pe_change*100:.2f}%/年
  平均估值贡献:         {avg_valuation*100:.2f}%/年

  PE 扩张次数: {pe_expansion_count}/{len(pe_contributions)} ({pe_expansion_count/len(pe_contributions)*100:.0f}%)

  解读：
  - 「基本面回报」= 盈利增长 + 股息率，代表企业实际创造的价值
  - 「估值贡献」= CRSP回报 - 基本面回报，代表市场情绪变化
  - 如果 PE 长期平均扩张 → 市场持续给予更高估值 → 支持低估假说
  - 注意：公司级别盈利 CAGR ({avg_earn*100:.2f}%) 高于 Shiller EPS ({5.16}%)
    因为包含了新公司加入的盈利贡献（成分股变动效应约 {avg_earn*100-5.16:.1f}%）
""")

    # 对比 Shiller 框架
    print(f"{'='*100}")
    print("框架对比：公司级别 vs Shiller 指数级")
    print(f"{'='*100}")

    if years:
        first_cd = company_data[years[0]]
        last_cd = company_data[years[-1]]
        n_years = years[-1] - years[0]
        earn_cagr_full = (last_cd['total_earnings_M'] / first_cd['total_earnings_M']) ** (1/n_years) - 1
        pe_first = first_cd['aggregate_pe'] or 1
        pe_last = last_cd['aggregate_pe'] or 1
        pe_annual_full = (pe_last / pe_first) ** (1/n_years) - 1
        avg_div_full = sum(company_data[y]['dividend_yield_pct'] for y in years if y in company_data) / len(years)

        print(f"""
                              公司级别(CRSP+Compustat)   Shiller(指数级)
  数据区间:                   {years[0]}-{years[-1]}              1928-2024
  CRSP 真实年化回报:          {geo_mean*100:.2f}%               8.91%（含股息）
  盈利年化增长:               {earn_cagr_full*100:.2f}%               5.16%
  PE 起始:                    {pe_first:.1f}                 11.1
  PE 结束:                    {pe_last:.1f}                 24.0
  PE 年化变化:                {pe_annual_full*100:.2f}%               0.81%
  平均股息率:                 {avg_div_full:.2f}%               2.90%

  回报分解对比:
                              公司级别             Shiller
    盈利增长:                  {earn_cagr_full*100:.2f}%              5.16%
    PE 扩张:                   {pe_annual_full*100:.2f}%              0.81%
    股息率:                    {avg_div_full:.2f}%              2.90%
    合计:                      {earn_cagr_full*100 + pe_annual_full*100 + avg_div_full:.2f}%              8.87%

  CRSP回报 vs 分解合计差异:
    CRSP 真实回报:             {geo_mean*100:.2f}%
    盈利+PE+股息:              {earn_cagr_full*100 + pe_annual_full*100 + avg_div_full:.2f}%
    差异:                      {geo_mean*100 - (earn_cagr_full*100 + pe_annual_full*100 + avg_div_full):.2f}%

  注：公司级别盈利CAGR ({earn_cagr_full*100:.2f}%) 包含成分股新陈代谢效应。
  扣除此效应后，每股盈利增长约 5.16%（接近 Shiller）。
  因此真实回报分解应参照：
    ~10% 名义回报 ≈ 5.16% EPS增长 + 0.81% PE扩张 + 2.90% 股息 + ~1% 残余
""")

if __name__ == "__main__":
    main()
