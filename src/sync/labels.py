"""
Synchronize repository labels.
"""

import logging
from typing import Optional

from ..github_api import GitHubClient, GitHubAPIError

logger = logging.getLogger(__name__)


def sync_labels(
    client: GitHubClient,
    owner: str,
    repo: str,
    labels: list,
    dry_run: bool = False,
) -> dict:
    """
    Synchronize repository labels.

    Args:
        client: GitHub API client
        owner: Repository owner
        repo: Repository name
        labels: List of desired labels
        dry_run: If True, only show what would change

    Returns:
        Dictionary with sync results
    """
    logger.info(f"Syncing labels for {owner}/{repo}")

    # Get current labels
    current_labels = client.get_labels(owner, repo)
    current_by_name = {label["name"].lower(): label for label in current_labels}

    results = {
        "created": [],
        "updated": [],
        "unchanged": [],
    }

    for desired_label in labels:
        name = desired_label["name"]
        name_lower = name.lower()

        # Normalize color (remove # if present)
        color = desired_label["color"].lstrip("#")
        description = desired_label.get("description", "")

        current_label = current_by_name.get(name_lower)

        if current_label is None:
            # Create new label
            logger.info(f"  Creating label: {name}")

            if dry_run:
                logger.info(f"  [DRY RUN] Would create label: {name}")
                results["created"].append(name)
                continue

            try:
                client.create_label(
                    owner,
                    repo,
                    {
                        "name": name,
                        "color": color,
                        "description": description,
                    },
                )
                results["created"].append(name)
                logger.info(f"  Created label: {name}")
            except GitHubAPIError as e:
                logger.error(f"  Failed to create label '{name}': {e}")
        else:
            # Check if update is needed
            needs_update = False
            changes = []

            if current_label["color"].lower() != color.lower():
                needs_update = True
                changes.append(f"color: {current_label['color']} -> {color}")

            current_desc = current_label.get("description") or ""
            if current_desc != description:
                needs_update = True
                changes.append(f"description changed")

            # Check if name case changed
            if current_label["name"] != name:
                needs_update = True
                changes.append(f"name case: {current_label['name']} -> {name}")

            if needs_update:
                logger.info(f"  Updating label '{name}': {', '.join(changes)}")

                if dry_run:
                    logger.info(f"  [DRY RUN] Would update label: {name}")
                    results["updated"].append(name)
                    continue

                try:
                    client.update_label(
                        owner,
                        repo,
                        current_label["name"],
                        {
                            "new_name": name,
                            "color": color,
                            "description": description,
                        },
                    )
                    results["updated"].append(name)
                    logger.info(f"  Updated label: {name}")
                except GitHubAPIError as e:
                    logger.error(f"  Failed to update label '{name}': {e}")
            else:
                results["unchanged"].append(name)

    # Summary
    logger.info(
        f"Labels sync complete: {len(results['created'])} created, "
        f"{len(results['updated'])} updated, {len(results['unchanged'])} unchanged"
    )

    return {
        "changed": len(results["created"]) > 0 or len(results["updated"]) > 0,
        "results": results,
        "dry_run": dry_run,
    }
