"""
Synchronize repository settings.
"""

import logging
from typing import Any

from ..github_api import GitHubClient

logger = logging.getLogger(__name__)

# Settings that can be updated via the repository API
UPDATABLE_SETTINGS = {
    "name",
    "description",
    "homepage",
    "private",
    "visibility",
    "has_issues",
    "has_projects",
    "has_wiki",
    "has_discussions",
    "is_template",
    "default_branch",
    "allow_squash_merge",
    "allow_merge_commit",
    "allow_rebase_merge",
    "allow_auto_merge",
    "delete_branch_on_merge",
    "allow_update_branch",
    "squash_merge_commit_title",
    "squash_merge_commit_message",
    "merge_commit_title",
    "merge_commit_message",
    "archived",
    "web_commit_signoff_required",
}


def sync_repository_settings(
    client: GitHubClient,
    owner: str,
    repo: str,
    settings: dict,
    dry_run: bool = False,
) -> dict:
    """
    Synchronize repository settings.

    Args:
        client: GitHub API client
        owner: Repository owner
        repo: Repository name
        settings: Desired repository settings
        dry_run: If True, only show what would change

    Returns:
        Dictionary with sync results
    """
    logger.info(f"Syncing repository settings for {owner}/{repo}")

    # Get current repository settings
    current = client.get_repository(owner, repo)

    # Filter to only updatable settings
    desired = {k: v for k, v in settings.items() if k in UPDATABLE_SETTINGS}

    # Calculate changes
    changes = calculate_changes(current, desired)

    if not changes:
        logger.info("Repository settings are already up to date")
        return {"changed": False, "changes": []}

    # Log changes
    for change in changes:
        logger.info(
            f"  {change['setting']}: {change['current']!r} -> {change['desired']!r}"
        )

    if dry_run:
        logger.info("[DRY RUN] Would update repository settings")
        return {"changed": False, "changes": changes, "dry_run": True}

    # Apply changes
    update_payload = {change["setting"]: change["desired"] for change in changes}
    client.update_repository(owner, repo, update_payload)

    logger.info(f"Successfully updated {len(changes)} repository setting(s)")

    return {"changed": True, "changes": changes}


def calculate_changes(current: dict, desired: dict) -> list:
    """
    Calculate the differences between current and desired settings.

    Args:
        current: Current repository settings
        desired: Desired repository settings

    Returns:
        List of changes to apply
    """
    changes = []

    for setting, desired_value in desired.items():
        current_value = current.get(setting)

        # Normalize values for comparison
        if normalize_value(current_value) != normalize_value(desired_value):
            changes.append(
                {
                    "setting": setting,
                    "current": current_value,
                    "desired": desired_value,
                }
            )

    return changes


def normalize_value(value: Any) -> Any:
    """Normalize a value for comparison."""
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip()
    return value
