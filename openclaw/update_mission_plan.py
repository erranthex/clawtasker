#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from typing import List


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description='Publish or update a mission plan in ClawTasker so human operators and AI agents share one mission brief.'
    )
    p.add_argument('--url', default=os.getenv('CLAWTASKER_MISSION_URL', 'http://127.0.0.1:3000/api/missions/plan'))
    p.add_argument('--token', default=os.getenv('CLAWTASKER_API_TOKEN', 'change-me-local'))
    p.add_argument('--id')
    p.add_argument('--title', required=True)
    p.add_argument('--objective', required=True)
    p.add_argument('--summary', default='')
    p.add_argument('--status', default='planned', choices=['draft', 'planned', 'active', 'blocked', 'review', 'done'])
    p.add_argument('--priority', default='P1', choices=['P0', 'P1', 'P2', 'P3'])
    p.add_argument('--horizon', default='This Week', choices=['Today', 'This Week', 'This Month', 'Later'])
    p.add_argument('--owner', default='orion')
    p.add_argument('--project', dest='project_ids', action='append', default=[])
    p.add_argument('--task', dest='task_ids', action='append', default=[])
    p.add_argument('--required-specialist', dest='required_specialists', action='append', default=[])
    p.add_argument('--assigned-agent', dest='assigned_agents', action='append', default=[])
    p.add_argument('--next-action', dest='next_actions', action='append', default=[])
    p.add_argument('--success', dest='success_criteria', action='append', default=[])
    p.add_argument('--dependency', action='append', default=[])
    p.add_argument('--risk', action='append', default=[])
    p.add_argument('--milestone', action='append', default=[])
    p.add_argument('--source', default=os.getenv('CLAWTASKER_MISSION_SOURCE', 'mission-control'))
    return p


def build_payload(args: argparse.Namespace) -> dict:
    mission = {
        'title': args.title,
        'objective': args.objective,
        'summary': args.summary,
        'status': args.status,
        'priority': args.priority,
        'horizon': args.horizon,
        'owner': args.owner,
        'project_ids': [item for item in args.project_ids if item],
        'task_ids': [item for item in args.task_ids if item],
        'required_specialists': [item for item in args.required_specialists if item],
        'assigned_agents': [item for item in args.assigned_agents if item],
        'next_actions': [item for item in args.next_actions if item],
        'success_criteria': [item for item in args.success_criteria if item],
        'dependencies': [item for item in args.dependency if item],
        'risks': [item for item in args.risk if item],
        'milestones': [item for item in args.milestone if item],
    }
    if args.id:
        mission['id'] = args.id
    return {'source': args.source, 'mission': {key: value for key, value in mission.items() if value not in (None, '', [])}}


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
        sys.stderr.write(f'mission plan publish failed: {exc}\n')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
