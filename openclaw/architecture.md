# OpenClaw — Architecture

## High-Level Diagram

```
WhatsApp / Telegram / Slack / Discord / Google Chat / Signal
iMessage / BlueBubbles / Microsoft Teams / Matrix / WebChat
                         ↓
              ┌─────────────────────┐
              │      Gateway        │  ws://127.0.0.1:18789
              │  (control plane)    │  (single source of truth)
              └──────────┬──────────┘
                         │
         ┌───────────────┼───────────────┐
         ↓               ↓               ↓
   Pi Agent (RPC)    CLI (openclaw)   WebChat UI
   macOS App         iOS / Android nodes
```

## Gateway

The single WebSocket control plane. Everything connects here.

**Responsibilities**:
- Maintain provider connections (Baileys for WhatsApp, grammY for Telegram, etc.)
- Route inbound messages to agents
- Manage sessions (global or per-agent)
- Expose typed WebSocket API to clients
- Handle cross-channel routing, chunking, retry
- Host Canvas HTTP server
- Run cron jobs, webhooks, Gmail Pub/Sub

**Default bind**: `127.0.0.1:18789` (configurable)

## Agent Runtime

Agents run in **RPC mode** over WebSocket to Gateway.

- Tool streaming + block streaming supported
- Session model: `main` (direct chat), `group` (isolated), `channel`, `automation`
- Reply-back ping-pong mechanism between sessions

## Session Model

| Type | Description | Tool Access |
|------|-------------|-------------|
| `main` | Direct DM chat | Full host access |
| `group` | Group chat isolation | Configurable (can sandbox) |
| `channel` | Channel-specific | Configurable |
| `automation` | Cron/webhook triggered | Configurable |

**Session features**:
- Per-session token-limited context
- Activation modes: `mention` | `always`
- Queue modes: `sequential` | `parallel`
- Automatic pruning of old sessions

## Nodes (Device Clients)

Device-side runtimes that connect to Gateway over WebSocket.

**Platforms**: macOS, iOS, Android, headless

**Capabilities**:
- Canvas (A2UI host)
- `camera.snap` / `camera.clip`
- `screen.record`
- `location.get`
- `notifications`
- `system.run` (macOS only)
- `system.notify`

## Multi-Agent Routing

```json5
{
  agents: {
    main: { workspace: "~/.openclaw/workspace" },
    design: { workspace: "~/.openclaw/workspace-design" }
  },
  routing: {
    whatsapp: {
      "supportNumber": "agent:support",
      "*": "agent:main"
    }
  }
}
```

## Security Model

| Context | Default |
|---------|---------|
| `main` session | Tools run on host (full access) |
| Non-main sessions | Can be sandboxed in Docker |

```json5
{
  agents: {
    defaults: {
      sandbox: {
        mode: "non-main"   // Sandbox all non-main sessions
      }
    }
  }
}
```

## First-Class Tools

| Tool | Description |
|------|-------------|
| `browser` | Dedicated Chrome/Chromium with CDP control |
| `canvas` | A2UI push/reset/eval/snapshot |
| `nodes` | Camera, screen, location, notifications |
| `cron` | Scheduled jobs |
| `webhooks` | External HTTP triggers |
| `sessions_list` | Discover active sessions |
| `sessions_history` | Get session transcript |
| `sessions_send` | Message another session |

## Tool Schema Guardrails (for plugin/skill devs)

- No `Type.Union` (avoid anyOf/oneOf/allOf)
- Use `stringEnum`/`optionalStringEnum` for string lists
- Top-level schema: `type: "object"` with `properties`
- Avoid raw `format` property names
