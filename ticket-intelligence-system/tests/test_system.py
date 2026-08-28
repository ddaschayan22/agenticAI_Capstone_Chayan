from pathlib import Path

from config.settings import Settings
from memory.store import MemoryStore
from retrieval.ticket_service import TicketService
from orchestration.orchestrator import Orchestrator


ROOT = Path(__file__).parents[1]
DATA = ROOT.parent / "Problem18" / "Tickets" / "TicketsForReference.txt"


def test_reference_dataset_is_loaded():
    service = TicketService(DATA)
    assert len(service.tickets) == 60
    assert service.get_ticket("IT-001")["customer_id"] == "CUST-101"


def test_missing_ticket_never_creates_business_action(tmp_path):
    settings = Settings(data_file=DATA, chroma_directory=tmp_path, dry_run=True)
    result = Orchestrator(settings).run("Investigate ticket IT-9999")
    assert result["execution"] == "BLOCKED"
    assert result["jira_actions"] == []
    assert result["missing_information"]


def test_working_memory_is_cleared(tmp_path):
    memory = MemoryStore(tmp_path)
    memory.working = {"step_id": "STEP-001", "temporary": True}
    memory.clear_working()
    assert memory.working == {}


def test_compound_workflow_creates_runtime_task_and_completes(tmp_path):
    settings = Settings(data_file=DATA, chroma_directory=tmp_path, dry_run=True)
    orchestrator = Orchestrator(settings)
    result = orchestrator.run("Which customers had the same login issue as IT-001, and did any churn afterward?")
    assert result["runtime_jira_issue"].startswith("SUP-DRY-")
    assert result["steps_completed"] == result["steps_total"]
    assert result["execution"] == "COMPLETED"
    assert orchestrator.jira.comments


def test_payment_refund_request_creates_business_action(tmp_path):
    settings = Settings(data_file=DATA, chroma_directory=tmp_path, dry_run=True)
    result = Orchestrator(settings).run("I want to create Jira ticket for a payment issue. My refund is still not processed for paymentID: 34567")
    assert result["execution"] == "COMPLETED"
    assert result["missing_information"] == []
    assert result["jira_actions"][0]["action"] == "CREATE"
    assert result["jira_actions"][0]["jira_issue"]["key"].startswith("SUP-DRY-")


def test_free_text_ticket_question_searches_dataset(tmp_path):
    settings = Settings(data_file=DATA, chroma_directory=tmp_path, dry_run=True)
    result = Orchestrator(settings).run("login failing repeatedly")
    assert result["execution"] == "COMPLETED"
    assert result["missing_information"] == []
    assert result["fresh_findings"] == []
    assert len(result["jira_actions"]) == 1


def test_low_relevance_ticket_creates_business_action(tmp_path):
    settings = Settings(data_file=DATA, chroma_directory=tmp_path, dry_run=True, low_relevance_threshold=0.5)
    orchestrator = Orchestrator(settings)
    result = orchestrator.run("login failing repeatedly")
    assert result["execution"] == "COMPLETED"
    assert result["jira_actions"]
    assert all(action["action"] == "CREATE" for action in result["jira_actions"])
    assert len(result["fresh_findings"]) == 0
    assert "new-user-request-ticket" in result["jira_actions"][0]["jira_issue"]["fields"]["labels"]


def test_high_confidence_top_result_prevents_low_confidence_action(tmp_path):
    settings = Settings(data_file=DATA, chroma_directory=tmp_path, dry_run=True, search_result_limit=3, create_ticket_confidence_threshold=0.8)
    result = Orchestrator(settings).run("login authentication password reset access")
    assert len(result["fresh_findings"]) == 3
    assert max(item["relevance"] for item in result["fresh_findings"]) >= 0.8
    assert result["jira_actions"] == []


def test_any_fetched_ticket_at_or_above_point_eight_blocks_creation(tmp_path):
    settings = Settings(data_file=DATA, chroma_directory=tmp_path, dry_run=True, search_result_limit=3, create_ticket_confidence_threshold=0.8)
    result = Orchestrator(settings).run("login authentication password reset access")
    assert any(finding["relevance"] >= 0.8 for finding in result["fresh_findings"])
    assert result["jira_actions"] == []


def test_low_confidence_similar_matches_create_one_request_ticket(tmp_path):
    settings = Settings(data_file=DATA, chroma_directory=tmp_path, dry_run=True, search_result_limit=3, create_ticket_confidence_threshold=0.8)
    result = Orchestrator(settings).run("Which tickets are related to IT-001?")
    assert result["execution"] == "COMPLETED"
    assert result["steps_completed"] == 2
    assert len(result["fresh_findings"]) == 1
    assert len(result["jira_actions"]) == 1
    action_issue = result["jira_actions"][0]["jira_issue"]
    assert "new-user-request-ticket" in action_issue["fields"]["labels"]
    assert "relevance" not in action_issue
