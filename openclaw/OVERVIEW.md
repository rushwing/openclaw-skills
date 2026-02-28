# OpenClaw — Overview

> Level 1: What OpenClaw is and key concepts. For deeper details, see the
> sibling files in this directory.

## What is OpenClaw?

OpenClaw is a **multi-channel, local-first personal AI assistant**.

- Runs on your own hardware (Raspberry Pi, Mac, Linux server, Docker)
- Connects to messaging channels you already use (WhatsApp, Telegram, Slack…)
- Orchestrates LLM calls with tools, skills, plugins, and hooks
- No cloud dependency — Gateway is a local WebSocket process

**History**: Warelay → Clawdbot → Moltbot → OpenClaw

## Core Architecture (one-line each)

| Component | Role |
|-----------|------|
| **Gateway** | Single WebSocket control plane (`127.0.0.1:18789`). Manages sessions, channels, tools, events. |
| **Agent** | LLM conversation thread. Has a workspace, memory, skills. |
| **Workspace** | Per-agent directory with `AGENTS.md`, `SOUL.md`, `skills/`, `hooks/`, `sessions/`, `memory/`. |
| **Skill** | `SKILL.md` + optional scripts. Injected into agent system prompt. |
| **Plugin** | TypeScript module running in-process with Gateway. Extends RPC/tools/CLI/skills. |
| **Hook** | Event-driven script. Fires on commands, gateway startup, message events. |
| **Node** | Device-side runtime (macOS/iOS/Android). Handles camera, screen, notifications. |
| **Canvas** | Agent-editable HTML/CSS/JS visualisation surface. |
| **MCP** | Bridged via mcporter. Dynamic addition of MCP servers without restart. |
| **Channel** | Messaging provider integration (WhatsApp/Telegram/Slack/Discord/iMessage…). |

## Key Concepts Glossary

**Session** — An LLM conversation context. Types: `main` (direct chat, full tool access), `group` (channel group isolation), `channel`, `automation` (cron/webhook).

**Skills loading precedence** (highest → lowest):
1. Workspace skills: `<workspace>/skills/<skill>/`
2. Managed/local: `~/.openclaw/skills/<skill>/`
3. Bundled: shipped with OpenClaw

**Plugin discovery precedence**:
1. Config `plugins.load.paths`
2. Workspace extensions: `<workspace>/.openclaw/extensions/`
3. Global extensions: `~/.openclaw/extensions/`
4. Bundled (disabled by default)

**ClawHub** — Public skill registry at https://clawhub.com.
Install: `clawhub install <slug>`, update: `clawhub update --all`.

## Supported Channels

**Built-in**: WhatsApp (Baileys), Telegram (grammY), Slack (Bolt), Discord (discord.js), Google Chat, Signal (signal-cli), BlueBubbles/iMessage, WebChat (browser)

**Plugin**: Microsoft Teams, Matrix, Zalo, Zalo Personal, Voice Call

## What This Repo Contains

- `openclaw/` — Knowledge extracted from official docs (you are here)
- `personas/` — Owner's custom SOUL.md, AGENTS.md, IDENTITY.md presets
- `skills/` — Custom skills for installation
- `mcps/` — Custom MCP server projects
- `plugins/` — Custom plugin/extension code
- `hooks/` — Custom hook scripts

## Further Reading

| Topic | File |
|-------|------|
| Architecture deep-dive | [architecture.md](architecture.md) |
| Skills system | [skills.md](skills.md) |
| Plugins | [plugins.md](plugins.md) |
| Hooks | [hooks.md](hooks.md) |
| MCP integration | [mcp.md](mcp.md) |
| Workspace structure | [workspace.md](workspace.md) |
| Channels & config | [channels.md](channels.md) |
| Deployment (Pi/Docker/Tailscale) | [deployment.md](deployment.md) |
| Chat commands | [commands.md](commands.md) |
