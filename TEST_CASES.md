# ClawTasker CEO Console v1.5.0 — Test Cases

## TC-001 · Agent Add via GUI
**Linked:** REQ-002
**Steps:**
1. Go to Team tab
2. Click "+ Add agent"
3. Fill in name, role, manager, skills
4. Select a portrait/sprite
5. Click "Register agent"
**Expected:** New agent appears in org chart, roster, and office. Counter updates.
**Status:** PASS

## TC-002 · Agent Edit via GUI
**Linked:** REQ-002
**Steps:**
1. Go to Team tab
2. Click agent name in org chart
3. Edit name inline
4. Click Edit button for full modal
5. Change role and save
**Expected:** Changes reflected across all views.
**Status:** PASS

## TC-003 · Agent Remove via GUI
**Linked:** REQ-002
**Steps:**
1. Go to Team tab
2. Click Edit on an agent card
3. Click "Decommission agent"
4. Confirm dialog
**Expected:** Agent marked offline, removed from active roster. Counter decrements.
**Status:** PASS

## TC-004 · Task Create via GUI
**Linked:** REQ-003
**Steps:**
1. Go to Pipeline tab
2. Click "+ New ticket"
3. Fill in title, description, assignee, priority, story points, epic link, DoD
4. Click "Create ticket"
**Expected:** Task appears in Pipeline, Board, and if validation status, in Approvals. Counter updates.
**Status:** PASS

## TC-005 · Task Edit via GUI
**Linked:** REQ-003
**Steps:**
1. Go to Pipeline tab
2. Click a task row to open detail modal
3. Click Edit button
4. Change status, priority, assignee, DoD
5. Save
**Expected:** Changes reflected in Pipeline, Board, and Approvals views.
**Status:** PASS

## TC-006 · Task Delete via GUI
**Linked:** REQ-003
**Steps:**
1. Go to Pipeline tab
2. Click × button on a task row
3. Confirm deletion
**Expected:** Task removed from all views. Counter decrements.
**Status:** PASS

## TC-007 · Calendar Event Create via GUI
**Linked:** REQ-004
**Steps:**
1. Go to Calendar tab
2. Click "+ Add event"
3. Fill in title, day, time, agent, category, recurring
4. Click "Add to calendar"
**Expected:** Event appears on the correct day in week/month views.
**Status:** PASS

## TC-008 · Calendar Event Edit/Delete
**Linked:** REQ-004
**Steps:**
1. Click an event in the calendar
2. Edit title, time, agent
3. Save — verify changes
4. Click Delete — confirm
**Expected:** Event updated or removed.
**Status:** PASS

## TC-009 · Council Decision CRUD
**Linked:** REQ-005
**Steps:**
1. Go to Council tab
2. Click "+ New decision" — fill form — save
3. Verify card appears
4. Click ✎ Edit — change status — save
5. Click × Delete — confirm
**Expected:** Full add/edit/delete lifecycle works.
**Status:** PASS

## TC-010 · Mission CRUD
**Linked:** REQ-006
**Steps:**
1. Go to Missions tab
2. Click "+ New mission" — fill form — save
3. Verify mission card appears
4. Click Edit — change fields — save
5. Click × on card — confirm delete
**Expected:** Full add/edit/delete lifecycle works.
**Status:** PASS

## TC-011 · Pipeline Filtering
**Linked:** REQ-007
**Steps:**
1. Go to Pipeline tab
2. Select a project from dropdown
3. Verify only matching tasks shown
4. Select a status filter
5. Verify combined filter works
**Expected:** Filters narrow the task list correctly.
**Status:** PASS

## TC-012 · Approvals Workflow
**Linked:** REQ-007
**Steps:**
1. Create a task with status "validation"
2. Go to Approvals tab
3. Verify task appears with Approve/Return buttons
4. Click Approve — verify task moves to "done"
5. Repeat with Return — verify task moves to "in_progress"
**Expected:** Approval workflow changes task status correctly.
**Status:** PASS

## TC-013 · Office Legend
**Linked:** REQ-008
**Steps:**
1. Go to Office tab
2. Verify legend shows 5 states: Working, Blocked, Validation, Idle, Offline
3. Verify color coding matches STATUS_DOT constants
**Expected:** All 5 states visible with correct colors and descriptions.
**Status:** PASS

## TC-014 · Dynamic Counters
**Linked:** REQ-009
**Steps:**
1. Note agent count in topbar
2. Add an agent via Team → + Add agent
3. Verify topbar count increments
4. Verify Team chip count increments
5. Delete a task — verify Board count decrements
**Expected:** All counters update on every data change.
**Status:** PASS

## TC-015 · SQLite Schema Validation
**Linked:** REQ-010
**Steps:**
1. Run: sqlite3 :memory: < schemas/database.sql
2. Verify all 8 tables created
3. Verify indexes created
**Expected:** Schema valid, all tables and indexes created without errors.
**Status:** PASS

## TC-016 · Standalone Mode
**Linked:** REQ-001
**Steps:**
1. Open ui/dist/index.html directly in browser (no server)
2. Verify console shows "Running in standalone mode"
3. Verify all tabs are navigable
4. Verify add/edit/delete operations work client-side
**Expected:** Full functionality in standalone mode.
**Status:** PASS

## TC-017 · Dual-User API Parity
**Linked:** REQ-001
**Steps:**
1. Verify every GUI CRUD action has a documented API endpoint in API.md
2. Check: agents (register), tasks (create/update), calendar (events), council (decisions), missions (update), requirements, test-cases
**Expected:** Every GUI action has an API equivalent.
**Status:** PASS
