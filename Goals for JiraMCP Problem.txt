Below is a more **implementation-oriented project plan**. Each **Goal → Sub-Goal → Task** includes:

* **Task:** What needs to be built/done
* **Requirement Details:** What the task specifically means for this requirement
* **Expected Outcome:** What should exist or work when the task is completed

I have also kept the architecture at **3 AI agents** and **Jira API Token integration** — **no Jira MCP server**.

---

# Goal 1 — Establish Multi-Agent Architecture

## Sub-Goal 1.1 — Define the Three AI Agents

### Task 1.1.1 — Define Ticket Planning Agent

**Requirement Details**

Create a dedicated agent whose only responsibility is to understand a compound support question and convert it into a structured execution plan.

The Planner should handle questions such as:

> "Which customers had the same login issue as IT-001, and did any of them churn afterward?"

The Planner should recognize that this requires multiple dependent operations:

```text
Analyze IT-001
      ↓
Find similar tickets
      ↓
Identify customers
      ↓
Check customer churn
      ↓
Check whether finding already exists
      ↓
Create/update Jira if required
```

The Planner should **not** retrieve the actual data or directly call Jira.

**Expected Outcome**

A dedicated `TicketPlanningAgent` exists and produces a validated structured plan containing:

* Plan ID
* Step ID
* Step description
* Dependencies
* Expected result
* Required tool/service
* Step status

---

### Task 1.1.2 — Define Ticket Execution Agent

**Requirement Details**

Create the execution agent responsible for executing one plan step at a time.

It should:

* Retrieve data.
* Search tickets.
* Find similar issues.
* Identify customers.
* Check customer history.
* Check churn.
* Grade relevance.
* Retry unsuccessful retrievals.
* Identify missing information.
* Identify actionable findings.
* Query long-term memory.

The Executor should not contain Jira API implementation.

**Expected Outcome**

A dedicated `TicketExecutionAgent` can receive:

```text
Plan Step + Context
```

and return:

```text
Step Result
+ Evidence
+ Status
+ Finding
+ Action Required
```

---

### Task 1.1.3 — Define Jira Action Agent

**Requirement Details**

Create a separate lightweight agent responsible for converting an actionable finding into a Jira action.

It should determine:

* Whether Jira action is required.
* Create vs update.
* Jira summary.
* Description.
* Category.
* Priority.
* Labels.
* Customer reference.
* Existing Jira issue reference.

**Expected Outcome**

A dedicated `JiraActionAgent` exists and returns a structured Jira action request.

---

# Goal 2 — Implement Agent Orchestration

## Sub-Goal 2.1 — Build Agent Orchestrator

### Task 2.1.1 — Implement Run Initialization

**Requirement Details**

Every user question should receive a unique execution ID.

Example:

```text
RUN-2026-0001
```

The Orchestrator initializes:

* User question
* Run ID
* Short-Term Memory
* Execution status
* Plan status

**Expected Outcome**

Every request has an isolated execution context.

---

### Task 2.1.2 — Invoke Planning Agent

**Requirement Details**

The Orchestrator sends the user's question to the Planning Agent and receives a structured execution plan.

The Orchestrator must validate the plan before execution.

**Expected Outcome**

Invalid or incomplete plans are rejected instead of being executed.

---

### Task 2.1.3 — Execute Plan Sequentially

**Requirement Details**

The Orchestrator should execute steps according to dependencies.

Example:

```text
STEP-001 → STEP-002 → STEP-003 → STEP-004
```

Step 3 must not execute until Step 2 has successfully produced the information required by Step 3.

**Expected Outcome**

Plan execution is deterministic and dependency-aware.

---

### Task 2.1.4 — Handle Step Failures

**Requirement Details**

If a step fails:

* Retry where appropriate.
* Record retry attempts.
* Determine whether the failure is recoverable.
* Prevent dependent steps from using invalid data.
* Mark the plan appropriately.

**Expected Outcome**

A failed retrieval does not silently become a fabricated result.

---

# Goal 3 — Implement Independent Model Configuration

## Sub-Goal 3.1 — Planner Model

### Task 3.1.1 — Configure Strong Reasoning Model

**Requirement Details**

