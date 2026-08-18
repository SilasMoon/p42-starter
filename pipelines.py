#!/usr/bin/env python3
"""P42 — the pipeline contract. What the benchmark needs a system to return.

`P42_Register.md` R40.

WHY. The benchmark called `ask_v2` directly, so it could measure exactly one
system - which makes it a report on that system rather than a benchmark. This
is the seam: any system that returns the shape below can be measured by the
same frame, the same judge and the same rules.

THE SHAPE IS NOT INVENTED HERE. It is the external specification's
`pipeline-response.schema.json` minus the access-governance fields P42
deliberately does not import (`policy_decision`, `access_decision_id`,
`audit_record_id`) - those belong to an access-controlled enterprise product,
and P42 measures retrieval over public standards.

    REQUIRED
      answer      the prose answer, as shown to a user
      sources     the passages put in front of the model, in order
      ranked      the FULL ranked list the context was cut from - without it
                  no rank statistic (Recall@k, MRR, nDCG) is computable, and
                  the benchmark dropped this field for two whole runs
      status      one of STATUS, the external spec's 8-value enum

    OPTIONAL
      confidence  0..1 if the system emits one; None unlocks nothing but is
                  honest. Absent everywhere in P42 today (R41)
      model, route, rerank, n_context, n_retrieved, error

A CONTRACT THAT ONLY DESCRIBES IS NOT A CONTRACT. `validate()` refuses a
response that is missing a required field, carries a status outside the enum,
or returns a `ranked` list shorter than its own `sources` - the last being
exactly the shape a system would produce if it reported the cut instead of the
ranking.

    python3 pipelines.py --self-test
    python3 pipelines.py --list
"""
import argparse
import importlib
import os
import sys

VERSION = "1.0"
PREREG = "P42_Register.md R40"

# The external specification's terminal states, adopted verbatim (EXT-2).
STATUS = ("supported_answer", "partial_answer", "needs_clarification",
          "insufficient_evidence", "missing_required_source",
          "conflicting_evidence", "access_restricted", "out_of_scope")

REQUIRED = ("answer", "sources", "ranked", "status")
OPTIONAL = ("confidence", "model", "route", "rerank", "n_context",
            "n_retrieved", "error")

# A source is a passage the system put in front of the model.
SOURCE_FIELDS = ("doc", "clause")          # the minimum a citation can resolve
RANKED_FIELDS = ("point_id",)              # the minimum a qrel can join on


def validate(resp, strict=True):
    """[] when the response satisfies the contract, else named problems.

    Named, not counted: a caller that cannot say WHICH field is wrong will
    report a pipeline as broken without saying how.
    """
    p = []
    if not isinstance(resp, dict):
        return ["response is %s, not a dict" % type(resp).__name__]
    if resp.get("error"):
        return []                    # an errored item is dropped, not scored
    for f in REQUIRED:
        if f not in resp:
            p.append("missing required field: %s" % f)
    if resp.get("status") is not None and resp["status"] not in STATUS:
        p.append("status %r is not one of the 8 permitted states"
                 % resp["status"])
    src = resp.get("sources")
    if src is not None and not isinstance(src, list):
        p.append("sources must be a list")
    elif src:
        for f in SOURCE_FIELDS:
            if any(f not in s for s in src):
                p.append("every source needs %r" % f)
    rk = resp.get("ranked")
    if rk is not None and not isinstance(rk, list):
        p.append("ranked must be a list")
    elif rk:
        for f in RANKED_FIELDS:
            if any(f not in r for r in rk):
                p.append("every ranked entry needs %r" % f)
    if strict and isinstance(rk, list) and isinstance(src, list) \
            and len(rk) < len(src):
        p.append("ranked (%d) is shorter than sources (%d) - the ranking is "
                 "being reported as the cut" % (len(rk), len(src)))
    c = resp.get("confidence")
    if c is not None and not (isinstance(c, (int, float)) and 0.0 <= c <= 1.0):
        p.append("confidence must be a number in 0..1 or absent, got %r" % c)
    return p


def normalise(resp):
    """Fill the optional fields so downstream code never guesses. Nothing
    required is invented - a missing required field stays missing so
    `validate` can name it."""
    out = dict(resp or {})
    for f in OPTIONAL:
        out.setdefault(f, None)
    return out


