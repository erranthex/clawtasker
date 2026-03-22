# Bill of Materials — ClawTasker CEO Console v1.5.0

Every required file, what it does, and what breaks without it.

## v1.5.0 — Modularization Complete

### Build Pipeline (required)
| File | Purpose | Breaks Without |
|------|---------|----------------|
| `scripts/build_ui.py` | Assembles ui/dist/index.html | Cannot rebuild from source |
| `scripts/verify_build.py` | 130-check CI verification | No regression detection |
| `ui/src/build-manifest.json` | Build order config | Build fails |
| `ui/src/modules/*.js` (20 files) | Modular JS source | Build produces empty JS |
| `ui/src/styles/monolith.css` | Complete CSS | All styling breaks |
| `ui/src/templates/*.html` (3 files) | HTML head/body/tail | Build produces malformed HTML |

### Build Command
```
python3 scripts/build_ui.py           # builds with manifest version
python3 scripts/build_ui.py 1.5.0     # explicit version override
python3 scripts/verify_build.py       # run 130 verification checks
```

## v1.4.0 Additions — Build Pipeline

| Item | Type | Purpose |
|------|------|---------|
| `scripts/build_ui.py` | Python script | Assembles ui/dist/index.html from modular sources |
| `scripts/modularize_v2.py` | Python script | Decomposes monolith into modular sources |
| `ui/src/build-manifest.json` | JSON config | Declares build order for CSS, HTML, JS |
| `ui/src/sections/*.js` (38 files) | JS source | Individual monolith sections |
| `ui/src/styles/monolith.css` | CSS source | Complete extracted CSS |
| `ui/src/templates/*.html` (3 files) | HTML templates | head, body, tail for assembly |

### Build Command
```
python3 scripts/build_ui.py [version]
```
Produces `ui/dist/index.html` — the self-contained monolith.  
If no version given, uses version from `build-manifest.json`.

### Build Verification
Build with version `1.3.0` MUST produce byte-identical output to the v1.3.0 monolith backup.

## v1.3.0 Additions

| Item | Type | Purpose |
|------|------|---------|
| `FURNITURE_RECTS` (in index.html JS) | Array of 14 objects | Furniture collision rectangles — agents navigate around desks/tables |
| `GAME_ZONES.kitchen` (in index.html JS) | 3-slot zone | Kitchen area for coffee break behavior |
| `GAME_ZONES.conference` (in index.html JS) | 6-slot zone | Conference room for meeting behavior |
| Enhanced `_drawSprite()` | Function | Name + status + dot labels below sprites |
| Enhanced `_pickNextDestination()` | Function | Task-aware movement with kitchen/conference routing |
| Missing agent detection | Roster feature | Stale heartbeat flagging + manual deletion |

## Critical Path Files

| File | Purpose | Breaks Without |
|------|---------|----------------|
| `server.py` | HTTP server; `WEB_DIR` MUST point to `ui/dist/` | Entire app fails to load |
| `ui/dist/index.html` | Complete self-contained app (CSS + HTML + JS) | Entire UI fails |
| `ui/dist/assets/styles.css` | Full CSS system including `sprite-avatar-frame` | All styling breaks, sprites invisible |
| `ui/dist/logo.svg` | App logo | Visual regression |
| `VERSION` | Single source of truth for version string | Version mismatch errors |

## UI Asset Files (ui/dist/assets/)

### Portraits (14 required)
All must be PNG files in `ui/dist/assets/portraits/`:
ceo, charlie, codex, echo, iris, ledger, mercury, orion, pixel, quill, ralph, scout, shield, violet

### Sprites (14 required)
All must be PNG files in `ui/dist/assets/sprites/`:
ceo, charlie, codex, echo, iris, ledger, mercury, orion, pixel, quill, ralph, scout, shield, violet

### Textures (19 required)
All must be PNG files in `ui/dist/assets/textures/`:
board_tile, bookshelf, chair_front, chair_side, chair_side_2, leaf_tile,
office_map_16bit, office_map_16bit_thumb, office_map_32bit,
office_map_day_32bit, office_map_night_32bit,
office_overlay_32bit, office_overlay_day_32bit, office_overlay_night_32bit,
path_tile, rug_green, rug_red, stone_tile, table_round, torch,
wood_bottom, wood_left, wood_right

### Vendor (Pocket Office Quest v9)
Directory: `ui/dist/assets/vendor/pocket-office-quest-v9/`
Must contain all avatar sheets, portraits, compat images, renderings, and source files.

**Note:** Legacy JS files (`main.js`, `legacy/`, `lib/`, `ui/`, `app.js`) were removed in v1.5.0 cleanup. The monolith `index.html` is fully self-contained.

## CSS Verification Checks

The compiled `ui/dist/assets/styles.css` MUST contain:
- `.sprite-avatar-frame` class (for character sprite rendering)
- `--sprite-url` CSS variable (for sprite sheet referencing)

## UI Feature Verification

The `ui/dist/index.html` MUST contain navigation for ALL 14 tabs:
Dashboard, Team, Council, Calendar, Board, Pipeline, Approvals, Missions, Conversations, Office, Access, Requirements, Test Cases, Appearance

## Server Configuration

`server.py` line `WEB_DIR` MUST equal `ROOT / 'ui' / 'dist'` — NEVER `ROOT / 'web'`.
The `web/` directory has been removed (v1.5.0). All UI is served from `ui/dist/`.
