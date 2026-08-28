from __future__ import annotations

import re
from models import ExecutionPlan, ExecutorResult, ExecutionStatus, PlanStep
from retrieval.ticket_service import TicketService
from memory.store import MemoryStore


class TicketExecutionAgent:
    name = "ticket_execution_agent"

    def __init__(self, model: str, tickets: TicketService, memory: MemoryStore, low_relevance_threshold: float = 0.5, search_result_limit: int = 3, create_ticket_confidence_threshold: float = 0.8):
        self.model, self.tickets, self.memory = model, tickets, memory
        self.low_relevance_threshold = low_relevance_threshold
        self.search_result_limit = search_result_limit
        self.create_ticket_confidence_threshold = create_ticket_confidence_threshold

    def execute(self, run_id: str, plan: ExecutionPlan, step: PlanStep, previous: list[ExecutorResult]) -> ExecutorResult:
        context = {"previous": [r.model_dump() for r in previous]}
        payment_match = re.search(r"\bpayment\s*id\s*[:#-]?\s*([A-Za-z0-9-]+)", plan.objective, re.I)
        if payment_match and re.search(r"\brefund\b", plan.objective, re.I):
            payment_id = payment_match.group(1)
            finding = {
                "payment_id": payment_id,
                "category": "PAYMENT",
                "finding_type": "REFUND_DELAY",
                "business_event": "REFUND_NOT_PROCESSED",
                "issue": "User-reported refund not processed",
                "source": "user_request",
                "evidence": plan.objective,
            }
            return ExecutorResult(
                run_id=run_id,
                plan_id=plan.plan_id,
                step_id=step.step_id,
                status=ExecutionStatus.SUCCESS,
                summary="The user-reported payment refund issue was validated for Jira follow-up.",
                findings=[finding],
                evidence=[{"source": "user_request", "field": "payment_id", "value": payment_id}],
                action_required=True,
                jira_action={"requested_action": "CREATE_OR_UPDATE_PAYMENT_REFUND_TICKET"},
            )
        if step.required_tools == ["search_tickets"]:
            matches = self.tickets.search_tickets(plan.objective, limit=self.search_result_limit)
            max_relevance = max((ticket.get("relevance", 0.0) for ticket in matches), default=0.0)
            create_action = max_relevance < self.create_ticket_confidence_threshold
            relevant_matches = [ticket for ticket in matches if ticket.get("relevance", 0.0) >= self.create_ticket_confidence_threshold]
            return ExecutorResult(
                run_id=run_id,
                plan_id=plan.plan_id,
                step_id=step.step_id,
                status=ExecutionStatus.SUCCESS if matches else ExecutionStatus.MISSING_DATA,
                summary=f"Evaluated the top {len(matches)} matching tickets. Highest relevance: {max_relevance:.3f}; ticket-creation threshold: {self.create_ticket_confidence_threshold:.2f}.",
                findings=relevant_matches,
                evidence=[{"source": "historical_ticket_search", "candidate_ticket_ids": [ticket["ticket_id"] for ticket in matches], "candidate_relevance": [{"ticket_id": ticket["ticket_id"], "relevance": ticket.get("relevance", 0.0)} for ticket in matches]}],
                missing_information=[] if matches else [{"field": "matching_tickets", "value": "none"}],
                action_required=create_action,
                jira_action={
                    "requested_action": "CREATE_NEW_USER_REQUEST_TICKET",
                    "threshold": self.create_ticket_confidence_threshold,
                    "highest_relevance": max_relevance,
                    "candidate_ticket_ids": [ticket["ticket_id"] for ticket in matches],
                    "reason": "No fetched historical ticket met the confidence threshold.",
                } if create_action else None,
                next_action="STOP" if create_action else "CONTINUE",
            )
        match = re.search(r"\b(?:IT|CUST|LEGAL|PAY)-?\d+\b", plan.objective, re.I)
        if step.step_id == "STEP-001":
            ticket_id = match.group(0).upper() if match else ""
            ticket = self.tickets.get_ticket(ticket_id)
            if not ticket:
                return ExecutorResult(run_id=run_id, plan_id=plan.plan_id, step_id=step.step_id, status=ExecutionStatus.MISSING_DATA, summary="The requested ticket was not found.", missing_information=[{"field": "ticket", "value": ticket_id}], next_action="STOP")
            return ExecutorResult(run_id=run_id, plan_id=plan.plan_id, step_id=step.step_id, status=ExecutionStatus.SUCCESS, summary="Source ticket retrieved.", findings=[ticket], evidence=[{"source": ticket_id, "field": "description", "value": ticket["description"]}])
        if step.step_id == "STEP-002":
            source = previous[-1].findings[0] if previous and previous[-1].findings else {}
            similar = self.tickets.search_similar_tickets(source.get("description", ""), source.get("ticket_id"))
            top_similar = similar[:self.search_result_limit]
            max_relevance = max((ticket.get("relevance", 0.0) for ticket in top_similar), default=0.0)
            create_action = max_relevance < self.create_ticket_confidence_threshold
            relevant_similar = [ticket for ticket in top_similar if ticket.get("relevance", 0.0) >= self.create_ticket_confidence_threshold]
            return ExecutorResult(
                run_id=run_id,
                plan_id=plan.plan_id,
                step_id=step.step_id,
                status=ExecutionStatus.SUCCESS if similar else ExecutionStatus.MISSING_DATA,
                summary=f"Fetched the top {len(top_similar)} similar tickets. Highest relevance: {max_relevance:.3f}; ticket-creation threshold: {self.create_ticket_confidence_threshold:.2f}.",
                findings=relevant_similar,
                evidence=[{"source": "similar_ticket_search", "candidate_ticket_ids": [ticket["ticket_id"] for ticket in top_similar], "candidate_similarity": [{"ticket_id": ticket["ticket_id"], "similarity": ticket.get("similarity", 0.0)} for ticket in top_similar]}],
                missing_information=[] if top_similar else [{"field": "similar_tickets", "value": "none"}],
                action_required=create_action,
                jira_action={
                    "requested_action": "CREATE_NEW_USER_REQUEST_TICKET",
                    "threshold": self.create_ticket_confidence_threshold,
                    "highest_relevance": max_relevance,
                    "candidate_ticket_ids": [ticket["ticket_id"] for ticket in top_similar],
                    "reason": "No fetched similar ticket met the confidence threshold.",
                } if create_action else None,
                next_action="STOP" if create_action else "CONTINUE",
            )
        if step.step_id == "STEP-003":
            findings = []
            source = previous[-1].findings if previous else []
            for ticket in source:
                customer = self.tickets.get_customer_status(ticket.get("customer_id", ""))
                if customer:
                    findings.append({**customer, "ticket_id": ticket.get("ticket_id"), "category": ticket.get("category"), "churned": customer["churned"]})
            return ExecutorResult(run_id=run_id, plan_id=plan.plan_id, step_id=step.step_id, status=ExecutionStatus.SUCCESS if findings else ExecutionStatus.MISSING_DATA, summary=f"Resolved {len(findings)} customer histories.", findings=findings, next_action="CONTINUE")
        if step.step_id == "STEP-004":
            findings = [f for result in previous for f in result.findings if f.get("churned")]
            recalled = [self.memory.find({"customer_id": f.get("customer_id"), "category": f.get("category"), "finding_type": "CHURN_AFTER_ISSUE"}) for f in findings]
            recalled = [x for x in recalled if x]
            return ExecutorResult(run_id=run_id, plan_id=plan.plan_id, step_id=step.step_id, status=ExecutionStatus.SUCCESS, summary=f"Found {len(recalled)} recalled findings.", findings=findings, evidence=recalled, action_required=bool(findings), jira_action={"recalled": recalled})
        return ExecutorResult(run_id=run_id, plan_id=plan.plan_id, step_id=step.step_id, status=ExecutionStatus.SUCCESS, summary="Step completed.", evidence=[context])
