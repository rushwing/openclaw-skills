# OpenClaw — Hooks

## What is a Hook?

An event-driven automation script that fires on Gateway/agent lifecycle events.
Unlike plugins, hooks are lightweight and focused on a single event handler.

## Hook Structure

```
my-hook/
├── HOOK.md        # Metadata (YAML frontmatter) + documentation
└── handler.ts     # TypeScript handler implementation
```

### HOOK.md Metadata

```markdown
---
name: my-hook
description: "What this hook does"
metadata:
  {
    "openclaw": {
      "emoji": "💾",
      "events": ["command:new", "message:received"],
      "requires": {
        "bins": ["node"],
        "env": ["API_KEY"]
      }
    }
  }
---
```

## Discovery Precedence (highest → lowest)

1. **Workspace hooks**: `<workspace>/hooks/` — per-agent, highest priority
2. **Managed hooks**: `~/.openclaw/hooks/` — user-installed, shared
3. **Bundled hooks**: shipped with OpenClaw

## Event Types

### Command Events
| Event | Fires When |
|-------|-----------|
| `command:new` | User sends `/new` |
| `command:reset` | User sends `/reset` |
| `command:stop` | User sends `/stop` |

### Agent Events
| Event | Fires When |
|-------|-----------|
| `agent:bootstrap` | Before workspace bootstrap |

### Gateway Events
| Event | Fires When |
|-------|-----------|
| `gateway:startup` | After channels start |

### Message Events
| Event | Fires When |
|-------|-----------|
| `message:received` | Inbound message received |
| `message:sent` | Outbound message sent |

## Handler Example

```typescript
import type { HookHandler } from "openclaw";

const handler: HookHandler = async (event) => {
  if (event.type !== "command" || event.action !== "new") return;

  console.log(`[my-hook] Session: ${event.sessionKey}`);
  event.messages.push("✨ Hook executed!");
};

export default handler;
```

## Installation

```bash
openclaw hooks install @acme/my-hooks   # From npm
openclaw hooks list                      # List hooks
openclaw hooks enable session-memory     # Enable a hook
openclaw hooks check                     # Check status
```

## Bundled Hooks

| Hook | Trigger | Description |
|------|---------|-------------|
| `session-memory` | `command:new` | Save session context to workspace memory |
| `bootstrap-extra-files` | `agent:bootstrap` | Inject extra workspace files |
| `command-logger` | All commands | Log to `~/.openclaw/logs/commands.log` |
| `boot-md` | `gateway:startup` | Run `BOOT.md` on gateway start |

## Custom Hooks in This Repo

See `../hooks/` directory for owner's custom hooks.
