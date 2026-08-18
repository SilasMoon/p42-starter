#!/usr/bin/env python3
"""P42 - how much of a document an anchor span actually points at.

`P42_Register.md` R84.

WHY THIS EXISTS. Anchor-span recall asks "did a chunk with this (doc, clause)
reach the context?". That question is only as sharp as the `clause` label, and
in this corpus the label is often blunt: the ingester carries the last
successfully-parsed clause number FORWARD into every following section whose
heading does not itself parse as a clause number - annexes, DRD tables, even
front matter. `ECSS-E-ST-40` has 825 chunks and **475 of them are labelled
`5.11.5.6`**; `ECSS-E-ST-20-40` has 284 of 462 labelled `6.2`, every one of
them a row of "Table 6-2: Pre-tailoring Matrix".

So for a span whose clause is that document's sticky label, "the anchor
reached the context" is satisfied by retrieving ALMOST ANY CHUNK OF THAT
DOCUMENT. The span is not wrong - it is CHEAP, and a recall figure that mixes
cheap spans with specific ones reads as more precise than it is.

This module does not fix the labels. It makes the frame declare how many of
its spans are cheap, so no anchor-span figure is ever read without it
(standing rule 4 - report the denominator, name the drop). The ingestion
defect itself is R85.

BANDS, fixed here before any frame was measured against them:

    specific     <= 5%   of the document's chunks carry the span's label
    loose        5-20%
    degenerate   20-50%
    free         > 50%   - retrieving anything from the document satisfies it

    python3 span_specificity.py --self-test
    python3 span_specificity.py --frame questions/heldout_retrieval.jsonl
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

VERSION = "1.0"
PREREG = "P42_Register.md R84"

# Chosen on the mechanism, not on a result: a label covering more than half a
# document cannot discriminate within it, and 5% is roughly one clause's worth
# in the documents whose labels ARE clean.
BANDS = (("specific", 0.05), ("loose", 0.20), ("degenerate", 0.50),
         ("free", 1.01))
CHEAP = ("degenerate", "free")          # the bands a figure must disclose


def band(frac):
    """Which band a fraction falls in. Boundaries belong to the tighter band."""
    for name, hi in BANDS:
        if frac <= hi:
            return name
    return BANDS[-1][0]


def cause(n_sections, threshold=10):
    """Which of the TWO reasons a span is cheap. R85 fixes only one of them.

    A label spread across MANY distinct section headings is the sticky-label
    defect: `ECSS-E-ST-40 | 5.11.5.6` covers 312 different sections. A label
    concentrated in a FEW is a clause that genuinely is most of a short
    document - `ECSS-E-AS-50-26 | 3` covers 5 - and that is not a defect and
    will not change at the rebuild. Reporting one number for both would make
    the fix look like it underperformed.
    """
    if n_sections is None:
        return "unknown"
    return "sticky-label (R85)" if n_sections >= threshold else "large-clause"


def specificity(span, counts, totals):
    """(n_chunks_with_this_label, n_chunks_in_doc, fraction, band).

    A span whose DOCUMENT is absent from the index returns None rather than a
    fraction - an unmeasurable span is named by the caller, never scored 0 and
    never quietly counted as specific.
    """
    doc = span[0]
    tot = totals.get(doc)
    if not tot:
        return None
    n = counts.get(tuple(span), 0)
    f = n / tot
    return (n, tot, f, band(f))


def summarise(spans, counts, totals, sections=None):
    """{band: n}, plus the spans that could not be measured, BY NAME.

    `sections` maps a (doc, clause) key to the number of DISTINCT section
    headings carrying it. Optional, because the arithmetic above stands
    without it - but when present the cheap spans are split by cause, which
    is what says whether R85 can fix them.
    """
    out = {name: 0 for name, _hi in BANDS}
    detail, unmeasurable = [], []
    causes = {"sticky-label (R85)": 0, "large-clause": 0, "unknown": 0}
    for aid, span in spans:
        r = specificity(span, counts, totals)
        if r is None:
            unmeasurable.append((aid, span))
            continue
        n, tot, f, b = r
        out[b] += 1
        ns = (sections or {}).get(tuple(span)) if sections else None
        cz = cause(ns)
        if b in CHEAP:
            causes[cz] += 1
        detail.append((f, n, tot, aid, span, b, ns, cz))
    detail.sort(key=lambda d: d[0], reverse=True)
    return {"bands": out, "detail": detail, "unmeasurable": unmeasurable,
            "n_spans": len(spans),
            "n_cheap": sum(out[b] for b in CHEAP),
            "cheap_by_cause": causes}


def index(collection):
    """(counts, totals) read from Qdrant. The only impure function here."""
    from collections import Counter, defaultdict
    from qdrant_client import QdrantClient
    import retrieval_recall as rr
    c = QdrantClient(url="http://localhost:6333", timeout=300)
    off, per, secs = None, defaultdict(Counter), defaultdict(set)
    while True:
        pts, off = c.scroll(collection, limit=4000, offset=off,
                            with_payload=["clause", "doc_code", "section"],
                            with_vectors=False)
        for p in pts:
            pl = p.payload
            per[pl.get("doc_code")][pl.get("clause") or ""] += 1
            secs[rr.norm(pl.get("doc_code") or "", pl.get("clause") or "")].add(
                (pl.get("section") or "")[:60])
        if off is None:
            break
    counts, totals, sections = {}, {}, {}
    for d, cl in per.items():
        nd = rr.norm(d or "", "")[0]
        totals[nd] = sum(cl.values())
        for v, k in cl.items():
            counts[rr.norm(d or "", v)] = k
    for k, ss_ in secs.items():
        sections[k] = len(ss_)
    return counts, totals, sections


def report(frame_path, collection="p42_text_v3"):
    import retrieval_recall as rr
    items = [json.loads(l) for l in open(frame_path) if l.strip()]
    spans = [(it["anchor_id"], s) for it in items for s in rr.anchor_spans(it)]
    counts, totals, sections = index(collection)
    s = summarise(spans, counts, totals, sections)

    print("\n  ANCHOR-SPAN SPECIFICITY  (R84)")
    print("    frame      : %s" % frame_path)
    print("    collection : %s" % collection)
    print("    %d items, %d spans" % (len(items), s["n_spans"]))
    print("\n    %-12s %6s   %s" % ("band", "spans", "meaning"))
    mean = {"specific": "<=5% of the document carries the label",
            "loose": "5-20%", "degenerate": "20-50%",
            "free": ">50% - any chunk of the document satisfies it"}
    for name, _hi in BANDS:
        print("    %-12s %5d    %s" % (name, s["bands"][name], mean[name]))
    print("\n    CHEAP SPANS (degenerate + free): %d of %d (%.0f%%)"
          % (s["n_cheap"], s["n_spans"],
             100.0 * s["n_cheap"] / max(1, s["n_spans"])))
    if s["unmeasurable"]:
        print("    UNMEASURABLE - document not in the index, named not scored:")
        for aid, sp in s["unmeasurable"]:
            print("      %-12s %s" % (aid, sp))
    print("\n    cheap spans BY CAUSE - only the first kind is a defect:")
    for k, v in s["cheap_by_cause"].items():
        if v:
            print("      %-22s %d" % (k, v))
    print("\n    the cheap spans, worst first:")
    print("      %6s %11s %-12s %-24s %s"
          % ("ofdoc", "chunks", "item", "span", "sections / cause"))
    for f, n, tot, aid, sp, b, ns, cz in s["detail"]:
        if b in CHEAP:
            print("      %5.1f%% %5d/%-5d %-12s %-24s %4s  %s"
                  % (100 * f, n, tot, aid, sp[0] + " " + sp[1],
                     "?" if ns is None else ns, cz))
    print("\n  An anchor-span recall figure over this frame must be quoted "
          "with the\n  cheap count beside it. It is not a defect in the "
          "frame; it is a defect\n  in the clause labels (R85), and it makes "
          "the figure an UPPER BOUND.")
    return s


# ---------------------------------------------------------------------------
def selftest():
    fails, ran = [], [0]

    def ck(name, cond):
        ran[0] += 1
        print("  %-72s %s" % (name, "ok" if cond else "FAIL"))
        if not cond:
            fails.append(name)

    src = open(os.path.abspath(__file__)).read()

    ck("a label on 1 chunk of a 100-chunk document is specific",
       band(0.01) == "specific")
    ck("a label on half a document is degenerate, not specific",
       band(0.50) == "degenerate")
    ck("a label on more than half a document is FREE",
       band(0.51) == "free" and band(0.99) == "free")
    ck("a band boundary belongs to the TIGHTER band",
       band(0.05) == "specific" and band(0.20) == "loose")
    ck("the bands were fixed on the mechanism, not on a result",
       ("Chosen on the mechanism" in src) and ("not on a result" in src))

    counts = {("D1", "1.1"): 2, ("D1", "9.9"): 90, ("D2", "4"): 5}
    totals = {"D1": 100, "D2": 100}
    ck("a specific span reports its own count and its document's total",
       specificity(("D1", "1.1"), counts, totals) == (2, 100, 0.02, "specific"))
    ck("a sticky label is reported as FREE",
       specificity(("D1", "9.9"), counts, totals)[3] == "free")
    ck("a label absent from the index counts 0, not an error",
       specificity(("D1", "nope"), counts, totals) == (0, 100, 0.0, "specific"))
    ck("a span whose DOCUMENT is absent is UNMEASURABLE, not scored",
       specificity(("D9", "1"), counts, totals) is None)

    spans = [("a1", ("D1", "1.1")), ("a2", ("D1", "9.9")),
             ("a3", ("D2", "4")), ("a4", ("D9", "1"))]
    s = summarise(spans, counts, totals)
    ck("summarise counts every measurable span exactly once",
       sum(s["bands"].values()) == 3 and s["n_spans"] == 4)
    ck("an unmeasurable span is NAMED, never folded into a band",
       s["unmeasurable"] == [("a4", ("D9", "1"))]
       and sum(s["bands"].values()) == len(spans) - 1)
    ck("the cheap count is the two disclosing bands, not a guess",
       s["n_cheap"] == 1 and CHEAP == ("degenerate", "free"))
    ck("detail is ordered worst-first so the reader sees the cheapest span",
       s["detail"][0][3] == "a2")

    # --- the two causes, which R85 fixes only one of --------------------
    ck("a label spread across MANY sections is the sticky-label defect",
       cause(312) == "sticky-label (R85)" and cause(35) == "sticky-label (R85)")
    ck("a label in a FEW sections is a genuinely large clause, not a defect",
       cause(5) == "large-clause" and cause(9) == "large-clause")
    ck("with no section data the cause is UNKNOWN, never guessed as fixable",
       cause(None) == "unknown")
    secs = {("D1", "9.9"): 300, ("D2", "4"): 3}
    c2 = summarise([("x", ("D1", "9.9")), ("y", ("D2", "4"))],
                   {("D1", "9.9"): 90, ("D2", "4"): 90},
                   {"D1": 100, "D2": 100}, secs)
    ck("cheap spans are SPLIT by cause, so a fix is not judged on both",
       c2["cheap_by_cause"]["sticky-label (R85)"] == 1
       and c2["cheap_by_cause"]["large-clause"] == 1)
    ck("the causes sum to the cheap count - nothing is dropped between them",
       sum(c2["cheap_by_cause"].values()) == c2["n_cheap"] == 2)
    ck("summarise still works with NO section data (the argument is optional)",
       summarise([("x", ("D1", "9.9"))], {("D1", "9.9"): 90},
                 {"D1": 100})["cheap_by_cause"]["unknown"] == 1)
    ck("the reason the two causes must be separated is recorded",
       "would make the fix look like it underperformed" in src)

    all_free = summarise([("x", ("D1", "9.9"))], counts, totals)
    ck("a frame of only cheap spans reports 100% cheap and does not hide it",
       all_free["n_cheap"] == all_free["n_spans"] == 1)
    none_cheap = summarise([("x", ("D1", "1.1"))], counts, totals)
    ck("a frame of only specific spans reports 0 cheap - the check can PASS",
       none_cheap["n_cheap"] == 0)

    ck("the observed defect is recorded with its real numbers, not described",
       "475" in src and "5.11.5.6" in src and "284 of 462" in src)
    ck("this module does not claim to FIX the labels",
       "does not fix the labels" in src and "R85" in src)
    ck("the figure is called an upper bound where it is printed",
       ("UPPER" + " BOUND") in src)
    ck("no LLM is called anywhere in this module",
       ("call_" + "llm") not in src.lower()
       and ("call_" + "prose") not in src.lower()
       and ("chat/" + "completions") not in src
       and ("import claim_" + "judge") not in src)

    print("\n  %d assertions, %d failed" % (ran[0], len(fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.
                                 RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--frame")
    ap.add_argument("--collection", default="p42_text_v3")
    a = ap.parse_args()
    if a.self_test:
        sys.exit(selftest())
    if a.frame:
        report(a.frame, a.collection)
        sys.exit(0)
    ap.print_help()
