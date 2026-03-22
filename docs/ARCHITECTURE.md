# Architecture — ClawTasker CEO Console v1.5.0

## Overview

ClawTasker CEO Console is a self-contained web application that provides a human CEO with a mission-control interface for managing AI agent teams.

## System Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    Browser (Client)                       │
│                                                          │
│  ui/dist/index.html (self-contained, ~345KB)            │
│    ├── Inline CSS (540 lines)                           │
│    ├── HTML body (524 lines, 11 view containers)        │
│    └── JavaScript (2,200+ lines, 109 functions)         │
│         Built from 20 modular source files              │
│                                                          │
└────────────────────┬─────────────────────────────────────┘
                     │ HTTP / SSE
┌────────────────────▼─────────────────────────────────────┐
│                    server.py (4,501 lines)                │
│    ├── REST API endpoints                                │
│    ├── SSE event stream (/api/events)                    │
│    ├── Static file serving (ui/dist/)                    │
│    └── Agent management (register, heartbeat, tasks)     │
└──────────────────────────────────────────────────────────┘
```

## Module Architecture (v1.5.0)

The UI is built from 20 modular source files in `ui/src/modules/`:

```
ui/src/modules/
├── data/
│   └── constants.js (157KB)    — All data constants
├── state/
│   └── store.js (1KB)          — Application state
├── lib/
│   ├── router.js (1KB)         — Navigation (goV)
│   ├── dom.js (2KB)            — DOM utilities
│   ├── theme.js (1KB)          — Dark/light mode
│   └── office-engine.js (22KB) — Canvas 2D game engine
├── views/
│   ├── dashboard.js (19KB)     — CEO command center
│   ├── team.js (16KB)          — Org chart + roster
│   ├── board.js (3KB)          — Sprint board
│   ├── missions.js (9KB)       — Mission planner
│   ├── conversations.js (1KB)  — Conversations
│   ├── calendar.js (7KB)       — Multi-view calendar
│   ├── office.js (3KB)         — Virtual office shell
│   ├── access.js (2KB)         — Access matrix
│   ├── appearance.js (4KB)     — Settings
│   └── requirements.js (12KB)  — Requirements + test cases
├── ui/
│   ├── modals.js (8KB)         — Task modals
│   ├── onboarding.js (4KB)     — Platform onboarding
│   └── api.js (3KB)            — SSE/API wiring
└── main.js (2KB)               — Entry point (bootstrap)
```

## Build Pipeline

```bash
python3 scripts/build_ui.py [version]
```

The build script:
1. Reads `ui/src/build-manifest.json` for module order
2. Concatenates `head.html` + `<style>` + CSS + `</style>` + `body.html` + `<script>` + JS modules + `</script>` + `tail.html`
3. Writes `ui/dist/index.html`

No Node.js, no bundler, no transpiler — Python-only.

## Verification

```bash
python3 scripts/verify_build.py
```

130 automated checks covering: files, assets, functions, constants, dependency order, features.

## Data Flow

1. **Agent → Server**: heartbeats, task updates, registration via REST API
2. **Server → Client**: SSE push events for real-time updates
3. **Client → Server**: task creation, mission updates, approvals via REST API
4. **Client-only**: office simulation, calendar, appearance run entirely client-side

## Key Design Decisions

- **Self-contained HTML**: `ui/dist/index.html` embeds all CSS, JS, and base64 image assets (~345KB). Works offline, no CDN.
- **Concatenation build**: No IIFE wrapper yet — 40+ inline HTML onclick handlers require global scope. Migration to addEventListener() planned.
- **Python-only toolchain**: Build and verification scripts use only Python 3 stdlib.
- **Base64 assets**: 44 PNG images (portraits, sprites, maps) embedded as data URIs to maintain single-file deployability.
