#!/usr/bin/env python3
"""
ask.py  v2.0  (2026-08-12)  --  Project 42 interactive query CLI, Campaign 2

  question -> retrieve.py (routed) -> rerank (:8081, optional)
           -> de-duplicate -> answer LLM (:8000) -> cited answer + sources

RUN:  source ~/p42/ingest-venv/bin/activate
      python ask.py "which verification methods apply to Category B software"

WHAT CHANGED FROM v1, AND WHY. Every item is a measured campaign-1 defect or a
gate-4 / gate-8 finding, not a preference.

  COLLECTION  p42_text_v3 (88 documents, 22134 chunks) instead of p42_text
              resolved via retrieve.py - ask_v2 defines no collection of
              its own, which is why repointing retrieve.py repoints this
      (23 documents). The old collection is untouched and still queryable.

  RETRIEVAL   delegated entirely to retrieve.py, which ROUTES by query type:
      identifier queries to the metadata filter (measured 100%), definitional
      queries to dense-dominant fusion with a definition boost (98% top-3,
      75% rank-1, up from 42%), everything else to dense-dominant fusion.
      ask.py, the harness and the Open WebUI Function must all import the SAME
      module - in campaign 1 they held three separate copies of the retrieval
      config and drifted apart.

  DEFAULTS    TOP_K 50, CONTEXT_K 10. Both were ADOPTED levers in campaign 1:
      top_k 20->50 lifted evidence recall 0.722 -> 0.889 (significant), and
      context_k 5->10 lifted graded correctness +0.079, CI [+0.020, +0.151].

  DE-DUPLICATION  24 of 76 campaign-1 questions wasted context slots on a
      repeated (document, clause) pair - 31 slots, one question burned 3 of
      its 5. Context is de-duplicated before the cut, so CONTEXT_K buys width
      rather than repeats.

  RERANK BATCHING  the TEI reranker accepts at most 32 texts per call. At
      TOP_K 50 an unbatched call fails SILENTLY on every request - campaign 1
      lost a whole experiment to this before --compare caught it. Batched, and
      a failure is REPORTED rather than swallowed.

  AUTHORITY   every chunk carries authority / source_class (ingest v3.1). A
      handbook advises, a standard imposes. The prompt now requires the answer
      to say so, and the source list prints it, so a reader can never mistake
      informative content for a requirement.

  CITATIONS   [document code | clause] from the payload, not the filename and
      heading. Campaign 1 defect D1: the prompt showed "[doc | section]" as a
      literal template and Qwen3 copied it verbatim - 15 fabricated citations.
      The prompt now describes the form and shows a REAL example.
"""

import os
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from retrieve import retrieve                                  # noqa: E402

TOP_K, CONTEXT_K = 50, 10
RERANK_BATCH = 32                    # TEI's hard limit; exceeded = silent fail
ANSWER = "http://localhost:8000"
RERANK = "http://localhost:8081"
# Same env var and same default as claim_extract.LLM_MODEL, so the pipeline and
# the scorer cannot drift onto different models without one of them saying so.
ANSWER_MODEL = os.environ.get("P42_LLM_MODEL", "nvidia/Qwen3-32B-NVFP4")

REFUSAL = "The corpus does not contain this information."

SYSTEM_PROMPT = (
    "You answer questions about ECSS space-engineering standards using ONLY "
    "the provided context passages.\n\n"
    "CITATIONS. Every factual claim must carry a citation in square brackets "
    "containing the document code, a vertical bar, and the clause number, "
    "taken from the SOURCE line of the passage you used. For example a claim "
    "drawn from clause 5.2.2 of ECSS-E-ST-40 is cited as "
    "[ECSS-E-ST-40 | 5.2.2]. Never invent a document code or a clause number, "
    "and never cite a passage that is not in the context above.\n\n"
    "AUTHORITY. Each passage states its authority. A passage marked "
    "'normative' comes from a standard and imposes a requirement. A passage "
    "marked 'informative' comes from a handbook or technical memorandum and "
    "only advises - it never imposes anything. If your answer rests on an "
    "informative passage, say so explicitly and do not phrase it as a "
    "requirement.\n\n"
    "MODAL VERBS. ECSS defines these normatively: 'shall' is a requirement, "
    "'should' is a recommendation, 'may' is a permission, 'can' is a "
    "statement of possibility. Preserve the modal verb the source uses. Do "
    "not upgrade 'should' to 'shall'.\n\n"
    "WHEN THE ANSWER IS NOT THERE. If the context does not contain the "
    "answer, your ENTIRE reply must be this one sentence, with no preamble, "
    "no explanation before it and nothing after it:\n"
    + REFUSAL + "\n"
    "Do not write 'the information provided does not specify...' and then add "
    "the sentence. Do not restate the question. The reply is that sentence "
    "alone. (Measured in campaign 1: soft refusals of exactly that shape were "
    "scored as answers by the grader and corrupted the refusal metric.)\n"
    "If the context answers PART of the question, do not refuse: answer that "
    "part, cite it, and state plainly which part is not covered and which "
    "document would govern it.\n\n"
    "Do not guess and do not use knowledge from outside the context."
)


