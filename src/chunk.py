"""Step 2 of the pipeline: SPLIT each cleaned document into chunks.

Why this file exists (Milestone 3, job 3 + 4):
  - "implement your chunking strategy (size + overlap from planning.md)"
  - "print 5 representative chunks and inspect them"

The strategy (from planning.md): most of my units of text (one Niche review, one
RMP rating, one article paragraph) are short and already make sense on their own.
So instead of cutting blindly every N characters, I:
  1. break the text on paragraph boundaries,
  2. pack whole paragraphs together until I reach ~CHUNK_SIZE characters,
  3. only split a paragraph by sentences if it is bigger than CHUNK_SIZE on its own,
  4. carry ~CHUNK_OVERLAP characters from the end of one chunk into the next, so a
     fact that lands on a boundary is still recoverable.

Run this file on its own to inspect the result (count + 5 random chunks):
    python src/chunk.py
"""

import re

from config import CHUNK_OVERLAP, CHUNK_SIZE   # the numbers I chose in planning.md
from ingest import load_documents              # step 1 (load + clean) feeds step 2


# ---------------------------------------------------------------------------
# Small helpers. Each does ONE simple thing so the main function stays readable.
# ---------------------------------------------------------------------------

def _paragraphs(text):
    """Split text into paragraphs on blank lines.

    Regex r"\\n\\s*\\n" = a newline, optional whitespace, another newline = a blank
    line between two paragraphs. We strip each piece and drop empty ones.
    """
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def _sentences(paragraph):
    """Split one paragraph into sentences.

    Regex r"(?<=[.!?])\\s+" means: split at the spaces that come right AFTER a
    '.', '!' or '?'. The (?<=...) is a "lookbehind" — it checks what's before the
    space without deleting the punctuation, so "Hi. Bye." -> ["Hi.", "Bye."].
    """
    parts = re.split(r"(?<=[.!?])\s+", paragraph)
    return [s.strip() for s in parts if s.strip()]


def _hard_wrap(s, size):
    """Last-resort: cut a string into fixed `size` pieces.

    Only used if a single sentence is somehow longer than a whole chunk, so we
    never produce a chunk bigger than the model can handle. s[i:i+size] is a
    Python slice; range(0, len(s), size) steps i by `size` each time.
    """
    return [s[i:i + size] for i in range(0, len(s), size)]


def _units(text, chunk_size):
    """Break text into 'units' that are each <= chunk_size.

    A unit is normally a whole paragraph. If a paragraph is too long, we pack its
    sentences into groups <= chunk_size. This is the "respect content boundaries"
    part — we prefer to break at paragraph, then sentence, never mid-word.
    """
    units = []
    for para in _paragraphs(text):
        if len(para) <= chunk_size:
            units.append(para)                  # common case: paragraph fits, keep whole
            continue
        # paragraph too long -> walk its sentences and pack them greedily
        cur = ""
        for sent in _sentences(para):
            if len(sent) > chunk_size:          # a single monster sentence
                if cur:
                    units.append(cur)
                    cur = ""
                units.extend(_hard_wrap(sent, chunk_size))   # last resort
            elif cur and len(cur) + 1 + len(sent) > chunk_size:
                # adding this sentence would overflow -> close current unit, start new
                units.append(cur)
                cur = sent
            else:
                cur = f"{cur} {sent}".strip()   # room left -> append sentence
        if cur:
            units.append(cur)                   # don't forget the last partial unit
    return units


def _overlap_tail(text, overlap):
    """Return the last ~overlap characters of text, trimmed to a word boundary.

    This is the bit that gets copied into the START of the next chunk so the two
    chunks share some context. We trim to the next space so we don't start in the
    middle of a word.
    """
    if overlap <= 0 or len(text) <= overlap:
        return text if overlap > 0 else ""
    tail = text[-overlap:]                       # last `overlap` characters
    if " " in tail:
        tail = tail[tail.index(" ") + 1:]        # drop the leading partial word
    return tail


def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Split ONE document's text into a list of chunk strings.

    Greedy packing: keep adding units to the current chunk until the next unit
    would push it past chunk_size; then close the chunk and start a new one that
    begins with the overlap tail of the chunk we just closed.
    """
    chunks, cur = [], ""
    for unit in _units(text, chunk_size):
        if cur and len(cur) + 2 + len(unit) > chunk_size:   # +2 = the "\n\n" join
            chunks.append(cur)                              # close the full chunk
            tail = _overlap_tail(cur, overlap)              # carry context forward
            cur = f"{tail}\n\n{unit}".strip() if tail else unit
        else:
            cur = f"{cur}\n\n{unit}".strip() if cur else unit
    if cur:
        chunks.append(cur)
    # the `if c.strip()` filter = the "drop empty chunks" rule from Milestone 3
    return [c.strip() for c in chunks if c.strip()]


def chunk_documents(docs=None, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Chunk EVERY document and attach metadata.

    Returns: [{"source": filename, "chunk_index": i, "text": chunk}, ...]
    chunk_index is the position of the chunk within its document. Together with
    source it lets us point at exactly which piece of which file an answer used.
    """
    docs = docs if docs is not None else load_documents()   # default: load + clean first
    out = []
    for doc in docs:
        for i, piece in enumerate(chunk_text(doc["text"], chunk_size, overlap)):
            out.append({"source": doc["source"], "chunk_index": i, "text": piece})
    return out


# Milestone 3 verification: print the count + 5 random chunks and READ them.
if __name__ == "__main__":
    import random

    chunks = chunk_documents()
    sizes = [len(c["text"]) for c in chunks]
    print(f"Total chunks: {len(chunks)}")
    print(f"Chunk size (chars): min {min(sizes)} | median {sorted(sizes)[len(sizes)//2]} "
          f"| max {max(sizes)}\n")

    random.seed(0)   # fixed seed = same 5 chunks every run, so the check is repeatable
    print("=== 5 random chunks ===")
    for c in random.sample(chunks, 5):
        print(f"\n[{c['source']} #{c['chunk_index']}] ({len(c['text'])} chars)")
        print(c["text"])
        print("-" * 70)
