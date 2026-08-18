# Project 42 — Starter Kit

**Version 1.0 — 18 August 2026.** For someone joining the project with no background in
AI, search systems, or measurement. Nothing here assumes you have seen any of it before.

Read this before you run anything. It is long, but it is the only long thing you have to read.

---

## 1. What we are building, in one paragraph

Engineers at our organisation have to follow **ECSS standards** — a large set of European
space engineering rulebooks. There are 145 of them here, and the answer to a practical
question is usually one paragraph buried in one of them. People waste hours looking.

So we built a system where you ask a question in plain English and get an answer **with the
evidence attached**: the document, the section, and the actual sentences it came from.

ECSS is not the real destination. It is the **proving ground**. The real goal is to point the
same system at our own project documents. ECSS is public, stable and well structured, so it
is a fair place to find out whether the thing works before we trust it with anything of ours.

---

## 2. The thing that makes this project unusual

Most people who build a system like this demo it, see that the answers look good, and ship it.

**We don't, because "looks good" and "is correct" are different things, and you cannot tell
them apart by reading answers.** Here is a real example from this project.

We asked the system how a "spacecraft elapsed time" value is laid out when it is sent over a
**data bus** (the wiring that carries data between parts of a spacecraft). It answered:

> The first 4 octets carry the Coarse Time. The next 3 octets carry the Fine Time.

(An **octet** is 8 bits — one byte. So this is saying which bytes hold which part of the time value.)

Fluent. Confident. Cites the correct clause of the correct standard. **And exactly backwards.**
The standard puts Fine Time first. An engineer building hardware from that answer would wire
it wrong.

Nothing about the answer's *appearance* revealed this. We only found it because someone
opened the standard and compared, line by line.

**That is why this project measures instead of demonstrating.** Everything below exists to
turn "it seems fine" into a number we can defend.

---

## 3. The words you will hear, in plain English

Take your time here. Almost everything later depends on these.

### About the system itself

**LLM (Large Language Model)**
The AI that writes the answer. Ours is called *Qwen3-32B*. You give it text, it continues the
text. That is genuinely all it does — everything else is arranging what text it sees.

**Prompt**
Everything we send the LLM: instructions, the question, and the evidence passages. The LLM
sees nothing else. It has no memory between questions.

**RAG (Retrieval-Augmented Generation)**
The shape of our system, and the most important idea here. Two steps:

1. **Retrieval** — search the 145 documents and find the handful of passages most likely to
   contain the answer.
2. **Generation** — hand those passages to the LLM and say "answer using only these".

The alternative would be to let the LLM answer from memory. We don't, because it has no
reliable memory of ECSS, and because an answer from memory has no evidence to show.

**Why "augmented"?** The LLM's own knowledge is *augmented* by the passages we retrieve. The
name is describing that hand-off.

**Chunk (or passage)**
Documents are too big to hand to an LLM whole, so at load time we cut them into pieces of
roughly a paragraph or two. A chunk is one piece. We have about 35,000 of them. **Retrieval
finds chunks, not documents** — and that distinction turns out to matter enormously (section 5).

**Ingestion**
The one-off job of reading all 145 PDFs, cutting them into chunks, and storing them so they
can be searched. Takes hours. When you change how ingestion works you have to redo all of it.

**Embedding (or vector)**
A way of turning text into a list of ~1000 numbers, such that text with similar *meaning*
gets similar numbers. This is what lets us search by meaning rather than by exact words — so
"how cold can it get" can match a passage about "minimum temperature" with no shared words.

The model that does this is called an **embedding model**. Ours is *BGE-M3*.

**Dense vs sparse search**
Two ways of searching, with opposite strengths:

- **Dense** = the meaning-based search just described. Great at paraphrase. **Bad at exact
  codes** — it cannot reliably tell `ECSS-E-ST-10-02C` from `ECSS-E-ST-10-03C`, because they
  *mean* almost the same thing.
- **Sparse** = old-fashioned keyword matching. Bad at paraphrase, excellent at exact codes.

