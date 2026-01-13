"""
GitHub REST API client using only Python standard library.
"""

import json
import logging
import urllib.request
import urllib.error
from typing import Any, Optional

logger = logging.getLogger(__name__)


class GitHubAPIError(Exception):
    """Custom exception for GitHub API errors."""

    def __init__(self, message: str, status_code: int = 0, response_body: str = ""):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class GitHubClient:
    """GitHub REST API client."""

    BASE_URL = "https://api.github.com"

    def __init__(self, token: str):
        """Initialize the GitHub client with an authentication token."""
        self.token = token
        self.headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "github-settings-sync-action",
        }

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[dict] = None,
    ) -> Optional[dict]:
        """Make an HTTP request to the GitHub API."""
        url = f"{self.BASE_URL}{endpoint}"

        body = None
        if data is not None:
            body = json.dumps(data).encode("utf-8")

        request = urllib.request.Request(
            url,
            data=body,
            headers=self.headers,
            method=method,
        )

        if body:
            request.add_header("Content-Type", "application/json")

        logger.debug(f"{method} {url}")

        try:
            with urllib.request.urlopen(request) as response:
                response_body = response.read().decode("utf-8")
                if response_body:
                    return json.loads(response_body)
                return None
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else ""
            logger.error(f"API error {e.code}: {error_body}")
            raise GitHubAPIError(
                f"GitHub API error: {e.code} {e.reason}",
                status_code=e.code,
                response_body=error_body,
            )
        except urllib.error.URLError as e:
            raise GitHubAPIError(f"Network error: {e.reason}")

    def get(self, endpoint: str) -> Optional[dict]:
        """Make a GET request."""
        return self._request("GET", endpoint)

    def post(self, endpoint: str, data: dict) -> Optional[dict]:
        """Make a POST request."""
        return self._request("POST", endpoint, data)

    def patch(self, endpoint: str, data: dict) -> Optional[dict]:
        """Make a PATCH request."""
        return self._request("PATCH", endpoint, data)

    def put(self, endpoint: str, data: dict) -> Optional[dict]:
        """Make a PUT request."""
        return self._request("PUT", endpoint, data)

    def delete(self, endpoint: str) -> Optional[dict]:
        """Make a DELETE request."""
        return self._request("DELETE", endpoint)

    # Repository methods
    def get_repository(self, owner: str, repo: str) -> dict:
        """Get repository information."""
        result = self.get(f"/repos/{owner}/{repo}")
        if result is None:
            raise GitHubAPIError(f"Repository {owner}/{repo} not found")
        return result

    def update_repository(self, owner: str, repo: str, settings: dict) -> dict:
        """Update repository settings."""
        result = self.patch(f"/repos/{owner}/{repo}", settings)
        if result is None:
            raise GitHubAPIError("Failed to update repository")
        return result

    # Labels methods
    def get_labels(self, owner: str, repo: str) -> list:
        """Get all labels for a repository."""
        result = self.get(f"/repos/{owner}/{repo}/labels")
        return result if result else []

    def create_label(self, owner: str, repo: str, label: dict) -> dict:
        """Create a new label."""
        result = self.post(f"/repos/{owner}/{repo}/labels", label)
        if result is None:
            raise GitHubAPIError(f"Failed to create label: {label.get('name')}")
        return result

    def update_label(
        self, owner: str, repo: str, label_name: str, label: dict
    ) -> dict:
        """Update an existing label."""
        # URL encode the label name for special characters
        encoded_name = urllib.request.quote(label_name, safe="")
        result = self.patch(f"/repos/{owner}/{repo}/labels/{encoded_name}", label)
        if result is None:
            raise GitHubAPIError(f"Failed to update label: {label_name}")
        return result

    def delete_label(self, owner: str, repo: str, label_name: str) -> None:
        """Delete a label."""
        encoded_name = urllib.request.quote(label_name, safe="")
        self.delete(f"/repos/{owner}/{repo}/labels/{encoded_name}")

    # Branch protection methods
    def get_branch_protection(
        self, owner: str, repo: str, branch: str
    ) -> Optional[dict]:
        """Get branch protection rules."""
        try:
            return self.get(f"/repos/{owner}/{repo}/branches/{branch}/protection")
        except GitHubAPIError as e:
            if e.status_code == 404:
                return None
            raise

    def update_branch_protection(
        self, owner: str, repo: str, branch: str, protection: dict
    ) -> dict:
        """Update branch protection rules."""
        result = self.put(
            f"/repos/{owner}/{repo}/branches/{branch}/protection", protection
        )
        if result is None:
            raise GitHubAPIError(f"Failed to update branch protection for: {branch}")
        return result

    def delete_branch_protection(self, owner: str, repo: str, branch: str) -> None:
        """Delete branch protection rules."""
        self.delete(f"/repos/{owner}/{repo}/branches/{branch}/protection")
