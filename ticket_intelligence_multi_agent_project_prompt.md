

## 1. Project Title

**Ticket Intelligence System — Multi-Agent Planning, Execution, Jira Automation, and ChromaDB Memory**

---

# 2. Role

You are a senior AI systems architect and full-stack engineer responsible for designing and implementing a production-quality multi-agent Ticket Intelligence System.

The system must support:

- Multi-hop reasoning.
- Multiple specialized AI agents.
- Independent model selection per agent.
- Tool registry and controlled tool access.
- Jira integration using the Jira REST API and API token.
- Automatic Jira task creation for runtime user requests.
- Jira task status management.
- JSON-formatted Jira comments containing agent outputs.
- Passing structured JSON outputs between agents.
- ChromaDB-based short-term, working, and long-term memory.
- Context retrieval from historical tickets and previous executions.
- Retry and failure handling.
- Missing-data handling.
- Duplicate-action prevention.
- Full execution traceability.
- Final response generation only after the required execution steps complete successfully.

Do not implement Jira through a custom MCP server.

Jira must be accessed through a dedicated Jira API service/client using a securely configured Jira API token.

---

# 3. Primary Business Requirement

The system must transform the current Planner + Executor architecture into a true multi-agent system.

The existing system can answer compound questions such as:

> "Which customers had the same login issue as ticket 4021, and did any of them churn afterward?"

The new system must additionally:

1. Understand the user's request.
2. Decompose the request into executable steps.
3. Automatically create Jira tasks representing the runtime execution work.
4. Execute those tasks using the Executor Agent.
5. Update Jira task status as execution progresses.
6. Add the Executor's output to Jira as a JSON-formatted comment.
7. Allow subsequent agents to consume the structured JSON output.
8. Use ChromaDB to maintain short-term, working, and long-term memory.
9. Detect previously known findings.
10. Prevent duplicate Jira business tickets/actions where appropriate.
11. Handle missing information without hallucinating.
12. Execute Jira actions automatically when an actionable finding is discovered.
13. Return a final result only after the workflow is completed successfully or clearly report why execution could not be completed.

---

# 4. Important Architectural Decision

Use exactly **three AI agents**:

1. **Ticket Planning Agent**
2. **Ticket Execution Agent**
3. **Jira Action Agent**

Do not create unnecessary AI agents for deterministic application responsibilities.

Use supporting application services for:

- Agent orchestration.
- Jira API communication.
- Ticket/data retrieval.
- Tool registry.
- Memory management.
- Execution tracing.
- Validation.
- Configuration.
- Security.

The architecture should be:

```text
User
  |
  v
Agent Orchestrator
  |
  v
Ticket Planning Agent
  |
  v
Execution Plan
  |
  v
Jira Task Creation
  |
  v
Ticket Execution Agent
  |
  +--------------------+
  |                    |
  v                    v
Tool Registry      ChromaDB Memory
  |                    |
  +---------+----------+
            |
            v
      Step Result JSON
            |
            v
     Jira Action Agent
            |
            v
       Jira API Service
            |
            v
          Jira
            |
            v
      Long-Term Memory
            |
            v
     Final Result Agent/
     Orchestrator Response
```

The final response generation may be implemented as a deterministic orchestration step using structured results. Do not introduce a fourth AI agent unless absolutely required by the existing codebase.

---

# 5. Core Architectural Principle

Every agent must have:

* Its own system .
* Its own model configuration.
* Its own input schema.
* Its own output schema.
* Its own allowed tools.
* Its own retry configuration.
* Its own temperature/token configuration.
* Its own observability metadata.

Do not hard-code one model globally for all agents.

The configuration must allow:

```yaml
agents:

  planner:
    model: <strong_reasoning_model>

  executor:
    model: <cost_optimized_model>

  jira_action:
    model: <lightweight_model>
```

Changing the Planner model must not require changing the Executor or Jira Action Agent.

---

# 6. Agent 1 — Ticket Planning Agent

## 6.1 Objective

The Ticket Planning Agent converts the user's natural-language request into a structured, executable multi-step plan.

It must be optimized for:

* Structured reasoning.
* Dependency identification.
* Multi-hop decomposition.
* Determining required data.
* Determining required tools.
* Determining which steps require Jira interaction.
* Identifying whether a step depends on another step's output.

Use the strongest available reasoning model for this agent.

---

## 6.2 Planner Inputs

The Planner receives:

```json
{
  "run_id": "RUN-001",
  "user_id": "USER-001",
  "user_question": "...",
  "conversation_context": [],
  "relevant_memory": [],
  "available_tools": []
}
```

---

## 6.3 Planner Output

The Planner must return strict JSON.

Example:

```json
{
  "plan_id": "PLAN-001",
  "objective": "Identify customers with the same login issue and determine whether they churned.",
  "steps": [
    {
      "step_id": "STEP-001",
      "sequence": 1,
      "description": "Retrieve ticket IT-001.",
      "purpose": "Understand the original login issue.",
      "depends_on": [],
      "required_tools": ["get_ticket"],
      "expected_output": "Original ticket issue details"
    },
    {
      "step_id": "STEP-002",
      "sequence": 2,
      "description": "Find historical tickets with the same issue.",
      "purpose": "Identify related tickets.",
      "depends_on": ["STEP-001"],
      "required_tools": ["search_similar_tickets"],
      "expected_output": "List of similar tickets"
    },
    {
      "step_id": "STEP-003",
      "sequence": 3,
      "description": "Identify customers associated with the similar tickets.",
      "purpose": "Map tickets to customers.",
      "depends_on": ["STEP-002"],
      "required_tools": ["get_customer"],
      "expected_output": "Customer list"
    },
    {
      "step_id": "STEP-004",
      "sequence": 4,
      "description": "Check customer churn status.",
      "purpose": "Determine whether any related customer churned.",
      "depends_on": ["STEP-003"],
      "required_tools": ["get_customer_status"],
      "expected_output": "Customer churn status"
    },
    {
      "step_id": "STEP-005",
      "sequence": 5,
      "description": "Check historical memory for previously identified findings.",
      "purpose": "Prevent duplicate reporting and Jira actions.",
      "depends_on": ["STEP-004"],
      "required_tools": ["search_long_term_memory"],
      "expected_output": "Previously known findings"
    },
    {
      "step_id": "STEP-006",
      "sequence": 6,
      "description": "Create or update Jira action for new actionable findings.",
      "purpose": "Ensure actionable findings are tracked.",
      "depends_on": ["STEP-005"],
      "required_tools": ["jira_search", "jira_create", "jira_update"],
      "expected_output": "Jira action result"
    }
  ]
}
```

