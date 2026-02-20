---
name: github-kb
description: "GitHub knowledge base manager. Maintains a local directory of cloned repos at /home/openclaw/.openclaw/workspace/github-kb, with one-line summaries indexed in CLAUDE.md. Use when: searching or browsing GitHub repos locally, cloning repos for offline analysis, checking issues/PRs, querying GitHub. Always check the local KB index first before going online. Triggers on: repo, repository, 仓库, clone, GitHub, issue, PR, pull request."
metadata:
  openclaw:
    emoji: "📚"
    requires:
      bins: ["gh"]
    install:
      - id: apt
        kind: apt
        package: gh
        bins: ["gh"]
        label: "Install GitHub CLI (apt)"
      - id: brew
        kind: brew
        formula: gh
        bins: ["gh"]
        label: "Install GitHub CLI (brew)"
---

# GitHub KB

Local knowledge base for GitHub repositories, powered by the `gh` CLI.

## Local KB Directory

**Path:** `/home/openclaw/.openclaw/workspace/github-kb`
**Index file:** `/home/openclaw/.openclaw/workspace/github-kb/CLAUDE.md`

### First-time setup

If `/home/openclaw/.openclaw/workspace/github-kb` does not exist, create it:

```bash
mkdir -p /home/openclaw/.openclaw/workspace/github-kb
```

If `/home/openclaw/.openclaw/workspace/github-kb/CLAUDE.md` does not exist, initialize it:

```bash
cat > /home/openclaw/.openclaw/workspace/github-kb/CLAUDE.md << 'EOF'
# GitHub KB — Repository Index

Local path: `/home/openclaw/.openclaw/workspace/github-kb`

## Repositories

EOF
```

### If the KB directory is missing or at a different path

1. Tell the user the directory was not found
2. Ask for the correct path
3. Use that path for all subsequent commands in the session

## Core Workflows

### 1. Answer questions about a repo

1. Read the index to check if the repo is already cloned locally:

```bash
cat /home/openclaw/.openclaw/workspace/github-kb/CLAUDE.md
```

2. If cloned: explore the local directory with read/grep/glob tools for fast, offline analysis
3. If not cloned: use `gh` CLI to query GitHub directly (see [gh-commands.md](references/gh-commands.md))

### 2. Download a repo

When the user says "下载" / "clone" / "download" a repo:

```bash
gh repo clone <owner>/<repo> /home/openclaw/.openclaw/workspace/github-kb/<repo>
```

After cloning, **always update the index**:

1. Read the repo's README (or key files) to produce a one-line summary
2. Append to `/home/openclaw/.openclaw/workspace/github-kb/CLAUDE.md`:

```
- **<repo>** (`<owner>/<repo>`): <one-line summary in ≤120 chars>
```

For large repos, use shallow clone to save disk space on the Pi:

```bash
gh repo clone <owner>/<repo> /home/openclaw/.openclaw/workspace/github-kb/<repo> -- --depth 1
```

### 3. Search GitHub

Use `gh` commands to search issues, PRs, repos, and code.
See [gh-commands.md](references/gh-commands.md) for the full reference.

Common patterns:

```bash
gh repo view <owner>/<repo>                          # Repo overview
gh issue list --repo <owner>/<repo>                  # List issues
gh pr list --repo <owner>/<repo>                     # List PRs
gh search repos <query>                              # Search repos
gh search issues <query> --repo <owner>/<repo>       # Search issues in a repo
```

### 4. List cloned repos

```bash
cat /home/openclaw/.openclaw/workspace/github-kb/CLAUDE.md
```

Or list directories directly:

```bash
ls /home/openclaw/.openclaw/workspace/github-kb/
```

## Behavior Guidelines

- **Prefer local first**: if a repo is in the KB, explore it locally—faster and richer than API
- **Update the index**: after every clone, always append a one-line summary to `CLAUDE.md`
- **Be concise**: summaries in CLAUDE.md should be ≤ 120 chars
- **Save disk space**: use `--depth 1` for large repos on the Pi unless full history is needed
- **Complement github skill**: this skill handles local KB management; for pure GitHub operations (PRs, CI, issue triage) prefer the `github` skill
- **Chinese OK**: respond in Chinese if the user writes in Chinese
