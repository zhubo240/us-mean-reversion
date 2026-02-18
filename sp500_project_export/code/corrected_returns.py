"""
修正 EPS 低估后的"真实"指数增长

逻辑：
- 观察到的回报 = 合理回报 + EPS低估带来的"意外"收益
- 如果市场一开始就正确预估了 EPS 增长，起始 PE 会更高，后续回报会更低
- 修正后的回报 = 观察到的回报 - EPS低估贡献
"""

# 复用 Shiller 数据
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
    y_first, y_last = years[0], years[-1]
    d_first, d_last = SHILLER_ANNUAL[y_first], SHILLER_ANNUAL[y_last]
    n_total = y_last - y_first

    # 基础数据
    total_eps_growth = (d_last["eps"] / d_first["eps"]) ** (1/n_total) - 1
    total_inflation = (d_last["cpi"] / d_first["cpi"]) ** (1/n_total) - 1
    pe_first = d_first["price"] / d_first["eps"]
    pe_last = d_last["price"] / d_last["eps"]
    total_pe_change = (pe_last / pe_first) ** (1/n_total) - 1
    total_price_return = (d_last["price"] / d_first["price"]) ** (1/n_total) - 1
    avg_div_yield = (d_first["div"]/d_first["price"] + d_last["div"]/d_last["price"]) / 2
    total_return = total_price_return + avg_div_yield
    avg_bond = sum(d["bond_yield"] for d in SHILLER_ANNUAL.values()) / len(SHILLER_ANNUAL)
    observed_risk_premium = total_return * 100 - avg_bond

    # Gordon 模型计算各时段的低估幅度
    underestimate_values = []
    for i in range(len(years)):
        y = years[i]
        d = SHILLER_ANNUAL[y]
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
        r = bond_yield + 0.02
        div_yield = d["div"] / d["price"]
        implied_g = r - div_yield
        actual_g = (d_future["eps"] / d["eps"]) ** (1/actual_n) - 1
        diff = actual_g - implied_g
        underestimate_values.append(diff)

    avg_underestimate = sum(underestimate_values) / len(underestimate_values)

    print("=" * 80)
    print("修正 EPS 低估后的 S&P 500 '真实'回报结构")
    print("=" * 80)

    print(f"""
┌─────────────────────────────────────────────────────────────┐
│            观察到的回报（实际发生的）                          │
├─────────────────────────────────────────────────────────────┤
│  名义总回报:            {total_return*100:>6.2f}%                         │
│    ├── 股息收益率:      {avg_div_yield*100:>6.2f}%                         │
│    ├── EPS 增长:        {total_eps_growth*100:>6.2f}%                         │
│    └── PE 扩张:         {total_pe_change*100:>6.2f}%                         │
│                                                             │
│  国债利率:              {avg_bond:>6.2f}%                         │
│  观察到的风险溢价:      {observed_risk_premium:>6.2f}%                         │
└─────────────────────────────────────────────────────────────┘
""")

    # 修正计算
    # EPS 低估平均幅度
    eps_underest = avg_underestimate * 100

    # 如果市场正确定价，PE 一开始就会更高
    # 多出来的 EPS 增长不会转化为"意外"回报
    # 所以修正后的回报 = 观察回报 - EPS低估贡献
    corrected_risk_premium = observed_risk_premium - eps_underest
    corrected_total_return = avg_bond + corrected_risk_premium

    print(f"""
┌─────────────────────────────────────────────────────────────┐
│            修正后的回报（如果市场正确定价）                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  EPS 低估的平均幅度:    {eps_underest:>6.2f}% /年                      │
│                                                             │
│  这意味着：如果市场一开始就预见到真实的 EPS 增长，             │
│  起始 PE 会更高，买入价更贵，后续回报更低。                    │
│                                                             │
│  修正后的风险溢价:      {corrected_risk_premium:>6.2f}%                         │
│  修正后的总回报:        {corrected_total_return:>6.2f}%                         │
│                                                             │
│  Mehra-Prescott 合理风险溢价: ~2.00%                        │
│  修正后的风险溢价:          {corrected_risk_premium:>6.2f}%                    │
│  残余未解释部分:            {corrected_risk_premium - 2:>6.2f}%                    │
└─────────────────────────────────────────────────────────────┘
""")

    print(f"""
┌─────────────────────────────────────────────────────────────┐
│                     回报归因总结                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  名义总回报  {total_return*100:.2f}%  =                                  │
│                                                             │
│    无风险利率（时间价值）         {avg_bond:>5.2f}%                   │
│    + 合理风险补偿                 2.00%  ← 理性承担风险的报酬 │
│    + EPS 低估修正                 {eps_underest:>5.2f}%  ← 你的假说     │
│    + 残余（恐惧/偏差/幸存者）     {total_return*100 - avg_bond - 2 - eps_underest:>5.2f}%                   │
│    ─────────────────────────────────                        │
│    合计                          {total_return*100:>5.2f}%                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
""")

    # 模拟：如果市场正确定价，1928 年投入 $100 的增长轨迹
    print("=" * 80)
    print("$100 投资增长对比（1928-2024）")
    print("=" * 80)

    actual_rate = total_return
    corrected_rate = corrected_total_return / 100
    bond_rate = avg_bond / 100

    actual_100 = 100 * (1 + actual_rate) ** n_total
    corrected_100 = 100 * (1 + corrected_rate) ** n_total
    bond_100 = 100 * (1 + bond_rate) ** n_total

    print(f"""
  1928 年投入 $100，到 2024 年:

  实际回报 ({total_return*100:.2f}%):               ${actual_100:>15,.0f}
  修正后回报 ({corrected_total_return:.2f}%):           ${corrected_100:>15,.0f}
  纯国债 ({avg_bond:.2f}%):                  ${bond_100:>15,.0f}

  EPS 低估给投资者额外带来的财富:   ${actual_100 - corrected_100:>15,.0f}
  占总财富的比例:                    {(actual_100 - corrected_100)/actual_100*100:.1f}%
""")

    # 按时段对比
    print("=" * 80)
    print("分时段对比：市场隐含增长 vs 实际增长 vs 修正影响")
    print("=" * 80)

    print(f"\n{'期间':<12} {'隐含g':>8} {'实际g':>8} {'低估幅度':>8} {'PE起→末':>12} {'如果正确定价PE':>14}")
    print("-" * 68)

    for i in range(len(years)):
        y = years[i]
        d = SHILLER_ANNUAL[y]
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
        r = bond_yield + 0.02
        div_yield = d["div"] / d["price"]
        implied_g = r - div_yield
        actual_g = (d_future["eps"] / d["eps"]) ** (1/actual_n) - 1
        diff = actual_g - implied_g

        pe_start = d["price"] / d["eps"]
        pe_end = d_future["price"] / d_future["eps"]

        # 如果市场用 actual_g 定价，PE 应该更高
        # Gordon: P = D/(r-g), PE = P/E = (D/E)/(r-g) = payout/(r-g)
        payout_ratio = d["div"] / d["eps"]
        if r - actual_g > 0.005:  # 避免除以接近 0
            fair_pe = payout_ratio / (r - actual_g)
        else:
            fair_pe = float('inf')

        fair_pe_str = f"{fair_pe:.1f}" if fair_pe < 100 else "∞"

        print(f"{y}-{y_future}   {implied_g*100:>6.2f}%  {actual_g*100:>6.2f}%  {diff*100:>6.2f}%  {pe_start:>5.1f}→{pe_end:<5.1f} {fair_pe_str:>12}")

    print(f"""
说明：
- "如果正确定价PE" = 如果市场当时就知道未来10年的真实EPS增长，PE应该是多少
- 当 fair_PE > 实际PE 时，说明市场低估了，买入价太便宜，后续收益偏高
- 当 fair_PE < 实际PE 时，说明市场高估了，买入价太贵，后续收益偏低
""")


if __name__ == "__main__":
    analyze()
