# ClawTasker CEO Console — Architecture Modularization Plan

## Executive Summary

The ClawTasker CEO Console currently has **two parallel, divergent codebases** serving the same UI:

1. **The Monolith** (`ui/dist/index.html`) — 2,951 lines, self-contained, working
2. **The Modular Source** (`ui/src/`) — 9,562 lines across 17 files, incomplete, not what gets served

This document provides a forensic analysis of the current state, recommends a phased modularization strategy, and defines the coding standards to prevent future regressions.

---

## 1. Forensic Analysis — Current State

### 1.1 The Monolith (`ui/dist/index.html`)

The working application is a single 2,951-line HTML file with everything inline:

| Section | Lines | Content |
|---------|-------|---------|
| HTML head | 1–8 | DOCTYPE, meta, fonts |
| Inline CSS | 9–548 | ~540 lines of complete styling |
| HTML structure | 548–1017 | ~469 lines — sidebar nav, 9 view containers, modals |
| Inline JavaScript | 1017–2949 | ~1,932 lines — all app logic, data, canvas rendering |
| Closing tags | 2949–2951 | 3 lines |

**Embedded assets:** 44 base64-encoded PNG images (~29KB of data URI strings) for portraits, sprite sheets, and office map textures — all inline in the JavaScript.

**Navigation system:** Uses `goV(id, btn)` function with a `META` object mapping view IDs to breadcrumb labels. Views are `<div id="V_xxx" class="vw">` containers toggled with CSS class `on`.

**Key functions in the monolith (1,932 lines of JS):**
- State management (agents, tasks, projects, events, conversations)
- 9 view renderers (dashboard, team, calendar, board, missions, conversations, office, access, appearance)
- Pocket Office v9 canvas engine (sprite animation, pathfinding, furniture placement)
- Portrait/sprite picker system
- Task ticket modal with full CRUD
- Calendar with Week/Month/Year navigation
- Theme system (dark/light/accent colors)
- CEO profile customization
- Mission planning forms

### 1.2 The Modular Source (`ui/src/`)

A parallel, more sophisticated codebase exists but does NOT generate the working app:

| File | Lines | Purpose |
|------|-------|---------|
| `legacy/bootstrap.js` | 2,217 | Parallel reimplementation of monolith JS using ES module imports |
| `ui/app-template.js` | 758 | HTML template string for the OpenClaw-style shell |
| `lib/office.js` | 232 | Office zone geometry, pathfinding, sprite depth sorting |
| `lib/theme.js` | 143 | Theme presets, palette resolution, CSS variable application |
| `lib/conversations.js` | 118 | Conversation normalization, badge labels, channel routing |
| `lib/selectors.js` | 74 | Task/agent filtering, sorting, grouping |
| `ui/app-shell.js` | 17 | Lit web component shell (stub) |
| `ui/app.ts` | 1 | Import redirect |
| `main.ts` | 1 | Style + component import |
| `main.js` | 1 | Entry stub |
| `styles/` (6 files) | 5,993 | Complete CSS system (far more extensive than monolith) |

**Total: 9,562 lines** — but the build script (`build_static_ui.py`) only copies files to `dist/` and generates a minimal HTML shell with `<clawtasker-app>` web component. It does NOT produce the working 2,951-line monolith.

### 1.3 The Build Pipeline

```
build_static_ui.py
├── Copies ui/src/legacy/, ui/src/lib/, ui/src/ui/ → dist/assets/
├── Concatenates 6 CSS files → dist/assets/styles.css (6,109 lines)
├── Copies ui/public/ (binary assets) → dist/
└── Generates minimal dist/index.html:
    <clawtasker-app></clawtasker-app>
    <script type="module" src="/assets/main.js"></script>
```

**The problem:** This build output is NOT the same as the hand-crafted monolith that `server.py` actually serves. The two have diverged completely.

### 1.4 The `web/` Fallback

A simplified standalone version in `web/` (app.js: 1,371–1,587 lines) exists as a static fallback. Its `app.js` calls `officeSceneMarkup()` which is defined in `ui/dist/assets/legacy/bootstrap.js` — so serving from `web/` instead of `ui/dist/` (the v1.2.0 bug) broke the office tab completely.

### 1.5 The Three v1.2.0 Bugs (Confirmed)

| Bug | Root Cause | Impact |
|-----|-----------|--------|
| Wrong `WEB_DIR` | `server.py` changed from `ROOT / 'ui' / 'dist'` to `ROOT / 'web'` | Office tab completely broken; CSS sprite system unreachable |
| Gutted `index.html` | Monolith (2,951 lines) replaced with thin shell (466 lines) | Lost all inline CSS, embedded base64 assets, full JS app logic |
| Broken sprites | Serving `web/styles.css` instead of `ui/dist/assets/styles.css` | `sprite-avatar-frame` CSS class and `--sprite-url` variables missing |

