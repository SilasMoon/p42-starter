# P42 — Retrieval Diagnosis

**Version 2.2 — 2026-08-18.** Where the benchmark's lost claims actually go. **§13 qualifies every anchor-span figure in this document as an upper bound; read it before quoting any of them.**

**Status: DIAGNOSTIC, not a validated improvement.** Every number here is measured on the **same 56
items that exposed the problem**. Nothing in it may be quoted as an improvement to the pipeline, and the
reason is in §5.

Source data: `benchmark/2026-08-14_191139` (protocol §9) and the adopted set's anchor spans. Retrieval is
deterministic (protocol §10a measured it identical on 56/56), so every experiment below is reproducible
and **none of it required a single LLM call**.

---

## 1. The question

The benchmark scored **0.864** with a clear failure profile: six items at zero, `multi_hop`
all-required at 0.455. That does not by itself say whether the pipeline **could not find** the evidence
or **found it and did not use it**. The two have completely different fixes, so the first job is to tell
them apart.

Every adopted item records the **anchor spans** its claims were extracted from — the document and clause
a correct answer must draw on. Each benchmark record stores the 10 context passages actually handed to
the model. Comparing the two answers the question directly.

## 2. The pipeline is retrieval-limited, not generation-limited

Items grouped by how many of their anchor spans reached the 10-slot context:

| anchor spans in context | items | mean claim coverage |
|---|---:|---:|
| **all present** | 45 | **0.936** |
| some present | 5 | 0.717 |
| **none present** | 6 | **0.167** |

**When the right passage reaches the model, the model uses it.** 0.936 against 0.167 is not a subtle
difference, and it holds across classes.

**Five of the six zeros had no anchor span in context at all.** The sixth, `A-TN-0024`, had its anchor
and still scored zero — the CIDL/ABCL row of a table whose CMP row was answered instead.

`multi_hop` shows the same thing item by item, and it explains the class:

```
2 of 2 anchors in context  ->  coverage 0.86, 1.00, 1.00, 1.00, 0.86, 0.88
1 of 2 anchors in context  ->  coverage 0.29, 0.50, 0.80, 1.00, 1.00
0 of 2 anchors in context  ->  coverage 0.00
```

A missing hop is not always fatal — ECSS repeats itself, so a requirement sometimes appears in a
document the retriever did reach — but the low scores in the class are concentrated exactly where a hop
is missing.

## 3. It is a recall problem, not a ranking or context-width problem

Twelve anchor spans never reached the context. Where were they in the candidate pool?

| | |
|---|---:|
| retrieved in the top-50 but lost before the 10-slot cut | **2 of 12** |
| **never retrieved at all** | **10 of 12** |

**Widening the context would fix almost nothing.** The two that were retrieved sat at ranks 45 and 45 —
`CONTEXT_K` would have to more than quadruple to catch them, and that spends context on 35 passages
nobody needs. The dense retriever simply never proposed the other ten.

## 4. Two changes recover two thirds of the loss

Both tested through the **real** path — `retrieve()`, then the cross-encoder over the whole pool, then
de-duplication, then the 10-slot cut — so these are final context positions, not dense ranks.

| configuration | anchors recovered into the context, of 12 |
|---|---:|
| baseline: `TOP_K=50`, query = `prompt_as_typed` | **0** |
| `TOP_K=200`, query = `prompt_as_typed` | **4** |
| **`TOP_K=200`, query = the QUESTION ONLY** | **8** |

**The cross-encoder is not the problem.** Once a passage is in the pool the reranker puts it near the
top — of the eight recovered, five land at context position 1 or 2. The candidate pool is what fails.

**The persona sentence is diluting the query.** Retrieval currently embeds the whole `prompt_as_typed`,
which opens *"I am the verification lead at a supplier developing a digital ASIC…"*. That is a third of
the text and it is about a role, not about the requirement. Dropping it from the **retrieval** query
alone doubles the recovery, from 4 to 8.

This is consistent with something already on the record and previously unexplained: the framing
measurement found the context sentence changed the retrieved passage set in **all 20** items, mean
overlap 0.37 (question protocol §1d). It was measured there as a curiosity. It is a defect.

