"""
重建完整 HTML 报告：加入左侧导航 + 公司级数据
"""
import json

# Load existing analysis data
with open("sp500_analysis.json") as f:
    analysis = json.load(f)

# Load turnover data
with open("turnover_data.json") as f:
    turnover = json.load(f)

# Load duration distribution
with open("duration_dist.json") as f:
    duration_dist = json.load(f)

data_json = json.dumps(analysis)
turnover_json = json.dumps(turnover)
duration_json = json.dumps(duration_dist)

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
    <div class="nav-group-title">Part IV · 结论</div>
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

  <!-- ========== PART IV: CONCLUSIONS ========== -->

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
</script>
</body>
</html>"""

output_path = "/sessions/quirky-tender-franklin/mnt/outputs/sp500_mean_reversion.html"
with open(output_path, 'w') as f:
    f.write(html)

print(f"✅ 文件已生成: {len(html):,} bytes")
