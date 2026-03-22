-- ClawTasker CEO Console v1.5.0 — Database Schema
-- SQLite database for persistent storage of all platform items
-- To initialize: sqlite3 data/clawtasker.db < schemas/database.sql

CREATE TABLE IF NOT EXISTS agents (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    role TEXT DEFAULT 'Agent',
    status TEXT DEFAULT 'idle' CHECK(status IN ('working','blocked','validation','idle','offline')),
    hue TEXT DEFAULT 'planning',
    manager_id TEXT REFERENCES agents(id),
    skills TEXT DEFAULT '[]',  -- JSON array
    workload_active INTEGER DEFAULT 0,
    workload_points INTEGER DEFAULT 0,
    portrait_asset TEXT DEFAULT 'ceo',
    sprite_asset TEXT DEFAULT 'ceo',
    last_heartbeat TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    status TEXT DEFAULT 'backlog' CHECK(status IN ('backlog','ready','in_progress','validation','done')),
    priority TEXT DEFAULT 'P1' CHECK(priority IN ('P0','P1','P2','P3')),
    story_points INTEGER DEFAULT 3,
    owner_id TEXT REFERENCES agents(id),
    project_id TEXT,
    project_name TEXT,
    mission_id TEXT REFERENCES missions(id),
    definition_of_done TEXT DEFAULT '[]',  -- JSON array
    validation_steps TEXT DEFAULT '[]',    -- JSON array
    comments TEXT DEFAULT '[]',            -- JSON array of {author, text, timestamp}
    due_date TEXT,
    blocked INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS missions (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    objective TEXT DEFAULT '',
    status TEXT DEFAULT 'active' CHECK(status IN ('active','blocked','completed','cancelled')),
    priority TEXT DEFAULT 'P1',
    horizon TEXT DEFAULT 'This Week',
    owner_id TEXT REFERENCES agents(id),
    agents TEXT DEFAULT '[]',           -- JSON array of agent IDs
    success_criteria TEXT DEFAULT '[]', -- JSON array
    dependencies TEXT DEFAULT '[]',     -- JSON array
    progress_percent INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS calendar_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    day TEXT NOT NULL CHECK(day IN ('Mon','Tue','Wed','Thu','Fri','Sat','Sun')),
    time TEXT NOT NULL,
    title TEXT NOT NULL,
    agent TEXT DEFAULT 'CEO',
    category TEXT DEFAULT 'hl-plan',
    recurring INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS council_decisions (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    summary TEXT DEFAULT '',
    status TEXT DEFAULT 'pending' CHECK(status IN ('decided','action-required','pending')),
    priority TEXT DEFAULT 'P1',
    participants TEXT DEFAULT '[]',  -- JSON array of agent IDs
    date TEXT DEFAULT (date('now')),
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS requirements (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    priority TEXT DEFAULT 'P1' CHECK(priority IN ('P0','P1','P2','P3')),
    status TEXT DEFAULT 'draft' CHECK(status IN ('draft','approved','in_progress','done')),
    linked_tasks TEXT DEFAULT '[]',  -- JSON array of task IDs
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS test_cases (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    linked_req TEXT REFERENCES requirements(id),
    steps TEXT DEFAULT '[]',     -- JSON array of step strings
    expected TEXT DEFAULT '',
    status TEXT DEFAULT 'PENDING' CHECK(status IN ('PENDING','PASS','FAIL')),
    last_run TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS sprints (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    project_id TEXT,
    goal TEXT DEFAULT '',
    start_date TEXT,
    end_date TEXT,
    status TEXT DEFAULT 'active' CHECK(status IN ('active','completed','cancelled')),
    created_at TEXT DEFAULT (datetime('now'))
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_owner ON tasks(owner_id);
CREATE INDEX IF NOT EXISTS idx_tasks_project ON tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_tasks_mission ON tasks(mission_id);
CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);
CREATE INDEX IF NOT EXISTS idx_calendar_day ON calendar_events(day);
CREATE INDEX IF NOT EXISTS idx_requirements_priority ON requirements(priority);