**Note what this does *not* propose.** The question put to the pipeline stays `prompt_as_typed` — that
is fixed in benchmark protocol §1a and tied to the census's reference standard. The proposal is to
**retrieve on the question and generate with the full prompt**, which changes an internal, not the
stimulus.

## 5. Why none of this is an improvement yet

**These twelve items are the ones that exposed the defect.** Choosing `TOP_K` and a query form by
watching which values recover them, then re-running the benchmark on the same 56 items, would report a
gain that is partly memorisation of this set. That is the failure the campaign's own rules exist to
prevent, and design §9 already prescribes the remedy — **Development / Frozen / Challenge splits**,
which campaign 2 does not have.

So the honest status is: **a mechanism is identified and a candidate fix is measured on the diagnostic
set.** Turning it into a claim requires held-out items.

**Also not established:**

- **That recovering an anchor yields the claim.** The 0.936 figure makes it likely, not certain. `A-TN-0024`
  had its anchor and scored zero.
- **The four that do not recover** — `A-AD-0001`, `A-AX-0002`, `A-MH-0007`, `A-MH-0046`. Two of them
  scored 1.00 anyway from other passages, so the anchor was not needed. The other two are unexplained
  and are the more interesting cases.
- **The cost.** `TOP_K=200` is a 4× larger cross-encoder load — seven rerank batches instead of two, on
  a pipeline already at 30–39s per item. Unmeasured here.
- **Whether question-only retrieval hurts anything.** It was tested only on the twelve failures. It could
  plausibly *lose* passages on items that currently succeed, and that has not been measured. **This is
  the first thing to check before adopting it**, and it needs the other 44 items, not these twelve.

> **Three of the four gaps above have since been measured. The list is kept as written** — it is what
> was known before §§7–9 ran, and deleting it would hide that the questions were asked first.
> **Question-only retrieval on all 56 → §8**, and alone it *does* lose a span, which is why configuration
> D pairs it with `TOP_K=200`. **Cost → §8d**, small against generation. **Anchor-to-claim causality →
> §9a**, tested once on `A-BD-0002` and held. The fourth — the four spans that never recover — is
> partly explained in §8c and remains open.

## 6. What to do, in order

1. **Measure the regression risk first.** Re-run retrieval only — no LLM, minutes — over all 56 items
   under each configuration, and count anchor spans reaching context. If question-only retrieval loses
   anchors on currently-passing items, that decides it immediately and cheaply.
2. **Build the splits campaign 2 skipped** (design §9). Without held-out items no retrieval change can be
   claimed as an improvement, only as a diagnosis.
3. **Then, and only then, adopt a configuration** and re-run the benchmark, publishing the before and
   after with the split it was validated on.
4. **Multi-hop deserves its own treatment.** Six of the twelve misses are second hops. A single query
   embedding cannot sit close to two different clauses; per-hop sub-queries are the standard answer and
   the evidence here points straight at it. Campaign-3 work.
5. **`A-BD-0002` is the cheapest concrete win.** Its anchor recovers to context position 1 under both
   changed configurations. Two independent runs reproduced its failure, so it is the clearest single
   before/after case available.

---

## 7. The regression sweep — pre-registered *(v1.1)*

Written before `retrieval_recall.py` was run once. §4 measured only the twelve failures, which can show
a gain and **cannot show a loss**. This measures all 56.

**Metric — anchor-span recall into context.** For each item, the fraction of its anchor spans
(`_anchor.spans`, matched on document code and clause) that appear among the final context passages,
after retrieval, cross-encoder rerank, de-duplication and the `CONTEXT_K` cut. Aggregated as **spans
reaching context over total spans**, with the item counts beside it.

**This is a proxy for claim coverage, and it is named as one.** §2 established that the two move
together — 0.936 against 0.167 — which is why the proxy is usable. It is not the benchmark and it does
not produce a score. **No LLM is called**, so nothing here can be confused with a benchmark result.

**Configurations, fixed here:**

| | `TOP_K` | retrieval query |
|---|---:|---|
| **A — baseline** | 50 | `prompt_as_typed` (the current pipeline) |
| B | 200 | `prompt_as_typed` |
| C | 50 | question only |
| D | 200 | question only |

