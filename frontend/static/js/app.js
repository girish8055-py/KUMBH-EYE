/* ── DETECTION DATA ────────────────────────────────────────────────── */
const crowdT = {}, vehT = {};
let parkRing = null;

function genAISummary(type) {
  if (type === 'crowd') {
    const tot = Object.values(crowdT).reduce((a, b) => a + b, 0);
    const el = $('aibt-crowd'), ac = $('aiba-crowd');
    if (!el) return;
    let txt = '', act = '', showAct = false;
    if (!tot) txt = '<strong>No people detected</strong> — area is clear.';
    else if (tot < 10) txt = `Small group of <strong>${tot} people</strong> across both cameras. Area is calm.`;
    else if (tot < 30) txt = `<strong>${tot} people</strong> detected. Crowd is moderate — normal activity.`;
    else { txt = `⚠ <strong>${tot} people</strong> detected! Crowd is <strong>HIGH</strong>.`; act = '👮 Recommended: Alert security personnel immediately.'; showAct = true; }
    el.innerHTML = txt;
    if (ac) { ac.textContent = act; ac.classList.toggle('on', showAct); }
  } else if (type === 'vehicle') {
    const tot = Object.values(vehT).reduce((a, b) => a + b, 0);
    const el = $('aibt-vehicle'), ac = $('aiba-vehicle');
    if (!el) return;
    let txt = '', act = '', showAct = false;
    if (!tot) txt = '<strong>No vehicles</strong> in monitored zones. Road is clear.';
    else if (tot < 10) txt = `<strong>${tot} vehicles</strong> spotted. Traffic is <strong>light</strong>.`;
    else if (tot < 25) txt = `<strong>${tot} vehicles</strong> in monitored areas. Traffic is <strong>moderate</strong>.`;
    else { txt = `⚠ <strong>${tot} vehicles</strong>! Traffic is <strong>heavy</strong>.`; act = '🚦 Recommended: Consider traffic management.'; showAct = true; }
    el.innerHTML = txt;
    if (ac) { ac.textContent = act; ac.classList.toggle('on', showAct); }
  }
}

function genParkSummary(d) {
  const el = $('aibt-parking'), ac = $('aiba-parking');
  if (!el) return;
  const avail = d.available || 0, rate = d.occupancy_rate || 0;
  let txt = '', act = '', showAct = false;
  if (!d.total_slots) txt = 'Waiting for parking data…';
  else if (avail === 0) { txt = '🚨 <strong>Parking lot is FULL</strong>. No free spots.'; act = '🚗 Advise incoming drivers to find alternative parking.'; showAct = true; }
  else if (rate > 80) { txt = `⚠ Parking <strong>almost full</strong>. Only <strong>${avail} spot${avail === 1 ? '' : 's'} left</strong>.`; act = '📢 Display "Almost Full" sign at entrance.'; showAct = true; }
  else if (rate < 20) txt = `Parking has <strong>plenty of space</strong>. <strong>${avail}/${d.total_slots}</strong> spots free.`;
  else txt = `<strong>${avail} free spots</strong> out of ${d.total_slots}. ${rate}% occupied.`;
  el.innerHTML = txt;
  if (ac) { ac.textContent = act; ac.classList.toggle('on', showAct); }
}

function updCrowd(id, d) {
  crowdT[id] = d.count || 0;
  set(`ol-cnt-${id}`, d.count ?? '—');
  set(`ol-ts-${id}`, fT(d.timestamp));
  const lo = $(`ol-lvl-${id}`);
  if (lo) {
    const lv = d.density_level || '—';
    lo.style.color = lv === 'High' ? '#f87171' : lv === 'Medium' ? '#fb923c' : '#4ade80';
    lo.textContent = lv + ' Density';
  }
  if (d.frame_size) set(`ol-res-${id}`, d.frame_size);
  set(`sr-${id}-cnt`, d.count ?? '—');
  set(`sr-${id}-den`, fD(d.density));
  set(`sr-${id}-conf`, fC(d.avg_confidence));
  set(`ss-${id}-mm`, `↓${fC(d.min_confidence)} ↑${fC(d.max_confidence)}`);
  set(`ss-${id}-ts`, `Updated ${fT(d.timestamp)}`);
  const le = $(`sr-${id}-lvl`);
  if (le) { const lv = d.density_level || 'Low'; le.innerHTML = `<div class="dlvl ${lv}">${lv}</div>`; }
  setW(`pb-${id}-cnt`, Math.min(100, (d.count || 0) / 50 * 100));
  setW(`pb-${id}-den`, Math.min(100, (d.density || 0) * 200));
  setW(`pb-${id}-conf`, (d.avg_confidence || 0) * 100);
  const tot = Object.values(crowdT).reduce((a, b) => a + b, 0);
  set('s-crowd-tot', tot);
  set('s-crowd-den', fD(d.density));
  set('s-crowd-conf', fC(d.avg_confidence));
  const ae = $('s-crowd-alert');
  if (ae) {
    const lv = d.density_level || 'Low';
    ae.style.setProperty('--vc', lv === 'High' ? 'var(--red)' : lv === 'Medium' ? 'var(--amber)' : 'var(--green)');
    ae.textContent = lv === 'High' ? '⚠ Alert!' : lv === 'Medium' ? 'Caution' : 'Safe';
  }
  if (d.count >= THRESHOLDS.crowd || d.density_level === 'High')
    pushAlert(`High crowd — ${d.count} people at ${id.replace('_', ' ').toUpperCase()}`, '🫂', 'crowd', id);
  genAISummary('crowd');
}

