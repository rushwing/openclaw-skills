# OpenClaw — Deployment

## Installation

```bash
npm install -g openclaw@latest
openclaw onboard --install-daemon   # Interactive setup wizard
```

## Release Channels

| Channel | Tag | Description |
|---------|-----|-------------|
| `stable` | `latest` | Tagged releases (vYYYY.M.D) |
| `beta` | `beta` | Prereleases (vYYYY.M.D-beta.N) |
| `dev` | `dev` | Moving HEAD on `main` |

```bash
openclaw update --channel stable|beta|dev
```

## Deployment Options

### 1. Local (Recommended for Solo Users)

Gateway runs locally on macOS/Linux/Windows (WSL2).

```
macOS/Linux/Windows
└── Gateway (127.0.0.1:18789)
    ├── launchd / systemd user service (auto-start)
    └── All channels + WebChat accessible locally
```

### 2. Remote Gateway (Linux Server / Raspberry Pi)

```
Raspberry Pi / Linux Server
└── Gateway (127.0.0.1:18789)
    ↕  SSH tunnel or Tailscale
macOS App / CLI / WebChat (client devices)
```

**Recommended**: Use Tailscale for secure remote access.

```json5
{
  gateway: {
    tailscale: { mode: "serve" }   // Tailnet-only access
  }
}
```

### 3. Docker

```bash
docker-compose up -d
```

See official Docker guide: https://docs.openclaw.ai/install/docker

Sandbox mode: non-main sessions run in Docker containers for isolation.

```json5
{
  agents: {
    defaults: {
      sandbox: {
        mode: "non-main",
        docker: {
          setupCommand: "pip install required-package"
        }
      }
    }
  }
}
```

## Diagnostics

```bash
openclaw doctor     # Full diagnostic check
openclaw status     # Current status
```

## Model / API Configuration

```json5
{
  agent: {
    model: "anthropic/claude-opus-4-6"   // Recommended
  },
  models: {
    "anthropic/claude-opus-4-6": {
      // OAuth or API key config
    },
    "openai/gpt-4": {
      apiKey: "sk-..."
    }
  }
}
```

## Raspberry Pi Specifics

- Run Gateway as systemd user service for auto-start on boot
- Use Tailscale for remote access from other devices
- Workspace dir typically at `~/.openclaw/workspace/`
- Skills can be managed via this repo (clone or copy `skills/` directories)
