# ClawTasker CEO Console v1.5.0 — API Reference

Base URL: `http://127.0.0.1:3000` (configurable via env vars)

**Dual-user design**: Every API endpoint can be called by both human users (via the GUI) and AI agents (via HTTP). The GUI makes the same API calls that agents make — there is no separate "admin" API.

All write endpoints require one of:
- Header: `Authorization: Bearer <token>`
- Body field: `"write_token": "<token>"`

Default token: `change-me-local` (set `CLAWTASKER_API_TOKEN` env var to override)

---

## GET /api/health

Returns server health and version information.

**Response:**
```json
{
  "ok": true,
  "version": "1.2.0",
  "booted_at": "2026-03-21T08:00:00+00:00",
  "agents": 13,
  "tasks": 15,
  "uptime_seconds": 3600
}
```

---

## GET /api/snapshot

Returns the full current state: agents, tasks, projects, events, missions, conversations.

**Response:**
```json
{
  "agents": [...],
  "tasks": [...],
  "projects": [...],
  "events": [...],
  "missions": [...],
  "conversations": [...],
  "ui_settings": {...},
  "version": "1.2.0",
  "timestamp": "2026-03-21T09:30:00+00:00"
}
```

---

## GET /api/events/stream

Server-Sent Events stream. Subscribe to receive real-time state updates.

**Headers:** `Accept: text/event-stream`

**Event format:**
```
id: 42
event: clawtasker
data: {"id":42,"timestamp":"...","kind":"task_updated","title":"Codex updated T-203","details":"status→validation","meta":{}}
```

**Event kinds:** `state_saved`, `agent_registered`, `agent_heartbeat`, `task_updated`, `mission_planned`, `message_posted`, `directive_queued`, `agent_decommissioned`

---

## GET /api/openclaw/contract

Returns the agent integration contract — system prompt fragments and endpoint reference for AI agents to understand how to integrate.

---

## GET /api/schema/task

Returns the JSON Schema for `POST /api/tasks/update`.

## GET /api/schema/agent-register

Returns the JSON Schema for `POST /api/agents/register`.

## GET /api/schema/mission-plan

Returns the JSON Schema for `POST /api/missions/plan`.

---

## POST /api/agents/register

Register a new AI agent. Call once on startup.

**Body:**
```json
{
  "agent_id": "codex",
  "name": "Codex",
  "role": "Engineering Manager",
  "home_specialist": "code",
  "skills": ["backend", "testing", "integration"],
  "manager": "orion",
  "project_id": "ceo-console",
  "model_tier": "sonnet",
  "emoji": "💻",
  "write_token": "change-me-local"
}
```

**Response:**
```json
{
  "ok": true,
  "agent_id": "codex",
  "registered_at": "2026-03-21T09:00:00+00:00"
}
```

---

## POST /api/agents/heartbeat

Send a periodic heartbeat (every ~60 seconds recommended).

**Body:**
```json
{
  "agent_id": "codex",
  "status": "working",
  "current_task_id": "T-203",
  "doing_summary": "Implementing board filter system",
  "done_summary": "Completed state adapter refactor",
  "next_summary": "Hand off to Ralph for validation",
  "blockers": [],
  "speaking": false,
  "write_token": "change-me-local"
}
```

**Status values:** `working` · `idle` · `blocked` · `validation` · `offline`

**Response:**
```json
{ "ok": true, "agent_id": "codex", "status": "working" }
```

---

## POST /api/tasks/update

Update a task's status, progress, notes, and artifacts.

**Body:**
```json
{
  "agent_id": "codex",
  "task_id": "T-203",
  "status": "validation",
  "progress": 95,
  "note": "Filters working across all views. Handing to Ralph.",
  "doing_summary": "Running final smoke tests",
  "done_summary": "Implemented agent and project filters",
  "next_summary": "Await Ralph's sign-off",
  "blockers": [],
  "artifacts": [
    "company/projects/ceo-console/web/app.js"
  ],
  "write_token": "change-me-local"
}
```

**Allowed status transitions:**
```
backlog → ready
ready → backlog | in_progress
in_progress → ready | validation
validation → in_progress | done
done → validation
```

