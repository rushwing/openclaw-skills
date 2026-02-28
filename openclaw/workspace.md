# OpenClaw — Workspace Structure

## What is a Workspace?

A per-agent directory that defines the agent's identity, personality, tools,
skills, hooks, sessions, and memory.

Default workspace: `~/.openclaw/workspace/`

## Standard Workspace Layout

```
~/.openclaw/workspace/
├── AGENTS.md          # Agent system prompt (who the agent is, capabilities)
├── SOUL.md            # Agent personality (tone, style, values)
├── TOOLS.md           # Tool instructions (how to use tools, injected as context)
├── BOOTSTRAP.md       # Startup instructions (run on agent init)
├── IDENTITY.md        # Owner/user identity (name, preferences, context)
├── USER.md            # Custom user section (freeform)
├── skills/            # Workspace-level skills (highest precedence)
│   ├── my-skill/
│   │   └── SKILL.md
│   └── ...
├── hooks/             # Per-agent hooks (highest precedence)
│   ├── my-hook/
│   │   ├── HOOK.md
│   │   └── handler.ts
│   └── ...
├── sessions/          # Session transcripts (.jsonl files)
├── memory/            # Session memory snapshots
└── tools/             # Downloaded tool binaries
```

## Key Files Explained

### AGENTS.md
The agent's system prompt. Defines:
- Who the agent is
- What capabilities it has
- How it should behave in specific contexts
- Agent-to-agent coordination rules

### SOUL.md
Personality layer injected into system prompt:
- Communication tone and style
- Values and principles
- Quirks and character traits
- Language preferences (e.g., Chinese/English mix)

### TOOLS.md
Instructions for tool usage. Injected as context when tools are available:
- When and how to use each tool
- Tool-specific guidelines and restrictions

### IDENTITY.md
User/owner identity information:
- Name, timezone, location
- User preferences and context
- Background relevant to the agent

### BOOTSTRAP.md
Runs on agent initialization:
- Startup checks
- Environment setup instructions
- Initial context loading

## Multiple Agents / Workspaces

```json5
{
  agents: {
    main: { workspace: "~/.openclaw/workspace" },
    design: { workspace: "~/.openclaw/workspace-design" },
    qa: { workspace: "~/.openclaw/workspace-qa" }
  }
}
```

## Personas in This Repo

The `../personas/` directory contains the owner's persona presets:
ready-to-use or reference versions of SOUL.md, AGENTS.md, IDENTITY.md, etc.

These can be copied to a workspace or used as templates when setting up
a new OpenClaw instance (e.g., on a new Raspberry Pi).
