# Project 42 — Design of the Knowledge-Base Pipeline and its Benchmark

**Version:** 3.13 (§6.2 set from the CENSUS — 56 adopted questions, two classes below the floor and shipped unscored by PoC-lead decision; §8 Layer 2 claim matching **retracted and replaced** by the validated entailment judge; weighted score RENORMALISED over the 7 scored classes and signed off; §6.3 unchanged, so tools declaring v3.8 §6.3 remain accurate) · **Date:** 2026-08-14
**Changes from v1.0 (round one):** 19 points adopted, 2 adapted. Two were defects: the corpus algorithm
was not what it claimed to be, and the claim schema could not express a table lookup.
**Changes from v2.0 (round two):** 17 points adopted, 1 adapted. One real defect: **the corpus-coverage
metric let the corpus choose its own denominator**, so the "smaller corpus is better" conclusion did not
follow. Re-measuring showed the fix is circular too — the corpus cannot be justified before the
questions exist. **Corpus size is now provisional and decided by a question-evidence closure test.**
A validation-gates table (§13a) has been added: nothing is generated until the design's assumptions are
measured.
**Changes from v3.0 (round three):** the 83.4% classifier figure reported in round two was **my own
diagnostic error** (self-references from page furniture); correct figures are 12.1% occurrence-level and
21.0% distinct-edge, and the closure numbers are unaffected. Investigating it uncovered a **real defect**:
the clause-2 normative-references parser contributes 2 of 165 distinct edges — it is barely working.
Gate 2 is upgraded from validation to repair. See `P42_Review_Response_v1/_v2/_v3.md`.
**Changes from v3.1 (gate execution).** Gates 1 and 2 have been run and both **PASS**. The clause-2
parser defect is repaired — root cause was not the scan window but `str.find` returning the
table-of-contents entry instead of the clause; distinct normative edges went from **3 to 428**. Gate 1
was found to be **defined against the wrong unit of analysis** (occurrence-level evidence used to judge
an edge-level classifier) and has been re-specified; the concern the reviews actually raised —
informative and handbook contamination — measures at a **0% false-positive rate**, and clause-2
extraction fidelity measures at **precision 0.991 / recall 1.000**. Consequently every corpus figure in
§4.2 is now **measured rather than provisional**, and the corpus is 87 documents from clause 2 alone (90 once v3.5's conditional-normative edges are included), not 35 or 39.
See `P42_Gate_Report_G1_G2.md`.
**Changes from v3.2 (governance).** Gate 1 is now recorded **in two parts** — FAIL as originally
specified, PASS as re-specified — rather than only as a pass. A gate that is re-defined after it fails
deserves suspicion, so the failing result, the diagnosis and the consequence of rejecting the
re-specification are all stated where a reviewer will see them (§13a rows 1 and 1b).
**Changes from v3.3 (acronym handling).** The design had no coherent treatment of acronyms — the one
place it named them, gate 6's "synonym normalisation", was a phrase rather than a specification. Added:
requirement **I9** (harvest clause 3.3 "Abbreviated terms" per document), **§5.4** (where normalisation
is applied and why it must be document-scoped), an **ambiguous-acronym question class**, an exclusion
rule in the §7.3 mutation gate, **gate 10**, and a correction to acronym-error severity that the
campaign-1 evidence contradicted. Measured: 1,451 acronyms over 117 documents, **99 of them genuine
semantic collisions** including `PDR`, `CDR`, `TM`, `TC` and `SW`.
**Changes from v3.4 (round four).** 5 points adopted, 3 adopted with a corrected implementation, 1
rejected; 3 reviewer claims were wrong against source and are corrected in `P42_Review_Response_v4.md`.
Material changes: **gate 1 is re-opened** and re-run under a pre-registered protocol with cluster-capping
(a fresh sample, not a re-label); acronym expansion moves from **query time to ingest time**
(dual-payload chunks), which removes the multi-hop commitment problem entirely; a second edge type
**`conditional_normative`** is added for conformance-phrase obligations that clause 2 omits, moving the
closure to **90 documents**; Track B is marked **EXPERIMENTAL / UNVALIDATED** until a blind SME
comparison; and **no gate may be recorded PASSED without a 5% human spot-audit**.
**Changes from v3.7 (arithmetic, weights and gate criteria).** Four corrections, all found by building
the anchor sampler against the live index and putting its output in front of human reviewers, and none
of them changing the architecture.

1. **§6.2's class-size total was wrong: the column sums to 155, not the 145 printed.** v3.4 added the
   10-slot ambiguous-acronym class and the total was never updated; v3.5's acronym-paired 10→5 with 5
   slots to multi-hop was neutral. The per-class rows are authoritative — each is derived from the
   confidence interval that class needs (L4.8) — so **155 is adopted** and §11's "~135 surviving items"
   becomes **~145**. Nothing about the design changes; one number is corrected.
2. **The published weights covered 7 of the 10 classes.** `applicability_authority` (10),
   `ambiguous_acronym` (10) and `acronym_paired` (5) — **25 items, 16% of the set** — carried no weight
   in the operational score that defines the gate, which also made gate 9's weight-robustness check
   untestable over a sixth of the benchmark. Same signature as (1): classes added without updating the
   aggregates around them. Weights are now stated for all scored classes, and `acronym_paired` is
   **excluded by design and said so** — it is a paired-variant probe, measured by gate 10(b), not a
   capability score. **SIGNED OFF by the PoC lead, 2026-08-14.**
3. **Gate 4 C1's criterion "< 5%, and zero for tables" is unsatisfiable as written.** Requirement I1
   emits a table whole, or divided by rows with its header repeated, so a table above the ceiling is a
   complete matrix and not a fragment. The failure the clause reached for is *a table part that lost
   its header*, which **C5 already measures** (96.8%). The clause is restated to point there.
   **SIGNED OFF 2026-08-14:** C1 is *"chunks at the size ceiling, measured over NON-TABLE chunks,
   < 5%"* — 1.8% (394 chunks) on the current index. The table cap-rate is a **reported property of
   I1**, not a criterion, because a whole table at the ceiling is I1 working correctly.
4. **Gate 4 C2 measures ingest-introduced duplication and is correct as it stands** — but the figure it
   reports (0.32%) is not the whole picture, because hashing `payload["text"]` embeds the breadcrumb,
   so identical bodies in different documents never collide. Body-level duplication measures **5.5%**.
   That is a property of ECSS — standards genuinely repeat text — not something the ingest created or
   can remove, so it is added as a **reported measurement, not a gate criterion**. Gating it would fail
   gate 4 for a fact about the corpus.

Also recorded in this round, in separate documents rather than here: the index was torn down and
rebuilt (`P42_Index_Rebuild_Record.md` v1.0 — gate 4 re-passed 4/4 with all four figures reproducing
exactly, which is the first evidence the ingest is deterministic across a full re-run), and the anchor
draw was audited twice by three independent reviewers (`P42_Anchor_Audit_Report.md` v1.0 — both rounds
ACCEPTED; three defects found that 75 automated assertions did not).

**Changes from v3.6 (execution).** The corpus is **ingested**: 88 documents, 22,138 chunks, ingest
v3.1. **Gate 4 (ingestion quality) PASSES** — chunks at the size ceiling **1.8%** against campaign 1's
27%, duplicates 0.32%, table headers 96.8%, acronym dual payload live on 56% of chunks. **Gates 1b and
2 are PASSED WITH AUDIT** — the owed 5% human spot-audits returned **6 of 6** and **7 of 7**. Retrieval
is now **routed by query type** rather than scored by one weight: identifier 100%, definitional 98%
top-3 and 75% rank-1, general 70% same-clause. Two limitations added: **L-3**, one normative reference
in three leaves the ECSS family; and the general-retrieval figure rests on a heading proxy rather than
on real questions.
**Changes from v3.5 (gate 1 closed).** Gate 1 was re-run under pre-registration and then **voided** by
its own human audit (11/15): the two decisive disagreements turned on ECSS knowledge the supplied
evidence did not carry, so gate 1 is a judgement gate that model labellers cannot satisfy at any sample
size. Rather than escalate further, gate 1 is **closed as a measured limitation**. The three mechanical
extensions its false-negative taxonomy identified are implemented — DRD/applicability table rows,
`"(document controlled by X)"`, and coordinated conformance lists — lifting measured recall from
**0.864 to 0.926** and the closure to **93 documents, 88 held**. The corpus is explicitly a **floor**;
gate 3 sets the final corpus. This is a deliberate proportionality call: the corpus error is bounded and
self-correcting, and the campaign had produced no pipeline measurements at all.
**Companion documents:** `P42_Lessons_Learned.md` (the evidence behind every design rule here) ·
`P42_Gate_Report_G1_G2.md` (gates 1 and 2 in full, with reproduction artefacts)

---

## How to review this document

This design is written to be attacked. It is a rebuild, decided after a first benchmark campaign
whose failures are documented in the companion lessons register. If you are reviewing it, the most
useful things you can do are, in order:

1. **Check the claims about ECSS content.** Every normative statement here should be verifiable in
   the cited clause. In the first campaign, an expert-sounding external review was checked clause by
   clause and **5 of its 11 normative claims were wrong**. Please assume the same of this document
   and verify rather than defer.
2. **Attack Section 7 (automated ground truth without human vetting).** This is the highest-risk part
   of the design. If it does not hold, the whole plan fails, because there is no human validation
   budget to fall back on.
3. **Attack Section 5.3 (the answer contract).** It changes what is being benchmarked. There is a
   real argument that it benchmarks a different product from the one users will use.
4. **Look for measurement that measures itself.** The first campaign produced a release where every
   automatic metric improved and answer quality did not move. Ask of every metric here: what would
   make this number rise without the system getting better?
5. **Tell us what we are not testing.** Section 12 lists the gaps we know about. The valuable
   contribution is the ones we have missed.

Where this document says "measured", the number comes from the first campaign: 228 independently
graded answers across three pipeline configurations, plus a reference-graph analysis over 105 ECSS
standards. Where it says "expected" or "target", it is a design intent that has not yet been
demonstrated.

---

## 1. What the system is, in plain terms

A group of space engineers needs to ask questions of the ECSS standards — the European standards that
govern how space projects are run, verified and assured. There are hundreds of documents, they
cross-reference each other constantly, and the answers matter: getting a factor of safety or a
verification method wrong has real consequences.

We are building a **retrieval-augmented question answering system**: the engineer asks a question in
plain language, the system finds the relevant passages in the standards, and an on-premises language
model composes an answer **that cites the passages it used**. Everything runs on local hardware with
no internet connection, because the documents and the questions are sensitive.

The benchmark is how we know whether that system is any good.

---

## 2. Objectives, and what each one demands of the design

The benchmark exists to serve four objectives. They are not the same objective and they pull the
design in different directions, so each is stated with what it requires.

| # | Objective | What it demands |
|---|---|---|
| **O1** | **Debug, improve and tune the pipeline** — ingestion and serving | Failures must be **localised** to a stage. "The score went down" is useless; "we lost four questions to table extraction and two to reranking" is actionable. Requires per-stage measurement and an error taxonomy. |
| **O2** | **Measure answer quality across a wide, varied set of question types** | Requires enough question classes to cover the ways the system can fail, and **enough items per class to measure it** — the first campaign had four classes with fewer than ten items, where a confidence interval is ±0.33 and nothing is measurable. |
| **O3** | **Prove to users the system is trustworthy — extensively tested, no hallucination or fabrication** | Requires **hallucination to be a first-class measured quantity**, not an absence of complaints. Requires the evidence to be inspectable: a user must be able to see why we claim the system is trustworthy. |
| **O4** | **Characterise strengths and weaknesses** | Requires a **reported vector**, not a single number, and honest reporting of the classes where the system is weak. |

**Where they conflict.** O3 wants a stable, frozen, defensible test set. O1 wants a fast, cheap,
iterate-many-times-a-day test set. The design resolves this with **three splits** (Section 9): a
fast development set for tuning, a frozen set for gates, and a held-back challenge set that is never
used for tuning.

---

## 3. Constraints

**C1 — Minimal human involvement.** This is the binding constraint and it shapes everything. There is
no budget for a person to vet questions or grade answers at scale. The generation and evaluation of
the benchmark must be **automated end to end**, with a human involved only in accepting or rejecting
whole batches and in occasional spot audits.

*Consequence:* we cannot rely on a human tiebreaker. Where automated layers disagree, the design must
**discard rather than escalate** (Section 7.4).

**C2 — The assessing assistant stays in the loop.** An AI assistant with access to the source
documents produces the assessment of every run, maintains the records, and proposes the next
experiment. It is not a rubber stamp: in the first campaign this layer found eight defects, including
two in the measurement code itself, and rejected five of eleven items in an external expert review as
factually wrong against the sources.

**C3 — Fully offline capable.** The deployed system runs air-gapped. Any evaluation component that
requires an external service must be clearly marked as a development-phase-only aid, and the design
must state what survives without it.

**C4 — Everything in the pipeline may be changed.** No legacy component is protected.

**C5 — The full ECSS active standards set is available** (152 documents), and more can be obtained.
Corpus size is therefore a design choice, not an availability limit.

---

## 4. Part I — The corpus

### 4.1 The problem with choosing documents by convenience

The first corpus was 23 standards chosen because they were to hand. Measuring the reference graph
afterwards produced the finding that motivated this rebuild:

| Measurement on the first corpus | Value |
|---|---|
| Documents | 23 |
| Distinct ECSS documents normatively invoked but absent | **87** |
| Total dangling references | **633** |
| Share of all inter-document references pointing outside the corpus | **47%** |

ECSS standards define terms and requirements by reference to each other. At 47% dangling, roughly
half of every "see clause X of standard Y" leads nowhere. Any question whose answer depends on
following such a reference is either unanswerable, or answerable only from the model's own training
knowledge — which the system prompt forbids, making a correct answer and a rule violation the same
event.

This was not hypothetical. One question asked for a severity vocabulary; the standard it cited
defines that vocabulary **by deferring to two standards that were not in the corpus**. We graded the
system down on it for three consecutive runs.

### 4.2 The envelope: typed normative closure

**Measured in v3.2. Every number in this section was provisional until gates 1 and 2 ran; they have now
run and both pass.** The figures below replace the 35- and 39-document figures carried in v2.0 and v3.1,
which were computed on a reference graph that contained 3 edges. Those figures are struck, not adjusted.

**Corrected in v2.0.** Version 1.0 said the corpus was defined by "transitive closure" and then used
an algorithm that added any document referenced **at least five times**. A reviewer pointed out that
these are not the same thing, and they were right — it is a frequency heuristic, and a single
normative reference to a definition can matter more than a hundred incidental mentions.

The method follows **typed dependencies**. A reference is followed only if it creates an obligation:

| Edge type | How it is detected | Followed? |
|---|---|---|
| **normative** | the referenced document appears in the citing document's clause 2 "Normative references" list, whose ECSS boilerplate states that these documents "constitute provisions of this ECSS Standard" | **yes** |
| **conditional_normative** *(v3.5)* | not in clause 2, but the target sits **inside a conformance phrase** in a sentence carrying `shall` — *in accordance with · in compliance with · as specified in · as defined in · according to · as per* — with `(see …)` and `(refer …)` parentheticals stripped first | **yes**, typed separately so the manifest reports both |
| **informative** | anything not in clause 2 and not in a conformance phrase — "see also", "for guidance", bibliography, NOTE and rationale contexts | no |
| **handbook / technical memorandum** | target code contains `-HB-` or `-TM-`; ECSS never makes these normative | no |

**Clause 2 is the primary source of normative status, with one measured exception — revised in v3.5.**
v3.4 made clause 2 the *sole* source. A round-four reviewer argued that clause 2 lists are incomplete
relative to body-text obligations and proposed accepting any sentence containing both `shall` and a
document code. Implemented literally that rule admits clear false positives — codes inside `(see …)`
parentheticals, and sentences where the `shall` governs a deliverable rather than the reference. The
**tightened conformance-phrase rule** above was measured instead:

| rule | new edges over the 353 clause-2 edges | quality |
|---|---|---|
| `shall` + code in the same sentence (as proposed) | 18 | contains clear false positives |
| **code inside a conformance phrase, parentheticals stripped** | **9** | all inspected, all legitimate |

Nine edges on a base of 362 is a **2.5% clause-2 omission rate**, measured exhaustively. This supersedes
the 1.3% figure quoted in v3.4, which counted *occurrences* in a 300-item sample rather than *distinct
edges* — the same unit-of-analysis error as gate 1, in the same document. Edge-level is the figure that
matters, because edges are what the closure walks.

#### Measured closure

Starting from the 23 documents currently ingested and following normative clause-2 edges to a fixed
point:

| | value |
|---|---|
| documents with text extracted and parsed | **128** |
| documents with a clause 2 successfully parsed | **116** (the 12 without are 7 adoption notices, 2 glossary/tailoring documents, 1 handbook — none has such a clause) |
| normative edges in the graph | **428** |
| **typed normative closure**, clause 2 only (`--clause2-only`) | **87 documents** |
| **typed normative closure**, all four sources *(v3.6, default)* | **93 documents — 88 held, 5 withdrawn** |
| normative edges by source *(v3.6)* | clause 2 **430** · DRD/applicability tables **20** · "controlled by" **4** · conformance phrase **13** = **467** |
| measured recall of the edge rule | **0.926** (clause 2 alone: 0.864) — below the 0.95 criterion, closed as a limitation |
| dangling normative edges inside the closure | **7 of 389 = 1.8%** (present 23-doc corpus: 75 of 144 = 52.1%) |
| … held and text-extracted | **82** |
| unresolved targets | **5** |
| dangling normative edges inside the closure | **7 of 353 = 2.0%** |
| dangling rate of the present 23-document corpus, same method | **69 of 126 = 54.8%** |

The closure reaches a fixed point in **4 hops**: 23 → 66 → 86 → 87 → 87. Almost all growth is one hop
out from the seed, which says the seed was well chosen but incomplete.

The 5 unresolved targets — `Q-ST-70-07`, `-70-08`, `-70-10`, `-70-11`, `-70-38` — are absent from the
*Active ECSS Standards* holdings, consistent with withdrawal or supersession. They are cited by active
standards, so these are **genuine dangling references in ECSS itself**, not gaps in our holdings. They
are recorded on the declared boundary (§4.3), and no question may depend on them.

**The 2.0% versus 54.8% comparison is the case for rebuilding the corpus rather than extending it.**
More than half of what the present 23-document corpus normatively depends on is not inside it.

#### Corpus size is measured, but still not *final*

The v3.1 position — that corpus size cannot be justified before questions exist — **still holds** and is
not repealed by having a measured closure. What has changed is that the starting point is now derived
from ECSS's own declarations rather than from a heuristic. The final corpus is still decided by tracing
each candidate question's evidence chain and classifying it **GREEN** (fully answerable inside the
corpus), **AMBER** (answerable with a boundary qualification) or **RED** (evidence genuinely missing),
then expanding where RED items cluster — gate 3 in §13a. Corpus selection remains an iterative loop with
question generation, not a phase that completes before it.

