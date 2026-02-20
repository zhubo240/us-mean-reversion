"""
重建完整 HTML 报告：加入左侧导航 + 公司级数据 + 三层回报分解
"""
import json
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

# Load existing analysis data
with open(os.path.join(DATA_DIR, "sp500_analysis.json")) as f:
    analysis = json.load(f)

# Load turnover data
with open(os.path.join(DATA_DIR, "turnover_data.json")) as f:
    turnover = json.load(f)

# Load duration distribution
with open(os.path.join(DATA_DIR, "duration_dist.json")) as f:
    duration_dist = json.load(f)

# Load 3-level decomposition data
decomp_path = os.path.join(DATA_DIR, "sp500_3level_decomposition.json")
if os.path.exists(decomp_path):
    with open(decomp_path) as f:
        decomposition = json.load(f)
else:
    decomposition = None

# Load Shiller complete data (1871-2025)
shiller_path = os.path.join(DATA_DIR, "shiller_complete.json")
if os.path.exists(shiller_path):
    with open(shiller_path) as f:
        shiller_data = json.load(f)
else:
    shiller_data = None

data_json = json.dumps(analysis)
turnover_json = json.dumps(turnover)
duration_json = json.dumps(duration_dist)
decomp_json = json.dumps(decomposition) if decomposition else 'null'
shiller_json = json.dumps(shiller_data) if shiller_data else 'null'