---

# 7. Planner Agent System 

Implement a dedicated Planner system  equivalent to:

```text
You are the Ticket Planning Agent.

Your responsibility is to decompose the user's request into a deterministic,
structured, executable multi-step plan.

You are a planning specialist, not an executor.

Do not retrieve data yourself unless explicitly allowed by the tool policy.

Do not invent data.

Do not invent ticket IDs, customer IDs, Jira IDs, statuses, or business facts.

Analyze the user's question and determine:

1. What information is required.
2. Which source should provide each piece of information.
3. Which steps depend on previous steps.
4. Which tools are required.
5. Which steps may produce actionable findings.
6. Which steps require memory lookup.
7. Which steps may require Jira actions.
8. What information is required before a Jira action is allowed.
9. Which steps can be executed independently.
10. Which steps must execute sequentially.

Return ONLY valid JSON conforming to the Planner output schema.

Every step must include:

- step_id
- sequence
- description
- purpose
- depends_on
- required_tools
- expected_output

Do not include unsupported tools.

Do not create unnecessary steps.

Do not assume information exists.

If the user's request cannot be fully satisfied because required data is unavailable,
create a plan that allows the Executor to explicitly identify the missing data.

The plan must be executable by another agent without requiring interpretation of
free-form prose.
```

---

# 8. Agent 2 — Ticket Execution Agent

## 8.1 Objective

The Ticket Execution Agent is the workhorse.

It executes the Planner's steps one at a time.

Use a smaller, cost-efficient model because this agent may execute many times during a single request.

Responsibilities include:

* Retrieving ticket information.
* Searching similar tickets.
* Retrieving customer information.
* Checking customer history.
* Evaluating relevance.
* Performing multi-hop execution.
* Managing retries.
* Detecting missing information.
* Producing structured JSON results.
* Checking memory.
* Triggering Jira Action Agent when necessary.
* Updating Jira execution-task status.
* Adding execution results as JSON comments to Jira.

---

# 9. Executor Agent Input

The Executor receives:

```json
{
  "run_id": "RUN-001",
  "plan_id": "PLAN-001",
  "step": {
    "step_id": "STEP-002",
    "description": "...",
    "depends_on": ["STEP-001"]
  },
  "short_term_memory": {},
  "working_memory": {},
  "previous_step_results": [],
  "available_tools": []
}
```

---

# 10. Executor Output Schema

The Executor must return strict JSON.

Example:

```json
{
  "run_id": "RUN-001",
  "plan_id": "PLAN-001",
  "step_id": "STEP-002",
  "status": "SUCCESS",
  "summary": "Two tickets were identified as similar.",
  "findings": [
    {
      "ticket_id": "IT-014",
      "similarity": 0.91,
      "category": "LOGIN",
      "customer_id": "CUST-114"
    }
  ],
  "missing_information": [],
  "evidence": [
    {
      "source": "IT-014",
      "field": "issue_description",
      "value": "Customer unable to authenticate."
    }
  ],
  "action_required": false,
  "jira_action": null,
  "retry_count": 0,
  "next_action": "CONTINUE"
}
```

---

# 11. Executor Status Values

Use controlled values:

```text
PENDING
IN_PROGRESS
SUCCESS
PARTIAL
FAILED
BLOCKED
MISSING_DATA
```

Do not use arbitrary status values.

---

# 12. Executor Agent System 

Implement a dedicated Executor system  equivalent to:

```text
You are the Ticket Execution Agent.

Your responsibility is to execute exactly one plan step at a time.

You must use the step definition and available tool registry to retrieve,
validate, compare, and reason over information.

Do not execute steps that are not assigned to you.

Do not invent information.

Do not assume missing data.

Do not use information from Working Memory belonging to another step.

Use previous step results only when explicitly provided through Short-Term Memory.

For every step:

1. Understand the step objective.
2. Validate required inputs.
3. Select appropriate registered tools.
4. Execute retrieval.
5. Evaluate relevance.
6. Retry when configured and appropriate.
7. Record intermediate information in Working Memory.
8. Determine whether the step succeeded.
9. Identify missing information.
10. Produce a strict JSON result.

If the required information does not exist:

- Return MISSING_DATA.
- Identify exactly what is missing.
- Do not fabricate a value.
- Do not infer unsupported business facts.
- Do not request a Jira action based on incomplete information.

If the step produces an actionable finding:

- Set action_required to true.
- Provide the finding in structured JSON.
- Request the Jira Action Agent through the orchestrator/tool interface.

Do not directly implement Jira HTTP calls.

All Jira operations must go through the Jira service/tool abstraction.

Every output must be machine-readable JSON.
```

---

# 13. Agent 3 — Jira Action Agent

## 13.1 Objective

The Jira Action Agent handles Jira-specific business actions.

It should be lightweight because its primary responsibilities are:

* Structured field mapping.
* Create/update decision.
* Duplicate detection.
* Jira field generation.
* Calling Jira tools.
* Returning structured Jira results.

---

# 14. Jira Action Agent Input

Example:

