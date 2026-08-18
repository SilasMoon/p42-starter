# Project 42 — Experiment Protocol for a Second Machine

**Version 1.0 — 18 August 2026.** How to run an experiment here so the result means something.
Read `P42_Starter_Kit.md` first — this document uses its vocabulary, and assumes you have met
terms like *chunk*, *span*, *collection*, *recall* and *baseline* there.

---

## The one-page version

1. Reproduce our baseline on your box. Change nothing. Confirm you match.
2. Write down what you are going to change and what result would count as a win — **before** running.
3. Change exactly one thing.
4. Re-run the same measurement on the same questions.
5. Read the individual cases that moved. All of them, if there are fewer than twenty.
6. Report gains and losses **separately**. Never report only the net.

Step 5 is the one people skip, and it is the one that has caught every real problem here.

---

## Why step 1 exists

Your machine is not our machine. Model weights, library versions and the built index can all
differ in ways nobody notices until they explain a result that was actually a difference in
setup.

If you skip the baseline and compare your "after" to our published "before", any difference
you find has at least two possible causes and you cannot separate them. **Reproducing first
turns your box into its own control.**

If you cannot reproduce our numbers, that is not a failure — it is a finding, and we need to
know before you do anything else. Report it.

---

## Task 0 — reproduce the baseline (do this first)

**No experiment. No swaps. Nothing changed.**

```bash
python3 retrieval_recall.py --self-test          # must pass before use
python3 retrieval_recall.py --run \
    --unregistered "baseline reproduction, <your name>, <date>" \
    --adopted questions/2026-08-16_150940/adopted_2026-08-16_150940.jsonl
```

**What you should get** (measured here on 18 August 2026, index `p42_text_v3_bgelex`):

```
A baseline        101/117 spans     96/111 items complete
B k=200           103/117           98/111
C q-only           99/117           93/111
D k=200 q-only     99/117           95/111
cheap spans        13 of 117 (11%)
```

**How close is close enough?** Retrieval here is deterministic, so **you should match exactly**.
If you are off by even one span, stop and find out why before continuing. A one-span
difference at this stage becomes an uninterpretable result later.

Do the same for the other two question sets listed in the "Question sets" section below.

**What "cheap spans" means and why it is printed:** some evidence locations are recorded
against a section label that covers a huge part of its document, so "we found the right
section" is nearly free for those. The tool reports how many, because a recall figure that
mixes them with precise ones reads as better than it is. Quote the cheap count beside any
recall number you report.

---

## Task 1 — the embedding model (highest value)

**The question:** does a different embedding model find the right passage more often?

This aims straight at the measured bottleneck: the right *document* is found 99% of the time,
the right *passage* only 86%, and that 86% does not improve with a bigger context window.

**Candidate:** `Qwen3-Embedding-4B` in place of `BGE-M3`.

### Read this before you start — it is not a config change

BGE-M3 gives us **two** things from one model: the meaning-based vector *and* the keyword
weights. Qwen3-Embedding gives you **only the meaning-based vector.**

So swapping it does not replace one part — it **deletes half of our hybrid search**, the half
that tells `ECSS-E-ST-10-02C` apart from `ECSS-E-ST-10-03C`. Exact document codes are
extremely common in these questions.

You therefore have a design decision to make and write down *before* running anything:

- **(a)** Compare dense-only-Qwen3 against dense-only-BGE-M3. Fair, one variable, but it is not
  our real system.
- **(b)** Keep BGE-M3's keyword half and swap only the meaning half. Closer to reality, but the
  two halves were trained together and may not combine as well.
- **(c)** Find a different source of keyword weights.

**There is no obviously right answer.** Pick one, write down why, and say which you did in every
number you report. (a) is the cleanest place to start.

### Practical notes

- A different embedding model produces vectors of a different size. You cannot put them in the
  existing index — you must **build a new one**, which means re-running ingestion over all 145
  documents. Budget several hours.
- Build into a **new collection name**. Never overwrite an existing one. A collection you
  overwrote is a measurement you can no longer reproduce.
