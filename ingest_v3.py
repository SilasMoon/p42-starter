# ---------------------------------------------------------------------------
# Project 42 - batch ingestion v3.3  (Campaign 2)
#
# v3.3 (2026-08-13) - THE MANIFEST IS NOW KEYED TO THE TARGET COLLECTION.
#
#      Found by trying to ingest the unchanged corpus into a NEW collection.
#      Result: "skipped: 88, ingested: 0" and an empty target. The ledger
#      records "have I ingested this FILE?" and the question it must answer is
#      "have I ingested this file INTO THIS COLLECTION?" - the skip decision
#      compared shas and never looked at where the points were going.
#
#      The failure mode is the dangerous kind: it SUCCEEDS. Exit 0, a clean
#      summary, an empty collection, and any tool pointed at that collection
#      then measures nothing and reports it as a result.
#
#      MANIFEST and CONFIG_PATH are now derived from TEXT_COLL after argument
#      parsing. p42_text_v2 keeps its existing ledger filenames so the recorded
#      state of the audited index is not orphaned; every other collection gets
#      kb-manifest-<collection>.json. --force re-ingests regardless of ledger.
#
# v3.2 (2026-08-13) - ONE CHANGE: the payload now carries "cut".
#
#      chunk_document() has always computed WHY each chunk ended - "structural"
#      (a requirement boundary), "paragraph" (a paragraph break past the slack),
#      or "hard_max" (the budget ran out) - and the payload dict written to
#      Qdrant did not carry it. Everything downstream therefore had to infer
#      chunk integrity from n_chars, and n_chars cannot carry that signal: the
#      flush condition is evaluated on the buffer BEFORE the current item is
#      appended, so a chunk can overshoot the budget (observed: 3798 chars) and
#      still have ended at a clean item boundary, while a chunk under the budget
#      can have ended because the budget ran out.
#
#      Found by anchor_sampler.py v1.0, whose nuance-class screen "the condition
#      was cut WITH its obligation" was keyed on this field and was therefore
#      accepting every chunk silently. That is the campaign-1 failure mode: the
#      reranker that failed on every call, the acronym dual payload that
#      reported success while doing nothing. A screen keyed on an absent field
#      does not fail - it passes everything, and the run still prints PASS.
#
#      "cut" is what requirement I6 is FOR. Emitting it makes I6's effect
#      measurable per chunk instead of assumed in aggregate.
#
#      TAKES EFFECT AT THE NEXT INGEST. The live p42_text_v2 does not carry the
#      field, so gates 1b/2/4 and their audits stand as recorded against the
#      index they were run on. Re-ingesting invalidates nothing that has been
#      passed, but it DOES produce a new index sha - gate 4 is cheap and should
#      be re-run on the new index before anchors are drawn from it.
#      The same change is needed in the runbook's ingest heredoc (DGX_Spark_
#      Setup_Runbook.md), or the next paste silently reverts it.
#
# WHAT CHANGED FROM v2.7, AND WHY. Every item traces to a measured defect or a
# design requirement in P42_Design_Pipeline_and_Benchmark v3.6.
#
#  I6  SUBCLAUSE-BOUNDARY CHUNKING (was: 1600-character cut).
#      Measured: 27% of all chunks sat at the size cap, 45% for table
#      reasoning. Splitting on length orphans a requirement from the condition
#      that qualifies it - "the margin shall be at least 2,0" is meaningless
#      without knowing which function and which model it applies to. v3.0 cuts
#      only at a requirement boundary (a numbered clause, a lettered item, or a
#      heading) and allows a chunk to run to HARD_MAX rather than split one.
#
#  I7  FULL BREADCRUMB PREPENDED BEFORE VECTORISATION.
#      Document code, revision, clause path and heading trail now lead the text
#      that is embedded, not just the text that is displayed.
#
#  I1  TABLES NEVER SPLIT; header repeated if a table must divide by rows.
#      v2.7 emitted tables whole but let an over-long table become one giant
#      chunk that the embedder truncated at 8000 chars. v3.0 divides by ROWS
#      and repeats the header on each part.
#
#  I3  DEFINITIONS AND ABBREVIATIONS INDEXED AS INDIVIDUAL UNITS.
#      Measured: glossary entries ranked 9th for their own term, because the
#      glossary is one enormous document whose entries competed with each
#      other. Clause 3.1 "Terms ... definitions" and clause 3.3 "Abbreviated
#      terms" are now split into one point per entry.
#
#  I9  ACRONYM TABLE PER DOCUMENT + DUAL PAYLOAD  (design 5.4).
#      Measured: 1451 acronyms across the corpus, 99 of them GENUINE SEMANTIC
#      COLLISIONS - PDR is "preliminary design review" in 21 documents and
#      "product definition review" in one; TC is telecommand in five and
#      thermocouple in one. A global dictionary would expand TC wrongly about
#      as often as rightly, and expanding at QUERY time forces a commitment
#      before retrieval that is wrong in both directions on a multi-hop
#      question. So every chunk is embedded with the acronyms expanded INLINE
#      using THAT DOCUMENT'S OWN clause 3.3 table:  "TC [telecommand]".
#      The raw text is kept verbatim for display and citation.
#
#  I4  CROSS-REFERENCES EXTRACTED AS STRUCTURED LINKS (payload "refs"), which
#      is what makes the boundary list and the dangling-reference question
#      class possible without re-parsing chunk text.
#
#  I8  IDENTIFIERS AND CLAUSE NUMBERS AS FILTERABLE METADATA, and a SPARSE
#      (lexical) vector alongside the dense one. Dense embeddings place
#      ECSS-E-ST-10-02C and ECSS-E-ST-10-03C almost on top of each other; the
#      sparse vector is what separates them. Payload indexes are created so
#      the filters are actually usable.
#
#  I5  EVERY INDEX BUILT HAS A QUERY PATH, OR IS DECLARED OUT OF SCOPE.
#      The ColQwen page collection (p42_pages) was built by every ingest and
#      queried by NOTHING - not the harness, not ask.py, not the Function
#      (defect H-2). It is therefore NOT built by default in v3.0: it costs a
#      6-7 GB model load and per-page GPU work for zero measured benefit. Pass
#      --with-pages to restore it. VL figure captions are KEPT, because those
#      do reach the text index and the figure question class depends on them.
#
#  AUTHORITY MODEL (v3.1). Every point carries four fields describing the
#  STANDING of the document it came from, not just its identity:
#
#      authority     normative | contractual | informative | record
#      source_class  standard | project_spec | drd_deliverable | handbook |
#                    minutes | correspondence
#      applies_to    project identifier; null for standards
#      tailors       document codes this one modifies or deviates from
#
#      WHY IT IS HERE ON DAY ONE. In compliance work documents have different
#      standing: a standard IMPOSES, a project specification COMMITS TO or
#      TAILORS, a handbook ADVISES, minutes RECORD. Without this, a project
#      document saying "margin 1,25" and ECSS-E-ST-32 saying "1,40" are
#      indistinguishable text, and an answer cannot tell the reader whether it
#      is quoting a requirement or a deviation from one. That is a hallucination
#      class we would have no way to DETECT, because nothing in the payload
#      distinguishes the two.
#
#      It changes four things: retrieval (filter and scope by project),
#      the answer prompt (state authority when quoting), grading (presenting
#      contractual content as normative becomes a mechanically detectable
#      forbidden claim), and the applicability/authority question class.
#
#      Everything ingested now is a standard, so these values are constant for
#      this corpus. The field exists anyway because adding it later means
#      re-ingesting 88 documents to backfill something that costs nothing now -
#      the same reasoning v2.7 used for document_revision, and for the same
#      reason.
#
#      BENCHMARK INTEGRITY: project documents belong in a SEPARATE collection,
#      queried alongside. The benchmark measures ECSS only, because ECSS has
#      public ground truth an outside reviewer can verify. Put project material
#      in the measured corpus and no one outside the team can check any result.
#
#  NEW COLLECTION. v3.1 writes p42_text_v2, leaving p42_text untouched and
#  queryable, so the two chunkings can be compared rather than one destroyed.
#
# RUN WITH:  ~/p42/ingest-venv/bin/python ingest_v3.py <path>...
#            (the system python3 has no docling - see the import guard below)
#
# Usage:  python ingest.py <path> [<path> ...]     files and/or folders
#         python ingest.py --remove <source_file> [...]
#         python ingest.py --list
#   flags: --with-pages     also build the ColQwen page collection (off)
#          --no-captions    skip the VL captioning pass (on by default)
#          --no-sparse      dense vectors only (sparse on by default)
#          --collection X   override the target text collection name
#          --authority X    normative (default) | contractual | informative | record
#          --source-class X standard (default) | project_spec | drd_deliverable |
#                           handbook | minutes | correspondence
#          --applies-to X   project identifier for project documents (default none)
#          --tailors A,B    document codes these documents tailor or deviate from
#          --ocr            run Docling's OCR pass (OFF by default - see below)
# ---------------------------------------------------------------------------
import sys, os, io, json, base64, hashlib, uuid, re, time, shutil, subprocess, tempfile
from collections import Counter
from datetime import datetime

