# NornWeave Skills

This folder contains official LLM skills for NornWeave that can be installed on AI coding assistants and agents that support the AgentSkills format.

## Compatible Tools

These skills work with:

- **Cursor** - Add to `.cursor/skills/` in your project or `~/.cursor/skills/` globally
- **Claude Code** - Install via the skills system
- **Codex** - Add to `$CODEX_HOME/skills/`
- **Moltbot** - Compatible with the AgentSkills format
- **Other tools** - Any AI assistant supporting the SKILL.md format

## Available Skills

| Skill | Description |
|-------|-------------|
| [nornweave-api](nornweave-api/SKILL.md) | Instructions for calling NornWeave REST APIs to manage inboxes, send/receive messages, and search threads |

## Installation

### Using npx (Recommended)

The easiest way to install skills is using the `npx skills` [CLI](https://skills.sh/):

```bash
# List available skills in this repository
npx skills add DataCovey/nornweave --list

# Install a specific skill
npx skills add DataCovey/nornweave --skill nornweave-api

# Install multiple skills at once
npx skills add DataCovey/nornweave --skill nornweave-api --skill another-skill
```

### Cursor

Copy the skill folder to your Cursor skills directory:

```bash
# Project-level (recommended)
cp -r skills/nornweave-api /path/to/your-project/.cursor/skills/

# Or global installation
cp -r skills/nornweave-api ~/.cursor/skills/
```

### Claude Code / Codex

```bash
# Using the skill installer
# (from within Claude Code or Codex)
install skill from github.com/yourusername/nornweave/skills/nornweave-api
```

### Manual Installation

1. Copy the skill folder to your AI tool's skills directory
2. Ensure the `SKILL.md` file is at the root of the skill folder
3. Reference files in `references/` are automatically available

## Skill Format

Each skill follows the AgentSkills format:

```
skill-name/
├── SKILL.md          # Main skill file with frontmatter and instructions
└── references/       # Optional additional documentation
    ├── webhooks.md
    └── other-docs.md
```

### SKILL.md Frontmatter

```yaml
---
name: skill-name
description: Short description of when to use this skill
---
```

The description helps AI tools determine when to automatically activate the skill.

## Creating New Skills

To contribute a new skill:

1. Create a new folder under `skills/`
2. Add a `SKILL.md` with frontmatter and comprehensive instructions
3. Include code examples in multiple languages where applicable
4. Add reference files for complex topics (webhooks, advanced config, etc.)
5. Submit a PR with your skill

See [nornweave-api](nornweave-api/SKILL.md) as a reference implementation.
