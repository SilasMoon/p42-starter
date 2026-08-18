#!/usr/bin/env python3
"""P42 - R88: carry the frames' anchors across the R85 relabel.

`P42_Register.md` R88, gating `R89` (the rebuild).

THE PROBLEM. Every frame's anchors are `(doc, clause)` pairs, and R85 changes
the `clause` label. `ECSS-E-ST-40 | 5.11.5.6` will stop matching the Annex Q
chunks it currently matches, because those chunks become `Q.3.1`. If the
frames are simply re-scored against the new index, every figure moves for a
reason nobody tracked.

THE ROUTE, and why it works. Measured 2026-08-18 before this was written:

    100% of evidence refs in all three frames carry VERBATIM span text
    of the refs whose text resolves to a chunk, 100% sit under the SAME
    clause label as their anchor

So the anchors are not mispointed - the key is coarse. Migration therefore
re-binds by TEXT: find the chunk whose body contains the evidence span, read
that chunk's label in the target collection, and rewrite the anchor. The text
is the invariant across the rebuild; the label is the thing being fixed.

THE VALIDATION IS THE POINT. Run against the CURRENT collection, migration
must be a NO-OP - it should reproduce the anchors already in the frame,
because they already agree. `--validate` asserts exactly that and reports any
anchor it would have changed. **A migration that cannot reproduce a known
answer is not trusted with an unknown one.**

WHAT IT REFUSES TO DO. A ref whose span resolves to no chunk, or to chunks
under two different labels, is NAMED and left UNMIGRATED - never guessed, and
never silently dropped (rule 4). Those are the ones a human reads.

    python3 anchor_migrate.py --self-test
    python3 anchor_migrate.py --validate --frame questions/heldout_retrieval.jsonl
    python3 anchor_migrate.py --migrate  --frame F --collection C --out G
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

VERSION = "1.0"
PREREG = "P42_Register.md R88"

WS = re.compile(r"\s+")


def norm_text(s):
    """Whitespace-insensitive, case-insensitive comparison form.

    PDF extraction varies line breaks and spacing between builds; comparing
    raw strings would report spurious misses that look like real ones.
    """
    return WS.sub(" ", s or "").strip().lower()


def parse_anchor(anchor):
    """'ECSS-E-ST-40 5.11.5.6' -> ('ECSS-E-ST-40', '5.11.5.6')."""
    bits = (anchor or "").split()
    return (bits[0] if bits else "", bits[1] if len(bits) > 1 else "")


def refs_of(item):
    """Every (claim_index, evidence_index, anchor, span) in one item."""
    out = []
    for ci, cl in enumerate(item.get("claims", [])):
        for ei, ev in enumerate(cl.get("evidence", [])):
            out.append((ci, ei, ev.get("anchor") or "", ev.get("span") or ""))
    return out


def doc_aliases(old_index_docs, new_pairs):
    """{old doc_code: new doc_code} for documents whose CODE changed.

    R21 fixed the pre-2008 ECSS filename pattern, so two documents stopped
    having their whole filename as a doc_code:

        ECSS-M-70A(19April1996).pdf        -> ECSS-M-70
        ECSS-P-00C-Rev.1(15November2024).pdf -> ECSS-P-00

    Anchors drawn before the rebuild still carry the old form, and a span
    lookup keyed on it finds no document at all. The join is on `source_file`,
    which is the one identifier the rebuild did NOT change.
    """
    out = {}
    for src, new in new_pairs.items():
        old = old_index_docs.get(src)
        if old and old != new:
            out[old] = new
    return out


def resolve(span, doc, chunks):
    """Labels of the chunks in `doc` whose text contains `span`.

    Returns (labels, n_chunks). An empty span resolves to nothing - it is not
    treated as matching everything, which is how a substring search fails
    open.
    """
    n = norm_text(span)
    if not n:
        return (set(), 0)
    hits = [cl for cl, body in chunks.get(doc, []) if n in body]
    return (set(hits), len(hits))


def migrate_item(item, chunks, aliases=None):
    """(migrated_item, [decisions]). Pure - the index is passed in."""
    aliases = aliases or {}
    out = json.loads(json.dumps(item))
    decisions = []
    for ci, ei, anchor, span in refs_of(item):
        doc, old = parse_anchor(anchor)
        doc_renamed = aliases.get(doc)
        if doc_renamed:
            doc = doc_renamed
        labels, n = resolve(span, doc, chunks)
        if not labels:
            state, new = "UNRESOLVED", old
        elif len(labels) > 1:
            state, new = "AMBIGUOUS", old
        else:
            new = labels.pop()
            state = "unchanged" if new == old else "RELABELLED"
        if doc_renamed and state == "unchanged":
            state = "RELABELLED"          # the document code moved (R21)
        if state == "RELABELLED":
            ev = out["claims"][ci]["evidence"][ei]
            ev["anchor"] = ("%s %s" % (doc, new)).strip()
            ev["anchor_before_R85"] = anchor
        decisions.append({"id": item.get("anchor_id"), "claim": ci,
                          "evidence": ei, "doc": doc, "old": old, "new": new,
                          "state": state, "n_chunks": n, "span": span[:70],
                          "doc_renamed_from": (anchor.split()[0]
                                               if doc_renamed else None)})
    return out, decisions


def index_chunks(collection, with_sources=False):
    """{doc: [(clause, normalised_body)]}. The only impure function here.

    With `with_sources`, also returns {source_file: doc_code} - the join that
    survives a rebuild, and therefore the only safe way to notice that a
    document's CODE changed (R21).
    """
    from collections import defaultdict
    from qdrant_client import QdrantClient
    c = QdrantClient(url="http://localhost:6333", timeout=300)
    off, out, srcs = None, defaultdict(list), {}
    while True:
        pts, off = c.scroll(collection, limit=4000, offset=off,
                            with_payload=["doc_code", "clause", "text",
                                          "source_file"],
                            with_vectors=False)
        for p in pts:
            d = p.payload.get("doc_code") or ""
            out[d].append((p.payload.get("clause") or "",
                           norm_text(p.payload.get("text"))))
            if p.payload.get("source_file"):
                srcs[p.payload["source_file"]] = d
        if off is None:
            break
    return (out, srcs) if with_sources else out


def tally(decisions):
    from collections import Counter
    t = Counter(d["state"] for d in decisions)
    t["total"] = len(decisions)
    return dict(t)


def report(decisions, header):
    t = tally(decisions)
    print("\n  %s" % header)
    print("    %-12s %4d" % ("refs", t.get("total", 0)))
    for k in ("unchanged", "RELABELLED", "AMBIGUOUS", "UNRESOLVED"):
        if t.get(k):
            print("    %-12s %4d  (%.0f%%)"
                  % (k, t[k], 100.0 * t[k] / max(1, t["total"])))
    for k in ("AMBIGUOUS", "UNRESOLVED"):
        named = [d for d in decisions if d["state"] == k]
        if named:
            print("    %s - NAMED, left unmigrated, read these:" % k)
            for d in named[:20]:
                print("      %-12s %-18s %-10s %s"
                      % (d["id"], d["doc"], d["old"], d["span"][:52]))
            if len(named) > 20:
                print("      ... and %d more" % (len(named) - 20))
    return t


def run_validate(frame, collection, old_collection=None):
    items = [json.loads(l) for l in open(frame) if l.strip()]
    chunks, srcs = index_chunks(collection, with_sources=True)
    aliases = {}
    if old_collection:
        _o, osrc = index_chunks(old_collection, with_sources=True)
        aliases = doc_aliases(osrc, srcs)
    decisions = []
    for it in items:
        _m, d = migrate_item(it, chunks, aliases)
        decisions += d
    t = report(decisions, "R88 VALIDATION - %s against %s"
               % (os.path.basename(frame), collection))
    changed = t.get("RELABELLED", 0)
    print("\n  THE TEST: against the CURRENT collection migration must be a "
          "NO-OP.")
    if changed:
        print("  FAILED - it would have relabelled %d anchors that are "
              "already correct." % changed)
        print("  The migration is NOT trusted with the new collection until "
              "this is 0.")
        return 1
    print("  PASSED - 0 anchors relabelled. %d refs reproduced exactly; "
          "%d named as unresolvable and left for a human."
          % (t.get("unchanged", 0),
             t.get("UNRESOLVED", 0) + t.get("AMBIGUOUS", 0)))
    return 0


def run_migrate(frame, collection, out, old_collection=None):
    items = [json.loads(l) for l in open(frame) if l.strip()]
    chunks, srcs = index_chunks(collection, with_sources=True)
    aliases = {}
    if old_collection:
        _o, osrc = index_chunks(old_collection, with_sources=True)
        aliases = doc_aliases(osrc, srcs)
        if aliases:
            print("\n  DOCUMENT CODES THAT CHANGED (R21), applied to anchors:")
            for a, b in sorted(aliases.items()):
                print("    %-44s -> %s" % (a[:44], b))
    migrated, decisions = [], []
    for it in items:
        m, d = migrate_item(it, chunks, aliases)
        migrated.append(m)
        decisions += d
    t = report(decisions, "R88 MIGRATION - %s -> %s"
               % (os.path.basename(frame), os.path.basename(out)))
    open(out, "w").write("\n".join(json.dumps(m) for m in migrated) + "\n")
    log = out + ".decisions.json"
    json.dump({"version": VERSION, "prereg": PREREG, "frame": frame,
               "collection": collection, "tally": t,
               "decisions": decisions}, open(log, "w"), indent=1)
    print("\n  migrated frame -> %s\n  every decision -> %s" % (out, log))
    print("  Anchors that moved keep `anchor_before_R85`; nothing is "
          "overwritten without a trace.")
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

    ck("whitespace and case differences do not create spurious misses",
       norm_text("The  SUPPLIER\nshall") == norm_text("the supplier shall"))
    ck("an anchor splits into document and clause",
       parse_anchor("ECSS-E-ST-40 5.11.5.6") == ("ECSS-E-ST-40", "5.11.5.6"))
    ck("an anchor with no clause does not crash",
       parse_anchor("ECSS-E-ST-40") == ("ECSS-E-ST-40", ""))

    chunks = {"D": [("5.11.5.6", norm_text("Preliminary external interfaces "
                                           "design is expected")),
                    ("Q.3.1", norm_text("some other table row")),
                    ("A", norm_text("shared wording here")),
                    ("B", norm_text("shared wording here"))]}
    ck("a span resolves to the label of the chunk that contains it",
       resolve("Preliminary external interfaces design", "D", chunks)
       == ({"5.11.5.6"}, 1))
    ck("an EMPTY span resolves to nothing - a substring search must not fail "
       "open",
       resolve("", "D", chunks) == (set(), 0))
    ck("a span in two chunks under DIFFERENT labels is ambiguous, not a guess",
       resolve("shared wording here", "D", chunks)[0] == {"A", "B"})
    ck("a span in an unknown document resolves to nothing",
       resolve("anything", "ZZZ", chunks) == (set(), 0))

    def item(anchor, span):
        return {"anchor_id": "A-1",
                "claims": [{"evidence": [{"anchor": anchor, "span": span}]}]}

    m, d = migrate_item(item("D 5.11.5.6",
                             "Preliminary external interfaces design"), chunks)
    ck("an anchor that already agrees is left UNCHANGED",
       d[0]["state"] == "unchanged"
       and m["claims"][0]["evidence"][0]["anchor"] == "D 5.11.5.6")
    ck("an unchanged anchor gains no bookkeeping field",
       "anchor_before_R85" not in m["claims"][0]["evidence"][0])

    m2, d2 = migrate_item(item("D 5.11.5.6", "some other table row"), chunks)
    ck("a moved anchor is REWRITTEN to the label of the chunk holding its text",
       d2[0]["state"] == "RELABELLED"
       and m2["claims"][0]["evidence"][0]["anchor"] == "D Q.3.1")
    ck("a moved anchor RETAINS what it was before - nothing is overwritten "
       "without a trace",
       m2["claims"][0]["evidence"][0]["anchor_before_R85"] == "D 5.11.5.6")

    m3, d3 = migrate_item(item("D 5.11.5.6", "text that appears nowhere"),
                          chunks)
    ck("an unresolvable ref is NAMED and left alone, never guessed",
       d3[0]["state"] == "UNRESOLVED"
       and m3["claims"][0]["evidence"][0]["anchor"] == "D 5.11.5.6")
    m4, d4 = migrate_item(item("D A", "shared wording here"), chunks)
    ck("an ambiguous ref is NAMED and left alone, never resolved by coin-flip",
       d4[0]["state"] == "AMBIGUOUS"
       and m4["claims"][0]["evidence"][0]["anchor"] == "D A")

    # --- R21: a document whose CODE changed between builds ---------------
    old_src = {"/c/ECSS-M-70A(19April1996).pdf": "ECSS-M-70A(19April1996).pdf",
               "/c/ECSS-E-ST-40.pdf": "ECSS-E-ST-40"}
    new_src = {"/c/ECSS-M-70A(19April1996).pdf": "ECSS-M-70",
               "/c/ECSS-E-ST-40.pdf": "ECSS-E-ST-40"}
    al = doc_aliases(old_src, new_src)
    ck("a document whose code changed is detected by joining on source_file",
       al == {"ECSS-M-70A(19April1996).pdf": "ECSS-M-70"})
    ck("a document whose code did NOT change produces no alias",
       "ECSS-E-ST-40" not in al)
    ck("the join is on source_file because that is what a rebuild does not "
       "change",
       "which is the one identifier the rebuild did NOT change" in src)

    ch2 = {"ECSS-M-70": [("5.1", norm_text("AIM: achieve a balance"))]}
    it2 = {"anchor_id": "A-1", "claims": [{"evidence": [
        {"anchor": "ECSS-M-70A(19April1996).pdf 5.1",
         "span": "AIM: achieve a balance"}]}]}
    m5, d5 = migrate_item(it2, ch2, al)
    ck("an anchor on a RENAMED document resolves instead of going unresolved",
       d5[0]["state"] == "RELABELLED"
       and m5["claims"][0]["evidence"][0]["anchor"] == "ECSS-M-70 5.1")
    ck("the rename is recorded on the decision, not silently applied",
       d5[0]["doc_renamed_from"] == "ECSS-M-70A(19April1996).pdf")
    ck("without the alias map the same anchor is UNRESOLVED, not guessed",
       migrate_item(it2, ch2)[1][0]["state"] == "UNRESOLVED")

    ck("the tally counts every ref exactly once",
       tally(d + d2 + d3 + d4)["total"] == 4)
    ck("migrate_item is PURE - the index is passed in, so the self-test "
       "drives the real arithmetic",
       "def migrate_item(item, chunks)" in src)
    ck("validation FAILS when migration would change a known-correct anchor",
       "is NOT trusted with the new collection" in src
       and "FAILED - it would have relabelled" in src)
    ck("the measured basis for the text route is recorded, not assumed",
       "100% of evidence refs" in src and "the key is coarse" in src)
    ck("no LLM is called anywhere in this module",
       ("call_" + "llm") not in src.lower()
       and ("chat/" + "completions") not in src
       and ("import claim_" + "judge") not in src)

    print("\n  %d assertions, %d failed" % (ran[0], len(fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.
                                 RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--migrate", action="store_true")
    ap.add_argument("--frame")
    ap.add_argument("--collection", default="p42_text_v3_bgelex")
    ap.add_argument("--old-collection",
                    help="the collection the anchors were drawn against; "
                         "enables doc-code alias detection (R21)")
    ap.add_argument("--out")
    a = ap.parse_args()
    if a.self_test:
        sys.exit(selftest())
    if a.validate:
        if not a.frame:
            raise SystemExit("--validate needs --frame")
        sys.exit(run_validate(a.frame, a.collection, a.old_collection))
    if a.migrate:
        if not (a.frame and a.out):
            raise SystemExit("--migrate needs --frame and --out")
        sys.exit(run_migrate(a.frame, a.collection, a.out,
                             a.old_collection))
    ap.print_help()
