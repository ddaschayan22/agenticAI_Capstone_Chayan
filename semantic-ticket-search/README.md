# Semantic Search Over Client Support Tickets

A modular ChromaDB-backed semantic search system using 20 synthetic historical support tickets for testing. Each ticket contains an issue and its eventual resolution.

## Architecture

```text
TXT tickets -> loader/parser -> chunker -> embeddings -> ChromaDB -> query embedding -> top semantic matches
```

The same fixed-size local hashing embedding model is used for ticket chunks and search queries. This avoids the PyTorch/Sentence Transformers dependency on Windows. ChromaDB uses cosine distance. The reported similarity is `1 - distance`; both values are returned. This is a lightweight lexical-vector baseline rather than a transformer semantic model.

## Setup

Python 3.10+ is recommended.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

No transformer or PyTorch model download is required.

## Commands

Index all tickets:

```powershell
python run.py index
```

Index any number of tickets in the future:

```powershell
python run.py index --limit 20
python run.py index --limit 100
```

Omit `--limit` to index all available `.txt` ticket files.

Search semantically:

```powershell
python run.py search "app keeps logging me out"
```

Evaluate the paraphrased query:

```powershell
python run.py evaluate
```

## Ticket format

Files in `data/tickets/` are UTF-8 `.txt` files. Optional metadata is supported:

```text
Ticket ID: TICKET-042
Status: Resolved

Customer:
My session expires randomly every few minutes.

Resolution:
Updated the authentication session configuration.
```

If metadata is absent, the ticket ID is derived from the filename and status is `unknown`. Invalid or empty files are skipped with a log message.

## Search behavior

Results include ticket ID, chunk index, text, resolution status, source filename, ChromaDB distance, and a derived similarity score. Ticket-level diversification keeps the strongest result per ticket so one ticket does not consume all top results.

## Evaluation

The bundled sample data contains 20 tickets, including `TICKET-042`, whose issue describes a session expiring randomly. The paraphrased query is `app keeps logging me out`; success requires that `TICKET-042` appears within the top three results.

## Limitations

The bundled data is synthetic and intended for demonstration. Semantic retrieval quality depends on the embedding model and ticket content. Scanned documents are not supported because this project loads plain text files only.