**Gains and losses are reported separately and never netted into a single number.** A configuration
that recovers 8 spans and loses 6 is not "+2"; it is a different pipeline with a different failure set,
and the campaign's sixth working rule says the six losses get read.

**Decision rule, fixed before the numbers:**

- **Any configuration that loses a span the baseline reaches is not adopted on this evidence.** Losses
  are read individually and reported whatever the net.
- **A clean result does not authorise adoption either.** These are still the 56 items that exposed the
  defect. A clean sweep authorises **building design §9's splits and testing there** — nothing more.
- **No threshold converts this into a verdict**, and no configuration is chosen by which number is
  largest. The output is evidence for a decision the PoC lead takes in the open.

**What would kill the proposal outright:** question-only retrieval losing anchor spans on items that
currently pass. That is the specific risk §5 named as untested, and it is why this sweep exists.

## 8. The sweep, as measured *(v1.2, 2026-08-14)*

`retrieval/2026-08-14_203025`, by `retrieval_recall.py` v1.0 (20 assertions). 56 items × 4
configurations, 362s, **no LLM call**.

| configuration | spans reaching context | items with all spans | items with none |
|---|---:|---:|---:|
| **A — baseline** | 55/67 | 45/56 | 6/56 |
| B — `TOP_K=200` | 58/67 | 48/56 | 4/56 |
| C — question-only | 61/67 | 50/56 | 2/56 |
| **D — `TOP_K=200` + question-only** | **63/67** | **52/56** | **2/56** |

**Gains and losses against the baseline, separately, per §7:**

| | recovered | **lost** |
|---|---:|---|
| B | +4 | **−1** — `A-NA-0025`, ECSS-Q-ST-70-31 4.3.2 |
| C | +7 | **−1** — `A-MH-0033`, ECSS-Q-ST-70-01 5.4.1.2.1 |
| **D** | **+8** | **none** |

### 8a. The finding that matters: the two changes only work together

**Each change alone causes a regression. Together they cause none.** Widening the pool to 200 gives the
cross-encoder more competitors and it drops `A-NA-0025`'s span; retrieving on the question alone at
`TOP_K=50` never proposes `A-MH-0033`'s. Each one's loss is covered by the other: the cleaner query stops
the wider pool from crowding the right passage out, and the wider pool catches what the narrower query
missed.

**On this evidence the two are adopted together or not at all.** That is not a preference — the sweep
measured both single changes and both lose something the pipeline currently gets right.

### 8b. Four of the six zeros recover completely

`A-AX-0001`, `A-BD-0002`, `A-MH-0022` and `A-TN-0005` all scored **0.00** in the benchmark with **no**
anchor span in context. Under D, every one of them has its **complete** anchor set. That includes the two
most diagnostic failures in the campaign: the **SEP acronym collision**, and `A-BD-0002`, whose cleanroom
classification failure two independent runs reproduced.

**What this does not say is that they would now score above zero.** §2's 0.936 makes it likely; only a
benchmark run on held-out items can establish it, and that run is not authorised yet.

### 8c. What remains unreached, and a pattern in it

Four spans still never arrive, and **two of them are definitions from the same document**:

| item | span | benchmark coverage |
|---|---|---:|
| `A-AD-0001` | **ECSS-S-ST-00-01 | 2.3.92** (*fault*) | 0.00 |
| `A-AX-0002` | **ECSS-S-ST-00-01 | 2.3.126** | 1.00 |
| `A-MH-0007` | ECSS-Q-ST-80 | 6.3.6.1 | 0.50 |
| `A-MH-0046` | ECSS-E-ST-10-06 | 8.2.3 | 0.80 |

**ECSS-S-ST-00-01 is the glossary**, and its `2.3.x` term definitions are not being retrieved even at
`TOP_K=200` with a clean query. Two cases is a pattern worth naming, not a conclusion — but it is a
different failure from the rest, and it is the one that costs `adversarial` its only item. `A-AX-0002`
scored 1.00 without its span, so a missing glossary definition is not automatically fatal.

### 8d. The latency objection, largely answered