def load(name):
    """Resolve a pipeline by name to a callable `answer(question) -> dict`.

    A name that does not resolve ABORTS by name rather than falling back to
    the built-in one: a benchmark that silently measured `ask_v2` when asked
    for something else would publish a figure against the wrong system.
    """
    try:
        mod = importlib.import_module(name)
    except Exception as e:
        raise SystemExit("ABORT - no pipeline %r (%s: %s)"
                         % (name, type(e).__name__, str(e)[:120]))
    fn = getattr(mod, "answer", None)
    if not callable(fn):
        raise SystemExit("ABORT - pipeline %r has no callable answer()" % name)
    return fn


def ask(name, question, fn=None):
    """Call a pipeline and return a normalised, contract-checked response."""
    fn = fn or load(name)
    r = normalise(fn(question))
    r.setdefault("pipeline", name)
    return r


# ---------------------------------------------------------------------------
def _good():
    return {"answer": "a", "sources": [{"doc": "D", "clause": "1"}],
            "ranked": [{"point_id": "p1"}, {"point_id": "p2"}],
            "status": "supported_answer"}


def selftest():
    fails, ran = [], [0]

    def ck(name, cond):
        ran[0] += 1
        print("  %-72s %s" % (name, "ok" if cond else "FAIL"))
        if not cond:
            fails.append(name)

    src = open(os.path.abspath(__file__)).read()

    ck("a complete response passes", validate(_good()) == [])
    for f in REQUIRED:
        r = _good()
        del r[f]
        ck("a response missing %-8s is REFUSED and the field is NAMED" % f,
           any(f in p for p in validate(r)))
    ck("a status outside the 8 states is refused",
       any("not one of the 8" in p
           for p in validate(dict(_good(), status="looks_fine"))))
    ck("all 8 external-spec states are accepted",
       all(validate(dict(_good(), status=s)) == [] for s in STATUS))
    ck("the enum is the external spec's, not one invented here",
       len(STATUS) == 8 and "needs_clarification" in STATUS
       and "not invented here" in src)

    ck("a source without doc/clause cannot resolve a citation, and is refused",
       any("every source needs" in p
           for p in validate(dict(_good(), sources=[{"doc": "D"}]))))
    ck("a ranked entry without point_id cannot join a qrel, and is refused",
       any("every ranked entry needs" in p
           for p in validate(dict(_good(), ranked=[{"doc": "D"}]))))
    ck("a ranking SHORTER than the context is refused - that is the cut, not "
       "the ranking",
       any("reported as the cut" in p
           for p in validate(dict(_good(), ranked=[{"point_id": "p1"}],
                                  sources=[{"doc": "D", "clause": "1"},
                                           {"doc": "E", "clause": "2"}]))))
    ck("the two-run field-drop that motivated this is named in the file",
       "dropped this field for two whole runs" in src)

    ck("confidence is optional", validate(_good()) == [])
    ck("a confidence outside 0..1 is refused",
       any("0..1" in p for p in validate(dict(_good(), confidence=1.7))))
    ck("a confidence of 0 is legal, not falsy-rejected",
       validate(dict(_good(), confidence=0)) == [])
    ck("an errored response is dropped, not validated into failure",
       validate({"error": "boom"}) == [])

    n = normalise({"answer": "a"})
    ck("normalise fills every OPTIONAL field so nothing downstream guesses",
       all(f in n for f in OPTIONAL))
    ck("normalise does NOT invent a required field",
       "ranked" not in normalise({"answer": "a"}))

    try:
        load("p42_no_such_pipeline")
        refused = False
    except SystemExit:
        refused = True
    ck("an unknown pipeline ABORTS rather than falling back to ask_v2",
       refused and "would publish a figure against the wrong system" in src)

    ck("the governance fields are deliberately NOT imported",
       "policy_decision" in src and "deliberately does not import" in src
       and "policy_decision" not in str(REQUIRED + OPTIONAL))

    got = ask("x", "q", fn=lambda q: _good())
    ck("ask() returns a normalised response and records which pipeline",
       got["pipeline"] == "x" and got["confidence"] is None)

    print("\n  %d assertions, %d failed" % (ran[0], len(fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.
                                 RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        sys.exit(selftest())
    if a.list:
        print("required : %s" % ", ".join(REQUIRED))
        print("optional : %s" % ", ".join(OPTIONAL))
        print("status   : %s" % ", ".join(STATUS))
        sys.exit(0)
    ap.print_help()
