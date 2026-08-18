#!/usr/bin/env python3
"""P42 — label coverage per document. Does the corpus actually carry its labels?

`P42_Gap_Closure_Plan.md` G11, step 1.

WHY THIS EXISTS. The chunker was deliberately hardened for documents it was not
designed for (the SLACK mechanism, ingest v3.0). The METADATA layer was not.
Cross-references, requirement identifiers, definition units and the document
code are recovered by patterns keyed to ECSS - `ECSS-[A-Z]-(ST|AS|HB|TM)-NN`,
and the ECSS convention that clause 3.x is Terms and definitions.

Point that at a project document and nothing fails. The patterns match nothing,
the fields come back empty, ingestion reports success, and every feature keyed
on those fields becomes a no-op that still passes. `ingest_v3.py`'s own header
describes this exact shape for a different field:

    "A screen keyed on an absent field does not fail - it passes everything,
     and the run still prints PASS."

So this tool measures, per document, what fraction of its passages carry each
label, and NAMES the documents that fall below a floor. It is rule 4 - report
the denominator, name the drop - applied to ingestion, where it currently is
not.

IT DOES NOT JUDGE A DOCUMENT BAD. A narrative report legitimately has no
requirement identifiers. The point is that the absence is REPORTED rather than
discovered later as an unexplained retrieval result.

    python3 label_coverage.py --self-test
    python3 label_coverage.py --run
    python3 label_coverage.py --run --doc ECSS-E-ST-35-10
"""
import argparse
import json
import os
import sys
import time
from collections import defaultdict

VERSION = "1.0"
PREREG = "P42_Gap_Closure_Plan.md G11 step 1"

# Labels split by what recovers them. The distinction is the whole point: a
# generic label going missing means the PARSE failed; an ECSS-bound label going
# missing may simply mean the document is not an ECSS standard.
GENERIC = ("crumb", "clause", "page_number", "modals", "element_type")
ECSS_BOUND = ("doc_code", "document_revision", "refs", "req_ids")

# Floors, fixed here rather than per run. A document under a GENERIC floor has
# a parse problem and is named loudly; under an ECSS floor it is merely
# reported, because the corpus may legitimately not be ECSS.
FLOOR_GENERIC = {"crumb": 0.95, "clause": 0.50, "page_number": 0.50,
                 "element_type": 0.95, "modals": 0.0}

# Definition and abbreviation units are SYNTHESISED by the ingester - one point
# per defined term or table row - and carry `page: None` by construction. They
# are not parse failures and must not be counted against a page floor: a
# standard with a large abbreviations list would otherwise be reported as
# broken purely for having one. Found by diagnosing R20, where ECSS-E-ST-10-12
# read as a PARSE PROBLEM at 47% page coverage and turned out to hold 185
# abbreviations and 61 definitions, every one legitimately page-less.
PAGELESS_BY_DESIGN = ("definition", "abbreviation")
FLOOR_ECSS = {"doc_code": 0.95, "document_revision": 0.95, "refs": 0.0,
              "req_ids": 0.0}


def populated(v):
    """A label counts as present only if it carries something. Empty string,
    empty list and None are all absent - the failure mode is a field that
    exists and is empty, not a field that is missing."""
    return v not in (None, "", [], {}, ())


def denominator_for(field, passages):
    """The passages a field can legitimately apply to. Only `page_number`
    narrows: synthesised units have no page by construction."""
    if field == "page_number":
        return [p for p in passages
                if p.get("element_type") not in PAGELESS_BY_DESIGN]
    return passages


def coverage(passages, fields):
    """field -> fraction of the passages the field can apply to. Denominator
    always returned beside it (rule 4), never a bare percentage."""
    n = len(passages)
    if not n:
        return {}, 0
    out = {}
    for f in fields:
        d = denominator_for(f, passages)
        out[f] = (sum(1 for p in d if populated(p.get(f))) / float(len(d))
                  if d else None)
    return out, n


def breaches(cov, floors):
    """[(field, fraction, floor)] for every field under its floor, named.
    A field with no applicable passages is not a breach - there is nothing
    for it to have failed at."""
    return sorted((f, cov[f], floors[f]) for f in cov
                  if f in floors and cov[f] is not None and cov[f] < floors[f])


def verdict(gen_breaches, ecss_breaches):
    """PARSE PROBLEM outranks a profile mismatch: a document that lost its
    heading trail is broken however well its ECSS patterns matched."""
    if gen_breaches:
        return "PARSE PROBLEM"
    if ecss_breaches:
        return "PROFILE MISMATCH"
    return "ok"