```json
{
  "run_id": "RUN-001",
  "step_id": "STEP-005",
  "finding": {
    "customer_id": "CUST-114",
    "category": "LOGIN",
    "issue": "Authentication issue",
    "churned": true
  },
  "memory_match": null,
  "existing_jira_issues": []
}
```

---

# 15. Jira Action Agent Output

Example:

```json
{
  "action": "CREATE",
  "status": "SUCCESS",
  "jira_issue": {
    "issue_key": "SUP-2045",
    "project": "SUPPORT",
    "issue_type": "Task",
    "summary": "Follow-up required for CUST-114 login issue",
    "priority": "High",
    "labels": [
      "login",
      "authentication",
      "churn-risk",
      "follow-up"
    ]
  },
  "reason": "New actionable finding with no existing Jira action."
}
```

---

# 16. Jira Agent System 

Implement a dedicated system  equivalent to:

```text
You are the Jira Action Agent.

Your responsibility is to convert validated findings into appropriate Jira
actions.

You must never create or update a Jira issue using incomplete or fabricated data.

Before creating an issue:

1. Validate the finding.
2. Check whether required fields are present.
3. Check long-term memory for previous actions.
4. Search Jira for an existing relevant issue when appropriate.
5. Determine CREATE, UPDATE, or NO_ACTION.
6. Generate the required Jira fields.
7. Execute the Jira operation through the registered Jira tools.
8. Return the Jira result as strict JSON.

Use the following decision rules:

CREATE:
Use when the finding is new, actionable, sufficiently supported, and no
existing Jira issue represents the same action.

UPDATE:
Use when a related Jira issue already exists and new information should
be added to that issue.

NO_ACTION:
Use when the finding was already actioned and no meaningful new information exists.

Never create a Jira issue solely because the user asked a question.

A Jira action must be supported by validated execution results.

Never fabricate:

- Jira issue keys.
- Customer IDs.
- Ticket IDs.
- Priority.
- Dates.
- Business outcomes.

Return only structured JSON conforming to the Jira Action Agent schema.
```

---

# 17. Jira Integration

Do NOT create an MCP server.

Use:

```text
Jira Action Agent
       |
       v
Jira Service
       |
       v
Jira REST API Client
       |
       v
Jira
```

Authentication must use:

```text
JIRA_BASE_URL
JIRA_EMAIL
JIRA_API_TOKEN
```

Store credentials in environment variables or a secret manager.

Never:

* Put tokens in source code.
* Put tokens in s.
* Store tokens in ChromaDB.
* Store tokens in Jira comments.
* Return tokens to agents.

---

# 18. Jira Operations

Implement a dedicated Jira service with functions such as:

```python
search_issues(...)
get_issue(...)
create_issue(...)
update_issue(...)
add_comment(...)
transition_issue(...)
```

The implementation must handle:

* HTTP errors.
* Authentication failures.
* Invalid project.
* Invalid issue type.
* Invalid fields.
* Invalid status transitions.
* Rate limits.
* Timeouts.
* Network failures.
* Jira validation errors.

---

# 19. Runtime Jira Task Creation

A critical requirement is:

> Every runtime user input must result in a Jira execution task.

When the user submits:

```text
Which customers had the same login issue as IT-001,
and did any of them churn afterward?
```

the orchestrator must create a Jira execution task.

Example:

```text
Jira:
SUP-3001

Summary:
Ticket Intelligence Execution - RUN-001

Description:
User request:
Which customers had the same login issue as IT-001,
and did any of them churn afterward?

Run ID:
RUN-001

Plan ID:
PLAN-001
```

This Jira issue represents the runtime execution.

---

# 20. Jira Runtime Task Lifecycle

The runtime Jira task should follow:

```text
CREATED
   |
   v
IN PROGRESS
   |
   v
STEP EXECUTION
   |
   v
OUTPUT COMMENT
   |
   v
NEXT STEP
   |
   v
...
   |
   v
COMPLETED
```

If execution fails:

```text
IN PROGRESS
     |
     v
BLOCKED / FAILED
```

---

# 21. Jira Status Updates

The Executor/Orchestrator must update the runtime Jira task.

Example:

```text
Created
   ↓
In Progress
   ↓
Step 1 Completed
   ↓
Step 2 In Progress
   ↓
Step 2 Completed
   ↓
Step 3 In Progress
   ↓
Completed
```

Do not rely only on comments.

Update the actual Jira status where Jira workflow permissions allow it.

If the workflow does not support a required transition, record the transition failure and continue only if the configured failure policy permits it.

---

# 22. JSON Jira Comments

Every completed Executor step must generate a JSON-formatted Jira comment.

Example:

```json
{
  "run_id": "RUN-001",
  "plan_id": "PLAN-001",
  "step_id": "STEP-002",
  "status": "SUCCESS",
  "summary": "Two similar login tickets found.",
  "findings": [
    {
      "ticket_id": "IT-014",
      "customer_id": "CUST-114",
      "category": "LOGIN",
      "similarity": 0.91
    }
  ],
  "missing_information": [],
  "action_required": false,
  "jira_action": null,
  "retry_count": 0,
  "next_action": "CONTINUE"
}
```

Store this JSON in the Jira comment.

Prefer a machine-readable format.

If Jira comments require markup, wrap JSON in a code block while preserving the underlying JSON content:

```text
{
  ...
}
```

---

# 23. JSON as Agent-to-Agent Context

The output JSON from one step must become structured input to subsequent steps.

Example:

```text
STEP 1
   |
   v
JSON RESULT
   |
   v
Short-Term Memory
   |
   v
STEP 2
   |
   v
Executor receives STEP 1 result
```

Do not force the next agent to parse natural-language summaries.

The primary inter-agent contract must be structured JSON.

---

# 24. ChromaDB Memory Architecture

Use ChromaDB as the persistence layer for memory and context management.

Do not implement one generic memory collection.

Use three logically separate memory layers.

Recommended collections:

```text
short_term_memory
working_memory
long_term_memory
```

Optionally create additional collections for:

