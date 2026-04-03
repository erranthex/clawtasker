# ClawTasker CEO Console v1.5.0 — Product Requirements

## REQ-001 · Dual-User Platform
**Priority:** P0 · **Status:** Done

### Description
The platform shall serve both human users (via GUI) and AI agents (via REST API). Every feature must be accessible through both interfaces.

### Acceptance Criteria
- [x] All CRUD operations available via GUI modals
- [x] All CRUD operations documented in API.md
- [x] Task creation, calendar events, agent registration work from both GUI and API
- [x] Standalone mode works without server (demo data)

---

## REQ-002 · Agent Management
**Priority:** P0 · **Status:** Done

### Description
Human CEOs and AI agents can add, edit, and remove AI agents. Each agent has a name, role, skills, profile picture/sprite, and reports to an orchestrator chief.

### Acceptance Criteria
- [x] Add agent via GUI with name, role, manager, skills, portrait/sprite selection
- [x] Add agent via API (POST /api/agents/register)
- [x] Edit agent (name, role) via inline editing
- [x] Remove agent via decommission flow
- [x] Agent appears in org chart, roster, office, and capability matrix
- [x] Platform supports 20+ agents

---

## REQ-003 · Task Ticket Management
**Priority:** P0 · **Status:** Done

### Description
Task tickets support full lifecycle management with rich fields. Both human and AI users can create, edit, and delete tasks linked to projects/EPICs.

### Acceptance Criteria
- [x] Create task with: title, description, assignee, priority, story points, epic/project link, DoD, mission link, status
- [x] Edit task via modal (all fields editable)
- [x] Delete task from pipeline view
- [x] Task appears on Board, Pipeline, and Approvals views
- [x] API endpoints for create, update, delete

---

## REQ-004 · Calendar Event Management
**Priority:** P0 · **Status:** Done

### Description
Calendar supports interactive event creation with day, time, agent assignment, category, and recurring options. Both GUI and API users can manage events.

### Acceptance Criteria
- [x] Add event via GUI modal
- [x] Edit event (title, time, agent)
- [x] Delete event
- [x] API endpoint for event creation
- [x] Events appear in week/month/year views

---

## REQ-005 · Council Decision Management
**Priority:** P1 · **Status:** Done

### Description
Council tab records executive decisions with CRUD operations.

### Acceptance Criteria
- [x] Add decision via GUI (title, summary, status, priority)
- [x] Edit decision
- [x] Delete decision
- [x] Decisions show participants, date, and status

---

## REQ-006 · Mission Management
**Priority:** P0 · **Status:** Done

### Description
Mission briefs can be created, edited, and deleted by both humans and AI agents.

### Acceptance Criteria
- [x] Create mission with title, objective, agents, success criteria, dependencies
- [x] Edit mission (all fields)
- [x] Delete mission from card view
- [x] Mission links to tasks

---

## REQ-007 · Pipeline & Approvals
**Priority:** P0 · **Status:** Done

### Description
Pipeline shows full task backlog filterable by project and status. Approvals tab shows tasks awaiting CEO validation.

### Acceptance Criteria
- [x] Pipeline table with filter by project and status
- [x] Create/edit/delete tasks from pipeline
- [x] Approvals shows validation tasks with approve/return buttons
- [x] Dynamic counter updates on all changes

---

## REQ-008 · Virtual Office
**Priority:** P1 · **Status:** Done

### Description
2D canvas office with animated agents showing status-based behavior, furniture collision, and full legend.

### Acceptance Criteria
- [x] Agents show name + status label + colored dot
- [x] Legend shows all 5 states: Working, Blocked, Validation, Idle, Offline
- [x] Furniture collision physics
- [x] Kitchen + conference zones
- [x] Day/night mode toggle
- [x] Click agent to inspect (tooltip)

---

## REQ-009 · Dynamic Counters
**Priority:** P1 · **Status:** Done

### Description
All counters in the UI update dynamically when data changes. No hardcoded values.

### Acceptance Criteria
- [x] Agent count in topbar, team, capability matrix
- [x] Task count on board
- [x] Project/entity count on access matrix
- [x] Counters refresh on every CRUD operation

---

