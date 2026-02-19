"""
探索 CRSP/Compustat 数据集：验证数据完整性、覆盖范围、合并可行性
"""
import csv
import os
from collections import defaultdict, Counter

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'crsp_compustat')

def load_csv(filename):
    path = os.path.join(DATA_DIR, filename)
    with open(path, 'r') as f:
        reader = csv.DictReader(f)
        return list(reader)

def explore_sp500():
    print("=" * 70)
    print("1. S&P 500 成分股列表 (sp500_constituents.csv)")
    print("=" * 70)
    rows = load_csv('sp500_constituents.csv')
    print(f"   总记录数: {len(rows)}")
    print(f"   字段: {list(rows[0].keys())}")

    # 统计 permno 数量
    permnos = set(r['permno'] for r in rows)
    print(f"   唯一 PERMNO 数: {len(permnos)}")

    # 日期范围
    starts = [r['start'] for r in rows if r['start']]
    ends = [r['ending'] for r in rows if r['ending']]
    print(f"   最早 start: {min(starts)}")
    print(f"   最晚 start: {max(starts)}")
    print(f"   最早 ending: {min(ends)}")
    print(f"   最晚 ending: {max(ends)}")

    # 每个十年有多少公司在指数中
    decade_counts = defaultdict(set)
    for r in rows:
        start_year = int(r['start'][:4])
        end_year = int(r['ending'][:4])
        for decade in range(1920, 2030, 10):
            if start_year <= decade + 9 and end_year >= decade:
                decade_counts[decade].add(r['permno'])

    print("\n   各十年代活跃成分股数:")
    for decade in sorted(decade_counts.keys()):
        print(f"     {decade}s: {len(decade_counts[decade])} 家")

    return rows, permnos

def explore_ccm():
    print("\n" + "=" * 70)
    print("2. CCM Link Table (ccm_link_table.csv)")
    print("=" * 70)
    rows = load_csv('ccm_link_table.csv')
    print(f"   总记录数: {len(rows)}")
    print(f"   字段: {list(rows[0].keys())}")

    gvkeys = set(r['gvkey'] for r in rows)
    permnos = set(r['LPERMNO'] for r in rows)
    print(f"   唯一 GVKEY 数: {len(gvkeys)}")
    print(f"   唯一 LPERMNO 数: {len(permnos)}")

    # LINKPRIM 分布
    linkprim = Counter(r['LINKPRIM'] for r in rows)
    print(f"   LINKPRIM 分布: {dict(linkprim)}")

    # LINKTYPE 分布
    linktype = Counter(r['LINKTYPE'] for r in rows)
    print(f"   LINKTYPE 分布: {dict(linktype)}")

    return rows, gvkeys, permnos

def explore_compustat():
    print("\n" + "=" * 70)
    print("3. Compustat Annual (compustat_annual.csv)")
    print("=" * 70)
    rows = load_csv('compustat_annual.csv')
    print(f"   总记录数: {len(rows)}")
    print(f"   字段: {list(rows[0].keys())}")

    gvkeys = set(r['gvkey'] for r in rows)
    print(f"   唯一 GVKEY 数: {len(gvkeys)}")

    # 日期范围
    dates = [r['datadate'] for r in rows if r['datadate']]
    print(f"   最早 datadate: {min(dates)}")
    print(f"   最晚 datadate: {max(dates)}")

    # GICS 行业覆盖
    gind_filled = sum(1 for r in rows if r.get('gind') and r['gind'].strip())
    gsubind_filled = sum(1 for r in rows if r.get('gsubind') and r['gsubind'].strip())
    print(f"   有 GICS Industry (gind): {gind_filled}/{len(rows)} ({gind_filled/len(rows)*100:.1f}%)")
    print(f"   有 GICS Sub-Industry (gsubind): {gsubind_filled}/{len(rows)} ({gsubind_filled/len(rows)*100:.1f}%)")

    # 关键字段覆盖率
    key_fields = ['epspx', 'epsfx', 'ni', 'revt', 'csho', 'prcc_f', 'dvpsx_f', 'at', 'bkvlps', 'seq']
    print("\n   关键字段覆盖率:")
    for field in key_fields:
        filled = sum(1 for r in rows if r.get(field) and r[field].strip())
        print(f"     {field:>10}: {filled:>7}/{len(rows)} ({filled/len(rows)*100:.1f}%)")

    # 每十年记录数
    decade_counts = defaultdict(int)
    for r in rows:
        if r['datadate']:
            year = int(r['datadate'][:4])
            decade = (year // 10) * 10
            decade_counts[decade] += 1

    print("\n   各十年代记录数:")
    for decade in sorted(decade_counts.keys()):
        print(f"     {decade}s: {decade_counts[decade]:>6} 条")

    return rows, gvkeys

def check_merge_coverage(sp500_permnos, ccm_rows, compustat_gvkeys):
    print("\n" + "=" * 70)
    print("4. 合并覆盖率检查")
    print("=" * 70)

    # SP500 PERMNO → CCM → GVKEY
    ccm_permno_to_gvkey = {}
    for r in ccm_rows:
        permno = r['LPERMNO']
        if permno not in ccm_permno_to_gvkey:
            ccm_permno_to_gvkey[permno] = set()
        ccm_permno_to_gvkey[permno].add(r['gvkey'])

    sp500_matched = 0
    sp500_gvkeys = set()
    for permno in sp500_permnos:
        if permno in ccm_permno_to_gvkey:
            sp500_matched += 1
            sp500_gvkeys.update(ccm_permno_to_gvkey[permno])

    print(f"   S&P 500 PERMNO 总数: {len(sp500_permnos)}")
    print(f"   能在 CCM 中找到 GVKEY: {sp500_matched} ({sp500_matched/len(sp500_permnos)*100:.1f}%)")
    print(f"   对应的唯一 GVKEY 数: {len(sp500_gvkeys)}")

    # 这些 GVKEY 在 Compustat 中有多少
    in_compustat = sp500_gvkeys & compustat_gvkeys
    print(f"   在 Compustat 中有数据: {len(in_compustat)} ({len(in_compustat)/len(sp500_gvkeys)*100:.1f}%)")
    print(f"   缺失: {len(sp500_gvkeys) - len(in_compustat)}")

    return sp500_gvkeys, in_compustat

def main():
    sp500_rows, sp500_permnos = explore_sp500()
    ccm_rows, ccm_gvkeys, ccm_permnos = explore_ccm()
    compustat_rows, compustat_gvkeys = explore_compustat()
    sp500_gvkeys, matched = check_merge_coverage(sp500_permnos, ccm_rows, compustat_gvkeys)

    print("\n" + "=" * 70)
    print("5. 结论")
    print("=" * 70)
    print(f"""
   数据可用性总结:
   - S&P 500 成分股: {len(sp500_permnos)} 家公司, 1925-2024
   - Compustat 财务数据: {len(compustat_gvkeys)} 家公司
   - 可合并覆盖率: {len(matched)}/{len(sp500_gvkeys)} ({len(matched)/len(sp500_gvkeys)*100:.1f}%)
   - Compustat 数据起点: ~1950 (卖家已确认)
   - CRSP 月度数据: 待下载 (57.1M, 需百度网盘客户端)

   可立即进行的分析:
   1. 1950-2024 S&P 500 成分股年度 EPS 聚合
   2. 公司级别 PE 计算 (prcc_f / epspx)
   3. GICS 行业分类下的盈利分析
   4. EPS 增长率 vs 市场预期对比 (验证低估假说)
""")

if __name__ == "__main__":
    main()