```text
execution_traces
ticket_context
jira_actions
```

but keep the three required memory layers clearly separated.

---

# 25. Short-Term Memory

Short-Term Memory represents the current execution run.

Store:

```text
run_id
user question
plan
current step
completed steps
step outputs
current findings
jira runtime task
execution status
```

Example:

```json
{
  "run_id": "RUN-001",
  "plan_id": "PLAN-001",
  "current_step": "STEP-003",
  "completed_steps": [
    "STEP-001",
    "STEP-002"
  ],
  "results": {}
}
```

Lifetime:

```text
Create at run start
       ↓
Use during execution
       ↓
Final result
       ↓
Expire/clear
```

---

# 26. Working Memory

Working Memory must contain information for the current step only.

Example:

```json
{
  "run_id": "RUN-001",
  "step_id": "STEP-002",
  "retrievals": [],
  "partial_results": [],
  "relevance_scores": [],
  "retry_count": 1,
  "temporary_errors": []
}
```

When the step completes:

```text
Working Memory
      |
      v
Step Result
      |
      v
Short-Term Memory
      |
      v
CLEAR
```

This must be enforced programmatically.

Working memory from STEP-002 must never automatically appear in STEP-003.

---

# 27. Long-Term Memory

Long-Term Memory persists across sessions.

Store validated facts and action history such as:

```json
{
  "customer_id": "CUST-114",
  "finding_hash": "abc123",
  "category": "LOGIN",
  "finding": "Customer experienced login issue and later churned.",
  "source_tickets": [
    "IT-001",
    "IT-014"
  ],
  "jira_issue_key": "SUP-2045",
  "action": "CREATE",
  "status": "ACTIONED",
  "first_seen": "2026-08-27T10:30:00Z",
  "last_seen": "2026-08-27T10:30:00Z"
}
```

---

# 28. Long-Term Memory Deduplication

Before creating a Jira business ticket:

```text
Finding
  |
  v
Generate normalized finding representation
  |
  v
Generate deterministic finding hash
  |
  v
Search ChromaDB
  |
  +---- Found ----> Previously Actioned
  |
  +---- Not Found -> New Finding
```

The finding hash should be based on normalized business identifiers and category rather than generated prose.

For example:

```text
customer_id
issue_category
business_event
```

Avoid using the LLM-generated summary alone as the deduplication key.

---

# 29. Memory Metadata

Use metadata to support efficient filtering.

Example:

```json
{
  "memory_type": "long_term",
  "customer_id": "CUST-114",
  "category": "LOGIN",
  "finding_type": "CHURN_AFTER_ISSUE",
  "jira_issue_key": "SUP-2045",
  "action_status": "ACTIONED",
  "run_id": "RUN-001"
}
```

---

# 30. ChromaDB Context Retrieval

Before executing a relevant step:

```text
Current Step
    |
    v
Generate retrieval query
    |
    v
ChromaDB
    |
    v
Relevant memory
    |
    v
Agent context
```

Only retrieve relevant memories.

Do not inject the entire memory database into the model context.

---

# 31. Context Isolation

Implement explicit context objects.

Example:

```python
ExecutionContext
    run_id
    user_question
    plan
    previous_step_results
    short_term_memory
    working_memory
    relevant_long_term_memory
```

For each step:

```python
StepContext
    run_id
    step_id
    step_definition
    required_inputs
    previous_step_outputs
    working_memory
    relevant_memory
```

When the step ends:

```python
working_memory.clear()
```

Do not reuse the StepContext object for another step without rebuilding it.

---

# 32. Tool Registry

Implement a centralized Tool Registry.

The agents must never dynamically call arbitrary functions.

Example:

```text
Tool Registry
│
├── get_ticket
├── search_tickets
├── search_similar_tickets
├── get_customer
├── get_customer_tickets
├── get_customer_status
├── get_churn_history
├── search_short_term_memory
├── search_working_memory
├── search_long_term_memory
├── jira_create
├── jira_update
├── jira_search
├── jira_get
├── jira_comment
└── jira_transition
```

---

# 33. Tool Definition

Every tool must contain metadata:

```json
{
  "name": "get_ticket",
  "description": "Retrieve a ticket by ID.",
  "input_schema": {
    "type": "object",
    "properties": {
      "ticket_id": {
        "type": "string"
      }
    },
    "required": ["ticket_id"]
  },
  "allowed_agents": [
    "ticket_execution_agent"
  ],
  "side_effect": false
}
```

For Jira:

```json
{
  "name": "jira_create",
  "description": "Create a Jira issue.",
  "allowed_agents": [
    "jira_action_agent"
  ],
  "side_effect": true
}
```

---

# 34. Tool Access Policy

Planner:

```text
Schema/catalog tools only.
No write operations.
No Jira mutation.
```

Executor:

```text
Retrieval tools.
Memory tools.
Jira Action Agent invocation.
No direct Jira implementation.
```

Jira Action Agent:

```text
Jira search.
Jira create.
Jira update.
Jira comment.
Jira transition.
Long-term memory lookup.
```

The orchestrator may invoke deterministic infrastructure services.

---

# 35. Tool Safety

Every tool must validate:

* Input schema.
* Authentication.
* Authorization.
* Allowed agent.
* Required fields.
* Side-effect policy.

Write tools must require structured inputs.

Do not permit an LLM to generate arbitrary HTTP requests.

---

# 36. Retrieval Service

Implement a deterministic Ticket Retrieval Service.

Required operations:

```python
get_ticket(ticket_id)

search_tickets(category=None)

search_similar_tickets(issue_description)

get_customer(customer_id)

get_customer_tickets(customer_id)

get_customer_status(customer_id)

get_churn_history(customer_id)
```

The retrieval service must return structured JSON.

Example:

```json
{
  "status": "SUCCESS",
  "data": [],
  "source": "ticket_database"
}
```

---

# 37. Missing Data Handling

Missing data is a first-class state.

