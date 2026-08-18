# Project 42 — starter bundle

Everything you need to run and measure the knowledge base pipeline on your own machine.

**Read `docs/P42_Starter_Kit.md` first.** It assumes no background in AI, search systems or
measurement. Then `docs/P42_External_Experiment_Protocol.md`, which tells you what to do in
what order — starting with reproducing our baseline before changing anything.

## Setting up

```bash
python3 -m venv ingest-venv
./ingest-venv/bin/python -m ensurepip
./ingest-venv/bin/python -m pip install -r requirements-ingest.txt
```

The 145 ECSS source documents are **not** in this bundle — they are third-party standards.
Download them from [ecss.nl](https://ecss.nl) into `corpus/pdf/`, then verify you have exactly
the same corpus we do:

```bash
awk -F'\t' 'NR>5{print $2"  corpus/pdf/"$1}' corpus/CORPUS_MANIFEST.tsv | sha256sum -c
```

Then build the index and check the tools before using them:

```bash
./ingest-venv/bin/python ingest_v3.py --self-test
./ingest-venv/bin/python ingest_v3.py --collection p42_text_v4 corpus/pdf/
./ingest-venv/bin/python retrieval_recall.py --self-test
```

## What is here

| | |
|---|---|
| the pipeline | `ask_v2.py`, `retrieve.py`, `ingest_v3.py` |
| measurement tools | `retrieval_recall.py`, `span_specificity.py`, `benchmark.py`, others |
| the question sets | `questions/`, `census/` — questions, their required claims, and the exact evidence locations |
| documentation | `docs/` — start with the starter kit |

## What is not here, and why

**Our system's answers, and our judge's verdicts on them.** That is deliberate. We may ask you
to act as an *independent evaluator* — someone who has not seen our outputs and can therefore
judge them fairly. That is genuinely valuable and it is something we cannot do for ourselves.
It only works if you have not already read the material.

If an experiment seems to need them, ask first rather than working around it.