---

## 2. Recommended Strategy — Fix First, Then Modularize

### Phase 1: Stabilize (v1.2.0 Hotfix)

**Do NOT modularize during a bug fix.** The immediate priority is:

1. Fix `WEB_DIR` in `server.py` → point back to `ui/dist/`
2. Surgical merge: Take v1.0.5's monolith as base, inject v1.2.0's Requirements + Test Cases tabs
3. Create BOM (`BILL_OF_MATERIALS.md`) + automated test (`tests/test_bom.py`) + release checklist
4. Verify all 14 agent sprites render, office canvas works, all tabs function
5. Ship working v1.2.0

**Why not modularize now:** The monolith is the known-working state. Modularizing introduces risk. You need a stable v1.2.0 first, then modularize in v1.3.0 with the monolith as the regression baseline.

### Phase 2: Modularize (v1.3.0)

**Goal:** Make `ui/src/` the single source of truth. The monolith dies. `ui/dist/` becomes a build artifact that is NEVER hand-edited.

---

## 3. Modularization Architecture

### 3.1 Target Module Structure

```
ui/src/
├── main.js                    # Entry point: imports, initialization, event wiring
├── index.html                 # HTML template (shell + view containers + modals)
│
├── data/                      # Pure data constants (no logic)
│   ├── agents.js              # AGENTS array (14 agent definitions)
│   ├── tasks.js               # TASKS array (15 task definitions)
│   ├── projects.js            # PROJECTS array (3 projects)
│   ├── events.js              # EVENTS + RECENT_RUNS
│   ├── conversations.js       # CONVERSATIONS_DATA
│   ├── requirements.js        # DEFAULT_REQS
│   ├── test-cases.js          # DEFAULT_TCS
│   └── assets.js              # Base64 portrait/sprite/texture data URIs (44 images)
│
├── state/                     # Application state management
│   ├── store.js               # APP state object, localStorage load/save
│   └── defaults.js            # Initial state factory
│
├── views/                     # One module per tab (render + event handlers)
│   ├── dashboard.js           # renderDash()
│   ├── team.js                # renderTeam() + portrait/sprite picker
│   ├── calendar.js            # renderCal() + week/month/year navigation
│   ├── board.js               # renderBoard() + drag/filter
│   ├── missions.js            # renderMissions() + mission form
│   ├── conversations.js       # renderConversations() + thread UI
│   ├── office.js              # renderOffice() + Pocket Office v9 canvas engine
│   ├── access.js              # renderAccess()
│   ├── appearance.js          # renderAppearance() + theme controls
│   ├── requirements.js        # renderRequirements() + CRUD
│   └── test-cases.js          # renderTestCases() + run simulation
│
├── lib/                       # Shared utilities (already partially exists)
│   ├── router.js              # goV() navigation, META breadcrumbs, hash routing
│   ├── dom.js                 # mk(), txt(), relTime(), mkPortrait(), mkFaceAv()
│   ├── office-engine.js       # Canvas office: geometry, pathfinding, sprite depth
│   ├── selectors.js           # Task/agent filtering, sorting (exists)
│   ├── theme.js               # Theme presets, palette, CSS vars (exists)
│   └── conversations.js       # Normalization, badges (exists)
│
├── ui/                        # Shell components
│   ├── sidebar.js             # Nav section generation
│   ├── topbar.js              # Breadcrumb, search, actions
│   ├── modals.js              # Task ticket, directive, requirement, test case dialogs
│   └── onboarding.js          # First-run guide overlay
│
└── styles/                    # CSS modules (already exists, 6 files)
    ├── config.css             # CSS custom properties (variables)
    ├── base.css               # Reset, typography, body
    ├── layout.css             # Shell grid, sidebar, topbar, main area
    ├── layout.mobile.css      # Responsive breakpoints
    ├── components.css         # Cards, chips, badges, tables, forms, buttons
    └── chat.css               # Conversation-specific styles
```

### 3.2 Module Rules

**Rule 1 — Single Source of Truth:**
`ui/dist/` is ALWAYS generated by `build_static_ui.py`. NEVER hand-edit files in `dist/`.

**Rule 2 — Each module exports explicitly:**
```javascript
// views/dashboard.js
export function renderDash(container, state) { ... }
```

**Rule 3 — No circular imports:**
Data → State → Lib → Views → UI → Main (one-directional dependency flow)

**Rule 4 — Pure data modules have zero side effects:**
`data/*.js` export only constants. No DOM access, no state mutation.

**Rule 5 — Views are self-contained:**
Each view module owns its HTML generation, event binding, and teardown. Views import from `lib/` and `state/` but never from other views.

