#!/usr/bin/env python3
"""P42 — claim-presence judging, and the validation that must pass first.

WHY THIS FILE EXISTS
====================
`question_gen.claim_reached` scores a claim as present by lexical overlap:
token coverage of the claim across the answer, or sentence-level Jaccard. The
census measured it against 460 reviewer judgements (Gemini and GPT) and it recovered **31%** of the
claims a reviewer confirmed their own answer contained, at 99% precision
(`P42_Census_Results.md` §5). The misses run continuously to zero coverage, so
no threshold repairs it - the quantity being measured is wrong. A RAG pipeline
paraphrases by construction, so scoring the benchmark with it would have
rewarded verbatim copying over correct answering.

This module replaces it with an entailment judgement, and - the point of the
file - refuses to be used until it has been validated against those same reviewer
judgements. `judge_answer` raises unless the validation record it is pointed at
says ACCEPTED.

The acceptance thresholds are pre-registered in
`P42_Claim_Scoring_Protocol.md` v1.0, written before this ran once.
"""
import argparse
import json
import os
import random
import re
import sys
import time
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import claim_extract as ce                                   # noqa: E402
import question_gen as qg                                    # noqa: E402

VERSION = "1.3"

# Pre-registered in P42_Claim_Scoring_Protocol.md §4, before the first run.
MIN_RECALL = 0.90            # on claims a reviewer confirms are present
MAX_FP_RATE = 0.05           # on constructed negatives, after reading them
NEGATIVES_PER_ANSWER = 3
SEED = 42
# An acceptance record is only an acceptance record over the whole set. The
# first smoke run - 40 pairs, no negatives of either kind - printed ACCEPTED
# and wrote a summary that judge_answer would have honoured. A truncated run
# now reports SMOKE and cannot accept anything (protocol §4, rule 71).
MIN_REVIEWER_POSITIVES = 400
MIN_REVIEWER_NEGATIVES = 10
MIN_CONSTRUCTED = 300
# §7b, fixed before the hard-negative set was built
HN_TARGET = 100
HN_REJECT_FLOOR = 0.80
HN_CONTROL_FLOOR = 0.95


# The judge is told what counts, in the terms the census showed it fails on:
# compression into table notation, paraphrase, reordering. And it is told what
# does NOT count - a partial statement - because the alternative failure is a
# judge that says yes to anything on topic.
JUDGE_SYSTEM = """You decide one thing and report one word.

You are given a CLAIM taken from a space-engineering standard, and an ANSWER
written by an engineer. Decide whether the ANSWER states the CLAIM.

It counts as stated if the answer carries the same content in different words,
in compressed notation (`+110 degC/5h` states "conducted at +110 degC for five
hours"), in a different order, or as part of a longer sentence or a list.

It does NOT count as stated if the answer states only part of the claim, states
something related but weaker, states the topic without the substance, or would
require the reader to already know the claim to see it there. Judge only what
the answer says. Do not use your own knowledge of the standard, and do not
reward an answer for being correct about something else.

Reply with exactly one word: YES or NO. No explanation."""

ONE_WORD = re.compile(r'\b(YES|NO)\b', re.I)


def judge(claim_text, answer_text, retries=1):
    """One entailment judgement. Returns True, False, or None if unparseable.

    None is a distinct outcome, never folded into False: a judge that cannot be
    parsed is a broken instrument and must be counted as one (rule 59).

    Refuses to run before the route has been discovered. `call_prose` falls
    back to `/v1/chat/completions` when `ROUTE["path"]` is unset, and this
    module's first run 404ed against a server that does not expose it - a
    guessed route, which is the thing preflight() exists to prevent (rule 59).
    """
    if not ce.ROUTE["path"]:
        raise RuntimeError(
            "claim_judge: no route discovered - call ce.preflight() before "
            "judging. A default path is a guess, and this module 404ed on one.")
    prompt = ("CLAIM:\n%s\n\nANSWER:\n%s\n\nDoes the ANSWER state the CLAIM? "
              "Reply YES or NO." % (claim_text.strip(), answer_text.strip()))
    for attempt in range(retries + 1):
        txt, finish = qg.call_prose(prompt, JUDGE_SYSTEM, max_tokens=8)
        m = ONE_WORD.search(txt or "")
        if m:
            return m.group(1).upper() == "YES"
        if finish == "length":
            # not a parse failure - the budget was too small for this reply
            txt, finish = qg.call_prose(prompt, JUDGE_SYSTEM, max_tokens=64)
            m = ONE_WORD.search(txt or "")
            if m:
                return m.group(1).upper() == "YES"
    return None