## REQ-010 · Data Persistence Architecture
**Priority:** P1 · **Status:** Planned

### Description
SQLite database for persistent storage of all platform items.

### Acceptance Criteria
- [x] SQLite schema defined (schemas/database.sql)
- [ ] Server integration with SQLite (planned v1.6.0)
- [ ] Data persists across browser sessions
- [ ] Search and retrieval of items

---

## REQ-011 · Direct Task Create & Delete
**Priority:** P0 · **Status:** Done

### Description
Tasks can be created and deleted directly via API endpoint and GUI, without requiring a mission or conversation as an intermediary. Deletions clean up all downstream references.

### Acceptance Criteria
- [x] `POST /api/tasks/create` — accepts title (required) + all optional task fields; auto-generates ID; returns enriched task object
- [x] `POST /api/tasks/delete` — permanently removes task; cleans mission `task_ids` lists and dependency chains (`depends_on` / `blocking`)
- [x] GUI task creation modal (`openNewTaskForm`) persists via API; falls back to optimistic local insert on error
- [x] GUI task detail modal has Edit and Delete action buttons
- [x] GUI pipeline table delete button (`×`) persists via API
- [x] New tasks initialised with `comments: []`

---

## REQ-012 · Task Comments
**Priority:** P1 · **Status:** Done

### Description
Any task can have a thread of comments, each with author, text, and timestamp. Comments are appendable by both human operators (GUI) and AI agents (API).

### Acceptance Criteria
- [x] `POST /api/tasks/comment` — appends `{id, author, text, timestamp}` to `task.comments[]`; returns comment object
- [x] Task detail modal shows existing comments and an inline "Add comment" input with Post button
- [x] Comments persist across server restarts (stored in `state.json`)
- [x] Old `state.json` files without `comments` field are automatically migrated on load — no data loss
- [x] Empty text rejected with `"text is required"` error

---

## REQ-013 · Delete for Missions, Sprints, and Projects
**Priority:** P1 · **Status:** Done

### Description
Missions, sprints, and projects can be permanently deleted. Deletions are non-cascading: linked tasks, agents, and references are preserved or cleaned gracefully.

### Acceptance Criteria
- [x] `POST /api/missions/delete` — removes mission; tasks that referenced it have `mission_id` cleared; emits `mission_deleted` event
- [x] `POST /api/sprints/delete` — removes sprint; tasks assigned to it have `sprint_id` set to `None`; emits `sprint_deleted` event
- [x] `POST /api/projects/delete` — removes project; tasks and agents retain their `project_id` for history; `ceo-console` is protected from deletion; emits `project_deleted` event
- [x] GUI mission card delete button persists via API
- [x] All three endpoints available to AI agents via API

---

## REQ-014 · Task Type Classification
**Priority:** P0 · **Status:** Done

### Description
Every task carries a `type` field that classifies it as one of: `bug`, `story`, `task`, `spike`, `epic`. Type is settable on creation and updatable at any time via GUI and API.

### Acceptance Criteria
- [x] `make_task()` initialises `type` as `"task"` by default
- [x] Valid types: `bug`, `story`, `task`, `spike`, `epic`; invalid values silently fall back to `"task"`
- [x] `POST /api/tasks/create` accepts optional `type` field
- [x] `POST /api/tasks/update` accepts `type` field; validates against allowed set
- [x] Task create modal shows type selector with icons (Bug/Story/Task/Spike/Epic)
- [x] Task edit modal shows type selector
- [x] Task detail view shows type icon/chip
- [x] Old `state.json` files without `type` field are migrated to `"task"` on load

---

## REQ-015 · Task Reporter
**Priority:** P0 · **Status:** Done

### Description
Every task records a `reporter` field (who filed it), set on creation and immutable afterwards. Defaults to the `author` of the API call, or `"ceo"` if not specified.

### Acceptance Criteria
- [x] `create_task()` sets `reporter` from `payload["reporter"]` → `payload["author"]` → `"ceo"`
- [x] Reporter is not in `TASK_FIELDS` and cannot be changed via `update_task()`
- [x] Task detail view shows reporter as a read-only chip
- [x] Migration adds `reporter: "ceo"` to existing tasks without the field

