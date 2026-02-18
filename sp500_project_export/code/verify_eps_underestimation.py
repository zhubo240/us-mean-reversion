"""
验证假说：市场系统性低估盈利增速，导致"风险溢价"部分来自盈利超预期

方法：
1. 下载 Shiller 历史数据（S&P 500 EPS, Price, Dividends, PE, CPI）
2. 分解历史回报为：股息收益率 + EPS增长 + PE变化
3. 用 Gordon 模型反推市场隐含增长预期，对比实际增长
4. 检验实际 EPS 增长是否系统性超越隐含预期
"""

import json
import math
import os

# ============================================================
# Shiller 年度数据（来源：Robert Shiller CAPE dataset）
# 取每年1月数据作为年度代表
# Fields: year, price, earnings(trailing 12m), dividend(trailing 12m), CPI, 10yr_treasury_yield
# ============================================================

SHILLER_ANNUAL = {
    1928: {"price": 17.53, "eps": 1.58, "div": 0.77, "cpi": 17.1, "bond_yield": 3.33},
    1929: {"price": 24.86, "eps": 1.82, "div": 0.88, "cpi": 17.2, "bond_yield": 3.42},
    1930: {"price": 21.71, "eps": 1.65, "div": 0.97, "cpi": 17.1, "bond_yield": 3.29},
    1935: {"price": 9.26,  "eps": 0.68, "div": 0.47, "cpi": 13.6, "bond_yield": 2.79},
    1940: {"price": 12.30, "eps": 1.06, "div": 0.67, "cpi": 13.9, "bond_yield": 2.26},
    1945: {"price": 13.49, "eps": 0.96, "div": 0.61, "cpi": 17.8, "bond_yield": 2.37},
    1950: {"price": 16.88, "eps": 2.34, "div": 1.14, "cpi": 23.5, "bond_yield": 2.32},
    1955: {"price": 36.75, "eps": 3.62, "div": 1.64, "cpi": 26.7, "bond_yield": 2.84},
    1960: {"price": 55.61, "eps": 3.27, "div": 1.95, "cpi": 29.4, "bond_yield": 4.72},
    1965: {"price": 84.75, "eps": 5.19, "div": 2.72, "cpi": 31.2, "bond_yield": 4.19},
    1970: {"price": 85.02, "eps": 5.51, "div": 3.07, "cpi": 37.8, "bond_yield": 7.79},
    1975: {"price": 70.23, "eps": 7.96, "div": 3.46, "cpi": 49.3, "bond_yield": 7.50},
    1980: {"price": 110.87,"eps": 14.82,"div": 5.97, "cpi": 72.6, "bond_yield": 10.80},
    1985: {"price": 171.61,"eps": 14.61,"div": 7.79, "cpi": 105.5,"bond_yield": 11.38},
    1990: {"price": 339.97,"eps": 22.36,"div": 11.05,"cpi": 127.4,"bond_yield": 8.21},
    1995: {"price": 470.42,"eps": 30.60,"div": 13.36,"cpi": 150.3,"bond_yield": 7.78},
    2000: {"price": 1425.59,"eps": 52.15,"div": 16.13,"cpi": 168.8,"bond_yield": 6.66},
    2005: {"price": 1181.41,"eps": 58.55,"div": 19.01,"cpi": 190.7,"bond_yield": 4.22},
    2010: {"price": 1123.58,"eps": 56.86,"div": 22.41,"cpi": 217.5,"bond_yield": 3.73},
    2015: {"price": 2028.18,"eps": 100.98,"div": 39.44,"cpi": 234.7,"bond_yield": 1.88},
    2020: {"price": 3278.20,"eps": 139.47,"div": 58.28,"cpi": 258.8,"bond_yield": 1.88},
    2024: {"price": 4742.83,"eps": 197.78,"div": 67.00,"cpi": 308.4,"bond_yield": 3.97},
}

