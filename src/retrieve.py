"""Step 4: given a question, return the top-k most similar chunks.

The model and collection are loaded once and cached, so importing retrieve() in
the app or generation step is cheap after the first call.

Run directly to eyeball retrieval on a few eval questions:
    python src/retrieve.py
"""

import chromadb
from sentence_transformers import SentenceTransformer

from config import CHROMA_DIR, COLLECTION_NAME, EMBED_MODEL, TOP_K

_model = None
_collection = None


def _load():
    global _model, _collection
    if _model is None:
        _model = SentenceTransformer(EMBED_MODEL)
    if _collection is None:
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        _collection = client.get_collection(COLLECTION_NAME)
    return _model, _collection


def retrieve(query, k=TOP_K):
    """Return [{'text', 'source', 'chunk_index', 'distance'}, ...] sorted by similarity."""
    model, collection = _load()
    query_emb = model.encode([query], normalize_embeddings=True).tolist()
    res = collection.query(
        query_embeddings=query_emb,
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )
    hits = []
    for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
        hits.append({
            "text": doc,
            "source": meta["source"],
            "chunk_index": meta["chunk_index"],
            "distance": dist,
        })
    return hits


if __name__ == "__main__":
    tests = [
        "Is the housing assignment actually random, and how hard is it to switch roommates?",
        "Is the caf food actually any good, and what do students complain about?",
        "Which professors do students actually like?",
        "Which CS professor at Knox gives the most useful feedback?",   # intended failure case
    ]
    for q in tests:
        print("=" * 90)
        print("Q:", q)
        for r in retrieve(q):
            preview = " ".join(r["text"].split())[:150]
            print(f"  [{r['distance']:.3f}] {r['source']} #{r['chunk_index']}: {preview}...")
