# Project 1 Planning: The Unofficial Knox Guide

## Domain

I went with student life at Knox College in Galesburg, IL, basically the stuff you only
figure out once you're actually here. Which dorms are worth fighting for, why the meal plan
is mandatory, whether the "cultural food" in the caf is the real thing, how the housing
lottery actually decides who gets what.

The reason this is worth doing is that none of it is on the official site. Knox's pages talk
about "diverse dining" and "vibrant residence life," but they're not going to tell you that
during Ramadan the caf served the same dish renamed every day, or that summer housing now
costs $308 a month, or that older dorms have fire alarms that go off for no reason. That
kind of thing lives in student reviews and in The Knox Student, spread out over a lot of
separate pages. The whole point of this project is to pull it into one place you can just
ask a question and get an answer that actually cites where it came from.

---

## Documents

All 10 documents are student-written. I left out the official college pages on purpose,
since the assignment is literally the *unofficial* guide. Knox is small and doesn't have an
active subreddit, so the three places students actually talk are Niche (reviews), Rate My
Professors, and The Knox Student (the campus paper, running since 1878). I collected these
on June 10, 2026.

| # | Source | Type | File |
|---|--------|------|------|
| 1 | Niche — Knox reviews page | Student reviews | `documents/niche_knox_student_reviews.txt` |
| 2 | Niche — Campus Life page | Reviews + polls (housing/dining/safety) | `documents/niche_knox_campus_life.txt` |
| 3 | Niche — Students/Academics | Reviews + facts (professors, demographics) | `documents/niche_knox_students_academics.txt` |
| 4 | Rate My Professors — Knox | Professor reviews (Shroyer, Schwartzman, Huguet, …) | `documents/rmp_knox_professors.txt` |
| 5 | The Knox Student — "Housing 101" | Student journalism (housing lottery) | `documents/tks_housing_101.txt` |
| 6 | The Knox Student — "Why is the meal plan mandatory?" | Student journalism (dining) | `documents/tks_meal_plan_mandatory.txt` |
| 7 | The Knox Student — "Lack of Cultural Food on Campus" | Student column (halal/cultural food) | `documents/tks_cultural_food.txt` |
| 8 | The Knox Student — "Freedom of movement is a privilege" | Student journalism (summer housing fees) | `documents/tks_summer_housing_policy.txt` |
| 9 | The Knox Student — "Fifth-Year for Free housing stipulations" | Student journalism (off-campus approval) | `documents/tks_fifthyear_offcampus_housing.txt` |
| 10 | The Knox Student — "New school year, new freshman dorms" | Student journalism (dorm renovations) | `documents/tks_freshman_dorm_renovations.txt` |

---

## Chunking Strategy

My documents come in two shapes. The Niche and RMP entries are short, usually one review or
one rating, a few sentences each. The Knox Student articles are long, with quotes spread
over several paragraphs. So instead of guessing a number, I measured it first.

I counted the natural "units" in the corpus (one review, one rating block, one article
paragraph), about 137 of them, and looked at how long they run:

- median is around 275 characters
- 90% are under roughly 480–660
- 87% are under 500, and 95% are under 700

So most reviews are short and already make sense on their own. If I just cut every 500
characters like the default does, I'd either glue two unrelated reviews together (noise) or
slice one longer review in half (lost context), which are exactly the two failure modes the
assignment warns about. So I'm going with about 600 characters per chunk, but splitting on
paragraph breaks first instead of cutting mid-sentence. That keeps roughly 95% of reviews
and quotes whole, and only the few really long article paragraphs get split.

For overlap I'm using about 100 characters, a sentence or two. I really only need it for the
long articles, where a fact and its number sometimes land in different paragraphs ("board is
mandatory" in one, "$5,637" in the next), and the overlap keeps those from getting cut
apart. For the short reviews it doesn't hurt anything.

One more reason 600 is safe: that's about 150 tokens, and MiniLM handles 256, so nothing
gets quietly chopped off by the model.

Before chunking I'll strip the leftover website junk (nav menus, "Latest Stories", ads,
footers) and make sure each review's rating and date stay attached to the review text. Every
chunk keeps its source filename so I can cite it later.

---

## Retrieval Approach

I'm using all-MiniLM-L6-v2 through sentence-transformers. It runs locally with no API key or
rate limits, and it's good enough for short English reviews.

For top-k I'm starting at 5. With ~600-character chunks that's about five reviews or quotes
of context, which is enough for the model to actually answer and show more than one opinion,
without burying it in loosely-related stuff. Too few and the right chunk might not even show
up; too many and the prompt gets watered down. I'll adjust once I can see the real distance
scores.

Semantic search helps here because it matches meaning, not exact words. So "is the food any
good" can still pull up a review that says "the caf is bland" even though they share no
words.

If cost weren't a concern I'd look at a bigger or API-hosted model. The main reason is
multilingual support: Knox is about 38% international students, so people might ask in other
languages, and MiniLM is mostly English. A bigger model would also do better at telling
near-identical opinions apart ("food is fine" vs "food is bland") and handle longer text. The
tradeoffs would be cost per call, latency, rate limits, and privacy, since keeping the
embeddings local means student data never leaves my machine.

---

## Evaluation Plan

I deliberately picked questions you *can't* just look up on the college website. The policy
pages will tell you the meal plan is mandatory or how priority numbers are calculated, but
they won't tell you whether students think the random roommate match is fair, or whether the
food is actually any good. That experiential, opinion side is the whole reason an unofficial
guide exists, so that's what I'm testing.

