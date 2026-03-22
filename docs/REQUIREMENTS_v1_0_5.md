# ClawTasker CEO Console Requirements v1.0.5

## Product vision
ClawTasker CEO Console v1.0.5 is the **stable first release** of the human-facing mission-control room for OpenClaw AI agent companies. It gives a human CEO one authoritative surface to observe, coordinate, and direct a chief coordinating agent and specialist sub-agents through missions, tasks, conversations, and a live office simulation — while keeping OpenClaw as the runtime source of truth.

---

## Visual and rendering requirements

### RQ-V01 — Atmospheric background
The application shell background shall use a rich dark gradient or layered radial gradient (not a flat solid colour) to create visual depth and atmosphere that communicates the "command center" aesthetic. Light mode shall use a corresponding light gradient.

### RQ-V02 — Panel / card visual hierarchy
Panel and card surfaces (`.pn`, `.kol`, metric cards) shall have clearly visible background fills distinct from the shell background, with subtle border and shadow, so tiled interface elements read as elevated cards against the background.

### RQ-V03 — Accent glow on hero metrics
Dashboard metric values (done count, blocked count, validation queue, active agents) shall display with a coloured accent or glow matching their semantic meaning (danger=red glow, warning=amber, ok=green, accent=teal) so the human CEO can scan status at a glance.

### RQ-V04 — Visual identity in sidebar
The sidebar brand area shall show a distinctive logo mark (CT initials with a claw icon) with a gradient background and the product name rendered in a characterful, non-generic typeface.

### RQ-V05 — Font pairing
The application shall load a distinctive display/UI font (e.g. JetBrains Mono or Space Mono for code-like identity elements, or a strong geometric sans for the brand) rather than falling back to Inter/system-ui for all text.

### RQ-V06 — Focus ring and keyboard accessibility
All interactive elements (buttons, nav items, inputs, task cards) shall show a visible focus ring using the accent colour when focused via keyboard, enabling keyboard-only navigation.

### RQ-V07 — Responsive sidebar
On viewport widths below 768 px the sidebar shall collapse to an icon-only rail (48 px wide) with tooltips, so the content area remains usable on laptop screens.

---

## Mission planner requirements

### RQ-M01 — Mission creation from UI
The Missions view shall expose a **New mission** button that opens an inline form letting the human CEO create a mission with: title (required), objective (required), priority, horizon, owner, project IDs, specialist requirements, assigned agents, and initial next actions.

### RQ-M02 — Mission edit from UI
Each mission card shall show an **Edit** button that opens the same form pre-populated with existing mission data, allowing the CEO to update any field and POST to `/api/missions/plan`.

### RQ-M03 — Staffing coverage visible on mission cards
Each mission card shall display a **staffing coverage %** badge (e.g. "100% staffed" or "⚠ 33% — gaps: qa") driven by `mission.staffing.coverage_percent` and `mission.staffing.gaps`.

### RQ-M04 — Risks visible on mission cards
Each mission card shall render up to three risk items with severity badges (critical=red, high=amber, low=muted). Clicking a risk item shall show its mitigation note in a tooltip or inline expand.

### RQ-M05 — Dependencies visible on mission cards
Each mission card shall render dependency items with a blocked/pending/done status indicator. Blocked dependencies shall be highlighted in red.

### RQ-M06 — Mission progress bar from linked tasks
Each mission card shall show a progress bar computed from `mission.progress_percent` (server-computed ratio of done/total linked tasks).

### RQ-M07 — Mission → task jump
Linked task IDs on each mission card shall be clickable chips that open the task ticket modal directly from the Missions view.

### RQ-M08 — Next actions and success criteria in mission detail
Expanding a mission card shall reveal next actions and success criteria in a readable checklist format.

---

## Task board requirements

### RQ-T01 — Board filter by project and specialist
The Board view shall expose filter controls for project (all / CEO Console / Market Radar / Atlas Core) and specialist (all / planning / code / research / ops / qa / security / design / docs / distribution). Filters shall apply in real time to the Kanban columns.

### RQ-T02 — Inline status advancement on task cards
Each task card shall show a **→ Advance** button (visible on hover) that moves the task to the next lifecycle state via `POST /api/tasks/update` without opening the full modal.

