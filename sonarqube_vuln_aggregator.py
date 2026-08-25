#!/usr/bin/env python3
"""
SonarQube Vulnerability Aggregator (Community Edition friendly)

Pulls VULNERABILITY-type issues from every project on a SonarQube server
and rolls them into:
  1. A single CSV file (one row per vulnerability, across all projects)
  2. A single self-contained HTML dashboard (charts + filterable/sortable table)

Usage:
    export SONAR_URL="http://localhost:9000"
    export SONAR_TOKEN="squ_xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    python3 sonarqube_vuln_aggregator.py --output-dir ./sonar_report

Requirements:
    pip install requests --break-system-packages

Auth token setup:
    SonarQube UI -> My Account -> Security -> Generate Token
    The token's user needs "Browse" permission on every project you want
    included (or use a global admin/service-account token).
"""

import os
import sys
import csv
import json
import argparse
import requests
from datetime import datetime

PAGE_SIZE = 500  # SonarQube max page size for issues/search


def get_session(token):
    s = requests.Session()
    s.auth = (token, "")  # SonarQube: token as username, blank password
    return s


def get_all_projects(session, base_url):
    """Return list of {key, name} for every project visible to the token."""
    projects = []
    page = 1
    while True:
        resp = session.get(
            f"{base_url}/api/projects/search",
            params={"p": page, "ps": PAGE_SIZE},
        )
        resp.raise_for_status()
        data = resp.json()
        for c in data.get("components", []):
            projects.append({"key": c["key"], "name": c.get("name", c["key"])})
        total = data.get("paging", {}).get("total", 0)
        if page * PAGE_SIZE >= total:
            break
        page += 1
    return projects


def get_vulnerabilities_for_project(session, base_url, project_key):
    """Return list of vulnerability issue dicts for a single project (paginated)."""
    issues = []
    page = 1
    while True:
        resp = session.get(
            f"{base_url}/api/issues/search",
            params={
                "componentKeys": project_key,
                "types": "VULNERABILITY",
                "statuses": "OPEN,CONFIRMED,REOPENED",  # exclude resolved/closed
                "p": page,
                "ps": PAGE_SIZE,
            },
        )
        if resp.status_code == 404:
            # project may have been deleted mid-run
            break
        resp.raise_for_status()
        data = resp.json()
        issues.extend(data.get("issues", []))
        total = data.get("paging", {}).get("total", 0)
        if page * PAGE_SIZE >= total or page * PAGE_SIZE >= 10000:
            # SonarQube search API caps at 10,000 results regardless of ps/p
            if page * PAGE_SIZE >= 10000 and total > 10000:
                print(
                    f"  WARNING: {project_key} has >10000 vulnerabilities; "
                    f"only first 10000 captured. Narrow with severity/date filters."
                )
            break
        page += 1
    return issues


def flatten_issue(project_key, project_name, base_url, issue):
    return {
        "project_key": project_key,
        "project_name": project_name,
        "rule": issue.get("rule", ""),
        "severity": issue.get("severity", ""),
        "message": issue.get("message", ""),
        "component": issue.get("component", ""),
        "line": issue.get("line", ""),
        "status": issue.get("status", ""),
        "creation_date": issue.get("creationDate", ""),
        "update_date": issue.get("updateDate", ""),
        "issue_key": issue.get("key", ""),
        "link": f"{base_url}/project/issues?id={project_key}&issues={issue.get('key','')}&open={issue.get('key','')}",
    }