If a ticket does not exist:

```json
{
  "status": "MISSING_DATA",
  "missing_information": [
    {
      "field": "ticket",
      "value": "IT-9999"
    }
  ],
  "action_required": false
}
```

The system must never:

* Guess the ticket.
* Generate a fictional customer.
* Assume churn.
* Create a Jira issue from incomplete information.

---

# 38. Retry Strategy

Implement retries at the tool/execution level.

Example:

```yaml
retry:
  max_attempts: 3
  backoff_seconds:
    - 1
    - 2
    - 5
```

Retry transient failures such as:

* Network timeout.
* Temporary database failure.
* Jira 429.
* Temporary service unavailable.

Do not repeatedly retry:

* Invalid input.
* Missing ticket.
* Unauthorized operation.
* Invalid Jira fields.

---

# 39. Jira Business Ticket vs Runtime Execution Ticket

Clearly distinguish:

## Runtime Execution Ticket

Created for every user input.

Purpose:

```text
Track execution of the user's request.
```

Example:

```text
SUP-3001
```

## Business Action Ticket

Created only when execution discovers a genuinely actionable business finding.

Example:

```text
SUP-2045
```

This distinction is critical.

Every runtime input must produce an execution Jira task.

Not every user request should create a separate business/action Jira ticket.

---

# 40. Runtime Execution Ticket Metadata

Include:

```text
run_id
plan_id
user request
created timestamp
agent version
model identifiers
execution status
current step
completed steps
```

Do not include secrets.

---

# 41. Jira Comment Strategy

The runtime Jira task should receive comments for:

1. Plan creation.
2. Each completed step.
3. Jira business actions.
4. Final execution result.
5. Failure/blocking information.

Example:

```json
{
  "event_type": "STEP_COMPLETED",
  "run_id": "RUN-001",
  "step_id": "STEP-002",
  "status": "SUCCESS",
  "output": {
    "similar_tickets": [
      "IT-014"
    ]
  }
}
```

---

# 42. Agent-to-Agent Communication

Agents must communicate through structured contracts.

Do not pass arbitrary free-form agent messages as the primary interface.

Example:

```text
Planner JSON
    ↓
Orchestrator
    ↓
Executor Input JSON
    ↓
Executor Output JSON
    ↓
Orchestrator
    ↓
Jira Action Agent Input JSON
    ↓
Jira Action Output JSON
```

---

# 43. Execution Orchestrator

Implement a deterministic workflow engine.

Responsibilities:

```text
1. Receive user input.
2. Generate run_id.
3. Retrieve relevant long-term memory.
4. Initialize short-term memory.
5. Invoke Planner.
6. Validate plan.
7. Create runtime Jira task.
8. Update Jira task to IN_PROGRESS.
9. Execute steps in dependency order.
10. Create working memory for each step.
11. Invoke Executor.
12. Validate Executor JSON.
13. Add Executor output as Jira comment.
14. Store result in short-term memory.
15. Clear working memory.
16. Trigger Jira Action Agent when required.
17. Persist validated findings to long-term memory.
18. Update Jira runtime task.
19. Continue until all steps finish.
20. Generate final response.
21. Add final JSON result to Jira.
22. Mark runtime Jira task COMPLETED.
23. Return final result to user.
```

---

# 44. Plan Validation

Before execution, validate:

* Valid JSON.
* Unique step IDs.
* Valid dependencies.
* No circular dependencies.
* Required tools exist.
* Tools are permitted for the relevant agent.
* Required fields exist.
* Steps are executable.

Reject invalid plans before execution.

---

# 45. Execution State Machine

Implement an explicit state machine:

```text
RECEIVED
   |
   v
PLANNING
   |
   v
PLAN_VALIDATED
   |
   v
JIRA_TASK_CREATED
   |
   v
EXECUTING
   |
   +----> STEP_FAILED
   |
   +----> STEP_MISSING_DATA
   |
   +----> JIRA_ACTION
   |
   v
ALL_STEPS_COMPLETED
   |
   v
MEMORY_PERSISTED
   |
   v
FINAL_RESPONSE
   |
   v
COMPLETED
```

---

# 46. Final Response Rules

The final response must clearly separate:

## Fresh Findings

Information discovered during the current execution.

## Recalled Findings

Information retrieved from long-term memory.

## Jira Actions

Actions performed during this run.

## Missing Information

Information that could not be established.

Example:

```text
Fresh findings:
- IT-014 has a similar login issue.
- CUST-114 subsequently churned.

Recalled findings:
- No previous record of this churn finding was found.

Jira actions:
- Runtime execution ticket SUP-3001 created.
- Business follow-up ticket SUP-2045 created.

Execution:
- All 6 planned steps completed successfully.
```

---

# 47. Do Not Re-announce Old Findings as New

If long-term memory returns:

```json
{
  "customer_id": "CUST-114",
  "finding_type": "CHURN_AFTER_LOGIN_ISSUE",
  "jira_issue_key": "SUP-2045",
  "status": "ACTIONED"
}
```

the system must report:

```text
Previously known finding:
CUST-114 had already been identified as a churn risk following a login issue.

Jira:
SUP-2045 was already created.

Action:
No duplicate Jira ticket created.
```

Do not say:

```text
New finding: CUST-114 churned.
```

---

# 48. New Information for Existing Finding

If memory contains:

```text
CUST-114 → SUP-2045
```

but the current execution discovers:

```text
New evidence:
Customer contacted support three additional times.
```

then:

```text
Jira Action Agent
       |
       v
UPDATE SUP-2045
```

Do not create a second business ticket unless the business rules explicitly require it.

Update long-term memory accordingly.

---

# 49. ChromaDB Persistence Strategy

Use a persistent ChromaDB configuration.

Development:

```text
./data/chroma
```

Production:

Use a persistent mounted volume or managed deployment appropriate for the environment.

Do not use an in-memory-only ChromaDB configuration for long-term memory.

