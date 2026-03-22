# ClawTasker roster sync helper

Use this helper when OpenClaw infrastructure changes the active team roster and you want the human-facing ClawTasker dashboard to mirror the current agents.

Principles:
- OpenClaw stays the source of truth for agent creation and runtime behavior.
- ClawTasker only mirrors roster metadata for visualization and collaboration.
- Publish only the fields needed for the human user: id, name, role, specialist/home_specialist, department, core_skills, manager, status, current_task_id, project_id, avatar_ref, profile_hue.

Endpoint:
- `POST /api/openclaw/roster_sync`

Minimal shell flow:

```bash
python openclaw/publish_roster.py \
  --file /path/to/roster.json \
  --source openclaw-agents-list
```

Example JSON file:

```json
{
  "agents": [
    {
      "id": "iris",
      "name": "Iris",
      "role": "HR Specialist",
      "specialist": "hr",
      "department": "People",
      "core_skills": ["hr", "people", "policy", "onboarding"],
      "manager": "orion",
      "status": "idle",
      "project_id": "ceo-console"
    }
  ]
}
```
