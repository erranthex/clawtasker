#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VERSION="$(cat "$ROOT/VERSION" | tr -d '[:space:]')"
SAFE_VERSION="${VERSION//./_}"
SAFE_VERSION="${SAFE_VERSION//-/_}"
NAME="clawtasker_ceo_console_v${SAFE_VERSION}"
OUT_DIR="${1:-$ROOT/..}"
ZIP_PATH="$OUT_DIR/${NAME}.zip"

cd "$ROOT"
python3 scripts/adapt_pocket_office_release.py
python3 scripts/build_static_ui.py
python3 docs/build_guide.py
python3 -m py_compile server.py
python3 -m unittest discover -s tests -v
node --test ui/tests/*.test.mjs
bash scripts/smoke_test.sh

TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT
mkdir -p "$TMPDIR/$NAME"
rsync -a --delete \
  --exclude='.git' \
  --exclude='__pycache__' \
  --exclude='.DS_Store' \
  --exclude='*.pyc' \
  "$ROOT/" "$TMPDIR/$NAME/"
(
  cd "$TMPDIR"
  zip -qr "$ZIP_PATH" "$NAME"
)
echo "Created $ZIP_PATH"
