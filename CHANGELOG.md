# ClawTasker CEO Console — Changelog

## v1.6.0 — Autonomous Execution Layer (2026-04-03)

### New API Endpoints
- `GET /api/tasks/next?owner={agent_id}[&project={id}]` — returns next eligible task for an agent (ready, unblocked, highest priority). Bearer auth required.
- `POST /api/tasks/event` — shorthand event publisher: `{type, task_id, agent_id, note?}`. Types: `started`, `blocked`, `done`, `needs-validation`. Adds comment + updates status in one call.
- `GET /api/tasks/templates` — returns 6 predefined task templates (no auth required).

### New Snapshot Fields
- `exception_dashboard` — four-bucket CEO exception view: blocked, validation, stale (3+ days), overdue. Available on every `GET /api/snapshot`.
- `has_unresolved_blockers` (per task) — true if depends_on or is-blocked-by links point to non-done tasks.
- `stale` (per task) — true if no status update in 3+ days.

### GUI Improvements
- **Pipeline → Lanes sub-view**: per-agent queue health cards showing ready/active/blocked counts and top tasks
- **Pipeline → List view**: blocked badge on tasks with unresolved blockers
- **Dashboard attention queue**: replaced with 4-bucket exception dashboard (blocked, needs approval, stale, overdue) — clickable items open task detail
- **Task creation**: "📋 Use template" button opens template chooser; AC warning banner when advancing status without acceptance criteria
- **Task edit**: Artifacts field (one per line) for linking output files, docs, and URLs
- **Task detail**: Artifacts displayed as clickable chips

### Agent Onboarding
- See `docs/AGENT_API_GUIDE.md` for the updated agent operating loop

## vNext — Task Field Completeness + Linked Issues + Activity Log (2026-03-27)

### Added
- **Task `type` field** — classify tasks as `bug`, `story`, `task`, `spike`, or `epic`; settable on create and via update; GUI create/edit modals show type selector; invalid values fall back to `"task"`
- **Task `reporter` field** — records who filed the task; set on creation from `reporter`/`author` field (defaults to `"ceo"`); shown read-only in task detail view
- **Task `acceptance_criteria` field** — structured list of completion conditions (distinct from DoD); editable in create/edit modals; shown as checklist in task detail view
- **Task `links` field + `POST /api/tasks/link`** — typed bidirectional links between tasks; types: `relates-to`, `duplicates`, `blocks`, `is-blocked-by`, `child-of`, `parent-of`; symmetric reverse link added automatically; deleting a task removes dangling links on other tasks
- **Task `assignees` field** — list of all assigned agent IDs; mirrors `owner` as the primary assignee
- **Task `activity` log** — `update_task()` appends `{id, author, action, field, from, to, timestamp}` entries for `status`, `owner`, `priority`, and `horizon` changes; shown in task detail view below comments
- **`POST /api/agents/update`** — update agent name, role, emoji, skills, org_level via API
- **`POST /api/agents/delete`** — permanently remove an agent; protects chief; unassigns tasks and missions; GUI team view remove button now calls this endpoint
- **Mission `status` dropdown** — mission form now shows Status field (draft/active/blocked/completed)
- **Mission `success_criteria` field** — mission form now shows Success Criteria textarea; previously always saved as `[]`
- **GUI task create/edit modals** — expanded with type selector, sprint/horizon/validator selectors, labels, blocked checkbox, Acceptance Criteria + DoD textareas
- **Team chart** — managers identified by `org_level === "manager"` (was hardcoded agent ID list)
- **Version single source of truth** — `APP_VERSION` reads from `VERSION` file; `build_ui.py` injects version into HTML; tests use dynamic `_EXPECTED_VERSION`

### Fixed
- Mission status and success_criteria were always reset on every save (ignored form values)
- Team chart managers were hard-coded to specific agent IDs

### Migration
- Existing tasks gain: `type`, `reporter`, `acceptance_criteria`, `links`, `assignees`, `activity` — automatic on first load, no data lost

---

## vNext — CRUD + Comments (2026-03-27)

