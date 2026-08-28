# Ticket Intelligence System

A modular educational implementation of the Problem18 ticket-intelligence workflow. It uses exactly three specialized agents:

1. `TicketPlanningAgent` — decomposes a request into validated steps.
2. `TicketExecutionAgent` — performs deterministic retrieval and multi-hop analysis.
3. `JiraActionAgent` — deduplicates validated actionable findings and creates business actions.

The `Orchestrator` controls execution, structured JSON contracts, context flow, Jira runtime tracking, and memory isolation. Jira is accessed through a REST client/service; no MCP server is used.

## Quick start

From this directory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python main.py
```

The default `JIRA_DRY_RUN=true` creates local deterministic Jira issue keys and stores comments in the service, so the acceptance flow can be demonstrated without credentials. Set it to `false` only after configuring Jira credentials in environment variables. Never commit `.env` or expose API tokens to agents, memory, or comments.

The default dataset path points to `Problem18/Tickets/TicketsForReference.txt`. Override it with `TICKET_DATA_FILE` when running from another location.

## Example

Ask: `Which customers had the same login issue as IT-001, and did any of them churn afterward?`

The result separates runtime Jira tracking, fresh findings, recalled findings, business Jira actions, missing information, and step completion. Long-term findings are persisted under `data/chroma/long_term_memory.json`; the storage interface is intentionally isolated so a ChromaDB collection can be enabled without changing agent contracts.

## Security and design notes

- Credentials are environment-driven and never persisted in memory.
- Tool access is intended to be centralized; agents receive structured contracts rather than arbitrary calls.
- Working memory is cleared after every step.
- Missing tickets produce `MISSING_DATA` and never trigger a business ticket.
- Finding identity is deterministic and based on business identifiers, not generated prose.
- Historical searches return the top three results. A business Jira ticket is created only when none of those three results has relevance/similarity of at least `0.8`.
- Production hardening should add Jira transition discovery, retry/backoff, real Chroma collections, model-provider implementations, and integration tests against a Jira sandbox.
