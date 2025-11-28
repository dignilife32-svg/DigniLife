#src/routers/playground.py
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["playground"])

@router.get("/playground", response_class=HTMLResponse)
async def playground(request: Request):
    html = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<title>DigniLife Chat Playground</title>
<meta name="viewport" content="width=device-width, initial-scale=1" />
<style>
body { font-family: system-ui; background: #0b1226; color: #eee; margin: 0; }
header { padding: 14px; background: #162a44; }
input, button { font-size: 15px; }
#wrap { padding: 12px; max-width: 860px; margin: 0 auto; }
#log { height: 60vh; overflow-y: auto; background: #131c33; padding: 10px; border-radius: 10px; }
.bubble { margin: 6px 0; padding: 10px; border-radius: 10px; max-width: 80%; }
.user { background: #253b8a; align-self: flex-end; color: #fff; }
.ai { background: #2a2e39; color: #eee; }
.row { display: flex; gap: 8px; margin-top: 10px; }
button { background: #3478f6; color: white; border: 0; border-radius: 8px; padding: 10px 14px; cursor: pointer; }
button:hover { background: #2a63c8; }
</style>
</head>
<body>
<header><strong>DigniLife Chat Playground</strong> <small>(local)</small></header>
<div id="wrap">
  <div id="log"></div>
  <div class="row">
    <input id="q" placeholder="Type your question..." style="flex:1; padding:10px; border-radius:8px; border:0;" />
    <button id="send">Send</button>
  </div>
</div>

<script>
function add(role, text) {
  const log = document.getElementById('log');
  const div = document.createElement('div');
  div.className = 'bubble ' + role;
  div.textContent = text;
  log.appendChild(div);
  log.scrollTop = log.scrollHeight;
}

async function send() {
  const api = '/v1/chat';
  const qEl = document.getElementById('q');
  const q = qEl.value.trim();
  if (!q) return;

  add('user', q);
  qEl.value = '';

  try {
    const body = {
      model: 'qwen2.5-7b-instruct',
      messages: [{ role: 'user', content: q }]
    };

    const res = await fetch(api, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });

    const data = await res.json();

    if (res.ok) {
      const msg = (data?.choices?.[0]?.message?.content)
        || data?.reply
        || data?.detail
        || "(no content)";
      add('ai', msg);
    } else {
      const err = (data && (data.detail || data.message)) || res.statusText || 'request failed';
      add('ai', 'Error: ' + err);
    }
  } catch (e) {
    add('ai', 'Network Error: ' + e.message);
  }
}

document.getElementById('send').onclick = send;
document.getElementById('q').addEventListener('keydown', (e) => {
  if (e.key === 'Enter') send();
});
</script>
</body>
</html>
"""
    return HTMLResponse(html)