### Added
- `POST /api/tasks/create` — create tasks directly (AI agents and GUI); auto-generates ID; returns enriched task object
- `POST /api/tasks/delete` — permanently delete a task; cleans mission `task_ids` lists and dependency chains
- `POST /api/tasks/comment` — append `{author, text, timestamp}` comment to any task; persists across restarts
- `POST /api/missions/delete` — delete mission; tasks preserved with `mission_id` cleared
- `POST /api/sprints/delete` — delete sprint; assigned tasks become unsprinted (`sprint_id` set to null)
- `POST /api/projects/delete` — delete project (`ceo-console` protected from deletion)
- `POST /api/agents/retire` — mark agent offline; optionally transfer tasks/missions to successor
- `POST /api/agents/replace` — transfer all assignments from old agent to new; retire old agent
- `POST /api/agents/merge` — absorb source agent into target (tasks, missions, skills); retire source
- `POST /api/blank/reset` — reset to minimal blank state (no demo data)
- `POST /api/org/bootstrap` — apply company info + agent/project manifest to blank state
- GUI: task detail modal shows comments thread + inline "Add comment" input
- GUI: Edit and Delete action buttons on task detail modal
- GUI: task create/edit/reassign operations now persist via API with optimistic fallback
- GUI: mission create/edit persists via `POST /api/missions/plan`
- GUI: pipeline and mission delete buttons call server delete endpoints

### Fixed
- `/api/agents/decommission` route: removed undefined `check_auth()` calls that caused `NameError` crashes
- `/api/agents/decommission` route: replaced undefined `body` variable with `payload`
- Removed duplicate dead-code route blocks for decommission and org/configure
- `decommission_agent()` now emits `agent_decommission` event to event log (previously silent)
- Fixed 6 additional route blocks (`org/configure`, `sprints/create`, `sprints/update`, `projects/configure`, `notifications/dismiss`) with same `check_auth`/`body` bugs

### Migration
- Existing `state.json` files are automatically migrated on first load: all tasks gain `comments: []`
- No manual action required; data is never lost on upgrade

---

## v1.5.0 — 2026-03-22 (Architecture Modularization Phase 6: GitHub Release)

**Release Date:** 2026-03-22
**Base:** v1.4.1 → v1.5.0
**Build:** `python3 scripts/build_ui.py` — Python-only, no Node.js dependency
**Verification:** `python3 scripts/verify_build.py` — 137/137 checks pass

### Architecture Modularization — Complete
All 6 phases implemented:
- Phase 1 (v1.2.0): Bug fixes, surgical merge — ✅
- Phase 2/3 (v1.3.0): CSS extraction, data constants, feature improvements — ✅
- Phase 4 (v1.4.0): Monolith decomposition into 38 sections with build pipeline — ✅
- Phase 5 (v1.4.1): Section reorganization into 19 logical modules — ✅
- Phase 6 (v1.5.0): main.js, CI pipeline, legacy cleanup, docs, bug fixes, new tabs — ✅

### Added — New Tabs
- **Council** tab — decision log, executive reviews, team alignment. Shows decision cards with participants, priority, and status (decided/action-required/pending). Sidebar under Operate section.
- **Pipeline** tab — full task backlog as a filterable table. Filter by project and status. Sortable by workflow priority. Shows ID, title, status badge, owner, project, and story points. Sidebar under Work section.
- **Approvals** tab — tasks awaiting CEO review, validation, or sign-off. Shows pending count badge, task cards with approve/return buttons. Sidebar under Work section.

### Added — Build & CI
- **`main.js` entry point** — documents all 21 modules and their load order
- **`scripts/verify_build.py`** — 137-check CI verification script
- **`views/council-pipeline-approvals.js`** — new module (4 functions: buildCouncil, renderPipeline, buildApprovals, openCouncilEntry)

### Fixed — Critical Bugs
- **App crash on load** — `main.js` was calling `document.querySelector('.sb-item')` which returned null (sidebar buttons use class `nv`). This caused a TypeError that killed the entire app. Fixed by removing the broken handler; the real bootstrap lives in `ui/api.js` → `loadSnapshot().then(startPolling)`.
- **Wrong version displayed** — 4 hardcoded version strings in HTML body template ("v1.2.0", "v1.0.5") were not updated by the build pipeline. Fixed by updating `ui/src/templates/body.html` to show v1.5.0 in sidebar brand, footer badge, topbar pill, and theme section.

### Updated Documentation (all aligned to v1.5.0)
- `README.md` — complete rewrite: module structure, build instructions, project map, API overview
- `CHANGELOG.md` — full release history v1.0.5 → v1.5.0
- `BILL_OF_MATERIALS.md` — v1.5.0 build pipeline section
- `docs/ARCHITECTURE.md` — system diagram, module inventory, build pipeline, design decisions
- `docs/AGENT_PROMPTS.md` — v1.5.0 architecture notes, updated onboarding flow
- `RELEASE_CHECKLIST.md` — v1.5.0 checklist

