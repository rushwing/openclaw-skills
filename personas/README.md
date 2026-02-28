# Personas & Memory Presets

This directory stores the owner's custom OpenClaw workspace identity files.
These are the files that define *who* the agent is on specific deployments
(e.g., the Raspberry Pi instance).

## What Goes Here

Each subdirectory is a named preset (e.g., `pi-default/`, `home-assistant/`).
A preset is a collection of any of these workspace files:

| File | Purpose |
|------|---------|
| `AGENTS.md` | Agent system prompt — capabilities, behavior rules |
| `SOUL.md` | Personality — tone, style, values, character |
| `IDENTITY.md` | Owner identity — name, timezone, preferences |
| `USER.md` | Custom user context section |
| `BOOTSTRAP.md` | Startup instructions |
| `TOOLS.md` | Tool usage instructions |
| `memory/` | Pre-seeded memory snapshots |

## Suggested Structure

```
personas/
├── README.md              # This file
├── pi-default/            # Main persona on Raspberry Pi
│   ├── AGENTS.md
│   ├── SOUL.md
│   └── IDENTITY.md
├── home-assistant/        # Variant for home automation context
│   ├── SOUL.md
│   └── AGENTS.md
└── minimal/               # Stripped-down persona for testing
    └── AGENTS.md
```

## How to Use

### Apply a preset to a workspace:

```bash
# Copy files to your workspace (merge, don't replace everything)
cp personas/pi-default/SOUL.md ~/.openclaw/workspace/SOUL.md
cp personas/pi-default/AGENTS.md ~/.openclaw/workspace/AGENTS.md
cp personas/pi-default/IDENTITY.md ~/.openclaw/workspace/IDENTITY.md
```

### Or symlink for live-sync:

```bash
ln -sf ~/Dev/everything_openclaw/personas/pi-default/SOUL.md \
       ~/.openclaw/workspace/SOUL.md
```

## Notes

- Keep sensitive personal information out of git. Use `.gitignore` to exclude
  files with private data if needed.
- SOUL.md and AGENTS.md are safe to commit (they define behavior, not secrets).
- IDENTITY.md may contain personal info — review before committing.
