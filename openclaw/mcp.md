# OpenClaw — MCP Integration

## How OpenClaw Supports MCP

OpenClaw integrates Model Context Protocol (MCP) via **mcporter**
(by Stefan Steinberger) as a **bridge model**, not a first-class runtime.

## Why Bridge vs. First-Class?

| Approach | Tradeoff |
|----------|----------|
| **Bridge (current)** | Flexible: add/modify MCP servers without Gateway restart. Core stays lean. MCP churn doesn't break stability. |
| First-class runtime | Tighter integration, but every MCP spec change requires a Gateway update. |

## Key Characteristics

- MCP servers can be **dynamically added or removed** without restarting Gateway
- Core tool surface remains minimal and stable
- MCP-related issues are isolated from core runtime

## Adding an MCP Server

MCP configuration is managed through the standard `openclaw.json` config.
Refer to the official docs for current MCP config schema, as it evolves
with mcporter versions.

## Custom MCPs in This Repo

See `../mcps/` directory for owner's custom MCP server projects.
Each MCP project should include a `README.md` explaining:
- What service/capability it exposes
- How to install and configure it
- Any required environment variables
