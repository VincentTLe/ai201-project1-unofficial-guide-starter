# The Unofficial Knox Guide — Project 1

A small RAG system that answers plain-language questions about student life at Knox College
(Galesburg, IL) using only real student-generated writing — Niche reviews, Rate My
Professors, and The Knox Student newspaper — and cites where each answer came from.

> Note to self: the technical sections are filled from real runs. Re-read the **Evaluation**,
> **Failure Case**, **Spec Reflection**, and **AI Usage** sections and put them in my own
> words before submitting.

## How to run
```powershell
# one-time: install deps into the project venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# build the vector store, then launch the app
.\.venv\Scripts\python.exe src\build_index.py     # embeds 123 chunks into ChromaDB
.\.venv\Scripts\python.exe src\app.py             # open http://localhost:7860

# or inspect each stage on its own
.\.venv\Scripts\python.exe src\chunk.py           # chunk count + 5 random chunks
.\.venv\Scripts\python.exe src\retrieve.py        # retrieval test
.\.venv\Scripts\python.exe src\evaluate.py        # full 5-question report
```
A `GROQ_API_KEY` (free, https://console.groq.com) must be in `.env` for generation.

---

## Domain

I picked student life at Knox College — the stuff you only figure out once you're actually
here: which dorms are worth fighting for, why the meal plan is mandatory, whether the
"cultural food" in the caf is the real thing, how the housing lottery decides who gets what.

It's valuable because none of it is on the official site. Knox's pages advertise "diverse
dining" and "vibrant residence life," but they won't tell you the caf renamed the same dish
every day of Ramadan, that summer housing now costs $308/month, or that older dorms have
fire alarms that go off for no reason. That knowledge is scattered across student reviews and
the campus newspaper. This system pulls it into one place you can ask a question and get a
cited answer.

---

## Document Sources

10 documents, all student-generated / unofficial (I deliberately left out the college's own
pages). Knox has no active subreddit, so the realistic sources are Niche, Rate My Professors,
and The Knox Student. Collected 2026-06-10.

| # | Source | Type | File |
|---|--------|------|------|
| 1 | Niche — Knox reviews page | Student reviews | `documents/niche_knox_student_reviews.txt` |
| 2 | Niche — Campus Life page | Reviews + polls | `documents/niche_knox_campus_life.txt` |
| 3 | Niche — Students/Academics | Reviews + facts | `documents/niche_knox_students_academics.txt` |
| 4 | Rate My Professors — Knox | Professor reviews | `documents/rmp_knox_professors.txt` |
| 5 | The Knox Student — "Housing 101" | Student journalism | `documents/tks_housing_101.txt` |
| 6 | The Knox Student — "Why is the meal plan mandatory?" | Student journalism | `documents/tks_meal_plan_mandatory.txt` |
| 7 | The Knox Student — "Lack of Cultural Food on Campus" | Student column | `documents/tks_cultural_food.txt` |
| 8 | The Knox Student — "Freedom of movement is a privilege" | Student journalism | `documents/tks_summer_housing_policy.txt` |
| 9 | The Knox Student — "Fifth-Year for Free housing stipulations" | Student journalism | `documents/tks_fifthyear_offcampus_housing.txt` |
| 10 | The Knox Student — "New school year, new freshman dorms" | Student journalism | `documents/tks_freshman_dorm_renovations.txt` |

---

## Chunking Strategy

**Chunk size:** ~600 characters. **Overlap:** ~100 characters. **Splitter:** paragraph-aware
(break on `\n\n`, then sentences, never mid-word). **Final chunk count: 123.**

I didn't guess these numbers — I measured my corpus first. The natural "units" (one Niche
review, one RMP rating, one article paragraph) have a median length of ~275 characters;
87% are under 500 and 95% under 700. So most reviews are short and self-contained. A blind
"split every 500 chars" would either glue two unrelated reviews together (noise) or cut one
review in half (lost context). A ~600-char target that respects paragraph boundaries keeps
~95% of reviews/quotes whole and only splits the few long article paragraphs. Overlap of
~100 chars (a sentence or two) matters for the long Knox Student articles, where a fact and
its number can land in adjacent paragraphs; for the short reviews it's harmless. 600 chars
is ~150 tokens, comfortably under MiniLM's 256-token limit, so nothing is silently truncated.

**Preprocessing before chunking:** strip provenance headers and leftover site chrome
(nav, "Latest Stories", ads, footers) and normalize fancy punctuation to ASCII; keep each
review's rating/date attached to its text. (On my corpus this removed only ~48 lines total,
because I had already hand-cleaned the text while collecting it — its real value is stripping
the source headers and acting as a safety net for messier documents added later.)

### Sample chunks (5, with source)

