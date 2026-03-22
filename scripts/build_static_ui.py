#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent.parent
UI = ROOT / 'ui'
SRC = UI / 'src'
PUBLIC = UI / 'public'
DIST = UI / 'dist'

if DIST.exists():
    shutil.rmtree(DIST)
(DIST / 'assets').mkdir(parents=True, exist_ok=True)

for sub in ['ui', 'legacy', 'lib']:
    shutil.copytree(SRC / sub, DIST / 'assets' / sub, dirs_exist_ok=True)
shutil.copy2(SRC / 'main.js', DIST / 'assets' / 'main.js')

parts = []
for name in ['base.css', 'layout.css', 'layout.mobile.css', 'components.css', 'chat.css', 'config.css']:
    parts.append((SRC / 'styles' / name).read_text(encoding='utf-8'))
(DIST / 'assets' / 'styles.css').write_text('\n\n'.join(parts), encoding='utf-8')

if PUBLIC.exists():
    for item in PUBLIC.iterdir():
        target = DIST / item.name
        if item.is_dir():
            shutil.copytree(item, target, dirs_exist_ok=True)
        else:
            shutil.copy2(item, target)

(DIST / 'index.html').write_text('''<!DOCTYPE html>
<html lang="en" data-theme="ceo" data-theme-mode="dark">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>ClawTasker CEO Console</title>
    <link rel="stylesheet" href="/assets/styles.css">
  </head>
  <body>
    <clawtasker-app></clawtasker-app>
    <script type="module" src="/assets/main.js"></script>
  </body>
</html>
''', encoding='utf-8')
