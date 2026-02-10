"""
将行业级可展开数据注入到现有HTML报告的数据表中
"""
import json

# Load industry data
with open("/sessions/quirky-tender-franklin/industry_data.json") as f:
    industry_data = json.load(f)

# Load existing HTML
html_path = "/sessions/quirky-tender-franklin/mnt/outputs/sp500_mean_reversion.html"
with open(html_path) as f:
    html = f.read()

industry_json = json.dumps(industry_data)

# === NEW CSS ===
new_css = """
  /* Expandable table */
  .expand-row { cursor: pointer; transition: background 0.2s; }
  .expand-row:hover td { background: rgba(96,165,250,0.08) !important; }
  .expand-row td:first-child::before {
    content: '▶';
    display: inline-block;
    margin-right: 8px;
    font-size: 0.7rem;
    transition: transform 0.2s;
    color: #60a5fa;
  }
  .expand-row.open td:first-child::before { transform: rotate(90deg); }
  .sub-row { display: none; }
  .sub-row.show { display: table-row; }
  .sub-row td { padding-left: 28px !important; font-size: 0.78rem; background: rgba(255,255,255,0.015); border-bottom: 1px solid rgba(255,255,255,0.02); }
  .sub-row td:first-child { color: #6b7a8d; }
  .verification-row td {
    background: rgba(96,165,250,0.05) !important;
    font-weight: 600;
    border-top: 1px solid rgba(96,165,250,0.2);
  }
  .match { color: #34d399; }
  .mismatch { color: #fbbf24; }
  .contrib-bar {
    display: inline-block;
    height: 12px;
    border-radius: 2px;
    vertical-align: middle;
    margin-right: 4px;
  }
"""

# === Replace the data table section ===
old_data_section = """  <div class="section" id="data">
    <h2>完整年度数据表</h2>
    <div class="desc">97年逐年数据——名义回报、通胀率、实际回报</div>
    <div class="data-table-wrapper">
      <table id="dataTable">
        <thead><tr><th>年份</th><th>名义回报 %</th><th>通胀率 %</th><th>实际回报 %</th></tr></thead>
        <tbody></tbody>
      </table>
    </div>
  </div>"""

new_data_section = """  <div class="section" id="data">
    <h2>完整年度数据表 — 点击展开行业分解</h2>
    <div class="desc">点击任意年份 → 展开5大行业的权重、回报、贡献。底部验证：∑行业贡献 ≈ 指数回报</div>
    <div class="data-table-wrapper" style="max-height:600px">
      <table id="dataTable">
        <thead>
          <tr>
            <th style="text-align:left">年份</th>
            <th>名义回报</th>
            <th>通胀率</th>
            <th>实际回报</th>
            <th>行业贡献之和</th>
            <th>误差</th>
          </tr>
        </thead>
        <tbody></tbody>
      </table>
    </div>
    <div class="insight" style="margin-top:12px">
      <strong>验证原理：</strong>指数回报 = ∑(行业权重 × 行业回报)。上表中"行业贡献之和"由Kenneth French数据库
      5大行业组合（市值加权）独立计算，与S&P 500实际名义回报高度吻合（误差来自：French覆盖全市场而非仅S&P 500成分股，
      权重为估算值，且分红处理方式略有不同）。
    </div>
  </div>"""