The Planner requires stronger reasoning because incorrect decomposition can cause the entire workflow to fail.

Configuration should include:

```text
model
temperature
max_tokens
timeout
retry_count
```

**Expected Outcome**

Planner model can be changed independently from other agents.

---

## Sub-Goal 3.2 — Executor Model

### Task 3.2.1 — Configure Cost-Efficient Model

**Requirement Details**

The Executor may run many times during one user query. Therefore it should use a smaller, cheaper model.

**Expected Outcome**

Executor model configuration is independent from Planner.

---

## Sub-Goal 3.3 — Jira Agent Model

### Task 3.3.1 — Configure Lightweight Model

**Requirement Details**

Jira Agent mostly performs structured field generation and action selection.

**Expected Outcome**

Jira Agent can use a lightweight model independently.

---

# Goal 4 — Implement Short-Term Memory

## Sub-Goal 4.1 — Define Current Run Memory

### Task 4.1.1 — Create Short-Term Memory Schema

**Requirement Details**

Short-Term Memory should contain:

```text
run_id
user_question
plan
current_step
completed_steps
step_results
current_findings
jira_actions
execution_status
```

It represents everything known **during the current request**.

**Expected Outcome**

The Executor can access results from previous steps during the same run.

---

### Task 4.1.2 — Update Memory After Every Step

**Requirement Details**

After a step completes:

```text
Step Result
    ↓
Short-Term Memory
```

The next step can then use that result.

**Expected Outcome**

Multi-hop execution works without requiring every step to repeat previous retrievals.

---

### Task 4.1.3 — Clear Short-Term Memory

**Requirement Details**

At the end of a run, the run-specific memory must be discarded.

**Expected Outcome**

Information from one request does not accidentally become context for another request.

---

# Goal 5 — Implement Working Memory

## Sub-Goal 5.1 — Step-Level State

### Task 5.1.1 — Create Working Memory

**Requirement Details**

At the beginning of each step:

```text
WorkingMemory(step_id)
```

should be created.

It can contain:

* Partial retrievals
* Intermediate results
* Relevance scores
* Retry attempts
* Temporary errors
* Temporary reasoning state

**Expected Outcome**

The Executor has isolated temporary state for the current step.

---

### Task 5.1.2 — Transfer Completed Step

**Requirement Details**

When the step completes:

```text
Working Memory
      ↓
Final Step Result
      ↓
Short-Term Memory
```

Only the final useful result should move forward.

**Expected Outcome**

Intermediate step state does not unnecessarily pollute later steps.

---

### Task 5.1.3 — Clear Working Memory

**Requirement Details**

Working Memory must be cleared before the next step.

**Expected Outcome**

This test must pass:

```text
Step 1 temporary data
       X
       ↓
Step 2
```

Step 2 cannot access Step 1's temporary retrieval/retry state unless that information was explicitly promoted to Short-Term Memory.

---

# Goal 6 — Implement Long-Term Memory

## Sub-Goal 6.1 — Persistent Finding Storage

### Task 6.1.1 — Define Long-Term Memory Schema

**Requirement Details**

Store meaningful business findings such as:

```text
customer_id
finding_id
issue_category
finding_description
source_ticket_ids
status
jira_ticket_id
action_taken
first_detected_at
last_verified_at
```

**Expected Outcome**

A finding can be recalled in a completely new session.

---

### Task 6.1.2 — Persist New Findings

**Requirement Details**

When a new actionable finding is confirmed:

```text
Finding
+
Evidence
+
Jira Action
      ↓
Long-Term Memory
```

**Expected Outcome**

The system remembers that the finding was already discovered and actioned.

---

### Task 6.1.3 — Retrieve Historical Findings

**Requirement Details**

Before creating Jira, the Executor must query long-term memory.

Example:

```text
Customer = CUST-114
Issue = Login
Finding = Churn after login issue
```

Search memory for an existing matching finding.

**Expected Outcome**

Previously discovered findings are recognized instead of being treated as new.

---

# Goal 7 — Implement Ticket Retrieval Service

## Sub-Goal 7.1 — Ticket Retrieval

### Task 7.1.1 — Implement Ticket Lookup

**Requirement Details**

Provide deterministic functions such as:

