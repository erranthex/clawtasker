# ClawTasker — Migration Guide

## How Upgrades Work

All runtime data lives in the `data/` directory:

```
data/state.json            — primary state (git-ignored)
data/state.backup.json     — previous state (git-ignored)
data/state.backup.prev.json — state before that (git-ignored)
data/event_log.jsonl       — audit log (git-ignored)
```

Because `data/` is in `.gitignore`, **`git pull` never touches your data**. Your tasks, missions, agents, projects, and conversations are always safe across code upgrades.

When the server starts (`python3 server.py`), `load_state()` automatically migrates any existing `state.json` to match the current schema:

1. **Auto-merge all top-level keys** — every key present in `default_state()` but missing from the loaded state is copied in from defaults. This means any new top-level section added in a new version appears automatically in existing installations.

2. **Deep-merge dict sub-keys** — for top-level keys that are dicts, missing sub-keys are also merged from defaults.

3. **Explicit migration guards** — for structural changes that auto-merge can't handle (new fields inside list items, renamed fields, type changes), a named guard is added in `load_state()`.

4. **`state_version` stamping** — after migration, `state["state_version"]` is set to the current `APP_VERSION`. This lets you see which version last wrote the file.

5. **Auto-save** — if any migration ran, the updated state is saved back to disk before the server finishes starting.

---

## Migration History

### v1.5.x — task comments + state_version (2026-03-27)

**New field:** `task.comments[]`

Every task now has a `comments` list. The migration guard in `load_state()`:

```python
for task in state.get("tasks", []):
    if "comments" not in task:
        task["comments"] = []
        changed = True
```

**New field:** `state.state_version`

The state file now records which app version last wrote it. Stamped automatically on load.

---

## Adding a New Migration

When you add a structural change that auto-merge cannot handle, add a named block in `load_state()` in `server.py`, **after** the auto-merge block and before `refresh_demo_state()`:

```python
# Migrate vX.Y.Z: <description of what changed>
for item in state.get("<collection>", []):
    if "<new_field>" not in item:
        item["<new_field>"] = <default_value>
        changed = True
```

Keep migration guards **additive only** — never delete data. If a field is removed from the schema, leave old data in place; it will be ignored by the server and won't cause errors.

Document every migration in this file under a new version heading.

---

## Emergency Recovery

If `state.json` is corrupt, the server falls back automatically:
`state.json` → `state.backup.json` → `state.backup.prev.json` → `default_state()` (demo data)

To manually restore from a backup:
```bash
cp data/state.backup.json data/state.json
python3 server.py
```
