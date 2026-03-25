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

    # Load criteria names from criteria.yaml
    criteria_file = TARGETS_DIR / target_name / "criteria.yaml"
    criteria_names = []
    if criteria_file.exists():
        for line in criteria_file.read_text().splitlines():
            line = line.strip()
            if line.startswith("- id:"):
                criteria_names.append(line.split(":", 1)[1].strip())

    kept = [r for r in rows if r["status"] == "keep"]
    discarded = [r for r in rows if r["status"] == "discard"]
    baseline = rows[0]["pass_rate"] if rows else 0
    best = max((r["pass_rate"] for r in kept), default=baseline)

    # Running best series
    running_best = []
    current_best = 0
    for r in rows:
        if r["status"] == "keep":
            current_best = max(current_best, r["pass_rate"])
        running_best.append(current_best)

    # Top hits (kept experiments ranked by delta)
    top_hits = []
    prev_rate = baseline
    for r in kept:
        delta = r["pass_rate"] - prev_rate
        top_hits.append({**r, "delta": delta})
        prev_rate = r["pass_rate"]
    top_hits.sort(key=lambda x: x["delta"], reverse=True)

    return {
        "name": target_name,
        "rows": rows,
        "kept_count": len(kept),
        "discarded_count": len(discarded),
        "baseline": baseline,
        "best": best,
        "improvement": best - baseline,
        "running_best": running_best,
        "top_hits": top_hits[:10],
        "criteria_names": criteria_names,
    }


def generate_html(targets_data: list[dict]) -> str:
    data_json = json.dumps(targets_data, indent=2)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>FOTW Autoresearch Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-annotation@3"></script>
<style>
  :root {{
    --bg: #0d1117;
    --surface: #161b22;
    --border: #30363d;
    --text: #e6edf3;
    --text-muted: #8b949e;
    --green: #3fb950;
    --green-dim: rgba(63, 185, 80, 0.15);
    --red: #f85149;
    --red-dim: rgba(248, 81, 73, 0.15);
    --yellow: #d29922;
    --blue: #58a6ff;
    --gray: #484f58;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.5;
    padding: 24px;
  }}
  h1 {{
    font-size: 24px;
    font-weight: 600;
    margin-bottom: 8px;
  }}
  .subtitle {{
    color: var(--text-muted);
    font-size: 14px;
    margin-bottom: 24px;
  }}
  .target-section {{
    margin-bottom: 48px;
  }}
  .target-header {{
    display: flex;
    align-items: baseline;
    gap: 16px;
    margin-bottom: 16px;
    border-bottom: 1px solid var(--border);
    padding-bottom: 12px;
  }}
  .target-header h2 {{
    font-size: 20px;
    font-weight: 600;
  }}
  .stat-cards {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 12px;
    margin-bottom: 24px;
  }}
  .stat-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 16px;
  }}
  .stat-card .label {{
    font-size: 12px;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }}
  .stat-card .value {{
    font-size: 28px;
    font-weight: 700;
    margin-top: 4px;
  }}
  .stat-card .value.green {{ color: var(--green); }}
  .stat-card .value.blue {{ color: var(--blue); }}
  .stat-card .value.yellow {{ color: var(--yellow); }}
  .stat-card .value.red {{ color: var(--red); }}
  .chart-container {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 16px;
    position: relative;
  }}
  .chart-container canvas {{
    max-height: 400px;
  }}
  .chart-row {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin-bottom: 16px;
  }}
  @media (max-width: 900px) {{
    .chart-row {{ grid-template-columns: 1fr; }}
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
  }}
  table th {{
    text-align: left;
    font-weight: 600;
    color: var(--text-muted);
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    padding: 8px 12px;
    border-bottom: 1px solid var(--border);
  }}
  table td {{
    padding: 8px 12px;
    border-bottom: 1px solid var(--border);
  }}
  table tr:hover td {{
    background: rgba(255,255,255,0.02);
  }}
  .status-keep {{
    color: var(--green);
    background: var(--green-dim);
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 500;
  }}
  .status-discard {{
    color: var(--red);
    background: var(--red-dim);
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 500;
  }}
  .status-pending {{
    color: var(--yellow);
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 500;
  }}
  .delta-positive {{ color: var(--green); }}
  .delta-negative {{ color: var(--red); }}
  .mono {{ font-family: 'SF Mono', SFMono-Regular, Consolas, monospace; font-size: 12px; }}
  .tab-bar {{
    display: flex;
    gap: 4px;
    margin-bottom: 16px;
    border-bottom: 1px solid var(--border);
    padding-bottom: 0;
  }}
  .tab {{
    padding: 8px 16px;
    cursor: pointer;
    color: var(--text-muted);
    border-bottom: 2px solid transparent;
    font-size: 14px;
    transition: all 0.15s;
  }}
  .tab:hover {{ color: var(--text); }}
  .tab.active {{
    color: var(--text);
    border-bottom-color: var(--blue);
  }}
  .tab-content {{ display: none; }}
  .tab-content.active {{ display: block; }}
