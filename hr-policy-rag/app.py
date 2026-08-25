"""HR policy Q&A with PDF/TXT ingestion, ChromaDB retrieval, and OpenRouter."""

from __future__ import annotations

import io
import os
from pathlib import Path
from typing import Any

import chromadb
import requests
import streamlit as st
from dotenv import load_dotenv
from pypdf import PdfReader
from sklearn.feature_extraction.text import HashingVectorizer


ROOT = Path(__file__).resolve().parent
POLICY_DIR = ROOT / "policy_docs"
CHROMA_DIR = ROOT / "chroma_db"
COLLECTION_NAME = "hr_policy_documents_hashing"
CHUNK_SIZE = 700
CHUNK_OVERLAP = 100
TOP_K = 5

DEFAULT_POLICIES = {
    "leave_policy.txt": "Annual Leave Policy\nEmployees receive annual leave according to their employment terms and applicable local requirements. Leave requests should be submitted through the approved HR system before the planned absence. Managers review requests based on staffing needs and policy eligibility. Employees should check their current balance in the HR system before submitting a request.\n\nSick Leave Policy\nEmployees who cannot work because of illness should notify their manager as soon as reasonably possible and follow the absence-reporting process. Medical documentation may be requested where permitted by applicable law and company policy. Questions about eligibility should be directed to HR.",
    "remote_work_policy.txt": "Remote Work Policy\nEligible employees may work remotely when their role, location, security requirements, and manager approval allow it. Remote work arrangements must comply with working-hour, confidentiality, information-security, and equipment requirements. Employees must remain reachable during agreed working hours and report changes to their arrangement through the approved HR process. Not every role or location is eligible for remote work.",
    "expenses_policy.txt": "Business Expenses Policy\nEmployees may request reimbursement for reasonable, necessary, and business-related expenses. Claims should include receipts and be submitted through the approved expense process within the applicable submission period. Expenses require the approvals defined by the employee's department and role. Personal expenses and unsupported claims are not reimbursable. Employees should contact Finance or HR when they need clarification.",
}


class LocalEmbeddingFunction:
    """Deterministic local embeddings without PyTorch or ONNX dependencies."""

    def __init__(self) -> None:
        self.vectorizer = HashingVectorizer(
            n_features=256,
            alternate_sign=False,
            norm="l2",
            lowercase=True,
            token_pattern=r"(?u)\b\w+\b",
        )

    def __call__(self, input: list[str]) -> list[list[float]]:
        return self.vectorizer.transform(input).toarray().astype(float).tolist()

    def embed_query(self, input: list[str]) -> list[list[float]]:
        """Embed query text using the same representation as policy chunks."""
        return self(input)

    @staticmethod
    def name() -> str:
        """Return the stable ChromaDB embedding-function name."""
        return "local_hashing_256"

    def default_space(self) -> str:
        """Declare the distance space used by this normalized embedder."""
        return "l2"


@st.cache_resource
def get_embedding_function() -> LocalEmbeddingFunction:
    return LocalEmbeddingFunction()


def ensure_default_documents() -> None:
    POLICY_DIR.mkdir(parents=True, exist_ok=True)
    if not any(POLICY_DIR.glob("*.txt")) and not any(POLICY_DIR.glob("*.pdf")):
        for filename, content in DEFAULT_POLICIES.items():
            (POLICY_DIR / filename).write_text(content, encoding="utf-8")


def extract_file_text(file: Any) -> str:
    file_bytes = file.getvalue()
    if file.name.lower().endswith(".pdf"):
        reader = PdfReader(io.BytesIO(file_bytes))
        return "\n".join(page.extract_text() or "" for page in reader.pages).strip()
    return file_bytes.decode("utf-8", errors="replace").strip()


def extract_path_text(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages).strip()
    return path.read_text(encoding="utf-8", errors="replace").strip()


def chunk_text(text: str, source: str) -> list[dict[str, Any]]:
    words = text.split()
    step = max(1, CHUNK_SIZE - CHUNK_OVERLAP)
    chunks = []
    for start in range(0, len(words), step):
        chunk = " ".join(words[start:start + CHUNK_SIZE]).strip()
        if chunk:
            chunks.append({"text": chunk, "source": source, "chunk": len(chunks) + 1})
        if start + CHUNK_SIZE >= len(words):
            break
    return chunks


