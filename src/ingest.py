"""Step 1: load the raw .txt documents and clean out leftover web boilerplate.

The files in documents/ were collected from Niche, Rate My Professors, and The
Knox Student. They still carry a provenance header (lines starting with "# Source:"
etc.) and a few stray site bits ("Write a review", "Skip to Content", footers).
We strip those so chunks contain real student text, not navigation.

Run directly to eyeball one cleaned document:
    python src/ingest.py
"""

import re

from config import DOCS_DIR

# Metadata/provenance comment lines at the top of each file (lowercased prefixes).
_META_PREFIXES = (
    "# source", "# site", "# subreddit", "# title", "# headline", "# author",
    "# retrieved", "# note", "# category", "# overall", "# each entry", "# mix of",
)

# Whole lines (lowercased, stripped) that are pure site chrome.
_JUNK_EXACT = {
    "share", "open comment sort options", "sort by: best", "write a review",
    "back to full profile", "people also ask about", "skip to content",
    "skip to main content", "open menu open navigation go to reddit home",
    "sign up log in", "best  top  new  controversial  old  q&a",
    "view story comments", "leave a comment", "more to discover",
}

# Substrings that mark a line as junk (ads, footers, reddit chrome).
_JUNK_SUBSTR = (
    "reddit, inc.", "© 2026", "•promoted", "latest stories", "trending stories",
    "continue with phone", "continue with email", "[skip to", "like this story",
    "people also ask about section",
)


# Fancy web punctuation -> plain ASCII (avoids console/encoding surprises downstream).
_NORMALIZE = {
    "—": "-", "–": "-",        # em / en dash
    "‘": "'", "’": "'",        # curly single quotes
    "“": '"', "”": '"',        # curly double quotes
    "…": "...",                      # ellipsis
    " ": " ",                        # non-breaking space
}


def _normalize(text: str) -> str:
    for bad, good in _NORMALIZE.items():
        text = text.replace(bad, good)
    return text


def _is_junk(line: str) -> bool:
    low = line.strip().lower()
    if not low:
        return False  # keep blank lines for now; we collapse them later
    if low.startswith(_META_PREFIXES):
        return True
    if low in _JUNK_EXACT:
        return True
    return any(sub in low for sub in _JUNK_SUBSTR)


def clean_text(raw: str) -> str:
    """Drop boilerplate lines and collapse extra blank lines."""
    kept = [ln for ln in raw.splitlines() if not _is_junk(ln)]
    text = "\n".join(kept)
    text = _normalize(text)
    text = re.sub(r"\n{3,}", "\n\n", text)   # 3+ blank lines -> one blank line
    return text.strip()


def load_documents(docs_dir=DOCS_DIR):
    """Return [{'source': filename, 'text': cleaned text}, ...], sorted by name."""
    docs = []
    for path in sorted(docs_dir.glob("*.txt")):
        raw = path.read_text(encoding="utf-8")
        text = clean_text(raw)
        if text:
            docs.append({"source": path.name, "text": text})
    return docs


if __name__ == "__main__":
    docs = load_documents()
    print(f"Loaded {len(docs)} documents from {DOCS_DIR}\n")
    sample = docs[0]
    print(f"--- cleaned preview: {sample['source']} ---")
    print(sample["text"][:1200])