function updVeh(id, d) {
  vehT[id] = d.total_count || 0;
  set(`ol-cnt-${id}`, d.total_count ?? '—');
  set(`ol-ts-${id}`, fT(d.timestamp));
  set(`sr-${id}-tot`, d.total_count ?? '—');
  set(`sr-${id}-den`, fD(d.density));
  set(`sr-${id}-conf`, fC(d.avg_confidence));
  set(`ss-${id}-ts`, `Updated ${fT(d.timestamp)}`);
  const ce = $(`sr-${id}-cls`);
  if (ce) {
    const es = Object.entries(d.class_breakdown || {});
    ce.textContent = es.length ? es.map(([k, v]) => `${k}:${v}`).join(' · ') : '—';
  }
  setW(`pb-${id}-tot`, Math.min(100, (d.total_count || 0) / 30 * 100));
  setW(`pb-${id}-den`, Math.min(100, (d.density || 0) * 200));
  setW(`pb-${id}-conf`, (d.avg_confidence || 0) * 100);
  const tot = Object.values(vehT).reduce((a, b) => a + b, 0);
  set('s-veh-tot', tot);
  set('s-veh-den', fD(d.density));
  set('s-veh-conf', fC(d.avg_confidence));
  const te = $('s-veh-traf');
  if (te) {
    const h = tot > 25;
    te.style.setProperty('--vc', h ? 'var(--red)' : tot > 12 ? 'var(--amber)' : 'var(--green)');
    te.textContent = h ? '⚠ Heavy' : tot > 12 ? 'Moderate' : 'Clear';
  }
  if (d.total_count >= THRESHOLDS.vehicle)
    pushAlert(`Heavy traffic — ${d.total_count} vehicles at ${id.replace('_', ' ').toUpperCase()}`, '🚗', 'vehicle', id);
  genAISummary('vehicle');
}

function updParking(d) {
  const occ = d.occupied || 0, avail = d.available || 0, total = d.total_slots || 0, rate = d.occupancy_rate || 0;
  set('s-park-tot', total);
  set('s-park-occ', occ);
  set('s-park-avail', avail);
  set('s-park-rate', rate + '%');
  set('pk-occ', occ);
  set('pk-avail', avail);
  set('pk-total', total);
  set('ring-rate', rate + '%');
  set('ol-pk-avail', avail);
  set('ol-ts-parking_1', fT(d.timestamp));
  const so = $('ol-pk-status');
  if (so) so.textContent = d.status || '—';
  if (total > 0) { setW('pkb-occ', occ / total * 100); setW('pkb-avail', avail / total * 100); }
  const tag = $('park-tag');
  if (tag) {
    tag.textContent = d.status || '—';
    const s = (d.status || '').toLowerCase();
    tag.className = 'park-tag ' + (s.includes('full') && !s.includes('almost') ? 'full' : s.includes('almost') ? 'almost' : 'ok');
  }
  buildSlots(total, occ);
  updRing(occ, avail);
  if (rate >= THRESHOLDS.parking)
    pushAlert(`Parking ${d.status} — ${avail} spots left`, '🅿', 'parking', 'parking_1');
  genParkSummary(d);
}

function buildSlots(total, occ) {
  const g = $('slotGrid');
  if (!g) return;
  if (!total) { g.innerHTML = '<div class="slot-wait"><div class="spin" style="border-top-color:var(--park)"></div>No slots detected</div>'; return; }
  g.innerHTML = Array.from({ length: total }, (_, i) =>
    `<div class="slot ${i < occ ? 'o' : 'a'}" title="Spot ${i + 1}: ${i < occ ? 'Taken' : 'Free'}">${i < occ ? 'OCC' : 'FREE'}</div>`
  ).join('');
}

function updRing(occ, avail) {
  const c = $('parkRing');
  if (!c) return;
  const data = {
    datasets: [{
      data: [occ, avail],
      backgroundColor: ['rgba(248,113,113,.55)', 'rgba(74,222,128,.5)'],
      borderColor: ['#f87171', '#4ade80'],
      borderWidth: 1.5,
      hoverOffset: 4,
    }],
    labels: ['Taken', 'Free'],
  };
  if (parkRing) { parkRing.data = data; parkRing.update(); }
  else {
    parkRing = new Chart(c.getContext('2d'), {
      type: 'doughnut', data,
      options: { cutout: '68%', animation: { duration: 500 }, plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => ` ${ctx.label}: ${ctx.parsed}` } } } },
    });
  }
}

function apply(d) {
  if (!d?.video_id) return;
  if (d.type === 'crowd') updCrowd(d.video_id, d);
  if (d.type === 'vehicle') updVeh(d.video_id, d);
  if (d.type === 'parking') updParking(d);
}

/* WS + POLL */
const socks = {};
const ALL = ['crowd_1', 'crowd_2', 'vehicle_1', 'vehicle_2', 'parking_1'];

function connectWS(id) {
  if (socks[id]) return;
  const ws = new WebSocket(`ws://localhost:8000/ws/${id}`);
  socks[id] = ws;
  ws.onmessage = e => { try { apply(JSON.parse(e.data)); } catch (_) { } };
  ws.onclose = () => { delete socks[id]; setTimeout(() => connectWS(id), 5000); };
  ws.onerror = () => ws.close();
}

async function poll(id) {
  try {
    const r = await fetch(`${API}/api/latest/${id}`, { signal: AbortSignal.timeout(3000) });
    if (r.ok) apply(await r.json());
  } catch (_) { }
}

async function init() {
  const ok = await checkBE();
  toast(ok ? '✓ Connected to SmartVision backend' : '✗ Backend offline — run: uvicorn main:app --port 8000', ok ? 'success' : 'error');
  ALL.forEach(id => { connectWS(id); poll(id); });
  setInterval(() => { checkBE(); ALL.forEach(poll); }, 4500);
  setInterval(() => {
    if (document.querySelector('#section-authority.active')) loadComplaints();
  }, 15000);
}
init();

