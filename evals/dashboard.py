#!/usr/bin/env python3
"""Generate an interactive HTML dashboard for autoresearch results.

Usage:
    ./evals/dashboard.py <target_name>       # Generate + open dashboard for one target
    ./evals/dashboard.py --all               # All targets in one dashboard
    ./evals/dashboard.py --list              # Terminal summary table

Generates a self-contained HTML file with interactive Chart.js charts.
No Python dependencies beyond the standard library.
"""

import csv
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

EVALS_DIR = Path(__file__).parent
TARGETS_DIR = EVALS_DIR / "targets"


def load_results(target_name: str) -> list[dict] | None:
    tsv = TARGETS_DIR / target_name / "results.tsv"
    if not tsv.exists():
        return None
    rows = []
    with open(tsv) as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            row["pass_rate"] = float(row["pass_rate"].rstrip("%"))
            row["score"] = int(row["score"])
            row["max_score"] = int(row["max_score"])
            rows.append(row)
    return rows if rows else None


def load_criteria(target_name: str) -> list[dict]:
    criteria_file = TARGETS_DIR / target_name / "criteria.yaml"
    criteria = []
    if criteria_file.exists():
        current = {}
        for line in criteria_file.read_text().splitlines():
            stripped = line.strip()
            if stripped.startswith("- id:"):
                if current:
                    criteria.append(current)
                current = {"id": stripped.split(":", 1)[1].strip().strip('"').strip("'")}
            elif stripped.startswith("question:") and current:
                current["question"] = stripped.split(":", 1)[1].strip().strip('"').strip("'")
        if current:
            criteria.append(current)
    return criteria


def load_config(target_name: str) -> dict:
    config_file = TARGETS_DIR / target_name / "config.yaml"
    config = {}
    if config_file.exists():
        for line in config_file.read_text().splitlines():
            if ":" in line and not line.startswith(" ") and not line.startswith("-"):
                key, val = line.split(":", 1)
                config[key.strip()] = val.strip().strip('"').strip("'")
    return config


def list_targets():
    targets = sorted(d.name for d in TARGETS_DIR.iterdir() if d.is_dir())
    if not targets:
        print("No targets found.")
        return

    print(f"{'Target':<25} {'Runs':>6} {'Best':>8} {'Latest':>8} {'Status'}")
    print("-" * 65)

    for name in targets:
        rows = load_results(name)
        if not rows:
            print(f"{name:<25} {'--':>6}")
            continue

        kept = [r for r in rows if r["status"] == "keep"]
        best = max((r["pass_rate"] for r in kept), default=0)
        latest = rows[-1]
        print(f"{name:<25} {len(rows):>6} {best:>7.1f}% {latest['pass_rate']:>7.1f}% {latest['status']}")


