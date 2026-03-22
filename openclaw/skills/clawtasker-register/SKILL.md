# ClawTasker agent registration helper

Use this helper when a new or existing OpenClaw agent needs to declare its identity to ClawTasker so the human CEO can see the agent in the company chart.

## Purpose
- register or update an agent name, role, and skills
- keep the roster and organisation chart readable for the human CEO
- let agents self-identify without replacing OpenClaw as the runtime source of truth

## Local contract
- endpoint: `http://127.0.0.1:3000/api/agents/register`
- schema: `http://127.0.0.1:3000/api/schema/agent-register`
- auth: `Authorization: Bearer $CLAWTASKER_API_TOKEN`

## Minimum payload contract
- `name`
- `role`
- at least one of: `skills`, `core_skills`, `specialist`, `home_specialist`, `specialists`

## Helper
```bash
python3 openclaw/register_agent.py \
  --name Iris \
  --role "HR Specialist" \
  --specialist hr \
  --skill "people ops" \
  --skill onboarding \
  --manager quill \
  --project ceo-console
```

## Display rules
- `name` shows on roster cards and in the company chart
- `role` shows on roster cards and in the company chart
- `skills` and `core_skills` feed chart summaries and specialist routing hints

## Safety
- do not publish secrets as skills or notes
- do not try to register as `ceo`
- keep ClawTasker as a local companion; OpenClaw still owns routing, sessions, and workspaces
