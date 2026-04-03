// ── Live API wiring (Option A) ─────────────────────────────────────────────
const POLL_MS = 15000;   // refresh every 15 s

function applySnapshot(snap) {
  // Populate the mutable globals the rest of the app reads
  if (snap.agents)   { AGENTS_DATA.length=0;   AGENTS_DATA.push(...snap.agents);   }
  if (snap.tasks)    { TASKS.length=0;          TASKS.push(...snap.tasks);          }
  if (snap.missions) { MISSIONS_DATA.length=0;  MISSIONS_DATA.push(...snap.missions); }
  if (snap.sprints)  { SPRINTS.length=0;        SPRINTS.push(...snap.sprints);      }
  if (snap.projects) { PROJECTS_DATA.length=0;  PROJECTS_DATA.push(...snap.projects); }
  if (snap.metrics)  { Object.assign(METRICS_DATA, snap.metrics); }
  if (snap.attention_queue) { AQ_DATA.length=0; AQ_DATA.push(...snap.attention_queue); }
  if (snap.exception_dashboard) { Object.assign(EXCEPTION_DATA, snap.exception_dashboard); }

  // Keep local AGENTS array in sync (used by office & team views)
  AGENTS.length=0;
  AGENTS_DATA.forEach(a => AGENTS.push({
    id: a.id, name: a.name, role: a.role||'', status: a.derived_status||a.status||'working',
    emoji: a.emoji||'🤖', profileHue: a.profile_hue||'teal',
    portrait: PT[a.avatar_asset_id||a.avatar_ref||a.id] || PT['ceo'],
    sprite: SPR[a.avatar_asset_id||a.avatar_ref||a.id] || SPR['ceo']
  }));

  // Refresh the live counter badge
  const unread = snap.unread_notifications || 0;
  const badge = document.getElementById('NOTIF_BADGE');
  if (badge) badge.textContent = unread > 0 ? unread : '';

  // Re-render everything
  buildDashboard();buildProjectHealth();buildActiveSprintCard();buildOrg();buildRoster();buildCapabilityMatrix();
  setCalV(calView, document.querySelector('.cal-vtab.on') || document.querySelector('.cal-vtab'));renderCal();
  renderBoard();buildMissions();renderThread(0);buildAccess();buildAppearance();
  buildSprintSelector();renderDirectiveTrail();refreshCounters();
  // Re-seed notifications only on first load
  if (!applySnapshot._seeded) { seedNotifications(); applySnapshot._seeded=true; }
  // Note: Office (canvas game) initialises lazily when the tab is opened
}

async function loadSnapshot() {
  const loadEl = document.getElementById('SNAP_LOADING');
  try {
    const res = await fetch('/api/snapshot', {
      headers: { 'Authorization': 'Bearer ' + API_TOKEN }
    });
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const snap = await res.json();
    if (loadEl) loadEl.style.display = 'none';
    applySnapshot(snap);
  } catch (err) {
    console.info('[clawtasker] Running in standalone mode (no server). Using demo data.');
    if (loadEl) loadEl.style.display = 'none';
    // Run with static stubs so the UI is not blank
    buildDashboard();buildProjectHealth();buildActiveSprintCard();buildOrg();buildRoster();buildCapabilityMatrix();
    setCalV('week',document.querySelector('.cal-vtab'));renderCal();
    renderBoard();buildMissions();renderThread(0);buildAccess();buildAppearance();
    buildSprintSelector();renderDirectiveTrail();seedNotifications();refreshCounters();
  }
}

function startPolling() {
  setInterval(async () => {
    try {
      const res = await fetch('/api/snapshot', {
        headers: { 'Authorization': 'Bearer ' + API_TOKEN }
      });
      if (res.ok) applySnapshot(await res.json());
    } catch (_) { /* silent — poll will retry */ }
  }, POLL_MS);
}

// Boot
loadSnapshot().then(startPolling);

