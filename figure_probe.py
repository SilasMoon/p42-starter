#!/usr/bin/env python3
"""P42 - R71: do questions whose answer lives in a DIAGRAM fail?

`P42_Register.md` R71, and R89's prediction 3.

WHY THIS RUNS BEFORE THE REBUILD. The live index was built with
`captions: False`. Element types across 35 166 passages are `text`, `table`,
`abbreviation`, `definition` - **there is no figure element**, so an answer
that lives in a diagram is unreachable by any route. That is an argument from
the build configuration. This turns it into a measurement, and it costs one
re-ingest less than turning captioning on and hoping.

THE CONTROL IS THE WHOLE DESIGN. Six questions whose answer is only in a
figure prove nothing on their own - a pipeline that fails them might be
failing the DOCUMENT, the vocabulary or the phrasing. So three control
questions are drawn from the SAME documents and the SAME pages, answerable
from the normative text beside the figure. The prediction is registered
before the run:

    figure_only    scores at or near zero
    text_control   scores high

**If the controls also fail, this run says nothing about figures** and is
reported as inconclusive rather than as evidence for R70.

EVERY FIGURE WAS READ BEFORE ITS QUESTION WAS WRITTEN. The page was rendered
and inspected; the claims are transcribed from the diagram, not inferred from
the surrounding prose. Two candidates were REJECTED during authoring because
their content turned out to be fully restated in the text (SpaceWire packet
format, Figure 5-21; bit numbering convention, Figure 3-1).

THAT WAS NOT ENOUGH, AND v1 GOT IT WRONG. Reading the figure tells you what
the figure SHOWS; it does not tell you whether the same content also sits in
the clause text. Five of v1's six "figure_only" items were misclassified -
ECSS-E-ST-50-11 specifies its lane state machine in normative prose ("When in
the LossOfSignal state ... Send 32 LOST_SIGNAL control words") and merely
ILLUSTRATES it in Figure 5-29. The pipeline answered them and cited the
clause. They are reclassified as controls, each carrying the reason, and the
superseded frame is retained.

THE AUTHORING RULE, learned from that failure: an item is figure-only when
the text **DELEGATES** to the figure - "shall be mapped ... according to
Figure 7-2", "in accordance with Figure 9-9" - not when it merely mentions
one. Across the corpus: **2 431 figure mentions, 313 explicitly illustrative,
and 48 DELEGATING references in 16 documents.** Those 48 are the population
this probe should be drawn from, and they bound what captioning can buy.

    python3 figure_probe.py --self-test
    python3 figure_probe.py --run
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

VERSION = "1.0"
PREREG = "P42_Register.md R71 / R89 prediction 3"
FRAME = "questions/figure_probe_v1.jsonl"
ARMS = ("figure_only", "text_control")

# Fixed here, before the run (rule 84 - register the direction).
PREDICTION = {"figure_only": "at or near 0.00",
              "text_control": "high; if it is not, the run is INCONCLUSIVE"}
CONTROL_FLOOR = 0.60      # below this the controls have not established a baseline


def load(path=FRAME):
    rows = [json.loads(l) for l in open(path) if l.strip()]
    bad = [r.get("id") for r in rows
           if not r.get("claims") or not r.get("question") or
           r.get("arm") not in ARMS]
    if bad:
        raise SystemExit("ABORT - malformed items, named: %s" % bad)
    return rows


def coverage(verdicts):
    """Fraction of claims judged present. None (unparseable) is NOT False."""
    ok = [v for v in verdicts if v is not None]
    return (sum(1 for v in ok if v) / len(ok)) if ok else None


def summarise(results):
    """Per-arm mean coverage, and the verdict on whether the run is readable."""
    out = {}
    for arm in ARMS:
        vals = [r["coverage"] for r in results
                if r["arm"] == arm and r["coverage"] is not None]
        out[arm] = {"n": len(vals),
                    "coverage": round(sum(vals) / len(vals), 4) if vals else None}
    ctl = out["text_control"]["coverage"]
    if ctl is None or ctl < CONTROL_FLOOR:
        verdict = ("INCONCLUSIVE - the controls did not establish that this "
                   "pipeline can answer from these documents at all")
    elif out["figure_only"]["coverage"] is None:
        verdict = "INCONCLUSIVE - no figure item produced a judgement"
    elif out["figure_only"]["coverage"] < ctl:
        verdict = ("FIGURE GAP CONFIRMED - controls answer, figure questions "
                   "do not")
    else:
        verdict = ("PREDICTION DID NOT HOLD - figure questions scored at or "
                   "above the controls; R70 loses its justification")
    out["verdict"] = verdict
    out["unparseable"] = sum(1 for r in results for v in r["verdicts"]
                             if v is None)
    return out


def run(outroot="figure_probe"):
    import claim_extract as ce
    import claim_judge as cj
    import pipelines
    import retrieve as retrieve_mod
    if not ce.preflight():
        raise SystemExit("ABORT - the answer LLM is not reachable")

    rows = load()
    print("\n  R71 FIGURE PROBE - %d items (%d figure_only, %d control)"
          % (len(rows), sum(1 for r in rows if r["arm"] == "figure_only"),
             sum(1 for r in rows if r["arm"] == "text_control")))
    print("  collection: %s" % retrieve_mod.COLL)
    print("  PREDICTION, fixed before the run: figure_only %s | text_control %s"
          % (PREDICTION["figure_only"], PREDICTION["text_control"]))

    results, t0 = [], time.time()
    for i, r in enumerate(rows, 1):
        a = pipelines.ask("pipeline_ask_v2", r["question"])
        ans = a.get("answer") or ""
        verdicts = [cj.judge(c, ans) for c in r["claims"]]
        cov = coverage(verdicts)
        results.append({"id": r["id"], "arm": r["arm"], "doc": r["doc"],
                        "figure": r.get("figure"), "question": r["question"],
                        "claims": r["claims"], "verdicts": verdicts,
                        "coverage": cov, "answer": ans,
                        "status": a.get("status"),
                        "sources": a.get("sources"),
                        "n_context": a.get("n_context")})
        print("  %2d/%d  %-11s %-13s coverage %s"
              % (i, len(rows), r["id"], r["arm"],
                 "n/a" if cov is None else "%.2f" % cov))

    s = summarise(results)
    print("\n  %-14s %3s  %s" % ("arm", "n", "claim coverage"))
    for arm in ARMS:
        b = s[arm]
        print("  %-14s %3d  %s" % (arm, b["n"],
                                   "n/a" if b["coverage"] is None
                                   else "%.3f" % b["coverage"]))
    print("\n  unparseable judgements: %d" % s["unparseable"])
    print("  VERDICT: %s" % s["verdict"])
    print("\n  Every item is READ before this is quoted - at n=9 reading beats "
          "judging,\n  and the judge is validated on answer-contains-claim "
          "only (rule 87).")

    stamp = time.strftime("%Y-%m-%d_%H%M%S")
    outdir = os.path.join(outroot, stamp)
    os.makedirs(outdir, exist_ok=True)
    rec = {"version": VERSION, "prereg": PREREG, "stamp": stamp,
           "collection": retrieve_mod.COLL, "frame": FRAME,
           "prediction": PREDICTION, "control_floor": CONTROL_FLOOR,
           "elapsed_s": round(time.time() - t0, 1),
           "summary": s, "items": results}
    p = os.path.join(outdir, "figure_probe_%s.json" % stamp)
    open(p, "w").write(json.dumps(rec, indent=2, sort_keys=True) + "\n")
    print("\n  record -> %s" % p)
    return 0


# ---------------------------------------------------------------------------
def selftest():
    fails, ran = [], [0]

    def ck(name, cond):
        ran[0] += 1
        print("  %-72s %s" % (name, "ok" if cond else "FAIL"))
        if not cond:
            fails.append(name)

    src = open(os.path.abspath(__file__)).read()

    rows = load()
    ck("the frame loads and every item names an arm",
       len(rows) == 10 and all(r["arm"] in ARMS for r in rows))
    ck("the frame carries BOTH arms - a probe with no control is refused by "
       "design",
       {r["arm"] for r in rows} == set(ARMS))
    ck("there are at least 3 controls, drawn from the same documents",
       sum(1 for r in rows if r["arm"] == "text_control") >= 3
       and {r["doc"] for r in rows if r["arm"] == "text_control"}
       <= {r["doc"] for r in rows})
    ck("every figure_only item names the figure it came from",
       all(r.get("figure") for r in rows if r["arm"] == "figure_only"))
    ck("every item records WHY it is figure-only or control",
       all(r.get("why_figure_only") for r in rows))

    ck("coverage counts present claims over PARSEABLE ones",
       coverage([True, False]) == 0.5 and coverage([True, None]) == 1.0)
    ck("an unparseable judgement is NOT folded into absent",
       coverage([None, None]) is None and coverage([False, None]) == 0.0)

    def mk(arm, cov, n=1):
        return [{"arm": arm, "coverage": cov, "verdicts": [cov == 1.0]}
                for _ in range(n)]

    good = summarise(mk("figure_only", 0.0, 6) + mk("text_control", 1.0, 3))
    ck("figure items at 0 and controls at 1 CONFIRMS the gap",
       "FIGURE GAP CONFIRMED" in good["verdict"])
    weak = summarise(mk("figure_only", 0.0, 6) + mk("text_control", 0.2, 3))
    ck("controls that FAIL make the run inconclusive, not evidence for R70",
       "INCONCLUSIVE" in weak["verdict"]
       and "did not establish" in weak["verdict"])
    flip = summarise(mk("figure_only", 1.0, 6) + mk("text_control", 0.9, 3))
    ck("figure items scoring AT OR ABOVE the controls is reported as the "
       "prediction failing, not quietly",
       "DID NOT HOLD" in flip["verdict"]
       and "loses its justification" in flip["verdict"])
    ck("the control floor is a fixed number, not chosen after the run",
       isinstance(CONTROL_FLOOR, float) and "CONTROL_FLOOR = 0.60" in src)
    ck("the prediction is recorded in the module and in the record",
       "PREDICTION" in src and '"prediction": PREDICTION' in src)

    ck("the record NAMES the collection that answered",
       ('"collection"' + ": retrieve_mod.COLL") in src)
    ck("a malformed frame ABORTS and names the items",
       "ABORT - malformed items, named" in src)
    ck("the two rejected candidates are recorded, not silently dropped",
       "Figure 5-21" in src and "Figure 3-1" in src
       and "fully restated in the text" in src)
    ck("v1's misclassification is recorded in the module, not quietly fixed",
       "v1 GOT IT WRONG" in src and "reclassified as controls" in src)
    ck("every reclassified item carries its reason in the frame",
       all(r.get("reclassified_2026-08-18")
           for r in load() if "RECLASSIFIED" in (r.get("why_figure_only") or "")))
    ck("the authoring rule is DELEGATION, and the population is sized",
       "DELEGATES" in src and "48 DELEGATING references" in src)
    ck("the judge is used only on the relation it is validated for, and says so",
       "answer-contains-claim" in src and "rule 87" in src)
    ck("preflight is called before any generation (rule 70)",
       "ce.preflight()" in src and src.index("ce.preflight()")
       < src.index("pipelines.ask"))

    print("\n  %d assertions, %d failed" % (ran[0], len(fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.
                                 RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        sys.exit(selftest())
    if a.run:
        sys.exit(run())
    ap.print_help()
