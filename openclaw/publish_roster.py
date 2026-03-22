#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path
from typing import Any, Dict, List


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description='Publish an OpenClaw roster snapshot to ClawTasker, including manager/team relationships when provided.')
    p.add_argument('--url', default=os.getenv('CLAWTASKER_ROSTER_URL', 'http://127.0.0.1:3000/api/openclaw/roster_sync'))
    p.add_argument('--token', default=os.getenv('CLAWTASKER_API_TOKEN', 'change-me-local'))
    p.add_argument('--source', default=os.getenv('CLAWTASKER_ROSTER_SOURCE', 'openclaw-agents-list'))
    p.add_argument('--replace-missing', action='store_true', help='Mark previously synced non-core agents missing from this payload as offline.')
    p.add_argument('--file', required=True, help='Path to a JSON file containing {"agents": [...]} or a raw list of agents.')
    return p


def build_payload(args: argparse.Namespace) -> Dict[str, Any]:
    raw = json.loads(Path(args.file).read_text(encoding='utf-8'))
    if isinstance(raw, list):
        agents = raw
    elif isinstance(raw, dict) and isinstance(raw.get('agents'), list):
        agents = raw['agents']
    elif isinstance(raw, dict) and isinstance(raw.get('roster', {}).get('agents'), list):
        agents = raw['roster']['agents']
    else:
        raise ValueError('Expected a JSON list of agents or an object with an agents array.')
    return {
        'roster': {
            'source': args.source,
            'replace_missing': bool(args.replace_missing),
            'agents': agents,
        }
    }


def main(argv: List[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        payload = build_payload(args)
    except Exception as exc:
        sys.stderr.write(f'roster build failed: {exc}\n')
        return 2
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
        sys.stderr.write(f'roster publish failed: {exc}\n')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
