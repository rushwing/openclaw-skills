# OpenClaw — Chat Commands Reference

Commands work in any connected channel (WhatsApp, Telegram, Slack, Discord, WebChat).

## Session Management

| Command | Description |
|---------|-------------|
| `/new` | Start a new session (resets context) |
| `/reset` | Reset current session |
| `/stop` | Stop current session |
| `/compact` | Compact session context (creates summary, frees tokens) |
| `/status` | Show session status (model, token usage) |

## Model Behavior

| Command | Description |
|---------|-------------|
| `/think off` | Disable extended thinking |
| `/think minimal` | Minimal thinking budget |
| `/think low` | Low thinking budget |
| `/think medium` | Medium thinking budget |
| `/think high` | High thinking budget |
| `/think xhigh` | Maximum thinking budget |
| `/verbose on\|off` | Toggle verbose output mode |

## Display Options

| Command | Description |
|---------|-------------|
| `/usage off` | Hide token usage footer |
| `/usage tokens` | Show token counts in footer |
| `/usage full` | Show full usage info in footer |

## Group-Specific Commands

| Command | Description | Who |
|---------|-------------|-----|
| `/activation mention` | Require @mention in group | Group admin |
| `/activation always` | Always respond in group | Group admin |
| `/restart` | Restart gateway | Owner only |

## CLI Commands (Terminal)

```bash
openclaw onboard         # Setup wizard
openclaw doctor          # Diagnostics
openclaw status          # Gateway status
openclaw update          # Update OpenClaw
openclaw update --channel beta   # Switch to beta channel

# Skills
clawhub install <slug>   # Install skill from ClawHub
clawhub update --all     # Update all managed skills

# Plugins
openclaw plugins install @openclaw/voice-call
openclaw plugins list
openclaw plugins enable <id>
openclaw plugins disable <id>

# Hooks
openclaw hooks install @acme/my-hooks
openclaw hooks list
openclaw hooks enable <id>
openclaw hooks check
```