/* ── CHARTS ───────────────────────────────────────────────────────── */
const _ch = {};
const destroyCh = () => Object.keys(_ch).forEach(k => { _ch[k]?.destroy(); delete _ch[k]; });
const gc = () => 'rgba(255,255,255,.04)', tc = () => '#3e5070';
const bo = {
  responsive: true, maintainAspectRatio: true,
  plugins: { legend: { labels: { color: '#7b90b8', font: { size: 10 } } } },
  scales: { x: { grid: { color: gc() }, ticks: { color: tc(), font: { size: 9 }, maxTicksLimit: 7 } }, y: { grid: { color: gc() }, ticks: { color: tc(), font: { size: 9 } } } },
};
const st = iso => iso ? new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : '';
const AL = { crowd_1: 'Camera 1 · Crowd', crowd_2: 'Camera 2 · Crowd', vehicle_1: 'Camera 1 · Vehicle', vehicle_2: 'Camera 2 · Vehicle', parking_1: 'Parking Lot' };

async function showAnalytics(vid) {
  destroyCh();
  const modal = $('analyticsModal');
  const cont = $('charts-cont');
  set('m-anly-title', `Analytics — ${AL[vid] || vid}`);
  cont.innerHTML = '<div class="mloading"><div class="spin"></div>Loading data…</div>';
  modal.classList.add('open');
  let data;
  try {
    const r = await fetch(`${API}/api/analytics/${vid}`, { signal: AbortSignal.timeout(6000) });
    if (r.status === 202) { cont.innerHTML = '<div class="merror">Not enough data yet — wait ~30s and retry.</div>'; return; }
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    data = await r.json();
  } catch (e) { cont.innerHTML = `<div class="merror">Failed: ${e.message}</div>`; return; }
  const ts = (data.timestamps || []).map(st);

  if (data.type === 'crowd') {
    cont.innerHTML = `<div class="charts-grid"><div class="chart-card wide"><div class="chart-title">People Count Over Time</div><canvas id="ac1"></canvas></div><div class="chart-card"><div class="chart-title">Area Density</div><canvas id="ac2"></canvas></div><div class="chart-card"><div class="chart-title">Crowd Level Breakdown</div><canvas id="ac3"></canvas></div><div class="chart-card wide"><div class="chart-title">AI Confidence</div><canvas id="ac4"></canvas></div></div>`;
    _ch.c1 = new Chart($('ac1').getContext('2d'), { type: 'line', data: { labels: ts, datasets: [{ label: 'People', data: data.counts, borderColor: '#22d3a0', backgroundColor: 'rgba(34,211,160,.08)', fill: true, tension: .35, pointRadius: 2, borderWidth: 2 }] }, options: { ...bo, plugins: { ...bo.plugins, legend: { display: false } } } });
    _ch.c2 = new Chart($('ac2').getContext('2d'), { type: 'line', data: { labels: ts, datasets: [{ label: 'Density', data: data.densities, borderColor: '#60a5fa', backgroundColor: 'rgba(96,165,250,.07)', fill: true, tension: .35, pointRadius: 2, borderWidth: 2 }] }, options: bo });
    const ld = data.level_distribution || {};
    _ch.c3 = new Chart($('ac3').getContext('2d'), { type: 'doughnut', data: { labels: ['Low — Safe', 'Medium', 'High — Alert'], datasets: [{ data: [ld.Low || 0, ld.Medium || 0, ld.High || 0], backgroundColor: ['rgba(74,222,128,.5)', 'rgba(251,146,60,.5)', 'rgba(248,113,113,.5)'], borderColor: ['#4ade80', '#fb923c', '#f87171'], borderWidth: 1.5 }] }, options: { responsive: true, maintainAspectRatio: true, cutout: '50%', plugins: { legend: { labels: { color: '#7b90b8', font: { size: 9 } } } } } });
    _ch.c4 = new Chart($('ac4').getContext('2d'), { type: 'line', data: { labels: ts, datasets: [{ label: 'Confidence', data: data.confidences, borderColor: '#fbbf24', backgroundColor: 'rgba(251,191,36,.07)', fill: true, tension: .35, pointRadius: 2, borderWidth: 2 }] }, options: { ...bo, scales: { ...bo.scales, y: { ...bo.scales.y, min: 0, max: 1 } } } });
  } else if (data.type === 'vehicle') {
    const cls = data.class_totals || {};
    const cL = Object.keys(cls), cV = Object.values(cls);
    cont.innerHTML = `<div class="charts-grid"><div class="chart-card wide"><div class="chart-title">Vehicle Count Over Time</div><canvas id="ac1"></canvas></div><div class="chart-card"><div class="chart-title">Vehicle Types</div><canvas id="ac2"></canvas></div><div class="chart-card"><div class="chart-title">Road Density</div><canvas id="ac3"></canvas></div><div class="chart-card wide"><div class="chart-title">AI Confidence</div><canvas id="ac4"></canvas></div></div>`;
    _ch.c1 = new Chart($('ac1').getContext('2d'), { type: 'line', data: { labels: ts, datasets: [{ label: 'Vehicles', data: data.totals, borderColor: '#fbbf24', backgroundColor: 'rgba(251,191,36,.08)', fill: true, tension: .35, pointRadius: 2, borderWidth: 2 }] }, options: { ...bo, plugins: { ...bo.plugins, legend: { display: false } } } });
    _ch.c2 = new Chart($('ac2').getContext('2d'), { type: 'bar', data: { labels: cL.length ? cL : ['No data'], datasets: [{ label: 'Count', data: cL.length ? cV : [0], backgroundColor: ['#3b82f6', '#fbbf24', '#f87171', '#4ade80', '#818cf8'].slice(0, Math.max(1, cL.length)), borderRadius: 4 }] }, options: { ...bo, plugins: { ...bo.plugins, legend: { display: false } } } });
    _ch.c3 = new Chart($('ac3').getContext('2d'), { type: 'line', data: { labels: ts, datasets: [{ label: 'Density', data: data.densities, borderColor: '#60a5fa', backgroundColor: 'rgba(96,165,250,.07)', fill: true, tension: .35, pointRadius: 2, borderWidth: 2 }] }, options: bo });
    _ch.c4 = new Chart($('ac4').getContext('2d'), { type: 'line', data: { labels: ts, datasets: [{ label: 'Conf', data: data.confidences, borderColor: '#22d3a0', backgroundColor: 'rgba(34,211,160,.07)', fill: true, tension: .35, pointRadius: 2, borderWidth: 2 }] }, options: { ...bo, scales: { ...bo.scales, y: { ...bo.scales.y, min: 0, max: 1 } } } });
  } else if (data.type === 'parking') {
    const last = data.occupied.length - 1;
    cont.innerHTML = `<div class="charts-grid"><div class="chart-card"><div class="chart-title">Current Snapshot</div><canvas id="ac1"></canvas></div><div class="chart-card"><div class="chart-title">Fill Rate %</div><canvas id="ac2"></canvas></div><div class="chart-card wide"><div class="chart-title">Taken vs Free Over Time</div><canvas id="ac3"></canvas></div></div>`;
    _ch.c1 = new Chart($('ac1').getContext('2d'), { type: 'doughnut', data: { labels: ['Taken', 'Free'], datasets: [{ data: [data.occupied[last] || 0, data.available[last] || 0], backgroundColor: ['rgba(248,113,113,.55)', 'rgba(74,222,128,.5)'], borderColor: ['#f87171', '#4ade80'], borderWidth: 1.5 }] }, options: { responsive: true, maintainAspectRatio: true, cutout: '60%', plugins: { legend: { labels: { color: '#7b90b8', font: { size: 10 } } } } } });
    _ch.c2 = new Chart($('ac2').getContext('2d'), { type: 'line', data: { labels: ts, datasets: [{ label: 'Fill %', data: data.occupancy_rates, borderColor: '#818cf8', backgroundColor: 'rgba(129,140,248,.08)', fill: true, tension: .35, pointRadius: 2, borderWidth: 2 }] }, options: { ...bo, scales: { ...bo.scales, y: { ...bo.scales.y, min: 0, max: 100 } } } });
    _ch.c3 = new Chart($('ac3').getContext('2d'), { type: 'bar', data: { labels: ts, datasets: [{ label: 'Taken', data: data.occupied, backgroundColor: 'rgba(248,113,113,.5)', borderRadius: 3 }, { label: 'Free', data: data.available, backgroundColor: 'rgba(74,222,128,.45)', borderRadius: 3 }] }, options: { ...bo, scales: { x: { ...bo.scales.x, stacked: true }, y: { ...bo.scales.y, stacked: true } } } });
  }
}

