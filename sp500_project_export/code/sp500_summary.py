"""
从 sp500_company_analysis.json 提取可靠年份数据，计算核心指标
"""
import json
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

with open(os.path.join(DATA_DIR, 'sp500_company_analysis.json')) as f:
    data = json.load(f)

# 从 1962 开始（之前数据不完整）
data = [r for r in data if r['year'] >= 1962]

print("=" * 90)
print("S&P 500 公司级别核心指标 (1962-2024, Compustat 真实数据)")
print("=" * 90)

# 关键年份
key_years = [1962, 1970, 1980, 1990, 2000, 2010, 2020, 2024]
print(f"\n{'年份':>6} {'公司数':>6} {'总盈利($B)':>10} {'总市值($B)':>11} {'聚合PE':>8} {'盈利率':>8} {'股息率':>8}")
print("-" * 68)
for r in data:
    if r['year'] in key_years:
        pe_str = f"{r['aggregate_pe']:>6.1f}" if r['aggregate_pe'] and r['aggregate_pe'] < 100 else "   N/A"
        print(f"{r['year']:>6} {r['companies']:>6} {r['total_earnings_M']/1000:>10,.1f} "
              f"{r['total_mktcap_M']/1000:>11,.1f} {pe_str} "
              f"{r['earnings_yield_pct']:>6.2f}% {r['dividend_yield_pct']:>6.2f}%")

# 全期计算 (1962-2024)
first, last = data[0], data[-1]
n = last['year'] - first['year']

earn_cagr = (last['total_earnings_M'] / first['total_earnings_M']) ** (1/n) - 1
mktcap_cagr = (last['total_mktcap_M'] / first['total_mktcap_M']) ** (1/n) - 1
pe1 = first['aggregate_pe']
pe2 = last['aggregate_pe']
pe_change = (pe2 / pe1) ** (1/n) - 1

# 平均股息率（排除异常年份）
valid_divs = [r['dividend_yield_pct'] for r in data if r['dividend_yield_pct'] < 10]
avg_div = sum(valid_divs) / len(valid_divs)

print(f"\n{'='*90}")
print(f"全期统计 (1962-2024, {n} 年)")
print(f"{'='*90}")
print(f"""
  总盈利增长:     ${first['total_earnings_M']/1000:.1f}B → ${last['total_earnings_M']/1000:.1f}B
  总盈利 CAGR:    {earn_cagr*100:.2f}%
  总市值增长:     ${first['total_mktcap_M']/1000:.1f}B → ${last['total_mktcap_M']/1000:.1f}B
  总市值 CAGR:    {mktcap_cagr*100:.2f}%
  PE 变化:        {pe1:.1f} → {pe2:.1f} (年化 {pe_change*100:.2f}%)
  平均股息率:     {avg_div:.2f}%
""")

# 回报分解
print(f"  回报分解:")
print(f"    市值增长    = 盈利增长 + PE扩张")
print(f"    {mktcap_cagr*100:.2f}%      = {earn_cagr*100:.2f}%     + {pe_change*100:.2f}%")
print(f"")
print(f"    名义总回报 ≈ 市值增长 + 股息率")
print(f"    {mktcap_cagr*100 + avg_div:.2f}%     ≈ {mktcap_cagr*100:.2f}%     + {avg_div:.2f}%")

# 5年滚动盈利增长
print(f"\n{'='*90}")
print("5年滚动盈利增长")
print(f"{'='*90}")
print(f"\n{'期间':>14} {'盈利CAGR':>10} {'PE变化':>10}")
print("-" * 40)

for i in range(len(data)):
    r1 = data[i]
    # 找 5 年后
    r2 = None
    for r in data:
        if r['year'] == r1['year'] + 5:
            r2 = r
            break
    if not r2:
        continue
    if r1['total_earnings_M'] <= 0 or r2['total_earnings_M'] <= 0:
        continue

    e_cagr = (r2['total_earnings_M'] / r1['total_earnings_M']) ** (1/5) - 1
    p1 = r1['aggregate_pe']
    p2 = r2['aggregate_pe']
    if p1 and p2 and p1 > 0 and p2 > 0 and p1 < 100 and p2 < 100:
        pe_c = (p2/p1)**(1/5) - 1
    else:
        pe_c = None

    pe_str = f"{pe_c*100:>8.2f}%" if pe_c is not None else "     N/A"
    print(f"{r1['year']}-{r2['year']:>4} {e_cagr*100:>8.2f}% {pe_str}")

# 10年滚动
print(f"\n{'='*90}")
print("10年滚动盈利增长")
print(f"{'='*90}")
print(f"\n{'期间':>14} {'盈利CAGR':>10} {'PE变化':>10} {'实际总盈利增长':>14}")
print("-" * 54)

for i in range(len(data)):
    r1 = data[i]
    r2 = None
    for r in data:
        if r['year'] == r1['year'] + 10:
            r2 = r
            break
    if not r2:
        continue
    if r1['total_earnings_M'] <= 0 or r2['total_earnings_M'] <= 0:
        continue

    e_cagr = (r2['total_earnings_M'] / r1['total_earnings_M']) ** (1/10) - 1
    total_growth = r2['total_earnings_M'] / r1['total_earnings_M']
    p1 = r1['aggregate_pe']
    p2 = r2['aggregate_pe']
    if p1 and p2 and p1 > 0 and p2 > 0 and p1 < 100 and p2 < 100:
        pe_c = (p2/p1)**(1/10) - 1
    else:
        pe_c = None

    pe_str = f"{pe_c*100:>8.2f}%" if pe_c is not None else "     N/A"
    print(f"{r1['year']}-{r2['year']:>4} {e_cagr*100:>8.2f}% {pe_str}   {total_growth:>10.1f}x")

# 对比 Shiller
print(f"\n{'='*90}")
print("对比 Shiller 指数级数据")
print(f"{'='*90}")
print(f"""
                          公司级别(Compustat)     Shiller(指数级)
  数据区间:               1962-2024              1928-2024
  盈利年化增长:           {earn_cagr*100:.2f}%                5.16%
  PE 起始:                {pe1:.1f}                  11.1
  PE 结束:                {pe2:.1f}                  24.0
  PE 年化变化:            {pe_change*100:.2f}%                0.81%
  平均股息率:             {avg_div:.2f}%                2.90%

  注意：
  1. 公司级别"总盈利增长"包含了新公司加入的盈利贡献
     （指数不断有新成分股加入，总盈利自然膨胀）
  2. Shiller 的 EPS 是"每单位指数"的盈利，已排除成分股变动影响
  3. 因此公司级别盈利增长（{earn_cagr*100:.2f}%）> Shiller EPS 增长（5.16%）是合理的
  4. 差值约 {earn_cagr*100 - 5.16:.1f}% 反映了指数"新陈代谢"带来的总盈利膨胀
""")
