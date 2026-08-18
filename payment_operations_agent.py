"""Agentic payment-operations demonstration.

This program is intentionally local and deterministic: it uses a synthetic,
clearly labeled dataset, an interpretable baseline classifier, configurable NLP
preprocessing experiments, evidence checks, policy rules, SLA prioritization,
communication drafting, escalation, and an optional historical-risk estimate.

Run:
    python payment_operations_agent.py

The model is an educational baseline, not an autonomous financial decision-maker.
"""

from __future__ import annotations

import json
import re
import time
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline


RANDOM_STATE = 42
DATA_FILE = Path(__file__).with_name("payment_cases_synthetic.json")

CATEGORIES = [
    "failed_payment",
    "duplicate_debit",
    "refund_request",
    "chargeback",
    "payment_dispute",
    "settlement_mismatch",
    "other_exception",
]

STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "been", "but", "by", "for",
    "from", "has", "have", "in", "is", "it", "my", "of", "on", "or", "our",
    "please", "that", "the", "this", "to", "was", "were", "with", "you", "your",
}

# Small rule-based lemmatizer keeps this project dependency-light and repeatable.
LEMMA_MAP = {
    "payments": "payment", "failed": "fail", "failures": "failure", "debits": "debit",
    "chargebacks": "chargeback", "disputes": "dispute", "refunds": "refund",
    "requests": "request", "mismatches": "mismatch", "exceptions": "exception",
    "transactions": "transaction", "transactions": "transaction", "merchants": "merchant",
    "customers": "customer", "systems": "system", "amounts": "amount", "days": "day",
    "missing": "miss", "received": "receive", "processing": "process", "processed": "process",
    "declined": "decline", "duplicated": "duplicate", "requested": "request",
}


@dataclass
class PaymentCase:
    case_id: str
    text: str
    label: str


@dataclass
class AgentResult:
    case_id: str
    issue_category: str
    payment_method: str
    severity_priority: str
    extracted_transaction_information: dict[str, Any]
    case_summary: str
    supporting_evidence: list[str]
    missing_evidence: list[str]
    recommended_resolution: str
    policy_rule_used: str
    sla_priority_or_urgency: str
    communication_draft: str
    escalation_required: str
    escalation_reason: str
    recommended_operations_team: str
    dispute_chargeback_likelihood: str
    preventive_control_recommendations: list[str]


def synthetic_cases() -> list[PaymentCase]:
    """Return a labeled synthetic dataset for demonstration and evaluation."""
    examples = {
        "failed_payment": [
            "Card payment failed for transaction TX1001 with error insufficient funds.",
            "UPI payment declined for TX1002; customer says the payment did not go through.",
            "ACH debit failed for TX1003 because the bank account could not be verified.",
            "Payment gateway returned a failure for card transaction TX1004.",
            "Wire transfer failed for TX1005 with bank rejection message.",
        ],
        "duplicate_debit": [
            "Customer reports two card debits for transaction TX2001 for $50.",
            "UPI payment appears duplicated; two debits show for reference TX2002.",
            "The same ACH payment was charged twice under TX2003.",
            "Merchant sees duplicate card capture for order TX2004.",
            "Customer reports repeated debit for wire reference TX2005.",
        ],
        "refund_request": [
            "Customer requests a refund for card transaction TX3001.",
            "Please investigate my UPI refund request for reference TX3002.",
            "Merchant asks for a refund on ACH payment TX3003.",
            "I want to request a refund for wire transfer TX3004.",
            "Customer wants payment reversed for card reference TX3005.",
        ],
        "chargeback": [
            "Chargeback notification received for card transaction TX4001.",
            "The cardholder filed a chargeback for payment TX4002.",
            "Merchant received a chargeback case with reason unauthorized transaction TX4003.",
            "Chargeback deadline requires evidence for TX4004.",
            "Network chargeback alert received for card payment TX4005.",
        ],
        "payment_dispute": [
            "Customer disputes a card payment TX5001 and requests investigation.",
            "UPI transaction TX5002 is disputed by the customer.",
            "Merchant and customer disagree about payment TX5003.",
            "Please review the payment dispute for ACH transaction TX5004.",
            "Customer says the wire payment TX5005 is not recognized and disputes it.",
        ],
        "settlement_mismatch": [
            "Settlement amount does not match the ledger for merchant TX6001.",
            "Merchant settlement is missing for UPI batch TX6002.",
            "ACH settlement total differs from expected amount TX6003.",
            "Wire settlement reconciliation shows a mismatch for TX6004.",
            "Card settlement transaction TX6005 is missing from the report.",
        ],
        "other_exception": [
            "Payment message cannot be interpreted for transaction TX7001.",
            "Merchant account has a policy-sensitive payment exception TX7002.",
            "Operations received an unclear issue with reference TX7003.",
            "Payment status is ambiguous and needs human review TX7004.",
            "High-risk payment exception was reported for TX7005.",
        ],
    }
    return [
        PaymentCase(f"SYN-{category[:3].upper()}-{index:03d}", text, category)
        for category, texts in examples.items()
        for index, text in enumerate(texts, start=1)
    ]