---

## REQ-016 · Acceptance Criteria Field
**Priority:** P1 · **Status:** Done

### Description
Tasks support a structured `acceptance_criteria` list (distinct from Definition of Done) that specifies the conditions under which a task is considered complete.

### Acceptance Criteria
- [x] `make_task()` initialises `acceptance_criteria` as `[]`
- [x] `POST /api/tasks/create` accepts `acceptance_criteria` as a list of strings (max 10 items, 280 chars each)
- [x] `POST /api/tasks/update` accepts `acceptance_criteria` list (replaces existing)
- [x] Task create and edit modals include an Acceptance Criteria textarea (one criterion per line)
- [x] Task detail view shows acceptance criteria as a checklist section
- [x] Migration adds `acceptance_criteria: []` to existing tasks without the field

---

## REQ-017 · Linked Issues with Named Link Types
**Priority:** P1 · **Status:** Done

### Description
Tasks can be linked to each other with typed, bidirectional relationships. Supported link types: `relates-to`, `duplicates`, `blocks`, `is-blocked-by`, `child-of`, `parent-of`.

### Acceptance Criteria
- [x] `make_task()` initialises `links` as `[]`; each link entry: `{type, target_id, title}`
- [x] `POST /api/tasks/link` — creates a link from `source_id` to `target_id` with `link_type`; automatically adds symmetric reverse link on the target task
- [x] Self-links rejected with error
- [x] Duplicate links rejected with error
- [x] Invalid link type rejected with list of valid types
- [x] Deleting a task removes all links pointing to it on other tasks
- [x] Task detail view shows linked issues section with type labels and clickable chips
- [x] Migration adds `links: []` to existing tasks without the field

---

## REQ-018 · Per-Task Activity Log
**Priority:** P1 · **Status:** Done

### Description
Each task maintains an `activity` list recording field-change events (status, owner, priority, horizon) with author, old value, new value, and timestamp. Activity is recorded automatically by `update_task()`.

### Acceptance Criteria
- [x] `make_task()` initialises `activity` as `[]`
- [x] `update_task()` appends an activity entry whenever `status`, `owner`, `priority`, or `horizon` changes
- [x] Activity entry fields: `id`, `author`, `action`, `field`, `from`, `to`, `timestamp`
- [x] No entry created when a field value does not actually change
- [x] `author` defaults to `"ceo"` if not supplied in the update payload
- [x] Task detail view shows activity log below comments, in chronological order

## REQ-019: Next Eligible Task API

**Priority:** P0 (Critical)
**Status:** Implemented (v1.6.0)

AI agents must be able to query ClawTasker for their next eligible task without human intervention.

- `GET /api/tasks/next?owner={agent_id}` returns the highest-priority `ready` task assigned to the agent with no unresolved blockers
- Optional `project` query parameter filters by project_id
- Response includes full enriched task object or `null` with message "no eligible tasks"
- Requires Bearer token authentication
- Tasks are sorted by priority (P0→P3) then by oldest update first

## REQ-020: Task Event Shorthand API

**Priority:** P1 (High)
**Status:** Implemented (v1.6.0)

AI agents must be able to publish task lifecycle events without constructing full update payloads.

- `POST /api/tasks/event` accepts `{type, task_id, agent_id, note?}`
- Valid event types: `started` (→ in_progress), `blocked` (sets blocked flag), `done` (→ done), `needs-validation` (→ validation)
- Automatically adds a comment to the task with the event note
- Updates activity log
- Requires Bearer token authentication

## REQ-021: Task Templates

**Priority:** P1 (High)
**Status:** Implemented (v1.6.0)

Users and AI agents must be able to access predefined task templates to reduce ambiguity and accelerate ticket creation.

- `GET /api/tasks/templates` returns all available templates (no auth required)
- Templates include: Compliance Memo, Market Validation, GTM Plan, Founder Decision, Research Brief, Software Feature
- Each template pre-fills: description, priority, type, definition_of_done, acceptance_criteria, labels
- GUI: "📋 Use template" button in task creation modal opens template chooser

## REQ-022: Exception Dashboard

**Priority:** P1 (High)
**Status:** Implemented (v1.6.0)

