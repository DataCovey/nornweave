---
name: /release
id: release
category: Release
description: Release a new version — updates CHANGELOG, pyproject.toml, creates git tag, and pushes
model: fast
---

Create a new release for NornWeave.

**Input**: The user MUST provide a version number (e.g., `/release 0.1.5`). If no version is provided, use the **AskQuestion tool** to prompt for it. Show the current version from `pyproject.toml` as context in the prompt.

**Steps**

1. **Validate the version number**

   - Read `pyproject.toml` and extract the current version
   - Confirm the new version is different from the current one
   - Confirm the new version follows semver (e.g., `0.1.5`, `1.0.0`)
   - If invalid, ask for a corrected version

2. **Update `pyproject.toml`**

   Replace the `version = "..."` line with the new version number.

3. **Update `CHANGELOG.md`**

   - Read the current `CHANGELOG.md`
   - Move everything under `## [Unreleased]` into a new `## [<version>] - <today's date YYYY-MM-DD>` section
   - Insert a fresh empty `## [Unreleased]` section at the top with placeholder subsections (Added, Changed, Deprecated, Removed, Fixed, Security — each with `- (None yet)`)
   - Update the comparison links at the bottom of the file:
     - Change `[Unreleased]` link to compare from the new tag: `v<version>...HEAD`
     - Add a new link for the version: `v<previous>...v<version>`

4. **Commit, tag, and push**

   Run these commands sequentially:

   ```bash
   git add pyproject.toml CHANGELOG.md
   git commit -m "chore: release <version>"
   git tag -a v<version> -m "Release <version>"
   git push origin main
   git push origin v<version>
   ```

5. **Show summary**

   Display:
   - Previous version → new version
   - Commit hash
   - Tag name
   - Confirm push succeeded
   - Link to the GitHub releases page: `https://github.com/DataCovey/nornweave/releases/tag/v<version>`

**Guardrails**
- Always validate the version number before making any changes
- Never skip the `pyproject.toml` update
- If the `## [Unreleased]` section has no meaningful entries (only `- (None yet)` placeholders), warn the user and ask for confirmation before proceeding
- If the tag already exists locally or on the remote, warn and ask how to proceed (delete and recreate, or abort)
- Do not amend existing commits — always create a fresh commit