def load_documents(uploaded_files: list[Any]) -> list[dict[str, Any]]:
    documents = []
    uploaded_names = set()
    for file in uploaded_files or []:
        uploaded_names.add(file.name)
        text = extract_file_text(file)
        if text:
            documents.extend(chunk_text(text, file.name))
    for path in list(POLICY_DIR.glob("*.txt")) + list(POLICY_DIR.glob("*.pdf")):
        if path.name not in uploaded_names:
            text = extract_path_text(path)
            if text:
                documents.extend(chunk_text(text, path.name))
    return documents


def build_collection(documents: list[dict[str, Any]]) -> chromadb.Collection:
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(COLLECTION_NAME, embedding_function=get_embedding_function())
    collection.add(
        ids=[f"{item['source']}-{item['chunk']}" for item in documents],
        documents=[item["text"] for item in documents],
        metadatas=[{"source": item["source"], "chunk": item["chunk"]} for item in documents],
    )
    return collection


def get_collection() -> chromadb.Collection:
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_or_create_collection(COLLECTION_NAME, embedding_function=get_embedding_function())


def retrieve(collection: chromadb.Collection, question: str) -> list[dict[str, Any]]:
    if collection.count() == 0:
        return []
    result = collection.query(query_texts=[question], n_results=min(TOP_K, collection.count()))
    return [
        {"text": text, "metadata": metadata, "distance": distance}
        for text, metadata, distance in zip(result["documents"][0], result["metadatas"][0], result["distances"][0])
    ]


def answer_with_openrouter(question: str, chunks: list[dict[str, Any]]) -> str:
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    model = os.getenv("OPENROUTER_MODEL", "").strip()
    if not api_key or not model or api_key.startswith("your_") or model == "your_model_name":
        return "OpenRouter is not configured. Add OPENROUTER_API_KEY and OPENROUTER_MODEL to .env."
    context = "\n\n".join(f"[Source: {item['metadata']['source']}]\n{item['text']}" for item in chunks)
    payload = {
        "model": model,
        "temperature": 0.0,
        "messages": [
            {"role": "system", "content": "Answer only from the retrieved HR policy context. If the context does not answer the question, say the policy documents do not provide enough information. Do not guess or invent policy, eligibility, deadlines, approvals, exceptions, or legal advice. Cite source file names."},
            {"role": "user", "content": f"Retrieved context:\n{context}\n\nQuestion:\n{question}"},
        ],
    }
    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except (requests.RequestException, ValueError, KeyError, IndexError, TypeError) as exc:
        return f"Unable to generate an answer from OpenRouter: {exc}"


def main() -> None:
    load_dotenv(ROOT / ".env")
    ensure_default_documents()
    st.set_page_config(page_title="HR Policy Assistant", page_icon="📘", layout="wide")
    st.title("📘 HR Policy Assistant")
    st.caption("Upload PDF or TXT policy documents and ask questions answered only from indexed policy content.")
    uploaded_files = st.file_uploader("Upload HR policy PDF or TXT files", type=["pdf", "txt"], accept_multiple_files=True)
    if st.button("Ingest / Rebuild Policy Index", type="primary"):
        try:
            documents = load_documents(uploaded_files)
            if not documents:
                st.error("No policy text was found. Use a text-based PDF or TXT file.")
            else:
                build_collection(documents)
                st.session_state["collection_ready"] = True
                st.success(f"Indexed {len(documents)} policy chunks into ChromaDB.")
        except Exception as exc:
            st.error(f"Could not ingest policy documents: {exc}")
    try:
        collection = get_collection()
    except Exception as exc:
        collection = None
        st.warning(f"Policy index is not available yet: {exc}")
    question = st.text_input("Ask a question about the policy documents")
    if st.button("Ask"):
        if not question.strip():
            st.warning("Enter a question first.")
        elif collection is None or collection.count() == 0:
            st.error("Ingest policy documents before asking a question.")
        else:
            chunks = retrieve(collection, question)
            st.subheader("Answer")
            st.write(answer_with_openrouter(question, chunks))
            with st.expander("Retrieved policy chunks"):
                for item in chunks:
                    st.markdown(f"**{item['metadata']['source']} — chunk {item['metadata']['chunk']}**")
                    st.write(item["text"])


if __name__ == "__main__":
    main()
