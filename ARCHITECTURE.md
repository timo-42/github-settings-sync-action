# Architecture

This document describes the architecture of the GitHub Settings Sync Action.

## High-Level Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                GitHub Actions Runner (Linux/macOS/Windows)           │
├─────────────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                 Composite Action (Python 3.13)                 │  │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────────┐   │  │
│  │  │   main.py   │───▶│  config.py  │───▶│ settings.json   │   │  │
│  │  │  (entry)    │    │  (loader)   │    │ (user config)   │   │  │
│  │  └──────┬──────┘    └─────────────┘    └─────────────────┘   │  │
│  │         │                                                      │  │
│  │         ▼                                                      │  │
│  │  ┌─────────────┐                                              │  │
│  │  │ github_api  │◀────────────────────────────────────────┐    │  │
│  │  │  (client)   │                                         │    │  │
│  │  └──────┬──────┘                                         │    │  │
│  │         │                                                │    │  │
│  │         ▼                                                │    │  │
│  │  ┌─────────────────────────────────────────────────┐    │    │  │
│  │  │                  sync modules                    │    │    │  │
│  │  │  ┌───────────┐ ┌───────────┐ ┌───────────────┐  │    │    │  │
│  │  │  │repository │ │  labels   │ │   branches    │  │────┘    │  │
│  │  │  └───────────┘ └───────────┘ └───────────────┘  │         │  │
│  │  └─────────────────────────────────────────────────┘         │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │      GitHub REST API        │
                    │   api.github.com/repos/*    │
                    └─────────────────────────────┘
```

## Component Details

### 1. Entry Point (`main.py`)

The orchestrator that:
- Reads environment variables (token, repo, settings file path)
- Loads and validates configuration
- Initializes the GitHub API client
- Calls each sync module in sequence
- Handles errors and produces output summary

```
Input: Environment variables
Output: GitHub Actions outputs, exit code
```

### 2. Configuration Loader (`config.py`)

Responsibilities:
- Load JSON configuration file from disk
- Validate structure and types
- Provide helpful error messages for invalid config

```
Input: File path
Output: Validated configuration dictionary
Errors: ConfigError
```

### 3. GitHub API Client (`github_api.py`)

A thin wrapper around `urllib.request` that:
- Handles authentication (Bearer token)
- Sets required headers (API version, User-Agent)
- Provides typed methods for each API operation
- Handles HTTP errors consistently

```
Input: Token, API endpoint, optional payload
Output: JSON response as dictionary
Errors: GitHubAPIError
```

### 4. Sync Modules (`sync/`)

Each module handles one type of settings:

| Module | Responsibility |
|--------|---------------|
| `repository.py` | General repo settings (description, features, merge options) |
| `labels.py` | Issue/PR labels (create, update) |
| `branches.py` | Branch protection rules |

Each sync function follows the same pattern:
1. Fetch current state from GitHub API
2. Compare with desired state from config
3. Calculate diff
4. Apply changes (or log them in dry-run mode)
5. Return results summary

## Data Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   JSON       │     │   Python     │     │   GitHub     │
│   Config     │────▶│   Dict       │────▶│   API        │
│   File       │     │   (validated)│     │   Payload    │
└──────────────┘     └──────────────┘     └──────────────┘
```

### Configuration Schema

```json
{
  "repository": { ... },      // Optional: repo settings
  "labels": [ ... ],          // Optional: label definitions
  "branch_protection": { ... } // Optional: branch rules
}
```

## Error Handling Strategy

```
┌─────────────────────────────────────────────────────────────┐
│                      Error Hierarchy                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Exception                                                   │
│    │                                                         │
│    ├── ConfigError          (config.py)                     │
│    │     • File not found                                   │
│    │     • Invalid JSON                                     │
│    │     • Schema validation failures                       │
│    │                                                         │
│    └── GitHubAPIError       (github_api.py)                 │
│          • HTTP 4xx/5xx responses                           │
│          • Network errors                                    │
│          • Rate limiting                                     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Execution Modes

### Normal Mode
- Applies all changes to the repository
- Returns exit code 0 on success, 1 on error

### Dry Run Mode
- Logs what would be changed
- Does not make any API mutations
- Always returns exit code 0 (unless config is invalid)

## Security Considerations

1. **Token Handling**
   - Token passed via environment variable (not command line)
   - Never logged or printed
   - Used only in Authorization header

2. **Permissions Required**
   - `contents: read` - Read settings file
   - `administration: write` - Update repo settings, branch protection
   - `issues: write` - Manage labels

3. **Input Validation**
   - All config values validated before use
   - No shell command execution
   - No dynamic code evaluation

## Extension Points

To add new functionality:

1. **New settings type**: Add module to `sync/`, update `config.py` validation
2. **New API endpoint**: Add method to `GitHubClient`
3. **New input**: Update `action.yml` and `main.py`

## Dependencies

```
Python 3.13 Standard Library Only
├── urllib.request    HTTP client
├── urllib.error      Error handling
├── json              Config parsing, API payloads
├── os                Environment variables
├── sys               Exit codes
├── logging           Structured logging
├── pathlib           File path handling
└── typing            Type annotations
```

## File Size Reference

| File | Purpose | ~Lines |
|------|---------|--------|
| `main.py` | Entry point | 130 |
| `github_api.py` | API client | 150 |
| `config.py` | Config loader | 160 |
| `sync/repository.py` | Repo sync | 90 |
| `sync/labels.py` | Labels sync | 110 |
| `sync/branches.py` | Branch protection | 150 |