**Hybrid search** runs both and merges the results, so we get both strengths. The merging
recipe is called **RRF (Reciprocal Rank Fusion)** — you don't need the maths, just know it is
the rule for combining two ranked lists into one.

**Reranker (or cross-encoder)**
Search returns 50 candidate chunks, roughly sorted. A reranker is a second, slower, more
careful model that re-sorts just those 50 and picks the best 10. It is more accurate than
search but far too slow to run over all 35,000 chunks — which is exactly why we search first
and rerank second.

Ours is *BGE-reranker-v2-m3*.

**Context**
The final ~10 chunks we actually put in the prompt. "It wasn't in the context" means the
right passage was never shown to the LLM — so the LLM had no way to get it right.

**Refusal**
When the system says "the corpus does not contain this information" instead of answering.
**A refusal is usually good.** A system that answers everything is a system that invents
things. We measure refusals deliberately.

**Corpus**
The whole set of documents the system can search. Ours is 145 ECSS standards.

**Collection (or index)**
A named store of chunks and their vectors inside the database. You can have several side by
side — for example one built with one embedding model and one with another. **Building into a
new collection rather than overwriting the old one is how you keep the ability to compare.**

**Context window**
How many chunks we put in the prompt — ten, for us. "Widening the context window" means showing
the LLM more chunks. We measured that this does not help us, which is a useful thing to know
before suggesting it.

**Span (or anchor span)**
The exact sentences in a standard that a claim came from — the evidence's precise location.
When you see "101/117 spans", it means: of 117 known evidence locations, retrieval found 101.

**Campaign**
One complete round of this work: write a set of questions, agree the correct answers, run the
system against them, publish the results. We are on campaign 3. Numbers from different
campaigns use different questions and **cannot be compared to each other.**

**Vision-language model (VL)**
A model that can look at an *image* as well as read text. We use one (*Qwen2.5-VL*) to describe
figures on a page, because the rest of the system only reads text and is therefore blind to
diagrams.

**A note on all these names.** *BGE-M3*, *Qwen3-32B*, *Qwen2.5-VL*, *Nemotron*, *Docling*,
*Qdrant* are just product names, like brands of tool. Which one is which matters far less than
**what job it does** — and every one of them is replaceable, which is exactly what your
experiments are for.

### About measuring

**Benchmark**
A fixed set of questions with known correct answers, used to score the system. "Fixed"
matters: if the questions change, two scores cannot be compared.

**Ground truth**
What the right answer actually is, decided in advance and written down. Without it you are
just admiring output.

**Claim**
We do not score answers as whole essays. We break the correct answer into separate factual
statements — claims — and check each one. For example:

> Q: What does the standard require for the review data package at PDR?
> Claim 1: A preliminary external interfaces design document is required.
> Claim 2: It must be traceable to the ICD.

(**PDR** = Preliminary Design Review, a formal project milestone. **ICD** = Interface Control
Document, which records how two pieces of hardware or software connect. You will meet a lot of
ECSS abbreviations like these; you do not need to learn them, you only need to notice when the
system gets one wrong.)

**Claim coverage**
The fraction of required claims the answer actually stated. If an answer states 3 of 4
required claims, coverage is 0.75. This is our headline score.

**Judge**
Checking thousands of claims by hand is impossible, so an LLM does it: "does this answer
state this claim? yes/no". We call it the judge.

**A judge is an instrument, and instruments have error.** Ours agrees with human-equivalent
reviewers 98% of the time *on that exact question*. It is much worse at other questions —
see section 6, which is one of the most important things in this document.

**Qrel (query relevance judgement)**
A record saying "for question Q, chunk C is a correct piece of evidence". Ours come from
**anchor spans** — the exact sentences in the standard that a claim came from. Qrels let us
measure retrieval *on its own*, with no LLM involved, which makes those experiments fast,
cheap and perfectly repeatable.

**Recall@k**
Of the evidence that should have been found, what fraction appeared in the top *k* results?
"Evidence recall@10 = 86%" means: in the 10 chunks we showed the LLM, we had the right
evidence 86% of the time. The other 14% of the time the LLM was set up to fail.