### RQ-T03 — Blocker reason on blocked cards
Blocked task cards shall display the first blocker reason string beneath the task title (not only a badge) so the CEO can triage without opening the modal.

### RQ-T04 — Reassign owner from task modal
The task modal shall include an **Assign to** dropdown populated from the agent roster, allowing the CEO to change `task.owner` and POST the update.

### RQ-T05 — Fix-routing action on mismatch tasks
Tasks with `routing_mismatch: true` shall show a **Fix routing** button next to the mismatch badge that, when clicked, sets `task.owner = task.recommended_owner` and POSTs the update.

### RQ-T06 — Empty-state illustration per Kanban column
When a Kanban column has zero tasks it shall render a short empty-state message (e.g. "Nothing ready — move tasks from backlog") rather than a blank column.

---

## Agent API and heartbeat requirements

### RQ-A01 — Last-heartbeat timestamp visible per agent
Each agent card in the Team roster shall show a relative timestamp of the last received heartbeat (e.g. "2 min ago", "never") derived from `agent.last_heartbeat`.

### RQ-A02 — Derived status used in UI
Agent status badges and office sprite poses shall use `agent.derived_status` (server-computed) rather than raw `agent.status` so validation, blocked, and speaking states are accurately reflected.

### RQ-A03 — Speaking indicator
Agents with `agent.speaking = true` shall show a pulsing speech-bubble indicator in both the Team roster and the office simulation.

### RQ-A04 — API health indicator in topbar
The topbar shall show a live connection indicator that reflects whether the most recent snapshot fetch succeeded (green dot) or failed (red dot / "offline"), distinguishing between server-up and server-down states.

### RQ-A05 — Mission plan arrival indicator
When a new mission plan is received via `/api/missions/plan` during an active session (via SSE or polling), the Missions nav item shall show a pulsing badge for 10 seconds to alert the CEO.

---

## Calendar requirements

### RQ-C01 — Today highlighted in week day tabs
The current day tab in the Week calendar shall be visually highlighted (accent border + accent text) even when a different day is selected.

### RQ-C02 — Hover tooltip on month event bars
Month-view event bars shall show a tooltip on hover containing the full task title, agent name, and time.

### RQ-C03 — Agent lane separation in week view
The Week view detail panel shall group events by agent, rendering each agent's events in a named sub-row with their face avatar on the left, so the CEO can scan each agent's day in one glance.

---

## OpenClaw API requirements (carried forward)

### RQ-001 — Recognizable OpenClaw shell  
### RQ-002 — Appearance settings  
### RQ-003 — CEO profile controls  
### RQ-004 — Modern command-center layout  
### RQ-005 — Pocket Office v9 office scene  
### RQ-006 — Office seat and depth mechanics  
### RQ-007 — Visualization-first role  
### RQ-008 — OpenClaw subagent boundary alignment  
### RQ-009 — Restart-safe behavior  
### RQ-010 — Error handling and degraded recovery  
### RQ-011 — Responsive shell assets  
### RQ-012 — System health and recovery center  
### RQ-013 — Agent publish contract visibility  
### RQ-014 — OpenClaw latest release compatibility  
### RQ-015 — OpenClaw publish ingress  
### RQ-016 — Live update channel  
### RQ-017 — Ticket lifecycle integrity  
### RQ-018 — Deterministic task ordering  
### RQ-019 — Idempotent OpenClaw publish dedupe  
### RQ-020 — Ticket system health visibility  
### RQ-021 — Agent roster scalability  
### RQ-022 — OpenClaw roster synchronization  
### RQ-023 — Flexible organisation templates  
### RQ-024 — Core-skill-aligned routing  
### RQ-025 — Scale-aware office rendering  
### RQ-026 — Manager-linked company chart  
### RQ-027 — Multiple managers and reporting relationships  
### RQ-028 — Manager and team metadata in OpenClaw roster sync  
### RQ-029 — Large virtual company scaling  
### RQ-030 — Pocket Office v9 compatibility pack  
### RQ-031 — Visible-face roster cards  
### RQ-032 — Office scene toggle  
### RQ-033 — Office area catalog  
### RQ-034 — Collision-safe office placement  
### RQ-035 — Layout-respecting office movement  
### RQ-036 — Conversation source badges  
### RQ-037 — Official channel handoff  
### RQ-038 — Directive versus discussion split  
### RQ-039 — Subagent summaries by default  
### RQ-040 — Audit-safe transcript linking  
### RQ-041 — Default CEO Console palette  
### RQ-042 — Protected office object bounds  
### RQ-043 — Object-safe office movement policy  
### RQ-044 — Agent self-registration contract  
### RQ-045 — Company-chart identity visibility  
### RQ-046 — Mission Control prompt pack  
### RQ-047 — Agent API guide  
### RQ-048 — Mission-plan contract  
### RQ-049 — Shared mission brief  
### RQ-050 — Staffing and coverage  
### RQ-051 — Risk and dependency radar  
### RQ-052 — Mission-linked task management  

