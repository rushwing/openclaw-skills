# OpenClaw — Plugins

## What is a Plugin?

A trusted TypeScript module running **in-process** with Gateway that can extend:
- Gateway RPC methods
- Gateway HTTP handlers
- Agent tools
- CLI commands
- Background services
- Config validation
- Skills (by listing `skills` dirs in manifest)
- Auto-reply commands

> **Security note**: Plugins run in-process with Gateway → treated as trusted code.
> Install only from trusted sources.

## Plugin Structure

```
my-plugin/
├── openclaw.plugin.json   # Manifest
├── index.ts               # Entry point
└── ...
```

### Manifest (`openclaw.plugin.json`)

```json
{
  "id": "voice-call",
  "configSchema": {
    "type": "object",
    "properties": {
      "provider": { "type": "string" }
    }
  },
  "uiHints": {
    "provider": {
      "label": "Provider",
      "placeholder": "twilio"
    }
  }
}
```

## Discovery Precedence (highest → lowest)

1. Config `plugins.load.paths`
2. Workspace extensions: `<workspace>/.openclaw/extensions/*.ts` or `*/index.ts`
3. Global extensions: `~/.openclaw/extensions/*.ts` or `*/index.ts`
4. Bundled extensions (disabled by default)

## Installation

```bash
openclaw plugins install @openclaw/voice-call   # From npm
openclaw plugins list                            # List installed
openclaw plugins enable <id>                     # Enable
openclaw plugins disable <id>                    # Disable
```

Install uses `npm install --ignore-scripts` (no lifecycle scripts run).

## Security Checks

Before loading, OpenClaw checks candidate paths for:
- Symlink / path traversal escapes
- World-writable directories
- Suspicious ownership (non-root plugins)

## openclaw.json Configuration

```json5
{
  plugins: {
    enabled: true,
    allow: ["voice-call"],              // Allowlist (optional)
    deny: ["untrusted"],               // Denylist (deny wins over allow)
    load: {
      paths: ["~/Projects/my-plugin"]  // Local dev paths
    },
    entries: {
      "voice-call": {
        enabled: true,
        config: { provider: "twilio" }
      }
    },
    slots: {
      memory: "memory-core"            // Exclusive slot: only one memory plugin
    }
  }
}
```

## Plugin Slots (Exclusive Categories)

Some plugin categories are mutually exclusive:

| Slot | Options |
|------|---------|
| `memory` | `memory-core` \| `memory-lancedb` \| `"none"` |

## Official Plugins

| Plugin | Description |
|--------|-------------|
| `@openclaw/msteams` | Microsoft Teams channel |
| `@openclaw/matrix` | Matrix channel |
| `@openclaw/zalo` | Zalo channel |
| `@openclaw/zalouser` | Zalo Personal channel |
| `@openclaw/voice-call` | Voice Call channel |
| `memory-core` | Built-in memory (bundled) |
| `memory-lancedb` | LanceDB-backed memory |

## Custom Plugins in This Repo

See `../plugins/` directory for owner's custom plugins.
