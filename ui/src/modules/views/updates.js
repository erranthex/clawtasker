// ── Updates view ─────────────────────────────────────────────────────────────

function buildUpdates() {
  // Called when the Updates tab is opened — loads version info from server
  checkForUpdates();
}

async function checkForUpdates() {
  const tok = typeof API_TOKEN !== 'undefined' ? API_TOKEN : '';
  const banner = document.getElementById('UPD_STATUS_BANNER');
  const btn = document.getElementById('UPD_BTN');
  if (banner) { banner.style.display = 'none'; }
  if (btn) btn.style.display = 'none';

  try {
    const res = await fetch('/api/system/version', {
      headers: { 'Authorization': 'Bearer ' + tok }
    });
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const d = await res.json();

    const localEl = document.getElementById('UPD_LOCAL_VER');
    const ghEl = document.getElementById('UPD_GH_VER');
    const dateEl = document.getElementById('UPD_GH_DATE');
    if (localEl) localEl.textContent = 'v' + (d.local_version || '–');
    if (ghEl) {
      ghEl.textContent = d.github_reachable ? ('v' + (d.github_version || '–')) : 'Unavailable';
      ghEl.style.color = d.update_available ? 'var(--dn)' : 'var(--go)';
    }
    if (dateEl) dateEl.textContent = d.published_at ? ('Released: ' + d.published_at.slice(0, 10)) : '';

    if (banner) {
      banner.style.display = 'block';
      if (!d.github_reachable) {
        banner.style.background = 'rgba(94,130,232,.1)';
        banner.style.border = '1px solid rgba(94,130,232,.3)';
        banner.style.color = 'var(--txs)';
        banner.textContent = 'GitHub is not reachable. Cannot check for updates — ensure you have internet access.';
      } else if (d.update_available) {
        banner.style.background = 'rgba(224,85,85,.1)';
        banner.style.border = '1px solid rgba(224,85,85,.3)';
        banner.style.color = 'var(--txs)';
        banner.textContent = 'Update available: v' + d.github_version + ' — click "Update now" to upgrade safely.';
        if (btn) btn.style.display = '';
      } else {
        banner.style.background = 'rgba(94,200,160,.1)';
        banner.style.border = '1px solid rgba(94,200,160,.3)';
        banner.style.color = 'var(--txs)';
        banner.textContent = 'You are on the latest version.';
      }
    }
  } catch (err) {
    if (banner) {
      banner.style.display = 'block';
      banner.style.background = 'rgba(224,85,85,.1)';
      banner.style.border = '1px solid rgba(224,85,85,.3)';
      banner.style.color = 'var(--txs)';
      banner.textContent = 'Could not reach server: running in standalone mode.';
    }
  }
}

async function triggerUpdate() {
  const tok = typeof API_TOKEN !== 'undefined' ? API_TOKEN : '';
  const btn = document.getElementById('UPD_BTN');
  const log = document.getElementById('UPD_LOG');
  const logPre = document.getElementById('UPD_LOG_PRE');
  const banner = document.getElementById('UPD_STATUS_BANNER');

  if (btn) { btn.disabled = true; btn.textContent = 'Updating…'; }
  if (log) log.style.display = 'none';

  try {
    const res = await fetch('/api/system/update', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + tok
      },
      body: JSON.stringify({})
    });
    const d = await res.json();

    // Build log text
    const lines = (d.steps || []).map(s =>
      (s.ok ? '✓' : '✗') + ' ' + s.step + ': ' + (s.detail || '')
    ).join('\n');

    if (logPre) logPre.textContent = lines;
    if (log) log.style.display = 'block';

    if (banner) {
      banner.style.display = 'block';
      if (d.ok) {
        banner.style.background = 'rgba(94,200,160,.1)';
        banner.style.border = '1px solid rgba(94,200,160,.3)';
        banner.textContent = (d.message || 'Update complete.') + ' Reload to apply.';
        if (btn) { btn.textContent = 'Reload page'; btn.disabled = false; btn.onclick = () => location.reload(); }
      } else {
        banner.style.background = 'rgba(224,85,85,.1)';
        banner.style.border = '1px solid rgba(224,85,85,.3)';
        banner.textContent = 'Update failed: ' + (d.error || 'Unknown error');
        if (btn) { btn.textContent = 'Update now'; btn.disabled = false; }
      }
    }
  } catch (err) {
    if (banner) {
      banner.style.display = 'block';
      banner.textContent = 'Update request failed: ' + (err.message || 'network error');
    }
    if (btn) { btn.textContent = 'Update now'; btn.disabled = false; }
  }
}
