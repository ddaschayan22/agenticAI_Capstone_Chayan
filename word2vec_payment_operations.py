"""Word2Vec, K-Means, and PCA analysis for payment-operations documents.

Install dependencies if needed:
    pip install gensim scikit-learn matplotlib pandas
"""

import re
from typing import List

import matplotlib.pyplot as plt
import pandas as pd
from gensim.models import Word2Vec
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA


N_CLUSTERS = 3
VECTOR_SIZE = 50
WINDOW = 4
EPOCHS = 300
RANDOM_SEED = 42

DOCUMENTS = [
    "Build an agentic payments operations solution that monitors failed payments, duplicate debits, chargebacks, refund requests, and settlement mismatches across card, UPI, ACH, wire, and merchant systems.",
    "Predict dispute likelihood and suggest preventive controls for recurring failure patterns.",
    "Reduce payment operations effort and improve resolution speed for exceptions, disputes, and chargebacks.",
    "Payment message interpretation, exception classification, dispute lifecycle automation, evidence retrieval, policy-based decisioning, SLA prioritization, and responsible escalation design.",
    "The agent should classify the issue, gather supporting evidence, recommend the correct resolution path, draft customer or merchant communication, and route high-risk or policy-sensitive cases to operations teams.",
]

KEY_WORDS = ["payment", "dispute", "chargeback", "settlement", "resolution"]
STOP_WORDS = {
    "a", "an", "and", "are", "as", "be", "but", "by", "could", "for", "from",
    "have", "in", "is", "it", "of", "on", "or", "should", "that", "the", "their",
    "this", "to", "was", "we",
}


def tokenize(text: str) -> List[str]:
    """Lowercase, remove punctuation, tokenize, and remove general stop words."""
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [word for word in words if word not in STOP_WORDS]


def print_documents() -> None:
    print("\nDOCUMENTS")
    for number, document in enumerate(DOCUMENTS, start=1):
        print(f"{number}. {document}")


def similarity_analysis(model: Word2Vec) -> None:
    print("\nTOP THREE SIMILAR WORDS")
    rows = []

    for key_word in KEY_WORDS:
        if key_word not in model.wv:
            rows.append([key_word, "Not in vocabulary", "-", "-"])
            continue

        similar_words = model.wv.most_similar(
            key_word,
            topn=min(3, len(model.wv) - 1),
        )
        for rank, (word, score) in enumerate(similar_words, start=1):
            rows.append([key_word, word, f"{score:.4f}", str(rank)])

    result = pd.DataFrame(
        rows,
        columns=["Key Word", "Similar Word", "Similarity Score", "Rank"],
    )
    print(result.to_string(index=False))
    print("\nNote: 'chargeback' may be unavailable because the corpus contains 'chargebacks'.")


def cluster_analysis(model: Word2Vec) -> pd.DataFrame:
    words = sorted(model.wv.index_to_key)
    vectors = model.wv[words]
    cluster_count = min(N_CLUSTERS, len(words))

    kmeans = KMeans(
        n_clusters=cluster_count,
        random_state=RANDOM_SEED,
        n_init=10,
    )
    labels = kmeans.fit_predict(vectors)

    clusters = pd.DataFrame({"Word": words, "Cluster": labels})
    clusters = clusters.sort_values(["Cluster", "Word"]).reset_index(drop=True)

    print(f"\nWORD CLUSTERS ({N_CLUSTERS} CLUSTERS)")
    print(clusters.to_string(index=False))

    print("\nCLUSTER INTERPRETATIONS")
    for cluster_number in sorted(clusters["Cluster"].unique()):
        words_in_cluster = clusters.loc[
            clusters["Cluster"] == cluster_number, "Word"
        ].tolist()
        print(f"Cluster {cluster_number}: {', '.join(words_in_cluster)}")
        print("  Meaning: inferred from the words produced by K-Means; not predetermined.")

    return clusters


def plot_clusters(model: Word2Vec, clusters: pd.DataFrame) -> None:
    words = clusters["Word"].tolist()
    coordinates = PCA(n_components=2, random_state=RANDOM_SEED).fit_transform(model.wv[words])

    plt.figure(figsize=(14, 9))
    for cluster_number in sorted(clusters["Cluster"].unique()):
        indexes = [
            index for index, value in enumerate(clusters["Cluster"])
            if value == cluster_number
        ]
        plt.scatter(
            coordinates[indexes, 0],
            coordinates[indexes, 1],
            s=80,
            label=f"Cluster {cluster_number}",
        )

    for word, (x, y) in zip(words, coordinates):
        plt.annotate(word, (x, y), xytext=(5, 5), textcoords="offset points")

    plt.title("Word2Vec Word Clusters — Payment Operations Domain")
    plt.xlabel("PCA Component 1")
    plt.ylabel("PCA Component 2")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.show()


def main() -> None:
    print("WORD2VEC + K-MEANS + PCA: PAYMENT OPERATIONS")
    print_documents()

    tokenized_documents = [tokenize(document) for document in DOCUMENTS]
    print("\nPREPROCESSED DOCUMENTS")
    for number, tokens in enumerate(tokenized_documents, start=1):
        print(f"{number}. {' '.join(tokens)}")

    model = Word2Vec(
        sentences=tokenized_documents,
        vector_size=VECTOR_SIZE,
        window=WINDOW,
        min_count=1,
        workers=1,
        epochs=EPOCHS,
        seed=RANDOM_SEED,
    )

    print(f"\nVocabulary size: {len(model.wv)}")
    print("These embeddings are demonstration-level because the corpus has only five short documents.")

    similarity_analysis(model)
    clusters = cluster_analysis(model)
    plot_clusters(model, clusters)

    print("\nFINAL ANALYSIS")
    print("Word2Vec similarity is based on word contexts in this small corpus.")
    print("K-Means groups mathematical vectors; cluster meanings are human interpretations.")
    print("PCA provides an approximate two-dimensional visualization of those vectors.")
    print("Do not treat these similarity, clustering, or PCA results as production-quality NLP findings.")


if __name__ == "__main__":
    main()