### RQ-053 — Dual-size agent avatar rendering
The rendering layer shall produce two avatar display sizes for each AI agent character:
- **Portrait card** (sm: 40×40, default: 64×64, lg: 80×80, xl: 100×100): full 160×160 pixel art character card, `object-fit: contain`, `image-rendering: pixelated`.
- **Face avatar** (sm: 24×24, default: 32×32, md: 40×40, lg: 52×52): circular crop of the face zone (portrait rows 30–82) using CSS offset technique.

---

## Office simulation requirements

### RQ-OFF01 — Agent pose driven by task state and zone
Each agent sprite in the office simulation shall adopt a pose determined by both its `derived_status` and its assigned zone:
- Agents at desks (`code_pod`, `research_pod`, `ops_pod`, `qa_pod`, `studio_pod`, `chief_desk`, `ceo_strip`) with status `working` shall use the `seated` pose.
- Agents at desks with status `blocked` shall use the `talk` pose (indicating they need help), not `idle`.
- Agents at collaboration zones (`scrum_table`, `review_rail`, `board_wall`) shall always use the `talk` pose regardless of status.
- Agents in the `lounge` with status `idle` shall use the `idle` pose; all other statuses in the lounge shall use `talk`.
- All other agent-zone combinations with status `working` shall use `seated`; all others shall use `idle`.

### RQ-OFF02 — Speech bubble gating and zone-aware offsets
The office simulation shall only render a speech bubble for an agent when at least one of the following is true: `agent.speaking === true`, `agent.blockers.length > 0`, or the agent is in the `review_rail` zone. Bubble position shall use a pre-computed per-zone, per-seat offset table (`officeBubbleOffset`) so bubbles never overlap sprite bodies or furniture.

### RQ-OFF03 — Depth-sorted sprite rendering
Agent sprites on the office canvas shall be sorted by their target Y coordinate (ascending) before being appended to the DOM, and each sprite shall carry an explicit `z-index` of `20 + target.y`. This ensures agents lower on the floor plane (further south) appear in front of agents further north, producing correct isometric depth layering.

### RQ-OFF04 — Dual-mode avatar in office (body sprite vs portrait face)
The `buildAvatar` function shall support a `body` option flag. When `body: true` or `size === 'office'`, it shall render the full character sprite strip (walk-cycle frames). When `body` is falsy and `size` is not `'office'`, it shall render the portrait face image. This allows the Team roster and the office canvas to use the same function with different modes.

### RQ-OFF05 — Single authoritative zone slot table
The office renderer shall use a single named constant (`OFFICE_ZONE_SLOTS`) for all zone seat coordinates. There shall be no duplicate or shadowed slot table in the codebase. Zone coordinates shall be calibrated for the 32-bit office map dimensions.


---

## Carried-forward requirements (maintained from prior releases)

The following requirements from prior releases remain in force for v1.0.5. Full descriptions are in REQUIREMENTS_v4_2_0_rc3.md; this section acts as the traceability anchor.

