# Custom MCP Servers

Custom Model Context Protocol servers for OpenClaw.

## Structure

Each subdirectory is a standalone MCP server project:

```
mcps/
├── README.md         # This file
└── <server-name>/
    ├── README.md     # What this MCP exposes, setup instructions
    ├── index.ts      # Entry point (or main.py for Python)
    └── ...
```

## OpenClaw MCP Integration

OpenClaw integrates MCP via **mcporter** as a bridge. Key benefit:
MCP servers can be added/removed without restarting the Gateway.

See `../openclaw/mcp.md` for integration details.

## Creating a New MCP Server

Refer to the `example-skills:mcp-builder` skill for guided MCP server creation.