def build_target_data(target_name: str) -> dict | None:
    rows = load_results(target_name)
    if not rows:
        return None

    criteria = load_criteria(target_name)
    config = load_config(target_name)

    kept = [r for r in rows if r["status"] == "keep"]
    discarded = [r for r in rows if r["status"] == "discard"]
    baseline = rows[0]["pass_rate"] if rows else 0
    best = max((r["pass_rate"] for r in kept), default=baseline)

    running_best = []
    current_best = 0
    for r in rows:
        if r["status"] == "keep":
            current_best = max(current_best, r["pass_rate"])
        running_best.append(current_best)

    top_hits = []
    prev_rate = baseline
    for r in kept[1:]:  # Skip baseline
        delta = r["pass_rate"] - prev_rate
        top_hits.append({**r, "delta": delta})
        prev_rate = r["pass_rate"]
    top_hits.sort(key=lambda x: x["delta"], reverse=True)

    tsv_path = TARGETS_DIR / target_name / "results.tsv"
    mtime = datetime.fromtimestamp(tsv_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")

    return {
        "name": target_name,
        "rows": rows,
        "kept_count": len(kept),
        "discarded_count": len(discarded),
        "baseline": baseline,
        "best": best,
        "improvement": best - baseline,
        "running_best": running_best,
        "top_hits": top_hits,
        "criteria": criteria,
        "config": config,
        "last_updated": mtime,
    }


def generate_html(targets_data: list[dict]) -> str:
    data_json = json.dumps(targets_data, indent=2)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Autoresearch Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-annotation@3"></script>
<style>
  :root {{
    --bg: #1a1a1a;
    --surface: #222;
    --surface-raised: #2a2a2a;
    --border: #333;
    --text: #ccc;
    --text-strong: #e8e8e8;
    --text-muted: #777;
    --accent: #e8a035;
    --kept: #4a9;
    --kept-dim: rgba(68,170,153,0.12);
    --discarded: #888;
    --discarded-dim: rgba(136,136,136,0.08);
    --negative: #c55;
    --negative-dim: rgba(204,85,85,0.12);
    --pending: #b8a040;
    --mono: 'SF Mono', SFMono-Regular, Consolas, 'Liberation Mono', Menlo, monospace;
  }}
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{
    font-family: var(--mono);
    font-size: 13px;
    background: var(--bg);
    color: var(--text);
    line-height: 1.6;
  }}

  /* --- Layout --- */
  .page {{ max-width: 1100px; margin: 0 auto; padding: 32px 24px; }}
  .page-header {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 32px;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--border);
  }}
  .page-header h1 {{
    font-size: 14px;
    font-weight: 600;
    color: var(--text-strong);
    text-transform: uppercase;
    letter-spacing: 1.5px;
  }}
  .page-header .meta {{
    font-size: 11px;
    color: var(--text-muted);
  }}

  /* --- Tabs --- */
  .tab-bar {{
    display: flex;
    gap: 0;
    margin-bottom: 24px;
    border-bottom: 1px solid var(--border);
  }}
  .tab {{
    padding: 8px 20px;
    cursor: pointer;
    color: var(--text-muted);
    font-size: 12px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    border-bottom: 2px solid transparent;
    transition: color 0.1s;
  }}
  .tab:hover {{ color: var(--text); }}
  .tab.active {{ color: var(--accent); border-bottom-color: var(--accent); }}
  .tab-content {{ display: none; }}
  .tab-content.active {{ display: block; }}

  /* --- Hero answer --- */
  .hero {{
    display: flex;
    align-items: baseline;
    gap: 24px;
    margin-bottom: 24px;
  }}
  .hero-metric {{
    font-size: 48px;
    font-weight: 700;
    line-height: 1;
  }}
  .hero-metric.positive {{ color: var(--kept); }}
  .hero-metric.negative {{ color: var(--negative); }}
  .hero-metric.neutral {{ color: var(--text-muted); }}
  .hero-context {{
    font-size: 12px;
    color: var(--text-muted);
    line-height: 1.8;
  }}
  .hero-context strong {{ color: var(--text); font-weight: 500; }}

  /* --- Stats row --- */
  .stats-row {{
    display: flex;
    gap: 32px;
    padding: 12px 0;
    margin-bottom: 24px;
    border-top: 1px solid var(--border);
    border-bottom: 1px solid var(--border);
  }}
  .stat {{
    display: flex;
    gap: 8px;
    align-items: baseline;
  }}
  .stat-label {{
    font-size: 11px;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }}
  .stat-value {{
    font-size: 14px;
    font-weight: 600;
    color: var(--text-strong);
  }}

  /* --- Sections --- */
  .section {{
    margin-bottom: 32px;
  }}
  .section-header {{
    font-size: 11px;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 12px;
    padding-bottom: 4px;
  }}
  .section-note {{
    font-size: 11px;
    color: var(--text-muted);
    margin-bottom: 12px;
    font-style: italic;
  }}

  /* --- Chart --- */
  .chart-wrap {{
    background: var(--surface);
    border: 1px solid var(--border);
    padding: 16px;
    margin-bottom: 16px;
  }}
  .chart-wrap canvas {{ max-height: 320px; }}

  /* --- Sparse data notice --- */
  .sparse-notice {{
    background: var(--surface);
    border: 1px solid var(--border);
    padding: 24px;
    text-align: center;
    color: var(--text-muted);
    font-size: 12px;
    margin-bottom: 16px;
  }}
  .sparse-notice strong {{ color: var(--text); display: block; margin-bottom: 4px; }}

  /* --- Tables --- */
  table {{ width: 100%; border-collapse: collapse; }}
  table th {{
    text-align: left;
    font-size: 10px;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    padding: 6px 8px;
    border-bottom: 1px solid var(--border);
    cursor: pointer;
    user-select: none;
  }}
  table th:hover {{ color: var(--text); }}
  table th .sort-arrow {{ font-size: 9px; margin-left: 2px; }}
  table td {{
    padding: 6px 8px;
    border-bottom: 1px solid rgba(51,51,51,0.5);
    font-size: 12px;
  }}
  table tr:hover td {{ background: var(--surface-raised); }}
  table td.mono {{ font-family: var(--mono); }}
  .pill {{
    display: inline-block;
    padding: 1px 8px;
    border-radius: 3px;
    font-size: 11px;
    font-weight: 500;
  }}
  .pill-keep {{ color: var(--kept); background: var(--kept-dim); }}
  .pill-discard {{ color: var(--negative); background: var(--negative-dim); }}
  .pill-pending {{ color: var(--pending); background: rgba(184,160,64,0.12); }}
  .pill-crash {{ color: var(--negative); background: var(--negative-dim); }}
  .delta-pos {{ color: var(--kept); }}
  .delta-neg {{ color: var(--negative); }}
  .delta-zero {{ color: var(--text-muted); }}
  .text-muted {{ color: var(--text-muted); }}
  .text-truncate {{
    max-width: 320px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }}

  /* --- Criteria list --- */
  .criteria-list {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
  }}
  @media (max-width: 700px) {{
    .criteria-list {{ grid-template-columns: 1fr; }}
    .stats-row {{ flex-wrap: wrap; gap: 16px; }}
    .hero {{ flex-direction: column; gap: 12px; }}
  }}
  .criteria-item {{
    font-size: 11px;
    padding: 8px 10px;
    background: var(--surface);
    border-left: 3px solid var(--border);
  }}
  .criteria-item code {{
    color: var(--accent);
    font-size: 11px;
  }}
  .criteria-item .q {{ color: var(--text-muted); margin-top: 2px; }}

  /* --- Chart row --- */
  .chart-pair {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
  }}
  @media (max-width: 700px) {{
    .chart-pair {{ grid-template-columns: 1fr; }}
  }}

  /* --- Status filter --- */
  .filters {{
    display: flex;
    gap: 8px;
    margin-bottom: 12px;
    font-size: 11px;
  }}
  .filter-btn {{
    padding: 3px 10px;
    border: 1px solid var(--border);
    background: transparent;
    color: var(--text-muted);
    cursor: pointer;
    font-family: var(--mono);
    font-size: 11px;
    transition: all 0.1s;
  }}
  .filter-btn:hover {{ border-color: var(--text-muted); color: var(--text); }}
  .filter-btn.active {{ border-color: var(--accent); color: var(--accent); }}
