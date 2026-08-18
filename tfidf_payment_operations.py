"""TF-IDF analysis of payment-operations documents.

Install the only external dependency if necessary:
    pip install scikit-learn

Run with:
    python tfidf_payment_operations.py
"""

import re
from typing import Dict, List, Sequence, Tuple

from sklearn.feature_extraction.text import TfidfVectorizer


DOCUMENTS: List[Tuple[str, str]] = [
    (
        "Document 1 - Payment Operations",
        "Build an agentic payments operations solution that monitors failed "
        "payments, duplicate debits, chargebacks, refund requests, and "
        "settlement mismatches across card, UPI, ACH, wire, and merchant systems.",
    ),
    (
        "Document 2 - Dispute Prediction",
        "Predict dispute likelihood and suggest preventive controls for recurring "
        "failure patterns.",
    ),
    (
        "Document 3 - Operations Efficiency",
        "Reduce payment operations effort and improve resolution speed for "
        "exceptions, disputes, and chargebacks.",
    ),
    (
        "Document 4 - Payment Intelligence",
        "Payment message interpretation, exception classification, dispute lifecycle "
        "automation, evidence retrieval, policy-based decisioning, SLA prioritization, "
        "and responsible escalation design.",
    ),
    (
        "Document 5 - Agent Responsibilities",
        "The agent should classify the issue, gather supporting evidence, recommend "
        "the correct resolution path, draft customer or merchant communication, and "
        "route high-risk or policy-sensitive cases to operations teams.",
    ),
]


WHY_IMPORTANT: Dict[str, str] = {
    "payment": "Core payment-operations subject and workflow context.",
    "payments": "Identifies payment transactions and operational scope.",
    "operations": "Describes the operational environment and target users.",
    "chargebacks": "Important payment-risk and post-transaction process.",
    "disputes": "Represents customer/payment disputes and their handling.",
    "dispute": "Signals dispute prediction and risk-management work.",
    "settlement": "Relates to reconciling and completing movement of funds.",
    "exceptions": "Identifies cases requiring investigation or intervention.",
    "exception": "Identifies classification and handling of unusual cases.",
    "resolution": "Represents the desired outcome for operational cases.",
    "evidence": "Supports explainable decisions and dispute handling.",
    "classification": "Enables routing and structured treatment of issues.",
    "automation": "Connects the analysis to agentic workflow automation.",
    "escalation": "Describes safe handoff of complex or risky cases.",
    "sla": "Represents service-level prioritization and operational urgency.",
    "merchant": "Important payment-network participant and communication audience.",
    "customer": "Important end-user communication and service audience.",
    "communication": "Represents customer and merchant case updates.",
    "agentic": "Directly describes the intended intelligent-agent solution.",
    "upi": "Payment rail-specific terminology.",
    "ach": "Payment rail-specific terminology.",
}


def clean_text(text: str) -> str:
    """Lowercase text and replace punctuation with spaces."""
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def format_table(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> str:
    """Return a simple, dependency-free table for terminal output."""
    widths = [len(header) for header in headers]
    for row in rows:
        for index, value in enumerate(row):
            widths[index] = max(widths[index], len(str(value)))

    def row_text(row: Sequence[str]) -> str:
        return " | ".join(str(value).ljust(widths[i]) for i, value in enumerate(row))

    separator = "-+-".join("-" * width for width in widths)
    return "\n".join([row_text(headers), separator] + [row_text(row) for row in rows])


def reason_for(term: str, document_names: Sequence[str]) -> str:
    """Provide beginner-friendly domain context for a term."""
    return WHY_IMPORTANT.get(
        term,
        f"Distinctive vocabulary found mainly in {', '.join(document_names)}.",
    )


def main() -> None:
    names = [name for name, _ in DOCUMENTS]
    raw_documents = [text for _, text in DOCUMENTS]
    cleaned_documents = [clean_text(text) for text in raw_documents]

    # norm='l1' makes term-frequency values comparable within each document.
    vectorizer = TfidfVectorizer(stop_words="english", norm="l1")
    matrix = vectorizer.fit_transform(cleaned_documents)
    terms = vectorizer.get_feature_names_out()

    print("TF-IDF ANALYSIS: PAYMENT OPERATIONS\n")
    print("DOCUMENTS")
    for number, (name, text) in enumerate(DOCUMENTS, start=1):
        print(f"{number}. {name}: {text}")

    # Overall importance is the sum of each term's TF-IDF scores across documents.
    overall_scores = matrix.sum(axis=0).A1
    term_document_scores = matrix.toarray()
    ranked_indices = sorted(
        range(len(terms)),
        key=lambda index: (-overall_scores[index], terms[index]),
    )

    print("\nTOP 15 TERMS ACROSS THE CORPUS")
    overall_rows = []
    for rank, index in enumerate(ranked_indices[:15], start=1):
        document_names = [
            names[doc_index]
            for doc_index, score in enumerate(term_document_scores[:, index])
            if score > 0
        ]
        overall_rows.append(
            [
                str(rank),
                terms[index],
                f"{overall_scores[index]:.4f}",
                ", ".join(document_names),
                reason_for(terms[index], document_names),
            ]
        )
    print(format_table(["Rank", "Term", "TF-IDF Score", "Document(s)", "Why It May Be Important"], overall_rows))

    print("\nTOP TF-IDF TERMS BY DOCUMENT")
    for doc_index, name in enumerate(names):
        document_indices = sorted(
            range(len(terms)),
            key=lambda index: (-term_document_scores[doc_index, index], terms[index]),
        )
        rows = [
            [str(rank), terms[index], f"{term_document_scores[doc_index, index]:.4f}"]
            for rank, index in enumerate(
                [i for i in document_indices if term_document_scores[doc_index, i] > 0][:5],
                start=1,
            )
        ]
        print(f"\n{name}")
        print(format_table(["Rank", "Term", "TF-IDF Score"], rows))

    print("\nINTERPRETATION")
    print("- TF-IDF means Term Frequency-Inverse Document Frequency.")
    print("- It increases when a term is prominent in one document but uncommon in the corpus.")
    print("- A term appearing in all five documents usually receives lower IDF because it is less distinctive.")
    print("- The 15 terms above are the most statistically distinctive terms in this small dataset.")
    print("- Terms especially relevant to an agentic solution include failures, disputes, chargebacks,")
    print("  settlement, exceptions, evidence, resolution, classification, automation, escalation, SLA,")
    print("  and customer/merchant communication.")
    print("- Important limitation: TF-IDF measures statistical distinctiveness, not business importance.")
    print("  A high score does not automatically mean that a term is the most important business concept.")
    print("- Results depend on preprocessing, the corpus, and the TF-IDF settings used here.")


if __name__ == "__main__":
    main()