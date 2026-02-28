# everything_openclaw — AI Context Guide

This repo is the owner's personal OpenClaw hub: extracted knowledge docs,
custom skills, MCP servers, plugins, hooks, and persona/memory presets.

## What is OpenClaw?

OpenClaw is a **multi-channel, local-first personal AI assistant framework**.
Core idea: one Gateway (WebSocket control plane) connects multiple messaging
channels (WhatsApp, Telegram, Slack, Discord, iMessage…) and routes them to
LLM agents running in workspaces on the user's own hardware.

Key tagline: "The AI that actually does things — on your device, your channels,
your rules."

## Repo Layout

```
everything_openclaw/
├── openclaw/        # Extracted OpenClaw knowledge (read this for context)
│   ├── OVERVIEW.md       # What OpenClaw is + key concepts glossary
│   ├── architecture.md   # Gateway, channels, nodes, session model
│   ├── skills.md         # Skill system: structure, loading, gating
│   ├── plugins.md        # Plugin system: types, discovery, config
│   ├── hooks.md          # Hook system: events, structure, examples
│   ├── mcp.md            # MCP integration via mcporter
│   ├── workspace.md      # Workspace file layout (AGENTS/SOUL/TOOLS…)
│   ├── channels.md       # Supported channels + config patterns
│   ├── deployment.md     # Local / Docker / Tailscale / Pi setup
│   └── commands.md       # Chat commands reference (/new, /think…)
├── personas/        # Persona + memory presets (SOUL.md, AGENTS.md, etc.)
├── skills/          # Custom skills installable by OpenClaw
├── mcps/            # Custom MCP server projects
├── plugins/         # Custom OpenClaw plugins/extensions
└── hooks/           # Custom OpenClaw hooks
```

## Quick Facts for Skill/MCP/Plugin/Hook Development

- **Skills**: directory with `SKILL.md` (YAML frontmatter + Markdown).
  Loading precedence: workspace > managed (`~/.openclaw/skills/`) > bundled.
- **Plugins**: in-process TypeScript modules. Install via `openclaw plugins install`.
  Can add RPC methods, HTTP handlers, agent tools, CLI commands, background services.
- **Hooks**: event-driven scripts. Events: `command:new|reset|stop`, `agent:bootstrap`,
  `gateway:startup`, `message:received|sent`.
- **MCP**: bridged via mcporter — dynamic, no Gateway restart needed.
- **Workspace files**: `AGENTS.md` (system prompt), `SOUL.md` (personality),
  `TOOLS.md` (tool instructions), `IDENTITY.md` (user identity), `BOOTSTRAP.md`.
- **Config file**: `openclaw.json` — controls skills, plugins, hooks, channels, agents.

## Read More

For detailed context, see `openclaw/OVERVIEW.md` first, then drill into
specific topic files as needed.
