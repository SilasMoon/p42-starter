#!/usr/bin/env bash
# kb-mode-update.sh — switch the Spark-1 KB from SERVING mode to UPDATE mode.
# Effect: KB goes OFFLINE for users; the serving stack is stopped (Qdrant stays up);
# the whole memory pool is freed for the ingestion pipeline (2.1.3).
# Output style (v4.36): numbered [n/5] step headers + one status line per
# container, NO colour codes — so a copy-paste into the build log stays clean.
set -u   # treat unset variables as errors; we do NOT use -e, so a stop on an
         # already-stopped container cannot abort the switch halfway (idempotent-ish)

BAR="============================================================"
SUB="------------------------------------------------------------"
step() { echo; echo "[$1/6] $2"; echo "$SUB"; }

# Root guard (v4.36): docker may work for a docker-group user, but the
# drop_caches write in step 5 needs root — refuse early, not fail late.
if [ "$(id -u)" -ne 0 ]; then
    echo "kb-mode-update.sh must run as root - use: sudo /opt/p42/bin/kb-mode-update.sh"
    exit 1
fi

# start_c (v4.54): start one container BY NAME with a clear status line -
# same helper as kb-mode-serve.sh.
start_c() {
    if docker ps --format '{{.Names}}' | grep -qx "$1"; then
        echo "  - $1 : already running"
    elif docker ps -a --format '{{.Names}}' | grep -qx "$1"; then
        docker start "$1" >/dev/null 2>&1 && echo "  - $1 : started" || echo "  - $1 : START FAILED (check: docker logs $1)"
    else
        echo "  - $1 : NOT CREATED - create it via 2.1.3.2 before ingesting PDFs"
    fi
}

# Timing (v4.32): the EXIT trap prints END/DURATION on every exit path,
# success or abort — 'date +%s' is seconds since 1970, for the arithmetic.
SCRIPT_START=$(date +%s)
echo "$BAR"
echo " kb-mode-update.sh -- KB: SERVING -> UPDATE (KB goes OFFLINE)"
echo " START $(date '+%Y-%m-%d %H:%M:%S')"
echo "$BAR"
finish() {
    local DUR=$(( $(date +%s) - SCRIPT_START ))
    echo
    echo "$BAR"
    echo " kb-mode-update.sh | END $(date '+%Y-%m-%d %H:%M:%S') | DURATION $((DUR/60))m $((DUR%60))s"
    echo "$BAR"
}
trap finish EXIT

# stop_c: stop one container BY NAME and report exactly what happened —
# running -> stopped; stopped -> "already stopped"; never created -> a
# pointer at the 2.1.1 Step 1 error decode instead of a raw docker error.
stop_c() {
    if docker ps --format '{{.Names}}' | grep -qx "$1"; then
        docker stop "$1" >/dev/null 2>&1 && echo "  - $1 : stopped" || echo "  - $1 : STOP FAILED (check: docker logs $1)"
    elif docker ps -a --format '{{.Names}}' | grep -qx "$1"; then
        echo "  - $1 : already stopped"
    else
        echo "  - $1 : not created yet (2.1.1 Step 1 error decode) - skipped"
    fi
}

step 1 "Confirm the maintenance window"
# The KB must only go down inside an ANNOUNCED maintenance window (see §2.1.1
# "The two modes"). This prompt forces the operator to confirm that.
echo "This switches the KB to UPDATE mode: OFFLINE for all users."
read -r -p "Has the maintenance window been announced to users? Type YES to continue: " ANSWER
if [ "$ANSWER" != "YES" ]; then echo "Aborted - announce the window first."; exit 1; fi
echo "  confirmed"

step 2 "Snapshot Qdrant (mandatory rollback point)"
# A full snapshot via Qdrant's REST API, BEFORE anything else changes. If the
# ingestion goes bad, we restore this snapshot instead of debugging live data.
# (Per-collection form: curl -X POST http://localhost:6333/collections/<name>/snapshots)
curl -s -X POST http://localhost:6333/snapshots || { echo "  SNAPSHOT FAILED - is Qdrant up? NOT switching modes."; exit 1; }
echo   # newline after curl's JSON output
echo "  snapshot OK (this is baseline N, the rollback point)"

step 3 "Stop the serving stack (qdrant + vllm-embed stay UP)"
# NOTE (v4.16): vllm-embed is deliberately NOT stopped - ingestion needs BGE-M3
# to embed the new chunks, and using the SAME embedding service for indexing and
# for later queries is what keeps retrieval consistent (a different embedder at
# ingestion time would silently break search). Qdrant stays up to receive vectors.
stop_c vllm-llm                          # answer LLM, vLLM container route
if pgrep -x llama-server >/dev/null 2>&1; then
    pkill llama-server && echo "  - llama-server : stopped"   # llama.cpp route
else
    echo "  - llama-server : not running"
fi
stop_c reranker                          # bge-reranker-v2-m3
stop_c open-webui                        # the KB user interface - users now see it gone

step 4 "Verify the GPU memory is released (eyeball the table)"
# No serving processes should remain. If something still holds memory, stop
# it before starting ingestion (§1.7: the pool is shared).
nvidia-smi

step 5 "Drop the page cache (§1.7 pre-load habit)"
# 'sync' flushes pending disk writes; writing 3 to drop_caches releases the
# Linux page cache so the ingestion models load into a clean pool.
sync; echo 3 > /proc/sys/vm/drop_caches
echo "  page cache dropped"

step 6 "Start the ingestion-side services AND wait until they answer"
# (v4.54, hit live TWICE) kb-mode-serve.sh stops vllm-vl on the way back to
# SERVING - so every new UPDATE window used to begin with a dead captioner
# on :8002, and the ingest batch failed file after file. Entering UPDATE
# mode now BRINGS UP what ingestion needs, symmetrically with the teardown.
# (v4.55, per PoC-lead) ...and WAITS until each service actually answers,
# instead of leaving the readiness gamble to the operator: a started
# container is not a ready model server (measured on this box: minutes).
start_c vllm-embed                # BGE-M3 (:8080) - normally already up, but
                                  # an UPDATE window entered straight after a
                                  # boot would otherwise miss it
start_c vllm-vl                   # Qwen2.5-VL captioning (:8002)

wait_ready() {   # $1=url  $2=label  $3=timeout seconds - probe every 5 s,
                 # progress line every 30 s; WARN (not abort) on timeout,
                 # because ingest.py's own preflight is the hard gate.
    local WAITED=0
    echo "  $2 waiting (timeout ${3}s)"
    until curl -sf "$1" >/dev/null 2>&1 || [ $WAITED -ge $3 ]; do
        sleep 5; WAITED=$((WAITED+5))
        if [ $((WAITED % 30)) -eq 0 ]; then echo "      ... ${WAITED}s elapsed, still loading"; fi
    done
    if curl -sf "$1" >/dev/null 2>&1; then
        echo "  $2 READY (after ~${WAITED}s)"
    else
        echo "  $2 WARN - not answering after ${3}s; check 'docker logs' before ingesting"
    fi
}
wait_ready http://localhost:8080/health    "BGE-M3 :8080      " 240
wait_ready http://localhost:8002/v1/models "VL captioner :8002" 480

echo
echo "UPDATE mode - run ingestion now (2.1.3). When done: /opt/p42/bin/kb-mode-serve.sh"