**Rule 6 — The `assets.js` module isolates base64 data:**
All 44 embedded PNG data URIs live in ONE file. This makes the file large (~29KB) but keeps the rest of the codebase clean. Binary assets (standalone PNGs) stay in `ui/public/assets/`.

### 3.3 Build Pipeline (Enhanced `build_static_ui.py`)

```python
# Phase 1: CSS
#   Concatenate styles/*.css → dist/assets/styles.css

# Phase 2: JavaScript
#   Option A (simple): Concatenate all JS → dist/assets/app.js (IIFE wrapper)
#   Option B (modern): Keep ES modules, use <script type="module">
#   Option C (full): Use Vite to bundle → dist/assets/app.js

# Phase 3: HTML
#   Read ui/src/index.html template
#   Inject version, asset paths
#   Write → dist/index.html

# Phase 4: Assets
#   Copy ui/public/ → dist/ (binary PNGs, logo.svg)
#   Copy vendor/ assets (Pocket Office v9)

# Phase 5: Verify
#   Run BOM check automatically
#   Validate all referenced files exist
```

**Recommended: Option A (concatenation) for now.** This project uses a simple Python HTTP server with no Node.js runtime in production. A concatenation-based build keeps the toolchain light while achieving the core goal: modular source → single distributable.

### 3.4 How to Extract the Monolith

Step-by-step process to decompose the 2,951-line monolith:

```
Step 1: Extract CSS (lines 9–548)
  → Split into styles/config.css (variables, ~30 lines)
  → Split into styles/base.css (resets, body, typography)
  → Split into styles/layout.css (sidebar, topbar, main grid)
  → Split into styles/components.css (cards, chips, buttons, tables)
  → VERIFY: concatenated CSS matches original inline block byte-for-byte

Step 2: Extract Data (from JS block, lines 1017–2949)
  → AGENTS array → data/agents.js
  → TASKS array → data/tasks.js
  → PROJECTS, EVENTS, RUNS → data/projects.js, data/events.js
  → CONVERSATIONS → data/conversations.js
  → Base64 data URIs (PT, SP, HEADS, DAY_MAP, etc.) → data/assets.js
  → VERIFY: data exports match monolith values

Step 3: Extract Views
  → For each goV target (dash, team, cal, board, miss, conv, off, acc, app):
    Find its render function(s)
    Find its event handlers
    Create views/<name>.js with export function render<Name>()
  → VERIFY: each view renders identically

Step 4: Extract Library Utilities
  → mk(), txt(), relTime(), mkPortrait(), mkFaceAv() → lib/dom.js
  → goV(), META → lib/router.js
  → Canvas office engine → lib/office-engine.js
  → VERIFY: all function signatures preserved

Step 5: Extract HTML Structure
  → Sidebar nav → ui/sidebar.js (returns HTML string)
  → Topbar → ui/topbar.js
  → View containers → index.html template
  → Modals (task ticket, directive) → ui/modals.js

Step 6: Wire main.js
  → Import all modules
  → Initialize state
  → Bind navigation
  → Render initial view
  → VERIFY: app boots and all tabs work

Step 7: Reconcile with existing ui/src/ modules
  → Merge selectors.js, theme.js, conversations.js, office.js
    (keep the more complete version, add missing features)
  → Delete legacy/bootstrap.js (replaced by new modular code)
  → Delete ui/app-template.js (replaced by index.html template)
```

---

## 4. Testing Strategy

### 4.1 Regression Gate

After modularization, the new `ui/dist/` output must pass:

1. **BOM Test** (`tests/test_bom.py`): Every required file exists with correct size/format
2. **Feature Parity Test**: All 11 tabs render (dashboard, team, calendar, board, missions, conversations, office, access, appearance, requirements, test cases)
3. **Asset Integrity Test**: All 14 agent sprites + 14 portraits + 19 textures present
4. **CSS Completeness Test**: `sprite-avatar-frame` class exists in compiled CSS, `--sprite-url` variable defined
5. **Office Canvas Test**: `officeSceneMarkup()` callable, canvas initializes
6. **Server Config Test**: `WEB_DIR` in `server.py` points to `ui/dist/`

### 4.2 Unit Tests Per Module

Each `views/*.js` module should have a corresponding test:
```
ui/tests/
├── dashboard.test.mjs
├── team.test.mjs
├── calendar.test.mjs
├── board.test.mjs
├── requirements.test.mjs
├── test-cases.test.mjs
├── router.test.mjs
├── state.test.mjs
└── ... (existing tests: selectors, conversations, theme, shell)
```

### 4.3 Continuous Integration