### Removed
- `ui/src/sections/` — 38 legacy section files (superseded by `ui/src/modules/`)

### Changed
- `VERSION` → 1.5.0
- `ui/dist/index.html` — now a build artifact with 14 view containers, 113 functions, 21 modules
- `ui/src/build-manifest.json` — 21 modules, IIFE deferred
- Sidebar reorganized: Operate (Dashboard, Team, Council, Calendar), Work (Board, Pipeline, Approvals, Missions, Conversations), Observe (Office, Access), Quality (Requirements, Test Cases), Settings (Appearance)

---

## v1.4.1 — 2026-03-22 (Architecture Modularization Phase 5: Module Reorganization)

**Release Date:** 2026-03-22
**Base:** v1.4.0 (516 files → 537 files)
**Build:** `python3 scripts/build_ui.py` — Python-only, no Node.js dependency

### Added
- **Module reorganization script**: `scripts/reorganize_modules.py` — merges 38 section files into 19 logical modules
- **19 logical modules** in `ui/src/modules/` organized by concern:

  | Module | Sections Merged | Size |
  |--------|----------------|------|
  | `data/constants.js` | 00-data | 157KB |
  | `state/store.js` | 01-state | 1KB |
  | `lib/router.js` | 02-nav | 1KB |
  | `lib/dom.js` | 03-util | 2KB |
  | `lib/theme.js` | 04-mode | 1KB |
  | `views/dashboard.js` | 05-dashboard + 19-capability-matrix + 20-project-health + 21-export-snapshot(part) + 31-notifications + 32-active-focus + 33-directives | 19KB |
  | `views/team.js` | 06-org-chart + 07-agent-roster + 16-sprite-modal + 17-org-config | 16KB |
  | `views/board.js` | 08-board + 30-sprint-management | 3KB |
  | `ui/modals.js` | 09-task-modal + 18-task-creation | 8KB |
  | `views/missions.js` | 10-mission-planner | 9KB |
  | `views/conversations.js` | 11-conversations | 1KB |
  | `views/calendar.js` | 12-calendar | 7KB |
  | `views/office.js` | 13-office | 3KB |
  | `views/access.js` | 14-access-matrix | 2KB |
  | `views/appearance.js` | 15-appearance | 4KB |
  | `lib/office-engine.js` | 21-export-snapshot(office constants) + 22-29(engine) | 22KB |
  | `ui/onboarding.js` | 34-init + 35-platform-onboarding-modal | 4KB |
  | `ui/api.js` | 36-live-api-wiring | 3KB |
  | `views/requirements.js` | 37-requirements-test-cases | 12KB |

- **Section splitting**: Section 21 (export-snapshot) was split — export function → `views/dashboard.js`, office engine constants → `lib/office-engine.js`
- Updated `scripts/build_ui.py` v3 — supports both legacy `js_sections` and new `js_modules` manifest format

### Build Verification
- 109/109 functions present in built output
- 11/11 view containers present
- 13/13 key constants (AGENTS, PT, SPR, HEADS, GAME_W, GAME_ZONES, etc.) declared before first use
- All dependency orderings verified (GAME_W before initCanvasOffice, AGENTS before buildDashboard, META before goV)
- **Note**: v1.4.1 build is NOT byte-identical to v1.3.0 — section order is reorganized by concern. It IS functionally equivalent.

### Changed
- `VERSION` → 1.4.1
- `ui/dist/index.html` title → "ClawTasker CEO Console v1.4.1"
- `ui/src/build-manifest.json` — now uses `js_modules` key pointing to `modules/` directory

### Architecture Notes
- Legacy `ui/src/sections/` preserved for reference and parity testing
- Build with `js_sections` still produces v1.3.0-parity output
- Build with `js_modules` produces reorganized but functionally equivalent output
- **Phase 6 (v1.5.0)**: Wire main.js entry point, add IIFE wrapper, full CI pipeline, delete legacy sections/

---

## v1.4.0 — 2026-03-22 (Architecture Modularization Phase 4: Monolith Decomposition)

**Release Date:** 2026-03-22
**Base:** v1.3.0 corrected project (452 files → 516 files)
**Build:** `python3 scripts/build_ui.py` — Python-only, no Node.js dependency