def rerank(query, chunks):
    """Cross-encoder rerank in batches of RERANK_BATCH. Returns (chunks, note)."""
    if not chunks:
        return chunks, "no chunks"
    scored, failed = [], 0
    for i in range(0, len(chunks), RERANK_BATCH):
        batch = chunks[i:i + RERANK_BATCH]
        try:
            r = requests.post(RERANK + "/rerank", timeout=60,
                              json={"query": query,
                                    "texts": [c["text"] for c in batch]})
            for d in r.json():
                scored.append((d["score"], batch[d["index"]]))
        except Exception:
            failed += 1
            scored.extend((0.0, c) for c in batch)
    if failed:
        return chunks, "RERANKER FAILED on %d of %d batches - order is " \
                       "retrieval order" % (failed,
                                            (len(chunks) + RERANK_BATCH - 1)
                                            // RERANK_BATCH)
    scored.sort(key=lambda x: -x[0])
    return [c for _s, c in scored], "reranked %d" % len(scored)


def render_context(ctx):
    """The context block exactly as the model sees it. Extracted so a
    measurement can build the same block, never a lookalike."""
    return "\n\n---\n\n".join(
        "SOURCE: [%s | %s]  authority: %s (%s)  section: %s\n%s"
        % (c["doc"], c["clause"] or "(no clause)", c["authority"],
           c["sclass"], c["crumb"], c["text"]) for c in ctx)


def build_messages(q, ctx, system=None, user=None):
    """The messages exactly as the pipeline sends them.

    Pure, so the prompt can be asserted without a server - the open-book path
    had no test of its prompt at all before this.

    `system` and `user` exist for ONE caller: the closed-book control's
    parametric arm, which must ask without a grounding instruction and without
    a context block (action plan §A1). That arm is deliberately NOT this
    pipeline and labels itself so. Every other caller leaves both None and gets
    the pipeline's own prompt.
    """
    return [{"role": "system",
             "content": SYSTEM_PROMPT if system is None else system},
            {"role": "user",
             "content": ("Context passages:\n\n" + render_context(ctx)
                         + "\n\nQuestion: " + q) if user is None else user}]


def generate(q, ctx, model_id, system=None, user=None):
    """The generation half of the pipeline: prompt, settings, POST, raw JSON.

    EXTRACTED WITH NO BEHAVIOUR CHANGE, for the same reason `answer()` was
    extracted from `main()` - so a measurement calls THE PIPELINE rather than a
    copy of it. On the open-book path this sends byte-identical messages to the
    inline version it replaces.

    Settings are inherited here and re-chosen nowhere (rule 60).
    """
    body = {"model": model_id, "temperature": 0.0, "max_tokens": 1536,
            "chat_template_kwargs": {"enable_thinking": False},
            "messages": build_messages(q, ctx, system, user)}
    return requests.post(ANSWER + "/v1/chat/completions", json=body,
                         timeout=600).json()


def answer(q):
    """Run the pipeline for one question. Returns a record, prints nothing.

    Extracted from main() with no behaviour change so that a measurement can
    call THE PIPELINE rather than a copy of it. main() below now calls this and
    only formats what it returns: a second implementation for measurement would
    be a different pipeline wearing the same name, and any drift between them
    would show up as a finding about the corpus.
    """
    hits, route = retrieve(q, k=TOP_K)
    if not hits:
        return {"question": q, "answer": "", "route": route, "rerank": "",
                "n_context": 0, "n_retrieved": 0, "sources": [],
                "refused": False, "error": "no passages retrieved"}
    # `_id` and `_score` are carried through so a measurement can compute
    # Recall@k / MRR / nDCG from the record instead of re-running retrieval.
    # The adopted items' anchor spans carry `point_id` and a `role` grading,
    # which makes them qrels; without the id here they could not be joined.
    # ADDITIVE ONLY - nothing below reads these, so retrieval, reranking,
    # de-duplication, the prompt and the answer are unchanged.
    chunks = [{"_id": str(h.id), "_score": float(getattr(h, "score", 0.0) or 0.0),
               "text": h.payload.get("text", ""),
               "doc": h.payload.get("doc_code") or h.payload.get("source_file", ""),
               "rev": h.payload.get("document_revision", ""),
               "clause": h.payload.get("clause", ""),
               "crumb": h.payload.get("crumb", ""),
               "etype": h.payload.get("element_type", ""),
               "authority": h.payload.get("authority", "normative"),
               "sclass": h.payload.get("source_class", "standard"),
               "page": h.payload.get("page_number", "")} for h in hits]

    chunks, rnote = rerank(q, chunks)

    seen, ctx = set(), []                       # de-duplicate before the cut
    for c in chunks:
        key = (c["doc"], c["clause"], c["crumb"])
        if key in seen:
            continue
        seen.add(key)
        ctx.append(c)
        if len(ctx) == CONTEXT_K:
            break

    # The model is DISCOVERED and never defaulted. v2.0 took data[0].id with no
    # check and, on any failure of /v1/models, fell back to the literal string
    # "default" - which it then SENT as the model and RECORDED as the model. A
    # run could therefore complete with provenance naming nothing, and with one
    # model served the silence looked like success. Rule 70: name the mismatch,
    # do not guess past it. On the happy path this resolves to exactly what
    # data[0].id resolved to, so no answered question changes.
    err = None
    try:
        served = [m.get("id") for m in
                  (requests.get(ANSWER + "/v1/models", timeout=10)
                   .json().get("data") or [])]
    except Exception as e:
        served, err = [], ("%s/v1/models did not answer: %s. The answer LLM "
                           "is not up: sudo /opt/p42/bin/kb-mode-serve.sh"
                           % (ANSWER, str(e)[:120]))
    if not err and not served:
        err = "%s/v1/models lists no models" % ANSWER
    if not err and ANSWER_MODEL not in served:
        err = ("configured model %r is not served; served: %s. Set P42_LLM_MODEL "
               "or fix the server - a measurement does not choose its own model."
               % (ANSWER_MODEL, ", ".join(served) or "(none)"))
    if err:
        return {"question": q, "answer": "", "route": route, "rerank": rnote,
                "n_context": len(ctx), "n_retrieved": len(chunks),
                "sources": [], "refused": False, "model": None,
                "error": "model discovery: " + err}
    model_id = ANSWER_MODEL

    data = generate(q, ctx, model_id)
    if "choices" not in data:
        return {"question": q, "answer": "", "route": route, "rerank": rnote,
                "n_context": len(ctx), "n_retrieved": len(chunks),
                "sources": [], "refused": False,
                "error": "LLM: %s" % str(data)[:300]}
    ans = data["choices"][0]["message"]["content"]
    if "</think>" in ans:
        ans = ans.split("</think>", 1)[1].lstrip()
    return {"question": q, "answer": ans, "route": route, "rerank": rnote,
            "n_context": len(ctx), "n_retrieved": len(chunks),
            "model": model_id,
            "sources": [{"doc": c["doc"], "clause": c["clause"],
                         "authority": c["authority"], "etype": c["etype"],
                         "point_id": c.get("_id"), "page": c.get("page"),
                         "rev": c.get("rev")}
                        for c in ctx],
            # THE FULL RANKED LIST, post-rerank, before de-duplication and the
            # CONTEXT_K cut. Recall@20 and nDCG need the ranking the context
            # was cut from; storing only the surviving 10 makes every rank-
            # sensitive statistic uncomputable from the record.
            "ranked": [{"point_id": c.get("_id"), "doc": c["doc"],
                        "clause": c["clause"], "page": c.get("page"),
                        "rev": c.get("rev"), "score": c.get("_score")}
                       for c in chunks],
            "non_normative": sum(1 for c in ctx
                                 if c["authority"] != "normative"),
            "refused": ans.strip().startswith(REFUSAL), "error": None}


def main():
    if len(sys.argv) < 2:
        print('usage: python ask.py "your question"')
        return 2
    q = " ".join(sys.argv[1:])
    r = answer(q)
    if r["error"]:
        print("\n" + r["error"])
        return 1

    print("\n" + r["answer"])
    print("\n" + "-" * 72)
    print("retrieval route : %s   |   %s   |   %d of %d passages used"
          % (r["route"], r["rerank"], r["n_context"], r["n_retrieved"]))
    if r["non_normative"]:
        print("NOTE: %d of the passages are NOT normative - the answer "
              "must say so where it relies on them." % r["non_normative"])
    print("SOURCES handed to the model:")
    for i, c in enumerate(r["sources"], 1):
        print("  [%2d] %-22s %-10s %-12s %-11s"
              % (i, c["doc"], c["clause"] or "-", c["etype"], c["authority"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
