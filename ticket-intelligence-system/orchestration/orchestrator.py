from __future__ import annotations

import json
from uuid import uuid4
from agents.planner import TicketPlanningAgent
from agents.executor import TicketExecutionAgent
from agents.jira_action import JiraActionAgent
from config.settings import Settings
from jira.service import JiraService
from memory.store import MemoryStore
from models import ExecutionContext, ExecutionStatus
from retrieval.ticket_service import TicketService


class Orchestrator:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()
        data_file = self.settings.resolved_data_file()
        self.memory = MemoryStore(self.settings.chroma_directory)
        self.tickets = TicketService(data_file)
        self.jira = JiraService(self.settings)
        self.planner = TicketPlanningAgent(self.settings.planner_model)
        self.executor = TicketExecutionAgent(self.settings.executor_model, self.tickets, self.memory, self.settings.low_relevance_threshold, self.settings.search_result_limit, self.settings.create_ticket_confidence_threshold)
        self.jira_agent = JiraActionAgent(self.settings.jira_action_model, self.jira, self.memory)

    def run(self, question: str) -> dict:
        run_id = f"RUN-{uuid4().hex[:8].upper()}"
        plan = self.planner.plan(question)
        context = ExecutionContext(run_id=run_id, user_question=question, plan=plan)
        runtime = self.jira.create_issue(f"Ticket Intelligence Execution - {run_id}", f"Run ID: {run_id}\nPlan ID: {plan.plan_id}\nUser request: {question}", ["ticket-intelligence", "runtime-execution"])
        runtime_key = runtime.get("key")
        for step in plan.steps:
            result = self.executor.execute(run_id, plan, step, context.previous_step_results)
            context.previous_step_results.append(result)
            self.memory.clear_working()
            if runtime_key:
                self.jira.add_comment(runtime_key, {"event_type": "STEP_COMPLETED", **result.model_dump(mode="json")})
            if result.status in {ExecutionStatus.MISSING_DATA, ExecutionStatus.FAILED, ExecutionStatus.BLOCKED}:
                context.missing_information.extend(result.missing_information)
                break
            if result.action_required:
                if result.jira_action and result.jira_action.get("requested_action") == "CREATE_NEW_USER_REQUEST_TICKET":
                    candidates = result.jira_action.get("candidate_ticket_ids", [])
                    highest_relevance = max(
                        (
                            finding.get("relevance", 0.0)
                            for finding in result.findings
                            if finding.get("ticket_id") in candidates
                        ),
                        default=0.0,
                    )
                    # This is the final safety gate: a fetched ticket at or above
                    # the confidence threshold always prevents ticket creation.
                    if highest_relevance >= self.settings.create_ticket_confidence_threshold:
                        continue
                    action_finding = {
                        "category": "USER_REQUEST",
                        "finding_type": "NEW_USER_REQUEST_TICKET",
                        "business_event": "NO_RELEVANT_HISTORICAL_TICKET",
                        "request": question,
                        "candidate_ticket_ids": result.jira_action.get("candidate_ticket_ids", []),
                    }
                    if not self.memory.find(action_finding):
                        action = self.jira_agent.act(run_id, action_finding)
                        context.jira_actions.append(action.model_dump())
                    if result.next_action == "STOP":
                        break
                else:
                    for finding in result.findings:
                        action_finding = {**finding}
                        if finding.get("churned"):
                            action_finding["finding_type"] = "CHURN_AFTER_ISSUE"
                        if not self.memory.find(action_finding):
                            action = self.jira_agent.act(run_id, action_finding)
                            context.jira_actions.append(action.model_dump())
        final = {"run_id": run_id, "plan_id": plan.plan_id, "runtime_jira_issue": runtime_key, "fresh_findings": [f for r in context.previous_step_results for f in r.findings], "recalled_findings": context.recalled_findings, "jira_actions": context.jira_actions, "missing_information": context.missing_information, "execution": "COMPLETED" if not context.missing_information else "BLOCKED", "steps_completed": len(context.previous_step_results), "steps_total": len(plan.steps)}
        if runtime_key:
            self.jira.add_comment(runtime_key, {"event_type": "FINAL_RESULT", "result": final})
        return final
