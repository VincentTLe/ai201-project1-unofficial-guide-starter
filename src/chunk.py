"""Step 2: split cleaned documents into ~600-char, paragraph-aware chunks.

Strategy (see planning.md): most reviews/quotes are short and self-contained, so
we pack whole paragraphs together up to CHUNK_SIZE instead of cutting blindly.
A paragraph longer than CHUNK_SIZE is split on sentence boundaries; a single
huge sentence is hard-wrapped as a last resort. Adjacent chunks share ~CHUNK_OVERLAP
characters so a fact split across a boundary stays recoverable.

Run directly to inspect the output (count + 5 random chunks):
    python src/chunk.py
"""

import re

from config import CHUNK_OVERLAP, CHUNK_SIZE
from ingest import load_documents


def _paragraphs(text):
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def _sentences(paragraph):
    parts = re.split(r"(?<=[.!?])\s+", paragraph)
    return [s.strip() for s in parts if s.strip()]


def _hard_wrap(s, size):
    return [s[i:i + size] for i in range(0, len(s), size)]


def _units(text, chunk_size):
    """Break text into pieces each <= chunk_size, preferring paragraph then sentence breaks."""
    units = []
    for para in _paragraphs(text):
        if len(para) <= chunk_size:
            units.append(para)
            continue
        cur = ""
        for sent in _sentences(para):
            if len(sent) > chunk_size:                         # one giant sentence
                if cur:
                    units.append(cur)
                    cur = ""
                units.extend(_hard_wrap(sent, chunk_size))
            elif cur and len(cur) + 1 + len(sent) > chunk_size:
                units.append(cur)
                cur = sent
            else:
                cur = f"{cur} {sent}".strip()
        if cur:
            units.append(cur)
    return units


def _overlap_tail(text, overlap):
    """Last ~overlap characters of text, trimmed to start at a word boundary."""
    if overlap <= 0 or len(text) <= overlap:
        return text if overlap > 0 else ""
    tail = text[-overlap:]
    if " " in tail:
        tail = tail[tail.index(" ") + 1:]
    return tail


def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Split one document's text into a list of chunk strings."""
    chunks, cur = [], ""
    for unit in _units(text, chunk_size):
        if cur and len(cur) + 2 + len(unit) > chunk_size:
            chunks.append(cur)
            tail = _overlap_tail(cur, overlap)
            cur = f"{tail}\n\n{unit}".strip() if tail else unit
        else:
            cur = f"{cur}\n\n{unit}".strip() if cur else unit
    if cur:
        chunks.append(cur)
    return [c.strip() for c in chunks if c.strip()]


def chunk_documents(docs=None, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Return [{'source', 'chunk_index', 'text'}, ...] across all documents."""
    docs = docs if docs is not None else load_documents()
    out = []
    for doc in docs:
        for i, piece in enumerate(chunk_text(doc["text"], chunk_size, overlap)):
            out.append({"source": doc["source"], "chunk_index": i, "text": piece})
    return out


if __name__ == "__main__":
    import random

    chunks = chunk_documents()
    sizes = [len(c["text"]) for c in chunks]
    print(f"Total chunks: {len(chunks)}")
    print(f"Chunk size (chars): min {min(sizes)} | median {sorted(sizes)[len(sizes)//2]} "
          f"| max {max(sizes)}\n")

    random.seed(0)
    print("=== 5 random chunks ===")
    for c in random.sample(chunks, 5):
        print(f"\n[{c['source']} #{c['chunk_index']}] ({len(c['text'])} chars)")
        print(c["text"])
        print("-" * 70)