#### Limitation, measured rather than asserted

**L-1 — trusting clause 2 exclusively.** Gate 1 measured both sides of this trade on a 300-edge
stratified sample:

| | result |
|---|---|
| handbook and technical-memorandum targets sampled | 32 |
| … wrongly classified normative | **0** |
| edges carrying an explicit informative cue ("see also", "for guidance", "handbook") | 9 |
| … wrongly classified normative | **0** (2 are classified normative and both are clause-2-listed pairs) |
| **false-positive rate on informative and handbook citations** | **0%** |
| normative dependencies imposed in body text but omitted from clause 2 — i.e. missed | **4 of 300 = 1.3%** |

The 0% is structural, not lucky: the parser never reads "see also" prose, so that prose cannot
contaminate it. The round-3 review's proposed remedy — refine the regular expressions to exclude
parenthetical and "see also" contexts — is unnecessary for the same reason. The price is the 1.3% of
body-text-only obligations that are missed; the dominant pattern is a tailoring clause invoking
`S-ST-00` in conformance language. **Consequence for authoring: a question must not depend on a
normative link that exists only in body text.**

**L-3 — one normative reference in three leaves the ECSS family.** Measured across the 88-document
corpus: clause 2 holds **357 ECSS-coded** normative references and **180 non-ECSS** ones — ISO (77
documents), ESCC (43), EN (16), IEC (14), IPC (13), plus MIL-STD, DIN, AMS and NAS. **37 of 88
documents** cite at least one, and two (`Q-ST-60-05`, `Q-ST-60-12`) have clause 2 lists that are
*entirely* non-ECSS, so the closure sees them as having no normative dependencies at all. The extractor
matches ECSS codes only, by design. The consequence is that the **1.8% dangling rate is the INTERNAL
rate**; the rate at which an evidence chain leaves the holdings altogether is far higher. Both are
reported separately from v3.7, and every external reference belongs on the declared boundary (§4.3), so
that the epistemic-boundary question class is built from the whole picture. Found by the project lead
during the gate-2 audit.

**L-2 — occurrence-level and document-level normative status are different questions.** A pair that
clause 2 declares normative routinely appears in the body as a NOTE, a "see also", or a change-record
line; 30 of 300 sampled occurrences (10%) look informative for pairs clause 2 declares normative. Any
future validation that samples *occurrences* to test an *edge-level* classifier will report a false
failure. This was discovered by making exactly that mistake — see gate 1 in §13a and the gate report.

**Reported figures.** The corpus manifest publishes three numbers, not one: **core normative closure**
(87), **extended practical envelope** (the wider set of 128 extracted documents available for optional
inclusion), and the **declared boundary** (everything invoked and deliberately excluded, including the
5 unresolved ECSS-internal dangling targets).

### 4.3 The boundary is a deliberate test asset

Full closure is neither achievable nor desirable — ECSS eventually references ISO, ECSS handbooks and
external standards. So the boundary is made **explicit and machine-readable**: a list of every
document that in-corpus clauses invoke and that we have deliberately not included.

