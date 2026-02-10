"""
Inject company-level & sector-level sections into the existing HTML report
"""

html_path = "/sessions/quirky-tender-franklin/mnt/outputs/sp500_mean_reversion.html"

with open(html_path, "r") as f:
    html = f.read()

# ========== NEW HTML SECTIONS ==========
new_sections_html = """
  <!-- NEW: Section 6 - Sector Weight Evolution -->
  <div class="section">
    <h2>图六：行业板块权重的历史演变 — 指数的"新陈代谢"</h2>
    <div class="desc">正是这种不断的行业轮替，让标普500能持续捕获经济增长的前沿，维持长期稳定回报</div>
    <div class="chart-container tall">
      <canvas id="sectorChart"></canvas>
    </div>
    <div class="insight">
      <strong>行业轮替是均值回归的引擎：</strong>1980年能源占26%、科技仅8%；到2024年完全反转——科技占30%、能源仅3.5%。
      衰落的行业被剔除，崛起的行业被纳入，指数始终代表经济最有活力的部分。
    </div>
  </div>

  <!-- NEW: Section 7 - Company Turnover Timeline -->
  <div class="section">
    <h2>图七：标普500的"创造性破坏" — 公司级别的换血</h2>
    <div class="desc">每年约22家公司被替换（4.4%换手率），超过半数现有成分股20年前并不在指数中</div>
    <div id="turnoverTimeline"></div>
    <div class="insight">
      <strong>关键事实：</strong>
      1957年创立时的500家公司，至今仅剩约53家（存活率10.6%）。
      公司在标普500中的平均寿命从1970年代的30-35年缩短到如今的15-20年。
      但每一家被移除的公司，都有一家更有活力的公司接替——Kodak让位Netflix，Enron让位Nvidia，AT&T让位Amazon。
    </div>
  </div>

  <!-- NEW: Section 8 - Top 10 Then vs Now -->
  <div class="section">
    <h2>图八：Top 10 权重股的变迁 — 2000 vs 2024</h2>
    <div class="desc">头部公司的"换脸"是行业轮替的最直观体现</div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:12px">
      <div>
        <div style="text-align:center;font-weight:600;color:#f87171;margin-bottom:10px;font-size:0.95rem">2000年 Top 10（互联网泡沫顶峰）</div>
        <div id="top10_2000"></div>
      </div>
      <div>
        <div style="text-align:center;font-weight:600;color:#34d399;margin-bottom:10px;font-size:0.95rem">2024年 Top 10（AI时代）</div>
        <div id="top10_2024"></div>
      </div>
    </div>
    <div class="insight">
      <strong>惊人的变化：</strong>2000年的Top 10中，只有 Microsoft 留在了2024年的Top 10。
      当年排名第一的 GE（通用电气）在2024年已经拆分成三家公司。
      当年的 Cisco、Intel、Lucent、WorldCom 要么大幅缩水、要么已不复存在。
    </div>
  </div>

  <!-- NEW: Section 9 - The Mechanism Explained -->
  <div class="section">
    <h2>核心机制：为什么个股兴衰，指数却能稳定在 ~6.8%？</h2>
    <div class="desc">三个层面的"均值回归"力量</div>
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px;margin-top:12px">
      <div class="card" style="text-align:left">
        <div class="label" style="color:#60a5fa;font-size:0.9rem;font-weight:600">① 指数委员会的"换血"机制</div>
        <div style="margin-top:10px;font-size:0.88rem;color:#a5b4c6;line-height:1.7">
          标普委员会定期调整成分股：移除衰落公司，纳入新兴龙头。这让指数始终代表美国经济中最大、最有活力的500家公司。<br><br>
          <span style="color:#6b7a8d">年均换手 ~22家 · 1976年单年换60家 · 原始500家仅存53家</span>
        </div>
      </div>
      <div class="card" style="text-align:left">
        <div class="label" style="color:#34d399;font-size:0.9rem;font-weight:600">② 市值加权的"自动调节"</div>
        <div style="margin-top:10px;font-size:0.88rem;color:#a5b4c6;line-height:1.7">
          市值加权意味着成功的公司权重自动增大（Apple从微不足道到6%），失败的公司权重自动缩小直至被移除。这是一种内置的"赢家加码"机制。<br><br>
          <span style="color:#6b7a8d">2000年Top10中仅Microsoft留存至今 · 7/10当今Top10在2000年不在指数中</span>
        </div>
      </div>
      <div class="card" style="text-align:left">
        <div class="label" style="color:#fbbf24;font-size:0.9rem;font-weight:600">③ 经济增长的底层驱动</div>
        <div style="margin-top:10px;font-size:0.88rem;color:#a5b4c6;line-height:1.7">
          美国实际GDP长期增长约3%，加上企业利润率和股东回报，构成了~6-7%实际回报的经济学基础。只要经济体持续创新和增长，指数回报就有底层支撑。<br><br>
          <span style="color:#6b7a8d">97年跨越：大萧条→二战→冷战→石油危机→互联网泡沫→金融危机→疫情</span>
        </div>
      </div>
    </div>
  </div>
"""

