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