- Ingestion has a `--collection` flag for exactly this.

### What counts as a result

Report, for each configuration:

```
spans reached / spans total        (and the cheap-span count)
items with ALL their spans found / items total
GAINS  - every span the new model found that the old one missed, listed individually
LOSSES - every span the old model found that the new one missed, listed individually
```

**Gains and losses are never netted into one number.** "+3 −1" is a different fact from "+2",
and the losses are where the mechanism usually is. Read every loss.

**Expect ambiguity, and do not resolve it by hand-waving.** Our two most promising retrieval
changes to date both came out around +3/−1 — too small to distinguish from noise on the data
available. If yours does too, say so plainly. "We cannot tell from this" is a legitimate and
useful result; a confident claim from an underpowered run is not.

**How big does a difference need to be?** Roughly: you need **≥56 questions** for an anchor-span
result to be trustworthy, and **≥80** for an answer-quality result. Runs smaller than that
cannot settle anything, however clean they look.

---

## Task 2 — figure and diagram handling (self-contained, and a real defect to fix)

**The question:** can figure content be captured reliably enough to be worth having?

Some requirements live in a diagram. The standard will say something like *"shall be mapped
into the CAN frame **according to Figure 7-1**"* — and the actual layout is only in the picture.
(A **CAN frame** is one message on a common spacecraft data bus. The point is not the acronym: the
requirement says "see the figure", so the answer is *only* in the figure.)
Our system cannot see pictures, so it guesses from the surrounding text, and we have caught it
guessing **backwards**.

**Size of the prize, measured:** across all 145 documents there are 2,431 mentions of figures,
but only **48** where the text hands the content to the figure like that. Most ECSS figures
just illustrate something the text already states. So this is a real gap but a bounded one —
please do not report it as "the system is blind to 2,431 things".

### The defect to fix — and it is a good brief

We turned figure captioning on for the first time on 18 August 2026. The model was shown each
page and asked to describe any figures, with the instruction *"if none, reply none"*.

It did not comply. It replied, in prose:

> There are no figures or diagrams present on this page. The content is purely textual...

That text — a median of 196 characters of pure noise — was pasted into the searchable text of
**29% of all chunks**. It would have degraded the very thing it was meant to improve. We caught
it 25 minutes into a 4.5-hour job by *reading the output*, and filtered it out.

**Your brief:** the instruction was a *request*, and the model declined it. Design an **output
contract** the model cannot violate in that way — for example a structured response like

```json
{"has_figure": true, "figures": [{"label": "Figure 7-1", "description": "..."}]}
```

That is **JSON** — a strict, machine-readable format where each field has a fixed name and type.
`has_figure` is a **boolean**: it can only be `true` or `false`. It cannot be a sentence, so
"there are no figures here" becomes **impossible to express** rather than something we have to
filter out afterwards. That is the difference between asking and enforcing. Then measure
whether it holds: run it over a few hundred pages, count how often the contract is broken, and
read a sample of what comes back.

**How to tell if it is actually working**, in order of strength:

1. The contract holds — the model returns valid structured output, and you can say how often.
2. Negative results are structurally impossible to index, not filtered out afterwards.
3. On pages that genuinely contain a figure, the description contains what the figure shows.
   Check by opening the PDF page and comparing. Twenty pages read carefully beats two thousand
   scored automatically.

A better vision model (`Qwen3-VL` in place of `Qwen2.5-VL`) is worth trying **as part of this**,
not as a separate study — the contract is the thing that matters, and a stronger model with a
loose contract will still produce unusable output.

---

## Task 3 — the answer model (do after 1 and 2)

**The question:** does a stronger LLM produce better answers from the same evidence?

Candidates: `Qwen3.6-35B-A3B`, `Nemotron 3 Super`, in place of `Qwen3-32B`.

**Manage your expectations, because we have measured this.** When the right evidence reaches the
LLM, it already scores 0.936. There is not much room. The LLM is not the bottleneck.

