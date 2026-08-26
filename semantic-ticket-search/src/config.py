"""Central configuration for semantic ticket search."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TICKETS_DIR = PROJECT_ROOT / "data" / "tickets"
CHROMA_DB_DIR = PROJECT_ROOT / "chroma_db"
COLLECTION_NAME = "support_tickets"
EMBEDDING_MODEL = "local-hashing-512"
CHUNK_SIZE = 700
CHUNK_OVERLAP = 100
DEFAULT_TOP_K = 4
EVALUATION_TOP_K = 3
RANDOM_SEED = 42