def load_dataset() -> list[PaymentCase]:
    """Load JSON if present; otherwise create and save the labeled synthetic data."""
    if DATA_FILE.exists():
        try:
            raw = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            return [PaymentCase(**item) for item in raw]
        except (OSError, json.JSONDecodeError, TypeError, KeyError) as exc:
            print(f"Warning: could not load dataset ({exc}); using synthetic data.")

    cases = synthetic_cases()
    DATA_FILE.write_text(json.dumps([asdict(case) for case in cases], indent=2), encoding="utf-8")
    return cases


def preprocess_text(text: str, remove_stopwords: bool = True, lemmatize: bool = True) -> str:
    """Reusable preprocessing function for all four experiment configurations."""
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    if remove_stopwords:
        tokens = [token for token in tokens if token not in STOP_WORDS]
    if lemmatize:
        tokens = [LEMMA_MAP.get(token, token) for token in tokens]
    return " ".join(tokens)


def configuration_name(remove_stopwords: bool, lemmatize: bool) -> str:
    return f"Stopwords {'ON' if remove_stopwords else 'OFF'} / Lemmatization {'ON' if lemmatize else 'OFF'}"


def evaluate_configuration(cases: list[PaymentCase], remove_stopwords: bool, lemmatize: bool) -> dict[str, Any]:
    start = time.perf_counter()
    texts = [preprocess_text(case.text, remove_stopwords, lemmatize) for case in cases]
    labels = [case.label for case in cases]
    train_texts, test_texts, train_labels, test_labels = train_test_split(
        texts, labels, test_size=0.30, random_state=RANDOM_STATE, stratify=labels
    )
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2))),
        ("classifier", LogisticRegression(max_iter=2000, random_state=RANDOM_STATE)),
    ])
    pipeline.fit(train_texts, train_labels)
    predictions = pipeline.predict(test_texts)
    elapsed = time.perf_counter() - start
    return {
        "configuration": configuration_name(remove_stopwords, lemmatize),
        "remove_stopwords": remove_stopwords,
        "lemmatize": lemmatize,
        "accuracy": accuracy_score(test_labels, predictions),
        "precision_macro": precision_score(test_labels, predictions, average="macro", zero_division=0),
        "recall_macro": recall_score(test_labels, predictions, average="macro", zero_division=0),
        "macro_f1": f1_score(test_labels, predictions, average="macro", zero_division=0),
        "weighted_f1": f1_score(test_labels, predictions, average="weighted", zero_division=0),
        "seconds": elapsed,
        "confusion_matrix": confusion_matrix(test_labels, predictions, labels=CATEGORIES).tolist(),
    }


