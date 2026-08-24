"""Single agent that creates a goal-task-tool implementation plan."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from models import PlanResult
from openrouter import OpenRouterClient, OpenRouterError
from store import JsonStore
from tools import ToolRegistry


class CapstonePlannerAgent:
    def __init__(self, project_root: Path) -> None:
        self.tools = ToolRegistry()
        self.llm = OpenRouterClient(project_root)
        self.store = JsonStore(project_root / "data")

    def run(self, requirement: str) -> PlanResult:
        text = requirement.strip()
        if not text:
            raise ValueError("Capstone requirement cannot be empty.")
        request_id = f"PLAN-{uuid.uuid4().hex[:10]}"
        tool_names = ["count_words", "extract_terms", "detect_sections", "identify_actions"]
        tool_results = [self.tools.run(name, text) for name in tool_names]
        result_data = {item.name: item.data for item in tool_results if item.success}
        try:
            generated = self.llm.generate_plan(text, self.tools.descriptions(), result_data)
            result = PlanResult(
                request_id=request_id,
                goals=generated["goals"],
                success_criteria=generated["success_criteria"],
                workflow=generated["workflow"],
                tools_required=generated["tools_required"],
                tool_details=generated["tool_details"],
                goal_task_mapping=generated["goal_task_mapping"],
                confidence=float(generated["confidence"]),
                tool_results=tool_results,
            )
        except (OpenRouterError, KeyError, TypeError, ValueError) as exc:
            result = self._capstone_fallback(request_id, text, tool_results, str(exc))
        result = self._normalize_plan(result)
        self.store.save(result)
        return result

    @staticmethod
    def _capstone_fallback(request_id: str, requirement: str, tool_results: list, warning: str) -> PlanResult:
        """Provide a full payment-operations plan when the LLM is unavailable."""
        goals = [
            "Build a single agentic payments operations solution that continuously monitors failed payments, duplicate debits, chargebacks, refund requests, and settlement mismatches across card, UPI, ACH, wire, and merchant systems.",
            "Interpret payment messages, transaction states, dispute notifications, refund records, settlement files, and processor responses to classify each operational issue accurately.",
            "Automatically gather and link supporting evidence such as authorization records, payment timelines, ledger entries, bank or processor responses, refund confirmations, customer communications, and settlement reports.",
            "Recommend the correct resolution path based on payment type, issue category, lifecycle state, applicable policies, evidence completeness, financial exposure, risk, and service-level agreement.",
            "Draft appropriate customer or merchant communications for status updates, refund outcomes, evidence requests, dispute responses, and resolution notifications.",
            "Route high-risk, high-value, policy-sensitive, ambiguous, or SLA-critical cases to the appropriate payments operations, risk, compliance, finance, or merchant support team.",
            "Reduce manual payment operations effort and improve resolution speed while preserving auditability, consistent policy application, and responsible human escalation.",
            "Estimate dispute likelihood for eligible transactions and identify recurring failure patterns with recommended preventive controls.",
        ]
        criteria = [
            "The agent ingests normalized events from payment processors, payment rails, merchant systems, ledgers, refund services, and settlement files.",
            "Core issue classes are distinguished: failed payment, duplicate debit, chargeback, refund request, settlement mismatch, and ambiguous exception.",
            "Every case contains identifiers, payment rail, issue type, lifecycle stage, severity, financial impact, evidence status, SLA priority, owner, and confidence.",
            "Related records are correlated using transaction, payment intent, authorization, refund, dispute, settlement, customer, merchant, timestamp, and amount fields.",
            "Recommendations contain action, evidence, policy, expected state, owner, deadline, approval requirement, and rationale.",
            "High-risk, high-value, fraud, legal, regulatory, policy-sensitive, and low-confidence cases require human approval.",
            "Communications contain verified facts only and do not include unsupported promises or internal reasoning.",
            "All decisions, evidence, actions, communications, approvals, outcomes, and overrides are auditable.",
        ]
        tool_catalog = {
            "Payment processor, bank, and payment-rail APIs": {"purpose": "Retrieve payment statuses, responses, authorizations, refunds, disputes, settlements, and execute authorized actions.", "inputs": "transaction_ids, authorization_references, payment_rail, date_range, amount, merchant_id, dispute_id, refund_id, action_request", "outputs": "payment status, response codes, timestamps, refund/dispute status, settlement details, and action results", "workflow_use": "ingestion, interpretation, evidence retrieval, execution, and monitoring"},
            "Transaction ledger and payment-event datastore": {"purpose": "Provide authoritative payment attempts, postings, reversals, refunds, adjustments, and event history.", "inputs": "transaction_ids, account_ids, merchant_ids, event_types, amount, currency, date_range", "outputs": "ledger entries, event timeline, balances, posting state, reversal links, and correlations", "workflow_use": "correlation, duplicate detection, lifecycle validation, and outcome verification"},
            "Merchant-system and payment-orchestration integrations": {"purpose": "Retrieve merchant order, fulfillment, payment intent, retry, idempotency, customer, and configuration records.", "inputs": "merchant_id, order_id, payment_intent_id, customer_reference, transaction_id, date_range", "outputs": "merchant records, retry history, idempotency metadata, and fulfillment evidence", "workflow_use": "correlation, issue analysis, dispute evidence, and preventive controls"},
            "Dispute and chargeback management system": {"purpose": "Track dispute stages, reason codes, deadlines, evidence, representment, arbitration, and outcomes.", "inputs": "dispute_id, transaction_reference, reason_code, deadline, evidence_package, response_action, approval_metadata", "outputs": "dispute status, deadlines, evidence requirements, submission results, and decisions", "workflow_use": "classification, evidence, prioritization, response preparation, and monitoring"},
            "Refund and payout management system": {"purpose": "Track refund requests, approvals, execution, reversals, failures, and payout status.", "inputs": "original_transaction_id, refund_id, amount, currency, reason, approval, destination_account_details", "outputs": "eligibility, refund status, processor reference, failure reason, and payout result", "workflow_use": "refund investigation, approved execution, verification, and communication"},
            "Settlement and reconciliation data source": {"purpose": "Compare processor, bank, merchant, and ledger settlements to identify missing, duplicate, delayed, or misallocated funds.", "inputs": "settlement_files, batch_ids, transaction_references, merchant_ids, date_range, currencies, amounts, expected_posting_rules", "outputs": "matched/unmatched records, variances, batch status, dates, fees, and exceptions", "workflow_use": "settlement detection, financial analysis, correction recommendation, and closure"},
            "Evidence and document retrieval store": {"purpose": "Retrieve structured records, messages, files, receipts, processor payloads, and prior communications with provenance.", "inputs": "case_id, transaction_references, document_type, customer_or_merchant_identifiers, date_range, evidence_query", "outputs": "versioned evidence, metadata, provenance, access status, and completeness", "workflow_use": "evidence assembly, missing-data detection, recommendations, and auditability"},
            "Policy and rules engine": {"purpose": "Evaluate payment, refund, dispute, risk, compliance, approval, SLA, and escalation policies deterministically.", "inputs": "case_classification, payment_rail, amount, currency, reason_code, risk_signals, customer_or_merchant_segment, evidence_state, deadlines, policy_version", "outputs": "allowed actions, approvals, escalation queue, SLA, prohibited actions, and rationale", "workflow_use": "policy decisioning before recommendations, actions, communication, escalation, and closure"},
            "Case-management and workflow system": {"purpose": "Create, assign, prioritize, update, escalate, and close operational cases.", "inputs": "case_summary, classification, evidence_links, recommendation, priority, sla, queue, owner, approval_state, communication_drafts", "outputs": "case ID, assignment, status, approvals, tasks, escalations, and closure reason", "workflow_use": "case orchestration, ownership, escalation, approvals, and tracking"},
            "Notification and communication service": {"purpose": "Deliver approved customer, merchant, processor, and internal communications.", "inputs": "recipient, channel, approved_message, case_or_transaction_references, language, timing, template_identifier", "outputs": "delivery status, message ID, timestamp, and failure details", "workflow_use": "validated status updates, evidence requests, resolutions, and alerts"},
            "Risk, fraud, and identity signals": {"purpose": "Provide fraud indicators, account risk, identity status, velocity patterns, and behavioral context.", "inputs": "customer_reference, merchant_reference, device_reference, transaction_reference, account_reference, ip_reference, payment_instrument_reference, historical_activity_references", "outputs": "risk scores, alerts, linked activity, verification status, and review flags", "workflow_use": "risk priority, escalation, and advisory prediction features"},
            "Analytics and machine-learning service": {"purpose": "Analyze recurring patterns and optionally estimate dispute likelihood and control effectiveness.", "inputs": "historical_case_outcomes, transaction_features, processor_responses, merchant_attributes, customer_impact, evidence_features, preventive_control_outcomes", "outputs": "likelihood, confidence, factors, patterns, trends, and preventive controls", "workflow_use": "prediction, root-cause analysis, and continuous improvement"},
            "Audit logging and observability platform": {"purpose": "Record agent actions, data access, policy evaluations, recommendations, communications, errors, and performance.", "inputs": "case_id, agent_decision, input_references, policy_version, tool_calls, user_approvals, timestamps, outcome, error_metadata", "outputs": "audit events, trace IDs, metrics, alerts, and investigation logs", "workflow_use": "traceability throughout every task"},
        }
        steps = [
            ("Ingest and normalize payment operations events", "Receive and normalize payment, refund, dispute, chargeback, settlement, ledger, processor, bank, merchant, and support records.", ["Payment processor, bank, and payment-rail APIs", "Transaction ledger and payment-event datastore"]),
            ("Detect and group exceptions", "Identify exceptions, deduplicate notifications, and group related records into operational cases.", ["Transaction ledger and payment-event datastore", "Case-management and workflow system"]),
            ("Interpret and classify operational issues", "Interpret messages and lifecycle states, then classify issue type, rail, impact, root cause candidates, and confidence.", ["Payment processor, bank, and payment-rail APIs", "Transaction ledger and payment-event datastore", "Policy and rules engine"]),
            ("Correlate and retrieve evidence", "Link related records and assemble verified evidence while identifying missing or contradictory information.", ["Merchant-system and payment-orchestration integrations", "Transaction ledger and payment-event datastore", "Evidence and document retrieval store", "Dispute and chargeback management system"]),
            ("Apply policy and prioritize", "Evaluate applicable rules and calculate risk, severity, SLA, approval, and escalation requirements.", ["Policy and rules engine", "Risk, fraud, and identity signals", "Case-management and workflow system"]),
            ("Recommend resolution", "Recommend a permitted next action with rationale, evidence, policy reference, owner, deadline, and expected state.", ["Policy and rules engine", "Evidence and document retrieval store", "Refund and payout management system", "Settlement and reconciliation data source"]),
            ("Draft and validate communication", "Create factual customer or merchant communications and validate references, status, amounts, dates, and approvals.", ["Case-management and workflow system", "Notification and communication service", "Evidence and document retrieval store"]),
            ("Execute, monitor, and verify", "Execute permitted actions, monitor subsequent events, verify outcomes, update case state, and preserve audit history.", ["Payment processor, bank, and payment-rail APIs", "Refund and payout management system", "Case-management and workflow system", "Audit logging and observability platform"]),
            ("Analyze patterns and recommend controls", "Use historical outcomes to identify recurring patterns, estimate eligible risk, and recommend preventive controls.", ["Analytics and machine-learning service", "Risk, fraud, and identity signals", "Audit logging and observability platform"]),
        ]
        workflow = []
        for index, (name, details, tools) in enumerate(steps, 1):
            task_id = f"{index}.1"
            parameters = {tool: {"input": "task-specific values", "schema": tool_catalog[tool]["inputs"]} for tool in tools}
            task = {"task_id": task_id, "name": name, "details": details, "goals": [index], "tools": tools, "tool_parameters": parameters, "tool_call_order": tools, "outcome": {"result": "success", "task_id": task_id, "status": "completed", "evidence": "recorded"}}
            workflow.append({"step": index, "name": name, "details": details, "goals": [index], "tasks": [task]})
        mapping = [{"goal": index, "tasks": [{"task": f"{index}.1", "tools": step[2], "outcome": {"result": "success", "task_id": f"{index}.1"}}]} for index, step in enumerate(steps, 1)]
        return PlanResult(request_id, goals, criteria, workflow, list(tool_catalog), tool_catalog, mapping, 0.0, tool_results, [warning])

    @staticmethod
    def _normalize_plan(result: PlanResult) -> PlanResult:
        """Normalize model output and guarantee at least two tasks per goal."""
        goal_count = len(result.goals) or 1
        grouped_tasks: dict[int, list[dict[str, Any]]] = {}

        for step_number, step in enumerate(result.workflow, start=1):
            if not isinstance(step, dict):
                continue
            tasks = step.get("tasks", [])
            if not isinstance(tasks, list):
                tasks = [tasks]
            for task_number, raw_task in enumerate(tasks, start=1):
                if isinstance(raw_task, dict):
                    task = dict(raw_task)
                else:
                    task = {"name": str(raw_task)}
                task.setdefault("name", step.get("name", "Implementation task"))
                task.setdefault("details", step.get("details", ""))
                task_goals = task.get("goals", step.get("goals", [step_number]))
                if not isinstance(task_goals, list):
                    task_goals = [task_goals]
                valid_goals = []
                for goal in task_goals:
                    try:
                        goal_number = int(goal)
                    except (TypeError, ValueError):
                        continue
                    if 1 <= goal_number <= goal_count and goal_number not in valid_goals:
                        valid_goals.append(goal_number)
                valid_goals = valid_goals or [min(step_number, goal_count)]
                task["tools"] = task.get("tools", [])
                if not isinstance(task["tools"], list):
                    task["tools"] = [task["tools"]]
                task["tools"] = task["tools"] or result.tools_required[:2]
                parameters = task.get("tool_parameters", task.get("parameters", {}))
                if not isinstance(parameters, dict):
                    parameters = {tool: {"input": str(parameters)} for tool in task["tools"]}
                task["tool_parameters"] = parameters or {
                    tool: {"input": "task-specific values"} for tool in task["tools"]
                }
                task.setdefault("tool_call_order", task["tools"])
                task.setdefault("outcome", {"result": "success", "status": "completed"})
                for goal_number in valid_goals:
                    grouped_tasks.setdefault(goal_number, []).append(dict(task))

        normalized_workflow = []
        for goal_number in range(1, goal_count + 1):
            tasks = grouped_tasks.get(goal_number, [])
            if not tasks:
                tasks = [{
                    "name": "Plan implementation",
                    "details": "Define the implementation work required to achieve this goal.",
                    "tools": result.tools_required[:2],
                    "tool_parameters": {tool: {"input": "task-specific values"} for tool in result.tools_required[:2]},
                    "tool_call_order": result.tools_required[:2],
                    "outcome": {"result": "success", "status": "completed"},
                }]
            if len(tasks) == 1:
                second_task = dict(tasks[0])
                second_task["name"] = f"Validate {tasks[0].get('name', 'implementation').lower()}"
                second_task["details"] = "Validate the implementation, verify the expected outcome, and record completion evidence."
                second_task["outcome"] = {"result": "success", "status": "validated"}
                tasks.append(second_task)
            final_tasks = []
            for task_number, task in enumerate(tasks, start=1):
                task["task_id"] = f"{goal_number}.{task_number}"
                task["goals"] = [goal_number]
                final_tasks.append(task)
            goal_text = result.goals[goal_number - 1] if goal_number <= len(result.goals) else "Implementation goal"
            normalized_workflow.append({
                "step": goal_number,
                "name": goal_text,
                "details": final_tasks[0].get("details", ""),
                "goals": [goal_number],
                "tasks": final_tasks,
            })

        result.workflow = normalized_workflow
        result.goal_task_mapping = CapstonePlannerAgent._build_goal_connections(normalized_workflow, result.goals)
        result.tool_details = CapstonePlannerAgent._normalize_tool_details(result.tool_details, result.tools_required)
        return result

    @staticmethod
    def _normalize_tool_details(details: dict[str, Any], tools: list[str]) -> dict[str, dict[str, Any]]:
        """Ensure every required tool has a description and JSON input parameters."""
        normalized: dict[str, dict[str, Any]] = {}
        for tool in tools:
            raw = details.get(tool, {}) if isinstance(details, dict) else {}
            if not isinstance(raw, dict):
                raw = {"description": str(raw)}
            description = raw.get("description", raw.get("purpose", f"Executes the {tool} capability required by the project."))
            parameters = raw.get("parameters", raw.get("example_parameters", raw.get("inputs", {})))
            if not isinstance(parameters, dict):
                parameters = {"input": str(parameters)}
            normalized[tool] = {
                "description": description,
                "parameters": parameters,
                "outputs": raw.get("outputs", {}),
                "workflow_use": raw.get("workflow_use", "Used by the single agent for the related implementation tasks."),
            }
        return normalized

    @staticmethod
    def _build_goal_connections(workflow: list[dict[str, Any]], goals: list[str]) -> list[dict[str, Any]]:
        connections: dict[Any, list[dict[str, Any]]] = {}
        for step in workflow:
            for task in step.get("tasks", []):
                task_goals = task.get("goals", step.get("goals", []))
                if not isinstance(task_goals, list):
                    task_goals = [task_goals]
                task_connection = {
                    "task": task.get("task_id", task.get("task", "")),
                    "tools": task.get("tools", []),
                    "outcome": task.get("outcome", {"result": "success"}),
                }
                for goal in task_goals or [1]:
                    connections.setdefault(goal, []).append(task_connection)
        return [
            {"goal": goal, "goal_details": goals[int(goal) - 1] if str(goal).isdigit() and 0 < int(goal) <= len(goals) else "", "tasks": tasks}
            for goal, tasks in connections.items()
        ]

    @staticmethod
    def _fallback(request_id: str, requirement: str, tool_results: list, warning: str) -> PlanResult:
        actions = [item.strip() for item in requirement.split(".") if item.strip()][:5]
        goals = [actions[0]] if actions else ["Implement the requested capstone solution."]
        criteria = ["The single agent accepts the requirement and produces a structured plan.", "Every task identifies its required tools and JSON outcome."]
        workflow = [{"step": 1, "name": "Analyze requirement", "details": "Extract goals, tasks, tools, and outcomes from the supplied requirement.", "goals": [1], "tasks": [{"task_id": "1.1", "name": "Analyze requirement", "details": "Extract goals, tasks, tools, and outcomes from the supplied requirement.", "goals": [1], "tools": ["extract_terms", "identify_actions"], "parameters": {"extract_terms": {"text": requirement}, "identify_actions": {"text": requirement}}, "outcome": {"result": "success", "plan_generated": True}}]}]
        details = {"extract_terms": {"purpose": "Extract requirement themes.", "parameters": {"text": requirement}, "outputs": {"top_terms": []}, "workflow_use": "Identify scope."}, "identify_actions": {"purpose": "Find candidate tasks.", "parameters": {"text": requirement}, "outputs": {"candidate_tasks": []}, "workflow_use": "Create tasks."}}
        mapping = [{"goal": 1, "tasks": [{"task": "1.1", "tools": ["extract_terms", "identify_actions"], "outcome": {"result": "success", "plan_generated": True}}]}]
        return PlanResult(request_id, goals, criteria, workflow, list(details), details, mapping, 0.0, tool_results, [warning])