# (v3.1) RUN THIS INSIDE ~/p42/ingest-venv. The heavy parsing stack (docling,
# torch, qdrant-client, pdf2image) is installed ONLY in that virtualenv, not in
# the system python. Running `python3 ingest_v3.py` outside it fails with a bare
# ModuleNotFoundError that says nothing about the cause, which is exactly the
# kind of silent-cause failure the preflight below exists to prevent - so the
# import guard names the fix.
try:
    import requests
    from docling.document_converter import DocumentConverter
    from qdrant_client import QdrantClient, models
except ModuleNotFoundError as _e:
    _venv = os.path.expanduser("~/p42/ingest-venv/bin/python")
    print("=" * 60)
    print(" ingest.py v3.1 - WRONG PYTHON ENVIRONMENT")
    print("=" * 60)
    print(" missing module: %s" % _e.name)
    print("")
    print(" The ingestion stack lives in ~/p42/ingest-venv, not in the system")
    print(" python. Run it with that interpreter:")
    print("")
    print("   %s ingest_v3.py <path>..." % _venv)
    print("")
    print(" or activate the environment first:")
    print("")
    print("   source ~/p42/ingest-venv/bin/activate")
    print("   python ingest_v3.py <path>...")
    print("=" * 60)
    sys.exit(2)

def fmt_dur(seconds):
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return ("%dh %dm %ds" % (h, m, s)) if h else ("%dm %ds" % (m, s))

BAR = "=" * 60
def banner(*lines):
    print(BAR)
    for l in lines:
        print(" " + l)
    print(BAR)

QDRANT   = "http://localhost:6333"
EMBED    = "http://localhost:8080"
VL       = "http://localhost:8002"
# (v3.3) The ledger answers "is this file already in THIS COLLECTION?", so it
# is per collection. p42_text_v2 keeps the historical filenames: renaming its
# ledger would orphan the record of the index gates 1b/2/4 were passed against,
# and the next run would silently re-ingest all 88 documents.
LEGACY_LEDGERS = {"p42_text_v2": ("~/p42/kb-manifest-v2.json",
                                  "~/p42/kb-ingest-config-v2.json")}


def ledger_paths(coll):
    m, c = LEGACY_LEDGERS.get(
        coll, ("~/p42/kb-manifest-%s.json" % coll,
               "~/p42/kb-ingest-config-%s.json" % coll))
    return os.path.expanduser(m), os.path.expanduser(c)


MANIFEST = os.path.expanduser("~/p42/kb-manifest-v2.json")   # rebound in main()
TEXT_COLL, PAGE_COLL = "p42_text_v2", "p42_pages_v2"

# --- chunking budget (I6) --------------------------------------------------
# TARGET is where we PREFER to end a chunk; HARD_MAX is the point past which we
# accept a mid-requirement cut because something has gone wrong with the parse.
# In v2.7 the single CHUNK_CHARS acted as both, which is why 27% of chunks sat
# exactly at it.
TARGET_CHARS = 1600
SLACK_CHARS  = 900        # how far past TARGET we hunt for a structural cut
HARD_MAX     = 3600
MIN_CHARS    = 120        # below this, merge forward rather than emit a stub
#
# WHY SLACK EXISTS (v3.0, found while checking non-ECSS reuse).
# The boundary rule below cuts only at a numbered clause, a lettered item or a
# requirement identifier. In an ECSS standard those are dense, so a chunk
# reaches one soon after TARGET. In a document that has NO such structure - a
# project narrative, a report, a scanned memo - a boundary may never appear,
# and every chunk would run to HARD_MAX and then sever mid-sentence anyway.
# So: past TARGET we prefer a structural boundary; past TARGET+SLACK we accept
# a plain paragraph break, which is a real boundary in prose. HARD_MAX remains
# the last resort. This makes the chunker degrade sensibly on documents it was
# not designed for, instead of silently producing 3600-character blocks.

SUPPORTED = (".pdf", ".docx", ".pptx", ".xlsx", ".html", ".htm", ".md")

INGEST_VERSION = "v3.3"
CONFIG_PATH   = os.path.expanduser("~/p42/kb-ingest-config-v2.json")  # rebound in main()
EMBED_MODEL   = "BAAI/bge-m3"
CAPTION_MODEL = "nvidia/Qwen2.5-VL-7B-Instruct-NVFP4"
COLQWEN_MODEL = "vidore/colqwen2.5-v0.2"
PDF_DPI       = 120

OPT = {"pages": False, "captions": True, "sparse": True, "ocr": False,
       "force": False}
#
# WHY OCR IS OFF BY DEFAULT (v3.1, measured 2026-08-12).
# Docling runs RapidOCR over every page by default. Measured across all 88
# corpus documents, the MINIMUM extractable text is 1186 characters per page
# and the median is 2286 - every document has a real text layer, and NONE is a
# scan. A scanned PDF would be near zero. So the OCR pass finds nothing it can
# add ("RapidOCR returned empty result") while costing minutes per document:
# ECSS-E-AS-11C, a TWELVE-page adoption notice, spent over four minutes in it.
# This is the same rule as I5 - do not build what nothing consumes - applied to
# a processing stage rather than an index. Pass --ocr to turn it back on if a
# scanned document is ever added to the corpus.

# --- authority model (v3.1) ------------------------------------------------
# Defaults describe what THIS corpus is: ECSS standards, which impose.
AUTHORITY_VALUES    = ("normative", "contractual", "informative", "record")
SOURCE_CLASS_VALUES = ("standard", "project_spec", "drd_deliverable",
                       "handbook", "minutes", "correspondence")
SRC = {"authority": "normative", "source_class": "standard",
       "applies_to": None, "tailors": []}

qc = QdrantClient(url=QDRANT, timeout=120)
converter = None            # built in make_converter() once OPT is parsed


def make_converter():
    """DocumentConverter with OCR per OPT["ocr"], table structure always on.

    The pipeline-options API has moved between Docling versions, so this falls
    back to a default converter and SAYS SO rather than failing the run - but a
    silent fallback would reintroduce the multi-minute OCR pass, so the message
    is explicit.
    """
    if OPT["ocr"]:
        print("  docling OCR : ON (--ocr)")
        return DocumentConverter()
    try:
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import PdfPipelineOptions
        from docling.document_converter import PdfFormatOption
        popts = PdfPipelineOptions()
        popts.do_ocr = False              # every corpus document has a text layer
        popts.do_table_structure = True   # this is what produces the table chunks
        print("  docling OCR : OFF (text layer present in all corpus documents)")
        return DocumentConverter(
            format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=popts)})
    except Exception as e:
        print("  docling OCR : COULD NOT DISABLE (%r)" % e)
        print("                falling back to the default converter - expect the")
        print("                OCR pass to cost minutes per document")
        return DocumentConverter()
_colqwen = None
_sparse_backend = None            # set by init_sparse(); recorded in the config

# ---------------------------------------------------------------------------
# ECSS structure recognisers
# ---------------------------------------------------------------------------
REF_RE = re.compile(r'ECSS-[A-Z]-(?:ST|AS|HB|TM)-[0-9]{2}(?:-[0-9]{2})*')
# A numbered clause at the start of a line.
#
# SPLIT IN TWO, v3.1, after live answers showed sources labelled
# "ECSS-E-ST-32-10 | 2019" and "ECSS-E-ST-20 | 25". The clause value is what
# ask.py puts on the SOURCE line the model is told to cite from, so a polluted
# clause becomes a citation that LOOKS fabricated but was handed to the model
# by us. It is also a filter key (I8).
#
# The old single pattern matched any line starting with a number followed by
# text, so it captured "1 August 2019" (page footer) and "25 mm shall be
# measured" (a requirement about a dimension) as clause numbers.
#
#   CLAUSE_DOTTED  4.3.2.4 - unambiguous, trusted anywhere in the document.
#   CLAUSE_BARE    5 Requirements - ambiguous with dates, dimensions and list
#                  items, so trusted ONLY on an item Docling identified as a
#                  heading, never on body text.
CLAUSE_DOTTED = re.compile(r'^[ \t]*((?:[1-9]|1[0-9])(?:\.\d{1,3}){1,4})[ \t]+(?=\S)')
CLAUSE_BARE = re.compile(r'^[ \t]*((?:[1-9]|1[0-9]))[ \t]+(?=[A-Z])')
CLAUSE_RE = CLAUSE_DOTTED          # boundary detection uses the safe form only


