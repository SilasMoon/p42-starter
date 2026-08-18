# Setting up a second box (spark2) to run the pipeline

**Version 1.0 — 18 August 2026.** What to install on a fresh DGX Spark so the knowledge base
pipeline runs. Read `P42_Starter_Kit.md` first for what any of this is.

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

Then check the tools before using them — this is a project rule, not a formality:

```bash
./ingest-venv/bin/python ingest_v3.py --self-test          # 45 assertions
./ingest-venv/bin/python retrieval_recall.py --self-test   # 30
./ingest-venv/bin/python span_specificity.py --self-test   # 26
```

**If any assertion fails, stop and report it.** A failing self-test on a fresh box is
information about the box, and we want it.

---

## Step 3 — the five services

Start them once; afterwards the mode scripts start and stop them for you.

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
| ingestion fails rendering pages | `poppler-utils` not installed |
| `Connection refused` on 8000 | you are in update mode, not serving mode |
| `Connection refused` on 8080 | you are in serving mode, not update mode |
| a container exits immediately | out of unified memory — check `--gpu-memory-utilization`, and that the other mode's containers are stopped |
| a self-test fails on a fresh box | **report it, do not work around it** |

The last row is the important one.
