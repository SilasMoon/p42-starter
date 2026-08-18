#!/usr/bin/env bash
# kb-mode-serve.sh — switch the Spark-1 KB from UPDATE mode back to SERVING mode.
# Effect: ingestion is stopped, the serving stack comes back, the KB is ONLINE
# again for users (end of the maintenance window; now at document baseline N+1).
# Output style (v4.36): numbered [n/6] step headers + one status line per
# container, NO colour codes — build-log copy-paste stays clean.
set -u   # unset variables are errors; no -e, same idempotent-ish reasoning as
         # in kb-mode-update.sh - a re-run must never abort halfway

BAR="============================================================"
SUB="------------------------------------------------------------"
step() { echo; echo "[$1/6] $2"; echo "$SUB"; }

# Root guard (v4.36): the drop_caches write and the systemd start need root.
if [ "$(id -u)" -ne 0 ]; then
    echo "kb-mode-serve.sh must run as root - use: sudo /opt/p42/bin/kb-mode-serve.sh"
    exit 1
fi

# Timing (v4.32): EXIT trap prints END/DURATION on every exit path.
SCRIPT_START=$(date +%s)
echo "$BAR"
echo " kb-mode-serve.sh -- KB: UPDATE -> SERVING (KB comes back ONLINE)"
echo " START $(date '+%Y-%m-%d %H:%M:%S')"
echo "$BAR"
finish() {
    local DUR=$(( $(date +%s) - SCRIPT_START ))
    echo
    echo "$BAR"
    echo " kb-mode-serve.sh | END $(date '+%Y-%m-%d %H:%M:%S') | DURATION $((DUR/60))m $((DUR%60))s"
    echo "$BAR"
}
trap finish EXIT

# start_c / stop_c: act on one container BY NAME and report exactly what
# happened; a never-created name points at the 2.1.1 Step 1 error decode
# instead of a raw docker error.
start_c() {
    if docker ps --format '{{.Names}}' | grep -qx "$1"; then
        echo "  - $1 : already running"
    elif docker ps -a --format '{{.Names}}' | grep -qx "$1"; then
        docker start "$1" >/dev/null 2>&1 && echo "  - $1 : started" || echo "  - $1 : START FAILED (check: docker logs $1)"
    else
        echo "  - $1 : NOT CREATED (2.1.1 Step 1 error decode) - create it via its 2.1.2/2.1.3 step"
    fi
}
stop_c() {
    if docker ps --format '{{.Names}}' | grep -qx "$1"; then
        docker stop "$1" >/dev/null 2>&1 && echo "  - $1 : stopped" || echo "  - $1 : STOP FAILED (check: docker logs $1)"
    elif docker ps -a --format '{{.Names}}' | grep -qx "$1"; then
        echo "  - $1 : already stopped"
    else
        echo "  - $1 : not created yet - skipped"
    fi
}

step 1 "Check for foreground ingestion jobs"
# 'docker stop' below only touches containers - Docling and ColQwen2.5 run as
# foreground Python jobs in a venv, which docker cannot see. 'pgrep -f' looks
# for them by name; if found, the operator decides: terminate or abort.
if pgrep -f "docling|colpali" > /dev/null; then
    echo "  WARNING: foreground ingestion processes detected!"
    pgrep -fl "docling|colpali"   # -l lists them with their command lines
    read -r -p "  Terminate them and continue? (y/N): " STOP_INGEST
    if [[ "$STOP_INGEST" =~ ^[Yy]$ ]]; then
        pkill -f "docling|colpali"
        echo "  terminated"
    else
        echo "  Aborting mode switch - let the ingestion finish first."
        exit 1
    fi
else
    echo "  none running"
fi

step 2 "Stop the ingestion containers"
stop_c vllm-vl                    # the Qwen2.5-VL captioning container (:8002)

step 3 "Verify the GPU memory is released (eyeball the table)"
nvidia-smi

step 4 "Drop the page cache before the big serving load (§1.7 habit)"
sync; echo 3 > /proc/sys/vm/drop_caches
echo "  page cache dropped"

step 5 "Start the serving stack, in order"
start_c qdrant                    # vector DB first (usually already up - it never stopped)
# Answer LLM - engine-aware (v4.6): the vLLM route is a container, the
# llama.cpp route is a systemd service or a hand-started process. Try each.
if docker ps -a --format '{{.Names}}' | grep -q '^vllm-llm$'; then
    start_c vllm-llm                                    # vLLM container route
elif systemctl list-unit-files | grep -q 'llama-server.service'; then
    systemctl start llama-server.service >/dev/null 2>&1 \
        && echo "  - llama-server.service : started (llama.cpp route, port 8001)" \
        || echo "  - llama-server.service : START FAILED (journalctl -u llama-server)"
else
    echo "  - answer LLM : NEITHER vllm-llm container NOR llama-server.service found -"
    echo "                 start your answer-LLM engine by hand before users return."
fi
start_c vllm-embed                # BGE-M3 embeddings
start_c reranker                  # bge-reranker-v2-m3
start_c open-webui                # the KB user interface, last

step 6 "Readiness probes (the two user-facing doors)"
# 'curl -sf' fails (non-zero) on any HTTP error, so a dead endpoint is caught
# here and not by the first user. A model server is not ready the instant its
# container starts. (v4.47) MEASURED LIVE on spark-9d0e: the 32B NVFP4 answer
# model takes ~4 MINUTES to become ready (weight load + CUDA graph capture) -
# the old 90 s window declared WARN on a perfectly healthy start. Window is
# now 8 minutes with a progress line every 30 s.
MAX_WAIT=480     # seconds - ~2x the measured ~4 min, so slow days still pass
WAITED=0
echo "  :8000 answer LLM   waiting (model load takes ~4 min here; timeout ${MAX_WAIT}s)"
until curl -sf http://localhost:8000/v1/models >/dev/null 2>&1 || [ $WAITED -ge $MAX_WAIT ]; do
    sleep 5
    WAITED=$((WAITED+5))
    if [ $((WAITED % 30)) -eq 0 ]; then echo "      ... ${WAITED}s elapsed, still loading"; fi
done
if curl -sf http://localhost:8000/v1/models >/dev/null 2>&1; then
    echo "  :8000 answer LLM   READY (after ~${WAITED}s)"
else
    echo "  :8000 answer LLM   WARN - not answering after ${MAX_WAIT}s; check 'docker logs vllm-llm' (or the llama-server logs) before announcing the KB back"
fi
curl -sf http://localhost:3000 >/dev/null \
    && echo "  :3000 Open WebUI   READY" \
    || echo "  :3000 Open WebUI   WARN - not answering; check the open-webui container"

echo
echo "SERVING mode - KB back online (announce end of maintenance window)."