</style>
</head>
<body>
<div class="page">

<div class="page-header">
  <h1>Autoresearch</h1>
  <span class="meta">generated {generated_at}</span>
</div>

<div id="app"></div>

</div>

<script>
const TARGETS = {data_json};
const MIN_EXPERIMENTS_FOR_CHARTS = 4;

function renderApp() {{
  const app = document.getElementById('app');

  if (TARGETS.length > 1) {{
    const tabBar = document.createElement('div');
    tabBar.className = 'tab-bar';
    TARGETS.forEach((t, i) => {{
      const tab = document.createElement('div');
      tab.className = 'tab' + (i === 0 ? ' active' : '');
      tab.textContent = t.name;
      tab.onclick = () => switchTab(i);
      tab.id = 'tab-' + i;
      tabBar.appendChild(tab);
    }});
    app.appendChild(tabBar);
  }}

  TARGETS.forEach((t, i) => {{
    const section = document.createElement('div');
    section.className = 'tab-content' + (i === 0 ? ' active' : '');
    section.id = 'content-' + i;
    section.innerHTML = renderTarget(t, i);
    app.appendChild(section);
  }});

  TARGETS.forEach((t, i) => {{
    if (t.rows.length >= MIN_EXPERIMENTS_FOR_CHARTS) {{
      renderCharts(t, i);
    }}
    setupTableSort(i);
    setupFilters(i);
  }});
}}