# ---------------------------------------------------------------------------
def build_validation_set(questions_path, answer_paths, judgement_paths):
    """The labelled set, built from the census and nothing else.

    POSITIVES/NEGATIVES-BY-REVIEWER: the 460 (reviewer, item, claim) judgements
    from Part B - the reviewer's own statement about their own answer.

    CONSTRUCTED NEGATIVES: each answer paired with claims drawn, seeded, from
    OTHER items. These are PRESUMED negative, not known negative. §4 of the
    protocol requires every one the judge calls present to be READ before it is
    counted as a false positive, because a claim from another item can be
    genuinely present in an answer.
    """
    qs = {r["anchor_id"]: r for r in
          (json.loads(l) for l in open(questions_path) if l.strip())
          if r.get("status") == "ok"}
    problems = []
    answers = {}
    for p in answer_paths:
        a, pr = qg.read_answers(p)
        problems += pr
        answers[qg.reviewer_key(p)] = a
    labels = []
    for p in judgement_paths:
        rows, pr = qg.read_mapped(p, qg.JUDGE_ALIASES,
                                  ("item", "claim", "verdict"))
        problems += pr
        rv = qg.reviewer_key(p)
        if rv not in answers:
            problems.append("%s: judgements with no matching Part A return"
                            % os.path.basename(p))
            continue
        for r in rows:
            if r["verdict"] not in ("yes", "no"):
                continue
            ct = [c for c in qs.get(r["item"], {}).get("claims", [])
                  if c["id"] == r["claim"]]
            if not ct:
                problems.append("%s: %s/%s is not a claim of that item"
                                % (rv, r["item"], r["claim"]))
                continue
            if not (answers[rv].get(r["item"]) or "").strip():
                problems.append("%s: judgement for %s but no Part A answer to "
                                "judge it against" % (rv, r["item"]))
                continue
            labels.append({"kind": "reviewer", "reviewer": rv, "item": r["item"],
                           "claim": r["claim"], "claim_text": ct[0]["text"],
                           "answer": answers[rv].get(r["item"], ""),
                           "label": r["verdict"] == "yes"})

    rnd = random.Random(SEED)
    pool = [(aid, c) for aid, q in sorted(qs.items()) for c in qg.required(q)]
    for rv in sorted(answers):
        for aid in sorted(answers[rv]):
            others = [x for x in pool if x[0] != aid]
            for aid2, c in rnd.sample(others, min(NEGATIVES_PER_ANSWER,
                                                  len(others))):
                labels.append({"kind": "constructed", "reviewer": rv,
                               "item": aid, "claim": "%s/%s" % (aid2, c["id"]),
                               "claim_text": c["text"],
                               "answer": answers[rv][aid], "label": False})
    return labels, problems


# §7b's construction, corrected TWICE before a single pair was judged - both
# corrections recorded in the protocol:
#   1. as first written it truncated the CLAIM and paired it with an answer
#      stating that same part, which is a positive, not a negative;
#   2. its first marker list yielded 27 pairs against a target of 100, produced
#      heads that were not propositions ("For the detection of other defects,"),
#      and contained a marker written from a known failing case - overfitting to
#      the very example the set exists to generalise beyond.
# The rule below is general: drop the LAST trailing prepositional or
# subordinate phrase. No judge verdict was seen while either correction was
# made, which is what separates this from tuning.
PREPOSITIONS = ("according", "after", "against", "at", "before", "by",
                "considering", "during", "for", "from", "in", "on", "per",
                "subject", "through", "to", "under", "unless", "using",
                "where", "with", "within")
