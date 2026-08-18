# Setting up a second box (spark2) to run the pipeline

**Version 1.0 — 18 August 2026.** Every command needed to take a fresh DGX Spark to a working
pipeline that answers a question.

**This is document 2 of 3.** Read `P42_Starter_Kit.md` first — it explains what a chunk, an
index, a reranker and a mode are, and this guide assumes all of that. When you finish here, go
to `P42_External_Experiment_Protocol.md` and start at Task 0.

The long-form runbook is `DGX_Spark_Setup_Runbook.md` (base OS, drivers, Docker, GPU checks).
**This document is the short path**: the specific things the pipeline needs, and nothing else.

---

## The shape of it

The pipeline is not one program. It is a small Python program that talks to **five services**,
each in its own Docker container:

| service | container | what it does | port |
|---|---|---|---|
| vector database | `qdrant` | stores the 35,166 chunks and their vectors | 6333 |
| embedding model | `vllm-embed` | turns text into vectors (`BAAI/bge-m3`) | 8080 |
| reranker | `reranker` | re-sorts the top 50 candidates (`BAAI/bge-reranker-v2-m3`) | 8081 |
| answer model | `vllm-llm` | writes the answer (`nvidia/Qwen3-32B-NVFP4`) | 8000 |
| figure captioner | `vllm-vl` | describes diagrams (`nvidia/Qwen2.5-VL-7B-Instruct-NVFP4`) | 8002 |

**They do not all fit in memory at once.** A Spark has one pool of unified memory shared
between CPU and GPU, and these models together exceed it. So the box runs in one of **two
modes**, and you switch between them:

- **serving mode** — answer model + reranker up. This is what you need to *ask questions*.
- **update mode** — embedder + captioner up. This is what you need to *load documents*.

`qdrant` stays up in both. The scripts in `ops/` do the switching (see below).

---

## What must already be done to the machine, before this guide starts

This guide assumes the box has been prepared by whoever administers it, following
`DGX_Spark_Setup_Runbook.md`. The split below is deliberate: everything in the first list is
**system-level, one-off, or proves the hardware works**, and none of it should be discovered as
a failure by the person trying to build an index.

**Administrator does, before handover:**

| runbook | why it cannot wait |
|---|---|
| §1.0 recovery dongle | physical, and it must be *tested*. If the box ever bricks this is the only way back |
| §1.1 first boot & system check | physical setup |
| §1.2 OS update, **driver pin**, firmware decision | see the warning below — this one is not optional |
| §1.3 Docker + NVIDIA container toolkit | **Step 1 of this guide assumes it.** Without it every container command fails |
| §1.5 smoke test — does the box serve a model? | proves driver, container stack and GPU work *end to end* before anyone else touches it |
| §1.7 Step 1, one-time memory protections | system-level settings |

> **The driver pin is a correctness matter, not housekeeping.** §1.2 Step 5 pins the driver at
> **580.x** (`sudo apt-mark hold nvidia-driver-580-open`) because the 590 series has three
> documented regressions on GB10 — a memory leak, a deadlock, and **data corruption**. Our
> reference box runs **580.173.02**. If the two machines run different drivers, a difference in
> results may be the driver rather than the change being tested — which defeats the purpose of
> Task 0. Record the version and check it matches.

**Left for the person using the box** — these are personal, and belong in their own account:

- **§1.2.a workstation tools** (browser, terminal, markdown editor). Set these up yourself, with
  your own logins.
- **§1.7 the rest** — the memory habits and the early-warning signals. Read them; they are about
  how not to wedge the machine.

**Not needed for this work:**

- **§1.4 uv and the Hugging Face CLI.** This guide uses plain `python3 -m venv`, and the models
  are pulled by the vLLM containers, so the HF CLI is not required.
- **§1.6 recording both machines' IPs.** Only relevant if two Sparks need to talk to each other.
  They do not, for this.

**Do not stop the preparation at §1.2.** The first command in Step 1 below is a
GPU-in-container test, which is §1.3 — if that has not been done, this guide fails on its first
instruction.

---

## Step 0 — the account, and the two groups it must be in

**Use a personal account.** Not for technical isolation — for the ordinary reason that the
person using the box will sign in to their own GitHub, mail and browser, and those belong in
their own home directory rather than in a shared login. The setup cost is nil: everything in
this guide is written relative to the home directory (`~/p42`), so it works under any username
with no changes.

