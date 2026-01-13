# GitHub Settings Sync Action

[![GitHub Marketplace](https://img.shields.io/badge/Marketplace-GitHub%20Settings%20Sync-blue?logo=github)](https://github.com/marketplace/actions/github-settings-sync)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Repository Settings as Code** — Define your GitHub repository settings in a JSON configuration file, and this action keeps them in sync.

## Features

- 🔧 **Repository Settings** — Manage description, visibility, merge options, and more
- 🏷️ **Labels** — Create and update issue/PR labels
- 🔒 **Branch Protection** — Configure branch protection rules
- 👀 **Dry Run Mode** — Preview changes before applying them
- 🎯 **Zero Dependencies** — Built with Python standard library only

## Quick Start

### 1. Create a settings file

Create `.github/settings.json` in your repository:

```json
{
  "repository": {
    "description": "My awesome project",
    "has_issues": true,
    "has_wiki": false,
    "delete_branch_on_merge": true
  },
  "labels": [
    { "name": "bug", "color": "d73a4a", "description": "Something isn't working" },
    { "name": "feature", "color": "a2eeef", "description": "New feature request" }
  ]
}
```

### 2. Create a workflow

Create `.github/workflows/settings-sync.yml`:

```yaml
name: Sync Repository Settings

on:
  push:
    branches: [main]
    paths: ['.github/settings.json']
  workflow_dispatch:

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Sync Settings
        uses: YOUR_USERNAME/github-settings-sync-action@v1
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
```

## Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `token` | **Yes** | — | GitHub token with `repo` permissions |
| `settings_file` | No | `.github/settings.json` | Path to the settings file |
| `dry_run` | No | `false` | Preview changes without applying |
| `repository` | No | Current repo | Target repository (`owner/repo`) |

## Outputs

| Output | Description |
|--------|-------------|
| `changes` | Summary of changes made |

## Configuration Reference

### Repository Settings

```json
{
  "repository": {
    "name": "repo-name",
    "description": "Repository description",
    "homepage": "https://example.com",
    "private": false,
    "visibility": "public",
    "has_issues": true,
    "has_projects": true,
    "has_wiki": true,
    "has_discussions": false,
    "is_template": false,
    "default_branch": "main",
    "allow_squash_merge": true,
    "allow_merge_commit": true,
    "allow_rebase_merge": true,
    "allow_auto_merge": false,
    "delete_branch_on_merge": true,
    "allow_update_branch": true,
    "squash_merge_commit_title": "PR_TITLE",
    "squash_merge_commit_message": "PR_BODY",
    "merge_commit_title": "PR_TITLE",
    "merge_commit_message": "PR_BODY",
    "web_commit_signoff_required": false
  }
}
```

### Labels

```json
{
  "labels": [
    {
      "name": "bug",
      "color": "d73a4a",
      "description": "Something isn't working"
    },
    {
      "name": "enhancement",
      "color": "a2eeef",
      "description": "New feature or request"
    },
    {
      "name": "documentation",
      "color": "0075ca",
      "description": "Improvements or additions to documentation"
    }
  ]
}
```

**Note:** Colors should be 6-character hex codes without the `#` prefix.

### Branch Protection

```json
{
  "branch_protection": {
    "main": {
      "required_status_checks": {
        "strict": true,
        "contexts": ["build", "test"]
      },
      "enforce_admins": true,
      "required_pull_request_reviews": {
        "dismiss_stale_reviews": true,
        "require_code_owner_reviews": false,
        "required_approving_review_count": 1,
        "require_last_push_approval": false
      },
      "restrictions": null,
      "required_linear_history": false,
      "allow_force_pushes": false,
      "allow_deletions": false,
      "block_creations": false,
      "required_conversation_resolution": true,
      "lock_branch": false,
      "allow_fork_syncing": false
    }
  }
}
```

## Examples

### Dry Run Mode

Preview changes without applying them:

```yaml
- name: Preview Settings Changes
  uses: YOUR_USERNAME/github-settings-sync-action@v1
  with:
    token: ${{ secrets.GITHUB_TOKEN }}
    dry_run: true
```

### Custom Settings File

Use a different settings file:

```yaml
- name: Sync Settings
  uses: YOUR_USERNAME/github-settings-sync-action@v1
  with:
    token: ${{ secrets.GITHUB_TOKEN }}
    settings_file: 'config/repo-settings.json'
```

### Sync to Another Repository

Apply settings to a different repository (requires a token with access):

```yaml
- name: Sync Settings to Other Repo
  uses: YOUR_USERNAME/github-settings-sync-action@v1
  with:
    token: ${{ secrets.PAT_TOKEN }}
    repository: 'owner/other-repo'
```

## Required Permissions

The `GITHUB_TOKEN` needs the following permissions:

- `contents: read` — To read the settings file
- `administration: write` — To update repository settings and branch protection
- `issues: write` — To manage labels (if using labels sync)

For branch protection on repositories you don't own, you may need a Personal Access Token (PAT) with `repo` scope.

## CLI Usage (Local Testing)

You can run the sync locally without GitHub Actions:

```bash
cd src

# Basic usage with dry run
python main.py --token ghp_xxxx --repository owner/repo --dry-run

# Apply settings from custom file
python main.py --token ghp_xxxx --repository owner/repo \
  --settings-file ../examples/full-settings.json

# Verbose output for debugging
python main.py --token ghp_xxxx --repository owner/repo --dry-run --verbose

# See all options
python main.py --help
```

### CLI Options

| Option | Description |
|--------|-------------|
| `--token` | GitHub token (or set `GITHUB_TOKEN` env var) |
| `--repository` | Target repo as `owner/repo` |
| `--settings-file` | Path to settings JSON (default: `.github/settings.json`) |
| `--dry-run` | Preview changes without applying |
| `--verbose, -v` | Enable debug logging |

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