---

# 50. Suggested Project Structure

Create a maintainable structure similar to:

```text
ticket-intelligence/
│
├── agents/
│   ├── planner/
│   │   ├── agent.py
│   │   ├── .py
│   │   ├── schemas.py
│   │   └── config.py
│   │
│   ├── executor/
│   │   ├── agent.py
│   │   ├── .py
│   │   ├── schemas.py
│   │   └── config.py
│   │
│   └── jira_action/
│       ├── agent.py
│       ├── .py
│       ├── schemas.py
│       └── config.py
│
├── orchestration/
│   ├── orchestrator.py
│   ├── state_machine.py
│   └── execution_context.py
│
├── tools/
│   ├── registry.py
│   ├── schemas.py
│   ├── ticket_tools.py
│   ├── memory_tools.py
│   └── jira_tools.py
│
├── memory/
│   ├── chroma_client.py
│   ├── short_term.py
│   ├── working_memory.py
│   ├── long_term.py
│   ├── embeddings.py
│   └── deduplication.py
│
├── jira/
│   ├── client.py
│   ├── service.py
│   ├── models.py
│   ├── transitions.py
│   └── exceptions.py
│
├── retrieval/
│   ├── ticket_service.py
│   ├── customer_service.py
│   └── schemas.py
│
├── observability/
│   ├── tracing.py
│   ├── logging.py
│   └── metrics.py
│
├── config/
│   ├── settings.py
│   └── agent_config.yaml
│
├── data/
│   └── sample_tickets/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── acceptance/
│
├── s/
│   ├── planner.md
│   ├── executor.md
│   └── jira_action.md
│
├── .env.example
├── requirements.txt
├── README.md
└── main.py
```

Adapt this structure to the existing project instead of unnecessarily rewriting the entire application.

---

# 51. Configuration

Create environment-driven configuration.

Example:

```env
JIRA_BASE_URL=
JIRA_EMAIL=
JIRA_API_TOKEN=
JIRA_PROJECT_KEY=

PLANNER_MODEL=
EXECUTOR_MODEL=
JIRA_ACTION_MODEL=

CHROMA_PERSIST_DIRECTORY=./data/chroma

MAX_EXECUTOR_RETRIES=3
JIRA_TIMEOUT_SECONDS=30
```

Never commit real secrets.

Provide:

```text
.env.example
```

with placeholder values.

---

# 52. Model Abstraction

Implement a model provider abstraction.

Example:

```python
class ModelProvider:
    def generate(self, messages, response_schema=None):
        ...
```

Agents should depend on the abstraction rather than a specific vendor/model implementation.

For example:

```text
PlannerAgent
     |
     v
ModelProvider
     |
     v
Configured Planner Model
```

This makes model swapping possible.

---

# 53. Structured Output

All agent outputs must use validated schemas.

Use Pydantic or equivalent schema validation.

Example:

```python
class ExecutorResult(BaseModel):
    run_id: str
    plan_id: str
    step_id: str
    status: ExecutionStatus
    summary: str
    findings: list
    missing_information: list
    action_required: bool
    jira_action: dict | None
    retry_count: int
    next_action: str
```

If model output fails schema validation:

1. Retry structured generation.
2. If retry fails, mark the step failed.
3. Do not continue using malformed data.

---

# 54. Observability

Every execution must produce a trace.

Capture:

```text
run_id
plan_id
step_id
agent
model
tool
tool input
tool result metadata
retry count
memory lookup
memory match
Jira operation
Jira issue key
execution status
latency
```

Do not log:

* Jira API tokens.
* Passwords.
* Secrets.
* Sensitive credentials.

---

# 55. Required Execution Trace

The UI/log should make it possible to see:

```text
USER REQUEST
    ↓
PLANNER
    ↓
PLAN
    ↓
JIRA RUNTIME TASK
    ↓
STEP 1
    ↓
EXECUTOR OUTPUT JSON
    ↓
JIRA COMMENT
    ↓
STEP 2
    ↓
EXECUTOR OUTPUT JSON
    ↓
JIRA COMMENT
    ↓
...
    ↓
JIRA ACTION AGENT
    ↓
CREATE/UPDATE
    ↓
LONG-TERM MEMORY
    ↓
FINAL RESULT
```

---

# 56. Test Dataset

Use the provided 60-ticket synthetic dataset.

The dataset should include realistic examples covering:

* IT issues.
* Customer issues.
* Legal issues.
* Payment issues.

Include relationships among:

* Ticket IDs.
* Customer IDs.
* Issue categories.
* Issue descriptions.
* Dates.
* Customer status.
* Churn events.
* Payment events.
* Legal events.
* Related tickets.

The test data must contain enough relationships to demonstrate multi-hop reasoning.

---

# 57. Required Acceptance Test 1 — New Finding

Input:

```text
Ask a compound question that requires multiple execution steps
and produces a genuinely new actionable finding.
```

Expected:

```text
Planner creates multi-step plan.

Runtime Jira task created.

Executor executes steps.

Each Executor output is JSON.

Each step output is added to Jira as a JSON comment.

Subsequent steps consume previous JSON outputs.

New actionable finding detected.

Long-term memory confirms finding is new.

Jira Action Agent creates business ticket.

Jira issue key is returned.

Finding is persisted in ChromaDB.

Runtime Jira task is marked COMPLETED.

Final response is returned.
```

---

# 58. Required Acceptance Test 2 — Previously Known Finding

Start a new session.

Ask a related question involving the same customer/finding.

Expected:

```text
Planner creates new plan.

Runtime Jira task is created.

Long-term memory retrieves previous finding.

System recognizes the finding as previously actioned.

No duplicate business Jira ticket is created.

Existing Jira issue may be retrieved/updated if new evidence exists.

Final response clearly distinguishes:

Recalled information
vs
Fresh information.
```

---

# 59. Required Acceptance Test 3 — Missing Information