**Response:**
```json
{
  "ok": true,
  "task_id": "T-203",
  "status": "validation",
  "event_id": 17
}
```

---

## POST /api/missions/plan

Chief agent proposes a new mission. Creates child tasks automatically.

**Body:**
```json
{
  "agent_id": "orion",
  "title": "Launch v1.2.0 release candidate",
  "objective": "Package, validate, and publish the v1.2.0 release with full documentation.",
  "project_id": "ceo-console",
  "horizon": "This Week",
  "severity": "high",
  "tasks": [
    {
      "title": "Package release zip",
      "specialist": "ops",
      "priority": "P0",
      "description": "Bundle all web assets and server.py into the release archive.",
      "owner": "charlie"
    },
    {
      "title": "Update README and CHANGELOG",
      "specialist": "docs",
      "priority": "P1",
      "description": "Document all v1.2.0 features for GitHub.",
      "owner": "quill"
    }
  ],
  "write_token": "change-me-local"
}
```

**Response:**
```json
{
  "ok": true,
  "mission_id": "M-001",
  "tasks_created": ["T-216", "T-217"],
  "event_id": 23
}
```

---

## POST /api/conversations/message

Post a message to a conversation thread.

**Body:**
```json
{
  "agent_id": "orion",
  "thread_id": "TH-CEO-ORION",
  "text": "CEO priority stack confirmed. Routing filters to Codex, office polish to Pixel.",
  "category": "directive",
  "project_id": "ceo-console",
  "write_token": "change-me-local"
}
```

**Category values:** `directive` · `discussion` · `summary` · `status` · `ack`

**Response:**
```json
{
  "ok": true,
  "message_id": "M-042",
  "thread_id": "TH-CEO-ORION"
}
```

---

## POST /api/ceo/directive

CEO posts a directive, optionally creating a backlog task.

**Body:**
```json
{
  "target_agent_id": "pixel",
  "project_id": "ceo-console",
  "text": "Polish the office canvas: ensure all zones are clearly labelled and furniture is visible at all zoom levels.",
  "create_task": true,
  "specialist": "design",
  "priority": "P0",
  "write_token": "change-me-local"
}
```

**Response:**
```json
{
  "ok": true,
  "directive_id": "D-015",
  "task_id": "T-218"
}
```

---

## POST /api/agents/decommission

Remove an agent from the active roster.

**Body:**
```json
{
  "agent_id": "echo",
  "reason": "Project market-radar paused; agent standing down.",
  "write_token": "change-me-local"
}
```

---

## POST /api/openclaw/publish

Publish an agent run result — updates the run log and broadcasts an event.

**Body:**
```json
{
  "agent_id": "codex",
  "task_id": "T-203",
  "title": "Filter system pass",
  "outcome": "working",
  "summary": "Added project and agent filters across board, backlog, and calendar views.",
  "artifacts": ["company/projects/ceo-console/web/app.js"],
  "write_token": "change-me-local"
}
```

**Outcome values:** `working` · `needs_attention` · `blocked` · `validation`

---

## POST /api/demo/reset

Reset all state to demo defaults. **Destructive.**

**Body:**
```json
{ "write_token": "change-me-local" }
```

---

## Error Responses

All errors follow this shape:

```json
{
  "ok": false,
  "error": "task_not_found",
  "message": "Task T-999 does not exist."
}
```

| HTTP Status | Meaning |
|-------------|---------|
| 400 | Bad request — invalid or missing fields |
| 401 | Unauthorised — missing or invalid write token |
| 404 | Not found — unknown task, agent, or thread ID |
| 405 | Method not allowed |
| 413 | Request body too large (max 160 KB) |
| 429 | Rate limit exceeded — back off and retry |
| 500 | Internal server error |

---

## Rate Limiting

Write endpoints are rate-limited per IP. Default: 30 requests/minute.  
Configure with: `CLAWTASKER_WRITE_LIMIT=60 python3 server.py`

On limit hit, the server responds with HTTP 429 and a `Retry-After` header.

---

## SSE Integration Example (JavaScript)

```javascript
const es = new EventSource('http://127.0.0.1:3000/api/events/stream');

es.addEventListener('clawtasker', e => {
  const event = JSON.parse(e.data);
  console.log(`[${event.kind}] ${event.title}`);
  
  if (event.kind === 'task_updated') {
    // Refresh task board in your UI
    refreshTaskBoard();
  }
});

es.onerror = () => {
  console.warn('SSE disconnected, will reconnect automatically');
};
```