function switchTab(idx) {{
  document.querySelectorAll('.tab').forEach((t, i) => t.className = 'tab' + (i === idx ? ' active' : ''));
  document.querySelectorAll('.tab-content').forEach((c, i) => c.className = 'tab-content' + (i === idx ? ' active' : ''));
}}

function renderTarget(t, idx) {{
  const n = t.rows.length;
  const impClass = t.improvement > 0 ? 'positive' : t.improvement < 0 ? 'negative' : 'neutral';
  const impSign = t.improvement > 0 ? '+' : '';
  const keepRate = t.kept_count + t.discarded_count > 0
    ? ((t.kept_count / (t.kept_count + t.discarded_count)) * 100).toFixed(0) + '%'
    : '—';
  const latest = t.rows[n - 1];

  const heroText = t.improvement === 0 && n <= 2
    ? 'Baseline established. Run experiments to see improvement.'
    : t.improvement > 0
      ? `${{impSign}}${{t.improvement.toFixed(1)}}% over baseline (${{t.baseline.toFixed(1)}}% &rarr; ${{t.best.toFixed(1)}}%)`
      : `No improvement yet over ${{t.baseline.toFixed(1)}}% baseline`;

  return `
    <!-- Hero: answer "is it working?" in 2 seconds -->
    <div class="hero">
      <div class="hero-metric ${{impClass}}">${{t.best.toFixed(1)}}%</div>
      <div class="hero-context">
        <strong>${{t.name}}</strong> &mdash; ${{n}} experiment${{n !== 1 ? 's' : ''}}<br>
        ${{heroText}}<br>
        <span class="text-muted">data from ${{t.last_updated}} &middot; model: ${{t.config.model || '?'}} &middot; judge: ${{t.config.judge_model || '?'}}</span>
      </div>
    </div>

    <!-- Compact stats -->
    <div class="stats-row">
      <div class="stat"><span class="stat-label">baseline</span> <span class="stat-value">${{t.baseline.toFixed(1)}}%</span></div>
      <div class="stat"><span class="stat-label">best</span> <span class="stat-value" style="color:var(--kept)">${{t.best.toFixed(1)}}%</span></div>
      <div class="stat"><span class="stat-label">latest</span> <span class="stat-value">${{latest.pass_rate.toFixed(1)}}%</span></div>
      <div class="stat"><span class="stat-label">kept</span> <span class="stat-value">${{t.kept_count}}</span></div>
      <div class="stat"><span class="stat-label">discarded</span> <span class="stat-value">${{t.discarded_count}}</span></div>
      <div class="stat"><span class="stat-label">keep rate</span> <span class="stat-value">${{keepRate}}</span></div>
    </div>

    <!-- Progress chart (or sparse notice) -->
    <div class="section">
      <div class="section-header">Progress</div>
      ${{n >= MIN_EXPERIMENTS_FOR_CHARTS
        ? `<div class="section-note">Each dot is one eval run. Green = kept improvement. Gray = discarded. Line = running best.</div>
           <div class="chart-wrap"><canvas id="progress-${{idx}}"></canvas></div>`
        : `<div class="sparse-notice">
             <strong>Not enough data for charts yet</strong>
             Run ${{MIN_EXPERIMENTS_FOR_CHARTS - n}} more experiment${{MIN_EXPERIMENTS_FOR_CHARTS - n !== 1 ? 's' : ''}} to unlock progress visualization.
             <br>Use: <code>./evals/run.sh ${{t.name}}</code>
           </div>`
      }}
    </div>

    ${{n >= MIN_EXPERIMENTS_FOR_CHARTS ? `
    <div class="section">
      <div class="chart-pair">
        <div class="chart-wrap"><canvas id="scores-${{idx}}"></canvas></div>
        <div class="chart-wrap"><canvas id="cumulative-${{idx}}"></canvas></div>
      </div>
    </div>
    ` : ''}}

    <!-- Experiment log -->
    <div class="section">
      <div class="section-header">Experiment Log</div>
      <div class="filters" id="filters-${{idx}}">
        <button class="filter-btn active" data-filter="all" onclick="filterTable(${{idx}}, 'all', this)">all</button>
        <button class="filter-btn" data-filter="keep" onclick="filterTable(${{idx}}, 'keep', this)">kept</button>
        <button class="filter-btn" data-filter="discard" onclick="filterTable(${{idx}}, 'discard', this)">discarded</button>
      </div>
      <table id="log-table-${{idx}}">
        <thead>
          <tr>
            <th data-col="idx" data-type="num"># <span class="sort-arrow"></span></th>
            <th data-col="commit">commit</th>
            <th data-col="score" data-type="num">score <span class="sort-arrow"></span></th>
            <th data-col="rate" data-type="num">rate <span class="sort-arrow"></span></th>
            <th data-col="status">status</th>
            <th data-col="desc">description</th>
          </tr>
        </thead>
        <tbody>
          ${{t.rows.map((r, i) => `
            <tr data-status="${{r.status}}">
              <td class="text-muted">${{i}}</td>
              <td style="font-size:11px">${{r.commit}}</td>
              <td>${{r.score}}/${{r.max_score}}</td>
              <td style="font-weight:600">${{r.pass_rate.toFixed(1)}}%</td>
              <td><span class="pill pill-${{r.status}}">${{r.status}}</span></td>
              <td class="text-truncate">${{r.description}}</td>
            </tr>
          `).join('')}}
        </tbody>
      </table>
    </div>

    ${{t.top_hits.length > 0 ? `
    <div class="section">
      <div class="section-header">Top Improvements</div>
      <div class="section-note">Kept experiments ranked by how much they improved over the previous best.</div>
      <table>
        <thead><tr><th>rank</th><th>delta</th><th>rate</th><th>commit</th><th>description</th></tr></thead>
        <tbody>
          ${{t.top_hits.map((h, i) => `
            <tr>
              <td class="text-muted">${{i + 1}}</td>
              <td class="${{h.delta > 0 ? 'delta-pos' : h.delta < 0 ? 'delta-neg' : 'delta-zero'}}">${{h.delta > 0 ? '+' : ''}}${{h.delta.toFixed(1)}}%</td>
              <td style="font-weight:600">${{h.pass_rate.toFixed(1)}}%</td>
              <td style="font-size:11px">${{h.commit}}</td>
              <td class="text-truncate">${{h.description}}</td>
            </tr>
          `).join('')}}
        </tbody>
      </table>
    </div>
    ` : ''}}

    <!-- Criteria reference -->
    ${{t.criteria.length > 0 ? `
    <div class="section">
      <div class="section-header">Evaluation Criteria</div>
      <div class="section-note">Binary pass/fail questions scored by the LLM judge for each run.</div>
      <div class="criteria-list">
        ${{t.criteria.map(c => `
          <div class="criteria-item">
            <code>${{c.id}}</code>
            <div class="q">${{c.question || ''}}</div>
          </div>
        `).join('')}}
      </div>
    </div>
    ` : ''}}
  `;
}}