/* HEATMAP */
async function openHeatmap(vid) {
  const modal = $('heatmapModal'), body = $('hm-body');
  body.innerHTML = '<div class="mloading"><div class="spin" style="border-top-color:var(--veh)"></div>Generating heatmap & movement trail…</div>';
  modal.classList.add('open');
  try {
    const r = await fetch(`${API}/api/heatmap/${vid}`, { signal: AbortSignal.timeout(18000) });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const blob = await r.blob();
    const url = URL.createObjectURL(blob);
    body.innerHTML = `<p class="hm-info">🟢 Green = start · 🔴 Red = latest · Lines show movement path over time</p>
      <div class="hm-img-wrap"><img src="${url}" alt="Heatmap"/></div>
      <div class="hm-footer"><a href="${url}" download="heatmap_${vid}.png" class="pill teal">⬇ Download PNG</a><button class="pill" onclick="closeModal('heatmapModal')">Close</button></div>`;
  } catch (e) { body.innerHTML = `<div class="merror">✗ ${e.message}</div>`; }
}

/* REPORT */
async function openReport(vid) {
  const modal = $('reportModal'), body = $('rpt-body');
  set('m-rpt-title', `Report — ${AL[vid] || vid}`);
  body.innerHTML = '<div class="mloading"><div class="spin" style="border-top-color:var(--park)"></div>Building report…</div>';
  modal.classList.add('open');
  try {
    const r = await fetch(`${API}/api/report/${vid}`, { signal: AbortSignal.timeout(20000) });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const html = await r.text();
    const blob = new Blob([html], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    body.innerHTML = `<div style="display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap">
      <a href="${url}" target="_blank" class="pill teal">🔗 Open in New Tab</a>
      <a href="${url}" download="report_${vid}.html" class="pill violet">⬇ Download HTML</a>
      <span style="font-size:10px;font-family:var(--fm);color:var(--t3);display:flex;align-items:center;padding:0 6px">Ctrl+P in new tab → Save as PDF</span>
    </div>
    <iframe src="${url}" class="report-frame" title="Report"></iframe>`;
  } catch (e) { body.innerHTML = `<div class="merror">✗ ${e.message}</div>`; }
}

/* ── COMPLAINT FORM ──────────────────────────────────────────────── */
let photoDB64 = '';

function handlePhoto(input) {
  const file = input.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = e => {
    photoDB64 = e.target.result;
    const prev = $('photoPreview');
    if (prev) { prev.src = photoDB64; prev.style.display = 'block'; }
    $('photoWrap')?.classList.add('has-photo');
  };
  reader.readAsDataURL(file);
}

async function submitComplaint() {
  const name = $('cf-name')?.value.trim();
  const phone = $('cf-phone')?.value.trim();
  const location = $('cf-location')?.value.trim();
  const category = $('cf-category')?.value;
  const desc = $('cf-desc')?.value.trim();
  const fb = $('cf-feedback');
  if (!name || !location || !category || !desc) {
    if (fb) fb.textContent = '⚠ Please fill in all required fields.';
    fb && (fb.style.color = 'var(--red)');
    return;
  }
  if (fb) { fb.textContent = 'Submitting…'; fb.style.color = 'var(--t3)'; }
  try {
    const res = await fetch(`${API}/api/complaint`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, phone, location, category, description: desc, photo_b64: photoDB64 }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    if (fb) { fb.textContent = `✓ Complaint submitted! ID: ${data.complaint_id.slice(0, 8).toUpperCase()}`; fb.style.color = 'var(--green)'; }
    ['cf-name', 'cf-phone', 'cf-location', 'cf-desc'].forEach(id => { const e = $(id); if (e) e.value = ''; });
    $('cf-category').value = '';
    photoDB64 = '';
    const prev = $('photoPreview');
    if (prev) { prev.src = ''; prev.style.display = 'none'; }
    $('photoWrap')?.classList.remove('has-photo');
    toast('✓ Complaint submitted to authorities', 'success');
    pushAlert(`New complaint — ${category} at ${location}`, '📝', 'complaint', 'system');
    await loadComplaints(true);
  } catch (e) {
    if (fb) { fb.textContent = `✗ Failed: ${e.message}`; fb.style.color = 'var(--red)'; }
    toast('Failed to submit complaint', 'error');
  }
}

/* ── AUTHORITY COMPLAINTS ────────────────────────────────────────── */
let allComplaints = [];
let currentFilter = 'all';

async function loadComplaints(silent = false) {
  try {
    const r = await fetch(`${API}/api/complaints`, { signal: AbortSignal.timeout(5000) });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const data = await r.json();
    allComplaints = data.complaints || [];
    renderComplaints();
    updateAuthStats();
    updateComplaintBadge();
    if (!silent && allComplaints.length) toast(`${allComplaints.length} complaint(s) loaded`, 'info');
  } catch (e) { if (!silent) toast(`Failed to load complaints: ${e.message}`, 'error'); }
}

function updateAuthStats() {
  const open = allComplaints.filter(c => c.status === 'Open').length;
  const inp = allComplaints.filter(c => c.status === 'In Progress').length;
  const res = allComplaints.filter(c => c.status === 'Resolved').length;
  set('auth-total', allComplaints.length);
  set('auth-open', open);
  set('auth-inprog', inp);
  set('auth-resolved', res);
}

function updateComplaintBadge() {
  const open = allComplaints.filter(c => c.status === 'Open').length;
  const badge = $('complaint-badge');
  if (badge) { badge.textContent = open; badge.style.display = open ? 'inline-flex' : 'none'; }
}

function filterComplaints(filter, btn) {
  currentFilter = filter;
  document.querySelectorAll('.cc-filter').forEach(b => b.classList.toggle('active', b.dataset.filter === filter));
  renderComplaints();
}

function renderComplaints() {
  const cont = $('complaintsList');
  if (!cont) return;
  const filtered = currentFilter === 'all' ? allComplaints : allComplaints.filter(c => c.status === currentFilter);
  if (!filtered.length) {
    cont.innerHTML = `<div class="af-empty" style="text-align:center;padding:30px">No ${currentFilter === 'all' ? '' : currentFilter.toLowerCase() + ' '}complaints.</div>`;
    return;
  }
  cont.innerHTML = filtered.map(c => {
    const statusClass = c.status === 'Open' ? 'open-c' : c.status === 'Resolved' ? 'resolved' : 'inprog';
    const photo = c.photo_b64 ? `<img src="${c.photo_b64}" class="cc-photo" onclick="openLightbox('${c.id}')" title="Click to enlarge"/>` : '';
    return `<div class="complaint-card ${statusClass}" id="cc-${c.id}">
      <div class="cc-top">
        <div>
          <div class="cc-title">${c.category} — ${c.location}</div>
          <div class="cc-meta">${c.name}${c.phone ? ' · ' + c.phone : ''} · ${c.timestamp}</div>
        </div>
        <div class="cc-status ${c.status.replace(' ', '-')}" onclick="cycleStatus('${c.id}')" title="Click to change status">${c.status}</div>
      </div>
      <div class="cc-body">
        <div class="cc-desc">${c.description}</div>
        ${photo}
        <div class="cc-actions">
          <button class="cc-action-btn inprog" onclick="setStatus('${c.id}','In Progress')">Mark In Progress</button>
          <button class="cc-action-btn resolve" onclick="setStatus('${c.id}','Resolved')">Mark Resolved</button>
        </div>
      </div>
    </div>`;
  }).join('');
  filtered.forEach(c => { if (c.photo_b64) window[`photo_${c.id}`] = c.photo_b64; });
}

function openLightbox(id) {
  const img = $('lbImg');
  const lb = $('lightbox');
  if (img && lb && window[`photo_${id}`]) { img.src = window[`photo_${id}`]; lb.classList.add('open'); }
}

async function setStatus(id, status) {
  try {
    const r = await fetch(`${API}/api/complaint/${id}/status`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ status }) });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    await loadComplaints(true);
    toast(`Status updated to "${status}"`, status === 'Resolved' ? 'success' : 'info');
  } catch (e) { toast(`Failed: ${e.message}`, 'error'); }
}

