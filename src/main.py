#!/usr/bin/env python3
"""
GitHub Settings Sync Action - Main Entry Point

This action synchronizes GitHub repository settings from a JSON configuration file.
"""

import logging
import os
import sys
from pathlib import Path

from config import load_config, ConfigError
from github_api import GitHubClient, GitHubAPIError
from sync import sync_repository_settings, sync_labels, sync_branch_protection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


def get_env(name: str, default: str = "") -> str:
    """Get an environment variable with optional default."""
    return os.environ.get(name, default)


def get_bool_env(name: str, default: bool = False) -> bool:
    """Get a boolean environment variable."""
    value = get_env(name, str(default)).lower()
    return value in ("true", "1", "yes")


def set_output(name: str, value: str) -> None:
    """Set a GitHub Actions output variable."""
    github_output = get_env("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"{name}={value}\n")
    else:
        # Fallback for local testing
        print(f"::set-output name={name}::{value}")


def main() -> int:
    """Main entry point."""
    logger.info("=" * 60)
    logger.info("GitHub Settings Sync Action")
    logger.info("=" * 60)

    # Get inputs from environment
    token = get_env("GITHUB_TOKEN")
    settings_file = get_env("SETTINGS_FILE", ".github/settings.json")
    dry_run = get_bool_env("DRY_RUN", False)
    target_repo = get_env("TARGET_REPOSITORY")

    # Validate required inputs
    if not token:
        logger.error("GITHUB_TOKEN is required")
        return 1

    # Determine repository
    if target_repo:
        owner, repo = target_repo.split("/", 1)
    else:
        # Get from GITHUB_REPOSITORY (set by GitHub Actions)
        github_repo = get_env("GITHUB_REPOSITORY")
        if not github_repo:
            logger.error("Could not determine target repository")
            return 1
        owner, repo = github_repo.split("/", 1)

    logger.info(f"Target repository: {owner}/{repo}")
    logger.info(f"Settings file: {settings_file}")
    logger.info(f"Dry run: {dry_run}")

    # Resolve settings file path
    workspace = get_env("GITHUB_WORKSPACE", os.getcwd())
    settings_path = Path(workspace) / settings_file

    # Load configuration
    try:
        config = load_config(str(settings_path))
    except ConfigError as e:
        logger.error(f"Configuration error: {e}")
        return 1

    # Create GitHub client
    client = GitHubClient(token)

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
                client, owner, repo, config["repository"], dry_run
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
            result = sync_labels(client, owner, repo, config["labels"], dry_run)
            if result.get("changed") or result.get("dry_run"):
                results = result.get("results", {})
                changes_summary.append(
                    f"Labels: {len(results.get('created', []))} created, "
                    f"{len(results.get('updated', []))} updated"
                )
        except GitHubAPIError as e:
            logger.error(f"Failed to sync labels: {e}")
            has_errors = True

    # Sync branch protection
    if "branch_protection" in config:
        logger.info("")
        logger.info("-" * 40)
        logger.info("Branch Protection")
        logger.info("-" * 40)
        try:
            result = sync_branch_protection(
                client, owner, repo, config["branch_protection"], dry_run
            )
            if result.get("changed") or result.get("dry_run"):
                results = result.get("results", {})
                changes_summary.append(
                    f"Branch protection: {len(results.get('updated', []))} branch(es)"
                )
        except GitHubAPIError as e:
            logger.error(f"Failed to sync branch protection: {e}")
            has_errors = True

    # Summary
    logger.info("")
    logger.info("=" * 60)
    if dry_run:
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