That list is not a gap. It is the source material for a question class we were not testing at all.
The correct answer to a question whose evidence chain crosses the boundary is:

> "Software criticality categories map to function severity via Table D-1, which I can give you. The
> severity definitions themselves are normative in ECSS-Q-ST-30 clause 5.4, which is not in this
> knowledge base."

**Knowing the edge of your own evidence is the single most valuable property of an engineering
assistant in a real project.** With 450 residual references across dozens of documents, we can
generate this question class systematically from the corpus itself, rather than inventing
out-of-scope questions about launchers and satellites — which the first system solved easily,
because the out-of-scope signal was a proper noun rather than a judgement.

---

## 5. Part II — The pipeline

### 5.1 Ingestion

Documents are PDFs with heavy use of tables and figures. Ingestion converts them into retrievable
passages. The first implementation had one defect that invalidated an entire question category.

**The defect, measured.** Passages were capped at 2000 characters with no awareness of structure.
On the live index, **27% of all retrieved passages sat exactly at the cap; 45% for table-reasoning
questions.** Wide applicability tables became header-only fragments. One question retrieved the
correct document at **rank 1 with perfect context precision** and still could not be answered,
because every passage was a table header with no rows. We recorded that as a reasoning failure. It
was an ingestion failure.

**Design requirements:**

| Req | Statement |
|---|---|
| **I1** | **Tables are never split.** A table that exceeds the passage budget is emitted as a single structured passage, with its header repeated if it must be divided by rows. |
| **I2** | Every passage carries **provenance**: document code, revision, clause number, heading trail, page, and element type (text / table / figure-caption / definition). |
| **I3** | **Definitions and abbreviations are indexed as individual units.** In the first campaign, glossary entries ranked 9th because the glossary is one enormous document and its individual entries competed with each other. |
| **I4** | **Cross-references are extracted as structured links**, not left as text. This is what makes the boundary list, the closure computation and the dangling-reference question class possible. |
| **I5** | Every index that is built has a **query path exercised by the benchmark**, or is declared out of scope with a reason. The first pipeline built a visual index that nothing ever queried. |
| **I6** | *(v2.0)* **Chunk on subclause boundaries, not character counts.** ECSS requirements nest deeply (`5.2.2.1`, item `a`, sub-item `1`). Splitting on length orphans a requirement from the condition that qualifies it — "the margin shall be at least 2,0" is meaningless without knowing which function and which model it applies to. |
| **I7** | *(v2.0)* **Prepend the full breadcrumb to every chunk before vectorisation**, not only for display: document, revision, clause path and heading trail. |
| **I9** | *(v3.4)* **Harvest each document's clause 3.3 "Abbreviated terms" into a per-document acronym table**, and index each entry as a retrievable unit (as I3 does for definitions). The clause is present in **117 of 127** documents, so this is nearly free. It must be **per document**: acronyms are not unique across ECSS — see §5.4. |
| **I8** | *(v2.0)* **Index identifiers and clause numbers as structured metadata** for filtering, and produce **sparse (lexical) vectors alongside dense ones**. See 5.2. |

**Ingestion quality gate — passes before any question is authored:**

| Check | First campaign | Target |
|---|---|---|
| Passages at the size cap | 27% | **< 5%, measured over non-table chunks** — restated in v3.8. "Zero for tables" is unsatisfiable under I1: a table above the ceiling is emitted whole and is a complete matrix, not a fragment. The failure that clause reached for is a table part that lost its header, measured by the row below |
| Tables reconstructable from one passage — **the real table-integrity check** | 96.8% (2703/2791) | > 95% |
| Duplicate `(document, clause)` in a retrieved context | 24 of 76 questions affected | < 2% |
| **Body-level duplication across documents** *(v3.8; SIGNED OFF 2026-08-14 as reported, NOT a gate)* | **5.5%** (1222/22134) | none. ECSS repeats text across standards; this is a corpus property the ingest did not create and cannot remove. It is published because it wastes context slots (S1) and makes an anchor's citation ambiguous — but gating it would fail gate 4 for a fact about the corpus |
| Named definition retrievable in the top 5 for its own term | failed (rank 9) | > 95% |

**Rationale for the gate.** Question ground truth is authored against the index. If the index is
corrupted, the ground truth encodes the corruption, and fixing ingestion later invalidates every
anchor. Ingestion first is not a preference; it is a dependency.

### 5.2 Serving

The retrieval path is: embed the question → search the passage index → re-rank the candidates with a
cross-encoder → hand the top passages to the language model → generate a cited answer.

This part of the first system worked and its measurement was sound. Two parameters were tuned on
evidence and are carried forward:

- **Retrieval depth 50** (from 20). Multi-hop evidence recall 0.722 → 0.889, statistically
  significant; cost +0.30 s on a pipeline averaging 17 s.
- **Context width 10 passages** (from 5). Independently graded quality 0.513 → 0.592, paired
  bootstrap +0.079, 95% CI [+0.020, +0.151]. Zeros fell from 24 to 14 of 76.

**Carried-forward requirements:**

| Req | Statement |
|---|---|
| **S1** | De-duplicate by `(document, clause)` before the context cut. Measured waste: 31 slots across 24 questions. Must not be applied to the list used for retrieval scoring, or a generation-family change silently becomes a retrieval-family one. |
| **S2** | The re-ranker is **not deterministic**. Two runs with identical inputs flipped a near-tie and moved a ranking metric by 0.007. This noise floor is measured, recorded, and used in every validity check. |
| **S3** | *(v2.0)* **Hybrid retrieval: dense plus lexical, with metadata filtering.** Dense embeddings place `ECSS-E-ST-10-02C` and `ECSS-E-ST-10-03C` almost on top of each other, which is why our identifier class was weakest and why glossary entries ranked 9th for their own term. When a query contains an explicit document code or clause number (regex-detectable), apply a metadata filter or boost. **Note for reviewers:** one review assumed this needs a second model. It does not — BGE-M3 already emits dense, sparse and multi-vector representations from the same forward pass, so we have been using one third of the model we already run. **Cheap is not the same as effective**, so this is a measured ablation, not an architectural conclusion: dense · dense+sparse · dense+sparse+metadata-filter, reported per question class — gate 8 in §13a. |
| **S4** | Grounding instructions are **identical across every client** — benchmark, command line, chat interface. In the first campaign these drifted apart and one client spent weeks serving a prompt with a known defect. |

### 5.3 The answer contract — post-hoc extraction

**Changed in v2.0.** Version 1.0 proposed forcing the pipeline to emit structured output so that
evaluation could be exact. **Both reviewers independently rejected this**, and they were right. The
objection: constraining a language model to emit JSON changes how it reasons, so you end up
benchmarking a structured-output engine rather than the prose assistant users actually get. One
reviewer added a sharper point — if the model emits its own claim list, **it controls the unit of
evaluation and can influence its own scoring granularity**.

**The design is now:**

```
        SAME PIPELINE, ONE OUTPUT
                   │
        prose answer with inline citations      <- what the user receives
                   │
        independent extractor (not the answering model)
                   │
        evaluation representation: decision · claims · citations · boundary
```

The structured mode is retained as a **development aid only**, because it makes debugging far easier.

**Two extractors, not one — added in v3.0.** Both reviewers identified the extractor as a new single
point of failure: if it misses a claim, a good answer is marked incomplete; if it invents one, the
pipeline is penalised for something it never said. The design now uses **two independent extractors —
one deterministic parser, one model-based** — and reports their **agreement** as part of evaluator
health. Where they disagree, the result is recorded as *extractor uncertainty*, not as a pipeline error.

**Calibration.** A 50-item calibration set with independently verified claim extraction. Note the
arithmetic honestly: **50 items with zero errors bounds the error rate at about 6% at 95% confidence,
so a "≥98% agreement" claim cannot be demonstrated from 50 samples.** The extractor is rejected on ≥2
disagreements, the measured agreement and its confidence bound are published, and samples accumulate
across rounds so the bound tightens — gate 6 in §13a.

### 5.4 Acronym handling — added in v3.4

**The problem.** An engineer asks *"what has to be closed out before PDR?"*. The standard says
*"Preliminary Design Review"*. Nothing in the pipeline connected those two strings — not at retrieval,
not at claim matching, not at grading. A correct answer using the other form would silently lose its
credit, and the failure would look like a knowledge failure rather than a string-matching failure.

**Why a single global dictionary would be wrong.** Harvesting clause 3.3 across the corpus:

| | value |
|---|---|
| documents with an "Abbreviated terms" clause | **117 of 127 (92%)** |
| distinct acronyms | **1,451** |
| definition occurrences | **3,031** |
| acronyms with more than one expansion, raw | **314** |
| … genuinely ambiguous after folding spelling variants | **219** (upper bound) |
| … **semantic collisions** — expansions sharing no words at all | **99** (lower bound) |

The collisions are not exotic. They include the acronyms an engineer uses most casually:

| acronym | competing expansions in this corpus |
|---|---|
| `PDR` | preliminary design review · **product definition review** · point drive residue |
| `CDR` | critical design review · **clock data recovery** |
| `TM` | telemetry · thermal model · Test Method · Technical Memorandum |
| `TC` | telecommand · **thermocouple** |
| `SW` | software · **solar wind** · switch |
| `CI` | configuration item · **critical item** · conformance inspection |
| `MS` | most-significant · mission statement · strength safety margin · mass spectroscopy |
| `SEE` | single event effect · **secondary electron emission** |

A global expansion table would resolve `TM` wrongly about as often as rightly. **Expansion is therefore
scoped to the citing document**, widened to the branch (E / M / Q / S / U) only when the document does
not define the term itself, and left unexpanded when neither does — an unexpanded acronym is a correct
outcome, a wrongly expanded one is a fabrication.

**Where normalisation is applied — three places, and only three:**

| Stage | What happens | Why here |
|---|---|---|
| **Retrieval (query side)** | if the query contains a token in the acronym table, search both forms; the sparse/lexical vector carries the literal token, the expansion widens recall | the engineer's form and the standard's form must find the same clause |
| **Claim matching (grading)** | acronym and expansion are **equivalent** for keypoint matching, scoped to the item's anchor document | otherwise a correct answer loses credit on formatting |
| **Fabrication detection** | expanding an acronym to a form **not** defined in the anchor document or its branch is a fabrication, detectable mechanically against the table | this is the pipeline's most common measured hallucination — see below |

Normalisation is **not** applied when constructing the answer prompt. The pipeline answers in whatever
form the source uses; it is not asked to expand or contract anything.

**Severity correction.** v3.3 stated that "a wrong acronym expansion is usually minor". The campaign-1
evidence contradicts this: of the **seven** recurring fabrications enumerated and source-verified,
**three were acronym errors** — one review acronym expanded wrongly and two expansions invented
outright. It is the single most frequent hallucination mode this pipeline exhibits. Severity is
therefore assigned by consequence, not by category: an expansion that names a **different engineering
artefact** (`PDR` as product definition review, `TC` as thermocouple) is `major`, because it changes what
the engineer does; a spelling or word-order variant of the correct expansion is `minor`.

