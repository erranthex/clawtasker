# GitHub workflow for ClawTasker teams

ClawTasker does not require live GitHub API integration to be useful, but it is designed to fit a simple GitHub workflow:

1. Create or link a task in ClawTasker.
2. Create a branch per task:
   - `agent/<agent>/<task-id>-<slug>`
3. Do the work in the shared project repository.
4. Open a pull request and link the task / issue.
5. Move the task to **Validation** when the branch is ready for review.
6. Merge after validation and move the task to **Done**.

## Recommended conventions

- Use one repository per product or project when you want strong separation.
- Keep shared playbooks and templates in a separate read-only repo or shared folder.
- Protect `main` (or `trunk`) with required reviews and status checks.
- Use `git worktree` when multiple specialists need parallel branches in the same repo.
- Let the chief agent manage priorities and blockers, not every commit.

## Helper script

Inside any Git repo, use:

```bash
scripts/git_task_flow.sh branch codex T-203 agent-and-project-filters main
```

Or create a worktree:

```bash
scripts/git_task_flow.sh worktree ../wt-codex codex T-203 agent-and-project-filters main
```

## What is not included

This package does **not** include live GitHub API synchronization or automatic PR creation. It provides the task model, branch naming conventions, and shared-project workspace pattern so you can connect those pieces in your own environment.
