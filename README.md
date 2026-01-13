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

### Rulesets

Rulesets are the modern way to protect branches and tags. They're more powerful than legacy branch protection.

```json
{
  "rulesets": [
    {
      "name": "main-protection",
      "target": "branch",
      "enforcement": "active",
      "branches": ["~DEFAULT_BRANCH", "main"],
      "rules": {
        "pull_request": {
          "required_approving_review_count": 1,
          "dismiss_stale_reviews_on_push": true,
          "require_code_owner_review": false,
          "require_last_push_approval": false,
          "required_review_thread_resolution": true
        },
        "required_status_checks": {
          "strict": true,
          "contexts": ["build", "test"]
        },
        "required_signatures": false,
        "required_linear_history": false,
        "non_fast_forward": true,
        "deletion": true
      }
    }
  ]
}
```

#### Ruleset Options

| Field | Description |
|-------|-------------|
| `name` | Unique name for the ruleset |
| `target` | `"branch"` or `"tag"` |
| `enforcement` | `"active"`, `"evaluate"` (audit only), or `"disabled"` |
| `branches` | Array of branch patterns (use `~DEFAULT_BRANCH` for default) |
| `conditions` | Advanced: `ref_name.include` and `ref_name.exclude` patterns |

#### Available Rules

| Rule | Description |
|------|-------------|
| `pull_request` | Require PRs with reviews |
| `required_status_checks` | Require CI checks to pass |
| `required_signatures` | Require signed commits |
| `required_linear_history` | Prevent merge commits |
| `required_deployments` | Require deployment to environments |
| `creation` | Restrict who can create matching refs |
| `update` | Restrict who can push updates |
| `deletion` | Prevent deletion |
| `non_fast_forward` | Prevent force pushes |

📚 **GitHub Docs:** [Repository Rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets)

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

## Authentication & Tokens

### Option 1: Use `GITHUB_TOKEN` (Recommended for same-repo)

The built-in `GITHUB_TOKEN` works for most use cases:

```yaml
- uses: your-username/github-settings-sync-action@v1
  with:
    token: ${{ secrets.GITHUB_TOKEN }}
```

### Option 2: Personal Access Token (PAT)

Required for:
- Managing settings on **other repositories**
- **Rulesets** (requires `administration:write`)
- **Organization-level** settings

#### Creating a Fine-Grained PAT (Recommended)

1. Go to [GitHub Settings → Developer settings → Personal access tokens → Fine-grained tokens](https://github.com/settings/tokens?type=beta)
2. Click **"Generate new token"**
3. Set token name and expiration
4. Under **"Repository access"**, select the repos you need
5. Under **"Permissions"**, enable:
   - `Administration`: Read and write
   - `Contents`: Read-only
   - `Issues`: Read and write (for labels)
   - `Metadata`: Read-only
6. Click **"Generate token"**

Or use the **GitHub CLI**:

```bash
# Create a fine-grained PAT with required permissions
gh auth token

# Or create a new token interactively
gh auth login --scopes "repo,admin:org"

# View your current token
gh auth status --show-token
```

#### Creating a Classic PAT

1. Go to [GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)](https://github.com/settings/tokens)
2. Click **"Generate new token (classic)"**
3. Select scopes:
   - `repo` (full control of private repositories)
   - `admin:org` (if managing org-level rulesets)
4. Click **"Generate token"**

Or use the **GitHub CLI**:

```bash
# Generate a classic token with repo scope
gh api -X POST /user/tokens -f scopes[]="repo" -f note="settings-sync"
```

#### Store the Token as a Secret

```bash
# Add token to your repository secrets using gh CLI
gh secret set PAT_TOKEN --body "ghp_xxxxxxxxxxxx"
```

Then use it in your workflow:

```yaml
- uses: your-username/github-settings-sync-action@v1
  with:
    token: ${{ secrets.PAT_TOKEN }}
```

### Required Permissions Summary

| Feature | GITHUB_TOKEN | Fine-Grained PAT | Classic PAT |
|---------|--------------|------------------|-------------|
| Repository settings | ✅ | `administration:write` | `repo` |
| Labels | ✅ | `issues:write` | `repo` |
| Rulesets | ❌ | `administration:write` | `repo` + `admin:org` |
| Other repos | ❌ | Select repos | `repo` |

📚 **GitHub Docs:**
- [Creating a fine-grained PAT](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token#creating-a-fine-grained-personal-access-token)
- [Creating a classic PAT](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token#creating-a-personal-access-token-classic)
- [Automatic token authentication](https://docs.github.com/en/actions/security-guides/automatic-token-authentication)

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