```text
get_ticket(ticket_id)
search_tickets(category)
search_similar_tickets(description)
```

**Expected Outcome**

Executor can reliably retrieve historical ticket information.

---

### Task 7.1.2 — Implement Customer Lookup

**Requirement Details**

Provide:

```text
get_customer(customer_id)
get_customer_tickets(customer_id)
get_customer_status(customer_id)
get_churn_history(customer_id)
```

**Expected Outcome**

Executor can follow the relationship:

```text
Ticket
 ↓
Customer
 ↓
Customer History
 ↓
Churn
```

---

# Goal 8 — Implement Jira API Integration

## Sub-Goal 8.1 — Jira Authentication

### Task 8.1.1 — Configure Jira API Token

**Requirement Details**

Use Jira API token authentication.

The token must be stored in:

* Secret manager
* Environment variable
* Secure configuration

It must never be placed in:

* Prompt
* Memory
* Source code
* Execution trace

**Expected Outcome**

Jira API connectivity works securely.

---

## Sub-Goal 8.2 — Jira Operations

### Task 8.2.1 — Implement Jira Search

**Requirement Details**

Implement:

```text
search_issue()
search_by_customer()
search_by_category()
```

This is required for duplicate detection and existing-ticket updates.

**Expected Outcome**

Jira Agent can determine whether a related issue already exists.

---

### Task 8.2.2 — Implement Jira Create

**Requirement Details**

Implement creation using the Jira API.

Fields should include, as applicable:

```text
Project
Issue Type
Summary
Description
Priority
Labels
Customer
Category
```

**Expected Outcome**

A valid actionable finding creates a Jira ticket.

---

### Task 8.2.3 — Implement Jira Update

**Requirement Details**

If an existing Jira issue is found and new information is available, update it rather than creating another issue.

**Expected Outcome**

Existing Jira tickets can be enriched without duplication.

---

# Goal 9 — Integrate Jira Actions Into Agent Execution

## Sub-Goal 9.1 — Identify Actionable Findings

### Task 9.1.1 — Define Actionability Rules

**Requirement Details**

Define when a finding should result in Jira action.

For example:

```text
Confirmed issue
+
Identified customer
+
Required evidence available
+
No previous action
=
Jira action
```

**Expected Outcome**

Executor can consistently identify when Jira action is appropriate.

---

## Sub-Goal 9.2 — Execute Jira Action

### Task 9.2.1 — Send Finding to Jira Agent

**Requirement Details**

Executor passes structured information:

```text
Customer
Issue Category
Finding
Evidence
Source Tickets
Existing Memory Result
```

to Jira Agent.

**Expected Outcome**

Jira Agent has enough structured context to determine the correct Jira operation.

---

### Task 9.2.2 — Execute Create/Update

**Requirement Details**

Jira Agent:

```text
Determine Action
      ↓
Search Jira if required
      ↓
Create / Update
      ↓
Return Jira ID
```

**Expected Outcome**

Jira action becomes part of the plan execution rather than a separate post-processing step.

---

# Goal 10 — Implement Finding Deduplication

## Sub-Goal 10.1 — Finding Identification

### Task 10.1.1 — Define Finding Identity

**Requirement Details**

Create a deterministic way to identify whether two findings represent the same business event.

Potential matching information:

```text
Customer
Issue Category
Finding Type
Source Ticket
Business Event
```

**Expected Outcome**

The system can distinguish a genuinely new finding from an existing one.

---

## Sub-Goal 10.2 — Deduplication Decision

### Task 10.2.1 — Classify Finding

**Requirement Details**

Classify each finding as:

```text
NEW
KNOWN
PREVIOUSLY_ACTIONED
UPDATED
```

**Expected Outcome**

The final response and Jira action are based on finding state.

---

### Task 10.2.2 — Prevent Duplicate Jira

**Requirement Details**

Before creation:

```text
Long-Term Memory Search
        ↓
Jira Search if necessary
        ↓
Duplicate?
```

If yes:

```text
Do not create
```

**Expected Outcome**

Repeated questions do not create duplicate Jira tickets.

---

# Goal 11 — Implement Missing Data Handling

## Sub-Goal 11.1 — Detect Missing Information

### Task 11.1.1 — Define Required Data

