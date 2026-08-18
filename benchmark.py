#!/usr/bin/env python3
"""P42 — the benchmark. The 56 adopted questions against the pipeline.

Pre-registered in `P42_Benchmark_Run_Protocol.md` v1.0, which fixes the frame,
the metrics, the interval method, the per-class reporting rule, the drop rules
and the abort conditions BEFORE this ran. Nothing here chooses a number.

    56 adopted questions asked as `prompt_as_typed`  (protocol §1a)
    49 scored across 7 classes, 156 required claims   (§1)
    7 asked, published, NOT scored - two classes below the floor of 3
      and one carrying no weight                      (§1)

    HEADLINE  unweighted macro over the 7 scored class means   (§2)
    BESIDE IT operational weighted score, v3.13 renormalised   (§2)
    INTERVAL  stratified bootstrap, items resampled WITHIN class (§3)
    PER CLASS point estimate and n. NO interval - no class reaches
              the pre-registered n>=20 at which a percentile
              bootstrap says anything                          (§4)

THE FRAME IS A FILE, NOT A FIELD. `questions_v3.jsonl` carries 65 records at
`status == "ok"`; that is the AUTHORING validator's result, not the census
verdict. The adopted set is the 56 in the census `scored/` directory. The
framing measurement selected on the status field and put three census-REJECTED
questions into a published measurement (L5.46, rule 77). This module takes the
adoption record by path, pins its digest, and asserts its per-class counts
before it asks anything.

The pipeline is CALLED, not reimplemented: `ask_v2.answer()` is the one code
path, as in `context_effect.py`.

    python3 benchmark.py --self-test
    python3 benchmark.py --run \
        --adopted census/2026-08-14_135406/scored/adopted_2026-08-14_151129.jsonl \
        --judge-validation judge/.../judge_validation_summary_....json
"""
import argparse
import hashlib
import json
import os
import random
import sys
import time
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import claim_extract as ce                                   # noqa: E402
import claim_judge as cj                                     # noqa: E402
import question_gen as qg                                    # noqa: E402

VERSION = "1.0"
PREREG = "P42_Benchmark_Run_Protocol.md v1.0"
DESIGN = "P42_Design_Pipeline_and_Benchmark.md v3.13 sec 6.2 / 8"

# --- §3, inherited from context_effect rather than re-chosen (rule 60) ------
SEED = 42
BOOTSTRAP = 10000

# --- §4, pre-registered. No class here reaches it; none will print one. -----
MIN_N_FOR_CLASS_CI = 20

# --- the question protocol's §7 floor, applied to SURVIVING items (§5) -----
CLASS_FLOOR = 3

# --- design §6.2 v3.13, renormalised. Fractions of 85, kept as integers
# because that is the form that stays exact; §6.2 says so explicitly.
WEIGHT_NUM = {"multi_hop": 22, "nuance_applicability": 18, "table_numeric": 14,
              "definitional": 14, "boundary": 10, "ambiguous_acronym": 4,
              "identifier": 3}
WEIGHT_DENOM = 85
SCORED_CLASSES = tuple(sorted(WEIGHT_NUM))

# Asked and published, never scored. adversarial and applicability_authority
# are below the floor of 3 (design §6.2, PoC-lead decision 2026-08-14);
# acronym_paired carries no weight in the v3.8 set and is not a scored class.
UNSCORED_CLASSES = ("acronym_paired", "adversarial", "applicability_authority")

# §1. Asserted against the file, never trusted.
EXPECTED_COUNTS = {"multi_hop": 11, "boundary": 9, "table_numeric": 8,
                   "nuance_applicability": 7, "ambiguous_acronym": 6,
                   "definitional": 5, "identifier": 3, "acronym_paired": 3,
                   "adversarial": 2, "applicability_authority": 2}
EXPECTED_TOTAL = 56

# --- CAMPAIGN 3, protocol §11, pre-registered 2026-08-16 -------------------
# A second registered frame, added rather than replacing campaign 2's, so both
# runs stay reproducible from this file. 111 adopted questions on the widened
# 145-document corpus.
#
# NO WEIGHTED SCORE (§11b, PoC-lead decision). The v3.8 weights put 22/85 - the
# heaviest in the set - on multi_hop, which now holds six items; a quarter of
# the score would rest on six questions. The weights are not retracted, they
# stand as signed off and return when a draw supports them.
EXPECTED_COUNTS_C3 = {"ambiguous_acronym": 20, "identifier": 18,
                      "definitional": 16, "acronym_paired": 12,
                      "boundary": 12, "nuance_applicability": 11,
                      "adversarial": 9, "multi_hop": 6, "table_numeric": 6,
                      "applicability_authority": 1}
EXPECTED_TOTAL_C3 = 111

# Rebound by --campaign 3. WEIGHTED is False there per §11b.
WEIGHTED = True
# 8 scored. The two exclusions have DIFFERENT reasons and §11a says so:
# acronym_paired is a PROBE by design §6.2 ("not a capability score") at any
# size; applicability_authority is below the §7 floor of 3.
SCORED_CLASSES_C3 = ("adversarial", "ambiguous_acronym", "boundary",
                     "definitional", "identifier", "multi_hop",
                     "nuance_applicability", "table_numeric")
UNSCORED_CLASSES_C3 = ("acronym_paired", "applicability_authority")

# Scoring protocol §8, verbatim. Printed beside every claim-coverage figure.
CAVEAT = (
    "Claim coverage is measured by an entailment judge validated at 94% (campaign 2)\n"
    "  and 98% (campaign 3) agreement against MODEL reviewers' judgements of their own\n"
    "  answers - NOT human judgement (scoring protocol §7, §9, §10). On claims a reviewer\n"
    "  states its own answer MISSED, the judge scores 23% as present (n=100, campaign 3;\n"
    "  50% at n=10 in campaign 2; 57% on constructed truncations, §8).\n"
    "  CLAIM COVERAGE IS THEREFORE AN UPPER BOUND where completeness of qualification\n"
    "  is concerned.")

# Design §8 asks for "all required claims present AND no critical forbidden
# claim". The adopted set carries no forbidden claims at all, so only the first
# half is measurable. The metric is therefore reported under a weaker name with
# this sentence attached, rather than being called what it is not (protocol §2).
NOT_FULLY_CORRECT = (
    "NOT called 'fully correct': the adopted set carries no forbidden claims,\n"
    "     so the second half of design §8's definition is not measurable here.")