**1 — `tks_housing_101.txt #0`**
> Housing selection is right around the corner and is often a nightmare for students. This
> lovely lottery-based system makes choosing a spot to live on par with a 20 page paper or an
> orgo lab report for causing anxiety in spring term. I'm here as your home-away-from-home RA
> for a how-to on housing. The most important thing you need to pay attention to is the
> housing timeline...

**2 — `tks_cultural_food.txt #0`**
> During my first night at Knox I heard two people talking in my first language from my dorm
> window, and for a second I felt like I had never left home. However, that feeling of pride
> and belonging soon turned into apprehension then disappointment as I continued to learn
> about Knox's treatment of students with diverse identities.

**3 — `rmp_knox_professors.txt #0`**
> ## Knox College professor rating summary (overall numbers)
> - Sarah Day-O'Connell - Music - 34% would take again, difficulty 3.6
> - Peter Schwartzman - Environmental Studies - 58% would take again, difficulty 3.3
> - Joan Huguet - Music - 100% would take again, difficulty 4 (3 ratings)
> - Mark Shroyer - Physics - see reviews below

**4 — `niche_knox_campus_life.txt #0`**
> # Knox College Campus Life — Galesburg, IL - Overall Rating 3.66/5 (573 reviews)
> Party Scene grade: B-  Safety grade: C+  Campus Food grade: C  Dorms grade: C
> Average Housing Cost: $5,091 per year. POLL: 34% of students say overall dorm quality is
> great (170 responses)...

**5 — `niche_knox_student_reviews.txt #2`**
> Rating 4/5 - Sophomore - 3 months ago: Good school if you're still trying to figure out what
> you want to study. There's not much around town.
> Rating 5/5 - Other - 7 months ago: It was a very fun and diverse college. Meeting new people
> from all types of backgrounds and interests makes communicating more fun...

---

## Embedding Model

**Model used:** `all-MiniLM-L6-v2` via sentence-transformers — runs locally, no API key, no
rate limits, 384-dim, ~256-token input. It's plenty for short English reviews and free.

**Production tradeoff reflection:** if cost weren't a constraint I'd weigh a larger / API
model (e.g. OpenAI `text-embedding-3-large`, Cohere `embed-multilingual`). The biggest reason
is **multilingual support** — Knox is ~38% international students, so real users may ask in
other languages, and MiniLM is English-centric. A bigger model would also separate near-
identical opinions ("food is fine" vs "food is bland") more reliably and handle longer
context. The downsides: per-call cost, latency, rate limits, and privacy — local embeddings
keep student data on my machine, which matters for a product built on student data.

---

## Grounded Generation

Generation uses Groq `llama-3.3-70b-versatile` at temperature 0. Grounding is enforced two
ways:

**System prompt (enforces, not suggests):**
> "Answer using ONLY the numbered context excerpts provided. Use only facts found in the
> context, never outside knowledge. If the context does not contain enough information, reply
> with EXACTLY: 'I don't have enough information on that.' Cite the source filename(s) in
> parentheses."

**Source attribution is guaranteed by code, not the model.** `ask()` returns the source
filenames taken from the retrieved chunks' metadata (deduped, in order). On a refusal it
returns no sources, so the system never cites documents for an answer it didn't actually give.
The model is *also* asked to cite filenames inline, which it does, but the displayed source
list comes from our retrieval metadata regardless.

