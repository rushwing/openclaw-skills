# OpenClaw — Skills System

## What is a Skill?

A directory containing:
- `SKILL.md` — YAML frontmatter metadata + Markdown instructions
- Optional scripts, assets, data files

The content is injected into the agent's system prompt when the skill is active.

## Directory Structure

```
my-skill/
├── SKILL.md          # Required: metadata + instructions
├── scripts/          # Optional: helper scripts
└── assets/           # Optional: templates, data files
```

## SKILL.md Frontmatter

```markdown
---
name: my-skill
description: "One-line description shown in skill list"
metadata:
  {
    "openclaw": {
      "always": false,              // Always include (skip gates)
      "emoji": "🔨",
      "homepage": "https://...",
      "os": ["darwin", "linux"],    // Platform restriction
      "requires": {
        "bins": ["node", "git"],    // Required binaries in PATH
        "anyBins": ["python3", "python"],  // At least one
        "env": ["API_KEY"],         // Required env vars or config
        "config": ["browser.enabled"]     // openclaw.json config paths
      },
      "primaryEnv": "API_KEY"       // Env var linked to apiKey config
    }
  }
---

# Instructions for the agent...
```

## Loading Precedence (highest → lowest)

1. **Workspace skills**: `<workspace>/skills/<skill>/` — per-agent overrides
2. **Managed skills**: `~/.openclaw/skills/<skill>/` — shared across agents
3. **Bundled skills**: shipped with OpenClaw package

Same-name skills: workspace overrides managed, managed overrides bundled.

## Gating / Eligibility

A skill is included in the agent's context if:
- `always: true` in metadata, OR
- All `requires.bins` are found in PATH, AND
- All `requires.anyBins` have at least one match, AND
- All `requires.env` exist (as env var or openclaw.json config), AND
- All `requires.config` paths exist in config

Eligibility is snapshotted at session start for performance.

## Token Cost Estimate

- Base overhead (≥1 skill active): ~195 chars ≈ 49 tokens
- Per skill: ~97 + len(name) + len(description) + len(location) chars

## openclaw.json Configuration

```json5
{
  skills: {
    entries: {
      "my-skill": {
        enabled: true,
        apiKey: "MY_API_KEY",          // Maps to primaryEnv var
        env: {
          MY_API_KEY: "the-key-value"  // Or use env var name
        },
        config: {
          endpoint: "https://...",
          model: "nano-pro"
        }
      },
      "some-skill": { enabled: false } // Disable a skill
    },
    load: {
      watch: true,               // Auto-reload on file change
      watchDebounceMs: 250
    },
    allowBundled: ["skill1"]     // Allowlist for bundled skills
  }
}
```

## ClawHub (Public Registry)

```bash
clawhub install <skill-slug>     # Install from clawhub.com
clawhub update --all             # Update all managed skills
clawhub sync --all               # Sync metadata
```

## Sandbox Considerations

- `requires.bins` checked on host at load time
- If agent runs in Docker sandbox, binaries must exist inside container
- Install via `agents.defaults.sandbox.docker.setupCommand`

## Skills in This Repo

See `../skills/` directory. Each skill is a drop-in directory for:
- `~/.openclaw/skills/` (global install)
- `<workspace>/skills/` (per-agent install)