def write_csv(rows, path):
    fieldnames = [
        "project_key", "project_name", "rule", "severity", "message",
        "component", "line", "status", "creation_date", "update_date",
        "issue_key", "link",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>SonarQube Vulnerability Report — {generated}</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>
<style>
  :root {{
    --bg: #0f1420; --panel: #171e2e; --border: #2a3448; --text: #e6e9ef;
    --muted: #8b93a7; --blocker: #d1394f; --critical: #e2622c;
    --major: #e0a72e; --minor: #4c8dd6; --info: #6b7280;
  }}
  * {{ box-sizing: border-box; }}
  body {{ margin:0; font-family: -apple-system, Segoe UI, Roboto, sans-serif; background:var(--bg); color:var(--text); }}
  header {{ padding: 24px 32px; border-bottom: 1px solid var(--border); }}
  header h1 {{ margin: 0 0 4px; font-size: 20px; }}
  header p {{ margin:0; color: var(--muted); font-size: 13px; }}
  .wrap {{ padding: 24px 32px; }}
  .cards {{ display:flex; gap:16px; flex-wrap:wrap; margin-bottom:24px; }}
  .card {{ background:var(--panel); border:1px solid var(--border); border-radius:10px; padding:16px 20px; min-width:140px; }}
  .card .n {{ font-size:26px; font-weight:700; }}
  .card .l {{ font-size:12px; color:var(--muted); text-transform:uppercase; letter-spacing:.04em; }}
  .charts {{ display:grid; grid-template-columns: 1fr 1fr; gap:16px; margin-bottom:24px; }}
  .chart-box {{ background:var(--panel); border:1px solid var(--border); border-radius:10px; padding:16px; }}
  .chart-box h3 {{ margin:0 0 12px; font-size:13px; color:var(--muted); font-weight:600; text-transform:uppercase; letter-spacing:.04em; }}
  .controls {{ display:flex; gap:10px; margin-bottom:12px; flex-wrap:wrap; }}
  select, input {{ background:var(--panel); border:1px solid var(--border); color:var(--text); padding:8px 10px; border-radius:6px; font-size:13px; }}
  table {{ width:100%; border-collapse:collapse; background:var(--panel); border:1px solid var(--border); border-radius:10px; overflow:hidden; font-size:13px; }}
  th, td {{ text-align:left; padding:10px 12px; border-bottom:1px solid var(--border); }}
  th {{ cursor:pointer; color:var(--muted); text-transform:uppercase; font-size:11px; letter-spacing:.03em; user-select:none; }}
  th:hover {{ color:var(--text); }}
  tr:hover td {{ background:#1c2436; }}
  .badge {{ padding:2px 8px; border-radius:20px; font-size:11px; font-weight:600; }}
  .BLOCKER {{ background: var(--blocker); }}
  .CRITICAL {{ background: var(--critical); }}
  .MAJOR {{ background: var(--major); color:#1a1a1a; }}
  .MINOR {{ background: var(--minor); }}
  .INFO {{ background: var(--info); }}
  a {{ color: #7db8ff; text-decoration:none; }}
  a:hover {{ text-decoration:underline; }}
</style>
</head>
<body>
<header>
  <h1>SonarQube Vulnerability Report</h1>
  <p>Aggregated across {project_count} projects · Generated {generated}</p>
</header>
<div class="wrap">
  <div class="cards" id="summaryCards"></div>
  <div class="charts">
    <div class="chart-box"><h3>By severity</h3><canvas id="severityChart"></canvas></div>
    <div class="chart-box"><h3>By project (top 10)</h3><canvas id="projectChart"></canvas></div>
  </div>
  <div class="controls">
    <input id="search" type="text" placeholder="Search message, component, project...">
    <select id="severityFilter"><option value="">All severities</option></select>
    <select id="projectFilter"><option value="">All projects</option></select>
  </div>
  <table id="issuesTable">
    <thead>
      <tr>
        <th data-key="severity">Severity</th>
        <th data-key="project_name">Project</th>
        <th data-key="rule">Rule</th>
        <th data-key="message">Message</th>
        <th data-key="component">Component</th>
        <th data-key="line">Line</th>
        <th data-key="creation_date">Created</th>
        <th>Link</th>
      </tr>
    </thead>
    <tbody id="tbody"></tbody>
  </table>
</div>

<script>
const DATA = {data_json};

const sevOrder = {{BLOCKER:0, CRITICAL:1, MAJOR:2, MINOR:3, INFO:4}};
let filtered = [...DATA];
let sortKey = "severity", sortAsc = true;

function renderCards() {{
  const counts = {{}};
  DATA.forEach(d => counts[d.severity] = (counts[d.severity]||0)+1);
  const total = DATA.length;
  const projects = new Set(DATA.map(d => d.project_key)).size;
  const html = [
    `<div class="card"><div class="n">${{total}}</div><div class="l">Total vulnerabilities</div></div>`,
    `<div class="card"><div class="n">${{projects}}</div><div class="l">Projects affected</div></div>`,
  ];
  Object.keys(sevOrder).forEach(s => {{
    if (counts[s]) html.push(`<div class="card"><div class="n">${{counts[s]}}</div><div class="l">${{s}}</div></div>`);
  }});
  document.getElementById('summaryCards').innerHTML = html.join('');
}}

function renderCharts() {{
  const sevCounts = {{}};
  DATA.forEach(d => sevCounts[d.severity] = (sevCounts[d.severity]||0)+1);
  const sevLabels = Object.keys(sevOrder).filter(s => sevCounts[s]);
  const sevColors = {{BLOCKER:'#d1394f', CRITICAL:'#e2622c', MAJOR:'#e0a72e', MINOR:'#4c8dd6', INFO:'#6b7280'}};
  new Chart(document.getElementById('severityChart'), {{
    type: 'doughnut',
    data: {{ labels: sevLabels, datasets: [{{ data: sevLabels.map(s=>sevCounts[s]), backgroundColor: sevLabels.map(s=>sevColors[s]) }}] }},
    options: {{ plugins: {{ legend: {{ labels: {{ color: '#e6e9ef' }} }} }} }}
  }});

  const byProject = {{}};
  DATA.forEach(d => byProject[d.project_name] = (byProject[d.project_name]||0)+1);
  const topProjects = Object.entries(byProject).sort((a,b)=>b[1]-a[1]).slice(0,10);
  new Chart(document.getElementById('projectChart'), {{
    type: 'bar',
    data: {{ labels: topProjects.map(p=>p[0]), datasets: [{{ label:'Vulnerabilities', data: topProjects.map(p=>p[1]), backgroundColor:'#4c8dd6' }}] }},
    options: {{
      indexAxis: 'y',
      plugins: {{ legend: {{ display:false }} }},
      scales: {{ x: {{ ticks: {{ color:'#8b93a7' }}, grid: {{ color:'#2a3448' }} }}, y: {{ ticks: {{ color:'#e6e9ef' }}, grid: {{ display:false }} }} }}
    }}
  }});
}}

function populateFilters() {{
  const sevSel = document.getElementById('severityFilter');
  Object.keys(sevOrder).forEach(s => {{
    const o = document.createElement('option'); o.value = s; o.textContent = s; sevSel.appendChild(o);
  }});
  const projSel = document.getElementById('projectFilter');
  [...new Set(DATA.map(d=>d.project_name))].sort().forEach(p => {{
    const o = document.createElement('option'); o.value = p; o.textContent = p; projSel.appendChild(o);
  }});
}}

function applyFilters() {{
  const q = document.getElementById('search').value.toLowerCase();
  const sev = document.getElementById('severityFilter').value;
  const proj = document.getElementById('projectFilter').value;
  filtered = DATA.filter(d => {{
    if (sev && d.severity !== sev) return false;
    if (proj && d.project_name !== proj) return false;
    if (q) {{
      const hay = (d.message + d.component + d.project_name + d.rule).toLowerCase();
      if (!hay.includes(q)) return false;
    }}
    return true;
  }});
  sortAndRender();
}}

function sortAndRender() {{
  filtered.sort((a,b) => {{
    let va = a[sortKey], vb = b[sortKey];
    if (sortKey === 'severity') {{ va = sevOrder[va]; vb = sevOrder[vb]; }}
    if (va < vb) return sortAsc ? -1 : 1;
    if (va > vb) return sortAsc ? 1 : -1;
    return 0;
  }});
  const rows = filtered.map(d => `
    <tr>
      <td><span class="badge ${{d.severity}}">${{d.severity}}</span></td>
      <td>${{d.project_name}}</td>
      <td>${{d.rule}}</td>
      <td>${{d.message}}</td>
      <td>${{d.component.split(':').pop()}}</td>
      <td>${{d.line || ''}}</td>
      <td>${{(d.creation_date||'').split('T')[0]}}</td>
      <td><a href="${{d.link}}" target="_blank">Open ↗</a></td>
    </tr>`).join('');
  document.getElementById('tbody').innerHTML = rows;
}}

document.querySelectorAll('th[data-key]').forEach(th => {{
  th.addEventListener('click', () => {{
    const key = th.dataset.key;
    if (sortKey === key) sortAsc = !sortAsc; else {{ sortKey = key; sortAsc = true; }}
    sortAndRender();
  }});
}});
document.getElementById('search').addEventListener('input', applyFilters);
document.getElementById('severityFilter').addEventListener('change', applyFilters);
document.getElementById('projectFilter').addEventListener('change', applyFilters);

renderCards();
renderCharts();
populateFilters();
sortAndRender();
</script>
</body>
</html>
"""


def write_html(rows, path, project_count):
    html = HTML_TEMPLATE.format(
        generated=datetime.now().strftime("%Y-%m-%d %H:%M"),
        project_count=project_count,
        data_json=json.dumps(rows),
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)


def main():
    parser = argparse.ArgumentParser(description="Aggregate SonarQube vulnerabilities across all projects.")
    parser.add_argument("--url", default=os.environ.get("SONAR_URL"), help="SonarQube base URL, e.g. http://localhost:9000")
    parser.add_argument("--token", default=os.environ.get("SONAR_TOKEN"), help="SonarQube user token")
    parser.add_argument("--output-dir", default="./sonar_vuln_report", help="Directory to write CSV + HTML into")
    parser.add_argument("--project-key", default=None, help="If set, report on just this one project instead of all projects")
    args = parser.parse_args()

    if not args.url or not args.token:
        sys.exit("ERROR: set SONAR_URL and SONAR_TOKEN (env vars or --url/--token flags).")

    base_url = args.url.rstrip("/")
    os.makedirs(args.output_dir, exist_ok=True)

    session = get_session(args.token)

    if args.project_key:
        print(f"Fetching single project: {args.project_key}")
        projects = [{"key": args.project_key, "name": args.project_key}]
    else:
        print(f"Fetching project list from {base_url} ...")
        projects = get_all_projects(session, base_url)
        print(f"Found {len(projects)} projects.")

    all_rows = []
    for i, proj in enumerate(projects, 1):
        print(f"[{i}/{len(projects)}] {proj['key']}")
        issues = get_vulnerabilities_for_project(session, base_url, proj["key"])
        for issue in issues:
            all_rows.append(flatten_issue(proj["key"], proj["name"], base_url, issue))

    csv_path = os.path.join(args.output_dir, "vulnerabilities.csv")
    html_path = os.path.join(args.output_dir, "vulnerabilities.html")
    write_csv(all_rows, csv_path)
    write_html(all_rows, html_path, len(projects))

    print(f"\nDone. {len(all_rows)} open vulnerabilities across {len(projects)} projects.")
    print(f"CSV:  {csv_path}")
    print(f"HTML: {html_path}")


if __name__ == "__main__":
    main()