**Requirement Details**

For each plan step define mandatory information.

Example:

```text
Churn verification requires:
Customer ID
Customer status/history
```

**Expected Outcome**

The system knows exactly what information is required before making a conclusion.

---

### Task 11.1.2 — Handle Empty Results

**Requirement Details**

If data does not exist:

```text
No Data Found
```

must not become:

```text
Assumed Data
```

**Expected Outcome**

The Executor explicitly reports missing information.

---

## Sub-Goal 11.2 — Block Invalid Jira Actions

### Task 11.2.1 — Validate Evidence Before Jira

**Requirement Details**

Jira creation should require sufficient evidence.

Example:

```text
Customer identified = YES
Issue identified = YES
Churn confirmed = NO
Required information = MISSING

→ Jira creation BLOCKED
```

**Expected Outcome**

No Jira ticket is created from incomplete information.

---

# Goal 12 — Implement Observability

## Sub-Goal 12.1 — Agent Execution Trace

### Task 12.1.1 — Capture Planner Trace

**Requirement Details**

Show:

* User question
* Planner model
* Generated plan
* Step dependencies

**Expected Outcome**

Reviewers can see how the compound question was decomposed.

---

### Task 12.1.2 — Capture Executor Trace

**Requirement Details**

Show:

* Step number
* Retrieval
* Results
* Relevance
* Retry
* Final step result

**Expected Outcome**

Reviewers can follow the complete multi-hop execution.

---

### Task 12.1.3 — Capture Jira Agent Trace

**Requirement Details**

Show:

```text
Finding
↓
Jira Decision
↓
Create/Update/Search
↓
Jira Fields
↓
Jira ID
```

**Expected Outcome**

Jira activity is fully auditable.

---

# Goal 13 — Configure Development and QA Environments

## Sub-Goal 13.1 — Development Environment

### Tasks

* Load the 60 historical tickets.
* Validate ticket data.
* Configure development database.
* Configure development memory.
* Configure development Jira project.
* Configure test Jira API token.
* Configure three agent models.
* Configure environment variables.
* Validate service connectivity.

**Expected Outcome**

Developers can run the entire system locally/in development.

---

## Sub-Goal 13.2 — QA Environment

### Tasks

* Create isolated QA configuration.
* Load all 60 tickets.
* Configure QA memory.
* Configure QA Jira project.
* Configure QA Jira token.
* Configure test model configuration.
* Configure test execution traces.
* Configure data reset/cleanup.

**Expected Outcome**

QA can repeatedly execute the acceptance tests without affecting production.

---

# Goal 14 — End-to-End Acceptance Testing

## Sub-Goal 14.1 — Test New Finding

### Task

Execute a compound question that produces a genuinely new finding.

**Validate:**

1. Planner generates correct plan.
2. Executor completes each step.
3. Finding is supported by data.
4. Long-Term Memory has no previous finding.
5. Jira Agent is invoked.
6. Correct Jira fields are generated.
7. Jira ticket is created through Jira API.
8. Jira ID is captured.
9. Finding is persisted.
10. Final response identifies the finding as new.

**Expected Outcome**

```text
New Finding
     ↓
Jira Created
     ↓
Memory Persisted
```

---

## Sub-Goal 14.2 — Test Existing Finding

### Task

Start a new session and ask a related question about the same customer.

**Validate:**

1. Long-Term Memory is searched.
2. Previous finding is recalled.
3. Previous Jira ticket is identified.
4. Finding is classified as previously actioned.
5. No duplicate Jira ticket is created.
6. Response distinguishes recalled information from fresh information.

**Expected Outcome**

```text
Existing Finding
      ↓
Memory Recalled
      ↓
Existing Jira
      ↓
No Duplicate
```

---

## Sub-Goal 14.3 — Test Missing Information

### Task

Ask a compound question requiring information that does not exist in the dataset.

**Validate:**

1. Planner creates appropriate steps.
2. Executor attempts retrieval.
3. Missing data is detected.
4. Step is marked incomplete.
5. No unsupported assumption is made.
6. Jira Agent is not invoked for incomplete evidence.
7. No Jira ticket is created.
8. User receives a clear explanation.

**Expected Outcome**

