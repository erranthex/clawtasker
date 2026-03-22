#!/usr/bin/env python3
"""Send sample updates to a local ClawTasker instance."""
from __future__ import annotations

import json
import os
import urllib.request

BASE_URL = os.getenv("CLAWTASKER_BASE_URL", "http://127.0.0.1:3000")
TOKEN = os.getenv("CLAWTASKER_API_TOKEN", "change-me-local")


def post(path: str, payload: dict) -> None:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"{BASE_URL}{path}",
        method="POST",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {TOKEN}",
        },
    )
    with urllib.request.urlopen(request) as response:
        print(response.read().decode("utf-8"))


def main() -> None:
    post(
        "/api/agents/heartbeat",
        {
            "agent": {
                "id": "codex",
                "status": "working",
                "current_task_id": "T-203",
                "project_id": "ceo-console",
                "metadata": {
                    "done_summary": "Refactored filter state.",
                    "doing_summary": "Linking project and agent filters to the board and backlog.",
                    "next_summary": "Hand off to Ralph for validation."
                }
            }
        },
    )
    post(
        "/api/conversations/message",
        {
            "sender": "ceo",
            "target": "orion",
            "project_id": "ceo-console",
            "specialist": "planning",
            "create_task": True,
            "text": "Keep the office simulation deterministic and low-overhead."
        },
    )


if __name__ == "__main__":
    main()