§5 flagged the 4× rerank load as an unmeasured cost. The whole sweep — 224 retrieve-and-rerank passes,
half of them at `TOP_K=200` — took **362s, about 1.6s per item-configuration**. Against a pipeline
spending **30–39s per item** on generation, the added rerank cost is small. Measured as a sweep average
rather than per configuration, so it bounds the cost rather than pricing it exactly.

### 8e. What follows, and what does not

**§7's decision rule applies unchanged, and it was written before these numbers existed:**

> A clean result does not authorise adoption. These are the 56 items that exposed the defect.

**So: `ask_v2.py` is not modified, and configuration D is not adopted.** What the sweep establishes is
that the leading candidate **survives the test designed to kill it** — it takes nothing away — and that
the two changes are a package. That is now enough to justify the real work: **build design §9's
Development / Frozen / Challenge splits, and measure D there.** Adopting it on these 56 would report a
gain partly memorised from the items that produced it.

## 9. The single-item probe — pre-registered *(v1.3)*

Written before it ran. **`A-BD-0002` only**, chosen before the result as the clearest case in the
campaign: it scored **0.00** in both benchmark runs, its failure mechanism was read and reproduced
independently (question protocol §1d), and §8b puts its complete anchor set in context under
configuration D.

**The one assumption under test.** §2 shows that items whose anchors reach context score 0.936 and
items whose anchors do not score 0.167. Everything in §6 and §8e rests on that association holding
**causally** for a given item — that putting the passage in front of the model actually produces the
claim. This tests it once.

**Method.** The real `ask_v2.answer()` path, with `retrieve` and `rerank` substituted at run time so
retrieval and reranking use the **question only at `TOP_K=200`**, while generation receives
`prompt_as_typed` and the real system prompt. `ask_v2.py` is **not edited**. Scored by the accepted
judge, as the benchmark scores.

**What n = 1 can do:** falsify the assumption cheaply. If the anchor is in context and the claim still
does not appear, §2's association is not causal for this item and §6's plan needs rethinking before any
split is built.

**What n = 1 cannot do:** support adoption, estimate a gain, or generalise. **A pass here changes
nothing about §8e** — configuration D still is not adopted and still needs held-out items. One item
chosen for being the clearest case is the weakest possible evidence for a positive claim and a
perfectly good one for a negative.

**Reported either way**, with the answer text, on the record beside the two runs that scored it zero.

### 9a. The probe, as measured *(v1.3, 2026-08-14)*

Both conditions run back to back, same judge record, same settings.

| | anchor in context | claim coverage |
|---|---|---:|
| **A — baseline, as the benchmark ran it** | **0 of 1** | **0.00** |
| **D — `TOP_K=200` + question-only retrieval** | **1 of 1** — ECSS-Q-ST-70-01 5.3.1.4 | **1.00** |

> **A:** *"The airborne controlled environment used for spacecraft integration is required to be a
> cleanroom, in which the concentration of airborne particles is controlled… \[ECSS-Q-ST-70-02 | 3.2.2]"*
>
> **D:** *"The airborne controlled environment used for spacecraft integration **shall be classified
> according to ISO 14644-1:1999** \[ECSS-Q-ST-70-01 | 5.3.1.4]."*

**The assumption was not falsified.** The passage reached the model and the model stated the claim, with
the governing clause cited correctly — the required claim almost word for word.

**Note what the failing answer looks like**, because it is the reason this failure mode is worth the
effort: the baseline answer is **fluent, correctly cited, and true**. It is not a refusal, not a hedge
and not a hallucination. It answers a *different question* — defining a cleanroom instead of stating how
one is classified — and nothing about its surface would tell a reader it had missed the requirement.
Claim-level scoring against an anchored ground truth is what catches that; a fluency or
citation-presence check would pass it.

**This does not move §8e.** n = 1, on the item selected as the clearest case in the campaign.
Configuration D remains unadopted, `ask_v2.py` remains unmodified, and held-out items remain the
prerequisite. What the probe buys is that the plan in §6 is no longer resting on an untested causal
step.

## 10. How configuration D gets validated — pre-registered before the set exists *(v1.4)*