## 6. Part III — What the benchmark measures

### 6.1 The capability model

An answer can be wrong in several independent ways, and lumping them together destroys the diagnostic
value (objective O1). We measure six capabilities separately:

| Capability | Question it answers | How it fails |
|---|---|---|
| **Retrieval** | Did the right evidence reach the system? | the clause is never found |
| **Evidence sufficiency** | Was the retrieved evidence *enough* to answer? | the right table is found with its rows truncated |
| **Grounding** | Does the answer follow from the evidence it was given? | the answer contradicts a passage in its own context |
| **Reasoning** | Were multiple pieces of evidence combined correctly? | the two hops are found, the inference is wrong |
| **Qualification** | Is the answer correctly hedged, scoped and conditioned? | a conditional requirement is stated as universal |
| **Honesty** | Does it refuse, or flag the boundary, when it should? | it invents a plausible value |

**Evidence sufficiency deserves emphasis.** It is the capability that separates "the pipeline
reasoned badly" from "the chunker destroyed the evidence". Without it, ingestion defects are recorded
as model failures — which is exactly what happened in the first campaign.

### 6.2 Question classes

Sizes are derived from the confidence interval we need, not from what happens to get written
(lesson L4.8). Target ±0.18 or better on the classes that drive decisions.

| Class | n | ±95% CI | What it tests | Why it exists |
|---|---|---:|---|---|
| **Multi-hop / cross-standard** | 35 | ±0.18 | combining evidence from two or more documents where neither is sufficient alone | the core engineering behaviour; was n=9 and unmeasurable |
| **Nuance & applicability** | 20 | ±0.22 | "it depends — and here is what on": tailoring, applicability conditions, scope boundaries, formally approved deviations | the class where a superficially confident answer is most dangerous |
| **Table & numeric reasoning** | 20 | ±0.22 | reading a value from a table under the right conditions, and reasoning over it | where the corpus is hardest and where the first pipeline sat at the floor |
| **Definitional & factual** | 20 | ±0.22 | what a term means, what a clause requires | the bread-and-butter case |
| **Epistemic boundary detection** | 15 | ±0.25 | evidence chain leaves the corpus; correct answer names the missing document | new; generated from the 450 residual references |
| **Adversarial & false premise** | 15 | ±0.25 | the question embeds a false inference or an unsupported premise | tests whether the system resists a confident framing |
| **Applicability & authority** *(v2.0)* | 10 | ±0.31 | does this requirement apply here; which standard governs when two appear to differ; what does tailoring permit | a reviewer's point: for engineering use this matters more than another twenty simple facts |
| **Acronym paired-variant probe** *(v3.5)* | 5 | — | identical question in acronym and expanded form | reduced from 10: dual-payload ingest makes retrieval invariance structural, so these now probe the **generation** path only, where 3 of the 7 measured fabrications occurred. 5 slots returned to multi-hop |
| **Ambiguous acronym** *(v3.4)* | 10 | ±0.31 | an acronym with two or more genuine expansions in the corpus; the correct answer resolves it **against the governing document**, or says which reading is meant and why | built from the 99 measured semantic collisions. Tests document-scoped reasoning rather than most-common-expansion guessing. Same logic as the corpus boundary: a real property of ECSS, turned into a test asset |
| **Identifier & sanity** | 5 | — | document codes, abbreviations | sanity check only; was saturated at 0.81–0.88 and consumed 10% of the set |
| **Total** | **155** | | | |

**§6.2 restated — v3.9, PoC lead decision 2026-08-14.** The table above is the **design target**. It was
not reached, and the reason is measured rather than estimated: the first full claim extraction
(`P42_Claim_Extraction_Results.md` v1.0) yielded 50%/51% validator-accepted items against a 71.8% floor,
and gate 6 measured extractor agreement at **0.667 against a 0.95 criterion**. Ground truth is therefore
established by human adjudication over the two-framing consensus set (`P42_Claim_Extraction_Protocol.md`
v1.3 §7), and the item count is restated to what that set contains rather than topped up with material
of unmeasured quality.

Preserving the proportions above exactly would give **N = 46** — `applicability_authority` (3 available)
and `definitional` (6) bind — discarding 34 adjudicable items to hold a ratio, and landing multi-hop at
n=10 (±0.31) rather than the ±0.18 it was sized for. Since the proportions cannot preserve the property
they exist to serve, the set is kept whole and **every score is published with its class n and CI**:

| Class | n (v3.11, adjudicated) | ±95% CI | design target |
|---|---:|---:|---:|
| Multi-hop / cross-standard | 17 | ±0.24 | 35 |
| Nuance & applicability | 11 | ±0.30 | 20 |
| Table & numeric reasoning | 11 | ±0.30 | 20 |
| Epistemic boundary detection | 9 | ±0.33 | 15 |
| Ambiguous acronym | 6 | ±0.40 | 10 |
| Definitional & factual | 6 | ±0.40 | 20 |
| Adversarial & false premise | 5 | — | 15 |
| Identifier & sanity | 4 | — | 5 |
| Acronym paired-variant probe | 3 | — | 5 |
| Applicability & authority | 2 | — | 10 |
| **Total** | **74** | | **155** |

**These counts are post-adjudication and final for this campaign.** Two reviewers adjudicated all 352
consensus claims independently, and 42 of those claims were **re-adjudicated** after a defect in the
adjudication packet's table renderer was found and corrected (`P42_Claim_Extraction_Results.md` v1.4
§6–7). Final: **348 adopted, 4 rejected, 0 unresolved, 343 claims across 74 items**; 6 items fell below
the two-claim threshold. Reviewer agreement is **98.9%** on whether a claim is true of its passage and
**96.8%** on whether it is essential — measured, reported, and not averaged into anything.

**§6.2 restated a second time — v3.13, post-census, 2026-08-14.** The 74 adjudicated items produced 74
questions; 9 were dropped at authoring, 65 went to a blinded two-part human census, and **56 were
adopted** under the decision rule pre-registered before the packet was sent
(`P42_Question_Generation_Protocol.md` §6, results in `P42_Census_Results.md` v1.3). These are the
counts the benchmark ships with.

| Class | n (v3.13, adopted) | ±95% CI | v3.11 | design target | status |
|---|---:|---:|---:|---:|---|
| Multi-hop / cross-standard | 11 | ±0.30 | 17 | 35 | scored |
| Epistemic boundary detection | 9 | ±0.33 | 9 | 15 | scored |
| Table & numeric reasoning | 8 | ±0.35 | 11 | 20 | scored |
| Nuance & applicability | 7 | ±0.37 | 11 | 20 | scored |
| Ambiguous acronym | 6 | ±0.40 | 6 | 10 | scored |
| Definitional & factual | 5 | — | 6 | 20 | scored |
| Identifier & sanity | 3 | — | 4 | 5 | scored |
| Acronym paired-variant probe | 3 | — | 3 | 5 | probe, not scored *(by design)* |
| Adversarial & false premise | 2 | — | 5 | 15 | **below floor — measured, not scored** |
| Applicability & authority | 2 | — | 2 | 10 | **below floor — measured, not scored** |
| **Total** | **56** | | 74 | 155 | 49 items carry the score |

**The two below-floor classes ship as they are — PoC lead decision, 2026-08-14.** `adversarial` had 3
authored and lost one to a single reviewer's unconfirmed self-report; `applicability_authority` only
ever had 2 anchors available. Neither is topped up, for a reason worth stating rather than assuming:
**going from 2 to 3 would not make either class measurable.** Three is the line at which §7 of the
question protocol stops pretending, not the line at which an interval becomes informative — and
authoring items after seeing which classes came up short is the shape rule 47 exists to prevent, even
when the intent is honest. The four items are published, excluded from both scores, and
`applicability_authority` is registered for campaign 3 at the size its argument deserves — 8 to 10
anchors drawn in the ordinary way, not two survivors.

**Consequence for the weighted score — RENORMALISED, PoC lead decision 2026-08-14.** The v3.8 weight set assigns
`adversarial` 7% and `applicability & authority` 8%. Both classes are now unscored, so **15% of the
weight sits on classes that cannot contribute**, and the weighted score is not computable as specified
(rule 57: a weight set is checked against the class list, not against 100%). **The weighted score is renormalised over the 7
scored classes.** This is a renormalisation, not a re-weighting: **no class's weight relative to any
other changes**, and the v3.8 ordering — which was argued from failure risk and signed off — is
preserved exactly.

The normative form is the fraction, because that is what stays exact:

```
multi-hop 22/85 · nuance 18/85 · table & numeric 14/85 · definitional 14/85
boundary 10/85 · ambiguous acronym 4/85 · identifier 3/85
```

As percentages, to two decimals, summing to 100.00 — checked, not asserted by eye (rule 57):

| class | v3.8 weight | v3.13 renormalised |
|---|---:|---:|
| multi-hop | 22% | **25.88%** |
| nuance & applicability | 18% | **21.18%** |
| table & numeric | 14% | **16.47%** |
| definitional & factual | 14% | **16.47%** |
| epistemic boundary | 10% | **11.76%** |
| ambiguous acronym | 4% | **4.71%** |
| identifier & sanity | 3% | **3.53%** |
| adversarial | 7% | *not scored* |
| applicability & authority | 8% | *not scored* |
| acronym paired-variant | not scored | *not scored* |
| **Total** | 85% *(of 100 assigned)* | **100.00%** |

**When either class returns to the floor, the v3.8 weights return unchanged** — the fractions above are
derived from them and carry no independent authority. Any implementation of the evaluator asserts that
its weight keys match the scored-class list and that the values sum to 1.0, per rule 57; a weight set
that sums correctly is exactly what a weight set with missing classes looks like, which is how the v3.7
set survived three revisions covering 7 of 10 classes.

Either way the caveat is the same and it is not a small one: **the weighting was justified by failure
risk, and the two classes carrying the highest failure risk are the ones that fell below the floor.**
A wrong applicability call and a confidently accepted false premise are precisely the failures §6.2
argued the score should punish hardest, and this campaign cannot score either. The unweighted macro
over 49 items remains the headline figure; the weighted score, whichever option is taken, is read with
that sentence attached.

**Claim scoring — replaced and revalidated, v3.13.** §8's Layer 2 claim matching used lexical overlap.
The census measured it against 460 human judgements with the machine's verdicts sealed beforehand and
found **31% recall**: it recovered under a third of the claims a reviewer confirmed their own answer
contained, because a competent answer paraphrases and compresses. It is retracted as a scorer, together
with the §4c answerability baseline it produced. Layer 2 is now the entailment judge specified and
pre-registered in `P42_Claim_Scoring_Protocol.md` v1.4, **validated at 94% recall / 0.5% on constructed
negatives / 0 unparseable over 850 pairs and ACCEPTED**. It carries one published caveat: on hard
negatives it misses the **dropped qualifier** — an answer that states a requirement but omits its
governing document or its condition — so claim-level scores run optimistic exactly there (§7a, §7c).