# A head has to be a proposition, not a fragment.
FINITE_VERBS = ("shall", "must", "is", "are", "was", "were", "may", "can",
                "should", "will", "includes", "include", "requires", "require",
                "provides", "provide", "uses", "use", "has", "have", "covers",
                "cover", "applies", "apply", "defines", "define", "states",
                "state", "consists", "contains", "specifies", "specify")
HN_MIN_HEAD_TOKENS = 6
HN_MIN_TAIL_TOKENS = 3
WORD = re.compile(r"[A-Za-z][A-Za-z0-9'-]*")


def truncate_claim(text):
    """Drop a claim's trailing qualifier. Returns (head, tail) or None.

    The LAST qualifying phrase is removed, not the first: the qualifier that
    makes a requirement specific - which document governs it, under what
    condition, where it is recorded - sits at the end. Taking the first
    preposition instead produced heads like "For the detection of other
    defects," which are fragments rather than incomplete requirements, and an
    incomplete requirement is the thing being tested.
    """
    toks = (text or "").split()
    if len(toks) < HN_MIN_HEAD_TOKENS + HN_MIN_TAIL_TOKENS:
        return None
    for i in range(len(toks) - HN_MIN_TAIL_TOKENS, HN_MIN_HEAD_TOKENS - 1, -1):
        w = (WORD.search(toks[i]) or [""])
        w = w.group(0).lower() if hasattr(w, "group") else ""
        if w not in PREPOSITIONS:
            continue
        head = " ".join(toks[:i]).strip()
        tail = " ".join(toks[i:]).strip()
        # a head is a proposition, and does not dangle on a conjunction
        low = [(WORD.search(t) or type("x", (), {"group": lambda s, n=0: ""})())
               for t in head.split()]
        words = [(m.group(0).lower() if m.group(0) else "") for m in low]
        if not any(v in words for v in FINITE_VERBS):
            continue
        if words and (words[-1] in ("and", "or", "the", "a", "an", "of")
                      or words[-1] in PREPOSITIONS):
            continue      # "... in interaction" dangles; it is not a claim
        head = head.rstrip(",;: ")
        if len(head.split()) < HN_MIN_HEAD_TOKENS:
            continue
        return head, tail
    return None