**PoC-lead decision, 2026-08-14: the held-out items are drawn fresh in campaign 3. The adopted 56 are
not split.** Design §9 assumes ~50 / ~50 / ~25; 56 items split two ways puts nearly every class below
the floor of 3 in each half, so it would buy statistical independence by making every per-class figure
unusable. The 56 cost two reviewers and 230 claim adjudications, and they are the campaign's headline
measurement. They stay whole.

This section is written **before the validation set exists**, which is the strongest form of
pre-registration available: the adoption criterion cannot be shaped by the items, because there are none
yet.

### 10a. Two metrics, and the cheap one is the primary

**Primary — anchor-span recall, paired, NO LLM.** Exactly what `retrieval_recall.py` measures: does the
anchor span reach the context. It needs a question and its anchor spans and nothing else.

**Confirmatory — claim coverage, paired, judged.** The benchmark's own metric, which is what anyone
actually cares about, and which §9a has now shown follows the primary at least once.

**The primary needs no census at all, and that is the point.** Anchor-span recall requires anchors and a
question that passes the model-free validator — **not** two-reviewer claim adjudication. So the
retrieval-validation set is **substantially cheaper to build** than the benchmark set was, and can be
larger for the same effort. Only the confirmatory subset needs the census.

**One caveat on that, stated now:** an un-censused question may be ambiguous or badly scoped, and a bad
question is hard to retrieve for. The model-free validator (`question_gen` §3) is therefore mandatory
for the primary set, and any item failing it is dropped by name rather than carried.

### 10b. How many items — computed, not guessed (rule 76)

From the diagnostic set: **7 of 56 items gain anchor spans** under D, of which 2 already score 1.00 and
have no room to improve, leaving **5 of 56 able to gain coverage**, at a mean gain of about **0.88**
(from 0.058 to the anchor-complete mean of 0.936). Simulated paired bootstrap, 95% CI excluding zero:

| n | power, anchor-span recall | power, claim coverage |
|---:|---:|---:|
| 20 | 0.27 | 0.10 |
| 40 | 0.75 | 0.43 |
| **56** | **0.95** | 0.75 |
| **80** | 0.99 | **0.94** |
| 120 | — | 0.99 |

**Registered sizes: n ≥ 56 for the primary, n ≥ 80 for the confirmatory.** Twenty items — the size of
the framing run — would resolve **nothing**, at power 0.10 on coverage. That is rule 76 applied in
advance rather than discovered afterwards.

**The assumptions, and they are the weak part.** Both columns assume the held-out items fail retrieval at
the same rate as these 56 and gain by the same magnitude. Both rates are estimated from a handful of
items — 7 and 5 respectively — so they carry wide uncertainty of their own, and a held-out set that
happens to be easier will need more items, not fewer. **If the observed mover rate on the held-out set
is materially below 12.5%, the power table is void and the honest report is "underpowered", not a null.**

### 10c. The decision rule, fixed now

- **Any loss disqualifies.** A configuration that drops an anchor span the baseline reaches is not
  adopted, whatever it gains, and every loss is read individually (§7, unchanged).
- **Material means the paired 95% bootstrap CI excludes zero** — inherited verbatim from the framing
  measurement's §1c rather than re-chosen (rule 60).
- **Both metrics are reported whatever they show**, and a primary that passes with a confirmatory that
  does not is reported as exactly that, not resolved in favour of either.
- **A null is reported as "no measurable effect at n = N"**, never as "the change does not help" — the
  same wording rule the framing run is held to.
- **`TOP_K` and the query form are frozen at configuration D as defined in §8**, and are not re-tuned on
  the held-out set. Tuning there would convert the held-out set into a second diagnostic set and leave
  the campaign with none.

---

## 11. The held-out test — configuration D is REJECTED *(v2.0, 2026-08-16)*

`retrieval/2026-08-16_173209`. The campaign-3 frame: **111 items, 117 anchor spans**, drawn with every
campaign-2 chunk excluded and verified at 0 overlap. **D was diagnosed on campaign 2 and has never seen
these items.** No LLM calls.

| configuration | spans reached | items complete | vs baseline |
|---|---:|---:|---|
| **A baseline** | **99/117** | **94/111** | — |
| B `TOP_K=200` | 100/117 | 95/111 | +3 / **−2** |
| C question-only | 95/117 | 90/111 | +5 / **−9** |
| **D — both** | **97/117** | **92/111** | **+6 / −8** |