```text
Missing Data
     ↓
Incomplete Finding
     ↓
No Fabrication
     ↓
No Jira Ticket
```

---

# Goal 15 — Prove Agent Model Independence

## Sub-Goal 15.1 — Planner Independence

### Tasks

* Run Planner with Model A.
* Replace with Model B.
* Run the same test.
* Verify Executor configuration is unchanged.
* Verify Jira Agent configuration is unchanged.

**Expected Outcome**

Planner model can be changed without code changes to other agents.

---

## Sub-Goal 15.2 — Executor Independence

### Tasks

* Run Executor with Model A.
* Replace with Model B.
* Run the same test.
* Compare execution.
* Verify Planner remains unchanged.

**Expected Outcome**

Executor model is independently replaceable.

---

## Sub-Goal 15.3 — Jira Agent Independence

### Tasks

* Run Jira Agent with Model A.
* Replace with Model B.
* Validate Jira payload generation.
* Verify Planner and Executor remain unchanged.

**Expected Outcome**

All three agents have independently swappable models.

---

# Goal 16 — Security and Production Readiness

## Sub-Goal 16.1 — Protect Jira Credentials

### Tasks

* Store API token securely.
* Remove token from source code.
* Remove token from prompts.
* Remove token from memory.
* Mask token in logs.
* Separate dev/QA/prod credentials.

**Expected Outcome**

Jira credentials cannot be exposed through agent output, memory, or execution traces.

---

## Sub-Goal 16.2 — Reliability

### Tasks

* Configure model timeout.
* Configure API timeout.
* Configure retry policies.
* Handle Jira failures.
* Handle retrieval failures.
* Handle memory failures.
* Handle agent failures.
* Implement graceful error responses.

**Expected Outcome**

Temporary failures do not cause incorrect findings or uncontrolled Jira actions.

---

# Goal 17 — Documentation and Demonstration

## Sub-Goal 17.1 — Technical Documentation

### Tasks

* Document three-agent architecture.
* Document Agent Orchestrator.
* Document model routing.
* Document three memory layers.
* Document retrieval service.
* Document Jira API service.
* Document deduplication logic.
* Document missing-data handling.

**Expected Outcome**

Another developer can understand and maintain the architecture.

---

## Sub-Goal 17.2 — Demonstration Evidence

### Tasks

Prepare evidence showing:

1. Planner's generated plan.
2. Executor's Step 1 execution.
3. Executor's Step 2 execution.
4. Executor's Step 3 execution.
5. Executor's subsequent steps.
6. Working Memory lifecycle.
7. Short-Term Memory state.
8. Long-Term Memory lookup.
9. Fresh vs recalled finding.
10. Jira Agent invocation.
11. Jira create/update operation.
12. Jira ticket ID.
13. Final response.

**Expected Outcome**

The implementation clearly demonstrates that the solution is actually **multi-agent + multi-hop + memory-aware + action-oriented**, rather than simply being a single LLM with a large prompt.

---

# Final Goal/Sub-Goal/Task Structure

For your project management tool, the hierarchy would therefore be:

