"""Step 3: embed every chunk and store it in a local ChromaDB collection.

Embeddings use all-MiniLM-L6-v2 (local, free). We store each chunk's text plus
its source filename and position so retrieval can cite where an answer came from.
Distances use cosine space, so smaller = more similar (0 = identical).

Run once (re-run any time documents change):
    python src/build_index.py
"""

import chromadb
from sentence_transformers import SentenceTransformer

from chunk import chunk_documents
from config import CHROMA_DIR, COLLECTION_NAME, EMBED_MODEL


def build():
    chunks = chunk_documents()
    texts = [c["text"] for c in chunks]
    print(f"Embedding {len(chunks)} chunks with {EMBED_MODEL} ...")

    model = SentenceTransformer(EMBED_MODEL)
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=True).tolist()

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    try:
        client.delete_collection(COLLECTION_NAME)   # start clean so we never double-add
    except Exception:
        pass
    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
    collection.add(
        ids=[f"{c['source']}::{c['chunk_index']}" for c in chunks],
        documents=texts,
        embeddings=embeddings,
        metadatas=[{"source": c["source"], "chunk_index": c["chunk_index"]} for c in chunks],
    )
    print(f"Stored {collection.count()} chunks in ChromaDB at {CHROMA_DIR}")


if __name__ == "__main__":
    build()