- **Visualization-first role**: ClawTasker explicitly describes itself as a visualization companion, not a runtime orchestrator.
- **OpenClaw subagent boundary alignment**: platform copy and API contract make the boundary explicit — OpenClaw keeps routing, sessions, and workspaces.
- **Restart-safe behavior**: product recovers the latest good state snapshot and agents can republish after recovery.
- **Error handling and degraded recovery**: platform exposes recovery states rather than silently failing.
- **System health and recovery center**: dashboard exposes write budget, live sync mode, and restart-safe boundaries.
- **Agent publish contract visibility**: agent-facing APIs are documented and discoverable via /api/openclaw/contract.
- **OpenClaw latest release compatibility**: release metadata documents the latest OpenClaw npm version and GitHub tag.
- **OpenClaw publish ingress**: POST /api/openclaw/publish supports heartbeat, task_update, validation, conversation_note, mission_plan, and run events.
- **Live update channel**: UI uses SSE with polling fallback for live state updates.
- **Ticket lifecycle integrity**: task system enforces status-transition rules and validator requirements.
- **Deterministic task ordering**: board orders blocked → status → priority → horizon → due date.
- **Idempotent OpenClaw publish dedupe**: publish endpoint deduplicates identical payloads within the retry window.
- **Ticket system health visibility**: dashboard exposes assignment drift, missing validators, and dedupe window facts.
- **Agent roster scalability**: Team view and snapshot expose scalability metadata for up to 64 rostered agents.
- **OpenClaw roster synchronization**: POST /api/openclaw/roster_sync supports manager/team metadata sync.
- **Flexible organisation templates**: snapshot exposes org templates and manager-linked model.
- **Core-skill-aligned routing**: routing helpers prefer skill-matched agents for task recommendations.
- **Scale-aware office rendering**: office view stays bounded at 16 visible agents while Team view remains authoritative.
- **Manager-linked company chart**: Team view renders CEO → chief → managers → specialists hierarchy.
- **Multiple managers and reporting relationships**: org structure supports multiple manager lanes.
- **Manager and team metadata in OpenClaw roster sync**: roster contract preserves manager, team_id, and team_name fields.
- **Large virtual company scaling**: product documents 64-agent tested target and office overflow behaviour.
- **Pocket Office v9 compatibility pack**: release ships portraits, sprite strips, and generated day/night office assets.
- **Visible-face roster cards**: roster view shows readable pixel art character cards with face-zone face avatars.
- **Office seat and depth mechanics**: office renderer keeps seat anchoring, table seats, and avatar depth sorting deterministic.
- **Office scene toggle**: UI exposes day and night office scene controls.
- **Office area catalog**: snapshot and office logic expose named zone areas.
- **Collision-safe office placement**: office placement algorithm avoids sprite collisions using zone slot allocation.
- **Layout-respecting office movement**: agents animate between zones via movement policy with snap behaviour.
- **Conversation source badges**: conversation threads show source badges (browser, Telegram, Discord, webhook, internal session).
- **Official channel handoff**: conversations expose official channel links and transcript references. Official channels are accessible for audit.
- **Directive versus discussion split**: operator composer distinguishes directives from discussion messages.
- **Subagent summaries by default**: summaries only for subagent-to-subagent threads by default, with manual reveal.
- **Audit-safe transcript linking**: threads carry transcript path, session key, and run ID references.
- **Default CEO Console palette**: Appearance tab defaults to the CEO Console theme preset.
- **Protected office object bounds**: office renderer respects declared object bounds as collision areas.
- **Object-safe office movement policy**: movement policy snaps across zone boundaries and respects protected bounds.
- **agent self-registration contract**: POST /api/agents/register lets agents publish name, role, and skills for roster and chart visibility (see RQ-044).
- **Company-chart identity visibility**: registered agents appear in the org chart and roster with name, role, and skills.
- **Mission Control prompt pack**: release ships the mission-control prompt pack for OpenClaw orchestrators.
- **Agent API guide**: docs/AGENT_API_GUIDE.md documents all agent-facing endpoints with examples.
- **Mission-plan contract**: POST /api/missions/plan and GET /api/schema/mission-plan expose the mission planning API.
- **Shared mission brief**: dashboard mission brief shows title, objective, staffing coverage, and linked tasks.
- **Staffing and coverage**: mission cards show coverage %, assigned agents, and specialist gaps.
- **Risk and dependency radar**: mission cards show risks with severity badges and blocked dependency indicators.
- **Mission-linked task management**: task_ids in mission plans link to board tickets; mission progress tracks task completion.


