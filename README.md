# everything_openclaw

Personal OpenClaw hub: knowledge base, custom skills, MCP servers, plugins,
hooks, and persona presets.

> **For AI assistants**: Read `CLAUDE.md` first, then `openclaw/OVERVIEW.md`
> for key concepts. Drill into `openclaw/*.md` as needed.

## What's Here

| Directory | Contents |
|-----------|----------|
| `openclaw/` | Extracted OpenClaw knowledge docs (architecture, skills, plugins, hooks, MCP, deployment…) |
| `personas/` | Custom SOUL.md / AGENTS.md / IDENTITY.md presets for different deployments |
| `skills/` | Custom skills installable by OpenClaw |
| `mcps/` | Custom MCP server projects |
| `plugins/` | Custom OpenClaw plugins/extensions |
| `hooks/` | Custom OpenClaw event hooks |

## Custom Skills

| Skill | Description | Requires |
|-------|-------------|---------|
| 📚 `github-kb` | GitHub knowledge base manager — local repo index with one-line summaries in `CLAUDE.md`, offline-first exploration before live queries | `gh` CLI |
| 🎓 `tutor` | One-on-one tutoring (math/physics/chemistry) — analyzes problem photos, generates Chinese HTML explanations, optionally produces narrated Manim animation videos | `manim`, `ffmpeg`, `edge-tts` |
| 💻 `kids-coding` | Children's programming coach — generates Mermaid flowcharts + HTML solution steps, optionally algorithm animation videos | `manim`, `ffmpeg`, `edge-tts` |

## OpenClaw Knowledge Base (`openclaw/`)

Progressive disclosure — start from the top, go deeper as needed:

| File | Topic |
|------|-------|
| [OVERVIEW.md](openclaw/OVERVIEW.md) | What OpenClaw is, key concepts, glossary |
| [architecture.md](openclaw/architecture.md) | Gateway, channels, nodes, session model, tools |
| [skills.md](openclaw/skills.md) | Skill structure, loading precedence, gating, config |
| [plugins.md](openclaw/plugins.md) | Plugin types, discovery, security, config |
| [hooks.md](openclaw/hooks.md) | Hook events, structure, handler examples |
| [mcp.md](openclaw/mcp.md) | MCP integration via mcporter |
| [workspace.md](openclaw/workspace.md) | Workspace file layout (AGENTS/SOUL/TOOLS…) |
| [channels.md](openclaw/channels.md) | Supported channels, DM policy, group config |
| [deployment.md](openclaw/deployment.md) | Local / Docker / Tailscale / Raspberry Pi |
| [commands.md](openclaw/commands.md) | Chat commands (/new, /think, /compact…) |

## Why This Repo?

When developing OpenClaw skills, MCPs, plugins, or hooks, load this repo as
context (via CLAUDE.md or github-kb skill) to get the essential OpenClaw
knowledge without pasting docs into every conversation.

The `personas/` directory lets you version-control your agent's identity files
and easily restore them when setting up a new OpenClaw instance.
