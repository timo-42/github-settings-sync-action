#!/usr/bin/env python3
"""
GitHub Settings Sync Action - Main Entry Point

This action synchronizes GitHub repository settings from a JSON configuration file.
"""

import argparse
import logging
import os
import sys
from pathlib import Path

from config import load_config, ConfigError
from github_api import GitHubClient, GitHubAPIError
from sync import sync_repository_settings, sync_labels, sync_rulesets

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


def get_env(name: str, default: str = "") -> str:
    """Get an environment variable with optional default."""
    return os.environ.get(name, default)


def set_output(name: str, value: str) -> None:
    """Set a GitHub Actions output variable."""
    github_output = get_env("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"{name}={value}\n")
    else:
        # Fallback for local testing
        print(f"::set-output name={name}::{value}")


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Synchronize GitHub repository settings from a JSON configuration file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run with default settings file
  python main.py --token ghp_xxx --dry-run

  # Apply settings from custom file
  python main.py --token ghp_xxx --settings-file config/settings.json

  # Target a different repository
  python main.py --token ghp_xxx --repository owner/repo

Environment variables:
  GITHUB_TOKEN         GitHub authentication token
  GITHUB_REPOSITORY    Default target repository (owner/repo)
  GITHUB_WORKSPACE     Workspace path for resolving settings file
  SETTINGS_FILE        Path to settings JSON file
  DRY_RUN              Set to 'true' for dry run mode
  TARGET_REPOSITORY    Override target repository
        """,
    )

    parser.add_argument(
        "--token",
        default=get_env("GITHUB_TOKEN"),
        help="GitHub token with repo permissions (default: $GITHUB_TOKEN)",
    )

    parser.add_argument(
        "--settings-file",
        default=get_env("SETTINGS_FILE", ".github/settings.json"),
        help="Path to the settings JSON file (default: .github/settings.json)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=get_env("DRY_RUN", "false").lower() in ("true", "1", "yes"),
        help="Preview changes without applying them",
    )

    parser.add_argument(
        "--repository",
        default=get_env("TARGET_REPOSITORY") or get_env("GITHUB_REPOSITORY"),
        help="Target repository as owner/repo (default: $GITHUB_REPOSITORY)",
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose (debug) logging",
    )

    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_args()

    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info("=" * 60)
    logger.info("GitHub Settings Sync Action")
    logger.info("=" * 60)

    # Validate required inputs
    if not args.token:
        logger.error("GitHub token is required. Use --token or set GITHUB_TOKEN")
        return 1

    if not args.repository:
        logger.error("Repository is required. Use --repository or set GITHUB_REPOSITORY")
        return 1

    # Parse repository
    if "/" not in args.repository:
        logger.error("Repository must be in format: owner/repo")
        return 1

    owner, repo = args.repository.split("/", 1)

    logger.info(f"Target repository: {owner}/{repo}")
    logger.info(f"Settings file: {args.settings_file}")
    logger.info(f"Dry run: {args.dry_run}")

    # Resolve settings file path
    workspace = get_env("GITHUB_WORKSPACE", os.getcwd())
    settings_path = Path(workspace) / args.settings_file

    # Load configuration
    try:
        config = load_config(str(settings_path))
    except ConfigError as e:
        logger.error(f"Configuration error: {e}")
        return 1

    # Create GitHub client
    client = GitHubClient(args.token)

    # Track overall changes
    changes_summary = []
    has_errors = False

    # Sync repository settings
    if "repository" in config:
        logger.info("")
        logger.info("-" * 40)
        logger.info("Repository Settings")
        logger.info("-" * 40)
        try:
            result = sync_repository_settings(
                client, owner, repo, config["repository"], args.dry_run
            )
            if result.get("changed") or result.get("dry_run"):
                changes_summary.append(
                    f"Repository: {len(result.get('changes', []))} setting(s)"
                )
        except GitHubAPIError as e:
            logger.error(f"Failed to sync repository settings: {e}")
            has_errors = True

    # Sync labels
    if "labels" in config:
        logger.info("")
        logger.info("-" * 40)
        logger.info("Labels")
        logger.info("-" * 40)
        try:
            result = sync_labels(client, owner, repo, config["labels"], args.dry_run)
            if result.get("changed") or result.get("dry_run"):
                results = result.get("results", {})
                changes_summary.append(
                    f"Labels: {len(results.get('created', []))} created, "
                    f"{len(results.get('updated', []))} updated"
                )
        except GitHubAPIError as e:
            logger.error(f"Failed to sync labels: {e}")
            has_errors = True

    # Sync rulesets
    if "rulesets" in config:
        logger.info("")
        logger.info("-" * 40)
        logger.info("Rulesets")
        logger.info("-" * 40)
        try:
            result = sync_rulesets(
                client, owner, repo, config["rulesets"], args.dry_run
            )
            if result.get("changed") or result.get("dry_run"):
                results = result.get("results", {})
                changes_summary.append(
                    f"Rulesets: {len(results.get('created', []))} created, "
                    f"{len(results.get('updated', []))} updated"
                )
        except GitHubAPIError as e:
            logger.error(f"Failed to sync rulesets: {e}")
            has_errors = True

    # Summary
    logger.info("")
    logger.info("=" * 60)
    if args.dry_run:
        logger.info("DRY RUN COMPLETE - No changes were made")
    else:
        logger.info("SYNC COMPLETE")
    logger.info("=" * 60)

    if changes_summary:
        summary = "; ".join(changes_summary)
        logger.info(f"Summary: {summary}")
        set_output("changes", summary)
    else:
        logger.info("No changes detected")
        set_output("changes", "No changes")

    return 1 if has_errors else 0


if __name__ == "__main__":
    sys.exit(main())