**Lossless configurations: NONE.** D reaches **fewer** spans than doing nothing.

**On campaign 2, D was +8 with no losses. On held-out data it is net negative.** §7's rule — *any
configuration that loses a span the baseline reaches is not adopted* — was fixed before these numbers
existed and disqualifies it. **`ask_v2.py` stays unmodified.**

### 11a. Why — and the mechanism is clean

The losses are not scattered. Six of C's nine and five of D's eight are **`definitional`** items, and
their clause numbers are the terms-and-definitions sections: `3.2.2`, `3.2.4`, `3.2.13`, `3.2.15`,
`3.2.45`, `3.2.1.6`, `3.2.1.16`.

**The persona sentence this diagnosis called noise is doing real work: it disambiguates which
document's definition is meant.** ECSS defines the same term in many standards. *"I am a thermal
engineer working on…"* selects the right one; strip it and retrieval lands on another document's
definition of the same word.

The gains confirm the same mechanism from the other side — they fall on `adversarial`, `boundary`,
`identifier` and `multi_hop`, which are **requirement** lookups where the persona genuinely is noise.

**Campaign 2's corpus could not show this.** At 88 documents there were too few colliding definitions;
at 145 the effect dominates. §8c's residual — *"two of the four still-unreached spans are `2.3.x` term
definitions from ECSS-S-ST-00-01, the glossary"* — was this signal, below the resolution of that set.

### 11b. What this establishes, beyond the configuration

**A change that was clearly good on the data it was diagnosed on is net negative on data it had not
seen.** Adopting D on campaign 2's evidence — +8 spans, zero losses, four of six benchmark zeros
recovered — would have made the pipeline worse with no way to detect it.

**This is the first time the campaign has used the benchmark to reject something**, and it is the
argument for held-out sets made concretely rather than in principle. §5 of this document declined to
call D an improvement on exactly this reasoning, before there was any evidence it would fail.

**No variant of D is proposed here.** Tuning around these eight losses would convert the held-out set
into a second diagnostic set, which §10c forbids and which is the whole failure mode the set exists to
prevent.

### 11c. What survives, and the hypothesis it generates

**The diagnosis in §2 is untouched:** retrieval remains the bottleneck — items whose anchors reach
context score 0.936, items whose anchors do not score 0.167. What is refuted is one specific fix.

**New hypothesis, registered and NOT tested here: the query form should be class-dependent.** Strip the
persona for requirement lookups, keep it for definitional ones. `retrieve.py` already routes by query
type, so it is a natural place to carry the distinction. **It is a new hypothesis generated by this
run's losses and must not be evaluated on this set** — it would need its own held-out draw, or it is
tuning on the data that suggested it.

---

## 12. §7's adoption rule — AMENDED 2026-08-18, before the amending evidence existed

**§7 said: *a configuration that loses a span the baseline reaches is not adopted on this evidence*.**
That clause is withdrawn as a general rule. It is replaced, and the replacement is written **before the
held-out sanity check has been run**, so it governs numbers nobody has seen.

### Why the old clause fails

**It cannot be satisfied by any real improvement.** Any change to ranking reshuffles results; something
always moves down. A rule requiring pure gains does not make adoption cautious, it makes adoption
impossible, and a pipeline that can never change cannot be improved.

**And it never did the work anyway.** Configuration D was **+8 / −0 on campaign 2 — perfectly
lossless** — and passed this clause cleanly. On held-out data it went **net negative**. The losses
clause has not once caught a bad configuration; **the held-out requirement caught the only bad
configuration the campaign has had.** The clause was guarding a door nobody used.

### The replacement

Adoption of a retrieval configuration requires **all** of:

1. **A design argument that does not depend on the measurement** — what the change is, why it should
   work, and what it costs. A change adopted only because a number moved is a number chased.
2. **No loss with a systematic mechanism.** Every lost span is **read individually**. A loss that
   reveals a pattern — a document class, a clause family, a query type — disqualifies **regardless of
   the net**, because it predicts failures the sample did not sample. A loss with no mechanism, in a
   document where another span was gained, is reshuffling.
