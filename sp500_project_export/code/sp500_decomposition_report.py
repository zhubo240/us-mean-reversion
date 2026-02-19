"""
三层分解报表输出：读取 JSON，打印格式化表格
"""
import json
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'sp500_3level_decomposition.json')

with open(DATA_PATH) as f:
    D = json.load(f)

agg = {r['year']: r for r in D['aggregate']}
sectors_by_year = {}
for r in D['sectors']:
    sectors_by_year.setdefault(r['year'], []).append(r)

def pct(v, w=8):
    if v is None:
        return f"{'N/A':>{w}}"
    return f"{v*100:>{w}.2f}%"

def money(v, w=12):
    if v is None:
        return f"{'N/A':>{w}}"
    return f"${v/1000:>{w-1},.0f}B"

# ═══════════════════════════════════════════════════════════
# 表1: 年度总量分解
# ═══════════════════════════════════════════════════════════
print("=" * 120)
print("表1: S&P 500 年度回报分解 (1985-2024)")
print("    总回报 = 盈利增长 + PE扩张 + 股息率")
print("=" * 120)

print(f"{'年份':>6} {'公司':>5} {'盈利($B)':>10} {'市值($B)':>11} {'PE':>7} "
      f"{'盈利增长':>9} {'PE扩张':>9} {'价格回报':>9} {'股息率':>8} {'总回报':>9}")
print("-" * 100)

for year in range(1985, 2025):
    a = agg.get(year)
    if not a:
        continue
    pe_str = f"{a['pe']:.1f}" if a['pe'] and a['pe'] < 100 else "N/A"
    print(f"{year:>6} {a['count']:>5} {a['ni']/1000:>9,.1f} {a['mktcap']/1000:>10,.1f} {pe_str:>7} "
          f"{pct(a['earnings_growth'], 9)} {pct(a['pe_expansion'], 9)} {pct(a['price_return'], 9)} "
          f"{pct(a['dividend_yield'], 8)} {pct(a['total_return'], 9)}")

# 全期
years = sorted(agg.keys())
first, last = agg[years[0]], agg[years[-1]]
n = years[-1] - years[0]
if first['mktcap'] > 0 and last['mktcap'] > 0:
    ann_price = (last['mktcap'] / first['mktcap_prior']) ** (1/n) - 1
    ann_earn = (last['ni'] / first['ni_prior']) ** (1/n) - 1 if first['ni_prior'] > 0 and last['ni'] > 0 else None
    avg_div = sum(a['dividend_yield'] or 0 for a in agg.values()) / len(agg)
    ann_pe = (1 + ann_price) / (1 + ann_earn) - 1 if ann_earn is not None else None
    ann_total = ann_price + avg_div

    print("-" * 100)
    print(f"{'全期':>6} {'':>5} {'':>10} {'':>11} {'':>7} "
          f"{pct(ann_earn, 9)} {pct(ann_pe, 9)} {pct(ann_price, 9)} "
          f"{pct(avg_div, 8)} {pct(ann_total, 9)}")
    print(f"\n  全期年化分解 ({years[0]}-{years[-1]}, {n}年):")
    print(f"    盈利增长:  {ann_earn*100:.2f}%")
    print(f"    PE 扩张:   {ann_pe*100:.2f}%")
    print(f"    股息率:    {avg_div*100:.2f}%")
    print(f"    ─────────────────")
    print(f"    总回报:    {ann_total*100:.2f}%")

# ═══════════════════════════════════════════════════════════
# 表2: 行业贡献（关键年份）
# ═══════════════════════════════════════════════════════════
print(f"\n{'=' * 120}")
print("表2: 行业对 S&P 500 回报的贡献 (市值加权)")
print(f"{'=' * 120}")

for year in [1990, 2000, 2010, 2020, 2024]:
    secs = sectors_by_year.get(year, [])
    a = agg.get(year)
    if not secs or not a:
        continue

    secs_sorted = sorted(secs, key=lambda x: -(x.get('weight') or 0))

    print(f"\n  ── {year} ──")
    print(f"  {'行业':<16} {'权重':>7} {'价格回报':>9} {'→贡献':>8} {'盈利增长':>9} {'PE扩张':>9} {'股息率':>8}")
    print("  " + "-" * 72)

    sum_contrib = 0
    for s in secs_sorted:
        if s['sector'] == 'XX':
            continue
        w = s.get('weight')
        if w is None:
            continue
        cp = s.get('contrib_price') or 0
        sum_contrib += cp
        print(f"  {s['sector_name']:<16} {w*100:>6.1f}% {pct(s['price_return'], 9)} "
              f"{cp*100:>+7.2f}% {pct(s['earnings_growth'], 9)} {pct(s['pe_expansion'], 9)} "
              f"{pct(s['dividend_yield'], 8)}")

    print("  " + "-" * 72)
    print(f"  {'Σ行业贡献':<16} {'':>7} {'':>9} {sum_contrib*100:>+7.2f}%")
    print(f"  {'总量直接计算':<16} {'':>7} {pct(a['price_return'], 9)} {a['price_return']*100:>+7.2f}%")
    diff_bps = (a['price_return'] - sum_contrib) * 10000
    print(f"  {'差异':<16} {'':>7} {'':>9} {diff_bps:>+7.1f}bp")

# ═══════════════════════════════════════════════════════════
# 表3: 验证表
# ═══════════════════════════════════════════════════════════
print(f"\n{'=' * 120}")
print("表3: 三层加总验证 (Σ公司 = Σ行业 = 总量)")
print(f"{'=' * 120}")