**What the smaller set costs, stated plainly.** The largest lever effect measured in campaign 1 was
**+0.079**. At n=17 the multi-hop CI is ±0.24, so this benchmark **cannot resolve an effect of that size
within a single class.** It can support the unweighted macro score across 80 items, per-class
directional findings, and the qualitative failure analysis that produced every lesson in the register.
Claiming more than that from 80 items would repeat L4.8 — sizing by what happened to get written, then
reporting as though the interval were the designed one.

**Revision-difference questions are deferred, not forgotten.** A reviewer proposed asking what changed
between two revisions of a standard. Verified: **zero documents in the available set appear in more
than one revision** — the library holds active standards only. These questions need superseded
revisions, which would have to be obtained. Applicability, scope-conflict and authority questions are
adopted now because they *are* answerable from the current corpus.

**Two headline scores, not one — corrected in v3.0.** A reviewer noted that nobody has justified why
multi-hop is 25% rather than 20%, and that the weights are currently my judgement while defining the
gate. Rather than defend them in the abstract, **both scores are published**:

- **Unweighted macro score** — every class contributes equally. Comparable across weight changes.
- **Operational weighted score** — the weights below, reflecting failure risk.

If the weights change later, historical results stay comparable through the unweighted figure. Gate 9
in §13a additionally checks that pipeline *rankings* do not flip under alternative weight sets; if they
do, the weights are doing the work rather than the measurement.

Weights are published as part of the specification because they define the gate:

```
multi-hop 22% · nuance 18% · table/numeric 14% · definitional 14%
applicability & authority 8% · adversarial 7% · boundary 10%
ambiguous acronym 4% · identifier 3%
                                              (acronym paired-variant: not scored)
```

**Corrected in v3.8 — the previous weight set covered 7 of 10 classes.** `applicability_authority`,
`ambiguous_acronym` and `acronym_paired` carried no weight at all: **25 items, 16% of the set**, outside
the score that defines the gate, and outside gate 9's robustness check by construction. The v3.7
weights are rescaled by 0.88 to make room and the two missing scored classes given weights reflecting
failure risk, which is the stated basis:

- **applicability & authority 8%**, placed *above* adversarial. §6.2's own argument for the class is
  that "for engineering use this matters more than another twenty simple facts"; a wrong answer about
  which standard governs changes an engineering decision, which is the definition used for a `critical`
  forbidden claim in §6.3.
- **ambiguous acronym 4%.** A real and measured property of ECSS (99 collisions), but a wrong expansion
  is usually recoverable by a reader, where a wrong applicability call is not.
- **acronym paired-variant: excluded, deliberately.** It is a *probe*, not a capability: the two forms
  of one question, where the measurement of interest is the **difference** between them, and gate 10(b)
  already requires no significant gap. Scoring it in the headline would double-count the underlying
  question and reward the pipeline for a property gate 10 tests directly.

**These weights are SIGNED OFF (PoC lead, 2026-08-14).** §6.2 states that weights define the gate and
are the PoC lead's call; they are adopted as written above.

**The unweighted macro score is the headline figure for this campaign, with the weighted score
published beside it.** That ordering is a consequence of the adjudicated set's shape: class sizes run
from 17 down to 2, so the weighted score leans hardest on the classes measured at ±0.40 or worse. The
unweighted macro also stays comparable across any later weight change — the case v3.0 introduced it
for — and gate 9 continues to check that pipeline *rankings* do not flip between the two. Neither
figure is reported without its per-class n and CI (§6.2, v3.11).

### 6.3 The item schema

```jsonc
{
  "id": "M-0042",
  "class": "multi_hop",
  "difficulty": "hard",
  "split": "dev | frozen | challenge",
  "question": "...",

  "evidence": [                                  // what SHOULD be retrieved, with roles
    {"document": "ECSS-Q-ST-80C", "clause": "Annex D Table D-1", "role": "classification"},
    {"document": "ECSS-E-ST-10-02C", "clause": "5.2.2.1d", "role": "method-constraint"}
  ],

  "claims": [                                    // what a correct answer must contain
    {"id": "C1", "text": "...", "tier": "required", "status": "explicit",
     "anchor": "ECSS-Q-ST-80C Annex D Table D-1", "quote": "verbatim source text"},
    {"id": "C2", "text": "...", "tier": "optional", "status": "derived",
     "anchors": ["...", "..."], "inference": "why C2 follows from both"}
  ],

  "forbidden_claims": [                          // what a correct answer must NOT contain
    {"id": "F1", "text": "ECSS prohibits review-of-design as a sole verification method",
     "detector": {"type": "string", "patterns": ["prohibit", "not permitted"]},
     "why": "'prohibited' appears 0 times in ECSS-E-ST-10-02C; 5.2.2.1d permits it with a risk assessment"}
  ],

  "decision": "qualified",                       // for deterministic polarity checking
  "minimal_correct_answer": "...",               // the floor: shortest fully-correct answer
  "boundary": [],                                // documents outside the corpus this needs, if any
  "provenance": {"generated_by": "...", "verified_by": ["...", "..."], "pilot_stats": {}}
}
```

**Claim evidence model — corrected in v2.0.** Version 1.0 required an `explicit` claim to be a
verbatim quote and a `derived` claim to have two or more anchors. A reviewer showed this breaks on
exactly the questions we care about, and it is worse than they said: **a single-table lookup is not
expressible at all.** "Function category II with no compensating provision ⇒ criticality B" is not a
quote (it fails `explicit`) and has one anchor (it fails `derived`). Table reasoning is a priority
class, so the schema made our most important questions unauthorable.

Claims now carry **evidence spans plus an inference type**:

```jsonc
{"id": "C1", "tier": "required",
 "evidence": [{"anchor": "ECSS-Q-ST-80C Annex D Table D-1", "span": "..."}],
 "inference": "table_lookup"}
```

| Inference type | Meaning | Validation |
|---|---|---|
| `direct` | the claim is stated in the span | span must contain the claim text |
| `table_lookup` | read from a table under stated conditions | the row and column conditions must be present in the span |
| `numeric_calculation` | computed from source values | source values present; calculation recorded |
| `logical_combination` | two or more spans combined | ≥2 spans; the inference stated |
| `cross_clause` / `cross_document` | chained across clauses or documents | each hop anchored |
| `conditional_application` | applies only under a stated condition | the condition must be in a span |
| `ordering` | sequence or precedence | the ordering evidence present |
| `definition_mapping` | term resolved via a definition | the definition anchored |

**Three schema rules, enforced by a validator and not by review discipline.** All four confirmed
question defects in the first campaign violate one of them:

1. **A `required` claim may not have `status: interpretive`.** Interpretation may earn credit; it may
   never be mandatory. *(Two defects.)*
2. **Every claim's evidence must satisfy its declared inference type**, per the table above.
   *(One defect: a keypoint asserted a fact absent from the clause it cited.)*
3. **Every anchor must resolve** to a real document and clause in the corpus. *(Would have rejected
   three non-existent clause numbers proposed in an external review.)*

Additionally: an item where **every** claim is `required` is rejected unless justified — in the first
campaign the optional tier existed and was used on **zero of 76 questions**, which alone cost four
correct answers their full credit.

**Forbidden claims carry a severity** — `critical`, `major` or `minor` — assigned once at authoring
time, so grading stays deterministic. "Category B software must always be tested" is critical because
it changes an engineering decision; a wrong acronym expansion is usually minor.

---

## 7. Part IV — Building ground truth without human vetting

This section carries the most risk. Constraint C1 says there is no human budget for vetting. The
first campaign's defect rate under author-then-verify was **5.3% of items** — the same order as the
largest effect we were trying to measure. Automation must do better than that, not worse.

The design rests on one idea: **make correctness checkable by construction, then verify adversarially,
then discard on disagreement.**

### 7.1 Two tracks — added in v2.0, renamed in v3.0

Version 1.0 named question representativeness as its biggest validity risk and then did nothing about
it. Both reviewers pushed on it. The benchmark now has **two tracks, reported separately and never
summed into one figure**:

| | **Track A — diagnostic** | **Track B — scenario-oriented** |
|---|---|---|
| Generated from | clause → claim → question | scenario → question |
| Answers | *which part of the pipeline is failing?* | *does this behave like an engineering assistant?* |
| Ground truth | maximally defensible | weaker, and reported as such |
| Size | ~90 items | ~35 items |

**Track B must be generatable without human authoring**, or it violates constraint C1. It is, because
**ECSS contains its own task frames**: Document Requirements Definitions state what a project must
produce, review definitions state what each milestone must demonstrate, and applicability matrices
state what applies to what. These yield genuinely task-shaped questions — *"I am preparing the PDR
data package; what does the software verification plan have to contain?"* — that remain traceable to
clauses.

**Renamed in v3.0.** Version 2.0 called this track "realistic". A reviewer objected that the name was
doing argumentative work the evidence does not support — task-shaped is not the same as representative.
It is now **scenario-oriented**, and it earns the word "realistic" only if it passes the plausibility
audit below.

**Fallback if the audit fails — added in v3.1.** If Track B does not score materially above Track A,
the next source is **historical project review actions**: review item discrepancies, review comments
and action items from completed programmes. These are the closest available record of what engineers
actually ask, and they are naturally task-shaped. They are project data rather than public standards,
so availability and sensitivity need confirming — but if available they would settle the
representativeness question outright rather than mitigating it, and are worth considering *before* the
audit rather than after.

**Plausibility audit — a deliberate exception to the minimal-human constraint.** 20–30 items per track,
rated by engineers on one question only: *"would an engineer plausibly ask this?"* No answer
verification, so the task costs perhaps twenty minutes. **If Track B does not score materially above
Track A, the two-track rationale collapses** and the honest response is a single track with an openly
stated validity limitation. This is the one place where a very small human input buys disproportionate
validity, which is why it overrides constraint C1.

### 7.2 Anchor-first generation — the process inversion

**The first campaign did this:** write a question → write the expected answer points → find a clause
to cite. Claims drift from the source, and nothing detects the drift.

**The design does this:**

```
clause text
   → extract a candidate claim, keeping its evidence span  (the anchor is attached by construction)
   → classify the claim: explicit / derived / interpretive, and its inference type
   → generate the question whose answer is that claim
   → generate the forbidden claims: the plausible near-misses this clause invites
   → MUTATE the question for realism, then gate on lexical overlap  (7.3)
```

For multi-hop items the same process runs over the **cross-reference graph** built at ingestion
(requirement I4). This is why the reference graph is an ingestion requirement rather than an analysis
convenience.

### 7.3 Persona mutation and the lexical-overlap gate — added in v2.0

A reviewer identified a bias I had missed: **questions generated from a passage inherit that
passage's vocabulary**, creating artificial resonance between question and gold chunk and inflating
retrieval scores. Real engineers use task framing and industry jargon, not normative drafting style.

Every generated question therefore passes through:

1. **Persona and paraphrase mutation** — rewrite under engineering personas (an AIT engineer on the
   floor; a project manager at a review; a subcontractor reading a requirement), substituting common
   industry terms for formal ECSS phrasing.