It is still worth doing for one specific reason: the failure described at the start of the starter kit — inventing
a byte ordering by inferring it from the wrong thing — is a *reasoning* failure, not a retrieval
failure. A stronger model might not make it. That is a narrow, testable question.

### The rule that must not be broken

**When you change the answer model, the judge must stay exactly as it is.**

The judge is an LLM too. If you swap the answer model and the judge in the same run, you have
changed the thing being measured and the thing doing the measuring at once, and the result is
worthless. This mistake has already cost this project a retraction.

Same rule for the questions, the claims and the scoring code: **only the answer model moves.**

### Warning: this task requires reading answers

Unlike Tasks 0–2, this one exposes you to our system's outputs. Check before starting — we may
want to keep you clear of them so you can serve as an independent reviewer later. Ask.

---

## Task 4 — the reranker (lowest priority; here so you know why)

Candidates: `Qwen3-Reranker-4B/8B` in place of `BGE-reranker-v2-m3`.

**We think this is not where the problem is, and we have evidence.** When we traced the passages
the system fails to find, they were not sitting just below the cut-off — 10 of 12 were **not in
the top 50 at all.** The reranker only ever sees those 50. It cannot promote something it was
never handed.

So a better reranker re-sorts the same flawed shortlist. **Do this after Task 1**, when the
shortlist may actually be better, and it becomes a sensible question again.

---

## The question sets

Three, all with evidence locations already recorded. Use whichever the task specifies, and
**never mix them in one comparison.**

| set | file | size |
|---|---|---|
| campaign 3 (main) | `questions/2026-08-16_150940/adopted_2026-08-16_150940.jsonl` | 111 questions, 117 spans |
| campaign 2 (older) | `census/2026-08-14_135406/scored/adopted_2026-08-14_151129.jsonl` | 56 questions, 67 spans |
| held-out | `questions/heldout_retrieval.jsonl` | 53 questions, 64 spans |

**The held-out set is special: do not use it while developing.** Its whole value is that nothing
has been tuned against it, so it can give an honest verdict at the end. Use it once, when you
think you have a result. Using it repeatedly destroys it, permanently and invisibly.

---

## Pre-registration template

Fill this in and save it **before** running. It takes ten minutes and it is the difference
between a measurement and a story.

```
EXPERIMENT:      <one line>
DATE:            <date>          WHO: <name>
QUESTION:        <what you are trying to find out, as a question>

WHAT CHANGES:    <exactly one thing>
WHAT STAYS:      <the settings you are inheriting unchanged>
QUESTION SET:    <file, and how many questions>
BASELINE:        <your own Task 0 numbers, from your own box>

WHAT WOULD COUNT AS A WIN:
                 <a number, decided now>
WHAT WOULD COUNT AS A LOSS:
                 <a number, decided now>
WHAT WOULD MEAN "CANNOT TELL":
                 <be honest - this is the most likely outcome>

WHAT I WILL READ BY HAND:
                 <every loss; a sample of gains>
```

**If you cannot fill in "what would count as a win" before running, you are not ready to run.**
That is not bureaucracy: without it, any result can be described as encouraging, and it always
will be.

---

## Reporting

For every experiment, hand back:

1. The pre-registration, unedited, including any prediction that turned out wrong. **Especially
   those.** A prediction that failed is the most informative thing in a report.
2. The numbers, with denominators. Never a bare percentage.
3. Gains and losses listed separately and individually.
4. What you read by hand, and what you concluded from reading it.
5. Anything you changed mid-run and why.
6. What you could **not** determine.

Point 6 is not a weakness. Most of our real findings have been "this measurement cannot answer
that question", and knowing it early has saved weeks.

---

## If something looks wrong

**Stop and say so.** Do not work around it.

Two of this project's most useful findings were things that looked like small oddities: a page
label that seemed slightly off (it turned out half a document was mislabelled), and a caption
that looked verbose (it turned out to be corrupting a third of the index).

Both were noticed by someone looking at raw output and thinking "that's odd". Neither would
have been caught by any test we had. That instinct is the most valuable thing you bring, and it
does not require knowing anything about AI.