Be clear about what it does and does not give you. It separates **files and credentials**. It
does not give a second working environment, because the things that matter most here are
**machine-wide, not per-user**:

- **Docker containers** are not namespaced by user. If two accounts each run
  `docker run --name qdrant`, the second fails on a name collision.
- **The GPU and its memory** are one shared pool. Only one mode's models fit at a time, so two
  people cannot serve and ingest simultaneously.
- **Ports** 6333 / 8000 / 8002 / 8080 / 8081 are one set per machine.

So if two people use the box, the sharing has to be by agreement — one person holds it in one
mode at a time — and a separate login does not change that. The containers, and therefore the
index, are shared no matter who is logged in.

Note also that anyone with `sudo` can read any other account's files, so the separation is
about tidiness and avoiding accidents, not about enforcement.

### Whichever account is used, it needs two group memberships

```bash
sudo usermod -aG docker <username>     # run containers without sudo
sudo usermod -aG sudo   <username>     # apt, and the mode scripts
# log out and back in for the groups to take effect
```

Check they took:

```bash
id                 # expect 'docker' and 'sudo' in the group list
docker ps          # must work WITHOUT sudo
```

**Both are genuinely required, not conveniences.** Without `docker` every container command
fails with a permission error. Without `sudo` the mode scripts refuse to run at all — they need
root to drop caches and start services — which means the box cannot be switched between serving
and update mode, and nothing in this guide past Step 3 is possible.

> **Note for whoever administers the box:** granting `sudo` is effectively granting full control
> of the machine. That is a trust decision rather than a technical one, but there is no partial
> version that still works — mode switching is root-only by design.

### Disk

Not a constraint. The model cache is about 4.3 GB and Docker images about 66 GB; a Spark ships
with several terabytes. If two accounts each keep their own `hf-cache`, the duplication is
irrelevant — do not complicate the setup to avoid it.

---

## Step 1 — system packages

```bash
sudo apt update
sudo apt install -y python3-venv poppler-utils
```

`poppler-utils` provides `pdftoppm`, which renders PDF pages to images. **Ingestion fails
without it** and the error is not obvious, so install it now.

Docker and the NVIDIA container toolkit are covered in `DGX_Spark_Setup_Runbook.md` §1.3.
Verify both before continuing:

```bash
docker run --rm --gpus all nvcr.io/nvidia/vllm:26.07-py3 nvidia-smi
```

If that prints a GPU table, the container stack works.

---

## Step 2 — the Python environment

```bash
git clone git@github.com:SilasMoon/p42-starter.git ~/p42
cd ~/p42
python3 -m venv ingest-venv
./ingest-venv/bin/python -m ensurepip
./ingest-venv/bin/python -m pip install -r requirements-ingest.txt
```

---

## Step 2a — run every self-test and SEND THE RESULT before going further

Every tool here carries named behavioural checks that must pass before it is used. On a fresh
machine they are also a test of *the machine*: if something passes on our box and fails on
yours, that difference is real information — about a library version, a driver, a locale — and
we want it **now**, not after you have spent three hours building an index on top of it.

Save this as `check.sh` in `~/p42` and run it:

```bash
#!/bin/bash
{
echo "P42 self-test sweep"
echo "host   : $(hostname)"
echo "date   : $(date -Is)"
echo "python : $(./ingest-venv/bin/python -V 2>&1)"
echo "---"
fail=0
for t in ingest_v3 pipelines pipeline_ask_v2 retrieval_recall span_specificity \
         anchor_migrate label_coverage benchmark claim_judge figure_probe \
         sparse_build; do
  [ -f "$t.py" ] || { printf '%-20s NOT IN BUNDLE\n' "$t"; continue; }
  out=$(./ingest-venv/bin/python "$t.py" --self-test 2>&1)
  sum=$(printf '%s' "$out" | grep -oE '[0-9]+ assertions, [0-9]+ failed' | tail -1)
  nfail=$(printf '%s' "$out" | grep -cE 'FAIL[[:space:]]*$')
  if [ -n "$sum" ]; then printf '%-20s %s\n' "$t" "$sum"
  elif [ "$nfail" -eq 0 ]; then printf '%-20s ok (%s checks)\n' "$t" "$(printf '%s' "$out" | grep -c ' ok$')"
  else printf '%-20s %s FAILING CHECKS\n' "$t" "$nfail"; fi
  [ "$nfail" -gt 0 ] && fail=$((fail+1))
done
echo "---"
echo "tools with failures: $fail"
} > "selftest-$(hostname).txt" 2>&1
cat "selftest-$(hostname).txt"
```