2. **A measured diagnostic, not a hard gate — corrected in v3.0.** Version 2.0 proposed rejecting
   questions whose lexical overlap with the gold passage exceeded a threshold. A reviewer showed both
   directions of that reasoning fail: low overlap can be a trivial synonym swap preserving the same
   semantic structure, and high overlap can be authentic — *"What verification method applies to a
   Category B software requirement?"* is exactly how an engineer speaks and legitimately contains ECSS
   terminology.

   **Acronym substitutions are excluded from the overlap computation — added in v3.4.** Swapping
   `PDR` for "Preliminary Design Review" changes lexical overlap enormously while changing the
   question's difficulty barely at all. Counting it would make the gate reward exactly the mutation
   that teaches us least, and penalise the realistic phrasing we are trying to produce. Overlap is
   therefore computed after normalising both texts through the document's acronym table (§5.4).
   Acronym form is instead handled as its **own mutation axis**: selected items are authored as
   **paired variants** — identical question, acronym form and expanded form — so that acronym
   robustness becomes a measured number rather than an assumption.

   The target is therefore restated: **avoid textual reconstruction of the source while preserving
   answerability** — not *minimise shared words*. Three signals are measured and published together:
   lexical overlap, semantic similarity, and question-to-source phrasing similarity. High combined
   similarity **flags** an item for review; it does not automatically reject it.

### 7.4 The four automated checks every candidate must pass

| Check | Method | Rejects |
|---|---|---|
| **Anchor resolution** | look up every anchor in the corpus index | non-existent clauses |
| **Evidence validation** | the span must satisfy the declared inference type (6.3) | claims not supported by their evidence |
| **Schema rules** | the three rules in 6.3 | interpretation smuggled in as fact |
| **Answerability** | an independent agent given *only* the listed evidence must produce the required claims | questions needing evidence we did not list; questions the corpus cannot answer |

The answerability check would have caught the first campaign's worst defect automatically — and would
have **reclassified it as a boundary-awareness item**, which is what it should have been.

### 7.5 The disagreement protocol — rewritten in v2.0

**Both reviewers independently attacked "discard on disagreement"**, and their convergence is itself
evidence. The argument: nuanced, conditional, multi-clause items are exactly where verifiers disagree,
so blanket discard systematically purges the most valuable questions and leaves a benchmark of easy
consensus facts — defeating objective O2.

They proposed an *uncertain* pool. That is better than discarding, but it still treats disagreement as
noise. **Most disagreements are actionable repairs:**

| Verifiers disagree about… | Action | Why |
|---|---|---|
| whether a claim is supported by its evidence | **reject that claim**, keep the item | factual contradiction |
| whether a claim is required or optional | **demote to optional**, keep the item | the disagreement *is* the evidence it is not required |
| whether the question is ambiguous | **rewrite the question**, re-verify | ambiguity is a question defect |
| whether a forbidden claim is truly false | **drop that forbidden claim**, keep the item | conservative |
| whether the item is answerable from the listed evidence | **reclassify as boundary-awareness**, or reject | how Q027 should have been handled |
| anything else, or repair fails twice | **UNCERTAIN pool** | honest |

Items in the `uncertain_items` pool are **excluded from the headline, retained, and reported as a
first-class number**. The human spot-audit samples from that pool preferentially, because that is
where the information is.

**Repair laundering — guarded in v3.0.** Both reviewers pressed on the risk that automated repair
*simplifies* hard items rather than fixing them: demote a disputed claim, rewrite an ambiguous question,
and a difficult item quietly becomes an easy one. Two mechanisms:

1. **Repair-complexity guard (hard rule).** If a repair would drop the required claims below two, or
   convert a multi-hop item into a single-hop item, **the item is not repaired** — it goes straight to
   the uncertain pool. This closes the loophole rather than only observing it.
2. **Repair-bias invariant (measurement).** Every repaired item retains `original_question`,
   `original_gold`, `disagreement`, `repair` and `post_repair_gold`. Difficulty, discrimination and
   claim count are compared **before and after repair** and reported as a benchmark-health metric. A
   systematic reduction across all three means the protocol is laundering, not repairing — gate 5 in
   §13a.

### 7.6 Adversarial verification

Each candidate goes to independent verifiers that do **not** see the generator's reasoning and are
instructed to **refute** rather than confirm. Each answers separately: is every required claim
supported by its evidence; is any required claim actually interpretive; is the question answerable
from the listed evidence and nothing else; is any forbidden claim in fact true; is the question
ambiguous?

**On independence — corrected in v2.0.** Version 1.0 claimed independence from using a different model
family. A reviewer correctly noted that different families still share training data, failure modes
and terminology priors, so that is **model-family diversity, not independence**. True independence
comes from **different evidence paths**: the generator works from retrieved passages, the verifier
works from the source corpus. Our design already had the stronger property; v1.0 was selling the
weaker one. Architectural separation is now the primary claim, model diversity a secondary defence.

### 7.5 What the human actually does

| Activity | Frequency | Effort |
|---|---|---|
| Approve the corpus envelope and the boundary list | once | ~30 min |
| Approve the class definitions and weights | once | ~30 min |
| Spot-audit a random sample of accepted items (~20 of 125) | once per generation round | ~45 min |
| Accept or reject the batch on the audit result | once per round | minutes |
| Arbitrate the assistant's flagged items — those it explicitly cannot settle | per run, expected < 5 | ~15 min |

**The audit is a tripwire, not a proof — corrected in v2.0.** Version 1.0 implied that a clean
20-item audit demonstrated a low ground-truth defect rate. A reviewer correctly pointed out the
arithmetic: 2 defects in 20 is **10%, not 2%**. Stated honestly:

- A 20-item audit with **zero defects** puts the 95% upper confidence bound on the defect rate at
  roughly **14%** (the rule of three, 3/n). It does not demonstrate a low defect rate.
- Demonstrating a defect rate **≤5% at 95% confidence** needs roughly **60 consecutive clean items**.

The audit is therefore an **acceptance-sampling rule** that catches a batch which has gone badly
wrong. Reject on **≥2 defects in 20**. Audits **accumulate across rounds**, so the confidence bound
tightens towards a figure worth quoting, and **the bound achieved so far is published with the
benchmark** rather than implied.

### 7.6 Pilot and cull

Ground truth being *correct* is not the same as items being *useful*. Measured on the first set:
**only 23 of 76 items (30%) ever changed verdict across three pipeline configurations.** 21 always
scored full marks, 21 were permanently stuck at partial credit, 11 never passed.

So candidates are piloted before they become a benchmark:

1. Run the full candidate pool against the pipeline, **plus a deliberately weakened variant** (for
   example retrieval disabled, or retrieval depth cut to 5) as a discrimination probe.
2. Compute per item: **difficulty** (how often it is passed), **discrimination** (does it track
   overall quality, and does it separate the strong pipeline from the weakened one), **stability**
   (does its verdict move under a null change).
3. Cull: drop items that every configuration passes, every configuration fails, or that flip under a
   null change.
4. **Exception:** items that fail for infrastructure reasons are kept and tagged as **corpus probes**.
   They are diagnostically valuable — they localise chunker and boundary failures — but they are
   reported separately and never sit unlabelled inside the headline accuracy number.

---

## 8. Part V — The evaluator

Four layers, in increasing cost and decreasing certainty. This architecture is carried forward from
the first campaign, where it was the strongest part of the design.

### Layer 1 — Deterministic

No language model. Exact comparisons made possible by the answer contract (5.3) and the item schema.

- decision polarity against `decision`
- numeric values, category letters, ordered sequences
- citation format, and whether every cited document was actually in the retrieved context
  (a citation to a document the system never saw is **fabrication**, mechanically detectable)
- **forbidden-claim detection by string and pattern match**
- boundary claims against the item's `boundary` list

**Seed data available immediately.** Seven recurring fabrications were enumerated and source-verified
in the first campaign, each stable across runs: a review acronym expanded wrongly, two acronym
expansions invented, a component-specific rule generalised to all technologies, a software-specific
scale applied to hardware, an invented eight-item list where the standard gives five, and a criticality
scheme borrowed from an unrelated standard. These become the first entries in the forbidden-claim
library on day one.

**Modal-verb fidelity — added in v2.0, and the single best find of the review round.** ECSS defines
its modal verbs normatively, in clause 3.4 "Nomenclature" of each standard (verified present in **46
of 105** documents). Verbatim from `ECSS-E-ST-10-02C`:

> "shall" expresses **requirements** · "should" expresses **recommendations** · "may" and "need not"
> express positive and negative **permissions** · "can" expresses **capabilities or possibilities**
> … *"In ECSS 'may' and 'can' have completely different meanings: 'may' is normative (permission),
> and 'can' is descriptive."*

If a clause says the supplier **shall** perform a thermal vacuum test and the system answers that
they **should**, semantic claim matching scores that as a perfect match. In compliance terms it is a
serious error. Layer 1 therefore carries a deterministic **modal-fidelity check**: where a claim's
evidence span contains a modal verb, weakening it in the answer is an automatic forbidden-claim hit.

Note this is a **four-way** distinction, not the three-way one usually assumed — ECSS explicitly flags
"may" versus "can" as a trap, so the check covers it.

**Both directions — corrected in v3.0.** Version 2.0 only tested weakening. A reviewer pointed out that
strengthening is equally wrong, so the check is now **normative modality fidelity** and tests all of:

| Source | Answer | Failure |
|---|---|---|
| shall | should | a requirement demoted to a recommendation |
| may | shall | an obligation invented where ECSS grants permission |
| can | may | a permission invented where ECSS is merely descriptive |
| should | shall | a recommendation promoted to a requirement |

**Layer 1 must itself be tested.** Both deterministic checks in the first pipeline were defective —
one recognised only one bracket style and undercounted citations by 7 of 66 answers; the other matched
only at the start of the answer and case-sensitively, under-reporting false refusals by more than
half. Every Layer 1 check ships with an adversarial battery of shapes it must handle.

### Layer 2 — Claim matching *(instrument replaced in v3.13)*

Per-claim: is this claim present in the answer? Semantic matching, because wording varies legitimately.
Produces **claim coverage** — the fraction of required claims covered — which is the **primary
continuous metric**.

> **"Semantic matching, because wording varies legitimately" was implemented as lexical overlap, and
> that is exactly the failure it was written to avoid.** Measured against 460 human judgements with the
> machine's verdicts sealed first: **31% recall**. Retracted. Layer 2 is now the entailment judge of
> `P42_Claim_Scoring_Protocol.md` v1.4 — validated at 94% recall over 850 pairs and ACCEPTED, with the
> dropped-qualifier caveat published beside every score it produces. The sentence above stated the
> requirement correctly for three revisions while the code did the opposite; a design statement is not
> a measurement (rule 67).

Why continuous: the first campaign's three-point grade put **45% of answers in the middle band**, so
two pipelines that were both "mostly right but incomplete" were indistinguishable on nearly half the
set. Re-scoring the same data as claim coverage reproduced the effect at finer grain at zero extra
cost. Items therefore carry enough claims (typically 3–6, against a first-campaign mean of 2.67) for
the metric to have resolution.

