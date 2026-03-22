# Agent Prompt Pack — v1.5.0

ClawTasker ships the Mission Control onboarding prompts inside the release package.

## Included files

- `openclaw/prompts/mission-control/README.md`
- `openclaw/prompts/mission-control/01-existing-sub-agents-prompt.md`
- `openclaw/prompts/mission-control/02-new-sub-agents-prompt.md`
- `openclaw/prompts/mission-control/03-mission-control-orchestrator-agent-prompt.md`

## How to use them

- use the **existing sub-agents** prompt when an established OpenClaw worker is being connected to ClawTasker for the first time
- use the **new sub-agents** prompt when provisioning a fresh specialist
- use the **Mission Control orchestrator** prompt when a chief, planner, or coordinator is responsible for keeping the rest of the team aligned

## Operational guidance

Pair the prompt pack with:
- `docs/AGENT_API_GUIDE.md` — full API reference for agent integration
- `openclaw/register_agent.py` — agent self-registration script
- `openclaw/update_mission_plan.py` — mission plan update script
- `openclaw/publish_status.py` — task/heartbeat status publisher
- `openclaw/publish_roster.py` — roster sync publisher

## Agent onboarding flow

1. **Register** — register the agent identity so the roster and company chart show the agent name, role, and skills
2. **Read** — read the shared mission brief, current project context, and task board
3. **Plan** — update the mission plan when staffing, dependencies, or success criteria change
4. **Work** — publish task or heartbeat updates as work progresses
5. **Communicate** — surface blockers early and keep handoffs explicit

## v1.5.0 Architecture Notes

As of v1.5.0, the CEO Console UI is built from modular source files:
- Agent-facing views (Team, Board, Missions) are in `ui/src/modules/views/`
- API wiring is in `ui/src/modules/ui/api.js`
- The office engine (agent movement, sprites) is in `ui/src/modules/lib/office-engine.js`
- Build with `python3 scripts/build_ui.py` — no Node.js required