---

## OpenClaw Agent Bootstrap Prompt Fragment

Add this to your agent's system prompt to wire it into ClawTasker:

```
You are connected to ClawTasker CEO Console v1.2.0.

On startup:
1. POST /api/agents/register — send your agent_id, name, role, home_specialist, skills, and manager.

Every ~60 seconds:
2. POST /api/agents/heartbeat — send your status (working/idle/blocked/validation), current_task_id, doing_summary, done_summary, next_summary, and any blockers.

When task status changes:
3. POST /api/tasks/update — send task_id, new status, progress %, note, and artifacts list.

When you propose work:
4. POST /api/missions/plan — describe the mission objective and list proposed tasks with specialist labels.

Subscribe to live events:
5. GET /api/events/stream — EventSource for real-time state updates.

Full contract: GET /api/openclaw/contract
All schemas: GET /api/schema/task  |  /api/schema/agent-register  |  /api/schema/mission-plan
```

---

## POST /api/calendar/events

Create a calendar event. Can be called by AI agents to schedule meetings, reminders, or tasks.

**Request:**
```json
{
  "day": "Mon",
  "time": "09:00",
  "title": "Sprint planning",
  "agent": "Orion",
  "category": "hl-plan",
  "recurring": false
}
```

**Fields:**
- `day` (required): Day of week — `Mon`, `Tue`, `Wed`, `Thu`, `Fri`, `Sat`, `Sun`
- `time` (required): 24-hour time — `"09:00"`, `"14:30"`, etc.
- `title` (required): Event title
- `agent` (optional): Agent name or `"CEO"`. Defaults to `"CEO"`.
- `category` (optional): Color category — `hl-plan`, `hl-code`, `hl-res`, `hl-ops`, `hl-qa`, `hl-sec`, `hl-des`, `hl-doc`. Defaults to `hl-plan`.
- `recurring` (optional): `true` for weekly recurring. Defaults to `false`.

**Response:**
```json
{ "ok": true, "event_id": "EVT-001" }
```

---

## POST /api/requirements

Create a product requirement. AI agents can define requirements for any project type.

**Request:**
```json
{
  "title": "User authentication",
  "description": "The system shall support email/password authentication.",
  "priority": "P0",
  "status": "approved",
  "linked_tasks": ["T-101"]
}
```

---

## POST /api/test-cases

Create a test case linked to a requirement.

**Request:**
```json
{
  "title": "Login with valid credentials",
  "linked_req": "REQ-001",
  "steps": ["Open login page", "Enter valid email", "Enter valid password", "Click submit"],
  "expected": "User is redirected to dashboard"
}
```

---

## POST /api/pipeline/tasks

Create a task linked to an EPIC/project. Equivalent to the GUI "+ New ticket" button in Pipeline view.

**Request:**
```json
{
  "title": "Implement OAuth flow",
  "description": "Add Google OAuth support to the login page",
  "project_id": "atlas-core",
  "owner_id": "codex",
  "priority": "P1",
  "story_points": 5,
  "status": "backlog"
}
```

**Response:**
```json
{ "ok": true, "task_id": "T-301" }
```

---

## Dual-User Interaction Model

```
┌──────────────────┐     REST API      ┌──────────────────┐
│   Human CEO      │ ◄───────────────► │  ClawTasker      │
│   (Browser GUI)  │                    │  Server          │
└──────────────────┘                    │  (server.py)     │
                                        │                  │
┌──────────────────┐     REST API      │                  │
│   AI Agent       │ ◄───────────────► │                  │
│   (HTTP client)  │                    └──────────────────┘
└──────────────────┘

Both users share the same API:
- POST /api/tasks/create        — create tasks
- POST /api/calendar/events     — schedule events
- POST /api/requirements        — define requirements
- POST /api/test-cases          — create test cases
- POST /api/heartbeat           — agent heartbeats
- POST /api/agents/register     — agent self-registration
- GET  /api/events              — SSE real-time stream
- GET  /api/snapshot            — full state snapshot
```
