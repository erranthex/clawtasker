#!/usr/bin/env python3
"""ClawTasker CEO Console - local-first control server.

A lightweight local web app for a human CEO orchestrating OpenClaw agents.
No external Python dependencies are required.
"""
from __future__ import annotations

import copy
import json
import os
import re
import shutil
import threading
import time
from collections import defaultdict, deque
from queue import Empty, Queue
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
WEB_DIR = ROOT / 'ui' / 'dist'
DATA_DIR = ROOT / "data"
STATE_FILE = DATA_DIR / "state.json"
STATE_BACKUP = DATA_DIR / "state.backup.json"
STATE_BACKUP_PREV = DATA_DIR / "state.backup.prev.json"
AUDIT_LOG = DATA_DIR / "event_log.jsonl"
SCHEMA_DIR = ROOT / "schemas"

HOST = os.getenv("CLAWTASKER_HOST", "127.0.0.1")
PORT = int(os.getenv("CLAWTASKER_PORT", "3000"))
API_TOKEN = os.getenv("CLAWTASKER_API_TOKEN", "change-me-local")
WRITE_LIMIT_PER_MINUTE = int(os.getenv("CLAWTASKER_WRITE_LIMIT", "30"))
HEARTBEAT_STALE_SECONDS = int(os.getenv("CLAWTASKER_STALE_SECONDS", "180"))
MAX_BODY_BYTES = 160 * 1024
APP_VERSION = "1.2.0"

OPENCLAW_LATEST = {
    "release_title": "openclaw 2026.3.13",
    "npm_version": "2026.3.13",
    "github_tag": "v2026.3.13-1",
    "released_at": "2026-03-14",
    "node_recommended": "24",
    "node_compatible": "22.16+",
    "control_ui_url": "http://127.0.0.1:18789",
    "install_command": "npm install -g openclaw@latest",
}

STATE_LOCK = threading.Lock()
STREAM_LOCK = threading.Lock()
STREAM_SUBSCRIBERS: List[Queue] = []
STREAM_REVISION = 0
LAST_STREAM_EVENT: Dict[str, Any] = {}
RATE_LIMITS: Dict[str, deque[float]] = defaultdict(deque)
RUNTIME_META: Dict[str, Any] = {
    "booted_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    "state_source": "cold_start",
    "last_recovered_from": "default",
    "last_load_at": None,
    "last_save_at": None,
    "backup_chain": 0,
    "load_errors": [],
}

VALID_STATUSES = ["backlog", "ready", "in_progress", "validation", "done"]
TASK_PRIORITIES = ["P0", "P1", "P2", "P3"]
HORIZONS = ["Today", "This Week", "This Month", "Later"]
MISSION_STATUSES = ["draft", "planned", "active", "blocked", "review", "done"]
MISSION_SEVERITIES = ["low", "medium", "high", "critical"]
MISSION_STATUS_SORT_ORDER = {"blocked": 0, "active": 1, "planned": 2, "draft": 3, "review": 4, "done": 5}
WEEK_DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
STATUS_SORT_ORDER = {"backlog": 0, "ready": 1, "in_progress": 2, "validation": 3, "done": 4}
PRIORITY_SORT_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
ACTIVE_TASK_STATUSES = {"in_progress", "validation"}
ALLOWED_STATUS_TRANSITIONS = {
    "backlog": {"backlog", "ready"},
    "ready": {"backlog", "ready", "in_progress"},
    "in_progress": {"backlog", "ready", "in_progress", "validation"},
    "validation": {"in_progress", "validation", "done"},
    "done": {"done", "validation"},
}
PUBLISH_DEDUPE_WINDOW_SECONDS = int(os.getenv("CLAWTASKER_PUBLISH_DEDUPE_WINDOW", "45"))

SPECIALIST_ROUTE_ORDER = {
    "planning": ["orion"],
    "code": ["codex", "charlie"],
    "research": ["violet", "scout"],
    "qa": ["ralph"],
    "security": ["shield", "charlie"],
    "ops": ["charlie", "shield"],
    "docs": ["quill"],
    "design": ["pixel"],
    "distribution": ["echo", "quill"],
    "hr": ["orion"],
    "procurement": ["charlie", "shield"],
    "media": ["violet", "echo"],
}

MODEL_TIERS = {
    "orion": "opus",
    "codex": "sonnet",
    "violet": "sonnet",
    "scout": "sonnet",
    "charlie": "sonnet",
    "ralph": "sonnet",
    "shield": "opus",
    "quill": "haiku",
    "pixel": "sonnet",
    "echo": "haiku",
}

HOME_ZONE_BY_SPECIALIST = {
    "planning": "chief_desk",
    "code": "code_pod",
    "research": "research_pod",
    "qa": "qa_pod",
    "security": "ops_pod",
    "ops": "ops_pod",
    "docs": "studio_pod",
    "design": "studio_pod",
    "distribution": "studio_pod",
    "hr": "studio_pod",
    "procurement": "ops_pod",
    "media": "research_pod",
}

ZONE_LABELS = {
    "ceo_strip": "CEO strip",
    "chief_desk": "Chief desk",
    "code_pod": "Engineering desks",
    "research_pod": "Research desks",
    "ops_pod": "Ops / Security desks",
    "qa_pod": "Validation desks",
    "studio_pod": "Design / Docs desks",
    "scrum_table": "Rectangular sync table",
    "review_rail": "Review rail",
    "board_wall": "Agile board wall",
    "lounge": "Lounge",
}


OFFICE_OBJECT_BOUNDS = [
    {"id": "board_wall", "x1": 540, "y1": 52, "x2": 740, "y2": 138},
    {"id": "sync_table", "x1": 556, "y1": 206, "x2": 724, "y2": 314},
    {"id": "eng_north", "x1": 112, "y1": 160, "x2": 336, "y2": 238},
    {"id": "eng_south", "x1": 112, "y1": 304, "x2": 336, "y2": 382},
    {"id": "research_north", "x1": 912, "y1": 160, "x2": 1136, "y2": 238},
    {"id": "research_south", "x1": 912, "y1": 304, "x2": 1136, "y2": 382},
    {"id": "ops_north", "x1": 112, "y1": 480, "x2": 336, "y2": 558},
    {"id": "ops_south", "x1": 112, "y1": 624, "x2": 336, "y2": 666},
    {"id": "review_rail", "x1": 874, "y1": 464, "x2": 1164, "y2": 530},
    {"id": "studio_a", "x1": 944, "y1": 612, "x2": 1156, "y2": 652},
    {"id": "studio_b", "x1": 1102, "y1": 612, "x2": 1288, "y2": 652},
    {"id": "ceo_desk", "x1": 596, "y1": 604, "x2": 730, "y2": 664},
    {"id": "chief_desk", "x1": 430, "y1": 604, "x2": 564, "y2": 664},
    {"id": "lounge", "x1": 408, "y1": 616, "x2": 912, "y2": 740},
]

DEFAULT_UI_SETTINGS = {
    "theme_preset": "ceo",
    "theme_mode": "dark",
    "office_scene": "day",
}

WORKSPACE_BLUEPRINT = [
    "company/",
    "company/control/",
    "company/control/directives/",
    "company/control/org/",
    "company/control/calendar/",
    "company/shared-playbooks/",
    "company/projects/atlas-core/",
    "company/projects/atlas-core/tasks/",
    "company/projects/atlas-core/src/",
    "company/projects/atlas-core/docs/",
    "company/projects/atlas-core/qa/",
    "company/projects/atlas-core/artifacts/",
    "company/projects/market-radar/",
    "company/projects/market-radar/research/",
    "company/projects/market-radar/publishing/",
    "company/projects/ceo-console/",
    "company/projects/ceo-console/web/",
    "company/projects/ceo-console/docs/",
]


OFFICE_VISUAL_CAPACITY = 16
SCALABILITY_TARGET_AGENTS = 64

SPECIALIST_CATALOG = {
    "planning": {"label": "Planning", "department": "Leadership", "keywords": ["planning", "triage", "delegation"]},
    "code": {"label": "Engineering", "department": "Engineering", "keywords": ["code", "backend", "integration"]},
    "research": {"label": "Research", "department": "Research", "keywords": ["research", "analysis", "signals"]},
    "qa": {"label": "Quality", "department": "Quality", "keywords": ["qa", "validation", "acceptance"]},
    "security": {"label": "Security", "department": "Security", "keywords": ["security", "policy", "risk"]},
    "ops": {"label": "Operations", "department": "Operations", "keywords": ["ops", "deployments", "automation"]},
    "docs": {"label": "Documentation", "department": "Documentation", "keywords": ["docs", "guides", "release notes"]},
    "design": {"label": "Design", "department": "Design", "keywords": ["design", "ux", "visual"]},
    "distribution": {"label": "Distribution", "department": "Publishing", "keywords": ["distribution", "publishing", "audience"]},
    "hr": {"label": "People Operations", "department": "People", "keywords": ["hr", "people", "onboarding", "policy"]},
    "procurement": {"label": "Procurement", "department": "Finance", "keywords": ["procurement", "purchasing", "vendor", "license"]},
    "media": {"label": "Media Analysis", "department": "Intelligence", "keywords": ["media", "coverage", "mentions", "narrative"]},
}

ROLE_TEMPLATES = [
    {"role": "HR Specialist", "specialist": "hr", "department": "People", "core_skills": ["hr", "people", "policy", "onboarding"], "manager": "quill", "team_id": "people-comms", "team_name": "People & Communications", "avatar_ref": "quill"},
    {"role": "Purchasing Specialist", "specialist": "procurement", "department": "Finance", "core_skills": ["procurement", "vendor", "license", "cost tracking"], "manager": "charlie", "team_id": "ops-security", "team_name": "Operations & Security", "avatar_ref": "charlie"},
    {"role": "Media Analyst", "specialist": "media", "department": "Intelligence", "core_skills": ["media", "coverage", "mentions", "signals"], "manager": "violet", "team_id": "intelligence", "team_name": "Research & Intelligence", "avatar_ref": "violet"},
]

DEFAULT_AVATAR_REF_BY_SPECIALIST = {
    "planning": "orion",
    "code": "codex",
    "research": "violet",
    "qa": "ralph",
    "security": "shield",
    "ops": "charlie",
    "docs": "quill",
    "design": "pixel",
    "distribution": "echo",
    "hr": "quill",
    "procurement": "charlie",
    "media": "violet",
}

DEFAULT_PROFILE_HUE_BY_SPECIALIST = {
    "planning": "teal",
    "code": "blue",
    "research": "indigo",
    "qa": "green",
    "security": "red",
    "ops": "amber",
    "docs": "teal",
    "design": "pink",
    "distribution": "lime",
    "hr": "teal",
    "procurement": "amber",
    "media": "purple",
}

MANAGER_TEAM_BLUEPRINTS = {
    "orion": {
        "team_id": "executive-operations",
        "team_name": "Executive Operations",
        "coordination_scope": "Company-wide prioritization, routing, approvals, and exception handling.",
        "org_level": "chief",
        "manager_title": "Chief Agent",
    },
    "codex": {
        "team_id": "engineering-product",
        "team_name": "Engineering & Product",
        "coordination_scope": "Coordinates engineering delivery, product implementation, quality loops, and UX release readiness.",
        "org_level": "manager",
        "manager_title": "Engineering Manager",
    },
    "violet": {
        "team_id": "intelligence",
        "team_name": "Research & Intelligence",
        "coordination_scope": "Coordinates research scanning, media analysis, and narrative distribution signals.",
        "org_level": "manager",
        "manager_title": "Intelligence Manager",
    },
    "charlie": {
        "team_id": "ops-security",
        "team_name": "Operations & Security",
        "coordination_scope": "Coordinates infrastructure changes, security review, procurement, and automation hardening.",
        "org_level": "manager",
        "manager_title": "Operations Manager",
    },
    "quill": {
        "team_id": "people-comms",
        "team_name": "People & Communications",
        "coordination_scope": "Coordinates documentation, people operations, onboarding, and communication workflows.",
        "org_level": "manager",
        "manager_title": "Knowledge & People Manager",
    },
}

DEFAULT_MANAGER_BY_SPECIALIST = {
    "planning": "orion",
    "code": "codex",
    "qa": "codex",
    "design": "codex",
    "research": "violet",
    "media": "violet",
    "distribution": "violet",
    "ops": "charlie",
    "security": "charlie",
    "procurement": "charlie",
    "docs": "quill",
    "hr": "quill",
}

TEAM_BY_SPECIALIST = {
    "planning": {"team_id": "executive-operations", "team_name": "Executive Operations"},
    "code": {"team_id": "engineering-product", "team_name": "Engineering & Product"},
    "qa": {"team_id": "engineering-product", "team_name": "Engineering & Product"},
    "design": {"team_id": "engineering-product", "team_name": "Engineering & Product"},
    "research": {"team_id": "intelligence", "team_name": "Research & Intelligence"},
    "media": {"team_id": "intelligence", "team_name": "Research & Intelligence"},
    "distribution": {"team_id": "intelligence", "team_name": "Research & Intelligence"},
    "ops": {"team_id": "ops-security", "team_name": "Operations & Security"},
    "security": {"team_id": "ops-security", "team_name": "Operations & Security"},
    "procurement": {"team_id": "ops-security", "team_name": "Operations & Security"},
    "docs": {"team_id": "people-comms", "team_name": "People & Communications"},
    "hr": {"team_id": "people-comms", "team_name": "People & Communications"},
}

CONVERSATION_SOURCE_LABELS = {
    "browser": "Browser chat",
    "telegram": "Telegram",
    "discord": "Discord",
    "slack": "Slack",
    "webhook": "Webhook",
    "internal_session": "OpenClaw session",
    "system": "System",
}

CONVERSATION_CATEGORY_LABELS = {
    "directive": "Directive",
    "discussion": "Discussion",
    "summary": "Summary",
    "status": "Status",
    "ack": "Ack",
    "system": "System",
}



def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_now() -> str:
    return utc_now().replace(microsecond=0).isoformat()


def parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def publish_stream_event(kind: str, title: str, details: str = "", meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    global STREAM_REVISION, LAST_STREAM_EVENT
    STREAM_REVISION += 1
    event = {
        "id": STREAM_REVISION,
        "timestamp": iso_now(),
        "kind": normalize_text(kind, 32) or "state",
        "title": normalize_text(title, 120) or "State updated",
        "details": normalize_text(details, 240),
        "meta": meta or {},
    }
    LAST_STREAM_EVENT = event
    dropped: List[Queue] = []
    with STREAM_LOCK:
        subscribers = list(STREAM_SUBSCRIBERS)
    for subscriber in subscribers:
        try:
            while subscriber.qsize() >= 3:
                subscriber.get_nowait()
            subscriber.put_nowait(event)
        except Exception:
            dropped.append(subscriber)
    if dropped:
        with STREAM_LOCK:
            for subscriber in dropped:
                if subscriber in STREAM_SUBSCRIBERS:
                    STREAM_SUBSCRIBERS.remove(subscriber)
    return event


def register_stream_subscriber() -> Queue:
    subscriber: Queue = Queue(maxsize=8)
    with STREAM_LOCK:
        STREAM_SUBSCRIBERS.append(subscriber)
    if LAST_STREAM_EVENT:
        try:
            subscriber.put_nowait(LAST_STREAM_EVENT)
        except Exception:
            pass
    return subscriber


def unregister_stream_subscriber(subscriber: Queue) -> None:
    with STREAM_LOCK:
        if subscriber in STREAM_SUBSCRIBERS:
            STREAM_SUBSCRIBERS.remove(subscriber)


def stream_frame(event: Dict[str, Any]) -> bytes:
    payload = json.dumps(event, ensure_ascii=False)
    return f"id: {event.get('id', 0)}\nevent: clawtasker\ndata: {payload}\n\n".encode("utf-8")


def normalize_text(value: Any, max_len: int = 4000) -> str:
    if value is None:
        return ""
    text = str(value)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[^\x09\x0A\x20-\x7E\u00A0-\uFFFF]", "", text)
    text = text.strip()
    if len(text) > max_len:
        text = text[: max_len - 1] + "…"
    return text


def normalize_list(values: Any, max_items: int = 12, item_len: int = 80) -> List[str]:
    if not values:
        return []
    if isinstance(values, str):
        values = [part.strip() for part in values.split(",")]
    result: List[str] = []
    for item in values:
        text = normalize_text(item, item_len)
        if text and text not in result:
            result.append(text)
        if len(result) >= max_items:
            break
    return result


def slugify_identifier(value: Any, max_len: int = 32) -> str:
    text = normalize_text(value, 120).lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    if len(text) > max_len:
        text = text[:max_len].rstrip("-")
    return text or "agent"


def infer_specialist_from_profile(payload: Dict[str, Any]) -> str:
    explicit = normalize_text(
        payload.get("home_specialist")
        or payload.get("specialist")
        or (payload.get("specialists", [""])[0] if isinstance(payload.get("specialists"), list) and payload.get("specialists") else ""),
        32,
    ).lower()
    if explicit in SPECIALIST_CATALOG:
        return explicit

    text_parts = [
        normalize_text(payload.get("role"), 160),
        normalize_text(payload.get("department"), 120),
        " ".join(normalize_list(payload.get("skills"), 12, 40)),
        " ".join(normalize_list(payload.get("core_skills"), 12, 40)),
        " ".join(normalize_list(payload.get("specialists"), 8, 32)),
    ]
    haystack = " ".join(part.lower() for part in text_parts if part).strip()
    if not haystack:
        return "planning"

    best_key = "planning"
    best_score = -1
    for key, meta in SPECIALIST_CATALOG.items():
        score = 0
        if re.search(rf"\b{re.escape(key)}\b", haystack):
            score += 6
        if re.search(rf"\b{re.escape(meta.get('label', '').lower())}\b", haystack):
            score += 4
        if re.search(rf"\b{re.escape(meta.get('department', '').lower())}\b", haystack):
            score += 2
        for keyword in meta.get("keywords", []):
            if re.search(rf"\b{re.escape(str(keyword).lower())}\b", haystack):
                score += 2
        if score > best_score:
            best_key = key
            best_score = score
    return best_key


def normalize_conversation_source(value: Any) -> str:
    raw = normalize_text(value, 40).lower().replace('-', '_').replace(' ', '_')
    aliases = {
        'browser_chat': 'browser',
        'control_ui': 'browser',
        'web': 'browser',
        'webui': 'browser',
        'tg': 'telegram',
        'channel_telegram': 'telegram',
        'channel_discord': 'discord',
        'channel_slack': 'slack',
        'session': 'internal_session',
        'subagent': 'internal_session',
        'internal': 'internal_session',
        'agent_session': 'internal_session',
        'api': 'webhook',
    }
    value = aliases.get(raw, raw)
    return value if value in CONVERSATION_SOURCE_LABELS else 'browser'


def normalize_conversation_category(value: Any) -> str:
    raw = normalize_text(value, 32).lower().replace('-', '_').replace(' ', '_')
    aliases = {
        'message': 'discussion',
        'note': 'summary',
        'update': 'status',
    }
    value = aliases.get(raw, raw)
    return value if value in CONVERSATION_CATEGORY_LABELS else 'discussion'


def conversation_source_label(value: Any) -> str:
    return CONVERSATION_SOURCE_LABELS.get(normalize_conversation_source(value), 'OpenClaw')


def conversation_category_label(value: Any) -> str:
    return CONVERSATION_CATEGORY_LABELS.get(normalize_conversation_category(value), 'Discussion')


def official_channel_url(source: Any, session_key: str = '', explicit_url: str = '') -> str:
    explicit = normalize_text(explicit_url, 260)
    if explicit:
        return explicit
    base = normalize_text(OPENCLAW_LATEST.get('control_ui_url'), 200).rstrip('/') or 'http://127.0.0.1:18789'
    source_id = normalize_conversation_source(source)
    route = {
        'browser': '/#/chat',
        'telegram': '/#/channels/telegram',
        'discord': '/#/channels/discord',
        'slack': '/#/channels/slack',
        'webhook': '/#/hooks',
        'internal_session': '/#/sessions',
        'system': '/#/chat',
    }.get(source_id, '/#/chat')
    session = normalize_text(session_key, 160)
    if session:
        return f"{base}{route}?sessionKey={session}"
    return f"{base}{route}"


def thread_summary_only(thread: Dict[str, Any]) -> bool:
    if bool(thread.get('summary_only')):
        return True
    participants = set(thread.get('participants') or [])
    mode = normalize_text(thread.get('mode'), 40)
    return 'ceo' not in participants and mode in {'chief-specialist', 'specialist-specialist', 'manager-specialist'}


def conversation_messages_visible_by_default(thread: Dict[str, Any]) -> List[Dict[str, Any]]:
    visible: List[Dict[str, Any]] = []
    summary_only = thread_summary_only(thread)
    for message in thread.get('messages', []):
        source = normalize_conversation_source(message.get('source'))
        category = normalize_conversation_category(message.get('category') or message.get('kind'))
        if summary_only and (message.get('hidden_by_default') or (source == 'internal_session' and category == 'discussion')):
            continue
        visible.append(message)
    return visible


def conversation_hidden_message_count(thread: Dict[str, Any]) -> int:
    return max(0, len(thread.get('messages', [])) - len(conversation_messages_visible_by_default(thread)))


def latest_conversation_context_message(thread: Dict[str, Any]) -> Dict[str, Any]:
    messages = conversation_messages_visible_by_default(thread) or thread.get('messages', [])
    if not messages:
        return {}
    for message in reversed(messages):
        if message.get('session_key') or message.get('transcript_path') or message.get('run_id') or message.get('channel_url') or message.get('source'):
            return message
    return messages[-1]


def transcript_reference_from_message(message: Dict[str, Any]) -> Dict[str, str]:
    ref: Dict[str, str] = {}
    if message.get('session_key'):
        ref['session_key'] = normalize_text(message.get('session_key'), 160)
    if message.get('run_id'):
        ref['run_id'] = normalize_text(message.get('run_id'), 120)
    if message.get('transcript_path'):
        ref['transcript_path'] = normalize_text(message.get('transcript_path'), 260)
    if message.get('transcript_url'):
        ref['transcript_url'] = normalize_text(message.get('transcript_url'), 260)
    return ref


def slugify(value: str) -> str:
    value = normalize_text(value, 96).lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "item"


def first_day_of_week(today: Optional[datetime] = None) -> datetime:
    today = today or utc_now()
    monday = today - timedelta(days=today.weekday())
    return monday.replace(hour=0, minute=0, second=0, microsecond=0)


def week_date_for(day_name: str, today: Optional[datetime] = None) -> datetime:
    week = first_day_of_week(today)
    index = WEEK_DAYS.index(day_name)
    return week + timedelta(days=index)


def relative_due(days: int, hour: int = 17, minute: int = 0) -> str:
    dt = utc_now() + timedelta(days=days)
    dt = dt.replace(hour=hour, minute=minute, second=0, microsecond=0)
    return dt.date().isoformat()


def human_status(status: str) -> str:
    return status.replace("_", " ").title()


def agent_display_name(agent_id: str, state: Dict[str, Any]) -> str:
    agent = next((item for item in state.get("agents", []) if item["id"] == agent_id), None)
    return agent["name"] if agent else agent_id


def recommended_owner_for(specialist: str, fallback: Optional[str] = None) -> str:
    routes = SPECIALIST_ROUTE_ORDER.get(specialist, [])
    if routes:
        return routes[0]
    return fallback or "orion"


def backup_owner_for(specialist: str, fallback: Optional[str] = None) -> str:
    routes = SPECIALIST_ROUTE_ORDER.get(specialist, [])
    if routes:
        return routes[-1]
    return fallback or "orion"


def known_actor_ids(state: Dict[str, Any]) -> set[str]:
    return {"ceo"} | {agent["id"] for agent in state.get("agents", [])}


def agent_specialist(agent: Dict[str, Any]) -> str:
    return normalize_text(agent.get("home_specialist") or (agent.get("specialists") or ["planning"])[0], 32) or "planning"


def default_manager_for_specialist(specialist: str) -> str:
    return DEFAULT_MANAGER_BY_SPECIALIST.get(normalize_text(specialist, 32), "orion")


def default_team_for_specialist(specialist: str) -> Dict[str, str]:
    specialist = normalize_text(specialist, 32)
    return copy.deepcopy(TEAM_BY_SPECIALIST.get(specialist, {"team_id": specialist or "company", "team_name": human_status(specialist or "company")}))


def org_card_payload(agent: Dict[str, Any]) -> Dict[str, Any]:
    payload = {
        "id": agent.get("id"),
        "name": agent.get("name"),
        "role": agent.get("role"),
        "manager": agent.get("manager"),
        "manager_name": agent.get("manager_name"),
        "team_id": agent.get("team_id"),
        "team_name": agent.get("team_name"),
        "department": agent.get("department"),
        "home_specialist": agent.get("home_specialist"),
        "specialists": list(agent.get("specialists") or []),
        "core_skills": list(agent.get("core_skills") or []),
        "skills": list(agent.get("skills") or []),
        "profile_hue": agent.get("profile_hue"),
        "avatar_ref": agent.get("avatar_ref"),
        "org_level": agent.get("org_level"),
        "coordination_scope": agent.get("coordination_scope", ""),
        "derived_status": agent.get("derived_status") or normalize_text(agent.get("status"), 32),
        "status": agent.get("status"),
        "current_task": agent.get("current_task") or agent.get("current_task_id") or "No active task",
        "project_name": agent.get("project_name") or agent.get("project_id"),
        "report_count": agent.get("report_count", 0),
    }
    return payload


def enrich_agent_record(agent: Dict[str, Any]) -> Dict[str, Any]:
    home = agent_specialist(agent)
    template = SPECIALIST_CATALOG.get(home, {"department": "Operations", "keywords": [home]})
    agent["home_specialist"] = home
    agent["specialists"] = normalize_list(agent.get("specialists") or [home], 8, 32) or [home]
    skill_seed = list(agent.get("skills") or []) + list(agent.get("specialists") or []) + template.get("keywords", [])
    agent["skills"] = normalize_list(skill_seed, 10, 40)
    core_seed = list(agent.get("core_skills") or []) + [home] + template.get("keywords", [])
    agent["core_skills"] = normalize_list(core_seed, 8, 32)
    agent.setdefault("department", template.get("department", "Operations"))
    team = default_team_for_specialist(home)
    blueprint = MANAGER_TEAM_BLUEPRINTS.get(agent.get("id"))
    if blueprint:
        agent.setdefault("org_level", blueprint.get("org_level", "manager"))
        agent.setdefault("team_id", blueprint.get("team_id"))
        agent.setdefault("team_name", blueprint.get("team_name"))
        agent.setdefault("coordination_scope", blueprint.get("coordination_scope"))
    elif agent.get("id") == "orion":
        agent.setdefault("org_level", "chief")
    else:
        agent.setdefault("org_level", "specialist")
        agent.setdefault("team_id", team.get("team_id"))
        agent.setdefault("team_name", team.get("team_name"))
        agent.setdefault("coordination_scope", "")
    agent.setdefault("avatar_ref", DEFAULT_AVATAR_REF_BY_SPECIALIST.get(home, "orion"))
    agent.setdefault("profile_hue", DEFAULT_PROFILE_HUE_BY_SPECIALIST.get(home, "teal"))
    agent.setdefault("manager", "ceo" if agent.get("id") == "orion" else default_manager_for_specialist(home))
    agent.setdefault("allowed_tools", [])
    agent["allowed_tools"] = normalize_list(agent.get("allowed_tools"), 12, 24)
    agent.setdefault("project_id", "ceo-console")
    agent.setdefault("note", "")
    agent.setdefault("blockers", [])
    agent["blockers"] = normalize_list(agent.get("blockers"), 6, 100)
    agent.setdefault("manager_title", (MANAGER_TEAM_BLUEPRINTS.get(agent.get("id"), {}) or {}).get("manager_title", ""))
    agent.setdefault("team_id", team.get("team_id"))
    agent.setdefault("team_name", team.get("team_name"))
    agent.setdefault("manager_name", "")
    agent.setdefault("collaborating_with", [])
    agent["collaborating_with"] = normalize_list(agent.get("collaborating_with"), 8, 24)
    return agent


def org_templates() -> List[Dict[str, Any]]:
    return copy.deepcopy(ROLE_TEMPLATES)


def build_org_structure(state: Dict[str, Any]) -> Dict[str, Any]:
    agents = [enrich_agent_record(copy.deepcopy(agent)) for agent in state.get("agents", [])]
    chief_id = normalize_text((state.get("sync_contract") or {}).get("chief_agent") or "orion", 32) or "orion"
    agent_map = {agent["id"]: agent for agent in agents}
    ceo = copy.deepcopy((state.get("company") or {}).get("ceo") or {"id": "ceo", "name": "CEO", "role": "CEO / Human operator"})
    chief = org_card_payload(agent_map.get(chief_id, {"id": chief_id, "name": chief_id.title(), "role": "Chief Agent", "org_level": "chief", "specialists": ["planning"], "core_skills": ["planning"]}))
    reports_by_manager: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for agent in agents:
        mgr = normalize_text(agent.get("manager"), 32)
        if mgr == "ceo":
            agent["manager_name"] = ceo.get("name", "CEO")
        elif mgr in agent_map:
            agent["manager_name"] = agent_map[mgr].get("name", mgr)
        if mgr and mgr != agent.get("id"):
            reports_by_manager[mgr].append(agent)
    for entries in reports_by_manager.values():
        entries.sort(key=lambda item: (item.get("org_level") != "manager", item.get("department") or "", item.get("name") or item.get("id")))
    managers: List[Dict[str, Any]] = []
    chief_direct_reports: List[Dict[str, Any]] = []
    seen = {chief_id}
    for agent in agents:
        if agent.get("id") == chief_id:
            continue
        if agent.get("org_level") == "manager" or reports_by_manager.get(agent.get("id")):
            payload = org_card_payload(agent)
            payload["report_count"] = len(reports_by_manager.get(agent.get("id"), []))
            payload["reports"] = [org_card_payload(report) for report in reports_by_manager.get(agent.get("id"), [])]
            payload["skills_summary"] = (agent.get("core_skills") or agent.get("skills") or [])[:4]
            managers.append(payload)
            seen.add(agent.get("id"))
            for report in payload["reports"]:
                seen.add(report.get("id"))
    managers.sort(key=lambda item: (item.get("manager") != chief_id, item.get("team_name") or "", item.get("name") or item.get("id")))
    chief_direct_reports = [org_card_payload(agent) for agent in reports_by_manager.get(chief_id, []) if agent.get("id") not in {m.get("id") for m in managers}]
    unassigned = [org_card_payload(agent) for agent in agents if agent.get("id") not in seen]
    return {
        "ceo": ceo,
        "chief": chief,
        "manager_lanes": managers,
        "chief_direct_reports": chief_direct_reports,
        "unassigned": unassigned,
        "manager_count": len(managers),
        "team_count": len({lane.get("team_id") for lane in managers if lane.get("team_id")}),
        "reporting_edges": sum(len(lane.get("reports", [])) for lane in managers) + len(chief_direct_reports),
    }


def _compute_workload(state: Dict) -> Dict[str, Any]:
    """Per-agent task count and story points."""
    result: Dict[str, Any] = {}
    for agent in state.get("agents", []):
        aid = agent["id"]
        agent_tasks = [t for t in state.get("tasks", []) if t.get("owner") == aid]
        active  = [t for t in agent_tasks if t.get("status") in ("ready","in_progress","validation","validating")]
        backlog = [t for t in agent_tasks if t.get("status") == "backlog"]
        pts     = sum(t.get("story_points") or 1 for t in active)
        result[aid] = {
            "active":       len(active),
            "backlog":      len(backlog),
            "total":        len(agent_tasks),
            "story_points": pts,
            "overloaded":   len(active) > 4,
        }
    return result


def refresh_state_metadata(state: Dict[str, Any]) -> Dict[str, Any]:
    state["agents"] = [enrich_agent_record(agent) for agent in state.get("agents", [])]
    state["missions"] = [normalize_mission_record(mission) for mission in state.get("missions", [])]
    state["access_matrix"] = build_access_matrix(state.get("projects", []), state.get("agents", []))
    state["org_structure"] = build_org_structure(state)
    state["agent_workload"] = _compute_workload(state)
    # Attach workload to each agent record
    wl = state["agent_workload"]
    for ag in state.get("agents", []):
        w = wl.get(ag["id"], {})
        ag["workload_active"] = w.get("active", 0)
        ag["workload_points"] = w.get("story_points", 0)
        ag["overloaded"]      = w.get("overloaded", False)
    # Auto-generate overloaded notifications
    for ag in state.get("agents", []):
        if ag.get("overloaded"):
            existing = any(n.get("agent_id")==ag["id"] and n.get("kind")=="overloaded" and not n.get("dismissed")
                          for n in state.get("notifications",[]))
            if not existing:
                _add_notification(state,"overloaded",
                    f"{ag['name']} overloaded",
                    f"{ag.get('workload_active',0)} active tasks",
                    ag["id"])
    # Sprint burndown
    active_sprints = [s for s in state.get("sprints",[]) if s.get("status")=="active"]
    if active_sprints:
        sp = active_sprints[0]
        sp_tasks = [t for t in state.get("tasks",[]) if t.get("sprint_id")==sp["id"]]
        total_pts = sum(t.get("story_points") or 1 for t in sp_tasks)
        done_pts  = sum(t.get("story_points") or 1 for t in sp_tasks if t.get("status")=="done")
        state.setdefault("metrics",{})["active_sprint"] = {
            "id": sp["id"], "name": sp["name"], "goal": sp.get("goal",""),
            "total_points": total_pts, "done_points": done_pts,
            "remaining_points": total_pts - done_pts,
            "pct_complete": round(done_pts/total_pts*100) if total_pts else 0,
            "status": sp.get("status"),
        }
    # Blocking map: compute which tasks each task is blocking
    tasks_by_id = {t["id"]: t for t in state.get("tasks",[])}
    blocking_map: Dict[str,List[str]] = {}
    for t in state.get("tasks",[]):
        for dep in t.get("depends_on",[]):
            blocking_map.setdefault(dep,[]).append(t["id"])
    for t in state.get("tasks",[]):
        t["blocking"] = blocking_map.get(t["id"],[])
    state["skill_catalog"] = copy.deepcopy(SPECIALIST_CATALOG)
    state["org_templates"] = org_templates()
    integration = state.setdefault("openclaw_integration", {})
    hooks = integration.setdefault("hooks_contract", {})
    hooks["allowedAgentIds"] = [agent["id"] for agent in state.get("agents", [])]
    integration.setdefault("roster_sync", {
        "last_synced_at": None,
        "source": "bootstrap",
        "managed_agents": len(state.get("agents", [])),
        "last_added": [],
        "last_updated": [],
        "replace_missing": False,
    })
    return state


def routing_candidates_for(state: Dict[str, Any], specialist: str, project_id: Optional[str] = None) -> List[str]:
    specialist = normalize_text(specialist, 32)
    if not specialist:
        return ["orion"]
    project = next((item for item in state.get("projects", []) if item.get("id") == project_id), None)
    allowed = set(project.get("allowed_agents", [])) if project else None
    ranked: List[Tuple[int, int, str]] = []
    for agent in state.get("agents", []):
        enrich_agent_record(agent)
        score = 0
        if agent.get("id") in SPECIALIST_ROUTE_ORDER.get(specialist, []):
            score += 25 - SPECIALIST_ROUTE_ORDER[specialist].index(agent.get("id"))
        if agent_specialist(agent) == specialist:
            score += 80
        if specialist in agent.get("specialists", []):
            score += 40
        if specialist in agent.get("core_skills", []):
            score += 28
        if allowed and agent.get("id") in allowed:
            score += 18
        if project_id and agent.get("project_id") == project_id:
            score += 8
        if normalized_agent_state(agent) == "offline":
            score -= 25
        if normalize_text(agent.get("status"), 32) == "blocked":
            score -= 12
        if score > 0:
            active_load = sum(1 for task in state.get("tasks", []) if task.get("owner") == agent.get("id") and task.get("status") in ACTIVE_TASK_STATUSES)
            ranked.append((-score, active_load, agent.get("id")))
    ranked.sort()
    if ranked:
        return [item[2] for item in ranked]
    return SPECIALIST_ROUTE_ORDER.get(specialist, ["orion"]) or ["orion"]


def recommended_owner_for_task(state: Dict[str, Any], task: Dict[str, Any]) -> str:
    candidates = routing_candidates_for(state, normalize_text(task.get("specialist"), 32), normalize_text(task.get("project_id"), 32))
    return candidates[0] if candidates else normalize_text(task.get("owner") or task.get("recommended_owner"), 32) or "orion"


def office_scale_profile(state: Dict[str, Any]) -> Dict[str, Any]:
    agent_count = len(state.get("agents", []))
    overflow = max(0, agent_count - OFFICE_VISUAL_CAPACITY)
    org = build_org_structure(state)
    return {
        "tested_agent_target": SCALABILITY_TARGET_AGENTS,
        "visual_capacity": OFFICE_VISUAL_CAPACITY,
        "agent_count": agent_count,
        "manager_count": org.get("manager_count", 0),
        "team_count": org.get("team_count", 0),
        "overflow_count": overflow,
        "overflow_strategy": "team-and-filter views remain authoritative when more agents exist than the office should show at once",
    }


def parse_date_key(value: str) -> Tuple[int, str]:
    value = normalize_text(value, 32)
    if not value:
        return (1, "9999-12-31")
    try:
        return (0, datetime.fromisoformat(value).date().isoformat())
    except Exception:
        return (1, value)


def task_sort_tuple(task: Dict[str, Any]) -> Tuple[int, int, int, int, str, float, str]:
    blocked_rank = 0 if task.get("blocked") else 1
    status_rank = STATUS_SORT_ORDER.get(task.get("status"), 99)
    priority_rank = PRIORITY_SORT_ORDER.get(task.get("priority"), 99)
    horizon_rank = HORIZONS.index(task.get("horizon")) if task.get("horizon") in HORIZONS else 99
    _due_rank, due_value = parse_date_key(task.get("due_date", ""))
    try:
        updated_ts = -parse_iso(task.get("updated_at", iso_now())).timestamp()
    except Exception:
        updated_ts = 0.0
    return (blocked_rank, status_rank, priority_rank, horizon_rank, due_value, updated_ts, normalize_text(task.get("id"), 32))


def ordered_tasks(tasks: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(tasks, key=task_sort_tuple)


def task_transition_error(task: Dict[str, Any], new_status: str) -> Optional[str]:
    old_status = task.get("status") or "backlog"
    if new_status not in VALID_STATUSES:
        return f"invalid task status: {new_status}"
    if new_status == old_status:
        return None
    allowed = ALLOWED_STATUS_TRANSITIONS.get(old_status, {old_status})
    if new_status not in allowed:
        return f"invalid task transition: {old_status} -> {new_status}"
    if new_status in {"validation", "done"} and not normalize_text(task.get("validation_owner"), 32):
        return "validation owner is required before moving a task into validation or done"
    if new_status == "done" and old_status != "validation":
        return "task must be in validation before moving to done"
    if new_status in {"validation", "done"} and task.get("blocked"):
        return "blocked task cannot move to validation or done"
    return None


def sync_task_assignment(state: Dict[str, Any], task: Dict[str, Any], previous_owner: Optional[str] = None, previous_status: Optional[str] = None) -> None:
    roster = {agent["id"]: agent for agent in state.get("agents", [])}
    previous_owner = previous_owner or task.get("owner")
    previous_status = previous_status or task.get("status")

    def release(agent_id: Optional[str]) -> None:
        if not agent_id:
            return
        agent = roster.get(agent_id)
        if not agent:
            return
        if agent.get("current_task_id") == task.get("id"):
            agent["current_task_id"] = ""
            if normalized_agent_state(agent) not in {"offline", "error"} and not agent.get("blockers"):
                agent["status"] = "idle"

    if previous_owner != task.get("owner") or previous_status not in ACTIVE_TASK_STATUSES or task.get("status") not in ACTIVE_TASK_STATUSES:
        release(previous_owner)

    owner = roster.get(task.get("owner"))
    if not owner:
        return
    if task.get("status") in ACTIVE_TASK_STATUSES or task.get("blocked"):
        owner["current_task_id"] = task.get("id")
        owner["project_id"] = task.get("project_id") or owner.get("project_id")
        if task.get("blocked"):
            owner["status"] = "blocked"
        elif task.get("status") == "validation":
            owner["status"] = "validation"
        else:
            owner["status"] = "working"
    else:
        release(task.get("owner"))


def task_system_health_from_state(state: Dict[str, Any]) -> Dict[str, Any]:
    tasks = state.get("tasks", [])
    roster = {agent["id"]: agent for agent in state.get("agents", [])}
    open_items = sum(1 for task in tasks if task.get("status") != "done")
    active_items = sum(1 for task in tasks if task.get("status") == "in_progress")
    validation_queue = sum(1 for task in tasks if task.get("status") == "validation")
    blocked_items = sum(1 for task in tasks if task.get("blocked"))
    routing_mismatches = sum(1 for task in tasks if task.get("owner") != recommended_owner_for_task(state, task) and task.get("status") not in {"done", "backlog"})
    unassigned_items = sum(1 for task in tasks if not normalize_text(task.get("owner"), 32))
    missing_validators = sum(1 for task in tasks if task.get("status") in {"validation", "done"} and not normalize_text(task.get("validation_owner"), 32))
    assignment_drift = sum(
        1 for task in tasks
        if task.get("status") in ACTIVE_TASK_STATUSES and roster.get(task.get("owner")) and roster[task.get("owner")].get("current_task_id") != task.get("id")
    )
    return {
        "transition_policy": "backlog -> ready -> in_progress -> validation -> done; done can reopen to validation",
        "sorted_by": "blocked, status, priority, horizon, due date, updated_at",
        "duplicate_publish_window_seconds": PUBLISH_DEDUPE_WINDOW_SECONDS,
        "open_items": open_items,
        "active_items": active_items,
        "validation_queue": validation_queue,
        "blocked_items": blocked_items,
        "routing_mismatches": routing_mismatches,
        "unassigned_items": unassigned_items,
        "missing_validators": missing_validators,
        "assignment_drift": assignment_drift,
    }


def register_publish_signature(state: Dict[str, Any], signature: str) -> bool:
    integration = state.setdefault("openclaw_integration", default_state()["openclaw_integration"])
    recent = integration.setdefault("recent_publish_signatures", [])
    cutoff = utc_now() - timedelta(seconds=PUBLISH_DEDUPE_WINDOW_SECONDS)
    keep = []
    duplicate = False
    for entry in recent:
        ts = normalize_text(entry.get("timestamp"), 40)
        try:
            if parse_iso(ts) < cutoff:
                continue
        except Exception:
            continue
        keep.append(entry)
        if entry.get("signature") == signature:
            duplicate = True
    if not duplicate:
        keep.insert(0, {"timestamp": iso_now(), "signature": signature})
    integration["recent_publish_signatures"] = keep[:40]
    return duplicate


def make_task(
    task_id: str,
    title: str,
    project_id: str,
    status: str,
    specialist: str,
    owner: str,
    priority: str,
    horizon: str,
    days_out: int,
    description: str,
    labels: Iterable[str],
    progress: int,
    validation_owner: str,
    blocked: bool = False,
    collaborators: Optional[Iterable[str]] = None,
) -> Dict[str, Any]:
    title = normalize_text(title, 120)
    specialist = normalize_text(specialist, 32) or "planning"
    branch_slug = slugify(title)
    return {
        "id": task_id,
        "title": title,
        "project_id": normalize_text(project_id, 32),
        "status": status if status in VALID_STATUSES else "backlog",
        "specialist": specialist,
        "owner": normalize_text(owner, 32),
        "priority": priority if priority in TASK_PRIORITIES else "P2",
        "horizon": horizon if horizon in HORIZONS else "This Week",
        "due_date": relative_due(days_out, 17),
        "description": normalize_text(description, 500),
        "labels": normalize_list(labels, 12, 32),
        "progress": max(0, min(100, int(progress))),
        "definition_of_done": [
            "Artifact linked or committed in the project repo",
            "Task summary updated for the CEO and chief agent",
            "Validation owner has an explicit review target",
        ],
        "validation_steps": [
            "Checklist reviewed",
            "Branch or artifact opened",
            "Acceptance outcome recorded on the task",
        ],
        "validation_owner": normalize_text(validation_owner, 32),
        "recommended_owner": recommended_owner_for(specialist, owner),
        "backup_owner": backup_owner_for(specialist, owner),
        "blocked": bool(blocked),
        "artifacts": [],
        "story_points": None,
        "sprint_id": None,
        "depends_on": [],
        "blocking": [],
        "collaborators": normalize_list(list(collaborators or []), 6, 24),
        "issue_ref": f"#{200 + int(task_id.split('-')[-1])}",
        "branch_name": f"agent/{owner}/{task_id.lower()}-{branch_slug[:36]}",
        "pr_status": "not-opened",
        "updated_at": iso_now(),
    }


def project_catalog() -> List[Dict[str, Any]]:
    return [
        {
            "id": "atlas-core",
            "name": "Atlas Core",
            "type": "software",
            "tagline": "Shared automation and integration backbone.",
            "repo": "github.com/your-org/atlas-core",
            "github_project": "Atlas delivery board",
            "workspace_root": "company/projects/atlas-core",
            "default_branch": "main",
            "allowed_agents": ["orion", "codex", "charlie", "ralph", "shield"],
            "visibility": "shared-rw",
            "increment_policy": "branch-per-task + PR review",
            "focus": ["integrations", "automation", "security"],
        },
        {
            "id": "market-radar",
            "name": "Market Radar",
            "type": "business",
            "tagline": "Daily briefings, scans, and distribution workflows.",
            "repo": "github.com/your-org/market-radar",
            "github_project": "Radar operations",
            "workspace_root": "company/projects/market-radar",
            "default_branch": "main",
            "allowed_agents": ["orion", "violet", "scout", "quill", "echo"],
            "visibility": "shared-rw",
            "increment_policy": "issue-linked summaries + publish branch",
            "focus": ["research", "briefings", "distribution"],
        },
        {
            "id": "ceo-console",
            "name": "CEO Console",
            "type": "software",
            "tagline": "Product UI, docs, and release packaging for ClawTasker.",
            "repo": "github.com/your-org/clawtasker",
            "github_project": "CEO Console product",
            "workspace_root": "company/projects/ceo-console",
            "default_branch": "main",
            "allowed_agents": ["orion", "codex", "pixel", "quill", "ralph"],
            "visibility": "shared-rw",
            "increment_policy": "short-lived branches + validation before merge",
            "focus": ["product", "ux", "docs"],
        },
    ]


def agent_catalog(now: datetime) -> List[Dict[str, Any]]:
    return [
        {
            "id": "orion",
            "name": "Orion",
            "role": "Chief Agent / Chief of Staff Engineer",
            "manager": "ceo",
            "emoji": "🧭",
            "profile_hue": "teal",
            "status": "working",
            "specialists": ["planning", "orchestration", "delegation"],
            "skills": ["planning", "triage", "CEO updates", "routing"],
            "allowed_tools": ["docs", "browser", "calendar"],
            "home_specialist": "planning",
            "project_id": "ceo-console",
            "current_task_id": "T-200",
            "note": "Running the executive control sweep and routing by exception.",
            "last_heartbeat": (now - timedelta(seconds=12)).replace(microsecond=0).isoformat(),
            "done_summary": "Closed two overnight validation items.",
            "doing_summary": "Preparing the Monday priority stack and delegating the next batch.",
            "next_summary": "Escalate only blockers, approvals, and routing mismatches.",
            "blockers": [],
            "collaborating_with": ["codex", "violet", "ralph"],
            "speaking": False,
        },
        {
            "id": "codex",
            "name": "Codex",
            "role": "Engineering Manager",
            "manager": "orion",
            "org_level": "manager",
            "team_id": "engineering-product",
            "team_name": "Engineering & Product",
            "coordination_scope": "Coordinates engineering delivery, QA loops, and product UX readiness.",
            "emoji": "💻",
            "profile_hue": "blue",
            "status": "working",
            "specialists": ["code", "reliability", "integration"],
            "skills": ["backend", "testing", "integration"],
            "allowed_tools": ["exec", "docs", "browser"],
            "home_specialist": "code",
            "project_id": "ceo-console",
            "current_task_id": "T-203",
            "note": "Implementing the conversation rail and board filters.",
            "last_heartbeat": (now - timedelta(seconds=16)).replace(microsecond=0).isoformat(),
            "done_summary": "Refactored the state adapter for project-aware filters.",
            "doing_summary": "Building the board, backlog, and calendar filters for agent/project views.",
            "next_summary": "Hand off the UI branch to QA after smoke tests pass.",
            "blockers": [],
            "collaborating_with": ["pixel", "ralph"],
            "speaking": False,
        },
        {
            "id": "violet",
            "name": "Violet",
            "role": "Intelligence Manager",
            "manager": "orion",
            "org_level": "manager",
            "team_id": "intelligence",
            "team_name": "Research & Intelligence",
            "coordination_scope": "Coordinates scanning, market intelligence, and narrative publishing signals.",
            "emoji": "🔎",
            "profile_hue": "indigo",
            "status": "working",
            "specialists": ["research", "analysis", "signals"],
            "skills": ["web research", "briefing", "synthesis"],
            "allowed_tools": ["browser", "docs"],
            "home_specialist": "research",
            "project_id": "market-radar",
            "current_task_id": "T-206",
            "note": "Compiling the 8am AI market briefing for the CEO.",
            "last_heartbeat": (now - timedelta(seconds=25)).replace(microsecond=0).isoformat(),
            "done_summary": "Closed yesterday’s trend delta summary.",
            "doing_summary": "Curating the most relevant agent-system and builder signals.",
            "next_summary": "Coordinate the noon radar handoff with Scout and Echo.",
            "blockers": [],
            "collaborating_with": ["scout", "echo"],
            "speaking": True,
        },
        {
            "id": "scout",
            "name": "Scout",
            "role": "Trend Radar",
            "manager": "violet",
            "team_id": "intelligence",
            "team_name": "Research & Intelligence",
            "emoji": "📡",
            "profile_hue": "purple",
            "status": "working",
            "specialists": ["research", "monitoring", "lead scoring"],
            "skills": ["signal clustering", "monitoring", "triage"],
            "allowed_tools": ["browser", "docs"],
            "home_specialist": "research",
            "project_id": "market-radar",
            "current_task_id": "T-207",
            "note": "Scanning creator feeds and release streams for the noon radar.",
            "last_heartbeat": (now - timedelta(seconds=31)).replace(microsecond=0).isoformat(),
            "done_summary": "Published the 6am scanner digest.",
            "doing_summary": "Pulling together the strongest new signals for Violet.",
            "next_summary": "Add product launch items to the backlog if they deserve follow-up.",
            "blockers": [],
            "collaborating_with": ["violet"],
            "speaking": False,
        },
        {
            "id": "charlie",
            "name": "Charlie",
            "role": "Operations Manager",
            "manager": "orion",
            "org_level": "manager",
            "team_id": "ops-security",
            "team_name": "Operations & Security",
            "coordination_scope": "Coordinates infrastructure changes, procurement, secrets, and security readiness.",
            "emoji": "🛠️",
            "profile_hue": "amber",
            "status": "blocked",
            "specialists": ["ops", "infrastructure", "automation"],
            "skills": ["ops", "deployments", "monitoring"],
            "allowed_tools": ["exec", "docs"],
            "home_specialist": "ops",
            "project_id": "atlas-core",
            "current_task_id": "T-209",
            "note": "Waiting on the last credential rotation before re-running the GitHub push workflow.",
            "last_heartbeat": (now - timedelta(seconds=48)).replace(microsecond=0).isoformat(),
            "done_summary": "Completed backup health checks and agent repo sync prep.",
            "doing_summary": "Blocked on one secret value before the deployment workflow can continue.",
            "next_summary": "Rejoin the sync table if the blocker persists after the next cycle.",
            "blockers": ["Legacy deploy secret missing from the access window"],
            "collaborating_with": ["shield", "orion"],
            "speaking": False,
        },
        {
            "id": "ralph",
            "name": "Ralph",
            "role": "QA & Validation Lead",
            "manager": "codex",
            "team_id": "engineering-product",
            "team_name": "Engineering & Product",
            "emoji": "✅",
            "profile_hue": "green",
            "status": "validating",
            "specialists": ["qa", "validation", "acceptance"],
            "skills": ["checklists", "acceptance", "regression"],
            "allowed_tools": ["browser", "docs"],
            "home_specialist": "qa",
            "project_id": "ceo-console",
            "current_task_id": "T-201",
            "note": "Reviewing the approval queue and the new office simulation edge cases.",
            "last_heartbeat": (now - timedelta(seconds=18)).replace(microsecond=0).isoformat(),
            "done_summary": "Validated the morning planning flow.",
            "doing_summary": "Running acceptance checks on the office and board filters.",
            "next_summary": "Approve if the update paths remain deterministic and prompt-safe.",
            "blockers": [],
            "collaborating_with": ["codex", "orion"],
            "speaking": False,
        },
        {
            "id": "shield",
            "name": "Shield",
            "role": "Security Reviewer",
            "manager": "charlie",
            "team_id": "ops-security",
            "team_name": "Operations & Security",
            "emoji": "🛡️",
            "profile_hue": "red",
            "status": "idle",
            "specialists": ["security", "policy", "risk"],
            "skills": ["hardening", "policy", "review"],
            "allowed_tools": ["docs"],
            "home_specialist": "security",
            "project_id": "atlas-core",
            "current_task_id": None,
            "note": "Ready to review webhook rules, token handling, and GitHub publish guardrails.",
            "last_heartbeat": (now - timedelta(seconds=63)).replace(microsecond=0).isoformat(),
            "done_summary": "Finished the weekly control review.",
            "doing_summary": "Standing by for security-sensitive changes.",
            "next_summary": "Pick up Charlie’s blocker if the deploy secret issue escalates.",
            "blockers": [],
            "collaborating_with": ["charlie"],
            "speaking": False,
        },
        {
            "id": "quill",
            "name": "Quill",
            "role": "Knowledge & People Manager",
            "manager": "orion",
            "org_level": "manager",
            "team_id": "people-comms",
            "team_name": "People & Communications",
            "coordination_scope": "Coordinates docs, onboarding, communication, and people operations.",
            "emoji": "✍️",
            "profile_hue": "teal",
            "status": "working",
            "specialists": ["docs", "copy", "playbooks"],
            "skills": ["release notes", "guides", "summaries"],
            "allowed_tools": ["docs", "browser"],
            "home_specialist": "docs",
            "project_id": "ceo-console",
            "current_task_id": "T-205",
            "note": "Updating the README and guide for the shared-workspace model.",
            "last_heartbeat": (now - timedelta(seconds=22)).replace(microsecond=0).isoformat(),
            "done_summary": "Refreshed the executive summary structure.",
            "doing_summary": "Writing the setup and GitHub workflow notes for the new release.",
            "next_summary": "Package the guide after Pixel finishes the UI screens.",
            "blockers": [],
            "collaborating_with": ["pixel", "orion"],
            "speaking": False,
        },
        {
            "id": "pixel",
            "name": "Pixel",
            "role": "Design Lead",
            "manager": "codex",
            "team_id": "engineering-product",
            "team_name": "Engineering & Product",
            "emoji": "🎨",
            "profile_hue": "pink",
            "status": "working",
            "specialists": ["design", "visual", "ux"],
            "skills": ["ui systems", "wallboards", "visual polish"],
            "allowed_tools": ["docs", "browser"],
            "home_specialist": "design",
            "project_id": "ceo-console",
            "current_task_id": "T-204",
            "note": "Polishing the pixel office, body avatars, and org chart for the CEO-facing release.",
            "last_heartbeat": (now - timedelta(seconds=14)).replace(microsecond=0).isoformat(),
            "done_summary": "Reworked the color system for light and dark themes.",
            "doing_summary": "Designing the one-floor coworking office and team filters.",
            "next_summary": "Send final UI assets to Quill and Codex.",
            "blockers": [],
            "collaborating_with": ["codex", "quill"],
            "speaking": False,
        },
        {
            "id": "echo",
            "name": "Echo",
            "role": "Distribution Specialist",
            "manager": "violet",
            "team_id": "intelligence",
            "team_name": "Research & Intelligence",
            "emoji": "📣",
            "profile_hue": "lime",
            "status": "idle",
            "specialists": ["distribution", "publishing", "rollout"],
            "skills": ["publishing", "scheduling", "channel ops"],
            "allowed_tools": ["docs", "browser"],
            "home_specialist": "distribution",
            "project_id": "market-radar",
            "current_task_id": None,
            "note": "Waiting for the noon brief and release note before publishing.",
            "last_heartbeat": (now - timedelta(seconds=51)).replace(microsecond=0).isoformat(),
            "done_summary": "Scheduled yesterday’s digest.",
            "doing_summary": "On standby for the next approved package.",
            "next_summary": "Take the final brief from Violet and Quill once validation clears.",
            "blockers": [],
            "collaborating_with": ["violet", "quill"],
            "speaking": False,
        },
        {
            "id": "iris",
            "name": "Iris",
            "role": "HR Specialist",
            "manager": "quill",
            "team_id": "people-comms",
            "team_name": "People & Communications",
            "emoji": "🧾",
            "profile_hue": "teal",
            "status": "idle",
            "specialists": ["hr", "people", "policy"],
            "skills": ["hr", "onboarding", "policy", "people ops"],
            "allowed_tools": ["docs", "browser"],
            "home_specialist": "hr",
            "project_id": "ceo-console",
            "current_task_id": None,
            "note": "Keeping onboarding checklists and people policies ready for the next team expansion.",
            "last_heartbeat": (now - timedelta(seconds=58)).replace(microsecond=0).isoformat(),
            "done_summary": "Refreshed the onboarding starter pack.",
            "doing_summary": "Standing by for people-ops requests and org updates.",
            "next_summary": "Coordinate with Quill if the roster grows this afternoon.",
            "blockers": [],
            "collaborating_with": ["quill"],
            "speaking": False,
        },
        {
            "id": "ledger",
            "name": "Ledger",
            "role": "Purchasing Specialist",
            "manager": "charlie",
            "team_id": "ops-security",
            "team_name": "Operations & Security",
            "emoji": "💳",
            "profile_hue": "amber",
            "status": "working",
            "specialists": ["procurement", "vendor", "license"],
            "skills": ["procurement", "vendor", "license", "cost tracking"],
            "allowed_tools": ["docs", "browser"],
            "home_specialist": "procurement",
            "project_id": "atlas-core",
            "current_task_id": None,
            "note": "Tracking tool renewals and supplier follow-up for the engineering toolchain.",
            "last_heartbeat": (now - timedelta(seconds=35)).replace(microsecond=0).isoformat(),
            "done_summary": "Reconciled the monthly tooling list.",
            "doing_summary": "Reviewing next-cycle procurement requests with Charlie.",
            "next_summary": "Package the approved purchasing queue for CEO review if spend changes.",
            "blockers": [],
            "collaborating_with": ["charlie", "shield"],
            "speaking": False,
        },
        {
            "id": "mercury",
            "name": "Mercury",
            "role": "Media Analyst",
            "manager": "violet",
            "team_id": "intelligence",
            "team_name": "Research & Intelligence",
            "emoji": "📰",
            "profile_hue": "purple",
            "status": "working",
            "specialists": ["media", "coverage", "signals"],
            "skills": ["media", "coverage", "mentions", "signals"],
            "allowed_tools": ["browser", "docs"],
            "home_specialist": "media",
            "project_id": "market-radar",
            "current_task_id": None,
            "note": "Tracking narrative shifts and notable mentions for the intelligence queue.",
            "last_heartbeat": (now - timedelta(seconds=27)).replace(microsecond=0).isoformat(),
            "done_summary": "Flagged two important creator signals.",
            "doing_summary": "Preparing the media pulse summary for Violet and Echo.",
            "next_summary": "Escalate only material narrative risks or launch inflections.",
            "blockers": [],
            "collaborating_with": ["violet", "echo"],
            "speaking": False,
        },
    ]


def task_catalog() -> List[Dict[str, Any]]:
    return [
        make_task("T-200", "Weekly executive operating plan", "ceo-console", "in_progress", "planning", "orion", "P0", "Today", 0, "Prepare the CEO briefing, priority stack, risks, approvals, and workspace decisions for the week.", ["ceo", "planning", "today"], 78, "ralph", collaborators=["codex", "violet"]),
        make_task("T-201", "Approval queue and validation rail", "ceo-console", "validation", "qa", "ralph", "P0", "Today", 0, "Review the approval queue, confirm reviewer ownership, and record the outcome for every sensitive change.", ["validation", "approval", "ceo"], 92, "orion", collaborators=["codex"]),
        make_task("T-202", "Shared workspace scaffold", "atlas-core", "done", "ops", "charlie", "P1", "This Week", -1, "Create the company/projects/shared-playbooks folder structure and document the branch-per-task workflow.", ["ops", "workspace", "git"], 100, "shield", collaborators=["orion"]),
        make_task("T-203", "Agent and project filters across board views", "ceo-console", "in_progress", "code", "codex", "P0", "Today", 1, "Add global filters so the week calendar, progression board, and backlog pipeline can show only the tasks for selected agents or projects.", ["code", "filters", "ui"], 66, "ralph", collaborators=["pixel"]),
        make_task("T-204", "Pocket Office engine polish", "ceo-console", "in_progress", "design", "pixel", "P0", "Today", 1, "Refine the Pocket Office-powered office engine with desk pods, a rectangular sync table, board wall, plants, furniture, depth-safe seating, and clearer specialist body avatars.", ["design", "office", "ux"], 61, "ralph", collaborators=["codex", "quill"]),
        make_task("T-205", "README and guide refresh", "ceo-console", "in_progress", "docs", "quill", "P1", "Today", 1, "Update the README and guide with conversations, shared project workspaces, GitHub workflow, and the office simulation model.", ["docs", "release"], 57, "orion", collaborators=["pixel"]),
        make_task("T-206", "8AM AI market briefing", "market-radar", "in_progress", "research", "violet", "P0", "Today", 0, "Collect AI, vibe-coding, and agent-system signals and prepare a source-backed executive brief.", ["research", "briefing", "daily"], 71, "orion", collaborators=["scout", "echo"]),
        make_task("T-207", "Noon trend radar", "market-radar", "in_progress", "research", "scout", "P1", "Today", 0, "Scan fast-moving releases and creator signals for the noon radar update.", ["research", "signals", "scanner"], 48, "violet", collaborators=["echo"]),
        make_task("T-208", "Conversation rail for CEO and chief", "ceo-console", "ready", "code", "codex", "P1", "This Week", 2, "Add a Conversations tab where the CEO can talk to the chief or specialists and the chief can coordinate sub-agents without bypassing the board.", ["code", "conversations", "coordination"], 0, "ralph", collaborators=["orion"]),
        make_task("T-209", "GitHub push workflow hardening", "atlas-core", "in_progress", "ops", "charlie", "P0", "Today", 0, "Complete the branch-per-task and PR workflow, then document how increments appear in GitHub Projects and release notes.", ["ops", "github", "blocked"], 33, "shield", blocked=True, collaborators=["orion", "shield"]),
        make_task("T-210", "Prompt-injection safety checklist", "atlas-core", "ready", "security", "shield", "P0", "This Week", 3, "Review task and conversation payload handling, enforce deterministic auto-replies only, and document secure webhook boundaries.", ["security", "safety"], 0, "ralph", collaborators=["charlie"]),
        make_task("T-211", "Release wallboard mode", "ceo-console", "backlog", "design", "pixel", "P2", "This Month", 6, "Create a big-screen wallboard layout for the command center, office, and approval queue.", ["design", "wallboard"], 0, "orion", collaborators=["quill"]),
        make_task("T-212", "Publish workflow and release notes", "market-radar", "ready", "distribution", "echo", "P1", "This Week", 2, "Define how approved briefings and release notes move from task completion to publication and audience channels.", ["distribution", "publishing"], 0, "orion", collaborators=["quill", "violet"]),
        make_task("T-213", "Validation SLA dashboard", "ceo-console", "backlog", "qa", "ralph", "P2", "This Month", 5, "Show time in validation, reviewer load, and overdue approvals for the human CEO.", ["qa", "analytics"], 0, "orion"),
        make_task("T-214", "Sub-agent routing prompt pack", "ceo-console", "done", "docs", "quill", "P1", "This Week", -1, "Finalize the chief and specialist prompt pack with specialist labels, handoff rules, and task-note expectations.", ["docs", "openclaw"], 100, "ralph", collaborators=["orion"]),
    ]


def mission_catalog() -> List[Dict[str, Any]]:
    return [
        {
            "id": "M-300",
            "title": "CEO Console rc3 release candidate",
            "objective": "Ship the refreshed CEO Console release candidate with mission planning, updated docs, and a GitHub-ready package.",
            "status": "active",
            "priority": "P0",
            "horizon": "This Week",
            "owner": "orion",
            "project_ids": ["ceo-console"],
            "task_ids": ["T-200", "T-201", "T-203", "T-204", "T-205", "T-208", "T-211", "T-213", "T-214"],
            "required_specialists": ["planning", "code", "design", "docs", "qa"],
            "assigned_agents": ["orion", "codex", "pixel", "quill", "ralph"],
            "summary": "Keep product, validation, and docs aligned for a clean release candidate handoff.",
            "next_actions": [
                "Close the validation rail for the release slice.",
                "Rebuild docs, static UI, and package artifacts.",
                "Confirm README and onboarding guidance for new agents.",
            ],
            "success_criteria": [
                "Release package builds cleanly.",
                "Validation queue is explicit and owned.",
                "Docs and agent onboarding assets are current.",
            ],
            "dependencies": [
                {"id": "D-300-1", "title": "Approval queue clear", "status": "pending", "owner": "ralph", "detail": "Approval queue and validation rail must finish before packaging."},
                {"id": "D-300-2", "title": "Docs packaged", "status": "in_progress", "owner": "quill", "detail": "README, guide, and release notes need the rc3 mission-planning updates."},
            ],
            "risks": [
                {"id": "R-300-1", "title": "Validation backlog delays packaging", "severity": "medium", "status": "open", "owner": "ralph", "mitigation": "Keep the CEO attention queue exception-only and close the remaining validation item early."},
            ],
            "milestones": [
                {"id": "MS-300-1", "title": "UI shell refresh", "status": "done", "due_date": relative_due(0, 17)},
                {"id": "MS-300-2", "title": "Docs and guide refresh", "status": "active", "due_date": relative_due(1, 17)},
                {"id": "MS-300-3", "title": "GitHub release candidate package", "status": "planned", "due_date": relative_due(2, 17)},
            ],
            "source": "default",
            "created_at": iso_now(),
            "updated_at": iso_now(),
        },
        {
            "id": "M-301",
            "title": "Morning AI market briefing",
            "objective": "Produce the daily briefing with sourced signals, clear narrative priorities, and a distribution-ready handoff.",
            "status": "active",
            "priority": "P0",
            "horizon": "Today",
            "owner": "violet",
            "project_ids": ["market-radar"],
            "task_ids": ["T-206", "T-207", "T-212"],
            "required_specialists": ["research", "distribution"],
            "assigned_agents": ["violet", "scout", "echo"],
            "summary": "Research and publishing stay connected so the human CEO sees the strongest market signals quickly.",
            "next_actions": ["Complete the 8AM brief.", "Prep the noon radar handoff.", "Package the approved summary for publishing."],
            "success_criteria": ["Briefing is sourced.", "Radar handoff is explicit.", "Publishing path is ready once approved."],
            "dependencies": [
                {"id": "D-301-1", "title": "Noon radar input", "status": "in_progress", "owner": "scout", "detail": "The midday signal sweep needs Scout's latest scanner output."}
            ],
            "risks": [
                {"id": "R-301-1", "title": "Publishing handoff waits on approval", "severity": "low", "status": "open", "owner": "echo", "mitigation": "Keep Echo attached early so packaging starts before final approval lands."}
            ],
            "milestones": [
                {"id": "MS-301-1", "title": "8AM brief drafted", "status": "active", "due_date": relative_due(0, 10)},
                {"id": "MS-301-2", "title": "Noon radar ready", "status": "planned", "due_date": relative_due(0, 13)},
            ],
            "source": "default",
            "created_at": iso_now(),
            "updated_at": iso_now(),
        },
        {
            "id": "M-302",
            "title": "Atlas workflow hardening",
            "objective": "Harden the GitHub workflow, safety checklist, and ops handoff so Atlas work is safe to push and recover.",
            "status": "blocked",
            "priority": "P0",
            "horizon": "Today",
            "owner": "charlie",
            "project_ids": ["atlas-core"],
            "task_ids": ["T-202", "T-209", "T-210"],
            "required_specialists": ["ops", "security", "qa"],
            "assigned_agents": ["charlie", "shield", "ralph"],
            "summary": "Ops and security need one reliable workflow so deployment and review remain recoverable.",
            "next_actions": ["Restore the missing deploy secret.", "Finish the push workflow hardening.", "Validate the safety checklist before merge."],
            "success_criteria": ["Blocked push workflow is cleared.", "Safety checklist is complete.", "Security review is explicit."],
            "dependencies": [
                {"id": "D-302-1", "title": "Deploy secret restored", "status": "blocked", "owner": "charlie", "detail": "The GitHub push workflow remains blocked until the legacy deploy secret is restored."}
            ],
            "risks": [
                {"id": "R-302-1", "title": "Secret gap blocks workflow hardening", "severity": "high", "status": "open", "owner": "charlie", "mitigation": "Escalate secret rotation and keep Shield paired for validation once restored."}
            ],
            "milestones": [
                {"id": "MS-302-1", "title": "Shared workspace scaffold", "status": "done", "due_date": relative_due(-1, 17)},
                {"id": "MS-302-2", "title": "Push workflow hardened", "status": "blocked", "due_date": relative_due(0, 17)},
            ],
            "source": "default",
            "created_at": iso_now(),
            "updated_at": iso_now(),
        },
    ]


def recurring_jobs() -> List[Dict[str, Any]]:
    jobs: List[Dict[str, Any]] = []
    for day in ["Mon", "Tue", "Wed", "Thu", "Fri"]:
        jobs.append({"id": f"J-{day}-001", "day": day, "time": "06:55", "title": "Chief morning kickoff", "owner": "orion", "specialist": "planning", "project_id": "ceo-console", "frequency": "daily"})
        jobs.append({"id": f"J-{day}-010", "day": day, "time": "08:00", "title": "8AM market briefing", "owner": "violet", "specialist": "research", "project_id": "market-radar", "frequency": "daily"})
        jobs.append({"id": f"J-{day}-020", "day": day, "time": "11:30", "title": "Noon radar prep", "owner": "scout", "specialist": "research", "project_id": "market-radar", "frequency": "daily"})
        jobs.append({"id": f"J-{day}-030", "day": day, "time": "16:00", "title": "Validation sweep", "owner": "ralph", "specialist": "qa", "project_id": "ceo-console", "frequency": "daily"})
    jobs.extend([
        {"id": "J-Sat-001", "day": "Sat", "time": "09:30", "title": "Weekly release note polish", "owner": "quill", "specialist": "docs", "project_id": "ceo-console", "frequency": "weekly"},
        {"id": "J-Sun-001", "day": "Sun", "time": "17:00", "title": "Operations readiness check", "owner": "charlie", "specialist": "ops", "project_id": "atlas-core", "frequency": "weekly"},
    ])
    return jobs


def calendar_blocks(agents: List[Dict[str, Any]], tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    task_lookup = {task["id"]: task for task in tasks}
    blocks: List[Dict[str, Any]] = []
    for agent in agents:
        current_task = task_lookup.get(agent.get("current_task_id"))
        for index, day in enumerate(WEEK_DAYS):
            title = current_task["title"] if current_task else "Open focus block"
            project_id = current_task["project_id"] if current_task else agent.get("project_id")
            blocks.append({
                "id": f"C-{agent['id']}-{index}",
                "agent": agent["id"],
                "agent_name": agent["name"],
                "day": day,
                "time": "09:00",
                "title": title,
                "specialist": current_task["specialist"] if current_task else agent.get("home_specialist", agent["specialists"][0]),
                "project_id": project_id,
                "state": agent["status"],
            })
        if agent["id"] in {"orion", "ralph", "violet"}:
            blocks.append({
                "id": f"R-{agent['id']}",
                "agent": agent["id"],
                "agent_name": agent["name"],
                "day": "Wed",
                "time": "14:30",
                "title": "Sync-table alignment",
                "specialist": "planning",
                "project_id": agent.get("project_id"),
                "state": "meeting",
            })
    return blocks


def recent_runs(now: datetime) -> List[Dict[str, Any]]:
    return [
        {
            "id": "R-2201",
            "agent": "orion",
            "project_id": "ceo-console",
            "title": "Executive control sweep",
            "outcome": "needs_attention",
            "summary": "Escalated Charlie’s blocker, queued one approval, and refreshed the weekly priorities.",
            "timestamp": (now - timedelta(minutes=11)).replace(microsecond=0).isoformat(),
            "artifacts": ["company/control/directives/weekly-operating-plan.md"],
        },
        {
            "id": "R-2202",
            "agent": "codex",
            "project_id": "ceo-console",
            "title": "Filter system pass",
            "outcome": "working",
            "summary": "Added project and agent filters across board, backlog, and calendar views.",
            "timestamp": (now - timedelta(minutes=19)).replace(microsecond=0).isoformat(),
            "artifacts": ["company/projects/ceo-console/ui/main.js"],
        },
        {
            "id": "R-2203",
            "agent": "violet",
            "project_id": "market-radar",
            "title": "8AM market briefing",
            "outcome": "working",
            "summary": "Curated the strongest AI agent and builder signals for the executive digest.",
            "timestamp": (now - timedelta(minutes=24)).replace(microsecond=0).isoformat(),
            "artifacts": ["company/projects/market-radar/research/briefing-8am.md"],
        },
        {
            "id": "R-2204",
            "agent": "ralph",
            "project_id": "ceo-console",
            "title": "Validation sweep",
            "outcome": "validation",
            "summary": "Validated the approval queue and flagged one routing mismatch for follow-up.",
            "timestamp": (now - timedelta(minutes=32)).replace(microsecond=0).isoformat(),
            "artifacts": ["company/projects/ceo-console/qa/validation-sweep.md"],
        },
        {
            "id": "R-2205",
            "agent": "charlie",
            "project_id": "atlas-core",
            "title": "GitHub push hardening",
            "outcome": "blocked",
            "summary": "Workflow ready except for one deploy secret still pending rotation.",
            "timestamp": (now - timedelta(minutes=41)).replace(microsecond=0).isoformat(),
            "artifacts": ["company/projects/atlas-core/docs/github-workflow.md"],
        },
    ]


def initial_events(now: datetime) -> List[Dict[str, Any]]:
    return [
        {
            "id": "E-2201",
            "timestamp": (now - timedelta(minutes=44)).replace(microsecond=0).isoformat(),
            "kind": "validation",
            "title": "Ralph moved Approval queue and validation rail into Validation",
            "actor": "ralph",
            "details": "Checklist nearly complete; CEO sign-off still pending.",
        },
        {
            "id": "E-2202",
            "timestamp": (now - timedelta(minutes=29)).replace(microsecond=0).isoformat(),
            "kind": "blocked",
            "title": "Charlie reported a blocker on GitHub push workflow hardening",
            "actor": "charlie",
            "details": "Legacy deploy secret missing from the access window.",
        },
        {
            "id": "E-2203",
            "timestamp": (now - timedelta(minutes=17)).replace(microsecond=0).isoformat(),
            "kind": "briefing",
            "title": "Violet started the 8AM AI market briefing",
            "actor": "violet",
            "details": "Signals arriving from Scout, release streams, and selected sources.",
        },
    ]


def initial_conversations(now: datetime) -> List[Dict[str, Any]]:
    return [
        {
            "id": "TH-CEO-ORION",
            "title": "CEO <> Orion",
            "mode": "ceo-chief",
            "project_id": "ceo-console",
            "participants": ["ceo", "orion"],
            "official_channel_source": "browser",
            "official_channel_label": "OpenClaw browser chat",
            "official_channel_url": official_channel_url("browser", "chat:ceo:orion"),
            "session_key": "chat:ceo:orion",
            "transcript_path": "~/.openclaw/sessions/chat-ceo-orion.jsonl",
            "messages": [
                {
                    "id": "M-001",
                    "timestamp": (now - timedelta(minutes=54)).replace(microsecond=0).isoformat(),
                    "sender": "ceo",
                    "text": "Prioritize the weekly operating plan, office polish, and GitHub workflow reliability. I only want blockers and approvals surfaced.",
                    "kind": "message",
                    "category": "directive",
                    "source": "browser",
                    "session_key": "chat:ceo:orion",
                    "transcript_path": "~/.openclaw/sessions/chat-ceo-orion.jsonl",
                    "transcript_url": official_channel_url("browser", "chat:ceo:orion"),
                },
                {
                    "id": "M-002",
                    "timestamp": (now - timedelta(minutes=52)).replace(microsecond=0).isoformat(),
                    "sender": "orion",
                    "text": "Acknowledged. I’ll route by specialist, keep the CEO queue exception-only, and track the blocker on the deploy secret.",
                    "kind": "ack",
                    "category": "ack",
                    "source": "browser",
                    "session_key": "chat:ceo:orion",
                    "transcript_path": "~/.openclaw/sessions/chat-ceo-orion.jsonl",
                    "transcript_url": official_channel_url("browser", "chat:ceo:orion"),
                },
            ],
        },
        {
            "id": "TH-ORION-CODEX",
            "title": "Orion <> Codex",
            "mode": "chief-specialist",
            "project_id": "ceo-console",
            "participants": ["orion", "codex"],
            "summary_only": True,
            "official_channel_source": "internal_session",
            "official_channel_label": "OpenClaw internal session",
            "official_channel_url": official_channel_url("internal_session", "session:orion:codex"),
            "session_key": "session:orion:codex",
            "transcript_path": "~/.openclaw/sessions/session-orion-codex.jsonl",
            "messages": [
                {
                    "id": "M-003",
                    "timestamp": (now - timedelta(minutes=46)).replace(microsecond=0).isoformat(),
                    "sender": "orion",
                    "text": "Take the filters and conversation rail. Keep updates on the board; only ping me if the data model forces a broader refactor.",
                    "kind": "message",
                    "category": "directive",
                    "source": "internal_session",
                    "related_task_id": "T-203",
                    "session_key": "session:orion:codex",
                    "transcript_path": "~/.openclaw/sessions/session-orion-codex.jsonl",
                    "transcript_url": official_channel_url("internal_session", "session:orion:codex"),
                },
                {
                    "id": "M-004",
                    "timestamp": (now - timedelta(minutes=44)).replace(microsecond=0).isoformat(),
                    "sender": "codex",
                    "text": "Understood. I’ll work in the CEO Console repo, branch per task, and hand validation to Ralph.",
                    "kind": "ack",
                    "category": "ack",
                    "source": "internal_session",
                    "related_task_id": "T-203",
                    "session_key": "session:orion:codex",
                    "transcript_path": "~/.openclaw/sessions/session-orion-codex.jsonl",
                    "transcript_url": official_channel_url("internal_session", "session:orion:codex"),
                },
                {
                    "id": "M-004A",
                    "timestamp": (now - timedelta(minutes=42)).replace(microsecond=0).isoformat(),
                    "sender": "codex",
                    "text": "Raw subagent thread: I may split the rail into source badges, directive categories, and transcript references if the state shape stays stable.",
                    "kind": "message",
                    "category": "discussion",
                    "source": "internal_session",
                    "hidden_by_default": True,
                    "related_task_id": "T-203",
                    "session_key": "session:orion:codex",
                    "transcript_path": "~/.openclaw/sessions/session-orion-codex.jsonl",
                    "transcript_url": official_channel_url("internal_session", "session:orion:codex"),
                },
                {
                    "id": "M-004B",
                    "timestamp": (now - timedelta(minutes=41)).replace(microsecond=0).isoformat(),
                    "sender": "codex",
                    "text": "Summary for ClawTasker: directive accepted, board remains the source of work, and transcript references will point back to the official OpenClaw session.",
                    "kind": "status",
                    "category": "summary",
                    "source": "internal_session",
                    "related_task_id": "T-203",
                    "session_key": "session:orion:codex",
                    "run_id": "run-203",
                    "transcript_path": "~/.openclaw/sessions/session-orion-codex.jsonl",
                    "transcript_url": official_channel_url("internal_session", "session:orion:codex"),
                },
            ],
        },
        {
            "id": "TH-ORION-VIOLET",
            "title": "Orion <> Violet",
            "mode": "chief-specialist",
            "project_id": "market-radar",
            "participants": ["orion", "violet"],
            "summary_only": True,
            "official_channel_source": "telegram",
            "official_channel_label": "Telegram",
            "official_channel_url": official_channel_url("telegram", "tg:market-radar:brief"),
            "session_key": "tg:market-radar:brief",
            "transcript_path": "~/.openclaw/sessions/tg-market-radar-brief.jsonl",
            "messages": [
                {
                    "id": "M-005",
                    "timestamp": (now - timedelta(minutes=39)).replace(microsecond=0).isoformat(),
                    "sender": "orion",
                    "text": "Keep the 8AM brief concise: finished, next, blockers, and signal links only.",
                    "kind": "message",
                    "category": "directive",
                    "source": "telegram",
                    "related_task_id": "T-206",
                    "session_key": "tg:market-radar:brief",
                    "transcript_path": "~/.openclaw/sessions/tg-market-radar-brief.jsonl",
                    "transcript_url": official_channel_url("telegram", "tg:market-radar:brief"),
                },
                {
                    "id": "M-006",
                    "timestamp": (now - timedelta(minutes=35)).replace(microsecond=0).isoformat(),
                    "sender": "violet",
                    "text": "Summary: Scout finished the source sweep, blockers are clear, and the channel-ready note is queued for Echo.",
                    "kind": "status",
                    "category": "summary",
                    "source": "telegram",
                    "related_task_id": "T-206",
                    "session_key": "tg:market-radar:brief",
                    "run_id": "run-206",
                    "transcript_path": "~/.openclaw/sessions/tg-market-radar-brief.jsonl",
                    "transcript_url": official_channel_url("telegram", "tg:market-radar:brief"),
                },
            ],
        },
        {
            "id": "TH-CHARLIE-SHIELD",
            "title": "Charlie <> Shield",
            "mode": "manager-specialist",
            "project_id": "atlas-core",
            "participants": ["charlie", "shield"],
            "summary_only": True,
            "official_channel_source": "internal_session",
            "official_channel_label": "OpenClaw internal session",
            "official_channel_url": official_channel_url("internal_session", "session:charlie:shield"),
            "session_key": "session:charlie:shield",
            "transcript_path": "~/.openclaw/sessions/session-charlie-shield.jsonl",
            "messages": [
                {
                    "id": "M-007",
                    "timestamp": (now - timedelta(minutes=28)).replace(microsecond=0).isoformat(),
                    "sender": "charlie",
                    "text": "Confirm whether the missing deploy secret changes the release path or only the hardened push hook.",
                    "kind": "message",
                    "category": "directive",
                    "source": "internal_session",
                    "related_task_id": "T-210",
                    "session_key": "session:charlie:shield",
                    "transcript_path": "~/.openclaw/sessions/session-charlie-shield.jsonl",
                    "transcript_url": official_channel_url("internal_session", "session:charlie:shield"),
                },
                {
                    "id": "M-008",
                    "timestamp": (now - timedelta(minutes=24)).replace(microsecond=0).isoformat(),
                    "sender": "shield",
                    "text": "Summary: blocker confirmed, no data exposure, release can proceed after secret rotation and webhook policy review.",
                    "kind": "status",
                    "category": "summary",
                    "source": "internal_session",
                    "related_task_id": "T-210",
                    "session_key": "session:charlie:shield",
                    "run_id": "run-210",
                    "transcript_path": "~/.openclaw/sessions/session-charlie-shield.jsonl",
                    "transcript_url": official_channel_url("internal_session", "session:charlie:shield"),
                },
            ],
        },
        {
            "id": "TH-CEO-QUILL",
            "title": "CEO <> Quill",
            "mode": "direct",
            "project_id": "ceo-console",
            "participants": ["ceo", "quill"],
            "official_channel_source": "discord",
            "official_channel_label": "Discord",
            "official_channel_url": official_channel_url("discord", "discord:release-room"),
            "session_key": "discord:release-room",
            "transcript_path": "~/.openclaw/sessions/discord-release-room.jsonl",
            "messages": [
                {
                    "id": "M-009",
                    "timestamp": (now - timedelta(minutes=18)).replace(microsecond=0).isoformat(),
                    "sender": "ceo",
                    "text": "Before we publish, keep the README concise and link the guide in the release candidate notes.",
                    "kind": "message",
                    "category": "discussion",
                    "source": "discord",
                    "session_key": "discord:release-room",
                    "transcript_path": "~/.openclaw/sessions/discord-release-room.jsonl",
                    "transcript_url": official_channel_url("discord", "discord:release-room"),
                },
                {
                    "id": "M-010",
                    "timestamp": (now - timedelta(minutes=16)).replace(microsecond=0).isoformat(),
                    "sender": "quill",
                    "text": "Done. I’ll treat the public note as discussion only; directives still become tasks so the board stays auditable.",
                    "kind": "status",
                    "category": "summary",
                    "source": "discord",
                    "session_key": "discord:release-room",
                    "transcript_path": "~/.openclaw/sessions/discord-release-room.jsonl",
                    "transcript_url": official_channel_url("discord", "discord:release-room"),
                },
            ],
        },
    ]



def build_access_matrix(projects: List[Dict[str, Any]], agents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    matrix: List[Dict[str, Any]] = []
    write_capable = {"orion", "codex", "violet", "charlie", "ralph", "quill", "pixel", "echo", "scout", "shield"}
    for project in projects:
        row = {
            "project_id": project["id"],
            "project_name": project["name"],
            "repo": project["repo"],
            "workspace_root": project["workspace_root"],
            "cells": [],
        }
        allowed = set(project.get("allowed_agents", []))
        for agent in agents:
            enrich_agent_record(agent)
            access = "rw" if agent["id"] in allowed else "none"
            if access == "none" and normalize_text(agent.get("project_id"), 64) == project["id"]:
                access = "ro"
            if access == "rw" and agent["id"] not in write_capable and agent_specialist(agent) in {"hr", "procurement", "media"}:
                access = "ro"
            row["cells"].append({"agent": agent["id"], "access": access, "department": agent.get("department")})
        row["cells"].insert(0, {"agent": "ceo", "access": "rw", "department": "Leadership"})
        matrix.append(row)
    return matrix


def default_state() -> Dict[str, Any]:
    now = utc_now()
    agents = [enrich_agent_record(agent) for agent in agent_catalog(now)]
    tasks = ordered_tasks(task_catalog())
    missions = mission_catalog()
    projects = project_catalog()
    company = {
        "name": "ClawTasker CEO Console",
        "tagline": "A human-first control room for OpenClaw agent companies, with a chief agent, specialist teams, shared project repos, and a deterministic dashboard that keeps the CEO in command.",
        "ceo": {
            "id": "ceo",
            "name": "You",
            "role": "CEO / Human operator",
            "emoji": "👩‍💼",
            "focus": ["priorities", "approvals", "budget", "exceptions", "team shape"],
        },
    }

    state = {
        "version": APP_VERSION,
        "created_at": iso_now(),
        "company": company,
        "openclaw_integration": {
            "latest_stable": OPENCLAW_LATEST["npm_version"],
            "release_title": OPENCLAW_LATEST["release_title"],
            "github_tag": OPENCLAW_LATEST["github_tag"],
            "released_at": OPENCLAW_LATEST["released_at"],
            "node_recommended": OPENCLAW_LATEST["node_recommended"],
            "node_compatible": OPENCLAW_LATEST["node_compatible"],
            "control_ui_url": OPENCLAW_LATEST["control_ui_url"],
            "install_command": OPENCLAW_LATEST["install_command"],
            "hooks_contract": {
                "defaultSessionKey": "hook:clawtasker",
                "allowRequestSessionKey": False,
                "allowedSessionKeyPrefixes": ["hook:"],
                "allowedAgentIds": [agent["id"] for agent in agents],
            },
            "team_publish": {
                "endpoint": "http://127.0.0.1:3000/api/openclaw/publish",
                "transport": "local bearer-token JSON publish",
                "supported_events": ["heartbeat", "task_update", "validation", "conversation_note", "run", "roster_sync", "agent_register", "mission_plan"],
            },
            "official_channels": [
                {"id": "browser", "label": "OpenClaw browser chat", "preferred_for": "CEO/chief operator chat"},
                {"id": "telegram", "label": "Telegram", "preferred_for": "field notifications and human replies"},
                {"id": "discord", "label": "Discord", "preferred_for": "team discussion"},
                {"id": "slack", "label": "Slack", "preferred_for": "company workspace chat"},
                {"id": "internal_session", "label": "OpenClaw internal session", "preferred_for": "subagent coordination"},
            ],
            "team_model": [
                "Chief agent coordinates specialists with OpenClaw session tools and agent-to-agent routing.",
                "Specialists publish status into ClawTasker through the local publish API, helper script, or agent registration helper.",
                "Cron jobs can target specific OpenClaw agents using agentId.",
                "Managers coordinate only their own teams while the chief agent keeps the cross-team exception queue.",
                "New agents can self-register name, role, and skills so the company chart stays visible to the human CEO.",
            ],
            "last_publish": None,
            "recent_publish_signatures": [],
        },
        "sync_contract": {
            "chief_agent": "orion",
            "principles": [
                "The chief agent plans, routes, and escalates by exception instead of micromanaging every worker step.",
                "Specialists update tasks, heartbeats, validation notes, and status information directly in ClawTasker.",
                "The office is a derived visualization. It mirrors the task system with the supplied Pocket Office Quest v9 character family and generated day/night office layouts; it does not replace the task system.",
                "ClawTasker is a companion surface for the human CEO and OpenClaw agents; OpenClaw keeps multi-agent routing, sessions, and workspaces.",
                "The CEO queue receives only blockers, approvals, validation, and priority changes.",
            ],
            "heartbeat_seconds": 30,
            "escalate_on": ["blocked", "validation", "overdue", "routing_mismatch", "error"],
            "shared_workspace_model": "project-level shared repos, branch-per-task, PR validation before merge",
        },
        "platform_contract": {
            "role": "Flexible collaboration hub for human user and AI specialist agents — any project type, any workflow.",
            "philosophy": [
                "Use what helps, skip what doesn't. No methodology is enforced.",
                "AI agents work at their own pace — the board, missions, and calendar are optional coordination aids, not constraints.",
                "The human CEO sees what they need; AI agents post only what is relevant.",
                "Projects may be software, business, coaching, manual, or anything else — the platform adapts.",
                "Sprints/iterations are optional focus periods, not mandatory ceremonies.",
                "Avoid process overhead: if a feature creates friction, don't use it.",
            ],
            "visualization_only": True,
            "api_for_agents": [
                "agent self-registration for company chart identity",
                "heartbeat status and derived status",
                "task status, story points, sprint assignment, and dependency links",
                "conversation notes and coordination context",
                "mission briefs, staffing plans, and risk summaries",
                "channel and transcript references for audit-safe linking",
                "sprint creation and update",
                "notification posting",
                "project type and specialist configuration",
            ],
            "non_goals": [
                "replace OpenClaw multi-agent routing",
                "replace OpenClaw session management",
                "become a required dependency for agent work to continue",
                "be the primary place where subagents discuss work in full detail",
                "enforce scrum, kanban, or any specific methodology",
                "slow down AI agents with mandatory ceremonies",
            ],
            "restart_contract": [
                "restart the UI server without changing agent workspaces",
                "reload the most recent good local snapshot",
                "allow agents to continue work and republish state later",
            ],
            "conversation_boundary": [
                "Use official OpenClaw channels for runtime chat and agent communication.",
                "Use ClawTasker as a thin operator conversation rail with directive badges, source badges, and transcript references.",
                "Show subagent summaries by default; keep full internal discussion in OpenClaw sessions.",
            ],
        },
        "projects": projects,
        "agents": agents,
        "tasks": tasks,
        "missions": missions,
        "calendar": {
            "week_of": first_day_of_week(now).date().isoformat(),
            "recurring_jobs": recurring_jobs(),
            "blocks": calendar_blocks(agents, tasks),
        },
        "recent_runs": recent_runs(now),
        "events": initial_events(now),
        "directives": [],
        "sprints": [],
        "notifications": [],
        "conversations": initial_conversations(now),
        "asset_library": {
            "name": "Pocket Office Quest - v9 Character Pack",
            "office_background": "office_map_day_32bit.png",
            "office_background_day": "office_map_day_32bit.png",
            "office_background_night": "office_map_night_32bit.png",
            "office_modes": ["day", "night"],
        "ui_theme_default": f"{DEFAULT_UI_SETTINGS['theme_preset']} / {DEFAULT_UI_SETTINGS['theme_mode']}",
        "office_object_bounds": len(OFFICE_OBJECT_BOUNDS),
            "vendor": "Pocket Office Quest v9",
            "engine_source": "Pocket Office Quest v9 character assets + ClawTasker deterministic office adapter",
            "office_layout_source": "Generated day/night office layouts matched to the Pocket Office Quest v9 roster pack",
            "avatar_mapping": {
                "ceo":     "aria",
                "orion":   "kai",
                "codex":   "rex",
                "violet":  "quinn",
                "charlie": "rowan",
                "ralph":   "marco",
                "shield":  "finn",
                "pixel":   "yuki",
                "echo":    "sasha",
                "quill":   "devon",
                "scout":   "zara",
                "iris":    "mina",
                "ledger":  "mina",
                "mercury": "zara",
                "_note": "v9 has 12 characters for 14 agents. ledger+iris share mina (both back-office people roles). scout+mercury share zara (both analyst/research roles). All other agents have a unique character."
            }
        },
        "ui_defaults": copy.deepcopy(DEFAULT_UI_SETTINGS),
        "office_layout": {
            "modes": ["day", "night"],
            "active_default": DEFAULT_UI_SETTINGS["office_scene"],
            "collision_policy": "unique seat anchors only",
            "movement_policy": {
                "cross_zone_behavior": "snap",
                "same_zone_max_animated_distance": 180,
                "respect_protected_bounds": True,
                "object_bounds_count": len(OFFICE_OBJECT_BOUNDS),
            },
            "object_bounds": copy.deepcopy(OFFICE_OBJECT_BOUNDS),
            "areas": [
                {"id": "ceo_strip", "label": "CEO strip", "purpose": "Human approvals and oversight"},
                {"id": "chief_desk", "label": "Chief desk", "purpose": "Chief agent exception-only coordination"},
                {"id": "code_pod", "label": "Engineering desks", "purpose": "Focused coding work"},
                {"id": "research_pod", "label": "Research desks", "purpose": "Research, media, and intelligence"},
                {"id": "ops_pod", "label": "Operations desks", "purpose": "Operations, security, and procurement"},
                {"id": "qa_pod", "label": "Validation desks", "purpose": "QA review and acceptance"},
                {"id": "studio_pod", "label": "Studio desks", "purpose": "Docs, design, HR, and communications"},
                {"id": "scrum_table", "label": "Sync table", "purpose": "Standups, blockers, and huddles"},
                {"id": "review_rail", "label": "Review rail", "purpose": "Owner and validator review pairing"},
                {"id": "board_wall", "label": "Agile board wall", "purpose": "Shared task visibility"},
                {"id": "lounge", "label": "Lounge", "purpose": "Idle and overflow space"}
            ]
        },
        "workspace_blueprint": WORKSPACE_BLUEPRINT,
        "skill_catalog": copy.deepcopy(SPECIALIST_CATALOG),
        "org_templates": org_templates(),
        "access_matrix": build_access_matrix(projects, agents),
        "github_flow": [
            "One repo per product or shared project workspace.",
            "Branch per task: agent/<agent>/<task-id>-<slug>.",
            "Link issues and PRs back to ClawTasker task IDs.",
            "Validate before merge; keep the chief agent exception-only.",
            "Use git worktree if two specialists need parallel branches in the same repo.",
        ],
    }
    return refresh_state_metadata(state)


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def save_state(state: Dict[str, Any]) -> None:
    ensure_dirs()
    payload = json.dumps(state, indent=2, ensure_ascii=False)
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(payload, encoding="utf-8")
    tmp.replace(STATE_FILE)
    if STATE_BACKUP.exists():
        shutil.copy2(STATE_BACKUP, STATE_BACKUP_PREV)
    STATE_BACKUP.write_text(payload, encoding="utf-8")
    RUNTIME_META["last_save_at"] = iso_now()
    RUNTIME_META["backup_chain"] = int(STATE_BACKUP.exists()) + int(STATE_BACKUP_PREV.exists())
    publish_stream_event("state_saved", "State snapshot saved", meta={"backup_chain": RUNTIME_META["backup_chain"], "version": APP_VERSION})


def _load_state_file(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    state = json.loads(path.read_text(encoding="utf-8"))
    required_keys = {"version", "projects", "agents", "tasks", "conversations", "calendar"}
    if not required_keys.issubset(state.keys()):
        raise ValueError(f"missing required keys in {path.name}")
    return state


def refresh_demo_state(state: Dict[str, Any]) -> bool:
    agents = state.get("agents", [])
    if not agents:
        return False
    now = utc_now()
    stale = 0
    for agent in agents:
        try:
            age = (now - parse_iso(agent.get("last_heartbeat", ""))).total_seconds()
        except Exception:
            age = HEARTBEAT_STALE_SECONDS + 1
        if age > HEARTBEAT_STALE_SECONDS:
            stale += 1
    if stale < max(1, len(agents) // 2):
        return False

    # Refresh demo timestamps so the packaged sample opens in a lively state
    offsets = [12, 16, 25, 31, 48, 18, 63, 22, 14, 51]
    for index, agent in enumerate(agents):
        offset = offsets[index % len(offsets)]
        agent["last_heartbeat"] = (now - timedelta(seconds=offset)).replace(microsecond=0).isoformat()
    for index, task in enumerate(state.get("tasks", [])):
        task["updated_at"] = (now - timedelta(minutes=min(index * 3, 75))).replace(microsecond=0).isoformat()
    state["created_at"] = now.replace(microsecond=0).isoformat()
    state["version"] = APP_VERSION
    return True


def load_state() -> Dict[str, Any]:
    ensure_dirs()
    defaults = default_state()
    errors: List[str] = []
    for label, candidate in (("primary", STATE_FILE), ("backup", STATE_BACKUP), ("backup_prev", STATE_BACKUP_PREV)):
        if not candidate.exists():
            continue
        try:
            state = _load_state_file(candidate)
            if state is None:
                continue
            changed = False
            for key in ["asset_library", "workspace", "sync_contract", "company", "platform_contract", "openclaw_integration", "skill_catalog", "org_templates", "office_layout"]:
                if key not in state and key in defaults:
                    state[key] = copy.deepcopy(defaults[key])
                    changed = True
            for key in ["asset_library", "office_layout"]:
                if isinstance(state.get(key), dict) and isinstance(defaults.get(key), dict):
                    for subkey, value in defaults[key].items():
                        if subkey not in state[key]:
                            state[key][subkey] = copy.deepcopy(value)
                            changed = True
            if refresh_demo_state(state):
                changed = True
            if label != "primary":
                changed = True
            RUNTIME_META["state_source"] = label
            RUNTIME_META["last_recovered_from"] = label
            RUNTIME_META["last_load_at"] = iso_now()
            RUNTIME_META["backup_chain"] = int(STATE_BACKUP.exists()) + int(STATE_BACKUP_PREV.exists())
            RUNTIME_META["load_errors"] = errors[-6:]
            state = refresh_state_metadata(state)
            if changed:
                save_state(state)
            return state
        except Exception as exc:
            errors.append(f"{label}:{exc}")
            continue
    state = refresh_state_metadata(defaults)
    RUNTIME_META["state_source"] = "default"
    RUNTIME_META["last_recovered_from"] = "default"
    RUNTIME_META["last_load_at"] = iso_now()
    RUNTIME_META["backup_chain"] = int(STATE_BACKUP.exists()) + int(STATE_BACKUP_PREV.exists())
    RUNTIME_META["load_errors"] = errors[-6:]
    save_state(state)
    return state


def append_event_log(event: Dict[str, Any]) -> None:
    ensure_dirs()
    with AUDIT_LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")


def relative_time_label(ts: str) -> str:
    try:
        dt = parse_iso(ts)
    except Exception:
        return "unknown"
    delta = utc_now() - dt
    seconds = int(delta.total_seconds())
    if seconds < 60:
        return f"{seconds}s ago"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h ago"
    return f"{hours // 24}d ago"


def normalized_agent_state(agent: Dict[str, Any]) -> str:
    state = agent.get("status", "idle")
    last = agent.get("last_heartbeat")
    if not last:
        return "offline"
    try:
        age = (utc_now() - parse_iso(last)).total_seconds()
    except Exception:
        return "offline"
    if age > HEARTBEAT_STALE_SECONDS:
        return "offline"
    return state


def current_task_for(agent: Dict[str, Any], tasks: Iterable[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    current_id = agent.get("current_task_id")
    return next((task for task in tasks if task["id"] == current_id), None)


def compute_target_zone(agent: Dict[str, Any], tasks: Iterable[Dict[str, Any]]) -> str:
    state = normalized_agent_state(agent)
    task = current_task_for(agent, tasks)
    if agent.get("id") == "orion" and state == "working":
        return "chief_desk"
    if state in {"blocked", "error"} or agent.get("blockers"):
        return "scrum_table"
    if state in {"validation", "validating"} or (task and task.get("status") == "validation"):
        return "review_rail"
    if agent.get("speaking"):
        return "scrum_table"
    if state == "working":
        specialist = agent.get("home_specialist") or (agent.get("specialists") or ["planning"])[0]
        return HOME_ZONE_BY_SPECIALIST.get(specialist, "studio_pod")
    if state == "offline":
        return HOME_ZONE_BY_SPECIALIST.get(agent.get("home_specialist", "planning"), "lounge")
    return "lounge"


def normalize_mission_status(value: str) -> str:
    value = normalize_text(value, 24)
    return value if value in MISSION_STATUSES else "draft"


def normalize_mission_dependency(items: Any) -> List[Dict[str, Any]]:
    result: List[Dict[str, Any]] = []
    for index, item in enumerate(items or []):
        if isinstance(item, str):
            title = normalize_text(item, 180)
            if title:
                result.append({"id": f"DEP-{index}", "title": title, "status": "pending", "owner": "", "detail": ""})
            continue
        if not isinstance(item, dict):
            continue
        title = normalize_text(item.get("title") or item.get("name") or item.get("detail"), 180)
        if not title:
            continue
        result.append({
            "id": normalize_text(item.get("id") or f"DEP-{index}", 32),
            "title": title,
            "status": normalize_text(item.get("status") or "pending", 24) or "pending",
            "owner": normalize_text(item.get("owner"), 32),
            "detail": normalize_text(item.get("detail") or item.get("summary"), 240),
        })
    return result[:12]


def normalize_mission_risks(items: Any) -> List[Dict[str, Any]]:
    result: List[Dict[str, Any]] = []
    for index, item in enumerate(items or []):
        if isinstance(item, str):
            title = normalize_text(item, 180)
            if title:
                result.append({"id": f"RISK-{index}", "title": title, "severity": "medium", "status": "open", "owner": "", "mitigation": ""})
            continue
        if not isinstance(item, dict):
            continue
        title = normalize_text(item.get("title") or item.get("name") or item.get("detail"), 180)
        if not title:
            continue
        severity = normalize_text(item.get("severity") or "medium", 24) or "medium"
        if severity not in MISSION_SEVERITIES:
            severity = "medium"
        result.append({
            "id": normalize_text(item.get("id") or f"RISK-{index}", 32),
            "title": title,
            "severity": severity,
            "status": normalize_text(item.get("status") or "open", 24) or "open",
            "owner": normalize_text(item.get("owner"), 32),
            "mitigation": normalize_text(item.get("mitigation") or item.get("detail"), 240),
        })
    return result[:12]


def normalize_mission_milestones(items: Any) -> List[Dict[str, Any]]:
    result: List[Dict[str, Any]] = []
    for index, item in enumerate(items or []):
        if isinstance(item, str):
            title = normalize_text(item, 180)
            if title:
                result.append({"id": f"MS-{index}", "title": title, "status": "planned", "due_date": ""})
            continue
        if not isinstance(item, dict):
            continue
        title = normalize_text(item.get("title") or item.get("name") or item.get("detail"), 180)
        if not title:
            continue
        result.append({
            "id": normalize_text(item.get("id") or f"MS-{index}", 32),
            "title": title,
            "status": normalize_text(item.get("status") or "planned", 24) or "planned",
            "due_date": normalize_text(item.get("due_date") or item.get("dueDate"), 24),
        })
    return result[:12]


def normalize_mission_record(mission: Dict[str, Any]) -> Dict[str, Any]:
    record = copy.deepcopy(mission or {})
    title = normalize_text(record.get("title"), 160)
    objective = normalize_text(record.get("objective"), 320)
    record["title"] = title
    record["objective"] = objective
    record["id"] = normalize_text(record.get("id"), 32) or slugify_identifier(title or objective or "mission", 32)
    record["status"] = normalize_mission_status(record.get("status") or "draft")
    priority = normalize_text(record.get("priority") or "P2", 8)
    record["priority"] = priority if priority in TASK_PRIORITIES else "P2"
    horizon = normalize_text(record.get("horizon") or "This Week", 24)
    record["horizon"] = horizon if horizon in HORIZONS else "This Week"
    record["owner"] = normalize_text(record.get("owner"), 32) or "orion"
    record["project_ids"] = normalize_list(record.get("project_ids") or record.get("projects"), 6, 32)
    record["task_ids"] = normalize_list(record.get("task_ids") or record.get("tasks"), 16, 32)
    record["required_specialists"] = normalize_list(record.get("required_specialists") or record.get("requiredSkills") or record.get("required_skills"), 12, 32)
    record["assigned_agents"] = normalize_list(record.get("assigned_agents") or record.get("assignedAgents") or record.get("agents"), 16, 32)
    record["summary"] = normalize_text(record.get("summary"), 280)
    record["next_actions"] = normalize_list(record.get("next_actions") or record.get("nextActions"), 8, 180)
    record["success_criteria"] = normalize_list(record.get("success_criteria") or record.get("successCriteria"), 8, 180)
    record["dependencies"] = normalize_mission_dependency(record.get("dependencies"))
    record["risks"] = normalize_mission_risks(record.get("risks"))
    record["milestones"] = normalize_mission_milestones(record.get("milestones"))
    record["source"] = normalize_text(record.get("source") or "mission-control", 40) or "mission-control"
    record["created_at"] = normalize_text(record.get("created_at"), 40) or iso_now()
    record["updated_at"] = normalize_text(record.get("updated_at"), 40) or iso_now()
    return record


def agent_matches_specialist(agent: Dict[str, Any], specialist: str) -> bool:
    specialist = normalize_text(specialist, 32)
    if not specialist:
        return False
    values = {normalize_text(agent.get("home_specialist"), 32), normalize_text(agent_specialist(agent), 32)}
    values.update(normalize_list(agent.get("specialists"), 12, 32))
    values.update(normalize_list(agent.get("core_skills"), 12, 32))
    values.update(normalize_list(agent.get("skills"), 12, 32))
    return specialist in values


def materialize_mission(mission: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
    record = normalize_mission_record(mission)
    roster = {agent["id"]: enrich_agent_record(copy.deepcopy(agent)) for agent in state.get("agents", [])}
    task_lookup = {task["id"]: task for task in state.get("tasks", [])}
    project_lookup = {project["id"]: project for project in state.get("projects", [])}

    related_tasks = [copy.deepcopy(task_lookup[task_id]) for task_id in record.get("task_ids", []) if task_id in task_lookup]
    if not related_tasks and record.get("id"):
        related_tasks = [copy.deepcopy(task) for task in state.get("tasks", []) if normalize_text(task.get("mission_id"), 32) == record["id"]]
    if not record.get("project_ids") and related_tasks:
        record["project_ids"] = normalize_list([task.get("project_id") for task in related_tasks if task.get("project_id")], 6, 32)
    if not record.get("required_specialists") and related_tasks:
        record["required_specialists"] = normalize_list([task.get("specialist") for task in related_tasks if task.get("specialist")], 12, 32)
    if not record.get("assigned_agents") and related_tasks:
        record["assigned_agents"] = normalize_list([task.get("owner") for task in related_tasks if task.get("owner")], 16, 32)

    assigned_ids = list(dict.fromkeys(record.get("assigned_agents") + [task.get("owner") for task in related_tasks if task.get("owner")]))
    assigned_agents = [roster[agent_id] for agent_id in assigned_ids if agent_id in roster]
    required_specialists = record.get("required_specialists") or []
    covered_specialists: List[str] = []
    gaps: List[str] = []
    recommendations: List[Dict[str, Any]] = []
    for specialist in required_specialists:
        matches = [agent for agent in assigned_agents if agent_matches_specialist(agent, specialist)]
        if matches:
            covered_specialists.append(specialist)
        else:
            gaps.append(specialist)
            candidates = routing_candidates_for(state, specialist, record.get("project_ids", [""])[0] if len(record.get("project_ids", [])) == 1 else None)
            recommendations.append({
                "specialist": specialist,
                "candidate_ids": candidates[:3],
                "candidate_names": [roster[item].get("name", item) for item in candidates[:3] if item in roster],
            })

    coverage_percent = 100 if not required_specialists else int(round(100 * len(covered_specialists) / max(1, len(required_specialists))))
    open_risks = [risk for risk in record.get("risks", []) if risk.get("status") not in {"mitigated", "closed", "done"}]
    open_risks.sort(key=lambda item: MISSION_SEVERITIES.index(item.get("severity")) if item.get("severity") in MISSION_SEVERITIES else 1, reverse=True)
    blocked_dependencies = [dep for dep in record.get("dependencies", []) if dep.get("status") in {"blocked", "waiting", "pending"}]
    done_tasks = sum(1 for task in related_tasks if task.get("status") == "done")
    progress_from_tasks = int(round(sum(int(task.get("progress") or 0) for task in related_tasks) / max(1, len(related_tasks)))) if related_tasks else 0
    milestone_done = sum(1 for item in record.get("milestones", []) if item.get("status") == "done")
    milestone_total = len(record.get("milestones", []))
    milestone_progress = int(round(100 * milestone_done / max(1, milestone_total))) if milestone_total else 0
    progress_percent = progress_from_tasks or milestone_progress

    record["owner_name"] = roster.get(record.get("owner"), {}).get("name", record.get("owner"))
    record["project_names"] = [project_lookup[item].get("name", item) for item in record.get("project_ids", []) if item in project_lookup]
    record["assigned_agents_detail"] = [org_card_payload(agent) for agent in assigned_agents]
    record["task_summaries"] = [{
        "id": task.get("id"),
        "title": task.get("title"),
        "status": task.get("status"),
        "owner": task.get("owner"),
        "owner_name": roster.get(task.get("owner"), {}).get("name", task.get("owner")),
        "progress": task.get("progress"),
    } for task in related_tasks]
    record["staffing"] = {
        "required_specialists": required_specialists,
        "covered_specialists": covered_specialists,
        "gaps": gaps,
        "missing_specialists": gaps,
        "coverage_percent": coverage_percent,
        "coverage_label": f"{len(covered_specialists)}/{max(1, len(required_specialists))} staffed" if required_specialists else "No specialist requirements",
        "assigned_agents": [agent.get("id") for agent in assigned_agents],
        "recommendations": recommendations,
    }
    record["dependencies_summary"] = {
        "total": len(record.get("dependencies", [])),
        "blocked": len(blocked_dependencies),
        "open": len([dep for dep in record.get("dependencies", []) if dep.get("status") != "done"]),
        "blocked_items": blocked_dependencies[:4],
    }
    record["risk_summary"] = {
        "total": len(record.get("risks", [])),
        "open": len(open_risks),
        "high_or_critical": len([risk for risk in open_risks if risk.get("severity") in {"high", "critical"}]),
        "top_risks": open_risks[:4],
    }
    record["milestone_summary"] = {
        "total": milestone_total,
        "done": milestone_done,
        "progress_percent": milestone_progress,
    }
    record["task_count"] = len(related_tasks)
    record["open_task_count"] = len([task for task in related_tasks if task.get("status") != "done"])
    record["blocked_task_count"] = len([task for task in related_tasks if task.get("blocked")])
    record["validation_task_count"] = len([task for task in related_tasks if task.get("status") == "validation"])
    record["progress_percent"] = progress_percent
    record["health_label"] = "blocked" if blocked_dependencies or any(risk.get("severity") in {"high", "critical"} and risk.get("status") == "open" for risk in open_risks) or gaps else record.get("status")
    if not record.get("summary"):
        record["summary"] = record.get("objective")
    return record


def mission_sort_tuple(mission: Dict[str, Any]) -> Tuple[int, int, int, str]:
    status_rank = MISSION_STATUS_SORT_ORDER.get(mission.get("status"), 99)
    priority_rank = PRIORITY_SORT_ORDER.get(mission.get("priority"), 99)
    horizon_rank = HORIZONS.index(mission.get("horizon")) if mission.get("horizon") in HORIZONS else 99
    return (status_rank, priority_rank, horizon_rank, normalize_text(mission.get("title"), 160))


def mission_control_from_state(state: Dict[str, Any]) -> Dict[str, Any]:
    missions = [materialize_mission(mission, state) for mission in state.get("missions", [])]
    missions.sort(key=mission_sort_tuple)
    focus = next((mission for mission in missions if mission.get("status") in {"active", "blocked", "planned"}), missions[0] if missions else None)
    return {
        "missions": missions,
        "focus_mission": focus,
        "active_count": sum(1 for mission in missions if mission.get("status") == "active"),
        "blocked_count": sum(1 for mission in missions if mission.get("status") == "blocked"),
        "staffing_gap_count": sum(len((mission.get("staffing") or {}).get("gaps", [])) for mission in missions),
        "open_risk_count": sum((mission.get("risk_summary") or {}).get("open", 0) for mission in missions),
        "coverage_percent": (focus or {}).get("staffing", {}).get("coverage_percent", 100) if focus else 100,
        "coverage_label": (focus or {}).get("staffing", {}).get("coverage_label", "No active mission") if focus else "No active mission",
        "dependency_blockers": sum((mission.get("dependencies_summary") or {}).get("blocked", 0) for mission in missions),
    }


def build_attention_queue(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    attention: List[Dict[str, Any]] = []
    roster = {agent["id"]: agent for agent in state["agents"]}
    for task in state["tasks"]:
        owner = roster.get(task.get("owner"))
        overdue = False
        try:
            due_dt = parse_iso(task["due_date"] + "T23:59:59+00:00")
            overdue = task.get("status") not in {"done", "backlog"} and due_dt < utc_now()
        except Exception:
            overdue = False

        if task.get("blocked"):
            attention.append({
                "kind": "blocked",
                "title": task["title"],
                "owner": owner["name"] if owner else task.get("owner", "Unassigned"),
                "detail": "Blocked work routes straight to the chief/CEO queue.",
                "task_id": task["id"],
                "project_id": task["project_id"],
            })
        elif task.get("status") == "validation":
            attention.append({
                "kind": "validation",
                "title": task["title"],
                "owner": owner["name"] if owner else task.get("owner", "Unassigned"),
                "detail": f"Waiting on validation owner {task.get('validation_owner')}",
                "task_id": task["id"],
                "project_id": task["project_id"],
            })
        elif task.get("owner") != recommended_owner_for_task(state, task) and task.get("status") not in {"done", "backlog"}:
            attention.append({
                "kind": "routing_mismatch",
                "title": task["title"],
                "owner": owner["name"] if owner else task.get("owner", "Unassigned"),
                "detail": f"Best fit specialist is {task.get('recommended_owner')}",
                "task_id": task["id"],
                "project_id": task["project_id"],
            })
        elif overdue:
            attention.append({
                "kind": "overdue",
                "title": task["title"],
                "owner": owner["name"] if owner else task.get("owner", "Unassigned"),
                "detail": "Past due and needs reprioritization.",
                "task_id": task["id"],
                "project_id": task["project_id"],
            })

    for mission in mission_control_from_state(state).get("missions", []):
        staffing = mission.get("staffing") or {}
        if mission.get("status") in {"active", "blocked", "planned"} and staffing.get("gaps"):
            attention.append({
                "kind": "staffing_gap",
                "title": mission["title"],
                "owner": mission.get("owner_name") or mission.get("owner"),
                "detail": "Missing specialist coverage: " + ", ".join(human_status(item) for item in staffing.get("gaps", [])[:3]),
                "task_id": mission["id"],
                "project_id": (mission.get("project_ids") or [""])[0],
            })
        top_risk = next((risk for risk in (mission.get("risk_summary") or {}).get("top_risks", []) if risk.get("severity") in {"high", "critical"}), None)
        if top_risk:
            attention.append({
                "kind": "mission_risk",
                "title": mission["title"],
                "owner": mission.get("owner_name") or mission.get("owner"),
                "detail": f"{human_status(top_risk.get('severity'))} risk: {top_risk.get('title')}",
                "task_id": mission["id"],
                "project_id": (mission.get("project_ids") or [""])[0],
            })
        blocked_dep = next(iter((mission.get("dependencies_summary") or {}).get("blocked_items", [])), None)
        if blocked_dep:
            attention.append({
                "kind": "dependency_blocked",
                "title": mission["title"],
                "owner": mission.get("owner_name") or mission.get("owner"),
                "detail": f"Dependency blocked: {blocked_dep.get('title')}",
                "task_id": mission["id"],
                "project_id": (mission.get("project_ids") or [""])[0],
            })
    return attention[:12]


def metrics_from_state(state: Dict[str, Any]) -> Dict[str, Any]:
    total = max(1, len(state["tasks"]))
    done = sum(1 for task in state["tasks"] if task["status"] == "done")
    backlog = sum(1 for task in state["tasks"] if task["status"] == "backlog")
    validation = sum(1 for task in state["tasks"] if task["status"] == "validation")
    blocked = sum(1 for task in state["tasks"] if task.get("blocked"))
    active_agents = sum(1 for agent in state["agents"] if normalized_agent_state(agent) not in {"idle", "offline"})
    offline_agents = sum(1 for agent in state["agents"] if normalized_agent_state(agent) == "offline")
    sync_efficiency = max(60, 97 - blocked * 6 - validation * 3 - offline_agents * 5)
    mission_control = mission_control_from_state(state)
    focus = mission_control.get("focus_mission") or {}
    return {
        "throughput": f"{done}/{total} done",
        "backlog": str(backlog),
        "validation_queue": str(validation),
        "blocked": str(blocked),
        "agent_utilization": f"{active_agents}/{len(state['agents'])} active",
        "sync_efficiency": f"{sync_efficiency}%",
        "mission_coverage": mission_control.get("coverage_label", "No active mission"),
        "mission_focus": focus.get("title", "Shared mission briefs"),
        "chief_mode": "exception-only",
        "workspace_model": "shared project repos + mission briefs",
        "team_scale": f"{len(state['agents'])} rostered / tested {SCALABILITY_TARGET_AGENTS}",
        "task_sort_policy": "blocked -> status -> priority -> horizon -> due",
    }


def recovery_playbook() -> List[str]:
    return [
        "If the UI restarts, OpenClaw agents keep working in their own sessions and workspaces.",
        "On boot, ClawTasker reloads the latest good local snapshot from primary or backup state.",
        "Agents can republish heartbeats, task updates, and conversation notes after recovery.",
        "The dashboard should surface degraded mode instead of blocking agent work.",
    ]


def system_health_from_state(state: Dict[str, Any]) -> Dict[str, Any]:
    roster = state.get("agents", [])
    offline = sum(1 for agent in roster if normalized_agent_state(agent) == "offline")
    active = sum(1 for agent in roster if normalized_agent_state(agent) not in {"idle", "offline"})
    attention = len(build_attention_queue(state))
    latest_event = (state.get("events") or [{}])[0] if state.get("events") else {}
    recent_kind = latest_event.get("kind", "idle")
    roster_sync = ((state.get("openclaw_integration") or {}).get("roster_sync") or {})
    return {
        "role": "visualization-companion",
        "visualization_only": True,
        "state_source": RUNTIME_META.get("state_source", "unknown"),
        "last_recovered_from": RUNTIME_META.get("last_recovered_from", "unknown"),
        "last_load_at": RUNTIME_META.get("last_load_at"),
        "last_save_at": RUNTIME_META.get("last_save_at"),
        "booted_at": RUNTIME_META.get("booted_at"),
        "backup_chain": RUNTIME_META.get("backup_chain", 0),
        "restart_safe": True,
        "agent_api_contract": [
            "agent registration",
            "heartbeats",
            "task updates",
            "validation updates",
            "conversation notes",
            "mission plans",
            "OpenClaw publish envelopes",
        ],
        "openclaw_boundary": "OpenClaw keeps routing, sessions, subagents, and workspaces.",
        "active_agents": active,
        "offline_agents": offline,
        "attention_items": attention,
        "agent_count": len(roster),
        "manager_count": build_org_structure(state).get("manager_count", 0),
        "team_count": build_org_structure(state).get("team_count", 0),
        "active_missions": mission_control_from_state(state).get("active_count", 0),
        "mission_staffing_gaps": mission_control_from_state(state).get("staffing_gap_count", 0),
        "open_mission_risks": mission_control_from_state(state).get("open_risk_count", 0),
        "scalability_target_agents": SCALABILITY_TARGET_AGENTS,
        "office_visual_capacity": OFFICE_VISUAL_CAPACITY,
        "office_modes": ["day", "night"],
        "ui_theme_default": f"{DEFAULT_UI_SETTINGS['theme_preset']} / {DEFAULT_UI_SETTINGS['theme_mode']}",
        "office_object_bounds": len(OFFICE_OBJECT_BOUNDS),
        "roster_last_synced_at": roster_sync.get("last_synced_at"),
        "manager_span_peak": max((lane.get("report_count", 0) for lane in build_org_structure(state).get("manager_lanes", [])), default=0),
        "roster_sync_source": roster_sync.get("source"),
        "recent_event_kind": recent_kind,
        "event_count": len(state.get("events", [])),
        "write_limit_per_minute": WRITE_LIMIT_PER_MINUTE,
        "max_body_kb": MAX_BODY_BYTES // 1024,
        "live_sync_mode": "sse-with-poll-fallback",
        "latest_openclaw_release": OPENCLAW_LATEST["npm_version"],
        "latest_openclaw_tag": OPENCLAW_LATEST["github_tag"],
        "load_errors": list(RUNTIME_META.get("load_errors", [])),
        "recovery_playbook": recovery_playbook(),
        "task_transition_policy": "backlog -> ready -> in_progress -> validation -> done",
        "publish_dedupe_window_seconds": PUBLISH_DEDUPE_WINDOW_SECONDS,
    }


def enrich_conversation_thread(thread: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
    messages = thread.get("messages", [])
    for message in messages:
        message["source"] = normalize_conversation_source(message.get("source") or thread.get("official_channel_source") or ("browser" if "ceo" in thread.get("participants", []) else "internal_session"))
        message["source_label"] = conversation_source_label(message.get("source"))
        message["category"] = normalize_conversation_category(message.get("category") or message.get("kind"))
        message["category_label"] = conversation_category_label(message.get("category"))
        if message.get("session_key") or thread.get("session_key"):
            message["session_key"] = normalize_text(message.get("session_key") or thread.get("session_key"), 160)
        if message.get("transcript_path") or thread.get("transcript_path"):
            message["transcript_path"] = normalize_text(message.get("transcript_path") or thread.get("transcript_path"), 260)
        if message.get("transcript_url"):
            message["transcript_url"] = normalize_text(message.get("transcript_url"), 260)
        elif message.get("session_key"):
            message["transcript_url"] = official_channel_url(message.get("source"), message.get("session_key"), message.get("channel_url") or message.get("transcript_url") or thread.get("official_channel_url") or "")
        if message.get("run_id"):
            message["run_id"] = normalize_text(message.get("run_id"), 120)
    thread["summary_only"] = thread_summary_only(thread)
    thread["hidden_message_count"] = conversation_hidden_message_count(thread)
    thread["visible_message_count"] = len(conversation_messages_visible_by_default(thread))
    context = latest_conversation_context_message(thread)
    thread["official_channel_source"] = normalize_conversation_source(thread.get("official_channel_source") or context.get("source") or ("browser" if "ceo" in thread.get("participants", []) else "internal_session"))
    thread["official_channel_label"] = normalize_text(thread.get("official_channel_label") or context.get("channel_label") or conversation_source_label(thread.get("official_channel_source")), 64)
    thread["official_channel_url"] = official_channel_url(thread.get("official_channel_source"), context.get("session_key") or thread.get("session_key") or "", thread.get("official_channel_url") or context.get("channel_url") or context.get("transcript_url") or "")
    thread["transcript_ref"] = transcript_reference_from_message(context)
    return thread


def conversation_preview(thread: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
    messages = conversation_messages_visible_by_default(thread) or thread.get("messages", [])
    last = messages[-1] if messages else {"timestamp": iso_now(), "text": "No messages yet.", "sender": thread["participants"][0], "source": thread.get("official_channel_source", "browser"), "category": "discussion"}
    participants = []
    for part in thread.get("participants", []):
        if part == "ceo":
            participants.append({"id": "ceo", "name": state["company"]["ceo"]["name"], "role": state["company"]["ceo"]["role"], "emoji": state["company"]["ceo"]["emoji"]})
        else:
            agent = next((agent for agent in state["agents"] if agent["id"] == part), None)
            if agent:
                participants.append({"id": agent["id"], "name": agent["name"], "role": agent["role"], "emoji": agent["emoji"]})
    transcript_ref = thread.get("transcript_ref") or transcript_reference_from_message(last)
    return {
        "id": thread["id"],
        "title": thread["title"],
        "mode": thread.get("mode", "direct"),
        "project_id": thread.get("project_id"),
        "participants": participants,
        "last_message": normalize_text(last.get("text"), 160),
        "last_sender": last.get("sender", "system"),
        "last_timestamp": last.get("timestamp", iso_now()),
        "message_count": len(thread.get("messages", [])),
        "visible_message_count": thread.get("visible_message_count", len(messages)),
        "hidden_message_count": thread.get("hidden_message_count", 0),
        "summary_only": bool(thread.get("summary_only")),
        "last_source": normalize_conversation_source(last.get("source") or thread.get("official_channel_source")),
        "last_source_label": conversation_source_label(last.get("source") or thread.get("official_channel_source")),
        "last_category": normalize_conversation_category(last.get("category") or last.get("kind")),
        "last_category_label": conversation_category_label(last.get("category") or last.get("kind")),
        "official_channel_label": thread.get("official_channel_label"),
        "official_channel_url": thread.get("official_channel_url"),
        "transcript_ref": transcript_ref,
    }


def build_filter_options(state: Dict[str, Any]) -> Dict[str, Any]:
    specialist_ids = sorted({*(state.get("skill_catalog") or SPECIALIST_CATALOG).keys(), *(agent_specialist(agent) for agent in state.get("agents", []))})
    return {
        "agents": [{"id": "all", "name": "All agents"}] + [{"id": agent["id"], "name": agent["name"]} for agent in state["agents"]],
        "projects": [{"id": "all", "name": "All projects"}] + [{"id": proj["id"], "name": proj["name"]} for proj in state["projects"]],
        "specialists": [{"id": "all", "name": "All specialist labels"}] + [{"id": key, "name": (state.get("skill_catalog") or SPECIALIST_CATALOG).get(key, {}).get("label", human_status(key))} for key in specialist_ids],
        "statuses": [{"id": "all", "name": "All statuses"}] + [{"id": status, "name": human_status(status)} for status in VALID_STATUSES],
        "horizons": [{"id": "all", "name": "All horizons"}] + [{"id": horizon, "name": horizon} for horizon in HORIZONS],
    }


def snapshot_state(state: Dict[str, Any]) -> Dict[str, Any]:
    snap = copy.deepcopy(state)
    snap["tasks"] = ordered_tasks(snap.get("tasks", []))
    task_lookup = {task["id"]: task for task in snap["tasks"]}
    roster = {agent["id"]: agent for agent in snap["agents"]}
    project_lookup = {project["id"]: project for project in snap["projects"]}

    for agent in snap["agents"]:
        enrich_agent_record(agent)
        agent["derived_status"] = normalized_agent_state(agent)
        task = task_lookup.get(agent.get("current_task_id"))
        agent["current_task"] = task["title"] if task else "No active task"
        agent["current_project"] = task["project_id"] if task else agent.get("project_id")
        agent["last_seen_label"] = relative_time_label(agent.get("last_heartbeat", ""))
        agent["model_tier"] = MODEL_TIERS.get(agent["id"], "sonnet")
        agent["target_zone"] = compute_target_zone(agent, snap["tasks"])
        agent["target_zone_label"] = ZONE_LABELS.get(agent["target_zone"], agent["target_zone"])
        agent["home_zone"] = HOME_ZONE_BY_SPECIALIST.get(agent.get("home_specialist", "planning"), "studio_pod")
        project = project_lookup.get(agent.get("current_project"))
        if project:
            agent["project_name"] = project["name"]
        manager_id = normalize_text(agent.get("manager"), 32)
        if manager_id == "ceo":
            agent["manager_name"] = (snap.get("company") or {}).get("ceo", {}).get("name", "CEO")
        elif manager_id in roster:
            agent["manager_name"] = roster[manager_id].get("name")
        else:
            agent["manager_name"] = ""
        if not agent.get("team_name"):
            team = default_team_for_specialist(agent.get("home_specialist", "planning"))
            agent["team_name"] = team.get("team_name")
            agent["team_id"] = team.get("team_id")
        agent["avatar_asset_id"] = agent.get("avatar_ref", DEFAULT_AVATAR_REF_BY_SPECIALIST.get(agent.get("home_specialist", "planning"), "orion"))

    for task in snap["tasks"]:
        owner = roster.get(task.get("owner"))
        validator = roster.get(task.get("validation_owner"))
        project = project_lookup.get(task.get("project_id"))
        task["routing_candidates"] = routing_candidates_for(snap, task.get("specialist"), task.get("project_id"))
        task["recommended_owner"] = task["routing_candidates"][0] if task["routing_candidates"] else task.get("recommended_owner")
        task["routing_mismatch"] = task.get("owner") != task.get("recommended_owner") and task.get("status") not in {"done", "backlog"}
        task["owner_name"] = owner["name"] if owner else task.get("owner", "Unassigned")
        task["validation_owner_name"] = validator["name"] if validator else task.get("validation_owner", "Unassigned")
        task["project_name"] = project["name"] if project else task.get("project_id")
        task["project_repo"] = project["repo"] if project else ""

    org_structure = build_org_structure(snap)
    snap["mission_control"] = mission_control_from_state(snap)
    snap["missions"] = copy.deepcopy(snap["mission_control"].get("missions", []))
    snap["metrics"] = metrics_from_state(snap)
    snap["attention_queue"] = build_attention_queue(snap)
    snap["filter_options"] = build_filter_options(snap)
    snap["conversations"] = [enrich_conversation_thread(thread, snap) for thread in snap.get("conversations", [])]
    snap["conversation_previews"] = [conversation_preview(thread, snap) for thread in snap.get("conversations", [])]
    snap["system_health"] = system_health_from_state(snap)
    snap["ticket_system"] = task_system_health_from_state(snap)
    snap["generated_at"] = iso_now()
    snap["zone_labels"] = ZONE_LABELS
    snap["scalability_profile"] = office_scale_profile(snap)
    snap["org_structure"] = org_structure
    snap["org_templates"] = org_templates()
    snap["ui_defaults"] = copy.deepcopy(snap.get("ui_defaults") or DEFAULT_UI_SETTINGS)
    snap["office_layout"] = copy.deepcopy(snap.get("office_layout") or {})
    snap["skill_catalog"] = copy.deepcopy(SPECIALIST_CATALOG)
    snap["roster_sync"] = copy.deepcopy((snap.get("openclaw_integration") or {}).get("roster_sync") or {})

    # v1.0.5: Blocking map — compute which tasks each task is blocking
    blocking_map: Dict[str, List[str]] = {}
    for t in snap.get("tasks", []):
        for dep in t.get("depends_on") or []:
            blocking_map.setdefault(dep, []).append(t["id"])
    for t in snap.get("tasks", []):
        t["blocking"] = blocking_map.get(t["id"], [])

    # v1.0.5: Workload per agent
    snap["agent_workload"] = _compute_workload(snap)
    wl = snap["agent_workload"]
    for ag in snap.get("agents", []):
        w = wl.get(ag["id"], {})
        ag["workload_active"] = w.get("active", 0)
        ag["workload_points"] = w.get("story_points", 0)
        ag["overloaded"]      = w.get("overloaded", False)

    # v1.0.5: Sprint burndown for active sprint
    active_sprints = [s for s in snap.get("sprints", []) if s.get("status") == "active"]
    if active_sprints:
        sp = active_sprints[0]
        sp_tasks = [t for t in snap.get("tasks", []) if t.get("sprint_id") == sp["id"]]
        total_pts = sum(t.get("story_points") or 1 for t in sp_tasks)
        done_pts  = sum(t.get("story_points") or 1 for t in sp_tasks if t.get("status") == "done")
        snap.setdefault("metrics", {})["active_sprint"] = {
            "id":               sp["id"],
            "name":             sp["name"],
            "goal":             sp.get("goal", ""),
            "total_points":     total_pts,
            "done_points":      done_pts,
            "remaining_points": total_pts - done_pts,
            "pct_complete":     round(done_pts / total_pts * 100) if total_pts else 0,
            "status":           sp.get("status"),
        }

    # v1.0.5: Notifications (unread count)
    snap["notifications"] = snap.get("notifications") or []
    snap["unread_notifications"] = sum(1 for n in snap["notifications"] if not n.get("read"))

    # v1.0.5: Sprints list
    snap.setdefault("sprints", [])

    return snap


def write_rate_limited(client_ip: str) -> bool:
    now = time.time()
    entries = RATE_LIMITS[client_ip]
    while entries and entries[0] < now - 60:
        entries.popleft()
    if len(entries) >= WRITE_LIMIT_PER_MINUTE:
        return True
    entries.append(now)
    return False


def read_json(handler: SimpleHTTPRequestHandler) -> Dict[str, Any]:
    length = int(handler.headers.get("Content-Length", "0"))
    if length <= 0 or length > MAX_BODY_BYTES:
        raise ValueError("invalid body size")
    data = handler.rfile.read(length)
    return json.loads(data.decode("utf-8"))


def require_auth(handler: SimpleHTTPRequestHandler, payload: Optional[Dict] = None) -> bool:
    """Accept token via Authorization header OR write_token field in JSON body."""
    auth = handler.headers.get("Authorization", "")
    if auth == f"Bearer {API_TOKEN}":
        return True
    # Fall back to write_token in body payload
    if isinstance(payload, dict) and payload.get("write_token") == API_TOKEN:
        return True
    send_json(handler, HTTPStatus.UNAUTHORIZED, {"error": "Unauthorized"})
    return False


def add_event(state: Dict[str, Any], kind: str, title: str, actor: str, details: str, project_id: Optional[str] = None) -> None:
    event = {
        "id": f"E-{int(time.time() * 1000)}",
        "timestamp": iso_now(),
        "kind": normalize_text(kind, 32),
        "title": normalize_text(title, 180),
        "actor": normalize_text(actor, 32),
        "details": normalize_text(details, 320),
        "project_id": normalize_text(project_id, 32),
    }
    state.setdefault("events", []).insert(0, event)
    state["events"] = state["events"][:120]
    append_event_log(event)


def find_thread(state: Dict[str, Any], thread_id: Optional[str] = None, participants: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
    if thread_id:
        return next((thread for thread in state.get("conversations", []) if thread["id"] == thread_id), None)
    if participants:
        target = sorted(participants)
        for thread in state.get("conversations", []):
            if sorted(thread.get("participants", [])) == target:
                return thread
    return None


def ensure_thread(
    state: Dict[str, Any],
    participants: List[str],
    project_id: Optional[str] = None,
    title: Optional[str] = None,
    mode: str = "direct",
    source: Optional[str] = None,
    official_channel_label: Optional[str] = None,
    session_key: Optional[str] = None,
    transcript_path: Optional[str] = None,
    official_channel_url_value: Optional[str] = None,
    summary_only: Optional[bool] = None,
) -> Dict[str, Any]:
    thread = find_thread(state, participants=participants)
    canonical_source = normalize_conversation_source(source or ("browser" if "ceo" in participants else "internal_session"))
    if thread:
        if canonical_source:
            thread["official_channel_source"] = canonical_source
        if official_channel_label:
            thread["official_channel_label"] = normalize_text(official_channel_label, 64)
        elif canonical_source and not thread.get("official_channel_label"):
            thread["official_channel_label"] = conversation_source_label(canonical_source)
        if session_key:
            thread["session_key"] = normalize_text(session_key, 160)
        if transcript_path:
            thread["transcript_path"] = normalize_text(transcript_path, 260)
        if official_channel_url_value:
            thread["official_channel_url"] = normalize_text(official_channel_url_value, 260)
        elif canonical_source and (thread.get("session_key") or session_key):
            thread["official_channel_url"] = official_channel_url(canonical_source, thread.get("session_key") or session_key, thread.get("official_channel_url") or "")
        if summary_only is not None:
            thread["summary_only"] = bool(summary_only)
        return thread
    normalized = [normalize_text(part, 32) for part in participants]
    session_value = normalize_text(session_key, 160)
    thread = {
        "id": f"TH-{int(time.time() * 1000)}",
        "title": title or " <> ".join(normalized),
        "mode": mode,
        "project_id": normalize_text(project_id, 32),
        "participants": normalized,
        "messages": [],
        "official_channel_source": canonical_source,
        "official_channel_label": normalize_text(official_channel_label or conversation_source_label(canonical_source), 64),
        "session_key": session_value,
        "official_channel_url": official_channel_url(canonical_source, session_value, official_channel_url_value or ""),
    }
    if transcript_path:
        thread["transcript_path"] = normalize_text(transcript_path, 260)
    if summary_only is not None:
        thread["summary_only"] = bool(summary_only)
    state.setdefault("conversations", []).append(thread)
    return thread


ACK_TEMPLATES = {
    "ceo": "Acknowledged. I’ll route this through the board and keep the CEO queue exception-only.",
    "orion": "Acknowledged. I’ll keep the task system updated directly and only ask for a huddle if a blocker appears.",
    "default": "Received. I’ll keep the task board current and surface blockers explicitly.",
}


def add_message(
    thread: Dict[str, Any],
    sender: str,
    text: str,
    kind: str = "message",
    related_task_id: Optional[str] = None,
    auto: bool = False,
    source: str = "browser",
    category: Optional[str] = None,
    session_key: Optional[str] = None,
    run_id: Optional[str] = None,
    transcript_path: Optional[str] = None,
    transcript_url: Optional[str] = None,
    channel_url: Optional[str] = None,
    channel_label: Optional[str] = None,
    hidden_by_default: bool = False,
) -> Dict[str, Any]:
    canonical_source = normalize_conversation_source(source or thread.get("official_channel_source"))
    session_value = normalize_text(session_key or thread.get("session_key"), 160)
    transcript_value = normalize_text(transcript_path or thread.get("transcript_path"), 260)
    transcript_link = normalize_text(transcript_url or channel_url or thread.get("official_channel_url") or official_channel_url(canonical_source, session_value), 260)
    message = {
        "id": f"M-{int(time.time() * 1000)}-{len(thread.get('messages', []))}",
        "timestamp": iso_now(),
        "sender": normalize_text(sender, 32),
        "text": normalize_text(text, 400),
        "kind": normalize_text(kind, 24),
        "category": normalize_conversation_category(category or kind),
        "source": canonical_source,
        "channel_label": normalize_text(channel_label or thread.get("official_channel_label") or conversation_source_label(canonical_source), 64),
        "session_key": session_value,
        "auto": bool(auto),
    }
    if transcript_value:
        message["transcript_path"] = transcript_value
    if transcript_link:
        message["transcript_url"] = transcript_link
    if run_id:
        message["run_id"] = normalize_text(run_id, 120)
    if related_task_id:
        message["related_task_id"] = normalize_text(related_task_id, 32)
    if hidden_by_default:
        message["hidden_by_default"] = True
    thread.setdefault("messages", []).append(message)
    thread["messages"] = thread["messages"][-80:]
    return message


def update_agent_heartbeat(state: Dict[str, Any], payload: Dict[str, Any], emit_event: bool = True) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    agent_payload = payload.get("agent", payload)
    ident = normalize_text(agent_payload.get("id") or agent_payload.get("name"), 64)
    if not ident:
        return None, "agent id or name is required"
    agent = next((item for item in state["agents"] if item["id"] == ident or item["name"].lower() == ident.lower()), None)
    if not agent:
        return None, f"unknown agent: {ident}"

    for field in ["status", "current_task_id", "note", "project_id"]:
        if field in agent_payload:
            agent[field] = normalize_text(agent_payload[field], 200)
    if "speaking" in agent_payload:
        agent["speaking"] = bool(agent_payload["speaking"])
    if "skills" in agent_payload:
        agent["skills"] = normalize_list(agent_payload["skills"], 8, 40)
    if "collaborating_with" in agent_payload:
        agent["collaborating_with"] = normalize_list(agent_payload["collaborating_with"], 6, 24)
    if "blockers" in agent_payload:
        agent["blockers"] = normalize_list(agent_payload["blockers"], 6, 100)

    metadata = agent_payload.get("metadata", {}) if isinstance(agent_payload.get("metadata"), dict) else {}
    for field in ["done_summary", "doing_summary", "next_summary"]:
        if field in metadata:
            agent[field] = normalize_text(metadata[field], 280)
    for field in ["session_key", "publish_kind", "run_id"]:
        if field in metadata:
            agent[field] = normalize_text(metadata[field], 160)
    if "speaking" in metadata:
        agent["speaking"] = bool(metadata["speaking"])
    if "blockers" in metadata:
        agent["blockers"] = normalize_list(metadata["blockers"], 6, 100)
    if "collaborating_with" in metadata:
        agent["collaborating_with"] = normalize_list(metadata["collaborating_with"], 6, 24)

    agent["last_heartbeat"] = iso_now()

    summary = agent.get("doing_summary") or agent.get("note") or "Heartbeat received."
    kind = "blocked" if agent.get("blockers") or agent.get("status") == "blocked" else "heartbeat"
    if emit_event:
        add_event(state, kind, f"{agent['name']} heartbeat", agent["id"], summary, agent.get("project_id"))
    return agent, None


TASK_FIELDS = {
    "title",
    "project_id",
    "status",
    "specialist",
    "owner",
    "priority",
    "horizon",
    "due_date",
    "description",
    "validation_owner",
    "branch_name",
    "issue_ref",
    "pr_status",
    "mission_id",
}


def update_task(state: Dict[str, Any], payload: Dict[str, Any], emit_event: bool = True) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    task_payload = payload.get("task", payload)
    task_id = normalize_text(task_payload.get("id"), 32)
    if not task_id:
        return None, "task id is required"
    task = next((item for item in state["tasks"] if item["id"] == task_id), None)
    if not task:
        return None, f"unknown task: {task_id}"

    old_status = task.get("status")
    old_owner = task.get("owner")
    old_priority = task.get("priority")
    old_horizon = task.get("horizon")

    if "status" in task_payload:
        requested_status = normalize_text(task_payload.get("status"), 32)
        transition_error = task_transition_error(task, requested_status)
        if transition_error:
            return None, transition_error
    if "priority" in task_payload:
        requested_priority = normalize_text(task_payload.get("priority"), 8)
        if requested_priority not in TASK_PRIORITIES:
            return None, f"invalid task priority: {requested_priority}"
    if "horizon" in task_payload:
        requested_horizon = normalize_text(task_payload.get("horizon"), 32)
        if requested_horizon not in HORIZONS:
            return None, f"invalid task horizon: {requested_horizon}"
    actor_ids = known_actor_ids(state)
    if "owner" in task_payload:
        requested_owner = normalize_text(task_payload.get("owner"), 32)
        if requested_owner and requested_owner not in actor_ids:
            return None, f"unknown owner: {requested_owner}"
    if "validation_owner" in task_payload:
        requested_validator = normalize_text(task_payload.get("validation_owner"), 32)
        if requested_validator and requested_validator not in actor_ids:
            return None, f"unknown validation owner: {requested_validator}"

    for field in TASK_FIELDS:
        if field in task_payload:
            task[field] = normalize_text(task_payload[field], 240)
    if task.get("priority") not in TASK_PRIORITIES:
        task["priority"] = old_priority or "P2"
    if task.get("horizon") not in HORIZONS:
        task["horizon"] = old_horizon or "This Week"
    if "labels" in task_payload:
        task["labels"] = normalize_list(task_payload["labels"], 12, 32)
    if "progress" in task_payload:
        try:
            task["progress"] = max(0, min(100, int(task_payload["progress"])))
        except Exception:
            return None, "invalid task progress"
    # v1.0.5 extensions: story points, sprint, dependencies
    if "story_points" in task_payload:
        sp = task_payload.get("story_points")
        task["story_points"] = int(sp) if sp in (1, 2, 3, 5, 8, 13) else None
    if "sprint_id" in task_payload:
        task["sprint_id"] = normalize_text(task_payload.get("sprint_id"), 20) or None
    if "depends_on" in task_payload:
        raw_deps = normalize_list(task_payload.get("depends_on") or [], 20, 32)
        cycle = _detect_circular_dep(task["id"], raw_deps, state.get("tasks", []))
        if cycle:
            return None, f"circular dependency: {' -> '.join(cycle)}"
        task["depends_on"] = raw_deps
        _propagate_dependencies(state)
    if task.get("status") == "done":
        task["progress"] = 100
    elif task.get("status") == "validation" and int(task.get("progress") or 0) < 80:
        task["progress"] = 80
    if "blocked" in task_payload:
        task["blocked"] = bool(task_payload["blocked"])
    if task.get("blocked") and task.get("status") == "done":
        return None, "blocked task cannot be done"
    if "collaborators" in task_payload:
        task["collaborators"] = normalize_list(task_payload["collaborators"], 6, 24)
    if "artifacts" in task_payload:
        task["artifacts"] = normalize_list(task_payload["artifacts"], 8, 120)
    routing = routing_candidates_for(state, task.get("specialist", "planning"), task.get("project_id"))
    task["recommended_owner"] = routing[0] if routing else recommended_owner_for(task.get("specialist", "planning"), task.get("owner"))
    task["backup_owner"] = routing[1] if len(routing) > 1 else backup_owner_for(task.get("specialist", "planning"), task.get("owner"))
    task["updated_at"] = iso_now()

    sync_task_assignment(state, task, previous_owner=old_owner, previous_status=old_status)

    note = normalize_text(payload.get("note"), 220)
    if emit_event:
        if task.get("status") != old_status:
            add_event(state, task["status"], f"{task['title']} -> {human_status(task['status'])}", task.get("owner", "system"), note or "Task status changed", task.get("project_id"))
        elif task.get("owner") != old_owner:
            add_event(state, "routing", f"{task['title']} reassigned", task.get("owner", "system"), note or "Task owner changed", task.get("project_id"))
        elif note:
            add_event(state, "task_note", f"{task['title']} updated", task.get("owner", "system"), note, task.get("project_id"))
    return task, None

def create_task_from_message(state: Dict[str, Any], sender: str, target: str, text: str, specialist: str, project_id: str) -> Dict[str, Any]:
    next_id = 200 + len(state["tasks"]) + 1
    routing = routing_candidates_for(state, specialist, project_id)
    owner = routing[0] if routing else recommended_owner_for(specialist, target)
    task = make_task(
        f"T-{next_id}",
        text[:74],
        project_id,
        "backlog",
        specialist,
        owner,
        "P1",
        "This Week",
        2,
        text,
        ["directive", specialist, project_id],
        0,
        "ralph",
        collaborators=[sender] if sender not in {"ceo", owner} else [],
    )
    state["tasks"].insert(0, task)
    add_event(state, "task_created", f"{task['id']} created from conversation", sender, task["title"], task["project_id"])
    return task


def add_directive(state: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
    directive = {
        "id": f"D-{int(time.time() * 1000)}",
        "timestamp": iso_now(),
        "target": normalize_text(payload.get("target") or "orion", 40),
        "project_id": normalize_text(payload.get("project_id") or "ceo-console", 32),
        "specialist": normalize_text(payload.get("specialist") or "planning", 24),
        "text": normalize_text(payload.get("text"), 500),
        "create_task": bool(payload.get("create_task", True)),
        "status": "queued",
    }
    state.setdefault("directives", [])
    state.setdefault("sprints", [])
    state.setdefault("notifications", [])
    # Add story_points=None and depends_on=[] to existing tasks that lack them
    for t in state.get("tasks", []):
        t.setdefault("story_points", None)
        t.setdefault("sprint_id", None)
        t.setdefault("depends_on", [])
        t.setdefault("blocking", []).insert(0, directive)
    state["directives"] = state["directives"][:60]
    add_event(state, "directive", f"CEO directive -> {directive['target']}", "ceo", directive["text"], directive["project_id"])
    if directive["create_task"] and directive["text"]:
        create_task_from_message(state, "ceo", directive["target"], directive["text"], directive["specialist"], directive["project_id"])
    return directive


def post_message(state: Dict[str, Any], payload: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    thread_id = normalize_text(payload.get("thread_id"), 48)
    sender = normalize_text(payload.get("sender") or "ceo", 32)
    target = normalize_text(payload.get("target") or "orion", 32)
    text = normalize_text(payload.get("text"), 500)
    project_id = normalize_text(payload.get("project_id") or "ceo-console", 32)
    specialist = normalize_text(payload.get("specialist") or "planning", 24)
    create_task = bool(payload.get("create_task"))
    classification = normalize_conversation_category(payload.get("classification") or payload.get("category") or ("directive" if create_task else "discussion"))
    source = normalize_conversation_source(payload.get("source") or "browser")

    if not text:
        return None, "message text is required"
    if sender != "ceo" and sender not in {agent["id"] for agent in state["agents"]}:
        return None, "unknown sender"
    if target != "ceo" and target not in {agent["id"] for agent in state["agents"]}:
        return None, "unknown target"

    participants = [sender, target]
    mode = "direct"
    if {sender, target} == {"ceo", "orion"}:
        mode = "ceo-chief"
    elif sender == "orion" or target == "orion":
        mode = "chief-specialist"

    thread = find_thread(state, thread_id=thread_id)
    if not thread:
        thread = ensure_thread(state, participants, project_id=project_id, title=None, mode=mode, source=source)
    thread["official_channel_source"] = source
    thread["official_channel_label"] = conversation_source_label(source)
    thread.setdefault("session_key", f"chat:clawtasker:{slugify(thread['id'])}")
    thread.setdefault("transcript_path", f"~/.openclaw/sessions/{slugify(thread['id'])}.jsonl")
    thread["official_channel_url"] = official_channel_url(source, thread.get("session_key", ""), thread.get("official_channel_url") or "")

    message = add_message(
        thread,
        sender,
        text,
        kind="message",
        source=source,
        category=classification,
        session_key=thread.get("session_key"),
        transcript_path=thread.get("transcript_path"),
        transcript_url=thread.get("official_channel_url"),
        channel_label=thread.get("official_channel_label"),
    )
    event_kind = "directive" if classification == "directive" else "conversation"
    add_event(state, event_kind, f"{sender} messaged {target}", sender, text, project_id)

    created_task = None
    if create_task:
        created_task = create_task_from_message(state, sender, target, text, specialist, project_id)
        add_message(thread, "system", f"Created {created_task['id']} in {created_task['project_name'] if 'project_name' in created_task else created_task['project_id']} and routed it to {created_task['owner']}", kind="system", category="system", related_task_id=created_task["id"], auto=True, source="browser", session_key=thread.get("session_key"), transcript_path=thread.get("transcript_path"), transcript_url=thread.get("official_channel_url"), channel_label=thread.get("official_channel_label"))

    if target != "ceo":
        ack = ACK_TEMPLATES.get(target, ACK_TEMPLATES["default"])
        if create_task and created_task:
            ack = f"Acknowledged. I linked the request to {created_task['id']} and will keep the board updated directly."
        add_message(thread, target, ack, kind="ack", category="ack", related_task_id=created_task["id"] if created_task else None, auto=True, source="internal_session", session_key=thread.get("session_key"), transcript_path=thread.get("transcript_path"), transcript_url=thread.get("official_channel_url"), channel_label=thread.get("official_channel_label"))

    return {"thread": thread, "message": message, "created_task": created_task}, None


def openclaw_publish_contract(state: Dict[str, Any]) -> Dict[str, Any]:
    integration = copy.deepcopy(state.get("openclaw_integration") or default_state().get("openclaw_integration", {}))
    integration["latest_stable"] = OPENCLAW_LATEST["npm_version"]
    integration["github_tag"] = OPENCLAW_LATEST["github_tag"]
    integration["node_recommended"] = OPENCLAW_LATEST["node_recommended"]
    integration["node_compatible"] = OPENCLAW_LATEST["node_compatible"]
    integration["publish_contract"] = {
        "endpoint": "/api/openclaw/publish",
        "events": ["heartbeat", "task_update", "validation", "conversation_note", "run", "mission_plan"],
        "auth": "Authorization: Bearer <CLAWTASKER_API_TOKEN>",
        "recommended_mode": "OpenClaw hooks or a local helper script publish status into ClawTasker.",
        "dedupe_window_seconds": PUBLISH_DEDUPE_WINDOW_SECONDS,
        "conversation_sources": list(CONVERSATION_SOURCE_LABELS.keys()),
        "conversation_categories": list(CONVERSATION_CATEGORY_LABELS.keys()),
        "summary_default": "summary_only default: Subagent/internal-session threads are summarized by default inside ClawTasker while full discussion remains in OpenClaw.",
        "non_goals": [
            "ClawTasker does not replace OpenClaw routing",
            "ClawTasker does not own OpenClaw sessions",
        ],
    }
    integration["roster_sync_contract"] = {
        "endpoint": "/api/openclaw/roster_sync",
        "purpose": "sync the human-facing roster with the agents.list-style team that exists in OpenClaw, including manager/team relationships",
        "merge_mode": "add-or-update by agent id; keep local visuals unless the payload overrides them",
        "tested_agent_target": SCALABILITY_TARGET_AGENTS,
        "fields": ["id", "name", "role", "manager", "team_id", "team_name", "specialist", "core_skills", "department", "org_level"],
    }
    integration["mission_plan_contract"] = {
        "endpoint": "/api/missions/plan",
        "schema": "/api/schema/mission-plan",
        "purpose": "allow a chief agent or specialist to publish a shared mission brief with staffing, dependencies, risks, and linked task ids",
        "auth": "Authorization: Bearer <CLAWTASKER_API_TOKEN>",
        "required_fields": ["title", "objective"],
        "accepted_fields": ["id", "title", "objective", "status", "priority", "horizon", "owner", "project_ids", "task_ids", "required_specialists", "assigned_agents", "summary", "next_actions", "success_criteria", "dependencies", "risks", "milestones"],
        "dashboard_visibility": [
            "mission brief appears in the dashboard",
            "staffing and coverage appear in the dashboard",
            "dependency and risk summaries feed the attention queue",
        ],
        "upsert_mode": "create or update by mission id (slugified from title when omitted)",
    }
    integration["agent_registration_contract"] = {
        "endpoint": "/api/agents/register",
        "schema": "/api/schema/agent-register",
        "purpose": "allow a new or existing agent to self-register identity, role, and skills so the company chart and roster stay human-readable",
        "auth": "Authorization: Bearer <CLAWTASKER_API_TOKEN>",
        "required_fields": ["name", "role", "skills_or_specialist"],
        "accepted_fields": ["id", "name", "role", "skills", "core_skills", "specialist", "home_specialist", "specialists", "department", "manager", "project_id", "team_id", "team_name", "status", "allowed_tools", "profile_hue", "avatar_ref"],
        "chart_visibility": [
            "name appears on roster cards and company chart",
            "role appears on roster cards and company chart",
            "skills feed specialist routing hints and chart summaries",
        ],
        "upsert_mode": "create or update by agent id (slugified from name when omitted)",
    }
    integration["conversation_contract"] = {
        "role": "thin-operator-rail",
        "official_channels": integration.get("official_channels") or default_state().get("openclaw_integration", {}).get("official_channels", []),
        "default_human_channel": "browser",
        "default_subagent_view": "summary_only",
        "directive_rule": "Directives become auditable work items or linked notes.",
        "discussion_rule": "Discussion stays conversational and does not silently mutate tasks.",
        "transcript_linking": "Expose session_key, run_id, and transcript_path where available.",
}
    integration["agent_onboarding_prompt"] = {
        "title": "ClawTasker CEO Console — Onboarding for AI Agents and Human Users",
        "philosophy": (
            "ClawTasker is a flexible collaboration aid — not a rigid methodology. "
            "Use it to coordinate tasks, share status, and keep the human CEO informed. "
            "AI agents work at their own natural pace. The platform adapts to you, "
            "not the other way around."
        ),
        "for_ai_agents": [
            "Register once via POST /api/agents/register — your name, role, specialist, and manager.",
            "Post heartbeats with your current status (working | idle | blocked | validation).",
            "Update tasks when you start, finish, or get blocked: POST /api/tasks/update.",
            "Post conversation notes for context that matters to the CEO or chief agent.",
            "Use missions to share a focus brief and staffing plan for larger efforts.",
            "Story points, sprints, and dependencies are optional — use them only if they help.",
            "If you are blocked, flag it immediately. The CEO attention queue is exception-only.",
        ],
        "for_human_user": [
            "Watch the Dashboard for attention items — blocked agents, overloaded agents, risks.",
            "Use the Board to see work status at a glance; create tasks via + New task.",
            "Use Missions for multi-agent efforts that need a shared objective and staffing plan.",
            "Use Calendar to see scheduled agent work and recurring jobs.",
            "Use Conversations to send directives and read agent summaries.",
            "Use the Office simulation to get a live feel for where agents are working.",
            "Sprint / iteration tracking is available but entirely optional.",
            "The platform supports any project type: software, business plan, coaching, "
            "manual process, product launch, or custom initiative.",
        ],
        "what_not_to_do": [
            "Do not impose scrum ceremonies on AI agents — they work faster than sprint cycles.",
            "Do not require agents to update every field — post only what is meaningful.",
            "Do not make the platform a bottleneck — agents should work even when it is down.",
            "Do not over-engineer workflow — if a feature adds friction, skip it.",
        ],
    }
    return integration



def sync_openclaw_roster(state: Dict[str, Any], payload: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    roster = payload.get("roster", payload)
    agents_in = roster.get("agents") if isinstance(roster, dict) else None
    if not isinstance(agents_in, list) or not agents_in:
        return None, "roster agents list is required"
    replace_missing = bool(roster.get("replace_missing")) if isinstance(roster, dict) else False
    existing = {agent["id"]: agent for agent in state.get("agents", [])}
    seen: set[str] = set()
    added: List[str] = []
    updated: List[str] = []
    for item in agents_in:
        if not isinstance(item, dict):
            continue
        agent_id = normalize_text(item.get("id") or item.get("agentId") or item.get("name"), 32)
        if not agent_id or agent_id == "ceo":
            continue
        seen.add(agent_id)
        record = existing.get(agent_id, {
            "id": agent_id,
            "name": item.get("name") or agent_id.title(),
            "status": item.get("status") or "idle",
            "current_task_id": item.get("current_task_id") or "",
            "note": "",
            "last_heartbeat": iso_now(),
            "blockers": [],
            "collaborating_with": [],
            "speaking": False,
        })
        incoming_manager = item.get("manager") or item.get("reports_to") or item.get("manager_id")
        if incoming_manager not in (None, ""):
            item["manager"] = incoming_manager
        for field in ["name", "role", "manager", "status", "project_id", "current_task_id", "note", "emoji", "department", "profile_hue", "avatar_ref", "org_level", "team_id", "team_name", "coordination_scope", "manager_title"]:
            if field in item and item[field] not in (None, ""):
                record[field] = normalize_text(item[field], 120)
        home_specialist = normalize_text(item.get("home_specialist") or item.get("specialist") or item.get("specialists", [""])[0] if isinstance(item.get("specialists"), list) and item.get("specialists") else item.get("specialist"), 32)
        if home_specialist:
            record["home_specialist"] = home_specialist
        if "specialists" in item or "specialist" in item or "home_specialist" in item:
            record["specialists"] = normalize_list(item.get("specialists") or [record.get("home_specialist")], 8, 32)
        if "skills" in item:
            record["skills"] = normalize_list(item.get("skills"), 10, 40)
        if "core_skills" in item:
            record["core_skills"] = normalize_list(item.get("core_skills"), 8, 32)
        if "allowed_tools" in item:
            record["allowed_tools"] = normalize_list(item.get("allowed_tools"), 12, 24)
        if "blockers" in item:
            record["blockers"] = normalize_list(item.get("blockers"), 6, 100)
        if "collaborating_with" in item:
            record["collaborating_with"] = normalize_list(item.get("collaborating_with"), 8, 24)
        if "last_heartbeat" in item:
            record["last_heartbeat"] = normalize_text(item.get("last_heartbeat"), 40) or iso_now()
        else:
            record.setdefault("last_heartbeat", iso_now())
        enrich_agent_record(record)
        if agent_id in existing:
            updated.append(agent_id)
        else:
            state.setdefault("agents", []).append(record)
            existing[agent_id] = record
            added.append(agent_id)
    if replace_missing:
        for agent in state.get("agents", []):
            if agent.get("id") in {"orion", "codex", "violet", "scout", "charlie", "ralph", "shield", "quill", "pixel", "echo"}:
                continue
            if agent.get("id") not in seen:
                agent["status"] = "offline"
                agent["note"] = "Inactive in the latest synced OpenClaw roster."
    refresh_state_metadata(state)
    integration = state.setdefault("openclaw_integration", default_state()["openclaw_integration"])
    integration["roster_sync"] = {
        "last_synced_at": iso_now(),
        "source": normalize_text(roster.get("source") if isinstance(roster, dict) else "manual", 40) or "manual",
        "managed_agents": len(state.get("agents", [])),
        "last_added": added[:24],
        "last_updated": updated[:24],
        "replace_missing": replace_missing,
    }
    add_event(state, "roster_sync", "OpenClaw roster sync applied", "orion", f"Added {len(added)} agents, updated {len(updated)} agents.", "ceo-console")
    return {"sync": integration["roster_sync"], "agents": state.get("agents", [])}, None


def register_agent(state: Dict[str, Any], payload: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    agent_payload = payload.get("agent", payload) if isinstance(payload, dict) else {}
    if not isinstance(agent_payload, dict):
        return None, "agent payload must be an object"

    name = normalize_text(agent_payload.get("name"), 120)
    role = normalize_text(agent_payload.get("role"), 120)
    if not name:
        return None, "agent name is required"
    if not role:
        return None, "agent role is required"

    has_skill_input = any(
        agent_payload.get(field)
        for field in ["skills", "core_skills", "specialist", "home_specialist", "specialists"]
    )
    if not has_skill_input:
        return None, "at least one skill, core skill, or specialist label is required"

    agent_id = normalize_text(agent_payload.get("id"), 32) or slugify_identifier(name, 32)
    if agent_id == "ceo":
        return None, "agent id cannot be ceo"

    specialist = infer_specialist_from_profile(agent_payload)
    specialists = normalize_list(agent_payload.get("specialists") or [agent_payload.get("home_specialist") or agent_payload.get("specialist") or specialist], 8, 32) or [specialist]
    skills = normalize_list(agent_payload.get("skills"), 10, 40)
    core_skills = normalize_list(agent_payload.get("core_skills"), 8, 32)
    if not skills:
        skills = normalize_list(list(core_skills) + specialists + SPECIALIST_CATALOG.get(specialist, {}).get("keywords", []), 10, 40)
    if not core_skills:
        core_skills = normalize_list(skills or specialists or [specialist], 8, 32)

    record: Dict[str, Any] = {
        "id": agent_id,
        "name": name,
        "role": role,
        "status": normalize_text(agent_payload.get("status") or "idle", 40) or "idle",
        "project_id": normalize_text(agent_payload.get("project_id") or "ceo-console", 32) or "ceo-console",
        "note": normalize_text(agent_payload.get("note"), 220),
        "department": normalize_text(agent_payload.get("department"), 80),
        "manager": normalize_text(agent_payload.get("manager"), 32),
        "team_id": normalize_text(agent_payload.get("team_id"), 40),
        "team_name": normalize_text(agent_payload.get("team_name"), 80),
        "org_level": normalize_text(agent_payload.get("org_level"), 24),
        "coordination_scope": normalize_text(agent_payload.get("coordination_scope"), 220),
        "manager_title": normalize_text(agent_payload.get("manager_title"), 80),
        "profile_hue": normalize_text(agent_payload.get("profile_hue"), 24),
        "avatar_ref": normalize_text(agent_payload.get("avatar_ref"), 32),
        "specialist": specialist,
        "home_specialist": specialist,
        "specialists": specialists,
        "skills": skills,
        "core_skills": core_skills,
        "allowed_tools": normalize_list(agent_payload.get("allowed_tools"), 12, 24),
        "blockers": normalize_list(agent_payload.get("blockers"), 6, 100),
        "collaborating_with": normalize_list(agent_payload.get("collaborating_with"), 8, 24),
        "current_task_id": normalize_text(agent_payload.get("current_task_id"), 32),
        "last_heartbeat": iso_now(),
    }

    sync_result, error = sync_openclaw_roster(
        state,
        {
            "roster": {
                "source": normalize_text(payload.get("source") or agent_payload.get("source") or "agent-register", 40) or "agent-register",
                "replace_missing": False,
                "agents": [record],
            }
        },
    )
    if error:
        return None, error

    refresh_state_metadata(state)
    integration = state.setdefault("openclaw_integration", default_state()["openclaw_integration"])
    operation = "registered"
    if agent_id in ((sync_result or {}).get("sync") or {}).get("last_updated", []):
        operation = "updated"
    integration["agent_registration"] = {
        "last_registered_at": iso_now(),
        "last_agent_id": agent_id,
        "last_operation": operation,
        "source": normalize_text(payload.get("source") or agent_payload.get("source") or "agent-register", 40) or "agent-register",
    }
    agent = next((item for item in state.get("agents", []) if item.get("id") == agent_id), None)
    add_event(
        state,
        "agent_register",
        f"{name} {operation}",
        agent_id,
        f"{role} • {', '.join((agent or {}).get('core_skills', [])[:3] or core_skills[:3])}",
        (agent or {}).get("project_id") or "ceo-console",
    )
    structure = build_org_structure(state)
    card = org_card_payload(agent or record)
    return {
        "agent": agent,
        "org_card": card,
        "org_structure": structure,
        "registration": integration["agent_registration"],
        "contract": openclaw_publish_contract(state).get("agent_registration_contract", {}),
    }, None


def plan_mission(state: Dict[str, Any], payload: Dict[str, Any], emit_event: bool = True) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    mission_payload = payload.get("mission", payload) if isinstance(payload, dict) else {}
    if not isinstance(mission_payload, dict):
        return None, "mission payload must be an object"

    title = normalize_text(mission_payload.get("title"), 160)
    objective = normalize_text(mission_payload.get("objective"), 320)
    if not title:
        return None, "mission title is required"
    if not objective:
        return None, "mission objective is required"

    mission_id = normalize_text(mission_payload.get("id"), 32) or slugify_identifier(title, 32)
    if not mission_id:
        return None, "mission id is required"

    record = normalize_mission_record({
        **mission_payload,
        "id": mission_id,
        "title": title,
        "objective": objective,
        "updated_at": iso_now(),
        "created_at": mission_payload.get("created_at") or iso_now(),
        "source": normalize_text(payload.get("source") or mission_payload.get("source") or "mission-control", 40) or "mission-control",
    })

    existing = next((item for item in state.get("missions", []) if item.get("id") == mission_id), None)
    operation = "created"
    if existing:
        record["created_at"] = existing.get("created_at") or record["created_at"]
        existing.clear()
        existing.update(record)
        stored = existing
        operation = "updated"
    else:
        state.setdefault("missions", []).append(record)
        stored = record

    for task in state.get("tasks", []):
        if task.get("id") in stored.get("task_ids", []):
            task["mission_id"] = stored["id"]

    state["missions"] = [normalize_mission_record(mission) for mission in state.get("missions", [])]
    materialized = materialize_mission(stored, state)
    if emit_event:
        add_event(
            state,
            "mission_plan",
            f"Mission {operation}",
            materialized.get("owner") or "orion",
            f"{materialized.get('title')} • {materialized.get('staffing', {}).get('coverage_label', 'no staffing data')}",
            (materialized.get("project_ids") or ["ceo-console"])[0],
        )
    return {
        "mission": materialized,
        "mission_control": mission_control_from_state(state),
        "contract": openclaw_publish_contract(state).get("mission_plan_contract", {}),
        "operation": operation,
    }, None


def post_openclaw_note(
    state: Dict[str, Any],
    sender: str,
    project_id: str,
    text: str,
    related_task_id: Optional[str] = None,
    source: str = "internal_session",
    category: str = "summary",
    session_key: Optional[str] = None,
    run_id: Optional[str] = None,
    transcript_path: Optional[str] = None,
    transcript_url: Optional[str] = None,
    channel_label: Optional[str] = None,
    summary_only: Optional[bool] = None,
) -> Optional[Dict[str, Any]]:
    text = normalize_text(text, 400)
    if not text:
        return None
    target = "orion" if sender != "orion" else "ceo"
    mode = "chief-specialist" if target == "orion" else "ceo-chief"
    canonical_source = normalize_conversation_source(source)
    thread = ensure_thread(state, [sender, target], project_id=project_id, mode=mode, source=canonical_source)
    thread["official_channel_source"] = canonical_source
    thread["official_channel_label"] = normalize_text(channel_label or thread.get("official_channel_label") or conversation_source_label(canonical_source), 64)
    if session_key:
        thread["session_key"] = normalize_text(session_key, 160)
    if transcript_path:
        thread["transcript_path"] = normalize_text(transcript_path, 260)
    if transcript_url or thread.get("session_key"):
        thread["official_channel_url"] = official_channel_url(canonical_source, thread.get("session_key", ""), transcript_url or thread.get("official_channel_url") or "")
    if summary_only is None:
        thread["summary_only"] = thread_summary_only(thread) or canonical_source == "internal_session"
    else:
        thread["summary_only"] = bool(summary_only)
    return add_message(thread, sender, text, kind="status", category=category, related_task_id=related_task_id, auto=False, source=canonical_source, session_key=thread.get("session_key"), run_id=run_id, transcript_path=thread.get("transcript_path"), transcript_url=thread.get("official_channel_url"), channel_label=thread.get("official_channel_label"), hidden_by_default=(canonical_source == "internal_session" and normalize_conversation_category(category) == "discussion"))


def publish_from_openclaw(state: Dict[str, Any], payload: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    publish = payload.get("publish", payload)
    agent_id = normalize_text(publish.get("agentId") or publish.get("agent_id") or publish.get("agent"), 64)
    if not agent_id:
        return None, "agentId is required"
    event_kind = normalize_text(publish.get("event") or publish.get("kind") or "heartbeat", 32).lower()
    status = normalize_text(publish.get("status") or publish.get("agentStatus") or "working", 32)
    task_id = normalize_text(publish.get("taskId") or publish.get("task_id"), 32)
    mission_id = normalize_text(publish.get("missionId") or publish.get("mission_id"), 32)
    project_id = normalize_text(publish.get("projectId") or publish.get("project_id") or "", 32)
    note = normalize_text(publish.get("note") or publish.get("message") or publish.get("summary"), 320)
    session_key = normalize_text(publish.get("sessionKey") or publish.get("session_key"), 160)
    run_id = normalize_text(publish.get("runId") or publish.get("run_id"), 96)
    blockers = normalize_list(publish.get("blockers"), 6, 100)
    collaborators = normalize_list(publish.get("collaboratingWith") or publish.get("collaborating_with"), 6, 24)
    metadata = publish.get("metadata") if isinstance(publish.get("metadata"), dict) else {}
    source = normalize_conversation_source(publish.get("source") or publish.get("channel") or metadata.get("source") or metadata.get("channel") or ("internal_session" if event_kind in {"conversation_note", "run", "note"} else "webhook"))
    category = normalize_conversation_category(publish.get("category") or metadata.get("category") or ("summary" if source == "internal_session" else "status"))
    transcript_path = normalize_text(publish.get("transcriptPath") or publish.get("transcript_path") or metadata.get("transcript_path"), 260)
    transcript_url = normalize_text(publish.get("transcriptUrl") or publish.get("transcript_url") or metadata.get("transcript_url"), 260)
    channel_label = normalize_text(publish.get("channelLabel") or publish.get("channel_label") or metadata.get("channel_label") or conversation_source_label(source), 64)
    channel_url = normalize_text(publish.get("channelUrl") or publish.get("channel_url") or metadata.get("channel_url"), 260)
    summary_only = bool(publish.get("summaryOnly") if publish.get("summaryOnly") is not None else metadata.get("summary_only") if metadata.get("summary_only") is not None else source == "internal_session")

    signature = "|".join([agent_id, event_kind, status or "", task_id or "", project_id or "", note or "", run_id or ""])
    duplicate_publish = register_publish_signature(state, signature)

    agent, error = update_agent_heartbeat(state, {
        "agent": {
            "id": agent_id,
            "status": status or metadata.get("status") or "working",
            "current_task_id": task_id or metadata.get("taskId") or metadata.get("task_id"),
            "project_id": project_id or metadata.get("projectId") or metadata.get("project_id"),
            "note": note,
            "blockers": blockers or metadata.get("blockers") or [],
            "collaborating_with": collaborators or metadata.get("collaborating_with") or [],
            "speaking": bool(publish.get("speaking") or metadata.get("speaking")),
            "metadata": {
                "done_summary": publish.get("doneSummary") or metadata.get("done_summary"),
                "doing_summary": publish.get("doingSummary") or metadata.get("doing_summary") or note,
                "next_summary": publish.get("nextSummary") or metadata.get("next_summary"),
                "session_key": session_key,
                "publish_kind": event_kind,
                "run_id": run_id,
            },
        }
    }, emit_event=not duplicate_publish)
    if error:
        return None, error

    task = None
    if task_id or isinstance(publish.get("task"), dict):
        task_source = publish.get("task") if isinstance(publish.get("task"), dict) else {}
        task_payload = {"id": task_id or normalize_text(task_source.get("id"), 32)}
        status_value = publish.get("taskStatus") or task_source.get("status") or ("validation" if event_kind == "validation" else None)
        if status_value:
            task_payload["status"] = status_value
        project_value = project_id or task_source.get("project_id") or task_source.get("projectId")
        if project_value:
            task_payload["project_id"] = project_value
        owner_value = publish.get("owner") or task_source.get("owner") or agent_id
        if owner_value:
            task_payload["owner"] = normalize_text(owner_value, 32)
        validation_value = publish.get("validationOwner") or task_source.get("validation_owner") or task_source.get("validationOwner")
        if validation_value:
            task_payload["validation_owner"] = normalize_text(validation_value, 32)
        if publish.get("progress") is not None or task_source.get("progress") is not None:
            task_payload["progress"] = publish.get("progress") if publish.get("progress") is not None else task_source.get("progress")
        if publish.get("blocked") is not None or task_source.get("blocked") is not None:
            task_payload["blocked"] = publish.get("blocked") if publish.get("blocked") is not None else task_source.get("blocked")
        labels_value = publish.get("labels") or task_source.get("labels")
        if labels_value:
            task_payload["labels"] = labels_value
        artifacts_value = publish.get("artifacts") or task_source.get("artifacts")
        if artifacts_value:
            task_payload["artifacts"] = artifacts_value
        branch_value = publish.get("branch") or task_source.get("branch_name") or task_source.get("branchName")
        if branch_value:
            task_payload["branch_name"] = branch_value
        issue_value = publish.get("issueRef") or task_source.get("issue_ref") or task_source.get("issueRef")
        if issue_value:
            task_payload["issue_ref"] = issue_value
        pr_status_value = publish.get("prStatus") or task_source.get("pr_status") or task_source.get("prStatus")
        if pr_status_value:
            task_payload["pr_status"] = pr_status_value
        mission_value = mission_id or task_source.get("mission_id") or task_source.get("missionId")
        if mission_value:
            task_payload["mission_id"] = mission_value
        task, task_error = update_task(state, {"task": task_payload, "note": note}, emit_event=not duplicate_publish)
        if task_error:
            return None, task_error

    mission = None
    if event_kind in {"mission_plan", "mission_update"}:
        mission_meta = metadata.get("mission") if isinstance(metadata.get("mission"), dict) else {}
        mission_payload = {
            "id": mission_id or mission_meta.get("id") or metadata.get("mission_id") or metadata.get("id"),
            "title": publish.get("title") or mission_meta.get("title") or metadata.get("title") or note or f"Mission from {agent_id}",
            "objective": publish.get("objective") or mission_meta.get("objective") or metadata.get("objective") or note or "Mission update published from OpenClaw.",
            "status": publish.get("missionStatus") or publish.get("mission_status") or mission_meta.get("status") or metadata.get("status") or "active",
            "priority": publish.get("priority") or mission_meta.get("priority") or metadata.get("priority") or "P1",
            "horizon": publish.get("horizon") or mission_meta.get("horizon") or metadata.get("horizon") or "This Week",
            "owner": publish.get("owner") or mission_meta.get("owner") or metadata.get("owner") or agent_id,
            "project_ids": publish.get("projectIds") or publish.get("project_ids") or mission_meta.get("project_ids") or metadata.get("project_ids") or ([project_id] if project_id else []),
            "task_ids": publish.get("taskIds") or publish.get("task_ids") or mission_meta.get("task_ids") or metadata.get("task_ids") or ([task.get("id")] if task else ([task_id] if task_id else [])),
            "required_specialists": publish.get("requiredSpecialists") or publish.get("required_specialists") or mission_meta.get("required_specialists") or metadata.get("required_specialists") or [],
            "assigned_agents": publish.get("assignedAgents") or publish.get("assigned_agents") or mission_meta.get("assigned_agents") or metadata.get("assigned_agents") or [agent_id],
            "summary": publish.get("summary") or mission_meta.get("summary") or metadata.get("summary") or note,
            "next_actions": publish.get("nextActions") or publish.get("next_actions") or mission_meta.get("next_actions") or metadata.get("next_actions") or [],
            "success_criteria": publish.get("successCriteria") or publish.get("success_criteria") or mission_meta.get("success_criteria") or metadata.get("success_criteria") or [],
            "dependencies": publish.get("dependencies") or mission_meta.get("dependencies") or metadata.get("dependencies") or [],
            "risks": publish.get("risks") or mission_meta.get("risks") or metadata.get("risks") or [],
            "milestones": publish.get("milestones") or mission_meta.get("milestones") or metadata.get("milestones") or [],
            "source": mission_meta.get("source") or metadata.get("source") or source,
        }
        mission, mission_error = plan_mission(state, {"source": source, "mission": mission_payload}, emit_event=not duplicate_publish)
        if mission_error:
            return None, mission_error

    thread_message = None
    if (event_kind in {"conversation_note", "note", "run", "mission_plan", "mission_update"} or publish.get("conversation") or note) and not duplicate_publish:
        project_hint = project_id or (task or {}).get("project_id") or agent.get("project_id") or "ceo-console"
        thread_message = post_openclaw_note(state, agent_id, project_hint, note or f"Published {event_kind}", related_task_id=task.get("id") if task else task_id or None, source=source, category=category, session_key=session_key, run_id=run_id, transcript_path=transcript_path, transcript_url=transcript_url or channel_url, channel_label=channel_label, summary_only=summary_only)

    integration = state.setdefault("openclaw_integration", default_state()["openclaw_integration"])
    integration["last_publish"] = {
        "timestamp": iso_now(),
        "agent_id": agent_id,
        "event": event_kind,
        "task_id": task.get("id") if task else task_id or None,
        "mission_id": mission.get("mission", {}).get("id") if isinstance(mission, dict) else mission_id or None,
        "project_id": (task or {}).get("project_id") or project_id or agent.get("project_id"),
        "session_key": session_key,
        "run_id": run_id,
        "source": source,
        "category": category,
        "channel_label": channel_label,
        "channel_url": channel_url or transcript_url or official_channel_url(source, session_key),
        "transcript_path": transcript_path,
        "duplicate": duplicate_publish,
    }
    return {
        "agent": agent,
        "task": task,
        "mission": mission,
        "thread_message": thread_message,
        "publish": integration["last_publish"],
        "duplicate_publish": duplicate_publish,
        "contract": openclaw_publish_contract(state),
    }, None


def send_json(handler: SimpleHTTPRequestHandler, status: HTTPStatus, payload: Dict[str, Any]) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(body)


class ClawTaskerHandler(SimpleHTTPRequestHandler):
    server_version = f"ClawTaskerCEOConsole/{APP_VERSION}"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def log_message(self, format: str, *args: Any) -> None:
        return

    def end_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "same-origin")
        self.send_header("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'; img-src 'self' data:; connect-src 'self'; font-src 'self' data:;",
        )
        super().end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            with STATE_LOCK:
                raw_state = load_state()
                health = system_health_from_state(raw_state)
            send_json(self, HTTPStatus.OK, {"ok": True, "time": iso_now(), "version": APP_VERSION, **health})
            return
        if parsed.path == "/api/snapshot":
            with STATE_LOCK:
                state = snapshot_state(load_state())
            send_json(self, HTTPStatus.OK, state)
            return
        if parsed.path == "/api/system/recovery":
            with STATE_LOCK:
                raw_state = load_state()
                payload = system_health_from_state(raw_state)
            send_json(self, HTTPStatus.OK, payload)
            return
        if parsed.path == "/api/schema/heartbeat":
            schema = json.loads((SCHEMA_DIR / "heartbeat.schema.json").read_text(encoding="utf-8"))
            send_json(self, HTTPStatus.OK, schema)
            return
        if parsed.path == "/api/schema/task":
            schema = json.loads((SCHEMA_DIR / "task.schema.json").read_text(encoding="utf-8"))
            send_json(self, HTTPStatus.OK, schema)
            return
        if parsed.path == "/api/schema/message":
            schema = json.loads((SCHEMA_DIR / "message.schema.json").read_text(encoding="utf-8"))
            send_json(self, HTTPStatus.OK, schema)
            return
        if parsed.path == "/api/schema/agent-register":
            schema = json.loads((SCHEMA_DIR / "agent_register.schema.json").read_text(encoding="utf-8"))
            send_json(self, HTTPStatus.OK, schema)
            return
        if parsed.path == "/api/schema/mission-plan":
            schema = json.loads((SCHEMA_DIR / "mission_plan.schema.json").read_text(encoding="utf-8"))
            send_json(self, HTTPStatus.OK, schema)
            return
        if parsed.path == "/api/openclaw/contract":
            with STATE_LOCK:
                payload = openclaw_publish_contract(load_state())
            send_json(self, HTTPStatus.OK, {"ok": True, **payload})
            return
        if parsed.path == "/api/events/stream":
            subscriber = register_stream_subscriber()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Connection", "keep-alive")
            self.end_headers()
            try:
                self.wfile.write(b": clawtasker live stream\n\n")
                self.wfile.flush()
                while True:
                    try:
                        event = subscriber.get(timeout=15)
                        self.wfile.write(stream_frame(event))
                        self.wfile.flush()
                    except Empty:
                        self.wfile.write(b": ping\n\n")
                        self.wfile.flush()
            except Exception:
                pass
            finally:
                unregister_stream_subscriber(subscriber)
            return
        if parsed.path == "/":
            self.path = "/index.html"
        super().do_GET()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        client_ip = self.client_address[0]
        if not parsed.path.startswith("/api/"):
            send_json(self, HTTPStatus.NOT_FOUND, {"error": "Unsupported route"})
            return
        # Read body first so we can check write_token as auth fallback
        try:
            payload = read_json(self)
        except Exception as exc:
            send_json(self, HTTPStatus.BAD_REQUEST, {"error": f"Invalid JSON payload: {exc}"})
            return
        if not require_auth(self, payload):
            return
        if write_rate_limited(client_ip):
            send_json(self, HTTPStatus.TOO_MANY_REQUESTS, {"error": "Rate limit exceeded"})
            return

        if parsed.path == "/api/agents/register":
            with STATE_LOCK:
                state = load_state()
                result, error = register_agent(state, payload)
                if error:
                    send_json(self, HTTPStatus.BAD_REQUEST, {"error": error})
                    return
                save_state(state)
                send_json(self, HTTPStatus.OK, {"ok": True, **(result or {})})
            return

        if parsed.path == "/api/agents/heartbeat":
            with STATE_LOCK:
                state = load_state()
                agent, error = update_agent_heartbeat(state, payload)
                if error:
                    send_json(self, HTTPStatus.BAD_REQUEST, {"error": error})
                    return
                save_state(state)
                snap = snapshot_state(state)
                output = next(item for item in snap["agents"] if item["id"] == agent["id"])
                send_json(self, HTTPStatus.OK, {"ok": True, "agent": output})
            return

        if parsed.path == "/api/missions/plan":
            with STATE_LOCK:
                state = load_state()
                result, error = plan_mission(state, payload)
                if error:
                    send_json(self, HTTPStatus.BAD_REQUEST, {"error": error})
                    return
                save_state(state)
                send_json(self, HTTPStatus.OK, {"ok": True, **(result or {})})
            return

        if parsed.path == "/api/tasks/update":
            with STATE_LOCK:
                state = load_state()
                task, error = update_task(state, payload)
                if error:
                    send_json(self, HTTPStatus.BAD_REQUEST, {"error": error})
                    return
                save_state(state)
                snap = snapshot_state(state)
                output = next(item for item in snap["tasks"] if item["id"] == task["id"])
                send_json(self, HTTPStatus.OK, {"ok": True, "task": output})
            return

        if parsed.path == "/api/agents/decommission":
            if not check_auth():
                return
            with STATE_LOCK:
                state = load_state()
                result, error = decommission_agent(state, body)
            if error:
                send_json(self, HTTPStatus.BAD_REQUEST, {"error": error})
            else:
                send_json(self, HTTPStatus.OK, result)
            return

        if parsed.path == "/api/org/configure":
            if not check_auth():
                return
            with STATE_LOCK:
                state = load_state()
                result, error = configure_org(state, body)
            if error:
                send_json(self, HTTPStatus.BAD_REQUEST, {"error": error})
            else:
                send_json(self, HTTPStatus.OK, result)
            return

        if parsed.path == "/api/agents/decommission":
            if not check_auth():
                return
            with STATE_LOCK:
                state = load_state()
                result, error = decommission_agent(state, body)
            if error:
                send_json(self, HTTPStatus.BAD_REQUEST, {"error": error})
            else:
                send_json(self, HTTPStatus.OK, result)
            return

        if parsed.path == "/api/org/configure":
            if not check_auth():
                return
            with STATE_LOCK:
                state = load_state()
                result, error = configure_org(state, body)
            if error:
                send_json(self, HTTPStatus.BAD_REQUEST, {"error": error})
            else:
                send_json(self, HTTPStatus.OK, result)
            return

        if parsed.path == "/api/sprints/create":
            if not check_auth():
                return
            with STATE_LOCK:
                state = load_state()
                result, error = create_sprint(state, body)
            if error:
                send_json(self, HTTPStatus.BAD_REQUEST, {"error": error})
            else:
                send_json(self, HTTPStatus.OK, result)
            return

        if parsed.path == "/api/sprints/update":
            if not check_auth():
                return
            with STATE_LOCK:
                state = load_state()
                result, error = update_sprint(state, body)
            if error:
                send_json(self, HTTPStatus.BAD_REQUEST, {"error": error})
            else:
                send_json(self, HTTPStatus.OK, result)
            return

        if parsed.path == "/api/projects/configure":
            if not check_auth():
                return
            with STATE_LOCK:
                state = load_state()
                result, error = configure_project(state, body)
            if error:
                send_json(self, HTTPStatus.BAD_REQUEST, {"error": error})
            else:
                send_json(self, HTTPStatus.OK, result)
            return

        if parsed.path == "/api/notifications/dismiss":
            if not check_auth():
                return
            with STATE_LOCK:
                state = load_state()
                result, error = dismiss_notifications(state, body)
            if error:
                send_json(self, HTTPStatus.BAD_REQUEST, {"error": error})
            else:
                send_json(self, HTTPStatus.OK, result)
            return

        if parsed.path == "/api/ceo/directive":
            with STATE_LOCK:
                state = load_state()
                directive = add_directive(state, payload)
                save_state(state)
                send_json(self, HTTPStatus.OK, {"ok": True, "directive": directive})
            return

        if parsed.path == "/api/conversations/message":
            with STATE_LOCK:
                state = load_state()
                result, error = post_message(state, payload)
                if error:
                    send_json(self, HTTPStatus.BAD_REQUEST, {"error": error})
                    return
                save_state(state)
                send_json(self, HTTPStatus.OK, {"ok": True, **(result or {})})
            return

        if parsed.path == "/api/openclaw/publish":
            with STATE_LOCK:
                state = load_state()
                result, error = publish_from_openclaw(state, payload)
                if error:
                    send_json(self, HTTPStatus.BAD_REQUEST, {"error": error})
                    return
                save_state(state)
                send_json(self, HTTPStatus.OK, {"ok": True, **(result or {})})
            return

        if parsed.path == "/api/openclaw/roster_sync":
            with STATE_LOCK:
                state = load_state()
                result, error = sync_openclaw_roster(state, payload)
                if error:
                    send_json(self, HTTPStatus.BAD_REQUEST, {"error": error})
                    return
                save_state(state)
                send_json(self, HTTPStatus.OK, {"ok": True, **(result or {})})
            return

        if parsed.path == "/api/demo/reset":
            with STATE_LOCK:
                state = default_state()
                save_state(state)
                send_json(self, HTTPStatus.OK, {"ok": True, "reset": True})
            return

        send_json(self, HTTPStatus.NOT_FOUND, {"error": "Unknown API endpoint"})



def decommission_agent(state, payload):
    """Mark an agent offline and remove from active assignments."""
    agent_id = str(payload.get("agent_id") or payload.get("id") or "").strip()[:32]
    if not agent_id:
        return None, "agent_id is required"
    if agent_id == "ceo":
        return None, "cannot decommission the CEO"
    agent = next((a for a in state.get("agents", []) if a.get("id") == agent_id), None)
    if not agent:
        return None, f"unknown agent: {agent_id}"
    reason = str(payload.get("reason") or "decommissioned")[:120]
    old_name = agent.get("name", agent_id)
    agent["status"] = "offline"
    agent["derived_status"] = "offline"
    agent["note"] = reason
    agent["last_heartbeat"] = iso_now()
    unassigned_tasks = []
    for task in state.get("tasks", []):
        if task.get("owner") == agent_id:
            task["owner"] = ""
            task["owner_name"] = "[unassigned]"
            unassigned_tasks.append(task["id"])
        if task.get("validation_owner") == agent_id:
            task["validation_owner"] = ""
            task["validation_owner_name"] = "[unassigned]"
    for mission in state.get("missions", []):
        assigned = mission.get("assigned_agents", [])
        if agent_id in assigned:
            assigned.remove(agent_id)
    save_state(state)
    return {
        "ok": True,
        "message": f"Agent {old_name} ({agent_id}) marked offline",
        "agent_id": agent_id,
        "reason": reason,
        "tasks_unassigned": unassigned_tasks,
    }, None


def configure_org(state, payload):
    """Configure org settings: chief agent, CEO display name/role, company name."""
    updates = {}
    chief_id = str(payload.get("chief_agent_id") or "").strip()[:32]
    if chief_id:
        existing = next((a for a in state.get("agents", []) if a.get("id") == chief_id), None)
        if not existing:
            return None, f"unknown agent for chief role: {chief_id}"
        state.setdefault("sync_contract", {})["chief_agent"] = chief_id
        existing["org_level"] = "chief"
        updates["chief_agent"] = chief_id
    ceo_name = str(payload.get("ceo_name") or "").strip()[:80]
    ceo_role = str(payload.get("ceo_role") or "").strip()[:120]
    company_name = str(payload.get("company_name") or "").strip()[:120]
    if ceo_name:
        state.setdefault("company", {}).setdefault("ceo", {})["name"] = ceo_name
        updates["ceo_name"] = ceo_name
    if ceo_role:
        state.setdefault("company", {}).setdefault("ceo", {})["role"] = ceo_role
        updates["ceo_role"] = ceo_role
    if company_name:
        state.setdefault("company", {})["name"] = company_name
        updates["company_name"] = company_name
    if not updates:
        return None, "no valid fields: chief_agent_id, ceo_name, ceo_role, company_name"
    save_state(state)
    return {
        "ok": True,
        "message": "Org configuration updated",
        "updates": updates,
        "org_structure": build_org_structure(state),
    }, None


def main() -> None:
    ensure_dirs()
    if not STATE_FILE.exists():
        save_state(default_state())
    httpd = ThreadingHTTPServer((HOST, PORT), ClawTaskerHandler)
    print(f"ClawTasker CEO Console listening on http://{HOST}:{PORT}")
    print("Write API token:", API_TOKEN)
    httpd.serve_forever()


if __name__ == "__main__":
    main()


# ═══════════════════════════════════════════════════════════════════════════
# v1.0.5 ADDITIONS: Sprints, dependencies, story points, project types,
#                   agent workload, notifications
# ═══════════════════════════════════════════════════════════════════════════

VALID_SPRINT_STATUSES = {"planning", "active", "closed"}

SPECIALIST_SETS: Dict[str, List[str]] = {
    "software":  ["planning","code","qa","ops","security","docs","design","distribution"],
    "manual":    ["planning","ops","docs"],
    "business":  ["planning","research","ops","docs"],
    "coaching":  ["planning","docs","hr","research"],
    "plan":      ["planning","research","docs","design"],
    "launch":    ["planning","design","distribution","media"],
    "custom":    [],
}

NOTIFICATION_KINDS = {
    "task_blocked","task_completed","mission_risk","agent_offline",
    "sprint_ending","dependency_cleared","directive_delivered","routing_mismatch",
    "overloaded",
}

def _next_id(prefix: str, items: List[Dict]) -> str:
    nums = [int(re.sub(r"[^0-9]","",i.get("id","0"))) for i in items if i.get("id","").startswith(prefix)]
    return f"{prefix}{(max(nums)+1 if nums else 1):03d}"


def _add_notification(state: Dict, kind: str, title: str, detail: str, agent_id: str = "") -> None:
    if kind not in NOTIFICATION_KINDS:
        return
    note: Dict[str, Any] = {
        "id": _next_id("N-", state.get("notifications", [])),
        "kind": kind,
        "title": title,
        "detail": detail,
        "agent_id": agent_id,
        "created_at": iso_now(),
        "read": False,
        "dismissed": False,
    }
    state.setdefault("notifications", []).insert(0, note)
    # Cap at 100 notifications
    state["notifications"] = state["notifications"][:100]


def _detect_circular_dep(task_id: str, depends_on: List[str], all_tasks: List[Dict]) -> List[str]:
    """Return cycle path if circular, else []."""
    task_map = {t["id"]: t.get("depends_on", []) for t in all_tasks}
    task_map[task_id] = depends_on
    visited: set = set()
    path: List[str] = []
    def dfs(tid: str) -> bool:
        if tid in path:
            return True
        if tid in visited:
            return False
        visited.add(tid)
        path.append(tid)
        for dep in task_map.get(tid, []):
            if dfs(dep):
                return True
        path.pop()
        return False
    dfs(task_id)
    return path if task_id in path else []


def _propagate_dependencies(state: Dict) -> None:
    """Auto-block tasks whose depends_on tasks are blocked; unblock when clear."""
    tasks_by_id = {t["id"]: t for t in state.get("tasks", [])}
    for task in state.get("tasks", []):
        deps = task.get("depends_on", [])
        if not deps:
            continue
        blocked_deps = [d for d in deps if tasks_by_id.get(d, {}).get("blocked")]
        if blocked_deps and not task.get("_dep_blocked"):
            task["blocked"] = True
            task["_dep_blocked"] = True
            task.setdefault("labels", [])
            for d in blocked_deps:
                dep_label = f"waiting:{d}"
                if dep_label not in task["labels"]:
                    task["labels"].append(dep_label)
        elif not blocked_deps and task.get("_dep_blocked"):
            task["_dep_blocked"] = False
            task["labels"] = [l for l in task.get("labels", []) if not l.startswith("waiting:")]
            # Only unblock if not blocked for another reason
            if not task.get("labels"):
                task["blocked"] = False



def create_sprint(state: Dict, payload: Dict) -> Tuple[Optional[Dict], Optional[str]]:
    name       = normalize_text(payload.get("name"), 80)
    project_id = normalize_text(payload.get("project_id") or "ceo-console", 32)
    goal       = normalize_text(payload.get("goal") or "", 240)
    start_date = normalize_text(payload.get("start_date") or "", 20)
    end_date   = normalize_text(payload.get("end_date") or "", 20)
    if not name:
        return None, "sprint name is required"
    sprints = state.setdefault("sprints", [])
    sprint_id = _next_id("SPR-", sprints)
    sprint: Dict[str, Any] = {
        "id": sprint_id, "name": name, "project_id": project_id,
        "goal": goal, "start_date": start_date, "end_date": end_date,
        "status": normalize_text(payload.get("status") or "planning", 20),
        "velocity": 0,
        "created_at": iso_now(),
    }
    if sprint["status"] not in VALID_SPRINT_STATUSES:
        sprint["status"] = "planning"
    sprints.insert(0, sprint)
    save_state(state)
    return {"ok": True, "sprint": sprint}, None


def update_sprint(state: Dict, payload: Dict) -> Tuple[Optional[Dict], Optional[str]]:
    sprint_id = normalize_text(payload.get("sprint_id") or payload.get("id"), 20)
    if not sprint_id:
        return None, "sprint_id is required"
    sprint = next((s for s in state.get("sprints", []) if s["id"] == sprint_id), None)
    if not sprint:
        return None, f"unknown sprint: {sprint_id}"
    for field in ("name","goal","start_date","end_date","status"):
        val = normalize_text(payload.get(field), 240)
        if val:
            sprint[field] = val
    if sprint["status"] == "closed":
        # compute velocity
        sprint_tasks = [t for t in state.get("tasks",[]) if t.get("sprint_id")==sprint_id and t.get("status")=="done"]
        sprint["velocity"] = sum(t.get("story_points") or 1 for t in sprint_tasks)
        _add_notification(state,"sprint_ending",f"Sprint '{sprint['name']}' closed",
                          f"Velocity: {sprint['velocity']} points")
    save_state(state)
    return {"ok": True, "sprint": sprint}, None


def configure_project(state: Dict, payload: Dict) -> Tuple[Optional[Dict], Optional[str]]:
    project_id = normalize_text(payload.get("project_id") or payload.get("id"), 32)
    if not project_id:
        return None, "project_id is required"
    project = next((p for p in state.get("projects", []) if p["id"] == project_id), None)
    if not project:
        return None, f"unknown project: {project_id}"
    for field in ("name","tagline","type"):
        val = normalize_text(payload.get(field), 120)
        if val:
            project[field] = val
    if "relevant_specialists" in payload:
        project["relevant_specialists"] = normalize_list(payload["relevant_specialists"], 12, 32)
    if not project.get("relevant_specialists"):
        project["relevant_specialists"] = SPECIALIST_SETS.get(project.get("type","software"), [])
    save_state(state)
    return {"ok": True, "project": project}, None


def get_notifications(state: Dict) -> List[Dict]:
    return [n for n in state.get("notifications", []) if not n.get("dismissed")]


def dismiss_notifications(state: Dict, payload: Dict) -> Tuple[Optional[Dict], Optional[str]]:
    dismiss_all = bool(payload.get("all"))
    note_id     = normalize_text(payload.get("id"), 20)
    dismissed   = 0
    for n in state.get("notifications", []):
        if dismiss_all or n.get("id") == note_id:
            n["dismissed"] = True
            n["read"]      = True
            dismissed += 1
    save_state(state)
    return {"ok": True, "dismissed": dismissed}, None

