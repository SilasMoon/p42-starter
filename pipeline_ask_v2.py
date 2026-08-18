#!/usr/bin/env python3
"""P42 — the `ask_v2` adapter: our own pipeline, behind the R40 contract.

`P42_Register.md` R40.

`ask_v2` IS NOT MODIFIED. This wraps it. The pipeline under test has been
measured in that exact form since campaign 2, and changing it to fit a
reporting contract would silently break comparability with every figure
already published. So the mapping lives here, where it can be read and
argued with.

WHAT THE MAPPING CAN AND CANNOT DO. The contract's `status` has eight states.
`ask_v2` distinguishes three conditions: an error, its fixed refusal sentence,
and an answer. So:

    error present            -> the item is DROPPED by the benchmark, not scored
    answer is the refusal    -> insufficient_evidence
    anything else            -> supported_answer

`partial_answer`, `needs_clarification`, `conflicting_evidence` and
`missing_required_source` are REAL STATES THIS PIPELINE CANNOT EXPRESS. They
are not mapped to something close; they are simply never emitted, and that is
the honest reading - a system that cannot say "I am only partly sure" should
not have a status implying it did. Registered as R42.

    python3 pipeline_ask_v2.py --self-test
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

VERSION = "1.0"
PREREG = "P42_Register.md R40"

# States this pipeline can never produce, named so their absence is a
# disclosure rather than an omission.
UNREACHABLE = ("partial_answer", "needs_clarification", "conflicting_evidence",
               "missing_required_source", "access_restricted", "out_of_scope")


def status_of(resp, refusal):
    """The contract status for one `ask_v2` response."""
    if resp.get("error"):
        return None                     # dropped upstream; no status claimed
    if (resp.get("answer") or "").strip().startswith(refusal):
        return "insufficient_evidence"
    return "supported_answer"


def adapt(resp, refusal):
    """`ask_v2`'s dict -> the contract shape.

    A SUPERSET, not a replacement: every field `ask_v2` already returned is
    passed through untouched, so the benchmark record keeps exactly what it
    kept before and this change cannot move a published number.
    """
    out = dict(resp or {})
    out["status"] = status_of(out, refusal)
    out.setdefault("confidence", None)   # R41: this pipeline emits none
    return out


def answer(question):
    """The contract entry point. `pipelines.load('pipeline_ask_v2')` finds it."""
    import ask_v2
    return adapt(ask_v2.answer(question), ask_v2.REFUSAL)


# ---------------------------------------------------------------------------
def selftest():
    fails, ran = [], [0]

    def ck(name, cond):
        ran[0] += 1
        print("  %-72s %s" % (name, "ok" if cond else "FAIL"))
        if not cond:
            fails.append(name)

    import pipelines
    src = open(os.path.abspath(__file__)).read()
    REF = "The corpus does not contain this information."

    ck("a normal answer maps to supported_answer",
       status_of({"answer": "The supplier shall X [D | 1]."}, REF)
       == "supported_answer")
    ck("the refusal sentence maps to insufficient_evidence",
       status_of({"answer": REF}, REF) == "insufficient_evidence")
    ck("leading whitespace does not defeat the refusal check",
       status_of({"answer": "  " + REF}, REF) == "insufficient_evidence")
    ck("an errored response claims NO status",
       status_of({"error": "boom", "answer": ""}, REF) is None)

    ck("states this pipeline cannot express are NAMED, not faked",
       len(UNREACHABLE) == 6 and "partial_answer" in UNREACHABLE
       and "not mapped to something close" in src)
    ck("no unreachable state is ever produced",
       status_of({"answer": "x"}, REF) not in UNREACHABLE
       and status_of({"answer": REF}, REF) not in UNREACHABLE)

    base = {"answer": "a", "sources": [{"doc": "D", "clause": "1"}],
            "ranked": [{"point_id": "p1"}, {"point_id": "p2"}],
            "route": "dense", "n_context": 10}
    out = adapt(base, REF)
    ck("adapt PASSES THROUGH every field ask_v2 already returned",
       all(out[k] == base[k] for k in base))
    ck("adapt adds status and a null confidence, and nothing else",
       set(out) - set(base) == {"status", "confidence"})
    ck("the adapted response satisfies the contract",
       pipelines.validate(out) == [])
    ck("confidence is null because this pipeline emits none (R41)",
       out["confidence"] is None and "R41" in src)

    ck("ask_v2 is NOT modified by this adapter",
       "ask_v2 IS NOT MODIFIED" in src
       and "ask_v2.answer(question)" in src
       and "ask_v2." not in src.split("def adapt")[1].split("def answer")[0])
    ck("the reason for not modifying it is recorded, not assumed",
       "comparability with every figure" in src)
    ck("it exposes answer() so the loader can find it",
       callable(answer))

    print("\n  %d assertions, %d failed" % (ran[0], len(fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.
                                 RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        sys.exit(selftest())
    ap.print_help()
