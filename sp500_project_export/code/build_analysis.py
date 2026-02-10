"""
均值回归分析：计算所有滚动年化收益率数据，输出为 JSON 供 HTML 可视化使用
"""
import json
import math
from sp500_data import SP500_TOTAL_RETURNS, CPI_INFLATION

years = sorted(SP500_TOTAL_RETURNS.keys())
n = len(years)

# ========== 1. 计算实际回报率（通胀调整后） ==========
real_returns = {}
for y in years:
    nominal = SP500_TOTAL_RETURNS[y] / 100
    inflation = CPI_INFLATION[y] / 100
    real = (1 + nominal) / (1 + inflation) - 1
    real_returns[y] = real * 100

# ========== 2. 计算累积增长（$100 投资） ==========
cumulative_nominal = []
cumulative_real = []
val_nom = 100
val_real = 100
for y in years:
    val_nom *= (1 + SP500_TOTAL_RETURNS[y] / 100)
    val_real *= (1 + real_returns[y] / 100)
    cumulative_nominal.append({"year": y, "value": round(val_nom, 2)})
    cumulative_real.append({"year": y, "value": round(val_real, 2)})

# ========== 3. 滚动年化收益率（不同窗口） ==========
def calc_rolling_cagr(returns_dict, window):
    """计算滚动N年年化复合收益率"""
    results = []
    for i in range(window, n):
        end_year = years[i]
        start_year = years[i - window]
        # 计算复合增长
        product = 1.0
        for j in range(i - window + 1, i + 1):
            product *= (1 + returns_dict[years[j]] / 100)
        cagr = (product ** (1.0 / window) - 1) * 100
        results.append({"year": end_year, "cagr": round(cagr, 2), "start": start_year})
    return results

windows = [1, 3, 5, 10, 15, 20, 30]
rolling_nominal = {}
rolling_real = {}
for w in windows:
    rolling_nominal[w] = calc_rolling_cagr(SP500_TOTAL_RETURNS, w)
    rolling_real[w] = calc_rolling_cagr(real_returns, w)

# ========== 4. 从任意年份开始持有到2024的CAGR ==========
hold_to_end = []
end_year_idx = n - 1
for i in range(n - 1):
    start_y = years[i]
    holding_period = end_year_idx - i
    product = 1.0
    for j in range(i, n):
        product *= (1 + real_returns[years[j]] / 100)
    cagr = (product ** (1.0 / (n - i)) - 1) * 100
    hold_to_end.append({
        "start_year": start_y,
        "holding_years": n - i,
        "cagr_real": round(cagr, 2)
    })

# ========== 5. 不同持有期的收益率分布（范围） ==========
range_by_window = {}
for w in windows:
    if w == 1:
        vals = [real_returns[y] for y in years]
    else:
        vals = [r["cagr"] for r in rolling_real[w]]
    if vals:
        range_by_window[w] = {
            "min": round(min(vals), 2),
            "max": round(max(vals), 2),
            "mean": round(sum(vals) / len(vals), 2),
            "median": round(sorted(vals)[len(vals)//2], 2),
            "count": len(vals)
        }

# ========== 6. 年度数据表 ==========
yearly_table = []
for y in years:
    yearly_table.append({
        "year": y,
        "nominal": SP500_TOTAL_RETURNS[y],
        "inflation": CPI_INFLATION[y],
        "real": round(real_returns[y], 2)
    })

# ========== 7. 汇总统计 ==========
all_real = [real_returns[y] for y in years]
overall_product = 1.0
for y in years:
    overall_product *= (1 + real_returns[y] / 100)
overall_cagr = (overall_product ** (1.0 / n) - 1) * 100

nominal_product = 1.0
for y in years:
    nominal_product *= (1 + SP500_TOTAL_RETURNS[y] / 100)
nominal_cagr = (nominal_product ** (1.0 / n) - 1) * 100

summary = {
    "period": f"{years[0]}-{years[-1]}",
    "total_years": n,
    "nominal_cagr": round(nominal_cagr, 2),
    "real_cagr": round(overall_cagr, 2),
    "avg_real_annual": round(sum(all_real) / len(all_real), 2),
    "best_year": {"year": max(real_returns, key=real_returns.get), "return": round(max(all_real), 2)},
    "worst_year": {"year": min(real_returns, key=real_returns.get), "return": round(min(all_real), 2)},
    "positive_years": sum(1 for r in all_real if r > 0),
    "negative_years": sum(1 for r in all_real if r <= 0),
}

# ========== 输出 JSON ==========
output = {
    "summary": summary,
    "yearly_table": yearly_table,
    "cumulative_nominal": cumulative_nominal,
    "cumulative_real": cumulative_real,
    "rolling_nominal": {str(k): v for k, v in rolling_nominal.items()},
    "rolling_real": {str(k): v for k, v in rolling_real.items()},
    "hold_to_end": hold_to_end,
    "range_by_window": {str(k): v for k, v in range_by_window.items()},
}

with open("sp500_analysis.json", "w") as f:
    json.dump(output, f)

print("=== 汇总统计 ===")
for k, v in summary.items():
    print(f"  {k}: {v}")
print()
print("=== 不同持有期的实际年化收益率范围 ===")
print(f"{'持有期':>6} | {'最低':>8} | {'最高':>8} | {'均值':>8} | {'中位数':>8}")
print("-" * 50)
for w in windows:
    r = range_by_window[w]
    print(f"{w:>4}年 | {r['min']:>7.2f}% | {r['max']:>7.2f}% | {r['mean']:>7.2f}% | {r['median']:>7.2f}%")
print()
print(f"✅ 数据输出到 sp500_analysis.json")