# (R85, 2026-08-18) An ANNEX heading, and an annex-numbered sub-heading.
# The clause label used to STICK: `clause = c if c else clause` kept the last
# body clause number across every heading that did not declare one, so the
# annexes inherited it. Measured before the fix: ECSS-E-ST-40 had 475 of its
# 825 chunks labelled `5.11.5.6`, spread across **312 distinct section
# headings** - Annex A, `<1> Introduction`, `R.2 Tailoring`, `Q.3.2`. The
# spread is the tell: a label concentrated in one or two sections is a large
# table and is legitimate; one spread across hundreds is broken.
ANNEX_HEAD = re.compile(r'^\s*Annex\s+([A-Z])\b', re.I)
ANNEX_CLAUSE = re.compile(r'^\s*([A-Z]\.\d+(?:\.\d+)*)\s+\S')


def clause_for_heading(text, current):
    """The clause label in force AFTER this heading.

    INHERITING IS NOT ALWAYS WRONG - a plain sub-heading inside clause 5.4
    genuinely sits in 5.4, and blanking the label there would lose real
    information. What was wrong was inheriting ACROSS AN ANNEX BOUNDARY, where
    the numbered-clause context has ended. So only annex headings and
    annex-numbered headings reset it; everything else still inherits.
    """
    c = clause_of(text, is_heading=True)
    if c:
        return c
    m = ANNEX_CLAUSE.match(text)
    if m:
        return m.group(1)
    m = ANNEX_HEAD.match(text)
    if m:
        return m.group(1).upper()
    return current


def clause_of(text, is_heading):
    """The clause number this line declares, or None."""
    m = CLAUSE_DOTTED.match(text)
    if m:
        return m.group(1)
    if is_heading:
        m = CLAUSE_BARE.match(text)
        if m:
            return m.group(1)
    return None
# a lettered requirement item: "a." / "b)" / "c. " - ECSS requirement grain
ITEM_RE = re.compile(r'^\s*([a-z])[.)]\s+(?=\S)')
# a numbered sub-item under a lettered item
SUBITEM_RE = re.compile(r'^\s*(\d{1,2})[.)]\s+(?=\S)')
# requirement identifiers ECSS stamps into the text, e.g. ECSS-Q-ST-70-61_1510138
REQID_RE = re.compile(r'\b(ECSS-[A-Z]-(?:ST|AS)-[0-9]{2}(?:-[0-9]{2})*_[0-9]{4,})\b')
MODAL_RE = re.compile(r'\b(shall|should|may|can)\b', re.I)

# clause 3.x headings we split into individual units (I3)
DEF_HEAD  = re.compile(r'^\s*3\.\d\s+Terms\b.*definition|^\s*Terms and definitions\s*$', re.I)
ABBR_HEAD = re.compile(r'^\s*3\.\d\s+Abbreviated terms\s*$|^\s*Abbreviated terms\s*$', re.I)
# "3.2.14 annular ring" - a defined term heading inside clause 3
DEFTERM_RE = re.compile(r'^\s*3(?:\.\d+){1,3}\s+([a-z][^\n]{1,80})$')
# an abbreviated-terms row: "TC   telecommand"
ABBRROW_RE = re.compile(r'^\s*([A-Z][A-Za-z0-9/\-]{1,9})\s{2,}([A-Za-z][^\n]{3,80})$')
ABBRROW_RE_M = re.compile(r'^\s*([A-Z][A-Za-z0-9/\-]{1,9})\s{2,}([A-Za-z][^\n]{3,80})$', re.M)
# (v3.1) the heading variants that actually occur: "Abbreviated terms and
# symbols", "Abbreviations", and a clause number other than 3.x (the Glossary
# ECSS-S-ST-00-01 uses 2.4). The negative lookbehind drops dot-leader lines.
ABBR_HEAD_WIDE = re.compile(r'^[ \t]*(?:\d+\.\d+[ \t]+)?'
                            r'Abbreviat(?:ed|ions?)[^\n]{0,40}?(?<!\.)[ \t]*$', re.I | re.M)
TOC_LINE = re.compile(r'\.{3,}\s*\d+\s*$')
ABBR_END = re.compile(r'^\s*(?:[3-9]\.\d|[45])\s+(?!Abbrev|Nomenclature)\S', re.M)


def layout_text(path):
    """Plain text of the document WITH ITS COLUMN LAYOUT PRESERVED.

    WHY THIS EXISTS (v3.1, found in the first smoke test).
    Docling's export_to_text() collapses runs of spaces. ECSS clause 3.3
    "Abbreviated terms" is a two-column table rendered as "TC   telecommand",
    and the row recogniser keys on that run of spaces. Fed Docling text the
    harvester returned ZERO acronyms on a document that actually defines 62 of
    them - so the whole I9 dual-payload feature was silently doing nothing while
    reporting success. Definitions survived (their recogniser keys on the clause
    number, not on spacing), which is why only half the feature looked broken.

    Order of preference:
      1. the sibling `pdftotext -layout` file the corpus assembly already made
      2. pdftotext -layout run on the fly into a temp file
      3. Docling text, with a warning - the acronym table will be empty
    """
    base = os.path.splitext(os.path.basename(path))[0]
    sib = os.path.join(os.path.dirname(os.path.dirname(path)), "txt", base + ".txt")
    if os.path.exists(sib):
        return open(sib, errors="ignore").read(), "sibling-layout-txt"
    if path.lower().endswith(".pdf") and shutil.which("pdftotext"):
        try:
            with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tf:
                tmp = tf.name
            subprocess.run(["pdftotext", "-layout", path, tmp],
                           check=True, capture_output=True, timeout=300)
            out = open(tmp, errors="ignore").read()
            os.unlink(tmp)
            return out, "pdftotext-on-the-fly"
        except Exception as e:
            print("        pdftotext -layout failed (%r)" % e)
    return "", "unavailable"


def dehyphenate(text):
    """Rejoin an ECSS code broken across a line or column break."""
    return re.sub(r'(ECSS-[A-Z]-(?:ST|AS|HB|TM)-[0-9]{2}(?:-[0-9]{2})*)-[ \t\n]+([0-9]{2})',
                  r'\1-\2', text)


# (R21, 2026-08-18) PRE-2008 ECSS NAMES HAVE NO ST/AS/HB/TM SEGMENT.
# `ECSS-M-70A(19April1996)` and `ECSS-P-00C-Rev.1(...)` matched neither the
# doc-code nor the revision pattern, so the WHOLE FILENAME became the doc_code
# and the revision came back empty. Three documents in the corpus were
# affected. The pre-2008 form is admitted as a SECOND alternative rather than
# by loosening the first, so a modern filename still has to match the modern
# shape.
_SEG = r'ECSS-[A-Z]-(?:ST|AS|HB|TM)-[0-9]{2}(?:-[0-9]{2})*'
_OLD = r'ECSS-[A-Z]-[0-9]{2}(?:-[0-9]{2})*'          # pre-2008: no ST/AS/HB/TM
DOC_CODE_RE = re.compile(r'(%s|%s)' % (_SEG, _OLD))
REVISION_RE = re.compile(r'(?:%s|%s)([A-Z])(?:[-_ ]?Rev\.?\s?(\d+))?'
                         % (_SEG, _OLD))


def doc_code_of(source):
    m = DOC_CODE_RE.match(os.path.basename(source))
    return m.group(1) if m else ""


def revision_of(source):
    """The revision letter, from the FILENAME.

    NOT from the document. That is a known limitation, recorded in R21: a
    corpus whose filenames do not carry the revision reports none, and
    `label_coverage.py` prints that as a profile mismatch rather than a
    failure. Reading it from the cover page is the proper fix and is not in
    this rebuild.
    """
    m = REVISION_RE.search(os.path.basename(source))
    if not m:
        return ""
    return m.group(1) + (" Rev." + m.group(2) if m.group(2) else "")


