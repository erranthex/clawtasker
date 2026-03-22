#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"
RUN_TAG="${RUN_TAG:-$(date +%s)}"
export RUN_TAG
DATA_BACKUP="$(mktemp -d)"
mkdir -p "$DATA_BACKUP/original"
rsync -a data/ "$DATA_BACKUP/original/"
python3 scripts/adapt_pocket_office_release.py
python3 scripts/build_static_ui.py
python3 docs/build_guide.py
python3 -m py_compile server.py
python3 -m unittest discover -s tests -v
node --test ui/tests/*.test.mjs
export CLAWTASKER_API_TOKEN="${CLAWTASKER_API_TOKEN:-change-me-local}"
python3 server.py >/tmp/clawtasker-smoke.log 2>&1 &
PID=$!
cleanup() {
  kill "$PID" >/dev/null 2>&1 || true
  wait "$PID" 2>/dev/null || true
  rm -rf "$ROOT_DIR/data"
  mkdir -p "$ROOT_DIR/data"
  rsync -a "$DATA_BACKUP/original/" "$ROOT_DIR/data/"
  rm -rf "$DATA_BACKUP"
}
trap cleanup EXIT
for _ in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:3000/api/health >/tmp/health.json 2>/dev/null; then
    break
  fi
  sleep 0.5
done
curl -fsS http://127.0.0.1:3000/api/snapshot >/tmp/snapshot.json
curl -fsS http://127.0.0.1:3000/api/openclaw/contract >/tmp/openclaw-contract.json
curl -fsS http://127.0.0.1:3000/api/schema/agent-register >/tmp/agent-register-schema.json
curl -fsS http://127.0.0.1:3000/api/schema/mission-plan >/tmp/mission-plan-schema.json
ROSTER='{"roster":{"source":"smoke-test","agents":[{"id":"iris","name":"Iris","role":"HR Specialist","specialist":"hr","core_skills":["hr","people","policy"],"department":"People","manager":"orion","project_id":"ceo-console","status":"idle"},{"id":"mercury","name":"Mercury","role":"Media Analyst","specialist":"media","core_skills":["media","coverage","signals"],"department":"Intelligence","manager":"violet","project_id":"market-radar","status":"working"}]}}'
curl -fsS -X POST http://127.0.0.1:3000/api/openclaw/roster_sync \
  -H "Authorization: Bearer ${CLAWTASKER_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "$ROSTER" >/tmp/openclaw-roster.json
REGISTER='{"source":"smoke-test","agent":{"id":"nova-'"$RUN_TAG"'","name":"Nova '"$RUN_TAG"'","role":"Signals Analyst","specialist":"research","skills":["signals","analysis","briefing"],"manager":"violet","department":"Intelligence","project_id":"market-radar"}}'
curl -fsS -X POST http://127.0.0.1:3000/api/agents/register \
  -H "Authorization: Bearer ${CLAWTASKER_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "$REGISTER" >/tmp/agent-register.json
curl -fsS http://127.0.0.1:3000/api/snapshot >/tmp/snapshot-after-register.json
MISSION='{"source":"smoke-test","mission":{"id":"M-SMOKE-'"$RUN_TAG"'","title":"Smoke mission '"$RUN_TAG"'","objective":"Validate shared mission planning surfaces and staffing visibility.","status":"active","priority":"P1","horizon":"Today","owner":"orion","project_ids":["ceo-console"],"task_ids":["T-201"],"required_specialists":["code","qa"],"assigned_agents":["codex"],"dependencies":[{"title":"QA validation window","status":"blocked","owner":"ralph"}],"risks":[{"title":"Packaging regression","severity":"high","status":"open"}],"next_actions":["Complete smoke validation."],"success_criteria":["Mission visible in snapshot."]}}'
curl -fsS -X POST http://127.0.0.1:3000/api/missions/plan \
  -H "Authorization: Bearer ${CLAWTASKER_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "$MISSION" >/tmp/mission-plan.json
curl -fsS http://127.0.0.1:3000/api/snapshot >/tmp/snapshot-after-mission.json
PAYLOAD='{"agentId":"codex","event":"task_update","status":"working","taskId":"T-201","projectId":"ceo-console","note":"Smoke test publish '"$RUN_TAG"'","progress":55,"sessionKey":"hook:clawtasker:smoke","runId":"smoke-run-'"$RUN_TAG"'"}'
curl -fsS -X POST http://127.0.0.1:3000/api/openclaw/publish \
  -H "Authorization: Bearer ${CLAWTASKER_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD" >/tmp/openclaw-publish.json
curl -fsS -X POST http://127.0.0.1:3000/api/openclaw/publish \
  -H "Authorization: Bearer ${CLAWTASKER_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD" >/tmp/openclaw-publish-dup.json
curl -fsS --max-time 2 http://127.0.0.1:3000/api/events/stream >/tmp/events-stream.txt || true
python3 - <<'PY'
import json
import os
from pathlib import Path
with open('/tmp/health.json','r',encoding='utf-8') as f:
    health=json.load(f)
assert health['ok'] is True
assert health['version']==Path('VERSION').read_text(encoding='utf-8').strip()
assert health['role']=='visualization-companion'
assert health['restart_safe'] is True
assert health['latest_openclaw_release']=='2026.3.13'
assert health['ui_theme_default']=='ceo / dark'
with open('/tmp/snapshot.json','r',encoding='utf-8') as f:
    snap=json.load(f)
assert 'agents' in snap and len(snap['agents']) >= 5
assert 'filter_options' in snap
assert 'asset_library' in snap
assert 'system_health' in snap
assert 'ticket_system' in snap
assert 'office_layout' in snap
assert snap['office_layout']['active_default'] == 'day'
assert snap['ui_defaults']['theme_preset'] == 'ceo'
assert snap['ui_defaults']['theme_mode'] == 'dark'
assert snap['asset_library']['office_modes'] == ['day', 'night']
assert any(area['id'] == 'scrum_table' for area in snap['office_layout']['areas'])
assert snap['office_layout']['movement_policy']['cross_zone_behavior'] == 'snap'
assert snap['office_layout']['movement_policy']['respect_protected_bounds'] is True
assert len(snap['office_layout']['object_bounds']) >= 10
assert snap['ticket_system']['sorted_by'].startswith('blocked')
assert 'openclaw_integration' in snap
assert 'skill_catalog' in snap and 'hr' in snap['skill_catalog']
assert 'org_templates' in snap and len(snap['org_templates']) >= 3
assert 'scalability_profile' in snap
assert snap['scalability_profile']['tested_agent_target'] == 64
assert 'org_structure' in snap
assert snap['org_structure']['manager_count'] >= 4
assert any(lane['id'] == 'violet' for lane in snap['org_structure']['manager_lanes'])
with open('/tmp/openclaw-contract.json','r',encoding='utf-8') as f:
    contract=json.load(f)
assert contract['ok'] is True
assert contract['latest_stable']=='2026.3.13'
assert contract['hooks_contract']['allowRequestSessionKey'] is False
assert contract['publish_contract']['dedupe_window_seconds'] == 45
assert contract['roster_sync_contract']['endpoint'] == '/api/openclaw/roster_sync'
assert contract['agent_registration_contract']['endpoint'] == '/api/agents/register'
assert contract['agent_registration_contract']['schema'] == '/api/schema/agent-register'
assert contract['mission_plan_contract']['endpoint'] == '/api/missions/plan'
assert contract['mission_plan_contract']['schema'] == '/api/schema/mission-plan'
with open('/tmp/agent-register-schema.json','r',encoding='utf-8') as f:
    register_schema=json.load(f)
assert 'name' in register_schema['properties']
assert 'role' in register_schema['properties']
with open('/tmp/mission-plan-schema.json','r',encoding='utf-8') as f:
    mission_schema=json.load(f)
assert 'mission' in mission_schema['properties']
assert 'objective' in mission_schema['properties']['mission']['properties']
with open('/tmp/agent-register.json','r',encoding='utf-8') as f:
    register=json.load(f)
run_tag = os.environ['RUN_TAG']
expected_agent_id = f'nova-{run_tag}'
expected_name = f'Nova {run_tag}'
assert register['ok'] is True
assert register['agent']['id'] == expected_agent_id
assert register['agent']['name'] == expected_name
assert register['agent']['role'] == 'Signals Analyst'
assert 'analysis' in register['agent']['skills']
assert register['org_card']['name'] == expected_name
assert register['registration']['last_operation'] in {'registered', 'updated'}
with open('/tmp/snapshot-after-register.json','r',encoding='utf-8') as f:
    snap_after=json.load(f)
lane = next(item for item in snap_after['org_structure']['manager_lanes'] if item['id'] == 'violet')
report = next(item for item in lane['reports'] if item['id'] == expected_agent_id)
assert report['name'] == expected_name
assert report['role'] == 'Signals Analyst'
assert 'analysis' in report['skills']
with open('/tmp/mission-plan.json','r',encoding='utf-8') as f:
    mission=json.load(f)
assert mission['ok'] is True
assert mission['mission']['title'].startswith('Smoke mission')
assert mission['mission']['staffing']['coverage_percent'] == 50
with open('/tmp/snapshot-after-mission.json','r',encoding='utf-8') as f:
    snap_mission=json.load(f)
assert 'mission_control' in snap_mission
assert snap_mission['mission_control']['focus_mission']['title'].startswith('Smoke mission')
assert 'qa' in snap_mission['mission_control']['focus_mission']['staffing']['gaps']
with open('/tmp/openclaw-roster.json','r',encoding='utf-8') as f:
    roster=json.load(f)
assert roster['ok'] is True
assert roster['sync']['source'] == 'smoke-test'
assert 'iris' in roster['sync']['last_added'] or 'iris' in roster['sync']['last_updated']
with open('/tmp/openclaw-publish.json','r',encoding='utf-8') as f:
    publish=json.load(f)
assert publish['ok'] is True
assert publish['publish']['agent_id']=='codex'
assert publish['duplicate_publish'] is False
with open('/tmp/openclaw-publish-dup.json','r',encoding='utf-8') as f:
    publish_dup=json.load(f)
assert publish_dup['ok'] is True
assert publish_dup['duplicate_publish'] is True
stream_text = Path('/tmp/events-stream.txt').read_text(encoding='utf-8', errors='ignore')
assert 'event: clawtasker' in stream_text or ': clawtasker live stream' in stream_text
root = Path('.')
version_tag = Path('VERSION').read_text(encoding='utf-8').strip().replace('.', '_').replace('-', '_')
assert (root / 'docs' / f'REQUIREMENTS_v{version_tag}.md').exists()
assert (root / 'docs' / f'TEST_TRACEABILITY_v{version_tag}.md').exists()
assert (root / 'docs' / f'ClawTasker_CEO_Console_Guide_v{version_tag}.pdf').exists()
assert (root / 'docs' / f'render_office_night_v{version_tag}.png').exists()
assert (root / 'ui' / 'dist' / 'assets' / 'main.js').exists()
assert (root / 'ui' / 'dist' / 'assets' / 'styles.css').exists()
assert (root / 'ui' / 'dist' / 'assets' / 'textures' / 'office_map_day_32bit.png').exists()
assert (root / 'ui' / 'dist' / 'assets' / 'textures' / 'office_map_night_32bit.png').exists()
assert (root / 'ui' / 'dist' / 'assets' / 'textures' / 'office_overlay_day_32bit.png').exists()
assert (root / 'ui' / 'dist' / 'assets' / 'textures' / 'office_overlay_night_32bit.png').exists()
assert (root / 'openclaw' / 'publish_status.py').exists()
assert (root / 'openclaw' / 'register_agent.py').exists()
assert (root / 'docs' / 'AGENT_API_GUIDE.md').exists()
assert (root / 'openclaw' / 'prompts' / 'mission-control' / '01-existing-sub-agents-prompt.md').exists()
PY
echo 'Smoke test passed.'