# ========== NEW JAVASCRIPT ==========
new_js = """

// ============================================================
// CHART 6: Sector Weight Evolution (Stacked Area)
// ============================================================
function buildSectorChart() {
  const ctx = document.getElementById('sectorChart').getContext('2d');

  // Historical sector weight data (approximate, from research)
  const sectorYears = [1960, 1965, 1970, 1975, 1980, 1985, 1990, 1995, 2000, 2005, 2008, 2010, 2015, 2020, 2024];

  const sectors = {
    'Technology': {
      data: [5, 5, 6, 6, 8, 10, 8, 12, 33, 15, 16, 19, 21, 28, 30],
      color: 'rgba(96, 165, 250, 0.7)', border: '#60a5fa'
    },
    'Energy': {
      data: [18, 17, 16, 20, 26, 18, 13, 9, 6, 10, 14, 11, 7, 2.4, 3.5],
      color: 'rgba(248, 113, 113, 0.7)', border: '#f87171'
    },
    'Financials': {
      data: [5, 5, 6, 8, 10, 12, 8, 13, 17, 22, 10, 16, 17, 11, 13],
      color: 'rgba(52, 211, 153, 0.7)', border: '#34d399'
    },
    'Healthcare': {
      data: [3, 4, 5, 6, 7, 8, 10, 11, 10, 13, 14, 11, 15, 14, 12],
      color: 'rgba(167, 139, 250, 0.7)', border: '#a78bfa'
    },
    'Industrials': {
      data: [20, 18, 17, 15, 14, 12, 14, 12, 9, 11, 12, 11, 10, 8, 9],
      color: 'rgba(251, 191, 36, 0.7)', border: '#fbbf24'
    },
    'Consumer': {
      data: [20, 22, 22, 20, 15, 17, 20, 18, 12, 12, 14, 14, 12, 14, 12],
      color: 'rgba(244, 114, 182, 0.7)', border: '#f472b6'
    },
    'Other': {
      data: [29, 29, 28, 25, 20, 23, 27, 25, 13, 17, 20, 18, 18, 22.6, 20.5],
      color: 'rgba(148, 163, 184, 0.5)', border: '#94a3b8'
    }
  };

  const datasets = Object.entries(sectors).map(([name, s]) => ({
    label: name,
    data: s.data,
    backgroundColor: s.color,
    borderColor: s.border,
    borderWidth: 1,
    fill: true,
    tension: 0.4,
    pointRadius: 3,
    pointHoverRadius: 6,
  }));

  new Chart(ctx, {
    type: 'line',
    data: { labels: sectorYears, datasets: datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { intersect: false, mode: 'index' },
      plugins: {
        legend: { position: 'top', labels: { usePointStyle: true, padding: 12, font: { size: 11 } } },
        tooltip: {
          callbacks: {
            label: item => `${item.dataset.label}: ${item.raw}%`
          }
        }
      },
      scales: {
        x: {
          title: { display: true, text: '年份', color: '#6b7a8d' },
          grid: { display: false }
        },
        y: {
          stacked: false,
          title: { display: true, text: '板块权重 %', color: '#6b7a8d' },
          ticks: { callback: v => v + '%' },
          grid: { color: 'rgba(255,255,255,0.04)' },
          max: 40
        }
      }
    }
  });
}

// ============================================================
// Company Turnover Timeline
// ============================================================
function buildTurnoverTimeline() {
  const container = document.getElementById('turnoverTimeline');

  const events = [
    { year: '1957', icon: '🏗️', title: 'S&P 500 创立', desc: '500家公司，以工业、能源、公用事业为主', color: '#60a5fa' },
    { year: '1976', icon: '🔄', title: '史上最大换血：60家公司被替换', desc: '40家金融公司加入（Wells Fargo, Chase Manhattan, Bank of America）', color: '#fbbf24' },
    { year: '1980', icon: '⛽', title: '能源巅峰：26%权重', desc: 'Exxon, Mobil, Chevron, Texaco 主导指数', color: '#f87171' },
    { year: '1982', icon: '🍎', title: 'Apple 加入 S&P 500', desc: '当时还是一家小型个人电脑公司', color: '#34d399' },
    { year: '1994', icon: '💻', title: 'Microsoft, Intel 崛起', desc: '科技股开始快速扩张在指数中的权重', color: '#60a5fa' },
    { year: '2000', icon: '💥', title: '互联网泡沫：科技权重达33%', desc: 'Cisco市值一度超5000亿，超越Microsoft成全球最大公司', color: '#f472b6' },
    { year: '2001', icon: '📉', title: 'Enron 崩盘被移除 → Nvidia 加入', desc: '史上最戏剧性的替换：财务造假巨头让位给未来AI芯片王者', color: '#a78bfa' },
    { year: '2005', icon: '📦', title: 'Amazon 加入 S&P 500', desc: '替换被收购的 AT&T，当时市值仅~170亿', color: '#34d399' },
    { year: '2008', icon: '🏦', title: '金融危机：Lehman, Bear Stearns 消失', desc: '金融板块从17%暴跌至10%，大量银行和保险公司被移除', color: '#f87171' },
    { year: '2010', icon: '📸', title: 'Kodak 被移除 → Netflix 加入', desc: '胶片巨头53年标普生涯终结（2年后破产），流媒体新星登场', color: '#fbbf24' },
    { year: '2012', icon: '📱', title: 'Facebook(Meta) 上市后加入', desc: '社交媒体时代的标志性事件', color: '#60a5fa' },
    { year: '2015', icon: '🔤', title: 'Google 重组为 Alphabet', desc: '反映科技公司向多元化平台转型的趋势', color: '#a78bfa' },
    { year: '2020', icon: '⚡', title: 'Tesla 加入', desc: '电动车革命的里程碑，加入当日即成前十大权重股', color: '#34d399' },
    { year: '2024', icon: '🤖', title: 'Nvidia 成为第一大权重股 (7.2%)', desc: 'AI芯片驱动，从2001年的小公司到指数之王。Palantir, Dell 加入', color: '#f472b6' },
  ];

  let html = '<div style="position:relative;padding:20px 0 20px 40px;border-left:2px solid rgba(255,255,255,0.1);margin-left:30px">';
  events.forEach(e => {
    html += `
      <div style="position:relative;margin-bottom:24px;padding-left:24px">
        <div style="position:absolute;left:-52px;top:0;width:24px;height:24px;border-radius:50%;background:${e.color};display:flex;align-items:center;justify-content:center;font-size:12px;border:2px solid #0a0e1a">${e.icon}</div>
        <div style="font-size:0.8rem;color:${e.color};font-weight:700;letter-spacing:1px">${e.year}</div>
        <div style="font-size:0.95rem;font-weight:600;color:#e0e6ed;margin:3px 0">${e.title}</div>
        <div style="font-size:0.83rem;color:#8896a8">${e.desc}</div>
      </div>
    `;
  });
  html += '</div>';
  container.innerHTML = html;
}

// ============================================================
// Top 10 Then vs Now
// ============================================================
function buildTop10Comparison() {
  const top2000 = [
    { name: 'General Electric', weight: 4.0, sector: 'Industrial', fate: '2024年拆分为3家公司', fateColor: '#fbbf24' },
    { name: 'Exxon Mobil', weight: 3.0, sector: 'Energy', fate: '仍在，但权重降至~1.3%', fateColor: '#60a5fa' },
    { name: 'Pfizer', weight: 2.8, sector: 'Healthcare', fate: '仍在，权重~0.5%', fateColor: '#60a5fa' },
    { name: 'Cisco Systems', weight: 2.7, sector: 'Tech', fate: '仍在，权重~0.5%', fateColor: '#60a5fa' },
    { name: 'Citigroup', weight: 2.6, sector: 'Financial', fate: '仍在，权重~0.3%', fateColor: '#60a5fa' },
    { name: 'Walmart', weight: 2.5, sector: 'Consumer', fate: '仍在，权重~0.9%', fateColor: '#60a5fa' },
    { name: 'Microsoft', weight: 2.4, sector: 'Tech', fate: '✅ 仍为Top 10 (5.3%)', fateColor: '#34d399' },
    { name: 'AIG', weight: 2.3, sector: 'Financial', fate: '2008年几乎破产，已移除', fateColor: '#f87171' },
    { name: 'Intel', weight: 2.2, sector: 'Tech', fate: '仍在，权重降至~0.3%', fateColor: '#fbbf24' },
    { name: 'Merck', weight: 2.1, sector: 'Healthcare', fate: '仍在，权重~0.6%', fateColor: '#60a5fa' },
  ];

  const top2024 = [
    { name: 'Nvidia', weight: 7.17, sector: 'Tech/AI', since: '2001年加入（替换Enron）' },
    { name: 'Alphabet (Google)', weight: 6.39, sector: 'Tech', since: '2006年加入' },
    { name: 'Apple', weight: 5.86, sector: 'Tech', since: '1982年加入' },
    { name: 'Microsoft', weight: 5.33, sector: 'Tech', since: '1994年加入' },
    { name: 'Amazon', weight: 3.98, sector: 'Tech/Retail', since: '2005年加入（替换AT&T）' },
    { name: 'Broadcom', weight: 2.51, sector: 'Semiconductors', since: '近年权重飙升' },
    { name: 'Meta (Facebook)', weight: 2.49, sector: 'Tech/Social', since: '2013年加入' },
    { name: 'Tesla', weight: 2.31, sector: 'EV/Tech', since: '2020年加入' },
    { name: 'Berkshire Hathaway', weight: 1.68, sector: 'Financial', since: '长期成分股' },
    { name: 'Eli Lilly', weight: 1.55, sector: 'Healthcare', since: 'GLP-1药物推动' },
  ];

  // Build 2000 table
  let html2000 = '<table style="width:100%"><thead><tr><th style="text-align:left">公司</th><th>权重</th><th style="text-align:left">现状</th></tr></thead><tbody>';
  top2000.forEach((c, i) => {
    html2000 += `<tr>
      <td style="text-align:left;font-size:0.85rem"><span style="color:#6b7a8d">${i+1}.</span> ${c.name}<br><span style="color:#6b7a8d;font-size:0.75rem">${c.sector}</span></td>
      <td style="font-size:0.85rem">${c.weight}%</td>
      <td style="text-align:left;font-size:0.78rem;color:${c.fateColor}">${c.fate}</td>
    </tr>`;
  });
  html2000 += '</tbody></table>';

  // Build 2024 table
  let html2024 = '<table style="width:100%"><thead><tr><th style="text-align:left">公司</th><th>权重</th><th style="text-align:left">来历</th></tr></thead><tbody>';
  top2024.forEach((c, i) => {
    html2024 += `<tr>
      <td style="text-align:left;font-size:0.85rem"><span style="color:#6b7a8d">${i+1}.</span> ${c.name}<br><span style="color:#6b7a8d;font-size:0.75rem">${c.sector}</span></td>
      <td style="font-size:0.85rem;color:#34d399">${c.weight}%</td>
      <td style="text-align:left;font-size:0.78rem;color:#8896a8">${c.since}</td>
    </tr>`;
  });
  html2024 += '</tbody></table>';

  document.getElementById('top10_2000').innerHTML = html2000;
  document.getElementById('top10_2024').innerHTML = html2024;
}

buildSectorChart();
buildTurnoverTimeline();
buildTop10Comparison();
"""

# ========== INJECT INTO HTML ==========
# 1. Insert new HTML sections before "<!-- Data Table -->"
marker = '  <!-- Data Table -->'
if marker in html:
    html = html.replace(marker, new_sections_html + '\n' + marker)
    print("✅ HTML sections injected")
else:
    print("❌ Could not find Data Table marker")

# 2. Insert new JS before the closing </script> tag
# Find the last </script> and insert before it
last_script_end = html.rfind('</script>')
if last_script_end > 0:
    html = html[:last_script_end] + new_js + '\n' + html[last_script_end:]
    print("✅ JavaScript injected")
else:
    print("❌ Could not find </script> tag")

with open(html_path, 'w') as f:
    f.write(html)

print(f"Final file size: {len(html):,} bytes")
print("✅ Done!")
