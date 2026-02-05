---
name: /commit-push
id: commit-push
category: Git
description: Commit and push all changes from this chat session using Conventional Commits
model: fast
---

Commit and push all changes made during this chat session to the current branch.

**Steps**

1. **Gather context** (run these in parallel)

   - `git status` — list all staged, unstaged, and untracked files
   - `git diff` and `git diff --cached` — see what changed
   - `git log --oneline -10` — recent commits for style reference
   - `git branch --show-current` — current branch name

2. **Stage relevant files**

   - Stage all modified and new files that were part of the work in this session
   - Do NOT stage files that are clearly unrelated to the session (e.g., editor configs, OS files)
   - Do NOT stage files that likely contain secrets (`.env`, credentials, tokens)
   - If unsure whether a file should be included, ask the user

3. **Craft the commit message**

   Follow [Conventional Commits](https://www.conventionalcommits.org/) strictly:

   - **Type**: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`, `ci`, `build`, `style`
   - **Scope** (optional): module or area affected, e.g. `feat(verdandi): ...`
   - **Subject**: imperative mood, lowercase, no period, ≤72 chars
   - **Body** (if needed): blank line after subject, wrap at 100 chars, explain *why* not *what*
   - **Breaking changes**: add `!` after type/scope and a `BREAKING CHANGE:` footer

   If the session touched multiple unrelated areas, create **separate commits** — one per logical change — rather than a single catch-all commit.

4. **Commit and push**

   ```bash
   git add <files>
   git commit -m "<message>"
   git push origin <current-branch>
   ```

   - If the branch has no upstream yet, use `git push -u origin <current-branch>`
   - If push is rejected (e.g., behind remote), do `git pull --rebase` first, then retry the push. Never force-push.

5. **Show summary**

   Display:
   - Branch name
   - Commit hash(es) and message(s)
   - Files changed count
   - Confirm push succeeded

**Guardrails**
- Never force-push (`--force` or `--force-with-lease`)
- Never push to `main` or `master` directly — warn the user and ask for confirmation first
- Never commit files that look like secrets (`.env`, `*credentials*`, `*secret*`, `*.pem`, `*.key`)
- Never amend existing commits — always create fresh commits
- Never skip the `git status` / `git diff` inspection step
- If there are no changes to commit, tell the user and stop