function cycleStatus(id) {
  const c = allComplaints.find(x => x.id === id);
  if (!c) return;
  const next = { Open: 'In Progress', 'In Progress': 'Resolved', Resolved: 'Open' };
  setStatus(id, next[c.status] || 'Open');
}

/* ── LIVE STREAM POLLING ─────────────────────────── */
const LS_URL = 'http://localhost:5000';
let lsPeak = 0, lsRendered = 0, lsMaxPeak = 1;

function lsPollState() {
  fetch(`${LS_URL}/get_state`, { signal: AbortSignal.timeout(3000) })
    .then(r => r.json())
    .then(d => {
      set('ls-count', d.count ?? '—');
      set('ls-raw', d.raw_count ?? '—');
      set('ls-fps', d.fps ?? '—');
      ['ls-count', 'ls-raw', 'ls-fps'].forEach(id => { const e = $(id); if (e) e.classList.remove('loading'); });
      const age = Math.round((Date.now() / 1000) - d.timestamp);
      const live = age < 5;
      const dot = $('ls-dot');
      if (dot) { dot.style.background = live ? '#22c55e' : '#94a3b8'; dot.style.boxShadow = live ? '0 0 6px #22c55e' : 'none'; }
      set('ls-status', live ? 'Live' : `Delayed (${age}s)`);
      set('ls-last-update', `Updated ${age}s ago`);
      set('ls-age', live ? 'Stream live' : `Signal delayed ${age}s`);
      if (d.count > lsPeak) {
        lsPeak = d.count;
        lsMaxPeak = lsPeak;
        set('ls-peak', lsPeak);
        set('ls-peak-time', 'at ' + new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }));
      }
    })
    .catch(() => {
      set('ls-status', 'app.py offline');
      const dot = $('ls-dot');
      if (dot) { dot.style.background = '#ef4444'; dot.style.boxShadow = 'none'; }
    });
}

