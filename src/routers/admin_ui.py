# src/routers/admin_ui.py
from __future__ import annotations

from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from jinja2 import Template
from fastapi.responses import HTMLResponse
from fastapi import Request, APIRouter

TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter(prefix="/admin", tags=["admin-ui"])

# --- DEMO: preview AI reply + feedback bar ---

router = APIRouter()
TEMPLATE_PATH = Path("src/templates/admin/ai_reply.html")

@router.get("/admin/demo/ai", response_class=HTMLResponse)
async def admin_ai_demo(request: Request):
    html = TEMPLATE_PATH.read_text(encoding="utf-8")
    t = Template(html)
    return t.render(
        request=request,
        trace_id="demo_" + "123456",
        explain={"reason": "short_answer", "confidence": 0.82},
        ai_text="<p>Hi CEO — this is a demo AI reply with <b>reason</b> & <i>confidence</i>.</p>",
    )

@router.get("/ui/bonus", name="bonus_ui")
async def bonus_ui(request: Request):
    return templates.TemplateResponse("admin/bonus_ui.html", {"request":request})

@router.get("/ui", response_class=HTMLResponse)
async def admin_ui() -> HTMLResponse:
    html = r"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>DigniLife · Admin Latency</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    :root {
      --bg: #0f172a;        /* slate-900 */
      --card:#111827;       /* gray-900 */
      --text:#e5e7eb;       /* gray-200 */
      --muted:#94a3b8;      /* slate-400 */
      --ok:#10b981;         /* emerald-500 */
      --warn:#f59e0b;       /* amber-500 */
      --bad:#ef4444;        /* red-500 */
      --chip:#1f2937;       /* gray-800 */
      --accent:#22d3ee;     /* cyan-400 */
    }
    *{box-sizing:border-box}
    body{
      margin:0; padding:24px;
      background:linear-gradient(180deg,#0b1220 0%, #0f172a 100%);
      color:var(--text); font:14px/1.45 ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, "Helvetica Neue", Arial;
    }
    h1{font-size:22px; margin:0 0 4px;}
    .muted{color:var(--muted)}
    .wrap{max-width:1100px; margin:0 auto; display:grid; gap:16px;}
    .row{display:grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap:12px}
    .card{
      background:var(--card); border:1px solid #1f2937; border-radius:14px; padding:16px;
      box-shadow:0 8px 24px rgba(0,0,0,.25);
    }
    .k{font-size:12px; color:var(--muted)}
    .v{font-size:28px; font-weight:700}
    .pill{display:inline-flex; gap:6px; align-items:center; background:var(--chip); padding:6px 10px; border-radius:999px; font-size:12px}
    .ok{color:var(--ok)} .warn{color:var(--warn)} .bad{color:var(--bad)}
    .toolbar{display:flex; gap:8px; align-items:center; justify-content:space-between}
    button{
      background:#0ea5e9; color:#001018; border:0; padding:8px 12px; border-radius:10px; font-weight:600; cursor:pointer;
    }
    button.ghost{background:#0b1220; color:var(--text); border:1px solid #1f2937}
    table{width:100%; border-collapse:collapse; font-size:12px}
    th, td{padding:8px 10px; border-bottom:1px solid #1f2937; text-align:left; white-space:nowrap}
    tr:hover{background:#0b1323}
    .grow{grid-column: span 2}
    @media (max-width:980px){ .row{grid-template-columns:1fr 1fr} .grow{grid-column: auto} }
    @media (max-width:560px){ .row{grid-template-columns:1fr} }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="toolbar">
      <div>
        <h1>Latency Monitor</h1>
        <div class="muted">Rolling window with p50/p90/p99, avg &amp; errors</div>
      </div>
      <div style="display:flex; gap:8px; align-items:center">
        <span class="pill"><span>Last updated:</span><b id="last-updated">—</b></span>
        <button id="btn-refresh" class="ghost">Refresh</button>
        <button id="btn-toggle" class="ghost">Pause</button>
        <button id="btn-reset">Reset window</button>
      </div>
    </div>

    <div class="row">
      <div class="card">
        <div class="k">p50</div>
        <div class="v" id="p50">—</div>
        <div class="k">ms</div>
      </div>
      <div class="card">
        <div class="k">p90</div>
        <div class="v" id="p90">—</div>
        <div class="k">ms</div>
      </div>
      <div class="card">
        <div class="k">p99</div>
        <div class="v" id="p99">—</div>
        <div class="k">ms</div>
      </div>
      <div class="card">
        <div class="k">Average</div>
        <div class="v" id="avg">—</div>
        <div class="k">ms</div>
      </div>
    </div>

    <div class="row">
      <div class="card">
        <div class="k">Count</div>
        <div class="v" id="count">—</div>
      </div>
      <div class="card">
        <div class="k">Error rate</div>
        <div class="v" id="error_rate">—</div>
      </div>
      <div class="card">
        <div class="k">Window</div>
        <div class="v" id="window_ms">—</div>
        <div class="k">ms</div>
      </div>
      <div class="card">
        <div class="k">Circuit</div>
        <div class="v" id="warn_flag">—</div>
        <div class="k muted">warn if p99 or error rate crosses threshold</div>
      </div>
    </div>

    <div class="card grow">
      <div class="toolbar" style="margin-bottom:8px">
        <strong>Recent requests</strong>
        <span class="muted">latest 50 rows</span>
      </div>
      <div style="overflow:auto; max-height:380px; border:1px solid #1f2937; border-radius:10px">
        <table>
          <thead>
            <tr>
              <th>ts</th>
              <th>ms</th>
              <th>error</th>
              <th>path</th>
            </tr>
          </thead>
          <tbody id="rows">
            <tr><td colspan="4" class="muted">Loading…</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>

<script>
const $ = (id) => document.getElementById(id);
let timer = null;
let paused = false;

function fmtMs(v){ return (v ?? 0).toFixed(1); }
function fmtRate(v){ return ((v ?? 0)*100).toFixed(2) + '%'; }
function fmtTs(ts){
  try { return new Date((ts ?? 0)*1000).toLocaleTimeString(); } catch { return '—'; }
}

async function fetchJSON(url, opts={}){
  const res = await fetch(url, opts);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return await res.json();
}

async function loadStats(){
  try{
    const j = await fetchJSON('/admin/latency');
    const s = j.stats || {};
    $('p50').textContent = fmtMs(s.p50);
    $('p90').textContent = fmtMs(s.p90);
    $('p99').textContent = fmtMs(s.p99);
    $('avg').textContent = fmtMs(s.avg);
    $('count').textContent = s.count ?? 0;
    $('error_rate').textContent = fmtRate(s.error_rate);
    $('window_ms').textContent = s.window_ms ?? '—';

    const warn = (s.warn_threshold_ms && s.p99 >= s.warn_threshold_ms) || (s.max_error_rate && s.error_rate >= s.max_error_rate);
    $('warn_flag').textContent = warn ? 'WARN' : 'OK';
    $('warn_flag').className = 'v ' + (warn ? 'warn' : 'ok');

    $('last-updated').textContent = new Date().toLocaleTimeString();
  }catch(e){
    $('last-updated').textContent = 'error';
    console.error(e);
  }
}

async function loadRows(){
  try{
    const j = await fetchJSON('/admin/latency/history?limit=50');
    const rows = j.rows || [];
    const tb = $('rows');
    tb.innerHTML = '';
    if(!rows.length){
      tb.innerHTML = '<tr><td colspan="4" class="muted">No rows in window</td></tr>';
      return;
    }
    for (const r of rows){
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td class="muted">${fmtTs(r.ts)}</td>
        <td>${fmtMs(r.ms)}</td>
        <td class="${r.error ? 'bad' : 'ok'}">${r.error ? 'true' : 'false'}</td>
        <td class="muted">${r.path || ''}</td>`;
      tb.appendChild(tr);
    }
  }catch(e){
    console.error(e);
  }
}

async function resetWindow(){
  try{
    await fetchJSON('/admin/latency/reset', { method: 'POST' });
    await Promise.all([loadStats(), loadRows()]);
  }catch(e){ console.error(e); }
}

function refreshAll(){ if (!paused){ loadStats(); loadRows(); } }

$('btn-refresh').addEventListener('click', refreshAll);
$('btn-reset').addEventListener('click', resetWindow);
$('btn-toggle').addEventListener('click', () => {
  paused = !paused;
  $('btn-toggle').textContent = paused ? 'Resume' : 'Pause';
});

(async function init(){
  await refreshAll();
  timer = setInterval(refreshAll, 5000); // auto-refresh every 5s
})();
</script>
</body>
</html>
    """
    return HTMLResponse(content=html)