### Layer 3 — The on-box judge

A local language model, used where semantics cannot be matched by rule: qualification, conditionality,
whether a nuanced answer is correctly hedged. **It is the only AI assessment layer that survives
air-gapped** (constraint C3), which is why it is kept despite its known weakness.

### Layer 4 — The independent assistant assessor

An assistant of a **different model family from the answer generator**, with access to the **source
documents** rather than only the retrieved context, and holding the campaign history. It produces the
run assessment, maintains the records, and proposes the next experiment (constraint C2).

Its independence is not a claim; it is a measurement. In the first campaign it disagreed with the
same-family judge on 23 of 76 items and was right in the great majority of the cases that were
checked against source.

**Governance, unchanged and important.** No automated layer is authoritative. Every assessment cites
the source clause for its factual claims so it can be checked. The audit sample (7.5) is what keeps
the assessor honest.

### 8.1 Four scorecards — restructured in v2.0

A reviewer proposed separating the reported numbers into four scorecards rather than one vector. This
is a cleaner articulation of something v1.0 had scattered, and it directly serves the "localise the
failure" objective — when an item fails you can say *"the table-reconstruction gate failed"* rather
than *"the system is bad"*.

```
MAIN BENCHMARK          claim coverage · fully-correct items · qualification
                        reported separately for Track A and Track B, never summed

CORPUS HEALTH           extraction quality · table reconstruction · figure recovery
                        · normative closure coverage

PIPELINE DIAGNOSTICS    document recall · clause recall · rank quality
                        · evidence sufficiency · context sufficiency

TRUSTWORTHINESS         unsupported-claim rate · critical-hallucination rate
                        · false-premise acceptance · boundary awareness
                        · modal-verb fidelity
```

**Two metrics for correctness, not one — added in v2.0.** A reviewer noted that claim coverage is
**gameable by decomposing claims more finely**: split one claim into four and the item gains four
scoring opportunities. The gaming vector is the item author, which is to say me. So we report both:

- **Claim coverage** — fraction of required claims present. Fine diagnostic resolution.
- **Fully-correct items** — all required claims present **and** no critical forbidden claim. Strict
  and interpretable.

**Hallucination needs a denominator — corrected in v2.0.** Version 1.0 said "forbidden claims
triggered per answer", which is ambiguous. Three separate metrics:

| Metric | Denominator |
|---|---|
| **Unsupported-claim rate** | claims |
| **Critical-hallucination rate** | answers containing ≥1 critical false claim, over answers |
| **False-premise acceptance** | adversarial items whose false premise was accepted, over adversarial items |

The last is the most valuable for objective O3 and is reported most prominently.

**Citation recall** — whether every required claim is cited at all — remains a gap the first design
did not measure and this one does.

## 9. Splits

| Split | Size | Use |
|---|---|---|
| **Development** | ~50 | tuning; may be inspected item by item; fast iteration |
| **Frozen** | ~50 | gate decisions; never inspected during tuning |
| **Challenge** | ~25 | held back entirely; disproportionately multi-hop, nuance, adversarial, boundary. Run **once**, at the gate |

The challenge split exists because a benchmark you tune against stops measuring generalisation. It is
cheap to hold back now and impossible to create later.

---

## 10. Part VI — Operating the benchmark

### 10.1 The run loop

```
1. Change ONE lever, and declare its family (retrieval or generation)
2. Run:  retrieval-family → retrieval-only mode, ~1 minute
         generation-family → full run, ~20 minutes
3. Compare against the baseline with paired bootstrap confidence intervals
4. Apply the family-appropriate check:
      retrieval-family  → did retrieval improve?  If not, stop.
      generation-family → is the retrieval scorecard UNCHANGED (within the measured
                          noise floor)?  If not, the lever leaked; the run is void.
5. Assistant produces the run assessment: what moved, what broke, what to do next
6. Record the lever, the deltas and the verdict in the ablation log
7. Adopt or revert ONLY on statistically significant results
```

**Two rules from painful experience.** *One lever at a time*: one run in the first campaign moved
three variables and was uninterpretable; another silently fell back to a default and moved two. *Never
compare to an exact zero*: the re-ranker is not deterministic, and an exact-zero criterion would have
voided a valid experiment.

### 10.2 Records maintained by the assistant

| Record | Content | Updated |
|---|---|---|
| **Run assessment** | per run: plumbing verdict, scorecard reading, source-verified verdicts on the worst items, error-taxonomy labels, recommended next lever, defects found | every run |
| **Ablation log** | one row per experiment: lever, family, run IDs, deltas with CIs, verdict, adopted or reverted | every experiment |
| **Defect register** | every defect in pipeline, harness, questions or corpus: symptom, root cause, fix, version | on discovery |
| **Lessons learned** | the companion document; general rules extracted from defects | on discovery |
| **Item health** | per item: difficulty, discrimination, stability, and whether it is a corpus probe | every run |

Item health is new and directly serves objective O4: it is how we notice a class going saturated or
an item silently becoming inert, rather than discovering it a year later.

---

## 13a. Validation gates — nothing is generated until these pass

Added in v3.0 on a reviewer's suggestion, and it is the most important structural change of the round.
The architecture has now survived two adversarial reviews. **Its assumptions have survived none.**

| # | Gate | Metric | Pass criterion |
|---|---|---|---|
| 1 | **CLOSED 2026-08-12 as a measured limitation — not PASSED.** Re-run under pre-registration, then **VOIDED** by its own 5% human audit (11/15 against ≥14/15). Two of the three decisive disagreements needed ECSS knowledge absent from the evidence — that `Q-ST-70-02` *is* an unnamed screening test, and that a clause-2 listing can be disclaimed in body text — so this is a judgement gate, and model labellers cannot satisfy it at any n. Recorded rather than escalated. **Measured recall 0.926** (0.864 before the three mechanical extensions), precision ≈0.97. **Consequence: the corpus is a floor, gate 3 sets the final corpus.** Superseded detail A fresh 300-pair sample is drawn under a protocol pre-registered before sampling: unit of analysis = **document pair**; evidence shown = the citing document's clause 2 excerpt plus up to 3 in-text occurrences; **cluster cap of 2 instances per document pair, per stratum**; labelling by independent model instances **plus a 5% human spot-audit**. Re-labelling the old sample was proposed and rejected as insufficient. **Original result, retained:** precision 0.853, recall 0.833 — **FAIL** "Precision and recall on a 300-edge stratified sample, independently classified", ≥95% both | **precision 0.853, recall 0.833 — FAIL.** Recorded rather than withdrawn. Diagnosis: the gate tested an edge-level classifier with occurrence-level evidence. All 30 apparent false positives are pairs the citing document lists in its own clause 2, sampled at a NOTE or change-record line; 16 of the 30 are one pair sampled 16 times. See `P42_Gate_Report_G1_G2.md` §3.1 |
| 1b | **PASSED 2026-08-12 — clause-2 extraction fidelity**, unaffected by gate 1's re-opening. **Human spot-audit COMPLETE: 6 of 6 agreed** (seed 1612). The first packet truncated its own evidence and produced one false disagreement; the auditor caught it, it was corrected and re-run — lesson L5.28 into the two measurements the reviews' concern actually reduces to | **(a) informative contamination:** false positives on handbook, TM and "see also" citations — **0%** (0 of 32 handbook, 0 of 9 informative-cue), against ≤5%. **(b) clause-2 extraction fidelity:** independent transcription of 20 raw clause-2 segments, stratified for truncation — **precision 0.991, recall 1.000**, against ≥0.95 both. **PASS.** Cost side recorded as limitation L-1: 1.3% of body-text-only obligations missed. **If the re-specification is rejected on review, §4.2 returns to provisional** |
| 2 | **PASSED 2026-08-12, human spot-audit COMPLETE: 7 of 7 agreed** (seed 1612) — Clause-2 parser repaired. Root cause was not the scan window: `str.find('normative references')` returned the **table-of-contents entry**, so the parser read the ToC. Repaired with whole-line heading anchors, enumerated variants, next-clause segment boundary, and a boilerplate-sentence fallback for adoption notices | **3 → 428 distinct normative edges. 116 of 128 documents parsed**; the 12 without a clause 2 verified as documents that have none. **PASS** |
| 3 | **Question-evidence closure** | share of answerable items whose evidence chain terminates inside the corpus (GREEN / AMBER / RED) | ≥99% GREEN. **This, not an aggregate statistic, decides the corpus size** |
| 4 | **Ingestion quality** | cap-rate, table reconstructability, duplicate rate, definition retrievability | as §5.1 |
| 5 | **Repair bias** | difficulty, discrimination and claim count before vs after repair | no systematic reduction beyond a stated tolerance |
| 6 | **Claim extraction** | **material** agreement between the two extractors, with confidence bound. Calibration first defines **equivalence rules** — order-insensitive claim sets, synonym normalisation, a stated claim-boundary convention — so that formatting noise is not counted as uncertainty | ≥95% measured; reject on ≥2 material disagreements in the 50-item calibration set |
| 7 | **Track separation** | SME plausibility, Track B vs Track A | Track B materially higher, or the two-track design is abandoned |
| 8 | **Retrieval** | dense vs hybrid vs hybrid+filter, per class | hybrid must improve the identifier and exact-query classes |
| 10 | *(v3.4)* **Acronym normalisation** | (a) harvest coverage: share of corpus acronyms captured from clause 3.3, spot-checked against the documents. (b) paired-variant agreement: for items authored in both acronym and expanded form, the difference in graded correctness | (a) ≥95% of acronyms appearing in authored items resolvable. (b) **no significant difference** between the paired forms. A significant gap is a pipeline defect, not a question defect, and blocks the acronym question class from the headline until fixed |
| 9 | **Weight robustness** | ranking correlation under alternative weight sets | high correlation, or the weights are doing the work |

**No gate is recorded as PASSED without a 5% human spot-audit** of its labelled data — adopted in
round four. **Gates 1b and 2: COMPLETE, 6/6 and 7/7.** Gate 4's checks are deterministic properties of
the index rather than labelled data, so no audit applies to it. A gate whose audit is owed is recorded
as **PASS (audit owed)**, never as PASS.

**The five validation experiments** both reviewers converged on, mapped to the gates: dependency
classifier (1, 2) · corpus/question closure (3) · repair bias (5) · extractor reliability (6) ·
Track-B realism (7).

## 11. Delivery plan

| Phase | Output | Gate before proceeding |
|---|---|---|
| **P0 — Corpus (measured, not yet final)** | **COMPLETE 2026-08-12.** 87-document normative closure, 428-edge typed graph, boundary list including 5 ECSS-internal dangling targets, 128 documents extracted | **gates 1 and 2 — both PASSED.** The corpus is still finalised in P5 against question-evidence closure (gate 3), but its starting point is now derived from ECSS's own clause-2 declarations rather than a heuristic |
| **P1 — Ingestion** | rebuilt ingestion, cross-reference graph, quality report | the four checks in 5.1 pass |
| **P2 — Contract** | structured answer mode + Layer 1 battery | battery green on all adversarial shapes |
| **P3 — Generation** | ~250 candidate items, anchor-first | validator clean; discard rate reported |
| **P4 — Verification** | adversarial verification, discard on disagreement | human audit of 20 items: ≤ 2 defects |
| **P5 — Pilot, cull, and CLOSE THE CORPUS LOOP** | ~145 surviving items, split three ways; corpus expanded where RED items cluster, then re-validated | **gates 3, 5, 7, 8, 9** plus item statistics. Corpus selection and question generation iterate here until GREEN ≥99% |
| **P6 — Evaluator** | full four-layer evaluator, reported vector | **reproduces the first campaign's known verdicts on its 228 archived graded answers** |

