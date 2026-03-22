#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from typing import List


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description='Publish an OpenClaw agent update to ClawTasker.')
    p.add_argument('--url', default=os.getenv('CLAWTASKER_URL', 'http://127.0.0.1:3000/api/openclaw/publish'))
    p.add_argument('--token', default=os.getenv('CLAWTASKER_API_TOKEN', 'change-me-local'))
    p.add_argument('--agent', required=True)
    p.add_argument('--event', default='heartbeat', choices=['heartbeat', 'task_update', 'validation', 'conversation_note', 'run'])
    p.add_argument('--status', default='working')
    p.add_argument('--task')
    p.add_argument('--project')
    p.add_argument('--note', default='')
    p.add_argument('--session-key')
    p.add_argument('--run-id')
    p.add_argument('--progress', type=int)
    p.add_argument('--branch')
    p.add_argument('--issue-ref')
    p.add_argument('--pr-status')
    p.add_argument('--blocked', action='store_true')
    p.add_argument('--speaking', action='store_true')
    p.add_argument('--artifact', action='append', default=[])
    p.add_argument('--blocker', action='append', default=[])
    p.add_argument('--collaborator', action='append', default=[])
    p.add_argument('--done-summary', default='')
    p.add_argument('--doing-summary', default='')
    p.add_argument('--next-summary', default='')
    return p


def build_payload(args: argparse.Namespace) -> dict:
    payload = {
        'agentId': args.agent,
        'event': args.event,
        'status': args.status,
        'note': args.note,
        'speaking': bool(args.speaking),
        'blocked': bool(args.blocked),
        'blockers': [item for item in args.blocker if item],
        'collaboratingWith': [item for item in args.collaborator if item],
        'artifacts': [item for item in args.artifact if item],
        'metadata': {
            'done_summary': args.done_summary,
            'doing_summary': args.doing_summary,
            'next_summary': args.next_summary,
        },
    }
    if args.task:
        payload['taskId'] = args.task
    if args.project:
        payload['projectId'] = args.project
    if args.session_key:
        payload['sessionKey'] = args.session_key
    if args.run_id:
        payload['runId'] = args.run_id
    if args.progress is not None:
        payload['progress'] = args.progress
    if args.branch:
        payload['branch'] = args.branch
    if args.issue_ref:
        payload['issueRef'] = args.issue_ref
    if args.pr_status:
        payload['prStatus'] = args.pr_status
    return payload


def main(argv: List[str] | None = None) -> int:
    args = parser().parse_args(argv)
    payload = build_payload(args)
    request = urllib.request.Request(
        args.url,
        data=json.dumps(payload).encode('utf-8'),
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {args.token}',
        },
        method='POST',
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            sys.stdout.write(response.read().decode('utf-8'))
            sys.stdout.write('\n')
        return 0
    except Exception as exc:
        sys.stderr.write(f'publish failed: {exc}\n')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