3. **A stated resolution.** The measurement must say **what size of effect it could have detected**
   (rule 76). Where it could not resolve the effect, that is **disclosed and the adoption rests on 1
   and 2**, never on an underpowered number presented as support.
4. **The effect is measured where it is visible.** Anchor-span recall cannot resolve a change of a few
   spans; claim coverage on a full benchmark run can. Adoption schedules that measurement rather than
   substituting for it.

### What this is not

It is **not** a relaxation to let a specific result through. The result that prompted it — BGE-M3
lexical weights, **+3 / −1** — **does not pass on its numbers under the old rule or the new one.**
Under the new rule it is adopted on **clause 1**, with clause 3 disclosing that **the measurement was
incapable of resolving it**: 4 of 117 spans moved, exact two-sided p = 0.625, and roughly **600 spans**
would be needed to reach significance at that ratio. **The amendment does not convert a failing number
into a passing one. It stops a number that means nothing from being treated as though it did.**

---

## 13. Every anchor-span figure in this document is an UPPER BOUND — found 2026-08-18

**This section was written after the figures above, and it qualifies all of them.** It is not a
retraction: the mechanisms in §§6–9 stand, and the association in §2 stands. What changes is how sharp
the counting was.

### 13a. The defect

Anchor-span recall asks: *did a chunk carrying the anchor's `(doc, clause)` reach the 10-slot context?*
That question is exactly as sharp as the `clause` label, and **nobody had ever asked how many chunks
share one.** They do, in bulk. The ingester keeps the last clause number it successfully parsed and
applies it to every following section whose heading does not itself parse as one:

```
ECSS-E-ST-40      475 of 825 chunks labelled 5.11.5.6   (Annex A, <4> Conventions, R.2 Tailoring, H.1.1)
ECSS-E-ST-20-40   284 of 462 chunks labelled 6.2        (every one a row of Table 6-2)
ECSS-Q-ST-60-03   181 of 300 chunks labelled 9.2
ECSS-E-ST-10      249 of 379 chunks labelled 7          (including <1> Introduction)

90 of 145 documents have a dominant label covering >20% of their chunks.
```

Registered as **R85**. It is an ingestion defect, not a defect in the question sets — the anchors are
right about where the answer lives; the *index* cannot tell that location from half the document.

### 13b. What it does to the figures

For a span sitting on a sticky label, *"the anchor reached the context"* is satisfied by retrieving
**almost any chunk of that document**. The span is not wrong. It is **cheap**. `span_specificity.py`
(R84, 19 assertions) bands every span by the fraction of its document carrying its label — bands fixed
on the mechanism before any frame was measured — and reports:

| frame | spans | specific ≤5% | loose | degenerate 20–50% | free >50% | **cheap** |
|---|---:|---:|---:|---:|---:|---:|
| campaign 2, the 56 items used throughout this document | 67 | 50 | 5 | 6 | 6 | **12 (18%)** |
| R10b held-out | 64 | 48 | 8 | 4 | 4 | **8 (12%)** |

So **§8's `55/67 → 63/67` sweep, §2's reached/not-reached split and §11's held-out rejection of
configuration D were all computed over a denominator in which roughly one span in five is nearly free.**
Every such figure is an upper bound on how precisely retrieval found the passage.

### 13c. What survives, and what does not

**Survives.** The direction of §2's association is if anything *understated*: a cheap span can be
counted "reached" when the specific passage never arrived, which puts genuinely-unserved items into the
high-scoring group and pulls 0.936 **down**. The §9a causal probe survives untouched — it was verified by
reading the answer, not by the label. The 10-of-12 never-retrieved finding survives: those spans were
absent from a 200-candidate pool, which no labelling slack can manufacture.

**Does not survive as stated.** Any *level* — 55/67, 63/67, 61/67 — reads as more precise than it is,
and the +3/−1 and +0/−1 deltas below are differences between two upper bounds.

### 13d. The rule from here

Any anchor-span figure ships with its cheap count beside it, in the same sentence, the same way §8's
qualifier caveat ships with every claim-coverage figure. `span_specificity.py --frame <file>` produces
it and costs no LLM call. **This does not license re-running the campaign-2 figures to "correct" them** —
they are what they are, they are on the record, and R85 is the fix.