print(f"{'年份':>6} {'总量盈利':>10} {'Σ公司盈利':>10} {'差值':>8} "
      f"{'总量市值':>12} {'Σ公司市值':>12} {'差值':>8} {'回报差(bp)':>10}")
print("-" * 84)

for v in D['verification']:
    y = v['year']
    if y % 5 == 0 or y == 2024:
        dr = f"{v['diff_return']:.1f}" if v['diff_return'] is not None else "N/A"
        print(f"{y:>6} {v['agg_ni']/1000:>9,.1f} {v['sum_company_ni']/1000:>9,.1f} {v['diff_ni']:>7,.1f} "
              f"{v['agg_mktcap']/1000:>11,.1f} {v['sum_company_mktcap']/1000:>11,.1f} {v['diff_mktcap']:>7,.1f} "
              f"{dr:>10}")

max_ni = max(abs(v['diff_ni']) for v in D['verification'])
max_mc = max(abs(v['diff_mktcap']) for v in D['verification'])
max_ret = max(abs(v['diff_return']) for v in D['verification'] if v['diff_return'] is not None)
print(f"\n  最大差异: 盈利 ${max_ni}M, 市值 ${max_mc}M, 回报 {max_ret} bp")
print(f"  结论: {'✓ 验证通过' if max_ni < 1 and max_mc < 1 else '✗ 需要检查'}")

# ═══════════════════════════════════════════════════════════
# 表4: 滚动窗口分解
# ═══════════════════════════════════════════════════════════
print(f"\n{'=' * 120}")
print("表4: 滚动窗口回报分解 (年化)")
print(f"{'=' * 120}")

for w in [5, 10, 20]:
    data = D['rolling'].get(str(w), [])
    if not data:
        continue
    print(f"\n  ── {w}年窗口 ──")
    print(f"  {'期间':>12} {'总回报':>9} {'盈利增长':>9} {'PE扩张':>9} {'股息率':>8}")
    print("  " + "-" * 52)

    for r in data:
        if r['start'] % 5 == 0 or r['end'] == 2024:
            eg = f"{r['ann_earnings_growth']:.2f}%" if r['ann_earnings_growth'] is not None else "N/A"
            pe = f"{r['ann_pe_expansion']:.2f}%" if r['ann_pe_expansion'] is not None else "N/A"
            dy = f"{r['ann_dividend_yield']:.2f}%" if r['ann_dividend_yield'] is not None else "N/A"
            print(f"  {r['start']}-{r['end']:>4} {r['ann_total_return']:>8.2f}% {eg:>9} {pe:>9} {dy:>8}")

# ═══════════════════════════════════════════════════════════
# 表5: 均值回归统计
# ═══════════════════════════════════════════════════════════
print(f"\n{'=' * 120}")
print("表5: 均值回归统计 — 持有时间越长，回报越收敛")
print(f"{'=' * 120}")

print(f"\n  {'窗口':>6} {'样本数':>6} {'均值':>8} {'标准差':>8} {'最小':>8} {'最大':>8} {'波动范围':>8}")
print("  " + "-" * 56)

for w in [5, 10, 20]:
    s = D['mean_reversion'].get(str(w))
    if not s:
        continue
    print(f"  {w:>4}年 {s['samples']:>6} {s['mean']:>7.2f}% {s['std']:>7.2f}% "
          f"{s['min']:>7.2f}% {s['max']:>7.2f}% {s['range']:>7.2f}%")

print(f"""
  解读:
  - 5年窗口: 标准差 {D['mean_reversion']['5']['std']:.2f}%, 范围 {D['mean_reversion']['5']['range']:.1f}% → 短期波动大
  - 20年窗口: 标准差 {D['mean_reversion']['20']['std']:.2f}%, 范围 {D['mean_reversion']['20']['range']:.1f}% → 长期收敛
  - 标准差缩小 {D['mean_reversion']['5']['std']/D['mean_reversion']['20']['std']:.1f}x → 均值回归效应显著
  - 20年均值 {D['mean_reversion']['20']['mean']:.2f}% ≈ 长期名义回报水平
""")

# ═══════════════════════════════════════════════════════════
# 表6: Top Contributors (最新年份)
# ═══════════════════════════════════════════════════════════
print(f"{'=' * 120}")
print("表6: 2024 年 Top 10 盈利变化公司")
print(f"{'=' * 120}")

for tc in D['top_contributors']:
    if tc['year'] == 2024:
        print(f"\n  {'排名':>4} {'公司':<30} {'行业':<14} {'盈利变化($M)':>14} {'当年盈利($M)':>14}")
        print("  " + "-" * 80)
        for i, e in enumerate(tc['top_earnings'][:10]):
            ch = e['change']
            print(f"  {i+1:>4} {e['name']:<30} {e['sector']:<14} {ch:>+13,.0f} {e['ni']:>13,.0f}")
        break

print(f"\n{'=' * 120}")
print("表6b: 2024 年 Top 10 PE 变化公司 (按市值影响)")
print(f"{'=' * 120}")

for tc in D['top_contributors']:
    if tc['year'] == 2024:
        print(f"\n  {'排名':>4} {'公司':<30} {'行业':<14} {'PE变化':>10} {'PE':>8} {'市值($B)':>10}")
        print("  " + "-" * 80)
        for i, e in enumerate(tc['top_pe'][:10]):
            print(f"  {i+1:>4} {e['name']:<30} {e['sector']:<14} {e['pe_change']:>+9.1f} "
                  f"{e['pe']:>7.1f} {e['mktcap']/1000:>9,.1f}")
        break