### Query interface
A Gradio web UI (`src/app.py`, http://localhost:7860): an input textbox ("Your question"), an
**Ask** button (Enter also works), an **Answer** box, and a **Retrieved from** box listing the
source files. Usable without explanation.

**Sample interaction transcript:**
```
Question:  Is the housing lottery actually random?
Answer:    The housing assignment is not entirely random, as Campus Life prioritizes pairs
           and suites that have already agreed to living together (tks_housing_101.txt). If
           you don't pick a roommate, you will be randomly assigned one (tks_housing_101.txt).
           Switching rooms can be very hard if you don't vibe with your roommate
           (niche_knox_student_reviews.txt).
Retrieved from:  • niche_knox_student_reviews.txt  • tks_housing_101.txt
                 • tks_fifthyear_offcampus_housing.txt  • niche_knox_campus_life.txt
```

### Example responses (2 grounded + 1 out-of-scope refusal)

**Grounded #1 —** *"Is the housing assignment actually random...?"*
> The housing assignment is not entirely random... If you don't pick a roommate, you will be
> randomly assigned one (tks_housing_101.txt). Switching rooms can be very hard if you don't
> vibe with your roommate (niche_knox_student_reviews.txt).
> Sources: tks_housing_101.txt, niche_knox_student_reviews.txt

**Grounded #2 —** *"Is the caf food any good, and what do students complain about?"*
> Students have mixed opinions... 43% highly rate the dining facilities
> (niche_knox_campus_life.txt). However, some complain about lack of flavor, cultural
> appropriation, and mislabeling (e.g. Feijoada made with vegetables) (tks_cultural_food.txt),
> and about cost (tks_meal_plan_mandatory.txt).
> Sources: tks_meal_plan_mandatory.txt, niche_knox_campus_life.txt, tks_cultural_food.txt

**Out-of-scope —** *"Which CS professor at Knox gives the most useful feedback?"*
> I don't have enough information on that.
> Sources: (none)

---

## Evaluation Report

Run with `python src/evaluate.py`. Distances are cosine (lower = closer).

| # | Question | System response (summary) | Retrieval | Accuracy |
|---|----------|---------------------------|-----------|----------|
| 1 | Is the housing assignment actually random, and how hard is it to switch roommates? | Not entirely random; random if you don't pick; very hard to change rooms. Cited correctly. | Relevant (top 0.339) | **Accurate** |
| 2 | Is the caf food any good, and what do students complain about? | Mixed; 43% rate it; complaints about flavor, cultural mislabeling, cost. | Relevant (top 0.366) | **Accurate** |
| 3 | What do international students say about how Knox treats them? | Financial aid "HORRIBLE", food not sustainable/hypocritical. **Missed** the summer-housing $308 angle. | Relevant (top 0.290) | **Partially accurate** |
| 4 | Which professors do students actually like, and is anyone hit-or-miss? | Generic ("dedicated, fun, accessible"); caught a co-teaching conflict; **did not name** Joan Huguet (the clearest favorite). | Partially relevant (top 0.447; named reviews ranked low) | **Partially accurate** |
| 5 | Which CS professor gives the most useful feedback? | "I don't have enough information on that." | Off-target (no CS data exists) | **Accurate** (correct refusal) |

---

## Failure Case Analysis

**Question that failed:** Q4 — "Which professors do students actually like, and is anyone
hit-or-miss?"

**What the system returned:** a vague answer ("students like professors who are dedicated,
diligent, fun, and accessible") that never named **Joan Huguet**, even though my corpus has a
glowing RMP review of her ("all-around amazing person... her door is literally always open").

**Root cause (chunking + retrieval):** the retrieved chunks were dominated by Niche
*grade-table* text (`niche_knox_students_academics #2`, distance 0.447) rather than the actual
RMP reviews, which only appeared at rank 4 (distance 0.571, above my 0.5 target). Two pipeline
causes: (1) my query said "professors" generically without names, which matches the grade
tables; and (2) my chunking split each professor's **name** away from their **review text** —
e.g. the chunk that contains Schwartzman's review starts mid-text ("makes me want to take
action...") because the heading "## Peter Schwartzman" landed in the previous chunk. So even
when a review is retrieved, the model can't tell whose review it is.

**What I would change:** chunk `rmp_knox_professors.txt` *per professor*, prepending the
professor's name to every one of their review chunks (so the name travels with the opinion),
or store the professor name as chunk metadata. That keeps "who" attached to "what."

*(Q5 is a second, intentional failure mode — an out-of-scope question with no data in the
corpus. Here the retrieval also returned off-topic chunks, but the grounding prompt caught it
and the system correctly refused instead of inventing a CS professor.)*

---

## Spec Reflection

**One way the spec helped:** writing the Chunking Strategy in `planning.md` *before* coding
forced me to measure my documents first. Because I'd already decided "~600 chars, paragraph-
aware, because 87% of my units are under 500," the implementation was a direct translation of
that decision instead of a blind default — and I could defend the number.

**One way the implementation diverged:** my plan assumed retrieval would mostly "just work" at
top-k=5. In practice the professor question (Q4) exposed that chunking choices upstream
(splitting names from reviews) quietly hurt retrieval — something the spec didn't anticipate.
I kept the weakness and documented it rather than over-tuning, but it changed how I think
about chunking: boundaries aren't just about size, they're about keeping an entity together
with what's said about it.

---

## AI Usage

**Instance 1 — implementing the pipeline from my spec.** I gave Claude my `planning.md`
Chunking section and asked it to implement `ingest.py` and `chunk.py`. It produced a
paragraph-aware ~600/100 splitter. I directed the key decisions myself: I had it measure my
corpus's paragraph lengths first so the 600 number was justified (not the default 500), and I
added a `_normalize` step to flatten em-dashes/curly quotes after I saw `�` artifacts in the
terminal.

**Instance 2 — overriding a bad AI suggestion about documents.** When I asked about sources,
one AI suggested I store each document as a short AI-written "summary note." I rejected that:
summarized documents would gut the chunking and retrieval requirements (one tiny chunk each,
nothing to match on). I insisted on collecting **real, verbatim** student text instead, which
is why the corpus is full Niche reviews and Knox Student articles.

**Instance 3 — directing the evaluation design.** Claude's first draft of test questions
included ones answerable from official pages ("why is the meal plan mandatory"). I replaced
them with experiential questions ("is the food actually good", "is housing really random")
because the whole point is the *unofficial* knowledge, and I deliberately kept the weak
professor question (Q4) to have an honest failure to analyze.
