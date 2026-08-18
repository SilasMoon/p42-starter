# P42 — The Ten Question Classes

**Version 2.0 — 2026-08-14.** What each class tests, why it exists, and a real example from the
**56-question adopted set**. Definitions are from `P42_Design_Pipeline_and_Benchmark.md` v3.13 §6.2;
every example is an actual question, chosen as the **median item by required-claim count** in its class
rather than picked for looking good.

**`n` is the adopted count — the questions that survived two-reviewer adjudication**, from
`census/2026-08-14_135406/scored/adopted_2026-08-14_151129.jsonl`. Class scores are from the benchmark
run of 2026-08-14 (`benchmark/2026-08-14_191139`, `P42_Benchmark_Run_Protocol.md` §9).

> **What changed in v2.0, and why it mattered.** v1.0 was written against the **65 authored** questions
> before the census, and its `n` was the authored count in every class. Three of its ten worked examples
> — `A-MH-0019`, `A-TN-0002`, `A-AD-0010` — are questions **the census rejected**. A document intended
> to explain the benchmark to a reader outside the project was showcasing items the project itself had
> thrown out. Same root cause as standing rule 77: the authored set and the adopted set are different
> populations and one of them is in a different file. Three further examples changed because the class
> shrank and the median moved. v1.0 also quoted `table_numeric` answerability at **3/10**, produced by
> the **retracted** lexical matcher (`P42_Claim_Scoring_Protocol.md` §1) — that figure is gone, not
> restated, and nothing replaces it because §4c was retracted rather than recomputed.

---

## 1. Multi-hop / cross-standard — n=11 · **claim coverage 0.756 · all-required 0.455**

**Tests:** combining evidence from two or more places where neither is sufficient alone. The item
carries two anchored passages and a correct answer needs both.

**Why it exists:** the core engineering behaviour, and campaign 1 had n=9, which was unmeasurable.

**Example — `A-MH-0046`** *(5 required claims — the most demanding class in the set, averaging 5.6)*
> *I am the verification lead at a supplier developing a digital ASIC for a spacecraft payload, and we
> are preparing our documentation package for the upcoming review.*
>
> **At the DEVICE Definition Phase review, what do we have to submit to the customer covering
> verification planning and requirement traceability?**

The answer needs the initial DEVICE VCD per ECSS-E-ST-10-02 Annex B, its required contents, traceability
to system requirements per ECSS-E-ST-10-06 8.2.3, **and** that technical requirements are traceable both
backwards and forwards. Five claims from more than one place; reaching four of five scores 0.80 on
coverage and **zero** on the strict metric.

**This class carries the benchmark's most important number.** Coverage 0.756 against all-required 0.455
is the widest gap in the set: the pipeline usually gets most of a multi-hop answer and rarely gets all
of it.

## 2. Table & numeric reasoning — n=8 · **claim coverage 0.700 · all-required 0.625**

**Tests:** reading a value from a table under the right conditions, and reasoning over it.

**Why it exists:** where the corpus is hardest, and where the first pipeline sat at the floor.

**Example — `A-TN-0026`** *(3 required claims)*
> *I am the procurement quality engineer reviewing printed circuit boards with ENEPIG and ENIPIG surface
> finishes delivered by our board supplier.*
>
> **What are the acceptance criteria and the required measurement method for hypercorrosion of ENEPIG
> and ENIPIG finishes at procurement inspection?**

Two row-and-condition reads — hypercorrosion of ENEPIG is not acceptable, Level I ENIPIG is acceptable
subject to conditions — plus the measurement method, down to 1000× magnification under bright field or
Nomarski DIC. Getting the finish right and the level wrong is a wrong answer.

**Lowest-scoring scored class at 0.700.** Its two zeros were read (§9b): in both the pipeline retrieved
the right table and answered from the wrong row.

## 3. Epistemic boundary detection — n=9 · **claim coverage 0.867 · all-required 0.778**

**Tests:** the evidence chain leaves the corpus, and a correct answer **names the missing document**
rather than inventing content for it.

**Why it exists:** knowing the edge of your own evidence is the single most valuable property of an
engineering assistant. Built from the corpus's own measured dangling references.

**Example — `A-BD-0003`** *(2 required claims)*
> *I am the product assurance engineer at a subcontractor supplying electronic units for a satellite,
> and we are setting up our facilities and procedures before hardware build starts.*
>
> **What are we required to put in place for ESD protection as a supplier of flight hardware, and
> which external standard must we follow?**