</style>
</head>
<body>

<h1>FOTW Autoresearch Dashboard</h1>
<p class="subtitle">Autonomous skill optimization — experiment results and progress tracking</p>

<div id="app"></div>

<script>
const TARGETS = {data_json};

function renderApp() {{
  const app = document.getElementById('app');

  if (TARGETS.length > 1) {{
    // Tab bar for multiple targets
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

  // Render charts after DOM is ready
  TARGETS.forEach((t, i) => renderCharts(t, i));
}}

function switchTab(idx) {{
  document.querySelectorAll('.tab').forEach((t, i) => {{
    t.className = 'tab' + (i === idx ? ' active' : '');
  }});
  document.querySelectorAll('.tab-content').forEach((c, i) => {{
    c.className = 'tab-content' + (i === idx ? ' active' : '');
  }});
}}

function renderTarget(t, idx) {{
  const keepRate = t.kept_count + t.discarded_count > 0
    ? ((t.kept_count / (t.kept_count + t.discarded_count)) * 100).toFixed(0)
    : '—';

  return `
    <div class="target-section">
      <div class="target-header">
        <h2>${{t.name}}</h2>
        <span style="color: var(--text-muted)">${{t.rows.length}} experiments</span>
      </div>

      <div class="stat-cards">
        <div class="stat-card">
          <div class="label">Baseline</div>
          <div class="value blue">${{t.baseline.toFixed(1)}}%</div>
        </div>
        <div class="stat-card">
          <div class="label">Best</div>
          <div class="value green">${{t.best.toFixed(1)}}%</div>
        </div>
        <div class="stat-card">
          <div class="label">Improvement</div>
          <div class="value ${{t.improvement >= 0 ? 'green' : 'red'}}">${{t.improvement >= 0 ? '+' : ''}}${{t.improvement.toFixed(1)}}%</div>
        </div>
        <div class="stat-card">
          <div class="label">Keep Rate</div>
          <div class="value yellow">${{keepRate}}%</div>
        </div>
        <div class="stat-card">
          <div class="label">Kept</div>
          <div class="value">${{t.kept_count}}</div>
        </div>
        <div class="stat-card">
          <div class="label">Discarded</div>
          <div class="value">${{t.discarded_count}}</div>
        </div>
      </div>

      <div class="chart-container">
        <canvas id="progress-${{idx}}"></canvas>
      </div>

      <div class="chart-row">
        <div class="chart-container">
          <canvas id="scores-${{idx}}"></canvas>
        </div>
        <div class="chart-container">
          <canvas id="cumulative-${{idx}}"></canvas>
        </div>
      </div>

      <div class="chart-container">
        <h3 style="margin-bottom:12px; font-size:15px;">Experiment Log</h3>
        <table>
          <thead>
            <tr>
              <th>#</th>
              <th>Commit</th>
              <th>Score</th>
              <th>Pass Rate</th>
              <th>Status</th>
              <th>Description</th>
            </tr>
          </thead>
          <tbody>
            ${{t.rows.map((r, i) => `
              <tr>
                <td style="color:var(--text-muted)">${{i}}</td>
                <td class="mono">${{r.commit}}</td>
                <td class="mono">${{r.score}}/${{r.max_score}}</td>
                <td class="mono" style="font-weight:600">${{r.pass_rate.toFixed(1)}}%</td>
                <td><span class="status-${{r.status}}">${{r.status}}</span></td>
                <td>${{r.description}}</td>
              </tr>
            `).join('')}}
          </tbody>
        </table>
      </div>

      ${{t.top_hits.length > 1 ? `
      <div class="chart-container" style="margin-top:16px">
        <h3 style="margin-bottom:12px; font-size:15px;">Top Hits (by improvement delta)</h3>
        <table>
          <thead>
            <tr>
              <th>Rank</th>
              <th>Delta</th>
              <th>Pass Rate</th>
              <th>Commit</th>
              <th>Description</th>
            </tr>
          </thead>
          <tbody>
            ${{t.top_hits.map((h, i) => `
              <tr>
                <td style="color:var(--text-muted)">${{i + 1}}</td>
                <td class="mono ${{h.delta >= 0 ? 'delta-positive' : 'delta-negative'}}">${{h.delta >= 0 ? '+' : ''}}${{h.delta.toFixed(1)}}%</td>
                <td class="mono" style="font-weight:600">${{h.pass_rate.toFixed(1)}}%</td>
                <td class="mono">${{h.commit}}</td>
                <td>${{h.description}}</td>
              </tr>
            `).join('')}}
          </tbody>
        </table>
      </div>
      ` : ''}}
    </div>
  `;
}}

function renderCharts(t, idx) {{
  const labels = t.rows.map((_, i) => i);
  const chartDefaults = {{
    color: '#8b949e',
    borderColor: '#30363d',
    font: {{ family: '-apple-system, BlinkMacSystemFont, sans-serif' }}
  }};

  Chart.defaults.color = chartDefaults.color;
  Chart.defaults.borderColor = chartDefaults.borderColor;

  // --- Progress chart (main) ---
  const progressCtx = document.getElementById('progress-' + idx);
  if (!progressCtx) return;

  const keptData = t.rows.map(r => r.status === 'keep' ? r.pass_rate : null);
  const discardedData = t.rows.map(r => r.status === 'discard' ? r.pass_rate : null);
  const pendingData = t.rows.map(r => r.status === 'pending' ? r.pass_rate : null);
  const crashData = t.rows.map(r => r.status === 'crash' ? r.pass_rate : null);

  new Chart(progressCtx, {{
    type: 'line',
    data: {{
      labels: labels,
      datasets: [
        {{
          label: 'Running Best',
          data: t.running_best,
          borderColor: '#3fb950',
          backgroundColor: 'rgba(63,185,80,0.08)',
          borderWidth: 2,
          fill: true,
          stepped: 'after',
          pointRadius: 0,
          order: 3,
        }},
        {{
          label: 'Kept',
          data: keptData,
          borderColor: 'transparent',
          backgroundColor: '#3fb950',
          pointRadius: 7,
          pointHoverRadius: 10,
          showLine: false,
          order: 1,
        }},
        {{
          label: 'Discarded',
          data: discardedData,
          borderColor: 'transparent',
          backgroundColor: 'rgba(139,148,158,0.4)',
          pointRadius: 4,
          pointHoverRadius: 7,
          showLine: false,
          order: 2,
        }},
        {{
          label: 'Pending',
          data: pendingData,
          borderColor: 'transparent',
          backgroundColor: '#d29922',
          pointRadius: 5,
          pointStyle: 'rectRot',
          showLine: false,
          order: 1,
        }},
        {{
          label: 'Crashed',
          data: crashData,
          borderColor: 'transparent',
          backgroundColor: '#f85149',
          pointRadius: 5,
          pointStyle: 'crossRot',
          showLine: false,
          order: 1,
        }},
      ]
    }},
    options: {{
      responsive: true,
      plugins: {{
        title: {{
          display: true,
          text: 'Pass Rate Over Experiments',
          font: {{ size: 16, weight: '600' }},
          padding: {{ bottom: 16 }},
        }},
        tooltip: {{
          callbacks: {{
            label: function(ctx) {{
              const i = ctx.dataIndex;
              const r = t.rows[i];
              return [
                `${{r.status}}: ${{r.pass_rate.toFixed(1)}}%`,
                `Score: ${{r.score}}/${{r.max_score}}`,
                `${{r.description}}`,
                `Commit: ${{r.commit}}`,
              ];
            }}
          }}
        }},
        annotation: {{
          annotations: {{
            baseline: {{
              type: 'line',
              yMin: t.baseline,
              yMax: t.baseline,
              borderColor: 'rgba(88,166,255,0.4)',
              borderWidth: 1,
              borderDash: [6, 4],
              label: {{
                content: `Baseline ${{t.baseline.toFixed(1)}}%`,
                display: true,
                position: 'start',
                backgroundColor: 'rgba(88,166,255,0.15)',
                color: '#58a6ff',
                font: {{ size: 11 }},
              }}
            }}
          }}
        }}
      }},
      scales: {{
        x: {{
          title: {{ display: true, text: 'Experiment #' }},
          grid: {{ color: 'rgba(48,54,61,0.5)' }},
        }},
        y: {{
          title: {{ display: true, text: 'Pass Rate %' }},
          grid: {{ color: 'rgba(48,54,61,0.5)' }},
          min: Math.max(0, t.baseline - 20),
          max: Math.min(100, t.best + 15),
        }}
      }}
    }}
  }});

  // --- Score bar chart ---
  const scoresCtx = document.getElementById('scores-' + idx);
  if (scoresCtx) {{
    new Chart(scoresCtx, {{
      type: 'bar',
      data: {{
        labels: labels,
        datasets: [{{
          label: 'Score',
          data: t.rows.map(r => r.score),
          backgroundColor: t.rows.map(r =>
            r.status === 'keep' ? 'rgba(63,185,80,0.7)' :
            r.status === 'discard' ? 'rgba(139,148,158,0.3)' :
            r.status === 'pending' ? 'rgba(210,153,34,0.5)' :
            'rgba(248,81,73,0.5)'
          ),
          borderRadius: 3,
        }}]
      }},
      options: {{
        responsive: true,
        plugins: {{
          title: {{ display: true, text: 'Raw Score Per Experiment', font: {{ size: 14 }} }},
          tooltip: {{
            callbacks: {{
              label: (ctx) => {{
                const r = t.rows[ctx.dataIndex];
                return `${{r.score}}/${{r.max_score}} (${{r.pass_rate.toFixed(1)}}%) — ${{r.description}}`;
              }}
            }}
          }}
        }},
        scales: {{
          x: {{ grid: {{ display: false }} }},
          y: {{ grid: {{ color: 'rgba(48,54,61,0.5)' }}, beginAtZero: true }}
        }}
      }}
    }});
  }}

  // --- Cumulative keep/discard ---
  const cumCtx = document.getElementById('cumulative-' + idx);
  if (cumCtx) {{
    let cumKept = 0, cumDisc = 0;
    const cumKeptData = [], cumDiscData = [];
    t.rows.forEach(r => {{
      if (r.status === 'keep') cumKept++;
      if (r.status === 'discard') cumDisc++;
      cumKeptData.push(cumKept);
      cumDiscData.push(cumDisc);
    }});

    new Chart(cumCtx, {{
      type: 'line',
      data: {{
        labels: labels,
        datasets: [
          {{
            label: 'Kept',
            data: cumKeptData,
            borderColor: '#3fb950',
            backgroundColor: 'rgba(63,185,80,0.1)',
            fill: true,
            tension: 0.1,
          }},
          {{
            label: 'Discarded',
            data: cumDiscData,
            borderColor: '#f85149',
            backgroundColor: 'rgba(248,81,73,0.08)',
            fill: true,
            tension: 0.1,
          }}
        ]
      }},
      options: {{
        responsive: true,
        plugins: {{
          title: {{ display: true, text: 'Cumulative Keep vs Discard', font: {{ size: 14 }} }},
        }},
        scales: {{
          x: {{ grid: {{ display: false }} }},
          y: {{ grid: {{ color: 'rgba(48,54,61,0.5)' }}, beginAtZero: true }}
        }}
      }}
    }});
  }}
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