### Added
- **Build pipeline**: `scripts/build_ui.py` — assembles `ui/dist/index.html` from modular source files
- **Extraction tool**: `scripts/modularize_v2.py` — decomposes monolith into modular sources
- **Build manifest**: `ui/src/build-manifest.json` — declares CSS, HTML, JS concatenation order
- **38 JS section modules** in `ui/src/sections/` — each monolith section extracted as an individual file:
  - `00-data.js` (156KB) — all data constants (AGENTS, PT, SPR, HEADS, DAY_MAP, NIGHT_MAP, CAL, AM, etc.)
  - `01-state.js` — state variables (darkMode, activePreset, ceoPortrait, etc.)
  - `02-nav.js` — navigation router (goV function, META breadcrumbs)
  - `03-util.js` — DOM utilities (mk, txt, relTime, mkPortrait, mkFaceAv, mkSprite)
  - `04-mode.js` — dark/light mode (toggleMode, applyMode)
  - `05-dashboard.js` — dashboard view (buildDashboard)
  - `06-org-chart.js` — org chart (buildOrg, mkOrgCard)
  - `07-agent-roster.js` — agent roster (buildRoster)
  - `08-board.js` — board view (LIFECYCLE, renderBoard refs)
  - `09-task-modal.js` — task detail modal (openTask, reassignTask, closeMo)
  - `10-mission-planner.js` — mission planner (buildMissions, mkMissionCard)
  - `11-conversations.js` — conversations view (renderThread, switchT, sendMsg)
  - `12-calendar.js` — calendar views (renderCal, renderWeek, renderMonth, renderYear)
  - `13-office.js` — office view shell (buildOffice, setScene)
  - `14-access-matrix.js` — access matrix view (buildAccess)
  - `15-appearance.js` — appearance/settings view
  - `16-sprite-modal.js` — sprite picker modal
  - `17-org-config.js` — org edit/decommission (openOrgEdit, openFullOrgEdit, confirmDecommission)
  - `18-task-creation.js` — new task form (openNewTaskForm, submitNewTask)
  - `19-capability-matrix.js` — capability matrix dashboard card
  - `20-project-health.js` — project health dashboard card
  - `21-export-snapshot.js` — export/snapshot functionality
  - `22-37: Office engine` — pickFreeSlot, initCanvasOffice, offTick, _pickNextDestination, _drawSprite, _drawSpeechBubble, showOfficeTooltip, setGameScene, randomiseAgents, buildScrumList
  - `30-sprint-management.js` — sprint CRUD
  - `31-notifications.js` — notification system
  - `32-active-focus-period-dashboard-card.js` — focus period card
  - `33-directives-trail.js` — CEO directives trail
  - `35-platform-onboarding-modal.js` — onboarding wizard
  - `36-live-api-wiring-option-a.js` — SSE/API integration
  - `37-requirements-test-cases-v1-2-0.js` — requirements & test cases views
- **CSS module**: `ui/src/styles/monolith.css` — complete extracted CSS (36,883 bytes)
- **HTML templates**: `ui/src/templates/` — head.html, body.html, tail.html

### Build Pipeline Verification
- Build with `python3 scripts/build_ui.py 1.3.0` produces **byte-identical** output to the v1.3.0 monolith
- Build with `python3 scripts/build_ui.py 1.4.0` produces output differing **only** in the version string
- No content loss, no reordering, no functional changes

### Changed
- `VERSION` → 1.4.0
- `ui/dist/index.html` title → "ClawTasker CEO Console v1.4.0"
- `ui/dist/index.html` is now a **build artifact** produced by `scripts/build_ui.py`

### Architecture Notes
- **Build strategy**: Concatenation — all JS sections concatenated in dependency order, wrapped in `<script>` tags
- **No IIFE yet** — sections share the global scope (same as monolith behavior)
- **Phase 5 (v1.4.x)**: Reorganize sections into logical modules (views/, lib/, data/, state/, ui/)
- **Phase 6 (v1.5.0)**: Wire main.js entry point, add IIFE wrapper, full CI pipeline

---

## v1.3.0 — 2026-03-22 (Architecture Modularization Phase 2/3 + Features)

