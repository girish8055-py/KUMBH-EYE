const localAlerts = [];
const cooldowns = {};
const THRESHOLDS = { crowd: 30, vehicle: 25, parking: 85 };
const COOLDOWN_MS = 10 * 60 * 1000;

function pushAlert(title, icon, cls, vid_id) {
  const key = `${vid_id}:${cls}`;
  const now = Date.now();
  if (cooldowns[key] && now - cooldowns[key] < COOLDOWN_MS) return;
  cooldowns[key] = now;
  localAlerts.unshift({ title, icon, cls, vid_id, ts: new Date().toISOString() });
  if (localAlerts.length > 60) localAlerts.pop();
  renderAlerts();
  toast(`⚠ ${title}`, 'warn');
}

function renderAlerts() {
  const list = $('alertList'), feed = $('globalAlertFeed');
  const bell = $('bellBtn'), badge = $('bellBadge');
  const n = localAlerts.length;
  if (badge) { badge.textContent = n > 9 ? '9+' : n; badge.classList.toggle('show', n > 0); }
  if (bell) bell.classList.toggle('hot', n > 0);
  if (list) {
    if (!n) list.innerHTML = '<div class="add-empty">All systems normal ✓</div>';
    else {
      list.innerHTML = localAlerts.map(a =>
        `<div class="add-item">
          <div class="add-ic ${a.cls}">${a.icon}</div>
          <div class="add-body">
            <div class="add-title2">${a.title}</div>
            <div class="add-meta">${new Date(a.ts).toLocaleTimeString()} · ${a.vid_id}</div>
          </div>
        </div>`
      ).join('');
    }
  }
  if (feed) {
    if (!n) feed.innerHTML = '<div class="af-empty">No alerts yet — all systems normal ✓</div>';
    else {
      feed.innerHTML = localAlerts.slice(0, 20).map(a =>
        `<div class="af-item ${a.cls}-a">
          <div class="af-icon">${a.icon}</div>
          <div><div class="af-title">${a.title}</div><div class="af-meta">${new Date(a.ts).toLocaleTimeString()} · ${a.vid_id.replace('_', ' ').toUpperCase()}</div></div>
        </div>`
      ).join('');
    }
  }
}

function toggleBell() { $('alertDD')?.classList.toggle('open'); }
function clearAlerts() { localAlerts.length = 0; renderAlerts(); $('alertDD')?.classList.remove('open'); }

document.addEventListener('click', e => {
  const dd = $('alertDD'), bell = $('bellBtn');
  if (dd && bell && !dd.contains(e.target) && !bell.contains(e.target)) dd.classList.remove('open');
});
