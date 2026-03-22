// ── ClawTasker CEO Console v1.5.0 — main.js ──────────────────────────────
//
// Module load order (concatenated by scripts/build_ui.py):
//   1. data/constants.js      — PT, SPR, HEADS, AGENTS, CAL, AM, etc.
//   2. state/store.js         — darkMode, META, ceoPortrait, etc.
//   3. lib/router.js          — goV(), breadcrumb navigation
//   4. lib/dom.js             — mk(), txt(), mkPortrait(), mkFaceAv(), mkSprite()
//   5. lib/theme.js           — toggleMode(), applyMode()
//   6. views/dashboard.js     — buildDashboard() + widgets
//   7. views/team.js          — buildOrg(), buildRoster(), sprite modal, org config
//   8. views/board.js         — renderBoard(), sprint management
//   9. ui/modals.js           — openTask(), submitNewTask()
//  10. views/missions.js      — buildMissions(), mkMissionCard()
//  11. views/conversations.js — renderThread(), sendMsg()
//  12. views/calendar.js      — renderCal(), renderWeek(), renderMonth(), renderYear()
//  13. views/office.js        — buildOffice(), setScene()
//  14. views/access.js        — buildAccess()
//  15. views/appearance.js    — appearance/settings
//  16. lib/office-engine.js   — GAME_ZONES, initCanvasOffice(), offTick(), _drawSprite()
//  17. ui/onboarding.js       — platform onboarding modal
//  18. ui/api.js              — SSE/API live wiring (contains bootstrap: loadSnapshot())
//  19. views/requirements.js  — requirements & test cases UI
//  20. main.js                — this file (documentation only)
//
// Bootstrap: ui/api.js calls loadSnapshot().then(startPolling) at the end.
// loadSnapshot() either loads data from /api/snapshot or falls back to
// static stubs, then calls all build*() and render*() functions.
// The Dashboard (V_dash) starts visible via class="on" in the HTML markup.
// No DOMContentLoaded handler is needed.