### Added
- Office: **Enhanced sprite labels** — characters now show name + status text (WORKING/BLOCKED/IDLE/OFFLINE) + colored status dot below sprite
- Office: **Kitchen zone** (3 slots) — agents take coffee breaks here during idle time
- Office: **Conference zone** (6 slots) — working/validation agents visit for meetings
- Office: **Furniture collision physics** — 14 `FURNITURE_RECTS` collision rectangles for desks, tables, counters; agents are pushed out of furniture areas during movement
- Office: **Task-aware movement AI** — working agents visit scrum table/conference; idle agents visit kitchen; validation agents visit review rail
- Office: **All-status speech bubbles** — working ("On it…", "📝 Focused"), idle ("☕ Break", "Ready"), blocked ("🚫 Stuck"), validation ("🔍 QA pass")
- Team: **Missing agent detection** — stale heartbeat (>10min) triggers "⚠ MISSING" flag + "heartbeat stale" indicator + "🗑 Remove agent" button
- Team: **Manual agent deletion** — missing/offline agents show removal button linked to `confirmDecommission()` flow

### Fixed
- Profile pictures: **Head rendering fix** — `face-av` CSS changed to `object-position: center 15%` with `transform: scale(1.08)` to eliminate neck gap and center heads properly in circular avatars

### Changed
- `VERSION` → 1.3.0
- `ui/dist/index.html` title → "ClawTasker CEO Console v1.3.0"
- Total GAME_ZONES: 10 → 12
- `_drawSprite()`: simple name label → enhanced pill with name + status + dot
- `_pickNextDestination()`: 2-status logic → 4-status task-aware AI with kitchen/conference routing
- Speech bubble trigger rate: 25% blocked/validation only → 18% all statuses

### Verification
- 38/38 tests passing (structure: 4, assets: 3, views: 11, agents: 13, features: 7)
- Full BOM check: all 14 portraits, 14 sprites, 14 heads, 23 textures, 9 JS modules, 56 vendor files, 11 view containers confirmed present

---

## v1.2.0 — 2026-03-21

### Added
- Calendar: **ISO week numbers** (W1–W53) as a left column in Month and Week views
- Calendar: **Day view** — hour-by-hour slot grid, tasks slotted by priority
- Calendar: **Week view** — 7-day strip with task chips per day, ISO week label
- Calendar: **Year view** — 12-month mini-grid; click any month to drill into Month view
- Calendar: **View tabs** — Day · Week · Month · Year switchable tabs
- `getISOWeekNumber()` — RFC 8601 compliant ISO week calculation
- Task Ticket Modal — full Jira-style dialog (title, description, DoD, linked tasks, assignees, priority, labels, artifacts, validation owner)
- Team: Portrait picker — click any portrait to swap it from all 14 assets
- Team: Sprite picker — "Change Sprite" button per agent card
- Office: Pokémon-style zone layout with 12 named areas
- Office: Furniture (desks, monitors, sync table, agile board, coffee machine, sofas, plants)
- Office: Agent status→zone mapping (working→desk, blocked→sync, validation→review, done→kitchen)
- Office: Coffee break animation with ☕ emoji; sprite facing direction
- Office: Day/Night toggle; sprite click tooltip
- Board: 5-column layout (Backlog · Ready · In Progress · Validating · Done)
- Backlog: Shows ALL task statuses, sorted by status priority
- Requirements Management tab (create/edit/delete, P0–P3, linked tasks)
- Test Cases tab (create/edit/delete/run, PASS/FAIL/PENDING, Run All)
- `TEST_CASES_v1_2_0.md` — 30 test cases across 9 suites
- `REQUIREMENTS_v1_2_0.md` — 10 full product requirements

### Changed  
- `VERSION` → 1.2.0
- `server.py` APP_VERSION → 1.2.0; WEB_DIR corrected to `web/`
- `web/styles.css` — merged v1.0.5 full stylesheet + v1.1.0 additions + v1.2.0 calendar CSS
- `web/app.js` — `renderCalendar()` refactored into Day/Week/Month/Year sub-renderers
- Calendar grid uses `32px repeat(7, 1fr)` to accommodate week-number column

### Fixed
- v1.1.0 regression: entire `ui/` source tree, `third_party/`, `openclaw/`, `scripts/`, `tests/`, `docs/` were missing — fully restored from v1.0.5
- v1.1.0 regression: `server.py` was absent from the web release zip
- v1.1.0 regression: CSS stripped from 2689→446 lines; restored and merged
- Calendar had no week numbers and no Day/Week/Year views

---

## v1.1.0 — 2026-03-21 (internal)
Calendar nav, ticket modal (partial), team pickers, office sprites, requirements/test UI.
Known regressions: missing server.py, truncated CSS, missing entire project tree.

## v1.0.5 — 2026-03-21
Full server.py REST API, SSE, agent integration, pocket-office-quest-v9, full ui/ source tree.
