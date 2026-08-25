# HR Policy RAG Assistant

A Streamlit application that indexes HR policy text files in ChromaDB and answers user questions using only retrieved policy context through an OpenRouter Chat Completions API model.

## Features

- Upload one or more `.pdf` or `.txt` HR policy documents in the UI.
- Includes a small default policy set for demonstration.
- Chunks policy text and stores embeddings in a persistent ChromaDB collection.
- Retrieves the most relevant semantic chunks for each question.
- Uses OpenRouter with a strict grounded-answer system prompt.
- Says the policy documents do not provide enough information instead of guessing.
- Displays retrieved chunks for transparency.

## Setup

Use Python 3.10 or newer:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and configure:

```text
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=your_model_name
```

## Run

From this project directory:

```powershell
streamlit run app.py
```

The app uses a deterministic local hashing embedder and does not load PyTorch or ONNX. Internet access is required for OpenRouter answers.

## Usage

1. Open the Streamlit URL shown in the terminal.
2. Upload `.pdf` or `.txt` HR policy files, or use the included default policies.
3. Click **Ingest / Rebuild Policy Index**.
4. Enter a question about the indexed policies.
5. Click **Ask**.
6. Review the answer and retrieved policy chunks.

## Grounding behavior

The model receives only the retrieved chunks and the question. It is instructed not to invent policy details, eligibility, deadlines, approvals, exceptions, or legal advice. If the retrieved context does not answer the question, the application requires an explicit uncertainty response.

This is a reference implementation. For production use, add access control, document-level permissions, PII protection, file validation, audit retention, model monitoring, and approved HR/legal review.
