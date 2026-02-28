# OpenClaw — Channels

## Built-in Channels

| Channel | Library | Notes |
|---------|---------|-------|
| WhatsApp | Baileys | Unofficial client |
| Telegram | grammY | Bot API |
| Slack | Bolt | App/Bot |
| Discord | discord.js | Bot |
| Google Chat | Chat API | Workspace |
| Signal | signal-cli | Requires Java |
| BlueBubbles | BlueBubbles server | Recommended for iMessage |
| iMessage | imsg (legacy) | macOS only |
| WebChat | Browser | Built-in web UI |

## Plugin Channels

| Channel | Package |
|---------|---------|
| Microsoft Teams | `@openclaw/msteams` |
| Matrix | `@openclaw/matrix` |
| Zalo | `@openclaw/zalo` |
| Zalo Personal | `@openclaw/zalouser` |
| Voice Call | `@openclaw/voice-call` |

## Channel Configuration Patterns

### DM Policy

```json5
{
  channels: {
    whatsapp: {
      dmPolicy: "pairing"   // Unknown senders need pairing code
    },
    telegram: {
      dmPolicy: "open",     // Open to allowlist
      allowlist: ["*"]      // "*" = anyone
    }
  }
}
```

### Group Management

```json5
{
  channels: {
    telegram: {
      groups: {
        "*": { requireMention: true },              // Default: require @bot
        "-1001234567890": { requireMention: false } // Specific group: always active
      }
    }
  }
}
```

### Message Chunking

Each channel has per-provider chunking rules respecting message size limits.
Default: 1 message per response for most providers.

## Gateway Exposure via Tailscale

```json5
{
  gateway: {
    tailscale: {
      mode: "off" | "serve" | "funnel"
      // serve = tailnet-only access
      // funnel = public internet access (requires password auth)
    },
    auth: {
      mode: "password"   // Required for funnel mode
    }
  }
}
```
