from __future__ import annotations

from jira.service import JiraService
from memory.store import MemoryStore
from models import JiraActionResult


class JiraActionAgent:
    name = "jira_action_agent"

    def __init__(self, model: str, jira: JiraService, memory: MemoryStore):
        self.model, self.jira, self.memory = model, jira, memory

    def act(self, run_id: str, finding: dict) -> JiraActionResult:
        prior = self.memory.find(finding)
        if prior and prior.get("jira_issue_key"):
            return JiraActionResult(action="NO_ACTION", status="SUCCESS", jira_issue=prior, reason="Finding was already actioned in long-term memory.")
        subject = finding.get("ticket_id") or finding.get("customer_id") or (f"payment {finding.get('payment_id')}" if finding.get("payment_id") else "user request")
        finding_type = finding.get("finding_type", "VALIDATED_BUSINESS_FINDING")
        summary = f"New ticket requested: {finding.get('request', subject)}" if finding_type == "NEW_USER_REQUEST_TICKET" else f"Follow-up required for {subject} {finding.get('category', 'ticket')} finding"
        issue = self.jira.create_issue(summary=summary[:255], description=f"Run: {run_id}\nValidated finding: {finding}", labels=["ticket-intelligence", "business-action", finding_type.lower().replace("_", "-")])
        stored = self.memory.persist_finding({**finding, "finding_type": finding_type, "jira_issue_key": issue.get("key"), "action_status": "ACTIONED", "run_id": run_id})
        return JiraActionResult(action="CREATE", status="SUCCESS", jira_issue={**issue, **stored}, reason="New validated actionable finding.")
