"""
╔══════════════════════════════════════════════════════════════╗
║     GRAVITY AI BRIDGE V9.0 PRO [Diamond-Tier Edition] — DASHBOARD WEB CON CHAT          ║
║     SPA interactiva: Estado + Chat + Gestión de modelos       ║
╚══════════════════════════════════════════════════════════════╝
Servidor Flask-less: HTTP puro para cero dependencias extra.
Sirve dashboard.html en / con chat streaming via /v1/chat/stream
"""
import json
import os
import sys
import time
import uuid
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import urllib.parse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Gravity AI — Dashboard</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root {
    --bg:       #090c10;
    --surface:  #0f1117;
    --card:     #161b22;
    --border:   #21262d;
    --accent:   #4f46e5;
    --accent2:  #7c3aed;
    --glow:     rgba(79,70,229,0.35);
    --text:     #e6edf3;
    --muted:    #8b949e;
    --success:  #3fb950;
    --warning:  #f0883e;
    --error:    #f85149;
    --user-bg:  #1c2128;
    --ai-bg:    #13131a;
  }
  *{box-sizing:border-box;margin:0;padding:0}
  html,body{height:100%;background:var(--bg);color:var(--text);font-family:'Inter',sans-serif;overflow:hidden}

  /* ── Layout Principal ── */
  .shell{display:grid;grid-template-columns:260px 1fr;grid-template-rows:56px 1fr;height:100vh;gap:0}
  .topbar{grid-column:1/-1;background:var(--surface);border-bottom:1px solid var(--border);
          display:flex;align-items:center;padding:0 20px;gap:16px;z-index:10}
  .sidebar{background:var(--surface);border-right:1px solid var(--border);
           display:flex;flex-direction:column;padding:16px 0;overflow-y:auto}
  .main{display:flex;flex-direction:column;overflow:hidden}

  /* ── Topbar ── */
  .logo{font-size:18px;font-weight:800;letter-spacing:-0.5px;
        background:linear-gradient(90deg,#818cf8,#c084fc);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
  .badge-online{background:rgba(63,185,80,0.15);border:1px solid rgba(63,185,80,0.3);
                color:var(--success);padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;
                display:flex;align-items:center;gap:5px}
  .dot{width:7px;height:7px;border-radius:50%;background:var(--success);
       box-shadow:0 0 6px var(--success);animation:blink 2s infinite}
  @keyframes blink{0%,100%{opacity:.6}50%{opacity:1}}
  .topbar-model{margin-left:auto;font-size:12px;color:var(--muted)}
  .topbar-model strong{color:var(--text);font-weight:600}
  .btn-icon{background:none;border:1px solid var(--border);color:var(--muted);
            padding:6px 12px;border-radius:6px;cursor:pointer;font-size:12px;font-family:'Inter',sans-serif;
            transition:.2s;margin-left:8px}
  .btn-icon:hover{border-color:var(--accent);color:var(--text)}

  /* ── Sidebar ── */
  .sidebar-section{padding:0 12px;margin-bottom:8px}
  .sidebar-label{font-size:10px;text-transform:uppercase;letter-spacing:1px;color:var(--muted);
                  padding:8px 8px 4px;font-weight:600}
  .nav-item{display:flex;align-items:center;gap:10px;padding:8px 10px;border-radius:8px;
            cursor:pointer;font-size:13px;color:var(--muted);transition:.15s;margin-bottom:2px}
  .nav-item:hover,.nav-item.active{background:rgba(79,70,229,0.12);color:var(--text)}
  .nav-item.active{border-left:2px solid var(--accent);padding-left:8px}
  .nav-icon{font-size:15px;width:20px;text-align:center}
  .model-card{background:var(--card);border:1px solid var(--border);border-radius:10px;
              margin:0 12px 8px;padding:12px}
  .model-name{font-size:12px;font-weight:600;color:var(--text);margin-bottom:4px;
              white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .model-meta{font-size:11px;color:var(--muted)}
  .provider-status{display:flex;align-items:center;gap:6px;font-size:11px;color:var(--muted);
                   padding:6px 10px;margin:0 12px 2px;border-radius:6px}
  .provider-status .dot-sm{width:6px;height:6px;border-radius:50%;flex-shrink:0}
  .dot-online{background:var(--success)}
  .dot-offline{background:var(--error)}

  /* ── Tabs ── */
  .tabs{display:flex;border-bottom:1px solid var(--border);padding:0 20px;background:var(--surface)}
  .tab{padding:12px 16px;font-size:13px;cursor:pointer;color:var(--muted);border-bottom:2px solid transparent;
       transition:.15s;margin-bottom:-1px}
  .tab:hover{color:var(--text)}
  .tab.active{color:var(--accent);border-bottom-color:var(--accent);font-weight:600}

  /* ── Panel de Chat ── */
  #tab-chat{flex:1;display:flex;flex-direction:column;overflow:hidden}
  .chat-messages{flex:1;overflow-y:auto;padding:24px 20px;display:flex;flex-direction:column;gap:16px}
  .chat-messages::-webkit-scrollbar{width:5px}
  .chat-messages::-webkit-scrollbar-track{background:transparent}
  .chat-messages::-webkit-scrollbar-thumb{background:var(--border);border-radius:3px}
  .msg{display:flex;flex-direction:column;gap:6px;max-width:85%;animation:msgIn .2s ease}
  @keyframes msgIn{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
  .msg.user{align-self:flex-end}
  .msg.ai{align-self:flex-start}
  .msg-bubble{padding:12px 16px;border-radius:12px;line-height:1.65;font-size:14px;white-space:pre-wrap;word-break:break-word}
  .msg.user .msg-bubble{background:var(--user-bg);border:1px solid var(--border);border-bottom-right-radius:3px}
  .msg.ai .msg-bubble{background:var(--ai-bg);border:1px solid var(--border);border-bottom-left-radius:3px}
  .msg-meta{font-size:11px;color:var(--muted)}
  .msg.user .msg-meta{text-align:right}
  .code-block{background:#0d1117;border:1px solid var(--border);border-radius:8px;
              font-family:'JetBrains Mono',monospace;font-size:12px;padding:12px;
              overflow-x:auto;margin:8px 0;white-space:pre}
  .cursor-blink{display:inline-block;width:2px;height:14px;background:var(--accent);
                margin-left:1px;animation:cur .7s infinite;vertical-align:text-bottom}
  @keyframes cur{0%,100%{opacity:1}50%{opacity:0}}

  .chat-input-area{border-top:1px solid var(--border);padding:16px 20px;background:var(--surface)}
  .input-row{display:flex;gap:10px;align-items:flex-end}
  #chat-input{flex:1;background:var(--card);border:1px solid var(--border);color:var(--text);
              border-radius:10px;padding:12px 16px;font-size:14px;font-family:'Inter',sans-serif;
              resize:none;outline:none;max-height:200px;min-height:46px;line-height:1.5;
              transition:border-color .2s}
  #chat-input:focus{border-color:var(--accent)}
  #chat-input::placeholder{color:var(--muted)}
  #send-btn{background:linear-gradient(135deg,var(--accent),var(--accent2));border:none;color:#fff;
            width:42px;height:42px;border-radius:10px;cursor:pointer;font-size:18px;
            display:flex;align-items:center;justify-content:center;flex-shrink:0;transition:.2s}
  #send-btn:hover{opacity:.85;transform:scale(1.05)}
  #send-btn:disabled{opacity:.4;cursor:not-allowed;transform:none}
  .input-hints{font-size:11px;color:var(--muted);margin-top:8px;display:flex;gap:16px;flex-wrap:wrap}
  .hint{cursor:pointer;padding:3px 8px;border-radius:4px;border:1px solid var(--border);transition:.15s}
  .hint:hover{border-color:var(--accent);color:var(--text)}

  /* ── Panel de Estado ── */
  #tab-status{flex:1;overflow-y:auto;padding:20px}
  .stats-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px;margin-bottom:24px}
  .stat-card{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:20px;
             transition:.2s}
  .stat-card:hover{border-color:var(--accent);box-shadow:0 0 20px var(--glow);transform:translateY(-2px)}
  .stat-card .label{font-size:11px;text-transform:uppercase;letter-spacing:1px;color:var(--muted);margin-bottom:12px}
  .stat-card .value{font-size:22px;font-weight:700}
  .table-wrap{background:var(--card);border:1px solid var(--border);border-radius:12px;overflow:hidden;margin-bottom:20px}
  .table-title{padding:14px 18px;font-size:12px;text-transform:uppercase;letter-spacing:1px;
               color:var(--muted);border-bottom:1px solid var(--border)}
  table{width:100%;border-collapse:collapse}
  th{text-align:left;padding:10px 18px;font-size:11px;text-transform:uppercase;
     letter-spacing:.8px;color:var(--muted);border-bottom:1px solid var(--border)}
  td{padding:11px 18px;font-size:13px;border-bottom:1px solid var(--border)}
  tr:last-child td{border:none}
  .badge{padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600}
  .badge-cloud{background:rgba(167,139,250,.1);color:#a78bfa;border:1px solid rgba(167,139,250,.2)}
  .badge-local{background:rgba(96,165,250,.1);color:#60a5fa;border:1px solid rgba(96,165,250,.2)}
  .online{color:var(--success)}
  .offline{color:var(--error)}

  /* ── Panel de Audit ── */
  #tab-audit{flex:1;overflow-y:auto;padding:20px}

  /* ── Panel de Configuración ── */
  #tab-config{flex:1;overflow-y:auto;padding:20px}
  .config-section{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:20px;margin-bottom:16px}
  .config-section h3{font-size:13px;font-weight:600;margin-bottom:16px;color:var(--text)}
  .form-row{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px}
  .form-label{font-size:13px;color:var(--muted)}
  .form-input{background:var(--surface);border:1px solid var(--border);color:var(--text);
              padding:7px 12px;border-radius:6px;font-size:13px;font-family:'Inter',sans-serif;width:220px;outline:none}
  .form-input:focus{border-color:var(--accent)}
  .btn-primary{background:var(--accent);color:#fff;border:none;padding:9px 20px;
               border-radius:8px;cursor:pointer;font-size:13px;font-family:'Inter',sans-serif;font-weight:600;transition:.2s}
  .btn-primary:hover{opacity:.85}

  /* ── Responsive ── */
  @media(max-width:768px){
    .shell{grid-template-columns:1fr}
    .sidebar{display:none}
  }
  .hidden{display:none!important}
</style>
</head>
<body>
<div class="shell">
  <!-- Topbar -->
  <header class="topbar">
    <span class="logo">⚡ GRAVITY AI</span>
    <div class="badge-online"><div class="dot"></div>ONLINE</div>
    <span class="topbar-model" id="active-model-label">Cargando estado...</span>
    <button class="btn-icon" onclick="refreshStatus()">⟳ Actualizar</button>
    <button class="btn-icon" onclick="clearChat()">🗑 Limpiar Chat</button>
  </header>

  <!-- Sidebar -->
  <aside class="sidebar">
    <div class="sidebar-section">
      <div class="sidebar-label">Menú</div>
      <div class="nav-item active" onclick="switchTab('chat',this)"><span class="nav-icon">💬</span>Chat</div>
      <div class="nav-item" onclick="switchTab('status',this)"><span class="nav-icon">📡</span>Estado del Sistema</div>
      <div class="nav-item" onclick="switchTab('audit',this)"><span class="nav-icon">📋</span>Audit Log</div>
      <div class="nav-item" onclick="switchTab('config',this)"><span class="nav-icon">⚙️</span>Configuración</div>
    </div>

    <div class="sidebar-section" style="margin-top:auto">
      <div class="sidebar-label">Modelo Activo</div>
      <div class="model-card">
        <div class="model-name" id="sidebar-model">Detectando...</div>
        <div class="model-meta" id="sidebar-provider">Proveedor: --</div>
      </div>
      <div class="sidebar-label" style="margin-top:8px">Proveedores</div>
      <div id="provider-list"></div>
    </div>
  </aside>

  <!-- Main -->
  <main class="main">
    <div class="tabs">
      <div class="tab active" id="tab-btn-chat" onclick="switchTab('chat',this)">💬 Chat</div>
      <div class="tab" id="tab-btn-status" onclick="switchTab('status',this)">📡 Estado</div>
      <div class="tab" id="tab-btn-audit" onclick="switchTab('audit',this)">📋 Audit Log</div>
      <div class="tab" id="tab-btn-config" onclick="switchTab('config',this)">⚙️ Config</div>
    </div>

    <!-- Tab Chat -->
    <div id="tab-chat" style="flex:1;display:flex;flex-direction:column;overflow:hidden">
      <div class="chat-messages" id="messages">
        <div class="msg ai">
          <div class="msg-bubble">
            <strong>👋 Bienvenido a Gravity AI Bridge V9.0 PRO [Diamond-Tier Edition]</strong><br><br>
            Puedo analizar código, responder preguntas técnicas, buscar en la web o ejecutar herramientas.<br><br>
            <strong>Atajos disponibles:</strong><br>
            &nbsp;• <code>/keys set openai</code> — configurar API keys<br>
            &nbsp;• <code>/verify archivo.py</code> — auditar código<br>
            &nbsp;• <code>!aprende &lt;regla&gt;</code> — persistir conocimiento<br>
            &nbsp;• <code>/search &lt;término&gt;</code> — búsqueda web en vivo
          </div>
          <span class="msg-meta">Sistema</span>
        </div>
      </div>
      <div class="chat-input-area">
        <div class="input-row">
          <textarea id="chat-input" placeholder="Escribe tu mensaje... (Enter para enviar, Shift+Enter para nueva línea)" rows="1" onkeydown="handleKey(event)" oninput="autoResize(this)"></textarea>
          <button id="send-btn" onclick="sendMessage()" title="Enviar (Enter)">➤</button>
        </div>
        <div class="input-hints">
          <span class="hint" onclick="injectHint('/search ')">🔍 Buscar web</span>
          <span class="hint" onclick="injectHint('/verify ')">🔬 Verificar</span>
          <span class="hint" onclick="injectHint('!aprende ')">🧠 Aprender</span>
          <span class="hint" onclick="injectHint('/keys list')">🔑 Ver claves</span>
          <span class="hint" onclick="injectHint('/cost')">💰 Costes</span>
        </div>
      </div>
    </div>

    <!-- Tab Status -->
    <div id="tab-status" class="hidden" style="flex:1;overflow-y:auto;padding:20px">
      <div class="stats-grid" id="stats-grid">
        <div class="stat-card"><div class="label">Estado</div><div class="value" style="color:var(--success)">ONLINE</div></div>
        <div class="stat-card"><div class="label">Proveedor Activo</div><div class="value" id="stat-provider" style="font-size:15px">--</div></div>
        <div class="stat-card"><div class="label">Modelo Activo</div><div class="value" id="stat-model" style="font-size:13px">--</div></div>
        <div class="stat-card"><div class="label">Backends Online</div><div class="value" id="stat-backends">--</div></div>
      </div>
      <div class="table-wrap">
        <div class="table-title">Motores de IA detectados</div>
        <table><thead><tr><th>Proveedor</th><th>Tipo</th><th>Estado</th><th>Latencia</th><th>Modelos</th></tr></thead>
        <tbody id="providers-table"></tbody></table>
      </div>
    </div>

    <!-- Tab Audit -->
    <div id="tab-audit" class="hidden" style="flex:1;overflow-y:auto;padding:20px">
      <div class="table-wrap">
        <div class="table-title">Audit Log — Últimas inferencias</div>
        <table><thead><tr><th>Timestamp</th><th>Proveedor / Modelo</th><th>Tokens ↓↑</th><th>Latencia</th><th>Coste USD</th></tr></thead>
        <tbody id="audit-table"></tbody></table>
      </div>
    </div>

    <!-- Tab Config -->
    <div id="tab-config" class="hidden" style="flex:1;overflow-y:auto;padding:20px">
      <div class="config-section">
        <h3>🔑 API Keys de Proveedores Cloud</h3>
        <div class="form-row">
          <span class="form-label">Proveedor</span>
          <input type="text" id="cfg-provider" class="form-input" placeholder="openai / anthropic / groq...">
        </div>
        <div class="form-row">
          <span class="form-label">API Key</span>
          <input type="password" id="cfg-key" class="form-input" placeholder="sk-...">
        </div>
        <button class="btn-primary" onclick="saveKey()">Guardar Key Cifrada</button>
      </div>
      <div class="config-section">
        <h3>📡 Observabilidad</h3>
        <div class="form-row">
          <span class="form-label">Métricas Prometheus</span>
          <a href="/metrics" target="_blank" style="color:var(--accent)">/metrics</a>
        </div>
        <div class="form-row">
          <span class="form-label">Audit JSON completo</span>
          <a href="/v1/audit" target="_blank" style="color:var(--accent)">/v1/audit</a>
        </div>
        <div class="form-row">
          <span class="form-label">Estado del bridge</span>
          <a href="/v1/status" target="_blank" style="color:var(--accent)">/v1/status</a>
        </div>
      </div>
    </div>
  </main>
</div>

<script>
const API = '';
let currentTab = 'chat';
let chatHistory = [];
let isStreaming = false;

// ── Tab navigation ─────────────────────────────────────────────────────────
function switchTab(name, el) {
  ['chat','status','audit','config'].forEach(t => {
    document.getElementById('tab-'+t)?.classList.add('hidden');
    document.getElementById('tab-btn-'+t)?.classList.remove('active');
  });
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.getElementById('tab-'+name)?.classList.remove('hidden');
  document.getElementById('tab-btn-'+name)?.classList.add('active');
  if (el) el.classList.add('active');
  currentTab = name;
  if (name === 'status') refreshStatus();
  if (name === 'audit')  refreshAudit();
}

// ── Auto-resize textarea ───────────────────────────────────────────────────
function autoResize(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 200) + 'px';
}

function handleKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
}

function injectHint(text) {
  const inp = document.getElementById('chat-input');
  inp.value = text;
  inp.focus();
  autoResize(inp);
}

function clearChat() {
  chatHistory = [];
  document.getElementById('messages').innerHTML = '';
  addAIMessage('Chat limpiado. ¿En qué puedo ayudarte?');
}

// ── Chat ──────────────────────────────────────────────────────────────────
function addUserMessage(text) {
  const box = document.getElementById('messages');
  const ts = new Date().toLocaleTimeString('es', {hour:'2-digit',minute:'2-digit'});
  const el = document.createElement('div');
  el.className = 'msg user';
  el.innerHTML = `<div class="msg-bubble">${escHtml(text)}</div><span class="msg-meta">${ts}</span>`;
  box.appendChild(el);
  box.scrollTop = box.scrollHeight;
}

function addAIMessage(text) {
  const box = document.getElementById('messages');
  const ts = new Date().toLocaleTimeString('es', {hour:'2-digit',minute:'2-digit'});
  const el = document.createElement('div');
  el.className = 'msg ai';
  el.dataset.id = 'ai-' + Date.now();
  el.innerHTML = `<div class="msg-bubble">${formatMd(escHtml(text))}</div><span class="msg-meta">Auditor · ${ts}</span>`;
  box.appendChild(el);
  box.scrollTop = box.scrollHeight;
  return el;
}

function addStreamingMessage() {
  const box = document.getElementById('messages');
  const ts = new Date().toLocaleTimeString('es', {hour:'2-digit',minute:'2-digit'});
  const el = document.createElement('div');
  el.className = 'msg ai';
  el.innerHTML = `<div class="msg-bubble" id="streaming-bubble"><span class="cursor-blink"></span></div><span class="msg-meta">Auditor · ${ts}</span>`;
  box.appendChild(el);
  box.scrollTop = box.scrollHeight;
  return el;
}

function escHtml(s) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function formatMd(s) {
  // Code blocks
  s = s.replace(/```(\w*)\n?([\s\S]*?)```/g, (_,lang,code)=>`<div class="code-block">${code.trim()}</div>`);
  // Inline code
  s = s.replace(/`([^`]+)`/g,'<code style="background:#0d1117;padding:1px 5px;border-radius:3px;font-family:\'JetBrains Mono\',monospace;font-size:12px">$1</code>');
  // Bold
  s = s.replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>');
  // Line breaks
  s = s.replace(/\n/g,'<br>');
  return s;
}

async function sendMessage() {
  if (isStreaming) return;
  const inp = document.getElementById('chat-input');
  const text = inp.value.trim();
  if (!text) return;

  inp.value = '';
  inp.style.height = 'auto';
  document.getElementById('send-btn').disabled = true;
  isStreaming = true;

  addUserMessage(text);
  chatHistory.push({ role: 'user', content: text });

  const streamEl = addStreamingMessage();
  const bubble = document.getElementById('streaming-bubble');
  let accum = '';

  try {
    const resp = await fetch('/v1/chat/completions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: 'gravity-bridge-auto',
        messages: chatHistory,
        stream: true
      })
    });

    if (!resp.ok) {
      bubble.innerHTML = `<span style="color:var(--error)">Error ${resp.status}: ${resp.statusText}</span>`;
    } else {
      const reader = resp.body.getReader();
      const dec = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = dec.decode(value);
        const lines = chunk.split('\n').filter(l => l.startsWith('data: '));
        for (const line of lines) {
          const data = line.slice(6);
          if (data === '[DONE]') continue;
          try {
            const obj = JSON.parse(data);
            const delta = obj.choices?.[0]?.delta?.content || '';
            accum += delta;
            bubble.innerHTML = formatMd(escHtml(accum)) + '<span class="cursor-blink"></span>';
            document.getElementById('messages').scrollTop = 9999;
          } catch {}
        }
      }
      // Final render sin cursor
      bubble.innerHTML = formatMd(escHtml(accum));
      chatHistory.push({ role: 'assistant', content: accum });
    }
  } catch (err) {
    bubble.innerHTML = `<span style="color:var(--error)">Error de conexión: ${err.message}<br><br>Asegúrate de que el bridge está corriendo en el mismo Puerto.</span>`;
  }

  isStreaming = false;
  document.getElementById('send-btn').disabled = false;
  inp.focus();
}

// ── Status ─────────────────────────────────────────────────────────────────
async function refreshStatus() {
  try {
    const [status, models] = await Promise.all([
      fetch('/v1/status').then(r=>r.json()),
      fetch('/v1/models').then(r=>r.json())
    ]);

    const prov = status.active_provider || '--';
    const mod  = status.active_model   || '--';
    document.getElementById('stat-provider').textContent = prov;
    document.getElementById('stat-model').textContent    = mod.length > 35 ? mod.slice(0,35)+'…' : mod;
    document.getElementById('active-model-label').innerHTML = `Motor: <strong>${prov} / ${mod.slice(0,30)}</strong>`;
    document.getElementById('sidebar-model').textContent = mod.length > 30 ? mod.slice(0,30)+'…' : mod;
    document.getElementById('sidebar-provider').textContent = 'Proveedor: ' + prov;

    const backends = (status.backends || []);
    const online = backends.filter(b=>b.healthy).length;
    document.getElementById('stat-backends').textContent = `${online} / ${backends.length}`;

    const tbody = document.getElementById('providers-table');
    tbody.innerHTML = backends.map(b => `
      <tr>
        <td><strong>${b.name}</strong></td>
        <td><span class="badge ${b.category==='cloud'?'badge-cloud':'badge-local'}">${(b.category||'local').toUpperCase()}</span></td>
        <td><span class="${b.healthy?'online':'offline'}">${b.healthy?'● Online':'○ Offline'}</span></td>
        <td style="color:var(--muted)">${b.healthy?(b.latency_ms||0)+'ms':'—'}</td>
        <td>${b.models||0}</td>
      </tr>`).join('');

    // Sidebar providers
    document.getElementById('provider-list').innerHTML = backends.map(b => `
      <div class="provider-status">
        <div class="dot-sm ${b.healthy?'dot-online':'dot-offline'}"></div>
        <span${b.healthy?'':' style="opacity:.4"'}>${b.name}</span>
      </div>`).join('');
  } catch(e) {
    console.error('Status error:', e);
  }
}

// ── Audit ──────────────────────────────────────────────────────────────────
async function refreshAudit() {
  try {
    const data = await fetch('/v1/audit').then(r=>r.json());
    const entries = (data.data || []).slice(-50).reverse();
    document.getElementById('audit-table').innerHTML = entries.map(e => `
      <tr>
        <td style="font-family:'JetBrains Mono',monospace;font-size:12px;color:var(--muted)">${(e.timestamp||'').slice(0,19)}</td>
        <td style="font-size:12px">${e.provider||'?'} / <span style="color:var(--muted)">${(e.model||'').slice(0,30)}</span></td>
        <td style="font-family:'JetBrains Mono',monospace;font-size:12px">${e.input_tokens||0}↓ ${e.output_tokens||0}↑</td>
        <td style="font-size:12px;color:var(--muted)">${Math.round(e.latency_ms||0)}ms</td>
        <td style="font-size:12px;color:#f0883e">$${(e.cost_usd||0).toFixed(5)}</td>
      </tr>`).join('') || '<tr><td colspan="5" style="color:var(--muted);padding:20px;text-align:center">Sin entradas todavía.</td></tr>';
  } catch(e) {}
}

// ── Config ─────────────────────────────────────────────────────────────────
async function saveKey() {
  const prov = document.getElementById('cfg-provider').value.trim();
  const key  = document.getElementById('cfg-key').value.trim();
  if (!prov || !key) { alert('Completa proveedor y key.'); return; }
  try {
    const r = await fetch('/v1/keys', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ provider: prov, key })
    });
    if (r.ok) {
      document.getElementById('cfg-key').value = '';
      addAIMessage(`✓ Clave para **${prov}** guardada de forma segura.`);
      switchTab('chat', null);
    } else {
      alert('Error guardando key: ' + r.statusText);
    }
  } catch(e) { alert('Error de conexión: ' + e.message); }
}

// ── Init ──────────────────────────────────────────────────────────────────
refreshStatus();
setInterval(refreshStatus, 15000);
document.getElementById('chat-input').focus();
</script>
</body>
</html>"""


class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/dashboard":
            body = DASHBOARD_HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(301)
            self.send_header("Location", "/")
            self.end_headers()

    def log_message(self, fmt, *args): pass


def run(port: int = 7861):
    server = ThreadingHTTPServer(("0.0.0.0", port), DashboardHandler)
    print(f"[Gravity Dashboard] http://localhost:{port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()


if __name__ == "__main__":
    run()