**Precision**
Of what we returned, what fraction was actually relevant. Recall asks "did we miss anything";
precision asks "did we return junk".

**MRR / nDCG**
Two standard scores for "was the good stuff near the top, not just present somewhere". Higher
is better. You do not need the formulas; the tools compute them.

**Hallucination**
When the system states something that is not true and not in the evidence. Ours does this on
about 1 answer in 90 — a number that took a full manual census to establish, and that we
originally got wrong by a factor of eight.

**Baseline**
The current measured behaviour, before your change. Without one, a number after your change
means nothing.

**Ablation / swap**
Changing exactly one component and re-measuring, to find out what that component contributes.
This is most of what you will be doing.

**Held-out**
Questions deliberately kept aside and never used while developing, so they can give an honest
verdict later. Once you tune against a set, it can no longer judge you fairly.

**Confidence interval (CI)**
A range that says how uncertain a measurement is. Our headline is 0.804 with a CI of
[0.735, 0.868]. **That width is the important part**: it means a change of 0.02 is invisible
to us. You cannot detect a difference smaller than your uncertainty, and pretending otherwise
is the most common mistake in this field.

**Determinism**
Whether running the same thing twice gives the same answer. Our *retrieval* is deterministic.
Our *generation* is not — the same question can produce different wording, and occasionally a
different score. So a single run is never proof.

---

## 4. What our pipeline actually does

One question, start to finish. There is exactly one code path — `ask_v2.answer()`.

```
   your question
        |
   [1] SEARCH          dense (meaning) + sparse (keywords), merged by RRF
        |              -> 50 candidate chunks
        |
   [2] RERANK          a slower, more careful model re-sorts those 50
        |              -> best 10 chunks = "the context"
        |
   [3] GENERATE        prompt = instructions + question + those 10 chunks
        |              LLM writes the answer, citing document and clause
        |
   the answer + its evidence
```

Settings are **inherited, never re-chosen**: temperature 0.0 (least random setting),
"thinking mode" off, 50 candidates, 10 in context. If you change one, say so loudly, because
every past number was measured with these.

**Loading the documents** (done once, separately):

```
   PDF -> Docling (reads layout, tables, headings)
       -> cut into chunks at section boundaries
       -> label each chunk (document, clause number, page, heading trail)
       -> embed each chunk into a vector
       -> store in Qdrant (the database that holds vectors)
```

---

## 5. Where it is actually weak — read this before choosing what to work on

We measured this rather than guessing, and it is not where most people assume.

```
   right DOCUMENT found:   99%     <- basically solved
   right PASSAGE found:    86%     <- the problem
```

And the crucial detail: **passage recall is 86% at 10 results and still 86% at 20.** The
missing 14% are not just below the cut-off — they are not in the top 50 *at all*. So making
the context window bigger fixes nothing.

The consequence is stark:

```
   when the right evidence reached the LLM:   score 0.936
   when it did not:                           score 0.167
```

**So the LLM is not the weak part. Finding the right passage is.** Two things follow, and
they should shape what you pick up:

- Work on **search and embeddings** is aimed at the actual bottleneck.
- Work on the **reranker** is probably not. We tested this: the reranker is doing its job
  well; it just cannot rescue a good passage that search never handed it. A better reranker
  re-sorts the same flawed 50 candidates.

---

## 6. The most important lesson this project has learned

**An instrument that was validated for one question is not valid for a different question.**

Our judge is validated at 98% on: *does this ANSWER contain this CLAIM?*

We then reused it — same model, same prompt style, same domain — for other questions that
sound similar. It failed all of them:

| what we asked the judge | how well it did |
|---|---|
| does this answer contain this claim | **98% — validated** |
| does this answer state this *false* claim | 12% correct |
| does this answer *accept a false assumption* | 0 out of 3 |
| does this *passage support* this claim | 0 out of 7 |
| does this answer state this *ordering* | 0 out of 1 |

