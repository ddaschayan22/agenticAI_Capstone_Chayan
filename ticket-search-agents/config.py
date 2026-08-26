"""Configuration for the planner/executor ticket-search workflow."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
TICKETS_DIR = PROJECT_ROOT / "data" / "tickets"
CHROMA_DB_DIR = PROJECT_ROOT / "data" / "chroma_db"
COLLECTION_NAME = "support_tickets"
EMBEDDING_MODEL = "local-hashing-512"
DEFAULT_TOP_K = 4
LOG_FILE = PROJECT_ROOT / "data" / "agent_workflow.log"
DETAIL_LOG_FILE = PROJECT_ROOT / "data" / "task_execution_details.jsonl"