Ask a compound question requiring information that does not exist.

Expected:

```text
Planner creates plan.

Executor attempts retrieval.

Required information cannot be found.

Executor returns MISSING_DATA.

No fabricated information is produced.

No business Jira ticket is created.

Runtime Jira execution task records the failure/missing-data state.

Jira comment contains structured JSON describing the missing information.

Final response clearly explains what could not be determined.
```

---

# 60. Required Acceptance Test 4 — Runtime Jira Task

For every user input:

```text
User input
    ↓
Jira runtime task created
```

Verify:

* Jira issue created.
* Correct project.
* Correct issue type.
* Run ID included.
* User request included.
* Status transitions correctly.
* Step comments added.
* Final result added.
* Final Jira status is correct.

---

# 61. Required Acceptance Test 5 — Executor Jira Updates

During execution verify:

```text
Executor Step
     ↓
Jira Runtime Task
     ↓
Status Update
     ↓
JSON Comment
```

For every completed step, verify that the Jira runtime task contains the corresponding JSON result.

---

# 62. Required Acceptance Test 6 — Agent Independence

Change:

```text
Planner model
``` 

without changing:

```text
Executor model
Jira Action model
```

Verify the system still functions.

Then change:

```text
Executor model
``` 

without changing:

```text
Planner
Jira Action
```

Verify the system still functions.

Repeat for Jira Action Agent.

---

# 63. Required Acceptance Test 7 — Working Memory Isolation

Execute:

```text
STEP-001
```

with temporary intermediate data.

Complete STEP-001.

Verify:

```text
Working Memory STEP-001 = cleared
```

Execute:

```text
STEP-002
```

Verify STEP-002 cannot access STEP-001's temporary working memory.

STEP-002 may access the finalized STEP-001 result through Short-Term Memory.

---

# 64. Required Acceptance Test 8 — Long-Term Memory Persistence

Run:

```text
Session 1
```

Create a finding and Jira business ticket.

Terminate the application.

Start:

```text
Session 2
```

Ask a related question.

Verify:

```text
ChromaDB still contains the previous finding.
```

The system must not lose the previous Jira action.

---

# 65. Duplicate Prevention

Implement duplicate prevention at multiple levels.

## Level 1 — Memory

Search ChromaDB.

## Level 2 — Jira

Search Jira for an existing issue.

## Level 3 — Deterministic Finding Hash

Compare normalized finding identity.

Only create a business ticket when all relevant checks indicate that the finding/action is genuinely new.

---

# 66. Jira Idempotency

Jira creation should be idempotent where possible.

Generate an idempotency/finding identifier such as:

```text
ticket-intelligence:<customer_id>:<category>:<event_type>
```

Store it in Jira labels or a dedicated field if supported.

Example:

```text
ti-cust114-login-churn
```

This provides an additional safeguard against duplicate tickets.

---

# 67. Error Handling

Implement centralized error handling.

Categories:

```text
PlannerError
PlanValidationError
ExecutorError
ToolError
MemoryError
JiraError
ModelError
SchemaValidationError
MissingDataError
```

Every error should include:

```text
run_id
step_id
agent
error_type
safe error message
retryable
```

---

# 68. Security Requirements

Implement:

* Environment-based secrets.
* No secrets in s.
* No secrets in memory.
* No secrets in Jira comments.
* Input validation.
* Tool authorization.
* Jira permission validation.
* Safe logging.
* Agent-specific tool permissions.

---

# 69. Performance Requirements

The system should avoid unnecessary model calls.

Use:

* Planner once per run.
* Executor once per step.
* Jira Action Agent only when required.
* Memory retrieval only when relevant.
* Tool retries only for retryable errors.

Do not repeatedly send the entire execution history to every model.

Use summarized/structured context.

---

# 70. Context Management

Each agent receives only the information required for its job.

Planner receives:

```text
Question
Relevant memory
Tool catalog
```

Executor receives:

```text
Current step
Required previous results
Relevant memory
Working memory
Allowed tools
```

Jira Action Agent receives:

```text
Validated finding
Relevant long-term memory
Existing Jira information
Allowed Jira tools
```

Do not send unnecessary raw history.

---

# 71. Implementation Order

Implement the project in this order:

## Phase 1 — Baseline

1. Inspect existing project.
2. Identify current Planner.
3. Identify current Executor.
4. Identify existing retrieval mechanisms.
5. Identify existing Jira integration.
6. Identify existing memory/context handling.
7. Do not rewrite working components unnecessarily.

## Phase 2 — Agent Abstraction

1. Define Agent interface.
2. Define model provider interface.
3. Define agent configuration.
4. Implement independent model routing.
5. Define schemas.

## Phase 3 — Tool Registry

1. Define Tool interface.
2. Implement Tool Registry.
3. Register retrieval tools.
4. Register memory tools.
5. Register Jira tools.
6. Implement agent-level tool permissions.

## Phase 4 — Planner

1. Implement Planner Agent.
2. Implement Planner .
3. Implement plan schema.
4. Validate plans.
5. Add dependency handling.

## Phase 5 — Executor

1. Implement Executor Agent.
2. Implement Executor .
3. Implement step execution.
4. Implement retry logic.
5. Implement missing-data handling.
6. Implement structured output.

## Phase 6 — Jira

1. Implement Jira client.
2. Implement Jira service.
3. Configure API token.
4. Implement search.
5. Implement create.
6. Implement update.
7. Implement comments.
8. Implement status transitions.
9. Implement error handling.

## Phase 7 — Jira Action Agent

1. Implement Jira Action Agent.
2. Implement .
3. Implement Jira decision logic.
4. Implement field generation.
5. Implement create/update/no-action.
6. Return structured output.

## Phase 8 — ChromaDB

1. Install/configure ChromaDB.
2. Implement Chroma client.
3. Implement Short-Term Memory.
4. Implement Working Memory.
5. Implement Long-Term Memory.
6. Implement metadata filtering.
7. Implement similarity retrieval.
8. Implement persistence.