The CEO dashboard must surface actionable exceptions rather than raw task data.

- Four exception buckets: Blocked, Needs Approval (validation), Stale (3+ days no update), Overdue
- Accessible via `GET /api/snapshot` in `exception_dashboard` field
- Each bucket contains up to 10 items with task_id, title, owner, status, priority
- Stale tasks include `days_stale` count
- Dashboard renders buckets with clickable items that open the task detail modal

## REQ-023: Unresolved Blocker Detection

**Priority:** P1 (High)
**Status:** Implemented (v1.6.0)

All task objects must expose whether they have unresolved blockers.

- `has_unresolved_blockers: true/false` computed field on every task in snapshot
- A blocker is unresolved if: a `depends_on` task is not `done`, or a `is-blocked-by` link points to a non-done task
- Used by: `GET /api/tasks/next` (skips blocked tasks), Lane view (shows blocked badge), Pipeline list (shows blocked chip)
- `stale: true/false` also computed: tasks with no status update in 3+ days

## REQ-024: Per-Agent Lane View

**Priority:** P1 (High)
**Status:** Implemented (v1.6.0)

The Pipeline tab must support a per-agent lane view showing queue health per agent.

- "Lanes" sub-tab in Pipeline shows one card per agent with assigned tasks
- Each card shows: ready count, active count, blocked count, in-review count, queue health badge (healthy/busy/blocked)
- Top 3 ready/in-progress tasks listed per card, clickable to open task detail
- "List" sub-tab retains the existing pipeline table view

## REQ-025: Task Artifacts

**Priority:** P2 (Medium)
**Status:** Implemented (v1.6.0)

Tasks must support linking to output artifacts (files, documents, URLs).

- `artifacts` field: array of strings (file paths, URLs, doc names)
- Editable via task edit form (one per line textarea)
- Displayed in task detail modal as clickable chips
- Included in `PATCH /api/tasks/update` payload
- Returned in all task responses
- [x] Migration adds `activity: []` to existing tasks without the field

## REQ-026: Content Security Policy — Inline Script Execution

**Priority:** P0 (Critical)
**Status:** Implemented (v1.6.0 hotfix)

The server's CSP header must permit execution of the inline JavaScript bundle.

**Root cause of v1.6.0 button regression:** `script-src 'self'` blocks inline `<script>` blocks. The entire ClawTasker UI is a single compiled HTML file with an inline JS bundle. Without `'unsafe-inline'` in `script-src`, the browser discards all JavaScript silently — the page renders its default state (Dashboard visible via hardcoded `class="on"`) but NO button clicks, navigation, or API calls work.

- [x] `script-src` in CSP must include `'unsafe-inline'`
- [x] Test: `GuiRegressionTests.test_csp_allows_inline_scripts` validates this on every build
- [x] Acceptable for a local-first tool (runs on `127.0.0.1` only); `'unsafe-inline'` risk is bounded

## REQ-027: GUI Regression Test Suite

**Priority:** P0 (Critical)
**Status:** Implemented (v1.6.0 hotfix)

A `GuiRegressionTests` test class must run on every build to catch issues that break the web interface without requiring a live browser.

Tests must cover:
- [x] CSP allows inline scripts (`test_csp_allows_inline_scripts`)
- [x] JS bundle is inline, not external (`test_js_bundle_is_inline_not_external`)
- [x] JS bundle parses without syntax errors (`test_js_bundle_has_no_syntax_errors`)
- [x] All nav button target view divs exist in HTML (`test_all_nav_view_ids_exist_in_html`)
- [x] All required view IDs (`V_dash`, `V_board`, …) present (`test_required_view_ids_present`)
- [x] All `onclick="fnName()"` functions defined in JS bundle (`test_all_onclick_functions_defined_in_bundle`)
- [x] `goV`, `applySnapshot`, `showToast`, `buildUpdates` defined
- [x] `API_TOKEN` defined in bundle
- [x] META map has entry for every nav target (`test_meta_map_includes_all_nav_targets`)
- [x] Build manifest version matches VERSION file
- [x] All manifest JS modules exist on disk
- [x] API smoke: `get_next_task` validates owner, `post_task_event` requires `type` field
