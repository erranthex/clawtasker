#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
ClawTasker Git task flow helper

Usage:
  scripts/git_task_flow.sh branch <agent> <task_id> <slug> [base_branch]
  scripts/git_task_flow.sh worktree <path> <agent> <task_id> <slug> [base_branch]

Examples:
  scripts/git_task_flow.sh branch codex T-203 agent-and-project-filters main
  scripts/git_task_flow.sh worktree ../wt-codex codex T-203 agent-and-project-filters main

Notes:
- Run this inside a Git repository.
- Branch naming format: agent/<agent>/<task_id>-<slug>
- Use GitHub Issues/PRs/Projects to track increments; this script only helps local Git flow.
EOF
}

slugify() {
  printf '%s' "$1" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//'
}

require_git_repo() {
  git rev-parse --is-inside-work-tree >/dev/null 2>&1 || {
    echo "error: run this inside a Git repository" >&2
    exit 1
  }
}

make_branch_name() {
  local agent="$1"
  local task_id="$2"
  local slug="$3"
  printf 'agent/%s/%s-%s' "$(slugify "$agent")" "$(slugify "$task_id")" "$(slugify "$slug")"
}

create_branch() {
  local agent="$1"
  local task_id="$2"
  local slug="$3"
  local base_branch="${4:-main}"
  local branch_name
  branch_name="$(make_branch_name "$agent" "$task_id" "$slug")"

  git fetch origin "$base_branch" >/dev/null 2>&1 || true
  git checkout "$base_branch"
  git pull --ff-only origin "$base_branch" >/dev/null 2>&1 || true
  git checkout -b "$branch_name"
  echo "created and checked out: $branch_name"
}

create_worktree() {
  local path="$1"
  local agent="$2"
  local task_id="$3"
  local slug="$4"
  local base_branch="${5:-main}"
  local branch_name
  branch_name="$(make_branch_name "$agent" "$task_id" "$slug")"

  git fetch origin "$base_branch" >/dev/null 2>&1 || true
  git worktree add -b "$branch_name" "$path" "$base_branch"
  echo "created worktree: $path"
  echo "branch: $branch_name"
}

main() {
  if [ "$#" -lt 1 ]; then
    usage
    exit 1
  fi

  require_git_repo

  case "$1" in
    branch)
      if [ "$#" -lt 4 ] || [ "$#" -gt 5 ]; then
        usage
        exit 1
      fi
      create_branch "$2" "$3" "$4" "${5:-main}"
      ;;
    worktree)
      if [ "$#" -lt 5 ] || [ "$#" -gt 6 ]; then
        usage
        exit 1
      fi
      create_worktree "$2" "$3" "$4" "$5" "${6:-main}"
      ;;
    -h|--help|help)
      usage
      ;;
    *)
      echo "error: unknown command: $1" >&2
      usage
      exit 1
      ;;
  esac
}

main "$@"
