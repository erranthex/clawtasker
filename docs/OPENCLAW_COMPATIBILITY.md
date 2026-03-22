# OpenClaw compatibility

ClawTasker CEO Console 4.0.0-rc1 is a companion surface for the latest stable OpenClaw team model.

Supported OpenClaw line at build time:
- npm version `2026.3.13`
- GitHub recovery tag `v2026.3.13-1`
- Node 24 recommended
- Node 22.16+ supported for compatibility

Boundary summary:
- OpenClaw remains the runtime and source of truth for agents, sessions, subagents, and workspaces.
- ClawTasker remains the human-facing visualization and collaboration companion.
- Agents may publish heartbeats, task updates, validation notes, conversation notes, and roster sync data into ClawTasker.

Office integration notes:
- Pocket Office Quest v9 portraits and sprite sheets are vendored in `third_party/pocket-office-quest-v9`.
- The supplied v9 archive does not include standalone office-background bitmaps, so ClawTasker generates compatible day/night office layouts for the visualization runtime.