# ---------------------------------------------------------------------------
# I9 - acronym table, harvested per document from its own clause 3.3
# ---------------------------------------------------------------------------
def harvest_acronyms(raw_text):
    """{ACRONYM: expansion} from this document's abbreviated-terms clause.

    Per document on purpose. 99 acronyms in this corpus have expansions that
    share no words at all across documents; a global table would be wrong.

    TWO PASSES, UNIONED (v3.1, after the first full-corpus run).
    Pass A is the strict heading "3.3 Abbreviated terms". Pass B accepts the
    real variants measured across the corpus: "Abbreviated terms and symbols"
    (5 documents), a different clause number - ECSS-S-ST-00-01 the Glossary
    uses "2.4" (140 acronyms, the single biggest miss) - and bare
    "Abbreviations". Table-of-contents lines are excluded by their trailing
    dot leader and page number.

    They are UNIONED rather than swapped because pass B alone regresses one
    document (ECSS-Q-ST-70-09C) whose layout pass A handles. Measured on the
    87-document corpus: pass A alone 2459 acronyms with 9 documents at zero;
    union 2590 with 2 at zero.
    """
    out = {}
    lines = raw_text.split("\n")

    # --- pass A: strict heading, line-by-line state machine
    inside = False
    for line in lines:
        if ABBR_HEAD.match(line):
            inside = True
            continue
        if inside:
            if re.match(r'^\s*[45]\s+\S|^\s*3\.\d\s+(?!Abbrev)', line):
                inside = False
                continue
            m = ABBRROW_RE.match(line)
            if m:
                short, expansion = m.group(1), re.sub(r'\s+', ' ', m.group(2)).strip()
                if not expansion.startswith("ECSS") and short not in out:
                    out[short] = expansion

    # --- pass B: broadened heading, segment to the next clause heading
    for m in ABBR_HEAD_WIDE.finditer(raw_text):
        head_line = raw_text[raw_text.rfind("\n", 0, m.start()) + 1: m.end()]
        if TOC_LINE.search(head_line):          # a table-of-contents entry
            continue
        start = m.end()
        nxt = ABBR_END.search(raw_text, start + 2)
        seg = raw_text[start: nxt.start() if nxt else start + 9000]
        for short, expansion in ABBRROW_RE_M.findall(seg):
            expansion = re.sub(r'\s+', ' ', expansion).strip()
            if (not expansion.startswith("ECSS") and short not in out
                    and short != "Abbreviation"):
                out[short] = expansion
    return out


def expand_acronyms(text, table):
    """Dual payload (design 5.4): 'TC' -> 'TC [telecommand]', once per acronym
    per chunk. The FIRST occurrence is annotated; later ones are left alone so
    the expanded text stays readable and the embedding is not swamped."""
    if not table:
        return text
    done = set()
    def sub(m):
        w = m.group(0)
        if w in table and w not in done:
            done.add(w)
            return "%s [%s]" % (w, table[w])
        return w
    return re.sub(r'\b[A-Z][A-Za-z0-9/\-]{1,9}\b', sub, text)


# ---------------------------------------------------------------------------
# I8 - sparse (lexical) vectors
# ---------------------------------------------------------------------------
def init_sparse():
    """Pick a sparse backend once, and record which one was used.

    Preferred: BGE-M3's own lexical weights, which is what the design specifies
    and costs no extra service (the same model already emits them). If
    FlagEmbedding is not installed, fall back to a deterministic hashed
    term-frequency vector. The fallback is NOT as good semantically, but it
    does the job the sparse vector exists for - separating ECSS-E-ST-10-02C
    from ECSS-E-ST-10-03C on an exact token match.
    """
    global _sparse_backend
    if not OPT["sparse"]:
        _sparse_backend = "disabled"
        return
    try:
        from FlagEmbedding import BGEM3FlagModel            # noqa: F401
        _sparse_backend = "bge-m3-lexical"
    except Exception:
        _sparse_backend = "hashed-term-frequency"
    print("  sparse backend: " + _sparse_backend)


_bgem3 = None
def sparse_vector(text):
    """-> (indices, values) or None."""
    global _bgem3
    if _sparse_backend in (None, "disabled"):
        return None
    if _sparse_backend == "bge-m3-lexical":
        if _bgem3 is None:
            from FlagEmbedding import BGEM3FlagModel
            print("        loading BGE-M3 for lexical weights (first use) ...")
            _bgem3 = BGEM3FlagModel(EMBED_MODEL, use_fp16=True)
        out = _bgem3.encode([text[:8000]], return_dense=False,
                            return_sparse=True, return_colbert_vecs=False)
        lw = out["lexical_weights"][0]
        if not lw:
            return None
        idx = [int(k) for k in lw.keys()]
        val = [float(v) for v in lw.values()]
        return idx, val
    # fallback: hashed term frequency, lower-cased, ECSS codes kept whole
    toks = re.findall(r'ECSS-[A-Z]-(?:ST|AS|HB|TM)-[0-9]{2}(?:-[0-9]{2})*'
                      r'|[A-Za-z][A-Za-z0-9\-]{1,}', text[:8000])
    if not toks:
        return None
    c = Counter(t.lower() for t in toks)
    idx, val = [], []
    for t, n in c.items():
        idx.append(int(hashlib.md5(t.encode()).hexdigest()[:8], 16) % (2 ** 31))
        val.append(float(n))
    return idx, val


# ---------------------------------------------------------------------------
# collections
# ---------------------------------------------------------------------------
def ensure_collections():
    if not qc.collection_exists(TEXT_COLL):
        cfg = dict(
            collection_name=TEXT_COLL,
            vectors_config={"dense": models.VectorParams(
                size=1024, distance=models.Distance.COSINE)})
        if OPT["sparse"]:
            cfg["sparse_vectors_config"] = {"sparse": models.SparseVectorParams()}
        qc.create_collection(**cfg)
        # I8: the filters are only usable if the fields are indexed
        for field, schema in (("doc_code", models.PayloadSchemaType.KEYWORD),
                              ("authority", models.PayloadSchemaType.KEYWORD),
                              ("source_class", models.PayloadSchemaType.KEYWORD),
                              ("applies_to", models.PayloadSchemaType.KEYWORD),
                              ("tailors", models.PayloadSchemaType.KEYWORD),
                              ("clause",   models.PayloadSchemaType.KEYWORD),
                              ("element_type", models.PayloadSchemaType.KEYWORD),
                              ("document_revision", models.PayloadSchemaType.KEYWORD),
                              ("refs", models.PayloadSchemaType.KEYWORD),
                              ("source_file", models.PayloadSchemaType.KEYWORD)):
            try:
                qc.create_payload_index(TEXT_COLL, field_name=field,
                                        field_schema=schema)
            except Exception as e:
                print("  payload index %s: %r" % (field, e))
    if OPT["pages"] and not qc.collection_exists(PAGE_COLL):
        qc.create_collection(PAGE_COLL, vectors_config=models.VectorParams(
            size=128, distance=models.Distance.COSINE,
            multivector_config=models.MultiVectorConfig(
                comparator=models.MultiVectorComparator.MAX_SIM)))


def load_manifest():
    if os.path.exists(MANIFEST):
        with open(MANIFEST) as f:
            return json.load(f)
    return {}

def save_manifest(m):
    with open(MANIFEST, "w") as f:
        json.dump(m, f, indent=2, sort_keys=True)