```bash
chmod +x check.sh && ./check.sh
```

**Send `selftest-<hostname>.txt` to Geoffray before you continue.** These are the numbers it
produces on our box on 18 August 2026:

```
ingest_v3            45 assertions, 0 failed
pipelines            21 assertions, 0 failed
pipeline_ask_v2      13 assertions, 0 failed
retrieval_recall     30 assertions, 0 failed
span_specificity     26 assertions, 0 failed
anchor_migrate       18 assertions, 0 failed
label_coverage       24 assertions, 0 failed
benchmark            70 assertions, 0 failed
claim_judge          32 assertions, 0 failed
figure_probe         20 assertions, 0 failed
sparse_build         ok (6 checks)
---
tools with failures: 0
```

**Any difference at all is worth reporting** — a different assertion count, a failure, or a
tool that will not start. Do not work around it and do not "fix" it locally; a self-test that
disagrees between two machines is telling you something about one of them, and finding out
which is cheaper now than later.

(Note the script matches `FAIL` only at the end of a line. Two assertions have the word
"FAILS" in their *names* — counting those as failures is exactly the kind of check-the-word-
not-the-condition mistake this project keeps a register of.)

---

## Step 3 — the five services

**Check whether they already exist before creating anything:**

```bash
docker ps -a --format '{{.Names}}\t{{.Status}}'
```

Docker containers belong to the **machine, not to your account**. If someone has already set
this box up under a different login, the containers are already there and any user in the
`docker` group can use them. In that case **skip the `docker run` commands below entirely** and
just start what you need:

```bash
docker start qdrant vllm-embed vllm-vl        # update mode
docker start qdrant vllm-llm reranker         # serving mode
```

Re-running `docker run` against an existing name fails with *"name is already in use"*. That is
the container telling you it already exists, not an error to work around — never delete and
recreate one to get past it, because the `qdrant` container holds the index.

If `docker ps -a` comes back empty, create them once. Afterwards the mode scripts start and
stop them for you.

```bash
# the vector database — stays up in both modes
docker run -d --name qdrant --restart unless-stopped \
  -p 6333:6333 -v ~/qdrant_storage:/qdrant/storage qdrant/qdrant:latest

# embedding model (update mode)
docker run -d --name vllm-embed --gpus all -p 8080:8000 \
  -v ~/p42/hf-cache:/root/.cache/huggingface nvcr.io/nvidia/vllm:26.07-py3 \
  vllm serve BAAI/bge-m3 --runner pooling --gpu-memory-utilization 0.15

# figure captioner (update mode)
docker run -d --name vllm-vl --gpus all -p 8002:8000 \
  -v ~/p42/hf-cache:/root/.cache/huggingface nvcr.io/nvidia/vllm:26.07-py3 \
  vllm serve nvidia/Qwen2.5-VL-7B-Instruct-NVFP4 --gpu-memory-utilization 0.3

# answer model (serving mode)
docker run -d --name vllm-llm --gpus all -p 8000:8000 \
  -v ~/p42/hf-cache:/root/.cache/huggingface nvcr.io/nvidia/vllm:26.07-py3 \
  vllm serve nvidia/Qwen3-32B-NVFP4 --gpu-memory-utilization 0.55

# reranker (serving mode)
docker run -d --name reranker --gpus all -p 8081:80 \
  -v ~/p42/hf-cache:/data \
  ddosify/text-embeddings-inference:blackwell-1.8.3-baai-bge-reranker-v2-m3 \
  --model-id BAAI/bge-reranker-v2-m3
```

**First start of each downloads model weights — tens of GB in total, and slow.** Do it on a
good connection and expect to wait. The `hf-cache` volume means it happens once.

The `--gpu-memory-utilization` numbers are not decoration: they are what lets the right
combination coexist. **Do not raise them** to make something load faster; you will make the
other service in that mode fail instead.

---

## Step 4 — the mode scripts

```bash
sudo mkdir -p /opt/p42/bin
sudo cp ~/p42/ops/kb-mode-serve.sh ~/p42/ops/kb-mode-update.sh ~/p42/ops/kb-boot.sh /opt/p42/bin/
sudo chmod +x /opt/p42/bin/*.sh
```