function lsPollHistory() {
  fetch(`${LS_URL}/get_history`, { signal: AbortSignal.timeout(3000) })
    .then(r => r.json())
    .then(entries => {
      if (entries.length === lsRendered) return;
      lsRendered = entries.length;
      set('ls-badge', entries.length);
      const list = $('ls-history-list');
      if (!list) return;
      if (!entries.length) { list.innerHTML = '<div style="padding:22px;text-align:center;color:var(--t3);font-size:11px">No changes yet…</div>'; return; }
      list.innerHTML = entries.slice().reverse().map((e, i) => {
        const pct = Math.min(100, Math.round((e.count / Math.max(lsMaxPeak, 1)) * 100));
        const isNew = i === 0;
        const arrow = e.delta > 0 ? '▲' : e.delta < 0 ? '▼' : '·';
        const aColor = e.delta > 0 ? '#22c55e' : e.delta < 0 ? '#ef4444' : '#94a3b8';
        return `<div style="display:grid;grid-template-columns:58px 44px 1fr 40px;align-items:center;gap:8px;padding:8px 14px;border-bottom:1px solid var(--bdr);font-size:11px;${isNew ? 'background:#fff7ed;border-left:3px solid var(--kumbh-orange)' : ''}">
          <span style="color:var(--t3);font-size:10px">${e.time_str}</span>
          <span style="font-weight:700;font-size:15px;color:${e.count === 0 ? '#cbd5e1' : 'var(--kumbh-orange)'};text-align:center">${e.count}<span style="font-size:9px;color:${aColor};margin-left:2px">${arrow}</span></span>
          <div style="background:var(--surf3);border-radius:3px;height:5px"><div style="height:5px;border-radius:3px;width:${pct}%;background:linear-gradient(90deg,#f97316,#ea6a0a)"></div></div>
          <span style="color:var(--t3);font-size:10px;text-align:right">${e.fps}fps</span>
        </div>`;
      }).join('');
    })
    .catch(() => {});
}

setInterval(() => {
  if (document.getElementById('section-livestream')?.classList.contains('active')) {
    lsPollState();
    lsPollHistory();
  }
}, 500);

/* ── HISTORY ─────────────────────────────────────────────────────── */
let histData = [];
let currentHistType = 'crowd';

const HIST_COLS = {
  crowd: ['#', 'Video', 'Count', 'Density', 'Avg Conf', 'Level', 'Timestamp'],
  vehicle: ['#', 'Video', 'Total', 'Density', 'Avg Conf', 'Classes', 'Timestamp'],
  parking: ['#', 'Video', 'Occupied', 'Available', 'Total', 'Rate%', 'Status', 'Timestamp'],
  alerts: ['#', 'Title', 'Camera', 'Alert Key', 'Timestamp'],
  complaints: ['#', 'Name', 'Location', 'Category', 'Description', 'Status', 'Submitted'],
};