SMOKE_NOTE = (
    "SMOKE RUN - %d items. A wiring check. Its numbers are NOT the measurement,\n"
    "its summary is marked `smoke: true`, and it cannot be quoted as the\n"
    "benchmark (protocol §6).")


# ---------------------------------------------------------------------------
# the frame
def load_adopted(path):
    """The adopted set, by file. Returns (items, problems).

    Adoption is what this FILE contains. The `status` field is not consulted
    and must not be: it is the authoring validator's verdict and it says "ok"
    for nine questions the census rejected (rule 77).
    """
    items, problems = [], []
    for ln, line in enumerate(open(path), 1):
        if not line.strip():
            continue
        try:
            items.append(json.loads(line))
        except ValueError as e:
            problems.append("%s line %d is not JSON: %s" % (path, ln, e))
            return items, problems
    if len(items) != EXPECTED_TOTAL:
        problems.append("%s holds %d records, the adopted set is %d - this is "
                        "not the adjudicated file (rule 77)"
                        % (path, len(items), EXPECTED_TOTAL))
    got = Counter(r.get("class") for r in items)
    for cls in sorted(set(EXPECTED_COUNTS) | set(got)):
        if got.get(cls, 0) != EXPECTED_COUNTS.get(cls, 0):
            problems.append("class %r: file has %d, §1 expects %d"
                            % (cls, got.get(cls, 0),
                               EXPECTED_COUNTS.get(cls, 0)))
    for r in items:
        if not qg.required(r):
            problems.append("item %s carries no required claim - it cannot be "
                            "scored and must not be silently skipped"
                            % r.get("anchor_id"))
    return items, problems


def check_weights():
    if not WEIGHTED:
        return []          # §11b: no weighted score is computed this campaign
    """Rule 57: a weight set is checked against the class list, not against 1.0.

    The v3.7 set summed correctly while covering 7 of 10 classes for three
    revisions, which is exactly what a set with missing classes looks like.
    """
    problems = []
    if tuple(sorted(WEIGHT_NUM)) != SCORED_CLASSES:
        problems.append("weight keys %s are not the scored-class list %s"
                        % (tuple(sorted(WEIGHT_NUM)), SCORED_CLASSES))
    if sum(WEIGHT_NUM.values()) != WEIGHT_DENOM:
        problems.append("weights sum to %d/%d, not 1.0"
                        % (sum(WEIGHT_NUM.values()), WEIGHT_DENOM))
    overlap = set(WEIGHT_NUM) & set(UNSCORED_CLASSES)
    if overlap:
        problems.append("class(es) %s are both weighted and unscored"
                        % sorted(overlap))
    return problems


