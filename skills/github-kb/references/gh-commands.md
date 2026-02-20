# GitHub CLI (`gh`) Command Reference

## Repository

```bash
gh repo view <owner>/<repo>                          # Summary, description, stars, topics
gh repo view <owner>/<repo> --json name,description,stargazerCount,topics
gh repo clone <owner>/<repo> <local-path>            # Clone repo
gh repo clone <owner>/<repo> <local-path> -- --depth 1  # Shallow clone (saves disk space)
gh repo list <owner>                                 # List user/org repos
```

## Issues

```bash
gh issue list --repo <owner>/<repo>                  # Open issues (default: 30)
gh issue list --repo <owner>/<repo> --state all      # All issues
gh issue list --repo <owner>/<repo> --label bug      # Filter by label
gh issue view <number> --repo <owner>/<repo>         # View single issue + comments
gh search issues "<query>" --repo <owner>/<repo>     # Search issues in a repo
gh search issues "<query>"                           # Search across GitHub
```

## Pull Requests

```bash
gh pr list --repo <owner>/<repo>                     # Open PRs
gh pr list --repo <owner>/<repo> --state all         # All PRs
gh pr view <number> --repo <owner>/<repo>            # View PR + diff summary
gh pr diff <number> --repo <owner>/<repo>            # Full diff
gh pr checks <number> --repo <owner>/<repo>          # CI status
gh search prs "<query>" --repo <owner>/<repo>        # Search PRs
```

## Search

```bash
gh search repos "<query>"                            # Find repos by keyword
gh search repos "<query>" --language python          # Filter by language
gh search repos "<query>" --sort stars               # Sort by stars
gh search issues "<query>"                           # Search issues globally
gh search prs "<query>"                              # Search PRs globally
gh search code "<query>" --repo <owner>/<repo>       # Search code in repo
```

## Releases & Tags

```bash
gh release list --repo <owner>/<repo>                # List releases
gh release view --repo <owner>/<repo>                # Latest release
gh release view <tag> --repo <owner>/<repo>          # Specific release
```

## Useful JSON flags

Add `--json <fields>` to get structured output. Common fields:

- repos: `name,description,stargazerCount,forkCount,updatedAt,topics,url`
- issues: `number,title,state,labels,author,createdAt,body`
- prs: `number,title,state,author,createdAt,additions,deletions`

Example:

```bash
gh issue list --repo <owner>/<repo> --json number,title,labels --limit 50
```

## Authentication

```bash
gh auth login          # Authenticate (one-time)
gh auth status         # Verify current auth status
```