function histRow(type, r) {
  const td = (v, color = '') => `<td style="padding:9px 14px;border-bottom:1px solid var(--bdr);color:${color || 'var(--t1)'};white-space:nowrap">${v ?? '—'}</td>`;
  const lvlColor = l => l === 'High' ? '#f87171' : l === 'Medium' ? '#fb923c' : '#4ade80';
  const badge = (v, col) => `<span style="padding:2px 8px;border-radius:20px;font-size:10px;font-weight:600;background:${col}22;color:${col};border:1px solid ${col}44">${v}</span>`;
  if (type === 'crowd') return `<tr>${td(r.id, 'var(--t3)')}${td(r.video_id)}${td(r.count, 'var(--crowd)')}${td(r.density?.toFixed(4))}${td((r.avg_conf * 100).toFixed(1) + '%')}${td(badge(r.level, lvlColor(r.level)))}${td(r.timestamp?.slice(0, 19), 'var(--t3)')}</tr>`;
  if (type === 'vehicle') return `<tr>${td(r.id, 'var(--t3)')}${td(r.video_id)}${td(r.total, 'var(--veh)')}${td(r.density?.toFixed(4))}${td((r.avg_conf * 100).toFixed(1) + '%')}${td(r.classes ? Object.entries(JSON.parse(r.classes)).map(([k, v]) => `${k}:${v}`).join(', ') : '—')}${td(r.timestamp?.slice(0, 19), 'var(--t3)')}</tr>`;
  if (type === 'parking') return `<tr>${td(r.id, 'var(--t3)')}${td(r.video_id)}${td(r.occupied, '#f87171')}${td(r.available, '#4ade80')}${td(r.total)}${td(r.rate + '%')}${td(badge(r.status, r.status === 'Lot Full' ? '#f87171' : r.status === 'Almost Full' ? '#fb923c' : '#4ade80'))}${td(r.timestamp?.slice(0, 19), 'var(--t3)')}</tr>`;
  if (type === 'alerts') return `<tr>${td(r.id, 'var(--t3)')}${td(r.title, '#f87171')}${td(r.video_id)}${td(r.alert_key)}${td(r.timestamp?.slice(0, 19), 'var(--t3)')}</tr>`;
  if (type === 'complaints') {
    const scol = r.status === 'Resolved' ? '#4ade80' : r.status === 'In Progress' ? '#fb923c' : '#f87171';
    return `<tr>${td(r.id?.slice(0, 8).toUpperCase(), 'var(--t3)')}${td(r.name)}${td(r.location)}${td(r.category)}<td style="padding:9px 14px;border-bottom:1px solid var(--bdr);color:var(--t2);max-width:200px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${r.description || '—'}</td>${td(badge(r.status, scol))}${td(r.timestamp?.slice(0, 16), 'var(--t3)')}</tr>`;
  }
  return '';
}

function renderHistTable(data) {
  const thead = $('hist-thead');
  const tbody = $('hist-tbody');
  const cols = HIST_COLS[currentHistType] || [];
  if (!thead || !tbody) return;
  thead.innerHTML = `<tr>${cols.map(c => `<th style="padding:9px 14px;text-align:left;font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.8px;color:var(--t3);white-space:nowrap">${c}</th>`).join('')}</tr>`;
  tbody.innerHTML = data.length ? data.map(r => histRow(currentHistType, r)).join('') : `<tr><td colspan="${cols.length}" style="padding:28px;text-align:center;color:var(--t3);font-size:12px">No records found.</td></tr>`;
  set('hist-count', `${data.length} records`);
}

function filterHistTable() {
  const q = ($('hist-search')?.value || '').toLowerCase();
  if (!q) { renderHistTable(histData); return; }
  const filtered = histData.filter(r => Object.values(r).some(v => String(v).toLowerCase().includes(q)));
  renderHistTable(filtered);
}

