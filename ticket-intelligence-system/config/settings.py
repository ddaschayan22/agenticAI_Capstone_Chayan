from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env", override=True)


@dataclass(frozen=True)
class Settings:
    data_file: Path = Path(os.getenv("TICKET_DATA_FILE", "../Problem18/Tickets/TicketsForReference.txt"))
    chroma_directory: Path = Path(os.getenv("CHROMA_PERSIST_DIRECTORY", "./data/chroma"))
    jira_base_url: str = os.getenv("JIRA_BASE_URL", "")
    jira_email: str = os.getenv("JIRA_EMAIL", "")
    jira_api_token: str = os.getenv("JIRA_API_TOKEN", "")
    jira_project_key: str = os.getenv("JIRA_PROJECT_KEY", "SUP")
    jira_issue_type: str = os.getenv("JIRA_ISSUE_TYPE", "Task")
    jira_timeout_seconds: float = float(os.getenv("JIRA_TIMEOUT_SECONDS", "30"))
    dry_run: bool = os.getenv("JIRA_DRY_RUN", "true").lower() == "true"
    planner_model: str = os.getenv("PLANNER_MODEL", "deterministic-planner")
    executor_model: str = os.getenv("EXECUTOR_MODEL", "deterministic-executor")
    jira_action_model: str = os.getenv("JIRA_ACTION_MODEL", "deterministic-jira-action")
    max_retries: int = int(os.getenv("MAX_EXECUTOR_RETRIES", "3"))
    low_relevance_threshold: float = float(os.getenv("LOW_RELEVANCE_THRESHOLD", "0.5"))
    search_result_limit: int = int(os.getenv("SEARCH_RESULT_LIMIT", "3"))
    create_ticket_confidence_threshold: float = float(os.getenv("CREATE_TICKET_CONFIDENCE_THRESHOLD", "0.8"))

    def resolved_data_file(self) -> Path:
        if self.data_file.is_absolute():
            return self.data_file
        return (PROJECT_ROOT / self.data_file).resolve()