Then:

```bash
sudo /opt/p42/bin/kb-mode-serve.sh     # ready to ANSWER questions
sudo /opt/p42/bin/kb-mode-update.sh    # ready to LOAD documents
```

**How to tell which mode you are in:** in serving mode `curl localhost:8000/v1/models` answers;
in update mode it does not, and `curl localhost:8080/health` does instead.

---

## Step 5 — the documents

The 145 ECSS PDFs are **not in the repository** — they are third-party standards. Download them
from [ecss.nl](https://ecss.nl) into `~/p42/corpus/pdf/`, then verify you have exactly the same
corpus we do:

```bash
cd ~/p42
awk -F'\t' 'NR>5{print $2"  corpus/pdf/"$1}' corpus/CORPUS_MANIFEST.tsv | sha256sum -c
```

Every line must say `OK`. **If any file differs, stop** — a different corpus means none of your
numbers can be compared with ours, and that is the whole point of the exercise.

---

## Step 6 — build the index

```bash
sudo /opt/p42/bin/kb-mode-update.sh
cd ~/p42
./ingest-venv/bin/python ingest_v3.py --self-test
./ingest-venv/bin/python ingest_v3.py --collection p42_text_v4 corpus/pdf/
```

**This takes about 3 hours** for 145 documents with figure captioning on. Expect
`chunks: 35166` at the end, and `errors: 0`.

Then build the keyword half of the search, which needs a second environment because the
library conflicts with the first:

```bash
python3 -m venv sparse-venv
./sparse-venv/bin/python -m ensurepip
./sparse-venv/bin/python -m pip install -r requirements-sparse.txt
./sparse-venv/bin/python sparse_build.py --self-test
./sparse-venv/bin/python sparse_build.py --source p42_text_v4 --target p42_text_v4_bgelex
```

That copies the meaning-vectors and rebuilds only the keyword half — about four minutes, not
another three hours.

---

## Step 7 — ask it a question

```bash
sudo /opt/p42/bin/kb-mode-serve.sh
cd ~/p42
P42_COLL=p42_text_v4_bgelex ./ingest-venv/bin/python -c "
import pipelines
r = pipelines.ask('pipeline_ask_v2', 'What does ECSS-Q-ST-60-13 require for the procurement of EEE components?')
print(r['status'], '| context', r['n_context'], 'of', r['n_retrieved'])
print(r['answer'][:400])
"
```

If that returns a cited answer, **the full pipeline works on your box.**

---

## What you can and cannot do with this bundle

**You can:** load documents, build indexes, ask questions, and run every retrieval measurement
(`retrieval_recall.py`, `span_specificity.py`, `anchor_migrate.py`, `label_coverage.py`). That
covers Tasks 0, 1, 2 and 4 of the experiment protocol — including the highest-value one.

**You cannot, yet:** reproduce our published answer-quality scores. That needs our run records,
which are deliberately not in this bundle — see the note in `P42_Starter_Kit.md` section 9, and
ask before you need them.

---

## If something does not work

| symptom | cause |
|---|---|
| `permission denied` on any docker command | the account is not in the `docker` group (Step 0) |
| `must run as root` from a mode script | the account is not in the `sudo` group (Step 0) |
| `name is already in use by container` | the container already exists — `docker start <name>`, do not re-run `docker run` |
| ingestion fails rendering pages | `poppler-utils` not installed |
| `Connection refused` on 8000 | you are in update mode, not serving mode |
| `Connection refused` on 8080 | you are in serving mode, not update mode |
| a container exits immediately | out of unified memory — check `--gpu-memory-utilization`, and that the other mode's containers are stopped |
| a self-test fails on a fresh box | **report it, do not work around it** |

The last row is the important one.

---

## When you have finished this guide

You should now have: a working environment, a self-test report sent back, the corpus verified
against our manifest, an index built as `p42_text_v4` and its keyword half as
`p42_text_v4_bgelex`, and a cited answer to a real question.

**Next: `P42_External_Experiment_Protocol.md`, and start at Task 0.**

Task 0 is not an experiment — it reproduces our published baseline on your machine and checks
that you get the same numbers. It is short, it needs no model calls, and everything you measure
afterwards depends on it. The protocol explains why, and gives you the figures to match.
