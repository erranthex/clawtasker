# ClawTasker mission planning helper

Use this helper when a chief agent, planner, or specialist team needs to keep one shared mission brief visible to the human CEO inside ClawTasker.

## Purpose
- publish or update a mission title, objective, staffing plan, and risk picture
- make dependencies, staffing gaps, and success criteria visible on the dashboard
- keep OpenClaw as the runtime while ClawTasker stays the local mission-control surface

## Local contract
- endpoint: `http://127.0.0.1:3000/api/missions/plan`
- schema: `http://127.0.0.1:3000/api/schema/mission-plan`
- auth: `Authorization: Bearer $CLAWTASKER_API_TOKEN`

## Minimum payload contract
- `title`
- `objective`

Recommended fields:
- `status`
- `priority`
- `horizon`
- `owner`
- `project_ids`
- `task_ids`
- `required_specialists`
- `assigned_agents`
- `dependencies`
- `risks`
- `next_actions`
- `success_criteria`

## Helper
```bash
python3 openclaw/update_mission_plan.py   --title "Morning AI market briefing"   --objective "Ship the 8AM briefing with market signals, release deltas, and confidence notes."   --status active   --priority P1   --project market-radar   --task T-207   --required-specialist research   --required-specialist distribution   --assigned-agent violet   --assigned-agent scout   --next-action "Confirm source set and release stream coverage."   --success "Briefing published before 08:00 local."   --dependency "Release stream snapshot confirmed"
```

## Display rules
- the mission title and objective appear in the dashboard mission brief
- required specialists and assigned agents feed the staffing/coverage view
- risks and dependencies appear in the mission radar and CEO attention queue
- linked task IDs let ClawTasker summarize mission progress from existing tasks

## Safety
- keep updates concise and readable for a human operator
- do not publish secrets in risks, dependencies, or notes
- use mission plans for coordination, not for replacing OpenClaw routing or sessions