The ESD protection programme is in the corpus; **EN 61340-5-1 / ANSI-ESD S20.20 are not**. A correct
answer names them as the governing external standards and does not fabricate their content.

**One failure in this class is worth reading**: `A-BD-0002` returned the cleanroom *definition* instead
of the *classification requirement* naming ISO 14644-1:1999. Two independent runs reproduced it — the
benchmark and the framing measurement (`P42_Question_Generation_Protocol.md` §1d). It is a retrieval
defect, not noise.

## 4. Nuance & applicability — n=7 · **claim coverage 1.000 · all-required 1.000**

**Tests:** *"it depends — and here is what on"*. Tailoring, applicability conditions, scope boundaries,
formally approved deviations.

**Why it exists:** the class where a superficially confident answer is most dangerous.

**Example — `A-NA-0027`** *(1 required claim)*
> *I am a structures engineer on a spacecraft platform, and several primary structure components will
> see cyclic loading throughout the operational life of the mission.*
>
> **What do we have to demonstrate for components that are subject to alternating stresses?**

The demonstration is that degradation of material properties **over the complete mission** stays
**within the specified limits**. Both qualifiers are the requirement; an answer that says "demonstrate
material degradation" has not stated it.

**Perfect score, read before being believed.** Three items in this class were read against their claims
(§9c): the answers restate the claims with their qualifiers intact. On the sample read the 1.000 is
real — but see the ceiling caveat below.

## 5. Ambiguous acronym — n=6 · **claim coverage 0.722 · all-required 0.667**

**Tests:** an acronym with two or more genuine expansions **in this corpus**. The correct answer
resolves it against the governing document, or says which reading is meant and why.

**Why it exists:** built from 99 measured semantic collisions. It tests document-scoped reasoning rather
than most-common-expansion guessing — a real property of ECSS turned into a test asset.

**Example — `A-AX-0006`** *(1 required claim)*
> *I am putting together the TCS documentation package for our satellite ahead of the design review.*
>
> **What does the TCS interface control document have to cover?**

`TCS` has more than one expansion in the corpus. The answer must cover TM/TC interfaces and the list of
on-board and ground control parameters — the reading the context selects.

**The class did its job.** `A-AX-0001` scored 0.00 because the pipeline resolved **SEP** to *System
Engineering Plan* when the claims concern *Single Event Phenomena* and radiation analyses. The answer
was fluent, cited, and about the wrong subject — precisely the failure this class exists to expose.

## 6. Definitional & factual — n=5 · **claim coverage 1.000 · all-required 1.000**

**Tests:** what a term means, what a clause requires.

**Why it exists:** the bread-and-butter case. Not trivial: definitions in ECSS are scoped, and the scope
is usually the point.

**Example — `A-DF-0008`** *(1 required claim)*
> *I am a ground segment engineer putting together the operations data deliverables for our satellite
> programme.*
>
> **When a deliverable is labelled as mission information, what is that term defined to cover?**

The answer is the defined extent — space **and** ground segment, pre-launch **and** post-launch. A
partial definition is a wrong answer, not a short one.

**Every item in this class carries exactly one required claim**, so its score can only take the values
0.0, 0.2, 0.4, 0.6, 0.8 or 1.0. Read the ceiling caveat below before treating 1.000 as headroom.

## 7. Identifier & sanity — n=3 *(at the §7 floor)* · **claim coverage 1.000 · all-required 1.000**

**Tests:** document codes, abbreviations, and workmanship criteria stated as plain facts.

**Why it exists:** a sanity check only. It was saturated at 0.81–0.88 in campaign 1 and consumed 10% of
the set, so it is deliberately small here. **A perfect score is the expected result, not a finding.**

**Example — `A-ID-0003`** *(3 required claims)*
> *I am a quality inspector reviewing hand-soldered harness terminations on flight hardware during
> manufacturing.*
>
> **What does an acceptable hand-soldered wire termination in a solder cup have to satisfy?**

Three concrete criteria: a fillet between conductor and cup entry slot, following the contour of the
opening, with the wire touching the bottom of the cup.

## 8. Adversarial & false premise — n=2 *(BELOW the §7 floor — measured, not scored)*

**Tests:** the question embeds a false inference or an unsupported premise, and a correct answer has to
**reject the premise** rather than answer around it.

**Why it exists:** tests whether the system resists a confident framing. A pipeline that agrees with a
plausible-sounding engineer is worse than one that says nothing.