def run_preprocessing_experiment(cases: list[PaymentCase]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    results = [
        evaluate_configuration(cases, remove_stopwords, lemmatize)
        for remove_stopwords, lemmatize in [(False, False), (True, False), (False, True), (True, True)]
    ]
    best = max(results, key=lambda result: (result["macro_f1"], result["weighted_f1"], result["accuracy"]))
    return results, best


def extract_entities(text: str) -> dict[str, Any]:
    amount_matches = re.findall(r"(?:[$€£]\s?\d+(?:\.\d{1,2})?|\b\d+(?:\.\d{1,2})?\s?(?:usd|inr|eur|gbp)\b)", text, re.I)
    transaction_ids = re.findall(r"\b(?:TX|REF|ORD|ID)[-_]?\d{3,}\b", text, re.I)
    methods = [method for method in ["card", "upi", "ach", "wire", "merchant"] if re.search(rf"\b{method}\b", text, re.I)]
    return {
        "transaction_ids": sorted(set(transaction_ids), key=str.lower),
        "amounts": amount_matches,
        "payment_methods": methods,
        "dates": re.findall(r"\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b", text),
        "error_messages": re.findall(r"(?:error|reason|message)\s+[^.;]+", text, re.I),
    }


def classify_issue(text: str) -> str:
    lowered = text.lower()
    rules = [
        ("duplicate_debit", ["duplicate", "twice", "two debits", "repeated debit"]),
        ("chargeback", ["chargeback"]),
        ("settlement_mismatch", ["settlement", "ledger", "reconciliation", "does not match", "missing from the report"]),
        ("refund_request", ["refund", "reversed"]),
        ("payment_dispute", ["dispute", "disputed", "disagree", "not recognized"]),
        ("failed_payment", ["failed", "failure", "declined", "did not go through", "rejected"]),
    ]
    for category, keywords in rules:
        if any(keyword in lowered for keyword in keywords):
            return category
    return "other_exception"


def gather_evidence(text: str, category: str, entities: dict[str, Any]) -> tuple[list[str], list[str]]:
    available = []
    missing = []
    if entities["transaction_ids"]:
        available.append("Transaction/reference ID present")
    else:
        missing.append("Transaction/reference ID")
    if entities["amounts"]:
        available.append("Amount present")
    else:
        missing.append("Amount and currency")
    if entities["payment_methods"]:
        available.append(f"Payment method identified: {', '.join(entities['payment_methods'])}")
    else:
        missing.append("Payment method or rail")
    if entities["error_messages"]:
        available.append("Error/reason text present")
    if category in {"chargeback", "payment_dispute"}:
        missing.append("Dispute reason, transaction record, and required supporting evidence")
    if category == "settlement_mismatch":
        missing.append("Processor settlement report and ledger/reconciliation comparison")
    if category == "refund_request":
        missing.append("Refund eligibility, original transaction status, and authorization")
    if not available:
        available.append("Only the submitted free-text case is available")
    return available, list(dict.fromkeys(missing))


def decide_case(text: str, category: str, evidence: list[str], missing: list[str]) -> tuple[str, str, str, str, str, str, str, str, list[str]]:
    lowered = text.lower()
    high_risk = any(term in lowered for term in ["high-risk", "unauthorized", "policy-sensitive", "compliance"])
    financially_sensitive = category in {"chargeback", "payment_dispute", "settlement_mismatch", "refund_request", "duplicate_debit"}
    ambiguous = category == "other_exception" or not evidence or len(missing) >= 3
    escalate = high_risk or financially_sensitive or ambiguous
    priority = "P1 - urgent human review" if high_risk else "P2 - high operational priority" if escalate else "P3 - standard review"
    sla = "Immediate routing to operations/compliance queue" if high_risk else "Review within the configured team SLA; no unsupported timeline promised"
    teams = {
        "failed_payment": "Payments operations",
        "duplicate_debit": "Payments operations and reconciliation",
        "refund_request": "Refunds/payment operations",
        "chargeback": "Disputes and chargebacks",
        "payment_dispute": "Disputes and chargebacks",
        "settlement_mismatch": "Settlement and reconciliation",
        "other_exception": "Payments operations triage",
    }
    resolutions = {
        "failed_payment": "Verify gateway/bank response, transaction status, and retry eligibility; do not claim success.",
        "duplicate_debit": "Reconcile authorization and capture records, then determine the corrective action under approved policy.",
        "refund_request": "Validate the original transaction and refund policy; request authorization before approving any refund.",
        "chargeback": "Open the chargeback workflow, preserve the deadline and evidence, and route for authorized response review.",
        "payment_dispute": "Investigate transaction records and dispute reason before recommending a customer or merchant outcome.",
        "settlement_mismatch": "Compare processor settlement data with the internal ledger and route discrepancies to reconciliation.",
        "other_exception": "Triage the message, identify the missing facts, and obtain human review before taking action.",
    }
    rule = "No refund, compensation, outcome, or completed action is asserted; configured policy and evidence review are required."
    reason = "High-risk, financially sensitive, ambiguous, or evidence-incomplete case." if escalate else "Case has a defined category and can begin standard evidence review."
    likelihood = "Not estimated: this demonstration has no independent historical dataset for safe prediction." 
    controls = []
    if "failure" in lowered or category == "failed_payment":
        controls.append("Track recurring gateway/bank failure codes and review preventive retry or routing controls.")
    if category in {"chargeback", "payment_dispute"}:
        controls.append("Improve evidence completeness and monitor recurring dispute reasons.")
    if not controls:
        controls.append("Collect labeled historical outcomes before recommending a case-specific preventive control.")
    return priority, sla, resolutions[category], rule, ("Yes" if escalate else "No"), reason, teams[category], likelihood, controls


def draft_communication(category: str, entities: dict[str, Any], escalation: str, missing: list[str]) -> str:
    audience = "customer or merchant"
    reference = entities["transaction_ids"][0] if entities["transaction_ids"] else "the referenced transaction"
    request = ", ".join(missing[:3]) if missing else "any additional information needed for verification"
    return (
        f"Hello,\n\nThank you for contacting us about {reference}. We understand that this {category.replace('_', ' ')} matter needs attention. "
        f"We are reviewing the information provided and have not assumed that any refund, correction, or other outcome is approved. "
        f"To help the {audience}, please provide {request}. "
        + ("This case will be routed for human operations review because it is risk- or policy-sensitive. " if escalation == "Yes" else "We will continue with the standard operations review. ")
        + "Regards,\nPayments Operations"
    )


def run_agent(case_text: str, selected_config: dict[str, Any]) -> AgentResult:
    category = classify_issue(case_text)
    entities = extract_entities(case_text)
    evidence, missing = gather_evidence(case_text, category, entities)
    decision = decide_case(case_text, category, evidence, missing)
    priority, sla, resolution, rule, escalation, reason, team, likelihood, controls = decision
    summary = f"Classified as {category.replace('_', ' ')} with {priority.lower()}; evidence review is required before any outcome."
    return AgentResult(
        case_id="LIVE-001",
        issue_category=category,
        payment_method=", ".join(entities["payment_methods"]) or "Unknown",
        severity_priority=priority,
        extracted_transaction_information=entities,
        case_summary=summary,
        supporting_evidence=evidence,
        missing_evidence=missing,
        recommended_resolution=resolution,
        policy_rule_used=rule,
        sla_priority_or_urgency=sla,
        communication_draft=draft_communication(category, entities, escalation, missing),
        escalation_required=escalation,
        escalation_reason=reason,
        recommended_operations_team=team,
        dispute_chargeback_likelihood=likelihood,
        preventive_control_recommendations=controls,
    )


def print_agent_result(result: AgentResult) -> None:
    print("\nAGENT RESULT")
    print(json.dumps(asdict(result), indent=2))


def main() -> None:
    cases = load_dataset()
    print("AGENTIC PAYMENTS OPERATIONS SOLUTION")
    print("Dataset: synthetic labeled payment cases for education and evaluation.")
    results, best = run_preprocessing_experiment(cases)
    table = [{key: value for key, value in result.items() if key != "confusion_matrix" and key not in {"remove_stopwords", "lemmatize"}} for result in results]
    print("\nPREPROCESSING EXPERIMENT")
    print("Same preprocessing function; same TF-IDF + Logistic Regression baseline; macro F1 selects the winner.")
    print(json.dumps(table, indent=2))
    print(f"\nBEST CONFIGURATION: {best['configuration']} (macro F1={best['macro_f1']:.3f})")
    print("Confusion matrices use rows=true labels and columns=predicted labels in CATEGORIES order:")
    for result in results:
        print(f"{result['configuration']}: {result['confusion_matrix']}")

    print("\nINTERACTIVE CASE ANALYSIS")
    print("Enter messy payment-operation text, or press Enter to run a representative example.")
    case_text = input("> ").strip()
    if not case_text:
        case_text = "UPI payment TX9001 failed twice and the customer says the amount was debited. Please investigate."
        print(f"Using example: {case_text}")
    print_agent_result(run_agent(case_text, best))
    print("\nResponsible-AI note: high-risk, financially sensitive, ambiguous, and evidence-incomplete cases are not autonomously approved; they are routed for human review.")
    print("Word2Vec/LLM-style semantic claims are not used here; this reproducible baseline is intentionally interpretable.")


if __name__ == "__main__":
    main()