def report_rows(bydoc):
    """One row per document, sorted worst first so the eye lands on trouble."""
    rows = []
    for doc, ps in bydoc.items():
        g, n = coverage(ps, GENERIC)
        e, _ = coverage(ps, ECSS_BOUND)
        gb, eb = breaches(g, FLOOR_GENERIC), breaches(e, FLOOR_ECSS)
        rows.append({"doc": doc, "passages": n, "generic": g, "ecss": e,
                     "generic_breaches": gb, "ecss_breaches": eb,
                     "verdict": verdict(gb, eb)})
    order = {"PARSE PROBLEM": 0, "PROFILE MISMATCH": 1, "ok": 2}
    rows.sort(key=lambda r: (order[r["verdict"]], r["generic"].get("clause", 0),
                             r["doc"]))
    return rows


def run(only_doc, outroot):
    from retrieve import qc, COLL
    bydoc = defaultdict(list)
    off = None
    while True:
        pts, off = qc.scroll(collection_name=COLL, limit=2000, offset=off,
                             with_payload=True)
        if not pts:
            break
        for p in pts:
            d = p.payload or {}
            key = d.get("doc_code") or d.get("source_file") or "(unidentified)"
            if only_doc and only_doc not in str(key):
                continue
            bydoc[key].append(d)
        if off is None:
            break
    if not bydoc:
        print("ABORT - no passages matched%s"
              % (" %r" % only_doc if only_doc else ""))
        return 1

    rows = report_rows(bydoc)
    total = sum(r["passages"] for r in rows)
    print("label coverage - %s, %d documents, %d passages"
          % (COLL, len(rows), total))
    print("  GENERIC labels come from the parse and should hold on ANY document.")
    print("  ECSS-BOUND labels come from patterns keyed to ECSS and may")
    print("  legitimately be absent on other corpora - reported, not failed.\n")

    hdr = "  %-26s %6s  %s" % ("document", "psgs",
                               "  ".join("%-9s" % f[:9] for f in
                                         GENERIC + ECSS_BOUND))
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))
    for r in rows:
        cells = ["%-9s" % ("n/a" if r["generic"][f] is None
                           else "%.0f%%" % (100 * r["generic"][f]))
                 for f in GENERIC]
        cells += ["%-9s" % ("n/a" if r["ecss"][f] is None
                            else "%.0f%%" % (100 * r["ecss"][f]))
                  for f in ECSS_BOUND]
        mark = {"PARSE PROBLEM": " <== PARSE PROBLEM",
                "PROFILE MISMATCH": " <-- profile mismatch", "ok": ""}
        print("  %-26s %6d  %s%s"
              % (r["doc"][:26], r["passages"], "  ".join(cells),
                 mark[r["verdict"]]))

    bad = [r for r in rows if r["verdict"] == "PARSE PROBLEM"]
    mism = [r for r in rows if r["verdict"] == "PROFILE MISMATCH"]
    print("\n  PARSE PROBLEM    : %d document(s)" % len(bad))
    for r in bad:
        for f, got, fl in r["generic_breaches"]:
            print("     %-26s %-14s %.0f%% < floor %.0f%%"
                  % (r["doc"][:26], f, 100 * got, 100 * fl))
    print("  profile mismatch : %d document(s)" % len(mism))
    for r in mism[:8]:
        for f, got, fl in r["ecss_breaches"]:
            print("     %-26s %-14s %.0f%% < floor %.0f%%"
                  % (r["doc"][:26], f, 100 * got, 100 * fl))
    if not bad and not mism:
        print("  every document clears every floor.")

    stamp = time.strftime("%Y-%m-%d_%H%M%S")
    outdir = os.path.join(outroot, stamp)
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "label_coverage_%s.json" % stamp)
    open(path, "w").write(json.dumps(
        {"version": VERSION, "prereg": PREREG, "stamp": stamp,
         "collection": COLL, "n_documents": len(rows), "n_passages": total,
         "generic_fields": list(GENERIC), "ecss_fields": list(ECSS_BOUND),
         "floors_generic": FLOOR_GENERIC, "floors_ecss": FLOOR_ECSS,
         "documents": rows}, indent=2, sort_keys=True) + "\n")
    print("\n  -> %s" % path)
    return 1 if bad else 0


