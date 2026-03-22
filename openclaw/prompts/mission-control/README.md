# ClawTasker Mission Control Prompts

This package contains three onboarding prompts for **OpenClaw AI agents** that need to operate through the **ClawTasker Mission Control API**.

## Files

- `01-existing-sub-agents-prompt.md` — onboarding prompt for existing OpenClaw sub-agents
- `02-new-sub-agents-prompt.md` — onboarding prompt for new OpenClaw sub-agents
- `03-mission-control-orchestrator-agent-prompt.md` — orchestration prompt for the Mission Control Orchestrator Agent

## Purpose

These prompts align OpenClaw AI agents with ClawTasker Mission Control so they can:

- register identity, skills, and role
- sync or create tasks on the shared task board
- update task status as done, in-progress, or blocked
- surface blockers early
- request collaboration through the API
- keep execution visible and aligned across the team

## Recommended usage

- Use each file directly as a system prompt, onboarding prompt, or internal README snippet.
- Adapt any wording to your exact API schema if your field names, endpoints, or lifecycle values differ.
- Keep task status values consistent with the live ClawTasker implementation.
