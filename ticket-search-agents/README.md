# Semantic Ticket Search — Planner and Executor Agents

A new workflow built around the existing `semantic-ticket-search` project.

## Agents

- **PlannerAgent**: converts a customer issue into an ordered task plan and selects the tools required for each task.
- **ExecutorAgent**: executes only the tools assigned by `PlannerAgent`, passes results between tasks, and returns structured outcomes.

The `PlannerAgent` saves tasks in `data/tasks.json` with `status: "pending"`. The `ExecutorAgent` reads that file, executes pending tasks, and updates each status to `in_progress`, then `resolved` or `failed`. The task file is ignored by Git because it is runtime state.

Ticket source files and the ChromaDB index are self-contained in this project:

- Tickets: `data/tickets/*.txt`
- ChromaDB index: `data/chroma_db/`

## Tools

- `search_tickets(query, top_k)` — retrieves semantic ticket matches using the existing ChromaDB search project.
- `get_ticket(ticket_id)` — retrieves the complete ticket text, including customer issue and resolution.

## Logs

Tasks are saved to `data/tasks.json`. The planner creates tasks with `status: "pending"`; the executor reads that file and updates each task to `in_progress`, then `resolved` or `failed`.

Logs are written to `data/agent_workflow.log` and include:

```text
agent_name=PlannerAgent | agent_type=planner
agent_name=ExecutorAgent | agent_type=executor
```

Each log also records task creation, task-file persistence, task selection, tool execution, status changes, outcomes, skips, and failures.

Detailed tool parameters, tool outcomes, and the reason for every task/tool outcome are also stored in `data/task_execution_details.jsonl`.

## Run

Install the dependencies if needed:

```powershell
pip install -r requirements.txt
```

Run from this directory:

```powershell
python main.py
```

Enter a customer issue such as `card payment approved but order not completed`. The planner creates the plan, and the executor runs the semantic search and complete-ticket retrieval tools using the local tickets and local ChromaDB index.