| # | Question | Expected answer (from the documents) |
|---|----------|--------------------------------------|
| 1 | Is the housing/roommate assignment actually random, and how hard is it to switch if you don't get along with your roommate? | Not fully random. If you pick your own roommate or suite you link up on MyHousing and the highest priority number in the group picks. But if you don't choose anyone, Campus Life randomly assigns you a roommate (one student calls it a "buzzfeed quiz"), and people say that if you don't vibe with them it's "very hard to change rooms." (Source: niche_knox_student_reviews, tks_housing_101) |
| 2 | Is the caf food actually any good, and what do students complain about most? | Opinions are split. Some call it "decent" or "surprisingly good" with decent variety; others say it's "usually missing flavor." The most consistent complaints are the repetitive menu and the lack of real cultural/halal options, including renamed dishes that aren't the real thing. (Source: niche_knox_student_reviews, tks_cultural_food) |
| 3 | What do international students say about how Knox actually treats them? | It's a recurring frustration. The caf renamed the same dish daily during Ramadan and mislabels food ("biryani" that's just chicken and rice); one student called the international financial aid office "HORRIBLE" for not helping with changed circumstances; and the return to paid summer housing ($308/month) hits international students who can't easily fly home. (Source: tks_cultural_food, niche_knox_student_reviews, tks_summer_housing_policy) |
| 4 | Which professors do students actually like, and is anyone hit-or-miss? | Students rave about Joan Huguet (caring, "door is literally always open," challenging but rewarding). Peter Schwartzman is a mixed bag: clearly passionate, but reviews say "every lecture ended up being about him" with a disconnect between readings and class. Mark Shroyer is split too, between "lectures easy to understand, grades fairly" and "unclear lectures, expects you to teach yourself." (Source: rmp_knox_professors) |
| 5 | **(this is my intended failure case)** Which CS professor at Knox gives the most useful feedback? | There are no CS professor reviews in my corpus at all (the RMP ones are Music, Physics, Environmental Studies, Art, Philosophy, Modern Languages). The right move for the system is to say it doesn't have enough information. This question is here to test whether grounding actually holds when the data isn't there. |

---

## Anticipated Challenges

1. Two very different document lengths. Short reviews and long articles don't want the same
   chunk size. Too small and an article's fact gets split across chunks, so retrieval only
   grabs half of it. Too big and unrelated reviews get mashed together and the embedding
   turns fuzzy. The ~600-character paragraph-aware chunking is my compromise, but it's the
   thing most likely to need tuning.

2. Leftover junk in the raw files. The documents still have nav menus, ads, "Latest
   Stories", and in the Niche file the rating line sometimes sits apart from the review it
   belongs to. If I don't clean that up, chunks fill with garbage and ratings get separated
   from the opinions they go with. So there's a cleaning pass before chunking.

3. Questions I have no data for. Nobody reviewed a CS professor, so "best CS prof" has no
   real answer in my corpus. If my prompt is loose the model will just invent one. I'm
   planning to handle it with a strict "only answer from the documents, otherwise say you
   don't know" instruction, plus citations so I can always check where an answer came from.

---

## Architecture

```
 [10 .txt documents]                      documents/*.txt (Niche, RMP, The Knox Student)
        │
        ▼
 1. INGESTION        load files + strip boilerplate            ── Python (ingest.py)
        │
        ▼
 2. CHUNKING         ~600 chars, ~100 overlap, paragraph-aware ── Python (chunk.py)
        │
        ▼
 3. EMBED + STORE    embed chunks, store with source metadata  ── all-MiniLM-L6-v2 + ChromaDB
        │                                                          (build_index.py)
        ▼
 4. RETRIEVAL        query → top-k=5 chunks + distances         ── ChromaDB similarity search
        │                                                          (retrieve.py)
        ▼
 5. GENERATION       grounded answer + cited source files      ── Groq llama-3.3-70b-versatile
                                                                   (generate.py, app.py)
                          │
                          ▼
                   [Gradio web UI: question → answer + sources]
```

---

## AI Tool Plan

**Milestone 3 (ingestion + chunking).** I'll give Claude my Documents table and the
Chunking Strategy section and ask it to write `ingest.py` (load the `.txt` files, strip the
boilerplate, keep each review's rating attached to its text) and `chunk.py` (the ~600/100
paragraph-aware splitter that also tracks which file each chunk came from). Then I'll print
5 random chunks and the total count myself to make sure they actually read like complete
thoughts.

**Milestone 4 (embedding + retrieval).** I'll give it the Retrieval Approach section and the
diagram and ask for `build_index.py` (embed with MiniLM, store in ChromaDB with the source
file and chunk index) and `retrieve.py` (a `retrieve(query, k=5)` that returns the text,
source, and distance). I'll test it on 3 of my eval questions and look at whether the
distances and chunks make sense before adding the LLM.

**Milestone 5 (generation + interface).** I'll give it my grounding rule and the output
format and ask for `generate.py` (Groq llama-3.3-70b, answer only from the retrieved
context or say it doesn't know, with the source filenames added in code rather than left to
the model) and `app.py` (a simple Gradio box: question in, answer plus sources out). I'll
test it on two normal questions and the CS-professor one, which should come back as "not
enough information."
