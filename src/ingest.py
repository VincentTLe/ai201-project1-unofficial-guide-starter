"""Step 1 of the pipeline: LOAD the raw .txt documents and CLEAN them.

Why this file exists (Milestone 3, job 1 + 2):
  - "load all your documents"  -> load_documents()
  - "clean each document, remove nav menus / ads / footers / boilerplate,
     keep the real review text, ratings, professor names" -> clean_text()

The files in documents/ were collected from Niche, Rate My Professors, and The
Knox Student. They still carry:
  - a provenance header at the very top (lines like "# Source: https://...")
  - a few stray website bits ("Write a review", "Skip to Content", footers)
  - fancy web punctuation (curly quotes, em dashes) that breaks on some terminals
clean_text() removes the first two and normalizes the third.

Run this file on its own to print ONE cleaned document and read it (that is the
"print one document and read it" verification step in Milestone 3):
    python src/ingest.py
"""

import re

from config import DOCS_DIR  # absolute path to the documents/ folder (see config.py)


# ---------------------------------------------------------------------------
# Rules describing what counts as "boilerplate" (junk to delete).
# I keep them as plain lists so they are easy to read and extend later.
# ---------------------------------------------------------------------------

# Lines that START with one of these are the provenance/metadata header I added
# when collecting each file (e.g. "# Source: https://...", "# Author: ...").
# They are notes about the document, not content, so we drop them. They are
# matched in lowercase, so "# Source:" and "# source:" both match.
_META_PREFIXES = (
    "# source", "# site", "# subreddit", "# title", "# headline", "# author",
    "# retrieved", "# note", "# category", "# overall", "# each entry", "# mix of",
)

# Lines that are EXACTLY one of these (after stripping + lowercasing) are pure
# website chrome left over from the original pages (nav bars, buttons, footers).
_JUNK_EXACT = {
    "share", "open comment sort options", "sort by: best", "write a review",
    "back to full profile", "people also ask about", "skip to content",
    "skip to main content", "open menu open navigation go to reddit home",
    "sign up log in", "best  top  new  controversial  old  q&a",
    "view story comments", "leave a comment", "more to discover",
}

# If any of these substrings appears ANYWHERE in a line, the whole line is junk
# (ads, cookie/footer text, reddit chrome). Use carefully so we don't nuke real text.
_JUNK_SUBSTR = (
    "reddit, inc.", "© 2026", "•promoted", "latest stories", "trending stories",
    "continue with phone", "continue with email", "[skip to", "like this story",
    "people also ask about section",
)

# Fancy web punctuation -> plain ASCII. The text is correct UTF-8 either way, but
# Windows terminals can't print "—" or curly quotes (they show as "�"), and plain
# ASCII keeps every chunk uniform. Left side = what to find, right side = replacement.
_NORMALIZE = {
    "—": "-", "–": "-",        # em dash / en dash -> hyphen
    "‘": "'", "’": "'",        # curly single quotes -> straight apostrophe
    "“": '"', "”": '"',        # curly double quotes -> straight quote
    "…": "...",                      # ellipsis character -> three dots
    " ": " ",                        # non-breaking space -> normal space
}


def _normalize(text: str) -> str:
    """Replace fancy punctuation with plain ASCII (see _NORMALIZE)."""
    for bad, good in _NORMALIZE.items():
        text = text.replace(bad, good)
    return text


def _is_junk(line: str) -> bool:
    """Return True if this single line is boilerplate we should delete."""
    low = line.strip().lower()          # compare in lowercase, ignore surrounding spaces
    if not low:
        return False                    # keep blank lines for now (we tidy them later)
    if low.startswith(_META_PREFIXES):  # str.startswith accepts a tuple = "any of these"
        return True
    if low in _JUNK_EXACT:              # exact-match junk line
        return True
    return any(sub in low for sub in _JUNK_SUBSTR)  # contains-a-junk-substring


def clean_text(raw: str) -> str:
    """Turn one raw document string into clean text ready for chunking."""
    # 1) keep only the lines that are NOT junk (this is the cleaning step)
    kept = [ln for ln in raw.splitlines() if not _is_junk(ln)]
    text = "\n".join(kept)
    # 2) normalize fancy punctuation to ASCII
    text = _normalize(text)
    # 3) collapse any run of 3+ newlines down to a single blank line, so paragraph
    #    splitting later is predictable
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def load_documents(docs_dir=DOCS_DIR):
    """Load every documents/*.txt file, clean it, and return a list of dicts.

    Returns: [{"source": "<filename>", "text": "<cleaned text>"}, ...]
    The "source" field is the filename, which we carry all the way to retrieval
    so every answer can cite which document it came from.
    """
    docs = []
    for path in sorted(docs_dir.glob("*.txt")):   # sorted() = stable, repeatable order
        raw = path.read_text(encoding="utf-8")     # read as UTF-8 so accents survive
        text = clean_text(raw)
        if text:                                   # skip a file that cleaned down to nothing
            docs.append({"source": path.name, "text": text})
    return docs


# This block only runs when you execute `python src/ingest.py` directly.
# It is the Milestone 3 "print one document and read it" check.
if __name__ == "__main__":
    docs = load_documents()
    print(f"Loaded {len(docs)} documents from {DOCS_DIR}\n")
    sample = docs[0]
    print(f"--- cleaned preview: {sample['source']} ---")
    print(sample["text"][:1200])   # first 1200 chars is enough to eyeball it