The **agent self-registration contract** (RQ-044) is implemented via `POST /api/agents/register` and the `/api/schema/agent-register` schema endpoint.


---

## Additional requirements (v1.0.2)

### RQ-N01 — Pre-cropped head-only avatars
Face avatar displays shall use pre-extracted head images cropped to portrait rows 32–83 (FACE zone only, no neck gap, no card border, no collar) embedded as a `HEADS` data constant. Avatar circles shall show only the character head using `object-fit: cover; object-position: center top` — no neck gap or disconnection visible at any avatar size.

### RQ-N02 — Office virtual environment stability
The office canvas container (`.off-wrap`) shall declare `aspect-ratio: 640/384` and use absolute-positioned map and sprite-overlay layers so the overlay is always co-extensive with the rendered map regardless of load order. Characters shall always appear inside the map bounds.

### RQ-N03 — Task creation from UI
The Board view shall expose a **New task** button that opens an inline form allowing the CEO to create a task with: title (required), description, owner, specialist, priority, and project. Created tasks enter the backlog immediately without requiring an API call.

### RQ-N04 — Agent capability matrix
The Team view shall include a **capability matrix** table showing each agent's name, role, specialist, core skills, and current status in a sortable grid, giving the CEO and OpenClaw agents a clear view of what each team member can do.

### RQ-N05 — Project development health
The Dashboard shall display a **project health** row with one card per project showing: total tasks, in-progress count, blocked count, and completion percentage with a progress bar, coloured by project identity.

### RQ-N06 — Snapshot export
The Access view shall provide an **Export** button that downloads the current in-memory snapshot (agents, tasks, missions, calendar, positions, metrics) as a timestamped JSON file for audit, debugging, or handoff to OpenClaw agents.

---

## New requirements — v1.0.5

### RQ-S01 — Sprint creation
The system shall support `POST /api/sprints/create` to create a named sprint with `id`, `name`, `project_id`, `goal`, `start_date`, `end_date`, and `status` (planning|active|closed).

### RQ-S02 — Sprint update and velocity
`POST /api/sprints/update` shall update sprint fields. Closing a sprint shall auto-compute `velocity` as the sum of story points on done tasks linked to that sprint.

### RQ-S03 — Sprint selector on Board
The Board tab shall expose a sprint selector dropdown. Selecting a sprint filters the Kanban to that sprint's tasks and shows the burndown bar.

### RQ-S04 — Active sprint card on Dashboard
The Dashboard shall show an Active Sprint card with task counts, point metrics, and a burndown bar.

### RQ-S05 — Sprint in snapshot
The snapshot shall include `sprints[]` and `metrics.active_sprint` with live burndown (total/done/remaining points, pct_complete).

### RQ-S06 — New sprint form
A `+ New sprint` form in the Board tab shall create sprints locally and POST to the server.

### RQ-D01 — Task dependency fields
Each task shall carry `depends_on: []` and `blocking: []` (computed). `POST /api/tasks/update` shall accept `depends_on`.

### RQ-D02 — Circular dependency detection
Circular dependency chains shall be detected and rejected with HTTP 400 identifying the cycle.

### RQ-D03 — Downstream auto-blocking
`_propagate_dependencies()` shall auto-block downstream tasks when an upstream task is blocked.

### RQ-D04 — Blocking map in snapshot
The blocking map shall be computed inside `snapshot_state` so it is always consistent.

### RQ-D05 — Dependency UI on task cards
Task cards shall show a dependency note when `depends_on` is set. The task modal shall show full Depends on and Blocking sections with clickable task ID chips.

### RQ-E01 — Story points field
Tasks shall carry `story_points` using the Fibonacci set (1|2|3|5|8|13|null).

### RQ-E02 — Story points validation
`POST /api/tasks/update` shall accept `story_points` — values not in the Fibonacci set shall be stored as null.

### RQ-E03 — Story points badge on task cards
Task cards shall show a teal points badge. Unestimated tasks show nothing.

### RQ-E04 — Story points in sprint burndown
Sprint burndown shall use story points (null counts as 1).

