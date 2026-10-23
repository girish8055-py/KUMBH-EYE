const API = 'http://localhost:8000';
const $  = id => document.getElementById(id);
const fC = v  => v != null ? (v*100).toFixed(1)+'%' : '—';
const fD = v  => v != null ? v.toFixed(3) : '—';
const fT = iso => iso ? new Date(iso).toLocaleTimeString() : '—';

function set(id, v) {
  const e = $(id);
  if (!e) return;
  e.classList.remove('loading');
  e.textContent = v;
}
function setW(id, p) {
  const e = $(id);
  if (e) e.style.width = Math.min(100, Math.max(0, p)) + '%';
}

function toast(msg, type = 'info') {
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.textContent = msg;
  $('toasts').appendChild(t);
  setTimeout(() => t.remove(), 3200);
}

function noVid(id) {
  const v = $(`vid-${id}`), n = $(`novid-${id}`);
  if (v) v.style.display = 'none';
  if (n) n.style.display = 'flex';
}

function clock() {
  const n = new Date(), tc = $('timeClock');
  if (tc) tc.textContent = n.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}
setInterval(clock, 1000);
clock();

let _conn = false;
function setConn(ok) {
  if (_conn === ok) return;
  _conn = ok;
  const d = $('connDot'), t = $('connTxt');
  if (ok) { d.className = 'conn-dot on'; t.textContent = 'Connected'; }
  else { d.className = 'conn-dot off'; t.textContent = 'Offline'; }
}

async function checkBE() {
  try {
    const r = await fetch(`${API}/api/status`, { signal: AbortSignal.timeout(3000) });
    setConn(r.ok);
    return r.ok;
  } catch (_) {
    setConn(false);
    return false;
  }
}

function switchTab(name, btn) {
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  $(`section-${name}`)?.classList.add('active');
  if (btn) btn.classList.add('active');
  if (name === 'authority') loadComplaints();
  if (name === 'history' && histData.length === 0) loadHistory('crowd');
}

const PALS = {
  '': { label: 'Dark' },
  serene: { label: 'Serene Blue' },
  navy: { label: 'Deep Navy' },
  carbon: { label: 'Carbon' },
  forest: { label: 'Forest' },
};
function applyPal(name) {
  document.body.dataset.theme = name;
  document.querySelectorAll('.ps').forEach(s => s.classList.toggle('active', s.dataset.theme === name));
  try { localStorage.setItem('sv-theme', name); } catch (_) { }
}
document.querySelectorAll('.ps').forEach(s => s.addEventListener('click', () => applyPal(s.dataset.theme)));
try { const sv = localStorage.getItem('sv-theme'); if (sv !== null) applyPal(sv); } catch (_) { }

function closeModal(id) {
  $(id)?.classList.remove('open');
  if (id === 'analyticsModal') destroyCh();
}
document.querySelectorAll('.modal').forEach(m => m.addEventListener('click', e => {
  if (e.target === m) m.classList.remove('open');
}));
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal.open').forEach(m => m.classList.remove('open'));
    $('lightbox')?.classList.remove('open');
  }
});