def analyze():
    years = sorted(SHILLER_ANNUAL.keys())

    print("=" * 80)
    print("验证假说：市场是否系统性低估了 S&P 500 盈利增速？")
    print("=" * 80)

    # ============================================================
    # Part 1: 历史 EPS 增长率（名义 & 实际）
    # ============================================================
    print("\n" + "=" * 80)
    print("Part 1: S&P 500 历史 EPS 增长")
    print("=" * 80)

    print(f"\n{'期间':<16} {'名义EPS增长':>10} {'通胀':>8} {'实际EPS增长':>10} {'PE起':>6} {'PE末':>6} {'PE年化变化':>10}")
    print("-" * 76)

    # 计算各时段 EPS 增长
    periods = []
    for i in range(len(years) - 1):
        y1, y2 = years[i], years[i+1]
        d1, d2 = SHILLER_ANNUAL[y1], SHILLER_ANNUAL[y2]
        n = y2 - y1

        # 名义 EPS CAGR
        eps_growth = (d2["eps"] / d1["eps"]) ** (1/n) - 1

        # CPI 通胀率
        inflation = (d2["cpi"] / d1["cpi"]) ** (1/n) - 1

        # 实际 EPS CAGR
        real_eps_growth = (1 + eps_growth) / (1 + inflation) - 1

        # PE
        pe1 = d1["price"] / d1["eps"]
        pe2 = d2["price"] / d2["eps"]
        pe_change = (pe2 / pe1) ** (1/n) - 1

        periods.append({
            "period": f"{y1}-{y2}",
            "years": n,
            "eps_growth": eps_growth,
            "inflation": inflation,
            "real_eps_growth": real_eps_growth,
            "pe_start": pe1,
            "pe_end": pe2,
            "pe_change": pe_change,
        })

        print(f"{y1}-{y2}  ({n:2d}yr)  {eps_growth*100:>8.2f}%  {inflation*100:>6.2f}%  {real_eps_growth*100:>8.2f}%  {pe1:>5.1f}  {pe2:>5.1f}  {pe_change*100:>8.2f}%")

    # 全期
    y_first, y_last = years[0], years[-1]
    d_first, d_last = SHILLER_ANNUAL[y_first], SHILLER_ANNUAL[y_last]
    n_total = y_last - y_first
    total_eps_growth = (d_last["eps"] / d_first["eps"]) ** (1/n_total) - 1
    total_inflation = (d_last["cpi"] / d_first["cpi"]) ** (1/n_total) - 1
    total_real_eps = (1 + total_eps_growth) / (1 + total_inflation) - 1
    pe_first = d_first["price"] / d_first["eps"]
    pe_last = d_last["price"] / d_last["eps"]
    total_pe_change = (pe_last / pe_first) ** (1/n_total) - 1

    print("-" * 76)
    print(f"{'全期':<7} ({n_total:2d}yr)  {total_eps_growth*100:>8.2f}%  {total_inflation*100:>6.2f}%  {total_real_eps*100:>8.2f}%  {pe_first:>5.1f}  {pe_last:>5.1f}  {total_pe_change*100:>8.2f}%")

    # ============================================================
    # Part 2: 回报分解
    # ============================================================
    print("\n" + "=" * 80)
    print("Part 2: 回报分解（名义总回报 ≈ 股息率 + EPS增长 + PE变化）")
    print("=" * 80)

    print(f"\n{'期间':<16} {'总回报':>8} {'股息率':>8} {'EPS增长':>8} {'PE变化':>8} {'三项之和':>8} {'误差':>6}")
    print("-" * 72)

    for i in range(len(years) - 1):
        y1, y2 = years[i], years[i+1]
        d1, d2 = SHILLER_ANNUAL[y1], SHILLER_ANNUAL[y2]
        n = y2 - y1

        # 近似总回报 = 价格升值 + 股息
        price_return = (d2["price"] / d1["price"]) ** (1/n) - 1
        avg_div_yield = (d1["div"]/d1["price"] + d2["div"]/d2["price"]) / 2
        total_return = price_return + avg_div_yield  # 简化近似

        eps_growth = (d2["eps"] / d1["eps"]) ** (1/n) - 1
        pe1 = d1["price"] / d1["eps"]
        pe2 = d2["price"] / d2["eps"]
        pe_change = (pe2 / pe1) ** (1/n) - 1

        decomp_sum = avg_div_yield + eps_growth + pe_change
        error = total_return - decomp_sum

        print(f"{y1}-{y2}  ({n:2d}yr)  {total_return*100:>6.2f}%  {avg_div_yield*100:>6.2f}%  {eps_growth*100:>6.2f}%  {pe_change*100:>6.2f}%  {decomp_sum*100:>6.2f}%  {error*100:>4.2f}%")

    # 全期分解
    total_price_return = (d_last["price"] / d_first["price"]) ** (1/n_total) - 1
    avg_div_all = (d_first["div"]/d_first["price"] + d_last["div"]/d_last["price"]) / 2
    total_return_all = total_price_return + avg_div_all
    decomp_all = avg_div_all + total_eps_growth + total_pe_change

    print("-" * 72)
    print(f"{'全期':<7} ({n_total:2d}yr)  {total_return_all*100:>6.2f}%  {avg_div_all*100:>6.2f}%  {total_eps_growth*100:>6.2f}%  {total_pe_change*100:>6.2f}%  {decomp_all*100:>6.2f}%  {(total_return_all-decomp_all)*100:>4.2f}%")

    # ============================================================
    # Part 3: Gordon 模型 - 隐含增长 vs 实际增长
    # ============================================================
    print("\n" + "=" * 80)
    print("Part 3: 市场隐含增长预期 vs 实际增长（Gordon 模型）")
    print("=" * 80)
    print("\n使用 Gordon 模型: g_implied = r - D/P")
    print("其中 r = 国债收益率 + 合理风险溢价(2%，Mehra-Prescott)")
    print("如果 actual_g > implied_g，说明市场低估了增长\n")

    print(f"{'起始年':<8} {'国债利率':>8} {'r(+2%)':>8} {'D/P':>8} {'隐含g':>8} {'实际10yr_g':>10} {'差值':>8} {'低估?':>6}")
    print("-" * 74)

    underestimate_count = 0
    total_diff = 0
    valid_count = 0

    for i in range(len(years)):
        y = years[i]
        d = SHILLER_ANNUAL[y]

        # 找到 10 年后的数据
        y_future = None
        for y2 in years:
            if y2 >= y + 8 and y2 <= y + 12:
                y_future = y2
                break

        if y_future is None:
            continue

        d_future = SHILLER_ANNUAL[y_future]
        actual_n = y_future - y

        bond_yield = d["bond_yield"] / 100
        r = bond_yield + 0.02  # 加 2% 合理风险溢价
        div_yield = d["div"] / d["price"]

        implied_g = r - div_yield

        # 实际名义 EPS 增长
        actual_g = (d_future["eps"] / d["eps"]) ** (1/actual_n) - 1

        diff = actual_g - implied_g
        is_under = "是" if diff > 0 else "否"

        if diff > 0:
            underestimate_count += 1
        total_diff += diff
        valid_count += 1

        print(f"{y:<8} {bond_yield*100:>6.2f}%  {r*100:>6.2f}%  {div_yield*100:>6.2f}%  {implied_g*100:>6.2f}%  {actual_g*100:>8.2f}%  {diff*100:>6.2f}%  {is_under:>4}")

    print("-" * 74)
    print(f"低估次数: {underestimate_count}/{valid_count}")
    print(f"平均差值（实际-隐含）: {total_diff/valid_count*100:.2f}%")

    # ============================================================
    # Part 4: 用实际观察到的风险溢价 vs 合理风险溢价分解
    # ============================================================
    print("\n" + "=" * 80)
    print("Part 4: '风险溢价'的分解")
    print("=" * 80)

    avg_bond = sum(d["bond_yield"] for d in SHILLER_ANNUAL.values()) / len(SHILLER_ANNUAL)

    print(f"""
全期统计（{y_first}-{y_last}）:
  名义总回报（近似）:       {total_return_all*100:.2f}%
  平均国债利率:             {avg_bond:.2f}%
  观察到的风险溢价:         {total_return_all*100 - avg_bond:.2f}%

回报分解:
  股息收益率:               {avg_div_all*100:.2f}%
  名义 EPS 增长:            {total_eps_growth*100:.2f}%
  PE 扩张:                  {total_pe_change*100:.2f}%

如果"合理"风险溢价只有 ~2%（Mehra-Prescott）:
  "合理"总回报:             {avg_bond + 2:.2f}%
  实际总回报:               {total_return_all*100:.2f}%
  "异常"超额部分:           {total_return_all*100 - avg_bond - 2:.2f}%

这 {total_return_all*100 - avg_bond - 2:.2f}% 的"异常"超额回报，可能的解释:
  1. 人类非理性恐惧 → 要求过高的风险补偿
  2. 市场系统性低估盈利增速 → 盈利持续超预期 → PE修正带来额外收益  ← 你的假说
  3. 幸存者偏差（美国市场是特例）
  4. 以上所有因素的组合
""")

    # ============================================================
    # Part 5: 关键论据总结
    # ============================================================
    print("=" * 80)
    print("Part 5: 结论")
    print("=" * 80)
    print(f"""
1. 全期名义 EPS 年化增长 = {total_eps_growth*100:.2f}%
   远超 GDP 增长（~3% 实际），显示企业部门持续扩大利润份额

2. PE 从 {pe_first:.1f} 扩张到 {pe_last:.1f}，年化 {total_pe_change*100:.2f}%
   确实有长期向上修正，但幅度有限

3. Gordon 模型测试: 在"合理"风险溢价(2%)假设下，
   市场隐含增长预期 vs 实际增长比较:
   - 低估次数: {underestimate_count}/{valid_count}
   - 平均低估幅度: {total_diff/valid_count*100:.2f}%

4. 是否需要公司级别数据？
   - 指数级别验证: 已可完成（用 Shiller 数据）
   - 公司级别可以进一步验证: 个股盈利预测 vs 实际盈利的偏差分布
   - 需要 I/B/E/S 分析师预测数据（1985年起）做最干净的验证
""")

if __name__ == "__main__":
    analyze()