**Example — `A-AD-0001`** *(1 required claim)*
> *I am the RAMS engineer on a spacecraft avionics unit and we are aligning terminology across our
> dependability analyses before the design review.*
>
> **Our reliability lead treats a fault as simply a failure that has already occurred, so can we use the
> two terms interchangeably in the FMECA?**

The premise is false: a fault is *a state of an item characterized by an inability to perform as
required*, and it can exist without a prior failure.

**This item is the clearest evidence that claim coverage is the wrong instrument for this class.** The
pipeline refused the premise correctly — fault and failure are not interchangeable — and still scored
**0.00**, because it never stated the definition that is the required claim. Design §8's
**false-premise-acceptance** metric is the right one for `adversarial` and is not computed in this
campaign. The class is unscored, so nothing propagated.

**Two questions against a floor of 3**, so under `P42_Question_Generation_Protocol.md` §7 it is reported
as measured but not scored, and is registered for a proper campaign-3 draw.

## 9. Acronym paired-variant probe — n=3 *(at the §7 floor, carries no weight by design)*

**Tests:** the same question in acronym form and expanded form, to measure whether the **generation**
path treats them differently.

**Why it exists:** dual-payload ingest makes retrieval invariance structural, so this probes generation
only — where 3 of campaign 1's 7 measured fabrications occurred. It is a probe measured at gate 10(b),
**not a capability score**, and it carries no weight in the operational score by design.

**Example — `A-AP-0002`** *(3 required claims)*
> *I am the structures analyst preparing the modal survey test correlation for our spacecraft, working
> from the reference FEM used in the analysis campaign.*
>
> **What are the requirements on the reduced FEM and on how it is derived from the reference FEM for
> modal survey test correlation?**

The paired variant asks the identical question with *finite element model* written out. Any difference
in the answers is the measurement.

## 10. Applicability & authority — n=2 *(BELOW the §7 floor — measured, not scored)*

**Tests:** does this requirement apply here; which standard governs when two appear to differ; what does
tailoring permit.

**Why it exists:** a reviewer's point in v2.0 — for engineering use this matters more than another
twenty simple facts.

**Example — `A-AA-0013`** *(1 required claim)*
> *I am the structures analyst on a spacecraft development programme and I need to set up the exchange
> of model data with the thermal control and optical subsystems.*
>
> **What are the acceptable means of transferring data and interfacing software between the structural
> subsystem and other subsystems such as thermal control and optical?**

The acceptable means are standard-based or direct electronic interfaces, or applicable documents — a
question about what is *permitted*, which is the shape of the class.

**Two questions against a floor of 3.** Design §6.2 records the decision: published, unscored, and
registered for campaign 3 at 8–10 anchors drawn in the ordinary way rather than two survivors.

---

## How the classes relate

Three of them are **not capability measures** and should never be read as one:

- **Identifier & sanity** is a floor check — near-saturation is the expected result.
- **Acronym paired-variant** is a probe of one failure mode, scored at gate 10(b).
- **Epistemic boundary** rewards a *refusal to answer* from corpus content, so a high score there and a
  low score elsewhere is a coherent, meaningful profile rather than a contradiction.

The remaining seven carry the weighted score, and the weights are in design §6.2 — signed off
2026-08-14, with the **unweighted macro score as the headline** because class sizes now run from 11 down
to 2.

## Two things to know before comparing these class scores

**1. The scores track claims per item, not only difficulty.** Benchmark §9a:

```
definitional 1.0 claims/item -> 1.000     ambiguous_acronym 1.8 -> 0.722
nuance       1.9 claims/item -> 1.000     table_numeric     4.4 -> 0.700
boundary     2.4 claims/item -> 0.867     multi_hop         5.6 -> 0.756
```

A one-claim item cannot partially fail; a 5.6-claim item usually does. **These seven numbers are not a
difficulty ranking**, and design §8 predicted the mechanism when it warned that claim coverage is
gameable by how finely claims are decomposed. Nothing was reweighted to compensate — that would be
standing rule 47.

**2. Every figure on this page is an upper bound.**

> **Claim coverage is measured by an entailment judge validated at 94% agreement against two
> independent model reviewers' judgements of their own answers (Gemini and GPT,
> `P42_Claim_Scoring_Protocol.md` §7 — not human judgement). On answers that state a requirement but omit its trailing
> qualifier — the governing document, the approving authority, the condition, the place of record — the
> judge accepts the answer 57% of the time (§8). Claim coverage is therefore an upper bound where
> completeness of qualification is concerned.**

This bites hardest exactly where the scores are highest: three classes reported at 1.000 have no room
above them, and the qualifier blind spot is the most likely thing sitting under them.
