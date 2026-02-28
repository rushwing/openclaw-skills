# Custom Plugins

Custom OpenClaw plugins/extensions.

## Structure

```
plugins/
├── README.md         # This file
└── <plugin-name>/
    ├── openclaw.plugin.json   # Plugin manifest
    ├── index.ts               # Entry point
    └── README.md              # What it does, how to install
```

## Installing a Plugin from This Repo

```bash
# Point OpenClaw to this directory
# In openclaw.json:
{
  plugins: {
    load: {
      paths: ["~/Dev/everything_openclaw/plugins/my-plugin"]
    }
  }
}
```

## Plugin Capabilities

Plugins can extend:
- Gateway RPC methods
- Gateway HTTP handlers
- Agent tools
- CLI commands
- Background services
- Config validation
- Skills (by listing `skills` dirs in manifest)
- Auto-reply commands

See `../openclaw/plugins.md` for full plugin development reference.
