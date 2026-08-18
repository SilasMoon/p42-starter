#!/usr/bin/env python3
"""P42 — anchor-span recall into context, across retrieval configurations.

Pre-registered in `P42_Retrieval_Diagnosis.md` §7, written before this ran.

§4 of that document measured only the twelve anchor spans the benchmark lost.
A test run on the failures can show a GAIN and is structurally incapable of
showing a LOSS. This runs all 56 adopted items under four configurations and
reports gains and losses SEPARATELY - a configuration that recovers 8 spans and
loses 6 is not "+2", it is a different pipeline with a different failure set.

    metric   anchor spans reaching the final context, over total anchor spans,
             after retrieval -> cross-encoder rerank -> de-duplication -> cut
    proxy    for claim coverage, and named as one: items whose anchors reach
             context scored 0.936, items whose anchors did not scored 0.167
             (§2). It is not the benchmark and produces no score.

NO LLM IS CALLED. Retrieval and the cross-encoder only, so nothing this prints
can be mistaken for a benchmark figure. Retrieval is deterministic (benchmark
protocol §10a, identical on 56/56), so the sweep is reproducible.

    python3 retrieval_recall.py --self-test
    python3 retrieval_recall.py --run \
        --adopted census/2026-08-14_135406/scored/adopted_2026-08-14_151129.jsonl
"""
import argparse
import json
import os
import sys
import time
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import benchmark as bm                                       # noqa: E402

VERSION = "1.0"
PREREG = "P42_Retrieval_Diagnosis.md v1.1 §7"

# §7, fixed before the run. (label, TOP_K, query field)
CONFIGS = (("A baseline", 50, "prompt_as_typed"),
           ("B k=200", 200, "prompt_as_typed"),
           ("C q-only", 50, "question"),
           ("D k=200 q-only", 200, "question"))
BASELINE = "A baseline"


def norm(doc, clause):
    return ((doc or "").strip(), (clause or "").strip())


def anchor_spans(item):
    """The (doc, clause) pairs an answer must draw on. Aborts if there are none:
    an item with no anchor cannot be scored by this metric and must not be
    silently counted as a pass."""
    spans = (item.get("_anchor") or {}).get("spans") or []
    out = {norm(s.get("doc_code"), s.get("clause")) for s in spans}
    out.discard(("", ""))
    return out


def query_for(item, field):
    if field == "question":
        return item.get("question") or item.get("prompt_as_typed") or ""
    return item.get("prompt_as_typed") or "%s %s" % (item.get("context", ""),
                                                     item.get("question", ""))


def context_for(query, top_k, retrieve_fn, rerank_fn, context_k):
    """The passages the pipeline would hand the model. Mirrors ask_v2.answer()'s
    order exactly - retrieve, rerank the WHOLE pool, de-duplicate, then cut -
    because a recall figure measured on a different order measures nothing."""
    hits, _route = retrieve_fn(query, k=top_k)
    chunks = [{"text": h.payload.get("text", ""),
               "doc": h.payload.get("doc_code")
               or h.payload.get("source_file", ""),
               "clause": h.payload.get("clause", ""),
               "crumb": h.payload.get("crumb", "")} for h in hits]
    chunks, _n = rerank_fn(query, chunks)
    seen, ctx = set(), []
    for c in chunks:
        k = (c["doc"], c["clause"], c["crumb"])
        if k in seen:
            continue
        seen.add(k)
        ctx.append(c)
        if len(ctx) == context_k:
            break
    return ctx


def sweep(items, retrieve_fn, rerank_fn, context_k, configs=CONFIGS,
          progress=None):
    """{config: {item: set(spans reached)}}. Pure apart from the two callables,
    so the self-test drives it with fakes and exercises the real arithmetic."""
    got = {label: {} for label, _k, _f in configs}
    for n, it in enumerate(items, 1):
        need = anchor_spans(it)
        for label, top_k, field in configs:
            ctx = context_for(query_for(it, field), top_k, retrieve_fn,
                              rerank_fn, context_k)
            have = {norm(c["doc"], c["clause"]) for c in ctx}
            got[label][it["anchor_id"]] = need & have
        if progress:
            progress(n, it["anchor_id"])
    return got