/* --- Sortable tables --- */
function setupTableSort(idx) {{
  const table = document.getElementById('log-table-' + idx);
  if (!table) return;
  const headers = table.querySelectorAll('th[data-col]');
  headers.forEach(th => {{
    th.addEventListener('click', () => {{
      const col = th.cellIndex;
      const type = th.dataset.type || 'str';
      const tbody = table.querySelector('tbody');
      const rows = Array.from(tbody.querySelectorAll('tr'));
      const asc = th.dataset.sort !== 'asc';
      headers.forEach(h => {{ h.dataset.sort = ''; h.querySelector('.sort-arrow').textContent = ''; }});
      th.dataset.sort = asc ? 'asc' : 'desc';
      th.querySelector('.sort-arrow').textContent = asc ? '\\u25B2' : '\\u25BC';
      rows.sort((a, b) => {{
        let va = a.cells[col].textContent.trim();
        let vb = b.cells[col].textContent.trim();
        if (type === 'num') {{
          va = parseFloat(va) || 0;
          vb = parseFloat(vb) || 0;
          return asc ? va - vb : vb - va;
        }}
        return asc ? va.localeCompare(vb) : vb.localeCompare(va);
      }});
      rows.forEach(r => tbody.appendChild(r));
    }});
  }});
}}