html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>标普500均值回归验证 — 1928-2024</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
    background: #0a0e1a;
    color: #e0e6ed;
    line-height: 1.6;
  }}

  /* === SIDEBAR NAV === */
  .sidebar {{
    position: fixed;
    left: 0; top: 0; bottom: 0;
    width: 220px;
    background: rgba(10, 14, 26, 0.97);
    border-right: 1px solid rgba(255,255,255,0.08);
    padding: 20px 0;
    overflow-y: auto;
    z-index: 100;
    backdrop-filter: blur(12px);
  }}
  .sidebar::-webkit-scrollbar {{ width: 4px; }}
  .sidebar::-webkit-scrollbar-thumb {{ background: rgba(255,255,255,0.1); border-radius: 2px; }}
  .sidebar .logo {{
    padding: 0 16px 16px;
    border-bottom: 1px solid rgba(255,255,255,0.06);
    margin-bottom: 12px;
  }}
  .sidebar .logo h3 {{
    font-size: 0.85rem;
    background: linear-gradient(135deg, #60a5fa, #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }}
  .sidebar .logo span {{ font-size: 0.7rem; color: #4a5568; }}
  .nav-group {{ padding: 0 8px; margin-bottom: 8px; }}
  .nav-group-title {{
    font-size: 0.65rem;
    color: #4a5568;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    padding: 8px 8px 4px;
    font-weight: 600;
  }}
  .nav-link {{
    display: block;
    padding: 7px 12px;
    color: #6b7a8d;
    text-decoration: none;
    font-size: 0.8rem;
    border-radius: 6px;
    transition: all 0.2s;
    line-height: 1.4;
  }}
  .nav-link:hover {{ background: rgba(96,165,250,0.1); color: #a5b4c6; }}
  .nav-link.active {{ background: rgba(96,165,250,0.15); color: #60a5fa; font-weight: 500; }}
  .nav-icon {{ margin-right: 6px; font-size: 0.85rem; }}

  /* === MAIN CONTENT === */
  .main {{ margin-left: 220px; padding: 20px; max-width: 1100px; }}

  .header {{
    text-align: center;
    padding: 30px 0 16px;
    border-bottom: 1px solid rgba(255,255,255,0.08);
    margin-bottom: 24px;
  }}
  .header h1 {{
    font-size: 1.8rem;
    background: linear-gradient(135deg, #60a5fa, #a78bfa, #f472b6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 6px;
  }}
  .header .subtitle {{ color: #6b7a8d; font-size: 0.9rem; }}

  .summary-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 12px;
    margin-bottom: 24px;
  }}
  .card {{
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 10px;
    padding: 16px;
    text-align: center;
  }}
  .card .label {{ font-size: 0.7rem; color: #6b7a8d; text-transform: uppercase; letter-spacing: 1px; }}
  .card .value {{ font-size: 1.6rem; font-weight: 700; margin-top: 4px; }}
  .card .value.green {{ color: #34d399; }}
  .card .value.blue {{ color: #60a5fa; }}
  .card .value.orange {{ color: #fbbf24; }}
  .card .value.pink {{ color: #f472b6; }}

  .section {{
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 14px;
    padding: 20px;
    margin-bottom: 20px;
    scroll-margin-top: 20px;
  }}
  .section h2 {{ font-size: 1.1rem; color: #a5b4c6; margin-bottom: 4px; }}
  .section .desc {{ font-size: 0.82rem; color: #4a5568; margin-bottom: 14px; }}
  .chart-container {{ position: relative; width: 100%; height: 380px; }}
  .chart-container.tall {{ height: 440px; }}

  .insight {{
    background: rgba(96, 165, 250, 0.06);
    border-left: 3px solid #60a5fa;
    padding: 12px 16px;
    border-radius: 0 6px 6px 0;
    margin-top: 12px;
    font-size: 0.85rem;
    color: #8896a8;
  }}
  .insight strong {{ color: #60a5fa; }}

  .tabs {{ display: flex; gap: 6px; margin-bottom: 12px; flex-wrap: wrap; }}
  .tab-btn {{
    padding: 5px 14px;
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 18px;
    background: transparent;
    color: #6b7a8d;
    cursor: pointer;
    font-size: 0.8rem;
    transition: all 0.2s;
  }}
  .tab-btn:hover {{ border-color: #60a5fa; color: #60a5fa; }}
  .tab-btn.active {{ background: #60a5fa; color: white; border-color: #60a5fa; }}

  /* Funnel */
  .funnel-grid {{
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 6px;
    align-items: end;
    height: 280px;
    padding: 16px 0;
  }}
  .funnel-bar {{
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: flex-end;
    height: 100%;
  }}
  .funnel-range {{
    width: 100%;
    border-radius: 6px;
    position: relative;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 30px;
    transition: all 0.3s;
  }}
  .funnel-range:hover {{ transform: scaleX(1.05); }}
  .funnel-range .val {{ font-size: 0.65rem; font-weight: 600; color: white; }}
  .funnel-range .mean-dot {{
    width: 8px; height: 8px;
    background: #fbbf24;
    border-radius: 50%;
    border: 2px solid white;
    position: absolute;
  }}
  .funnel-label {{
    text-align: center;
    margin-top: 6px;
    font-size: 0.7rem;
    color: #6b7a8d;
  }}
  .funnel-label strong {{ display: block; color: #e0e6ed; font-size: 0.8rem; }}

  /* Table */
  .data-table-wrapper {{
    max-height: 400px;
    overflow-y: auto;
    border-radius: 6px;
  }}
  .data-table-wrapper::-webkit-scrollbar {{ width: 5px; }}
  .data-table-wrapper::-webkit-scrollbar-thumb {{ background: rgba(255,255,255,0.12); border-radius: 3px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.82rem; }}
  th {{
    background: rgba(255,255,255,0.06);
    padding: 8px 10px;
    text-align: right;
    color: #6b7a8d;
    position: sticky;
    top: 0;
    z-index: 1;
    font-weight: 600;
  }}
  th:first-child {{ text-align: left; }}
  td {{
    padding: 6px 10px;
    text-align: right;
    border-bottom: 1px solid rgba(255,255,255,0.03);
  }}
  td:first-child {{ text-align: left; color: #a5b4c6; }}
  tr:hover td {{ background: rgba(255,255,255,0.03); }}
  .pos {{ color: #34d399; }}
  .neg {{ color: #f87171; }}

  .footer {{
    text-align: center;
    padding: 24px 0;
    color: #3a4352;
    font-size: 0.75rem;
  }}

  /* Responsive */
  @media (max-width: 900px) {{
    .sidebar {{ display: none; }}
    .main {{ margin-left: 0; }}
    .funnel-grid {{ grid-template-columns: repeat(4, 1fr); }}
  }}
</style>
</head>
<body>

<!-- ====== SIDEBAR NAVIGATION ====== -->
<nav class="sidebar">
  <div class="logo">
    <h3>S&P 500 均值回归</h3>
    <span>1928-2024 · 97年数据</span>
  </div>

  <div class="nav-group">
    <div class="nav-group-title">Part I · 指数层面</div>
    <a class="nav-link" href="#summary"><span class="nav-icon">📊</span>核心数据</a>
    <a class="nav-link" href="#s1"><span class="nav-icon">📈</span>每年实际回报率</a>
    <a class="nav-link" href="#s2"><span class="nav-icon">🔻</span>均值回归漏斗</a>
    <a class="nav-link" href="#s3"><span class="nav-icon">〰️</span>滚动年化收益率</a>
    <a class="nav-link" href="#s4"><span class="nav-icon">🎯</span>任意入场 → 2024</a>
    <a class="nav-link" href="#s5"><span class="nav-icon">💰</span>$100 累积增长</a>
  </div>

  <div class="nav-group">
    <div class="nav-group-title">Part II · 行业层面</div>
    <a class="nav-link" href="#s6"><span class="nav-icon">🔄</span>行业权重演变</a>
    <a class="nav-link" href="#s8"><span class="nav-icon">🏆</span>Top 10 变迁</a>
  </div>

  <div class="nav-group">
    <div class="nav-group-title">Part III · 公司层面</div>
    <a class="nav-link" href="#s7"><span class="nav-icon">🕰️</span>创造性破坏时间线</a>
    <a class="nav-link" href="#s9"><span class="nav-icon">📉</span>年度换手率</a>
    <a class="nav-link" href="#s10"><span class="nav-icon">⏱️</span>公司存活时间分布</a>
    <a class="nav-link" href="#s11"><span class="nav-icon">🧬</span>1194家公司全景</a>
  </div>

  <div class="nav-group">
    <div class="nav-group-title">Part IV · 回报分解</div>
    <a class="nav-link" href="#decomp1"><span class="nav-icon">📊</span>年度回报分解</a>
    <a class="nav-link" href="#decomp2"><span class="nav-icon">📉</span>均值回归收敛</a>
    <a class="nav-link" href="#shiller20"><span class="nav-icon">📈</span>153年滚动分解</a>
    <a class="nav-link" href="#shillerLog"><span class="nav-icon">📐</span>对数累积增长</a>
    <a class="nav-link" href="#sectorDecomp"><span class="nav-icon">🔀</span>行业回报分解</a>
    <a class="nav-link" href="#decomp3"><span class="nav-icon">🏭</span>行业贡献分解</a>
    <a class="nav-link" href="#decomp4"><span class="nav-icon">✅</span>三层加总验证</a>
  </div>

  <div class="nav-group">
    <div class="nav-group-title">Part V · 结论</div>
    <a class="nav-link" href="#mechanism"><span class="nav-icon">⚙️</span>核心机制解析</a>
    <a class="nav-link" href="#data"><span class="nav-icon">📋</span>完整年度数据</a>
  </div>
</nav>

<!-- ====== MAIN CONTENT ====== -->
<div class="main">

  <div class="header">
    <h1>标普500 均值回归验证</h1>
    <div class="subtitle">S&P 500 Mean Reversion · 1928-2024 · 97年数据 · 1194家公司 · 从指数到个股的全景分析</div>
  </div>

  <!-- Summary Cards -->
  <div class="summary-grid" id="summary">
    <div class="card">
      <div class="label">实际年化复合回报</div>
      <div class="value green">6.70%</div>
    </div>
    <div class="card">
      <div class="label">名义年化复合回报</div>
      <div class="value blue">9.94%</div>
    </div>
    <div class="card">
      <div class="label">历史成分股总数</div>
      <div class="value orange">1,194</div>
    </div>
    <div class="card">
      <div class="label">1996年原始股存活率</div>
      <div class="value pink">29%</div>
      <div class="label" style="margin-top:2px">142/487</div>
    </div>
    <div class="card">
      <div class="label">年均换手率</div>
      <div class="value blue">4.4%</div>
      <div class="label" style="margin-top:2px">~22家/年</div>
    </div>
  </div>

  <!-- ========== PART I: INDEX LEVEL ========== -->

  <div class="section" id="s1">
    <h2>图一：每年的实际回报率（通胀调整后）</h2>
    <div class="desc">红绿交替，感受市场的剧烈波动——这是均值回归的"原始素材"</div>
    <div class="chart-container tall"><canvas id="annualChart"></canvas></div>
    <div class="insight">
      <strong>关键观察：</strong>单看任何一年，回报率从 -38% 到 +54% 剧烈波动。97年中 66年盈利、31年亏损（68%正回报）。
    </div>
  </div>

  <div class="section" id="s2">
    <h2>图二：均值回归的"漏斗" — 持有期越长，波动越小</h2>
    <div class="desc">最直观的证据：随着持有时间拉长，年化收益率的波动范围急剧收窄</div>
    <div id="funnelContainer"></div>
    <div class="insight">
      <strong>核心发现：</strong>持有1年波动 91.8pp（-38% ~ +54%），持有30年收窄到仅 5.8pp（+4.3% ~ +10.1%）。时间是最强大的"稳定器"。
    </div>
  </div>

  <div class="section" id="s3">
    <h2>图三：滚动年化收益率 — 切换窗口看收敛</h2>
    <div class="desc">选择不同持有期窗口，观察曲线如何从"剧烈跳动"变为"贴着均值走"</div>
    <div class="tabs" id="rollingTabs"></div>
    <div class="chart-container tall"><canvas id="rollingChart"></canvas></div>
  </div>

  <div class="section" id="s4">
    <h2>图四：从任意年份入场持有到2024</h2>
    <div class="desc">无论在大崩盘前还是泡沫顶点入场，持有够久都会回归</div>
    <div class="chart-container tall"><canvas id="holdChart"></canvas></div>
    <div class="insight">
      <strong>启示：</strong>1929大崩盘前、2000互联网泡沫顶点、2008金融危机前入场——只要持有够久，年化回报最终都回归 6-8% 区间。
    </div>
  </div>

  <div class="section" id="s5">
    <h2>图五：$100 的累积增长轨迹</h2>
    <div class="desc">名义增长 vs 实际购买力（对数刻度）</div>
    <div class="chart-container tall"><canvas id="cumulativeChart"></canvas></div>
  </div>

  <!-- ========== PART II: SECTOR LEVEL ========== -->

  <div class="section" id="s6">
    <h2>图六：行业权重历史演变 — 指数的"新陈代谢"</h2>
    <div class="desc">能源从26%跌到3.5%，科技从8%涨到30%——行业轮替是均值回归的引擎</div>
    <div class="chart-container tall"><canvas id="sectorChart"></canvas></div>
    <div class="insight">
      <strong>行业轮替：</strong>1980年代能源主导，2000年科技泡沫，2008金融危机，2020年代AI革命——每个时代的"主角"都不同，但指数回报稳定。
    </div>
  </div>

  <div class="section" id="s8">
    <h2>图七：Top 10 权重股变迁 — 2000 vs 2024</h2>
    <div class="desc">2000年Top 10中仅Microsoft存活至今的Top 10</div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:10px">
      <div>
        <div style="text-align:center;font-weight:600;color:#f87171;margin-bottom:8px;font-size:0.9rem">2000年 Top 10（互联网泡沫顶峰）</div>
        <div id="top10_2000"></div>
      </div>
      <div>
        <div style="text-align:center;font-weight:600;color:#34d399;margin-bottom:8px;font-size:0.9rem">2024年 Top 10（AI时代）</div>
        <div id="top10_2024"></div>
      </div>
    </div>
    <div class="insight">
      <strong>惊人变化：</strong>GE从第一大权重股拆分为三；Cisco、Intel大幅缩水；AIG几乎破产。而Nvidia从无名小卒变成第一大权重股（7.2%）。
    </div>
  </div>

  <!-- ========== PART III: COMPANY LEVEL ========== -->

  <div class="section" id="s7">
    <h2>图八：创造性破坏时间线 — 公司级别的换血</h2>
    <div class="desc">从1957年至今，1194家不同的公司先后进出标普500</div>
    <div id="turnoverTimeline"></div>
  </div>

  <div class="section" id="s9">
    <h2>图九：年度成分股换手率（1996-2026）</h2>
    <div class="desc">基于GitHub开源数据（fja05680/sp500），每年有多少公司被替换</div>
    <div class="chart-container tall"><canvas id="turnoverChart"></canvas></div>
    <div class="insight">
      <strong>数据来源：</strong>GitHub上1996-2026年逐日成分股快照，共1194家不同公司先后出现。
      2000年换手最猛（10.8%），互联网泡沫破灭导致大批公司进出。
    </div>
  </div>

  <div class="section" id="s10">
    <h2>图十：公司在标普500中的存活时间分布</h2>
    <div class="desc">大多数公司在指数中的寿命远短于你想象</div>
    <div class="chart-container"><canvas id="durationChart"></canvas></div>
    <div class="insight">
      <strong>残酷的现实：</strong>平均存活11.6年，中位数仅8.8年。30%的公司不到5年就被移除。只有142家（29%）从1996年坚持到现在。
    </div>
  </div>

  <div class="section" id="s11">
    <h2>图十一：当前503家成分股的行业分布</h2>
    <div class="desc">工业(80) > 金融(76) > 科技(70) > 医疗(60) —— 行业数量 ≠ 权重</div>
    <div class="chart-container"><canvas id="sectorPieChart"></canvas></div>
    <div class="insight">
      <strong>注意：</strong>科技虽然只有70家公司（第3多），但因为每家公司市值巨大，在权重上（30%）远超80家工业股。这就是市值加权的力量。
    </div>
  </div>

  <!-- ========== PART IV: RETURN DECOMPOSITION (3-Level) ========== -->

  <div class="section" id="decomp1">
    <h2>年度回报分解：盈利增长 + PE 扩张 + 股息</h2>
    <div class="desc">S&P 500 每年总回报的三因子分解 (1985-2024, Compustat 公司级别数据)</div>
    <div class="chart-container tall"><canvas id="chartDecomp1"></canvas></div>
    <div style="margin-top:12px;font-size:0.82rem;color:#6b7a8d;line-height:1.7">
      <b>公式：</b>总回报 = 盈利增长 + PE 扩张 + 股息率 &nbsp;|&nbsp;
      数据来源：Compustat 公司年报聚合，覆盖 ~500 家 S&P 500 成分股<br>
      <b>注：</b>盈利恢复年份（如2003/2009）因前期盈利趋近零，分解值极端，图表截断于±100%，悬停可见实际值
    </div>
  </div>

  <div class="section" id="decomp2">
    <h2>均值回归：持有时间越长，回报越收敛</h2>
    <div class="desc">5/10/20 年滚动窗口的回报标准差对比</div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
      <div class="chart-container"><canvas id="chartDecomp2a"></canvas></div>
      <div class="chart-container"><canvas id="chartDecomp2b"></canvas></div>
    </div>
    <div id="mrSummary" style="margin-top:14px;display:grid;grid-template-columns:repeat(3,1fr);gap:12px"></div>
    <div style="margin-top:24px">
      <h3 style="color:#e0e6ed;font-size:1.05rem;margin-bottom:6px">回报来源分解：持有越久，PE 扩张越趋近零</h3>
      <div class="desc">不同持有期的平均年化回报拆分 — 盈利增长 + PE 扩张 + 股息</div>
      <div class="chart-container"><canvas id="chartDecomp2c"></canvas></div>
      <div style="margin-top:8px;font-size:0.82rem;color:#6b7a8d;line-height:1.7">
        <b>核心结论：</b>20年窗口 PE 扩张趋近零 → 长期回报 ≈ 盈利增长 + 股息。短期"赚估值的钱"不可持续，长期只有"赚盈利的钱"。
      </div>
    </div>
  </div>

  <div class="section" id="shiller20">
    <h2>153年均值回归：20年滚动回报分解 (Shiller 1871-2025)</h2>
    <div class="desc">每个数据点 = 过去20年的年化回报率及其三因子分解 &nbsp;|&nbsp; 总回报 = 盈利增长 + PE 扩张 + 股息率</div>
    <div class="chart-container" style="height:420px"><canvas id="chartShiller20"></canvas></div>
    <div style="margin-top:10px;font-size:0.82rem;color:#6b7a8d;line-height:1.7">
      <b>数据来源：</b>Robert Shiller / multpl.com，1871-2025年1月值。EPS = Price / PE（衍生值）。<br>
      <b>核心结论：</b>任何20年窗口，PE 扩张（紫色）围绕零线波动且贡献极小；回报长期由盈利增长（蓝色）+ 股息（绿色）驱动。<br>
      <b>153年全期 CAGR：</b>9.0% = 盈利增长 4.2% + PE 扩张 0.6% + 股息 4.3%
    </div>
  </div>

  <div class="section" id="shillerLog">
    <h2>153年累积增长：对数坐标 + 线性拟合 (Shiller 1871-2025)</h2>
    <div class="desc">对数坐标下，直线 = 恒定年化增速 &nbsp;|&nbsp; 斜率 = CAGR &nbsp;|&nbsp; PE 围绕均值震荡，不贡献长期增长</div>
    <div class="chart-container" style="height:460px"><canvas id="chartShillerLog"></canvas></div>
    <div id="shillerLogStats" style="margin-top:12px;display:grid;grid-template-columns:repeat(4,1fr);gap:12px"></div>
    <div style="margin-top:8px;font-size:0.82rem;color:#6b7a8d;line-height:1.7">
      <b>解读：</b>对数坐标下恒定增长率呈直线。Price = EPS × PE，即 log(Price) = log(EPS) + log(PE)。<br>
      PE 在对数尺度上近似水平（无长期趋势），说明价格的长期增长完全来自盈利增长。<br>
      总回报 = 价格增长 + 股息再投资，两条线之间的差距即为股息的累积贡献。
    </div>
  </div>

  <div class="section" id="sectorDecomp">
    <h2>行业累积增长：对数坐标 + 线性拟合 (1985-2024)</h2>
    <div class="desc">对数坐标下，直线 = 恒定年化增速 &nbsp;|&nbsp; 按行业查看累积增长轨迹及 CAGR</div>
    <div style="margin-bottom:10px">
      <select id="sectorDecompSelect" style="background:#1a1f2e;color:#e0e6ed;border:1px solid rgba(255,255,255,0.1);padding:6px 12px;border-radius:6px;font-size:0.85rem;min-width:180px">
      </select>
    </div>
    <div class="chart-container" style="height:460px"><canvas id="chartSectorDecomp"></canvas></div>
    <div id="sectorDecompStats" style="margin-top:12px;display:grid;grid-template-columns:repeat(4,1fr);gap:12px"></div>
    <div style="margin-top:8px;font-size:0.82rem;color:#6b7a8d;line-height:1.7">
      <b>解读：</b>对数坐标下恒定增长率呈直线。Price = EPS × PE，即 log(Price) = log(EPS) + log(PE)。<br>
      总回报 = 价格增长 + 股息再投资。盈利为负的年份（如金融2008）盈利线中断。<br>
      <b>数据来源：</b>Compustat 公司级别数据按 GICS 行业聚合 (1985-2024)
    </div>
  </div>

  <div class="section" id="decomp3">
    <h2>行业贡献分解</h2>
    <div class="desc">各 GICS 行业对 S&P 500 总回报的贡献 (按市值加权)</div>
    <div style="margin-bottom:10px">
      <select id="decompYearSelect" style="background:#1a1f2e;color:#e0e6ed;border:1px solid rgba(255,255,255,0.1);padding:6px 12px;border-radius:6px;font-size:0.85rem">
      </select>
    </div>
    <div class="chart-container tall"><canvas id="chartDecomp3"></canvas></div>
  </div>

  <div class="section" id="decomp4">
    <h2>三层加总验证：公司 = 行业 = 总量</h2>
    <div class="desc">验证分析数据的内部一致性：个体公司之和 = GICS 行业之和 = S&P 500 总量</div>
    <div class="data-table-wrapper">
      <table id="verifyTable">
        <thead><tr>
          <th>年份</th><th>总量盈利($B)</th><th>公司盈利($B)</th><th>差值</th>
          <th>总量市值($B)</th><th>公司市值($B)</th><th>差值</th><th>回报差(bp)</th>
        </tr></thead>
        <tbody></tbody>
      </table>
    </div>
    <div id="verifyResult" style="margin-top:10px;font-size:0.85rem"></div>
  </div>

  <!-- ========== PART V: CONCLUSIONS ========== -->

  <div class="section" id="mechanism">
    <h2>核心机制：为什么个股兴衰，指数却稳定在 ~6.8%？</h2>
    <div class="desc">三个层面的"均值回归"力量</div>
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px;margin-top:10px">
      <div class="card" style="text-align:left">
        <div class="label" style="color:#60a5fa;font-size:0.85rem;font-weight:600">① 指数委员会的"换血"机制</div>
        <div style="margin-top:8px;font-size:0.83rem;color:#8896a8;line-height:1.7">
          移除衰落公司，纳入新兴龙头。1194家公司先后进出，年均换手22家。1957年的500家只剩约53家（10.6%）。
        </div>
      </div>
      <div class="card" style="text-align:left">
        <div class="label" style="color:#34d399;font-size:0.85rem;font-weight:600">② 市值加权的"自动调节"</div>
        <div style="margin-top:8px;font-size:0.83rem;color:#8896a8;line-height:1.7">
          成功的公司权重自动增大（Nvidia: 0% → 7.2%），失败的自动缩小。内置的"赢家加码"机制。
        </div>
      </div>
      <div class="card" style="text-align:left">
        <div class="label" style="color:#fbbf24;font-size:0.85rem;font-weight:600">③ 经济增长的底层驱动</div>
        <div style="margin-top:8px;font-size:0.83rem;color:#8896a8;line-height:1.7">
          美国实际GDP长期增长~3%，加上企业利润率和股东回报，构成6-7%实际回报的经济学基础。横跨大萧条→二战→冷战→石油危机→互联网泡沫→金融危机→疫情。
        </div>
      </div>
    </div>
  </div>

  <div class="section" id="data">
    <h2>完整年度数据表</h2>
    <div class="desc">97年逐年数据——名义回报、通胀率、实际回报</div>
    <div class="data-table-wrapper">
      <table id="dataTable">
        <thead><tr><th>年份</th><th>名义回报 %</th><th>通胀率 %</th><th>实际回报 %</th></tr></thead>
        <tbody></tbody>
      </table>
    </div>
  </div>

  <div class="footer">
    数据来源：S&P 500 Total Returns (含分红再投资) · CPI (BLS) · 1928-2024<br>
    公司数据：<a href="https://github.com/fja05680/sp500" style="color:#4a5568">github.com/fja05680/sp500</a> · 1996-2026 历史成分股<br>
    注：S&P 500指数始于1957，此前基于S&P 90及Cowles Commission数据
  </div>
</div>

<script>
// ============================================================
// DATA
// ============================================================
const DATA = {data_json};
const TURNOVER = {turnover_json};
const DURATION = {duration_json};
const DECOMP = {decomp_json};
const SHILLER = {shiller_json};

Chart.defaults.color = '#6b7a8d';
Chart.defaults.borderColor = 'rgba(255,255,255,0.05)';
Chart.defaults.font.family = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', sans-serif";

// ============================================================
// SIDEBAR: Active link tracking
// ============================================================
(function() {{
  const links = document.querySelectorAll('.nav-link');
  const sections = [];
  links.forEach(link => {{
    const id = link.getAttribute('href').slice(1);
    const el = document.getElementById(id);
    if (el) sections.push({{ link, el }});
  }});

  function updateActive() {{
    let current = sections[0];
    for (const s of sections) {{
      if (s.el.getBoundingClientRect().top <= 100) current = s;
    }}
    links.forEach(l => l.classList.remove('active'));
    if (current) current.link.classList.add('active');
  }}
  window.addEventListener('scroll', updateActive);
  updateActive();
}})();

// ============================================================
// CHART 1: Annual Returns
// ============================================================
(function() {{
  const ctx = document.getElementById('annualChart').getContext('2d');
  const years = DATA.yearly_table.map(d => d.year);
  const returns = DATA.yearly_table.map(d => d.real);
  new Chart(ctx, {{
    type: 'bar',
    data: {{
      labels: years,
      datasets: [{{ data: returns, backgroundColor: returns.map(r => r >= 0 ? 'rgba(52,211,153,0.7)' : 'rgba(248,113,113,0.7)'), borderWidth: 0, borderRadius: 2 }}]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      plugins: {{
        legend: {{ display: false }},
        tooltip: {{ callbacks: {{
          title: items => items[0].label + '年',
          label: item => {{
            const d = DATA.yearly_table[item.dataIndex];
            return [`实际: ${{d.real > 0 ? '+' : ''}}${{d.real}}%`, `名义: ${{d.nominal > 0 ? '+' : ''}}${{d.nominal}}%`, `通胀: ${{d.inflation}}%`];
          }}
        }} }}
      }},
      scales: {{
        x: {{ ticks: {{ maxRotation: 0, autoSkip: true, maxTicksLimit: 20, font: {{ size: 10 }} }}, grid: {{ display: false }} }},
        y: {{ ticks: {{ callback: v => v + '%' }}, grid: {{ color: 'rgba(255,255,255,0.04)' }} }}
      }}
    }}
  }});
}})();

// ============================================================
// CHART 2: Funnel
// ============================================================
(function() {{
  const container = document.getElementById('funnelContainer');
  const windows = [1, 3, 5, 10, 15, 20, 30];
  const rangeData = DATA.range_by_window;
  const gradients = [
    'linear-gradient(180deg, rgba(248,113,113,0.6), rgba(52,211,153,0.6))',
    'linear-gradient(180deg, rgba(248,113,113,0.5), rgba(52,211,153,0.5))',
    'linear-gradient(180deg, rgba(248,113,113,0.4), rgba(52,211,153,0.4))',
    'linear-gradient(180deg, rgba(167,139,250,0.4), rgba(96,165,250,0.4))',
    'linear-gradient(180deg, rgba(167,139,250,0.35), rgba(96,165,250,0.35))',
    'linear-gradient(180deg, rgba(96,165,250,0.35), rgba(52,211,153,0.35))',
    'linear-gradient(180deg, rgba(52,211,153,0.4), rgba(52,211,153,0.3))'
  ];
  let html = '<div class="funnel-grid">';
  windows.forEach((w, i) => {{
    const d = rangeData[w];
    const totalRange = d.max - d.min;
    const heightPct = (totalRange / 100) * 100;
    const meanPos = ((d.mean - d.min) / totalRange) * 100;
    html += `<div class="funnel-bar"><div class="funnel-range" style="height:${{Math.max(heightPct, 12)}}%;background:${{gradients[i]}};border:1px solid rgba(255,255,255,0.1)"><div class="val" style="position:absolute;top:2px">+${{d.max}}%</div><div class="mean-dot" style="bottom:${{meanPos}}%;left:50%;transform:translate(-50%,50%)" title="均值:${{d.mean}}%"></div><div class="val" style="position:absolute;bottom:2px">${{d.min}}%</div></div><div class="funnel-label"><strong>${{w}}年</strong>${{totalRange.toFixed(1)}}pp</div></div>`;
  }});
  html += '</div><div style="text-align:center;margin-top:6px;font-size:0.75rem;color:#4a5568">黄色圆点 = 均值 · 柱高 = 波动范围</div>';
  container.innerHTML = html;
}})();

// ============================================================
// CHART 3: Rolling CAGR
// ============================================================
let rollingChart = null;
let activeWindow = 10;
const rollingWindows = [1, 3, 5, 10, 15, 20, 30];

(function() {{
  const container = document.getElementById('rollingTabs');
  rollingWindows.forEach(w => {{
    const btn = document.createElement('button');
    btn.className = 'tab-btn' + (w === activeWindow ? ' active' : '');
    btn.textContent = w + '年';
    btn.onclick = () => {{
      activeWindow = w;
      document.querySelectorAll('#rollingTabs .tab-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      updateRollingChart();
    }};
    container.appendChild(btn);
  }});
  updateRollingChart();
}})();

function updateRollingChart() {{
  const ctx = document.getElementById('rollingChart').getContext('2d');
  const d = DATA.rolling_real[activeWindow];
  if (rollingChart) rollingChart.destroy();
  rollingChart = new Chart(ctx, {{
    type: 'line',
    data: {{
      labels: d.map(x => x.year),
      datasets: [
        {{ label: `${{activeWindow}}年滚动实际年化`, data: d.map(x => x.cagr), borderColor: '#60a5fa', backgroundColor: 'rgba(96,165,250,0.08)', fill: true, tension: 0.3, pointRadius: 0, borderWidth: 2 }},
        {{ label: '均值 6.70%', data: d.map(() => 6.70), borderColor: '#fbbf24', borderWidth: 2, borderDash: [8, 4], pointRadius: 0, fill: false }},
        {{ label: '零线', data: d.map(() => 0), borderColor: 'rgba(248,113,113,0.3)', borderWidth: 1, borderDash: [4, 4], pointRadius: 0, fill: false }}
      ]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      interaction: {{ intersect: false, mode: 'index' }},
      plugins: {{
        legend: {{ position: 'top', labels: {{ usePointStyle: true, padding: 12 }} }},
        tooltip: {{ callbacks: {{
          title: items => items[0].label + '年',
          label: item => item.datasetIndex === 0 ? `${{activeWindow}}年年化: ${{d[item.dataIndex].cagr > 0 ? '+' : ''}}${{d[item.dataIndex].cagr}}%（${{d[item.dataIndex].start}}-${{d[item.dataIndex].year}}）` : item.dataset.label
        }} }}
      }},
      scales: {{
        x: {{ ticks: {{ maxRotation: 0, autoSkip: true, maxTicksLimit: 20, font: {{ size: 10 }} }}, grid: {{ display: false }} }},
        y: {{ ticks: {{ callback: v => v + '%' }}, grid: {{ color: 'rgba(255,255,255,0.04)' }} }}
      }}
    }}
  }});
}}

// ============================================================
// CHART 4: Hold to 2024
// ============================================================
(function() {{
  const ctx = document.getElementById('holdChart').getContext('2d');
  const d = DATA.hold_to_end;
  new Chart(ctx, {{
    type: 'line',
    data: {{
      labels: d.map(x => x.start_year),
      datasets: [
        {{ label: '实际年化回报', data: d.map(x => x.cagr_real), borderColor: '#a78bfa', backgroundColor: 'rgba(167,139,250,0.08)', fill: true, tension: 0.3, pointRadius: 1.5, borderWidth: 2 }},
        {{ label: '均值 6.70%', data: d.map(() => 6.70), borderColor: '#fbbf24', borderWidth: 2, borderDash: [8, 4], pointRadius: 0, fill: false }}
      ]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      interaction: {{ intersect: false, mode: 'index' }},
      plugins: {{
        legend: {{ position: 'top', labels: {{ usePointStyle: true, padding: 12 }} }},
        tooltip: {{ callbacks: {{
          title: items => `从 ${{items[0].label}}年 入场`,
          label: item => item.datasetIndex === 0 ? `持有${{d[item.dataIndex].holding_years}}年 → ${{d[item.dataIndex].cagr_real > 0 ? '+' : ''}}${{d[item.dataIndex].cagr_real}}%` : item.dataset.label
        }} }}
      }},
      scales: {{
        x: {{ title: {{ display: true, text: '入场年份', color: '#4a5568' }}, ticks: {{ maxRotation: 0, autoSkip: true, maxTicksLimit: 20, font: {{ size: 10 }} }}, grid: {{ display: false }} }},
        y: {{ title: {{ display: true, text: '年化实际回报 %', color: '#4a5568' }}, ticks: {{ callback: v => v + '%' }}, grid: {{ color: 'rgba(255,255,255,0.04)' }} }}
      }}
    }}
  }});
}})();

// ============================================================
// CHART 5: Cumulative (Log)
// ============================================================
(function() {{
  const ctx = document.getElementById('cumulativeChart').getContext('2d');
  new Chart(ctx, {{
    type: 'line',
    data: {{
      labels: DATA.cumulative_nominal.map(d => d.year),
      datasets: [
        {{ label: '名义增长', data: DATA.cumulative_nominal.map(d => d.value), borderColor: '#60a5fa', backgroundColor: 'rgba(96,165,250,0.04)', fill: true, tension: 0.3, pointRadius: 0, borderWidth: 2 }},
        {{ label: '实际购买力', data: DATA.cumulative_real.map(d => d.value), borderColor: '#34d399', backgroundColor: 'rgba(52,211,153,0.04)', fill: true, tension: 0.3, pointRadius: 0, borderWidth: 2 }}
      ]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      interaction: {{ intersect: false, mode: 'index' }},
      plugins: {{
        legend: {{ position: 'top', labels: {{ usePointStyle: true, padding: 12 }} }},
        tooltip: {{ callbacks: {{ label: item => '$' + item.raw.toLocaleString() + (item.datasetIndex === 0 ? ' (名义)' : ' (实际)') }} }}
      }},
      scales: {{
        x: {{ ticks: {{ maxRotation: 0, autoSkip: true, maxTicksLimit: 20, font: {{ size: 10 }} }}, grid: {{ display: false }} }},
        y: {{ type: 'logarithmic', ticks: {{ callback: v => [100,500,1000,5000,10000,50000,100000,500000,1000000].includes(v) ? '$'+v.toLocaleString() : '' }}, grid: {{ color: 'rgba(255,255,255,0.04)' }} }}
      }}
    }}
  }});
}})();

// ============================================================
// CHART 6: Sector Evolution
// ============================================================
(function() {{
  const ctx = document.getElementById('sectorChart').getContext('2d');
  const years = [1960,1965,1970,1975,1980,1985,1990,1995,2000,2005,2008,2010,2015,2020,2024];
  const sectors = {{
    'Technology': {{ data: [5,5,6,6,8,10,8,12,33,15,16,19,21,28,30], color: 'rgba(96,165,250,0.8)', border: '#60a5fa' }},
    'Energy': {{ data: [18,17,16,20,26,18,13,9,6,10,14,11,7,2.4,3.5], color: 'rgba(248,113,113,0.8)', border: '#f87171' }},
    'Financials': {{ data: [5,5,6,8,10,12,8,13,17,22,10,16,17,11,13], color: 'rgba(52,211,153,0.8)', border: '#34d399' }},
    'Healthcare': {{ data: [3,4,5,6,7,8,10,11,10,13,14,11,15,14,12], color: 'rgba(167,139,250,0.8)', border: '#a78bfa' }},
    'Industrials': {{ data: [20,18,17,15,14,12,14,12,9,11,12,11,10,8,9], color: 'rgba(251,191,36,0.8)', border: '#fbbf24' }},
    'Consumer': {{ data: [20,22,22,20,15,17,20,18,12,12,14,14,12,14,12], color: 'rgba(244,114,182,0.8)', border: '#f472b6' }},
  }};
  new Chart(ctx, {{
    type: 'line',
    data: {{ labels: years, datasets: Object.entries(sectors).map(([name, s]) => ({{ label: name, data: s.data, backgroundColor: s.color.replace('0.8','0.1'), borderColor: s.border, borderWidth: 2, fill: false, tension: 0.4, pointRadius: 3, pointHoverRadius: 6 }})) }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      interaction: {{ intersect: false, mode: 'index' }},
      plugins: {{ legend: {{ position: 'top', labels: {{ usePointStyle: true, padding: 10, font: {{ size: 11 }} }} }}, tooltip: {{ callbacks: {{ label: item => `${{item.dataset.label}}: ${{item.raw}}%` }} }} }},
      scales: {{
        x: {{ grid: {{ display: false }} }},
        y: {{ ticks: {{ callback: v => v + '%' }}, grid: {{ color: 'rgba(255,255,255,0.04)' }}, max: 38 }}
      }}
    }}
  }});
}})();

// ============================================================
// Top 10 Comparison
// ============================================================
(function() {{
  const top2000 = [
    {{ name: 'General Electric', weight: 4.0, fate: '2024年拆分为3家', fateColor: '#fbbf24' }},
    {{ name: 'Exxon Mobil', weight: 3.0, fate: '仍在，权重~1.3%', fateColor: '#60a5fa' }},
    {{ name: 'Pfizer', weight: 2.8, fate: '仍在，权重~0.5%', fateColor: '#60a5fa' }},
    {{ name: 'Cisco Systems', weight: 2.7, fate: '仍在，权重~0.5%', fateColor: '#60a5fa' }},
    {{ name: 'Citigroup', weight: 2.6, fate: '仍在，权重~0.3%', fateColor: '#60a5fa' }},
    {{ name: 'Walmart', weight: 2.5, fate: '仍在，权重~0.9%', fateColor: '#60a5fa' }},
    {{ name: 'Microsoft', weight: 2.4, fate: '✅ 仍为Top10 (5.3%)', fateColor: '#34d399' }},
    {{ name: 'AIG', weight: 2.3, fate: '2008年几乎破产', fateColor: '#f87171' }},
    {{ name: 'Intel', weight: 2.2, fate: '仍在，权重~0.3%', fateColor: '#fbbf24' }},
    {{ name: 'Merck', weight: 2.1, fate: '仍在，权重~0.6%', fateColor: '#60a5fa' }}
  ];
  const top2024 = [
    {{ name: 'Nvidia', weight: 7.17, since: '2001年加入（替换Enron）' }},
    {{ name: 'Alphabet', weight: 6.39, since: '2006年加入' }},
    {{ name: 'Apple', weight: 5.86, since: '1982年加入' }},
    {{ name: 'Microsoft', weight: 5.33, since: '1994年加入' }},
    {{ name: 'Amazon', weight: 3.98, since: '2005年加入' }},
    {{ name: 'Broadcom', weight: 2.51, since: '近年权重飙升' }},
    {{ name: 'Meta', weight: 2.49, since: '2013年加入' }},
    {{ name: 'Tesla', weight: 2.31, since: '2020年加入' }},
    {{ name: 'Berkshire', weight: 1.68, since: '长期成分股' }},
    {{ name: 'Eli Lilly', weight: 1.55, since: 'GLP-1药物驱动' }}
  ];

  let h = '<table style="width:100%"><thead><tr><th style="text-align:left">公司</th><th>权重</th><th style="text-align:left">现状</th></tr></thead><tbody>';
  top2000.forEach((c, i) => {{ h += `<tr><td style="text-align:left;font-size:0.82rem"><span style="color:#4a5568">${{i+1}}.</span> ${{c.name}}</td><td style="font-size:0.82rem">${{c.weight}}%</td><td style="text-align:left;font-size:0.78rem;color:${{c.fateColor}}">${{c.fate}}</td></tr>`; }});
  h += '</tbody></table>';
  document.getElementById('top10_2000').innerHTML = h;

  h = '<table style="width:100%"><thead><tr><th style="text-align:left">公司</th><th>权重</th><th style="text-align:left">来历</th></tr></thead><tbody>';
  top2024.forEach((c, i) => {{ h += `<tr><td style="text-align:left;font-size:0.82rem"><span style="color:#4a5568">${{i+1}}.</span> ${{c.name}}</td><td style="font-size:0.82rem;color:#34d399">${{c.weight}}%</td><td style="text-align:left;font-size:0.78rem;color:#6b7a8d">${{c.since}}</td></tr>`; }});
  h += '</tbody></table>';
  document.getElementById('top10_2024').innerHTML = h;
}})();

// ============================================================
// Timeline
// ============================================================
(function() {{
  const events = [
    {{ year:'1957', title:'S&P 500 创立', desc:'500家公司，工业/能源/公用事业为主', color:'#60a5fa' }},
    {{ year:'1976', title:'史上最大换血：60家替换', desc:'40家金融公司加入（Wells Fargo, Chase, BofA）', color:'#fbbf24' }},
    {{ year:'1980', title:'能源巅峰：占指数26%', desc:'Exxon, Mobil, Chevron, Texaco 主导', color:'#f87171' }},
    {{ year:'1982', title:'Apple 加入', desc:'当时还是一家小型PC公司', color:'#34d399' }},
    {{ year:'2000', title:'互联网泡沫：科技权重达33%', desc:'Cisco市值超5000亿，年度换手率10.8%', color:'#f472b6' }},
    {{ year:'2001', title:'Enron崩盘 → Nvidia加入', desc:'财务造假巨头让位未来AI芯片王者', color:'#a78bfa' }},
    {{ year:'2005', title:'Amazon加入', desc:'替换被收购的AT&T，当时市值仅~170亿', color:'#34d399' }},
    {{ year:'2008', title:'金融危机：Lehman消失', desc:'金融板块从17%暴跌至10%', color:'#f87171' }},
    {{ year:'2010', title:'Kodak移除 → Netflix加入', desc:'53年标普生涯终结(2年后破产)，流媒体登场', color:'#fbbf24' }},
    {{ year:'2020', title:'Tesla加入', desc:'电动车革命里程碑，加入即为前十大权重', color:'#34d399' }},
    {{ year:'2024', title:'Nvidia成为第一大权重股(7.2%)', desc:'AI芯片驱动，23年前的小公司变成指数之王', color:'#f472b6' }},
  ];
  let html = '<div style="position:relative;padding:16px 0 16px 36px;border-left:2px solid rgba(255,255,255,0.08);margin-left:24px">';
  events.forEach(e => {{
    html += `<div style="position:relative;margin-bottom:20px;padding-left:20px"><div style="position:absolute;left:-44px;top:2px;width:16px;height:16px;border-radius:50%;background:${{e.color}}"></div><div style="font-size:0.75rem;color:${{e.color}};font-weight:700;letter-spacing:1px">${{e.year}}</div><div style="font-size:0.9rem;font-weight:600;color:#e0e6ed;margin:2px 0">${{e.title}}</div><div style="font-size:0.8rem;color:#6b7a8d">${{e.desc}}</div></div>`;
  }});
  html += '</div>';
  document.getElementById('turnoverTimeline').innerHTML = html;
}})();

// ============================================================
// CHART 9: Annual Turnover Rate
// ============================================================
(function() {{
  const ctx = document.getElementById('turnoverChart').getContext('2d');
  new Chart(ctx, {{
    type: 'bar',
    data: {{
      labels: TURNOVER.map(d => d.year),
      datasets: [
        {{ label: '新增', data: TURNOVER.map(d => d.added), backgroundColor: 'rgba(52,211,153,0.7)', borderRadius: 2 }},
        {{ label: '移除', data: TURNOVER.map(d => -d.removed), backgroundColor: 'rgba(248,113,113,0.7)', borderRadius: 2 }}
      ]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      plugins: {{
        legend: {{ position: 'top', labels: {{ usePointStyle: true, padding: 12 }} }},
        tooltip: {{ callbacks: {{
          title: items => items[0].label + '年',
          label: item => {{
            const d = TURNOVER[item.dataIndex];
            return item.datasetIndex === 0 ? `新增: +${{d.added}}家` : `移除: -${{d.removed}}家 (换手${{d.turnover_pct}}%)`;
          }}
        }} }}
      }},
      scales: {{
        x: {{ stacked: true, ticks: {{ maxRotation: 45, font: {{ size: 10 }} }}, grid: {{ display: false }} }},
        y: {{ stacked: true, ticks: {{ callback: v => Math.abs(v) }}, grid: {{ color: 'rgba(255,255,255,0.04)' }} }}
      }}
    }}
  }});
}})();

// ============================================================
// CHART 10: Duration Distribution
// ============================================================
(function() {{
  const ctx = document.getElementById('durationChart').getContext('2d');
  new Chart(ctx, {{
    type: 'bar',
    data: {{
      labels: DURATION.map(d => d.range),
      datasets: [{{ data: DURATION.map(d => d.count), backgroundColor: DURATION.map((d,i) => {{
        const colors = ['#f87171','#fb923c','#fbbf24','#34d399','#60a5fa','#a78bfa','#f472b6','#e2e8f0'];
        return colors[i] || '#6b7a8d';
      }}), borderWidth: 0, borderRadius: 4 }}]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      plugins: {{
        legend: {{ display: false }},
        tooltip: {{ callbacks: {{ label: item => `${{item.raw}}家公司` }} }}
      }},
      scales: {{
        x: {{ grid: {{ display: false }} }},
        y: {{ ticks: {{ callback: v => v + '家' }}, grid: {{ color: 'rgba(255,255,255,0.04)' }} }}
      }}
    }}
  }});
}})();

// ============================================================
// CHART 11: Current Sector Distribution (Doughnut)
// ============================================================
(function() {{
  const ctx = document.getElementById('sectorPieChart').getContext('2d');
  const sectorData = [
    {{ name: 'Industrials', count: 80, color: '#fbbf24' }},
    {{ name: 'Financials', count: 76, color: '#34d399' }},
    {{ name: 'Info Tech', count: 70, color: '#60a5fa' }},
    {{ name: 'Health Care', count: 60, color: '#a78bfa' }},
    {{ name: 'Consumer Disc.', count: 48, color: '#f472b6' }},
    {{ name: 'Consumer Stap.', count: 36, color: '#fb923c' }},
    {{ name: 'Utilities', count: 31, color: '#94a3b8' }},
    {{ name: 'Real Estate', count: 31, color: '#e2e8f0' }},
    {{ name: 'Materials', count: 26, color: '#6ee7b7' }},
    {{ name: 'Comm Services', count: 23, color: '#c4b5fd' }},
    {{ name: 'Energy', count: 22, color: '#f87171' }}
  ];
  new Chart(ctx, {{
    type: 'doughnut',
    data: {{
      labels: sectorData.map(s => `${{s.name}} (${{s.count}})`),
      datasets: [{{ data: sectorData.map(s => s.count), backgroundColor: sectorData.map(s => s.color), borderWidth: 1, borderColor: '#0a0e1a' }}]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      plugins: {{
        legend: {{ position: 'right', labels: {{ font: {{ size: 11 }}, padding: 8, usePointStyle: true }} }},
        tooltip: {{ callbacks: {{ label: item => `${{item.label}}: ${{item.raw}}家公司` }} }}
      }}
    }}
  }});
}})();

// ============================================================
// Data Table
// ============================================================
(function() {{
  const tbody = document.querySelector('#dataTable tbody');
  [...DATA.yearly_table].reverse().forEach(d => {{
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${{d.year}}</td><td class="${{d.nominal >= 0 ? 'pos' : 'neg'}}">${{d.nominal > 0 ? '+' : ''}}${{d.nominal.toFixed(2)}}%</td><td>${{d.inflation.toFixed(2)}}%</td><td class="${{d.real >= 0 ? 'pos' : 'neg'}}">${{d.real > 0 ? '+' : ''}}${{d.real.toFixed(2)}}%</td>`;
    tbody.appendChild(tr);
  }});
}})();

// ============================================================
// DECOMPOSITION CHARTS (Part IV - 3-Level Analysis)
// ============================================================
if (DECOMP) {{

// CHART D1: Annual Return Decomposition (Stacked Bar)
// Cap extreme values at ±100% for readability (earnings rebound years like 2003, 2009)
(function() {{
  const agg = DECOMP.aggregate;
  const CAP = 100;
  const cap = v => v == null ? 0 : Math.max(-CAP, Math.min(CAP, +(v * 100).toFixed(2)));
  const raw = v => v == null ? 0 : +(v * 100).toFixed(2);
  const rawEG = agg.map(d => raw(d.earnings_growth));
  const rawPE = agg.map(d => raw(d.pe_expansion));
  const ctx = document.getElementById('chartDecomp1').getContext('2d');
  const chart = new Chart(ctx, {{
    type: 'bar',
    data: {{
      labels: agg.map(d => d.year),
      datasets: [
        {{
          label: 'Earnings Growth',
          data: agg.map(d => cap(d.earnings_growth)),
          backgroundColor: agg.map(d => (d.earnings_growth != null && Math.abs(d.earnings_growth * 100) > CAP) ? '#3b82f6' : '#60a5fa'),
          stack: 'stack1',
          hidden: false,
        }},
        {{
          label: 'PE Expansion',
          data: agg.map(d => cap(d.pe_expansion)),
          backgroundColor: agg.map(d => (d.pe_expansion != null && Math.abs(d.pe_expansion * 100) > CAP) ? '#7c3aed' : '#a78bfa'),
          stack: 'stack1',
          hidden: false,
        }},
        {{
          label: 'Dividend Yield',
          data: agg.map(d => d.dividend_yield != null ? +(d.dividend_yield * 100).toFixed(2) : 0),
          backgroundColor: '#34d399',
          stack: 'stack1',
          hidden: false,
        }},
        {{
          label: 'Total Return',
          data: agg.map(d => d.total_return != null ? +(d.total_return * 100).toFixed(2) : null),
          type: 'line',
          borderColor: '#fbbf24',
          backgroundColor: 'transparent',
          borderWidth: 2,
          pointRadius: 2,
          tension: 0.3,
        }}
      ]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      interaction: {{ intersect: false, mode: 'index' }},
      plugins: {{
        legend: {{ position: 'top', labels: {{ usePointStyle: true, padding: 12 }} }},
        tooltip: {{ callbacks: {{
          title: items => items[0].label + ' Year',
          label: function(item) {{
            let val = item.parsed.y;
            let suffix = '';
            if (item.datasetIndex === 0 && Math.abs(rawEG[item.dataIndex]) > CAP) {{
              val = rawEG[item.dataIndex]; suffix = ' (capped in chart)';
            }} else if (item.datasetIndex === 1 && Math.abs(rawPE[item.dataIndex]) > CAP) {{
              val = rawPE[item.dataIndex]; suffix = ' (capped in chart)';
            }}
            return item.dataset.label + ': ' + (val >= 0 ? '+' : '') + val.toFixed(2) + '%' + suffix;
          }}
        }} }}
      }},
      scales: {{
        x: {{ stacked: true, ticks: {{ maxRotation: 0, autoSkip: true, maxTicksLimit: 20, font: {{ size: 10 }} }}, grid: {{ display: false }} }},
        y: {{ stacked: true, suggestedMin: -80, suggestedMax: 80, ticks: {{ callback: v => v + '%' }}, grid: {{ color: 'rgba(255,255,255,0.04)' }} }}
      }}
    }}
  }});
  // Force all datasets visible (workaround for Chart.js off-screen init issue)
  for (let i = 0; i < chart.data.datasets.length; i++) {{
    chart.getDatasetMeta(i).hidden = null;
  }}
  chart.update('none');
}})();

// CHART D2a: Rolling Window Total Return (Line)
(function() {{
  const r5 = DECOMP.rolling['5'] || [];
  const r10 = DECOMP.rolling['10'] || [];
  const r20 = DECOMP.rolling['20'] || [];
  const ctx = document.getElementById('chartDecomp2a').getContext('2d');
  new Chart(ctx, {{
    type: 'line',
    data: {{
      labels: r5.map(d => d.end),
      datasets: [
        {{ label: '5-Year', data: r5.map(d => d.ann_total_return), borderColor: '#f87171', borderWidth: 1.5, pointRadius: 0, tension: 0.3 }},
        {{ label: '10-Year', data: r10.map(d => d.ann_total_return), borderColor: '#fbbf24', borderWidth: 1.5, pointRadius: 0, tension: 0.3 }},
        {{ label: '20-Year', data: r20.map(d => d.ann_total_return), borderColor: '#34d399', borderWidth: 2, pointRadius: 0, tension: 0.3 }},
      ]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      plugins: {{
        title: {{ display: true, text: 'Annualized Total Return by Holding Period', color: '#8896a8', font: {{ size: 12 }} }},
        legend: {{ position: 'top', labels: {{ usePointStyle: true, padding: 10 }} }},
        tooltip: {{ callbacks: {{ label: item => item.dataset.label + ': ' + item.parsed.y.toFixed(2) + '%' }} }}
      }},
      scales: {{
        x: {{ ticks: {{ maxRotation: 0, autoSkip: true, maxTicksLimit: 12, font: {{ size: 10 }} }}, grid: {{ display: false }} }},
        y: {{ ticks: {{ callback: v => v + '%' }}, grid: {{ color: 'rgba(255,255,255,0.04)' }} }}
      }}
    }}
  }});
}})();

// CHART D2b: Mean Reversion - Std Dev convergence (Bar)
(function() {{
  const mr = DECOMP.mean_reversion;
  const windows = ['5', '10', '20'];
  const ctx = document.getElementById('chartDecomp2b').getContext('2d');
  new Chart(ctx, {{
    type: 'bar',
    data: {{
      labels: windows.map(w => w + ' Years'),
      datasets: [
        {{
          label: 'Std Dev (%)',
          data: windows.map(w => mr[w] ? mr[w].std : 0),
          backgroundColor: ['#f87171', '#fbbf24', '#34d399'],
          borderRadius: 4,
        }},
        {{
          label: 'Range (%)',
          data: windows.map(w => mr[w] ? mr[w].range : 0),
          backgroundColor: ['rgba(248,113,113,0.3)', 'rgba(251,191,36,0.3)', 'rgba(52,211,153,0.3)'],
          borderRadius: 4,
        }}
      ]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      plugins: {{
        title: {{ display: true, text: 'Return Volatility Shrinks with Holding Period', color: '#8896a8', font: {{ size: 12 }} }},
        legend: {{ position: 'top', labels: {{ usePointStyle: true, padding: 10 }} }},
        tooltip: {{ callbacks: {{ label: item => item.dataset.label + ': ' + item.parsed.y.toFixed(2) + '%' }} }}
      }},
      scales: {{
        x: {{ grid: {{ display: false }} }},
        y: {{ ticks: {{ callback: v => v + '%' }}, grid: {{ color: 'rgba(255,255,255,0.04)' }} }}
      }}
    }}
  }});

  // Summary cards
  const container = document.getElementById('mrSummary');
  windows.forEach((w, i) => {{
    const s = mr[w];
    if (!s) return;
    const colors = ['#f87171', '#fbbf24', '#34d399'];
    container.innerHTML += `<div class="card" style="text-align:center">
      <div style="font-size:2rem;font-weight:700;color:${{colors[i]}}">${{s.std.toFixed(1)}}%</div>
      <div class="label">${{w}}-Year Std Dev</div>
      <div style="font-size:0.78rem;color:#4a5568;margin-top:4px">Range: ${{s.min.toFixed(1)}}% ~ ${{s.max.toFixed(1)}}%</div>
    </div>`;
  }});
}})();

// CHART D2c: Return Decomposition by Holding Period (Stacked Bar)
(function() {{
  const rolling = DECOMP.rolling;
  // Compute average decomposition for each window
  function avg(arr, key) {{
    const vals = arr.filter(r => r[key] != null).map(r => r[key]);
    return vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : 0;
  }}
  const windows = [
    {{ label: '5年窗口', eg: avg(rolling['5']||[], 'ann_earnings_growth'), pe: avg(rolling['5']||[], 'ann_pe_expansion'), dy: avg(rolling['5']||[], 'ann_dividend_yield') }},
    {{ label: '10年窗口', eg: avg(rolling['10']||[], 'ann_earnings_growth'), pe: avg(rolling['10']||[], 'ann_pe_expansion'), dy: avg(rolling['10']||[], 'ann_dividend_yield') }},
    {{ label: '20年窗口', eg: avg(rolling['20']||[], 'ann_earnings_growth'), pe: avg(rolling['20']||[], 'ann_pe_expansion'), dy: avg(rolling['20']||[], 'ann_dividend_yield') }},
  ];
  // Add full period
  const agg = DECOMP.aggregate;
  const yrs = agg.map(d => d.year).sort((a,b) => a - b);
  const first = agg.find(d => d.year === yrs[0]);
  const last = agg.find(d => d.year === yrs[yrs.length - 1]);
  const n = yrs[yrs.length - 1] - yrs[0];
  const fullEarn = Math.pow(last.ni / first.ni_prior, 1/n) - 1;
  const fullPrice = Math.pow(last.mktcap / first.mktcap_prior, 1/n) - 1;
  const fullPE = (1 + fullPrice) / (1 + fullEarn) - 1;
  const fullDiv = agg.reduce((s, d) => s + (d.dividend_yield || 0), 0) / agg.length;
  windows.push({{ label: '全期(39年)', eg: fullEarn * 100, pe: fullPE * 100, dy: fullDiv * 100 }});
  // First 3 are already in % from rolling data, full period was raw → converted above
  // Actually rolling data is already in %, fix:
  // rolling ann_earnings_growth is already in percentage points? Let me check...
  // No - rolling data stores raw decimals... let me check the JSON
  // From the earlier output: 20yr avg total return 9.88% - that matches rolling output
  // So rolling data IS in percentage points already

  const ctx = document.getElementById('chartDecomp2c').getContext('2d');
  new Chart(ctx, {{
    type: 'bar',
    data: {{
      labels: windows.map(w => w.label),
      datasets: [
        {{ label: '盈利增长', data: windows.map(w => +w.eg.toFixed(2)), backgroundColor: '#60a5fa' }},
        {{ label: 'PE 扩张', data: windows.map(w => +w.pe.toFixed(2)), backgroundColor: '#a78bfa' }},
        {{ label: '股息率', data: windows.map(w => +w.dy.toFixed(2)), backgroundColor: '#34d399' }},
      ]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      indexAxis: 'y',
      plugins: {{
        legend: {{ position: 'top', labels: {{ usePointStyle: true, padding: 12 }} }},
        tooltip: {{
          callbacks: {{
            label: item => item.dataset.label + ': ' + (item.parsed.x >= 0 ? '+' : '') + item.parsed.x.toFixed(2) + '%',
            afterBody: function(items) {{
              const idx = items[0].dataIndex;
              const w = windows[idx];
              const total = w.eg + w.pe + w.dy;
              return ['─────────', '总回报: ' + total.toFixed(2) + '%'];
            }}
          }}
        }}
      }},
      scales: {{
        x: {{
          stacked: true,
          ticks: {{ callback: v => v + '%' }},
          grid: {{ color: 'rgba(255,255,255,0.04)' }},
          title: {{ display: true, text: '年化回报 (%)', color: '#6b7a8d' }}
        }},
        y: {{
          stacked: true,
          grid: {{ display: false }}
        }}
      }}
    }}
  }});
}})();

// CHART SHILLER20: 153-year 20yr rolling decomposition (Stacked Bar + Line)
(function() {{
  if (!SHILLER || !SHILLER.rolling || !SHILLER.rolling['20']) return;
  const r20 = SHILLER.rolling['20'];
  const years = r20.map(d => d.end_year);
  // Force exact additivity: pe_adj = total - eps - div
  const eps = r20.map(d => (d.ann_eps_growth || 0) * 100);
  const div = r20.map(d => (d.avg_div_yield || 0) * 100);
  const total = r20.map(d => (d.ann_total_return || 0) * 100);
  const pe = total.map((t, i) => +(t - eps[i] - div[i]).toFixed(2));

  const ctx = document.getElementById('chartShiller20').getContext('2d');
  const chart = new Chart(ctx, {{
    type: 'bar',
    data: {{
      labels: years,
      datasets: [
        {{
          label: '_bar_eps',
          data: eps,
          backgroundColor: 'rgba(96,165,250,0.35)',
          borderColor: 'rgba(96,165,250,0.5)',
          borderWidth: 0.5,
          stack: 'decomp',
          order: 3,
          hidden: false,
        }},
        {{
          label: '_bar_pe',
          data: pe,
          backgroundColor: 'rgba(167,139,250,0.35)',
          borderColor: 'rgba(167,139,250,0.5)',
          borderWidth: 0.5,
          stack: 'decomp',
          order: 3,
          hidden: false,
        }},
        {{
          label: '_bar_div',
          data: div,
          backgroundColor: 'rgba(52,211,153,0.35)',
          borderColor: 'rgba(52,211,153,0.5)',
          borderWidth: 0.5,
          stack: 'decomp',
          order: 3,
          hidden: false,
        }},
        {{
          label: '总回报',
          data: total,
          type: 'line',
          borderColor: '#fbbf24',
          borderWidth: 2.5,
          pointRadius: 0,
          pointHoverRadius: 4,
          tension: 0.3,
          yAxisID: 'y2',
          order: 1,
          hidden: false,
        }},
        {{
          label: '盈利增长 (趋势)',
          data: eps,
          type: 'line',
          borderColor: '#60a5fa',
          borderWidth: 2,
          pointRadius: 0,
          pointHoverRadius: 3,
          tension: 0.3,
          borderDash: [6, 3],
          yAxisID: 'y2',
          order: 1,
          hidden: false,
        }},
        {{
          label: 'PE 扩张 (趋势)',
          data: pe,
          type: 'line',
          borderColor: '#a78bfa',
          borderWidth: 2,
          pointRadius: 0,
          pointHoverRadius: 3,
          tension: 0.3,
          borderDash: [6, 3],
          yAxisID: 'y2',
          order: 1,
          hidden: false,
        }},
        {{
          label: '股息率 (趋势)',
          data: div,
          type: 'line',
          borderColor: '#34d399',
          borderWidth: 2,
          pointRadius: 0,
          pointHoverRadius: 3,
          tension: 0.3,
          borderDash: [6, 3],
          yAxisID: 'y2',
          order: 1,
          hidden: false,
        }},
      ]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      interaction: {{ mode: 'index', intersect: false }},
      plugins: {{
        legend: {{
          position: 'top',
          labels: {{
            usePointStyle: true, padding: 14, font: {{ size: 12 }},
            filter: item => !item.text.startsWith('_bar_')
          }}
        }},
        tooltip: {{
          filter: item => !item.dataset.label.startsWith('_bar_'),
          callbacks: {{
            title: items => items[0].label + '年 (过去20年年化)',
            label: function(item) {{
              const sign = item.parsed.y >= 0 ? '+' : '';
              return item.dataset.label + ': ' + sign + item.parsed.y.toFixed(2) + '%';
            }},
            afterBody: function(items) {{
              const idx = items[0].dataIndex;
              return ['─────────',
                '验证: ' + eps[idx].toFixed(2) + ' + ' + pe[idx].toFixed(2) + ' + ' + div[idx].toFixed(2) + ' = ' + total[idx].toFixed(2) + '%'];
            }}
          }}
        }}
      }},
      scales: {{
        x: {{
          stacked: true,
          ticks: {{ maxRotation: 0, autoSkip: true, maxTicksLimit: 16, font: {{ size: 10 }} }},
          grid: {{ display: false }}
        }},
        y: {{
          stacked: true,
          ticks: {{ callback: v => v + '%' }},
          grid: {{ color: 'rgba(255,255,255,0.04)' }},
          title: {{ display: true, text: '年化回报率 (%)', color: '#6b7a8d' }}
        }},
        y2: {{
          display: false,
          ticks: {{ callback: v => v + '%' }},
        }}
      }}
    }}
  }});
  // Force visibility workaround
  for (let i = 0; i < chart.data.datasets.length; i++) {{
    chart.getDatasetMeta(i).hidden = null;
  }}
  chart.update('none');
}})();

// CHART SHILLER-LOG: Cumulative growth on log scale with linear fits
(function() {{
  if (!SHILLER || !SHILLER.annual || !SHILLER.decomposition) return;
  const annual = SHILLER.annual;
  const decomp = SHILLER.decomposition;
  const years = Object.keys(annual).map(Number).sort((a,b) => a - b);

  // Build series: Price, EPS, PE, Total Return Index, Dividend Compound Index
  const price = years.map(y => annual[String(y)].price);
  const eps = years.map(y => annual[String(y)].eps);
  const pe = years.map(y => annual[String(y)].pe);

  // Total Return Index: $1 compounded by (price_return + div_yield) each year
  const totalIdx = [1];
  const divIdx = [1];
  for (let i = 0; i < decomp.length; i++) {{
    const d = decomp[i];
    totalIdx.push(totalIdx[totalIdx.length - 1] * (1 + d.total_return));
    divIdx.push(divIdx[divIdx.length - 1] * (1 + d.div_yield));
  }}
  // Align: decomp starts at year 1872, so totalIdx[0]=1 at year 1871, totalIdx[1] at 1872, ...
  // years array starts at 1871
  // totalIdx has length = years.length (1871..2025 = 155 entries)

  // Normalize all to index 100 at first year for visual comparison
  const p0 = price[0], e0 = eps[0], pe0 = pe[0];
  const priceNorm = price.map(v => v / p0 * 100);
  const epsNorm = eps.map(v => v / e0 * 100);
  const peNorm = pe.map(v => v / pe0 * 100);
  const totalNorm = totalIdx.map(v => v * 100);
  const divNorm = divIdx.map(v => v * 100);

  // Linear regression on log10 values: y = slope * x + intercept
  function linreg(xs, ys) {{
    const n = xs.length;
    let sx = 0, sy = 0, sxx = 0, sxy = 0;
    for (let i = 0; i < n; i++) {{
      if (ys[i] <= 0) continue;
      const logy = Math.log10(ys[i]);
      sx += xs[i]; sy += logy; sxx += xs[i] * xs[i]; sxy += xs[i] * logy;
    }}
    const slope = (n * sxy - sx * sy) / (n * sxx - sx * sx);
    const intercept = (sy - slope * sx) / n;
    const cagr = Math.pow(10, slope) - 1;
    return {{ slope, intercept, cagr }};
  }}

  const fitPrice = linreg(years, priceNorm);
  const fitEps = linreg(years, epsNorm);
  const fitPe = linreg(years, peNorm);
  const fitTotal = linreg(years, totalNorm);

  // Generate fit lines
  function fitLine(fit, xs) {{
    return xs.map(x => Math.pow(10, fit.slope * x + fit.intercept));
  }}
  const fitPriceLine = fitLine(fitPrice, years);
  const fitEpsLine = fitLine(fitEps, years);
  const fitPeLine = fitLine(fitPe, years);
  const fitTotalLine = fitLine(fitTotal, years);

  const ctx = document.getElementById('chartShillerLog').getContext('2d');
  const chart = new Chart(ctx, {{
    type: 'line',
    data: {{
      labels: years,
      datasets: [
        // Actual data
        {{ label: '总回报 (含股息再投资)', data: totalNorm, borderColor: '#fbbf24', borderWidth: 2, pointRadius: 0, tension: 0.1, hidden: false }},
        {{ label: 'S&P 500 价格', data: priceNorm, borderColor: '#f87171', borderWidth: 2, pointRadius: 0, tension: 0.1, hidden: false }},
        {{ label: '每股盈利 (EPS)', data: epsNorm, borderColor: '#60a5fa', borderWidth: 2, pointRadius: 0, tension: 0.1, hidden: false }},
        {{ label: 'PE 比率', data: peNorm, borderColor: '#a78bfa', borderWidth: 2, pointRadius: 0, tension: 0.1, hidden: false }},
        // Fit lines
        {{ label: '拟合: 总回报 CAGR ' + (fitTotal.cagr * 100).toFixed(1) + '%', data: fitTotalLine, borderColor: 'rgba(251,191,36,0.5)', borderWidth: 1.5, borderDash: [8, 4], pointRadius: 0, tension: 0, hidden: false }},
        {{ label: '拟合: 价格 CAGR ' + (fitPrice.cagr * 100).toFixed(1) + '%', data: fitPriceLine, borderColor: 'rgba(248,113,113,0.5)', borderWidth: 1.5, borderDash: [8, 4], pointRadius: 0, tension: 0, hidden: false }},
        {{ label: '拟合: EPS CAGR ' + (fitEps.cagr * 100).toFixed(1) + '%', data: fitEpsLine, borderColor: 'rgba(96,165,250,0.5)', borderWidth: 1.5, borderDash: [8, 4], pointRadius: 0, tension: 0, hidden: false }},
        {{ label: '拟合: PE CAGR ' + (fitPe.cagr * 100).toFixed(1) + '%', data: fitPeLine, borderColor: 'rgba(167,139,250,0.5)', borderWidth: 1.5, borderDash: [8, 4], pointRadius: 0, tension: 0, hidden: false }},
      ]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      interaction: {{ mode: 'index', intersect: false }},
      plugins: {{
        legend: {{ position: 'top', labels: {{ usePointStyle: true, padding: 10, font: {{ size: 11 }} }} }},
        tooltip: {{
          callbacks: {{
            title: items => items[0].label + '年',
            label: function(item) {{
              const v = item.parsed.y;
              if (item.dataset.label.startsWith('拟合')) return item.dataset.label;
              return item.dataset.label + ': ' + v.toFixed(1) + ' (×' + (v / 100).toFixed(1) + ')';
            }}
          }}
        }}
      }},
      scales: {{
        x: {{
          ticks: {{ maxRotation: 0, autoSkip: true, maxTicksLimit: 16, font: {{ size: 10 }} }},
          grid: {{ display: false }}
        }},
        y: {{
          type: 'logarithmic',
          title: {{ display: true, text: '指数 (1871=100, 对数坐标)', color: '#6b7a8d' }},
          ticks: {{
            callback: function(v) {{
              if ([1, 10, 100, 1000, 10000, 100000, 1000000].includes(v)) return v.toLocaleString();
              return '';
            }}
          }},
          grid: {{ color: 'rgba(255,255,255,0.04)' }}
        }}
      }}
    }}
  }});
  for (let i = 0; i < chart.data.datasets.length; i++) {{
    chart.getDatasetMeta(i).hidden = null;
  }}
  chart.update('none');

  // Stats cards
  const container = document.getElementById('shillerLogStats');
  const items = [
    {{ name: '总回报', cagr: fitTotal.cagr, color: '#fbbf24', mult: totalNorm[totalNorm.length - 1] / 100 }},
    {{ name: '价格', cagr: fitPrice.cagr, color: '#f87171', mult: priceNorm[priceNorm.length - 1] / 100 }},
    {{ name: 'EPS', cagr: fitEps.cagr, color: '#60a5fa', mult: epsNorm[epsNorm.length - 1] / 100 }},
    {{ name: 'PE', cagr: fitPe.cagr, color: '#a78bfa', mult: peNorm[peNorm.length - 1] / 100 }},
  ];
  items.forEach(it => {{
    container.innerHTML += `<div class="card" style="text-align:center">
      <div style="font-size:1.8rem;font-weight:700;color:${{it.color}}">${{(it.cagr * 100).toFixed(1)}}%</div>
      <div class="label">${{it.name}} CAGR</div>
      <div style="font-size:0.78rem;color:#4a5568;margin-top:4px">${{it.mult.toFixed(0)}}x in 153yr</div>
    </div>`;
  }});
}})();

// CHART SECTOR-DECOMP: Cumulative growth on log scale (switchable by sector)
(function() {{
  if (!DECOMP) return;
  const agg = DECOMP.aggregate;
  const sectors = DECOMP.sectors;
  const select = document.getElementById('sectorDecompSelect');
  const statsEl = document.getElementById('sectorDecompStats');

  // Build sector list
  const sectorMap = {{}};
  sectors.forEach(s => {{
    if (s.sector !== 'XX') sectorMap[s.sector] = s.sector_name;
  }});
  const sectorCodes = Object.keys(sectorMap).sort((a,b) => sectorMap[a].localeCompare(sectorMap[b]));

  const optAll = document.createElement('option');
  optAll.value = 'ALL'; optAll.text = '所有行业 (S&P 500 聚合)'; optAll.selected = true;
  select.appendChild(optAll);
  sectorCodes.forEach(code => {{
    const opt = document.createElement('option');
    opt.value = code; opt.text = sectorMap[code];
    select.appendChild(opt);
  }});

  // Linear regression on log10 values
  function linreg(xs, ys) {{
    let n = 0, sx = 0, sy = 0, sxx = 0, sxy = 0;
    for (let i = 0; i < xs.length; i++) {{
      if (ys[i] == null || ys[i] <= 0) continue;
      const logy = Math.log10(ys[i]);
      sx += xs[i]; sy += logy; sxx += xs[i] * xs[i]; sxy += xs[i] * logy; n++;
    }}
    if (n < 2) return null;
    const slope = (n * sxy - sx * sy) / (n * sxx - sx * sx);
    const intercept = (sy - slope * sx) / n;
    const cagr = Math.pow(10, slope) - 1;
    return {{ slope, intercept, cagr }};
  }}
  function fitLine(fit, xs) {{
    if (!fit) return xs.map(() => null);
    return xs.map(x => Math.pow(10, fit.slope * x + fit.intercept));
  }}

  let chart = null;
  // Persist legend hidden state across sector switches
  // Keys: dataset labels that are toggled OFF by user
  const hiddenLabels = new Set();
  // Map from semantic key to dataset label (labels change with CAGR values)
  const labelKeys = ['总回报', '价格', '盈利', 'PE', '拟合总回报', '拟合价格', '拟合盈利', '拟合PE', '指数权重'];
  function getLabelKey(label) {{
    if (label.startsWith('总回报')) return '总回报';
    if (label === '价格') return '价格';
    if (label === '盈利') return '盈利';
    if (label.startsWith('PE')) return 'PE';
    if (label === '指数权重') return '指数权重';
    if (label.includes('总回报')) return '拟合总回报';
    if (label.includes('价格')) return '拟合价格';
    if (label.includes('盈利')) return '拟合盈利';
    if (label.includes('PE')) return '拟合PE';
    return label;
  }}
  function saveHiddenState() {{
    if (!chart) return;
    hiddenLabels.clear();
    chart.data.datasets.forEach((ds, i) => {{
      if (chart.getDatasetMeta(i).hidden) {{
        hiddenLabels.add(getLabelKey(ds.label));
      }}
    }});
  }}

  function renderSector(sectorCode) {{
    let data, title;
    if (sectorCode === 'ALL') {{
      data = agg.slice().sort((a,b) => a.year - b.year);
      title = 'S&P 500 聚合';
    }} else {{
      data = sectors.filter(s => s.sector === sectorCode).sort((a,b) => a.year - b.year);
      title = sectorMap[sectorCode];
    }}
    if (data.length < 2) return;

    const years = data.map(d => d.year);

    // Build cumulative indices (base 100 at first year)
    // Total Return Index: cumulate (1 + price_return + dividend_yield)
    const totalIdx = [100];
    // Price Index: cumulate (1 + price_return)
    const priceIdx = [100];
    // Earnings Index: cumulate (1 + earnings_growth), null when earnings_growth is null
    const earnIdx = [100];
    let earnBroken = false;

    for (let i = 1; i < data.length; i++) {{
      const d = data[i];
      const pr = d.price_return != null ? d.price_return : 0;
      const dy = d.dividend_yield != null ? d.dividend_yield : 0;
      const tr = (sectorCode === 'ALL' && d.total_return != null) ? d.total_return : pr + dy;

      priceIdx.push(priceIdx[i - 1] * (1 + pr));
      totalIdx.push(totalIdx[i - 1] * (1 + tr));

      if (d.earnings_growth != null && !earnBroken) {{
        const next = earnIdx[earnIdx.length - 1] * (1 + d.earnings_growth);
        earnIdx.push(next > 0 ? next : null);
        if (next <= 0) earnBroken = true;
      }} else {{
        // Try to recover from break using ni ratio
        if (d.ni != null && d.ni > 0 && data[0].ni != null && data[0].ni > 0) {{
          earnIdx.push(100 * d.ni / data[0].ni);
          earnBroken = false;
        }} else {{
          earnIdx.push(null);
        }}
      }}
    }}

    // PE index: derive from price / earnings, or use raw pe normalized
    const peIdx = years.map((y, i) => {{
      if (earnIdx[i] != null && earnIdx[i] > 0) {{
        return priceIdx[i] / earnIdx[i] * 100;
      }}
      // fallback: use raw pe field if available
      const d = data[i];
      if (d.pe != null && d.pe > 0 && data[0].pe != null && data[0].pe > 0) {{
        return 100 * d.pe / data[0].pe;
      }}
      return null;
    }});

    // Weight data (% of S&P 500 market cap)
    const weights = data.map(d => d.weight != null ? +(d.weight * 100).toFixed(1) : null);
    const showWeight = sectorCode !== 'ALL';

    // Compute fits
    const fitTotal = linreg(years, totalIdx);
    const fitPrice = linreg(years, priceIdx);
    const fitEarn  = linreg(years, earnIdx);
    const fitPe    = linreg(years, peIdx);

    // Build datasets
    const datasets = [
      {{ label: '总回报 (含股息再投资)', data: totalIdx, borderColor: '#fbbf24', borderWidth: 2.5, pointRadius: 0, tension: 0.1, yAxisID: 'y' }},
      {{ label: '价格', data: priceIdx, borderColor: '#f87171', borderWidth: 2, pointRadius: 0, tension: 0.1, yAxisID: 'y' }},
      {{ label: '盈利', data: earnIdx, borderColor: '#60a5fa', borderWidth: 2, pointRadius: 0, tension: 0.1, spanGaps: false, yAxisID: 'y' }},
      {{ label: 'PE 比率', data: peIdx, borderColor: '#a78bfa', borderWidth: 2, pointRadius: 0, tension: 0.1, spanGaps: false, yAxisID: 'y' }},
      {{ label: fitTotal ? '拟合: 总回报 CAGR ' + (fitTotal.cagr * 100).toFixed(1) + '%' : '拟合: 总回报',
         data: fitLine(fitTotal, years), borderColor: 'rgba(251,191,36,0.45)', borderWidth: 1.5, borderDash: [8,4], pointRadius: 0, tension: 0, yAxisID: 'y' }},
      {{ label: fitPrice ? '拟合: 价格 CAGR ' + (fitPrice.cagr * 100).toFixed(1) + '%' : '拟合: 价格',
         data: fitLine(fitPrice, years), borderColor: 'rgba(248,113,113,0.45)', borderWidth: 1.5, borderDash: [8,4], pointRadius: 0, tension: 0, yAxisID: 'y' }},
      {{ label: fitEarn ? '拟合: 盈利 CAGR ' + (fitEarn.cagr * 100).toFixed(1) + '%' : '拟合: 盈利',
         data: fitLine(fitEarn, years), borderColor: 'rgba(96,165,250,0.45)', borderWidth: 1.5, borderDash: [8,4], pointRadius: 0, tension: 0, yAxisID: 'y' }},
      {{ label: fitPe ? '拟合: PE CAGR ' + (fitPe.cagr * 100).toFixed(1) + '%' : '拟合: PE',
         data: fitLine(fitPe, years), borderColor: 'rgba(167,139,250,0.45)', borderWidth: 1.5, borderDash: [8,4], pointRadius: 0, tension: 0, yAxisID: 'y' }},
    ];
    // Add weight area for individual sectors
    if (showWeight) {{
      datasets.push({{
        label: '指数权重',
        data: weights,
        borderColor: 'rgba(255,255,255,0.3)',
        backgroundColor: 'rgba(255,255,255,0.06)',
        borderWidth: 1,
        pointRadius: 0,
        tension: 0.3,
        fill: true,
        yAxisID: 'y2',
        order: 10,
      }});
    }}

    saveHiddenState();
    if (chart) chart.destroy();
    const ctx = document.getElementById('chartSectorDecomp').getContext('2d');
    chart = new Chart(ctx, {{
      type: 'line',
      data: {{ labels: years, datasets: datasets }},
      options: {{
        responsive: true, maintainAspectRatio: false,
        interaction: {{ mode: 'index', intersect: false }},
        plugins: {{
          title: {{
            display: true, text: title,
            color: '#e0e6ed', font: {{ size: 14, weight: '600' }}, padding: {{ bottom: 10 }}
          }},
          legend: {{
            position: 'top',
            labels: {{
              usePointStyle: true, padding: 10, font: {{ size: 11 }}
            }}
          }},
          tooltip: {{
            callbacks: {{
              title: items => items[0].label + '年',
              label: function(item) {{
                const v = item.parsed.y;
                if (v == null) return '';
                if (item.dataset.label.startsWith('拟合')) return null;
                if (item.dataset.label === '指数权重') return '指数权重: ' + v.toFixed(1) + '%';
                return item.dataset.label + ': ' + v.toFixed(1) + ' (×' + (v / 100).toFixed(1) + ')';
              }},
              afterBody: function(items) {{
                if (!showWeight) return [];
                const idx = items[0].dataIndex;
                const w = weights[idx];
                const d = data[idx];
                const lines = ['─────────'];
                if (w != null) lines.push('占 S&P 500 市值: ' + w.toFixed(1) + '%');
                if (d.count != null) lines.push('公司数: ' + d.count);
                return lines;
              }}
            }},
            filter: item => !item.dataset.label.startsWith('拟合')
          }}
        }},
        scales: {{
          x: {{
            ticks: {{ maxRotation: 0, autoSkip: true, maxTicksLimit: 20, font: {{ size: 10 }} }},
            grid: {{ display: false }}
          }},
          y: {{
            type: 'logarithmic',
            position: 'left',
            title: {{ display: true, text: '指数 (1985=100, 对数坐标)', color: '#6b7a8d' }},
            ticks: {{
              callback: function(v) {{
                if ([10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 50000].includes(v)) return v.toLocaleString();
                return '';
              }}
            }},
            grid: {{ color: 'rgba(255,255,255,0.04)' }}
          }},
          y2: {{
            type: 'linear',
            position: 'right',
            display: showWeight,
            min: 0,
            max: Math.max(50, ...weights.filter(w => w != null)) * 1.3,
            title: {{ display: showWeight, text: '指数权重 (%)', color: '#6b7a8d' }},
            ticks: {{ callback: v => v + '%', font: {{ size: 10 }}, color: 'rgba(255,255,255,0.3)' }},
            grid: {{ display: false }}
          }}
        }}
      }}
    }});
    // Restore legend hidden state from previous render
    for (let i = 0; i < chart.data.datasets.length; i++) {{
      const key = getLabelKey(chart.data.datasets[i].label);
      if (hiddenLabels.has(key)) {{
        chart.getDatasetMeta(i).hidden = true;
      }} else {{
        chart.getDatasetMeta(i).hidden = null;
      }}
    }}
    chart.update('none');

    // Stats cards
    const n = years.length;
    const items = [
      {{ name: '总回报', fit: fitTotal, color: '#fbbf24', mult: totalIdx[n-1] / 100 }},
      {{ name: '价格', fit: fitPrice, color: '#f87171', mult: priceIdx[n-1] / 100 }},
      {{ name: '盈利', fit: fitEarn, color: '#60a5fa', mult: earnIdx[n-1] != null ? earnIdx[n-1] / 100 : null }},
      {{ name: 'PE', fit: fitPe, color: '#a78bfa', mult: peIdx[n-1] != null ? peIdx[n-1] / 100 : null }},
    ];
    statsEl.innerHTML = items.map(it => {{
      const cagr = it.fit ? (it.fit.cagr * 100).toFixed(1) + '%' : 'N/A';
      const mult = it.mult != null ? it.mult.toFixed(1) + 'x' : 'N/A';
      return `<div class="card" style="text-align:center">
        <div style="font-size:1.5rem;font-weight:700;color:${{it.color}}">${{cagr}}</div>
        <div class="label">${{it.name}} CAGR</div>
        <div style="font-size:0.75rem;color:#4a5568;margin-top:2px">${{mult}} in ${{n}}yr</div>
      </div>`;
    }}).join('');
  }}

  select.addEventListener('change', () => renderSector(select.value));
  renderSector('ALL');
}})();

// CHART D3: Industry Contribution (Horizontal Bar, switchable by year)
(function() {{
  const sectors = DECOMP.sectors;
  const select = document.getElementById('decompYearSelect');
  const years = [...new Set(sectors.map(s => s.year))].sort();
  years.forEach(y => {{
    const opt = document.createElement('option');
    opt.value = y; opt.text = y + ' Year';
    if (y === 2024) opt.selected = true;
    select.appendChild(opt);
  }});

  let chart = null;
  function renderYear(year) {{
    const data = sectors.filter(s => s.year === year && s.sector !== 'XX')
      .sort((a, b) => (b.contrib_price || 0) - (a.contrib_price || 0));
    const labels = data.map(d => d.sector_name);
    const contribPrice = data.map(d => d.contrib_price != null ? +(d.contrib_price * 100).toFixed(2) : 0);
    const contribDiv = data.map(d => d.contrib_div != null ? +(d.contrib_div * 100).toFixed(2) : 0);

    if (chart) chart.destroy();
    const ctx = document.getElementById('chartDecomp3').getContext('2d');
    chart = new Chart(ctx, {{
      type: 'bar',
      data: {{
        labels: labels,
        datasets: [
          {{ label: 'Price Return Contribution', data: contribPrice, backgroundColor: '#60a5fa', borderRadius: 3 }},
          {{ label: 'Dividend Contribution', data: contribDiv, backgroundColor: '#34d399', borderRadius: 3 }},
        ]
      }},
      options: {{
        responsive: true, maintainAspectRatio: false,
        indexAxis: 'y',
        plugins: {{
          legend: {{ position: 'top', labels: {{ usePointStyle: true, padding: 10 }} }},
          tooltip: {{ callbacks: {{ label: item => item.dataset.label + ': ' + (item.parsed.x >= 0 ? '+' : '') + item.parsed.x.toFixed(2) + '%' }} }}
        }},
        scales: {{
          x: {{ ticks: {{ callback: v => v + '%' }}, grid: {{ color: 'rgba(255,255,255,0.04)' }} }},
          y: {{ grid: {{ display: false }} }}
        }}
      }}
    }});
  }}

  select.addEventListener('change', () => renderYear(+select.value));
  renderYear(2024);
}})();

// Verification Table
(function() {{
  const vdata = DECOMP.verification;
  const tbody = document.querySelector('#verifyTable tbody');
  vdata.forEach(v => {{
    const tr = document.createElement('tr');
    const diffNi = v.diff_ni.toFixed(1);
    const diffMc = v.diff_mktcap.toFixed(1);
    const diffRet = v.diff_return != null ? v.diff_return.toFixed(1) : 'N/A';
    tr.innerHTML = `<td>${{v.year}}</td>
      <td>${{(v.agg_ni/1000).toFixed(1)}}</td><td>${{(v.sum_company_ni/1000).toFixed(1)}}</td>
      <td class="${{Math.abs(v.diff_ni) < 1 ? 'pos' : 'neg'}}">${{diffNi}}</td>
      <td>${{(v.agg_mktcap/1000).toLocaleString('en',{{maximumFractionDigits:0}})}}</td>
      <td>${{(v.sum_company_mktcap/1000).toLocaleString('en',{{maximumFractionDigits:0}})}}</td>
      <td class="${{Math.abs(v.diff_mktcap) < 1 ? 'pos' : 'neg'}}">${{diffMc}}</td>
      <td class="${{Math.abs(v.diff_return||0) < 1 ? 'pos' : 'neg'}}">${{diffRet}}</td>`;
    tbody.appendChild(tr);
  }});

  const maxNi = Math.max(...vdata.map(v => Math.abs(v.diff_ni)));
  const maxMc = Math.max(...vdata.map(v => Math.abs(v.diff_mktcap)));
  const el = document.getElementById('verifyResult');
  const ok = maxNi < 1 && maxMc < 1;
  el.innerHTML = `<span style="color:${{ok ? '#34d399' : '#f87171'}};font-weight:600">${{ok ? '✓ Verification Passed' : '✗ Check Required'}}</span>
    &nbsp;—&nbsp; Max earnings diff: $${{maxNi.toFixed(1)}}M, Max market cap diff: $${{maxMc.toFixed(1)}}M`;
}})();

}} // end if (DECOMP)

</script>
</body>
</html>"""

output_path = os.path.join(os.path.dirname(__file__), '..', 'report', 'sp500_mean_reversion.html')
with open(output_path, 'w') as f:
    f.write(html)
print(f"Report written to: {output_path}")

print(f"✅ 文件已生成: {len(html):,} bytes")
