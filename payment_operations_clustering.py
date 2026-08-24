"""Synthetic payment-operations clustering with preprocessing, Word2Vec, K-Means, and PCA.

Run from the Session2 folder:
    python payment_operations_clustering.py

The dataset is synthetic and contains 240 records. It is intended for training,
not for production decisions. This module imports preprocess_text from
payment_operations_agent.py so the clustering workflow uses the existing
preprocessing implementation.
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from gensim.models import Word2Vec
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score

from payment_operations_agent import preprocess_text


RANDOM_STATE = 42
N_RECORDS_PER_CATEGORY = 30
EMBEDDING_SIZE = 60
WINDOW = 5
EPOCHS = 150
K_VALUES = range(2, 9)
DATA_FILE = Path(__file__).with_name("payment_operations_records.csv")

CATEGORY_TEMPLATES = {
    "failed_payment": [
        "{method} payment failed for {actor} transaction {ref}; gateway returned {detail}.",
        "{method} payment was declined for {actor}; operations must verify {detail}.",
        "Payment attempt on {method} did not complete for {actor} because of {detail}.",
        "{actor} reports a failed {method} payment; reference {ref} needs status review.",
    ],
    "duplicate_debit": [
        "{actor} reports two {method} debits for transaction {ref}.",
        "Duplicate {method} charge appears in the ledger for {actor} reference {ref}.",
        "The same {method} payment was captured twice; reconcile authorization {ref}.",
        "Repeated debit detected on {method}; verify reversal eligibility for {actor}.",
    ],
    "refund_request": [
        "{actor} requested a refund for the {method} payment {ref}.",
        "Refund request received for {method} transaction {ref}; verify eligibility.",
        "Customer asks to reverse a {method} payment after the original transaction.",
        "Merchant submitted a refund case for {method}; authorization and status are required.",
    ],
    "chargeback": [
        "Chargeback notification received for {method} transaction {ref}; evidence is required.",
        "Card network opened a chargeback case for {actor}; review reason and deadline.",
        "Chargeback response package needs transaction evidence for reference {ref}.",
        "Unauthorized payment chargeback reported on {method}; route to disputes team.",
    ],
    "payment_dispute": [
        "{actor} disputes the {method} payment {ref}; investigate the transaction record.",
        "Payment dispute opened for {method}; collect customer reason and supporting evidence.",
        "Customer says the {method} transaction is not recognized; dispute review is needed.",
        "Merchant and customer disagree about {method} payment {ref}; preserve case history.",
    ],
    "settlement_mismatch": [
        "Merchant settlement for {method} does not match the expected payout {ref}.",
        "Settlement reconciliation found a missing {method} transaction in the ledger.",
        "Processor settlement total differs from expected amount; investigate batch {ref}.",
        "Merchant payout mismatch requires comparing settlement file with internal records.",
    ],
    "transfer_exception": [
        "{method} transfer is pending beyond the expected processing window for {actor}.",
        "{method} transfer returned because bank account information requires verification.",
        "Wire or ACH exception requires bank response, beneficiary details, and operations review.",
        "Payment rail exception is unresolved for reference {ref}; escalate if compliance risk appears.",
    ],
}

METHODS = ["card", "upi", "ach", "wire", "merchant"]
ACTORS = ["customer", "merchant", "operations team", "account holder"]
DETAILS = ["insufficient funds", "bank rejection", "timeout", "invalid account information", "processor error"]


def generate_synthetic_dataset() -> pd.DataFrame:
    """Generate 240 varied, labeled records for a reproducible demonstration."""
    rows = []
    record_number = 1
    categories = list(CATEGORY_TEMPLATES)
    for category_index, category in enumerate(categories):
        templates = CATEGORY_TEMPLATES[category]
        for index in range(N_RECORDS_PER_CATEGORY):
            template = templates[index % len(templates)]
            method = METHODS[(index + category_index) % len(METHODS)]
            actor = ACTORS[(index + category_index) % len(ACTORS)]
            detail = DETAILS[(index + category_index) % len(DETAILS)]
            ref = f"PO{category_index + 1:02d}{index + 1:04d}"
            text = template.format(method=method, actor=actor, detail=detail, ref=ref)
            rows.append({
                "id": f"CASE-{record_number:04d}",
                "text": text,
                "payment_method": method,
                "issue_type": category,
                "priority": "high" if category in {"chargeback", "settlement_mismatch"} else "medium",
                "merchant_or_customer": actor,
            })
            record_number += 1
    return pd.DataFrame(rows)


def load_data() -> pd.DataFrame:
    """Load the synthetic CSV, creating it if necessary."""
    if DATA_FILE.exists():
        df = pd.read_csv(DATA_FILE)
        if len(df) < 200:
            print("Existing dataset has fewer than 200 records; regenerating the synthetic dataset.")
            df = generate_synthetic_dataset()
            df.to_csv(DATA_FILE, index=False)
    else:
        df = generate_synthetic_dataset()
        df.to_csv(DATA_FILE, index=False)
    required = {"id", "text"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Dataset is missing required columns: {sorted(missing)}")
    if len(df) < 200:
        raise ValueError(f"At least 200 records are required; found {len(df)}")
    df["text"] = df["text"].fillna("").astype(str)
    df = df[df["text"].str.strip().ne("")].copy()
    if len(df) < 200:
        raise ValueError("At least 200 non-empty records are required after cleaning.")
    return df.reset_index(drop=True)


def average_embeddings(model: Word2Vec, cleaned_texts: pd.Series) -> np.ndarray:
    """Average known Word2Vec vectors for each cleaned record."""
    vectors = []
    zero_vector = np.zeros(model.vector_size, dtype=np.float32)
    for text in cleaned_texts:
        tokens = text.split()
        known = [model.wv[token] for token in tokens if token in model.wv]
        vectors.append(np.mean(known, axis=0) if known else zero_vector)
    return np.vstack(vectors)


def choose_k(embeddings: np.ndarray) -> tuple[pd.DataFrame, int]:
    rows = []
    for k in K_VALUES:
        model = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=20)
        labels = model.fit_predict(embeddings)
        rows.append({
            "k": k,
            "inertia": model.inertia_,
            "silhouette": silhouette_score(embeddings, labels),
        })
    scores = pd.DataFrame(rows)
    best_k = int(scores.loc[scores["silhouette"].idxmax(), "k"])
    return scores, best_k


def representative_rows(df: pd.DataFrame, embeddings: np.ndarray, model: KMeans, cluster: int, count: int = 3) -> pd.DataFrame:
    indexes = np.flatnonzero(model.labels_ == cluster)
    distances = np.linalg.norm(embeddings[indexes] - model.cluster_centers_[cluster], axis=1)
    selected = indexes[np.argsort(distances)[:count]]
    return df.iloc[selected]


def cluster_terms(df: pd.DataFrame, cluster: int, top_n: int = 8) -> list[str]:
    text = " ".join(df.loc[df["cluster"] == cluster, "cleaned_text"])
    return [term for term, _ in Counter(text.split()).most_common(top_n)]


def interpret_cluster(df: pd.DataFrame, cluster: int) -> str:
    labels = set(df.loc[df["cluster"] == cluster, "issue_type"])
    if labels & {"chargeback", "payment_dispute"}:
        return "Customer-facing dispute and chargeback investigation"
    if "settlement_mismatch" in labels:
        return "Merchant payout and settlement reconciliation"
    if labels & {"failed_payment", "transfer_exception"}:
        return "Payment failures and bank/rail exceptions"
    if "duplicate_debit" in labels:
        return "Duplicate debit investigation and correction"
    if "refund_request" in labels:
        return "Refund eligibility and payment reversal requests"
    return "Mixed payment-operations exception pattern"


def make_summary(df: pd.DataFrame, embeddings: np.ndarray, model: KMeans) -> pd.DataFrame:
    rows = []
    for cluster in sorted(df["cluster"].unique()):
        subset = df[df["cluster"] == cluster]
        representatives = representative_rows(df, embeddings, model, cluster)
        rows.append({
            "Cluster": cluster,
            "Records": len(subset),
            "Dominant Pattern": subset["issue_type"].value_counts().index[0],
            "Key Terms": ", ".join(cluster_terms(df, cluster)),
            "Payment Methods": ", ".join(subset["payment_method"].value_counts().head(3).index),
            "Interpretation": interpret_cluster(df, cluster),
            "Representative Records": " | ".join(representatives["text"].tolist()),
        })
    return pd.DataFrame(rows)


def plot_clusters(embeddings: np.ndarray, labels: np.ndarray, model: KMeans) -> None:
    coordinates = PCA(n_components=2, random_state=RANDOM_STATE).fit_transform(embeddings)
    plt.figure(figsize=(13, 9))
    for cluster in sorted(set(labels)):
        points = coordinates[labels == cluster]
        plt.scatter(points[:, 0], points[:, 1], s=28, alpha=0.72, label=f"Cluster {cluster}")
        center = coordinates[labels == cluster].mean(axis=0)
        plt.annotate(f"C{cluster}", center, fontsize=12, weight="bold")
    plt.title("Payment Operations Records — KMeans Clusters using Average Word2Vec + PCA")
    plt.xlabel("PCA Component 1")
    plt.ylabel("PCA Component 2")
    plt.legend()
    plt.grid(alpha=0.25)
    plt.tight_layout()
    plt.savefig(Path(__file__).with_name("payment_operations_clusters.png"), dpi=150)
    plt.show()


def main() -> None:
    print("PAYMENT OPERATIONS WORD2VEC + KMEANS WORKFLOW")
    print("Dataset is synthetic and created for NLP training; it is not production data.")
    df = load_data()
    print(f"\nRecords: {len(df)} | Columns: {len(df.columns)}")
    print(df.head(5).to_string(index=False))
    print("\nBasic statistics:")
    print(df.describe(include="all").transpose()[["count", "unique"]].to_string())

    df["cleaned_text"] = df["text"].apply(lambda value: preprocess_text(value))
    print("\nPREPROCESSING EXAMPLES")
    print(df[["text", "cleaned_text"]].head(5).to_string(index=False))

    token_lists = [text.split() for text in df["cleaned_text"]]
    word2vec = Word2Vec(
        sentences=token_lists,
        vector_size=EMBEDDING_SIZE,
        window=WINDOW,
        min_count=1,
        workers=1,
        epochs=EPOCHS,
        seed=RANDOM_STATE,
    )
    embeddings = average_embeddings(word2vec, df["cleaned_text"])
    print(f"\nEmbedding matrix shape: {embeddings.shape}")
    print(f"Word2Vec vocabulary size: {len(word2vec.wv)}")

    scores, best_k = choose_k(embeddings)
    print("\nK SELECTION (silhouette higher is better; inertia lower is better)")
    print(scores.round(4).to_string(index=False))
    print(f"Selected k={best_k} from the highest silhouette score. Review interpretability before production use.")

    kmeans = KMeans(n_clusters=best_k, random_state=RANDOM_STATE, n_init=20)
    df["cluster"] = kmeans.fit_predict(embeddings)
    print("\nCLUSTER SUMMARY")
    summary = make_summary(df, embeddings, kmeans)
    print(summary.drop(columns="Representative Records").to_string(index=False))

    for _, row in summary.iterrows():
        print(f"\nCluster {row['Cluster']} — {row['Interpretation']}")
        print(f"Size: {row['Records']} records")
        print(f"Common terms: {row['Key Terms']}")
        print("Representative records:")
        print("- " + "\n- ".join(row["Representative Records"].split(" | ")))
        print("Evidence-based interpretation: dominant issue type, terms, methods, and representative records shown above.")

    df.to_csv(Path(__file__).with_name("payment_operations_clustered.csv"), index=False)
    summary.to_csv(Path(__file__).with_name("payment_operations_cluster_summary.csv"), index=False)
    plot_clusters(embeddings, kmeans.labels_, kmeans)

    print("\nFINAL ANALYSIS")
    print("Clusters can support routing, evidence checklists, SLA queues, communication templates, and preventive-control monitoring.")
    print("Customer-facing patterns are usually failures, refunds, disputes, and chargebacks; settlement patterns are mainly merchant/reconciliation-related.")
    print("High-risk disputes, chargebacks, ambiguous cases, and financially significant mismatches should remain human-in-the-loop.")
    print("Some categories overlap because short messages share payment, transaction, customer, and operations vocabulary; average Word2Vec vectors also lose word order.")
    print("These findings are statistical and synthetic. Validate cluster meanings on real labeled operations data before using them for decisions.")


if __name__ == "__main__":
    main()