/* --- Status filters --- */
function filterTable(idx, status, btn) {{
  const table = document.getElementById('log-table-' + idx);
  if (!table) return;
  const container = document.getElementById('filters-' + idx);
  container.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  table.querySelectorAll('tbody tr').forEach(tr => {{
    if (status === 'all' || tr.dataset.status === status) {{
      tr.style.display = '';
    }} else {{
      tr.style.display = 'none';
    }}
  }});
}}

/* --- Charts --- */
function renderCharts(t, idx) {{
  const labels = t.rows.map((_, i) => i);
  Chart.defaults.color = '#777';
  Chart.defaults.borderColor = '#333';
  Chart.defaults.font.family = "'SF Mono', SFMono-Regular, Consolas, monospace";
  Chart.defaults.font.size = 11;

  const keptData = t.rows.map(r => r.status === 'keep' ? r.pass_rate : null);
  const discardedData = t.rows.map(r => r.status === 'discard' ? r.pass_rate : null);
  const pendingData = t.rows.map(r => r.status === 'pending' ? r.pass_rate : null);

  new Chart(document.getElementById('progress-' + idx), {{
    type: 'line',
    data: {{
      labels,
      datasets: [
        {{ label: 'Running Best', data: t.running_best, borderColor: '#4a9', backgroundColor: 'rgba(68,170,153,0.06)', borderWidth: 2, fill: true, stepped: 'after', pointRadius: 0, order: 3 }},
        {{ label: 'Kept', data: keptData, backgroundColor: '#4a9', pointRadius: 6, pointHoverRadius: 9, showLine: false, order: 1 }},
        {{ label: 'Discarded', data: discardedData, backgroundColor: 'rgba(136,136,136,0.5)', pointRadius: 3, pointHoverRadius: 6, showLine: false, order: 2 }},
        {{ label: 'Pending', data: pendingData, backgroundColor: '#b8a040', pointRadius: 4, pointStyle: 'rectRot', showLine: false, order: 1 }},
      ]
    }},
    options: {{
      responsive: true,
      plugins: {{
        title: {{ display: false }},
        legend: {{ display: true, position: 'top', labels: {{ boxWidth: 8, padding: 16 }} }},
        tooltip: {{ callbacks: {{ label: ctx => {{
          const r = t.rows[ctx.dataIndex];
          return [`${{r.status}}: ${{r.pass_rate.toFixed(1)}}%`, `${{r.score}}/${{r.max_score}}`, r.description, r.commit];
        }} }} }},
        annotation: {{ annotations: {{ baseline: {{
          type: 'line', yMin: t.baseline, yMax: t.baseline,
          borderColor: 'rgba(232,160,53,0.3)', borderWidth: 1, borderDash: [4, 4],
          label: {{ content: 'baseline ' + t.baseline.toFixed(1) + '%', display: true, position: 'start', backgroundColor: 'transparent', color: '#e8a035', font: {{ size: 10 }} }}
        }} }} }}
      }},
      scales: {{
        x: {{ title: {{ display: true, text: 'experiment #' }}, grid: {{ color: 'rgba(51,51,51,0.5)' }} }},
        y: {{ title: {{ display: true, text: 'pass rate %' }}, grid: {{ color: 'rgba(51,51,51,0.5)' }},
             min: Math.max(0, Math.min(t.baseline, t.best) - 15), max: Math.min(100, t.best + 10) }}
      }}
    }}
  }});

  // Score bars
  new Chart(document.getElementById('scores-' + idx), {{
    type: 'bar',
    data: {{
      labels,
      datasets: [{{ label: 'Score', data: t.rows.map(r => r.score),
        backgroundColor: t.rows.map(r => r.status === 'keep' ? 'rgba(68,170,153,0.6)' : r.status === 'discard' ? 'rgba(136,136,136,0.25)' : 'rgba(184,160,64,0.4)'),
        borderRadius: 2 }}]
    }},
    options: {{
      responsive: true,
      plugins: {{ title: {{ display: true, text: 'Raw Score', font: {{ size: 12 }} }}, legend: {{ display: false }},
        tooltip: {{ callbacks: {{ label: ctx => {{ const r = t.rows[ctx.dataIndex]; return `${{r.score}}/${{r.max_score}} (${{r.pass_rate.toFixed(1)}}%)`; }} }} }} }},
      scales: {{ x: {{ grid: {{ display: false }} }}, y: {{ grid: {{ color: 'rgba(51,51,51,0.5)' }}, beginAtZero: true }} }}
    }}
  }});

  // Cumulative
  let ck = 0, cd = 0;
  const cumK = [], cumD = [];
  t.rows.forEach(r => {{ if (r.status === 'keep') ck++; if (r.status === 'discard') cd++; cumK.push(ck); cumD.push(cd); }});
  new Chart(document.getElementById('cumulative-' + idx), {{
    type: 'line',
    data: {{
      labels,
      datasets: [
        {{ label: 'Kept', data: cumK, borderColor: '#4a9', backgroundColor: 'rgba(68,170,153,0.08)', fill: true, tension: 0.1, pointRadius: 2 }},
        {{ label: 'Discarded', data: cumD, borderColor: '#888', backgroundColor: 'rgba(136,136,136,0.06)', fill: true, tension: 0.1, pointRadius: 2 }}
      ]
    }},
    options: {{
      responsive: true,
      plugins: {{ title: {{ display: true, text: 'Cumulative', font: {{ size: 12 }} }}, legend: {{ display: true, position: 'top', labels: {{ boxWidth: 8 }} }} }},
      scales: {{ x: {{ grid: {{ display: false }} }}, y: {{ grid: {{ color: 'rgba(51,51,51,0.5)' }}, beginAtZero: true }} }}
    }}
  }});
}}

renderApp();
</script>
</body>
</html>"""


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    if sys.argv[1] == "--list":
        list_targets()
        return

    if sys.argv[1] == "--all":
        targets = sorted(d.name for d in TARGETS_DIR.iterdir() if d.is_dir())
        data = [d for name in targets if (d := build_target_data(name)) is not None]
        if not data:
            print("No targets with results found.")
            sys.exit(1)
        out = EVALS_DIR / "dashboard.html"
    else:
        target_name = sys.argv[1]
        if not (TARGETS_DIR / target_name).is_dir():
            print(f"Target not found: {target_name}")
            print(f"Available: {', '.join(d.name for d in TARGETS_DIR.iterdir() if d.is_dir())}")
            sys.exit(1)
        d = build_target_data(target_name)
        if not d:
            print(f"No results for {target_name}")
            sys.exit(1)
        data = [d]
        out = TARGETS_DIR / target_name / "dashboard.html"

    html = generate_html(data)
    out.write_text(html)
    print(f"Dashboard: {out}")

    if sys.platform == "darwin":
        subprocess.run(["open", str(out)], check=False)


if __name__ == "__main__":
    main()