def digest(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def corpus_provenance():
    """Which corpus answered. Reported, never guessed - and never fatal.

    `retrieve.COLL` names the collection every answer was retrieved from. It
    was absent from this summary until the corpus grew from 88 documents to
    145 between two runs, at which point two records with the same question
    frame described two different systems and nothing in either said so.
    """
    try:
        import retrieve
        from qdrant_client import QdrantClient
        qc = QdrantClient(url=os.environ.get("P42_QDRANT",
                                             "http://localhost:6333"))
        info = qc.get_collection(retrieve.COLL)
        return {"collection": retrieve.COLL, "points": info.points_count}
    except Exception as e:
        return {"collection": None, "points": None,
                "error": "could not read the collection: %s" % str(e)[:120]}


# ---------------------------------------------------------------------------
# scoring one item
def item_coverage(item, answer_text, verdicts_fn=None):
    """(coverage, verdicts). coverage is None when a judgement is unparseable.

    None means NOT SCORED. It is never folded into a NO and never scored 0.0 -
    the retracted matcher's 31% was survivable partly because its failures
    looked like low scores rather than like failures.

    `verdicts_fn` takes (claim_texts, answer) and returns one verdict each.
    The run passes `cj.judge_answer`, which REFUSES unless the validation record
    says ACCEPTED - a second, independent check on top of run()'s own, because
    this module's whole reason for existing is that a scoring function was once
    used for an entire stage before anyone measured it.
    """
    req = qg.required(item)
    if not req:
        raise ValueError("item %s has no required claim; load_adopted() should "
                         "have aborted before this" % item.get("anchor_id"))
    vf = verdicts_fn or (lambda texts, a: [cj.judge(t, a) for t in texts])
    verdicts = vf([c.get("text", "") for c in req], answer_text)
    if len(verdicts) != len(req):
        raise ValueError("item %s: %d verdicts for %d required claims"
                         % (item.get("anchor_id"), len(verdicts), len(req)))
    if any(v is None for v in verdicts):
        return None, verdicts
    return sum(1 for v in verdicts if v) / float(len(req)), verdicts


# ---------------------------------------------------------------------------
# aggregation. Pure, so the self-test exercises the real arithmetic.
def aggregate(class_scores, weights=None):
    """Unweighted macro over classes, or weighted by WEIGHT_NUM.

    MACRO IS OVER CLASSES, NOT ITEMS (design §8): every class contributes
    equally whatever its size, so a class of 3 counts as much as one of 11.
    Weights are renormalised over the classes actually present, so a class
    dropping out cannot silently shrink the total.
    """
    cs = {c: v for c, v in class_scores.items() if v is not None}
    if not cs:
        return None
    if weights is None:
        return sum(cs.values()) / float(len(cs))
    tot = sum(weights.get(c, 0) for c in cs)
    if not tot:
        return None
    return sum(weights.get(c, 0) * cs[c] for c in cs) / float(tot)


def stratified_bootstrap(by_class, weights=None, n=BOOTSTRAP, seed=SEED):
    """95% percentile CI. Items resampled WITHIN class (protocol §3).

    The classes are a designed taxonomy - fixed strata, not a sample from a
    population of classes - so resampling classes would answer a question
    nobody asked. The item is the sampled unit within its stratum.
    """
    cls = sorted(c for c in by_class if by_class[c])
    if not cls:
        return None, None
    rnd = random.Random(seed)
    out = []
    for _ in range(n):
        means = {}
        for c in cls:
            vals = by_class[c]
            k = len(vals)
            means[c] = sum(rnd.choice(vals) for _ in range(k)) / float(k)
        out.append(aggregate(means, weights))
    out.sort()
    return out[int(0.025 * n)], out[int(0.975 * n) - 1]


# Every field the record takes from the pipeline result, copied by name.
#
# THIS LIST EXISTS BECAUSE A FIELD WAS SILENTLY DROPPED FOR TWO RUNS. The
# record was an inline dict literal naming each field individually, `ask_v2`
# began emitting `ranked` on 2026-08-16, and the literal was never updated -
# so the post-rerank ranking was thrown away by both campaign-3 runs and every
# rank statistic stayed uncomputable. A run was launched specifically to
# capture it and captured nothing (L5.49, rule 80).
#
# A named list is testable; an inline literal is not. Anything `ask_v2`
# returns that the scorecard needs belongs here.
PIPELINE_FIELDS = ("answer", "route", "rerank", "n_context", "n_retrieved",
                   "sources", "ranked", "model", "refused", "error",
                   "status", "confidence", "pipeline")

# Which system is measured. Resolved by name through the R40 contract; the
# default is our own pipeline behind its adapter. A run records this, because
# a score without the system that produced it is not a measurement.
PIPELINE = os.environ.get("P42_PIPELINE", "pipeline_ask_v2")


def pipeline_record(a):
    """The pipeline's half of the record. Pure, so it can be tested without a
    server - which is why the dropped field is now catchable."""
    return {k: a.get(k) for k in PIPELINE_FIELDS}


def class_ci_publishable(n):
    """§4, fixed before the run: only n >= 20 gets a per-class interval."""
    return n >= MIN_N_FOR_CLASS_CI


def class_bootstrap_ci(vals, n=BOOTSTRAP, seed=SEED):
    """Percentile bootstrap over the items of ONE class.

    This is the stratified bootstrap restricted to a single stratum - items
    resampled within their class - not a second method. Same seed, same
    replicate count, so it is reproducible on the same terms as the macro.
    """
    if not vals:
        return None
    rnd = random.Random(seed)
    k = len(vals)
    out = sorted(sum(rnd.choice(vals) for _ in range(k)) / float(k)
                 for _ in range(n))
    return out[int(0.025 * n)], out[int(0.975 * n) - 1]


def class_block(vals, cov, allreq):
    """One class's published figures.

    §4 SAYS n >= 20 GETS AN INTERVAL, AND FOR TWO CAMPAIGNS THIS RETURNED
    None FOR EVERY CLASS REGARDLESS OF n. `class_ci_publishable` was written
    and self-tested but never called here, so campaign 3's `ambiguous_acronym`
    - the first class ever to reach 20 - had its interval withheld with the
    arithmetically false reason "n=20 < 20". Defect corrected 2026-08-17,
    benchmark protocol §4a. The threshold is unchanged; the code now
    implements it. Publishing an interval §4 already required cannot flatter
    a result, and the macro is untouched.
    """
    n = len(vals)
    pub = class_ci_publishable(n)
    ci = class_bootstrap_ci(vals) if pub else None
    return {"n": n,
            "claim_coverage": round(cov, 4),
            "all_required_present": round(allreq, 4),
            "ci": None if ci is None else [round(ci[0], 4), round(ci[1], 4)],
            "ci_withheld_because": None if pub else
            "n=%d < %d (protocol §4)" % (n, MIN_N_FOR_CLASS_CI)}


def summarise(rows, bootstrap=BOOTSTRAP):
    """Everything derived from the item rows. No I/O, no model, no globals."""
    notes = []
    kept, dropped = [], []
    for r in rows:
        if r.get("error"):
            dropped.append((r, "pipeline error: %s" % str(r["error"])[:90]))
        elif r.get("coverage") is None:
            dropped.append((r, "a claim judgement came back unparseable"))
        else:
            kept.append(r)

    # Membership is SCORED_CLASSES, NOT the weight dict. They coincided in
    # campaign 2 and do not in campaign 3, where `adversarial` is scored but
    # carries no v3.8 weight - testing against WEIGHT_NUM dropped it from the
    # score in silence, which the item counts caught only by arithmetic.
    scored_rows = [r for r in kept if r["class"] in SCORED_CLASSES]
    cov_by, all_by = defaultdict(list), defaultdict(list)
    for r in scored_rows:
        cov_by[r["class"]].append(r["coverage"])
        all_by[r["class"]].append(1.0 if r["all_required"] else 0.0)

    # §5: a class whose SURVIVING n falls below the floor is reported unscored,
    # and the macro's denominator changes - which is stated, never inferred.
    unscored_by_drop = []
    for cls in SCORED_CLASSES:
        if cls not in cov_by:
            unscored_by_drop.append((cls, 0))
        elif len(cov_by[cls]) < CLASS_FLOOR:
            unscored_by_drop.append((cls, len(cov_by[cls])))
    for cls, n_ in unscored_by_drop:
        cov_by.pop(cls, None)
        all_by.pop(cls, None)
        notes.append("class %r has %d surviving item(s), below the floor of "
                     "%d - reported UNSCORED" % (cls, n_, CLASS_FLOOR))
    if unscored_by_drop:
        # counted AFTER every removal: computing it inside the loop reports the
        # denominator part-way through its own change, which is how a summary
        # ends up disagreeing with the table beneath it.
        notes.append("the macro is therefore over %d class(es), not %d - "
                     "stated here rather than left to be inferred from an "
                     "unchanged label"
                     % (len(cov_by), len(SCORED_CLASSES)))

    cls_cov = {c: sum(v) / float(len(v)) for c, v in cov_by.items()}
    cls_all = {c: sum(v) / float(len(v)) for c, v in all_by.items()}

    macro = aggregate(cls_cov)
    weighted = aggregate(cls_cov, WEIGHT_NUM) if WEIGHTED else None
    macro_all = aggregate(cls_all)
    m_lo, m_hi = stratified_bootstrap(cov_by, None, n=bootstrap)
    w_lo, w_hi = (stratified_bootstrap(cov_by, WEIGHT_NUM, n=bootstrap)
                  if WEIGHTED else (None, None))
    a_lo, a_hi = stratified_bootstrap(all_by, None, n=bootstrap)

    # published, not scored
    other = {}
    for cls in UNSCORED_CLASSES:
        v = [r["coverage"] for r in kept if r["class"] == cls]
        if v:
            other[cls] = {"n": len(v), "mean_coverage": sum(v) / float(len(v))}

    return {
        "n_asked": len(rows), "n_kept": len(kept), "n_dropped": len(dropped),
        "dropped": [{"item": r.get("item"), "class": r.get("class"),
                     "why": why} for r, why in dropped],
        "n_scored_items": sum(len(v) for v in cov_by.values()),
        "scored_classes": sorted(cov_by),
        "per_class": {c: class_block(cov_by[c], cls_cov[c], cls_all[c])
                      for c in sorted(cov_by)},
        "macro_claim_coverage": None if macro is None else round(macro, 4),
        "macro_ci95": None if m_lo is None else [round(m_lo, 4),
                                                 round(m_hi, 4)],
        "weighted_claim_coverage": None if weighted is None
        else round(weighted, 4),
        "weighted_ci95": None if w_lo is None else [round(w_lo, 4),
                                                    round(w_hi, 4)],
        "macro_all_required_present": None if macro_all is None
        else round(macro_all, 4),
        "all_required_ci95": None if a_lo is None else [round(a_lo, 4),
                                                        round(a_hi, 4)],
        "refusals": sum(1 for r in kept if r.get("refused")),
        "unscored_classes": other,
        "notes": notes,
    }


# ---------------------------------------------------------------------------
def run(adopted_path, validation_summary, outroot, limit=0):
    items, problems = load_adopted(adopted_path)
    problems += check_weights()
    if problems:
        print("ABORT - the frame is not what the protocol registered:")
        for p_ in problems:
            print("   " + p_)
        print("   Nothing was asked. Fix the frame or amend §1 with a reason.")
        return 1
    print("frame: %s" % adopted_path)
    print("  sha256 %s" % digest(adopted_path)[:16])
    print("  %d adopted items, %d scored across %d classes, %d required claims"
          % (len(items),
             sum(1 for r in items if r.get("class") in SCORED_CLASSES),
             len(SCORED_CLASSES),
             sum(len(qg.required(r)) for r in items
                 if r.get("class") in SCORED_CLASSES)))
    print("  asked and published but NOT scored: %s"
          % ", ".join("%s %d" % (c, EXPECTED_COUNTS[c])
                      for c in UNSCORED_CLASSES))

    s = json.load(open(validation_summary))
    if s.get("verdict") != "ACCEPTED":
        print("ABORT - the claim judge is not validated: %s says %r"
              % (validation_summary, s.get("verdict")))
        return 1
    print("judge: validated %s, recall %.2f - §8's upper-bound caveat applies"
          % (s.get("stamp"), s.get("recall") or 0.0))

    if limit:
        # round-robin across classes, never the head of an ordered list
        # (rule 71, and rule 75 for the fact that it had to be written twice).
        byc = defaultdict(list)
        for it in sorted(items, key=lambda r: r["anchor_id"]):
            byc[it.get("class")].append(it)
        picked, order = [], sorted(byc)
        while len(picked) < limit and any(byc[c] for c in order):
            for c in order:
                if byc[c] and len(picked) < limit:
                    picked.append(byc[c].pop(0))
        items = picked
        print("\n" + SMOKE_NOTE % limit)

    if not ce.preflight():
        return 1
    # The pipeline is resolved by NAME through the R40 contract, so the
    # benchmark can be pointed at any system that returns the agreed shape.
    # The default is our own, behind its adapter - identical behaviour, since
    # the adapter only adds `status` and a null `confidence` to what ask_v2
    # already returned.
    import pipelines
    ask_fn = pipelines.load(PIPELINE)
    print("pipeline: %s (R40 contract)" % PIPELINE)

    # judge_answer re-checks the ACCEPTED record on every call and raises if it
    # is not. run() checked it above; this is the check that cannot be skipped
    # by a future caller that forgets the first one.
    def judge(texts, ans):
        return cj.judge_answer(texts, ans, validation_summary)

    rows, t0 = [], time.time()
    for n, it in enumerate(sorted(items, key=lambda r: r["anchor_id"]), 1):
        req = qg.required(it)
        query = it.get("prompt_as_typed") or "%s %s" % (it.get("context", ""),
                                                        it.get("question", ""))
        a = pipelines.normalise(ask_fn(query))
        a["pipeline"] = PIPELINE          # which system produced this row
        bad = pipelines.validate(a, strict=False)
        if bad:
            a = dict(a, error="contract: " + "; ".join(bad[:2]))
        cov, verdicts = (None, []) if a.get("error") \
            else item_coverage(it, a.get("answer") or "", judge)
        row = {"item": it["anchor_id"], "class": it.get("class"),
               "query": query, "n_required": len(req)}
        row.update(pipeline_record(a))
        row.update({
            "coverage": cov,
            "claims_reached": sum(1 for v in verdicts if v),
            "all_required": (cov is not None and cov >= 1.0),
            "verdicts": {c.get("id"): v for c, v in zip(req, verdicts)},
            "optional_claims": len(it.get("claims") or []) - len(req)})
        rows.append(row)
        print("  %2d/%d  %-12s %-22s %s%s"
              % (n, len(items), rows[-1]["item"], rows[-1]["class"],
                 "%.2f" % cov if cov is not None else "NOT SCORED",
                 "  REFUSED" if rows[-1]["refused"] else ""))
    dt = time.time() - t0

    summ = summarise(rows)
    stamp = time.strftime("%Y-%m-%d_%H%M%S")
    outdir = os.path.join(outroot, stamp)
    os.makedirs(outdir, exist_ok=True)
    rp = os.path.join(outdir, "benchmark_%s.jsonl" % stamp)
    with open(rp, "w") as f:
        for r in rows:
            f.write(json.dumps(r, sort_keys=True) + "\n")

    print("\n  %d items in %.0fs (%.0fs per item)"
          % (len(rows), dt, dt / max(1, len(rows))))
    if summ["n_dropped"]:
        print("  %d item(s) NOT SCORED - named, counted, never zeroed:"
              % summ["n_dropped"])
        for d in summ["dropped"]:
            print("     %-12s %-22s %s" % (d["item"], d["class"], d["why"]))
    for note in summ["notes"]:
        print("  NOTE %s" % note)

    print("\n  TRACK A. claim coverage, %d items over %d scored classes"
          % (summ["n_scored_items"], len(summ["scored_classes"])))
    print("  %-24s %3s %14s %14s" % ("class", "n", "coverage", "all-required"))
    for c in sorted(summ["per_class"]):
        pc = summ["per_class"][c]
        print("  %-24s %3d %14.3f %14.3f"
              % (c, pc["n"], pc["claim_coverage"],
                 pc["all_required_present"]))
    _with = [c for c, pc in summ["per_class"].items() if pc["ci"]]
    if _with:
        print("  per-class 95%% CI, published only at n >= %d (protocol §4):"
              % MIN_N_FOR_CLASS_CI)
        for c in sorted(_with):
            pc = summ["per_class"][c]
            print("     %-22s n=%-3d [%.3f, %.3f]"
                  % (c, pc["n"], pc["ci"][0], pc["ci"][1]))
        print("  every other class is below %d and its interval is withheld."
              % MIN_N_FOR_CLASS_CI)
    else:
        print("  (no per-class interval: protocol §4 publishes one only at "
              "n >= %d, and the largest class here is %d)"
              % (MIN_N_FOR_CLASS_CI,
                 max([pc["n"] for pc in summ["per_class"].values()] or [0])))

    def fig(v, ci):
        if v is None:
            return "n/a"
        return "%.3f%s" % (v, "" if ci is None
                           else "   95%% CI [%.3f, %.3f]" % (ci[0], ci[1]))

    print("\n  HEADLINE - unweighted macro claim coverage over %d classes"
          % len(summ["scored_classes"]))
    print("     %s" % fig(summ["macro_claim_coverage"], summ["macro_ci95"]))
    if WEIGHTED:
        print("  operational weighted score (design §6.2, v3.13 renormalised)")
        print("     %s" % fig(summ["weighted_claim_coverage"],
                              summ["weighted_ci95"]))
        print("     the weighting was justified by failure risk, and the two "
              "highest-risk\n     classes are the two that fell below the "
              "floor and cannot contribute.")
    else:
        print("  NO WEIGHTED SCORE this campaign (protocol §11b, PoC lead).")
        print("     The v3.8 weights put 22/85 - the heaviest - on multi_hop, "
              "which holds 6\n     items: a quarter of the score would rest on "
              "six questions. The weights are\n     NOT retracted; they return "
              "when a draw supports them.")
    print("  all required claims present (design §8's second metric)")
    print("     %s" % fig(summ["macro_all_required_present"],
                          summ["all_required_ci95"]))
    print("     " + NOT_FULLY_CORRECT)
    print("  refusals: %d of %d answered items (scored, never dropped - a "
          "pipeline\n     that declined hard questions would otherwise raise "
          "its own score)" % (summ["refusals"], summ["n_kept"]))

    if summ["unscored_classes"]:
        print("\n  asked and published, NOT scored (protocol §1):")
        for c in sorted(summ["unscored_classes"]):
            u = summ["unscored_classes"][c]
            print("     %-24s n=%d  coverage %.3f  - descriptive only"
                  % (c, u["n"], u["mean_coverage"]))

    print("\n  %s" % CAVEAT)

    summ.update({"version": VERSION, "prereg": PREREG, "design": DESIGN,
                 "stamp": stamp, "smoke": bool(limit), "limit": limit or 0,
                 "adopted_record": adopted_path,
                 "adopted_sha256": digest(adopted_path),
                 "judge_validation": validation_summary,
                 "pipeline": PIPELINE,
                 "seed": SEED, "bootstrap": BOOTSTRAP,
                 "min_n_for_class_ci": MIN_N_FOR_CLASS_CI,
                 "weights": {c: "%d/%d" % (WEIGHT_NUM[c], WEIGHT_DENOM)
                             for c in WEIGHT_NUM} if WEIGHTED else None,
                 "generation": {"temperature": 0.0, "thinking": ce.THINKING,
                                "model": ce.ROUTE["model"],
                                "route": ce.ROUTE["path"]},
                 # WHICH CORPUS. Without this, two runs on different corpora
                 # differ only by timestamp - and the corpus went from 88
                 # documents to 145 between two runs of this very file, which
                 # is exactly when a reader needs to be able to tell them
                 # apart. The frame (the questions) was already pinned by
                 # sha256; the corpus was not pinned at all.
                 "corpus": corpus_provenance(),
                 "elapsed_s": round(dt, 1), "records": rp,
                 "caveat": " ".join(CAVEAT.split())})
    sp = os.path.join(outdir, "benchmark_summary_%s.json" % stamp)
    open(sp, "w").write(json.dumps(summ, indent=2, sort_keys=True) + "\n")
    if limit:
        print("\n  SMOKE RUN (--limit %d): `smoke: true`. The measurement is "
              "the whole adopted set." % limit)
    print("\n  records -> %s\n  summary -> %s" % (rp, sp))
    return 0


# ---------------------------------------------------------------------------
def selftest():
    fails, ran = [], [0]

    def ck(name, cond):
        ran[0] += 1
        print("  %-68s %s" % (name, "ok" if cond else "FAIL"))
        if not cond:
            fails.append(name)

    src = open(os.path.abspath(__file__)).read()

    def item(aid, cls, n_req, n_opt=0, status="ok"):
        cl = [{"id": "C%d" % i, "tier": "required", "text": "claim %d" % i}
              for i in range(1, n_req + 1)]
        cl += [{"id": "O%d" % i, "tier": "optional", "text": "opt %d" % i}
               for i in range(1, n_opt + 1)]
        return {"anchor_id": aid, "class": cls, "status": status,
                "claims": cl, "question": "q?", "context": "ctx.",
                "prompt_as_typed": "ctx. q?"}

    def full_set(**over):
        out, i = [], 0
        for cls, n in EXPECTED_COUNTS.items():
            for _ in range(over.get(cls, n)):
                i += 1
                out.append(item("A-%03d" % i, cls, 2))
        return out

    def write(td, name, recs):
        p = os.path.join(td, name)
        open(p, "w").write("".join(json.dumps(r) + "\n" for r in recs))
        return p

    # --- rule 57: the weight set, checked against the class list ------------
    ck("campaign 3's frame is a SECOND registered set, campaign 2 untouched",
       EXPECTED_TOTAL == 56 and EXPECTED_TOTAL_C3 == 111
       and sum(EXPECTED_COUNTS_C3.values()) == 111)
    ck("campaign 3 scores 8 classes; the two exclusions differ in reason",
       len(SCORED_CLASSES_C3) == 8
       and set(SCORED_CLASSES_C3) | set(UNSCORED_CLASSES_C3)
       == set(EXPECTED_COUNTS_C3)
       and "acronym_paired" in UNSCORED_CLASSES_C3)
    ck("acronym_paired is excluded as a PROBE, not for size - it has 12 items",
       EXPECTED_COUNTS_C3["acronym_paired"] == 12
       and EXPECTED_COUNTS_C3["acronym_paired"] > CLASS_FLOOR)
    ck("adversarial becomes scoreable in campaign 3 and was not in campaign 2",
       "adversarial" in SCORED_CLASSES_C3
       and "adversarial" in UNSCORED_CLASSES)
    ck("scored membership uses SCORED_CLASSES, never the weight dict - they "
       "differ in campaign 3",
       ('in SCORED_' + 'CLASSES]') in src
       and set(SCORED_CLASSES_C3) != set(WEIGHT_NUM)
       and "adversarial" in SCORED_CLASSES_C3
       and "adversarial" not in WEIGHT_NUM)
    ck("with no weighted score, the rule-57 weight check does not fire",
       check_weights() == [])
    ck("the weight keys are exactly the scored-class list (rule 57)",
       check_weights() == [] and set(WEIGHT_NUM) == set(SCORED_CLASSES))
    ck("the weights sum to 1.0 as fractions of 85",
       abs(sum(WEIGHT_NUM.values()) / float(WEIGHT_DENOM) - 1.0) < 1e-12)
    ck("no class is both weighted and published-unscored",
       not (set(WEIGHT_NUM) & set(UNSCORED_CLASSES)))
    ck("the 7 scored classes and 3 unscored ones account for all 10",
       len(set(WEIGHT_NUM) | set(UNSCORED_CLASSES)) == 10
       and set(WEIGHT_NUM) | set(UNSCORED_CLASSES) == set(EXPECTED_COUNTS))
    ck("the expected counts sum to the adopted 56",
       sum(EXPECTED_COUNTS.values()) == EXPECTED_TOTAL)

    import tempfile
    with tempfile.TemporaryDirectory() as td:
        good = write(td, "good.jsonl", full_set())
        gi, gp = load_adopted(good)
        ck("a correct adoption record loads with no problems",
           gp == [] and len(gi) == EXPECTED_TOTAL)

        # rule 77: adoption is the FILE. A record the authoring validator
        # marked `dropped` is still adopted if this file holds it.
        odd = full_set()
        odd[0]["status"] = "dropped"
        ck("adoption is the FILE, not the `status` field (rule 77)",
           load_adopted(write(td, "odd.jsonl", odd))[1] == [])

        short = full_set(multi_hop=10)
        sp_ = write(td, "short.jsonl", short)
        ck("a file with the wrong record count ABORTS by name",
           any("is not the adjudicated file" in x
               for x in load_adopted(sp_)[1]))
        ck("a class whose count differs from §1 is NAMED with both numbers",
           any("multi_hop" in x and "expects 11" in x
               for x in load_adopted(sp_)[1]))

        swapped = full_set(multi_hop=10, boundary=10)
        ck("a swap that keeps the TOTAL at 56 is still caught per class",
           len(swapped) == EXPECTED_TOTAL
           and any("multi_hop" in x for x in
                   load_adopted(write(td, "sw.jsonl", swapped))[1]))

        noreq = full_set()
        noreq[0]["claims"] = [{"id": "O1", "tier": "optional", "text": "o"}]
        ck("an item carrying no required claim ABORTS rather than being "
           "skipped", any("no required claim" in x for x in
                          load_adopted(write(td, "nr.jsonl", noreq))[1]))

    # --- scoring one item, with an injected judge --------------------------
    it3 = item("A-1", "multi_hop", 3)
    ck("coverage is required claims reached over required claims",
       item_coverage(it3, "a",
                     lambda ts, a: [t != "claim 2" for t in ts])[0] == 2 / 3.0)
    ck("an unparseable judgement returns None, not a zero",
       item_coverage(it3, "a", lambda ts, a: [None if t == "claim 2" else True
                                              for t in ts])[0] is None)
    ck("optional claims are not scored",
       item_coverage(item("A-2", "multi_hop", 2, n_opt=5), "a",
                     lambda ts, a: [True] * len(ts))[0] == 1.0)
    try:
        item_coverage(it3, "a", lambda ts, a: [True, True])
        short_verdicts_caught = False
    except ValueError as e:
        short_verdicts_caught = "2 verdicts for 3" in str(e)
    ck("a judge returning fewer verdicts than claims ABORTS by name",
       short_verdicts_caught)
    ck("the run scores through judge_answer, which refuses an unvalidated "
       "judge", "cj.judge_answer(texts, ans, validation_summary)" in src
       and ("item_coverage(it, a.get(\"answer\") or \"\", " + "judge)") in src)

    # --- aggregation: macro is over CLASSES, not items ---------------------
    macro_case = {"a": 1.0, "b": 0.0}
    ck("the macro is the unweighted mean over CLASSES",
       aggregate(macro_case) == 0.5)
    rows = ([{"class": "a", "coverage": 1.0, "all_required": True,
              "error": None, "item": "x"}]
            + [{"class": "b", "coverage": 0.0, "all_required": False,
                "error": None, "item": "y%d" % i} for i in range(4)])
    ck("a small class counts as much as a large one (macro != item mean)",
       abs(aggregate({"a": 1.0, "b": 0.0}) - 0.5) < 1e-12
       and abs(sum(r["coverage"] for r in rows) / len(rows) - 0.2) < 1e-12)
    ck("the weighted score uses the renormalised fractions of 85",
       abs(aggregate({c: 1.0 for c in SCORED_CLASSES}, WEIGHT_NUM) - 1.0)
       < 1e-12
       and abs(aggregate({"multi_hop": 1.0, "identifier": 0.0}, WEIGHT_NUM)
               - 22 / 25.0) < 1e-12)
    ck("weights RENORMALISE over the classes present, never over 85 blindly",
       abs(aggregate({"multi_hop": 1.0}, WEIGHT_NUM) - 1.0) < 1e-12)

    # --- drops -------------------------------------------------------------
    def srow(cls, cov, **kw):
        r = {"item": kw.get("item", "I-%s-%s" % (cls, cov)), "class": cls,
             "coverage": cov, "all_required": (cov == 1.0), "error": None,
             "refused": False}
        r.update(kw)
        return r

    base = []
    for cls in SCORED_CLASSES:
        base += [srow(cls, 1.0, item="%s%d" % (cls, i)) for i in range(3)]
    s_ok = summarise(base, bootstrap=200)
    ck("a clean set scores 1.000 over all 7 classes",
       s_ok["macro_claim_coverage"] == 1.0
       and len(s_ok["scored_classes"]) == 7)

    with_err = base + [srow("multi_hop", None, item="E1",
                            error="LLM: connection refused")]
    s_err = summarise(with_err, bootstrap=200)
    ck("a pipeline error DROPS the item and is not scored as 0.0",
       s_err["n_dropped"] == 1 and s_err["macro_claim_coverage"] == 1.0
       and "E1" in [d["item"] for d in s_err["dropped"]])
    ck("the drop is named with its reason, not just counted",
       any("connection refused" in d["why"] for d in s_err["dropped"]))
    s_unp = summarise(base + [srow("multi_hop", None, item="U1")],
                      bootstrap=200)
    ck("an unparseable judgement DROPS the item and is named",
       s_unp["n_dropped"] == 1
       and any("unparseable" in d["why"] for d in s_unp["dropped"]))

    refused = base + [srow("multi_hop", 0.0, item="R1", refused=True)]
    s_ref = summarise(refused, bootstrap=200)
    ck("a REFUSAL is scored, not dropped - a pipeline cannot raise its score "
       "by declining", s_ref["n_dropped"] == 0 and s_ref["refusals"] == 1
       and s_ref["macro_claim_coverage"] < 1.0)

    thin = [r for r in base if r["class"] != "identifier"]
    thin += [srow("identifier", 1.0, item="id0")]
    s_thin = summarise(thin, bootstrap=200)
    ck("a class below the floor of 3 after drops is reported UNSCORED",
       "identifier" not in s_thin["scored_classes"]
       and len(s_thin["scored_classes"]) == 6)
    ck("the macro's denominator change is STATED, not left to be inferred",
       any("therefore over 6 class(es), not 7" in n for n in s_thin["notes"]))
    ck("the denominator is counted after ALL removals, not part-way through",
       len([n for n in s_thin["notes"] if "therefore over" in n]) == 1)

    # --- the second metric --------------------------------------------------
    partial = [srow(c, 1.0, item="p%s" % c) for c in SCORED_CLASSES] * 3
    partial = [dict(r, item="%s%d" % (r["item"], i))
               for i, r in enumerate(partial)]
    two_thirds = [dict(r, coverage=2 / 3.0, all_required=False)
                  for r in partial]
    s_two = summarise(two_thirds, bootstrap=200)
    ck("all-required-present is STRICTER than coverage (2 of 3 scores 0)",
       abs(s_two["macro_claim_coverage"] - 2 / 3.0) < 1e-4
       and s_two["macro_all_required_present"] == 0.0)
    ck("the forbidden-claim half of design §8 is named as absent, not "
       "silently dropped",
       ("forbidden " + "claims") in NOT_FULLY_CORRECT
       and ("not " + "measurable") in NOT_FULLY_CORRECT
       and ("+ NOT_FULLY" + "_CORRECT") in src)

    # --- the interval -------------------------------------------------------
    const = {c: [0.5] * 5 for c in SCORED_CLASSES}
    lo, hi = stratified_bootstrap(const, None, n=300)
    ck("the bootstrap of a constant sample has zero width",
       abs(lo - 0.5) < 1e-9 and abs(hi - 0.5) < 1e-9)
    spread = {c: [0.0, 1.0] * 5 for c in SCORED_CLASSES}
    lo2, hi2 = stratified_bootstrap(spread, None, n=800)
    ck("a spread sample produces an interval with real width", hi2 - lo2 > 0.05)
    ck("the bootstrap is seeded, so the interval is reproducible",
       stratified_bootstrap(spread, None, n=300)
       == stratified_bootstrap(spread, None, n=300))
    one_class = {"multi_hop": [0.0, 1.0] * 5}
    ck("resampling is WITHIN class - a class of constants cannot move",
       stratified_bootstrap({"a": [0.4] * 4, "b": [0.6] * 4}, None,
                            n=200) == (0.5, 0.5))
    ck("the weighted interval differs from the unweighted one",
       stratified_bootstrap(spread, WEIGHT_NUM, n=800)
       != stratified_bootstrap(spread, None, n=800))
    ck("an empty set yields no interval rather than a spurious one",
       stratified_bootstrap({}, None, n=10) == (None, None))
    del one_class

    # --- §4, the per-class rule --------------------------------------------
    ck("no per-class CI is published below n=20, fixed before the run",
       MIN_N_FOR_CLASS_CI == 20 and not class_ci_publishable(11)
       and not class_ci_publishable(19) and class_ci_publishable(20))
    ck("campaign 2 had no class at the floor; campaign 3 has one",
       max(EXPECTED_COUNTS[c] for c in SCORED_CLASSES) < MIN_N_FOR_CLASS_CI
       and max(EXPECTED_COUNTS_C3[c] for c in SCORED_CLASSES_C3)
       >= MIN_N_FOR_CLASS_CI)
    # The rule was STATED and self-tested as a predicate for two campaigns
    # while the reporting path hardcoded None. These test the wiring, which
    # is what was actually broken.
    ck("a class AT the floor is given its interval, not just declared eligible",
       class_block([0.8] * MIN_N_FOR_CLASS_CI, 0.8, 0.8)["ci"] is not None)
    ck("a class one item below the floor is withheld, and says why",
       class_block([0.8] * (MIN_N_FOR_CLASS_CI - 1), 0.8, 0.8)["ci"] is None
       and "%d < %d" % (MIN_N_FOR_CLASS_CI - 1, MIN_N_FOR_CLASS_CI)
       in class_block([0.8] * (MIN_N_FOR_CLASS_CI - 1), 0.8,
                      0.8)["ci_withheld_because"])
    ck("a published interval brackets the class mean",
       class_block([0.0, 1.0] * MIN_N_FOR_CLASS_CI, 0.5, 0.5)["ci"][0]
       <= 0.5 <=
       class_block([0.0, 1.0] * MIN_N_FOR_CLASS_CI, 0.5, 0.5)["ci"][1])
    ck("a class with no spread gives a degenerate interval, not a crash",
       class_block([1.0] * MIN_N_FOR_CLASS_CI, 1.0, 1.0)["ci"] == [1.0, 1.0])
    ck("the per-class bootstrap is reproducible on the same seed",
       class_bootstrap_ci([0.3, 0.9] * 10)
       == class_bootstrap_ci([0.3, 0.9] * 10))
    ck("every per-class row carries an interval XOR the reason it has none",
       all((s_ok["per_class"][c]["ci"] is not None)
           != (s_ok["per_class"][c]["ci_withheld_because"] is not None)
           for c in s_ok["per_class"]))

    # --- what the run says --------------------------------------------------
    # --- the record shape, which had no test at all until it lost a field ---
    _need = ("rank" + "ed", "sour" + "ces", "ans" + "wer", "refu" + "sed")
    ck("every field the scorecard needs is copied from the pipeline by name",
       all(f in PIPELINE_FIELDS for f in _need))
    ck("the ranking reaches the record intact, not just the surviving context",
       pipeline_record({"ranked": [{"point_id": "p1", "doc": "D"}],
                        "sources": [{"doc": "D"}]})["ranked"]
       == [{"point_id": "p1", "doc": "D"}])
    ck("a pipeline that emits no ranking yields None, never a silent {}",
       pipeline_record({"answer": "a"})["ranked"] is None)
    ck("a field ask_v2 emits but PIPELINE_FIELDS omits cannot reach the record",
       "extra" not in pipeline_record({"extra": 1, "answer": "a"}))
    ck("the record is built from the named list, not an inline literal",
       "row.update(pipeline_" + "record(a))" in src)

    ck("the pipeline is resolved by NAME through the R40 contract",
       "pipelines.load(PIPELINE)" in src and "ask_fn(query)" in src
       and ("SYSTEM" + "_PROMPT") not in src)
    ck("the default pipeline is ours, behind its adapter",
       PIPELINE == "pipeline_ask_v2")
    ck("a response that breaks the contract is DROPPED by name, not scored",
       'error="contract: "' in src)
    ck("the run records WHICH system was measured, in the summary AND per row",
       '"pipeline": PIPELINE' in src and 'a["pipeline"] = PIPELINE' in src)
    ck("the question is asked as `prompt_as_typed`, the form the census "
       "reviewers saw", '"prompt_as_typed"' in src)
    ck("scoring ABORTS unless the judge's record says ACCEPTED",
       's.get("verdict") != "ACCEPTED"' in src)
    ck("the run ABORTS before asking anything if the frame is wrong",
       "Nothing was " + "asked" in src)
    ck("§8's upper-bound caveat is carried into the output, with both of its "
       "numbers",
       ("UPPER " + "BOUND") in CAVEAT and "94%" in CAVEAT and "57%" in CAVEAT
       and ("% " + "CAVEAT") in src)
    ck("a limited run spreads across classes instead of taking the head "
       "(rule 71/75)", "round-robin across classes" in src)
    ck("a limited run is MARKED smoke and cannot be quoted as the benchmark",
       '"smoke": bool(limit)' in src
       and ("NOT the " + "measurement") in SMOKE_NOTE
       and ("SMOKE_NOTE " + "%") in src)
    ck("the run records the frame's digest, not just its path",
       '"adopted_sha256"' in src and "def digest" in src)
    cp = corpus_provenance()
    ck("the run records WHICH CORPUS answered, not only which questions",
       isinstance(cp, dict) and "collection" in cp and "points" in cp
       and '"corpus": corpus_provenance()' in src)
    ck("an unreachable corpus is reported by name, never fatal to the record",
       "could not read the collection" in src)
    ck("generation settings are recorded in the summary (rule 59)",
       '"generation"' in src and '"thinking": ce.THINKING' in src)
    ck("the record keeps the retrieval evidence for later analysis",
       '"sources": a.get("sources")' in src and '"route"' in src)

    print("\n  %d assertions, %d failed" % (ran[0], len(fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.
                                 RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--adopted", metavar="ADOPTED_JSONL",
                    help="the adjudicated adoption record - NOT "
                         "questions_v3.jsonl (rule 77)")
    ap.add_argument("--judge-validation", metavar="SUMMARY_JSON",
                    help="the ACCEPTED record from claim_judge --validate")
    ap.add_argument("--out", default=os.path.expanduser("~/p42/benchmark"))
    ap.add_argument("--campaign", type=int, default=2, choices=(2, 3),
                    help="which registered frame. 3 = the 111 adopted "
                         "questions on the 145-document corpus, 8 scored "
                         "classes, NO weighted score (protocol §11).")
    ap.add_argument("--pipeline", default=None,
                    help="name of a module exposing answer(q) per the R40 "
                         "contract (default: pipeline_ask_v2)")
    ap.add_argument("--limit", type=int, default=0,
                    help="smoke only; marks the summary and disqualifies it")
    a = ap.parse_args()
    if a.self_test:
        sys.exit(selftest())
    if a.pipeline:
        globals()["PIPELINE"] = a.pipeline
    if a.campaign == 3:
        g = globals()
        g["EXPECTED_COUNTS"] = EXPECTED_COUNTS_C3
        g["EXPECTED_TOTAL"] = EXPECTED_TOTAL_C3
        g["SCORED_CLASSES"] = SCORED_CLASSES_C3
        g["UNSCORED_CLASSES"] = UNSCORED_CLASSES_C3
        g["WEIGHTED"] = False
        g["PREREG"] = "P42_Benchmark_Run_Protocol.md v2.0 §11"
    if a.run:
        if not (a.adopted and a.judge_validation):
            ap.error("--run needs --adopted and --judge-validation")
        sys.exit(run(a.adopted, a.judge_validation, a.out, a.limit))
    ap.print_help()
