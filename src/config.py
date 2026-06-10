"""Central config for The Unofficial Knox Guide.

Keeping the knobs (chunk size, top-k, model names, paths) in one place so the
ingestion, embedding, retrieval, and generation steps all agree.
"""

from pathlib import Path

# repo root = the folder that contains documents/ , src/ , planning.md ...
BASE_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = BASE_DIR / "documents"
CHROMA_DIR = BASE_DIR / "chroma_db"          # where the vector store is persisted
COLLECTION_NAME = "knox_guide"

# --- chunking (see planning.md "Chunking Strategy") ---
CHUNK_SIZE = 600        # characters; ~150 tokens, under MiniLM's 256 limit
CHUNK_OVERLAP = 100     # characters carried between adjacent chunks

# --- retrieval / generation ---
EMBED_MODEL = "all-MiniLM-L6-v2"
TOP_K = 5
GROQ_MODEL = "llama-3.3-70b-versatile"