**The P6 gate deserves attention.** We keep the first campaign's 228 independently graded answers as a
**calibration set**. The new evaluator must reproduce the verdicts we already trust — the two adopted
levers and the eight found defects. If it does not, the evaluator is wrong, and we find that out
before it is used to make decisions.

The first benchmark is also **kept frozen as a regression suite**. It has six runs of history. It is
not the primary instrument, but it is free continuity.

---

## 12. What this design does not test

Stated plainly, because the most useful review contribution is what we have missed.

- **Multi-turn conversation.** Every item is single-turn. Real engineers ask follow-ups.
- **Figures and diagrams — OUT OF SCOPE for campaign 2, decided 2026-08-14.** Requirement I5 leaves
  figure references unreachable, the page-level visual index was built and never queried by any path
  (L2.3) and was deleted during the index rebuild, and the anchor audit measured a case where this
  bites. Wiring a visual query path in at this stage would add an unmeasured retrieval mode to a
  campaign whose ground truth is already fixed. Figure content is therefore whatever the text
  extraction recovered from figure regions, and no class depends on it. Recorded here rather than left
  implicit, because an unstated limitation reads as an oversight.
- **Revision conflicts.** Now partly addressed by the applicability and authority class, but true
  revision-difference questions remain untested because we hold only active revisions (decision D8).
- **Latency under load.** Single-user latency only.
- **Tailoring against a real project's applicability matrix** — arguably the most valuable real-world
  behaviour, and out of scope because it needs project data, not standards.
- **Long-answer synthesis.** No item requires a page-long structured answer, which is what an engineer
  actually wants for "how do I plan my verification programme".
- **Whether the questions resemble what engineers really ask.** Partly addressed in v2.0 by Track B,
  but Track B is still generated *from the standards*. Whether that is genuinely representative or
  merely a second synthetic distribution in a costume is **still the design's biggest validity risk**.
- **Whether the extractor is a single point of failure.** Every metric now flows through the post-hoc
  extractor introduced in 5.3.
- **Whether automated repair simplifies hard items.** The disagreement protocol in 7.5 repairs rather
  than discards; if repairs systematically soften difficult items, the bias we removed returns by
  another route.
- **Whether the class weights are right.** Both reviewers endorsed weighting; neither challenged
  *these* weights, and they define the gate.

---

## 13. Open decisions

All five v1.0 decisions are now closed by the review round. Three new ones replace them.

| # | v1.0 decision | Resolution |
|---|---|---|
| D1 | Corpus size | **Closed, and re-measured in v3.2.** Neither 56 nor 62 nor 39. Typed normative closure on the repaired graph gives **87 documents** from clause 2, **90** including v3.5's conditional-normative edges, reached in 4 hops, with a **2.0% internal dangling rate against 54.8% for the present 23-document corpus**. The v2.0/v3.1 figures of 35 and 39 were computed on a graph holding 3 edges and are struck. Final size still set by gate 3. |
| D2 | Answer contract | **Closed.** Prose output with post-hoc extraction. Both reviewers agreed independently. |
| D3 | Class weights | **Closed.** Weighted, as proposed. Both reviewers endorsed. |
| D4 | Audit threshold | **Closed.** ≥2 defects in 20 rejects the batch, framed as acceptance sampling with the achieved confidence bound published. |
| D5 | Verifier model families | **Closed.** Different families, but the primary claim is now **different evidence paths**. |

| # | **New decision** | Options | Recommendation |
|---|---|---|---|
| **D6** | Track A / Track B ratio | 90/35 as proposed, or more weight on realistic | 90/35 initially; revisit once Track B's ground-truth quality is measured |
| **D7** | Lexical-overlap threshold for the mutation gate | needs calibration against real engineer phrasing | set provisionally, publish the distribution, tighten on evidence |
| **D8** | Obtain superseded revisions to enable revision-difference questions | yes / no | **worth doing** — a reviewer argued convincingly that revision and applicability resolution matters more for engineering use than additional simple facts |

## Appendix A — The 87-document normative closure

Computed 2026-08-12 from the repaired clause-2 parser, following normative clause-2 edges only
(handbooks and technical memoranda excluded), to a fixed point in 4 hops from the 23-document seed.
**5 of these are not held** (`ECSS-Q-ST-70-07`, `-70-08`, `-70-10`, `-70-11`, `-70-38`) — they are
withdrawn or superseded and appear on the declared boundary.

**Branch S** (1) — `ECSS-S-ST-00-01`

**Branch M** (4) — `ECSS-M-ST-10` · `ECSS-M-ST-10-01` · `ECSS-M-ST-40` · `ECSS-M-ST-80`

**Branch E** (34) — `ECSS-E-AS-11` · `ECSS-E-HB-11` · `ECSS-E-ST-10` · `ECSS-E-ST-10-02` · `ECSS-E-ST-10-03` · `ECSS-E-ST-10-04` · `ECSS-E-ST-10-06` · `ECSS-E-ST-10-09` · `ECSS-E-ST-10-11` · `ECSS-E-ST-10-12` · `ECSS-E-ST-10-24` · `ECSS-E-ST-20` · `ECSS-E-ST-20-01` · `ECSS-E-ST-20-06` · `ECSS-E-ST-20-07` · `ECSS-E-ST-20-08` · `ECSS-E-ST-20-20` · `ECSS-E-ST-20-40` · `ECSS-E-ST-31` · `ECSS-E-ST-32` · `ECSS-E-ST-32-01` · `ECSS-E-ST-32-02` · `ECSS-E-ST-32-08` · `ECSS-E-ST-32-10` · `ECSS-E-ST-32-11` · `ECSS-E-ST-33-01` · `ECSS-E-ST-33-11` · `ECSS-E-ST-35` · `ECSS-E-ST-40` · `ECSS-E-ST-50` · `ECSS-E-ST-50-05` · `ECSS-E-ST-50-14` · `ECSS-E-ST-70` · `ECSS-E-ST-80`

**Branch Q** (48) — `ECSS-Q-ST-10` · `ECSS-Q-ST-10-04` · `ECSS-Q-ST-10-09` · `ECSS-Q-ST-20` · `ECSS-Q-ST-20-07` · `ECSS-Q-ST-20-08` · `ECSS-Q-ST-20-10` · `ECSS-Q-ST-30` · `ECSS-Q-ST-30-02` · `ECSS-Q-ST-30-11` · `ECSS-Q-ST-40` · `ECSS-Q-ST-60` · `ECSS-Q-ST-60-03` · `ECSS-Q-ST-60-05` · `ECSS-Q-ST-60-12` · `ECSS-Q-ST-60-13` · `ECSS-Q-ST-60-14` · `ECSS-Q-ST-60-15` · `ECSS-Q-ST-70` · `ECSS-Q-ST-70-01` · `ECSS-Q-ST-70-02` · `ECSS-Q-ST-70-04` · `ECSS-Q-ST-70-06` · `ECSS-Q-ST-70-07` · `ECSS-Q-ST-70-08` · `ECSS-Q-ST-70-09` · `ECSS-Q-ST-70-10` · `ECSS-Q-ST-70-11` · `ECSS-Q-ST-70-12` · `ECSS-Q-ST-70-13` · `ECSS-Q-ST-70-15` · `ECSS-Q-ST-70-18` · `ECSS-Q-ST-70-21` · `ECSS-Q-ST-70-22` · `ECSS-Q-ST-70-26` · `ECSS-Q-ST-70-28` · `ECSS-Q-ST-70-29` · `ECSS-Q-ST-70-30` · `ECSS-Q-ST-70-31` · `ECSS-Q-ST-70-36` · `ECSS-Q-ST-70-37` · `ECSS-Q-ST-70-38` · `ECSS-Q-ST-70-39` · `ECSS-Q-ST-70-45` · `ECSS-Q-ST-70-60` · `ECSS-Q-ST-70-61` · `ECSS-Q-ST-70-71` · `ECSS-Q-ST-80`

## Appendix B — Measurements cited in this document

| Measurement | Value | Source |
|---|---|---|
| Normative closure from the 23-doc seed | **87 documents** (clause 2) · **90** (incl. conditional) | repaired clause-2 parser, 428-edge graph, gate 2 |
| Clause-2 omission rate, edge-level exhaustive | **2.5%** (9 of 362) | conformance-phrase scan over all 82 documents, round four |
| Acronym collision skew, `PDR` | 21 documents majority · 1 minority | clause 3.3 harvest |
| Text volume, 23-doc seed → 82-doc corpus | 6.94 MB → 18.03 MB = **2.60×** | extracted text; corrects a reviewer's "nearly 4-fold" |
| Dangling normative-edge rate, present 23-doc corpus | **54.8%** (69 of 126) | same graph, same method |
| Dangling normative-edge rate, inside the 87-doc closure | **2.0%** (7 of 353) | same |
| Clause-2 parser, before → after repair | **3 → 428** distinct normative edges | gate 2 |
| Clause-2 extraction fidelity | **precision 0.991, recall 1.000** (108 of 109 entries) | gate 1a, 20 documents, independent transcription |
| Informative / handbook false-positive rate | **0%** (0 of 32 handbook, 0 of 9 informative-cue) | gate 1, 300-edge stratified sample |
| Body-text-only normative obligations missed | **1.3%** (4 of 300) | same sample |
| Occurrence-level vs edge-level normative disagreement | **10%** (30 of 300) | same sample — the reason gate 1 was re-specified |
| Dangling reference rate, first corpus, untyped | 47% (633 refs, 87 documents) | untyped reference graph over 23 documents |
| Passages at the size cap | 27% overall, 45% table-reasoning | live index, run 2026-08-11 |
| Duplicate `(document, clause)` in context | 24 of 76 questions, 31 slots | same |
| Question defect rate | 4 of 76 (5.3%) per run | independent grading, 3 runs |
| Items that ever changed verdict | 23 of 76 (30%) | 3 pipeline configurations |
| Answers in the middle grade band | 45% | run 2026-08-11_224919 |
| Judge / independent assessor disagreement | 23 of 76 | run 2026-08-11_180323 |
| External expert review claims wrong against source | 5 of 11 | clause-by-clause verification |
| Re-ranker run-to-run noise floor | 0.007 on document-level MRR | two identical-input runs |
| Retrieval depth 20 → 50 | evidence recall 0.722 → 0.889, significant | paired bootstrap |
| Context width 5 → 10 | graded quality +0.079, CI [+0.020, +0.151] | paired bootstrap, 76 items |
