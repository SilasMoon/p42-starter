# Project 42 — starter bundle

The knowledge base pipeline, the tools that measure it, and the question sets, for running
experiments on your own machine.

**Do not run anything yet.** Three documents, in this order — each one hands off to the next.

## 1. Understand what this is → `docs/P42_Starter_Kit.md`

Read this first, cover to cover. It assumes **no background** in AI, search systems or
measurement: what the project is for, every term you will meet, how the pipeline works, where it
is actually weak, and the rules we work by. About half an hour.

Nothing else will make sense without it, and it is the only long thing you have to read.

## 2. Get it running → `docs/P42_Second_Box_Setup.md`

Every command you need, in order, from a fresh machine to a working pipeline that answers a
question. **All the setup instructions live there and only there** — this README deliberately
does not repeat them, so there is one place to follow and nothing to reconcile.

Be aware before you start: the pipeline is a small Python program plus **five Docker services**,
and the machine runs in one of two modes because they do not all fit in memory at once. The
guide explains both. It also lists what the administrator must already have done to the box, so
check that first.

Step 2a asks you to send back a self-test report **before** you build anything. Please do —
it is a five-minute check that catches differences between your machine and ours while they are
still cheap to find.

## 3. Do the work → `docs/P42_External_Experiment_Protocol.md`

What to run, in what order, and how to report it. **Task 0 is reproducing our baseline before
changing anything**, which is what makes every later measurement mean something.

---

## What is here

| | |
|---|---|
| the pipeline | `ask_v2.py`, `retrieve.py`, `ingest_v3.py` |
| measurement tools | `retrieval_recall.py`, `span_specificity.py`, `benchmark.py`, and others |
| the question sets | `questions/`, `census/` — questions, their required claims, and the exact evidence locations |
| the mode scripts | `ops/` — switching the box between answering and loading |
| documentation | `docs/` — read in the order above |

The 145 ECSS source documents are **not** here: they are third-party standards, and a repository
redistributes. `corpus/CORPUS_MANIFEST.tsv` lets you verify you have the identical corpus once
you have downloaded them. The setup guide covers this at Step 5.

## What is not here, and why

**Our system's answers, and our judge's verdicts on them.** That is deliberate. We may ask you to
act as an *independent evaluator* — someone who has not seen our outputs and can therefore judge
them fairly. It is a gap we cannot close ourselves, and it only works if you have not already
read the material.

Tasks 0 to 2 of the protocol need none of it. If an experiment seems to need it, **ask first**
rather than working around it.

## If you get stuck

Every tool has a `--self-test`. Run it. Beyond that: the setup guide ends with a troubleshooting
table covering the failures people actually hit, and the starter kit's last line applies
throughout — **if something is unclear, that is a defect in the document, not in you.** Say so.
