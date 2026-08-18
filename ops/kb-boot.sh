#!/usr/bin/env bash
# kb-boot.sh — bring the Spark-1 KB to SERVING mode after a FRESH BOOT.
# What a reboot leaves behind: every KB container still exists on disk but is
# STOPPED — none auto-start (deliberate: the operator decides whether the box
# comes up SERVING or stays down for an UPDATE window). This script is that
# one deliberate action. It first runs the host checks learned live in WP1
# (§1.5 post-reboot failure: containers started before the GPU driver and DNS
# were ready died with CUDA-compat and name-resolution errors), then hands
# over to kb-mode-serve.sh so the start sequence itself lives in ONE place.
# Usage: sudo /opt/p42/bin/kb-boot.sh   (after every power-on or reboot)
# Output style (v4.36): numbered [n/5] step headers, one clear verdict line
# per check, NO colour codes — build-log copy-paste stays clean.
set -u

BAR="============================================================"
SUB="------------------------------------------------------------"
step() { echo; echo "[$1/5] $2"; echo "$SUB"; }

# Root guard (v4.34): without root, 'swapoff' and 'systemctl restart docker'
# fail - and '|| true' would MASK the swapoff failure, so the script would
# print "swap OFF" while swap is still on. Refuse early instead.
if [ "$(id -u)" -ne 0 ]; then
    echo "kb-boot.sh must run as root - use: sudo /opt/p42/bin/kb-boot.sh"
    exit 1
fi

SCRIPT_START=$(date +%s)
echo "$BAR"
echo " kb-boot.sh -- fresh boot -> host checks -> SERVING mode"
echo " START $(date '+%Y-%m-%d %H:%M:%S')"
echo "$BAR"
finish() {
    local DUR=$(( $(date +%s) - SCRIPT_START ))
    echo
    echo "$BAR"
    echo " kb-boot.sh | END $(date '+%Y-%m-%d %H:%M:%S') | DURATION $((DUR/60))m $((DUR%60))s"
    echo "$BAR"
}
trap finish EXIT

step 1 "Wait for the Docker daemon"
# 'docker info' answers only when the daemon is actually ready to run
# containers. After a boot that can lag the login prompt by a while, so:
# probe every 3 s up to 20 times (~60 s), one dot per probe. If it is STILL
# down, restart the daemon once (the fix that worked live in §1.5) and only
# then give up.
echo -n "  probing "
TRIES=0
until docker info >/dev/null 2>&1 || [ $TRIES -eq 20 ]; do echo -n "."; sleep 3; ((TRIES++)); done; echo
if ! docker info >/dev/null 2>&1; then
    echo "  not answering - restarting the daemon once (the section-1.5 post-reboot fix)..."
    systemctl restart docker
    sleep 10
    docker info >/dev/null 2>&1 || { echo "  FATAL: Docker daemon still down - fix Docker before starting the KB."; exit 1; }
fi
echo "  docker daemon READY"

step 2 "Wait for the GPU driver"
# nvidia-smi answers only once the driver stack is fully initialised; a
# container that grabs the GPU before that point fails with CUDA errors.
echo -n "  probing "
TRIES=0
until nvidia-smi >/dev/null 2>&1 || [ $TRIES -eq 20 ]; do echo -n "."; sleep 3; ((TRIES++)); done; echo
nvidia-smi >/dev/null 2>&1 || { echo "  FATAL: nvidia-smi not answering - GPU driver not up; NOT starting the stack."; exit 1; }
echo "  GPU driver READY"

step 3 "Check DNS (name resolution)"
# The section-1.5 post-reboot failure included DNS errors inside containers.
# 'getent hosts' asks the system resolver the same way programs do. This is a
# WARNING, not a blocker: a stack serving from local caches (HF_HUB_OFFLINE)
# survives without DNS, but anything needing a download would fail.
if getent hosts nvcr.io >/dev/null 2>&1; then
    echo "  DNS READY"
else
    echo "  WARN: DNS not resolving (nvcr.io) - fine for offline serving, but downloads would fail."
fi

step 4 "Re-assert the section-1.7 memory discipline"
# swapoff is NOT persistent: swap comes back at every boot, and the standing
# policy is swap OFF in operation (swap on this box turns memory pressure
# into silent, machine-freezing thrash instead of a clean failure).
swapoff -a || true
echo "  swap OFF"

step 5 "Hand over to the SERVING-mode switch"
# Everything from here (cache drop, ordered container starts, engine-aware
# answer-LLM start, readiness probes, smoke checks) is kb-mode-serve.sh's
# job - called rather than copied, so the sequence is maintained in ONE file.
echo "  calling /opt/p42/bin/kb-mode-serve.sh ..."
/opt/p42/bin/kb-mode-serve.sh
