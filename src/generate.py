"""Step 5: turn retrieved chunks into a grounded, cited answer with Groq.

The whole point here is GROUNDING: the model must answer only from the chunks we
retrieved, and refuse when they don't contain the answer. Two safeguards:
  1. A strict system prompt ("use ONLY the context, else say you don't know").
  2. Source filenames are attached by OUR code from the retrieval metadata, not
     left to the model to invent. On a refusal we attach no sources.

Run directly to test grounding on a few questions (needs GROQ_API_KEY in .env):
    python src/generate.py
"""

import os

from dotenv import load_dotenv
from groq import Groq

from config import BASE_DIR, GROQ_MODEL, TOP_K
from retrieve import retrieve

load_dotenv(BASE_DIR / ".env")   # read GROQ_API_KEY from the .env file at repo root

# The exact sentence the model must use when the context is insufficient.
REFUSAL = "I don't have enough information on that."

SYSTEM_PROMPT = (
    "You are The Unofficial Knox Guide, a Q&A assistant about student life at Knox "
    "College (professors, dining, housing, campus life). Answer the question using "
    "ONLY the numbered context excerpts provided. Rules:\n"
    "1. Use only facts found in the context. Never add outside knowledge or guesses.\n"
    f'2. If the context does not contain enough information, reply with EXACTLY: "{REFUSAL}" '
    "and nothing else.\n"
    "3. When you do answer, cite the source filename(s) in parentheses, e.g. "
    "(tks_housing_101.txt).\n"
    "4. Keep it concise and grounded in what students actually said."
)

_client = None


def _groq():
    """Create the Groq client once (lazy, so importing this file never crashes)."""
    global _client
    if _client is None:
        key = os.environ.get("GROQ_API_KEY")
        if not key or key == "your_key_here":
            raise RuntimeError(
                "GROQ_API_KEY is missing. Copy .env.example to .env and paste your key "
                "from https://console.groq.com"
            )
        _client = Groq(api_key=key)
    return _client


def _format_context(hits):
    """Number the retrieved chunks and label each with its source file."""
    return "\n\n".join(
        f"[{i + 1}] (source: {h['source']}) {h['text']}" for i, h in enumerate(hits)
    )


def ask(query, k=TOP_K):
    """Return {'answer': str, 'sources': [filenames]} for a user question."""
    hits = retrieve(query, k)
    context = _format_context(hits)

    response = _groq().chat.completions.create(
        model=GROQ_MODEL,
        temperature=0,                      # deterministic, less room to wander off-context
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Context excerpts:\n{context}\n\nQuestion: {query}"},
        ],
    )
    answer = response.choices[0].message.content.strip()

    # Attach sources OURSELVES from the retrieved chunks (guaranteed, not model-invented).
    # On a refusal, the answer wasn't drawn from any document, so we cite nothing.
    if REFUSAL.lower() in answer.lower():
        sources = []
    else:
        sources = list(dict.fromkeys(h["source"] for h in hits))  # unique, keep order

    return {"answer": answer, "sources": sources}


if __name__ == "__main__":
    tests = [
        "Is the housing assignment actually random, and how hard is it to switch roommates?",
        "Is the caf food actually any good, and what do students complain about?",
        "Which CS professor at Knox gives the most useful feedback?",   # should refuse
    ]
    for q in tests:
        print("=" * 90)
        print("Q:", q)
        result = ask(q)
        print("\nANSWER:", result["answer"])
        print("SOURCES:", result["sources"] or "(none)")
        print()