def compare(items, got, baseline=BASELINE):
    """Gains and losses against the baseline, per §7 never netted into one."""
    need = {it["anchor_id"]: anchor_spans(it) for it in items}
    total = sum(len(v) for v in need.values())
    rows = {}
    for label in got:
        reached = sum(len(got[label][a]) for a in need)
        full = sum(1 for a in need if need[a] and got[label][a] == need[a])
        none = sum(1 for a in need if need[a] and not got[label][a])
        gains, losses = [], []
        for a in need:
            b = got[baseline][a]
            for s in sorted(got[label][a] - b):
                gains.append((a, s))
            for s in sorted(b - got[label][a]):
                losses.append((a, s))
        rows[label] = {"spans_reached": reached, "spans_total": total,
                       "items_all_spans": full, "items_no_span": none,
                       "items_total": len(need),
                       "gains": gains, "losses": losses}
    return rows


def run(adopted_path, outroot, unregistered=None):
    """`unregistered` names a population that is NOT a registered benchmark
    frame - a held-out sanity check, say. The frame assertion is then skipped
    BY NAME and the label is stamped through the output and the record, so a
    run on some other file can never be mistaken for the benchmark (rule 77
    exists because exactly that happened). Skipping it silently is not
    offered."""
    if unregistered:
        items = [json.loads(l) for l in open(adopted_path) if l.strip()]
        print("UNREGISTERED FRAME: %r" % unregistered)
        print("  This is NOT the benchmark frame and its numbers are not the")
        print("  benchmark. The protocol's per-class counts are NOT asserted.")
    else:
        items, problems = bm.load_adopted(adopted_path)
        if problems:
            print("ABORT - the frame is not what the protocol registered:")
            for p_ in problems:
                print("   " + p_)
            return 1
    noanchor = [it["anchor_id"] for it in items if not anchor_spans(it)]
    if noanchor:
        print("ABORT - %d item(s) carry no anchor span, so this metric cannot "
              "score them: %s" % (len(noanchor), ", ".join(noanchor)))
        return 1
    print("frame: %s\n  %d items, %d anchor spans, sha256 %s"
          % (adopted_path, len(items),
             sum(len(anchor_spans(i)) for i in items),
             bm.digest(adopted_path)[:16]))
    print("  NO LLM IS CALLED - retrieval and the cross-encoder only. This "
          "produces no score.")
    print("  configurations (§7, fixed before the run):")
    for label, k, f in CONFIGS:
        print("    %-16s TOP_K=%-4d query=%s" % (label, k, f))

    import retrieve as retrieve_mod
    import span_specificity as ss
    from retrieve import retrieve
    import ask_v2
    t0 = time.time()

    def prog(n, aid):
        print("  %2d/%d  %s" % (n, len(items), aid))

    got = sweep(items, retrieve, ask_v2.rerank, ask_v2.CONTEXT_K,
                progress=prog)
    dt = time.time() - t0
    rows = compare(items, got)

    print("\n  %d items x %d configurations in %.0fs"
          % (len(items), len(CONFIGS), dt))

    # R84. Anchor-span recall is only as sharp as the clause label, and in this
    # corpus the label sticks (R85). Every figure below is therefore an upper
    # bound, and the frame declares by how much rather than leaving the reader
    # to assume all spans are equal (rule 4).
    try:
        counts, totals, sections = ss.index(retrieve_mod.COLL)
    except Exception as e:
        raise SystemExit("ABORT - cannot compute span specificity (R84) from "
                         "%r: %s: %s. A recall figure is not published "
                         "without it." % (retrieve_mod.COLL, type(e).__name__,
                                          str(e)[:100]))
    spec = ss.summarise([(it["anchor_id"], sp) for it in items
                         for sp in anchor_spans(it)], counts, totals,
                        sections)
    print("\n  SPAN SPECIFICITY (R84) - how much of a document each span "
          "points at")
    print("    %s" % "   ".join("%s %d" % (b, spec["bands"][b])
                                for b, _h in ss.BANDS))
    print("    CHEAP (degenerate+free): %d of %d spans (%.0f%%) - the figures "
          "below are UPPER BOUNDS"
          % (spec["n_cheap"], spec["n_spans"],
             100.0 * spec["n_cheap"] / max(1, spec["n_spans"])))
    print("    cheap by cause: %s"
          % ("  ".join("%s %d" % (k, v)
                       for k, v in spec["cheap_by_cause"].items() if v)
             or "none"))
    if spec["unmeasurable"]:
        print("    UNMEASURABLE spans, named: %s"
              % ", ".join("%s %s" % (a, sp) for a, sp in spec["unmeasurable"]))
    print("\n  ANCHOR-SPAN RECALL INTO CONTEXT  (proxy for coverage, §7)")
    print("  %-16s %14s %16s %14s" % ("config", "spans reached",
                                      "items all spans", "items none"))
    for label, _k, _f in CONFIGS:
        r = rows[label]
        print("  %-16s %8d/%-5d %10d/%-5d %8d/%-5d"
              % (label, r["spans_reached"], r["spans_total"],
                 r["items_all_spans"], r["items_total"],
                 r["items_no_span"], r["items_total"]))

    print("\n  AGAINST THE BASELINE - gains and losses, never netted (§7)")
    for label, _k, _f in CONFIGS:
        if label == BASELINE:
            continue
        r = rows[label]
        print("  %-16s +%d recovered   -%d LOST"
              % (label, len(r["gains"]), len(r["losses"])))
        for a, s in r["losses"]:
            print("       LOST  %-12s %s | %s" % (a, s[0], s[1]))

    clean = [lb for lb, _k, _f in CONFIGS
             if lb != BASELINE and not rows[lb]["losses"]]
    print("\n  §7 decision rule, fixed before these numbers existed:")
    print("    - a configuration that loses a span the baseline reaches is "
          "NOT adopted on this evidence")
    print("    - a clean result does NOT authorise adoption either: these are "
          "the 56 items")
    print("      that exposed the defect. It authorises building design §9's "
          "splits and testing there.")
    print("    lossless configurations: %s"
          % (", ".join(clean) if clean else "NONE"))

    stamp = time.strftime("%Y-%m-%d_%H%M%S")
    outdir = os.path.join(outroot, stamp)
    os.makedirs(outdir, exist_ok=True)
    # WHICH INDEX ANSWERED. Two runs of this tool that differ only by
    # P42_COLL produce records that are otherwise identical - so without this
    # field the comparison rests on which shell set which variable, i.e. on
    # memory. `benchmark.py` has recorded it since 2026-08-16; this tool did
    # not, and R10b is the first comparison that turns on it (rule 75).
    summary = {"version": VERSION, "prereg": PREREG, "stamp": stamp,
               "collection": retrieve_mod.COLL,
               "adopted_record": adopted_path,
               "adopted_sha256": bm.digest(adopted_path),
               "context_k": ask_v2.CONTEXT_K, "elapsed_s": round(dt, 1),
               "configs": [{"label": lb, "top_k": k, "query": f}
                           for lb, k, f in CONFIGS],
               "lossless": clean,
               "span_specificity": {"bands": spec["bands"],
                                    "n_cheap": spec["n_cheap"],
                                    "n_spans": spec["n_spans"],
                                    "cheap_by_cause": spec["cheap_by_cause"],
                                    "unmeasurable":
                                    [[a, list(x)] for a, x
                                     in spec["unmeasurable"]]},
               "unregistered_frame": unregistered,
               "results": {lb: {kk: (vv if kk not in ("gains", "losses")
                                     else [[a, list(s)] for a, s in vv])
                                for kk, vv in rows[lb].items()}
                           for lb in rows},
               "per_item": {lb: {a: sorted(list(s))
                                 for a, s in got[lb].items()} for lb in got}}
    sp = os.path.join(outdir, "retrieval_recall_%s.json" % stamp)
    open(sp, "w").write(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print("\n  summary -> %s" % sp)
    return 0


# ---------------------------------------------------------------------------
def selftest():
    fails, ran = [], [0]

    def ck(name, cond):
        ran[0] += 1
        print("  %-70s %s" % (name, "ok" if cond else "FAIL"))
        if not cond:
            fails.append(name)

    src = open(os.path.abspath(__file__)).read()

    def it(aid, spans, q="the question", p="persona. the question"):
        return {"anchor_id": aid, "question": q, "prompt_as_typed": p,
                "_anchor": {"spans": [{"doc_code": d, "clause": c}
                                      for d, c in spans]}}

    class H(object):
        def __init__(self, d, c, t=""):
            self.payload = {"doc_code": d, "clause": c, "text": t,
                            "crumb": "%s|%s" % (d, c)}

    ck("configurations are fixed in the module, not chosen at the prompt",
       len(CONFIGS) == 4 and CONFIGS[0][0] == BASELINE
       and [c[1] for c in CONFIGS] == [50, 200, 50, 200])
    ck("the baseline configuration is the pipeline as it actually runs",
       CONFIGS[0][1] == 50 and CONFIGS[0][2] == "prompt_as_typed")

    ck("anchor spans are read from the anchor record, doc and clause",
       anchor_spans(it("A", [("D1", "1.1"), ("D2", "2.2")]))
       == {("D1", "1.1"), ("D2", "2.2")})
    ck("an item with no anchor span yields an empty set, not a false pass",
       anchor_spans({"anchor_id": "X", "_anchor": {}}) == set())
    ck("the question-only query really is the question, not the whole prompt",
       query_for(it("A", []), "question") == "the question"
       and query_for(it("A", []), "prompt_as_typed") == "persona. the question")

    # context assembly must mirror ask_v2: rerank the WHOLE pool, then cut
    pool = [H("D%d" % i, "%d.0" % i) for i in range(1, 21)]

    def ret(q, k):
        return pool[:k], "route"

    def rr_reverse(q, chunks):
        return list(reversed(chunks)), "reranked"
    ctx = context_for("q", 20, ret, rr_reverse, 3)
    ck("the reranker is applied to the WHOLE pool before the cut, not after",
       [c["doc"] for c in ctx] == ["D20", "D19", "D18"])
    ck("a larger TOP_K changes what the reranker can promote",
       [c["doc"] for c in context_for("q", 5, ret, rr_reverse, 3)]
       == ["D5", "D4", "D3"])

    dup = [H("D1", "1.0"), H("D1", "1.0"), H("D2", "2.0")]
    ck("de-duplication happens before the cut, as in ask_v2",
       len(context_for("q", 3, lambda q, k: (dup[:k], "r"),
                       lambda q, c: (c, "n"), 3)) == 2)

    # the arithmetic, on fakes: config C reaches a span A misses, and loses one
    items = [it("I1", [("D1", "1.0")]), it("I2", [("D2", "2.0")])]

    def ret2(q, k):
        # question-only finds D1 for I1; the persona prompt finds D2 instead
        return ([H("D1", "1.0")] if q == "the question"
                else [H("D2", "2.0")]), "r"
    got = sweep(items, ret2, lambda q, c: (c, "n"), 10)
    rows = compare(items, got)
    ck("a configuration that reaches a new span records it as a GAIN",
       len(rows["C q-only"]["gains"]) == 1
       and rows["C q-only"]["gains"][0][0] == "I1")
    ck("a configuration that drops a baseline span records it as a LOSS",
       len(rows["C q-only"]["losses"]) == 1
       and rows["C q-only"]["losses"][0][0] == "I2")
    ck("gains and losses are separate fields and are never netted (§7)",
       "gains" in rows["C q-only"] and "losses" in rows["C q-only"]
       and "net" not in rows["C q-only"])
    ck("the loss is named with its item and its document/clause",
       rows["C q-only"]["losses"][0][1] == ("D2", "2.0"))
    ck("a lossless configuration is identified only when it loses NOTHING",
       rows[BASELINE]["losses"] == [])
    ck("every count carries its denominator (rule: no bare percentage)",
       rows[BASELINE]["spans_total"] == 2
       and rows[BASELINE]["items_total"] == 2)

    # An item with no anchor span must abort the run, not be counted as a pass.
    # Driven, not grepped: compare() would otherwise score it items_all_spans.
    noanchor = [{"anchor_id": "N1", "question": "q", "prompt_as_typed": "p",
                 "_anchor": {"spans": []}}]
    g2 = sweep(noanchor, lambda q, k: ([], "r"), lambda q, c: (c, "n"), 10)
    r2 = compare(noanchor, g2)
    ck("an anchor-less item is never counted as having all its spans reached",
       r2[BASELINE]["items_all_spans"] == 0
       and r2[BASELINE]["spans_total"] == 0)
    ck("the run ABORTS on an anchor-less item rather than scoring it",
       ("no anchor " + "span, so this metric") in src and "ABORT" in src)
    ck("a campaign-3 frame can be checked without duplicating the frame rules",
       ("EXPECTED_COUNTS_" + "C3") in src and "--campaign" in src)
    ck("the frame is checked by benchmark.load_adopted, so rule 77 travels",
       "bm.load_adopted(adopted_path)" in src)
    # Needles built at runtime: written whole, each would plant the very string
    # it searches for and the assertion could never fail (rule 3, inverted).
    ck("an unregistered frame must be NAMED - it cannot be skipped silently",
       ("unregistered=None" in src) and ("UNREGISTERED FRAME" in src)
       and ("Skipping it silently is not" in src))
    ck("the label is stamped into the record so it cannot pass as the benchmark",
       '"unregistered_frame": unregistered' in src)
    ck("the registered path still asserts the protocol counts",
       "bm.load_adopted(adopted_path)" in src
       and "the frame is not what the" in src)

    ck("the record NAMES the collection that answered",
       '"collection": retrieve_mod.COLL' in src)
    ck("the module alias is NOT shadowed by the imported function of the "
       "same name",
       "import retrieve as retrieve_mod" in src
       and "from retrieve import retrieve" in src
       and ("retrieve" + ".COLL")
       not in src.replace("retrieve_mod" + ".COLL", ""))
    ck("the reason the collection is recorded is stated, not assumed",
       "rests on which shell set which variable" in src)

    ck("every run DISCLOSES how many of its spans are cheap (R84)",
       "span_specificity" in src and 'spec["n_cheap"]' in src
       and ("UPPER" + " BOUNDS") in src)
    # The 2026-08-18 near-miss: span_specificity.index() grew a third return
    # value and this call site still unpacked two. Nothing in this self-test
    # touches Qdrant, so 29 assertions passed against a module that would have
    # crashed on its first real run. Assert the CONTRACT between the modules.
    import inspect
    import span_specificity as _ss
    _ret = [l.strip() for l in inspect.getsource(_ss.index).splitlines()
            if l.strip().startswith("return ")][-1][len("return "):]
    _lhs = src.split("= ss.index(")[0].splitlines()[-1]
    ck("span_specificity.index() returns exactly as many values as this "
       "module unpacks - the cross-module contract a Qdrant-free test misses",
       _ret.count(",") + 1 == _lhs.count(",") + 1)

    ck("a run that cannot compute the disclosure ABORTS rather than "
       "publishing a bare recall figure",
       "cannot compute span specificity" in src
       and "is not published" in src)

    ck("no LLM is called anywhere in this module",
       ("call_" + "llm") not in src.lower()
       and ("chat/" + "completions") not in src
       and ("import claim_" + "judge") not in src)
    ck("the metric is declared a PROXY for coverage, not a score",
       "proxy" in src.lower() and ("claim " + "coverage") in src.lower()
       and ("produces no " + "score") in src)
    ck("the decision rule states that a clean result does not authorise "
       "adoption", "does NOT authorise adoption" in src)

    print("\n  %d assertions, %d failed" % (ran[0], len(fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.
                                 RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--adopted", metavar="ADOPTED_JSONL")
    ap.add_argument("--unregistered", metavar="LABEL",
                    help="run on a population that is NOT a registered frame; "
                         "the label is stamped through the output and record")
    ap.add_argument("--campaign", type=int, default=2, choices=(2, 3),
                    help="which registered frame to check the file against. "
                         "3 = the 111 campaign-3 questions (benchmark protocol "
                         "§11). The frame check lives in benchmark.py and is "
                         "reused rather than duplicated.")
    ap.add_argument("--out", default=os.path.expanduser("~/p42/retrieval"))
    a = ap.parse_args()
    if a.self_test:
        sys.exit(selftest())
    if a.campaign == 3:
        g = vars(bm)
        g["EXPECTED_COUNTS"] = bm.EXPECTED_COUNTS_C3
        g["EXPECTED_TOTAL"] = bm.EXPECTED_TOTAL_C3
        g["SCORED_CLASSES"] = bm.SCORED_CLASSES_C3
        g["UNSCORED_CLASSES"] = bm.UNSCORED_CLASSES_C3
        g["WEIGHTED"] = False
    if a.run:
        if not a.adopted:
            ap.error("--run needs --adopted")
        sys.exit(run(a.adopted, a.out, a.unregistered))
    ap.print_help()
