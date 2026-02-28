# Custom Hooks

Custom OpenClaw event-driven hooks.

## Structure

```
hooks/
├── README.md         # This file
└── <hook-name>/
    ├── HOOK.md       # Metadata (YAML frontmatter) + docs
    └── handler.ts    # TypeScript handler
```

## Installing a Hook from This Repo

```bash
# Copy to managed hooks directory (shared across agents)
cp -r hooks/my-hook ~/.openclaw/hooks/

# Or copy to workspace hooks (per-agent, highest precedence)
cp -r hooks/my-hook ~/.openclaw/workspace/hooks/

# Enable it
openclaw hooks enable my-hook
```

## Hook Events Quick Reference

| Event | Trigger |
|-------|---------|
| `command:new` | `/new` command |
| `command:reset` | `/reset` command |
| `command:stop` | `/stop` command |
| `agent:bootstrap` | Before workspace bootstrap |
| `gateway:startup` | After channels start |
| `message:received` | Inbound message |
| `message:sent` | Outbound message |

See `../openclaw/hooks.md` for full hook development reference.
