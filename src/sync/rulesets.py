"""
Synchronize repository rulesets (newer API replacing branch protection).

GitHub Rulesets API: https://docs.github.com/en/rest/repos/rules
"""

import logging
from typing import Any, Optional

from ..github_api import GitHubClient, GitHubAPIError

logger = logging.getLogger(__name__)


def sync_rulesets(
    client: GitHubClient,
    owner: str,
    repo: str,
    rulesets: list,
    dry_run: bool = False,
) -> dict:
    """
    Synchronize repository rulesets.

    Args:
        client: GitHub API client
        owner: Repository owner
        repo: Repository name
        rulesets: List of desired rulesets
        dry_run: If True, only show what would change

    Returns:
        Dictionary with sync results
    """
    logger.info(f"Syncing rulesets for {owner}/{repo}")

    # Get current rulesets
    current_rulesets = client.get_rulesets(owner, repo)
    current_by_name = {rs["name"]: rs for rs in current_rulesets}

    results = {
        "created": [],
        "updated": [],
        "unchanged": [],
        "failed": [],
    }

    for desired in rulesets:
        name = desired["name"]
        current = current_by_name.get(name)

        # Build the ruleset payload
        payload = build_ruleset_payload(desired)

        if current is None:
            # Create new ruleset
            logger.info(f"  Creating ruleset: {name}")

            if dry_run:
                logger.info(f"  [DRY RUN] Would create ruleset: {name}")
                results["created"].append(name)
                continue

            try:
                client.create_ruleset(owner, repo, payload)
                results["created"].append(name)
                logger.info(f"  Created ruleset: {name}")
            except GitHubAPIError as e:
                logger.error(f"  Failed to create ruleset '{name}': {e}")
                results["failed"].append({"name": name, "error": str(e)})
        else:
            # Update existing ruleset
            if not needs_update(current, desired):
                logger.info(f"  Ruleset '{name}' is up to date")
                results["unchanged"].append(name)
                continue

            logger.info(f"  Updating ruleset: {name}")

            if dry_run:
                logger.info(f"  [DRY RUN] Would update ruleset: {name}")
                results["updated"].append(name)
                continue

            try:
                client.update_ruleset(owner, repo, current["id"], payload)
                results["updated"].append(name)
                logger.info(f"  Updated ruleset: {name}")
            except GitHubAPIError as e:
                logger.error(f"  Failed to update ruleset '{name}': {e}")
                results["failed"].append({"name": name, "error": str(e)})

    # Summary
    logger.info(
        f"Rulesets sync complete: {len(results['created'])} created, "
        f"{len(results['updated'])} updated, {len(results['unchanged'])} unchanged, "
        f"{len(results['failed'])} failed"
    )

    return {
        "changed": len(results["created"]) > 0 or len(results["updated"]) > 0,
        "results": results,
        "dry_run": dry_run,
    }


def build_ruleset_payload(desired: dict) -> dict:
    """
    Build the ruleset API payload.

    See: https://docs.github.com/en/rest/repos/rules#create-a-repository-ruleset
    """
    payload = {
        "name": desired["name"],
        "target": desired.get("target", "branch"),
        "enforcement": desired.get("enforcement", "active"),
    }

    # Build conditions (which branches/tags to target)
    if "conditions" in desired:
        payload["conditions"] = build_conditions(desired["conditions"])
    elif "branches" in desired:
        # Shorthand: list of branch patterns
        payload["conditions"] = {
            "ref_name": {
                "include": desired["branches"],
                "exclude": desired.get("exclude_branches", []),
            }
        }

    # Build rules array
    if "rules" in desired:
        payload["rules"] = build_rules(desired["rules"])

    # Bypass actors (who can bypass the rules)
    if "bypass_actors" in desired:
        payload["bypass_actors"] = desired["bypass_actors"]

    return payload


def build_conditions(conditions: dict) -> dict:
    """Build the conditions object for branch/tag targeting."""
    result = {}

    if "ref_name" in conditions:
        result["ref_name"] = {
            "include": conditions["ref_name"].get("include", []),
            "exclude": conditions["ref_name"].get("exclude", []),
        }

    return result


def build_rules(rules: dict) -> list:
    """
    Build the rules array from a simplified config format.

    Converts user-friendly config to GitHub API format.
    """
    result = []

    # Pull request rules
    if "pull_request" in rules:
        pr = rules["pull_request"]
        rule = {"type": "pull_request"}
        params = {}

        if "required_approving_review_count" in pr:
            params["required_approving_review_count"] = pr["required_approving_review_count"]
        if "dismiss_stale_reviews_on_push" in pr:
            params["dismiss_stale_reviews_on_push"] = pr["dismiss_stale_reviews_on_push"]
        if "require_code_owner_review" in pr:
            params["require_code_owner_review"] = pr["require_code_owner_review"]
        if "require_last_push_approval" in pr:
            params["require_last_push_approval"] = pr["require_last_push_approval"]
        if "required_review_thread_resolution" in pr:
            params["required_review_thread_resolution"] = pr["required_review_thread_resolution"]

        if params:
            rule["parameters"] = params
        result.append(rule)

    # Required status checks
    if "required_status_checks" in rules:
        rsc = rules["required_status_checks"]
        rule = {
            "type": "required_status_checks",
            "parameters": {
                "strict_required_status_checks_policy": rsc.get("strict", False),
                "required_status_checks": [
                    {"context": ctx} if isinstance(ctx, str) else ctx
                    for ctx in rsc.get("contexts", [])
                ],
            },
        }
        result.append(rule)

    # Required signatures
    if rules.get("required_signatures"):
        result.append({"type": "required_signatures"})

    # Required linear history
    if rules.get("required_linear_history"):
        result.append({"type": "required_linear_history"})

    # Required deployments
    if "required_deployments" in rules:
        result.append({
            "type": "required_deployments",
            "parameters": {
                "required_deployment_environments": rules["required_deployments"],
            },
        })

    # Creation restriction
    if rules.get("creation"):
        result.append({"type": "creation"})

    # Update restriction
    if rules.get("update"):
        result.append({"type": "update"})

    # Deletion restriction
    if rules.get("deletion"):
        result.append({"type": "deletion"})

    # Non-fast-forward (prevent force push)
    if rules.get("non_fast_forward"):
        result.append({"type": "non_fast_forward"})

    return result


def needs_update(current: dict, desired: dict) -> bool:
    """
    Check if the ruleset needs to be updated.

    Compares key fields to determine if an update is necessary.
    """
    # Check enforcement level
    if current.get("enforcement") != desired.get("enforcement", "active"):
        return True

    # Check target
    if current.get("target") != desired.get("target", "branch"):
        return True

    # For simplicity, always update if rules are specified
    # A more sophisticated implementation would deep-compare rules
    if "rules" in desired:
        return True

    return False
