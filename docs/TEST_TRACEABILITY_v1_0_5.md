# ClawTasker CEO Console Test Traceability v1.0.5

## Traceability matrix

| Requirement group | Description | Automated checks |
|---|---|---|
| RQ-001 to RQ-005 | Shell structure, appearance surfaces, office canvas, dashboard mission sections | `ui/tests/shell.test.mjs`, `tests/test_server.py` |
| RQ-006, RQ-032 to RQ-043 | Office rules, scene toggle, protected bounds, movement snap | `ui/tests/theme-and-office.test.mjs`, `tests/test_server.py`, `scripts/smoke_test.sh` |
| RQ-007 to RQ-020 | Visualization boundary, recovery, live updates, ticket integrity, contract surfaces | `tests/test_server.py`, `ui/tests/shell.test.mjs`, `scripts/smoke_test.sh` |
| RQ-021 to RQ-031 | Roster scale, org chart, manager lanes, Pocket Office v9 assets | `tests/test_server.py`, `tests/test_release_requirements.py` |
| RQ-036 to RQ-043 | Conversation source badges, official channel handoff, transcript references, default CEO palette, protected office bounds | `ui/tests/shell.test.mjs`, `ui/tests/theme-and-office.test.mjs`, `tests/test_server.py` |
| RQ-044, RQ-045 | Agent self-registration and company-chart identity visibility | `tests/test_server.py`, `scripts/smoke_test.sh` |
| RQ-046, RQ-047 | Mission Control prompt pack and agent API guide | `tests/test_release_requirements.py` |
| RQ-048 to RQ-052 | Mission-plan contract, mission brief, staffing coverage, radar, mission-linked task state | `tests/test_server.py`, `ui/tests/shell.test.mjs`, `tests/test_release_requirements.py`, `scripts/smoke_test.sh` |
| RQ-S01 to RQ-S06 | Sprint / iteration system | `tests/test_server.py` (SprintTests), `scripts/smoke_test.sh` |
| RQ-D01 to RQ-D05 | Inter-task dependency system | `tests/test_server.py` (DependencyTests) |
| RQ-E01 to RQ-E04 | Story points and estimation | `tests/test_server.py` (StoryPointsTests) |
| RQ-P01 to RQ-P05 | Project type system | `tests/test_server.py` (ProjectTypeTests) |
| RQ-W01 to RQ-W04 | Agent workload computation | `tests/test_server.py` (WorkloadTests) |
| RQ-G01 to RQ-G06 | CEO notification inbox | `tests/test_server.py` (NotificationTests) |
| RQ-X01 to RQ-X03 | Directive history trail | `tests/test_server.py` |
| RQ-STR01 to RQ-STR06 | Structural / repo hygiene | `tests/test_release_requirements.py` |

---

## Test inventory

### Python unit tests (`tests/test_server.py`) — 171 tests

- **Core state**: state defaults and runtime boundary, snapshot content and generated metadata, restart-safe backup recovery chain
- **OpenClaw contract**: publish contract contents, agent registration helper and upsert behavior, mission-plan helper and upsert behavior
- **Org chart / roster**: org-chart visibility for name, role, and skills; mission visibility for title, objective, staffing coverage, gaps, risk, and dependency blockers
- **SprintTests** (7): create sprint, update sprint, close sprint with velocity, burndown computation, sprint selector, active sprint in snapshot, new sprint form
- **DependencyTests** (5): depends_on field, circular cycle rejection, downstream auto-blocking, blocking map in snapshot, dependency UI language in state
- **StoryPointsTests** (5): Fibonacci validation, null for invalid values, badge in task record, burndown uses points, column sums
- **ProjectTypeTests** (5): type field present, default types, configure endpoint, specialist sets, non-software routing
- **WorkloadTests** (5): per-agent workload dict, overloaded flag, notification trigger, workload fields on agent record, colour-coded bar data
- **NotificationTests** (8): notifications list in state, GET endpoint, dismiss one, dismiss all, seed on load, bell badge count data, drawer content, directive_delivered kind

### Python release requirements tests (`tests/test_release_requirements.py`) — 30 tests

- Version identity: VERSION == APP_VERSION == 1.0.5, README declares 1.0.5
- Versioned docs exist: REQUIREMENTS, TEST_TRACEABILITY, REGRESSION_REPORT, TEST_RESULTS, POCKET_OFFICE_MAPPING, all render PNGs, PDF guide
- Evergreen docs: ARCHITECTURE.md, AGENT_API_GUIDE.md, AGENT_PROMPTS.md, schemas
- Vendor: v9 pack complete; v4 and brick-edition absent
- UI source files: `ui/src/main.ts`, `ui/src/ui/app.ts`, `ui/vite.config.ts`, mobile CSS
- `web/` legacy layer: `index.html`, `app.js` present
- data/ policy: state.json absent or under 100 bytes; .gitignore covers state and dist
- GitHub hygiene: PR template, CI workflow, LICENSE, README, CHANGELOG
- Server state shape: company, ceo, access_matrix, github_flow, asset_library, platform_contract, office_layout
- UI defaults and office policy: theme_preset=ceo, cross_zone_behavior=snap, respect_protected_bounds=true
- v1.0.5 state keys: sprints list, notifications list, task depends_on and story_points, project type field
- Requirements phrase coverage: 40+ platform phrases, 5 mission phrases, 7 v1.0.5 feature phrases
- README phrase coverage: 17 key feature phrases + 7 v1.0.5 phrases + repository layout section
- OpenClaw companion: all files present, config fields, README mentions 2026.3.13 release
- Roster helper: correct endpoint and header

### Node UI tests (`ui/tests/`) — 44 tests

- **shell.test.mjs**: shell template structure, nav sections, dashboard mission brief language, staffing and radar language, conversation layout, directive trail language, sprint card language
- **conversations.test.mjs**: source badge markup, official channel controls, directive vs discussion split, summary mode language
- **theme-and-office.test.mjs**: theme defaults, office physics helpers, day/night toggle, object bounds, movement policy
- **selectors.test.mjs**: CSS selector helpers and state-driven class logic

### Smoke gate (`scripts/smoke_test.sh`)

1. Adapts Pocket Office v9 assets
2. Builds static UI bundle
3. Rebuilds PDF guide
4. Runs Python unit tests
5. Runs Node unit tests
6. Starts local server
7. Verifies: `/api/health`, `/api/snapshot`, `/api/openclaw/contract`, `/api/agents/register`, `/api/schema/mission-plan`, `/api/missions/plan`, `/api/openclaw/roster_sync`, `/api/openclaw/publish`, `/api/sprints/create`, `/api/notifications`, `/api/ceo/directive`
8. Confirms sprint, dependency, story-points, notification, and directive data in snapshot

---

## Total test counts

| Suite | Tests |
|---|---|
| `tests/test_server.py` | 150 |
| `tests/test_release_requirements.py` | 36 |
| `ui/tests/` (Node) | 44 |
| **Total** | **230** |
