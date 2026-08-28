from __future__ import annotations

import re
from uuid import uuid4
from models import ExecutionPlan, PlanStep


class TicketPlanningAgent:
    name = "ticket_planning_agent"

    def __init__(self, model: str):
        self.model = model

    def plan(self, question: str) -> ExecutionPlan:
        payment_match = re.search(r"\bpayment\s*id\s*[:#-]?\s*([A-Za-z0-9-]+)", question, re.I)
        ticket_match = re.search(r"\b(?:IT|CUST|LEGAL|PAY)-?\d+\b", question, re.I)
        steps = []
        if payment_match and re.search(r"\brefund\b", question, re.I):
            payment_id = payment_match.group(1)
            steps.append(PlanStep(
                step_id="STEP-001",
                sequence=1,
                description=f"Validate the user-reported delayed refund for payment {payment_id}.",
                purpose="Capture the supplied payment identifier and refund issue as an actionable finding without inventing transaction facts.",
                required_tools=["validate_payment_issue"],
                expected_output="Validated payment refund issue",
            ))
        elif ticket_match:
            ticket_id = ticket_match.group(0).upper()
            steps.extend([
                PlanStep(step_id="STEP-001", sequence=1, description=f"Retrieve ticket {ticket_id}.", purpose="Understand the source issue.", required_tools=["get_ticket"], expected_output="Source ticket details"),
                PlanStep(step_id="STEP-002", sequence=2, description="Find historical tickets with the same issue.", purpose="Identify comparable incidents.", depends_on=["STEP-001"], required_tools=["search_similar_tickets"], expected_output="Similar tickets"),
                PlanStep(step_id="STEP-003", sequence=3, description="Map similar tickets to customers and retrieve customer history.", purpose="Perform multi-hop customer analysis.", depends_on=["STEP-002"], required_tools=["get_customer_tickets", "get_customer_status"], expected_output="Customer status results"),
                PlanStep(step_id="STEP-004", sequence=4, description="Check prior findings and prevent duplicate actions.", purpose="Separate recalled from fresh findings.", depends_on=["STEP-003"], required_tools=["search_long_term_memory"], expected_output="Memory matches"),
            ])
        else:
            steps.append(PlanStep(step_id="STEP-001", sequence=1, description="Search the historical ticket dataset for the requested information.", purpose="Find evidence for the question.", required_tools=["search_tickets"], expected_output="Matching tickets"))
        return ExecutionPlan(plan_id=f"PLAN-{uuid4().hex[:8].upper()}", objective=question, steps=steps)