Read that table twice. The judge is not "good" or "bad" — it is good at **one specific
comparison** and unreliable outside it. "It's a claim checker and this is about claims" is a
name collision, not a validation.

**What this means for you:** if you use any automated checker for something it was not
measured on, you are producing decoration, not evidence. Measure it first, on cases where you
already know the answer.

There is a second, related lesson. Recently the figure-captioning model was switched on for
the first time. It was asked to describe figures on a page, and told "if none, reply none".
It instead replied, in prose, *"There are no figures or diagrams present on this page. The
content is purely textual..."* — and that text was pasted into 29% of our searchable chunks.

Nobody had ever read its output, because the feature had always been off. **A feature turned
on for the first time has never been checked, however old the code is.**

---

## 7. How we work, and why

These are not style preferences. Each one exists because ignoring it cost us real work.

**1. Write down what you expect before you run it.**
Decide your threshold, your success criterion and what would count as failure *first*. A
number chosen after seeing the data is not a measurement — it is a description of the data.

**2. Never move the goalposts to make a result pass.**
If you catch yourself adjusting a threshold because the number came out badly, stop and write
down what you were about to do. This is our oldest rule and it has saved us more than once —
including on a result we *wanted* to be true.

**3. Change one thing at a time.**
Swap the embedding model *or* the reranker, never both. If two things change, the result is
uninterpretable and the whole run is wasted.

**4. Always report the denominator.**
Not "86%" — "86% of 117 spans". And if something was skipped, say what and why. A silently
dropped case looks identical to a passing one.

**5. Read the individual cases, not just the total.**
Every finding that mattered here came from reading 5–20 actual examples. Every serious error
we made came from trusting a summary number. The backwards-octets answer in section 2 was found by
reading. The caption disaster in section 6 was found by reading. The pattern is not subtle.

**6. Keep mistakes on the record.**
We have retracted three sets of results and one scoring function. They all stay in the
documents with the reason. Deleting a mistake means the next person repeats it.

**7. Every tool must self-test.**
Each script has `--self-test` with named checks that must pass before it is used. Run it
first, every time.

---

## 8. Your box vs our box

You have your own Spark machine. That is deliberate — you can run experiments without
blocking anything here.

But it means **your numbers and our numbers are not directly comparable.** Different machine,
possibly different model versions, possibly a differently built index. Comparing your
"after" to our "before" would attribute the difference to your change when it might be the
machine.

**So your very first job is not an experiment.** It is to reproduce our current baseline on
your own box and confirm you get the same figures. Only then does a swap mean anything —
because then you are comparing your "after" to *your own* "before".

The experiment protocol document covers exactly how.

---

## 9. One thing to be careful about

Some of what is in this repository is **ground truth that must stay uncontaminated** — the
questions, the correct answers, our system's outputs, and the judge's verdicts.

There is a real possibility that we will later ask you to act as an *independent evaluator* —
someone who has not seen our answers, and can therefore judge them fairly. That is genuinely
valuable and it is a gap we cannot close ourselves. But it only works if you have not already
read the material.

So: **the retrieval experiments deliberately do not require you to read any answers.** They
work with questions and evidence locations only. Stick to those unless you are told
otherwise, and if you find yourself about to open a file full of our system's answers, ask
first.

---

## 10. Where to look things up

Start here. Do not read the whole `docs/` folder — there are 40+ files, many superseded.

| I want to know | read |
|---|---|
| how to run an experiment properly | `P42_External_Experiment_Protocol.md` |
| what the pipeline does, in detail | `P42_Design_Pipeline_and_Benchmark.md` sections 6.2 and 8 |
| what all the current results are | `P42_Campaign3_Results.md` |
| where retrieval loses answers | `P42_Retrieval_Diagnosis.md` |
| every mistake we have made and why | `P42_Lessons_Learned.md` |
| the list of open work | `P42_Register.md` |

**If something here is unclear, that is a defect in this document, not in you.** Say so and
it gets fixed — several sections exist because someone said exactly that.
