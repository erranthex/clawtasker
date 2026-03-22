# ClawTasker CEO Console Regression Report v1.0.5

## Summary

This regression pass validates the full v1.0.5 feature set: sprint/iteration system, inter-task dependencies, story points, project types, agent workload, CEO notification inbox, and directive history trail — on top of the stabilised CEO Console shell, mission planning layer, Mission Control prompt pack, and agent self-registration flow. It also validates the structural changes introduced in v1.0.5: version identity alignment, removal of live state from the repository, trimmed `docs/` (current artefacts only), single vendor version in `third_party/`, and the new `docs/ARCHITECTURE.md`.

## Release focus (v1.0.5)

**New features:**
- Sprint / iteration system (`POST /api/sprints/create`, `POST /api/sprints/update`) with velocity tracking and Board burndown
- Inter-task dependency system with circular cycle detection and downstream auto-blocking
- Story points (Fibonacci) with sprint burndown integration
- Project type system (`software|manual|business|coaching|plan|launch|custom`) with per-type specialist routing
- Agent workload computation with overload threshold and colour-coded roster bars
- CEO notification inbox (`GET /api/notifications`, `POST /api/notifications/dismiss`) with bell and slide-in drawer
- Directive history trail in Conversations tab with `POST /api/ceo/directive`

**Structural changes:**
- Version identity unified: `VERSION`, `server.APP_VERSION`, folder name, README all read `1.0.5`
- `data/state.json` removed from repository and `.gitignore` updated to cover `data/state.json` and `ui/dist/`
- `docs/` trimmed to current-version artefacts and evergreen docs only
- `third_party/pocket-office-quest-v4` and `pocket-office-quest-brick-edition` removed
- `docs/ARCHITECTURE.md` added (explains `web/` vs `ui/`, `data/` policy, CI)
- `tests/test_release_requirements.py` updated with 30 tests covering all structural and feature requirements

**Retained from prior releases:**
- Screenshot-aligned CEO Console shell, agent self-registration, company-chart visibility
- Mission planning layer: `POST /api/missions/plan`, `GET /api/schema/mission-plan`, dashboard mission brief, staffing, risk radar
- Mission Control onboarding prompt pack and agent API guide
- Pocket Office Quest v9 office simulation, day/night scene, collision-safe movement
- OpenClaw roster-sync bridge, publish ingress, restart-safe recovery

## Validation gate

```text
python3 scripts/adapt_pocket_office_release.py
python3 scripts/build_static_ui.py
python3 docs/build_guide.py
python3 -m py_compile server.py
python3 -m unittest discover -s tests -v
node --test ui/tests/*.test.mjs
bash scripts/smoke_test.sh
```

## Results

- Python compile: **passed**
- Python unit suite (`test_server.py`): **150 / 150 passed**
- Python release requirements suite (`test_release_requirements.py`): **36 / 36 passed**
- Node UI suite: **44 / 44 passed**
- Smoke gate: **passed**
- Static UI bundle, preview renders, and PDF guide regenerated successfully.
- Version identity check: `VERSION` = `server.APP_VERSION` = `1.0.5` ✓
- Structural checks: `data/state.json` absent ✓, `ui/dist/` gitignored ✓, obsolete vendor dirs absent ✓, `docs/ARCHITECTURE.md` present ✓
- Sprint: `POST /api/sprints/create` and `POST /api/sprints/update` confirmed; velocity computed on close ✓
- Dependencies: cycle detection confirmed (HTTP 400); downstream blocking propagated ✓
- Notifications: `GET /api/notifications` confirmed; bell badge data present in snapshot ✓
- Directives: `POST /api/ceo/directive` confirmed; `directive_delivered` notification generated ✓

## Total test count

| Suite | Tests | Status |
|---|---|---|
| `tests/test_server.py` | 150 | ✅ all passed |
| `tests/test_release_requirements.py` | 36 | ✅ all passed |
| `ui/tests/` (Node) | 44 | ✅ all passed |
| **Total** | **230** | ✅ |

## Exit criteria

- [x] All automated tests pass (230 / 230)
- [x] Version identity consistent across VERSION, server.py, README, folder name
- [x] `data/state.json` absent from repository
- [x] `docs/` contains only current-version and evergreen files
- [x] `third_party/` contains only `pocket-office-quest-v9`
- [x] `docs/ARCHITECTURE.md` present with web/ vs ui/ explanation
- [x] Static UI bundle present in `web/`
- [x] PDF guide regenerated for v1.0.5
- [x] Smoke test confirms all API endpoints including new sprint, notification, and directive routes
- [x] GitHub-ready release ZIP built from validated repo state

## Notes

Raw test execution output is recorded in `docs/TEST_RESULTS_v1_0_5.txt`.