# === New JS for expandable table ===
new_js = """
// ============================================================
// INDUSTRY DATA (from Kenneth French Data Library)
// ============================================================
const INDUSTRY = """ + industry_json + """;

const SECTOR_COLORS = {
  'Cnsmr': '#f472b6', 'Manuf': '#fbbf24', 'HiTec': '#60a5fa',
  'Hlth': '#a78bfa', 'Other': '#94a3b8'
};
const SECTOR_CN = {
  'Cnsmr': '消费', 'Manuf': '制造', 'HiTec': '科技',
  'Hlth': '医疗', 'Other': '其他'
};

// Override data table builder
(function() {
  const tbody = document.querySelector('#dataTable tbody');
  const sectors = ['Cnsmr', 'Manuf', 'HiTec', 'Hlth', 'Other'];

  [...DATA.yearly_table].reverse().forEach(d => {
    const yearStr = String(d.year);
    const indData = INDUSTRY[yearStr];
    const hasIndustry = !!indData;

    // Main row
    const tr = document.createElement('tr');
    tr.className = hasIndustry ? 'expand-row' : '';

    let contribHtml = '', diffHtml = '';
    if (hasIndustry) {
      const contrib = indData.total_contribution;
      const diff = (contrib - d.nominal).toFixed(1);
      const diffAbs = Math.abs(parseFloat(diff));
      const diffClass = diffAbs < 3 ? 'match' : 'mismatch';
      contribHtml = `<span style="color:#60a5fa">${contrib > 0 ? '+' : ''}${contrib.toFixed(1)}%</span>`;
      diffHtml = `<span class="${diffClass}">${diff > 0 ? '+' : ''}${diff}%</span>`;
    } else {
      contribHtml = '<span style="color:#3a4352">—</span>';
      diffHtml = '<span style="color:#3a4352">—</span>';
    }

    tr.innerHTML = `
      <td>${d.year}</td>
      <td class="${d.nominal >= 0 ? 'pos' : 'neg'}">${d.nominal > 0 ? '+' : ''}${d.nominal.toFixed(2)}%</td>
      <td>${d.inflation.toFixed(2)}%</td>
      <td class="${d.real >= 0 ? 'pos' : 'neg'}">${d.real > 0 ? '+' : ''}${d.real.toFixed(2)}%</td>
      <td>${contribHtml}</td>
      <td>${diffHtml}</td>
    `;
    tbody.appendChild(tr);

    // Sub rows for industry breakdown
    if (hasIndustry) {
      const subId = 'sub_' + d.year;

      sectors.forEach(s => {
        const sd = indData.sectors[s];
        const subTr = document.createElement('tr');
        subTr.className = 'sub-row ' + subId;

        const barWidth = Math.min(Math.abs(sd.contribution) * 4, 80);
        const barColor = sd.contribution >= 0 ? 'rgba(52,211,153,0.6)' : 'rgba(248,113,113,0.6)';

        subTr.innerHTML = `
          <td style="padding-left:28px">
            <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${SECTOR_COLORS[s]};margin-right:6px;vertical-align:middle"></span>
            ${SECTOR_CN[s]}
            <span style="color:#3a4352;font-size:0.7rem;margin-left:6px">${sd.firms}家</span>
          </td>
          <td style="color:${sd.return >= 0 ? '#34d399' : '#f87171'}">${sd.return > 0 ? '+' : ''}${sd.return.toFixed(2)}%</td>
          <td style="color:#4a5568;font-size:0.75rem">权重 ${sd.weight.toFixed(1)}%</td>
          <td></td>
          <td>
            <span class="contrib-bar" style="width:${barWidth}px;background:${barColor}"></span>
            <span style="color:${sd.contribution >= 0 ? '#34d399' : '#f87171'}">${sd.contribution > 0 ? '+' : ''}${sd.contribution.toFixed(2)}%</span>
          </td>
          <td></td>
        `;
        tbody.appendChild(subTr);
      });

      // Verification row
      const vTr = document.createElement('tr');
      vTr.className = 'sub-row verification-row ' + subId;
      const contrib = indData.total_contribution;
      const diff = Math.abs(contrib - d.nominal);
      vTr.innerHTML = `
        <td style="padding-left:28px;color:#60a5fa">∑ 验证</td>
        <td style="color:#60a5fa">${d.nominal > 0 ? '+' : ''}${d.nominal.toFixed(2)}%</td>
        <td style="color:#4a5568">${indData.total_firms}家公司</td>
        <td></td>
        <td style="color:#60a5fa">${contrib > 0 ? '+' : ''}${contrib.toFixed(2)}%</td>
        <td><span class="${diff < 3 ? 'match' : 'mismatch'}">${diff < 3 ? '✓' : '~'} Δ${diff.toFixed(1)}%</span></td>
      `;
      tbody.appendChild(vTr);

      // Click handler
      tr.addEventListener('click', () => {
        tr.classList.toggle('open');
        document.querySelectorAll('.' + subId).forEach(el => el.classList.toggle('show'));
      });
    }
  });
})();
"""

# === INJECT ===
# 1. Add CSS
html = html.replace('/* Responsive */', new_css + '\n  /* Responsive */')

# 2. Replace data section
html = html.replace(old_data_section, new_data_section)

# 3. Remove old data table JS (the IIFE that builds the table)
old_table_js = """// ============================================================
// Data Table
// ============================================================
(function() {
  const tbody = document.querySelector('#dataTable tbody');
  [...DATA.yearly_table].reverse().forEach(d => {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${d.year}</td><td class="${d.nominal >= 0 ? 'pos' : 'neg'}">${d.nominal > 0 ? '+' : ''}${d.nominal.toFixed(2)}%</td><td>${d.inflation.toFixed(2)}%</td><td class="${d.real >= 0 ? 'pos' : 'neg'}">${d.real > 0 ? '+' : ''}${d.real.toFixed(2)}%</td>`;
    tbody.appendChild(tr);
  });
})();"""

html = html.replace(old_table_js, new_js)

# 4. Update nav link text
html = html.replace(
    '<a class="nav-link" href="#data"><span class="nav-icon">📋</span>完整年度数据</a>',
    '<a class="nav-link" href="#data"><span class="nav-icon">📋</span>年度数据 (可展开)</a>'
)

with open(html_path, 'w') as f:
    f.write(html)

print(f"✅ 文件更新完成: {len(html):,} bytes")
print(f"   行业数据: {len(industry_data)} 年 (1927-2019)")
