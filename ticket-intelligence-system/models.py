from __future__ import annotations

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class ExecutionStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    MISSING_DATA = "MISSING_DATA"


class PlanStep(BaseModel):
    step_id: str
    sequence: int
    description: str
    purpose: str
    depends_on: list[str] = Field(default_factory=list)
    required_tools: list[str]
    expected_output: str


class ExecutionPlan(BaseModel):
    plan_id: str
    objective: str
    steps: list[PlanStep]


class ExecutorResult(BaseModel):
    run_id: str
    plan_id: str
    step_id: str
    status: ExecutionStatus
    summary: str
    findings: list[dict[str, Any]] = Field(default_factory=list)
    missing_information: list[dict[str, Any]] = Field(default_factory=list)
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    action_required: bool = False
    jira_action: dict[str, Any] | None = None
    retry_count: int = 0
    next_action: str = "CONTINUE"


class JiraActionResult(BaseModel):
    action: str
    status: str
    jira_issue: dict[str, Any] | None = None
    reason: str


class ExecutionContext(BaseModel):
    run_id: str
    user_question: str
    plan: ExecutionPlan | None = None
    previous_step_results: list[ExecutorResult] = Field(default_factory=list)
    recalled_findings: list[dict[str, Any]] = Field(default_factory=list)
    jira_actions: list[dict[str, Any]] = Field(default_factory=list)
    missing_information: list[dict[str, Any]] = Field(default_factory=list)
