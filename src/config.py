"""
Configuration file loader and validator.
"""

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Valid keys for each configuration section
VALID_REPOSITORY_KEYS = {
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

VALID_LABEL_KEYS = {"name", "color", "description", "new_name"}

VALID_RULESET_KEYS = {
    "name",
    "target",
    "enforcement",
    "conditions",
    "branches",
    "exclude_branches",
    "rules",
    "bypass_actors",
}

VALID_RULESET_RULES_KEYS = {
    "pull_request",
    "required_status_checks",
    "required_signatures",
    "required_linear_history",
    "required_deployments",
    "creation",
    "update",
    "deletion",
    "non_fast_forward",
}


class ConfigError(Exception):
    """Custom exception for configuration errors."""

    pass


def load_config(file_path: str) -> dict:
    """Load and validate a configuration file."""
    path = Path(file_path)

    if not path.exists():
        raise ConfigError(f"Configuration file not found: {file_path}")

    if not path.is_file():
        raise ConfigError(f"Configuration path is not a file: {file_path}")

    logger.info(f"Loading configuration from: {file_path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        raise ConfigError(f"Invalid JSON in configuration file: {e}")
    except IOError as e:
        raise ConfigError(f"Error reading configuration file: {e}")

    if not isinstance(config, dict):
        raise ConfigError("Configuration must be a JSON object")

    validate_config(config)

    return config


def validate_config(config: dict) -> None:
    """Validate the configuration structure."""
    valid_sections = {"repository", "labels", "rulesets"}
    unknown_sections = set(config.keys()) - valid_sections

    if unknown_sections:
        logger.warning(f"Unknown configuration sections: {unknown_sections}")

    # Validate repository section
    if "repository" in config:
        validate_repository_config(config["repository"])

    # Validate labels section
    if "labels" in config:
        validate_labels_config(config["labels"])

    # Validate rulesets section
    if "rulesets" in config:
        validate_rulesets_config(config["rulesets"])


def validate_repository_config(repo_config: Any) -> None:
    """Validate repository configuration."""
    if not isinstance(repo_config, dict):
        raise ConfigError("'repository' must be an object")

    unknown_keys = set(repo_config.keys()) - VALID_REPOSITORY_KEYS
    if unknown_keys:
        logger.warning(f"Unknown repository settings: {unknown_keys}")

    # Type validation for common fields
    bool_fields = {
        "private",
        "has_issues",
        "has_projects",
        "has_wiki",
        "has_discussions",
        "is_template",
        "allow_squash_merge",
        "allow_merge_commit",
        "allow_rebase_merge",
        "allow_auto_merge",
        "delete_branch_on_merge",
        "allow_update_branch",
        "archived",
        "web_commit_signoff_required",
    }

    for field in bool_fields:
        if field in repo_config and not isinstance(repo_config[field], bool):
            raise ConfigError(f"Repository setting '{field}' must be a boolean")

    string_fields = {
        "name",
        "description",
        "homepage",
        "default_branch",
        "visibility",
        "squash_merge_commit_title",
        "squash_merge_commit_message",
        "merge_commit_title",
        "merge_commit_message",
    }

    for field in string_fields:
        if field in repo_config and not isinstance(repo_config[field], str):
            raise ConfigError(f"Repository setting '{field}' must be a string")


def validate_labels_config(labels_config: Any) -> None:
    """Validate labels configuration."""
    if not isinstance(labels_config, list):
        raise ConfigError("'labels' must be an array")

    for i, label in enumerate(labels_config):
        if not isinstance(label, dict):
            raise ConfigError(f"Label at index {i} must be an object")

        if "name" not in label:
            raise ConfigError(f"Label at index {i} is missing required 'name' field")

        if "color" not in label:
            raise ConfigError(f"Label at index {i} is missing required 'color' field")

        unknown_keys = set(label.keys()) - VALID_LABEL_KEYS
        if unknown_keys:
            logger.warning(f"Unknown label keys at index {i}: {unknown_keys}")

        # Validate color format (6 hex characters, without #)
        color = label["color"]
        if isinstance(color, str):
            color = color.lstrip("#")
            if len(color) != 6 or not all(c in "0123456789abcdefABCDEF" for c in color):
                raise ConfigError(
                    f"Label '{label['name']}' has invalid color format. Use 6 hex characters (e.g., 'ff0000')"
                )


def validate_rulesets_config(rulesets_config: Any) -> None:
    """Validate rulesets configuration."""
    if not isinstance(rulesets_config, list):
        raise ConfigError("'rulesets' must be an array")

    for i, ruleset in enumerate(rulesets_config):
        if not isinstance(ruleset, dict):
            raise ConfigError(f"Ruleset at index {i} must be an object")

        if "name" not in ruleset:
            raise ConfigError(f"Ruleset at index {i} is missing required 'name' field")

        name = ruleset["name"]

        # Validate target
        if "target" in ruleset:
            if ruleset["target"] not in ("branch", "tag"):
                raise ConfigError(
                    f"Ruleset '{name}' target must be 'branch' or 'tag'"
                )

        # Validate enforcement
        if "enforcement" in ruleset:
            if ruleset["enforcement"] not in ("active", "evaluate", "disabled"):
                raise ConfigError(
                    f"Ruleset '{name}' enforcement must be 'active', 'evaluate', or 'disabled'"
                )

        # Validate branches (shorthand)
        if "branches" in ruleset:
            if not isinstance(ruleset["branches"], list):
                raise ConfigError(f"Ruleset '{name}' branches must be an array")

        # Validate rules
        if "rules" in ruleset:
            if not isinstance(ruleset["rules"], dict):
                raise ConfigError(f"Ruleset '{name}' rules must be an object")

            rules = ruleset["rules"]
            unknown_rules = set(rules.keys()) - VALID_RULESET_RULES_KEYS
            if unknown_rules:
                logger.warning(f"Unknown rules in ruleset '{name}': {unknown_rules}")

            # Validate pull_request rules
            if "pull_request" in rules:
                pr = rules["pull_request"]
                if not isinstance(pr, dict):
                    raise ConfigError(
                        f"Ruleset '{name}' pull_request rules must be an object"
                    )
                if "required_approving_review_count" in pr:
                    count = pr["required_approving_review_count"]
                    if not isinstance(count, int) or count < 0 or count > 10:
                        raise ConfigError(
                            f"Ruleset '{name}' required_approving_review_count must be 0-10"
                        )

            # Validate required_status_checks
            if "required_status_checks" in rules:
                rsc = rules["required_status_checks"]
                if not isinstance(rsc, dict):
                    raise ConfigError(
                        f"Ruleset '{name}' required_status_checks must be an object"
                    )
                if "contexts" in rsc and not isinstance(rsc["contexts"], list):
                    raise ConfigError(
                        f"Ruleset '{name}' required_status_checks.contexts must be an array"
                    )
