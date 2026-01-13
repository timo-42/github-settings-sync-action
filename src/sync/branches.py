"""
Synchronize branch protection rules.
"""

import logging
from typing import Any, Optional

from ..github_api import GitHubClient, GitHubAPIError

logger = logging.getLogger(__name__)


def sync_branch_protection(
    client: GitHubClient,
    owner: str,
    repo: str,
    branch_protection: dict,
    dry_run: bool = False,
) -> dict:
    """
    Synchronize branch protection rules.

    Args:
        client: GitHub API client
        owner: Repository owner
        repo: Repository name
        branch_protection: Dictionary of branch name -> protection rules
        dry_run: If True, only show what would change

    Returns:
        Dictionary with sync results
    """
    logger.info(f"Syncing branch protection for {owner}/{repo}")

    results = {
        "updated": [],
        "unchanged": [],
        "failed": [],
    }

    for branch_name, desired_protection in branch_protection.items():
        logger.info(f"  Processing branch: {branch_name}")

        try:
            # Get current protection (if any)
            current_protection = client.get_branch_protection(owner, repo, branch_name)

            # Build the protection payload
            protection_payload = build_protection_payload(desired_protection)

            if current_protection is not None:
                # Check if update is needed
                if not needs_update(current_protection, desired_protection):
                    logger.info(f"    Branch '{branch_name}' protection is up to date")
                    results["unchanged"].append(branch_name)
                    continue

            logger.info(f"    Updating protection for '{branch_name}'")

            if dry_run:
                logger.info(f"    [DRY RUN] Would update branch protection: {branch_name}")
                results["updated"].append(branch_name)
                continue

            client.update_branch_protection(
                owner, repo, branch_name, protection_payload
            )
            results["updated"].append(branch_name)
            logger.info(f"    Updated branch protection: {branch_name}")

        except GitHubAPIError as e:
            logger.error(f"    Failed to update branch protection for '{branch_name}': {e}")
            results["failed"].append({"branch": branch_name, "error": str(e)})

    # Summary
    logger.info(
        f"Branch protection sync complete: {len(results['updated'])} updated, "
        f"{len(results['unchanged'])} unchanged, {len(results['failed'])} failed"
    )

    return {
        "changed": len(results["updated"]) > 0,
        "results": results,
        "dry_run": dry_run,
    }


def build_protection_payload(desired: dict) -> dict:
    """
    Build the branch protection API payload.

    The GitHub API requires specific structure for branch protection.
    """
    payload = {
        # Required fields with defaults
        "required_status_checks": None,
        "enforce_admins": None,
        "required_pull_request_reviews": None,
        "restrictions": None,
    }

    # Required status checks
    if "required_status_checks" in desired:
        rsc = desired["required_status_checks"]
        if rsc is not None:
            payload["required_status_checks"] = {
                "strict": rsc.get("strict", False),
                "contexts": rsc.get("contexts", []),
            }

    # Enforce admins
    if "enforce_admins" in desired:
        payload["enforce_admins"] = desired["enforce_admins"]

    # Required pull request reviews
    if "required_pull_request_reviews" in desired:
        rprr = desired["required_pull_request_reviews"]
        if rprr is not None:
            payload["required_pull_request_reviews"] = {}
            if "dismiss_stale_reviews" in rprr:
                payload["required_pull_request_reviews"]["dismiss_stale_reviews"] = rprr[
                    "dismiss_stale_reviews"
                ]
            if "require_code_owner_reviews" in rprr:
                payload["required_pull_request_reviews"][
                    "require_code_owner_reviews"
                ] = rprr["require_code_owner_reviews"]
            if "required_approving_review_count" in rprr:
                payload["required_pull_request_reviews"][
                    "required_approving_review_count"
                ] = rprr["required_approving_review_count"]
            if "require_last_push_approval" in rprr:
                payload["required_pull_request_reviews"][
                    "require_last_push_approval"
                ] = rprr["require_last_push_approval"]

    # Restrictions (who can push)
    if "restrictions" in desired:
        rest = desired["restrictions"]
        if rest is not None:
            payload["restrictions"] = {
                "users": rest.get("users", []),
                "teams": rest.get("teams", []),
                "apps": rest.get("apps", []),
            }

    # Additional boolean settings
    bool_settings = [
        "required_linear_history",
        "allow_force_pushes",
        "allow_deletions",
        "block_creations",
        "required_conversation_resolution",
        "lock_branch",
        "allow_fork_syncing",
    ]

    for setting in bool_settings:
        if setting in desired:
            payload[setting] = desired[setting]

    return payload


def needs_update(current: dict, desired: dict) -> bool:
    """
    Check if the branch protection needs to be updated.

    This is a simplified comparison - in production you might want
    more detailed comparison logic.
    """
    # For simplicity, we always update if protection is specified
    # A more sophisticated implementation would compare each field
    return True
