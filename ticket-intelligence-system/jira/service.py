from __future__ import annotations

import base64
import json
from typing import Any
import requests
from config.settings import Settings


class JiraService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.comments: list[dict[str, Any]] = []
        self.issues: list[dict[str, Any]] = []

    @staticmethod
    def _validate_issue_payload(payload: dict[str, Any]) -> None:
        fields = payload.get("fields", {})
        if not fields.get("project", {}).get("key"):
            raise ValueError("JIRA_PROJECT_KEY is required.")
        if not fields.get("summary"):
            raise ValueError("Jira issue summary is required.")
        if fields.get("description", {}).get("type") != "doc":
            raise ValueError("Jira Cloud descriptions must use Atlassian Document Format.")
        if not fields.get("issuetype", {}).get("name"):
            raise ValueError("JIRA_ISSUE_TYPE is required.")

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if self.settings.dry_run:
            return {}
        if not self.settings.jira_base_url or "your-domain.atlassian.net" in self.settings.jira_base_url:
            raise ValueError("JIRA_BASE_URL is still a placeholder. Set JIRA_DRY_RUN=true or configure a real Jira URL.")
        token = base64.b64encode(f"{self.settings.jira_email}:{self.settings.jira_api_token}".encode()).decode()
        response = requests.request(method, f"{self.settings.jira_base_url.rstrip('/')}{path}", json=payload, timeout=self.settings.jira_timeout_seconds, headers={"Authorization": f"Basic {token}", "Accept": "application/json", "Content-Type": "application/json"})
        if response.status_code >= 400:
            try:
                details = response.json()
            except ValueError:
                details = response.text[:500]
            raise RuntimeError(f"Jira API error {response.status_code}: {details}")
        return response.json() if response.content else {}

    def create_issue(self, summary: str, description: str, labels: list[str]) -> dict[str, Any]:
        description_document = {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": [{"type": "text", "text": description}]}]}
        payload = {"fields": {"project": {"key": self.settings.jira_project_key}, "summary": summary, "description": description_document, "issuetype": {"name": self.settings.jira_issue_type}, "labels": labels}}
        self._validate_issue_payload(payload)
        if self.settings.dry_run:
            issue = {"key": f"{self.settings.jira_project_key}-DRY-{len(self.issues)+1}", "fields": payload["fields"]}
            self.issues.append(issue)
            return issue
        return self._request("POST", "/rest/api/3/issue", payload)

    def add_comment(self, issue_key: str, value: dict[str, Any]) -> dict[str, Any]:
        self.comments.append({"issue_key": issue_key, "body": value})
        if self.settings.dry_run:
            return {"issue_key": issue_key, "body": value}
        return self._request("POST", f"/rest/api/3/issue/{issue_key}/comment", {"body": {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": [{"type": "text", "text": json.dumps(value)}]}]}})

    def transition_issue(self, issue_key: str, transition_id: str) -> dict[str, Any]:
        if self.settings.dry_run:
            return {"issue_key": issue_key, "transition": transition_id}
        return self._request("POST", f"/rest/api/3/issue/{issue_key}/transitions", {"transition": {"id": transition_id}})