The existing `.github/workflows/regression.yml` should be updated to:
1. Run `python scripts/build_static_ui.py`
2. Run `python -m pytest tests/test_bom.py`
3. Run `node --test ui/tests/*.test.mjs`
4. Fail the build if any check fails

---

## 5. Best Practices & Coding Standards

### 5.1 File Organization

- **One concept per file.** Don't mix data constants with rendering logic.
- **Flat is better than nested.** Max 2 levels deep in `ui/src/`.
- **Name files by what they export**, not by feature area. (`router.js` not `navigation-helpers.js`)

### 5.2 JavaScript Style

- **`'use strict';`** at top of every non-module file
- **ES module `export`/`import`** for source files
- **No global variables.** All state goes through `state/store.js`
- **Pure functions where possible.** Views receive state as argument, return HTML string or mutate a container
- **JSDoc comments** on every exported function:
  ```javascript
  /**
   * Renders the dashboard view into the given container.
   * @param {HTMLElement} container - The view container element
   * @param {Object} state - Current application state
   */
  export function renderDash(container, state) { ... }
  ```

### 5.3 CSS Standards

- **CSS custom properties** for all colors, spacing, radii (already done in `config.css`)
- **BEM-light naming**: `.card-portrait`, `.nav-link`, `.board-column`
- **No inline styles in JavaScript** except for truly dynamic values (canvas positioning)
- **Mobile-first** with breakpoint overrides in `layout.mobile.css`

### 5.4 Build Hygiene

- **`ui/dist/` is gitignored.** The build generates it fresh each time.
- **`build_static_ui.py` runs in CI.** No manual dist/ commits.
- **VERSION file is the single source** for version strings. `server.py`, `index.html`, `README.md` all read from it.

### 5.5 Preventing the v1.2.0 Regression Pattern

The three bugs happened because:
1. A critical path (`WEB_DIR`) was changed without testing
2. A 2,951-line file was replaced without reading it
3. Sprite rendering was never verified visually

**Safeguards:**

| Safeguard | Prevents |
|-----------|----------|
| `BILL_OF_MATERIALS.md` | "What files must exist" — explicit manifest |
| `tests/test_bom.py` | Automated check that every BOM entry exists with correct format |
| `RELEASE_CHECKLIST.md` | Human verification steps ("Open Office tab, verify sprites render") |
| CI build + test | Build from source every commit, fail on missing assets |
| `server.py` self-check | On startup, verify `WEB_DIR/index.html` exists and is >1000 lines |

---

## 6. Migration Timeline

| Phase | Version | Scope | Risk |
|-------|---------|-------|------|
| **Phase 1** | v1.2.0 | Fix 3 bugs, surgical merge, create BOM/tests | Low — monolith is base |
| **Phase 2** | v1.3.0 | Extract CSS into modules, verify parity | Low — CSS is easiest |
| **Phase 3** | v1.3.x | Extract data constants, verify parity | Low — pure data, no logic |
| **Phase 4** | v1.4.0 | Extract views (dashboard, team first), verify | Medium — logic extraction |
| **Phase 5** | v1.4.x | Extract remaining views + office canvas | Medium — canvas is complex |
| **Phase 6** | v1.5.0 | Wire main.js, kill the monolith, full CI pipeline | High — single cutover |

Each phase ships a working release. The monolith remains the fallback until Phase 6 proves equivalence.

---

## 7. Decision: Concatenation vs. ES Modules vs. Bundler

| Approach | Pros | Cons | Recommended? |
|----------|------|------|-------------|
| **Concatenation** (IIFE) | No runtime deps, Python-only build, simple | No tree-shaking, manual order matters | ✅ **Yes, for now** |
| **ES Modules** (`<script type="module">`) | Native browser support, clean imports | 17+ HTTP requests per page load, no bundling | For dev only |
| **Vite bundler** | Tree-shaking, HMR in dev, optimized output | Adds Node.js dependency, complex build | Future (v2.0+) |

**Recommendation:** Use concatenation for the build, ES modules for source. The build script concatenates in dependency order and wraps in an IIFE. This keeps the production artifact (one HTML + one JS + one CSS) simple and self-contained — matching the project's "local-first, no dependencies" philosophy.

---

## 8. Summary

**The answer to "should we modularize?" is absolutely yes** — the monolith is fragile, hard to maintain, and the v1.2.0 regression proves that AI agents (and humans) can't safely modify a 2,951-line file without breaking something.

But **modularize methodically, not during a crisis fix.** The plan:

1. **v1.2.0:** Fix bugs, add safeguards (BOM + tests + checklist)
2. **v1.3.0+:** Extract modules incrementally, one layer at a time
3. **v1.5.0:** Kill the monolith, modular source is the single truth
4. **Every step:** Verify output matches previous version before shipping