### RQ-P01 — Project type field
Each project shall carry `type`: `software|manual|business|coaching|plan|launch|custom`.

### RQ-P02 — Default project types
Default projects shall be typed: ceo-console=software, market-radar=business, atlas-core=software.

### RQ-P03 — Project configure endpoint
`POST /api/projects/configure` shall update type, name, tagline, and `relevant_specialists`.

### RQ-P04 — Specialist sets per project type
`SPECIALIST_SETS` shall map each project type to its default specialist list.

### RQ-P05 — Non-software project routing
Non-software projects shall route tasks to appropriate non-code specialists.

### RQ-W01 — Agent workload computation
`snapshot_state` shall compute `agent_workload` — per-agent dict with `active`, `backlog`, `total`, `story_points`, `overloaded` (bool, threshold >4 active tasks).

### RQ-W02 — Workload fields on agent records
Each agent record in the snapshot shall include `workload_active`, `workload_points`, `overloaded`.

### RQ-W03 — Overloaded notification
Agents with >4 active tasks shall auto-generate an `overloaded` notification.

### RQ-W04 — Workload bar on roster cards
Roster cards shall show a colour-coded workload bar (green→amber→red) with active task count and story points.

### RQ-G01 — Notification storage
`state.notifications[]` shall store notifications with `id`, `kind`, `title`, `detail`, `agent_id`, `created_at`, `read`, `dismissed`.

### RQ-G02 — Notification kinds
Supported notification kinds: `task_blocked`, `task_completed`, `mission_risk`, `agent_offline`, `sprint_ending`, `dependency_cleared`, `directive_delivered`, `routing_mismatch`, `overloaded`.

### RQ-G03 — Notification API
`GET /api/notifications` shall return undismissed notifications. `POST /api/notifications/dismiss` shall dismiss one or all.

### RQ-G04 — Seed notifications on load
On page load, `seedNotifications()` shall generate initial notifications from current state.

### RQ-G05 — Notification bell in topbar
The topbar shall show a bell icon with a red badge count reflecting unread notifications.

### RQ-G06 — Notification drawer
Clicking the bell shall open a slide-in notification drawer with kind icons and Dismiss buttons.

### RQ-X01 — Directive trail panel
The Conversations tab shall show a **Directive trail** panel below the threads.

### RQ-X02 — Directive send form
A `+ Send directive` button shall open an inline form (target agent, context, text).

### RQ-X03 — Directive history
Directives shall be stored in `localDirectives[]`, posted to `POST /api/ceo/directive`, and rendered as a newest-first trail with avatar, text, agent name, context, and timestamp. Each sent directive shall generate a `directive_delivered` notification.

---

## Structural requirements — v1.0.5

### RQ-STR01 — Single version identity
The repository shall have a single canonical version declared in `VERSION`. The folder name, README `**Version:**` header, and `server.APP_VERSION` constant shall all match.

### RQ-STR02 — No live state in repository
`data/state.json` shall be listed in `.gitignore` and shall not be present in the release archive (or shall be an empty placeholder under 100 bytes).

### RQ-STR03 — Current docs only
The `docs/` folder shall contain only current-version artefacts and evergreen documents. Historical versioned artefacts from prior releases shall not be present.

### RQ-STR04 — v9 only in third_party
`third_party/` shall contain only `pocket-office-quest-v9`. The v4 and brick-edition versions are removed as v9 supersedes both and is the sole version used by the office renderer and asset pipeline.

### RQ-STR07 — Avatar mapping correctness
The `avatar_mapping` in `server.py` and `AGENT_MAP` in `scripts/adapt_pocket_office_release.py` shall be identical and consistent. Since v9 provides 12 characters for 14 agents, exactly 2 sharing pairs are permitted: `iris`+`ledger` → `mina` (back-office/people roles) and `scout`+`mercury` → `zara` (analyst/research roles). No other character shall be shared across agents.

### RQ-STR05 — gitignore covers dist and state
`.gitignore` shall include `ui/dist/` and `data/state.json`.

### RQ-STR06 — ARCHITECTURE.md present
`docs/ARCHITECTURE.md` shall document the `web/` vs `ui/` relationship and the data/ policy.
