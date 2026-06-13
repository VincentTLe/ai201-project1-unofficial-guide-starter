"""Step 7: run the 5 evaluation questions end-to-end and print a report.

For each question it prints: the question, the expected answer, the chunks that
were retrieved (source + distance), the system's actual answer, and the sources.
You (the human) read this and fill in the accuracy judgment in the README.

Run (needs GROQ_API_KEY in .env):
    python src/evaluate.py
"""

from generate import ask
from retrieve import retrieve

# The 5 test questions from planning.md, each with its ground-truth answer.
EVAL = [
    {
        "q": "Is the housing assignment actually random, and how hard is it to switch if you don't get along with your roommate?",
        "expected": "Not fully random: you can pick your own roommate/suite (highest priority number picks). If you don't choose, Campus Life randomly assigns one ('buzzfeed quiz'), and students say it's very hard to change rooms.",
    },
    {
        "q": "Is the caf food actually any good, and what do students complain about most?",
        "expected": "Mixed. Some say decent/surprisingly good; others say bland. Biggest complaints: repetitive menu and lack of real cultural/halal options (renamed dishes).",
    },
    {
        "q": "What do international students say about how Knox actually treats them?",
        "expected": "Recurring frustration: renamed/mislabeled cultural food, 'HORRIBLE' international financial aid office, and paid summer housing ($308/mo) that hits students who can't fly home.",
    },
    {
        "q": "Which professors do students actually like, and is anyone hit-or-miss?",
        "expected": "Joan Huguet is loved (caring, door always open). Peter Schwartzman and Mark Shroyer are mixed (passionate but 'lectures about himself' / 'unclear, teach yourself').",
    },
    {
        "q": "Which CS professor at Knox gives the most useful feedback?",
        "expected": "FAILURE CASE: corpus has no CS-professor reviews, so the system should say it doesn't have enough information.",
    },
]


def main():
    for i, item in enumerate(EVAL, 1):
        print("=" * 95)
        print(f"Q{i}: {item['q']}")
        print(f"\nEXPECTED: {item['expected']}")

        print("\nRETRIEVED CHUNKS (source #idx | distance):")
        for h in retrieve(item["q"]):
            preview = " ".join(h["text"].split())[:110]
            print(f"  {h['distance']:.3f}  {h['source']} #{h['chunk_index']}: {preview}...")

        result = ask(item["q"])
        print(f"\nSYSTEM ANSWER: {result['answer']}")
        print(f"SOURCES: {result['sources'] or '(none)'}")
        print("\nACCURACY (fill in): accurate / partially accurate / inaccurate\n")


if __name__ == "__main__":
    main()