```text
GOAL 1  — Multi-Agent Architecture
  ├─ SG 1.1 — Define Agents
  │   ├─ Define Planning Agent
  │   ├─ Define Execution Agent
  │   └─ Define Jira Action Agent
  ├─ SG 1.2 — Define Communication
  └─ SG 1.3 — Define Workflow

GOAL 2  — Planning Agent
  ├─ SG 2.1 — Build Planner
  ├─ SG 2.2 — Configure Strong Model
  └─ SG 2.3 — Validate Planning

GOAL 3  — Execution Agent
  ├─ SG 3.1 — Build Executor
  ├─ SG 3.2 — Retrieval Execution
  └─ SG 3.3 — Retry & Relevance

GOAL 4  — Jira Action Agent
  ├─ SG 4.1 — Build Jira Agent
  ├─ SG 4.2 — Jira Field Generation
  └─ SG 4.3 — Jira Action Decision

GOAL 5  — Agent Orchestrator
  ├─ SG 5.1 — Run Management
  ├─ SG 5.2 — Step Management
  └─ SG 5.3 — Error Management

GOAL 6  — Short-Term Memory
  ├─ SG 6.1 — Schema
  ├─ SG 6.2 — Integration
  └─ SG 6.3 — Lifecycle

GOAL 7  — Working Memory
  ├─ SG 7.1 — Step State
  ├─ SG 7.2 — Step Lifecycle
  └─ SG 7.3 — Isolation

GOAL 8  — Long-Term Memory
  ├─ SG 8.1 — Persistent Schema
  ├─ SG 8.2 — Memory Operations
  └─ SG 8.3 — Finding Persistence

GOAL 9  — Deduplication
  ├─ SG 9.1 — Finding Identity
  ├─ SG 9.2 — Finding Classification
  └─ SG 9.3 — Jira Deduplication

GOAL 10 — Retrieval Service
  ├─ SG 10.1 — Ticket Retrieval
  ├─ SG 10.2 — Customer Retrieval
  └─ SG 10.3 — Retrieval Reliability

GOAL 11 — Jira API Integration
  ├─ SG 11.1 — Authentication
  ├─ SG 11.2 — Jira Operations
  └─ SG 11.3 — Error Handling

GOAL 12 — Jira Execution Integration
  ├─ SG 12.1 — Actionable Findings
  ├─ SG 12.2 — Jira Actions
  └─ SG 12.3 — Persistence

GOAL 13 — Missing Data & Hallucination Prevention
  ├─ SG 13.1 — Missing Data
  ├─ SG 13.2 — Evidence Validation
  └─ SG 13.3 — Jira Blocking

GOAL 14 — Observability
  ├─ SG 14.1 — Planner Trace
  ├─ SG 14.2 — Executor Trace
  ├─ SG 14.3 — Jira Trace
  └─ SG 14.4 — Memory Trace

GOAL 15 — Development Environment
GOAL 16 — QA Environment

GOAL 17 — Acceptance Testing
  ├─ SG 17.1 — New Finding → Jira
  ├─ SG 17.2 — Existing Finding → No Duplicate
  └─ SG 17.3 — Missing Data → No Jira

GOAL 18 — Model Independence
  ├─ SG 18.1 — Planner Model
  ├─ SG 18.2 — Executor Model
  └─ SG 18.3 — Jira Model

GOAL 19 — Security & Production Readiness
  ├─ SG 19.1 — Secrets
  ├─ SG 19.2 — Access Control
  └─ SG 19.3 — Reliability

GOAL 20 — Documentation & Demonstration
  ├─ SG 20.1 — Technical Documentation
  └─ SG 20.2 — Demonstration Evidence
```

## Key acceptance outcome

The most important thing to demonstrate at the end is this complete chain:

```text
                    USER QUESTION
                          │
                          ▼
                 PLANNING AGENT
                 Strong Model
                          │
                          ▼
                  EXECUTION PLAN
                          │
                          ▼
                SHORT-TERM MEMORY
                          │
                          ▼
                 EXECUTION AGENT
                 Cost-Efficient Model
                          │
              ┌───────────┴───────────┐
              │                       │
              ▼                       ▼
       Retrieval Service        Working Memory
              │                       │
              └───────────┬───────────┘
                          ▼
                   FINDING FOUND
                          │
                          ▼
                LONG-TERM MEMORY
                   Check Existing
                    /        \
                  New       Existing
                   │            │
                   ▼            ▼
             JIRA AGENT    No Duplicate
           Lightweight          │
               Model            │
                   │            │
                   ▼            │
               JIRA API         │
                   │            │
                   ▼            │
              CREATE/UPDATE     │
                   │            │
                   └──────┬─────┘
                          ▼
                 LONG-TERM MEMORY
                          │
                          ▼
                   FINAL RESPONSE
```

**The three critical acceptance paths are therefore:**

| Scenario                         | Expected behavior                                                          |
| -------------------------------- | -------------------------------------------------------------------------- |
| **New actionable finding**       | Find → Jira Agent → Jira Create → Persist memory                           |
| **Previously actioned finding**  | Recall memory → recognize existing Jira → **no duplicate**                 |
| **Missing required information** | Detect missing data → clearly report → **no fabricated finding → no Jira** |

This gives you a clean **Goal → Sub-Goal → Task** structure while keeping each task directly traceable to the original requirement.