## Phase 9 — Orchestrator

1. Implement runtime workflow.
2. Create Jira execution task.
3. Update Jira status.
4. Execute plan steps.
5. Add JSON comments.
6. Pass JSON outputs forward.
7. Manage memory.
8. Trigger Jira Action Agent.
9. Persist long-term findings.
10. Update Jira runtime task.
11. Continue until all steps finish.
12. Generate final response.
13. Add final JSON result to Jira.
14. Mark runtime Jira task COMPLETED.
15. Return final result to user.

## Phase 10 — Testing

Implement unit, integration, and acceptance tests.

---

# 72. Unit Tests

Test:

* Planner schema.
* Executor schema.
* Jira Action schema.
* Tool registry.
* Tool permissions.
* ChromaDB memory operations.
* Memory isolation.
* Finding hash.
* Duplicate detection.
* Jira client.
* Jira status transition.
* Retry logic.
* Missing data handling.

---

# 73. Integration Tests

Test:

```text
Planner → Orchestrator
Orchestrator → Executor
Executor → Retrieval
Executor → ChromaDB
Executor → Jira Action Agent
Jira Action Agent → Jira API
Jira → Orchestrator
Orchestrator → ChromaDB
```

---

# 74. End-to-End Test

The complete flow must work:

```text
User
 ↓
Planner
 ↓
Plan
 ↓
Jira Runtime Task
 ↓
Executor Step 1
 ↓
JSON Comment
 ↓
Executor Step 2
 ↓
JSON Comment
 ↓
Executor Step 3
 ↓
JSON Comment
 ↓
Jira Action Agent
 ↓
Jira Create/Update
 ↓
ChromaDB Long-Term Memory
 ↓
Final Response
```

---

# 75. Expected Final Demonstration

The final demonstration should show:

## Agent configuration

```text
Planner Agent
Model: Strong Reasoning Model

Executor Agent
Model: Cost-Optimized Model

Jira Action Agent
Model: Lightweight Model
```

## Execution

```text
User request
 ↓
Planner
 ↓
Plan
 ↓
Jira Runtime Task
 ↓
Executor
 ↓
Step-by-step JSON outputs
 ↓
Jira comments/status updates
 ↓
Jira Action Agent
 ↓
Business Jira action
 ↓
ChromaDB persistence
 ↓
Final response
```

## Memory

Show:

```text
Fresh information
vs
Recalled information
```

## Jira

Show:

```text
Runtime execution ticket
Business action ticket
```

---

# 76. Expected Deliverables

The implementation must provide:

1. Three independent AI agents.
2. Agent-specific s.
3. Agent-specific models.
4. Model provider abstraction.
5. Tool registry.
6. Tool schemas.
7. Agent-specific tool permissions.
8. Agent orchestrator.
9. Ticket retrieval service.
10. Jira API client.
11. Jira service.
12. Jira Action Agent.
13. ChromaDB integration.
14. Short-Term Memory.
15. Working Memory.
16. Long-Term Memory.
17. Deduplication mechanism.
18. Finding identity/hash mechanism.
19. Runtime Jira task creation.
20. Jira status updates.
21. JSON Jira comments.
22. Structured agent-to-agent communication.
23. Retry handling.
24. Missing-data handling.
25. Execution tracing.
26. Unit tests.
27. Integration tests.
28. End-to-end tests.
29. Acceptance tests.
30. README/documentation.
31. `.env.example`.
32. Sample configuration.
33. Sample 60-ticket dataset integration.

---

# 77. Definition of Done

The project is complete only when all of the following are true:

* The Planner can decompose compound questions.
* The Executor can execute each plan step independently.
* The Jira Action Agent can create/update Jira issues.
* Each agent can use a different model.
* Models can be swapped independently.
* Tool access is controlled by a registry.
* Every runtime user request creates a Jira execution task.
* The Jira execution task receives status updates.
* Executor results are written to Jira as JSON comments.
* JSON results can be consumed by subsequent steps.
* Short-Term Memory stores current run state.
* Working Memory stores current-step state only.
* Working Memory is cleared between steps.
* Long-Term Memory persists across sessions.
* ChromaDB is used for persistent memory/context retrieval.
* Previously actioned findings are detected.
* Duplicate Jira business tickets are prevented.
* Existing Jira tickets can be updated when new evidence appears.
* Missing data does not result in hallucination.
* Missing data does not create an unsupported business Jira ticket.
* Jira API errors are handled.
* Agent outputs are schema validated.
* Execution traces are available.
* The three acceptance scenarios pass.
* The application survives a restart without losing long-term memory.
* No secrets are stored in source code, s, ChromaDB, or Jira comments.

---

# 78. Final Engineering Principle

The system should not be implemented as:

```text
One Large Agent
       |
       +-- Planner
       +-- Executor
       +-- Jira
       +-- Memory
```

Instead implement:

```text
                 Orchestrator
                      |
          +-----------+-----------+
          |           |           |
          v           v           v
       Planner     Executor     Jira Agent
       Agent       Agent        Agent
          |           |           |
       Model A      Model B      Model C
          |           |           |
          +-----------+-----------+
                      |
                 Tool Registry
                      |
          +-----------+-----------+
          |           |           |
          v           v           v
      Retrieval    ChromaDB     Jira API
       Service      Memory       Service
```

The architecture must demonstrate genuine specialization:

**Planner = decide what needs to be done**

**Executor = perform the investigation**

**Jira Action Agent = decide and perform Jira business actions**

**Orchestrator = deterministically control the workflow**

**Tool Registry = control what agents are allowed to use**

**ChromaDB = provide persistent contextual memory**

**Jira = provide runtime execution tracking and business action tracking**

The final system must be modular, observable, testable, secure, model-independent, and capable of executing multi-hop ticket intelligence workflows end-to-end.
