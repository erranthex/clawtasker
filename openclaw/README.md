# OpenClaw companion files

This folder contains example assets for using ClawTasker with a current OpenClaw team.

## Compatibility target
- latest stable npm version: `2026.3.13`
- latest GitHub recovery tag: `v2026.3.13-1`
- Node recommendation: `24`
- compatibility fallback: Node `22.16+`

## Boundary
- OpenClaw keeps routing, sessions, subagents, and workspaces.
- ClawTasker is the human-facing visualization, mission-planning, and collaboration surface.
- Agents can self-register identity data, publish heartbeats, task changes, validation notes, conversation notes, roster sync updates, and shared mission briefs into ClawTasker through the local API.
- If ClawTasker restarts, OpenClaw agents continue working and can republish state later.

## Files
- `openclaw.json5.example` - example config aligned to the current OpenClaw hooks, sessions, agent-to-agent, and cron model
- `publish_status.py` - local helper to publish an agent update into ClawTasker
- `publish_roster.py` - local helper to publish an OpenClaw roster snapshot into ClawTasker
- `register_agent.py` - local helper to register or update an agent name, role, and skills for the company chart
- `update_mission_plan.py` - local helper to publish or refresh a shared mission brief
- `skills/clawtasker-publish/SKILL.md` - copy/paste helper skill for agent workspaces
- `skills/clawtasker-roster-sync/SKILL.md` - helper guidance for publishing roster data from OpenClaw infrastructure
- `skills/clawtasker-register/SKILL.md` - helper guidance for agent self-registration
- `skills/clawtasker-mission-plan/SKILL.md` - helper guidance for mission planning and staffing/risk visibility
- `prompts/mission-control/` - shipped onboarding prompts for existing agents, new agents, and the Mission Control orchestrator

## Recommended onboarding order
1. Use `register_agent.py` so ClawTasker can display the agent's name, role, and skills.
2. Read `docs/AGENT_API_GUIDE.md` and the prompt pack to understand the local contract.
3. Use `update_mission_plan.py` when a chief, planner, or specialist team needs to keep one shared mission brief visible.
4. Use `publish_roster.py` when infrastructure needs to sync the full team or manager relationships.
5. Use `publish_status.py` for heartbeat, task, validation, or conversation updates.