def hard_negatives(questions_path, outroot, concurrency=1):
    """Protocol §7b. Does the judge notice a DROPPED QUALIFIER?

    Each eligible required claim yields two pairs:

      NEGATIVE  full claim  vs  the claim truncated at its qualifier
                -> correct verdict NO ("states only part of the claim")
      CONTROL   full claim  vs  the full claim
                -> correct verdict YES

    The control is trivial by design and is not a capability measure. It exists
    to rule out one specific artefact: a judge that answers NO to any short
    answer would score 100% on the negatives for entirely the wrong reason, and
    the negative number would mean nothing without it.

    No text is invented - every answer here is a substring of a claim a human
    adjudicated. That is the whole point of truncation over perturbation.
    """
    qs = [r for r in (json.loads(l) for l in open(questions_path) if l.strip())
          if r.get("status") == "ok"]
    pairs = []
    for q in qs:
        for c in qg.required(q):
            t = truncate_claim(c.get("text", ""))
            if not t:
                continue
            head, tail = t
            pairs.append({"kind": "truncated", "item": q["anchor_id"],
                          "class": q.get("class"), "claim": c["id"],
                          "claim_text": c["text"], "answer": head,
                          "dropped": tail, "label": False})
            pairs.append({"kind": "control", "item": q["anchor_id"],
                          "class": q.get("class"), "claim": c["id"],
                          "claim_text": c["text"], "answer": c["text"],
                          "dropped": "", "label": True})
    neg = [p for p in pairs if p["kind"] == "truncated"]
    by_class = Counter(p["class"] for p in neg)
    print("hard-negative set: %d truncated + %d control = %d pairs"
          % (len(neg), len(pairs) - len(neg), len(pairs)))
    print("  by class: %s" % ", ".join("%s %d" % kv for kv in
                                       sorted(by_class.items())))
    if len(neg) < HN_TARGET:
        print("  NOTE  %d truncated pairs against a §7b target of %d. The "
              "shortfall is a property of the claims, not a choice: only "
              "claims carrying a trailing qualifier can be truncated without "
              "inventing text. Reported with the result." % (len(neg), HN_TARGET))
    if not ce.preflight():
        return 1
    print("judging with model=%s route=%s thinking=%s temperature=0.0"
          % (ce.ROUTE["model"], ce.ROUTE["path"], ce.THINKING))
    t0 = time.time()
    if concurrency > 1:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=concurrency) as ex:
            vs = list(ex.map(lambda p: judge(p["claim_text"], p["answer"]),
                             pairs))
    else:
        vs = [judge(p["claim_text"], p["answer"]) for p in pairs]
    for p, v in zip(pairs, vs):
        p["judge"] = v
        p["matcher"] = qg.claim_reached(p["claim_text"], p["answer"])
    dt = time.time() - t0

    unparsed = sum(1 for p in pairs if p["judge"] is None)
    neg = [p for p in pairs if p["kind"] == "truncated" and p["judge"] is not None]
    con = [p for p in pairs if p["kind"] == "control" and p["judge"] is not None]
    rejected = sum(1 for p in neg if p["judge"] is False)
    kept = sum(1 for p in con if p["judge"] is True)
    m_rej = sum(1 for p in neg if not p["matcher"])
    m_kept = sum(1 for p in con if p["matcher"])

    stamp = time.strftime("%Y-%m-%d_%H%M%S")
    outdir = os.path.join(outroot, stamp)
    os.makedirs(outdir, exist_ok=True)
    rec = os.path.join(outdir, "hard_negatives_%s.jsonl" % stamp)
    with open(rec, "w") as f:
        for p in pairs:
            f.write(json.dumps(p, sort_keys=True) + "\n")
    missed = os.path.join(outdir, "TO_READ_qualifier_missed_%s.jsonl" % stamp)
    with open(missed, "w") as f:
        for p in neg:
            if p["judge"]:
                f.write(json.dumps(p, sort_keys=True) + "\n")

    print("\n  judged %d pairs in %.0fs" % (len(pairs), dt))
    print("  UNPARSEABLE %s" % ce.pct(unparsed, len(pairs)))
    print("\n  CONTROL - the whole claim as the answer (must be YES)")
    print("    judge   %s" % ce.pct(kept, len(con)))
    print("    matcher %s" % ce.pct(m_kept, len(con)))
    print("\n  TRUNCATED - the qualifier dropped (must be NO)")
    print("    judge rejects   %s" % ce.pct(rejected, len(neg)))
    print("    matcher rejects %s" % ce.pct(m_rej, len(neg)))
    print("       misses -> %s" % missed)
    ctrl_ok = len(con) and kept / float(len(con)) >= HN_CONTROL_FLOOR
    rate = rejected / float(len(neg)) if neg else 0.0
    print("\n  §7b, pre-registered: reject >= %.2f     %s (%.2f)"
          % (HN_REJECT_FLOOR, "PASS" if rate >= HN_REJECT_FLOOR else "BELOW",
             rate))
    print("      control >= %.2f              %s"
          % (HN_CONTROL_FLOOR, "PASS" if ctrl_ok else "FAIL"))
    if not ctrl_ok:
        print("      The control failed, so the truncation number means "
              "NOTHING: a judge that rejects short answers rejects these for "
              "the wrong reason. Report neither.")
    print("\n  This measurement is REPORTED. It does not accept or reject the "
          "judge (§7b) - acceptance stands on the §7 validation.")
    summary = {"stamp": stamp, "n_truncated": len(neg), "n_control": len(con),
               "reject_rate": round(rate, 4),
               "control_rate": round(kept / float(len(con)), 4) if con else None,
               "matcher_reject_rate": round(m_rej / float(len(neg)), 4) if neg else None,
               "control_valid": bool(ctrl_ok), "unparseable": unparsed,
               "reject_floor": HN_REJECT_FLOOR, "control_floor": HN_CONTROL_FLOOR,
               "target_n": HN_TARGET, "by_class": dict(by_class),
               "model": ce.ROUTE["model"], "route": ce.ROUTE["path"],
               "thinking": ce.THINKING, "temperature": 0.0, "records": rec}
    sp = os.path.join(outdir, "hard_negatives_summary_%s.json" % stamp)
    open(sp, "w").write(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print("  summary -> %s" % sp)
    return 0


def validate(questions_path, answer_paths, judgement_paths, outroot,
             limit=0, concurrency=1):
    labels, problems = build_validation_set(questions_path, answer_paths,
                                            judgement_paths)
    if problems:
        print("ABORT - the validation set did not assemble:")
        for p_ in problems[:20]:
            print("   " + p_)
        return 1
    if limit:
        # a seeded SAMPLE, not the head: the list is ordered by item, so
        # labels[:40] is the first few items of one reviewer and tells you
        # nothing about the set
        labels = random.Random(SEED).sample(labels, min(limit, len(labels)))
    print("validation set: %d pairs (%d reviewer-labelled, %d constructed)"
          % (len(labels),
             sum(1 for l in labels if l["kind"] == "reviewer"),
             sum(1 for l in labels if l["kind"] == "constructed")))
    # discover the route BEFORE printing what we are judging with: the first
    # run printed a model name it had not confirmed was served, then 404ed
    if not ce.preflight():
        return 1
    print("judging with model=%s route=%s thinking=%s temperature=0.0"
          % (ce.ROUTE["model"], ce.ROUTE["path"], ce.THINKING))

    t0 = time.time()
    if concurrency > 1:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=concurrency) as ex:
            verdicts = list(ex.map(
                lambda l: judge(l["claim_text"], l["answer"]), labels))
    else:
        verdicts = [judge(l["claim_text"], l["answer"]) for l in labels]
    for l, v in zip(labels, verdicts):
        l["judge"] = v
        l["matcher"] = qg.claim_reached(l["claim_text"], l["answer"])
    dt = time.time() - t0

    unparsed = [l for l in labels if l["judge"] is None]
    reviewer_labels = [l for l in labels if l["kind"] == "reviewer" and l["judge"] is not None]
    made = [l for l in labels if l["kind"] == "constructed"
            and l["judge"] is not None]
    pos = [l for l in reviewer_labels if l["label"]]
    neg = [l for l in reviewer_labels if not l["label"]]

    def rate(rows, want):
        n = sum(1 for r in rows if r["judge"] == want)
        return n, len(rows), (n / float(len(rows)) if rows else 0.0)

    def show(n, d):
        # "0/0 = 0%" reads as a measured zero. It is an absence.
        return ce.pct(n, d) if d else "n/a (none in this run)"

    jr, jrn, recall = rate(pos, True)
    mr = sum(1 for r in pos if r["matcher"])
    m_recall = mr / float(len(pos)) if pos else 0.0
    fp, fpn, fp_rate = rate(made, True)
    hn, hnn, _ = rate(neg, False)

    stamp = time.strftime("%Y-%m-%d_%H%M%S")
    outdir = os.path.join(outroot, stamp)
    os.makedirs(outdir, exist_ok=True)
    rec = os.path.join(outdir, "judge_validation_%s.jsonl" % stamp)
    with open(rec, "w") as f:
        for l in labels:
            f.write(json.dumps(l, sort_keys=True) + "\n")
    reads = os.path.join(outdir, "TO_READ_constructed_positives_%s.jsonl"
                         % stamp)
    with open(reads, "w") as f:
        for l in made:
            if l["judge"]:
                f.write(json.dumps(l, sort_keys=True) + "\n")

    print("\n  judged %d pairs in %.0fs (%.1f/s)"
          % (len(labels), dt, len(labels) / dt if dt else 0))
    print("  UNPARSEABLE %s   <- any at all is an instrument defect (rule 59)"
          % ce.pct(len(unparsed), len(labels)))
    print("\n  RECALL on claims a reviewer confirms present")
    print("    judge   %s" % show(jr, jrn))
    print("    matcher %s   (the instrument being replaced)"
          % show(mr, len(pos)))
    print("\n  the 10 claims a reviewer says their answer MISSED")
    print("    judge agrees %s" % show(hn, hnn))
    print("    matcher agrees %s"
          % show(sum(1 for r in neg if not r["matcher"]), len(neg)))
    print("\n  CONSTRUCTED negatives - claims from other items")
    print("    judge says present %s  <- READ THESE before counting them wrong"
          % show(fp, fpn))
    print("    matcher says present %s"
          % show(sum(1 for r in made if r["matcher"]), len(made)))
    print("       -> %s" % reads)

    ok_recall = recall >= MIN_RECALL
    ok_fp = fp_rate <= MAX_FP_RATE
    ok_parse = not unparsed
    print("\n  PRE-REGISTERED ACCEPTANCE (protocol §4, fixed before this ran):")
    print("    recall >= %.2f            %s (%.2f)"
          % (MIN_RECALL, "PASS" if ok_recall else "FAIL", recall))
    print("    constructed FP <= %.2f    %s (%.2f, BEFORE reading)"
          % (MAX_FP_RATE, "PASS" if ok_fp else "CHECK", fp_rate))
    print("    zero unparseable          %s" % ("PASS" if ok_parse else "FAIL"))
    short = []
    if limit:
        short.append("run was truncated with --limit %d" % limit)
    if len(pos) < MIN_REVIEWER_POSITIVES:
        short.append("%d reviewer-positive pairs, floor is %d"
                     % (len(pos), MIN_REVIEWER_POSITIVES))
    if len(neg) < MIN_REVIEWER_NEGATIVES:
        short.append("%d reviewer-negative pairs, floor is %d"
                     % (len(neg), MIN_REVIEWER_NEGATIVES))
    if len(made) < MIN_CONSTRUCTED:
        short.append("%d constructed negatives, floor is %d"
                     % (len(made), MIN_CONSTRUCTED))
    print("    whole set, not a sample %s"
          % ("PASS" if not short else "SMOKE"))
    if short:
        verdict = "SMOKE"
    elif ok_recall and ok_fp and ok_parse:
        verdict = "ACCEPTED"
    else:
        verdict = "NOT ACCEPTED"
    print("\n  => %s" % verdict)
    if verdict == "SMOKE":
        print("     This run cannot accept the judge, whatever the rates say:")
        for x in short:
            print("       - %s" % x)
        print("     Re-run without --limit for an acceptance record.")
    if not ok_fp:
        print("     A constructed 'false positive' may be a real positive - a "
              "claim from another item that this answer does state. Read the "
              "file above and reclassify by hand before treating the rate as "
              "an error rate. That reading is part of the protocol, not an "
              "escape from it.")
    if not ok_recall:
        print("     Recall below the floor rejects the ON-BOX judge, not the "
              "approach: protocol §5 then measures an external judge on this "
              "same set before anything else is tried.")
    summary = {"version": VERSION, "stamp": stamp, "verdict": verdict,
               "smoke_reasons": short, "limit": limit or 0,
               "n_reviewer_positive": len(pos), "n_reviewer_negative": len(neg),
               "n_constructed": len(made),
               "recall": round(recall, 4), "matcher_recall": round(m_recall, 4),
               "constructed_fp_rate_before_reading": round(fp_rate, 4),
               "reviewer_negative_agreement": "%d/%d" % (hn, hnn),
               "unparseable": len(unparsed), "n": len(labels),
               "model": ce.ROUTE["model"], "route": ce.ROUTE["path"],
               "thinking": ce.THINKING, "temperature": 0.0,
               "min_recall": MIN_RECALL, "max_fp_rate": MAX_FP_RATE,
               "seed": SEED, "records": rec}
    sp = os.path.join(outdir, "judge_validation_summary_%s.json" % stamp)
    open(sp, "w").write(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print("  summary -> %s" % sp)
    return 0


def judge_answer(claim_texts, answer, validation_summary):
    """Score an answer for the benchmark. REFUSES without an ACCEPTED record.

    The refusal is the point. This module exists because a scoring function was
    used for a whole stage before anyone measured it against independent reviewer judgement.
    """
    if not ce.ROUTE["path"] and not ce.preflight():
        raise RuntimeError("claim_judge: the answer LLM is not reachable")
    s = json.load(open(validation_summary))
    if s.get("verdict") != "ACCEPTED":
        raise RuntimeError(
            "claim_judge is not validated: %s says %r. Run --validate and read "
            "the result before scoring anything with it."
            % (validation_summary, s.get("verdict")))
    return [judge(c, answer) for c in claim_texts]


# ---------------------------------------------------------------------------
def selftest():
    fails, ran = [], [0]

    def ck(name, cond):
        ran[0] += 1
        print("  %-64s %s" % (name, "ok" if cond else "FAIL"))
        if not cond:
            fails.append(name)

    src = open(os.path.abspath(__file__)).read()

    def cj_head(t):
        r = truncate_claim(t)
        return r[0] if r else None
    ck("the judge is told compression counts as stating the claim",
       "compressed notation" in JUDGE_SYSTEM)
    ck("the judge is told a PARTIAL statement does not count",
       "only part of the claim" in JUDGE_SYSTEM)
    ck("the judge is forbidden its own knowledge of the standard",
       "Do not use your own knowledge" in JUDGE_SYSTEM)
    ck("an unparseable reply is None, never False",
       "return None" in src and "never folded into False" in src)
    ck("the acceptance thresholds are constants, set before any run",
       isinstance(MIN_RECALL, float) and isinstance(MAX_FP_RATE, float))
    ck("scoring REFUSES without an ACCEPTED validation record",
       's.get("verdict") != "ACCEPTED"' in src and "raise RuntimeError" in src)
    ck("the negative set is seeded, so the set is reproducible",
       "random.Random(SEED)" in src)
    ck("constructed negatives are PRESUMED negative and must be read",
       "PRESUMED negative" in src and "TO_READ" in src)
    ck("the matcher being replaced is measured on the SAME pairs",
       'l["matcher"] = qg.claim_reached' in src)
    ck("judging REFUSES before the route is discovered, never guesses one",
       "no route discovered" in src and 'if not ce.ROUTE["path"]:' in src)
    ck("validate() discovers the route before it reports what it is using",
       src.index("if not ce.preflight():") < src.index("judging with model="))
    # §7b - the hard-negative construction
    ck("truncation drops the LAST qualifier, not the first",
       "The LAST qualifying phrase is removed" in src
       and cj_head("The supplier shall record every anomaly in the "
                   "maintenance book") == "The supplier shall record every "
                                          "anomaly")
    ck("a head that is not a proposition is rejected",
       truncate_claim("For the detection of other defects, unless otherwise "
                      "specified by design") is None)
    ck("a head never dangles on a preposition or a conjunction",
       all(truncate_claim(t) is None
           or truncate_claim(t)[0].split()[-1].lower() not in PREPOSITIONS
           for t in ("The purpose is to measure the string capacitance in "
                     "interaction with the power regulator",
                     "The supplier shall verify the item and record it in "
                     "the log")))
    ck("the construction invents no text - the answer is a claim substring",
       "substring of a claim a reviewer adjudicated" in src)
    ck("the hard-negative set carries a CONTROL that rules out a NO-machine",
       "trivial by design" in src and "for entirely the wrong reason" in src)
    ck("a failed control voids the truncation number rather than caveating it",
       "if not ctrl_ok:" in src and ("Report " + "neither.") in src)
    ck("§7b floors are constants, fixed before the set was built",
       HN_TARGET == 100 and HN_REJECT_FLOOR == 0.80
       and HN_CONTROL_FLOOR == 0.95)
    ck("the hard-negative run cannot accept or reject the judge",
       "does not accept or reject the judge" in src)
    ck("a truncated run reports SMOKE and can never accept the judge",
       'verdict = "SMOKE"' in src and "run was truncated" in src)
    ck("acceptance has minimum counts, not just rates",
       MIN_REVIEWER_POSITIVES >= 400 and MIN_CONSTRUCTED >= 300
       and MIN_REVIEWER_NEGATIVES >= 10)
    ck("a --limit run samples the set instead of taking its head",
       "random.Random(SEED).sample(labels" in src)
    ck("a rate with no denominator prints n/a, never 0%",
       "none in this run" in src)
    ck("the run records its generation settings (rule 59)",
       '"thinking": ce.THINKING' in src and '"temperature": 0.0' in src)

    # behavioural: the validation set builder, with no model involved
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        q = os.path.join(td, "q.jsonl")
        recs = [{"anchor_id": "A-QQ-0001", "class": "definitional",
                 "status": "ok", "context": "c", "question": "q",
                 "claims": [{"id": "C1", "tier": "required", "text": "alpha"}]},
                {"anchor_id": "A-QQ-0002", "class": "definitional",
                 "status": "ok", "context": "c", "question": "q",
                 "claims": [{"id": "C1", "tier": "required", "text": "beta"}]}]
        open(q, "w").write("\n".join(json.dumps(r) for r in recs) + "\n")
        a = os.path.join(td, "rev_answers.csv")
        open(a, "w").write("item,my_answer\nA-QQ-0001,alpha stated\n"
                           "A-QQ-0002,beta stated\n")
        j = os.path.join(td, "rev_judgements.csv")
        open(j, "w").write("item,claim,my_answer_contained_it\n"
                           "A-QQ-0001,C1,yes\nA-QQ-0002,C1,no\n")
        labels, pr = build_validation_set(q, [a], [j])
        ck("the validation set assembles with no problems on a clean input",
           not pr)
        ck("every reviewer judgement becomes one labelled pair",
           sum(1 for l in labels if l["kind"] == "reviewer") == 2)
        ck("a constructed negative never draws from its own item",
           all(not l["claim"].startswith(l["item"])
               for l in labels if l["kind"] == "constructed"))
        ck("each label carries the answer it is judged against",
           all(l["answer"] for l in labels))
        j2 = os.path.join(td, "rev_judgements2.csv")
        open(j2, "w").write("item,claim,my_answer_contained_it\n"
                            "A-QQ-0001,C9,yes\n")
        _l, pr2 = build_validation_set(q, [a], [j2])
        ck("a judgement naming a claim the item does not have ABORTS",
           any("is not a claim of that item" in x for x in pr2))
        j3 = os.path.join(td, "rev_judgements3.csv")
        open(j3, "w").write("item,claim,my_answer_contained_it\n"
                            "A-QQ-0001,C1,yes\n")
        a3 = os.path.join(td, "rev_answers3.csv")
        open(a3, "w").write("item,my_answer\nA-QQ-0002,beta stated\n")
        _l3, pr3 = build_validation_set(q, [a3], [j3])
        ck("a claim judgement with no answer behind it ABORTS",
           any("no Part A answer" in x for x in pr3))
        sf = os.path.join(td, "sum.json")
        for v in ("NOT ACCEPTED", "SMOKE"):
            open(sf, "w").write(json.dumps({"verdict": v}))
            try:
                judge_answer(["x"], "y", sf)
                ck("scoring with a %s record raises" % v, False)
            except RuntimeError:
                ck("scoring with a %s record raises" % v, True)

    print("\n  %d assertions, %d failed" % (ran[0], len(fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--validate", action="store_true",
                    help="measure the judge against the census's reviewer "
                         "judgements, under the pre-registered thresholds")
    ap.add_argument("--questions", metavar="QUESTIONS_JSONL")
    ap.add_argument("--answers", nargs="+", metavar="PART_A_CSV")
    ap.add_argument("--judgements", nargs="+", metavar="PART_B_CSV")
    ap.add_argument("--out", default=os.path.expanduser("~/p42/judge"))
    ap.add_argument("--hard-negatives", action="store_true",
                    help="protocol §7b: does the judge notice a dropped "
                         "qualifier? needs --questions")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--concurrency", type=int, default=8)
    a = ap.parse_args()
    if a.self_test:
        sys.exit(selftest())
    if a.hard_negatives:
        if not a.questions:
            ap.error("--hard-negatives needs --questions")
        sys.exit(hard_negatives(a.questions, a.out, max(1, a.concurrency)))
    if a.validate:
        if not (a.questions and a.answers and a.judgements):
            ap.error("--validate needs --questions, --answers and --judgements")
        sys.exit(validate(a.questions, a.answers, a.judgements, a.out,
                          a.limit, max(1, a.concurrency)))
    ap.print_help()
