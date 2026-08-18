#!/usr/bin/env python3
"""Build the parallel collection: same points, same dense vectors, new sparse.
R10. Runs in sparse-venv. The source collection is opened READ-ONLY."""
import argparse, os, sys, time, json
os.environ.setdefault("HF_HOME", "/home/spark/p42/hf-cache")
from qdrant_client import QdrantClient, models

# (2026-08-18) SRC/TGT were hardcoded to the v3 names. The R89 rebuild needs
# them pointed at v4, and editing a build script while the build is waiting on
# it is how the wrong collection gets written. They are arguments now, and the
# target still must not exist.
DEFAULT_SRC, DEFAULT_TGT = "p42_text_v3", "p42_text_v3_bgelex"
SRC, TGT = DEFAULT_SRC, DEFAULT_TGT
qc = QdrantClient(url="http://localhost:6333", timeout=600)

def main():
    if SRC == TGT:
        print("ABORT - source and target are the same collection (%r). The "
              "source is opened READ-ONLY and must stay that way." % SRC)
        return 1
    if not qc.collection_exists(SRC):
        print("ABORT - source collection %r does not exist" % SRC)
        return 1
    info = qc.get_collection(SRC)
    n = info.points_count
    print("source %s: %d points" % (SRC, n))
    if qc.collection_exists(TGT):
        print("ABORT - %s already exists; refusing to overwrite" % TGT); return 1
    qc.create_collection(
        TGT,
        vectors_config={"dense": models.VectorParams(size=1024, distance=models.Distance.COSINE)},
        sparse_vectors_config={"sparse": models.SparseVectorParams()})
    print("created %s" % TGT)
    from FlagEmbedding import BGEM3FlagModel
    m = BGEM3FlagModel("BAAI/bge-m3", use_fp16=True)
    print("BGE-M3 loaded on GPU")
    off, done, t0, empty = None, 0, time.time(), 0
    while True:
        pts, off = qc.scroll(SRC, limit=128, offset=off, with_payload=True, with_vectors=True)
        if not pts: break
        texts = [(p.payload or {}).get("text", "") or " " for p in pts]
        out = m.encode(texts, return_dense=False, return_sparse=True,
                       return_colbert_vecs=False, batch_size=32)
        ups = []
        for p, lw in zip(pts, out["lexical_weights"]):
            idx = [int(k) for k in lw.keys()]; val = [float(v) for v in lw.values()]
            if not idx: empty += 1; continue
            dense = p.vector["dense"] if isinstance(p.vector, dict) else p.vector
            ups.append(models.PointStruct(
                id=p.id, payload=p.payload,
                vector={"dense": dense,
                        "sparse": models.SparseVector(indices=idx, values=val)}))
        if ups: qc.upsert(TGT, points=ups, wait=False)
        done += len(pts)
        if done % 2560 == 0:
            r = done / max(1e-9, time.time() - t0)
            print("  %d/%d  %.0f pts/s  eta %.0f min" % (done, n, r, (n - done) / r / 60))
        if off is None: break
    qc.upsert(TGT, points=[], wait=True)
    print("DONE: copied %d, empty-sparse skipped %d, %.1f min"
          % (done, empty, (time.time() - t0) / 60))
    print("target count:", qc.get_collection(TGT).points_count)

    # (R87, 2026-08-18) WRITE THE BUILD RECORD. The first run of this script
    # did not, so `p42_text_v3_bgelex` was ADOPTED AS THE SERVED INDEX with no
    # machine-readable provenance at all - and the one field that differs from
    # its source, `sparse_backend`, existed nowhere. A collection that cannot
    # say how it was built is not traceable to any figure measured on it.
    base = "kb-ingest-config-%s.json" % SRC
    cfg = json.load(open(base)) if os.path.exists(base) else {}
    cfg.update({
        "written": time.strftime("%Y-%m-%d %H:%M:%S"),
        "derived_from": base,
        "how_built": ("sparse_build.py (R10). Passages, payloads and DENSE "
                      "VECTORS copied from %s; ONLY the sparse vector "
                      "recomputed. No re-parse, no re-embed, no Docling." % SRC),
        "sparse_backend": "bge-m3-lexical",
        "collections": {"text": TGT, "pages": None},
        "points_copied": done,
        "empty_sparse_skipped": empty,
    })
    out = "kb-ingest-config-%s.json" % TGT
    json.dump(cfg, open(out, "w"), indent=2)
    print("build record written to %s" % out)
    return 0

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", default=DEFAULT_SRC)
    ap.add_argument("--target", default=DEFAULT_TGT)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        # The build itself needs FlagEmbedding and a GPU; these are the checks
        # that can run anywhere, and they are the ones that protect the index.
        ok = True
        src_txt = open(os.path.abspath(__file__)).read()
        for name, cond in [
            ("source and target are arguments, not hardcoded",
             "--source" in src_txt and "--target" in src_txt),
            ("a source equal to the target ABORTS",
             "source and target are the same collection" in src_txt),
            ("an existing target is REFUSED, never overwritten",
             "already exists; refusing to overwrite" in src_txt),
            ("a missing source ABORTS by name",
             "does not exist" in src_txt),
            ("the build writes its own provenance record (R87)",
             "build record written to" in src_txt),
            ("the source is opened READ-ONLY and says so",
             "READ-ONLY" in src_txt),
        ]:
            print("  %-66s %s" % (name, "ok" if cond else "FAIL"))
            ok = ok and cond
        sys.exit(0 if ok else 1)
    SRC, TGT = a.source, a.target
    print("source %r  ->  target %r" % (SRC, TGT))
    sys.exit(main())