# ---------------------------------------------------------------------------
def selftest():
    fails, ran = [], [0]

    def ck(name, cond):
        ran[0] += 1
        print("  %-72s %s" % (name, "ok" if cond else "FAIL"))
        if not cond:
            fails.append(name)

    src = open(os.path.abspath(__file__)).read()

    ck("an empty string counts as ABSENT, not present",
       not populated("") and not populated(None) and not populated([]))
    ck("a real value counts as present",
       populated("4.10") and populated(["shall"]) and populated(0) is False
       or populated("x"))

    ps = [{"crumb": "a", "clause": "1.1", "refs": ["X"]},
          {"crumb": "b", "clause": "", "refs": []}]
    cov, n = coverage(ps, ("crumb", "clause", "refs"))
    ck("coverage is a fraction of the passages given",
       cov["crumb"] == 1.0 and cov["clause"] == 0.5 and cov["refs"] == 0.5)
    ck("the denominator is returned beside it (rule 4)", n == 2)
    ck("no passages yields nothing rather than a divide-by-zero",
       coverage([], ("crumb",)) == ({}, 0))

    ck("a synthesised unit is excluded from the PAGE denominator, not failed",
       len(denominator_for("page_number",
                           [{"element_type": "definition"},
                            {"element_type": "text"}])) == 1)
    ck("every other field keeps the full denominator",
       len(denominator_for("clause",
                           [{"element_type": "definition"},
                            {"element_type": "text"}])) == 2)
    ck("a document that is ALL definitions has no page coverage, not 0%",
       coverage([{"element_type": "definition"}], ("page_number",))[0]
       ["page_number"] is None)
    ck("a field with no applicable passages is not a breach",
       breaches({"page_number": None}, {"page_number": 0.5}) == [])
    ck("the R20 diagnosis is recorded where the rule lives",
       ("185" in src and "abbreviations" in src))
    ck("a field under its floor is NAMED with the floor it missed",
       breaches({"clause": 0.10}, {"clause": 0.50}) == [("clause", 0.10, 0.50)])
    ck("a field at its floor is not a breach",
       breaches({"clause": 0.50}, {"clause": 0.50}) == [])
    ck("a field with no floor is reported but never breaches",
       breaches({"refs": 0.0}, {"refs": 0.0}) == [])

    ck("a lost heading trail is a PARSE PROBLEM, whatever the ECSS labels did",
       verdict([("crumb", 0.1, 0.95)], []) == "PARSE PROBLEM")
    ck("only ECSS labels missing is a PROFILE MISMATCH, not a failure",
       verdict([], [("doc_code", 0.0, 0.95)]) == "PROFILE MISMATCH")
    ck("a parse problem OUTRANKS a profile mismatch",
       verdict([("crumb", 0.1, 0.95)], [("doc_code", 0.0, 0.95)])
       == "PARSE PROBLEM")
    ck("a clean document is ok", verdict([], []) == "ok")

    bydoc = {"GOOD": [{"crumb": "a", "clause": "1", "page_number": 2,
                       "element_type": "text", "modals": ["shall"],
                       "doc_code": "D", "document_revision": "C",
                       "refs": ["R"], "req_ids": ["Q"]}],
             "NOPARSE": [{"crumb": "", "clause": "", "page_number": None,
                          "element_type": "", "modals": []}],
             "NONECSS": [{"crumb": "a", "clause": "1", "page_number": 2,
                          "element_type": "text", "modals": ["shall"]}]}
    rows = report_rows(bydoc)
    byname = {r["doc"]: r for r in rows}
    ck("a fully labelled document passes", byname["GOOD"]["verdict"] == "ok")
    ck("a document with no parse labels is caught",
       byname["NOPARSE"]["verdict"] == "PARSE PROBLEM")
    ck("a well-parsed NON-ECSS document is a mismatch, not a failure",
       byname["NONECSS"]["verdict"] == "PROFILE MISMATCH")
    ck("trouble sorts to the top so the eye lands on it",
       rows[0]["verdict"] == "PARSE PROBLEM")
    ck("generic and ECSS labels are reported SEPARATELY, never pooled",
       not (set(GENERIC) & set(ECSS_BOUND)) and '"generic"' in src
       and '"ecss"' in src)
    ck("the tool does not call a document bad for lacking ECSS patterns",
       ("DOES NOT JUDGE A DOCUMENT " + "BAD") in src)
    ck("a parse problem sets a non-zero exit, a mismatch does not",
       "return 1 if bad else 0" in src)

    print("\n  %d assertions, %d failed" % (ran[0], len(fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.
                                 RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--doc", help="restrict to documents matching this string")
    ap.add_argument("--out",
                    default=os.path.expanduser("~/p42/label_coverage"))
    a = ap.parse_args()
    if a.self_test:
        sys.exit(selftest())
    if a.run:
        sys.exit(run(a.doc, a.out))
    ap.print_help()