def sha256_of(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def point_id(source, index):
    """POSITIONAL id - v3. Retained ONLY for the page collection, where the
    index IS the page number and position is the identity."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, source + "#v3#" + str(index)))


def content_point_id(source, body, occurrence=0):
    """CONTENT id - v4. Register R86.

    WHY THIS REPLACED THE POSITIONAL ID. `point_id` keyed on the chunk's
    ordinal position in the document, so inserting anything - turning figure
    captioning on (R70) is exactly that - RENUMBERED every chunk after the
    insertion. Every stored `ranked` list, qrel and scorecard reference then
    stopped resolving, and stopped resolving SILENTLY, because the ids still
    looked like valid UUIDs.

    THE KEY IS THE RAW BODY, and deliberately not the clause, the crumb or the
    embedded text. R85 changes clause labels in this same rebuild; keying on
    anything that carries the clause would make every relabelled chunk look
    like a new one and destroy the before/after diff this id exists to enable.

    `occurrence` disambiguates a document that repeats a chunk verbatim -
    without it the second copy would collide with the first and one would
    silently overwrite the other in Qdrant.
    """
    h = hashlib.sha1(body.encode("utf-8")).hexdigest()[:20]
    return str(uuid.uuid5(uuid.NAMESPACE_URL,
                          "%s#v4#%s#%d" % (source, h, occurrence)))

def delete_points(source):
    flt = models.Filter(must=[models.FieldCondition(
        key="source_file", match=models.MatchValue(value=source))])
    colls = [TEXT_COLL] + ([PAGE_COLL] if OPT["pages"] else [])
    for coll in colls:
        if qc.collection_exists(coll):
            qc.delete(coll, points_selector=models.FilterSelector(filter=flt))

def embed(text):
    r = requests.post(EMBED + "/v1/embeddings", timeout=120, json={
        "model": EMBED_MODEL, "input": text[:8000]})
    return r.json()["data"][0]["embedding"]

# (2026-08-18) NEGATIVE CAPTIONS ARE NOISE, AND THEY WERE BEING INDEXED.
# The old prompt said "If none, reply none" and the guard tested
# `cap.strip().lower() != "none"`. The model does not comply: it answers
# "There are no figures or diagrams present on this page. The content is
# purely textual, ..." - a median of 196 characters. Measured on the first 12
# documents of the R89 rebuild: **600 captions injected, 548 of them (91%)
# negative**, appended to real requirement chunks and embedded into their
# dense vectors. Caught by reading the index 25 minutes into the run.
#
# Fixed at BOTH ends: the prompt demands a bare token, and the response is
# filtered anyway, because a prompt is a request and a guard is a guarantee.
CAPTION_PROMPT = ("Describe any figures, diagrams, drawings or schematics on "
                  "this page in 2-3 sentences. Describe only what the figure "
                  "shows. If the page has no figure, diagram, drawing or "
                  "schematic, reply with the single word NONE and nothing "
                  "else. Do not explain that there are none. Do not describe "
                  "tables or body text.")

# Phrasings the captioner actually produced when there was nothing to caption.
_NO_FIGURE = re.compile(
    r"there (?:are|is) no (?:figures|diagrams|drawings|schematics|images)"
    r"|no (?:figures|diagrams|drawings|schematics) (?:or|are|is|present)"
    r"|does not (?:contain|include|have) any (?:figures|diagrams)"
    r"|purely textual|only text|no visual|contains no (?:figures|diagrams)",
    re.I)
MIN_CAPTION_CHARS = 25


def usable_caption(cap):
    """The caption to index, or None if there is nothing worth indexing.

    Returns None for a bare NONE, for any of the model's prose ways of saying
    the same thing, and for anything too short to carry a description. A
    caption that merely reports the ABSENCE of a figure is worse than no
    caption: it is indexed, embedded, and can be retrieved.
    """
    c = (cap or "").strip()
    if not c:
        return None
    bare = c.strip(" .\t\n\"'").lower()
    if bare in ("none", "no", "n/a", "nothing"):
        return None
    if _NO_FIGURE.search(c):
        return None
    if len(c) < MIN_CAPTION_CHARS:
        return None
    return c


def caption(img):
    buf = io.BytesIO(); img.save(buf, format="JPEG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    r = requests.post(VL + "/v1/chat/completions", timeout=300, json={
        "model": CAPTION_MODEL,
        "messages": [{"role": "user", "content": [
            {"type": "image_url",
             "image_url": {"url": "data:image/jpeg;base64," + b64}},
            {"type": "text", "text": CAPTION_PROMPT}]}]})
    return r.json()["choices"][0]["message"]["content"]

def get_colqwen():
    global _colqwen
    if _colqwen is None:
        import torch
        from colpali_engine.models import ColQwen2_5, ColQwen2_5_Processor
        print("        loading ColQwen (" + COLQWEN_MODEL + ")")
        t_load = time.time()
        model = ColQwen2_5.from_pretrained(
            COLQWEN_MODEL, torch_dtype=torch.bfloat16, device_map="cuda").eval()
        proc = ColQwen2_5_Processor.from_pretrained(COLQWEN_MODEL)
        _colqwen = (model, proc)
        print("        ColQwen ready (" + fmt_dur(time.time() - t_load) + ")")
    return _colqwen


# ---------------------------------------------------------------------------
# I1 - tables, divided by rows with the header repeated
# ---------------------------------------------------------------------------
def split_table_markdown(md, budget=HARD_MAX):
    """A markdown table -> list of parts, each carrying the header rows."""
    lines = [l for l in md.split("\n") if l.strip()]
    if len(md) <= budget or len(lines) < 4:
        return [md]
    header = lines[:2]                      # header row + separator row
    body = lines[2:]
    parts, cur = [], list(header)
    hdr_len = sum(len(l) + 1 for l in header)
    cur_len = hdr_len
    for row in body:
        if cur_len + len(row) + 1 > budget and len(cur) > 2:
            parts.append("\n".join(cur))
            cur, cur_len = list(header), hdr_len
        cur.append(row)
        cur_len += len(row) + 1
    if len(cur) > 2:
        parts.append("\n".join(cur))
    return parts or [md]


# ---------------------------------------------------------------------------
# I6/I7 - subclause-boundary chunking with full breadcrumbs
# ---------------------------------------------------------------------------
def is_boundary(text):
    """True if this paragraph starts a new requirement unit, i.e. a place where
    cutting does NOT separate a requirement from its qualifying condition."""
    return bool(CLAUSE_RE.match(text) or ITEM_RE.match(text)
                or REQID_RE.match(text.strip()))


def chunk_document(doc, meta):
    """Walk Docling items in reading order and emit requirement-grained chunks.

    meta: {"doc_code", "revision", "acronyms"} - used for the I7 breadcrumb.
    """
    chunks, crumbs, buf, page = [], [], [], None
    clause = ""                                     # current numbered clause

    def breadcrumb():
        head = " > ".join(c for c in crumbs if c) or "(document)"
        bits = [b for b in (meta["doc_code"], meta["revision"]) if b]
        prefix = " ".join(bits)
        return ("%s | %s | %s" % (prefix, clause, head) if clause
                else "%s | %s" % (prefix, head))

    def flush(etype="text", cut="section"):
        nonlocal buf, page
        if not buf:
            return
        body = "\n".join(buf).strip()
        if not body:
            buf = []
            return
        crumb = breadcrumb()
        chunks.append({"body": body,
                       "cut": cut,
                       "crumb": crumb,
                       "section": " > ".join(c for c in crumbs if c) or "(document)",
                       "clause": clause,
                       "page": page,
                       "etype": etype})
        buf = []

    for item, _level in doc.iterate_items():
        label = str(getattr(item, "label", ""))
        text = (getattr(item, "text", "") or "").strip()
        prov = getattr(item, "prov", [])
        item_page = prov[0].page_no if prov else None

        if label in ("section_header", "title"):
            flush()
            depth = getattr(item, "level", 1)
            crumbs = crumbs[:max(depth - 1, 0)] + [text]
            # R85: annex boundaries reset the label; other headings inherit
            clause = clause_for_heading(text, clause)
            page = item_page
            continue

        if label == "table":
            flush()
            try:
                md = item.export_to_markdown(doc)
            except TypeError:
                md = item.export_to_markdown()
            if md.strip():
                for part in split_table_markdown(md.strip()):
                    buf, page = [part], item_page
                    flush(etype="table")
            continue

        if not text:
            continue

        if page is None:
            page = item_page
        cur_len = sum(len(t) for t in buf)
        # I6: prefer a requirement boundary; fall back to a paragraph break once
        # past TARGET+SLACK (see the SLACK_CHARS note above); HARD_MAX last.
        structural = cur_len >= TARGET_CHARS and is_boundary(text)
        paragraph  = cur_len >= TARGET_CHARS + SLACK_CHARS
        if buf and (structural or paragraph or cur_len >= HARD_MAX):
            if cur_len >= MIN_CHARS:
                flush(cut="structural" if structural
                      else ("paragraph" if paragraph else "hard_max"))
        c = clause_of(text, is_heading=False)       # body text: dotted only
        if c:
            clause = c
        buf.append(text)

    flush()
    return chunks


# ---------------------------------------------------------------------------
# I3 - definitions and abbreviations as individual units
# ---------------------------------------------------------------------------
def definition_units(raw_text, meta):
    """One chunk per defined term and per abbreviation.

    Measured reason: glossary entries ranked 9th for their own term because one
    enormous document's entries competed with each other.
    """
    units = []
    lines = raw_text.split("\n")
    # defined terms: a "3.2.14 annular ring" heading followed by its body
    i = 0
    while i < len(lines):
        m = DEFTERM_RE.match(lines[i])
        if m:
            term = m.group(1).strip()
            body = []
            j = i + 1
            while j < len(lines) and not DEFTERM_RE.match(lines[j]) \
                    and not re.match(r'^\s*[45]\s+\S', lines[j]):
                if lines[j].strip():
                    body.append(lines[j].strip())
                if sum(len(b) for b in body) > 1200:
                    break
                j += 1
            if body:
                units.append({"body": "%s\n%s" % (term, "\n".join(body)),
                              "cut": "definition",
                              "crumb": "%s %s | definition | %s"
                                       % (meta["doc_code"], meta["revision"], term),
                              "section": "Terms and definitions",
                              "clause": lines[i].split()[0],
                              "page": None, "etype": "definition"})
            i = j
            continue
        i += 1
    # abbreviations: one point per row
    for short, expansion in meta["acronyms"].items():
        units.append({"body": "%s - %s" % (short, expansion),
                      "cut": "definition",
                      "crumb": "%s %s | abbreviated terms | %s"
                               % (meta["doc_code"], meta["revision"], short),
                      "section": "Abbreviated terms",
                      "clause": "3.3", "page": None, "etype": "abbreviation"})
    return units


# ---------------------------------------------------------------------------
def ingest_file(path, source, digest):
    rec = {"pages": 0, "chunks": 0, "definitions": 0, "abbreviations": 0,
           "acronyms": 0, "expanded_chunks": 0,
           "tables": 0, "at_hard_max": 0, "parse_s": 0.0, "visual_s": 0.0,
           "embed_s": 0.0}
    t = time.time()
    print("  [1/4] parsing with Docling ...")
    doc = converter.convert(path).document

    # Clause-3 passes need LAYOUT-PRESERVING text - see layout_text().
    raw_text, raw_src = layout_text(path)
    if raw_text:
        raw_text = dehyphenate(raw_text)
    else:
        try:
            raw_text = dehyphenate(doc.export_to_text())
            raw_src = "docling-collapsed"
        except Exception:
            raw_src = "none"
    print("        clause-3 text source: %s" % raw_src)

    # ECSS handbooks and technical memoranda are NEVER normative (design 4.2),
    # so a corpus-wide --authority normative must not silently mislabel one.
    per_file = dict(SRC)
    _code = doc_code_of(source)
    if per_file["source_class"] == "standard" and ("-HB-" in _code or "-TM-" in _code):
        per_file["authority"] = "informative"
        per_file["source_class"] = "handbook"
        print("        authority override: %s is a handbook/TM -> informative"
              % _code)

    meta = {"doc_code": doc_code_of(source) or os.path.basename(source),
            "revision": revision_of(source),
            "acronyms": harvest_acronyms(raw_text)}
    print("        acronyms harvested: %d" % len(meta["acronyms"]))
    # An ECSS standard with no acronym table is almost always a parse failure,
    # not a document without acronyms. Say so rather than proceed quietly.
    if not meta["acronyms"] and _code and "-ST-" in _code:
        print("        WARNING: an ECSS standard yielded ZERO acronyms. I9 "
              "(dual payload) is inactive for this document. Text source was "
              "'%s'; expected 'sibling-layout-txt' or 'pdftotext-on-the-fly'."
              % raw_src)

    chunks = chunk_document(doc, meta)
    units = definition_units(raw_text, meta)
    rec["acronyms"] = len(meta["acronyms"])
    rec["definitions"] = sum(1 for u in units if u["etype"] == "definition")
    rec["abbreviations"] = sum(1 for u in units if u["etype"] == "abbreviation")
    chunks += units

    rec["parse_s"] = round(time.time() - t, 1)
    rec["chunks"] = len(chunks)
    rec["tables"] = sum(1 for c in chunks if c["etype"] == "table")
    rec["at_hard_max"] = sum(1 for c in chunks if len(c["body"]) >= HARD_MAX - 50)
    rec["cut_structural"] = sum(1 for c in chunks if c.get("cut") == "structural")
    rec["cut_paragraph"] = sum(1 for c in chunks if c.get("cut") == "paragraph")
    rec["cut_hard_max"] = sum(1 for c in chunks if c.get("cut") == "hard_max")
    print("        chunks: %d (tables %d, definitions %d, abbreviations %d) "
          "| revision: %s" % (len(chunks), rec["tables"], rec["definitions"],
                              rec["abbreviations"], meta["revision"] or "(none)"))
    print("        at hard max: %d (%.0f%%) - target is near zero"
          % (rec["at_hard_max"], 100.0 * rec["at_hard_max"] / max(len(chunks), 1)))
    print("        cuts: structural %d | paragraph %d | hard-max %d"
          % (rec["cut_structural"], rec["cut_paragraph"], rec["cut_hard_max"]))

    t = time.time()
    if path.lower().endswith(".pdf") and (OPT["captions"] or OPT["pages"]):
        from pdf2image import convert_from_path
        print("        rendering pages to images (poppler) ...")
        pages = convert_from_path(path, dpi=PDF_DPI)
        rec["pages"] = len(pages)
        print("  [2/4] visual pass: captions=%s pages=%s over %d pages"
              % (OPT["captions"], OPT["pages"], len(pages)))
        if OPT["pages"]:
            import torch
            model, proc = get_colqwen()
        for n, img in enumerate(pages, start=1):
            if n % 10 == 0 or n == len(pages):
                print("        page %d/%d" % (n, len(pages)))
            if OPT["captions"]:
                cap = usable_caption(caption(img))
                rec["captions_seen"] = rec.get("captions_seen", 0) + 1
                if cap and chunks:
                    rec["captions_kept"] = rec.get("captions_kept", 0) + 1
                    near = min((c for c in chunks if c["page"] is not None),
                               key=lambda c: abs(c["page"] - n), default=chunks[0])
                    near["body"] += "\n[FIGURES p" + str(n) + "] " + cap
            if OPT["pages"]:
                import torch
                with torch.no_grad():
                    mv = model(**proc.process_images([img]).to("cuda"))[0]
                qc.upsert(PAGE_COLL, [models.PointStruct(
                    id=point_id(source, "page" + str(n)),
                    vector=mv.cpu().float().tolist(),
                    payload={"source_file": source, "page_number": n,
                             "doc_sha256": digest,
                             "document_revision": meta["revision"],
                             "element_type": "page"})])
    else:
        print("  [2/4] visual pass: skipped")
    rec["visual_s"] = round(time.time() - t, 1)

    t = time.time()
    print("  [3/4] embedding %d chunks (dense%s) ..."
          % (len(chunks), " + sparse" if OPT["sparse"] else ""))
    seen_bodies = Counter()          # R86: disambiguate verbatim repeats
    for i, c in enumerate(chunks):
        # I7: the breadcrumb leads the text that is EMBEDDED, not only shown.
        display = "SECTION: %s\n%s" % (c["crumb"], c["body"])
        # I9: dual payload - acronyms expanded inline for the embedding only.
        _exp = expand_acronyms(c["body"], meta["acronyms"])
        if _exp != c["body"]:
            rec["expanded_chunks"] += 1
        embedded = "SECTION: %s\n%s" % (c["crumb"], _exp)
        refs = sorted({r for r in REF_RE.findall(c["body"])
                       if r != meta["doc_code"]})        # I4
        vectors = {"dense": embed(embedded)}
        sv = sparse_vector(embedded) if OPT["sparse"] else None
        if sv:
            vectors["sparse"] = models.SparseVector(indices=sv[0], values=sv[1])
        qc.upsert(TEXT_COLL, [models.PointStruct(
            id=content_point_id(source, c["body"],
                                seen_bodies[c["body"]]), vector=vectors,
            payload={"source_file": source,
                     # --- authority model (v3.1): what STANDING this text has
                     "authority": per_file["authority"],
                     "source_class": per_file["source_class"],
                     "applies_to": per_file["applies_to"],
                     "tailors": per_file["tailors"],
                     "doc_code": meta["doc_code"],
                     "document_revision": meta["revision"],
                     "page_number": c["page"],
                     "section": c["section"],
                     "clause": c["clause"],
                     "crumb": c["crumb"],
                     "element_type": c["etype"],
                     # (v3.2) WHY this chunk ended: structural | paragraph |
                     # hard_max | definition. Requirement I6's own output. A
                     # consumer cannot reconstruct it from n_chars - see the
                     # header note.
                     "cut": c["cut"],
                     "refs": refs,
                     "req_ids": sorted(set(REQID_RE.findall(c["body"]))),
                     "modals": sorted({m.lower() for m in
                                       MODAL_RE.findall(c["body"])}),
                     "n_chars": len(c["body"]),
                     "text": display,
                     "text_expanded": embedded})])
        seen_bodies[c["body"]] += 1
    rec["embed_s"] = round(time.time() - t, 1)
    print("  [4/4] %d chunks upserted into %s" % (len(chunks), TEXT_COLL))
    return rec


def lib_versions():
    from importlib.metadata import version, PackageNotFoundError
    out = {}
    for pkg in ("docling", "colpali-engine", "qdrant-client", "torch",
                "pdf2image", "transformers", "FlagEmbedding"):
        try:
            out[pkg] = version(pkg)
        except PackageNotFoundError:
            out[pkg] = None
    return out


def save_ingest_config():
    cfg = {"ingest_version": INGEST_VERSION,
           "authority_model": dict(SRC),
           "written": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
           "python": sys.version.split()[0],
           "target_chars": TARGET_CHARS, "hard_max": HARD_MAX,
           "min_chars": MIN_CHARS,
           "chunking": "subclause-boundary (I6), paragraph fallback past "
                       "TARGET+SLACK, hard cut at HARD_MAX",
           "slack_chars": SLACK_CHARS,
           "breadcrumb_embedded": True,
           "acronym_dual_payload": True,
           "sparse_backend": _sparse_backend,
           # (R87, 2026-08-18) WHICH SCHEMES BUILT THIS INDEX. Without these
           # two fields, a collection built before and after the 2026-08-18
           # rebuild is indistinguishable from its config alone - and they are
           # the fields that decide whether a stored point_id or a stored
           # anchor still resolves.
           "point_id_scheme": "content-v4 (R86): uuid5(source#v4#sha1(body)#n)"
                              " - independent of chunk position",
           "clause_label_scheme": "annex-aware (R85): a heading that declares"
                                  " no clause number inherits, EXCEPT an annex"
                                  " heading or an annex-numbered heading,"
                                  " which resets the label",
           "docling_ocr": OPT["ocr"],
           "options": dict(OPT),
           "pdf_render_dpi": PDF_DPI,
           "embed_model": EMBED_MODEL,
           "caption_model": CAPTION_MODEL,
           "colqwen_model": COLQWEN_MODEL if OPT["pages"] else None,
           "collections": {"text": TEXT_COLL,
                           "pages": PAGE_COLL if OPT["pages"] else None},
           "versions": lib_versions()}
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)
    print("processing config recorded to " + CONFIG_PATH)


def collect(paths):
    files = []
    for p in paths:
        if os.path.isdir(p):
            for root, _dirs, names in os.walk(p):
                files += [os.path.join(root, n) for n in sorted(names)
                          if n.lower().endswith(SUPPORTED)]
        else:
            files.append(p)
    return files


def selftest():
    """Behavioural assertions for the PURE parts of the ingester.

    Rule 3 says every tool has one. This one did not, and it acquired R86's
    change to the point id with nothing testing it. Only the pure functions
    are covered here - anything needing Docling, an embedder or Qdrant is out
    of scope and is NOT faked into a passing assertion.
    """
    fails, ran = [], [0]

    def ck(name, cond):
        ran[0] += 1
        print("  %-72s %s" % (name, "ok" if cond else "FAIL"))
        if not cond:
            fails.append(name)

    src = open(os.path.abspath(__file__)).read()
    B = "The supplier shall demonstrate compliance."

    # --- R86: the content id -------------------------------------------
    a = content_point_id("/c/D.pdf", B, 0)
    ck("R86 the point id is STABLE for the same body",
       a == content_point_id("/c/D.pdf", B, 0))
    ck("R86 a different body gives a different id",
       a != content_point_id("/c/D.pdf", B + " x", 0))
    ck("R86 a different source document gives a different id",
       a != content_point_id("/c/E.pdf", B, 0))
    ck("R86 a verbatim REPEAT does not collide with the first copy",
       a != content_point_id("/c/D.pdf", B, 1))
    ck("R86 the id does NOT depend on the chunk's position - that is the "
       "whole point",
       "index" not in content_point_id.__code__.co_varnames)
    ck("R86 the id does NOT key on clause or crumb, which R85 changes",
       "clause" not in content_point_id.__code__.co_varnames
       and "crumb" not in content_point_id.__code__.co_varnames
       and "deliberately not the clause" in src)
    ck("R86 the id is a valid UUID",
       bool(uuid.UUID(a)))
    ck("R86 the positional id is retained ONLY for the page collection, and "
       "says so",
       "POSITIONAL id - v3" in src and "page collection" in src
       and 'point_id(source, "page"' in src)
    ck("R86 the text chunk upsert uses the CONTENT id",
       "id=content_point_id(source, c[" in src)
    ck("R86 repeats are counted so the occurrence is real, not always 0",
       "seen_bodies = Counter()" in src and "seen_bodies[c[" in src)

    ck("R87 the config records WHICH point-id and clause-label schemes built "
       "the index",
       '"point_id_scheme"' in src and '"clause_label_scheme"' in src
       and "content-v4 (R86)" in src and "annex-aware (R85)" in src)

    # --- caption filtering. Every REJECT string below was produced by the
    # captioner during the first 12 documents of the R89 rebuild; none is
    # invented. -----------------------------------------------------------
    for bad in ("none", "None.", "  none  ", "NONE", "n/a",
                "There are no figures or diagrams present on this page.",
                "There are no figures or diagrams present on this page. The "
                "content is purely textual, presenting a table that outlines "
                "the Technology Readiness Level (TRL) summary.",
                "The page does not contain any figures or diagrams.",
                "This page contains no figures; it is only text."):
        ck("a NEGATIVE caption is not indexed: %r" % bad[:44],
           usable_caption(bad) is None)
    for good in ("The page contains Figure 6-4, which is a diagram "
                 "illustrating project phases and the generalized commercial "
                 "prime programme expectation of TRA outcome.",
                 "Figure 7-1 shows the SCET wire format: Fine Time occupies "
                 "octets 1 to 3 and Coarse Time occupies octets 4 to 7."):
        ck("a REAL caption IS indexed: %r" % good[:44],
           usable_caption(good) == good)
    ck("the filter cannot reject everything - it passes a real description",
       usable_caption("Figure 5-29 is a state machine with ten states "
                      "including ClearLine and Connected.") is not None)
    ck("an empty or whitespace caption yields nothing",
       usable_caption("") is None and usable_caption("   ") is None
       and usable_caption(None) is None)
    ck("a caption too short to describe anything is rejected",
       usable_caption("A diagram.") is None
       and MIN_CAPTION_CHARS == 25)
    ck("the prompt asks for a BARE token and forbids explaining the absence",
       "single word NONE" in CAPTION_PROMPT
       and "Do not explain that there are none" in CAPTION_PROMPT)
    ck("the guard exists SEPARATELY from the prompt - a prompt is a request, "
       "a guard is a guarantee",
       "a prompt is a request and a guard is a guarantee" in src
       and "usable_caption(caption(img))" in src)
    ck("the measured contamination that motivated this is recorded",
       "548 of them (91%)" in src)
    ck("kept and seen caption counts are recorded so the rate is reportable",
       'rec["captions_kept"]' in src and 'rec["captions_seen"]' in src)

    # --- R21: pre-2008 ECSS filenames -----------------------------------
    ck("R21 a modern filename still parses as it always did",
       doc_code_of("ECSS-E-ST-40C_Rev.1(3March2009).pdf") == "ECSS-E-ST-40"
       and revision_of("ECSS-E-ST-40C_Rev.1(3March2009).pdf") == "C Rev.1")
    ck("R21 the pre-2008 form ECSS-M-70A now yields a code and a revision",
       doc_code_of("ECSS-M-70A(19April1996).pdf") == "ECSS-M-70"
       and revision_of("ECSS-M-70A(19April1996).pdf") == "A")
    ck("R21 ECSS-P-00C-Rev.1 yields its revision too",
       doc_code_of("ECSS-P-00C-Rev.1(15November2024).pdf") == "ECSS-P-00"
       and revision_of("ECSS-P-00C-Rev.1(15November2024).pdf") == "C Rev.1")
    ck("R21 a filename with NO revision letter still returns empty, not a "
       "guess",
       revision_of("ECSS-Q-ST-30-09(31July2008).pdf") == "")
    ck("R21 the whole filename no longer becomes the doc_code",
       doc_code_of("ECSS-M-70A(19April1996).pdf")
       != "ECSS-M-70A(19April1996).pdf")
    ck("R21 reading the revision from the FILENAME is named as a limitation",
       "NOT from the document" in src and "R21" in src)

    # --- clause parsing -------------------------------------------------
    ck("a dotted clause number is recognised in body text",
       clause_of("5.11.5.6 Software validation", False) == "5.11.5.6")
    ck("a bare clause number is recognised ONLY in a heading",
       clause_of("7 Requirement traceability", True) == "7"
       and clause_of("7 Requirement traceability", False) is None)
    # --- R85: the clause label no longer sticks across an annex ---------
    ck("R85 an Annex heading RESETS the label instead of inheriting 5.11.5.6",
       clause_for_heading("Annex A (informative) Software documentation",
                          "5.11.5.6") == "A")
    ck("R85 an annex-numbered sub-heading takes its own label",
       clause_for_heading("Q.3.1 PDR/SWRR", "5.11.5.6") == "Q.3.1"
       and clause_for_heading("R.2 Tailoring", "5.11.5.6") == "R.2"
       and clause_for_heading("H.1.1 Requirement identification",
                              "5.11.5.6") == "H.1.1")
    ck("R85 a real clause heading still wins",
       clause_for_heading("5.4 Software validation", "9.9") == "5.4"
       and clause_for_heading("7 Requirement traceability", "9.9") == "7")
    ck("R85 a PLAIN sub-heading still INHERITS - blanking it would lose real "
       "information",
       clause_for_heading("Software validation specification task "
                          "identification", "5.4") == "5.4")
    ck("R85 the fix does not fire on ordinary prose-like headings",
       clause_for_heading("NOTE 1 The state diagram", "5.4") == "5.4"
       and clause_for_heading("General", "5.4") == "5.4")
    ck("R85 the sticky-label defect and its measured size are recorded",
       "475 of its" in src and "312 distinct section" in src)
    _code = "\n".join(l for l in src.splitlines()
                      if not l.lstrip().startswith("#"))
    ck("R85 the ingest loop calls the new resolver, not the old inherit "
       "(checked in CODE, not in the comment that documents it)",
       "clause = clause_for_heading(text, clause)" in _code
       and ("clause = c if c else " + "clause") not in _code)

    ck("a heading that declares no clause returns None, not the last one",
       clause_of("Annex A (informative) Software documentation", True) is None
       and clause_of("Q.3.1 PDR/SWRR", True) is None)

    print("\n  %d assertions, %d failed" % (ran[0], len(fails)))
    return 1 if fails else 0


def main():
    global TEXT_COLL
    if "--self-test" in sys.argv[1:]:
        sys.exit(selftest())
    args = []
    it = iter(sys.argv[1:])
    for a in it:
        if a == "--with-pages":
            OPT["pages"] = True
        elif a == "--no-captions":
            OPT["captions"] = False
        elif a == "--no-sparse":
            OPT["sparse"] = False
        elif a == "--ocr":
            OPT["ocr"] = True
        elif a == "--force":
            OPT["force"] = True
        elif a == "--collection":
            TEXT_COLL = next(it)
        elif a == "--authority":
            SRC["authority"] = next(it)
        elif a == "--source-class":
            SRC["source_class"] = next(it)
        elif a == "--applies-to":
            SRC["applies_to"] = next(it)
        elif a == "--tailors":
            SRC["tailors"] = [x.strip() for x in next(it).split(",") if x.strip()]
        else:
            args.append(a)
    if not args:
        print("usage: python ingest.py [--with-pages] [--no-captions] "
              "[--no-sparse] [--collection NAME] [--force]")
        print("                        [--authority A] [--source-class C] "
              "[--applies-to P] [--tailors A,B] <path>...")
        print("       python ingest.py --remove <file>... | --list")
        return
    # Validate rather than let a typo become a payload value nothing filters on.
    if SRC["authority"] not in AUTHORITY_VALUES:
        print("ABORT - --authority must be one of: " + ", ".join(AUTHORITY_VALUES))
        return
    if SRC["source_class"] not in SOURCE_CLASS_VALUES:
        print("ABORT - --source-class must be one of: "
              + ", ".join(SOURCE_CLASS_VALUES))
        return

    # (v3.3) MUST happen after --collection is parsed, or the ledger for the
    # default collection decides what gets skipped for a different one.
    global MANIFEST, CONFIG_PATH
    MANIFEST, CONFIG_PATH = ledger_paths(TEXT_COLL)
    print("ledger           : %s" % MANIFEST)
    if not os.path.exists(MANIFEST):
        print("                   (none yet - every document will be ingested)")

    manifest = load_manifest()
    if args[0] == "--list":
        for src in sorted(manifest):
            print("baseline:", src, manifest[src][:12])
        print(str(len(manifest)) + " documents in the manifest")
        return

    print("target collection: %s   (p42_text from campaign 1 is untouched)"
          % TEXT_COLL)
    print("authority        : %s | %s | applies_to=%s | tailors=%s"
          % (SRC["authority"], SRC["source_class"],
             SRC["applies_to"] or "(none)", SRC["tailors"] or "(none)"))
    init_sparse()
    global converter
    converter = make_converter()
    ensure_collections()

    if args[0] == "--remove":
        for p in args[1:]:
            src = os.path.abspath(p)
            delete_points(src)
            manifest.pop(src, None)
            save_manifest(manifest)
            print("remove:", src)
        return

    def up(url, name, hint):
        try:
            requests.get(url, timeout=5)
            print("  service OK : " + name)
            return True
        except Exception:
            print("  service DOWN: %s (%s) - %s" % (name, url, hint))
            return False
    print("service preflight:")
    ok = up(QDRANT + "/collections", "Qdrant :6333", "restart per 2.1.2.3")
    ok = up(EMBED + "/health", "BGE-M3 embeddings :8080",
            "stays up in UPDATE mode - restart per 2.1.2.2") and ok
    if OPT["captions"]:
        ok = up(VL + "/v1/models", "VL captioner :8002",
                "docker start vllm-vl; allow 1-2 min for model load") and ok
    if not ok:
        print("ABORT - nothing was ingested. Fix the DOWN service(s), then "
              "re-run the SAME command (the manifest makes re-runs safe).")
        return

    files = collect(args)
    print("corpus scan: %d file(s) to consider" % len(files))
    done_n = skip_n = err_n = 0
    file_recs = []
    for idx, f in enumerate(files, start=1):
        src = os.path.abspath(f)
        try:
            digest = sha256_of(src)
            if manifest.get(src) == digest and not OPT["force"]:
                print("[%d/%d] skip   : %s (unchanged)" % (idx, len(files), src))
                skip_n += 1
                continue
            action = "update" if src in manifest else "ingest"
            print("[%d/%d] %-7s: %s" % (idx, len(files), action, src))
            t_file = time.time()
            if action == "update":
                delete_points(src)
            rec = ingest_file(src, src, digest)
            manifest[src] = digest
            save_manifest(manifest)
            done_n += 1
            rec.update(file=os.path.basename(src), action=action,
                       total_s=round(time.time() - t_file, 1))
            file_recs.append(rec)
            print("  file time: " + fmt_dur(time.time() - t_file))
        except Exception as e:
            err_n += 1
            print("  ERROR:", src, "-", repr(e))
    print()
    print("SUMMARY  ingested/updated: %d | skipped: %d | errors: %d"
          % (done_n, skip_n, err_n))
    if file_recs:
        tot_chunks = sum(r["chunks"] for r in file_recs)
        tot_cap = sum(r["at_hard_max"] for r in file_recs)
        print("INGESTION QUALITY (gate 4 inputs):")
        print("  chunks              : %d" % tot_chunks)
        print("  at hard max         : %d (%.1f%%)  [v2.7 measured 27%% at cap]"
              % (tot_cap, 100.0 * tot_cap / max(tot_chunks, 1)))
        print("  tables              : %d" % sum(r["tables"] for r in file_recs))
        print("  definition units    : %d" % sum(r["definitions"] for r in file_recs))
        print("  abbreviation units  : %d" % sum(r["abbreviations"] for r in file_recs))
        _noac = [r["file"] for r in file_recs if r.get("acronyms", 0) == 0]
        print("  acronyms harvested  : %d across %d documents"
              % (sum(r.get("acronyms", 0) for r in file_recs), len(file_recs)))
        print("  chunks acronym-expanded (I9): %d (%.0f%%)"
              % (sum(r.get("expanded_chunks", 0) for r in file_recs),
                 100.0 * sum(r.get("expanded_chunks", 0) for r in file_recs)
                 / max(tot_chunks, 1)))
        if _noac:
            print("  DOCUMENTS WITH NO ACRONYM TABLE (%d) - check these:" % len(_noac))
            for fn in _noac[:12]:
                print("    " + fn)
    if done_n:
        save_ingest_config()
    if file_recs:
        run_rec = {"end": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                   "ingest_version": INGEST_VERSION,
                   "collection": TEXT_COLL,
                   "ingested": done_n, "skipped": skip_n, "errors": err_n,
                   "pages": sum(r["pages"] for r in file_recs),
                   "chunks": sum(r["chunks"] for r in file_recs),
                   "files": file_recs}
        with open(os.path.expanduser("~/p42/ingest-runs.jsonl"), "a") as f:
            f.write(json.dumps(run_rec) + "\n")
        print("metrics appended to ~/p42/ingest-runs.jsonl")


_t0 = time.time()
banner("ingest.py %s -- Project 42 KB batch ingestion (Campaign 2)"
       % INGEST_VERSION,
       "START " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
try:
    main()
finally:
    print()
    banner("ingest.py | END " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
           + " | DURATION " + fmt_dur(time.time() - _t0))