function renderHistStats(data, type) {
  const el = $('hist-stats');
  if (!el || !data.length) { el.innerHTML = ''; return; }
  let cards = '';
  if (type === 'crowd') {
    const avg = (data.reduce((a, r) => a + r.count, 0) / data.length).toFixed(1);
    const peak = Math.max(...data.map(r => r.count));
    const high = data.filter(r => r.level === 'High').length;
    cards = `<div class="summ-card" style="--acc:var(--crowd);--ibg:var(--crowd-dim)"><div class="summ-icon">📋</div><div><div class="summ-lbl">Total Records</div><div class="summ-val" style="--vc:var(--crowd)">${data.length}</div></div></div>
      <div class="summ-card" style="--acc:#60a5fa;--ibg:rgba(96,165,250,.12)"><div class="summ-icon">👥</div><div><div class="summ-lbl">Avg Count</div><div class="summ-val" style="--vc:#60a5fa">${avg}</div></div></div>
      <div class="summ-card" style="--acc:var(--green);--ibg:rgba(74,222,128,.12)"><div class="summ-icon">📈</div><div><div class="summ-lbl">Peak Count</div><div class="summ-val" style="--vc:var(--green)">${peak}</div></div></div>
      <div class="summ-card" style="--acc:var(--red);--ibg:rgba(248,113,113,.12)"><div class="summ-icon">⚠</div><div><div class="summ-lbl">High-Level Frames</div><div class="summ-val" style="--vc:var(--red)">${high}</div></div></div>`;
  } else if (type === 'vehicle') {
    const avg = (data.reduce((a, r) => a + r.total, 0) / data.length).toFixed(1);
    const peak = Math.max(...data.map(r => r.total));
    cards = `<div class="summ-card" style="--acc:var(--veh);--ibg:var(--veh-dim)"><div class="summ-icon">📋</div><div><div class="summ-lbl">Total Records</div><div class="summ-val" style="--vc:var(--veh)">${data.length}</div></div></div>
      <div class="summ-card" style="--acc:#60a5fa;--ibg:rgba(96,165,250,.12)"><div class="summ-icon">🚗</div><div><div class="summ-lbl">Avg Vehicles</div><div class="summ-val" style="--vc:#60a5fa">${avg}</div></div></div>
      <div class="summ-card" style="--acc:var(--green);--ibg:rgba(74,222,128,.12)"><div class="summ-icon">📈</div><div><div class="summ-lbl">Peak Count</div><div class="summ-val" style="--vc:var(--green)">${peak}</div></div></div>
      <div class="summ-card" style="--acc:var(--amber);--ibg:rgba(251,146,60,.12)"><div class="summ-icon">📊</div><div><div class="summ-lbl">Cameras</div><div class="summ-val" style="--vc:var(--amber)">${[...new Set(data.map(r => r.video_id))].length}</div></div></div>`;
  } else if (type === 'parking') {
    const avgRate = (data.reduce((a, r) => a + (r.rate || 0), 0) / data.length).toFixed(1);
    const fullCount = data.filter(r => r.status === 'Lot Full').length;
    cards = `<div class="summ-card" style="--acc:var(--park);--ibg:var(--park-dim)"><div class="summ-icon">📋</div><div><div class="summ-lbl">Total Records</div><div class="summ-val" style="--vc:var(--park)">${data.length}</div></div></div>
      <div class="summ-card" style="--acc:var(--amber);--ibg:rgba(251,146,60,.12)"><div class="summ-icon">📉</div><div><div class="summ-lbl">Avg Occupancy</div><div class="summ-val" style="--vc:var(--amber)">${avgRate}%</div></div></div>
      <div class="summ-card" style="--acc:var(--red);--ibg:rgba(248,113,113,.12)"><div class="summ-icon">🚫</div><div><div class="summ-lbl">Times Full</div><div class="summ-val" style="--vc:var(--red)">${fullCount}</div></div></div>
      <div class="summ-card" style="--acc:var(--green);--ibg:rgba(74,222,128,.12)"><div class="summ-icon">✅</div><div><div class="summ-lbl">Avg Free</div><div class="summ-val" style="--vc:var(--green)">${(data.reduce((a, r) => a + (r.available || 0), 0) / data.length).toFixed(0)}</div></div></div>`;
  } else if (type === 'alerts') {
    cards = `<div class="summ-card" style="--acc:var(--red);--ibg:rgba(248,113,113,.12)"><div class="summ-icon">🚨</div><div><div class="summ-lbl">Total Alerts</div><div class="summ-val" style="--vc:var(--red)">${data.length}</div></div></div>
      <div class="summ-card" style="--acc:var(--crowd);--ibg:var(--crowd-dim)"><div class="summ-icon">🫂</div><div><div class="summ-lbl">Crowd Alerts</div><div class="summ-val" style="--vc:var(--crowd)">${data.filter(r => r.alert_key?.includes('crowd')).length}</div></div></div>
      <div class="summ-card" style="--acc:var(--veh);--ibg:var(--veh-dim)"><div class="summ-icon">🚗</div><div><div class="summ-lbl">Vehicle Alerts</div><div class="summ-val" style="--vc:var(--veh)">${data.filter(r => r.alert_key?.includes('vehicle')).length}</div></div></div>
      <div class="summ-card" style="--acc:var(--park);--ibg:var(--park-dim)"><div class="summ-icon">🅿</div><div><div class="summ-lbl">Parking Alerts</div><div class="summ-val" style="--vc:var(--park)">${data.filter(r => r.alert_key?.includes('parking')).length}</div></div></div>`;
  } else if (type === 'complaints') {
    const open = data.filter(r => r.status === 'Open').length;
    const res = data.filter(r => r.status === 'Resolved').length;
    cards = `<div class="summ-card" style="--acc:var(--user);--ibg:var(--user-dim)"><div class="summ-icon">📋</div><div><div class="summ-lbl">Total</div><div class="summ-val" style="--vc:var(--user)">${data.length}</div></div></div>
      <div class="summ-card" style="--acc:var(--red);--ibg:rgba(248,113,113,.12)"><div class="summ-icon">🔴</div><div><div class="summ-lbl">Open</div><div class="summ-val" style="--vc:var(--red)">${open}</div></div></div>
      <div class="summ-card" style="--acc:var(--green);--ibg:rgba(74,222,128,.12)"><div class="summ-icon">✅</div><div><div class="summ-lbl">Resolved</div><div class="summ-val" style="--vc:var(--green)">${res}</div></div></div>
      <div class="summ-card" style="--acc:var(--amber);--ibg:rgba(251,146,60,.12)"><div class="summ-icon">🟡</div><div><div class="summ-lbl">In Progress</div><div class="summ-val" style="--vc:var(--amber)">${data.length - open - res}</div></div></div>`;
  }
  el.innerHTML = cards;
}

async function loadHistory(type, btn) {
  currentHistType = type;
  histData = [];
  document.querySelectorAll('[data-ht]').forEach(b => b.classList.toggle('active', b.dataset.ht === type));
  const titles = { crowd: 'Crowd Detection History', vehicle: 'Vehicle Detection History', parking: 'Parking History', alerts: 'Alert Log', complaints: 'Complaint Log' };
  set('hist-table-title', titles[type] || 'History');
  set('hist-count', 'Loading…');
  const tbody = $('hist-tbody');
  if (tbody) tbody.innerHTML = `<tr><td colspan="8" style="padding:28px;text-align:center;color:var(--t3)"><div class="spin" style="margin:0 auto;border-top-color:var(--primary)"></div></td></tr>`;
  try {
    const r = await fetch(`${API}/api/history/${type}`, { signal: AbortSignal.timeout(8000) });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const d = await r.json();
    histData = d.data || [];
    renderHistTable(histData);
    renderHistStats(histData, type);
    if ($('hist-search')) $('hist-search').value = '';
  } catch (e) {
    if (tbody) tbody.innerHTML = `<tr><td colspan="8" style="padding:28px;text-align:center;color:var(--red);font-size:12px">✗ Failed to load: ${e.message}</td></tr>`;
    set('hist-count', 'Error');
  }
}

function exportCSV() {
  if (!histData.length) { toast('No data to export', 'warn'); return; }
  const cols = HIST_COLS[currentHistType] || [];
  const keys = Object.keys(histData[0]);
  const header = cols.join(',');
  const rows = histData.map(r => keys.map(k => `"${String(r[k] ?? '').replace(/"/g, '""')}"`).join(','));
  const csv = [header, ...rows].join('\n');
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `kumbheye_${currentHistType}_${Date.now()}.csv`;
  a.click();
  URL.revokeObjectURL(url);
  toast('✓ CSV exported', 'success');
}
