# Agents Guide

This document provides guidance for AI agents working with the GitHub Settings Sync Action codebase.

## Project Overview

This is a **GitHub Action** written in pure Python (no 3rd party dependencies) that synchronizes repository settings from a JSON configuration file. It implements "Settings as Code" for GitHub repositories.

## Key Design Decisions

1. **No external dependencies** - Uses only Python standard library (`urllib`, `json`, `os`, `logging`)
2. **Composite action** - Runs directly on the runner (Linux, macOS, Windows) using Python 3.13
3. **JSON configuration** - YAML is not in stdlib, so JSON is used instead
4. **Modular sync system** - Each settings type (repo, labels, branches) has its own module

## Directory Structure

```
├── action.yml          # GitHub Action definition (composite, inputs, outputs)
├── src/
│   ├── main.py         # Entry point - orchestrates the sync process
│   ├── config.py       # JSON config loading and validation
│   ├── github_api.py   # REST API client using urllib
│   └── sync/
│       ├── repository.py   # Sync repo settings (description, features, etc.)
│       ├── labels.py       # Sync issue/PR labels
│       └── branches.py     # Sync branch protection rules
├── examples/           # Example configuration files
└── .github/
    ├── settings.json   # Dogfooding: this repo's own settings
    └── workflows/      # CI workflows
```

## How to Make Changes

### Adding a New Setting Type

1. Create a new sync module in `src/sync/` (e.g., `webhooks.py`)
2. Implement a `sync_*` function following the pattern in existing modules
3. Add the function to `src/sync/__init__.py`
4. Add validation in `src/config.py`
5. Call the sync function from `src/main.py`
6. Update `README.md` with the new configuration options

### Modifying the GitHub API Client

The `GitHubClient` class in `src/github_api.py` wraps `urllib.request`. To add new API endpoints:

1. Add a method to `GitHubClient` class
2. Use existing `get()`, `post()`, `patch()`, `put()`, `delete()` helpers
3. Handle errors with `GitHubAPIError`

### Testing Changes Locally

```bash
# Run with command line arguments
cd src
python main.py --token "ghp_xxx" --repository "owner/repo" --dry-run

# Or use environment variables
export GITHUB_TOKEN="your-token"
export GITHUB_REPOSITORY="owner/repo"
python main.py --dry-run

# See all options
python main.py --help
```

## Code Conventions

- **Type hints** - Use typing annotations for function signatures
- **Docstrings** - Every public function should have a docstring
- **Logging** - Use the `logging` module, not `print()`
- **Error handling** - Raise `ConfigError` for config issues, `GitHubAPIError` for API issues

## Common Tasks

| Task | Files to Modify |
|------|-----------------|
| Add new repo setting | `config.py` (validation), `sync/repository.py` (sync logic) |
| Add new label field | `config.py`, `sync/labels.py` |
| Add branch protection option | `config.py`, `sync/branches.py` |
| Change action inputs | `action.yml`, `src/main.py` |

## API Reference

### GitHub REST API Endpoints Used

- `GET /repos/{owner}/{repo}` - Get repository info
- `PATCH /repos/{owner}/{repo}` - Update repository settings
- `GET /repos/{owner}/{repo}/labels` - List labels
- `POST /repos/{owner}/{repo}/labels` - Create label
- `PATCH /repos/{owner}/{repo}/labels/{name}` - Update label
- `GET /repos/{owner}/{repo}/branches/{branch}/protection` - Get branch protection
- `PUT /repos/{owner}/{repo}/branches/{branch}/protection` - Set branch protection

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GITHUB_TOKEN` | Authentication token | Yes |
| `GITHUB_REPOSITORY` | Target repo (owner/repo) | Yes* |
| `GITHUB_WORKSPACE` | Workspace path | Auto-set |
| `SETTINGS_FILE` | Config file path | No |
| `DRY_RUN` | Preview mode | No |
| `TARGET_REPOSITORY` | Override target repo | No |

*Auto-set by GitHub Actions
