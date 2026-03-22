#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from typing import List


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description='Register or update an agent identity in ClawTasker so the roster and company chart can display name, role, and skills.')
    p.add_argument('--url', default=os.getenv('CLAWTASKER_REGISTER_URL', 'http://127.0.0.1:3000/api/agents/register'))
    p.add_argument('--token', default=os.getenv('CLAWTASKER_API_TOKEN', 'change-me-local'))
    p.add_argument('--id', help='Stable agent id. If omitted, ClawTasker derives one from the name.')
    p.add_argument('--name', required=True)
    p.add_argument('--role', required=True)
    p.add_argument('--specialist', help='Primary specialist label such as code, research, docs, or ops.')
    p.add_argument('--home-specialist', dest='home_specialist')
    p.add_argument('--specialist-label', dest='specialists', action='append', default=[])
    p.add_argument('--skill', action='append', default=[])
    p.add_argument('--core-skill', dest='core_skills', action='append', default=[])
    p.add_argument('--department')
    p.add_argument('--manager')
    p.add_argument('--project')
    p.add_argument('--team-id')
    p.add_argument('--team-name')
    p.add_argument('--status', default='idle')
    p.add_argument('--tool', dest='allowed_tools', action='append', default=[])
    p.add_argument('--profile-hue')
    p.add_argument('--avatar-ref')
    p.add_argument('--source', default=os.getenv('CLAWTASKER_REGISTER_SOURCE', 'mission-control'))
    return p


def build_payload(args: argparse.Namespace) -> dict:
    agent = {
        'name': args.name,
        'role': args.role,
        'status': args.status,
        'department': args.department,
        'manager': args.manager,
        'project_id': args.project,
        'team_id': args.team_id,
        'team_name': args.team_name,
        'allowed_tools': [item for item in args.allowed_tools if item],
        'profile_hue': args.profile_hue,
        'avatar_ref': args.avatar_ref,
        'source': args.source,
    }
    if args.id:
        agent['id'] = args.id
    if args.specialist:
        agent['specialist'] = args.specialist
    if args.home_specialist:
        agent['home_specialist'] = args.home_specialist
    specialist_labels = [item for item in args.specialists if item]
    if specialist_labels:
        agent['specialists'] = specialist_labels
    skills = [item for item in args.skill if item]
    if skills:
        agent['skills'] = skills
    core_skills = [item for item in args.core_skills if item]
    if core_skills:
        agent['core_skills'] = core_skills
    return {'source': args.source, 'agent': {key: value for key, value in agent.items() if value not in (None, '', [])}}


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
        sys.stderr.write(f'agent registration failed: {exc}\n')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
