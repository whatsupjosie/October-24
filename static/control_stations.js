/**
 * PubCast AI — control_stations.js (Phase 1 hardened)
 * Hooks into app.js via window.__pubcastStationsHook and window.__pubcastRecHandler.
 * Add to control.html: <script type="module" src="/static/control_stations.js"></script>
 */

// ── Station tab switcher ──────────────────────────────────────────────────────
(function initStations() {
  const bar = document.getElementById('stations-bar');
  if (!bar) return;
  bar.addEventListener('click', e => {
    const btn = e.target.closest('[data-station]'); if (!btn) return;
    const target = btn.dataset.station;
    document.querySelectorAll('[id^="station-"]').forEach(el => el.classList.add('hidden'));
    bar.querySelectorAll('[data-station]').forEach(b => b.classList.remove('active'));
    const panel = document.getElementById(`station-${target}`);
    if (panel) panel.classList.remove('hidden');
    btn.classList.add('active');
    if (target === 'recorder') loadRecorderStation();
  });
  // Default to director on load
  const dir = bar.querySelector('[data-station="director"]');
  if (dir) dir.click();
})();

// ── Recording station ─────────────────────────────────────────────────────────
let _timerInterval = null, _recStartTs = null;

async function loadRecorderStation() {
  await refreshStorage();
}

async function refreshStorage() {
  const el = document.getElementById('rec-storage'); if (!el) return;
  try {
    const s = await fetch('/api/recording/storage').then(r => r.json());
    el.innerHTML = `Local free: <strong>${s.local_free_gb??'—'} GB</strong> &nbsp;·&nbsp;
      Recorded: <strong>${s.recorded_gb??0} GB</strong> &nbsp;·&nbsp;
      Cloud: <strong>${s.cloud_used_gb??'—'} GB</strong> &nbsp;·&nbsp;
      Backup: <strong>${s.backup_status??'—'}</strong>`;
  } catch(_) { el.innerText = 'Storage info unavailable.'; }
}
document.getElementById('rec-storage-refresh')?.addEventListener('click', refreshStorage);

function startRecTimer(startedAt) {
  _recStartTs = startedAt || (Date.now() / 1000);
  stopRecTimer(); // clear any existing
  setBadge('REC', '#c22');
  const panel = document.getElementById('rec-active-panel'); if (panel) panel.style.display = 'block';
  _timerInterval = setInterval(() => {
    const sec = Math.floor(Date.now()/1000 - _recStartTs);
    const t = document.getElementById('rec-active-timer');
    if (t) t.innerText = `${pad(Math.floor(sec/3600))}:${pad(Math.floor((sec%3600)/60))}:${pad(sec%60)}`;
  }, 1000);
}
function stopRecTimer() {
  if (_timerInterval) { clearInterval(_timerInterval); _timerInterval = null; }
  setBadge('IDLE', '#555');
  const panel = document.getElementById('rec-active-panel'); if (panel) panel.style.display = 'none';
}
function setBadge(text, color) {
  const b = document.getElementById('rec-status-badge'); if (!b) return;
  b.innerText = text; b.style.background = color;
}
function pad(n) { return String(n).padStart(2,'0'); }

// Register as the recording event handler for app.js to call
window.__pubcastRecHandler = function(ev) {
  if (ev.type === 'recording_started') {
    startRecTimer(ev.payload.started_at);
    const idEl = document.getElementById('rec-active-id');
    if (idEl) idEl.innerText = ev.payload.session_id;
  }
  if (ev.type === 'recording_stopped' || ev.type === 'recording_archived') stopRecTimer();
  if (ev.type === 'recording_paused')  setBadge('PAUSED', '#a80');
  if (ev.type === 'recording_resumed') setBadge('REC', '#c22');
};

// General WS hook (receives all events from app.js onWsEvent)
window.__pubcastStationsHook = function(ev) {
  // Forward recording events to the rec handler
  if (ev.type.startsWith('recording_') && typeof window.__pubcastRecHandler === 'function') {
    window.__pubcastRecHandler(ev);
  }
};

// ── Chyron ────────────────────────────────────────────────────────────────────
document.getElementById('chy-apply')?.addEventListener('click', async () => {
  const lower = document.getElementById('chy-lower')?.value || '';
  try {
    await fetch('/api/state/production', {method:'POST',
      headers:{'Content-Type':'application/json'}, body: JSON.stringify({lower_third: lower})});
  } catch(e) { console.warn('Chyron failed', e); }
});

// ── Teleprompter ──────────────────────────────────────────────────────────────
let _proTimer = null;
document.getElementById('pro-start')?.addEventListener('click', () => {
  const el = document.getElementById('pro-script'); if (!el||!el.value.trim()) return;
  const spd = parseFloat(document.getElementById('pro-speed')?.value||'5') * 0.4;
  if (_proTimer) clearInterval(_proTimer);
  _proTimer = setInterval(() => { el.scrollTop += spd; }, 50);
});
document.getElementById('pro-stop')?.addEventListener('click', () => {
  if (_proTimer) { clearInterval(_proTimer); _proTimer = null; }
});

// ── VTR ───────────────────────────────────────────────────────────────────────
async function prodPatch(patch) {
  await fetch('/api/state/production',{method:'POST',
    headers:{'Content-Type':'application/json'}, body:JSON.stringify(patch)});
}
document.getElementById('vtr-load')?.addEventListener('click', async () => {
  const a = document.getElementById('vtr-asset')?.value; if (!a) return;
  await prodPatch({mode:'REPLAY', replay_asset: a});
});
document.getElementById('vtr-play')?.addEventListener('click', () => prodPatch({on_air:true}));
document.getElementById('vtr-stop')?.addEventListener('click', () => prodPatch({on_air:false}));

// ── Audio mixer ───────────────────────────────────────────────────────────────
document.getElementById('mixer-apply')?.addEventListener('click', () => {
  const pgm  = document.getElementById('mixer-program')?.value;
  const host = document.getElementById('mixer-hosts')?.value;
  const mus  = document.getElementById('mixer-music')?.value;
  console.log(`Audio mix — PGM:${pgm} Hosts:${host} Music:${mus}`);
  // Phase 2: POST to /api/audio/mix
});

// ── Keyboard shortcuts (Space/C = Cut, F = Fade) ──────────────────────────────
document.addEventListener('keydown', e => {
  if (['INPUT','TEXTAREA','SELECT'].includes(e.target.tagName)) return;
  if (e.code==='Space'||e.key==='c'||e.key==='C') { e.preventDefault(); document.getElementById('vm-cut')?.click(); }
  if (e.key==='f'||e.key==='F') { e.preventDefault(); document.getElementById('vm-take')?.click(); }
});
