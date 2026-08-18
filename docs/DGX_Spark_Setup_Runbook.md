# Project 42 — DGX Spark Setup Runbook (WP1: Internet Shakedown Phase)

**Airbus — internal working draft.**

**Version:** v4.63 — EXECUTION EDITION &nbsp;|&nbsp; **Date:** 2026-08-13 &nbsp;|&nbsp; **Programme:** Project 42 — RFM AI Proof of Concept (Airbus UK)

> ### ⚠ Read before rebuilding a box from this runbook
>
> **This runbook builds CAMPAIGN 1.** Everything in §2.1 is correct and current for the campaign-1
> stack — `ingest.py` v2.7 → `p42_text`, 23 documents — and campaign 2 replaced most of it. This
> document contains **zero** mentions of `ingest_v3`, `retrieve.py`, `ask_v2.py`, `anchor_sampler.py`,
> `gate4_check.py`, `p42_text_v2` or `p42_text_v3`.
>
> **See §2.2 at the end of this document** for the campaign-2 artefact inventory, the rebuild command,
> and the two ingest defects that must not be reintroduced. §2.2 is an inventory, **not** a build
> procedure: transcribing the campaign-2 heredocs into this runbook is an open task.

> [!IMPORTANT]
> **How to use this execution edition.** This runbook is now a **fillable procedure**: every executable section ends with a **📋 STEP RECORD** block — tick it, initial it, date it, and write the values it asks for (versions, tags, measured numbers, anomalies). The completed records ARE the build log that the air-gap installation and the reset kit later depend on — an unticked or unvalued step is an incomplete step. Print one copy per machine or fill the markdown directly (one copy per machine: `buildlog-spark1.md`, `buildlog-spark2.md`). The **master progress checklist** below tracks the whole run at a glance.

**Master progress checklist** (tick as each section's STEP RECORD is completed):

| § | Step | Spark-1 | Spark-2 |
|---|---|---|---|
| [1.0](#10-recovery-dongle--create-it-and-test-it-before-anything-else-new-in-v10) | Recovery dongle created AND tested | ☐ | *(shared — one test reflash)* |
| [1.1](#11-first-boot--system-check) | First boot & system check (box state captured in build log) | ☐ | ☐ |
| [1.2](#12-os-update-driver-pin--firmware-decision-v20-step-format) | OS update, driver pinned 580.x, firmware policy read | ☐ | ☐ |
| [1.2.a](#12a-workstation-tools--browser-terminal-markdown-editor-new-in-v11) | Workstation tools (Chrome / Terminator+tmux / VS Code) + runbook copied on-box | ☐ | ☐ |
| [1.3](#13-docker--the-gpu-in-container-test-v20-step-format) | Docker + GPU-in-container test | ☐ | ☐ |
| [1.4](#14-python-tooling-uv--hugging-face-cli-v20-step-format) | Python tooling (uv) + Hugging Face CLI | ☐ | ☐ |
| [1.5](#15-smoke-test-does-the-box-serve-a-model-v20-step-format) | Serving smoke test (NGC vLLM) | ☐ | ☐ |
| [1.6](#16-record-both-ips-how-spark-2-reaches-spark-1-v20-step-format) | IPs recorded; Spark-2 → Spark-1 reachability TEST | ☐ | ☐ |
| [1.7](#17-unified-memory-discipline-v20-step-format--read-before-running-anything-big) | Memory discipline set up | ☐ | ☐ |
| [2.1](#21-knowledge-base-rag--do-this-first-most-detail-v40-step-format--single-spark-mode-exclusive) | KB track (2.1.1–2.1.5, entirely on Spark-1, mode-exclusive) + TESTs | ☐ | — |
| [2.2](#22-coding-assist-code-gen--review--unit-tests-v30-step-format) | Coding clients (Cline / aider / pi) | ☐ | — |
| [2.3](#23-autocomplete-fim--optional-defer-unless-a-ladder-asks-for-it-v30-step-format)–[2.7](#27-data--log-analysis-new-in-v02-v30-step-format) | Further Part B tracks attempted (each has its own STEP RECORD — list which were run) | ☐ | ☐ |
| [2.8](#28-optional-clustering-for-the-quality-ceiling-test-v30-step-format) (+[2.8.a](#28a-deepseek-v4-flash-cluster-serving--source-rebuild-route-aiden-recipe-class-new-in-v010-v30-step-format)) | Clustering experiment (if run) | ☐ (pair) | — |
| [2.9](#29-optional-unsloth-fine-tuning-feasibility-spike-new-in-v04-v30-step-format) | Unsloth fine-tune spike (if run) | — | ☐ |
| [2.10](#210-new-in-v013-kbagent-bridge-via-mcp--integration-spike-v30-step-format) | MCP p42-kb spike (if run) | ☐ | — |
| [C](#part-c--hardware-benchmark-protocol-wp13--new-in-v02) (+C.2) | Benchmark protocol + llama-benchy JSONs filed | ☐ | ☐ |
| [D](#part-d--familiarisation-sessions--discipline-sandboxes-wp14--new-in-v02) | Familiarisation sessions & sandboxes | ☐ (team) | — |
| [3.a.1](#3a1-chat-template--tool-calling-known-issues--per-model-fixes-new-in-v011) | Template smoke test per agent-facing model | ☐ | ☐ |
| [4](#4-wp1-exit-checklist-new-in-v02) | WP1 exit checklist signed | ☐ (project) | — |

**Applies to:** 2× NVIDIA DGX Spark (GB10 Grace-Blackwell, 128 GB unified memory, ARM64 / aarch64, DGX OS)
**Source of truth for commands:** `research_dgxspark_setup.md` (verified 2026-07-09), **re-verified against live official sources 2026-07-10** (v0.3 pass — see changelog). Where this runbook and the research note now differ, this runbook is current; the research note should be updated to match.
**Companion documents:** `Project42_PoC_Plan_Draft_A.docx` (WPs, gates, schedule) · `Project42_UseCase_Template_Draft_A.docx` · `Project42_MVP_Examples_Draft_A.docx` (worked examples + seed ladders) · `Project42_LLM_Model_Catalogue.md` v0.8 (model roles, plain language) · `Project42_DGXSpark_AirGap_Install_Runbook.md` v0.8 (the enclave rebuild this run feeds) · `Project42_GoldenImage_USB_Howto.md` v0.3 (recovery dongle + reset kit reference) · `Project42_Artifactory_Mirror_List.md` v0.13 (what IT must mirror).

**At a glance:**

| Part | What it covers | Produces (WP1 deliverable) |
|---|---|---|
| §0 | Ground rules · engine policy · track priorities | — |
| Part A (§1.0–1.7) | Recovery dongle · base setup on both machines · update/driver policy · memory discipline | Infrastructure readiness note |
| Part B (§2.1–2.10) | Per-capability-track setup + TEST (KB first) | Baseline stack description |
| Part C | Hardware benchmark protocol (canonical figures, spec-decode, concurrency) | Hardware benchmark memo |
| Part D | Familiarisation sessions & discipline sandboxes | Sessions held + sandboxes live |
| §3–§4 | Model matrix · ports · troubleshooting · verify + WP1 exit checklists | — |


---

## 0. Read me first

### 0.1 Where this runbook sits in Project 42

This runbook is the working procedure for **WP1 — Infrastructure setup and familiarisation (3 Aug – 11 Sep 2026)**; a **WP** ("work package") is one phase of the project plan, and the **PoC** ("proof of concept") is the whole pilot project this runbook belongs to. Its outputs are WP1's deliverables in the PoC plan:

| WP1 deliverable (plan) | Produced by |
|---|---|
| Infrastructure readiness note | Part A build log + §3.d verify checklist, §4 exit checklist |
| Baseline stack description with configuration | Part B — the proven recipe per capability track |
| Hardware benchmark memo | Part C — benchmark protocol results |
| Familiarisation sessions held | Part D — session plan + sandbox setup |

Timing matters: **the stack must be proven before G1 (MVP Agreement, w/c 14 Sep)** — G1/G2 are the project's "gates", the go/no-go decision points between phases — because *technical feasibility on the DGX Spark* is the top-weighted scoring criterion (25%) for selecting MVPs (an **MVP**, "minimum viable product", is one small pilot use case to be built in this PoC). Part C's measured numbers — not community figures — are what the scoring uses. Familiarisation (Part D) should land **before the ladder submission deadline (Fri 4 Sep)** so disciplines calibrate their ambitions on the real machines.

### 0.2 Scope — dirty / internet-connected shakedown ONLY

Both Sparks are freshly received, connected to the **open internet**, with **NO project data, NO Airbus network access, and NO controlled material of any kind on them**. The whole point of this phase is to work out the *software recipe* for each capability track using **public stand-in data only**, so that the real build can be reproduced cleanly later.

> [!IMPORTANT]
> **This is NOT the production build.** The clean, controlled rebuild happens later — on a controlled network (**air-gapped**: physically disconnected from the internet), with all artefacts transferred via controlled media (mirrored pip/apt, pre-pulled container images, pre-downloaded model **weights** — a model's weights are its learned numbers, the multi-GB files you download; "mirrored" means copied onto an approved internal server first) — and **before any real RFM data is loaded** (at the latest, before WP4 data ingestion; sequencing per the PoC plan and IT/Security). Nothing here that reaches out to the internet is representative of the final locked-down system — this phase only *discovers* the correct set of components and commands. Keep the build log complete enough that the production rebuild needs no internet-era guesswork.

### 0.3 Golden rules

1. **Commands drift.** The versions, tags, and flags below were verified 2026-07-09. Before you run an install, open the official doc linked in that step and reconcile. Where the research flags something unproven on this hardware, there is an explicit **VERIFY** callout — do not skip it.
2. **The ARM64 `:latest` trap.** DGX Spark is aarch64 (the ARM processor family — a different instruction set from the amd64 of ordinary Intel/AMD PCs, so software must be built specifically for it). A huge number of `:latest` tags on Docker Hub (the main public library of Docker container images — Docker itself is explained in §1.3) are **amd64-only**; pulling one and running it gives `exec format error`. For **every** non-NVIDIA image, before you wire it into anything:
   ```bash
   docker run --rm <image> uname -m      # --rm = delete the throwaway container after it exits; MUST print: aarch64
   ```
   Prefer **NGC images (`nvcr.io/...`)** and images with an explicit `linux/arm64` manifest (the manifest is an image's published list of supported processor types). When in doubt, use the NVIDIA-provided container.
3. **The Spark validates QUALITY, not speed.** Memory bandwidth (273 GB/s) dominates token generation — a **token** is the word-fragment unit (roughly three-quarters of an English word) in which models read and write text, and **tok/s** (tokens per second) is the speed unit used throughout this runbook. A 32B *dense* model may run at ~10 tok/s while a 30B-class *MoE* model runs several times faster (~30 tok/s plain serving; roughly double that with speculative decoding, a lossless speed-up technique explained in §0.6). **Dense** means every parameter of the model works on every token; **MoE** ("Mixture of Experts") means the model is split into many specialist sub-networks of which only a few activate per token — so it generates much faster than its size suggests (see Annex B). Slow is expected and is NOT a failure. We are proving that a given model/pipeline produces *correct, grounded* (backed by the supplied source material, not invented)*, usable* answers — not that it is fast. Latency numbers you see here are not representative of production hardware.
4. **Memory discipline or the box hangs.** (New in v0.4.) On unified memory, running out does NOT give a clean CUDA OOM (**OOM** = an "out of memory" error; **CUDA** = NVIDIA's GPU-computing software layer — see Annex B) — it hangs the whole machine (driver zombie state, SSH dead, physical reboot). Follow §1.7 before running anything big. Community reference: the "memory creep" and "zombie OOM" forum threads in the Know-How compendium.
5. **Log everything, from day one.** (New in v0.2.) Keep a dated **build log** per machine (every install, version, deviation from this runbook, and VERIFY outcome) — it becomes the infrastructure readiness note and the production-rebuild recipe. And leave **request/usage logging ON** in the serving layer — the programs that host the models and answer requests (vLLM, llama-server, Open WebUI; §0.6 introduces them) — (Open WebUI keeps chat history; vLLM/llama-server log requests): in WP5 the serving logs are the measurement instrument for benchmarking and ROI, so the habit and the configuration start now.

### 0.4 Role split (keep to this for day-to-day) (v4.0)

Since v4.0 the **KB** (knowledge base — the cited document question-answering system built in §2.1) is a **single-box system on Spark-1**, run in one of two mutually exclusive modes (§2.1 "The two modes"): SERVING (users get answers) or UPDATE (KB offline, **ingestion** — converting documents into the KB's searchable form, §2.1 — runs). Spark-2 no longer runs any part of the KB — it hosts the clients and experiments. In the table, an **LLM** ("large language model") is the AI text model itself; the "answer LLM" is the model that writes the KB's answers (the other components are explained at the top of §2.1 and in Annex B).

| Machine | Role | Runs |
|---|---|---|
| **Spark-1** | KB single-box (mode-exclusive serving/update) + serving endpoints | SERVING mode: answer LLM, embeddings, reranker, Qdrant, KB UI, coding-model endpoint. UPDATE mode (KB offline): Docling, VLM captioning, ColQwen page vectors → Qdrant on the same box |
| **Spark-2** | Clients / experimentation | Coding clients (§2.2) and benchmarks (Part C), data-analysis notebooks (§2.7), fine-tune spike (§2.9), experiments — reaches Spark-1's endpoints as a client; hot-spare option if Spark-1 is down |

Clustering the two together (§2.8) is a **one-off** quality-ceiling experiment, not the day-to-day topology.

**The whole WP1 architecture in one picture (v4.10):**

![Project 42 WP1 architecture — Spark-1 mode-exclusive KB, Spark-2 clients, internet sources](Project42_WP1_Architecture.png)

*Figure: the shakedown topology. Spark-1 runs the KB in exactly one mode at a time — SERVING (blue: Open WebUI :3000 → answer LLM :8000/:8001, embeddings :8080, reranker :8081) or UPDATE (amber: Docling → VL captioning :8002 → ColQwen, strictly sequential), with Qdrant :6333 up in both and the `kb-mode-*.sh` scripts as the only way to switch. Spark-2 (green) hosts the coding clients, notebooks and benchmarks, reaching Spark-1 over the OpenAI-compatible API. Everything red is the open internet — shakedown only; the enclave build replaces it with the Artifactory mirrors (see the Air-Gap Runbook and the JEDI connection request). The figure file `Project42_WP1_Architecture.png` sits alongside this document.* The topology decision (single-box KB vs the old 2-Spark split, which §2.1 keeps as a documented fallback) is confirmed at G2.

### 0.5 What each setup track de-risks (map to the MVP portfolio)

The MVP portfolio is decided at G1, so WP1 cannot know the final list — but the worked examples and seed ladders (`Project42_MVP_Examples_Draft_A.docx`) tell us which capability tracks the candidates draw on (a **ladder** is a discipline's stepped MVP proposal — rungs from simple to ambitious — submitted on the use-case template). Prioritise in this order:

| § | Capability track | Candidate MVPs it de-risks | Priority |
|---|---|---|---|
| 2.1 | Knowledge base / RAG with citations | UC-OPS-2 (worked example), UC-DB-1, UC-SE-2, parts of UC-FVI-1 | **1 — do first** |
| 2.4 | Repo-map code navigation & Q&A | UC-GNC-2 (worked example), UC-FSW-2 support | **2** |
| 2.5 | Grounded document drafting | UC-FV-2, UC-FVI-2, UC-SE-1, UC-FSW-3 | **3** |
| 2.7 | Data & log analysis (new) | UC-FV-1 (log triage), GNC Monte-Carlo triage, UC-DB-2 consistency checks | **4** |
| 2.2 | Coding assist (agent, diffs, unit tests) | UC-FSW-1/2 | 5 |
| 2.6 | CI agents (batch, sandboxed) | UC-FSW stretch options | optional |
| 2.3 | Autocomplete (FIM) | no current seed MVP needs it | optional — defer unless a ladder asks for it |
| 2.8 | Two-Spark clustering | quality-ceiling check for any track | one-off experiment |
| 2.9 | Unsloth fine-tuning spike | evidence for Rung-3/2027 fine-tune options | optional, 1–2 days |

If time in WP1 runs short, tracks 2.1 and 2.4 are the must-haves: they carry the two worked-example MVPs and the majority of the seed ladders.

### 0.6 Serving-engine policy (v0.5)

A **serving engine** is the program that loads a model into memory and answers requests to it over the network — every chat, agent and pipeline in this runbook talks to one. Engines are selected against three criteria, **in this order: 1) proven maturity (as per community experience on this hardware), 2) quality of outputs, 3) performance.** Everything in this runbook tests the baseline that wins on those criteria:

| Engine | Verdict | Rationale against the criteria |
|---|---|---|
| **vLLM (NGC container)** | **Baseline — measured, concurrent, NVFP4** | (1) The only engine NVIDIA packages and validates for the Spark in an NGC container, with an official playbook; industry-standard serving engine; also the target production engine of the AI strategy — using it in the PoC de-risks the scale-up. (2) Serves original safetensors weights incl. NVIDIA's verified NVFP4 matrix; explicit context/sampling control, no hidden defaults. (3) Best concurrency and NVFP4 throughput. |
| **llama.cpp** | **Baseline — single-user GGUF serving** | (1) The most battle-tested engine on this specific hardware: author-maintained canonical benchmark thread on GB10, community playbooks, open source, full flag control. (2) Explicit quantisation choice and explicit context size — nothing silent. (3) Fastest single-stream. |
| **LM Studio** | Excluded from baseline (optional, laptop-side only) | Officially supported on Spark (NVIDIA playbook; llama.cpp engine with CUDA 13, ARM64, headless API server) — but it is the *same engine* as our baseline under a closed-source GUI wrapper: it adds accessibility, not capability or quality; model/GUI management duplicates Open WebUI; closed-source freeware on the enclave box is an avoidable governance question. Fine for personal exploration on laptops. |
| **Ollama** | **Removed entirely (v0.5)** | Fails criterion 2 outright: silently truncates prompts to its small default context window (plausible-but-wrong answers — unacceptable where "no citation, no claim" applies) and auto-selects quantisations. Fails criterion 3 per community measurement (slowest of the engines; Docker image worst, a known cause of silent CPU inference). Its only asset was install convenience, which the NGC-container smoke test (§1.5) makes redundant. |

*Terms in the table, in plain language:* **NGC** is NVIDIA's official download service for containers and software. **Quantisation** stores a model's numbers at reduced precision to make it smaller and faster — **NVFP4**, **FP8** and **MXFP4** are 4- and 8-bit quantisation formats, and llama.cpp's **Q8_0/Q4**-style names are its quantisation levels. **GGUF** is llama.cpp's single-file model format; **safetensors** is the standard raw-weights format vLLM serves. A model's **context window** (or context length) is how much text, counted in tokens, it can consider at once — anything beyond it is invisible to the model. Annex B holds the full glossary of these and all other AI/serving terms.

One consequence worth stating: **every measured, demoed or user-facing token in this PoC comes from vLLM or llama.cpp with an explicitly recorded flag set.** No convenience wrappers in the serving path.

**(v4.3) Speculative-decoding policy — GATED DEFAULT.** Speculative decoding (a small, pinned "drafter" model proposes tokens the big model verifies — lossless by construction, typically 1.8–2.5× faster single-stream on this bandwidth-limited hardware) is the **required target profile for every primary interactive model in §3.a**. It is not enabled blind: each target model MUST be paired with its designated, repo-pinned drafter during that model's Part C measurement. **Gate:** acceptance rate (the share of the drafter's proposed tokens the big model accepts) ≥ 60 % AND a measured net decode speedup (no regression of **TTFT** — time-to-first-token, the wait before the answer starts appearing) AND a clean §3.a.1 template smoke test with the drafter active. Pass → the drafter is part of that model's recorded baseline flag set. Fail → fall back to non-speculative serving and log the deviation in the STEP RECORD. Until a model's gate has been run, its recipe serves non-speculative. **(v4.24)** For the DeepSeek-V4 family the tracked in-baseline route is **llama.cpp PR #25784** (DeepSeek-V4 MTP support — MTP is the model's built-in draft module; draft PR as of 2026-08-07, author-measured ~16.5 → 26–29 tok/s on a Spark, acceptance 0.651; https://github.com/ggml-org/llama.cpp/pull/25784) — with one drafter-gate caveat: **Unsloth's GGUF builds ship WITHOUT the MTP module**, so verify that the quant source actually carries it before running the gate.

### 0.7 Single best source

- **NVIDIA DGX Spark playbooks hub:** https://build.nvidia.com/spark
- **Mirror (GitHub, ~45 playbooks):** https://github.com/NVIDIA/dgx-spark-playbooks
- **DGX Spark User Guide:** https://docs.nvidia.com/dgx/dgx-spark/index.html

### 0.8 How to read this runbook (v2.0 — the step format)

**Step tags (v4.39):** every step title in §2.1 (and, progressively, the rest of the document) carries one bracketed tag immediately after the step number, answering "is this step for me?" before a single line is read: **[ALL]** = everyone runs it, always; **[DECISION]** = choose between named routes — no commands, and the step lists which later steps implement each route; **[ROUTE: X — alternative to Step N]** = run only if the named DECISION chose route X, skip otherwise; **[OPTIONAL]** = skippable extra the baseline never depends on. A route step always names the step(s) it replaces, so "alternative to WHAT?" is never implicit.

Every executable section is a sequence of **numbered steps**, and every step follows the same anatomy, in this order:

1. ☐ **Step N — what you are about to do** *(tick when done)*
2. **Why** — what this step achieves, in plain language.
3. **Before you run it** — everything you must know or decide FIRST. **All warnings and decision rules live here, before the commands — never after them.** If a step says "DECISION", do not type anything until you have worked through its rule.
4. **Run** — the exact commands.
5. **Expect / If not** — what success looks like, and what to do for each known failure.

**(v4.7) The placeholder convention:** anything printed in angle brackets — `<spark-1-ip>`, `<model.gguf>`, `<new-kernel-version>`, `⟨version⟩` — is a **placeholder**: replace the whole thing, brackets included, with your real value before running. Never type the brackets: the shell reads `<` and `>` as input/output redirection (Annex A.1), so a literally-typed placeholder produces confusing errors like `No such file or directory`. **(v4.22) The vLLM image in every example is written out concretely as `nvcr.io/nvidia/vllm:26.07-py3` — the tag validated by this project's §1.5 smoke test. If your smoke test pinned a different tag (the §1.5 fallback rule), substitute yours consistently everywhere.**

Two further rules of the format: **no prior Linux or infrastructure knowledge is assumed** — every technical term is explained at first use, **Annex A** explains every Linux command, and **Annex B** (new in v4.5) is the plain-language glossary of every AI and serving-stack concept — read A for commands, B for concepts; the two exist so that no step ever assumes prior knowledge. And each section still ends with its **📋 STEP RECORD** — fill it as you finish the section, not later. Every runnable command appears in its own grey command box — commands are never buried inline in prose. **(v4.17)** Two more standing rules of the format: every alert box (IMPORTANT / WARNING / CAUTION / NOTE / TIP) is written as a full explanation — the fact, why it matters here, and what to do about it, never a telegraphic fragment — and every command flag is explained in plain language at its first use in the document (as a `#` comment in the command box or a flag-rationale sentence beside it; later uses are not re-explained).

> [!NOTE]
> **Migration status:** Part A (§1.0–§1.7) **and** Part B (§2.1–§2.10) are fully in this format. Part C/D and the appendices (§3.x, §4, Annexes A/B) are reference material, not step sequences — the cautions-first rule applies there: read each of their CAUTION/IMPORTANT boxes in full before running any of their commands.

---

# Part A — Base setup (do once on BOTH machines)

Run Part A on Spark-1 **and** Spark-2. The two boxes are identical at this stage.

## 1.0 Recovery dongle — create it and TEST it before anything else (NEW in v1.0)

*What & why:* the day-one policy (§1.1 caution) has always said "create AND test the recovery USB before doing anything else" — these are the concrete steps, folded in from the Golden-Image USB How-To v0.3 §2 (which stays the full reference, including the P42-RESTORE side of the reset kit). The recovery dongle is the disaster floor: whatever gets broken later, this stick returns the machine to factory state. Testing it NOW, while the machines are empty, is free; discovering a bad stick after weeks of configuration is not.

> [!CAUTION]
> **Using the dongle — the three rules that prevent a bricked machine (read BEFORE building or testing a stick):** (1) the recovery **erases the entire internal disk** — it is a full reset, never a repair; (2) **NEVER power-cycle a Spark that looks stuck during recovery or any firmware operation** — if it seems frozen: unplug peripherals except the display, wait, retry — never the power; (3) wall power (original 240 W adapter) for the whole operation. After a recovery completes, the machine is at factory first-boot → re-enter this runbook at §1.1 (or hand the machine to the air-gap runbook / reset kit as appropriate).

**Steps:**

1. ☐ **Confirm the SKU** (the "stock-keeping unit" — the exact product variant of the hardware). Founders Edition → NVIDIA's procedure below. An OEM variant ("original equipment manufacturer" — the same hardware sold under another vendor's brand: Dell Pro Max GB10 / MSI EdgeXpert / ASUS GX10) → use that vendor's own recovery article and image instead; the rest of this section still applies in spirit. Record the SKU + serials.
2. ☐ **Download the recovery image** from NVIDIA's official recovery page (linked from the User Guide's System Recovery section; NOT the enterprise DGX OS ISO / Enterprise Download Center): `https://www.nvidia.com/en-us/drivers/dgx-spark-recovery-software/` — a `dgx-spark-recovery-image-⟨version⟩.tar.gz` archive (~5.5 GB; current at time of writing: 1.135.34, released 2026-05-31). Record the exact version and the archive's SHA-256 (a cryptographic **checksum** — a short fingerprint computed from the file; if it matches later, the copy is byte-for-byte identical to the original). *(Older copies of this runbook pointed at a developer.nvidia.com download path — the nvidia.com page above is the one NVIDIA's own docs now link to.)*
3. ☐ **Prepare 2× USB sticks ≥16 GB (32 GB recommended)** — both will be fully erased. One becomes the working stick, one the sealed spare.
4. ☐ **Build each stick:** extract the archive and run the script for your platform with admin rights: `CreateUSBKey.cmd` (Windows) / `CreateUSBKey.sh` (Linux) / `CreateUSBKeyMacOS.sh` (macOS).
   > [!TIP]
   > **The Windows script is known-broken on many machines.** If `CreateUSBKey.cmd` fails with the error `Set-Disk : Not Supported`, the script is at fault, not your USB stick — the fix is to prepare the stick by hand, which produces exactly what the script would have produced. Using Windows' built-in `diskpart` disk tool: create ONE primary **FAT32** partition on the stick and mark it **active** (i.e. bootable); copy the contents of the archive's `usbimg.customer\usb\` folder onto it; create a file `EFI\BOOT\recovery.txt` containing just the text `RECOVERY` (the marker file the recovery boot looks for); and set the volume label to `BOOTME`. A stick built this way boots identically to a script-built one.
5. ☐ **TEST the working stick with a full reflash of ONE machine — now, while it is still factory-fresh.** Procedure to boot from it (this is also the procedure any future reset uses):
   - Machine off → insert stick → power on **holding Esc (or Del)** → UEFI setup (**UEFI** is the machine's built-in boot firmware; this is its settings screen — §1.2 explains firmware fully).
   - Restore UEFI defaults; ensure **Secure Boot enabled with factory keys** (Secure Boot is the firmware feature that only boots cryptographically signed software; on some units, restoring the factory keys requires switching Secure Boot to *Custom* mode first, then restoring defaults); save & exit.
   - Re-enter UEFI → **Boot Override** → select the USB stick → follow the on-screen recovery prompts to completion.
6. ☐ **Label both sticks** (`P42-FACTORY-⟨image version⟩-⟨date⟩`), seal the spare, store per the media procedure.

**TEST:** the reflashed machine reaches the DGX OS first-boot wizard; both sticks labelled; version + SHA-256 recorded.

> **📋 STEP RECORD — §1.0** &nbsp;&nbsp; ☐ Done &nbsp; ☐ Deviation logged &nbsp; ☐ N/A (reason below)
> Machine: ☐ Spark-1 ☐ Spark-2 &nbsp;·&nbsp; Operator: `____________` &nbsp;·&nbsp; Date: `____________`
> Values recorded (versions / tags / measurements / anomalies): `________________________________________________`
>
> **Notes / observations / follow-ups** *(use as much of this space as needed)*:
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`

## 1.1 First boot & system check

*Goal of this section:* get the machine through NVIDIA's first-boot wizard safely, gain remote access, and capture a complete record of the machine's delivered state (the "birth certificate") before anything is changed.

☐ **Step 1 — Set up the hardware before applying power.**
**Why:** the unit powers on the instant wall power is applied — there is no separate power moment, so everything must be connected first.
**Before you run it:** §1.0 (recovery dongle, tested) must already be done — do not proceed without it. Use the **original 240 W power adapter and wall power** (no extension strips with switches, no USB-C hubs for power).
**Run:** connect monitor + keyboard + mouse, then apply power. *Headless alternative:* power on with no monitor — the Spark raises a Wi-Fi hotspot (network name and password are on the Quick Start sticker); connect a laptop to it and a setup page opens in the browser.
**Expect:** NVIDIA's first-boot wizard appears (on screen or in the laptop browser).

☐ **Step 2 — Let the first-boot wizard run to completion, untouched.**
**Why:** the wizard downloads and installs the full DGX OS software image.
**Before you run it:** this takes up to ~10 minutes and **the machine may reboot itself more than once — that is normal.** The critical rule (community-confirmed, machines have been permanently bricked): **NEVER remove power from a Spark that looks stuck during first boot or any firmware operation.** If it seems frozen: unplug every peripheral except the monitor cable (peripherals alone have caused boot loops), wait several minutes, retry — never the power.
**Run:** follow the wizard; create the local user account; note the credentials in the team password store.
**Expect:** a Ubuntu-style desktop. Reference docs: first boot https://docs.nvidia.com/dgx/dgx-spark/first-boot.html · DGX OS https://docs.nvidia.com/dgx/dgx-spark/dgx-os.html

☐ **Step 3 — Establish SSH access BEFORE touching anything else.**
**Why:** SSH ("secure shell") lets you operate the machine from another computer over the network; to connect you need the Spark's **IP address** (its numeric address on the local network). Several display/black-screen traps exist on this hardware; if the screen ever goes dark, SSH is your way back in — so it must exist *before* any experiment.
**Run (on the Spark):**
```bash
ip -4 addr show | grep inet      # -4 = IPv4 addresses only; note the machine's LAN IP address
```
**Run (from your laptop):**
```bash
ssh <username>@<that-ip>
```
**Expect:** a command prompt on the Spark, from the laptop. **If not:** confirm laptop and Spark are on the same network; on the Spark check the SSH service is running:
```bash
systemctl status ssh
```

☐ **Step 4 — Capture the box state (the birth certificate).**
**Why:** the air-gapped production rebuild must reproduce this machine exactly; it cannot discover any of these values later. The capture also proves the machine is what we think it is.
**Run** (paste as one block — it loops over every check, prints a `### <command>` banner between outputs, shows everything live, and saves it all to a dated per-machine file):

```bash
sudo bash -c 'export PATH="$PATH:/usr/local/cuda/bin"; OUT="/home/${SUDO_USER:-$USER}/p42/boxstate-$(hostname)-$(date +%F).txt"; mkdir -p "$(dirname "$OUT")"; { for CMD in "date -u" "hostname" "dmidecode -s system-manufacturer" "dmidecode -s system-product-name" "dmidecode -s system-serial-number" "nvidia-smi" "uname -m" "uname -a" "cat /etc/os-release" "lsb_release -a" "nvcc --version" "free -h" "head -n 20 /proc/meminfo" "df -h" "lsblk" "lscpu" "nproc" "docker version" "nvidia-ctk --version" "ls /etc/apt/sources.list.d/" "head -n 50 /etc/apt/sources.list.d/*"; do printf "\n\n============================================================\n### %s\n============================================================\n" "$CMD"; $CMD 2>&1; done; } | tee "$OUT"; chown "${SUDO_USER:-$USER}": "$OUT" 2>/dev/null; echo; echo "Box state saved to $OUT"'
```

*Flag gloss for the checks inside the block:* `date -u` = time in UTC; `dmidecode -s <keyword>` = print one specific hardware identification string; `uname -m` / `uname -a` = machine architecture / all kernel details; `free -h` and `df -h` = memory and disk sizes in human-readable units; `head -n 20` = first 20 lines only; `lsb_release -a` = all OS release details.

**What each section of the output means, and what to expect:**

| Section | Why / expected |
|---|---|
| `date -u` / `hostname` | timestamps the capture; identifies the machine |
| `dmidecode` ×3 | SKU confirmation (§1.0 step 1 — Founders Edition reports NVIDIA as manufacturer) + serial for the build log |
| `nvidia-smi` | GPU + driver + CUDA table (GB10 Blackwell). Memory line is *unified* — see NOTE below |
| `uname -m` / `uname -a` | **MUST print `aarch64`**; kernel version |
| `/etc/os-release` / `lsb_release -a` | DGX OS (Ubuntu 24.04 base) |
| `nvcc --version` | CUDA toolkit (preinstalled; the command's PATH export makes it visible under sudo) |
| `free -h` / `/proc/meminfo` | unified memory — expect ~128 GB total (shared CPU+GPU) |
| `df -h` / `lsblk` | disk layout (~4 TB NVMe) |
| `lscpu` / `nproc` | CPU — expect 20 cores (10× Cortex-X925 + 10× Cortex-A725) |
| `docker version` / `nvidia-ctk --version` | the preinstalled-versions record the VERIFY box below asks for |
| apt sources listing + contents | **RECORD verbatim** — the air-gapped production build reproduces these against the Artifactory mirrors and cannot discover them later |

**Expect / If not — the four hard gates:** `uname -m` MUST say `aarch64`, `free -h` MUST show ~128 GB, `nproc` MUST say 20, and `nvidia-smi` MUST show a GB10/Blackwell GPU with a 580-series driver. **If any of these four fails, STOP — the box is not what this runbook is written for** (wrong image, wrong machine, or damaged unit). Record what you see and raise it before proceeding. One display quirk that is NOT a failure: `nvidia-smi`'s memory column reads oddly because memory is *unified* (one 128 GB pool shared by CPU and GPU — there is no separate video memory on this machine).

☐ **Step 5 — File the capture and fill the record.**
**Run:** nothing further — the file is already at `~/p42/boxstate-<hostname>-<date>.txt`. Write that path in this section's STEP RECORD "Values" line; the file IS the captured box state. Repeat this whole section on the other machine.

**TEST:** the four hard gates of Step 4 pass on this machine; SSH works from the laptop; the boxstate file exists.

> **📋 STEP RECORD — §1.1** &nbsp;&nbsp; ☐ Done &nbsp; ☐ Deviation logged &nbsp; ☐ N/A (reason below)
> Machine: ☐ Spark-1 ☐ Spark-2 &nbsp;·&nbsp; Operator: `____________` &nbsp;·&nbsp; Date: `____________`
> Values recorded (versions / tags / measurements / anomalies): `________________________________________________`
>
> **Notes / observations / follow-ups** *(use as much of this space as needed)*:
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`

## 1.2 OS update, driver pin & firmware decision (v2.0 step format)

*Goal of this section:* bring the operating system fully up to date **without breaking the GPU driver**, freeze the driver at the known-good version, make a deliberate (not accidental) decision about firmware, and install the everyday tools.

*Terms used in this section, in plain language:* the **kernel** is the core of Linux — the part that talks to the hardware. A **driver** is the software that lets the kernel use a device (here: the GPU); it loads into the kernel as **modules** which must match the kernel version exactly. **Firmware** is different from all of the above: it is software that lives *inside* the hardware itself and keeps running below the operating system — the **EC** ("embedded controller") is one such chip, managing fans and power, and **UEFI** is the firmware that boots the machine.

☐ **Step 1 — Refresh the software catalogue.**
**Why:** `apt`, Ubuntu's package manager, works from a local catalogue of available software (fed by **repositories** — online catalogues of installable packages); refreshing it is always the first move.
**Before you run it:** updates are done from the command line ONLY — **never use the DGX Dashboard's graphical updater** (documented to wedge mid-update and half-remove the driver). And **never add NVIDIA's generic CUDA repository** from their download pages — its signing keys conflict with DGX OS's preinstalled repositories and completely break `apt`. (CUDA — NVIDIA's GPU-computing software layer, the thing every AI framework here builds on — is already installed; there is nothing to add.)
**Run:**
```bash
sudo apt-get update
```
**Expect:** a list of repositories, ending without errors. **If not:** an `EXPKEYSIG` error is a known fleet-wide expired-key incident (AI Workbench repo) — re-import the key (search the DGX Spark forum for `EXPKEYSIG` for the current fix) or a later `apt full-upgrade` refreshes it. `Signed-By conflict` errors mean a generic CUDA repo was added at some point: remove the offending `cuda-ubuntu2404-*.list` files from `/etc/apt/sources.list.d/` and retry.

☐ **Step 2 — Upgrade the installed software (do NOT reboot yet).**
**Why:** `dist-upgrade` upgrades every installed package, adding or removing dependencies where needed — this may include a new kernel.
**Before you run it:** at the end, Ubuntu may print a message recommending a reboot to load the new kernel. **Do not reboot yet, even though it asks** — whether rebooting is safe is exactly what Step 3 decides.
**Run:**
```bash
sudo apt-get -y dist-upgrade      # -y = assume "yes" to the confirmation prompts (unattended run)
```
**Expect:** the upgrade completes without errors. Note in the build log whether a `linux-image-...` package (a new kernel) was among the upgrades.

☐ **Step 3 — DECISION: is it safe to reboot?** *(the kernel/driver-module check)*
**Why:** on an ordinary Ubuntu PC, a mechanism called **DKMS** ("Dynamic Kernel Module Support") automatically rebuilds the GPU driver modules for every new kernel, so a reboot after an upgrade "just works". **DGX OS on this ARM64 machine has no DKMS.** The NVIDIA driver ships as pre-compiled modules matched to one exact kernel version. If Step 2 installed a new kernel but not the matching module package, rebooting boots a kernel with **no GPU driver at all** — `nvidia-smi` dead (this hit three GB10 machines at once in one forum report).
**Run:**
```bash
uname -r                                    # -r = print just the running kernel's version (the kernel running NOW)
ls -1 /boot/vmlinuz-* | sort -V | tail -1   # the kernel that will boot NEXT: -1 = one name per line, sort -V = version-number order, tail -1 = keep the newest
apt list --installed 2>/dev/null | grep -E 'linux-image|linux-modules-nvidia'   # grep -E = extended pattern, matches either name
```
**Decide:** take the version string of the NEXT kernel (everything after `vmlinuz-`) and look for a `linux-modules-nvidia-580-...` line carrying **that same version**.

- **Match found →** safe; go to Step 4.
- **No match →** do NOT reboot. Install the matching modules first (use Tab-completion for the exact name), then re-run the check:

  ```bash
  sudo apt-get install linux-modules-nvidia-580-open-<new-kernel-version>
  ```

- **No such package exists at all →** do NOT reboot; stay on the running kernel (which still works) and investigate — a running system with an old kernel is recoverable from anywhere, a GPU-less boot is a worse starting point. Log it as a deviation.

> [!CAUTION]
> **Kernel-regression watch (v4.15) — HOLD the known-good kernel.** A forum report (2026-08-06, single reporter, on an ASUS GX10 + DGX Spark pair) documents a severe **one-way inbound RDMA regression** on kernel `6.17.0-1029-nvidia` (**RDMA** is the direct card-to-card data transfer, bypassing the CPU, that the §2.8 two-box link depends on): inbound traffic collapsed to **13.2 Gbit/s** while outbound stayed normal, and rolling back to the `-1026` kernel restored **111.7 Gbit/s**. Rule: **stay on the current known-good kernel and do NOT take `-1029` (or later) until inbound RDMA has been verified in BOTH directions** (the §2.8 bidirectional `ib_write_bw` check). This only matters for the §2.8 cluster experiment — but a kernel is far easier to refuse now than to roll back later. Note it also as **OEM-divergence evidence**: the same GB10 silicon does not guarantee the same platform behaviour across vendor variants. Source: https://forums.developer.nvidia.com/t/severe-one-way-rdma-performance-regression-on-asus-ascent-gx10-with-kernel-6-17-0-1029-nvidia/379303

☐ **Step 4 — Reboot and verify the driver survived.**
**Run:**
```bash
sudo reboot
# then, after logging back in:
nvidia-smi && dpkg -l | grep nvidia-driver   # dpkg -l = list installed packages; grep keeps the driver line
```
**Expect:** the GB10 GPU table appears and the driver package shows a **580.x** version. **If `nvidia-smi` fails:** the Step 3 check was missed or mis-read — reboot into the previous kernel (hold Shift/Esc for the GRUB boot menu → "Advanced options" → pick the older kernel), install the matching modules per Step 3, and log the incident.

☐ **Step 5 — Pin the driver at 580.x.**
**Why:** the 590-series driver has three documented regressions on GB10 (a memory leak, a deadlock, and a data-corruption bug), and NVIDIA staff **re-confirmed 2026-08-04** that 590 is still not supported on DGX Spark; a 595.x/CUDA 13.2 pipeline exists but is **beta — not for this project**. "Pinning" (`apt-mark hold`) tells apt to freeze a package: future upgrades will skip it until the hold is removed.
**Run:**
```bash
sudo apt-mark hold nvidia-driver-580-open
```
**Expect:** `apt-mark showhold` lists `nvidia-driver-580-open`.

☐ **Step 6 — Record firmware versions and the idle-temperature baseline.**
**Why:** before *any* firmware decision you need to know what versions the machine came with, and what "normal" temperatures look like on this specific unit — otherwise a later regression has nothing to be compared against.
**Run — versions** (record every device's firmware version — EC and UEFI especially — in the build log):
```bash
sudo fwupdmgr get-devices
```
**Run — idle temperature:** first make the box truly idle (`docker ps` empty, `nvidia-smi` shows 0 % GPU use, then leave it ~10 minutes, on wall power, in its normal position), then:

```bash
# all temperature sensors, labelled, in °C:
paste <(cat /sys/class/thermal/thermal_zone*/type) <(cat /sys/class/thermal/thermal_zone*/temp) | awk '{printf "%-24s %6.1f °C\n", $1, $2/1000}'
# the GPU sensor on its own (--query-gpu = ask for the named values only; --format=csv,noheader = print the bare value, no table):
nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader
```

**Expect:** GPU sensor idling around **30–35 °C**; the **CPU sensor reading ~10–15 °C hotter than the GPU is normal on this machine** — record every sensor's value, because future comparisons must be like-for-like (GPU vs GPU, CPU vs CPU). **If a sensor already idles at ≥45–50 °C on a factory-fresh unit:** stop and investigate cooling before loading any work (the §3.c thermal entries; possibly a warranty conversation).

☐ **Step 7 — DECISION: update the firmware, or leave it alone?**
**Why:** firmware updates on this platform are **not automatically safe**: an EC firmware series (0x0300) shipped with a broken fan curve fleet-wide — machines idling at ~60 °C and throttling instantly under load, unfixable from the operating system.
**Before you run it:** check the DGX Spark forum's thermal threads for the *current* EC firmware status — specifically the **latest posts** in these (v2.1: links added):
- Rollback-fix thread (the community-validated downgrade; its recent posts track which EC versions are currently safe): https://forums.developer.nvidia.com/t/nvidia-dgx-spark-gb10-thermal-throttling-fan-curve-fix-via-ec-firmware-rollback/377069
- Symptom thread (throttling after EC/UEFI updates, fans not ramping): https://forums.developer.nvidia.com/t/dgx-spark-gb10-thermal-throttling-after-ec-uefi-updates-acpi-zones-96-97c-fans-not-ramping/377044
- General thermal-status thread: https://forums.developer.nvidia.com/t/status-and-experience-on-thermal-performance/351345
- *(Generic re-check in future: search the "DGX Spark / GB10" category on forums.developer.nvidia.com for "EC firmware", sorted by latest.)*

Then decide by **which EC version Step 6 recorded on YOUR unit** (deep-dive status as of 2026-08-04):

- **EC is 0x02-series (e.g. `0x02004e18` — the known-good branch) →** do **NOT** run `fwupdmgr upgrade`: it would install the 0x0300-series EC, whose first release (`0x03000302`) shipped the broken fan curve, and the newer `0x03000508` (2026-07-15, "performance and stability") has **no community confirmation of a fan-curve fix** and no NVIDIA statement. Skip firmware entirely — nothing in WP1 requires newer firmware. This is the expected case for factory-fresh units and the safest position.
- **EC is already 0x0300-series →** let the Step 6 idle baseline decide: idle ~30–35 °C → keep it, record it, monitor. Idle ≥45–50 °C → the fan-curve bug: roll back (on wall power, never interrupt), then reboot. Verified result: idle ~32 °C, 35–37 °C under load. Note: the rollback is community-validated, not NVIDIA-sanctioned — log it as a deviation.

  ```bash
  sudo fwupdmgr get-devices              # copy the EC's Device ID
  sudo fwupdmgr downgrade <device-id>    # select 0x02004e18 — then reboot
  ```

- **Before re-visiting this decision later:** read the **latest posts** of the rollback thread (link above) for the eventual all-clear; do not update the EC before it appears there.

**A different-looking twin (do not confuse):** hot idle *immediately after* an update can also be a **silently failed USB Type-C firmware install** (forum-documented, late July 2026) — check `sudo fwupdmgr get-devices` for pending/failed updates; the fix is a full power-off with the cord removed for ~30 minutes, which lets the pending firmware install on the next boot. Check this before concluding you have the EC fan-curve bug.

**After ANY firmware change:** repeat Step 6's temperature check and compare like-for-like against your baseline.

☐ **Step 8 — Install the everyday tools.**
**Why:** the basic building blocks the rest of the runbook assumes: `git` (source-code fetching), `curl`/`wget` (downloading), `build-essential` (compilers, for the llama.cpp build in §2.1), `ca-certificates` (secure-connection trust store), `jq` (reading **JSON** output — JSON is the standard text format programs use to exchange structured data; you will see it in every API reply).
**Run:**
```bash
sudo apt-get install -y git curl wget build-essential ca-certificates jq
```
**Expect:** `git --version` and `curl --version` print versions.

**TEST:** driver shows 580.x after reboot; `apt-mark showhold` lists the driver; firmware versions + full idle-temperature baseline are in the build log; a deliberate yes/no firmware decision is recorded.

> **📋 STEP RECORD — §1.2** &nbsp;&nbsp; ☐ Done &nbsp; ☐ Deviation logged &nbsp; ☐ N/A (reason below)
> Machine: ☐ Spark-1 ☐ Spark-2 &nbsp;·&nbsp; Operator: `____________` &nbsp;·&nbsp; Date: `____________`
> Values recorded (versions / tags / measurements / anomalies): `________________________________________________`
>
> **Notes / observations / follow-ups** *(use as much of this space as needed)*:
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`

## 1.2.a Workstation tools — browser, terminal, markdown editor (NEW in v1.1)

*What & why:* from this point on, the operator works **on the Spark itself** — including following and filling the markdown copy of THIS runbook on the box. That needs three everyday tools installed first: a browser (NVIDIA playbooks, NGC, Hugging Face pages, Open WebUI later), a proper terminal (split panes for command-plus-server-log work; sessions that survive SSH drops during multi-hour model pulls), and a markdown editor to fill the STEP RECORDs in (**markdown** is the plain-text formatting notation this runbook is written in — headings, tables and checkboxes typed as ordinary characters). Everything below is either an official vendor `.deb` or a standard Ubuntu 24.04 arm64 package — no third-party builds (Golden Rule: provenance).

**Steps:**

1. ☐ **Google Chrome — official ARM64 build** (new: Google shipped ARM64 Linux Chrome in Q2 2026; confirmed working on DGX Spark in the NVIDIA forum). Installing the `.deb` also registers Google's signed apt repo, so Chrome then updates via the normal `sudo apt upgrade`:
   ```bash
   cd ~/Downloads
   wget https://dl.google.com/linux/direct/google-chrome-stable_current_arm64.deb
   sudo apt install ./google-chrome-stable_current_arm64.deb
   google-chrome --version    # RECORD the version in the build log
   ```
   > [!NOTE]
   > This build is only weeks old (Google's support pages did not yet formally list ARM64 Linux at the time of writing) — treat glitches as early-days behaviour, not a broken box. Fallbacks if needed: `sudo snap install chromium`, or the preinstalled Firefox. Do **NOT** install any unofficial "Chrome for ARM" build from elsewhere.
2. ☐ **Terminal: Terminator + tmux** (both from the standard Ubuntu arm64 repos). Terminator gives split panes — server log in one pane, commands in the other, which is exactly the Part B workflow. tmux keeps long jobs alive when SSH drops (SSH-first policy, §1.1):
   ```bash
   sudo apt update
   sudo apt install terminator tmux
   # tmux habit for every long-running job (model pulls, benchmarks):
   #   tmux new -s pull        → start the job (-s = give the session a name, here "pull") → detach: Ctrl-b d
   #   tmux attach -t pull     → reattach later, from any SSH session (-t = target that named session)
   ```
   (Prefer a GPU-accelerated single-window terminal instead? `sudo apt install kitty` — same repo, equally fine.)
3. ☐ **Markdown editor: VS Code — official Microsoft arm64 `.deb`.** This is deliberately VS Code and not a lighter viewer: it is also the host for **Cline (§2.2)**, so it earns its place on the box twice:
   ```bash
   wget "https://update.code.visualstudio.com/latest/linux-deb-arm64/stable" -O code_arm64.deb   # -O = save the download under this filename
   sudo apt install ./code_arm64.deb
   ```
   Open a markdown file and preview with **Ctrl+Shift+V**. Tables, checkboxes and code fences render out of the box; if this runbook's alert boxes (`[!NOTE]`, `[!CAUTION]`, …) show as plain quotes, install the **"Markdown Preview GitHub Styling"** extension (plus **"Markdown All in One"** for editing). Record the VS Code version + extensions installed.
4. ☐ **Optional — glow, terminal markdown reader** (for reading the runbook inside an SSH session; official Charm signed apt repo — never disable signature checking):
   ```bash
   sudo mkdir -p /etc/apt/keyrings          # -p = create parent folders as needed; no error if it already exists
   # curl -fsSL = fail on HTTP errors, silent progress, still show real errors, follow redirects;
   # gpg --dearmor -o = convert the signing key to the binary form apt needs, written to the named file
   curl -fsSL https://repo.charm.sh/apt/gpg.key | sudo gpg --dearmor -o /etc/apt/keyrings/charm.gpg
   echo "deb [signed-by=/etc/apt/keyrings/charm.gpg] https://repo.charm.sh/apt/ * *" | sudo tee /etc/apt/sources.list.d/charm.list
   sudo apt update && sudo apt install glow
   glow DGX_Spark_Setup_Runbook.md
   ```
5. ☐ **Put this runbook on the box and start filling it.** Copy the markdown master onto the Spark (scp from a laptop, or USB), then make the per-machine working copy this header prescribes and **back-fill the §1.0–§1.2 records now**, while they are fresh:
   ```bash
   mkdir -p ~/p42 && cd ~/p42
   # scp user@laptop:.../DGX_Spark_Setup_Runbook.md .   (or copy from USB)
   cp DGX_Spark_Setup_Runbook.md buildlog-$(hostname).md
   code buildlog-$(hostname).md
   ```

> [!NOTE]
> **Enclave note (decide at G2, not now):** these are shakedown-phase convenience tools. The Ubuntu-repo packages (terminator, tmux, kitty) are already covered by the existing apt mirrors. If Chrome, VS Code or glow are to survive into the **enclave** build (the "enclave" is the future air-gapped, controlled-network environment where the production system is rebuilt — see §0.2), their vendor repos (Google, Microsoft, Charm) must be added to the Artifactory Mirror List first — VS Code is the likely keeper (it hosts Cline, §2.2); Chrome is likely shakedown-only. Record in the STEP RECORD which of these you actually ended up using — that is the G2 keep/drop evidence.

**TEST:** `google-chrome --version` prints; Terminator opens and splits (Ctrl+Shift+E); a `tmux` session survives detach/reattach; VS Code renders this runbook's preview (tables + alert boxes); the per-machine `buildlog-<hostname>.md` copy exists with §1.0–§1.2 back-filled.

> **📋 STEP RECORD — §1.2.a** &nbsp;&nbsp; ☐ Done &nbsp; ☐ Deviation logged &nbsp; ☐ N/A (reason below)
> Machine: ☐ Spark-1 ☐ Spark-2 &nbsp;·&nbsp; Operator: `____________` &nbsp;·&nbsp; Date: `____________`
> Values recorded (versions / tags / measurements / anomalies): `________________________________________________`
>
> **Notes / observations / follow-ups** *(use as much of this space as needed)*:
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`

## 1.3 Docker & the GPU-in-container test (v2.0 step format)

*Goal of this section:* confirm that Docker can use the GPU. **Docker** runs software in **containers** — isolated, pre-packaged bundles that carry their own dependencies (most of our AI stack ships this way); the **NVIDIA Container Toolkit** is the bridge that lets a container reach the GPU. Both come **preinstalled and preconfigured** on DGX Spark — this section verifies rather than installs. Official doc: https://docs.nvidia.com/dgx/dgx-spark/nvidia-container-runtime-for-docker.html

☐ **Step 1 — (Optional) let your user run docker without sudo.**
**Why:** by default only the administrator may talk to Docker; adding yourself to the `docker` group removes the need to prefix every command with `sudo`.
**Before you run it — how the change takes effect (v3.2 clarification):** Linux reads your group memberships **once, at login** — so the `usermod` change becomes permanent for every shell only after a **full logout/login** (SSH: disconnect and reconnect; desktop terminals: log out of the desktop session and back in, or reboot). The `newgrp docker` command is only a stop-gap that grants the group to **the current shell alone** — other or new terminals from the same session will still need `sudo docker` until you re-login. That is expected, not a failure.
**Run:**
```bash
sudo usermod -aG docker $USER   # -aG = Append your user to the named Group, leaving other memberships untouched
newgrp docker        # stop-gap for THIS shell only — re-login makes it permanent everywhere
```
**Expect:** in this shell, `docker ps` works without sudo now; after your next full logout/login it works in every shell. Verify membership with:
```bash
id -nG               # -nG = print your group memberships by Name; the list should include: docker
```

☐ **Step 2 — The GPU-in-container test.**
**Why:** one command proves the whole chain: Docker runs → it can pull from NVIDIA's registry → the container sees the GPU. That last link is the one that matters: the entire serving stack (vLLM, Qdrant, Open WebUI) runs in containers, and this is the mechanism they all rely on.
**Before you run it — what this command actually does (v3.1 clarification):** `docker run` means "start a container from the named image — and if the image is not on this machine yet, **download it first**" (Docker calls the download a *pull*). So the first run fetches the image from `nvcr.io`, NVIDIA's container registry (NGC) — a few GB coming DOWN to your machine; **nothing is uploaded anywhere.** Later runs start instantly from the on-disk copy. The image itself is a packaged mini Ubuntu 24.04 with NVIDIA's CUDA toolkit pre-installed; the container provides no service and does nothing on its own — it exists purely to run the one command appended at the end of the line (`nvidia-smi`) *inside* the isolated environment, print the result, and exit. A throwaway probe; the only trace it leaves is the cached image. Flags: `-it` = show me an interactive terminal; `--gpus=all` = grant the container GPU access (the Container Toolkit's job — without it, no container sees the GPU). The images this project uses are **free public-tier** — no paid subscription — and normally pull without any login.
**Run:**
```bash
docker run -it --gpus=all nvcr.io/nvidia/cuda:13.0.1-devel-ubuntu24.04 nvidia-smi
```
**Expect:** the same GB10 GPU table as on the host. **If not:**
- **Pull refused with a 401/403 error →** Step 3 (the login fallback), then retry.
- **`exec format error` →** the image is for the wrong processor type (see Step 4's rule) — with this exact NVIDIA image that would be surprising; re-check the image name for typos.

☐ **Step 3 — FALLBACK (only if Step 2's pull was refused): log in to NGC.**
**Why:** some networks/accounts hit an authentication wall even on public images. The fix is a free API key.
**Run:** create a free account at ngc.nvidia.com → Setup → Generate API Key; then log in with username exactly `$oauthtoken` (that literal text) and the API key as password:
```bash
docker login nvcr.io
```
Record in the build log that login was needed — the enclave's Artifactory remote (**Artifactory** is the internal server that mirrors approved software into the enclave; a "remote" is one of its upstream sources) needs the same key then.
**Expect:** "Login Succeeded"; Step 2 now works.

☐ **Step 4 — Confirm the container's architecture and the toolkit's health.**
**Why:** this machine is **aarch64** (the ARM processor family), but most Docker images on the internet are built for **amd64** (Intel/AMD PCs) — pulling one gives the `exec format error` crash. This check, run here once, becomes a standing habit: **every non-NVIDIA image gets an architecture check before you trust it.**
**Run:**
```bash
docker run --rm --gpus=all nvcr.io/nvidia/cuda:13.0.1-devel-ubuntu24.04 uname -m   # → aarch64
nvidia-ctk --version
docker info | grep -iA3 runtime          # shows Docker's registered runtimes (-i = ignore case, -A3 = include the 3 lines After each match)
```
*(v3.3 note: `/etc/docker/daemon.json` may legitimately NOT exist — on current DGX OS the toolkit can register via CDI (a newer standard mechanism for exposing devices to containers) or defaults instead. The `docker info` line above is the reliable check; and if Step 2's GPU test passed, the stack is proven regardless. Only if Step 2 FAILED, configure it yourself and retry:)*
```bash
sudo nvidia-ctk runtime configure --runtime=docker && sudo systemctl restart docker
```
**Expect:** `aarch64`; a toolkit version prints; the daemon config shows the nvidia runtime. Record the versions in the build log (the §1.1 capture already caught `docker version`).

**TEST:** the containerised `nvidia-smi` shows the GB10 AND the container `uname -m` prints `aarch64`.

> **📋 STEP RECORD — §1.3** &nbsp;&nbsp; ☐ Done &nbsp; ☐ Deviation logged &nbsp; ☐ N/A (reason below)
> Machine: ☐ Spark-1 ☐ Spark-2 &nbsp;·&nbsp; Operator: `____________` &nbsp;·&nbsp; Date: `____________`
> Values recorded (versions / tags / measurements / anomalies): `________________________________________________`
>
> **Notes / observations / follow-ups** *(use as much of this space as needed)*:
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`

## 1.4 Python tooling (uv) + Hugging Face CLI (v2.0 step format)

*Goal of this section:* install the two tools every Python-side task in this runbook relies on: **uv** (a fast manager for Python environments) and the **Hugging Face CLI** (`hf`; a **CLI** is a "command-line interface" — a tool driven by typed commands — and this one is the official tool for downloading models from Hugging Face, the standard online repository for open AI models).

*One concept first:* a **venv** ("virtual environment") is a private, per-project copy of Python so that projects cannot break each other or the system. Ubuntu 24.04 actively *blocks* installing packages into the system Python (you would see an `externally-managed-environment` error from bare `pip install`) — so on this machine, **everything Python goes through uv**.

☐ **Step 1 — Install uv.**
**Before you run it:** the command downloads the official installer script and runs it — the `curl ... | sh` pattern is acceptable here because it is the vendor's documented route (uv docs: https://docs.astral.sh/uv/) and ships an official aarch64 build.
**Run** (then open a new shell, or follow the installer's PATH hint):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh   # -LsSf = follow redirects, silent progress, show real errors, fail cleanly on HTTP errors
```
**Expect:** `uv --version` prints a version.
**For later (the per-project pattern):**
```bash
# (v4.27) The PROJECT CONVENTION — venvs are NAMED and live under ~/p42/, one per
# pipeline, so any new shell can find and re-activate them explicitly:
mkdir -p ~/p42
uv venv ~/p42/<name>-venv                  # create it ONCE (e.g. ingest-venv, render-venv, lab-venv)
source ~/p42/<name>-venv/bin/activate      # activate it in EVERY shell that uses it
uv pip install <package>                   # installs into the ACTIVE venv
# Activation is per-shell and per-session: a new terminal, a reboot, or a script all
# start WITHOUT it — re-run the source line first (or call ~/p42/<name>-venv/bin/python
# directly). This runbook creates three: render-venv (§2.1.2.5), ingest-venv (§2.1.3),
# lab-venv (§2.7). CLI apps (hf, aider, llama-benchy) are different: they install once,
# venv-free, via 'uv tool install'.
```

☐ **Step 2 — Install the Hugging Face CLI.**
**Before you run it:** the command is **`hf`** — two naming traps, both confirmed: in **huggingface_hub 1.x — which is what this runbook's install gives you** — the old `huggingface-cli` command no longer works (it prints an error, it is not aliased), and `hf login` does not exist — authentication lives under `hf auth ...`. *(v4.6 scope note: on machines carrying an older pre-1.0 huggingface_hub, `huggingface-cli` still exists — that is why some external guides still show it. Everything installed by this runbook is 1.x: use `hf` only.)*
**Run:**
```bash
uv tool install "huggingface_hub[cli]"
# alternatives: inside a venv:     uv pip install huggingface_hub
#               without installing: uvx --from huggingface_hub hf --help
```
**Expect:** `hf --help` prints usage. CLI guide: https://huggingface.co/docs/huggingface_hub/guides/cli

☐ **Step 3 — Log in and set the token.**
**Why:** some models require an account ("gated" models); serving containers also read the token from the `HF_TOKEN` environment variable (an **environment variable** is a named value your shell passes on to the programs it starts — see Annex A.1).
**Before you run it — how to obtain the token (v3.4):** (1) sign in to the **project** Hugging Face account at huggingface.co (never a personal one); (2) avatar → **Settings → Access Tokens → Create new token**; (3) type **Read** (all this project needs — never Write), name it identifiably (e.g. `p42-spark1`); (4) **copy it immediately** — it is shown only once (starts `hf_…`); if lost, delete and create a new one. The token is a password-equivalent — **treat it as a secret** (never in the build log or a screenshot; store in the team password store). Extra rule for *gated* models (e.g. Meta's Llama family): the token alone is not enough — you must also open that model's page on the website while logged in and accept its licence terms once; the token then works for it.
**Run** (browser flow or paste a token; add the second line to `~/.bashrc` so future shells inherit it):
```bash
hf auth login
export HF_TOKEN=hf_xxx
```
**Expect:** `hf auth whoami` prints the project account name.

☐ **Step 4 — Sanity download.**
**Why:** proves the whole chain (CLI → authentication → download → disk) before the multi-hundred-GB model pulls of Part B; also stages a model §2.3 can use.
**Run** (a ~15 GB download; run it inside tmux — §1.2.a habit):
```bash
hf download Qwen/Qwen2.5-Coder-7B-Instruct
```
**Expect:** completes without error; files land under `~/.cache/huggingface/`.

**TEST:** `uv --version` prints; `hf auth whoami` prints the project account.

> **📋 STEP RECORD — §1.4** &nbsp;&nbsp; ☐ Done &nbsp; ☐ Deviation logged &nbsp; ☐ N/A (reason below)
> Machine: ☐ Spark-1 ☐ Spark-2 &nbsp;·&nbsp; Operator: `____________` &nbsp;·&nbsp; Date: `____________`
> Values recorded (versions / tags / measurements / anomalies): `________________________________________________`
>
> **Notes / observations / follow-ups** *(use as much of this space as needed)*:
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`

## 1.5 Smoke test: does the box serve a model? (v2.0 step format)

*Goal of this section:* prove the machine can serve a language model over an **API** ("application programming interface" — a machine-readable web interface that programs call, as opposed to a screen humans click), using the **same NGC vLLM container as the production stack** (§0.6 policy: the smoke test doubles as validation of the container everything else depends on; if a shipping unit has Ollama preinstalled, leave it unused — per §0.6 nothing measured, demoed or user-facing runs on it).

☐ **Step 1 — Pull and start the serving container with a small model.**
**Before you run it — what "image tag" means, and today's concrete answer (v4.9):** a Docker image name has two parts — `nvcr.io/nvidia/vllm` says *which* software (vLLM from NVIDIA's registry), and the part after the colon is the **tag**: *which monthly release* of it (named year.month — `26.07-py3` = July 2026 build). **As of 2026-08-05 the newest tag is `26.07-py3` (published 2026-07-27); the previous is `26.06-py3`.** Decision rule: pull the newest; if this section's smoke test misbehaves on it, fall back ONE tag and retry; pin and record whichever passes — this smoke test is exactly what validates the tag, so no further research is needed. Re-check what "newest" is on the day you run this: NGC tag list https://catalog.ngc.nvidia.com/orgs/nvidia/containers/vllm/tags · playbook https://build.nvidia.com/spark/vllm (GitHub mirror: https://github.com/NVIDIA/dgx-spark-playbooks/tree/main/nvidia/vllm — its official launch form is `vllm serve <model>`, confirmed 2026-08-05). Two known variations to expect: the command below uses the NGC-standard `vllm serve <model> <flags>` subcommand form — if the chosen tag's entrypoint already wraps vllm, the bare-flags form (`--model ...`) may be needed instead (record which form your tag accepts) — and the first pull downloads ~15–20 GB (run in `tmux`). **(v4.6) Settle the entrypoint question deterministically BEFORE the first launch** — inspect what the image runs by default:

```bash
# the image must be pulled BEFORE it can be inspected (inspect reads local metadata);
# replace the placeholder with your confirmed real tag — example shown:
docker pull nvcr.io/nvidia/vllm:26.07-py3      # newest as of 2026-08-05 — re-check per the note above
docker inspect nvcr.io/nvidia/vllm:26.07-py3 --format '{{.Config.Entrypoint}} {{.Config.Cmd}}'   # --format = print only these two fields: the image's default entrypoint and command
```

If the entrypoint already invokes vllm, use the bare-flags form; if it is a plain shell/python entrypoint, use `vllm serve ...` as below; last-resort classic invocation that works on any vLLM image: `python3 -m vllm.entrypoints.openai.api_server --model <model> <flags>`. Record which form your tag needed. **(v4.13, both found live)** Make the xet kill-switch permanent on both machines — `echo 'export HF_HUB_DISABLE_XET=1' >> ~/.bashrc` — because environment variables are per-shell and a forgotten export re-enables the broken backend silently ("Reconstructing..." in a download progress bar = xet is active). And after ANY sudo'd container has written into `~/.cache/huggingface`, root-owned lock/blob files can block later host-side downloads (`PermissionError ... .locks/...`): fix with `sudo chown -R $USER: ~/.cache/huggingface` (`-R` = recursively, the whole folder tree; `$USER:` = make your own user the owner again). Note the `-e HF_HUB_DISABLE_XET=1` in the command — the HF Xet download backend is broken on ARM64 (§3.c signature; found live in WP1); best practice is to pre-download on the host (`hf download <model>` with `HF_HUB_DISABLE_XET=1` exported) so the container loads from the mounted cache. The model used, `nvidia/Llama-3.1-8B-Instruct-FP8`, is from NVIDIA's verified matrix and is deliberately small; `--gpu-memory-utilization 0.5` caps it at half the memory pool, which is safe on an otherwise-empty box.
**Run:**
```bash
docker run --name vllm-smoke --gpus all -p 8000:8000 \
  --ipc=host --ulimit memlock=-1 --ulimit stack=67108864 \
  -e HF_TOKEN=$HF_TOKEN -e HF_HUB_DISABLE_XET=1 -v ~/.cache/huggingface:/root/.cache/huggingface \
  nvcr.io/nvidia/vllm:26.07-py3 \
  vllm serve nvidia/Llama-3.1-8B-Instruct-FP8 --gpu-memory-utilization 0.5   # tag = the one you validated above
```
*Flag rationale for the launch line (first use — every later `docker run` in this runbook reuses these):* `--gpus all` grants the container GPU access (§1.3); `-p 8000:8000` publishes the container's port 8000 on the host's port 8000, which is what makes the API reachable from outside the container; `--ipc=host` lets the container use the host's inter-process shared memory (vLLM needs it under load — §2.1.2); `--ulimit memlock=-1` removes the limit on how much memory the process may lock in place (−1 = unlimited) and `--ulimit stack=67108864` raises the per-thread stack limit to 64 MiB — both standard NVIDIA-container settings that prevent crashes under load; `-e` passes an environment variable into the container (here the HF token and the xet kill-switch); `-v ~/.cache/huggingface:/root/.cache/huggingface` mounts the host's model cache into the container, so weights downloaded once are reused by every container.

**Expect:** the startup log settles at a "server running / listening" line. **If not:** `exec format error` → wrong-architecture image (§1.3 Step 4); authentication error → HF_TOKEN not set in this shell (§1.4 Step 3); crash citing memory → another model is already loaded (`docker ps`, teardown first).

☐ **Step 2 — Test the API.**
**Why:** the serving container exposes an "OpenAI-compatible" web API — the industry-standard interface every client in this project (Open WebUI, Cline, aider…) speaks. (In the commands, `localhost` means "this same machine".)
**Run (second terminal — a Terminator split pane, §1.2.a):**
```bash
curl http://localhost:8000/v1/models
curl http://localhost:8000/v1/chat/completions -H "Content-Type: application/json" \
  -d '{"model":"nvidia/Llama-3.1-8B-Instruct-FP8","messages":[{"role":"user","content":"hello"}]}'
```
*Flag gloss:* curl's `-H` adds a request header (here: declaring the body is JSON) and `-d` sends the given text as the request body (which also turns the request into a POST).

**Expect:** the first lists the served model; the second returns JSON containing a coherent assistant reply.

☐ **Step 3 — The silent-CPU-fallback check (v4.14 — long-probe version).**
**Why:** a mis-built stack can quietly run the model on the CPU — everything *works*, just absurdly slowly. **Before you run it:** a short "hello" completes too fast to observe (found in execution) — use a deliberately LONG generation (~2,000 tokens ≈ 1–2 minutes of sustained load) and watch the GPU live in a second pane.
**Run (pane 1 — the long probe):**
```bash
curl http://localhost:8000/v1/chat/completions -H "Content-Type: application/json" \
  -d '{"model":"nvidia/Llama-3.1-8B-Instruct-FP8","messages":[{"role":"user","content":"Write a detailed 1500-word essay on the history of lunar exploration."}],"max_tokens":2000}'
```
**Run (pane 2 — live GPU readout, one line per second; Ctrl-C to stop):**
```bash
nvidia-smi --query-gpu=power.draw,utilization.gpu,clocks.sm --format=csv,noheader -l 1   # -l 1 = loop: refresh every 1 second (query/format flags per §1.2)
```
**Expect:** utilisation well above 0 %, power in the tens of watts, clocks near ~2100 MHz while generating (this is also §3.c's healthy power-state fingerprint — learn it now), and the CPU NOT pegged at 100 %. **If reversed (0 % GPU, 100 % CPU):** the model runs on CPU — wrong build or failed GPU access; stop and fix (§3.c).

> [!NOTE]
> **(v4.14) Three log signatures from the first live runs — read your startup log against these:** (1) On 26.07-py3 with the 580.x driver, the entrypoint prints a banner saying "**compatibility mode is UNAVAILABLE**". It looks alarming, but on this platform it is **non-blocking noise**: the stack initialises and serves normally regardless. Judge the launch by whether the server actually answers requests (Step 2), not by this banner. (2) The warning "Checkpoint does not provide a q scaling factor / Using KV cache scaling factor 1.0" means the fp8 KV cache is running **uncalibrated** on this checkpoint — the 8-bit compression is applied without a model-specific tuning factor. That is harmless for a smoke test, and it is exactly why the runbook's fp8-KV default carries a Part C quality spot-check per model before real use. (3) "Default sampling parameters overridden by the model's generation_config.json" means the model shipped its own sampling defaults and vLLM is silently using them instead of its own. That is fine for casual chat — but anything MEASURED (Part C / M42) must pin sampling explicitly so runs stay comparable (the `--generation-config vllm` flag makes the server ignore the model's file). Finally, ignore the cosmetic `UnicodeDecodeError` traceback printed during interpreter cleanup after every clean shutdown of this build — it appears *after* a successful stop and means nothing.

☐ **Step 4 — Teardown.**
**Why:** port 8000 (a **port** is a numbered door on a machine through which one network service talks; §1.6 explains the full port plan) is a single slot (§3.b) and the memory pool is shared — every track leaves the box clean.
**Run:**
```bash
docker ps                  # find the running container's name
docker stop <container>
nvidia-smi                 # confirm the memory is released
```

**TEST:** Step 2's `curl` returns a coherent completion AND Step 3 shows it came from the GPU. Part A serving capability is proven. (llama.cpp, the second baseline engine, is built and tested in §2.1/§2.2.)

> **📋 STEP RECORD — §1.5** &nbsp;&nbsp; ☐ Done &nbsp; ☐ Deviation logged &nbsp; ☐ N/A (reason below)
> Machine: ☐ Spark-1 ☐ Spark-2 &nbsp;·&nbsp; Operator: `____________` &nbsp;·&nbsp; Date: `____________`
> Values recorded (versions / tags / measurements / anomalies): `________________________________________________`
>
> **Notes / observations / follow-ups** *(use as much of this space as needed)*:
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`

## 1.6 Record both IPs; how Spark-2 reaches Spark-1 (v2.0 step format)

*Goal of this section:* fix each machine's network identity in writing, and prove the two machines can reach each other's services. Why this matters day-to-day (v4.0): Spark-2 reaches **Spark-1's serving endpoints as a client** (an **endpoint** is a service's callable network address — IP + port + path) for the other tracks — coding clients (§2.2), notebooks (§2.7), benchmarks (Part C). The KB itself, ingestion included, runs entirely on Spark-1 since v4.0 (§2.1), so nothing is pushed from Spark-2 into Spark-1's Qdrant any more.

☐ **Step 1 — Record each machine's address.**
**Run (on each Spark)** — note the LAN IP (**LAN** = local-area network, the office network both machines share):
```bash
ip -4 addr show | grep inet     # -4 = IPv4 only (first explained in §1.1)
hostname -I                     # -I = print all of this machine's IP addresses
```
Fill this in (keep it visible):

| Machine | Hostname | LAN IP |
|---|---|---|
| Spark-1 (KB single-box + serving) | `__________` | `__________` |
| Spark-2 (clients / experiments) | `__________` | `__________` |

**Before relying on these:** if the office network hands out addresses dynamically (DHCP), the IPs can change on reboot — if that happens in practice, ask IT for reserved addresses (note it in the record).

☐ **Step 2 — Understand the port plan.**
**Why:** each service on Spark-1 listens on a numbered **port**; any client on the LAN reaches it as `http://<spark-1-ip>:<port>`. One rule matters for reachability: services must listen on `0.0.0.0` (all network interfaces), not `localhost` (machine-internal only) — the `docker run -p` flags used throughout this runbook already do this.

| Port | Service | Endpoint |
|---|---|---|
| 8000 | vLLM **or** llama-server (answer / coding LLM) — one engine at a time; stop the other before rebinding | `/v1/chat/completions`, `/v1/completions`, `/v1/models` |
| 8001 | Always-on llama-server systemd service, *if* set up (§2.1.2.1 TIP) — kept off 8000 so it never collides with a vLLM container | same as 8000 |
| 8002 | vLLM (Qwen2.5-VL captioning) — Spark-1, **UPDATE mode only** (§2.1.3) | `/v1/chat/completions` (vision) |
| 8080 | Embeddings (BGE-M3) | `/embed` (TEI) or `/v1/embeddings` (vLLM) |
| 8081 | Reranker (bge-reranker-v2-m3) | `/rerank` (TEI) |
| 6333 / 6334 | Qdrant | REST + dashboard / gRPC |
| 3000 | Open WebUI | web UI |
| 8888 | JupyterLab (Spark-2, §2.7) | notebooks |

> For headless cross-LAN access, plain SSH port-forwards or the NVIDIA **Tailscale** playbook (Tailscale is a zero-configuration private-network/VPN tool) are simpler than NVIDIA Sync (which assumes a laptop client app).

☐ **Step 3 — Prove cross-machine reachability.**
**Before you run it:** Spark-1 must have a model serving (if you just finished §1.5's teardown, restart the §1.5 container for this test, then tear down again).
**Run (from Spark-2):**
```bash
curl http://<spark-1-ip>:8000/v1/models
```
**Expect:** the model list, same as locally on Spark-1. **If it hangs:** the service is bound to `localhost` instead of `0.0.0.0`, or a firewall is blocking the port — check on Spark-1 (shows what is listening where):
```bash
sudo ss -tlnp | grep 8000   # -tlnp = TCP sockets, Listening only, Numeric ports, with the owning Process shown
```

**TEST:** the table above is filled in ink; the Step 3 curl succeeds from Spark-2.

> **📋 STEP RECORD — §1.6** &nbsp;&nbsp; ☐ Done &nbsp; ☐ Deviation logged &nbsp; ☐ N/A (reason below)
> Machine: ☐ Spark-1 ☐ Spark-2 &nbsp;·&nbsp; Operator: `____________` &nbsp;·&nbsp; Date: `____________`
> Values recorded (versions / tags / measurements / anomalies): `________________________________________________`
>
> **Notes / observations / follow-ups** *(use as much of this space as needed)*:
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`

## 1.7 Unified-memory discipline (v2.0 step format — read before running anything big)

*Goal of this section:* set up the protections that keep the machine alive when a model is too big.

*Why this matters, in plain language:* this machine has **one** 128 GB memory pool shared by CPU and GPU ("unified memory"). On a normal computer, a program that asks for too much memory gets a clean error ("**OOM**" — out of memory) and dies alone. Here, exhausting the pool does NOT produce a clean error: **the whole machine locks up** — driver dead, SSH dead, only the power button left (and §1.0 explained why we hate the power button). Docker's memory limits do not contain GPU allocations, so containers do not protect you either. These are standing rules on BOTH machines.

☐ **Step 1 — One-time protections.**
**Why, line by line:** **swap** is the OS using disk as overflow memory — on an inference box (**inference** = running a trained model to produce answers, as opposed to training it) it turns "fail fast with a clear error" into "grind unusably for an hour first", so we disable it. The second command protects SSH: when Linux runs critically low on memory it kills processes to survive (the "OOM killer"); the setting tells it **never kill SSH** — your escape hatch stays alive even in a memory crisis.
**Run:**
```bash
sudo swapoff -a      # -a = disable ALL swap areas
sudo mkdir -p /etc/systemd/system/ssh.service.d && printf '[Service]\nOOMScoreAdjust=-1000\n' | sudo tee /etc/systemd/system/ssh.service.d/oom.conf
sudo systemctl daemon-reload && sudo systemctl restart ssh
```
**Expect:** `free -h` shows Swap `0B`; ssh restarts cleanly (your session survives).

☐ **Step 2 — Learn the pre-load habit (every large model load, every training run).**
**Why:** Linux keeps recently-read files in spare memory (the "page cache") — normally harmless, but here it competes with the GPU's huge allocations and causes the lock-up *even when `free -h` looks fine*. Flushing it before every big load is the single most important habit on this machine.
**Run (before every large load):**
```bash
sudo sh -c 'sync; echo 3 > /proc/sys/vm/drop_caches'
```
*(§2.1's TIP automates this for permanent services via systemd `ExecStartPre` — the habit covers everything started by hand.)*

☐ **Step 3 — Know your early-warning signal.**
**Why:** free-memory numbers lie on this machine (engines deliberately reserve ~95 % of the pool — **~9 GB "free" is by design, not a leak**). The honest signal is **PSI** ("pressure stall information"): how much time processes spend *waiting* for memory.
**Run (during heavy runs, in a spare pane):**
```bash
cat /proc/pressure/memory
```
Rising `avg10`/`avg60` numbers = pressure building; act (smaller model/context) before the lock-up, not after.

☐ **Step 4 — Rules for heavy jobs and vLLM memory budgets.**

- Heavy batch/training jobs run capped (the cap protects the OS; the GPU side is governed by the engine flags below):

  ```bash
  # --scope = run the command in its own transient cgroup; -p MemoryMax=100G = the cap: the job is killed
  # before it can take the whole box past 100 GB
  systemd-run --scope -p MemoryMax=100G <command>
  ```

- **vLLM:** `--gpu-memory-utilization` divides the *shared* pool. Budget: **all instances together ≤ ~0.75 when the KB services co-reside** (worked split: answer LLM 0.55 + embeddings 0.15); up to **0.85 only for one solo big model** — 0.9 risks the lock-up. Useful flags: `--enforce-eager` (skip CUDA-graph capture — a GPU launch optimisation — and run operations one at a time) saves ~13 GB; `--kv-cache-dtype fp8` shrinks the **KV cache** (the model's working memory of the conversation so far — it grows with context length) by storing it in 8-bit numbers; `--load-format fastsafetensors` (a faster weight-loading path) cuts startup ~40 %; keep the default `mp` (plain multiprocessing) executor (**Ray**, a cluster-coordination framework used in §2.8, adds overhead that trips the OOM threshold single-node).

☐ **Step 5 — Set up Spark-aware monitoring.**
**Why:** `nvidia-smi` reports memory as "N/A" on unified memory — it cannot see the pool properly. Use a Spark-aware monitor (`nv-monitor` or `spark-smi`, per the §1.1 capture note) and watch PSI/swap-out rate, not raw free-memory numbers.
**(v4.2) vLLM's built-in metrics are the richest early-warning source:** every vLLM server exposes live **metrics** (internal measurements: memory use, queue depth, timings) at `/metrics` on its serving port, in the text format read by **Prometheus**, the standard open-source monitoring system — no flag needed. During heavy runs, watch KV-cache usage, time-to-first-token and queue depth:

```bash
curl -s http://localhost:8000/metrics | grep -E 'kv_cache|ttft|num_requests'   # -s = silent (no progress bar); grep -E keeps any of the three metric names
```

(A proper Prometheus/Grafana scrape of the same endpoint — Grafana is Prometheus's usual dashboarding companion — is a nice-to-have, not required for WP1.)

**Symptom decoder (record any occurrence):** "thermal throttling" reports are usually memory pressure in disguise — check `free -h` and whether the GPU clock is stuck at 513 MHz (vs ~2100 baseline). Sudden hard shutdowns under load are usually power spikes, not heat — cap clocks with `sudo nvidia-smi -lgc 2100,2400` (`-lgc` = lock the GPU clocks to the given min,max MHz range) if they occur, and see §3.c.

**TEST:** swap is off; the ssh OOM protection file exists; you can state the pre-load habit from memory; monitoring runs on both machines.

> **📋 STEP RECORD — §1.7** &nbsp;&nbsp; ☐ Done &nbsp; ☐ Deviation logged &nbsp; ☐ N/A (reason below)
> Machine: ☐ Spark-1 ☐ Spark-2 &nbsp;·&nbsp; Operator: `____________` &nbsp;·&nbsp; Date: `____________`
> Values recorded (versions / tags / measurements / anomalies): `________________________________________________`
>
> **Notes / observations / follow-ups** *(use as much of this space as needed)*:
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`

# Part B — Per-capability-track setup + test

Each track is self-contained: run **one at a time**, and run the **Teardown** at the end before switching. General teardown pattern:

```bash
docker compose down                 # for compose stacks
docker stop <name> && docker rm <name>   # for standalone containers
pkill llama-server                  # free a llama.cpp model from GPU
nvidia-smi                          # confirm GPU memory released
```

Work in the §0.5 priority order. For every track, the exit questions are the same: *does the recipe work end-to-end on public stand-in data, what exactly is the recipe (image tags, flags, model handles), and what quality did we see?* Those answers go into the baseline stack description.

---

## 2.1 Knowledge base (RAG) — DO THIS FIRST (most detail) (v4.0 step format — single-Spark, mode-exclusive)

*Goal of this section:* ingest technical PDFs (tables + diagrams) and answer grounded questions with source-page citations, using only local models — **everything on Spark-1**: the box is either *serving* answers to users or *updating* its document base, never both at once (see "The two modes" below).

*Terms used in this section, in plain language:* **RAG** ("retrieval-augmented generation") means the model does not answer from memory — relevant document passages are *retrieved* first and handed to it, so every answer can cite its source. An **embedding** is a list of numbers (a **vector**) a model computes from a piece of text so that similar meanings get similar numbers — that is how "find the passages about X" works mathematically. A **vector database** (here: **Qdrant**) stores those number lists and searches them fast. A **reranker** is a second, more careful model that re-orders the retrieved passages by true relevance. A **VLM** ("vision-language model") is a model that can look at images — used here to caption figures and diagrams. **Ingestion** is the pipeline that turns raw PDFs into all of the above. A **maintenance window** is an announced period during which a service is deliberately taken offline so changes can be made safely — users know in advance the KB is unavailable. A **snapshot** is a point-in-time copy of a database's contents, saved as a file, that can be restored later to return the database to exactly that state.

**De-risks:** UC-OPS-2 (worked example — cited assistant over RFM documentation), UC-DB-1 (TM/TC — telemetry/telecommand — query), UC-SE-2 (traceability Q&A). The mandatory-citation behaviour ("no citation, no claim") that UC-OPS-2's acceptance criteria demand is exercised here for the first time — check it on stand-in data.

**How §2.1 is organised — read this map first (v4.39, restructured after operator feedback).** The old letter scheme (`2.1.2.2`-style) is gone: subsections are plain decimal levels, ECSS-style, and **every step title carries a tag** saying who runs it (full legend in §0.8):

- **[ALL]** — every operator runs this step, on every route. Skipping it leaves the stack broken.
- **[DECISION]** — read and choose between named routes; the step contains no commands, and it states which later steps implement each route.
- **[ROUTE: X]** — run ONLY if the named DECISION step chose route X; the tag states explicitly which step(s) it is the alternative to. Steps for the route you did not choose are skipped entirely.
- **[OPTIONAL]** — a genuinely skippable extra; the baseline never depends on it.

| Order | Subsection | What it builds | Route decisions inside |
|---|---|---|---|
| 1 | **2.1.1** Modes + lifecycle scripts | The SERVING/UPDATE mode framework and the three `/opt/p42/bin` scripts | — |
| 2 | **2.1.2** Serving stack (five components, in order) | 2.1.2.1 answer LLM → 2.1.2.2 embeddings + reranker → 2.1.2.3 Qdrant → 2.1.2.4 Open WebUI → 2.1.2.5 rendering layer | **Two:** engine route (2.1.2.1 Step 1) and embeddings route (2.1.2.2 Step 1) |
| 3 | **2.1.3** Ingestion pipeline (four components, in order) | 2.1.3.1 Docling → 2.1.3.2 VL captioning → 2.1.3.3 ColQwen → 2.1.3.4 ingest script + lifecycle runs | — |
| 4 | **2.1.4** End-to-end TEST + mode rehearsal | The proof the whole KB works, and the formal mode-switch rehearsal | — |
| 5 | **2.1.5** Teardown | Clean exit before the other Part-B tracks | — |

Work strictly top to bottom: nothing in a later subsection is needed by an earlier one, and every component a later subsection depends on has been built by the time it is reached.

### 2.1.1 The two modes and the lifecycle scripts — how the single-box KB works

The KB runs entirely on Spark-1 in one of two **mutually exclusive modes — never both at once**:

| Mode | What runs | Who can use it | How you get there |
|---|---|---|---|
| **SERVING** | Answer LLM (:8000) + BGE-M3 embeddings (:8080) + bge-reranker (:8081) + Qdrant (:6333/6334) + Open WebUI (:3000) — ~80 GB, comfortable in the 128 GB pool | Everyone — normal KB operation | `/opt/p42/bin/kb-mode-serve.sh` |
| **UPDATE** | Docling + Qwen2.5-VL-7B captioning (:8002) + ColQwen2.5 — the answer LLM, reranker and Open WebUI are torn down, so ingestion gets the pool; **Qdrant stays up** to receive the vectors and **BGE-M3 embeddings (:8080) stays up** to embed the new chunks (v4.16 — same embedder at ingestion and query time, or retrieval breaks) | Nobody — KB offline to users, in an **announced maintenance window** | `/opt/p42/bin/kb-mode-update.sh` (snapshots Qdrant first) |

One component is deliberately common to both rows: **Qdrant stays up in both modes** — in SERVING mode it answers retrieval queries, in UPDATE mode it receives the new vectors.

Why this design (rationale, for the record):

- **Bandwidth contention and co-residency OOM risk are eliminated by construction** — the serving stack and the ingestion stack are never resident together, so the §1.7 zombie-OOM class of failure cannot arise from KB co-residency at all.
- **Updates run as fast as on a dedicated box** — ingestion gets the whole 128 GB pool and the full 273 GB/s of bandwidth.
- **An ingestion hang during a window hurts nobody** — the KB was announced offline anyway; recover at leisure, no user ever sees a degraded half-working KB.
- **It matches document-baseline configuration management** — the KB is at any moment either "serving baseline N" or "updating to baseline N+1", so answers and citations are reproducible per baseline.
- **It frees the second Spark entirely** for the client, benchmark, notebook and fine-tune tracks (§2.2, §2.7, §2.9, Part C — see §0.4).

**Fallback:** the old 2-Spark split (serving on Spark-1, ingestion pushed from Spark-2) remains a documented fallback option — e.g. if Spark-1 is down or away on RMA (returned to the manufacturer for repair) — and the topology decision is confirmed at G2.

> [!IMPORTANT]
> **Mandatory rollback safety: snapshot Qdrant before EVERY update — no exceptions.** Why: an ingestion run that goes wrong can leave the database half-updated, and untangling that on live data is slow and error-prone — so the standing rule is that a bad ingestion is *rolled back*, never debugged live, and the snapshot taken before the update is what makes that rollback possible. `kb-mode-update.sh` below takes the snapshot automatically via Qdrant's snapshot **REST** API (a REST API is a web-style interface driven by ordinary HTTP requests — the `curl` commands here; curl's `-X POST` flag sends an HTTP POST, the "do something" request type, instead of curl's default read-only GET). The full-snapshot call is `curl -X POST http://localhost:6333/snapshots`; a per-collection alternative exists: `curl -X POST http://localhost:6333/collections/<name>/snapshots`. **Restore path — what to do if an ingestion goes bad:** do NOT debug the live data. First list the available snapshots (`curl http://localhost:6333/snapshots`), then recover from the chosen one — either per collection (`PUT /collections/<name>/snapshots/recover` with the snapshot location in the JSON body), or by stopping the container and restoring the snapshot file into the mounted `qdrant_storage` volume per the Qdrant docs (https://qdrant.tech/documentation/concepts/snapshots/). Either way the KB is back at baseline N, as if the failed update had never happened.

☐ **Step 1 [ALL] — Create the three lifecycle scripts (two mode switches + the fresh-boot script).**
**Why:** the switch between modes must be one deliberate, repeatable action — not a remembered sequence of docker commands. Three small scripts encode the whole lifecycle: every KB update is `kb-mode-update.sh` → run ingestion → `kb-mode-serve.sh`, and every **fresh boot** (power-on or reboot) is one command, `kb-boot.sh` (v4.33) — needed because none of the KB containers auto-start at boot (deliberate: the *operator*, not the boot sequence, decides whether the box comes up SERVING or stays down for an UPDATE window), and because starting containers too early after a boot is a **known live failure** on this box (§1.5 experience: containers launched before the GPU driver and DNS were ready failed with CUDA-compatibility and name-resolution errors, fixed by host checks + a Docker restart). `kb-boot.sh` encodes exactly those host checks, then hands over to `kb-mode-serve.sh` so the actual start sequence lives in one place only.
**Before you run it:** the block below uses a **heredoc** ("here document") — the shell construct `<<'EOF' … EOF` that feeds everything between the two markers into a command as text; quoting the first marker (`'EOF'`) matters: the quotes stop YOUR shell from expanding `$variables` while writing the file — they must expand later, when the script runs — so the script text lands on disk exactly as written. Alternatively, paste the same content with an editor (`sudo nano /opt/p42/bin/kb-mode-update.sh`). One naming convention makes the scripts work: **start the 2.1.2 / 2.1.3 containers with explicit `--name` flags** (`vllm-llm` for the answer-LLM container, `vllm-embed` for embeddings, `reranker` for the reranker, `vllm-vl` for the :8002 captioning container — `qdrant` and `open-webui` are already named in their commands), because the scripts stop and start containers by those names. The scripts are *idempotent-ish*: each `docker` line ends in `|| true`, so re-running a script, or running it when some component is already in the target state, is harmless.
**Run (create the UPDATE-mode script):**
```bash
sudo mkdir -p /opt/p42/bin && sudo tee /opt/p42/bin/kb-mode-update.sh >/dev/null <<'EOF'
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
EOF
```
**Run (create the SERVING-mode script):**
```bash
sudo tee /opt/p42/bin/kb-mode-serve.sh >/dev/null <<'EOF'
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
EOF
```
**Run (create the fresh-boot script — v4.33):**
```bash
sudo tee /opt/p42/bin/kb-boot.sh >/dev/null <<'EOF'
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
EOF
```
**Run (make all three executable):**
```bash
sudo chmod +x /opt/p42/bin/kb-mode-update.sh /opt/p42/bin/kb-mode-serve.sh /opt/p42/bin/kb-boot.sh
```
**Expect / If not:** all three files exist and are executable (`ls -l /opt/p42/bin/`). **Error decode — `No such container: <name>` (v4.35, hit live on spark-9d0e):** `docker start` can only *restart* a container that already exists in Docker's inventory — it never creates one. The containers these scripts manage are **created** by the `docker run --name ...` commands spread through §2.1.2/2.1.3 (`qdrant` in 2.1.2.3, `vllm-llm` in 2.1.2, `vllm-embed` in 2.1.2.2, `reranker` and `open-webui` in their 2.1.2 steps, `vllm-vl` in 2.1.3.2). So this message always means "that container has not been created yet (or was removed)" — never "it failed to start" — and it is **expected, and harmless, if a mode script is run before §2.1.2 is complete**: each `docker` line ends in `|| true`, so the script prints the error and continues; the readiness probes at the end will then warn for the same reason. The scripts only become fully meaningful once the whole §2.1.2 stack exists — which is exactly why the formal switch rehearsal sits in §2.1.4 Step 2. Check what exists with `docker ps -a --format '{{.Names}}\t{{.Status}}'`, then create the missing container(s) with their §2.1.2/2.1.3 run commands. Note the deliberate design choice: `kb-boot.sh` is run **by hand** after each boot, not installed as an auto-start service — auto-starting the serving stack at boot would fight the mode-exclusive design (a box booted *for* an UPDATE window must not race into SERVING mode) and would hide the host-readiness failures this script exists to surface. If hands-off boot-to-serving is ever wanted (e.g. for the production enclave), that is a G2+ decision: a systemd unit calling this same script, recorded as such. **REHEARSE the switch once as a TEST** — done formally in 2.1.4 Step 2, after the stack below exists; do not consider this section complete until that rehearsal (including the snapshot/restore check) has been run.

> [!NOTE]
> **Powering the Spark down safely (v4.44).** Three rules. (1) **Never power off during an ingestion run** — let it finish or Ctrl-C it first; the manifest saves after every file, so the worst case of a clean interrupt is one file re-ingesting. (2) **No teardown is required before shutdown**: a normal OS shutdown stops Docker cleanly, which stops every container cleanly, and all of them survive as stopped containers; Qdrant's data is on disk in `~/p42/qdrant_storage/`. (3) **Always shut down gracefully** — `sudo shutdown -h now`, never a held power button: Qdrant flushes its writes on a clean stop, and a hard power cut mid-write is the one corruption path the pre-update snapshots do NOT cover. **Powering back up:** `sudo /opt/p42/bin/kb-boot.sh` (host checks → SERVING); if the next task is ingestion, follow with `sudo /opt/p42/bin/kb-mode-update.sh` and restart the VL container per 2.1.3.2 — or, while the stack is still under construction, the pragmatic minimum is `sudo swapoff -a` then `docker start qdrant vllm-embed vllm-vl`.

### 2.1.2 Serving stack — five components, in order (SERVING mode, all on Spark-1)

> [!NOTE]
> **(v4.16) Why the serving stack comes BEFORE the ingestion pipeline** — the order looks backwards ("surely the KB needs content first?") but is dependency-driven, three ways: (1) ingestion *writes into* Qdrant, which is stood up here in 2.1.2.3; (2) ingestion *embeds with* the BGE-M3 service stood up here in 2.1.2.2 — deliberately the same service queries will use; (3) UPDATE mode is defined as a transformation OF the serving stack (the mode scripts stop/start these containers by name), so the stack must exist before the first mode switch. What this section can NOT prove yet is retrieval over real content — each component is only smoke-checked empty here (expect "no documents found" from any retrieval test, that is normal), and the full proof deliberately waits until 2.1.4, after 2.1.3 has filled the database.

#### 2.1.2.1 Answer LLM (:8000) — ONE of two engine routes

☐ **Step 1 [DECISION] — Choose the engine that serves the answer LLM: vLLM (→ Step 2) or llama.cpp (→ Steps 3–4).**
**Why:** the answer LLM is the model that writes the cited answers; both baseline engines (§0.6) can serve it, with different strengths.
**Before you run it:** decide by these rules — then do Step 2 (vLLM) *or* Steps 3–4 (llama.cpp), not both at once (port 8000 is a single slot, §3.b):

- **Recommended: vLLM (NVIDIA aarch64 container)** — optimised for ARM64 + Blackwell with NVFP4/FP8, PagedAttention, continuous batching (vLLM's techniques for using memory efficiently and serving many requests at once), OpenAI-compatible API. Playbook: https://github.com/NVIDIA/dgx-spark-playbooks/tree/main/nvidia/vllm &nbsp;|&nbsp; build page: https://build.nvidia.com/spark/vllm
- **Simpler alternative for the first end-to-end pass: llama.cpp server** — the second baseline engine per §0.6, most battle-tested on this hardware, explicit quant/context control.
- **Recommendation:** llama.cpp for the first pass and single-user work; switch to NGC vLLM when you need concurrency, agents, or NVFP4 models.

Good single-box answer models: `gpt-oss-120b` (MoE, best workhorse — via llama.cpp; measured ~35–46 tok/s baseline, ~55–59 tok/s with tuned llama.cpp/vLLM per NVIDIA), `nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-NVFP4` (MoE, vLLM — note the doubled "NVIDIA" in the handle), `nvidia/Llama-3.3-70B-Instruct-NVFP4` (dense, quality-leaning, slower).

☐ **Step 2 [ROUTE: vLLM — only if Step 1 chose vLLM; this is the alternative to Steps 3–4] — Serve the answer LLM in the NGC vLLM container.**
**Why:** one container gives an OpenAI-compatible endpoint on port 8000 that every client in this runbook can talk to.
**Before you run it:** use the NVIDIA/NGC aarch64 vLLM image (`nvcr.io/nvidia/vllm:<tag>`, e.g. `26.02-py3` or later) — **confirm the exact tag in the playbook first.** Key flags: `--gpu-memory-utilization` (the share of the memory pool this instance claims; default 0.92 in current vLLM; older builds 0.9), `--max-model-len` (the maximum context length the server reserves KV-cache memory for — reduce on OOM), `--max-num-seqs` (how many requests may be processed simultaneously — reduce for long context). Use CUDA 13.0+ and the `26.02-py3` (or later) container. Read all four boxes below BEFORE launching:

> [!IMPORTANT]
> **v0.4 flag corrections (community):** four hard-won rules for every vLLM launch on this box, each with its reason spelled out.
>
> - **Memory share:** set `--gpu-memory-utilization` to **0.6–0.75 when other services co-reside** (the KB stack: Qdrant, Open WebUI, embeddings — see §1.7). The flag claims a share of the *single shared 128 GB pool*, and whatever vLLM takes, the co-resident services cannot have. 0.85 is the maximum even for a solo big model — 0.9 risks the §1.7 zombie-OOM hang (the whole machine locks up, physical reboot required).
> - **Stability under load:** `--ipc=host` (let the container share the host's inter-process shared memory) plus the memlock ulimits are required under load — without them the server can crash mid-generation once real traffic arrives (the exact flags and their meanings are in the §1.5 flag rationale).
> - **NVFP4 MoE models need `--moe-backend marlin`.** The GB10 GPU has no native FP4 compute path in vLLM's stock GPU kernels; the Marlin backend supplies one. Without the flag the model loads and appears to work but produces garbled `!!!!!` output. Also set the environment variables `VLLM_FLASHINFER_MOE_FP4=1` / `VLLM_USE_FLASHINFER_MXFP4_MOE=1` per model class, as that model's playbook directs.
> - **Where vLLM itself comes from:** never install vLLM from plain PyPI on this box — those wheels ship without sm_121 GPU kernels (the compute programs compiled for this GPU's architecture), so nothing runs on the GPU. Use the NGC image or the nightly cu130 wheel index (`wheels.vllm.ai/nightly/cu130`) only.
>
> **(v4.2) Two further standing rules for the vLLM recipes:** (1) add **`--kv-cache-dtype fp8`** to every vLLM launch by default — it stores the KV cache (the model's working memory of the conversation) in 8-bit numbers, which on GB10 roughly halves the cache's memory cost vs fp16 at no meaningful quality cost. Confirm that cost really is negligible with the Part C quality spot-check the first time each model uses it. Note the llama.cpp side already enforces its own, stricter ≥`q8_0` KV rule — on that engine anything lower produces token loops. (2) **Speculative decoding follows the §0.6 GATED-DEFAULT policy (v4.3)** — it is the required target profile for the primary interactive models, but a drafter model enters this recipe only through its mandatory Part C gate (acceptance ≥ 60 % + net speedup + clean template smoke test, with the drafter repo-pinned and quantisation-matched). Until that gate has been passed — and whenever it fails (logged) — the recipe serves non-speculative.

> [!IMPORTANT]
> **Total vLLM memory budget (v0.8 clarification):** `--gpu-memory-utilization` is set per instance, but every instance draws from the same shared 128 GB pool — the instances do not know about each other, so nothing stops their combined claims from exceeding what the machine has. The rule that prevents that: **all vLLM instances together stay ≤ ~0.75** when the KB services (Qdrant, Open WebUI) co-reside, leaving the rest of the pool for them and the OS. Worked split: answer LLM 0.55 + embeddings 0.15. (The VL captioning instance at 0.3 runs only in UPDATE mode, §2.1.3, when the answer LLM is torn down — the two are never co-resident, so their shares never add up.) A single solo model may go to 0.85.

> [!WARNING]
> **VERIFY — two checks before the first launch.** (1) Confirm the exact NVIDIA aarch64 vLLM image tag in the playbook before pulling — tags change monthly, and this runbook cannot know today's newest. Then prove the image really is built for this processor: run `docker run --rm <vllm-arm64-image> uname -m` and expect `aarch64` (a wrong-architecture image only fails later, with `exec format error` — §1.3 Step 4). (2) Verify the tag's **entrypoint form** — that is, what the container runs by default. The command below uses the NGC-standard `vllm serve <model> <flags>` subcommand form; but if the chosen tag's entrypoint already wraps vllm, typing `vllm serve` again would fail, and the bare-flags form (`--model ...`) is needed instead. The §1.5 `docker inspect` check settles this deterministically — record which form works in the build log.

> [!NOTE]
> **Updated 2026-07-10:** Docker Hub `vllm/vllm-openai:latest` is now **multi-arch (amd64 + arm64)** — the old "amd64-only, exec format error" warning no longer holds. The NVIDIA NGC image (`nvcr.io/nvidia/vllm:26.02-py3` or later, per the playbook) remains the preferred choice for Blackwell/NVFP4 optimisation; whatever you pull, run the `uname -m` check anyway (Golden Rule 2).

**Run:**
```bash
docker run --name vllm-llm --gpus all -p 8000:8000 \
  --ipc=host --ulimit memlock=-1 --ulimit stack=67108864 \
  -e HF_TOKEN=$HF_TOKEN -e HF_HUB_DISABLE_XET=1 -v ~/.cache/huggingface:/root/.cache/huggingface \
  nvcr.io/nvidia/vllm:26.07-py3 \
  vllm serve nvidia/Qwen3-32B-NVFP4 --gpu-memory-utilization 0.55   # 0.55 per the §1.7 worked budget (0.55 LLM + 0.15 embeddings ≤ 0.75 co-resident) — 0.70 here would bust it

# test
curl http://localhost:8000/v1/chat/completions -H "Content-Type: application/json" \
  -d '{"model":"nvidia/Qwen3-32B-NVFP4","messages":[{"role":"user","content":"hi"}]}'
```
**Expect / If not:** the test `curl` returns JSON with a coherent assistant reply. Garbled `!!!!!` output on an NVFP4 MoE model → the `--moe-backend marlin` flag is missing (see the IMPORTANT box above). `exec format error` → wrong-architecture image (§1.3 Step 4). Crash citing memory → another model is loaded, or the budget rules above were exceeded.

**Option A2 (v4.18) — gpt-oss-120b on vLLM: the multi-user KB seat.** The Qwen command above is the verified-matrix example; the project's KB workhorse **gpt-oss-120b** can equally hold this seat on vLLM. When to prefer which: gpt-oss-120b's *canonical* route is llama.cpp (Step 3–4 — where the community reference numbers were measured; fastest single-user) — but **vLLM is the right engine when several users query the KB at once** (continuous batching is vLLM's strength and llama.cpp's weakness). The trade is settled by measurement, not opinion: run Part C's concurrency sweep on both routes and record which serves the KB seat.

**Before you run it:** the repo is **`openai/gpt-oss-120b`** (OpenAI's original — it ships natively in MXFP4 quantisation, so no separate `nvidia/` build exists). Two things change vs the Qwen command: the env `VLLM_USE_FLASHINFER_MXFP4_MOE=1` enables the MXFP4 mixture-of-experts kernels (same class of need as Marlin for NVFP4 — without it the format has no fast path on this chip), and the memory budget moves: the weights alone are ~61 GB, so 0.55 (~66 GB share) would leave almost no KV cache — use **0.60 with `--max-model-len 32768`** (0.60 + 0.15 embeddings = 0.75, exactly at the co-residency ceiling). Pre-download first (`hf download openai/gpt-oss-120b`, ~65 GB, in tmux) and drop caches before the load — at this size the §1.7 habit is load-bearing.

**Run:**
```bash
sudo sh -c 'sync; echo 3 > /proc/sys/vm/drop_caches'    # §1.7 pre-load habit — mandatory at this model size
docker run --name vllm-llm --gpus all -p 8000:8000 \
  --ipc=host --ulimit memlock=-1 --ulimit stack=67108864 \
  -e HF_TOKEN=$HF_TOKEN -e HF_HUB_DISABLE_XET=1 \
  -e VLLM_USE_FLASHINFER_MXFP4_MOE=1 \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  nvcr.io/nvidia/vllm:26.07-py3 \
  vllm serve openai/gpt-oss-120b --gpu-memory-utilization 0.60 --max-model-len 32768
```
**Expect / If not:** startup reaches "Application startup complete" (first load of a 61 GB model takes minutes — watch `free -h` climb); the test `curl` (adjust the model name) returns a coherent reply. **Gates before this becomes the recorded KB seat:** the §3.a.1 three-turn template smoke test MUST pass on this exact combination — gpt-oss uses its own "harmony" chat format, natively handled by recent vLLM but *verify on your pinned build*, tool-calling especially — and the full flag set goes in the STEP RECORD.

☐ **Step 3 [ROUTE: llama.cpp — only if Step 1 chose llama.cpp; Steps 3–4 together are the alternative to Step 2] — Build llama.cpp once.**
**Why:** llama.cpp is compiled from source on the box, targeting this GPU exactly.
**Before you run it:** the `121a` architecture suffix enables native FP4 — do a clean rebuild if changing arch. *(v0.11)* plain `sm_121` targets and native-arch autodetection have failed with `Instruction 'mma with block scale' not supported on .target 'sm_121'` (llama.cpp #18425, a recurring regression class). Keep the explicit `121a`; **if a build still fails on that error, add `-DGGML_NATIVE=OFF` and retry before touching anything else.**
**Run:**
```bash
git clone https://github.com/ggml-org/llama.cpp && cd llama.cpp
# -B build = configure the build into the build/ folder; -DGGML_CUDA=ON = build the CUDA GPU backend;
# -DCMAKE_CUDA_ARCHITECTURES=121a = compile for exactly this GPU (GB10; the "a" suffix enables native FP4);
# -DGGML_CUDA_FA_ALL_QUANTS=ON = build flash-attention kernels for every KV-cache quant type (needed for the q8_0 KV flags used at serve time)
cmake -B build -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=121a -DGGML_CUDA_FA_ALL_QUANTS=ON
cmake --build build -j        # --build = compile what was just configured; -j = use all CPU cores in parallel
```
**Expect / If not:** the build completes without error. On the #18425-class error above → add `-DGGML_NATIVE=OFF` (turns off host-CPU feature autodetection, the part that mis-fires) and rebuild.

☐ **Step 4 [ROUTE: llama.cpp — continues Step 3] — Serve gpt-oss-120b with the community-validated flag set.**
**Why:** this serves the workhorse answer model as an OpenAI-compatible endpoint on port 8000.
**Before you run it — flag rationale (community-measured), one flag at a time:** `-m` names the GGUF model file to load, and `--port 8000` puts the server on the standard answer-LLM port (§3.b). `-ngl 999` sets how many of the model's layers are offloaded to the GPU — 999 simply means "all of them", i.e. full GPU offload; never use the CPU-MoE offload flags you may see in other guides — those exist for VRAM-limited discrete GPUs and only slow this unified-memory machine down. `-fa on` enables flash attention, the faster attention implementation (the reason the build switched on `-DGGML_CUDA_FA_ALL_QUANTS=ON`). `--no-mmap` makes llama.cpp read the model fully into memory instead of memory-mapping the file — effectively mandatory on unified memory, where the mapped file competes with the GPU for the same pool. `-b 2048 -ub 2048` set the batch and micro-batch sizes — how many prompt tokens are processed per step — to the community-tuned value for this hardware. `--cache-type-k q8_0 --cache-type-v q8_0` store the KV cache in 8-bit; do not go below `q8_0` — a lower-precision KV cache produces token loops and gibberish. **(v4.24) And do not treat `q8_0` itself as universally safe either: it is a per-model floor, not a universal setting.** Community-verified 2026-08: on DeepSeek-V4-Flash-0731 an 8-bit (`q8_0`) KV cache produces garbled output — that model must run its KV cache at 16-bit, which simply means omitting both `--cache-type-*` flags. The standing rule from this: **KV-cache quantisation joins the per-model validation checklist alongside the §3.a.1 template smoke test** — verify it on each model before recording it in that model's flag set. `--jinja` turns on the model's **chat template** — the small script, written in the Jinja templating language, that formats the conversation and tool definitions into the exact text layout the model was trained on — and is needed for **tool calling** (the mechanism by which the model asks its client to run a named tool and return the result; every agent workflow rests on it — known pitfalls in §3.a.1). Remember the §1.7 pre-load cache flush before this large load.
**Run:**
```bash
# serve gpt-oss-120b (GGUF/MXFP4) with the community-validated flag set — OpenAI-compatible on :8000
./build/bin/llama-server -m <gpt-oss-120b-mxfp4.gguf> --port 8000 \
  -ngl 999 -fa on --no-mmap -b 2048 -ub 2048 \
  --cache-type-k q8_0 --cache-type-v q8_0 --jinja
```
**Expect / If not:** server up on :8000; gpt-oss-120b ≈ 35–46 tok/s decode, ~1,700–1,800 tok/s prefill (**decode** = generating the answer token by token; **prefill** = the much faster initial reading of the prompt — see Annex B; canonical figures, Part C). Well below ~35 tok/s → suspect the silent CPU fallback (Step 6) or a wrong build.

☐ **Step 5 [OPTIONAL — llama.cpp route only] — Automate the drop-cache habit for an always-on llama-server.**
**Why:** humans forget the §1.7 pre-load cache flush; a service can do it for them.
**Before you run it:** only relevant if llama-server graduates from "run when needed" to an always-on service. Note the deliberate port choice inside the unit file.

> [!TIP]
> **(v0.12, per technical review) Automate the drop-cache habit for permanent services.** Wrap llama-server in a systemd unit whose `ExecStartPre` performs the flush automatically, so every (re)start is safe:
> ```ini
> # /etc/systemd/system/llama-server.service (excerpt)
> [Service]
> ExecStartPre=/bin/sh -c 'sync; echo 3 > /proc/sys/vm/drop_caches'
> ExecStart=/home/<user>/llama.cpp/build/bin/llama-server -m <model.gguf> --port 8001 <flag set above>
> # NOTE: the service deliberately uses port 8001 (not 8000) so it never collides with a
> # vLLM container or an interactively-launched llama-server on 8000 — point clients accordingly.
> Restart=on-failure
> ```
> For the Docker-managed vLLM containers the equivalent is procedural: the runbooks already prescribe the flush immediately before every `docker run`/`docker start` of a model container — keep that pairing whenever containers are recreated.

☐ **Step 6 [ALL — run on whichever engine you chose] — The silent-CPU-fallback check.**
**Why:** a mis-built stack can quietly run the model on the CPU — everything *works*, just absurdly slowly.
**Before you run it:** a completion must be generating while you check.
**Run:**
```bash
nvidia-smi
```
**Expect / If not:** during generation, GPU utilisation >0 in `nvidia-smi` and CPU NOT pegged at 100%. 0% GPU + 100% CPU = the model is running on CPU (wrong build arch or failed offload — historically also the now-removed Ollama Docker image). gpt-oss-120b well below ~35 tok/s is the tell.

#### 2.1.2.2 Embeddings (:8080) and reranker (:8081) — one route decision, two required endpoints

☐ **Step 1 [DECISION] — Choose the embeddings route: vLLM mainline (→ Step 2) or TEI (→ Step 4). The reranker (Step 3) is required on BOTH routes and is not part of this decision.**
**Why:** the KB needs two endpoints from this subsection: an **embeddings** endpoint (BGE-M3, :8080) and a **reranker** endpoint (bge-reranker-v2-m3, :8081) — both are part of the SERVING stack the mode scripts manage. On this ARM64 box not every packaging of them runs. **The decision below concerns the embeddings route only** (vLLM mainline vs TEI): vLLM has no rerank endpoint at all, so the reranker is served by a TEI-family container *regardless* of which embeddings route you pick — skipping it is not an option (v4.38 — an operator correctly following the mainline path ended up with no reranker, because its launch command used to live inside the "(Alternative)" step).
**Before you run it** — the decision rule, including what was previously a post-command warning:

- **Mainline (lowest-risk on arm64): serve BGE-M3 via the NVIDIA aarch64 vLLM container** (confirmed arm64) → Step 2.
- **TEI (Text Embeddings Inference — Hugging Face's dedicated server for embedding-class models).** **(v4.19) What this choice changes and what it does not:** output quality is **identical either way** — both routes serve the same `BAAI/bge-m3` weights, and an embedding is a deterministic computation of the model, so this decision cannot make retrieval better or worse. "Cleaner API" means the *interface shape*: TEI has purpose-built endpoints — `/embed` (texts in → vectors out) and, importantly, `/rerank` (query + passages in → relevance scores out), because reranking is a different operation from embedding and vLLM has no natural endpoint for it (hence the workaround routes here). TEI is also leaner in principle (small specialised server, high-throughput embedding batching, vs vLLM carrying a full LLM engine to serve a 2 GB model). **The decider is maturity, not elegance:** but **CONFIRMED 2026-07-10 (was "unverified"): stock TEI GPU images are x86_64 only** (per-arch tags turing/86/89/hopper/blackwell); the only prebuilt arm64 image is CPU (`cpu-arm64-*`). So stock TEI-with-GPU will NOT run on the Spark without building `Dockerfile-cuda` yourself with `--platform linux/arm64` (the build flag that forces the image to target ARM64). TEI repo: https://github.com/huggingface/text-embeddings-inference
- **Last resort (no image-arch risk):** `pip install sentence-transformers` in a venv (pure PyTorch on the Spark GPU) for both embeddings and cross-encoder reranking.

(The reranker image options that used to sit in this list have moved into **Step 3**, where the reranker is actually launched — they were decision-support for a component that is not optional.)

☐ **Step 2 [ROUTE: vLLM mainline — only if Step 1 chose vLLM; this is the alternative to Step 4] — Serve BGE-M3 as an embedding model via vLLM.**
**Why:** gives `/v1/embeddings` on port 8080 with no image-architecture risk.
**Before you run it:** current vLLM uses `--runner pooling` — the flag that runs the model as a pooling/embedding model, returning vectors instead of chat text (the older `--task embed` is DEPRECATED/removed on main; it may still work on older pinned images — use whichever the container's vLLM accepts, and record which).
**Run:**
```bash
# embeddings via vLLM, reachable at /v1/embeddings on port 8080
# (-p 8080:8000 = the host's port 8080 maps onto the container's internal 8000, so embeddings live on :8080)
docker run --name vllm-embed --gpus all -p 8080:8000 \
  --ipc=host --ulimit memlock=-1 --ulimit stack=67108864 \
  -e HF_TOKEN=$HF_TOKEN -e HF_HUB_DISABLE_XET=1 -v ~/.cache/huggingface:/root/.cache/huggingface \
  nvcr.io/nvidia/vllm:26.07-py3 \
  vllm serve BAAI/bge-m3 --runner pooling --gpu-memory-utilization 0.15
# (v4.20, hit live) vllm serve = the explicit subcommand this tag's entrypoint requires — bare
# --model flags fail with "exec: --: invalid option"; --name vllm-embed = the exact name the
# kb-mode scripts manage this container by; --gpu-memory-utilization 0.15 = the embeddings
# share of the §1.7 budget (WITHOUT it vLLM defaults to ~0.92 and grabs the pool next to the
# answer LLM); --ipc=host + ulimits = the shared-memory settings the container itself asks for
```
**Expect / If not:** the container serves `/v1/embeddings` on :8080. If the tag rejects `--runner pooling`, try the deprecated `--task embed` (older pinned images) and record which form worked.

☐ **Step 3 [ALL — required on BOTH embeddings routes] — Serve the reranker (bge-reranker-v2-m3) on :8081.**
**Why:** the reranker is the precision stage of the baseline pipeline (hybrid retrieval finds candidates, the cross-encoder re-orders them by true relevance — the "hybrid + rerank" the KB trade-off study made the deployed baseline). It is **not optional and not part of the Step 1 decision**: vLLM cannot serve it (no rerank endpoint exists there), so whichever embeddings route you chose, the reranker runs as its own TEI-family container named `reranker` — the exact name the mode scripts manage.
**Before you run it:** stock TEI GPU images are **x86_64-only** (Step 1), so an **arm64-verified build** is needed. Candidate images, in order: **(1)** the community arm64 build `ddosify/text-embeddings-inference:blackwell-1.8.3-baai-bge-reranker-v2-m3` (single model-specific reranker tag; source: https://hub.docker.com/r/ddosify/text-embeddings-inference ); **(2)** `hwdsl2/docker-embeddings` built from its `Dockerfile.arm64` (https://github.com/hwdsl2/docker-embeddings/blob/main/Dockerfile.arm64 ); **(3)** self-build TEI's `Dockerfile-cuda` with `--platform linux/arm64`. These are **community images — engine-policy candidates, not validated baseline** (§0.6): verify the architecture before first use, record image tag + digest in the STEP RECORD, and treat a passing smoke test below as the WP1 validation that admits it. Memory note: the reranker is a ~2 GB-class model — negligible against the §1.7 budget.
**Run (v4.41 — corrected against the live spark-9d0e session; two facts first):** this image sets `text-embeddings-router` as its **ENTRYPOINT** — the program Docker runs when the container starts — so anything typed after the image name becomes *arguments to the router*, not a command of its own; that is why the architecture check must override the entrypoint with `--entrypoint uname`. And despite the model-specific tag name, the router still **requires `--model-id`**: the tag bakes the model *weights* into the image, but not a launch default — without the flag the container exits immediately with "the following required arguments were not provided: --model-id".
```bash
# Architecture check FIRST (expect: aarch64 - anything else is the wrong build).
# --entrypoint uname REPLACES the image's default program (the router) with
# uname for this one run; the trailing -m is then an argument to uname:
docker run --rm --entrypoint uname \
  ddosify/text-embeddings-inference:blackwell-1.8.3-baai-bge-reranker-v2-m3 -m

# Launch the reranker - --name reranker = the exact name the mode scripts manage;
# -p 8081:80 = TEI's internal port 80 appears on the host as 8081;
# --model-id = REQUIRED (see above), everything after the image name goes to the router:
docker run -d --name reranker --gpus all -p 8081:80 \
  ddosify/text-embeddings-inference:blackwell-1.8.3-baai-bge-reranker-v2-m3 \
  --model-id BAAI/bge-reranker-v2-m3

# Record the pinned artefact (tag + digest) for the STEP RECORD:
docker inspect reranker --format '{{.Config.Image}} {{.Image}}'

# Smoke test - the exact call shape the benchmark harness uses (expect a JSON
# array of {index, score}, with the relevant text scoring clearly higher):
curl -s http://localhost:8081/rerank -H 'Content-Type: application/json' \
  -d '{"query":"thermal margin","texts":["thermal design margins are applied to predictions","the cafeteria opens at nine"]}'
```
**Expect / If not:** `aarch64` from the first command; the container stays `Up` (`docker ps -a --filter name=reranker`); the smoke test returns clearly separated scores — the live spark-9d0e validation run returned `[{"index":0,"score":0.8376},{"index":1,"score":0.0000167}]`, and that passing test IS this community image's WP1 admission under §0.6 (record tag, digest and scores in the STEP RECORD). Decodes: **empty reply from curl** → the container is not (yet) running — check `docker ps -a --filter name=reranker` and give a freshly started one a few seconds to load the model; **`Exited (2)` + logs showing "required arguments were not provided: --model-id"** → the launch was missing the `--model-id` flag above — remove the dead container (`docker rm -f reranker`) and relaunch with the full command; **`error: unexpected argument 'uname' found`** → the entrypoint override was omitted on the architecture check; **`exec format error`** → wrong architecture — try candidate (2) or (3). A failed attempt always leaves a dead container holding the name: `docker rm -f reranker` before every relaunch. If all three candidate images fail, the sentence-transformers last-resort from Step 1 covers reranking too (record whichever route passed as the validated one).

☐ **Step 4 [ROUTE: TEI — only if Step 1 chose TEI; this is the alternative to Step 2] — TEI container for the embeddings side.**
**Why:** kept for the case where a TEI arm64 build (community or self-built) checks out for **embeddings** — same output quality as Step 2 (same model weights), but a purpose-built `/embed` endpoint and a leaner memory footprint (see the comparison in the Step 1 option list). Proven-but-awkward (vLLM) beats elegant-but-unproven (TEI) until the arm64 story firms up. The reranker is NOT part of this alternative — it already runs from Step 3.
**Before you run it:** the stock command below will fail on the Spark with the stock GPU tags (x86_64-only, per Step 1) — substitute an arm64-verified image and run the `uname -m` architecture check first. Do not run this while `vllm-embed` holds :8080 — one embeddings server per port (stop the other first, and record which route is the validated one).
**Run:**
```bash
# embeddings via TEI (SUBSTITUTE an arm64-verified image for the stock tag below)
docker run --name tei-embed --gpus all -p 8080:80 -v $PWD/data:/data \
  ghcr.io/huggingface/text-embeddings-inference:latest --model-id BAAI/bge-m3
# endpoint: POST /embed
```
**Expect / If not:** `POST /embed` answers on :8080. `exec format error` → you pulled a stock x86_64 GPU tag — go back to the Step 1 decision rule (vLLM mainline, or an arm64-verified build).

#### 2.1.2.3 Qdrant vector database (:6333 / :6334, persistent volume)

☐ **Step 1 [ALL] — Start Qdrant with a persistent volume.**
**Why:** Qdrant is the vector database that holds every **chunk** (a passage-sized piece of a document — retrieval works on chunks, not whole files) and page vector the ingestion pipeline (2.1.3) produces; the mounted folder makes the data survive container restarts.
**Before you run it (v4.37 — restructured after live operator confusion; no commands in this paragraph):** three facts to know, then ONE command block to run. (1) **Nothing to install first** — Qdrant ships as a Docker image, and exactly as §1.3 Step 2 explained, `docker run` **downloads the image automatically on first use** (a ~100 MB pull from Docker Hub), then starts it; later runs start instantly from the local copy. Official install doc, for reference only: https://qdrant.tech/documentation/installation/ (multi-arch image, arm64 published). (2) **Where you run it matters:** the command mounts `$(pwd)/qdrant_storage` — a folder *under the directory you are standing in* — as the database's permanent home, which is what makes the data survive container restarts. The Run block therefore starts with `cd ~/p42`, so the database always lives at `~/p42/qdrant_storage/` — do not skip that line, or the database lands wherever you happened to be standing. That folder must be a **local/POSIX filesystem** (the Spark's own disk — fine) — NOT a network mount (NFS) or object storage (S3). (3) **One known platform issue to watch for at start:** some ARM hosts hit a historical jemalloc "Unsupported system page size" error (https://github.com/qdrant/qdrant/issues/4298); DGX OS's default page size should be fine, but the Expect check below confirms the container started cleanly rather than assuming it.

**Run (start Qdrant — this is the only block needed to bring it up):**
```bash
# cd ~/p42: pins the database folder to ~/p42/qdrant_storage (see Before-you-run-it).
# -d = run detached, in the background; --name qdrant = a fixed container name, so the §2.1 mode scripts
# can stop/start it by name; -p = publish both Qdrant ports; -v = keep the database in a host folder.
cd ~/p42
docker run -d --name qdrant \
  -p 6333:6333 -p 6334:6334 \
  -v $(pwd)/qdrant_storage:/qdrant/storage \
  qdrant/qdrant:latest
```
**Expect / If not:** ports 6333 (HTTP/REST + dashboard) and 6334 (gRPC) up; `docker logs qdrant` shows a clean start (no jemalloc/page-size error) and the dashboard loads at `http://localhost:6333/dashboard`. If the jemalloc error appears → the known aarch64 page-size issue (link above) — record it and raise before proceeding.

**Record (AFTER the start — STEP RECORD provenance duty):** two commands that only work once the container exists; their output goes into the STEP RECORD, because the enclave build needs a **pinned artefact** (exact version + digest), not `:latest`:
```bash
# Image tag + content digest — copy both into the STEP RECORD:
docker inspect qdrant --format '{{.Config.Image}} {{.Image}}'
# Confirm the image really is the arm64 build (expect: aarch64):
docker run --rm qdrant/qdrant:latest uname -m
```

#### 2.1.2.4 KB user interface — Open WebUI (:3000, confirmed arm64)

☐ **Step 1 [ALL] — Start Open WebUI.**
**Why:** Open WebUI is the chat interface users (and Part D's sandboxes) see; it also has built-in RAG.
**Before you run it:** Open WebUI docs explicitly state it works on **Linux ARM64 incl. DGX Spark**, and NVIDIA ships an **Open WebUI playbook**. One thing to know about the `--add-host=host.docker.internal:host-gateway` flag in the command: `host.docker.internal` (the name a container uses to reach services on its host machine) needs Docker v20.10+ (DGX OS ships newer — fine) and can be blocked by restrictive iptables/ufw firewall configurations on some Linux setups; if the UI cannot reach the model server, test connectivity from inside the container and fall back to the Spark's LAN IP instead of `host.docker.internal`. Docs: https://docs.openwebui.com &nbsp;|&nbsp; playbook: https://github.com/NVIDIA/dgx-spark-playbooks/tree/main/nvidia/open-webui
**Run:**
```bash
# -d = background; -p 3000:8080 = the UI's container port 8080 appears on the host as 3000;
# --add-host = teach the container the host.docker.internal name (caveat above);
# -v open-webui:... = a named Docker volume for its data; --restart always = come back automatically after reboots/crashes
docker run -d -p 3000:8080 \
  --add-host=host.docker.internal:host-gateway \
  -v open-webui:/app/backend/data \
  --name open-webui --restart always \
  ghcr.io/open-webui/open-webui:main
```
**Expect:** the UI loads at `http://<spark-1-ip>:3000`.

☐ **Step 2 [ALL] — Configure Open WebUI to use the local endpoints.**
**Why:** out of the box it knows nothing about the Spark's model, embedding and reranker servers.
**Before you run it:** use `host.docker.internal` in every URL because the model servers run on the host, not in the Open WebUI container. For the reranker, **give the FULL endpoint path** (e.g. `http://host.docker.internal:8081/rerank`) — Open WebUI does not auto-append the path (env vars: `RAG_RERANKING_ENGINE=external`, `RAG_EXTERNAL_RERANKER_URL`).

> [!NOTE]
> **Project 42 note:** Open WebUI is also the surface for the **discipline sandboxes and familiarisation sessions (Part D)** — while you are in Admin Settings, note where user accounts and per-user knowledge collections are managed; you will need them in Part D. Chat history/logging stays ON (Golden Rule 5).

**Run (in the browser — browse to `http://<spark-1-ip>:3000`, create the first admin account):**
1. **Admin Settings → Connections → OpenAI → Add Connection.** URL = `http://host.docker.internal:8000/v1` (vLLM or llama-server); API key = any string.
2. **Admin Settings → Documents / RAG:** set the **embedding model** connection to the BGE-M3 endpoint (`http://host.docker.internal:8080/...`); enable **hybrid search** (searching by exact keywords AND by meaning/embeddings at the same time, then merging the two result lists); enable the **reranker** with engine **external** and point it at bge-reranker-v2-m3 with the full endpoint path per the caveat above. Open WebUI has built-in RAG and can use Docling as its content extractor (`CONTENT_EXTRACTION_ENGINE=docling` + `DOCLING_SERVER_URL`). **(v4.2) Fusion tuning knob:** when hybrid search is on, the method that merges the keyword and semantic result lists matters — prefer **Reciprocal Rank Fusion (RRF)** where the setting is exposed (in Open WebUI or in our own pipeline) before the reranker pass, and validate the choice on the golden question set (the **golden set** is the project's fixed list of test questions with known correct answers — the same questions every time, so quality changes are measurable) rather than by feel; it typically helps most on tables/datasheet-style content (UC-OPS-2, UC-DB-1).
3. Build a **Knowledge base** (Workspace → Knowledge → create a collection, upload documents into it through the UI), then attach it in chat **via `#`**: type `#` as the first character of a message, a picker lists your Knowledge collections, click one and it attaches to the conversation as a chip — from then on, questions in that chat are answered through retrieval over that collection. (v4.48 clarification: `#` searches **only** collections uploaded through the Open WebUI interface — it does NOT see the documents ingest.py put into the project's own Qdrant collections; those are exercised by the benchmark harness. Two parallel retrieval paths, deliberately using the same embedder and reranker services.)
**Expect:** a chat with the Knowledge base attached returns answers using the local model, embeddings and reranker.

☐ **Step 3 [ALL] — Wire the PROJECT KB into the chat picker: the "Project 42 KB" Function (v4.50).**
**Why:** this is the missing bridge between the two retrieval paths: out of the box, Open WebUI's chat can only search its own uploaded collections (`#`, path B) — it cannot see the project's Qdrant collections that ingest.py fills. A **Function** of type *pipe* is Open WebUI's plugin mechanism for exactly this: a small Python class that appears as a **selectable model in the chat picker** and, when chosen, answers by running the project's own pipeline — BGE-M3 → Qdrant `p42_text` → reranker → answer LLM, with the same grounding prompt as the benchmark harness and `ask.py`, and a source list appended to every answer.
**Before you run it:** SERVING mode (all four services up). The Function's code runs **inside the Open WebUI container**, so it reaches the host services via `host.docker.internal` — if a test chat later reports a KB ERROR naming a service, and the service is demonstrably up, edit the Function's **Valves** (the gear icon on the Function entry) and replace the hostname with the Spark's LAN IP in every URL. **Status: assistant-drafted, needs its live validation on the box** — the Expect below is the admission test. Known v1 limitation, by design: retrieval runs on the **latest question only** (no conversation memory in retrieval); each question should be self-contained.
**Run (in the browser):** Admin Panel → **Functions** → **+** (new Function) → set the name to `Project 42 KB` → replace the template code with the block below → **Save** → flip the Function's **enable toggle** on. Then open a **new chat** and pick **Project 42 KB** in the model dropdown.

```python
"""
title: Project 42 KB
version: 0.1
description: Grounded, cited Q&A over the project KB (Qdrant p42_text) via the
             project pipeline - BGE-M3 -> Qdrant -> reranker -> answer LLM.
"""
import requests
from pydantic import BaseModel, Field


class Pipe:
    class Valves(BaseModel):
        EMBED_URL: str = Field(default="http://host.docker.internal:8080/v1/embeddings")
        EMBED_MODEL: str = Field(default="BAAI/bge-m3")
        QDRANT_URL: str = Field(default="http://host.docker.internal:6333")
        COLLECTION: str = Field(default="p42_text")
        RERANK_URL: str = Field(default="http://host.docker.internal:8081/rerank")
        LLM_URL: str = Field(default="http://host.docker.internal:8000/v1/chat/completions")
        LLM_MODEL: str = Field(default="auto",
                               description="auto = discover from /v1/models (vLLM needs the real name)")
        TOP_K: int = Field(default=20)
        CONTEXT_K: int = Field(default=5)
        MAX_TOKENS: int = Field(default=700)

    # (v4.61, Run-2 lesson D1) 'in the form [doc | section]' made Qwen3
    # sometimes copy the template literally ('[doc | ...]' citations).
    SYSTEM_PROMPT = (
        "You answer questions using ONLY the provided context. "
        "Each context passage begins with its source label in square "
        "brackets. Cite every claim by copying that passage's source label "
        "EXACTLY as shown, brackets included. Never write placeholder words "
        "such as 'doc' or 'section' inside a citation. If the context does "
        "not contain the answer, say exactly: The corpus does not contain "
        "this information. Do not guess and do not use outside knowledge.")

    def __init__(self):
        self.valves = self.Valves()

    def pipe(self, body: dict) -> str:
        v = self.valves
        q = ""
        for m in reversed(body.get("messages") or []):
            if m.get("role") == "user":
                c = m.get("content")
                q = c if isinstance(c, str) else " ".join(
                    p.get("text", "") for p in c if isinstance(p, dict))
                break
        if not q.strip():
            return "Ask a question about the ingested Project 42 knowledge base."
        try:
            vec = requests.post(v.EMBED_URL, timeout=60, json={
                "model": v.EMBED_MODEL, "input": q}).json()["data"][0]["embedding"]
        except Exception as e:
            return "KB ERROR - embeddings service unreachable (%s): %r" % (v.EMBED_URL, e)
        try:
            hits = requests.post(
                v.QDRANT_URL + "/collections/" + v.COLLECTION + "/points/search",
                timeout=60, json={"vector": vec, "limit": v.TOP_K,
                                  "with_payload": True}).json()["result"]
        except Exception as e:
            return "KB ERROR - Qdrant unreachable (%s): %r" % (v.QDRANT_URL, e)
        chunks = [{"text": h["payload"].get("text", ""),
                   "doc": str(h["payload"].get("source_file", "")).split("/")[-1],
                   "crumb": h["payload"].get("section", ""),
                   "page": h["payload"].get("page_number", "")} for h in hits]
        if not chunks:
            return "The knowledge base is empty - ingest documents first (runbook 2.1.3)."
        try:    # reranker: optional precision stage, skipped silently if down
            order = sorted(requests.post(v.RERANK_URL, timeout=60, json={
                "query": q, "texts": [c["text"] for c in chunks]}).json(),
                key=lambda d: d["score"], reverse=True)
            chunks = [chunks[d["index"]] for d in order]
        except Exception:
            pass
        ctx = chunks[: v.CONTEXT_K]
        model = v.LLM_MODEL
        if model == "auto":   # vLLM needs the REAL served-model name (v4.53)
            try:
                model = requests.get(
                    v.LLM_URL.rsplit("/chat/completions", 1)[0] + "/models",
                    timeout=10).json()["data"][0]["id"]
            except Exception:
                model = "default"                 # llama-server route
        llm_body = {"model": model, "temperature": 0.0,
                    "max_tokens": v.MAX_TOKENS,
                    "chat_template_kwargs": {"enable_thinking": False},
                    "messages": [
                        {"role": "system", "content": self.SYSTEM_PROMPT},
                        {"role": "user", "content": "Context:\n" + "\n\n".join(
                            "[" + c["doc"] + " | " + c["crumb"] + "] " + c["text"]
                            for c in ctx) + "\n\nQuestion: " + q}]}
        try:
            data = requests.post(v.LLM_URL, timeout=600, json=llm_body).json()
            if "choices" not in data:
                return "KB ERROR - answer LLM returned: %r" % (data,)
            ans = data["choices"][0]["message"]["content"]
            if "</think>" in ans:
                ans = ans.split("</think>", 1)[1].lstrip()
        except Exception as e:
            return "KB ERROR - answer LLM unreachable (%s): %r" % (v.LLM_URL, e)
        src = "\n".join("[%d] %s | %s | p.%s" % (i, c["doc"], c["crumb"], c["page"])
                        for i, c in enumerate(ctx, 1))
        return (ans + "\n\n---\n**Sources** (context passages handed to the model):\n"
                + src)
```

**Expect (this is the Function's live admission test — record the outcome in the STEP RECORD):** "Project 42 KB" appears in the model picker of a new chat; a question answerable from the ingested documents returns a cited answer with the Sources block listing document, breadcrumb and page; an unanswerable question returns the explicit refusal; and the same question through `ask.py` returns substantially the same sources (both run the identical pipeline — a large divergence means a Valve is pointing at the wrong service). **If not:** the KB ERROR messages name the unreachable service and the URL tried — check the service, then the `host.docker.internal` note above; the Function not appearing in the picker = the enable toggle on the Functions page is off.

☐ **Step 4 [OPTIONAL — later, only if RBAC is needed] — Evaluate Onyx.**
**Why:** **Onyx** (ex-Danswer) gives role-based access control (RBAC) — an option for multi-user governance later.
**Before you run it:** RBAC is an **Enterprise-edition feature**, so check licensing fits before planning around it. **VERIFY (still uncertain on arm64):** no official arm64 support statement; its multi-service compose (**Postgres + OpenSearch** + Redis/MinIO — corrected 2026-07-10: Vespa is legacy, current stack is OpenSearch) may pull amd64-only images. Trial it only after the `docker compose ... up` below succeeds on the Spark. The dev file is an **override**, combined with the base file. Repo: https://github.com/onyx-dot-app/onyx
**Run:**
```bash
git clone https://github.com/onyx-dot-app/onyx.git
cd onyx/deployment/docker_compose
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d   # -f = use this compose file (two -f flags merge base + override); -d = background; exec-format error -> stay on Open WebUI
```
**Expect / If not:** all services come up → point Onyx at the Spark endpoint via **Settings → LLM** (base URL + key + model). `exec format error` → amd64-only images — stay on Open WebUI.

#### 2.1.2.5 Output rendering layer — Word / PowerPoint export

☐ **Step 1 [ALL] — Install the rendering toolchain.**
**Why:** KB answers and KB-derived reports must be exportable **into project Office templates**, not just read in a chat window. The model never writes .docx/.pptx directly: it produces structured content (markdown or JSON fields) and a deterministic renderer builds the file — so formatting is code, not generation, and the output is always in the approved template. Both routes below are pure-Python/ARM64-safe (no image-architecture risk).
**Before you run it:** *(v0.12, per technical review)* stage the **approved corporate Word template** at `/opt/p42/templates/airbus_corporate_template.docx` as a **pinned artefact** (obtain the approved file from the comms/quality owner, record its SHA-256 in the build log, same regime as the chat-template files) so every export gets corporate typography automatically.
**Run:**
```bash
sudo apt-get install -y pandoc
# (v4.25, hit live) uv pip install REFUSES to run without an active virtual environment
# (the §1.4 rule: nothing installs into the system Python on Ubuntu 24.04).
# Create the project rendering venv ONCE, activate it, then install:
mkdir -p ~/p42 && cd ~/p42
uv venv render-venv                       # creates ~/p42/render-venv (a private Python)
source ~/p42/render-venv/bin/activate     # activate = this shell now uses that Python
uv pip install python-docx python-pptx docxtpl
```
**Expect:** `pandoc --version` prints; with the venv active, `python -c "import docx, pptx, docxtpl"` exits silently (success). **Remember for every later use:** any script or shell that calls these libraries must first run `source ~/p42/render-venv/bin/activate` (or invoke `~/p42/render-venv/bin/python` directly) — a new terminal does NOT inherit the activation (§1.4/Annex A: environment state is per-shell).

☐ **Step 2 [DECISION] — Which rendering route per output?**
**Why:** two routes cover the two output classes.
**Before you run it** — the decision rule:

- **Pandoc route (fast, for notes/reports):** LLM writes markdown → pandoc renders it against the reference doc, which carries house fonts/styles/headers. Good default for exported KB answers.
- **Template-filling route (for formal deliverables):** mark up the official Word template with `docxtpl` (Jinja) placeholders → LLM outputs the fields as JSON → code injects them. For PowerPoint, `python-pptx` populates the corporate .potx layouts from model-produced JSON (titles/bullets/notes).

**Run (pandoc route):**
```bash
# --reference-doc = copy all styles/fonts/headers from this template document; -o = the output file to write
pandoc answer.md --reference-doc=/opt/p42/templates/airbus_corporate_template.docx -o answer.docx
```
**Expect:** a .docx in the template's styles. Keep the citations in the export: the `source_file` + `page_number` payload fields render as a references table or footnotes, so the "no citation, no claim" rule survives the round-trip into Word. (Reading Office formats is already covered — Docling ingests .docx/.pptx — so the KB is round-trip: Office in, Office out.)

### 2.1.3 Ingestion pipeline — four components, in order (UPDATE mode, all on Spark-1)

> [!IMPORTANT]
> **(v4.6) UPDATE-mode stages run STRICTLY SEQUENTIALLY — one at a time, never in parallel.** The mode gives ingestion the whole memory pool, but that is one budget shared by all stages, not an invitation to run them together: Docling parsing → VL captioning (port 8002) → ColQwen page vectors → Qdrant upsert, each stage torn down (and caches dropped per §1.7) before the next starts. Launching the VL model and ColQwen simultaneously can exceed the pool and hang the box (§1.7 — no clean error on this hardware). One stage, verify, tear down, next stage.

Everything in 2.1.3 runs on **Spark-1, in UPDATE mode only**: switch first with `sudo /opt/p42/bin/kb-mode-update.sh` (which snapshots Qdrant and tears down the serving stack, freeing the whole pool for the models below — Qdrant alone stays up to receive the vectors), and return with `sudo /opt/p42/bin/kb-mode-serve.sh` when the ingestion run is done.

#### 2.1.3.1 Docling (document parsing)

☐ **Step 1 [ALL] — Install Docling and convert a first PDF.**
**Why:** Docling is the pipeline's *reader*: it turns a PDF into structured text — headings, paragraphs and, crucially, **tables recognised as tables** (rows and columns preserved), not garbled character soup. Everything downstream works on Docling's output.
**Before you run it — three things that would otherwise confuse (v4.28):** (1) Docling has **two conversion modes**: the standard pipeline (fast, fine for cleanly-produced PDFs) and a "VLM pipeline" for *hard layouts* — scanned pages, dense multi-column datasheets — where a small **document-specialised vision model called GraniteDocling** reads the page image itself. That GraniteDocling model is **not** the Qwen2.5-VL captioner of 2.1.3.2 — two different vision models, two different jobs: GraniteDocling *reads page layout* inside Docling; Qwen2.5-VL *describes figures* in the next stage. (2) **First use downloads models automatically** (a few GB into `~/.cache/huggingface` — your `~/.bashrc` xet kill-switch applies), so the first conversion is slow and needs network; later ones are not. (3) The example URL below is just a handy public test PDF (Docling's own technical report) — any PDF file or URL works, and **the output lands in the current directory** as `<name>.md`. Docs: https://docling-project.github.io/docling/ · repo: https://github.com/docling-project/docling (Linux arm64 supported; runs on the GPU via PyTorch).
**Before you run it (v4.31 — found live on spark-9d0e):** Docling's page-layout model runs under `torch.compile`, PyTorch's just-in-time compiler. On its first use, that compiler generates a tiny C bridge file and builds it with `gcc` **against the Python C headers** (`Python.h`). Those headers are NOT part of Python itself and NOT provided by any venv — they come from the system package `python3-dev`, which DGX OS does not preinstall. Without it, every page of every PDF fails in the layout stage with the signature `fatal error: Python.h: No such file or directory`, and Docling reports `Document ... failed to convert`. Install the headers first — one package, once per machine:

```bash
# python3-dev provides the Python C headers (Python.h) that PyTorch's JIT
# compiler needs to build its small gcc-compiled bridge module on first use.
sudo apt-get update && sudo apt-get install -y python3-dev
```

Everything else in that first-run log is benign noise: the dynamo "Graph break" warnings, "Not enough SMs to use max_autotune_gemm" (expected on GB10), and the `torch_dtype` deprecation line are all safe to ignore. Emergency fallback only if the package install is impossible: `TORCHDYNAMO_DISABLE=1 docling ...` disables the compiler entirely — it works but slows every page, so it is the workaround, not the fix.

**Run:**
```bash
# (v4.26) ONE named venv serves the whole ingestion pipeline (Docling here, ColQwen in
# 2.1.3.3, and the ingest script) — created once, activated in EVERY ingestion shell:
mkdir -p ~/p42 && uv venv ~/p42/ingest-venv
source ~/p42/ingest-venv/bin/activate
uv pip install docling

# Standard conversion — writes ./2408.09869.md into the current directory:
cd ~/p42
docling https://arxiv.org/pdf/2408.09869

# VLM pipeline — ONLY for PDFs the standard mode mangles (scans, brutal layouts);
# slower, downloads GraniteDocling on first use:
docling --pipeline vlm --vlm-model granite_docling <pdf-url-or-path>
```
**Expect:** a readable `.md` file appears in `~/p42`, with the document's tables rendered as markdown tables (first conversion ≈ 40 s — the compile cache is cold; later documents are faster). **If not:** `Python.h: No such file or directory` repeated per page + `failed to convert` = the `python3-dev` package from the Before-you-run-it box is missing — install it and re-run; first run stalling = model download in progress (`du -sh ~/.cache/huggingface` growing); mangled tables = retry that document with the VLM pipeline line.

**TEST (Docling):** convert a PDF that has a table; confirm the table appears as structured markdown, not garbled text. (This is the make-or-break check for UC-OPS-2 and UC-DB-1 — RFM documentation is heavily tabular.)

#### 2.1.3.2 Qwen2.5-VL figure captioning (:8002)

☐ **Step 1 [ALL] — Serve the vision model on port 8002.**
**Why:** the VLM captions each figure/diagram during ingestion so their content becomes searchable text.
**Before you run it:** `nvidia/Qwen2.5-VL-7B-Instruct-NVFP4` is in the **official NVIDIA vLLM matrix** (confirmed arm64/Blackwell). *(Corrected 2026-07-10: Qwen2.5-VL is a natively supported vLLM architecture — no `--trust-remote-code` needed.)* This container runs in **UPDATE mode only** (the answer LLM is down, so the pool is free); the command below already carries the `--name vllm-vl` the mode scripts manage.

> [!WARNING]
> **VERIFY:** Qwen2.5-VL-7B-NVFP4 is the confirmed choice — it sits in NVIDIA's published matrix for this hardware, so nothing further needs checking. If you instead try **Qwen3-VL**, know two things before pulling it: it needs **vLLM ≥ 0.11.0** (an older container's vLLM will refuse to load it), and it is NOT in NVIDIA's published matrix — meaning nobody has validated it on this hardware for you. Check the vLLM version of your container build on the box first, and treat the whole combination as unproven until it passes your own test.

**Run:**
```bash
docker run --name vllm-vl --gpus all -p 8002:8000 \
  --ipc=host --ulimit memlock=-1 --ulimit stack=67108864 \
  -e HF_TOKEN=$HF_TOKEN -e HF_HUB_DISABLE_XET=1 -v ~/.cache/huggingface:/root/.cache/huggingface \
  nvcr.io/nvidia/vllm:26.07-py3 \
  vllm serve nvidia/Qwen2.5-VL-7B-Instruct-NVFP4 --gpu-memory-utilization 0.3
# (v4.20) same fixes as the embeddings block: vllm serve subcommand form; --name vllm-vl for
# the mode scripts; explicit 0.3 budget (UPDATE mode has headroom, but never leave the
# default 0.92 in place)
```
**Expect:** an OpenAI-compatible endpoint on :8002 that accepts **images inside chat messages** (as a URL or base64-encoded file). Smoke-test it with a public image (v4.28):

```bash
curl http://localhost:8002/v1/chat/completions -H "Content-Type: application/json" -d '{
  "model": "nvidia/Qwen2.5-VL-7B-Instruct-NVFP4",
  "messages": [{"role":"user","content":[
    {"type":"image_url","image_url":{"url":"https://upload.wikimedia.org/wikipedia/commons/3/3f/Fronalpstock_big.jpg"}},
    {"type":"text","text":"Describe this image in one sentence."}]}]}'
```

**Expect:** a JSON reply containing a sensible one-sentence description (a mountain landscape). That proves the exact call shape the ingest script uses for figure captioning.

#### 2.1.3.3 ColQwen2.5 visual page retrieval (multivectors → Qdrant)

☐ **Step 1 [ALL] — Install the ColQwen2.5 stack.**
**Why:** ColQwen retrieves by *looking at page images*: it emits **multi-vectors (one per image patch)** so a query can match a diagram it could never match through text alone.
**Before you run it:** pure-Python + PyTorch, runs on the Spark GPU. **ColQwen2.5 needs `colpali-engine` > 0.3.1** (the checkpoint was trained with 0.3.7). **(v4.43) Checkpoint = `vidore/colqwen2.5-v0.2`** — the canonical release from the ColPali authors (public, public Qwen2.5-VL-3B base, 128-dim multivectors). The previously named `Metric-AI/ColQwen2.5-7b-multilingual-v1.0` is UNUSABLE: its base repo went gated on Hugging Face (HTTP 401, verified live 2026-08-10) and the adapter cannot load without it. Repo: https://github.com/illuin-tech/colpali &nbsp;|&nbsp; Qdrant tutorial: https://qdrant.tech/documentation/tutorials-search-engineering/pdf-retrieval-at-scale/

> [!WARNING]
> **VERIFY:** confidence in this component is high, because it is pure Python + PyTorch with no architecture-specific binaries — so there is no ARM64 packaging risk to worry about. What nobody has measured yet is its **speed on this GPU**: it has not been benchmarked on GB10. Before relying on it for a large document set, run a small ingestion batch on the box, check that the pages-per-minute throughput is acceptable, and record the figure in the STEP RECORD.

**Run:**
```bash
source ~/p42/ingest-venv/bin/activate   # (v4.26) same ingestion venv as Step 1 — a new
                                        # terminal does NOT inherit a previous activation
# (v4.46) >=0.3.14 is a HARD floor, not the model card's outdated ">0.3.1":
# 0.3.14 fixed a silent failure seen live on spark-9d0e - with newer
# transformers, older colpali-engine loads the ColQwen LoRA adapter with
# mismatched key names, prints a LOAD REPORT full of lora_A/lora_B
# MISSING/UNEXPECTED lines, and falls back to RANDOMLY INITIALIZED
# projection weights: no error, garbage page vectors, broken visual
# retrieval. The 0.3.14 release notes name this exact fix.
uv pip install "colpali-engine>=0.3.14" "qdrant-client>=1.12.0" pdf2image pillow

# (v4.42) pdf2image is only a thin Python wrapper around poppler's pdftoppm -
# a SYSTEM program that renders PDF pages to images. It comes from an apt
# package, not from pip, and a venv can never provide it. Without it, page
# rendering fails at run time with "Unable to get page count. Is poppler
# installed?" even though the pip install above succeeded:
sudo apt-get install -y poppler-utils
```
**Expect:** installs cleanly, and `pdftoppm -v` prints a poppler version. Air-gap note: `poppler-utils` joins `python3-dev` in the per-machine OS package set the enclave rebuild must mirror. Flow: render each PDF page → model emits multi-vectors → store in a **Qdrant multivector collection** (`MultiVectorConfig` / `MAX_SIM`) on Spark-1 → query gets multi-vectors → late-interaction (MaxSim) ranking (each query vector is matched against its best-matching page-patch vector and the scores are summed — that late per-patch matching is what lets a query hit a diagram).

#### 2.1.3.4 Ingestion flow and lifecycle — the ingest script and its runs

☐ **Step 1 [ALL — read first] — Understand what separates "simple" from "best".**
**Why:** the v4.28 flow shipped a **v0 reference script** described as "deliberately simple" — which raised the fair operator question: *simple as opposed to WHAT?* This step answers it. Ingestion quality is not one dial but a small set of named **quality levers**; the v1 script in Step 2 pulls the highest-value ones, and the rest are listed so every later refinement is a deliberate, measured decision instead of folklore.
**Before you run it — the levers, what each means in plain language, and which ones v1 already pulls:**

| Quality lever | What it is and why it matters | In the v1 script below? |
|---|---|---|
| **Structure-aware chunking** | Split the text on the document's **own headings and sections**, not at fixed character counts, aiming for roughly **200–500 tokens per chunk with ~15 % overlap** between neighbours (a *token* is the model's word-fragment unit; overlap means the end of one chunk is repeated at the start of the next so no fact is stranded on a boundary). Two hard rules: **NEVER split a table mid-way** — half a table is garbage for retrieval — and **prepend a "breadcrumb" of the section path** (e.g. `SECTION: Installation > Torque values`) to every chunk, so a retrieved chunk carries its own context instead of arriving as an orphan paragraph. | **YES** |
| **Figure captions attached to the nearest chunk** | The VL captioner (2.1.3.2) describes each page's figures; ideally each caption is attached to the *specific chunk* it belongs to, not dumped at page level, so the caption is retrieved together with the text that discusses the figure. | Page-level for now (refinement candidate) |
| **Rich payload metadata** | Store **source file, page number, section title, the document's SHA-256** (a *SHA-256* is a cryptographic fingerprint — same bytes, same fingerprint), **the document revision letter and the element type** (`text` / `table` / `page`) alongside every vector. This is what enables **filtered search** ("search only this manual", "tables only"), **precise citations** (file + page in every answer), and — once the corpus carries multiple revisions — **revision-aware retrieval** (prefer the current revision unless an older one is asked for). The revision and element-type fields are recorded from the very first ingestion *deliberately*: payload fields added later would require re-ingesting the whole corpus. | **YES** |
| **Boilerplate removal** | Strip repeated page headers/footers ("Company Confidential", running titles, page numbers) before chunking — repeated boilerplate matches *every* query a little and pollutes retrieval. | **NO** (refinement candidate) |
| **Chunk-level embedding** | Embed each chunk as its own vector. The v0 script embedded **whole pages** — one vector per page is coarse: a page mixing three topics gets one blurred vector that matches none of them well. | **YES** |
| **Hybrid dense+keyword retrieval with cross-encoder rerank** | Serving-side quality: search by meaning AND by exact keywords, merge, then let a cross-encoder reranker re-score the finalists. This is **already the configured serving path (§2.1.2.4)** — ingestion's job is producing chunks that make it work well. | Serving side — already configured |

**The governing rule (unchanged):** EVERY refinement to this pipeline is judged on the **golden question set** (§2.1.2.4 — the fixed list of test questions with known answers), never by feel, and every change is recorded in the build log. A lever that does not move the golden-set score does not enter the recipe.

> [!NOTE]
> **Where this sits relative to the state of the art (v4.29, per PoC-lead challenge).** The architecture in use here — hybrid dense+keyword retrieval, cross-encoder reranking, and late-interaction visual retrieval (ColQwen) — **IS the current community state-of-the-art BASELINE** per the project's KB trade-off study; it is a strong, conservative starting point, not a shortcut. What is deliberately NOT adopted (yet): **LLM-based semantic chunking** (an LLM decides chunk boundaries), **GraphRAG-style graph enrichment** (entities and relations extracted into a knowledge graph beside the vectors), and **agentic always-on retrieval** (an agent loop that re-queries and reasons between retrievals). Each of these is a **G2 evaluation option**: it must beat this baseline on the golden set to enter the recipe. And the definition to hold onto: **"production-ready" is by definition the G2-frozen recipe after that evaluation — not WP1 code.** WP1's job is discovering the recipe, and this pipeline is the instrument for doing so.

☐ **Step 2 [ALL] — Create the batch ingest script v2 (`~/p42/ingest.py` — replaces v0/v1).**
**Why:** v0 proved the four-stage flow end to end but handled one PDF at a time, embedded whole pages, and had no notion of a document *lifecycle* (what happens when a document changes, or is withdrawn?). v1 kept the same four services and added: **multi-format batch ingestion** (files or whole folders), **structure-aware chunking** with section breadcrumbs, **stable point IDs** so re-ingestion overwrites cleanly, and an **incremental manifest** so unchanged documents are skipped and changed ones updated in place. v2 (v4.30) adds **two payload fields decided BEFORE the first corpus ingestion, because adding them later would force a full re-ingest**: `document_revision` (the revision letter parsed from ECSS-style filenames — e.g. `ECSS-E-ST-10-02C.pdf` → `C`; empty for non-ECSS names — the field the benchmark's future *revision* question class and any prefer-current-revision retrieval logic will filter on) and `element_type` (`text`, `table`, or `page` — which lets retrieval and the error taxonomy distinguish a table chunk from prose without parsing the chunk text).
**Before you run it:** the heredoc below **overwrites** the v0 script — that is intended; v0 was the scaffold. Requirements are the ones already installed in `~/p42/ingest-venv` (Docling from (a), `colpali-engine`/`qdrant-client`/`pdf2image` from (c)). The script processes **one file at a time, sequentially** — the §2.1.3 sequential rule is built in, so never launch several copies in parallel. The visual pipeline (page captions + ColQwen page vectors) applies to **PDFs only**, because only PDFs render to page images; DOCX/PPTX/XLSX/HTML/MD get text chunks only — their figures become a G2 question if it matters.
**Run:**
```bash
source ~/p42/ingest-venv/bin/activate
cat > ~/p42/ingest.py <<'EOF'
# ---------------------------------------------------------------------------
# Project 42 - batch ingestion v2.7 (v4.58: PROCESSING-CONFIG RECORD -
# every ingesting run writes ~/p42/kb-ingest-config.json: script version,
# chunking + render settings, the exact model names used, and the installed
# library versions (docling, colpali-engine, torch, ...). The benchmark
# harness embeds this file in its run metrics record, so a
# scorecard traces to HOW the corpus was processed, not just which files.
# Model names + DPI are now module constants: one place, used AND recorded.
# v2.6 (v4.54): built-in SERVICE PREFLIGHT -
# the batch refuses to start if Qdrant :6333, BGE-M3 :8080 or the VL
# captioner :8002 is down, instead of failing every file after minutes of
# parsing; v2.5 per-file metrics -> ingest-runs.jsonl; v2.4 no silent gaps;
# v2.3 vidore ColQwen; v2.2 progress display; v2.1 timing; v2 payloads.
# Every run prints START / END / DURATION banners, and each ingested file
# prints its own stage lines and elapsed time - copy these into the build log.
# No colour codes on purpose: build-log copy-paste stays clean text.
# Usage:  python ingest.py <path> [<path> ...]     files and/or folders
#                                                  (folders walked recursively)
#         python ingest.py --remove <source_file> [...]   remove from the KB
#         python ingest.py --list                  show the manifest (baseline)
# Stages per file: Docling parse -> structure-aware chunking -> (PDF only:
# VL captions on :8002 + ColQwen page multi-vectors) -> BGE-M3 embeddings on
# :8080 per chunk -> upsert into Qdrant on :6333. UPDATE mode only
# (kb-mode-update.sh first). Files are handled ONE AT A TIME, sequentially.
# ---------------------------------------------------------------------------
import sys, os, io, json, base64, hashlib, uuid, re, time, requests
from datetime import datetime
from docling.document_converter import DocumentConverter
from qdrant_client import QdrantClient, models

def fmt_dur(seconds):
    # 754.3 -> "12m 34s"; keeps timing lines human-readable in the build log.
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return ("%dh %dm %ds" % (h, m, s)) if h else ("%dm %ds" % (m, s))

BAR = "=" * 60
def banner(*lines):
    # Boxed banner for run start/end - visually distinct in a long log.
    print(BAR)
    for l in lines:
        print(" " + l)
    print(BAR)

QDRANT   = "http://localhost:6333"
EMBED    = "http://localhost:8080"     # BGE-M3 embedding service
VL       = "http://localhost:8002"     # Qwen2.5-VL captioning service
MANIFEST = os.path.expanduser("~/p42/kb-manifest.json")
TEXT_COLL, PAGE_COLL = "p42_text", "p42_pages"
CHUNK_CHARS = 1600                     # ~400 tokens (a token is ~4 chars of English)
# Docling is MULTI-FORMAT NATIVELY - one converter reads all of these:
SUPPORTED = (".pdf", ".docx", ".pptx", ".xlsx", ".html", ".htm", ".md")
# (v2.7) Processing configuration as CONSTANTS - each value is used by the
# code below AND recorded verbatim in kb-ingest-config.json, so the record
# cannot drift from what actually ran. Change a value here = a new corpus
# processing baseline (re-ingest, and the benchmark's run record shows it).
INGEST_VERSION = "v2.7"
CONFIG_PATH   = os.path.expanduser("~/p42/kb-ingest-config.json")
EMBED_MODEL   = "BAAI/bge-m3"
CAPTION_MODEL = "nvidia/Qwen2.5-VL-7B-Instruct-NVFP4"
COLQWEN_MODEL = "vidore/colqwen2.5-v0.2"
PDF_DPI       = 120                    # page-image render resolution

qc = QdrantClient(url=QDRANT, timeout=120)
converter = DocumentConverter()
_colqwen = None                        # ColQwen is heavy - loaded once, on demand

def ensure_collections():
    # Same shapes as v0: dense text vectors (1024, cosine) and per-patch
    # page multi-vectors (128, MAX_SIM late-interaction scoring).
    if not qc.collection_exists(TEXT_COLL):
        qc.create_collection(TEXT_COLL, vectors_config=models.VectorParams(
            size=1024, distance=models.Distance.COSINE))
    if not qc.collection_exists(PAGE_COLL):
        qc.create_collection(PAGE_COLL, vectors_config=models.VectorParams(
            size=128, distance=models.Distance.COSINE,
            multivector_config=models.MultiVectorConfig(
                comparator=models.MultiVectorComparator.MAX_SIM)))

def load_manifest():
    # The manifest is the KB ledger, {source_file: sha256} - it is what makes
    # re-runs INCREMENTAL: unchanged files skipped, changed files updated.
    if os.path.exists(MANIFEST):
        with open(MANIFEST) as f:
            return json.load(f)
    return {}

def save_manifest(m):
    with open(MANIFEST, "w") as f:
        json.dump(m, f, indent=2, sort_keys=True)

def sha256_of(path):
    # Fingerprint the file bytes; the manifest stores this per document.
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def revision_of(source):
    # Parse the revision from an ECSS-style filename, e.g.
    # "ECSS-E-ST-10-02C.pdf" -> "C", "ECSS-E-HB-11A.pdf" -> "A",
    # "ECSS-E-AS-50-21C-Rev.2(5Dec2024).pdf" -> "C Rev.2" (v4.43: the AS
    # adoption-notice type and the -Rev.N suffix are real ecss.nl filename
    # shapes, seen live). Non-ECSS filenames return "" (field exists, empty).
    # Feeds the future revision question class and prefer-current-revision
    # retrieval - recorded from day one so no re-ingest is needed later.
    m = re.search(r"ECSS-[A-Z]-(?:ST|HB|TM|AS)-\d+(?:-\d+)?([A-Z])"
                  r"(?:[-_ ]?Rev\.?\s?(\d+))?",
                  os.path.basename(source))
    if not m:
        return ""
    return m.group(1) + (" Rev." + m.group(2) if m.group(2) else "")

def point_id(source, index):
    # STABLE IDs: uuid5 maps (source_file + chunk index) to the SAME UUID
    # every run, and Qdrant upsert means insert-or-replace by ID - so
    # re-ingesting a changed file OVERWRITES its old points, no duplicates.
    return str(uuid.uuid5(uuid.NAMESPACE_URL, source + "#" + str(index)))

def delete_points(source):
    # Delete all points of one file in BOTH collections by payload filter -
    # needed because a changed file may now produce FEWER chunks than
    # before, and upsert alone would leave the stale tail behind.
    flt = models.Filter(must=[models.FieldCondition(
        key="source_file", match=models.MatchValue(value=source))])
    for coll in (TEXT_COLL, PAGE_COLL):
        qc.delete(coll, points_selector=models.FilterSelector(filter=flt))

def embed(text):
    # One dense vector per CHUNK (not per page - see the Step 1 lever table).
    r = requests.post(EMBED + "/v1/embeddings", timeout=120, json={
        "model": EMBED_MODEL, "input": text[:8000]})
    return r.json()["data"][0]["embedding"]

def caption(img):
    # Ask the VL server what a page image shows, so figures become searchable.
    buf = io.BytesIO(); img.save(buf, format="JPEG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    r = requests.post(VL + "/v1/chat/completions", timeout=300, json={
        "model": CAPTION_MODEL,
        "messages": [{"role": "user", "content": [
            {"type": "image_url",
             "image_url": {"url": "data:image/jpeg;base64," + b64}},
            {"type": "text", "text": "List and describe any figures or "
             "diagrams on this page in 2-3 sentences. If none, reply none."}]}]})
    return r.json()["choices"][0]["message"]["content"]

def get_colqwen():
    # Load the ColQwen model ONCE per run (it is several GB on the GPU).
    # (v4.43) Model SWAPPED from Metric-AI/ColQwen2.5-7b-multilingual-v1.0:
    # that adapter's base repo (Metric-AI/colqwen2.5-7b-base) went GATED on
    # Hugging Face (HTTP 401, verified 2026-08-10) making it unloadable.
    # vidore/colqwen2.5-v0.2 is the CANONICAL checkpoint from the ColPali
    # authors: public, public base (Qwen2.5-VL-3B), same classes, same
    # 128-dim multivectors - the maturity-first choice.
    global _colqwen
    if _colqwen is None:
        import torch
        from colpali_engine.models import ColQwen2_5, ColQwen2_5_Processor
        name = COLQWEN_MODEL                       # (v2.7) constant, recorded
        # (v4.45) Announce the load - on FIRST use this downloads ~6-7 GB
        # and previously looked like a hang (silent gap between the chunks
        # line and the visual-pass line).
        print("        loading ColQwen (" + name + ") - FIRST use downloads")
        print("        ~6-7 GB; check progress: du -sh ~/.cache/huggingface")
        t_load = time.time()
        model = ColQwen2_5.from_pretrained(
            name, torch_dtype=torch.bfloat16, device_map="cuda").eval()
        proc = ColQwen2_5_Processor.from_pretrained(name)
        _colqwen = (model, proc)
        print("        ColQwen ready (" + fmt_dur(time.time() - t_load) + ")")
    return _colqwen

def chunk_document(doc):
    # STRUCTURE-AWARE CHUNKING (the Step 1 lever): walk Docling items in
    # reading order, keep the current heading path as a breadcrumb, gather
    # text under it, and flush a chunk near CHUNK_CHARS. The last paragraph
    # is carried into the next chunk as overlap so no fact sits on a cut.
    # Tables are ALWAYS emitted whole, as their own chunk - never split.
    chunks, crumbs, buf, page = [], [], [], None

    def flush(overlap, etype="text"):
        # etype records WHAT KIND of content the chunk is ("text" or "table")
        # so the payload can carry element_type without re-parsing chunk text.
        nonlocal buf, page
        if buf:
            section = " > ".join(c for c in crumbs if c) or "(document)"
            chunks.append({"text": "SECTION: " + section + "\n"
                           + "\n".join(buf), "section": section, "page": page,
                           "etype": etype})
            buf = [buf[-1]] if overlap else []     # ~15 percent carry-over

    for item, _level in doc.iterate_items():
        label = str(getattr(item, "label", ""))
        text = (getattr(item, "text", "") or "").strip()
        prov = getattr(item, "prov", [])
        item_page = prov[0].page_no if prov else None
        if label in ("section_header", "title"):
            flush(overlap=False)                   # a new section: clean break
            depth = getattr(item, "level", 1)      # heading depth -> breadcrumb
            crumbs, page = crumbs[:max(depth - 1, 0)] + [text], item_page
            continue
        if label == "table":
            flush(overlap=False)                   # never split a table:
            try:                                   # emit it whole, alone
                md = item.export_to_markdown(doc)
            except TypeError:
                md = item.export_to_markdown()
            if md.strip():
                buf, page = [md.strip()], item_page
                flush(overlap=False, etype="table")
            continue
        if text:
            if page is None:
                page = item_page
            buf.append(text)
            if sum(len(t) for t in buf) >= CHUNK_CHARS:
                flush(overlap=True)
    flush(overlap=False)
    return chunks

def ingest_file(path, source, digest):
    # (v2.5) Returns a per-file metrics record {pages, chunks, parse_s,
    # visual_s, embed_s} - appended to ~/p42/ingest-runs.jsonl per run,
    # the data source for maintenance-window planning.
    rec = {"pages": 0, "chunks": 0, "parse_s": 0.0, "visual_s": 0.0,
           "embed_s": 0.0}
    t = time.time()
    print("  [1/3] parsing with Docling ...")
    doc = converter.convert(path).document
    chunks = chunk_document(doc)
    rev = revision_of(source)                      # "" for non-ECSS names
    rec["parse_s"] = round(time.time() - t, 1)
    rec["chunks"] = len(chunks)
    print("        chunks: %d | revision: %s" % (len(chunks), rev or "(none)"))
    t = time.time()
    if path.lower().endswith(".pdf"):
        # PDFs only: page images exist, so run the visual pipeline too.
        import torch
        from pdf2image import convert_from_path
        model, proc = get_colqwen()
        print("        rendering pages to images (poppler) ...")
        pages = convert_from_path(path, dpi=PDF_DPI)
        rec["pages"] = len(pages)
        print("  [2/3] visual pass (VL captions + ColQwen): %d pages" % len(pages))
        for n, img in enumerate(pages, start=1):
            if n % 10 == 0 or n == len(pages):
                print("        page %d/%d" % (n, len(pages)))
            cap = caption(img)
            if cap.strip().lower() != "none" and chunks:
                # Attach the caption to the chunk NEAREST that page
                # (page-level attachment - a named refinement candidate).
                near = min((c for c in chunks if c["page"] is not None),
                           key=lambda c: abs(c["page"] - n), default=chunks[0])
                near["text"] += "\n[FIGURES p" + str(n) + "] " + cap
            with torch.no_grad():
                mv = model(**proc.process_images([img]).to("cuda"))[0]
            qc.upsert(PAGE_COLL, [models.PointStruct(
                id=point_id(source, "page" + str(n)),
                vector=mv.cpu().float().tolist(),
                payload={"source_file": source, "page_number": n,
                         "doc_sha256": digest, "document_revision": rev,
                         "element_type": "page"})])
    else:
        print("  [2/3] visual pass: skipped (not a PDF - text chunks only)")
    rec["visual_s"] = round(time.time() - t, 1)
    t = time.time()
    print("  [3/3] embedding %d chunks (BGE-M3) + upserting to Qdrant ..." % len(chunks))
    for i, c in enumerate(chunks):
        # Rich payload = filtered search + precise citations (Step 1 levers).
        qc.upsert(TEXT_COLL, [models.PointStruct(
            id=point_id(source, i), vector=embed(c["text"]),
            payload={"source_file": source, "page_number": c["page"],
                     "section": c["section"], "doc_sha256": digest,
                     "document_revision": rev,
                     "element_type": c["etype"],
                     "text": c["text"]})])
    rec["embed_s"] = round(time.time() - t, 1)
    print("        %d chunks upserted" % len(chunks))
    return rec

def lib_versions():
    # (v2.7) Installed versions of the libraries that DEFINE the processing
    # result. Docling's parser, the chunker's input, ColQwen's weights
    # loading - a version change in any of these can change the corpus even
    # with identical documents, so they belong in the trace.
    from importlib.metadata import version, PackageNotFoundError
    out = {}
    for pkg in ("docling", "colpali-engine", "qdrant-client", "torch",
                "pdf2image", "transformers"):
        try:
            out[pkg] = version(pkg)
        except PackageNotFoundError:
            out[pkg] = None                        # recorded as unknown
    return out

def save_ingest_config():
    # (v2.7) One JSON file = the corpus PROCESSING baseline: what script,
    # what settings, what models, what library versions built the points
    # now in Qdrant. Written after every run that actually (re)processed
    # at least one document. The benchmark harness embeds this file in
    # run_metrics.json, closing the trace: documents (manifest shas) +
    # processing (this file) + serving (live service identities) +
    # generation (GEN_PARAMS) = the full execution configuration.
    # NOTE: if this run followed a config change and SKIPPED unchanged
    # files, those points still reflect the OLD config - after changing
    # any constant above, re-ingest the full corpus so the baseline is
    # uniform (ingest-runs.jsonl keeps the per-run history).
    cfg = {"ingest_version": INGEST_VERSION,
           "written": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
           "python": sys.version.split()[0],
           "chunk_chars": CHUNK_CHARS,
           "pdf_render_dpi": PDF_DPI,
           "embed_model": EMBED_MODEL,
           "caption_model": CAPTION_MODEL,
           "colqwen_model": COLQWEN_MODEL,
           "collections": {"text": TEXT_COLL, "pages": PAGE_COLL},
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

def main():
    args = sys.argv[1:]
    if not args:
        print("usage: python ingest.py <path>... | --remove <file>... | --list")
        return
    manifest = load_manifest()
    if args[0] == "--list":
        for src in sorted(manifest):
            print("baseline:", src, manifest[src][:12])
        print(str(len(manifest)) + " documents in the manifest")
        return
    ensure_collections()
    if args[0] == "--remove":
        for p in args[1:]:
            src = os.path.abspath(p)
            delete_points(src)                     # both collections
            manifest.pop(src, None)                # and the ledger entry
            save_manifest(manifest)
            print("remove:", src)
        return
    # (v2.6) SERVICE PREFLIGHT - fail fast, before any parsing. Hit live
    # TWICE: a dead :8002 failed every file only AFTER minutes of Docling
    # parsing and page rendering per file. Five seconds here prevents that.
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
    ok = up(VL + "/v1/models", "VL captioner :8002",
            "docker start vllm-vl (kb-mode-update.sh step 6 starts it; "
            "allow 1-2 min for model load)") and ok
    if not ok:
        print("ABORT - nothing was ingested. Fix the DOWN service(s), then "
              "re-run the SAME command (the manifest makes re-runs safe).")
        return
    files = collect(args)
    print("corpus scan: %d file(s) to consider" % len(files))
    done_n = skip_n = err_n = 0
    file_recs = []                                 # (v2.5) per-file metrics
    for idx, f in enumerate(files, start=1):
        src = os.path.abspath(f)
        try:
            digest = sha256_of(src)
            if manifest.get(src) == digest:
                print("[%d/%d] skip   : %s (unchanged)" % (idx, len(files), src))
                skip_n += 1
                continue
            action = "update" if src in manifest else "ingest"
            print("[%d/%d] %-7s: %s" % (idx, len(files), action, src))
            t_file = time.time()                   # per-file clock
            if action == "update":
                delete_points(src)                 # clear old points first
            rec = ingest_file(src, src, digest)
            manifest[src] = digest
            # Saved after EVERY file: a crash costs one file, not the batch.
            save_manifest(manifest)
            done_n += 1
            rec.update(file=os.path.basename(src), action=action,
                       total_s=round(time.time() - t_file, 1))
            file_recs.append(rec)
            print("  file time: " + fmt_dur(time.time() - t_file))
        except Exception as e:
            # Log and CONTINUE - one bad document must not kill the run.
            err_n += 1
            print("  ERROR:", src, "-", repr(e))
    print()
    print("SUMMARY  ingested/updated: %d | skipped: %d | errors: %d"
          % (done_n, skip_n, err_n))
    if done_n:
        # (v2.7) At least one document was (re)processed by THIS config -
        # record it. Skipped-only runs do not overwrite the record: their
        # points were built by whatever config last wrote the file.
        save_ingest_config()
    # (v2.5) Metrics log: one JSON line per run, appended - per-file pages/
    # chunks and stage timings. This is the empirical base for sizing
    # maintenance windows ("N pages took M minutes") and for spotting a
    # stage that suddenly got slower after a change.
    if file_recs:
        run_rec = {"end": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                   "ingested": done_n, "skipped": skip_n, "errors": err_n,
                   "pages": sum(r["pages"] for r in file_recs),
                   "chunks": sum(r["chunks"] for r in file_recs),
                   "files": file_recs}
        with open(os.path.expanduser("~/p42/ingest-runs.jsonl"), "a") as f:
            f.write(json.dumps(run_rec) + "\n")
        print("metrics appended to ~/p42/ingest-runs.jsonl")

# Run banner (v4.32): START / END / DURATION printed around every invocation
# (ingest, --remove and --list alike). The try/finally guarantees the END
# line even when the run stops on an error - copy all three into the build log.
_t0 = time.time()
banner("ingest.py -- Project 42 KB batch ingestion",
       "START " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
try:
    main()
finally:
    print()
    banner("ingest.py | END " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
           + " | DURATION " + fmt_dur(time.time() - _t0))
EOF
```
**Expect:** the file `~/p42/ingest.py` exists; `python -m py_compile ~/p42/ingest.py` exits silently (a syntax check that runs no ingestion). **If not:** a syntax error means the paste was mangled — re-run the whole `cat` block; do not hand-repair.

☐ **Step 3 [ALL] — Run the lifecycle: first batch, incremental update, removal, listing.**
**Why:** these four invocations ARE the KB document lifecycle — the same script covers first ingestion, re-ingestion after edits, withdrawal of a document, and auditing what the KB currently contains.
**Before you run it:** the box must be in **UPDATE mode** (`sudo /opt/p42/bin/kb-mode-update.sh` — snapshot taken, serving stack down) with Qdrant (:6333), BGE-M3 (:8080) and the VL container (:8002) up. Keep the corpus in one folder (e.g. `~/p42/kb-docs/`) — the manifest then makes that folder the single source of truth. **And run the dependency preflight (v4.42 — added after a live `No module named 'pdf2image'` failure):** the script's Python dependencies were installed across THREE earlier steps, so a skipped step or a shell without the venv only surfaces at run time, possibly minutes into a batch. The check below fails in two seconds instead. If a module is missing, the name tells you which step to (re)run: `docling` → 2.1.3.1 Step 1; `pdf2image` / `colpali_engine` / `qdrant_client` / `torch` → 2.1.3.3 Step 1; `requests` → comes with the others. `pdftoppm` missing → the `poppler-utils` system package from 2.1.3.3 Step 1 (a venv can never provide it — see there).

```bash
# Dependency preflight - two seconds now vs a failed batch later.
# The python -c line imports every module the ingest script needs; the first
# missing one names itself in the error. pdftoppm -v proves poppler is present.
source ~/p42/ingest-venv/bin/activate
python -c "import docling, requests, qdrant_client, pdf2image, colpali_engine, torch; print('ingest deps OK')"
python -c "from importlib.metadata import version; v=version('colpali-engine'); assert tuple(map(int,v.split('.')[:3]))>=(0,3,14), 'colpali-engine '+v+' TOO OLD - silent LoRA fallback bug, need >=0.3.14'; print('colpali-engine', v, 'OK')"
pdftoppm -v 2>&1 | head -1

# Service preflight (v4.46) - the batch talks to three live services; a dead
# one fails EVERY file mid-run (seen live: Connection refused on :8002 after
# a 13-minute model download). Each line must answer, none may hang:
curl -s http://localhost:6333/collections | head -c 120; echo   # Qdrant
curl -s http://localhost:8080/health; echo                      # BGE-M3 embeddings
curl -s http://localhost:8002/v1/models | head -c 120; echo     # VL captioner (2.1.3.2)
```

**Benign warnings during the batch (v4.56 — asked live):** `[RapidOCR] The text detection result is empty` / `RapidOCR returned empty result!` appears whenever OCR inspects an **image region with no readable text** in it — a pure diagram, a logo, a decorative cover band. On born-digital PDFs (all ECSS standards) the text comes from the PDF's own text layer, OCR only runs on pictures, and "found nothing in this picture" is the correct result — expect dozens per batch. The decode rule: **warning + healthy chunk count = ignore; warning + near-zero chunks on a substantial document = that file's extraction actually failed** — retry it with the VLM pipeline per 2.1.3.1. The figure content itself is not lost either way: stage [2/3] captures it via VL captions and ColQwen page vectors.

**Run (first full batch — every supported file under the folder, recursively):**
```bash
source ~/p42/ingest-venv/bin/activate
python ~/p42/ingest.py ~/p42/kb-docs/
```
**Run (incremental re-run — e.g. after editing two documents; SAME command, the manifest does the detecting):**
```bash
python ~/p42/ingest.py ~/p42/kb-docs/     # expect: 2 x "update:", the rest "skip:"
```
**Run (removing a withdrawn document — deletes its points AND its manifest entry):**
```bash
python ~/p42/ingest.py --remove ~/p42/kb-docs/<withdrawn-document.pdf>
```
**Run (list the current baseline, then verify the vectors actually landed):**
```bash
python ~/p42/ingest.py --list
curl -s http://localhost:6333/collections/p42_text  | python3 -c "import sys,json; print('text points:',  json.load(sys.stdin)['result']['points_count'])"
curl -s http://localhost:6333/collections/p42_pages | python3 -c "import sys,json; print('page points:', json.load(sys.stdin)['result']['points_count'])"
```
**Expect:** one action line per file (`ingest:` / `skip:` / `update:` / `remove:`) plus a chunk count per ingested file, then the `SUMMARY` line, `processing config recorded to ~/p42/kb-ingest-config.json` (v2.7 — only on runs that actually (re)processed a document; the benchmark reads this file) and `metrics appended to ~/p42/ingest-runs.jsonl`; both point counts non-zero and the page count roughly equal to the total PDF page count. **If not:** connection refused on :6333 → Qdrant is not up (it should survive the mode switch); on :8080 → BGE-M3 is down (the v4.16 rule: it stays UP in UPDATE mode); on :8002 → the VL container is not started for this window (2.1.3.2). CUDA out-of-memory at the ColQwen stage → a previous heavy stage is still resident — tear it down, drop caches (§1.7), rerun. `ERROR:` lines are **per-file**: the run continues past a bad document — fix or `--remove` the file it names, re-run the same command, and everything already ingested is skipped.

> [!WARNING]
> **(v4.60) Renaming a corpus file is a lifecycle event, not a cosmetic change.** The manifest is keyed by the file's **absolute path** and point IDs derive from it, so a renamed file is a *new document* to ingest.py: the old path's manifest entry goes stale, its points stay in Qdrant under the old `source_file`, and re-ingesting the folder adds the same content AGAIN under the new name — duplicates in the KB. Correct sequence, inside an UPDATE window: `python ingest.py --remove <old path>` (works even after the file is gone — the path string is the key), then re-run the folder ingest. Check with `--list` that the old path no longer appears. And when fixing a filename, use the **exact ECSS code** — the issue letter goes after the full number (`ECSS-E-ST-10-03C`, never `ECSS-E-ST-10C-03`): the benchmark and the citation display both match question codes against the filename by containment, and a transposed code both orphans that document's questions AND can collide with a *shorter* real code (`ECSS-E-ST-10C` is a prefix of `ECSS-E-ST-10C-03…`), silently mis-crediting another document's scores.

When the run is checked, switch back with `sudo /opt/p42/bin/kb-mode-serve.sh`. Two closing facts of the lifecycle: the **manifest + the Qdrant snapshot together ARE the recorded "document baseline N"** of the mode-exclusive design — file both; and the FULL update cycle always happens **inside the `kb-mode-update.sh` / `kb-mode-serve.sh` windows** — the script never runs against a serving KB.

### 2.1.4 TEST — end-to-end KB and mode-switch rehearsal

> [!NOTE]
> **(v4.49) How to actually QUERY the project KB — the three routes.** The documents ingest.py loads live in the **project's Qdrant collections** (`p42_text` / `p42_pages`). Three things can query them: **(1)** the benchmark harness — batch, not interactive; **(2)** `ask.py` below — an interactive command-line interface using exactly the harness's retrieval path (embed → Qdrant → rerank → answer LLM with citations), available immediately; **(3)** an Open WebUI **Function** ("pipe") that surfaces the project KB as a selectable model in the chat picker — the proper end-user UI, planned as its own step once validated. Open WebUI's `#` knowledge feature is NOT one of these routes: it searches only its own uploaded collections (path B in Step 2 below), never the project Qdrant.

☐ **Step 0 [ALL] — Create `ask.py`, the interactive query CLI for the project KB.**
**Why:** the first moment the KB is real is the first time you can *ask it something* — this tool is that moment, and every answer it gives goes through the exact pipeline the benchmark measures (same embedder, same search, same reranker, same answer model, same grounding prompt), so what you see interactively is what the harness scores.
**Before you run it:** SERVING mode (or at minimum: Qdrant :6333, BGE-M3 :8080, answer LLM :8000 up; the reranker :8081 is used when present, skipped silently when not). Uses the ingest venv for `qdrant_client`.
**Run:**
```bash
cat > ~/p42/ask.py <<'EOF'
#!/usr/bin/env python3
# ask.py -- Project 42: interactive query CLI for the project KB (v1, runbook v4.49).
# Usage: python ask.py "your question here"
# Path: embed (:8080) -> Qdrant p42_text (:6333) -> rerank (:8081, optional)
#       -> answer LLM (:8000) -> answer + numbered source list.
# Same retrieval path and grounding prompt as the benchmark harness.
import sys, requests
from qdrant_client import QdrantClient

TOP_K, CONTEXT_K = 20, 5
# (v4.61, Run-2 lesson D1) template-placeholder fix - see 2.1.2.4 note.
SYSTEM_PROMPT = ("You answer questions using ONLY the provided context. "
    "Each context passage begins with its source label in square "
    "brackets. Cite every claim by copying that passage's source label "
    "EXACTLY as shown, brackets included. Never write placeholder words "
    "such as 'doc' or 'section' inside a citation. If the context does "
    "not contain the answer, say exactly: The corpus does not contain "
    "this information. Do not guess and do not use outside knowledge.")

def main():
    if len(sys.argv) < 2:
        print('usage: python ask.py "your question"'); return
    q = " ".join(sys.argv[1:])
    vec = requests.post("http://localhost:8080/v1/embeddings", timeout=60,
        json={"model": "BAAI/bge-m3", "input": q}).json()["data"][0]["embedding"]
    # (v4.52) query_points is the current qdrant-client search API - the old
    # .search() method was REMOVED in recent client versions (hit live).
    hits = QdrantClient(host="localhost", port=6333).query_points(
        collection_name="p42_text", query=vec, limit=TOP_K,
        with_payload=True).points
    chunks = [{"text": h.payload.get("text",""), "doc": h.payload.get("source_file",""),
               "crumb": h.payload.get("section",""), "page": h.payload.get("page_number","")}
              for h in hits]
    try:    # optional reranker - skipped silently if :8081 is down
        order = sorted(requests.post("http://localhost:8081/rerank", timeout=60,
            json={"query": q, "texts": [c["text"] for c in chunks]}).json(),
            key=lambda d: d["score"], reverse=True)
        chunks = [chunks[d["index"]] for d in order]
    except Exception:
        pass
    ctx = chunks[:CONTEXT_K]
    # (v4.53) vLLM REQUIRES the real served-model name in the request (a
    # placeholder like "default" gets an error JSON back, no "choices" key;
    # llama-server tolerates anything). Discover it from /v1/models - both
    # engines expose that endpoint, so this stays engine-agnostic.
    try:
        model_id = requests.get("http://localhost:8000/v1/models",
            timeout=10).json()["data"][0]["id"]
    except Exception:
        model_id = "default"                      # llama-server route
    # (v4.57) enable_thinking False: Qwen3-class models otherwise burn the
    # whole token budget on <think> deliberation (seen live at Run 0);
    # other engines ignore the unknown field. Residual think blocks stripped.
    body = {"model": model_id, "temperature": 0.0, "max_tokens": 1200,
        "chat_template_kwargs": {"enable_thinking": False},
        "messages": [{"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "Context:\n" + "\n\n".join(
                "[" + c["doc"].split("/")[-1] + " | " + c["crumb"] + "] " + c["text"]
                for c in ctx) + "\n\nQuestion: " + q}]}
    data = requests.post("http://localhost:8000/v1/chat/completions",
        json=body, timeout=600).json()
    if "choices" not in data:                     # surface the server's own error
        print("LLM ERROR - the answer server returned:", data); return
    ans = data["choices"][0]["message"]["content"]
    if "</think>" in ans:
        ans = ans.split("</think>", 1)[1].lstrip()
    print("\n" + ans + "\n\nSOURCES (context passages handed to the model):")
    for i, c in enumerate(ctx, 1):
        print("  [%d] %s | %s | p.%s" % (i, c["doc"].split("/")[-1], c["crumb"], c["page"]))

main()
EOF
python -m py_compile ~/p42/ask.py && echo "ask.py OK"
```
**Run (ask your first question):**
```bash
source ~/p42/ingest-venv/bin/activate
python ~/p42/ask.py "What is this document about?"
```
**Expect:** a cited answer built ONLY from ingested content, followed by the numbered source list (document, section breadcrumb, page). Ask something the corpus cannot answer and expect the explicit refusal, not a guess. **If not:** connection refused names the dead service by port (:8080 embeddings, :6333 Qdrant, :8000 answer LLM — restart per 2.1.2); an empty/irrelevant answer with healthy sources = read the sources first — retrieval quality questions belong to the benchmark, not to ad-hoc judgement.

☐ **Step 1 [ALL] — Run the end-to-end KB test.**
**Why:** this is the section's proof: table extraction, visual retrieval, grounding discipline and Office export all checked in one pass.
**Before you run it — stand-in data (NOT project data), and know WHICH of the two retrieval paths each check exercises (v4.48):** grab a couple of public technical PDFs that each contain **a pinout/spec table AND a block diagram** — e.g. any public component datasheet. There are two parallel retrieval paths, and this test covers both: **(path A — the project pipeline)** switch to UPDATE mode, ingest the PDFs with the 2.1.3 flow so their chunks + page vectors land in the project's Qdrant collections, switch back to SERVING mode — this first real pass through update → ingest → serve is itself part of the test; path A is *queried* by the benchmark harness (the 10-question dev spot-check per the benchmark spec), NOT by `#` in the chat UI. **(path B — the Open WebUI knowledge path)** upload the SAME PDFs into an Open WebUI Knowledge collection (2.1.2.4 Step 2 item 3) — that is what `#` in chat searches, through the same embedder and reranker services. The chat questions below run against **path B**; a wrong-path attachment is the first thing to check if the chat "finds nothing" while the harness retrieves fine.
**Run (in Open WebUI at `http://<spark-1-ip>:3000`, with the Knowledge collection attached via `#` — type `#` first in the message box, pick the collection, confirm the chip appears):**
1. Ask a question whose answer is **in a table** (e.g. "What is the maximum supply voltage of part X?").
2. Ask a question whose answer is **in a diagram** (e.g. "Which pin connects to the clock input?" or "What blocks feed into the output stage?").
3. *(New in v0.2)* Ask a question whose answer is **NOT in the corpus** (e.g. about a part that isn't there). **Expected: an explicit "not found" — not a fabricated answer.** UC-OPS-2's golden set includes ~10% unanswerable questions; prove the behaviour now.
4. *(New in v0.3)* Export one answer through the rendering layer (§2.1.2.5): markdown → pandoc with a reference doc. **Expected:** a .docx that opens in Word, in the template's styles, with the citation(s) present as a references line — no manual reformatting needed.

**Expect / If not — exact check:**
- Both answerable answers are **factually correct** against the source PDF.
- Each answer **cites the source document and page number** (from the Qdrant payload).
- The table answer proves Docling table extraction worked; the diagram answer proves VLM captioning + ColQwen visual retrieval worked; the unanswerable question proves grounding discipline.
- If the diagram question fails but the table one works, the visual-retrieval path (VLM caption or ColQwen multivectors) is the weak link — check those before blaming the LLM.

☐ **Step 2 [ALL] — REHEARSE the mode switch and the snapshot/restore path.**
**Why:** the first mode switch and the first snapshot restore must not happen for real during a live maintenance window — rehearse both now, while the corpus is disposable stand-in data.
**Before you run it:** the serving stack (2.1.2) must be up and the stand-in corpus ingested. The rehearsal is: switch to UPDATE mode (watch the confirm prompt and the snapshot happen), verify the serving stack is really gone and the memory released, switch back to SERVING mode, verify the smoke checks pass — then prove the snapshot is usable.
**Run (the round trip):**
```bash
sudo /opt/p42/bin/kb-mode-update.sh    # answer YES; watch the snapshot + teardown + nvidia-smi
sudo /opt/p42/bin/kb-mode-serve.sh     # watch the restart order + the two smoke checks
```
**Run (the snapshot/restore check — list the snapshots the update script created):**
```bash
curl http://localhost:6333/snapshots
```
**Expect / If not:** the round trip ends with both smoke checks OK and Open WebUI answering again; the snapshot list is non-empty and shows the pre-update snapshot with a plausible timestamp and size. Then perform one restore against a throwaway copy or the stand-in collection (per-collection `PUT /collections/<name>/snapshots/recover`, or the storage-volume route — both described in the IMPORTANT box under "The two modes") and confirm a query still answers afterwards. If the snapshot list is empty, the update script's snapshot step failed silently — fix that before ANY real update; the snapshot-before-update rule is mandatory.

☐ **Step 3 [ALL] — Co-residency CUDA-context check (v4.15).**
**Why:** the whole SERVING design assumes several GPU services share the GPU at once — each holds its own **CUDA context** (a process's live working connection to the GPU). An unconfirmed forum report (2026-08-05) describes a second CUDA process failing with `CUDA_ERROR_NO_DEVICE` while another process already holds a context. Confirming that ALL our GPU services hold contexts simultaneously *and still answer* is cheap to check now — and expensive to discover at the demo.
**Before you run it:** the full SERVING stack (2.1.2) must be up: answer LLM, embeddings and reranker all loaded (ports per the 2.1.2.2 route you chose; the examples below use the worked :8000 / :8080 / :8081 split).
**Run (all three calls in the same session, one after another):**
```bash
# one embeddings call (| head -c 200 = show only the first 200 bytes of the reply — enough to see success):
curl -s http://localhost:8080/v1/embeddings -H "Content-Type: application/json" \
  -d '{"model":"BAAI/bge-m3","input":"co-residency probe"}' | head -c 200; echo
# one rerank call (path/port per your 2.1.2.2 route):
curl -s http://localhost:8081/rerank -H "Content-Type: application/json" \
  -d '{"query":"co-residency probe","texts":["first passage","second passage"]}' | head -c 200; echo
# one chat completion:
curl -s http://localhost:8000/v1/chat/completions -H "Content-Type: application/json" \
  -d '{"model":"<served-model>","messages":[{"role":"user","content":"Say OK."}]}' | head -c 200; echo
```
**Expect / If not:** all three services answer while co-resident — no `CUDA_ERROR_NO_DEVICE` (or any device-not-found error) anywhere in the replies or the service logs. If a second service fails to see the GPU while another holds a context, record the exact error and the loading order in the STEP RECORD and resolve it before any demo — do not work around it by serving the services one at a time.

**TEST:** all four checks of Step 1 pass on the stand-in corpus; the Step 2 mode-switch rehearsal completed with both smoke checks OK; snapshot listed and restore exercised once; the Step 3 co-residency check shows all GPU services answering with contexts held simultaneously.

### 2.1.5 Teardown before switching track

☐ **Step 1 [ALL] — Teardown.**
**Why:** every track leaves the box clean (shared memory pool, single port slots).
**Run:**
```bash
docker stop open-webui qdrant && docker rm open-webui qdrant   # (keep the qdrant_storage volume)
docker ps                                     # stop any vllm/embed/reranker/VLM containers similarly
pkill llama-server                            # if llama.cpp is serving
nvidia-smi                                    # confirm GPU memory freed
sudo sh -c 'sync; echo 3 > /proc/sys/vm/drop_caches'   # v0.4: reclaim page cache before the next big load
```
**Expect:** `nvidia-smi` shows the GPU memory freed; `docker ps` empty.

---

> **📋 STEP RECORD — §2.1** &nbsp;&nbsp; ☐ Done &nbsp; ☐ Deviation logged &nbsp; ☐ N/A (reason below)
> Machine: ☐ Spark-1 ☐ Spark-2 &nbsp;·&nbsp; Operator: `____________` &nbsp;·&nbsp; Date: `____________`
> Values recorded (versions / tags / measurements / anomalies): `________________________________________________`
>
> **Notes / observations / follow-ups** *(use as much of this space as needed)*:
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`

### 2.1.6 [OPTIONAL] On-box assistant — Claude Code on the Spark (v4.62)

> [!NOTE]
> **What this is.** Until now the project assistant (the §5.e layer of the benchmark spec) ran off-box — desktop app on a Windows machine, files shuttled by USB key. **Claude Code** is Anthropic's terminal assistant; it runs natively on ARM64 Linux (DGX OS qualifies: Ubuntu-based, ARM64, ≥4 GB RAM), works directly in `~/p42`, and can execute the whole Run-Assessment cycle in place: run the harness, read the outputs, verify claims against the source PDFs in `~/p42/kb-docs`, write the assessment and the assistant-overlay grading form into the run folder. Same assistant layer, same governance (spec §5.c/§5.e — never authoritative), zero file shuttling.
>
> **Enclave caveat — read before relying on it.** Claude Code needs `api.anthropic.com` over HTTPS. That works in the shakedown phase (this box already pulls from HF and Docker Hub) and will NOT work in the enclave. This is a shakedown/tuning-phase tool; the **on-box judge (`--judge`) remains the only AI-assessment layer that works air-gapped**, which is why the benchmark keeps both.

☐ **Step 1 [ALL] — Install and verify.**
**Why:** native installer, auto-updating, signed; one command.
**Run:**
```bash
curl -fsSL https://claude.ai/install.sh | bash
claude --version          # expect a version number, e.g. "2.x.y (Claude Code)"
claude doctor             # read-only diagnostics if anything looks off
```
**Expect / If not:** `command not found` after install → open a new shell (the installer adds `~/.local/bin` to PATH via your profile). DGX OS is Ubuntu-based ARM64 — fully supported.

☐ **Step 2 [ALL] — Log in (the operator does this personally).**
**Why:** Claude Code requires a Pro/Max/Team/Enterprise or Console account — the free tier does not include it. Per the project's standing credential rule, **the operator performs the login themselves**; credentials never pass through the assistant, never into the build log.
**Run:** `claude` — then follow the browser login prompt (the Spark has a browser; over SSH, the printed URL can be opened from any machine). Use the **project account**, not a personal one (same reasoning as the HF-token rule: access must survive personnel changes and stay auditable).

☐ **Step 3 [ALL] — Deploy the assistant's briefing file (CLAUDE.md).**
**Why:** Claude Code automatically reads `CLAUDE.md` in the working directory at session start — it is how a fresh on-box session knows the project, the file layout, the Run-Assessment procedure and the governance rules without being retold. This file IS the §5.e procedure, operationalised.
**Run:**
```bash
cat > ~/p42/kb-bench/CLAUDE.md <<'EOF'
# Project 42 — KB benchmark workspace (DGX Spark, on-box assistant briefing)

## What this is
RAG pipeline benchmark for an ECSS-standards knowledge base. Pipeline under
test: BGE-M3 embeddings (:8080) -> Qdrant (:6333, collection p42_text) ->
bge-reranker (:8081) -> Qwen3-32B answer LLM (:8000) -> cited answers.
kb_bench.py is the harness; kb_questions.json the golden question set.
The benchmark spec (Project42_KB_Benchmark_Spec.md, copy in ~/p42/docs/ if
present) is the authority on scoring and governance; this file summarises
what you need to operate.

## File map
- kb_bench.py                harness. Modes: full | N (dry) | --judge |
                             --retrieval-only | --top-k N | --context-k N |
                             --report <graded csv> | --compare <A> <B>
- kb_questions.json          76 questions; clause-anchored ground truth
- runs/<stamp>/              one folder per run: run_metrics_*.json,
                             verification_report_*.csv, contexts_*.json
                             (exact chunks per question), and on full runs
                             answers_*.csv + grading_*.html
- ~/p42/kb-docs/             the SOURCE PDFs (use pdftotext -layout to
                             verify claims against actual clause text)
- ~/p42/kb-manifest.json     corpus ledger; ~/p42/kb-ingest-config.json
                             processing baseline (may not exist yet)

## Governance — non-negotiable
- Your grades and verdicts are NEVER authoritative (spec 5.c). The human's
  grading columns (keypoints_covered, wrong_content, correctness,
  citation_ok, notes) are theirs alone - never fill or alter them in a csv.
  Your channel is the assistant_* columns and the prefills they drive.
- Every factual claim in an assessment must cite the source clause
  (verify in ~/p42/kb-docs, not from memory).
- Editing kb_questions.json: set author to an assistant-draft tag and
  CLEAR verified_by - a human must re-verify. Anchors: ASCII only; the
  keypoint text must never contain '|' (csv separator).
- One lever per experiment (two-families rule); adopt or revert a lever
  only on --compare rows marked SIGNIFICANT.

## Run Assessment procedure (spec 5.e) — on request or after a run
Given runs/<stamp>/, produce IN THAT FOLDER:
1. RunAssessment_<stamp>.md with: plumbing verdict (did the run measure
   what it claims - check mode, question sha, corpus sha, config diffs vs
   previous run, reranker.failed_calls); scorecard reading vs the previous
   run (use --compare); source-verified verdicts on triage-top rows;
   judge/assistant disagreement list; error-taxonomy labels
   (RETRIEVAL-MISS / RETRIEVAL-CHUNK / ANSWER-FABRICATION /
   TABLE-REASONING / OVER-REFUSAL / GROUND-TRUTH-DEFECT / PROMPT-DEFECT);
   recommended next lever + family; defects found.
2. assistant_grades_<stamp>.csv: id, judge_grade, assistant_grade,
   assistant_keypoints (one y/n per keypoint), assistant_wrong,
   assistant_citation_ok (y/n/na/'' where '' = cannot decide),
   assistant_rationale. Grade every answer independently - do NOT copy the
   judge's keypoint flags (a copied flag error has already happened once).
   Use contexts_<stamp>.json to verify citation support against the exact
   chunks the model saw.
3. The overlay form: load answers_<stamp>.csv, insert the assistant_*
   columns before triage_order, fill them, then regenerate via:
     python3 - <<'PY'
     import csv, sys; sys.path.insert(0, ".")
     import kb_bench
     # read answers csv -> cols, rows; add/fill assistant_* columns;
     kb_bench.write_grading_html("runs/<stamp>/grading_<stamp>.html",
                                 "<stamp>", cols, rows)
     PY
Refusal rows: assistant_citation_ok = "na". Unanswerable + exact refusal
sentence = grade 1; answerable + refusal = grade 0.

## Conventions
- Timestamps/shas identify everything; never overwrite a run folder.
- The masters (spec/runbook) carry version numbers + changelogs - if you
  edit one, bump the version, add a changelog row, and say so.
- Answer path runs thinking OFF; the judge runs thinking ON - do not
  change either without a spec change.
EOF
```
**Expect:** `claude` started from `~/p42/kb-bench` greets with project awareness (it read CLAUDE.md). Keep this file under version control with the other masters — it is the on-box §5.e procedure.

☐ **Step 4 [OPTIONAL] — The one-command run-and-assess wrapper.**
**Why:** makes the assessment part of the run, not a separate chore: one command runs the harness, then hands the fresh run folder to Claude Code headless (`claude -p` = non-interactive print mode) for the Run Assessment.
**Run:**
```bash
cat > ~/p42/kb-bench/kb-assess.sh <<'EOF'
#!/usr/bin/env bash
# kb-assess.sh - run the benchmark, then the on-box 5.e Run Assessment.
# Usage: ./kb-assess.sh [kb_bench.py args, e.g. --retrieval-only --top-k 50]
set -e
cd "$(dirname "$0")"
python3 kb_bench.py "$@"
LATEST=$(ls -td runs/*/ | head -1)
echo "=== handing ${LATEST} to the on-box assistant (claude -p) ==="
claude -p "Perform the Run Assessment for ${LATEST} exactly per the 'Run
Assessment procedure' in CLAUDE.md. Write RunAssessment, assistant_grades
csv and (for full runs) the assistant-overlay grading html into that
folder. Compare against the most recent comparable previous run." \
  --allowedTools "Read,Write,Edit,Bash,Glob,Grep" \
  --permission-mode acceptEdits
echo "=== assessment done - see ${LATEST} ==="
EOF
chmod +x ~/p42/kb-bench/kb-assess.sh
```
**Expect:** `./kb-assess.sh --retrieval-only` = scorecards + assessment in ~2–3 minutes; `./kb-assess.sh` = full run + assessment. For interactive work (debugging a failure, designing a lever), just run `claude` in `~/p42/kb-bench` and talk.

> [!NOTE]
> **What stays where.** Document mastering (spec/runbook versioning, docx generation) can move on-box too — copy the `Deliverables` masters to `~/p42/docs/` and Claude Code maintains them there (it has the full changelog discipline via CLAUDE.md). The desktop-app workflow on the Windows machine keeps working in parallel — same account, both are the §5.e assistant. The judge/assistant independence argument is unchanged: Claude (any surface) is a different model from the pipeline's Qwen3.

## 2.2 Coding assist (code gen / review / unit tests) (v3.0 step format)

*Goal of this section:* serve a coding model on Spark-1 and connect the three coding clients — the tools engineers use to get code written, reviewed and tested by the model.

**De-risks:** UC-FSW-1 (coding-standard review assist), UC-FSW-2 (unit-test scaffolding).
**Machines:** answer/coding model on **Spark-1**; client on the engineer's laptop or Spark-2.

☐ **Step 1 — Serve a coding model on Spark-1.**
**Why:** every client below talks to this one OpenAI-compatible endpoint.
**Before you run it:** Qwen3-Coder-30B "Flash" MoE is the primary coding model — fast on Spark; `Qwen/Qwen3-Coder-Next` (80B-A3B MoE, 256K context — corrected name, there is no "Qwen3-Coder-80B" repo) for more capability. Alternative to the llama.cpp command below: the NVIDIA aarch64 vLLM container (NVFP4, concurrency) at :8000 — remember `--moe-backend marlin` for NVFP4 MoE.
**Run:**
```bash
# via llama.cpp (GGUF from the HF mirror — build per §2.1(a)):
./build/bin/llama-server -m <qwen3-coder-30b-a3b.gguf> --port 8000 \
  -ngl 999 -fa on --no-mmap --cache-type-k q8_0 --cache-type-v q8_0 --jinja
```
**Expect:** an OpenAI-compatible endpoint on :8000.

☐ **Step 2 — Install Cline (VS Code extension) — the CONFIRMED interactive IDE client for engineers.** (An **IDE** — "integrated development environment" — is the program engineers write code in; here, VS Code.)
**Why:** open source (Apache-2.0), talks to any OpenAI-compatible endpoint, and — decisive for us — is a **native MCP client** (MCP, the Model Context Protocol, is the standard way of plugging tools into AI agents — explained fully in §2.10): once the §2.10 `p42-kb` server exists, engineers get cited knowledge-base answers *inside the IDE* while coding. Yes, it is slower than the headless tools — its human-approval loop (review every edit/command before it runs) is a *feature* in a flight-software context, not a defect.
**Before you run it:** known UI regression: the Base URL field can be missing under the plain "OpenAI" provider — use **"OpenAI Compatible"** specifically. Ref: https://github.com/cline/cline/issues/7114 Docs: https://docs.cline.bot/provider-config/openai-compatible
**Run (in VS Code):** install "Cline" from the Marketplace (enclave: pinned **VSIX** — VS Code's installable extension-package file format — from the GitHub-releases mirror, `cline/cline`) → ⚙️ Settings → API Provider = **"OpenAI Compatible"** → Base URL `http://<spark-1-ip>:8000/v1`, API Key = any string, Model ID = the exact served model name.
**Expect:** Cline chats against the Spark endpoint from inside VS Code.

☐ **Step 3 — Install aider (CLI).**
**Why:** the repo-map specialist (§2.4) and one of the two scored M42 harnesses. A **harness** is the program wrapped around a model that lets it act on a repository — read files, propose edits, run commands — rather than just chat; **M42** is the project's coding benchmark (Benchmark Strategy companion document).
**Before you run it:** the model name **MUST** be prefixed with `openai/`. Docs: https://aider.chat/docs/llms/openai-compat.html
**Run:**
```bash
uv tool install aider-chat                   # (v4.26) CLI apps install via uv tool — bare pip is PEP-668-blocked on this OS (upgrade later: uv tool upgrade aider-chat)
export OPENAI_API_BASE=http://<spark-1-ip>:8000/v1
export OPENAI_API_KEY=dummy
aider --model openai/<served-model-name>     # MUST prefix the model with openai/
```
**Expect:** aider starts and answers against the served model.

☐ **Step 4 — Install pi (terminal coding agent) — NEW in v0.14, WP1 evaluation.**
**Why:** minimal open-source terminal harness (MIT, `@earendil-works/pi-coding-agent` on npm, ~76k-star project) with properties that fit this stack unusually well: **first-class llama.cpp support**, proper **headless modes** (headless = runs without a user interface, fully scriptable; `-p` one-shot, `--mode json` structured events) and **JSONL session logs** (JSONL = a log file with one JSON record per line, trivially machine-readable) — exactly the instrumentation the M42 benchmark wants.
**Before you run it:** no built-in MCP (extension route only). Evaluate during WP1 familiarisation as a **candidate M42 harness** (Benchmark Strategy v0.5 rules apply); the scored harness set is decided and frozen at G2.
**Run:**
```bash
npm install -g --ignore-scripts @earendil-works/pi-coding-agent   # -g = install system-wide; --ignore-scripts = do not run packages' own install scripts (provenance hygiene); via the npm mirror in the enclave
# point it at the Spark endpoint (OpenAI-compatible custom provider or /llama for llama-server)
```
**Expect:** `pi` runs and reaches the Spark endpoint.

**TEST:** point the client at a small public sample repo. Ask it to (a) write a unit test for one function, or (b) fix a seeded bug. **Expected:** it produces a **sensible diff** that applies cleanly and, for the unit test, actually runs against the function. For the UC-FSW-1 angle, also ask it to review a short C function against a stated coding rule and check the comments are on-point rather than generic.

☐ **Step 5 — Teardown.**
**Run:**
```bash
pkill llama-server              # and/or stop the vllm container
nvidia-smi
```
**Expect:** GPU memory released.

---

> **📋 STEP RECORD — §2.2** &nbsp;&nbsp; ☐ Done &nbsp; ☐ Deviation logged &nbsp; ☐ N/A (reason below)
> Machine: ☐ Spark-1 ☐ Spark-2 &nbsp;·&nbsp; Operator: `____________` &nbsp;·&nbsp; Date: `____________`
> Values recorded (versions / tags / measurements / anomalies): `________________________________________________`
>
> **Notes / observations / follow-ups** *(use as much of this space as needed)*:
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`

## 2.3 Autocomplete (FIM) — OPTIONAL, defer unless a ladder asks for it (v3.0 step format)

*Goal of this section:* self-hosted inline code autocomplete via Tabby. **FIM** ("fill-in-the-middle") means the model completes code *between* what is before and after the cursor — the "ghost text" style of assistant.

**De-risks:** no current seed MVP. (New in v0.2: deprioritised — set this up only if a discipline's submitted ladder includes autocomplete, or if WP1 has spare time.)
**Machine:** Spark-1 (self-hosted Tabby) + IDE plugin on the laptop.

☐ **Step 1 — DECISION: which Tabby route?**
**Why:** the obvious Docker route does not work on this machine, so the route must be chosen before typing anything.
**Before you run it** — the previously post-command warning, now the decision rule:

- **CONFIRMED 2026-07-10 (was "unverified"): there is NO official arm64 Tabby image** — all `tabbyml/tabby` Docker Hub tags are linux/amd64 only, and the arm64 request (TabbyML/tabby#623) was never resolved with an official CUDA arm64 image. **The stock docker command in Step 2 will therefore fail on the Spark.**
- **Mainline route on Spark:** run Tabby built from source OR (simpler) run Tabby anywhere convenient and point its **HTTP model config** (`[model.completion.http]` / `[model.chat.http]`) at a Spark-served Qwen2.5-Coder endpoint (vLLM/llama.cpp). Ref: https://tabby.tabbyml.com/docs/administration/model/ · https://github.com/TabbyML/tabby/issues/623
- Note also the current docs' image is `registry.tabbyml.com/tabbyml/tabby` (Docker Hub `tabbyml/tabby` still exists).

☐ **Step 2 — Set up Tabby (per the chosen route) with Qwen2.5-Coder.**
**Why:** Qwen2.5-Coder has native fill-in-the-middle support. Docs: https://tabby.tabbyml.com/docs/quick-start/installation/docker/
**Before you run it:** the command below is the stock Docker form — per the Step 1 decision it fails on the Spark (amd64-only image); it applies only off-box or as the reference for the source-built/HTTP-config route. FIM template for Qwen2.5-Coder: `<|fim_prefix|>{prefix}<|fim_suffix|>{suffix}<|fim_middle|>`.
**Run:**
```bash
# -v = persist Tabby's data in $HOME/.tabby on the host; --device cuda = run inference on the GPU
docker run -d --gpus all -p 8080:8080 -v $HOME/.tabby:/data \
  tabbyml/tabby:latest serve --model Qwen2.5-Coder-7B --device cuda
```
Then install the Tabby IDE plugin (VS Code / JetBrains / Vim).
**Expect / If not:** on the Spark, `exec format error` is EXPECTED with the stock image — use the Step 1 mainline route (source build, or HTTP model config against a Spark endpoint).

> [!NOTE]
> **Honest caveat:** autocomplete is the most latency-sensitive use case, and **latency on the Spark is NOT representative** of production hardware. Judge *quality/relevance* of completions here, not responsiveness.

**TEST:** in the editor with the Tabby plugin active, start typing a function; confirm **inline ghost-text completions** appear and are acceptable.

☐ **Step 3 — Teardown.**
**Run:**
```bash
docker stop tabby && docker rm tabby      # container name may be auto-generated; check `docker ps`
nvidia-smi
```
**Expect:** GPU memory released.

---

> **📋 STEP RECORD — §2.3** &nbsp;&nbsp; ☐ Done &nbsp; ☐ Deviation logged &nbsp; ☐ N/A (reason below)
> Machine: ☐ Spark-1 ☐ Spark-2 &nbsp;·&nbsp; Operator: `____________` &nbsp;·&nbsp; Date: `____________`
> Values recorded (versions / tags / measurements / anomalies): `________________________________________________`
>
> **Notes / observations / follow-ups** *(use as much of this space as needed)*:
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`

## 2.4 Codebase navigation & Q&A (repo map) (v3.0 step format)

*Goal of this section:* prove cited question-answering over a large codebase. A **repo map** is aider's compressed index of a repository (files, functions, call relationships) that lets the model navigate code far bigger than its context window.

**De-risks:** UC-GNC-2 (worked example — RFM GNC codebase interrogation). This track rehearses exactly what UC-GNC-2's acceptance criteria will measure: cited answers (file/function), correct navigation, no uncited claims.
**Machine:** coding/reasoning model on Spark-1; **aider** (or Cline) with a repo map on the laptop/Spark-2.

☐ **Step 1 — Serve the coding/reasoning model on Spark-1.**
**Why:** same endpoint pattern as §2.2.
**Before you run it:** model choice as in §2.2 Step 1 (Qwen3-Coder-30B or Qwen3-Coder-Next).
**Run:** per §2.2 Step 1 (llama.cpp or the vLLM container on :8000).
**Expect:** endpoint live on :8000.

☐ **Step 2 — Run aider over a sizeable public sample repo.**
**Why:** aider builds a **repo map** over a large codebase — that is why it is the tool for this track.
**Before you run it:** prefer an **embedded/control-flavoured C/C++ project** (closer to GNC flight code than a web framework); the model name must carry the `openai/` prefix.
**Run:**
```bash
uv tool install aider-chat   # (v4.26) not pip — see §2.2 Step 3
export OPENAI_API_BASE=http://<spark-1-ip>:8000/v1
export OPENAI_API_KEY=dummy
cd <sample-large-public-repo>
aider --model openai/<served-model-name>
```
**Expect:** aider indexes the repo and answers navigation questions with file/function citations.

**TEST:** in the sample repo, ask navigation questions: *"How does `<module>` work?"* and *"Where is `<behaviour>` implemented?"* **Expected:** the model gives **correct, cited navigation** — names the right files/functions, and its explanation matches the actual code (spot-check the files it names). *(New in v0.2)* Also rehearse the change-impact pattern: pick a function, ask *"what breaks if I change this signature?"*, and verify the caller list against `grep` — this is UC-GNC-2's core benchmark and its recall/precision habit starts here.

☐ **Step 3 — Teardown.**
**Run:**
```bash
pkill llama-server             # or stop the vllm container
nvidia-smi
```
**Expect:** GPU memory released.

---

> **📋 STEP RECORD — §2.4** &nbsp;&nbsp; ☐ Done &nbsp; ☐ Deviation logged &nbsp; ☐ N/A (reason below)
> Machine: ☐ Spark-1 ☐ Spark-2 &nbsp;·&nbsp; Operator: `____________` &nbsp;·&nbsp; Date: `____________`
> Values recorded (versions / tags / measurements / anomalies): `________________________________________________`
>
> **Notes / observations / follow-ups** *(use as much of this space as needed)*:
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`

## 2.5 Grounded document drafting (v3.0 step format)

*Goal of this section:* prove that the model can draft formal documents that stay **grounded** — every statement traceable to the supplied input, nothing invented.

**De-risks:** UC-FV-2 (procedure & script drafting), UC-FVI-2 (integration sequences), UC-SE-1 (document QA), UC-FSW-3 (SW doc drafting).
**Machine:** reasoning model on Spark-1; interact via Open WebUI or aider/curl.

☐ **Step 1 — Serve a reasoning model on Spark-1.**
**Why:** drafting quality leans on reasoning strength.
**Before you run it:** e.g. `nvidia/Qwen3-32B-NVFP4` via vLLM (§2.1.2.1 Step 2), or gpt-oss-120b via llama.cpp (§2.1.2.1 Step 4).
**Run:** per §2.1.2.1.
**Expect:** endpoint live on :8000.

☐ **Step 2 — Request a grounded draft from a public stand-in input.**
**Why:** exercises the pattern the FV/SE use cases need: structured input in, traceable draft out.
**Before you run it:** feed a **public stand-in** for structured input — e.g. a public requirements/test table (NOT project data) — and ask for a test-procedure draft or a doc section.
**Run:**
```bash
curl http://<spark-1-ip>:8000/v1/chat/completions -H "Content-Type: application/json" \
  -d '{"model":"nvidia/Qwen3-32B-NVFP4","messages":[
        {"role":"system","content":"You draft formal verification test procedures from a requirements table."},
        {"role":"user","content":"<paste the public requirements/test table here>"}]}'
```
**Expect:** a draft grounded in the supplied table (checked properly in the TEST below).

**TEST:** ask for a test-procedure draft from the sample table. **Expected:** the draft is **grounded in the supplied table** (every step traces back to a requirement/row — no invented requirements) and is **usable** as a first draft with light editing. Check specifically that it did not hallucinate requirements not present in the input. *(New in v0.2)* For the UC-SE-1 angle, also run the reverse: give it a short document with **seeded defects** (a broken cross-reference, an inconsistent ID) and ask it to QA-check — confirm it flags the seeded issues and does not invent others.

☐ **Step 3 — Teardown.**
**Run:**
```bash
docker stop <vllm-container>    # or `pkill llama-server`
nvidia-smi
```
**Expect:** GPU memory released.

---

> **📋 STEP RECORD — §2.5** &nbsp;&nbsp; ☐ Done &nbsp; ☐ Deviation logged &nbsp; ☐ N/A (reason below)
> Machine: ☐ Spark-1 ☐ Spark-2 &nbsp;·&nbsp; Operator: `____________` &nbsp;·&nbsp; Date: `____________`
> Values recorded (versions / tags / measurements / anomalies): `________________________________________________`
>
> **Notes / observations / follow-ups** *(use as much of this space as needed)*:
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`

## 2.6 CI agents — OPTIONAL (v3.0 step format)

> [!NOTE]
> **(v4.2) Watchlist — NVIDIA NemoClaw/OpenShell:** NVIDIA now ships **NemoClaw** (Apache-2.0), a reference stack that runs AI agents inside **OpenShell** sandbox containers on DGX Spark with network-policy control and credential custody — independent validation of exactly this section's sandbox-the-agent posture. **Not adoptable here yet:** it currently supports only the OpenClaw / Hermes / LangChain Deep Agents frameworks — NOT OpenHands, Cline, aider or pi. Re-evaluate at G2/WP3 if its framework support widens. Docs: https://docs.nvidia.com/nemoclaw/

*Goal of this section:* trial OpenHands, an autonomous "CI agent" — an AI agent that works on a code task end-to-end (edit, run, test) inside a sandboxed environment, suited to batch jobs rather than live interaction. (**CI** — "continuous integration" — is the automated build-and-test pipeline that runs on a code repository; a CI agent is an AI worker slotted into that kind of pipeline.)

**De-risks:** UC-FSW stretch options only — set up if the FSW ladder points this way.
**Machine:** OpenHands via Docker (on Spark-2 or the laptop), pointing at Spark-1's endpoint.

☐ **Step 1 — Start OpenHands and point it at the Spark endpoint.**
**Why:** proves the agent loop runs against a local model.
**Before you run it:** docs: https://docs.openhands.dev/openhands/usage/llms/local-llms From inside the OpenHands container the host endpoint is `host.docker.internal`, not `localhost`. And the architecture caveat, before pulling anything:

> [!NOTE]
> **Updated 2026-07-10:** OpenHands runs its **app container plus a separate sandbox, now called the "agent-server"** (`ghcr.io/openhands/agent-server:<ver>-python`; the old `runtime:*-nikolaik` image naming is obsolete). Good news: **agent-server images are published for linux/arm64**. The app image's arm64 manifest could not be confirmed remotely — check on box: `docker run --rm <image> uname -m` → `aarch64` for BOTH images before relying on it. Docs: https://docs.openhands.dev/openhands/usage/llms/local-llms · https://docs.openhands.dev/sdk/guides/agent-server/docker-sandbox

**Run:** follow the docker run quickstart from the docs, then configure in the browser:
open `http://localhost:3000` → Settings → LLM → enable Advanced → **Base URL** = `http://host.docker.internal:8000/v1` (vLLM), set LLM Model + a dummy key.
**Expect / If not:** the UI loads and a chat reaches the Spark model. `exec format error` → an amd64-only image slipped in — re-check both images' architecture per the NOTE above.

> [!TIP]
> **Note:** run CI agents as **batch** jobs — they are slow on the Spark (multi-step autonomous loops). Speed here is not representative; judge whether the change is correct and tested.

**TEST:** give OpenHands a **trivial seeded issue** on a small sample repo (e.g. "function returns wrong value for empty input; fix and add a test"). **Expected:** it returns a **tested change** (a diff plus a passing test).

☐ **Step 2 — Teardown.**
**Run:**
```bash
docker compose down             # or stop both OpenHands containers
# stop the vllm container serving the endpoint
nvidia-smi
```
**Expect:** GPU memory released.

---

> **📋 STEP RECORD — §2.6** &nbsp;&nbsp; ☐ Done &nbsp; ☐ Deviation logged &nbsp; ☐ N/A (reason below)
> Machine: ☐ Spark-1 ☐ Spark-2 &nbsp;·&nbsp; Operator: `____________` &nbsp;·&nbsp; Date: `____________`
> Values recorded (versions / tags / measurements / anomalies): `________________________________________________`
>
> **Notes / observations / follow-ups** *(use as much of this space as needed)*:
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`

## 2.7 Data & log analysis (NEW in v0.2) (v3.0 step format)

*Goal of this section:* prove the notebooks-plus-LLM pattern — deterministic data crunching in code, the LLM only for the language layer, every figure checked back against the data.

**De-risks:** UC-FV-1 (test-log triage), GNC Monte-Carlo campaign triage, UC-DB-2 (database–documentation consistency checks). Several seed ladders lean on "cluster these logs / cross-check these tables" — that is a notebooks-plus-LLM pattern, not a RAG pattern, so it gets its own track.
**Machine:** Spark-2 (notebooks + batch analysis), calling Spark-1's LLM endpoint where language help is needed.

☐ **Step 1 — Set up JupyterLab and the analysis stack on Spark-2.**
**Why:** notebooks are the working surface for this track (**JupyterLab** is the browser-based notebook environment; a **notebook** is a document mixing runnable code, its results and explanatory text).
**Before you run it:** DGX OS ships the **DGX Dashboard** with a managed **JupyterLab** — check it first (User Guide) before installing your own. Only if you install your own, proceed below. All these packages are pure-Python or ship aarch64 wheels — no image-architecture risk.
**Run:**
```bash
uv venv ~/p42/lab-venv && source ~/p42/lab-venv/bin/activate   # (v4.26) named venv — reactivate in every new shell
uv pip install jupyterlab pandas polars pyarrow matplotlib openai
jupyter lab --ip 0.0.0.0 --port 8888 --no-browser   # --ip 0.0.0.0 = listen on all interfaces (reachable from your laptop); --no-browser = don't try to open one on the Spark
```
**Expect:** browse to `http://<spark-2-ip>:8888` (token printed in the terminal) and the notebook UI loads.

☐ **Step 2 — Wire the notebook to Spark-1's LLM endpoint.**
**Why:** the `openai` client points at Spark-1 for LLM assistance inside notebooks.
**Run (in a notebook cell):**
```python
from openai import OpenAI
llm = OpenAI(base_url="http://<spark-1-ip>:8000/v1", api_key="dummy")  # vLLM or llama-server endpoint
```
**Expect:** a completion call from the notebook returns.

☐ **Step 3 — Prove the pattern on stand-in data.**
**Why:** this division of labour — deterministic code for numbers, LLM for words — is the whole point of the track.
**Before you run it:** use public or synthetic stand-in data — e.g. generate a synthetic "test campaign" CSV of a few thousand runs with seeded anomaly clusters. The pattern to prove:
1. Load logs/tables with pandas/polars; do the deterministic heavy lifting (parsing, grouping, thresholding) in code — not in the LLM.
2. Use the LLM for the language layer: summarise each anomaly cluster, propose a disposition, draft the report paragraph — always from the computed data you pass it.
3. Round-trip check: every number in the LLM's summary must exist in the dataframe you gave it.
**Expect:** the notebook pipeline runs end-to-end on the synthetic data.

**TEST:** on the synthetic campaign data, the notebook pipeline (a) finds the seeded anomaly clusters deterministically, and (b) the LLM writes a per-cluster summary in which **every quoted figure matches the dataframe** — no invented statistics. For the UC-DB-2 angle: give it two small tables with seeded mismatches (one value different, one row missing) and confirm the produced mismatch report finds exactly the seeded discrepancies.

☐ **Step 4 — Teardown.**
**Run:**
```bash
# stop the JupyterLab process with Ctrl-C in its terminal — nothing else to release
nvidia-smi    # confirm, if the notebook loaded models
```
**Expect:** nothing left on the GPU.

---

> **📋 STEP RECORD — §2.7** &nbsp;&nbsp; ☐ Done &nbsp; ☐ Deviation logged &nbsp; ☐ N/A (reason below)
> Machine: ☐ Spark-1 ☐ Spark-2 &nbsp;·&nbsp; Operator: `____________` &nbsp;·&nbsp; Date: `____________`
> Values recorded (versions / tags / measurements / anomalies): `________________________________________________`
>
> **Notes / observations / follow-ups** *(use as much of this space as needed)*:
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`

## 2.8 (Optional) Clustering for the quality-ceiling test (v3.0 step format)

*Goal of this section:* physically join the two Sparks into one 256 GB pair for a one-off experiment on models too big for a single box.

*Terms used in this section, in plain language:* **clustering** here means connecting the two machines with a direct high-speed cable so one model can span both. **Tensor parallelism (TP)** splits a single model's computation across both GPUs. **NCCL** is NVIDIA's library that moves data between the GPUs; it only performs over **RDMA/RoCE** (card-to-card data transfer that bypasses the CPU) — plain TCP networking is the slow fallback. A **DAC** is the passive direct-attach copper cable joining the two QSFP network ports (the square high-speed network sockets on the back of each unit).

> [!IMPORTANT]
> **One-off experiment, NOT day-to-day.** Purpose: see whether a model too big for one box answers *materially* better on the same KB/coding eval — in particular whether a ~480B-class open coding model writes materially better **new code** (greenfield C flight-SW modules, Python tooling) than the single-box 30B coder. Models for this experiment: §3.a cluster-path table. The result is direct evidence for the 2027 hardware recommendation. For normal work, keep the Spark-1 / Spark-2 role split. In Project 42 terms this feeds the WP3 implementation definition: if the big model is materially better on a track that matters, that is evidence for the scale-up recommendation in WP6, not a reason to run clustered day-to-day.

Playbook: https://github.com/NVIDIA/dgx-spark-playbooks/tree/main/nvidia/connect-two-sparks &nbsp;|&nbsp; User Guide "Spark Stacking": https://docs.nvidia.com/dgx/dgx-spark/spark-clustering.html

The steps below are the gist — **follow the playbook exactly.**

☐ **Step 1 — Cable the two machines.**
**Why:** the direct QSFP link is the only path fast enough for cross-machine model serving.
**Before you run it:** cable the two **QSFP / ConnectX-7** ports directly with a passive DAC. The official stacking doc lists **Amphenol NJAAKK-N911** and **Luxshare 400G QSFP112** cables; the NVIDIA `Q56-200G-CU0-5` 200G QSFP56 DAC is the part bundled/sold by resellers with Founders Edition units (corrected 2026-07-10 — either works, follow the doc).
**Run:** physical cabling only — no commands.
**Expect:** link lights on both ports.

☐ **Step 2 — DECISION: identify the correct interface names.**
**Why:** each CX-7 port shows two names (e.g. `enp1s0f1np1` and `enP2p1s0f1np1`), and the docs disagree on which to use.
**Before you run it:** the GitHub playbook says to use the `enp1...` names (note: the docs.nvidia.com stacking page's own examples use `enP2...`, so reconcile against the output below on your units). **VERIFY:** the exact interface names must be confirmed against `ip link` output on your units.
**Run:**
```bash
ip link
```
**Decide:** record the names your units actually show and use those consistently in every NCCL/vLLM environment variable below.

☐ **Step 3 — Set up SSH/discovery between the nodes.**
**Why:** the cluster tools need passwordless SSH both ways.
**Run** (from one node):
```bash
discover-sparks.sh   # NVIDIA's script, from the playbook — auto-configures passwordless SSH both ways
```
**Expect:** each node can SSH to the other without a password prompt.

☐ **Step 4 — Build NCCL.**
**Why:** NCCL is the transport every distributed-inference option below rides on.
**Before you run it:** the NCCL playbook builds NCCL from source for **Blackwell (compute_121/sm_121)** (corrected 2026-07-10: the playbook does not claim source-build is *required* for full bandwidth — follow it as the supported recipe). **VERIFY:** NCCL-from-source must be confirmed against your units. Playbook: https://github.com/NVIDIA/dgx-spark-playbooks/tree/main/nvidia/nccl
**Run:** follow the NCCL playbook.
**Expect:** the playbook's NCCL tests pass across the link.

☐ **Step 5 — Run distributed inference.**
**Why:** this is the experiment itself — serving a model that spans both boxes.
**Before you run it — read the traps FIRST; they are the difference between a working cluster and a silent week-long debug:**

> [!WARNING]
> **v0.4 community additions — the four clustering traps:**
> 1. **Give NCCL BOTH RoCE halves of the CX-7 port — or silently lose half the bandwidth.** Each CX-7 port appears to Linux as TWO RoCE devices, and NCCL uses only the ones you name. Name both: `export NCCL_IB_HCA=rocep1s0f1,roceP2p1s0f1` — and mind the naming trap: lowercase `p1` in the first device name, uppercase `P2` in the second. Also point `NCCL_SOCKET_IFNAME`/`GLOO_SOCKET_IFNAME`/`UCX_NET_DEVICES` at the link interface, and set MTU 9000 ("jumbo frames" — larger network packets). Validate the jumbo frames with `ping -M do -s 8972`: `-M do` forbids splitting the packet and `-s 8972` sets a payload that exactly fills a 9000-byte frame, so the ping only succeeds if jumbo frames genuinely work end-to-end. Why all this matters: omitting one RoCE half produces no error — it just silently halves bandwidth. A healthy link runs ≈ 24.4 GB/s; verify by launching with `NCCL_DEBUG=INFO` (NCCL's verbose logging) and checking the log lists both NET/IB devices.
> 2. **TCP over the 200G link is CPU-bound (~13–16 Gbps) — that is normal, not a fault.** The link only reaches its rated speed via RDMA/RoCE (direct card-to-card transfer); ordinary TCP networking over the same cable is limited by the CPU, not the cable. Consequence for daily use: admin traffic (SSH, file copies) goes over the ordinary LAN, and the QSFP link is reserved for NCCL only. Only investigate if the link is slow even on the RDMA test tool `ib_write_bw` — that genuinely-broken case has been fixed in the field by a CX-7 firmware update followed by a full power-off with the cables physically disconnected.
> 3. **Known vLLM TP=2 hang** — the symptom is "one node drops, the other pegged at 100% forever". The cause is CUDA graphs (a GPU launch optimisation) crashing on the cross-node path. Prevention: pin PyTorch at 2.9.1 (not 2.10.0), or serve with `--enforce-eager` (which disables CUDA-graph capture and runs GPU operations one at a time). A related warning sign to watch for: `NCCL INFO NET/IB : No device found` in the worker's log means NCCL silently fell back from RDMA to plain sockets — everything still "works", but performance dies; fix the device naming per trap 1 rather than accepting it.
> 4. **Start from the community images built for exactly this** (`eugr/spark-vllm-docker` — battle-tested single/multi-node GB10 builds) instead of building your own stack and fighting compiler errors like `ptxas: sm_121a not defined` from scratch. And set expectations correctly: clustering buys **capacity** — a ~170 GB practical two-node model ceiling, with big-MoE models plus EAGLE3 speculative decoding as the real unlock — and up to ~1.8× TP speedups on some dense models. It does not make everything faster: llama.cpp RPC on models that already fit one box is slightly *slower* than just running them on that one box.
> 5. **(v0.11) The cross-node NCCL all-reduce deadlock is a LAUNCH-METHOD problem, not a transport problem.** A fully-diagnosed forum case: TP=2 hung at the first all-reduce (~96 % GPU, forever) across three vLLM versions AND TRT-LLM, on both RoCE and TCP — while standalone `all_reduce_perf` passed. Resolution: launching via `eugr/spark-vllm-docker`'s `launch-cluster.sh` (which sets the full env-var set on both nodes) worked immediately, with and without Ray — **bare manual `--nnodes/--master-addr` launches were the culprit.** Do not hand-roll the cluster launch. Also confirmed there: **Ubuntu 25.10 is unsupported on GB10** — stay on DGX OS; and if TP init still wedges, pipeline parallelism (PP=2 — splitting the model's *layers* between the two machines, instead of splitting every layer across both as TP does) avoids the cross-node all-reduce at init as a fallback.
> 6. **(v4.15) Validate the link bandwidth in BOTH directions — a one-way test can pass while the return direction is broken.** Run `ib_write_bw` twice, swapping roles (server on node A / client on node B, then the reverse) — a one-way test would have passed the 2026-08 kernel regression (§1.2 caution), which crippled only *inbound* RDMA. Expect roughly symmetric ~100+ Gbit/s both ways; any asymmetry → check the kernel version against the §1.2 kernel-regression caution before debugging anything else.
>
>    ```bash
>    # direction 1:  on node A: ib_write_bw          # server, waits
>    #               on node B: ib_write_bw <node-A-link-ip>
>    # direction 2 (SWAP):  server on node B, client on node A — repeat
>    # PASS: both directions report ~symmetric ~100+ Gbit/s
>    ```

**Run — the two options:**
- **vLLM + Ray** with tensor parallelism (e.g. quantized **Llama-3.1-405B**): start the Ray cluster on both nodes via `run_cluster.sh` (the official playbook's script), then `vllm serve` from the head node with `--gpu-memory-utilization 1.0`; verify with `ray status`. Env: `NCCL_SOCKET_IFNAME`, `UCX_NET_DEVICES`, `VLLM_HOST_IP`. **In practice, prefer `launch-cluster.sh` from `eugr/spark-vllm-docker` over any hand-rolled launch — see trap 5 above** (bare `--nnodes/--master-addr` launches are the documented cause of the all-reduce deadlock).
- **llama.cpp RPC** ("remote procedure call" — llama.cpp's mode where one machine hosts part of the model and the other calls into it over the network) to split a large GGUF across both boxes.
**Expect / If not:** the clustered model serves; if TP=2 hangs at the first all-reduce → trap 5 (launch method); if bandwidth is half of ~24.4 GB/s → trap 1 (only one RoCE half); if TCP speeds appear → traps 1–2 (silent socket fallback).

☐ **Step 6 (v4.24) — Soak-test the cluster under sustained high concurrency BEFORE G2.**
**Why:** a cluster that serves one benchmark run cleanly can still fall over under sustained load — and a reboot-under-load is a **G2 availability finding**, so it must be looked for deliberately, not discovered at the demo.
**Before you run it** — read both cautions first:

> [!WARNING]
> **A published dual-Spark lab crashed under exactly this load — reproduce before trusting, and before adopting any mitigation.** The fact: a public dual-Spark lab report documents a **kernel Oops followed by a spontaneous reboot of the head node** under sustained RoCE load, attributed by the lab to the `nvidia-dgx-telemetry` service polling the ConnectX-7 firmware while the link was saturated (source: https://github.com/elsung/dgx-spark-deepseek-v4-flash — a single lab, and its benchmarks were AI-executed per the repo's own disclaimer, so treat it as a lead to reproduce, not an established fact). Why it matters here: if the same failure exists on our pair, the cluster cannot be trusted for the multi-user evaluation window, and G2 must know that. What to do: run the soak below and watch the kernel log; if the box reboots or Oopses, record it as a G2 availability finding. **One explicit warning about the circulated fix:** a `vm.compaction_proactiveness=0` sysctl mitigation circulates with this story, but that setting (memory-compaction tuning) does **NOT** match the stated telemetry-polling root cause — verify what the source lab actually changed before adopting any mitigation, and never apply a mitigation whose mechanism you cannot connect to the diagnosis.

**Run** (≥ 60 minutes of continuous concurrent load against the clustered endpoint, kernel log watched throughout):
```bash
# four parallel client loops = sustained high concurrency; ( … ) & runs each loop in the
# background so they run simultaneously; wait = only return when every loop has finished;
# > /dev/null discards the replies — this soak tests survival, not answer content
for i in 1 2 3 4; do
  ( for n in $(seq 1 200); do    # seq 1 200 = the numbers 1..200, i.e. 200 requests per client
      curl -s http://<head-node-ip>:8000/v1/chat/completions -H "Content-Type: application/json" \
        -d '{"model":"<served-model>","messages":[{"role":"user","content":"Summarise the four clustering traps in 500 words."}],"max_tokens":1024}' > /dev/null
    done ) &
done
wait

# meanwhile, in a second terminal on the HEAD node:
sudo dmesg --follow    # --follow = keep printing new kernel messages as they arrive; watch for "Oops" / RoCE / mlx5 errors
```
**Expect / If not:** the full soak completes with no kernel Oops, no spontaneous reboot, and throughput that degrades gracefully rather than collapsing. Any Oops or reboot → capture `dmesg`, note whether `nvidia-dgx-telemetry` was running, record the event in the STEP RECORD **and flag it to G2 as an availability finding** — do not silently retry.

> **📋 STEP RECORD — §2.8** &nbsp;&nbsp; ☐ Done &nbsp; ☐ Deviation logged &nbsp; ☐ N/A (reason below)
> Machine: ☐ Spark-1 ☐ Spark-2 &nbsp;·&nbsp; Operator: `____________` &nbsp;·&nbsp; Date: `____________`
> Values recorded (versions / tags / measurements / anomalies): `________________________________________________`
>
> **Notes / observations / follow-ups** *(use as much of this space as needed)*:
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`

### 2.8.a DeepSeek-V4-Flash cluster serving — source-rebuild route ("Aiden-recipe" class, NEW in v0.10) (v3.0 step format)

*Goal of this section:* rebuild, from auditable sources, the community's strongest 2-Spark serving result.

> [!NOTE]
> **What this is:** the community's strongest 2-Spark serving result (the "Aiden recipe": V4-Flash + b12x kernels, up to 1M context) ships as an unauditable binary image — but every ingredient is published as source, so we rebuild the capability ourselves. Full background and quality assessment: **Model Catalogue §4.2.a**.

Build once on the internet-connected shakedown pair; record everything for the enclave reproduction.

☐ **Step 1 — Install the b12x kernels at a pinned version.**
**Why:** the b12x kernels are what make V4-Flash fast on GB10. (In GPU jargon a **kernel** is a small compute program that runs on the GPU — unrelated to the Linux kernel of §1.2.)
**Before you run it:** pin the version (Apache-2.0, source at `lukealonso/b12x`). The kernels are enabled at serve time via `VLLM_USE_B12X_MOE=1` (+ `VLLM_USE_B12X_WO_PROJECTION` per recipe). Check whether the b12x integration has landed in `eugr/spark-vllm-docker` (issue #174) — if yes, prefer that maintained path.
**Run:**
```bash
uv pip install b12x==0.10.x    # pinned version — record the exact pin. (v4.26) NOTE: this install
                               # belongs INSIDE the recipe's Docker image build (b12x runs in the serving
                               # container, not on the host); if testing on the host anyway, activate a venv first
```
**Expect:** installs at the recorded pin.

☐ **Step 2 — Clone the recipe repos and harden the pins.**
**Why:** the recipes carry the staged Dockerfiles + vendored patches + build script.
**Before you run it:** the target checkpoint is now **V4-Flash-0731** (released 2026-07-31; same architecture, retrained — large agentic gains: DeepSWE 7.3→54.4, Cybergym 38.7→76.7; verified 2026-08-05). Clone `tonyd2wild/deepseek-v4-flash-dgx-spark` (plain V4-Flash TP=2 — the quality-first target) and, for the 1M-context variant, the recipe's **0731 successor** `tonyd2wild/DeepSeek-v4-Flash-0731-DSpark-1M-NVFP4-KV-2x-DGX-Spark` (the pre-0731 `...DeepSeek-v4-Flash-DSpark-1M...` repo is superseded); as an alternative 0731 DSpark recipe, `MiaAI-Lab/DeepSeek-v4-Flash-DSpark-2x-DGX-Spark` is also fully sourced. Note the 1M/DSpark recipes' OLD quality flag was measured on the **pre-0731** checkpoint — it must be **re-measured on 0731** in step 5, not carried forward blindly. **Harden the pins before building:** replace any floating upstream references (vLLM, FlashInfer, base image) with exact commit SHAs/tags in the Dockerfiles; record them in the build log.
**Run:** clone the repos and edit the Dockerfile pins as above.
**Expect:** no floating references remain in the Dockerfiles.

☐ **Step 3 — Build, tag and serve.**
**Why:** a locally-built, locally-tagged image is auditable and reproducible.
**Before you run it:** §2.8 traps 1–3 apply in full — both RoCE halves, PyTorch pin, no Ray.
**Run:** build & tag the image locally as p42/vllm-v4flash:⟨date⟩; serve per the recipe's compose/env template
(TP=2, `--distributed-executor-backend mp` — the plain-multiprocessing executor, per §1.7's no-Ray rule — FP8 KV, `shm_size: 64gb`, `memlock=-1`).
**Expect:** the clustered V4-Flash endpoint serves.

☐ **Step 4 — Check against the reference numbers.**
**Why:** the community numbers are a misconfiguration detector, not targets to exceed.
**Expect:** plain V4-Flash ≈ 38–44 tok/s single-stream at 200K ctx; Aiden-image class ≈ 30–45 tok/s at 1M ctx; TTFT ~53 s @32K / ~250 s @128K is *normal* on this config. **If far below** ⇒ misconfiguration (RoCE halves, b12x not active — check startup log for the b12x kernel banner).

☐ **Step 5 — Quality gate before any adoption.**
**Why:** speed without quality is worthless here.
**Run:** run the M42 dev subset + KB spot-checks; the DSpark spec-decode variant's quality flag (Catalogue §4.3) was measured on the **pre-0731** checkpoint and is **re-opened, not cleared** — re-measure it on 0731 here; adopt plain-V4-Flash-0731+b12x unless DSpark *measures* clean on 0731.
**Expect:** a recorded pass/fail per variant.

☐ **Step 6 — Record for the air-gap build.**
**Why:** the enclave reproduces this from mirrored sources only (air-gap runbook §7.3).
**Run:** record image name+digest, all pinned SHAs, the b12x version, and the compose file and env in the build log.
**Expect:** the build log entry is complete enough to rebuild without internet.

**TEST:** run the **same** KB or coding eval you used above, now against the big clustered model. **Expected outcome to record:** does the larger model answer *materially* better (correctness/grounding), and is that worth the operational cost? Speed note (corrected 2026-07-10): the widely-quoted "dual slower than single" figure (~47 vs ~57 t/s for gpt-oss-120b) is specific to **llama.cpp RPC** (no RDMA/tensor-parallel; upstream calls RPC proof-of-concept). With **vLLM tensor-parallel over the 200G link**, two Sparks are reported *faster* than one (up to ~1.8×). Either way, the point of the experiment is the **capacity/quality ceiling** — fitting a model class that cannot run on one box.

☐ **Step 7 — Teardown.**
**Run:**
```bash
# stop the Ray/vLLM cluster on both nodes, then on each node:
nvidia-smi
```
Return to single-node operation.
**Expect:** both nodes back to single-node operation, GPU memory released.

---

> **📋 STEP RECORD — §2.8.a** &nbsp;&nbsp; ☐ Done &nbsp; ☐ Deviation logged &nbsp; ☐ N/A (reason below)
> Machine: ☐ Spark-1 ☐ Spark-2 &nbsp;·&nbsp; Operator: `____________` &nbsp;·&nbsp; Date: `____________`
> Values recorded (versions / tags / measurements / anomalies): `________________________________________________`
>
> **Notes / observations / follow-ups** *(use as much of this space as needed)*:
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`

## 2.9 (Optional) Unsloth fine-tuning feasibility spike (NEW in v0.4) (v3.0 step format)

*Goal of this section:* answer "can we fine-tune on this hardware?" with a measured yes/no. **Fine-tuning** means further training an existing model on your own examples; **LoRA/QLoRA** is the cheap form that trains a small "adapter" instead of the whole model.

> [!NOTE]
> **One bounded experiment on public data** (Spark-2, ≤1–2 days): answer "can we fine-tune on this hardware?" with a measured yes/no in the benchmark memo, so Rung-3/2027 fine-tuning options (a bench-script DSL — "domain-specific language", a small purpose-built notation; house-style drafting; NCR — non-conformance report — classification) rest on evidence. Not a committed MVP capability.

☐ **Step 1 — Choose the container route — never pip.**
**Why:** the pip route is launch-era dependency hell (ARM64 + GB10 + CUDA 13).
**Before you run it:** use NVIDIA's official Unsloth playbook (based on `nvcr.io/nvidia/pytorch:25.11-py3`-class images; https://build.nvidia.com/spark/unsloth) or the weekly-rebuilt community image `thekozugroup/unsloth-dgxspark`. Required env: `TORCH_CUDA_ARCH_LIST=12.1`, `HF_HUB_DISABLE_XET=1` (xet — Hugging Face's newer download backend — is broken on ARM64).
**Run:** pull and start the chosen container per its playbook, with the required env set.
**Expect:** the training environment comes up inside the container.

☐ **Step 2 — Attention implementation: SDPA, not flash-attn.**
**Why:** **attention** is the core computation of a transformer model; SDPA and flash-attention are two interchangeable implementations of it. flash-attention drags in CUDA-12 libs; community reports SDPA faster on Blackwell anyway.
**Before you run it:** do not install flash-attention; set `attn_implementation="sdpa"`. If the HF path complains about the flash-attn3 kernel, apply the RobG transformers patches (gist linked in the Know-How compendium).

☐ **Step 3 — Apply the memory discipline to the training run.**
**Why:** training is exactly the heavy-job class §1.7 exists for.
**Before you run it:** training runs cgroup-capped per §1.7 (a **cgroup** is the Linux mechanism `systemd-run` uses to enforce a memory cap on a group of processes); drop caches before starting (NVIDIA's own playbook prescribes it).
**Run:**
```bash
sudo sh -c 'sync; echo 3 > /proc/sys/vm/drop_caches'   # then launch the capped training run per §1.7
```
**Expect:** the run starts under the §1.7 cap.

☐ **Step 4 — Run the spike within the realistic envelope.**
**Why:** the answer must be a measured envelope, not a single lucky run.
**Before you run it:** LoRA/QLoRA on a 4–14B dense model, small public dataset. Reference: 9B LoRA ≈ 7–17 h on a ~3K-pair dataset depending on context length. Note: MoE-LoRA adapters are currently ignored by vLLM at serving time — spike on a dense model.
**Run:** the LoRA/QLoRA fine-tune per the playbook, inside the container.
**Expect:** see the TEST below; record steps/s, peak memory and wall-clock in the benchmark memo.

**TEST:** the run completes without OOM/hang; loss decreases; the adapted model loads and answers differently from base on held-out prompts. Record steps/s, peak memory and wall-clock in the benchmark memo.

☐ **Step 5 — Teardown.**
**Run:**
```bash
docker stop <unsloth-container>
nvidia-smi
sudo sh -c 'sync; echo 3 > /proc/sys/vm/drop_caches'   # drop caches
```
**Expect:** GPU memory released, caches dropped.

---

> **📋 STEP RECORD — §2.9** &nbsp;&nbsp; ☐ Done &nbsp; ☐ Deviation logged &nbsp; ☐ N/A (reason below)
> Machine: ☐ Spark-1 ☐ Spark-2 &nbsp;·&nbsp; Operator: `____________` &nbsp;·&nbsp; Date: `____________`
> Values recorded (versions / tags / measurements / anomalies): `________________________________________________`
>
> **Notes / observations / follow-ups** *(use as much of this space as needed)*:
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`

## 2.10 (NEW in v0.13) KB↔agent bridge via MCP — integration spike (v3.0 step format)

*Goal of this section:* a bounded spike proving that coding agents can consult the knowledge base mid-task through a project-controlled MCP server.

> [!NOTE]
> **What & why (plain language).** MCP — the **Model Context Protocol** — is the open industry standard for connecting AI agents to tools and data: a small "server" program advertises tools (e.g. "search the knowledge base") and any MCP-capable agent can discover and call them. It is the natural way to let the **coding agents consult the knowledge base mid-task** (e.g. an OpenHands agent fixing C code queries the coding standard or an ICD — "interface control document" — and gets cited passages back). This section is a bounded WP1 spike (~1–2 days); whether the bridge ships in a use case is a WP3/G2 decision.

> [!IMPORTANT]
> **(v4.24) Precondition — before the p42-kb spike starts, target the MCP 2026-07-28 spec revision.** The fact: on 2026-07-28 the MCP specification was rewritten in a **breaking revision** — the protocol core is now stateless, the `Mcp-Session-Id` header is **removed** from the Streamable HTTP transport, routing is header-based, and a Tasks concept plus an Apps extension framework were added. Why it matters here: the p42-kb bridge sits between `fastmcp` on the server side and OpenHands' MCP client on the agent side — a bridge built against the old session-header behaviour **will break** as soon as either side moves to the new revision, and a spike validated on the old protocol would be validating something already obsolete. What to do: before writing any code, confirm **which fastmcp version implements the 2026-07-28 revision** and **whether OpenHands' MCP client has migrated**, then pin both sides to spec-consistent versions and record the pins in the STEP RECORD. Links: https://blog.modelcontextprotocol.io/posts/2026-07-28/ · https://modelcontextprotocol.io/specification/2026-07-28/changelog

☐ **Step 1 — DECISION: build the small custom "p42-kb" MCP server — not raw database exposure.**
**Why:** the tool interface must preserve the project's retrieval architecture and citations.
**Before you run it** — the settled design rule: the official Qdrant MCP server exists but exposes *raw vector search*, which would bypass the project's retrieval architecture (hybrid **BM25** (the classic keyword-match scoring formula) + dense (embedding/semantic) search + rerank, mandatory citations — per the KB trade-off study). The p42-kb server wraps **our own fast-path retrieval** and exposes 2–3 tools only: `kb_search(query) → cited passages`, `kb_fetch(doc, section)`, optionally `register_lookup(id)`. Implementation: official Python SDK ("software development kit" — the official programming library; `mcp` / `fastmcp` from the PyPI mirror), stdio or streamable-HTTP transport (how client and server exchange messages: over the server process's own input/output pipes, or over a local web connection), **local/enclave only**. This also gives the agentic-escalation path (trade-off study §6.2) its tool interface for free.
**Run:** implement the p42-kb server per the rule above (Python SDK, 2–3 tools, local transport).
**Expect:** the server starts and advertises exactly the p42 tools.

☐ **Step 2 — Wire the clients — support is uneven, plan for it.**
**Why:** not every harness can consume MCP.
**Before you run it:** **OpenHands = native MCP client** (configure the server under `mcpServers`, restrict with `filter_tools_regex` to the p42 tools only). **Cline = native MCP client** (v0.14 — this is what puts cited KB answers inside the engineers' IDE, the flagship consumer of `p42-kb`). **Open WebUI = native MCP support** (alternative to its built-in RAG — evaluate, don't assume better). **aider = NO native MCP client** (open upstream request) and **pi = no built-in MCP** (extension route) — for those, KB context arrives via repository conventions files / read-only doc extracts, or a bridge approved through the provenance process.
**Run:** configure OpenHands (mcpServers + filter_tools_regex, per the rule above), Cline and Open WebUI against the p42-kb server.
**Expect:** each native client lists the p42 tools and nothing else.

☐ **Step 3 — Enforce benchmark parity (feeds M42).**
**Why:** otherwise aider-vs-OpenHands comparisons measure tool access, not model quality.
**Before you run it:** KB tools must be **identically available or identically absent across harnesses** in any scored M42 run. Baseline M42 runs: KB tools OFF. A separate exploratory arm may measure the "KB-tools ON" delta on OpenHands only, reported as such.

☐ **Step 4 — Apply the security posture.**
**Why:** MCP tool descriptions are part of the prompt surface — a hostile description is an injection vector.
**Before you run it:** only project-written or provenance-approved MCP servers, mirrored and pinned like any package; **no third-party MCP servers from public registries**; the p42-kb server's descriptions are project-controlled text under version control.

☐ **Step 5 — Run the spike test.**
**Why:** the spike's exit evidence, for G2.
**Run:** from an OpenHands session, have the agent call kb_search against the WP1 sandbox KB; run the same query through Open WebUI; capture tool-call logs in the build log.
**Spike TEST:** from an OpenHands session, the agent calls `kb_search` against the WP1 sandbox KB and receives cited passages; the same query through Open WebUI returns consistent citations; tool-call logs captured in the build log. **Record for G2:** latency per call, token cost of tool descriptions, and whether the escalation path should route through the same server.

---

> **📋 STEP RECORD — §2.10** &nbsp;&nbsp; ☐ Done &nbsp; ☐ Deviation logged &nbsp; ☐ N/A (reason below)
> Machine: ☐ Spark-1 ☐ Spark-2 &nbsp;·&nbsp; Operator: `____________` &nbsp;·&nbsp; Date: `____________`
> Values recorded (versions / tags / measurements / anomalies): `________________________________________________`
>
> **Notes / observations / follow-ups** *(use as much of this space as needed)*:
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`

# Part C — Hardware benchmark protocol (WP1.3 — NEW in v0.2)

**Why:** the *hardware benchmark memo* is a WP1 deliverable, and *technical feasibility on DGX Spark* is the top-weighted G1 scoring criterion. The core team must be able to answer, for any proposed MVP, "will its model class run acceptably on this box?" with **measured** numbers, not community figures.

**When:** after Part A on both boxes, interleaved with Part B (benchmark each model as you first pull it).

**What to measure, per candidate model** (shopping list in §3.a; at minimum: gpt-oss-120b, Qwen3-Coder-30B, Qwen3-32B-NVFP4, BGE-M3):

| Field | How |
|---|---|
| Engine + exact image tag / build | from the build log |
| Quantisation | MXFP4 / NVFP4 / Q4 etc. |
| Load time + resident memory | `free -h` and a Spark-aware monitor (nv-monitor/spark-smi, per §1.7 — `nvidia-smi` reports N/A on unified memory) before/after load |
| Single-stream decode tok/s | `llama-bench` (llama.cpp/GGUF models) or `vllm bench serve` (vLLM's built-in benchmark CLI) |
| Prefill tok/s (long prompt) | same tools, long-input case — matters for RAG contexts |
| Max usable context before OOM | step `--max-model-len` up; record the flag set that worked |
| Concurrency sweep (v0.4) | c = 1 / 4 / 32 / 128 (c = number of simultaneous requests): aggregate tok/s + p95 latency (the time the slowest 5 % of requests exceed) per level. Community data shows near-linear scaling to c≈256 (gpt-oss-120b: ~33 → ~863 tok/s aggregate) — this measurement sizes our batch workloads (benchmark suite, agents, document sweeps) |
| Speculative decoding (v4.3 — MANDATORY for primary interactive models, per the §0.6 gated-default policy) | Pair the target with its designated pinned drafter (MTP/EAGLE3/DFlash per model family; chat-tuned head for chat-tuned target) and measure with/without. Gate: acceptance ≥ 60 % AND net decode speedup AND clean §3.a.1 smoke test → drafter joins the recorded baseline flag set; else fallback logged. Community-measured 2–2.7× single-stream. Record acceptance rate from engine metrics (don't fly blind); >3 speculative tokens degrades |
| Quality spot-check | 3–5 fixed prompts per track (KB answer, code diff, doc draft) — keep the prompts fixed across models so results compare |

Method notes: use `llama-bench` for llama.cpp-served GGUF models and `vllm bench serve` for vLLM-served models (vLLM bench docs: https://docs.vllm.ai/en/latest/cli/bench/serve/). Run each measurement twice; record the flag set verbatim — a tok/s number without its flags is not reproducible.

**C.2 The community-comparable baseline (llama-benchy) — mandatory, once per serving config (NEW in v0.10).** `llama-benchy` (`eugr/llama-benchy`, on PyPI) is the de-facto forum-standard benchmark: it drives any OpenAI-compatible endpoint (vLLM, llama.cpp, SGLang — another serving engine) with the same pp/tg-at-depth sweep (pp = prompt processing/prefill, tg = text generation/decode, "depth" = how much context is already filled) the community posts, so our numbers become directly comparable with every forum thread — a free misconfiguration detector, and later the enclave acceptance reference. For each serving configuration that survives Part B:

```bash
uv tool install llama-benchy          # via the PyPI mirror in the enclave
llama-benchy --base-url http://localhost:8000/v1 --model ⟨served model id⟩ \
  --depth 0 4096 8192 16384 32768 --latency-mode generation --runs 3 \
  --output json | tee ~/benchy-⟨model⟩-$(hostname)-$(date +%F).json
```

*Flag rationale:* `--base-url` / `--model` say which endpoint and served model to drive; `--depth 0 4096 8192 16384 32768` measures at each of those already-filled context depths; `--latency-mode generation` times token generation (the tg figure); `--runs 3` repeats each measurement three times for stable numbers; `--output json` emits machine-readable results, which `tee` both displays and files.

Keep the flag set EXACTLY as above (it mirrors the forum convention — changing depths breaks comparability). File the JSON in the build log: **§10.3 of the air-gap runbook re-runs this on the enclave build and compares against these files.** Sanity anchors from the forum: gpt-oss-120b TP=2 ≈ 81.5 ± 0.9 tok/s (patched builds); ~59.6 tok/s at 100 k depth.

**Canonical sanity-check figures (v0.4 — ggerganov's reference thread, https://github.com/ggml-org/llama.cpp/discussions/16578):** gpt-oss-120b MXFP4 ≈ 1,700–1,800 tok/s pp2048 / 35–46 tok/s tg (55–59 tuned/spec-decode); gpt-oss-20b ≈ 2,000+ pp / ~60 tg; Qwen3-Coder-30B-A3B Q8_0 ≈ 1,650 pp / ~44 tg; dense 70B FP8 ≈ 2.7 tok/s (why dense-70B is batch-only). **If a measurement lands far below these, the config is wrong** (usual suspects: silent CPU fallback, non-121a build, mmap on, wrong container) — fix before recording. Expect ~30% decode loss at 32K context depth; prefer native-context models over YaRN extension (YaRN = a method that stretches a model's context window beyond its training length, at some quality cost).

**Output:** one table per machine in the benchmark memo, plus a one-paragraph "what fits" summary the G1 scoring can quote (e.g. "120B-MoE class: fine interactively; 70B dense: batch only; 400B class: clustered experiment only").

---

> **📋 STEP RECORD — Part C** &nbsp;&nbsp; ☐ Done &nbsp; ☐ Deviation logged &nbsp; ☐ N/A (reason below)
> Machine: ☐ Spark-1 ☐ Spark-2 &nbsp;·&nbsp; Operator: `____________` &nbsp;·&nbsp; Date: `____________`
> Values recorded (versions / tags / measurements / anomalies): `________________________________________________`
>
> **Notes / observations / follow-ups** *(use as much of this space as needed)*:
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`

# Part D — Familiarisation sessions & discipline sandboxes (WP1.4 — NEW in v0.2)

**Why:** WP1's fourth deliverable. Discipline representatives write better MVP ladders after hands-on time — the sessions calibrate ambition against what the machines actually do, *before* the Fri 4 Sep submission deadline.

**When:** target the **week of 1 Sep** (reps returning from leave; submission that Friday). Two sessions, ~2 h each, 3–4 reps per session so everyone drives.

**Sandbox setup (before the sessions):**
1. In Open WebUI, create **one account per discipline representative** (plus deputies). Keep chat history ON.
2. Create a **shared demo knowledge base** from the public stand-in PDFs of §2.1.4, plus **one empty knowledge collection per discipline** they can upload public/stand-in material into during and after the session.
3. Have the coding endpoint live (§2.2) with aider on a demo laptop, and one §2.7 notebook with the synthetic campaign data.
4. Print or share the one-page "golden rules for users": public/stand-in data only in this phase; quality-not-speed; every answer needs a citation; log stays on.

**Session plan:**

| Block | Content | Ties to |
|---|---|---|
| 1. What this is (15 min) | The two Sparks, what "local AI" means, dirty-phase rules, why slow ≠ bad | Golden Rules |
| 2. KB drive-time (45 min) | Reps ask real-shaped questions against the demo KB; see citations; see a "not found"; see a wrong answer and how citation checking catches it | UC-OPS-2 pattern |
| 3. Code & drafting demo (30 min) | aider on the sample repo (navigation Q&A + a unit-test diff); one grounded-drafting example from a requirements table | UC-GNC-2 / UC-FV-2 patterns |
| 4. Notebook triage demo (15 min) | Synthetic campaign → clusters → LLM summary, round-trip checked | UC-FV-1 pattern |
| 5. Your ladder (15 min) | Walk the template + worked examples; what makes a rung feasible on this hardware; Q&A on their draft ideas | WP2 submission |

**Expectation-setting is a deliverable of the session:** show one thing the model does badly (an uncited confident answer, or a slow dense model) on purpose. Reps who have seen the failure modes write benchmarkable acceptance criteria; reps who have only seen demos write science fiction.

**Record:** attendance per discipline (WP1 exit evidence) and every question the reps asked that the stack couldn't handle — those are free inputs to the w/c 7 Sep workshop.

---

> **📋 STEP RECORD — Part D** &nbsp;&nbsp; ☐ Done &nbsp; ☐ Deviation logged &nbsp; ☐ N/A (reason below)
> Machine: ☐ Spark-1 ☐ Spark-2 &nbsp;·&nbsp; Operator: `____________` &nbsp;·&nbsp; Date: `____________`
> Values recorded (versions / tags / measurements / anomalies): `________________________________________________`
>
> **Notes / observations / follow-ups** *(use as much of this space as needed)*:
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`

# 3. Appendix

## 3.a Model selection & download matrix (v1.0)

> [!NOTE]
> **Two documents, two jobs.** The team-facing description of each model — what it is good at, its weaknesses, which role it plays and why — lives in **`Project42_LLM_Model_Catalogue.md` (v0.8)**; that catalogue is the authority on *which model plays which role*. This matrix is the authority on *exact repositories, pins, and validation gates* for WP1 downloads. One deliberate difference to be aware of: the catalogue's headline single-Spark coder, **Qwen3-Coder-Next**, sits here as a Part-C-first candidate — it enters the coding seat only after its §3.a.1 tool-calling gate passes on the pinned build; until then `Qwen3-Coder-30B-A3B` holds that seat.

**Selection rule (applies §0.6 criteria to models):** a model enters the baseline only if it is Spark-validated by one of: **[NV]** NVIDIA's verified vLLM matrix or an official DGX Spark playbook (optimised *for* this hardware — the NVFP4/FP8 builds under the `nvidia/` HF org); **[C]** measured on GB10 in the canonical community benchmark thread (llama.cpp discussion #16578) or an equivalent sourced measurement; or **[P]** pure-PyTorch/architecture-agnostic and validated by us in WP1. Anything else is a **candidate**: it must pass Part C (benchmark + quality spot-check) before any MVP depends on it. Download **only the exact repos below**, pin the revision (the exact version snapshot of the model repository), record SHA-256 in the build log. Quant format follows the engine: `nvidia/` NVFP4/FP8 safetensors for vLLM; GGUF for llama.cpp.

**vLLM path (NGC container) — NVFP4/FP8 safetensors:**

| Role | Exact repo (huggingface.co/…) | Validated | Prio |
|---|---|---|---|
| Smoke test / small chat | `nvidia/Llama-3.1-8B-Instruct-FP8` | [NV] verified matrix | P1 |
| Mid reasoning | `nvidia/Qwen3-32B-NVFP4` (dense — ~10 tok/s single-stream, batch-leaning) | [NV] verified matrix | P1 |
| Figure/diagram captioning (KB ingestion) | `nvidia/Qwen2.5-VL-7B-Instruct-NVFP4` | [NV] verified matrix | P1 |
| Alt 120B workhorse (concurrent serving) | `nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-NVFP4` (~23 tok/s single; strong batched) | [NV] matrix + community-measured | P2 |
| Newcomer-friendly fast MoE | Nemotron-3-Nano-30B-A3B NVFP4 — official playbook model; confirm exact repo/tag on box | [NV] playbook | P2 |
| Perf-champion mid MoE + spec decode | Qwen3.6-35B-A3B NVFP4 + DFlash drafter (~84–125 tok/s measured) — confirm exact repos on box | [C] community | P2 — Part C first |
| Dense quality option | `nvidia/Llama-3.3-70B-Instruct-NVFP4` | [NV] verified matrix | P3 — batch only (~2.7 tok/s single) |

**llama.cpp path — GGUF (MXFP4/Q8_0 class; KV cache ≥ q8_0 per §2.1):**

| Role | Exact repo | Validated | Prio |
|---|---|---|---|
| Workhorse answer LLM (single-user) | `ggml-org/gpt-oss-120b-GGUF` (MXFP4 — the exact repo behind the canonical GB10 numbers, 35–46 tok/s tg) | [C] canonical thread | P1 |
| Small chat / quick tests | `ggml-org/gpt-oss-20b-GGUF` (~60 tok/s tg) | [C] canonical thread | P1 |
| Primary coding-agent model | `unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF` (**Q8_0** per community numbers, ~44 tok/s; Q4_K_M fallback; unsloth repo carries chat-template fixes) | [C] canonical thread | P1 |
| Bigger coding option | `Qwen/Qwen3-Coder-Next` (80B-A3B, 256K ctx) — GGUF variant TBC on box | candidate — Part C first | P2 |
| Frontier-class on ONE Spark (candidate) | `unsloth/DeepSeek-V4-Flash-0731` GGUF (UD-IQ2_M ~85 GiB / UD-IQ3_XXS ~97 GiB) | candidate — Part C first (2–3-bit quant vs quality-first policy; ~6.5-min load). **(v4.24) A published MAINLINE llama.cpp config now exists — adopt it VERBATIM as the Part-C starting configuration (still §3.a.1-gated):** forum, 2026-08-04, correctness-checked — build 10235, Unsloth UD-IQ2_M, 524288 total ctx ÷ 4 slots = 131K/slot, `--flash-attn on --no-mmap` (`--flash-attn on` = the long form of `-fa on`), **KV cache at 16-bit — `q8_0` KV garbles on this model (§2.1.2.1)**; measured 19.7 tok/s single-stream, ~52 tok/s at 4-concurrent, pp2048 ≈ 459; 96 % on a 5-category eval. **Measured limit:** 4 concurrent requests × 16K prior context each collapsed to **6.3 tok/s combined** — single-box V4-Flash is NOT a viable multi-agent serving seat; long single-agent context is fine. Source: https://forums.developer.nvidia.com/t/1x-dgx-spark-deepseek-v4-flash-0731-on-llama-cpp-131k-ctx-slot-19-7-tok-s-single-stream-52-tok-s-4-concurrent/379129 | P2 |

**Two-Spark cluster path (256 GB pair — §2.8 experiment only, all candidates, Part C + §2.8 gates first):**

| Role | Exact repo / class | Validated | Notes |
|---|---|---|---|
| Flagship open coding model (the ceiling test for new-code quality) | `Qwen/Qwen3-Coder-480B-A35B-Instruct` — quantized GGUF ~168 GB (Q4-class; pick quant to leave KV room) via llama.cpp RPC | [C] community: runs at ~10 tok/s on 2 Sparks | Batch/agentic only at this speed; the question is code *quality*, not latency — run the coding-benchmark ceiling config on it |
| Fast big MoE with long context | DeepSeek-V4-Flash-**0731** (2026-07-31 checkpoint — now the target; 2-Spark "DSpark" spec-decode variant; ~60–67 tok/s, up to 1M ctx) — confirm exact repo/tag on box | [C] community-measured on 2× GB10 (speed pre-0731; DSpark quality flag re-opened — re-measure on 0731, §2.8.a step 5) | Strongest usable-speed cluster option; NVFP4 KV pooling |
| Alternative big MoEs (vLLM/SGLang TP over RDMA) | GLM-4.7(-Flash), MiniMax-M2.x-AWQ, Kimi K2.5-class — per the eugr-validated set; AWQ currently beats NVFP4 in vLLM on GB10 | [C] community (eugr/spark-vllm-docker) | Working set on 2–4 Sparks; ~170 GB practical two-node ceiling |
| NOT worth it | GLM-5.2 full FP8 (~750 GB — Tier-B territory); 1-bit extreme quants (community verdict: research-only, unusable TTFT at long context) | [C] community | Record as exclusions, don't burn time |

**Retrieval stack — pure PyTorch, architecture-agnostic:**

| Role | Exact repo | Validated | Prio |
|---|---|---|---|
| Dense/hybrid embeddings | `BAAI/bge-m3` | [P] WP1 | P1 |
| Cross-encoder reranker | `BAAI/bge-reranker-v2-m3` | [P] WP1 | P1 |
| Visual page retrieval (multivectors) | `vidore/colqwen2.5-v0.2` (v4.43 — replaces Metric-AI 7b: its base repo went gated on HF, unloadable) | [P] WP1 (throughput check on box) | P1 |
| FIM/autocomplete (deferred track) | `Qwen/Qwen2.5-Coder-7B-Instruct` | candidate | P3 |

**Speculative-decode drafters:** per model family (MTP / EAGLE3 / DFlash — the main drafter techniques; see Annex B). The drafter must match the instruction-tuned target — base-variant drafters measurably degrade throughput. Exact drafter repos are selected and recorded during the Part C speculative-decoding measurement; do not guess them in advance.

> [!IMPORTANT]
> **Provenance rule:** prefer `nvidia/` repos on the vLLM path (hardware-vendor-optimised for this box) and `ggml-org/` on the llama.cpp path (engine-author-published; what the canonical benchmarks ran). `unsloth/` GGUFs are the accepted community standard where no ggml-org repo exists. **Avoid unpinned third-party quants** — an arbitrary community quant is an unaudited artefact and does not meet criterion 1.

## 3.a.1 Chat-template & tool-calling known issues — per-model fixes (NEW in v0.11)

> [!CAUTION]
> **This is a real, systemic problem, not an edge case.** The Qwen family's HF-shipped Jinja templates use Python-isms (`[::-1]` step-slicing, `startswith`, `items` on non-mappings) that C++ Jinja engines only partially support, and several tool-call parsers have shipped broken. The nastiest property: **llama.cpp falls back to a generic chatml template SILENTLY when it cannot parse the embedded template** — the model still chats, but tool calling and thinking-mode handling are quietly broken. Every agentic use case (aider, OpenHands) sits on top of this layer. Validated 2026-07-22 from llama.cpp/vLLM issue trackers, Unsloth docs and the DGX Spark forum.

*Plain language for this section:* a **chat template** is the small script shipped inside each model that converts the structured conversation (system/user/assistant/tool messages) into the exact text the model was trained to expect — get it wrong and quality quietly collapses; **minja** is llama.cpp's small C++ engine for running these Jinja-language scripts; **thinking mode** means the model writes private reasoning before its visible answer; tool calling is explained at §2.1.2.1 Step 4.

**Per-model status and fixes:**

| Model + engine | Failure mode | Validated fix |
|---|---|---|
| **Qwen3 / Qwen3-Coder GGUF, llama.cpp `--jinja`** | Embedded template unparseable by minja (`[::-1]`, `startswith`) → **silent chatml fallback**; tool calling broken; affected ALL GGUF uploads, not just Unsloth's (llama.cpp #13178, #14915) | Use Unsloth's **re-uploaded** GGUFs (30B-A3B quants embed the fix); for 480B-A35B pass the corrected template explicitly: `--chat-template-file` (= serve with the named template file instead of the model's embedded one; Unsloth docs). **CHECK the server log** for `failed to parse chat template (defaulting to chatml)` — that line = broken serving |
| **Qwen3.5/3.6, llama.cpp** | (a) stock template **crashes on `developer`-role messages** — which agent harnesses emit; (b) with thinking ON, tool calls emitted as raw XML inside the think block, generation halts (llama.cpp #20837-class, open); (c) PEG parser fails when the model prints text before `<tool_call>` (#20260, open); (d) deep template nesting costs ~80 % throughput + breaks prefix caching [community] | Serve with `--jinja --chat-template-file ⟨fixed template⟩` — community-maintained fixed templates: `froggeric/Qwen-Fixed-Chat-Templates` (HF, v21.x: minijinja-safe, thinking-boundary fixes, flattened AST → KV-cache-friendly) or the sudoingX developer-role gist. Workaround for (b): `enable_thinking:false` for tool-calling sessions. VALIDATE on box — these are community artefacts |
| **Qwen3.5, vLLM** | Tool calls interleaved with thinking tokens → silent parser failures; the officially recommended `--tool-call-parser qwen3_coder` **breaks on `<`,`>`,`&` and nested/streaming JSON**; long sessions drift XML↔JSON | `--tool-call-parser qwen3_xml` (`--tool-call-parser` selects which built-in vLLM parser extracts tool calls from the model's output) + community-enhanced template via `--chat-template` (allanchan339 `qwen3.5-enhanced.jinja`) — community-validated over a 138 k-token continuous agent session. **Qwen3.6 reportedly ships a fixed template out-of-box** [single source — verify]: prefer 3.6 over 3.5 as baseline |
| **Qwen3-Coder-Next GGUF, llama.cpp** | Malformed JSON tool parameters (agents report `Invalid input for tool write: JSON parsing failed`); PR #19239 only partial | pwilkin's **autoparser** branch resolved it per multiple users — as of the sweep NOT yet confirmed merged to mainline: **WP1 must verify tool calling on the pinned build before this model enters the coding seat** |
| **llama-server, ALL models (OpenAI-compat)** | Regression from PR #18675: `tool_calls.arguments` returned as a JSON **object** instead of the OpenAI-spec **string** → crashes the OpenAI SDK and harnesses that `json.loads` it; `--jinja`/`--chat-template` do NOT work around it | Pin a llama.cpp build verified against the §3.a.1 smoke test below; if the pinned build is affected, pick pre-#18675 or a build with the fix |
| **DeepSeek-V4/V4-Flash, vLLM** | DSML tool-parser edge cases: spurious `arguments`/`input` wrapper mishandled; schema params legitimately named `arguments` collide; **streaming holds back plaintext forever when no tool call follows** (vLLM #41240) | Fixed upstream — **require a vLLM build containing PR #41241 (+#41198)** for the cluster route; always pass `--tokenizer deepseek-ai/DeepSeek-V4-Flash` (`--tokenizer` = load the tokeniser from this exact repo; a silent GPT-2 fallback happens otherwise) |

**Mandatory template smoke test (add to every serving-config sign-off, and to §3.d):** before recording a model+engine config in the build log, run a scripted 3-turn agentic exchange that (1) triggers a tool call and confirms the harness parses it (`arguments` arrives as a JSON *string*); (2) includes a `developer`-role message; (3) runs once with thinking on and off, confirming no reasoning tags leak into content and no halt after the tool call; (4) greps the server log for the silent-chatml-fallback line. Record the exact template file (and its SHA-256) next to the model revision — **fixed template files are pinned artefacts like model weights** and go to the air-gap build log.

> **📋 STEP RECORD — §3.a.1** &nbsp;&nbsp; ☐ Done &nbsp; ☐ Deviation logged &nbsp; ☐ N/A (reason below)
> Machine: ☐ Spark-1 ☐ Spark-2 &nbsp;·&nbsp; Operator: `____________` &nbsp;·&nbsp; Date: `____________`
> Values recorded (versions / tags / measurements / anomalies): `________________________________________________`
>
> **Notes / observations / follow-ups** *(use as much of this space as needed)*:
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`

## 3.b Ports & endpoints (default)

| Port | Machine | Service | Key endpoints |
|---|---|---|---|
| 8000 | Spark-1 | vLLM **or** llama-server (answer / coding LLM) — a single slot: one engine binds it at a time, run the track teardown before switching | `/v1/chat/completions`, `/v1/completions`, `/v1/models` |
| 8001 | Spark-1 | Always-on llama-server systemd service, if configured (§2.1.2.1 TIP) | same as 8000 |
| 8002 | Spark-1 (UPDATE mode only) | vLLM (Qwen2.5-VL, ingestion — §2.1.3) | `/v1/chat/completions` (vision) |
| 8080 | Spark-1 | Embeddings (BGE-M3) or Tabby | `/embed` or `/v1/embeddings` |
| 8081 | Spark-1 | Reranker (bge-reranker-v2-m3) | `/rerank` |
| 6333 / 6334 | Spark-1 | Qdrant | REST + dashboard / gRPC |
| 3000 | Spark-1 | Open WebUI | web UI |
| 8888 | Spark-2 | JupyterLab (§2.7) | notebooks |

Reach services across the LAN as `http://<spark-ip>:<port>`. From inside a container calling a host service, use `host.docker.internal`.

## 3.c Troubleshooting

- **`exec format error` (the aarch64 image trap):** the image is amd64-only. Run `docker run --rm <img> uname -m` — if it is not `aarch64`, use the NGC/NVIDIA arm64 image, a confirmed arm64 community build, or build from source. This is the single most common failure on the Spark.
- **OOM despite free RAM (128 GB unified):** memory is shared CPU+GPU and Linux page cache can conflict with large GPU allocations. Flush caches: `sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches'`. Also reduce `--gpu-memory-utilization`, `--max-model-len`, or `--max-num-seqs` in vLLM.
- **"Model is too slow":** expected — the Spark validates **quality, not speed** (273 GB/s bandwidth). Prefer **MoE + NVFP4** for interactive use (a 30B-class MoE runs several times faster than a 32B dense model — ~30 t/s vs ~10 t/s plain serving, more with speculative decoding). Do not treat slow tokens as a failure.
- **Tool calling broken / agent loops fail (v0.11):** check the server log for `failed to parse chat template (defaulting to chatml)` — the silent-fallback signature — then work through §3.a.1 (fixed template file, right parser flag, arguments-as-string check).
- **vLLM returns HTTP 500 on `/v1/models` after a system update (v0.11):** known failure signature `AttributeError: '_IncludedRouter' object has no attribute 'path'` — an unpinned FastAPI release (≥0.137) pulled into the container. Fix: `pip install 'fastapi<0.137'` inside the image or roll back to the previous pinned container tag. General lesson: after ANY update, re-run the §1.5 smoke test before deeper debugging.
- **Garbled/corrupted generation on cluster TP=2 (v0.11):** seen on unvetted community dev-build images (coherent server, gibberish output). Not diagnosed upstream — treat as a build-provenance problem: fall back to the recorded known-good image digest; never debug quality on an unpinned image.
- **Sudden hard power-off under load / idle temp ≥45 °C (v0.11):** forum-documented thermal-management failures (dry thermal paste; EC firmware fan-curve regression). On GB10 the **CPU sensor reads hotter than the GPU** (~10–15 °C) — monitor both. Mitigations while a unit is suspect: `nvidia-smi -lgc` clock cap, improve airflow, EC firmware check per §1.2; a unit that hard-powers-off is a warranty conversation, not a software bug.
- **GPU stuck at low power under load (v1.0 — community power-state taxonomy):** run a GPU workload, then `nvidia-smi --query-gpu=power.draw,utilization.gpu,clocks.sm --format=csv,noheader`. Healthy ≈ tens of watts at high utilisation. Three distinct sick states: **~5 W draw + 0 % utilisation with a clean dmesg** = stale driver stack (fix: our pinned 580.x + CUDA 13 baseline — should not occur on DGX OS, but check after any restore); **stuck ~30 W and never escalating** = USB-C power-delivery negotiation failure in the PD controller — community consensus: not fixable in software, **RMA the unit**; **power plateauing ~100 W** (vs 240 W rating) = thermal protection — cooling/airflow/ambient problem, see the thermal entries above.
- **Model download hangs silently for many minutes, then `CAS Client Error ... error decoding response body` (v4.12 — hit live in WP1):** the Hugging Face **Xet** transfer backend is broken on ARM64 (already known from §2.9). Signature: container parks after the attention-backend log line with no cache growth, then the xet error. Fix: set `HF_HUB_DISABLE_XET=1` in EVERY environment that downloads from Hugging Face — host shell AND containers (`-e HF_HUB_DISABLE_XET=1`; now baked into every launch block in this runbook). Prefer pre-downloading weights on the host with `hf download` so containers only ever load from the mounted cache.
- **Where to get help:** NVIDIA playbooks hub https://build.nvidia.com/spark (⇄ https://github.com/NVIDIA/dgx-spark-playbooks) and the DGX Spark User Guide https://docs.nvidia.com/dgx/dgx-spark/index.html.

## 3.d "Verify-at-install" checklist (consolidated)

Tick each on the actual box before hard-coding it into the production recipe:

- [ ] **Preinstalled versions** — record `nvidia-smi`, `nvcc --version`, `docker version`, `nvidia-ctk --version`.
- [ ] **Every non-NVIDIA image is arm64** — `docker run --rm <img> uname -m` → `aarch64`.
- [ ] **vLLM aarch64 image tag** — confirm the exact NVIDIA/NGC tag from the playbook.
- [ ] **TEI GPU on aarch64: NOT prebuilt (confirmed 2026-07-10)** — use vLLM-embeddings; reranker via `ddosify/...:blackwell-1.8.3-baai-bge-reranker-v2-m3`, `hwdsl2` Dockerfile.arm64, self-built TEI Dockerfile-cuda, or sentence-transformers.
- [ ] **Qdrant startup on aarch64** — no jemalloc/page-size error; dashboard loads.
- [ ] **Onyx on arm64 (UNVERIFIED)** — `docker compose -f docker-compose.yml -f docker-compose.dev.yml up` succeeds; else stay on Open WebUI. RBAC = Enterprise edition.
- [ ] **Tabby: NO official arm64 GPU image (confirmed 2026-07-10)** — build from source or use Tabby's HTTP model config against a Spark endpoint. *(Optional track — only if a ladder needs FIM.)*
- [ ] **OpenHands on aarch64** — agent-server images ship linux/arm64; verify the APP image is arm64 on box (`uname -m` check on both). *(Optional track.)*
- [ ] **vLLM embeddings flag** — current images: `--runner pooling`; older pinned images may need the deprecated `--task embed`. Record which one the chosen tag accepts.
- [ ] **Qwen3-VL on GB10 (VERIFY)** — needs vLLM ≥0.11.0; Qwen2.5-VL-7B-NVFP4 is the confirmed choice.
- [ ] **ColQwen2.5 throughput on GB10** — high confidence but re-check on box.
- [ ] **DGX Dashboard JupyterLab** — check the managed JupyterLab before self-installing (§2.7).
- [ ] **Clustering** — NCCL-from-source + exact CX-7 interface names from `ip link`.
- [ ] **tok/s figures** — community single-stream numbers, not SLAs; re-benchmark target models per **Part C** (`llama-bench` / vLLM benchmark).
- [ ] **Chat-template smoke test (v0.11)** — the §3.a.1 3-turn agentic exchange passes for every serving config headed for an agent harness; template file + SHA-256 recorded beside the model revision.
- [ ] **Thermal baseline (v0.11)** — idle temperature ~30–35 °C recorded per unit (CPU and GPU sensors); EC/UEFI firmware versions recorded (`fwupdmgr get-devices`).

---

# 4. WP1 exit checklist (NEW in v0.2)

WP1 closes (11 Sep, ahead of G1 w/c 14 Sep) when all of the following hold. This checklist, plus the build logs, IS the infrastructure readiness note.

- [ ] Part A complete on both machines; build log per machine (= the completed STEP RECORDs) records every version and deviation.
- [ ] (v1.0) §1.0 recovery dongles: 2 sticks built, 1 test reflash completed, versions + SHA-256 recorded; **P42 Reset Kit trial run per `Project42_GoldenImage_USB_Howto.md` v0.3 §7** (Route A replay trial mandatory; Route B live-boot VERIFY attempted and outcome recorded).
- [ ] (v0.4) SSH access established before any display experiments.
- [ ] (v0.4) Driver held at 580.x (`apt-mark showhold`); §1.7 memory-discipline settings applied (sshd OOM protection, swap policy, drop-caches habit); Spark-aware monitoring (nv-monitor/spark-smi) running.
- [ ] (v0.4) Silent-CPU-fallback check performed once per serving engine and recorded.
- [ ] Track 2.1 (KB) end-to-end TEST passed, including the unanswerable-question check.
- [ ] Track 2.4 (codebase navigation) TEST passed on an embedded-flavoured public repo, including the change-impact rehearsal.
- [ ] Track 2.5 (grounded drafting) TEST passed, including the seeded-defect QA check.
- [ ] Track 2.7 (data & log analysis) TEST passed on synthetic data, including the round-trip figure check.
- [ ] Tracks 2.2 / 2.3 / 2.6: done, or explicitly deferred with the reason logged (no ladder needs them yet).
- [ ] Part C benchmark memo drafted: measured table per machine + "what fits" summary, ready for G1 scoring.
- [ ] (v4.3) Speculative-decoding gate run for EVERY primary interactive model in §3.a: drafter pass/fail recorded with acceptance rate; passing drafters present in the recorded baseline flag sets, failures logged as deviations.
- [ ] Part D: both familiarisation sessions held; attendance recorded; discipline sandboxes live; unanswered-question list handed to the w/c 7 Sep workshop.
- [ ] Baseline stack description written: the exact recipe (images, tags, flags, model handles) per track — reproducible without internet-era guesswork.
- [ ] §3.d verify checklist fully ticked or exceptions logged.
- [ ] Serving/usage logging confirmed ON and its location documented (WP5 will depend on it).

---

> **📋 STEP RECORD — §4** &nbsp;&nbsp; ☐ Done &nbsp; ☐ Deviation logged &nbsp; ☐ N/A (reason below)
> Machine: ☐ Spark-1 ☐ Spark-2 &nbsp;·&nbsp; Operator: `____________` &nbsp;·&nbsp; Date: `____________`
> Values recorded (versions / tags / measurements / anomalies): `________________________________________________`
>
> **Notes / observations / follow-ups** *(use as much of this space as needed)*:
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`
> `____________________________________________________________________________________________________`


---

## Annex A — Linux command primer: what every command in this runbook does (NEW in v1.5)

*Purpose:* learn the shell while executing the runbook. Every command and shell construct used anywhere in this document is listed here with a one-line plain-language explanation. Read A.1 first — it decodes the *grammar* of a command line; the rest are reference tables to look up as you meet each command.

### A.1 How to read a command line

| Construct | What it means |
|---|---|
| `sudo <command>` | "super-user do" — run the command as the administrator (root). Needed for anything that changes the system |
| `# text` | a comment — the shell ignores everything after `#`; used in this runbook to annotate commands |
| `command --flag -f` | options modifying behaviour; `--long-name` and single-letter `-f` forms. `command --help` usually lists them |
| `a \| b` | the **pipe**: feed command *a*'s output into command *b* as its input. Chains small tools into one operation |
| `> file` / `>> file` | redirect output into a file — `>` overwrites, `>>` appends |
| `2>&1` / `2>/dev/null` | error messages are a separate stream (stream 2): `2>&1` merges them into normal output (so they get captured too); `2>/dev/null` throws them away |
| `a && b` | run *b* only if *a* succeeded — a safety chain (`build && install`) |
| `a ; b` | run *b* after *a* regardless of success |
| `$NAME` / `${NAME}` | insert a **variable**'s value; `export NAME=value` sets one that later commands inherit |
| `$(command)` | insert a command's *output* into the line — e.g. `boxstate-$(hostname).txt` puts the machine name in the filename |
| `<(command)` | treat a command's output as if it were a file (used in the §1.2 temperature one-liner to `paste` two outputs side-by-side) |
| `'single'` vs `"double"` quotes | both group words; single quotes keep everything literal, double quotes still expand `$variables` |
| `*` | wildcard — `*.txt` means every file ending `.txt` |
| `~` · `.` · `..` · `./prog` | your home folder · current folder · parent folder · run program `prog` from the current folder |
| `\` at end of line | the command continues on the next line (long commands split for readability) |
| `for X in …; do …; done` | a loop: run the body once per item, with `$X` holding the current item (the §1.1 capture command is one big loop) |
| `bash -c '…'` | run the quoted text as one shell script — how the runbook's one-liners package several steps into one paste |

### A.2 Working with files and text

| Command | What it does |
|---|---|
| `ls` | list a folder's contents (`ls -la`: with details and hidden files) |
| `cd` / `pwd` | change into a folder / print which folder you are in |
| `mkdir -p` | create a folder (`-p`: including any missing parents, no error if it exists) |
| `cp` / `scp` | copy files locally / copy files **between machines** over SSH |
| `cat` | print a file's whole contents (con*cat*enate) |
| `head -n 50` | print only the first 50 lines of a file or stream |
| `grep pattern` | keep only lines matching a pattern — the everyday filter (`dpkg -l \| grep nvidia`) |
| `tee file` | split a stream: show it on screen **and** save it to a file at the same time (the §1.1 capture) |
| `echo` / `printf` | print text (printf: with precise formatting) — also used with `>` to write small files |
| `paste` | glue two inputs together line-by-line into columns (§1.2 temperature check) |
| `awk '…'` | a mini-language for processing text tables — here just reformatting numbers (millidegrees → °C) |
| `dirname` | strip the filename off a path, leaving the folder part |
| `chown user file` | change a file's owner (used after `sudo` created a file so *you* own it, not root) |
| `source file` | run a file's commands **in the current shell** (activating a Python venv changes *this* shell's environment) |
| `wget URL` / `curl URL` | download from the web — wget saves to a file by default; curl prints by default (`-o` to save) and also *sends* requests, which is how the runbook tests model endpoints |

### A.3 Asking the system about itself

| Command | What it does |
|---|---|
| `uname -m` / `uname -a` | machine architecture (**must** say `aarch64` here) / kernel + everything |
| `hostname` / `date -u` | machine name / current time (UTC) |
| `lscpu` / `nproc` | CPU details / just the core count (expect 20) |
| `free -h` | memory usage, human-readable (expect ~128 GB unified) |
| `df -h` / `lsblk` | disk space per filesystem / the disks-and-partitions tree |
| `lsb_release -a` | OS release name and version |
| `cat /etc/os-release` | same idea — `/etc` is where system configuration lives as plain text files |
| `cat /proc/meminfo`, `/sys/class/thermal/…` | `/proc` and `/sys` are **virtual** files: reading them queries the live kernel (memory stats, temperatures). Writing to some of them changes kernel behaviour — that is what `echo 3 > /proc/sys/vm/drop_caches` (§1.7) does |
| `dmidecode -s …` | read the manufacturer/product/serial burned into the hardware (the §1.0/§1.1 SKU check) |
| `ip -4 addr show` / `ip link` | network addresses / network interfaces |
| `ping` | test whether another machine answers on the network (§2.8 uses it to validate jumbo frames) |

### A.4 Installing and managing software

| Command | What it does |
|---|---|
| `apt` / `apt-get` | Ubuntu's package manager. `update` = refresh the catalogue; `install X` = install; `dist-upgrade` = upgrade everything, allowing new dependencies; `full-upgrade` similar (see §1.2 cautions before upgrading!) |
| `apt-mark hold` / `apt-mark showhold` | freeze a package at its current version / list frozen packages — how the 580.x driver pin is enforced |
| `apt list --installed 'pattern'` | list installed packages matching a pattern (the §1.2 pre-reboot kernel-module check) |
| `dpkg -l` | lower-level list of every installed package (`dpkg` is the tool `apt` builds on) |
| `gpg --dearmor` | convert a repository's signing key into binary form for apt — part of *verifying* downloads, never to be skipped |
| `snap install` | Ubuntu's other package system (containerised apps) — fallback route for Chromium in §1.2.a |
| `fwupdmgr` | firmware updater: `get-devices` lists firmware versions (RECORD them), `refresh`/`upgrade` updates, `downgrade` rolls back (the EC 0x0300 fix) |
| `git clone URL` | copy a source-code repository from the internet (then `cd` into it to build) |
| `cmake -B build …` / `cmake --build build` | configure a source build into folder `build/` with the given options / actually compile it (the llama.cpp §2.1 build) |
| `python -m pip install` | install a Python package (module form of pip; on this OS prefer uv inside a venv — PEP 668 blocks bare pip) |
| `uv venv` / `uv pip install` / `uvx` / `uv tool install` | uv = fast Python environment manager: create an isolated env / install into it / run a tool without installing / install a tool on the PATH |
| `npm install -g` | Node.js package manager, `-g` = system-wide (the pi agent, §2.2) |
| `systemctl` | control background services (`start`/`stop`/`enable`); services are defined by unit files like the §2.1 llama-server example |
| `sudo reboot` | restart the machine (§1.2: only after the pre-reboot module check!) |

### A.5 Processes, sessions and system state

| Command | What it does |
|---|---|
| `pkill name` | stop every process whose name matches — the teardown for llama-server |
| `usermod -aG docker $USER` / `newgrp docker` | add yourself to the `docker` group (so docker works without sudo) / refresh group membership without logging out |
| `swapoff -a` | disable swap (§1.7: on these boxes, fail fast instead of thrashing) |
| `sync` | flush pending disk writes — done before dropping caches |
| `tmux` | terminal sessions that survive disconnection: `tmux new -s name` → work → `Ctrl-b d` to detach → `tmux attach -t name` later. Use for every long job (§1.2.a) |
| `ssh user@host` | open a secure shell on another machine — the day-one access policy rests on it |

### A.6 Project-specific tools (quick reference)

| Command | What it does |
|---|---|
| `nvidia-smi` | the GPU dashboard: driver/CUDA versions, utilisation, temperature, power. The runbook's most-used diagnostic (§3.c power-state taxonomy runs on its `--query-gpu` form) |
| `nvcc --version` | the CUDA compiler — printing its version proves the CUDA toolkit is present |
| `nvidia-ctk` | NVIDIA Container Toolkit — the bridge that lets Docker containers use the GPU |
| `docker` | runs software in isolated **containers**: `run` (start, with `-p` port mapping, `-v` folder mapping, `-e` environment variables, `--gpus all` GPU access), `ps` (list running), `stop`/`rm` (teardown), `login` (registry authentication), `compose` (multi-container stacks), `version` |
| `hf` | Hugging Face CLI — `hf auth login`, model downloads (the runbook pins exact repos, §3.a) |
| `llama-server` / `llama-bench` | llama.cpp's OpenAI-compatible model server / its benchmark tool (Part C) |
| `llama-benchy` | the community-standard endpoint benchmark (Part C.2 — frozen flag set, do not vary) |
| `vllm serve` / `ray` | vLLM's serve command (inside the NGC container) / the cluster coordinator used in §2.8 |
| `aider` / `code` / `glow` | terminal coding assistant (§2.2) / VS Code editor (markdown preview + Cline host) / terminal markdown reader |
| `docling` / `jupyter` | document-parsing pipeline (§2.1.3 ingestion) / notebook environment (§2.7) |
| `google-chrome` / `terminator` | the browser and split-pane terminal installed in §1.2.a |

> [!TIP]
> **Two habits that teach you the rest:** (1) `man <command>` opens any command's full manual (`q` to quit); `<command> --help` gives the short version. (2) Before running a runbook one-liner, read it aloud left-to-right using the A.1 table — if you can narrate what it will do, you understand it; if not, ask before running. `history` shows everything you have typed, which is useful when filling a STEP RECORD after the fact.

---

## Annex B — AI & serving concepts: plain-language glossary (NEW in v4.5)

*Purpose:* Annex A explains every Linux **command** in this runbook; this annex explains every AI and serving-stack **concept** — read A for commands, B for concepts; the two exist together so that no step ever assumes prior knowledge.

| Term | What it means |
|---|---|
| **LLM (large language model)** | The AI model itself: a program trained on huge amounts of text that reads and writes language. Everything this runbook serves, benchmarks or connects to is an LLM or a helper model around one. |
| **Token / tok/s** | A token is the word-fragment unit (roughly three-quarters of an English word) in which models read and write text. tok/s — tokens per second — is the standard speed measure. |
| **Prompt** | The full text sent to the model for one request: instructions, the user's question, and any retrieved documents. |
| **Context window (context length, ctx)** | How much text, counted in tokens, the model can consider at once — prompt plus answer. Anything beyond it is invisible to the model. "128K ctx" = about 130,000 tokens. |
| **Prefill vs decode** | The two phases of answering: prefill is the fast initial reading of the whole prompt; decode is generating the answer one token at a time. Decode speed is what a user feels; prefill speed matters for long RAG prompts. |
| **TTFT (time to first token)** | The wait between sending a request and the first word of the answer appearing — the "did it hang?" metric. |
| **KV cache** | The model's working memory of the conversation so far (its computed Keys and Values). It grows with context length and can rival the model itself in size; storing it in 8-bit (fp8/q8_0) halves that cost. |
| **Inference** | Running a trained model to produce answers — as opposed to training it. These boxes are inference machines. |
| **Weights** | A model's learned numbers — the multi-GB files you download. Serving a model = loading its weights into memory. |
| **Parameters / 30B, 120B…** | The count of a model's weights; "30B" = 30 billion. Bigger is usually smarter but slower and hungrier. |
| **Dense model** | A model in which every parameter works on every token — quality per parameter is high, but speed on bandwidth-limited hardware is low. |
| **MoE (Mixture of Experts)** | A model split into many specialist sub-networks ("experts") of which only a few activate per token — so it generates much faster than its total size suggests. The Spark's preferred model class. |
| **Active parameters ("A3B", "A12B"…)** | In an MoE name like 80B-A3B: 80 billion parameters total, but only ~3 billion active per token. Speed follows the active count; memory needs the total. |
| **Quantisation** | Storing a model's numbers at reduced precision (4- or 8-bit instead of 16) to make it smaller and faster, at a small quality cost. The format names below are all quantisation schemes. |
| **NVFP4** | NVIDIA's 4-bit format, hardware-optimised for Blackwell GPUs like this one — the preferred vLLM format here. |
| **FP8 / MXFP4** | 8-bit floating point (used for weights and KV caches) / a block-scaled 4-bit format (gpt-oss ships in it). |
| **Q8_0, Q4_K_M, IQ2, UD-IQ2_M…** | llama.cpp's quantisation level names: the first digit ≈ bits per weight (Q8 ≈ near-lossless, Q4 ≈ standard, IQ2 ≈ aggressive 2-bit). 2–3-bit quants trade real quality for fitting huge models — hence the §3.a caution. |
| **GGUF** | llama.cpp's single-file model format — one downloadable file containing the quantised weights plus metadata (including the chat template). |
| **safetensors** | The standard raw-weights file format on Hugging Face — what vLLM serves directly. |
| **AWQ** | "Activation-aware weight quantisation" — another 4-bit method, currently the best-performing on GB10 in vLLM for some big MoEs. |
| **Serving engine** | The program that loads a model and answers requests to it over the network — here vLLM (measured/concurrent) and llama.cpp (single-user); SGLang is a third the community also uses. |
| **vLLM** | The industry-standard open-source serving engine; NVIDIA packages a Spark-optimised build of it in an NGC container. PagedAttention and continuous batching are its techniques for efficient memory use and serving many users at once. |
| **llama.cpp / llama-server** | A lean open-source engine, the most battle-tested on this hardware; runs GGUF files; llama-server is its API server. |
| **API / OpenAI-compatible endpoint** | An API is a machine-readable interface programs call. "OpenAI-compatible" means it uses the same URL paths and JSON shapes as OpenAI's API (`/v1/chat/completions`…), so any client that speaks that de-facto standard works with our local servers. |
| **Endpoint** | A service's callable network address — IP + port + path, e.g. `http://spark-1:8000/v1`. |
| **Port** | A numbered door on a machine through which one network service talks (8000, 6333, 3000… — see §3.b). |
| **REST / gRPC** | Two ways programs call services over a network: REST = web-style HTTP requests (what `curl` sends); gRPC = a faster binary alternative. |
| **JSON / JSONL** | JSON is the standard text format for structured data programs exchange; JSONL is a log-file convention with one JSON record per line. |
| **RAG (retrieval-augmented generation)** | The KB pattern: relevant document passages are *retrieved* first and handed to the model with the question, so answers come from your documents (with citations) rather than from the model's memory. |
| **Knowledge base (KB)** | This project's RAG system as users see it: ingested documents + retrieval + an answer model + a chat interface, with mandatory citations. |
| **Embedding / embedding model** | An embedding is a list of numbers (a vector) computed from text so that similar meanings get similar numbers; the embedding model (BGE-M3 here) computes them. This is how "find passages about X" works mathematically. |
| **Vector / vector database** | The vector is that list of numbers; a vector database (Qdrant here) stores millions of them and finds the nearest ones to a query fast. |
| **Chunk / chunking** | A passage-sized piece of a document. Retrieval works on chunks, not whole files — chunking is the splitting step during ingestion. |
| **Ingestion** | The pipeline that turns raw documents into the KB's searchable form: parse (Docling) → caption figures (VLM) → embed → store in Qdrant. |
| **Payload** | The metadata stored alongside each vector in Qdrant (source file, page number…) — it is what makes citations possible. |
| **Upsert** | Insert-or-update: write a record, replacing any existing one with the same ID. |
| **Reranker / cross-encoder** | A second, more careful model that re-orders the retrieved passages by true relevance. It reads query and passage *together* (hence "cross-encoder") — slower but sharper than embedding search. |
| **BM25** | The classic keyword-match scoring formula from traditional search engines — exact terms, no AI. Strong on part numbers and acronyms that embeddings blur. |
| **Hybrid search** | Running BM25 keyword search AND embedding (semantic) search on the same query, then merging the two result lists — each catches what the other misses. |
| **RRF (Reciprocal Rank Fusion)** | The standard formula for that merge: each result scores by its rank position in each list, so items ranked well by both float to the top. |
| **Multi-vector / late interaction (ColQwen, MaxSim)** | Instead of one vector per page, one per image patch; at query time each query vector matches its best patch and the scores sum ("late interaction"/MaxSim). This is what lets a text query hit a diagram. |
| **VLM (vision-language model)** | A model that understands images as well as text — used in ingestion to caption figures, and as GraniteDocling for hard layouts. |
| **Grounding / grounded** | An answer is grounded when every statement is backed by the supplied source material — nothing invented. "No citation, no claim" is the enforcement rule. |
| **Hallucination** | The failure mode grounding prevents: the model confidently stating something false or invented. Citations + the unanswerable-question test (§2.1.4) are the countermeasures. |
| **Golden set** | A fixed list of test questions with known correct answers (including ~10 % deliberately unanswerable ones). Asking the same set every time makes quality changes measurable. |
| **Speculative decoding (spec-decode)** | A small "drafter" model proposes several tokens ahead; the big model verifies them in one pass. Correctly implemented it is lossless (identical output distribution) and typically 2× faster on this hardware. Policy: §0.6. |
| **Drafter** | The small pinned model doing the proposing. **Acceptance rate** = the share of its proposals the big model accepts (the gate demands ≥ 60 %). **MTP / EAGLE3 / DFlash** are the main drafter techniques, chosen per model family. |
| **Single-stream vs concurrency / batch** | Single-stream = one request at a time (what one user feels); concurrency = many requests served simultaneously — aggregate throughput scales far better than single-stream on this box, which is why batch workloads suit it. |
| **Chat template (Jinja, minja)** | The small script shipped inside each model that converts the structured conversation (system/user/assistant/tool messages) into the exact text layout the model was trained on. Written in the Jinja templating language; minja is llama.cpp's C++ engine for it. Broken templates fail *silently* — see §3.a.1. |
| **Tool calling** | The model asking its client to run a named tool/function with arguments and return the result — the mechanism every agent workflow rests on. |
| **Thinking mode** | The model writing private reasoning steps before its visible answer. Improves hard answers; interacts badly with tool calling on some models (§3.a.1). |
| **Agent / agentic** | An AI setup where the model does not just answer but acts in a loop — reads files, edits, runs commands, calls tools — toward a goal, with results fed back to it. |
| **Harness** | The program wrapped around a model that gives it those abilities and enforces the rules (aider, Cline, OpenHands, pi). Same model + different harness = different results, which is why M42 scores harnesses under parity rules. |
| **M42** | The project's coding benchmark suite (defined in the Benchmark Strategy companion): fixed tasks, scored harnesses, parity rules. |
| **MCP (Model Context Protocol)** | The open standard for connecting AI agents to tools and data: a small server advertises tools ("search the KB") and any MCP-capable agent can discover and call them. §2.10 builds ours. |
| **FIM (fill-in-the-middle) / autocomplete** | The model completing code *between* what is before and after the cursor — the "ghost text" style of assistant (§2.3, Tabby). |
| **Repo map** | aider's compressed index of a repository (files, functions, call relationships) that lets a model navigate a codebase far bigger than its context window. |
| **Fine-tuning** | Further training an existing model on your own examples so it adopts your style or task. |
| **LoRA / QLoRA / adapter** | The cheap form of fine-tuning: train a small "adapter" bolted onto the frozen model instead of the whole thing (QLoRA = same, on a quantised model). The adapter is a small separate file. |
| **Tensor parallelism (TP)** | Splitting every layer of one model across two GPUs/machines, computing in lockstep — how a model too big for one Spark spans the pair (TP=2). |
| **Pipeline parallelism (PP)** | The alternative split: machine 1 holds the first half of the layers, machine 2 the second — less cross-talk, used as a fallback when TP init wedges. |
| **RDMA / RoCE** | Direct card-to-card memory transfer that bypasses the CPU (RoCE = RDMA over Converged Ethernet). The only way the 200G link between the Sparks pays; plain TCP over it is the slow fallback. |
| **NCCL** | NVIDIA's library that moves data between GPUs during clustered serving — the transport everything in §2.8 rides on. |
| **Ray** | A general cluster-coordination framework vLLM can use for multi-node serving (§2.8). Single-node, its overhead is why we keep the default `mp` executor. |
| **RPC (llama.cpp)** | "Remote procedure call" — llama.cpp's simple clustering mode where one machine hosts part of the model and the other calls into it over the network. No RDMA, hence slower than vLLM TP. |
| **CUDA** | NVIDIA's GPU-computing software layer — the foundation every AI framework here builds on. Preinstalled on DGX OS; never install it separately (§1.2). |
| **GPU kernel** | In GPU jargon, a small compute program that runs on the GPU (e.g. the b12x kernels, §2.8.a) — unrelated to the Linux kernel. |
| **GB10 / Grace-Blackwell / Blackwell** | The chip in these machines: an NVIDIA superchip combining a Grace ARM CPU and a Blackwell-generation GPU sharing one 128 GB memory pool. |
| **Unified memory** | That single shared CPU+GPU pool. No separate video RAM — which is why OOM behaves so badly here (§1.7) and why `nvidia-smi` cannot report memory properly. |
| **NGC** | NVIDIA GPU Cloud — NVIDIA's official download service for containers and software (`nvcr.io`). The free public tier covers everything this runbook uses. |
| **Image vs container / registry** | An image is the downloadable packaged software bundle; a container is a running instance of one; a registry (NGC, Docker Hub) is the online library images are pulled from. Full explanation: §1.3. |
| **Repository (three senses)** | (1) apt repository = an online catalogue of installable packages; (2) git repository = a source-code project you `git clone`; (3) model repository = a Hugging Face page holding one model's files (`nvidia/Qwen3-32B-NVFP4`). Context tells you which. |
| **Revision / pin / SHA-256** | A revision is an exact version snapshot; pinning means fixing on one revision instead of "latest"; SHA-256 is the cryptographic checksum proving a downloaded file is byte-for-byte the intended one. The build log records all three. |
| **Gated model** | A model whose download requires being logged in and having accepted its licence on the Hugging Face website (e.g. Meta's Llama family) — see §1.4 Step 3. |
| **Hugging Face (HF)** | The standard online repository for open AI models (and the `hf` CLI that downloads from it). `HF_TOKEN` is your access key to it. |
| **Prometheus / metrics / Grafana** | Metrics are a server's live internal measurements, exposed at `/metrics` in the text format read by Prometheus (the standard monitoring system); Grafana is its usual dashboarding companion. |
| **Enclave / air-gap / mirror / Artifactory** | The enclave is the future controlled environment where the production system is rebuilt air-gapped (no internet). Everything it needs must first be mirrored — copied onto Artifactory, the internal server holding approved packages, images and models. |
| **Smoke test** | The quickest possible end-to-end check — switch it on and see whether smoke comes out — run before trusting or measuring anything (§1.5, §3.a.1). |
| **Teardown** | Deliberately stopping a track's services and confirming the memory is released before starting the next — mandatory here because the memory pool is shared and port 8000 is a single slot. |

---

## Revision history

<details>
<summary><b>📜 Revision history — click to expand</b></summary>

> **v4.62 (2026-08-11, per PoC-lead request — everything on the Spark, no more USB shuttle):** new **§2.1.6 [OPTIONAL] On-box assistant — Claude Code on the Spark**. Claude Code runs natively on ARM64 Linux (DGX OS = Ubuntu-based, supported): native installer + verify (`claude --version` / `claude doctor`), operator-performed login (project account, credentials never through the assistant — the standing rule), **CLAUDE.md** briefing file deployed to `~/p42/kb-bench` (the §5.e Run-Assessment procedure operationalised: file map, governance including never-authoritative and never-touch-human-columns, the assessment output contract, error taxonomy, conventions), and an optional **kb-assess.sh** wrapper (harness run → headless `claude -p` Run Assessment into the run folder — one command from lever to assessed result). Explicit **enclave caveat**: needs api.anthropic.com, shakedown-phase only; the on-box judge remains the only air-gapped AI-assessment layer. Companion: benchmark spec v0.38 (§5.e note). Doc-only for existing steps; new section is additive.
>
> **v4.61 (2026-08-11, Run-2 lesson D1 — the citation-template placeholder; companion: benchmark spec v0.30 / harness v0.19):** the shared grounding prompt told the model to cite "in the form [doc | section]" — and in Run 2 Qwen3 copied the template **literally**, emitting 14 citations reading `[doc | …]` in a single answer. The SYSTEM_PROMPT in **ask.py** (§2.1.4 Step 0) and the **Open WebUI Function** (§2.1.2.4 Step 3) now instructs copying each passage's actual source label exactly, brackets included, and forbids placeholder words — same wording as the benchmark harness, keeping the one-prompt-three-clients rule. Generation-family change: citation behaviour improves from the next run; benchmark citation metrics re-baseline (spec v0.30). Re-paste ask.py; re-install the Function code in the browser.
>
> **v4.60 (2026-08-11, operator rename on the box — the corpus-file RENAME rule):** the PoC lead renamed the E-ST-10-03 corpus file on the Spark, exposing a documented-lifecycle gap: §2.1.3.4 Step 3 covered ingest / update / remove but never renames. New WARNING block in Step 3: a rename is `--remove <old path>` + re-ingest (manifest is path-keyed; skipping the remove leaves orphaned points AND creates duplicates on the next folder ingest), verified with `--list`. Plus the exact-code rule: the ECSS issue letter goes after the full number (`ECSS-E-ST-10-03C`, never `ECSS-E-ST-10C-03`) — a transposed code orphans that document's benchmark questions (containment match fails) and collides with the shorter `ECSS-E-ST-10C` code, silently mis-crediting another document's scores. Doc-only change, no re-paste.
>
> **v4.59 (2026-08-11, self-review companion to benchmark spec v0.23):** one staleness-proofing fix in the ingest.py heredoc comment: it pinned a harness version ("kb_bench.py v0.11 embeds this file…") that the spec has since moved past — now reads version-agnostically ("the benchmark harness embeds this file in its run metrics record"), so future harness bumps cannot strand it. Comment-only; behaviour unchanged; folds into the already-pending §2.1.3.4 Step 2 re-paste.
>
> **v4.58 (2026-08-11, full execution trace — the corpus records HOW it was processed):** companion to benchmark spec v0.20 / harness v0.11 (per PoC-lead request: every scorecard must trace to models *and versions*, the whole execution configuration). ingest.py v2.6 → **v2.7**: (1) every run that actually (re)processes at least one document now writes **`~/p42/kb-ingest-config.json`** — script version, `chunk_chars`, render DPI, the exact embed/caption/ColQwen model names, Python version, and the installed versions of docling / colpali-engine / qdrant-client / torch / pdf2image / transformers — the *processing baseline* of the points now in Qdrant, which the benchmark harness embeds in `run_metrics.json` (the serving-side identities — TEI/vLLM/Qdrant versions and loaded-model shas — the harness collects itself from the live APIs). (2) Model names and DPI hoisted to module **constants** (`EMBED_MODEL`, `CAPTION_MODEL`, `COLQWEN_MODEL`, `PDF_DPI`): one place, used by the code *and* recorded verbatim, so record and behaviour cannot drift. Skipped-only runs do **not** overwrite the record (their points were built by whatever config last wrote it); after changing any processing constant, re-ingest the full corpus so the baseline is uniform. Re-paste §2.1.3.4 Step 2's heredoc; the next ingesting run backfills the config file.
>
> **v4.57 (2026-08-11, Run-0 lesson — Qwen3 thinking mode ate the answers):** companion to benchmark spec v0.18. Run 0 revealed that Qwen3-class answer models **think by default**: at the previous token budgets, most completions were partially or entirely `<think>` deliberation, truncated, sometimes with no final answer at all. Fixed in the two runbook clients that generate answers: **ask.py** (§2.1.4 Step 0) and the **Open WebUI Function** (§2.1.2.4 Step 3) now send `chat_template_kwargs: {enable_thinking: false}` (honoured by vLLM for Qwen3; ignored by other engines), raise the token budget (ask.py 700 → 1200), and strip residual `<think>` blocks from displayed answers. Note for the catalogue's Part-C thinking-mode experiments: thinking stays available as a deliberate lever — what changed is that the DEFAULT for cited KB answering is thinking OFF, so the budget goes to the answer. Re-paste ask.py; re-install the Function code in the browser.

> **v4.56 (2026-08-10, operator question during the corpus batch — RapidOCR "empty result" warnings):** benign-warning decode added to §2.1.3.4 Step 3: the RapidOCR empty-result warnings mean OCR inspected an image region (diagram/logo/decoration) containing no readable text — the correct outcome on born-digital PDFs, expect dozens per batch; decode rule = warning + healthy chunk count → ignore, warning + near-zero chunks on a substantial document → real extraction failure, retry that file with the 2.1.3.1 VLM pipeline. Doc-only change, no re-paste.

> **v4.55 (2026-08-10, per PoC-lead — kb-mode-update.sh now WAITS for its services):** step 6 upgraded from "start and hope" to start **and wait until each service answers**: `start_c` now also covers `vllm-embed` (an UPDATE window entered straight after a boot would otherwise miss it), and a `wait_ready` helper (same probe pattern as the serve script: 5 s probes, progress line every 30 s, READY reports elapsed time) blocks on BGE-M3 :8080 (timeout 240 s) and the VL captioner :8002 (timeout 480 s, matching the measured minutes-scale model load). Timeout is a WARN, not an abort — ingest.py's v2.6 preflight remains the hard gate — but the normal path now ends with both READY lines, so "UPDATE mode - run ingestion now" is finally literally true the moment it prints. Re-paste kb-mode-update.sh (+chmod).

> **v4.54 (2026-08-10, live finding on spark-9d0e — the dead-:8002 failure recurred on the REAL corpus batch, root-caused as a mode-script asymmetry):** the first 23-document corpus run failed file after file with `Connection refused` on :8002 — the same failure as v4.46, and this time the systemic cause is clear: **kb-mode-serve.sh stops `vllm-vl` on the way back to SERVING, but kb-mode-update.sh never started it on the way into UPDATE** — so every new update window began with a dead captioner unless the operator remembered 2.1.3.2 by hand. Two symmetrical fixes: (1) **kb-mode-update.sh gains step 6 "Start the ingestion-side services"** (`start_c vllm-vl`, helper added; first creation still 2.1.3.2's job) — entering UPDATE mode now brings up what ingestion needs, mirroring the teardown; (2) **ingest.py v2.5 → v2.6: built-in service preflight** — the batch refuses to start (clear per-service DOWN lines + fix hints, ABORT before any parsing) if Qdrant :6333, BGE-M3 :8080 or the VL captioner :8002 is unreachable, ending the failure mode where each doomed file burned minutes of Docling parsing first. The manual preflight block in 2.1.3.4 Step 3 remains as documentation, but the script now enforces it. Re-paste: kb-mode-update.sh (+chmod) and the §2.1.3.4 Step 2 ingest heredoc.

> **v4.53 (2026-08-10, live finding on spark-9d0e — `KeyError: 'choices'` from the answer LLM):** root cause: the requests used the placeholder `"model": "default"` — llama-server tolerates any name, but **vLLM rejects unknown model names with an error JSON** (no `choices` key), and the answer seat runs on vLLM. Fixed in all THREE clients that shared the defect: ask.py, the benchmark harness (spec v0.17 / harness v0.8) and the Open WebUI Function. Fix is engine-agnostic: the served model name is **discovered from `/v1/models`** at startup (both engines expose it; llama-server fallback = "default"), the harness prints it in RUN CONFIG and records it in run_metrics.json (`answer_model` — provenance that was missing anyway), the Function gains an `LLM_MODEL` valve (default `auto` = discover), and every client now surfaces the server's own error body on a missing `choices` instead of a bare KeyError. Runtime-tested in the mock rig (which now asserts the discovered name is actually sent). Re-paste ask.py + the Function; harness folds into the pending re-paste.

> **v4.52 (2026-08-10, live finding on spark-9d0e — ask.py crashed on qdrant-client API removal):** `AttributeError: 'QdrantClient' object has no attribute 'search'` — recent qdrant-client versions (our floor is `>=1.12`, which resolves to the latest) have **removed** the long-deprecated `.search()` method; the current call is **`.query_points(...).points`**. Fixed in ask.py (§2.1.4 Step 0) — and, decisively, in the **benchmark harness**, which shared the same call and would have crashed identically at Run 0 (spec v0.16 / harness v0.7; the earlier mocked smoke test stubbed the client itself and therefore could not catch a client-API change — the re-test stub now mirrors the real API shape, including the absence of `.search`). ingest.py (upsert-only) and the Open WebUI Function (REST) are unaffected. Re-paste ask.py; the harness re-paste folds into the pending v0.15→v0.16 one.

> **v4.51 (2026-08-10, per PoC-lead request — metrics collection; companion: benchmark spec v0.14 / harness v0.6):** ingest.py v2.4 → **v2.5**: each ingested file now records pages, chunks and per-stage timings (parse / visual / embed), and every run appends one JSON line to **`~/p42/ingest-runs.jsonl`** (run totals + per-file records) — the empirical base for sizing maintenance windows ("N pages took M minutes") and for spotting a stage that suddenly got slower after a change. The bigger half of the request lives in the benchmark spec v0.14: harness v0.6 with per-stage latency (mean/p50/p95), token usage + answer throughput, retrieval score diagnostics (absence-vs-buried decode), enriched RUN CONFIG provenance (question-file sha256, live collection point count), and a per-run **run_metrics.json** so ablation rows compare by diffing files. Re-paste: the §2.1.3.4 Step 2 ingest heredoc and the spec §6 Step 1 harness heredoc.

> **v4.50 (2026-08-10, follow-through on the v4.49 gap — the "Project 42 KB" chat UI):** new **§2.1.2.4 Step 3 [ALL]** — an Open WebUI **Function** (type *pipe*, ~85 lines, assistant-drafted, live validation = the step's Expect) that puts **"Project 42 KB" in the chat model picker**: selecting it routes every question through the project pipeline (BGE-M3 :8080 → Qdrant `p42_text` :6333 via REST → reranker :8081 optional → answer LLM :8000) with the same grounding prompt as the harness and ask.py, and appends a Sources block (doc | breadcrumb | page) to every answer. Endpoints, TOP_K/CONTEXT_K and MAX_TOKENS are editable **Valves**; runs inside the Open WebUI container (host.docker.internal, LAN-IP fallback documented); KB ERROR messages name the unreachable service+URL; known v1 limitation stated (retrieval on the latest question only). Admission test: cited answer + refusal behaviour + source agreement with ask.py on the same question. Onyx renumbered Step 3 → **Step 4**. This completes the three query routes of v4.49: harness (measurement), ask.py (engineer CLI), Function (end-user chat).

> **v4.49 (2026-08-10, operator question — "what UI queries the ingested KB?" — a real product gap closed):** the honest answer was NONE: the project's Qdrant collections were queryable only by the batch harness, Open WebUI's `#` sees only its own uploads, and the runbook's mode table called Open WebUI "the KB user interface" without saying that wiring it to the project KB needs a component that did not exist. Two changes: (1) **new §2.1.4 NOTE** naming the three query routes (harness = batch; ask.py = interactive CLI, available now; Open WebUI Function/pipe = the proper chat-picker UI, planned as its own validated step); (2) **new §2.1.4 Step 0 — `~/p42/ask.py`**, a ~60-line interactive query CLI using EXACTLY the harness's retrieval path (BGE-M3 :8080 → Qdrant p42_text → optional reranker :8081 → answer LLM :8000, same grounding prompt) and printing the answer plus a numbered source list (doc | breadcrumb | page) — so what the operator sees interactively is what the benchmark scores. If-not decodes included; refusal behaviour testable interactively. The Open WebUI Function step follows once drafted and live-validated.

> **v4.48 (2026-08-10, operator question — "attached via #" + a real path conflation in 2.1.4):** the question "what does *attached via #* mean" exposed more than a UI-mechanics gap. (1) `#` explained at both mentions: typing `#` first in Open WebUI's message box opens a picker of Knowledge collections; selecting one attaches it as a chip and routes that chat's questions through retrieval over the collection. (2) **The real fix:** 2.1.4 Step 1 conflated the two retrieval paths — it said to ingest the test PDFs with the 2.1.3 flow (which fills the PROJECT's Qdrant collections) and then query via `#` (which searches ONLY Open WebUI's own uploaded collections and would have found nothing). Step rewritten as two explicit paths: **path A** = project pipeline (2.1.3 ingest, queried by the benchmark harness / 10-question dev spot-check), **path B** = Open WebUI Knowledge collection (same PDFs uploaded through the UI, same embedder/reranker services, queried via `#`); the chat questions run against path B, and "chat finds nothing while the harness retrieves fine" is decoded as a wrong-path attachment. 2.1.2.4 Step 2 item 3 expanded to walk the create-upload-attach sequence.

> **v4.47 (2026-08-10, live finding on spark-9d0e — serve script's readiness window mis-calibrated):** `kb-mode-serve.sh` declared WARN on a perfectly healthy answer-LLM start: the :8000 readiness probe gave up after ~90 s (based on a 45–90 s estimate), but the **measured** ready time for the 32B NVFP4 answer model on this box is **~4 minutes** (weight load + CUDA graph capture — normal, not a fault). Probe rewritten: window now **480 s** (~2× measured, so slow days still pass), 5 s probe interval, a progress line every 30 s ("… 120s elapsed, still loading"), READY reports the actual elapsed time (a free per-boot measurement for the build log), and the final verdict re-probes rather than inferring from the counter. kb-boot.sh inherits the fix automatically (it calls this script). **Functional script change — re-paste the kb-mode-serve.sh heredoc** (§2.1.1 Step 1) + chmod.

> **v4.46 (2026-08-10, live findings on spark-9d0e — dead :8002 mid-batch + a SILENT ColQwen LoRA failure):** the re-run surfaced two problems. (1) Every file errored with `Connection refused` on :8002 — the VL captioning container was not running; the batch talks to three live services and a dead one fails every file only after minutes of work, so §2.1.3.4 Step 3's preflight now also **curls all three services** (:6333 Qdrant, :8080 embeddings, :8002 VL) before the batch. (2) **The dangerous one:** the ColQwen load printed LOAD REPORT tables with every `lora_A/lora_B` key MISSING/UNEXPECTED — the LoRA adapter did NOT attach (transformers layer-rename mismatch) and colpali-engine **silently fell back to randomly initialized projection weights**: no error, garbage page vectors, broken visual retrieval. Verified against the colpali-engine release notes: **0.3.14** names this exact fix ("preventing silent fallback to randomly initialized projection adapters"). 2.1.3.3 Step 1's install floor raised from the model card's outdated `>0.3.1` to **`>=0.3.14`** with the why, and the Step 3 preflight now asserts the installed version. Nothing was ingested in the failed runs (the :8002 error aborted before any upsert), so no cleanup is needed.

> **v4.45 (2026-08-10, live finding on spark-9d0e — apparent hang after `chunks: 23 | revision: C`):** not a hang — the first-use ColQwen download (~6–7 GB) ran in a silent gap between the chunks line and the `[2/3] visual pass` line, exactly the invisible-wait pattern this project has hit before (§1.5 xet lesson). ingest.py v2.3 → **v2.4**: the model load announces itself (name, download warning, the `du -sh ~/.cache/huggingface` check to watch, and a `ColQwen ready (Xm Ys)` line with the load time), and page rendering prints its own line before poppler runs — no stage is silent any more. Operational note recorded with it: if `du` is NOT growing during the quiet period, check `echo $HF_HUB_DISABLE_XET` prints 1 in the ingest shell (the §1.5 xet stall signature); Ctrl-C + export + re-run is safe — the manifest never marks an unfinished file as done.

> **v4.44 (2026-08-10, operator question — safe power-down):** NOTE added to §2.1.1 after the lifecycle-scripts step: powering the Spark down safely (never mid-ingestion; no teardown needed — clean OS shutdown stops containers gracefully and all survive; always `sudo shutdown -h now`, never a hard power cut — a mid-write power cut is the one Qdrant corruption path the pre-update snapshots do not cover), and powering back up (kb-boot.sh → optionally kb-mode-update.sh for ingestion work; pragmatic minimum while the stack is under construction: swapoff + `docker start qdrant vllm-embed vllm-vl`).

> **v4.43 (2026-08-10, live finding on spark-9d0e — ColQwen checkpoint unloadable + revision parser gaps):** the first ingest attempt failed on every PDF with `OSError: Metric-AI/colqwen2.5-7b-base is not a local folder and is not a valid model identifier`. Root cause verified externally: the Metric-AI 7b multilingual checkpoint is a LoRA adapter whose **base repo went gated on Hugging Face (HTTP 401, checked live 2026-08-10)** — the adapter cannot load without granted access. Fix per the maturity-first policy: ingest.py v2.2 → **v2.3** swaps to **`vidore/colqwen2.5-v0.2`**, the canonical ColPali-authors checkpoint (public, public Qwen2.5-VL-3B base, same ColQwen2_5 classes, same 128-dim multivectors — collection config unchanged; nothing had been ingested, so no index invalidated). 2.1.3.3 Before text and the §3 model table updated; Model Catalogue carries the same swap at its next edit; the vidore repos join the mirror list at G2. Second fix in the same script: **`revision_of()` broadened** — the `AS` (adoption notice) document type and `-Rev.N` suffixes are real ecss.nl filename shapes (seen live: `ECSS-E-AS-50-21C-Rev.2(...)` now → `C Rev.2`; previously `(none)`). Operator action: re-paste the §2.1.3.4 Step 2 ingest heredoc, re-run the batch — the manifest re-ingests the three error files automatically (errors are not recorded as done).

> **v4.42 (2026-08-10, live finding on spark-9d0e — §2.1.3.4 Step 3, ingest run failed with `No module named 'pdf2image'`):** root cause is a dependency-visibility flaw, not a broken package: the ingest script's Python dependencies are installed across three earlier steps (docling in 2.1.3.1, colpali-engine/pdf2image/qdrant-client/torch in 2.1.3.3), so a skipped step — or a shell without the ingest-venv active — only surfaces at run time. Two fixes: (1) **2.1.3.4 Step 3 gains a two-second dependency preflight** before the first batch — one `python -c` import line covering every module the script needs (a missing module names itself and the Before text maps each name to the step that installs it) plus a `pdftoppm -v` check. (2) **Latent second failure preempted:** pdf2image is only a wrapper around poppler's `pdftoppm`, a SYSTEM program pip cannot provide — without it page rendering dies at run time with "Unable to get page count. Is poppler installed?" even after a clean pip install; `sudo apt-get install -y poppler-utils` added to 2.1.3.3 Step 1 with the why, and poppler-utils joins python3-dev in the air-gap OS package set.

> **v4.41 (2026-08-10, live operator fixes on spark-9d0e — §2.1.2.2 Step 3, reranker launch corrected):** both v4.38 command defects found and fixed BY THE OPERATOR, working sequence adopted verbatim. (1) The architecture check `docker run --rm <image> uname -m` failed with "unexpected argument 'uname'": the image's ENTRYPOINT is `text-embeddings-router`, so trailing words become router arguments — check now uses `--entrypoint uname … -m`, with the ENTRYPOINT concept explained at the point of use. (2) The launch was missing **`--model-id BAAI/bge-reranker-v2-m3`** — despite the model-specific tag, the router requires the flag (the tag bakes the weights, not a launch default); without it the container exits (2) immediately. Expect/If-not rebuilt with the live decodes (empty curl reply = container not up; Exited(2)+logs = missing --model-id; unexpected-argument = missing entrypoint override; dead container holds the name → `docker rm -f reranker` before every relaunch) and the live validation result recorded: aarch64 confirmed, digest sha256:f2429a72acd1…, smoke scores 0.8376 vs 0.0000167 — the §0.6 WP1 admission for this community image. Mirror-list note: the ddosify image joins the Artifactory mirror list at G2 if retained.

> **v4.40 (2026-08-10, self-review double-check of the v4.39 restructure):** two residues found and fixed. (1) The 2.1.5 Teardown step was the one §2.1 step the tag pass missed — now `[ALL]` (26 → 27 tagged). (2) `kb-mode-update.sh`'s maintenance-window comment cited `§2.1 "The two modes"` across a line break, which the reference sweep could not match — now `§2.1.1` (comment-only script change; folds into the already-pending cosmetic re-paste). Verified clean in the same pass: zero old-scheme references in either document body, all 14 new headings unique, flow map correctly placed before 2.1.1, all five embedded scripts still extract and compile, benchmark-spec cross-references consistent.

> **v4.39 (2026-08-10, per PoC-lead direction — §2.1 architecture overhaul: decimal numbering + step tags):** the confusing letter-in-letter scheme (`2.1.A (b)`-style) and the ambiguous alternative/option labelling are gone. (1) **Renumbering to ECSS-style decimal**, old → new: 2.1 modes+scripts intro → **2.1.1**; 2.1.A → **2.1.2** (components (a)–(e) → **2.1.2.1**–**2.1.2.5**); 2.1.B → **2.1.3** ((a)–(c) → **2.1.3.1**–**2.1.3.3**; "Ingestion flow and lifecycle" → **2.1.3.4**); 2.1.C → **2.1.4**; 2.1.D → **2.1.5**. (2) **Step tags on every §2.1 step** (legend added to §0.8): `[ALL]` = everyone runs it; `[DECISION]` = choose a route, no commands, lists which steps implement each route; `[ROUTE: X]` = only if that route was chosen, and the tag names explicitly which step(s) it is the alternative to; `[OPTIONAL]` = skippable extra. (3) **Flow map added at the top of §2.1**: the 2.1.1→2.1.5 order, what each subsection builds, and where the only two route decisions live. (4) **Cross-reference sweep**: 60+ old-scheme references updated document-wide in the body and inside the script heredocs (scripts' messages now cite 2.1.1/2.1.3 — a re-paste updates the cosmetic references only; nothing functional changed since v4.38). Historical changelog entries and STEP RECORDs keep their original numbering — they are dated history. Companion: benchmark spec v0.13 (its runbook cross-references updated to the new scheme).

> **v4.38 (2026-08-10, live operator finding — §2.1.A(b) restructured; the reranker was structurally skippable):** an operator correctly following the mainline path (Step 2, skipping Step 3 "(Alternative)") ended up with **no reranker container at all** — `kb-mode-serve.sh` reported `reranker : NOT CREATED`. Root cause: the ONLY command creating the `reranker` container lived inside the alternative-TEI step, but the Step 1 decision was only ever about the *embeddings* route — the reranker is a REQUIRED baseline component (the precision stage of hybrid+rerank) and, since vLLM has no rerank endpoint, it must run as a TEI-family container on BOTH routes. Fix: **new Step 3 "(REQUIRED, both routes) Serve the reranker on :8081"** — arm64-candidate image order (ddosify model-specific tag → hwdsl2 arm64 build → self-built TEI Dockerfile-cuda; community images = §0.6 candidates: arch check first, tag+digest into the STEP RECORD, smoke test = the WP1 validation), launch command with the mode-script-managed `--name reranker`, provenance inspect, and a `/rerank` smoke test using the exact call shape the benchmark harness sends. Old Step 3 becomes **Step 4 "(Alternative, embeddings only)"** with the reranker command removed and a one-server-per-port caution added; Step 1 retitled to scope the decision to embeddings explicitly; reranker image options moved out of the Step 1 list into Step 3.

> **v4.37 (2026-08-10, live operator confusion — §2.1.A(c) Step 1 restructured):** the Qdrant start step violated the §0.8 anatomy in three ways and was rebuilt. (1) The `docker inspect qdrant` provenance command sat in a code box INSIDE the Before-you-run-it text, *before* the `docker run` that creates the container — it can only work after; it now lives in a new "**Record (AFTER the start)**" block following Expect, together with the arm64 `uname -m` check. (2) The closing code fence had prose glued onto the same line (broken rendering, unreadable block boundaries) — the persistence and jemalloc cautions are now numbered facts in the Before paragraph, which explicitly states it contains no commands. (3) The `$(pwd)/qdrant_storage` mount depended on wherever the operator happened to be standing — the Run block now begins with `cd ~/p42`, pinning the database to `~/p42/qdrant_storage/`, with the why explained. Step now reads: Before (3 numbered facts, no commands) → Run (one block) → Expect/If-not → Record (2 commands, after start).

> **v4.36 (2026-08-10, per PoC-lead request — clear progress display in all operational scripts):** consistent output format across the three shell scripts and ingest.py (companion: benchmark spec v0.12 / kb_bench.py v0.5). Design: boxed `====` START/END banners with timestamps and duration; numbered `[n/total]` step headers with a `----` rule; one status line per action; deliberately **NO colour codes** so build-log copy-paste stays clean text. Substantive upgrades that came with the reformat: **(1)** mode scripts gained `stop_c`/`start_c` helpers that report per-container what actually happened (`stopped` / `already stopped` / `already running` / `started` / `NOT CREATED → pointer at the 2.1 Step 1 error decode`) instead of raw docker errors — the v4.35 finding is now handled in the scripts' own output; **(2)** engine-aware llama-server start/stop now reports its status explicitly (and serve's `systemctl` dropped its redundant inner `sudo` — the script is root-guarded); **(3)** root guards extended to update/serve (drop_caches needs root); **(4)** ingest.py v2.1 → **v2.2**: corpus-scan count up front, `[i/N]` per-file counters with aligned `ingest/update/skip` verbs, three numbered stages per file (Docling parse → visual pass with `page n/M` progress every 10 pages → embed+upsert), and an end-of-run `SUMMARY` line (ingested/skipped/errors). All five scripts must be **re-pasted** on the box (three §2.1 Step 1 heredocs + chmod, §2.1.B ingest block, spec §6 harness block).

> **v4.35 (2026-08-10, live finding on spark-9d0e — §2.1 Step 1):** `kb-mode-serve.sh` reported `No such container: qdrant` when run before §2.1.A(c) had been executed. Not a script bug — `docker start` only restarts containers that already exist; creation happens in the §2.1.A/B `docker run --name` steps, and the `|| true` design means the scripts print such errors and continue. New error-decode paragraph added to Step 1's Expect/If-not: the message always means "not created yet (or removed)", never "failed to start"; it is expected and harmless before §2.1.A completes; includes the per-container map of WHERE each managed name is created and the `docker ps -a` inventory check. No script content changed — no re-paste needed.

> **v4.34 (2026-08-10, self-review double-check fix):** kb-boot.sh gains a **root guard**: run without sudo, `swapoff -a || true` fails silently (the `|| true` masks the permission error) and the script would print "swap OFF" while swap is still on — the §1.7 discipline silently NOT re-asserted, which is exactly the class of quiet failure the script exists to prevent. It now refuses to run as non-root with a clear usage message. Found by self-review; no other content changed.

> **v4.33 (2026-08-10, per PoC-lead request — fresh-boot startup script):** new third lifecycle script **`/opt/p42/bin/kb-boot.sh`** added to §2.1 Step 1 (step retitled "three lifecycle scripts"), closing a real gap: no KB container auto-starts after a reboot, and the §1.5 live experience showed that starting containers too early fails (CUDA-compat + DNS errors, fixed then by host checks and a Docker restart). kb-boot.sh encodes exactly that recovery as a preflight — wait for the Docker daemon (probe 3 s × 20, then ONE `systemctl restart docker` before failing hard), wait for the GPU driver (`nvidia-smi` probe loop), DNS check (`getent hosts` — warning only, offline serving survives without it), re-assert `swapoff -a` (NOT persistent across boots; §1.7 policy is swap off in operation) — then **calls kb-mode-serve.sh** for the actual ordered start, so the start sequence is maintained in one file only. v4.32 timing banners included. Deliberately NOT installed as an auto-start service: auto-boot-to-SERVING would fight the mode-exclusive design and hide the host-readiness failures the script exists to surface; a systemd unit wrapping this same script is named as a G2+ option for the enclave. chmod line and Expect updated for three files.

> **v4.32 (2026-08-10, per PoC-lead request — run timing in all operational scripts):** the three runbook scripts now clearly display **start time, end time and execution duration**. `kb-mode-update.sh` / `kb-mode-serve.sh`: timing banner + an EXIT `trap` so END/DURATION print on every exit path, including aborted switches (trap mechanism explained in the script comments). `ingest.py` v2 → **v2.1**: START/END/DURATION banners around every invocation via try/finally (so the END line survives errors), plus a per-file `file time:` line after each document — batch timings are build-log material for planning future maintenance windows. Companion change: benchmark spec v0.10 (kb_bench.py v0.4, same banner pattern). Operators who already created the scripts must re-paste the heredocs (§2.1 mode-scripts blocks + chmod, §2.1.B(a) ingest block) — nothing else changes.

> **v4.31 (2026-08-10, live finding on spark-9d0e — §2.1.B(a) Step 1):** Docling's first conversion failed on every page with `fatal error: Python.h: No such file or directory` in the layout stage. Root cause: Docling's RT-DETR layout model runs under `torch.compile`, whose Triton backend compiles a small C bridge module with gcc against the Python C headers on first use — and DGX OS does not preinstall `python3-dev` (venvs never provide C headers). Fix adopted into the step as a Before-you-run-it box: `sudo apt-get install -y python3-dev`, once per machine, BEFORE the Docling smoke test; If-not line gains the error signature; benign first-run noise named as safe to ignore (dynamo graph-break warnings, "Not enough SMs to use max_autotune_gemm" on GB10, `torch_dtype` deprecation); emergency fallback documented (`TORCHDYNAMO_DISABLE=1`, works-but-slower). Air-gap note: python3-dev joins the per-machine OS package set the enclave rebuild must mirror.

> **v4.30 (2026-08-10, pre-first-ingestion payload schema — third external review pass, triaged):** ingest script v1 → **v2**: two payload fields added to every point in both collections, timed deliberately BEFORE the first corpus ingestion so the schema decision never forces a re-ingest. (1) `document_revision` — the revision letter parsed from ECSS-style filenames (new `revision_of()`, regex on the trailing letter of the document code; empty for non-ECSS names); feeds the benchmark's deferred *revision* question class and future prefer-current-revision retrieval. (2) `element_type` — `text` / `table` / `page`; the chunker now tags whole-table chunks at flush time, enabling element-filtered search and cleaner error-taxonomy attribution without re-parsing chunk text. §2.1.B quality-levers "Rich payload metadata" row updated accordingly. Adoption source: third external review pass (2026-08-10) §17–18, triaged ADAPT — the reviewer's full schema (bbox, figure IDs, parent elements) stays a G2 option; only the two zero-cost-now fields were taken.

> **v4.29 (2026-08-08, per PoC-lead challenge on ingestion maturity):** §2.1.B's ingestion subsection replaced by **"Ingestion flow and lifecycle"**. (1) New quality-levers guidance step — "deliberately simple" made explicit ("simple as opposed to WHAT?"): a table of the named levers (structure-aware chunking with breadcrumbs and never-split tables; caption-to-chunk attachment; rich payload metadata; boilerplate removal; chunk-level vs page-level embedding; hybrid+rerank on the serving side), each marked implemented-in-v1 or refinement candidate, all governed by the standing rule — refinements are judged on the golden question set only, never by feel. (2) Ingest script v0 → **v1** (`~/p42/ingest.py`): multi-format batch ingestion (PDF/DOCX/PPTX/XLSX/HTML/MD via Docling; VL captions + ColQwen page vectors for PDFs only), structure-aware chunks with `SECTION:` breadcrumbs and whole-table chunks, stable uuid5 point IDs (re-ingestion overwrites), **manifest-driven incremental updates** (`~/p42/kb-manifest.json`: unchanged skipped, changed deleted-then-re-ingested, per-file action lines), `--remove` and `--list` lifecycle commands, per-file error isolation; lifecycle run examples added (first batch / incremental / removal / listing), and manifest + Qdrant snapshot named as the recorded "document baseline N". (3) Positioning NOTE: the deployed baseline (hybrid retrieval + cross-encoder rerank + late-interaction visual retrieval) IS the community state of the art per the KB trade-off study; LLM-based semantic chunking, GraphRAG-style enrichment and agentic retrieval are deliberately-named G2 evaluation options that must beat the baseline on the golden set to enter; "production-ready" = the G2-frozen recipe, not WP1 code.
>
> **v4.28 (2026-08-08, §2.1.B clarity rewrite — operator feedback):** (a) Docling step rewritten — the two conversion modes explained, the two vision models disambiguated (GraniteDocling reads page layout inside Docling; Qwen2.5-VL captions figures in the next stage), first-use downloads and output location stated, Expect/If-not added. (b) redundant naming instruction removed; concrete image-captioning smoke test added (the exact call shape the ingest script uses). Minimal flow upgraded from prose to a runnable **reference ingest script v0** (`~/p42/ingest.py`: Docling → per-page captions → BGE-M3 embeddings → ColQwen multi-vectors → Qdrant upsert into `p42_text`/`p42_pages` with page-citing payloads), plus a run step with REST point-count verification and failure decodes. Deliberately simple — WP1 refinements go in the build log.
>
> > **v4.27 (2026-08-08, follow-up to the venv sweep):** §1.4's teaching paragraph updated from the anonymous `.venv` pattern to the project convention the sweep established — named venvs under `~/p42/`, one per pipeline (render/ingest/lab), created once and explicitly re-activated per shell; the venv-vs-`uv tool` distinction (libraries vs CLI apps) stated where venvs are first taught.
>
> > **v4.26 (2026-08-08, systematic venv sweep after the v4.25 finding):** every Python install site audited for venv context. Fixed: §2.1.B now uses ONE named ingestion venv (`~/p42/ingest-venv`) created at the Docling step and explicitly re-activated at the ColQwen step (new terminals do not inherit activation); §2.2/§2.4 aider install corrected from PEP-668-blocked bare `python -m pip` to `uv tool install aider-chat` (2 sites); §2.8.a b12x line clarified (the install belongs inside the recipe's Docker image build, not on the host); §2.7 Jupyter venv named (`~/p42/lab-venv`). Already correct: hf/llama-benchy (`uv tool install`), §2.9 (container route), in-container pip (no PEP 668 inside containers). Standing pattern now explicit: venvs are named, live under `~/p42/`, and every block that needs one starts with its activation line.
>
> > **v4.25 (2026-08-08, LIVE FINDING):** §2.1.A(e) Step 1 ran `uv pip install` with no virtual environment — uv refuses (by design; the §1.4 system-Python rule). Fixed: the step now creates and activates a dedicated `~/p42/render-venv` first, verifies with an import check, and states the per-shell activation rule for every later use of the rendering libraries.
>
> > **v4.24 (2026-08-07, weekly watch-report batch #2 — triaged):** five adoptions + one vindication from the sweep window 2026-07-31→08-07. (1) **§2.1.A(a) KV rule refined:** `q8_0` KV is a **per-model floor, NOT universally safe** — community-verified 2026-08: DeepSeek-V4-Flash-0731 garbles on q8_0 KV and must run its KV cache at 16-bit (omit the `--cache-type-*` flags); KV-cache quantisation joins the per-model §3.a.1-style validation checklist — verify on each model before recording it in the flag set. (2) **§3.a single-Spark V4-Flash-0731 row updated:** a published MAINLINE llama.cpp config (forum 2026-08-04, correctness-checked — build 10235, Unsloth UD-IQ2_M, 524288 total ctx ÷ 4 slots = 131K/slot, `--flash-attn on --no-mmap`, 16-bit KV; 19.7 tok/s single-stream, ~52 tok/s at 4-concurrent, pp2048 ≈ 459; 96 % on a 5-category eval) adopted VERBATIM as the Part-C starting configuration (still §3.a.1-gated); measured limit added: 4 concurrent × 16K prior context collapsed to 6.3 tok/s combined — single-box V4-Flash is NOT a multi-agent serving seat (long single-agent context fine). (3) **§0.6 spec-decode policy:** llama.cpp PR #25784 (DeepSeek-V4 MTP, draft as of 2026-08-07, author-measured ~16.5→26–29 tok/s on a Spark, acceptance 0.651) tracked as the in-baseline route for this family; drafter-gate caveat — Unsloth GGUFs ship WITHOUT the MTP module, verify the quant source carries it before the gate. (4) **§2.8 gains Step 6 — sustained-high-concurrency soak before G2:** a published dual-Spark lab hit a kernel Oops + spontaneous head-node reboot under sustained RoCE load, attributed to `nvidia-dgx-telemetry` polling ConnectX-7 firmware (single lab, AI-executed benchmarks per the repo's own disclaimer — reproduce before trusting); the circulated `vm.compaction_proactiveness=0` mitigation does NOT match the stated telemetry root cause — verify what the source lab actually changed before adopting any mitigation; a reboot-under-load is a G2 availability finding. (5) **§2.10 gains a precondition:** target the MCP 2026-07-28 spec revision (breaking rewrite — stateless core, `Mcp-Session-Id` header removed from Streamable HTTP, header-based routing, Tasks + Apps extension framework) — confirm which fastmcp version implements it and whether OpenHands' MCP client has migrated before the p42-kb spike; a session-header-dependent bridge will break. Plus the vindication: the ds4-fork "~2×" claim **failed independent replication** (0.0 % draft acceptance; ~22 vs 19.7 tok/s ≈ +12 %) — non-adoption vindicated, and the G2 evidence note is weakened accordingly (Model Catalogue v0.10 carries the amendment).
>
> **v4.23 (2026-08-07, editorial + figure):** revision history moved from the header to the END of the document (execution content first); architecture figure redrawn — NEW always-on layer (Qdrant + BGE-M3, reflecting the v4.16 fix visually), UPDATE-mode embed-chunks arrow to :8080, API arc no longer crosses the UPDATE box, validated 26.07-py3 tag and xet kill-switch named on the internet side.
>
> > **v4.22 (2026-08-07, two operator requests):** (1) §2.1.A(c) Step 1 now states there is NOTHING to install for Qdrant — `docker run` pulls the image automatically on first use (§1.3 lesson restated at the point of doubt), plus the provenance duty: record the image tag + digest via `docker inspect` (no `:latest` in the enclave). (2) All 5 remaining `<vllm-openai-arm64-image>` placeholders replaced with the concrete validated default **`nvcr.io/nvidia/vllm:26.07-py3`**; §0.8 notes the substitution rule if the §1.5 smoke test pinned a different tag.
>
> > **v4.21 (2026-08-07, systematic sweep after the v4.20 finding):** programmatic scan of every `docker run` block for the v4.20 defect classes (bare `--model` flags, missing memory budget, missing `--ipc=host`/ulimits, missing xet kill-switch, missing container name). Result: zero remaining bare-flags/budget/ipc/xet issues; four missing `--name`s fixed — §1.5 smoke test (`vllm-smoke`), **§2.1.A(a) Qwen answer LLM (`vllm-llm` — the name the kb-mode scripts stop/start; without it the mode switch would silently miss the container)**, and the two TEI alternative blocks (`tei-embed`, `reranker` — note: adopting the TEI route means aligning the kb-mode scripts' container names). Qdrant and Open WebUI blocks already carried their names.
>
> > **v4.20 (2026-08-07, LIVE FINDING — embeddings launch failed with `exec: --: invalid option`):** the v4.1 `vllm serve` entrypoint standardisation had missed the two service blocks — §2.1.A(b) embeddings and §2.1.B VL captioning still used bare `--model` flags, which this tag's entrypoint cannot exec. Both blocks fixed to the `vllm serve` form and hardened with what they were also missing: container names (`vllm-embed`, `vllm-vl` — the exact names the kb-mode scripts manage), explicit memory budgets (0.15 embeddings — without it vLLM defaults to ~0.92 and grabs the pool next to the answer LLM; 0.3 VL), and the `--ipc=host` + ulimit set the container itself requests.
>
> > **v4.19 (2026-08-07, decision clarity — operator question):** §2.1.A(b)'s vLLM-vs-TEI choice now states what it does and does not change: output quality identical (same BGE-M3 weights, deterministic computation); "cleaner API" = purpose-built `/embed` and `/rerank` endpoints (rerank has no natural vLLM equivalent); TEI leaner in principle but no arm64 GPU image — maturity decides for vLLM; revisit condition stated.
>
> > **v4.18 (2026-08-07, per PoC-lead question during §2.1 execution):** §2.1.A(a) gains **Option A2 — gpt-oss-120b on vLLM** as a documented answer-seat variant: repo `openai/gpt-oss-120b` (native MXFP4), env `VLLM_USE_FLASHINFER_MXFP4_MOE=1`, budget 0.60 + `--max-model-len 32768` (weights ~61 GB; 0.55 would starve the KV cache; 0.60+0.15 = the 0.75 ceiling), pre-download + mandatory cache drop, §3.a.1 harmony-template gate before adoption; framing: llama.cpp = canonical single-user route, vLLM = multi-user KB seat, Part C concurrency sweep decides.
>
> > **v4.17 (2026-08-06, clarity pass per PoC-lead feedback):** editorial pass, document-wide — no command, flag value, pin, URL, model name or warning changed. (1) **9 alert boxes rewritten in full-explanation form** (fact → why it matters → what to do), replacing telegraphic fragments: the §1.0 manual-USB-build TIP, the §1.5 log-signatures NOTE, the §2.1 snapshot/restore IMPORTANT, §2.1.A's vLLM flag-corrections IMPORTANT + memory-budget IMPORTANT + image-tag/entrypoint VERIFY, the §2.1.B Qwen3-VL and ColQwen VERIFYs, and §2.8 clustering traps 1–4; the §2.1.A(a) llama.cpp flag-rationale paragraph likewise rewritten one flag at a time. (2) **~85 command flags given first-use explanations** (in-block `#` comments or a flag-rationale sentence right after the block — among them `-ngl 999`, `-fa on`, `--no-mmap`, `-b/-ub 2048`, `--cache-type-k/v q8_0`, `--ipc=host`, the two `--ulimit`s, `-p`/`-v`/`-e`/`-d`/`--rm`/`--name`/`--restart`, `--runner pooling`, `--enforce-eager`, `--max-model-len`/`--max-num-seqs`, the cmake `-D` set, `usermod -aG`, `ss -tlnp`, `nvidia-smi -l`/`-lgc`/`--query-gpu`, `curl -sf/-H/-d/-X`, and the llama-benchy set). (3) §0.8 now states both as standing format rules. Changelog entries, STEP RECORDs, Annex A/B one-liner tables and the master checklist deliberately untouched.
>
> **v4.16 (2026-08-06, operator ordering question exposed a real dependency bug):** UPDATE mode had NO embedder — the ingestion flow's upsert needs BGE-M3, but `kb-mode-update.sh` stopped the `vllm-embed` container. Fixed: **BGE-M3 stays up in UPDATE mode** (mode table, script and ingestion step 4 aligned), with the deeper reason stated — the index and future queries must use the IDENTICAL embedding service or retrieval silently breaks. Also added the "why 2.1.A before 2.1.B" NOTE (Qdrant and BGE-M3 are stood up in A because B writes into them; UPDATE mode transforms the serving stack so it must exist first; empty-KB retrieval tests returning nothing in A is expected — the full proof is 2.1.C).
>
> > **v4.15 (2026-08-06, weekly watch-report batch — triaged):** three adoptions from the weekly community watch report. (1) §1.2 Step 3 gains a **kernel-regression watch CAUTION**: a forum report (2026-08-06, single reporter, ASUS GX10 + DGX Spark pair) of a severe **one-way inbound RDMA regression** on kernel `6.17.0-1029-nvidia` (13.2 Gbit/s inbound vs 111.7 Gbit/s after rollback to `-1026`) — rule: HOLD at the current known-good kernel, do NOT take `-1029` (or later) until inbound RDMA is verified in both directions; only matters for the §2.8 cluster experiment, but a kernel is easier to refuse than to roll back. Also logged as OEM-divergence evidence (same GB10 silicon ≠ same platform behaviour). (2) §2.8 trap list gains trap 6: **bidirectional `ib_write_bw` verification** (server on node A / client on B, then swap) — a one-way test would have passed the 2026-08 kernel regression; expect ~symmetric ~100+ Gbit/s, asymmetry → check the kernel against the §1.2 caution. (3) §2.1.C gains the **co-residency CUDA-context check** (all GPU services hold CUDA contexts simultaneously and answer — one embeddings call, one rerank call, one chat completion in the same session), motivated by an unconfirmed forum report (2026-08-05) of `CUDA_ERROR_NO_DEVICE` for a second CUDA process while another holds a context — cheap to check now, expensive at the demo. Also noted but NOT adopted: the ds4-fork single-Spark V4-Flash numbers (~1,000 tok/s prefill / ~28 tok/s decode @12K, self-reported) are logged as G2 evidence on the two-engine baseline's performance cost (Model Catalogue v0.9 §3.9.a) — the engine fails the §0.6 maturity criterion; the Aiden-recipe source-rebuild precedent applies if it matures.
>
> **v4.14 (2026-08-06, from the first live §1.5 pass — SECTION PASSED on 26.07-py3):** Step 3 rewritten as a **long-probe** (2,000-token generation + one-per-second `nvidia-smi` power/util/clocks readout) — the old "hello" completed too fast to observe GPU load (operator finding). New NOTE with three verified log signatures: compat-UNAVAILABLE banner = non-blocking on this platform (judge by function); uncalibrated fp8-KV scaling warning = the reason for the Part C quality gate; generation_config.json sampling override = pin sampling for measured runs. Reference values from the pass: weights 58 s, cold start ~1 m 53 s (compile cache reused), 8.54 GiB weights + 50.84 GiB KV + 1.32 GiB graphs ≈ the 0.5 budget, 832,880-token KV pool.
>
> > **v4.13 (2026-08-05, two more live WP1 findings):** §1.5 — (1) xet kill-switch made permanent via ~/.bashrc (per-shell exports get forgotten; "Reconstructing" in a progress bar = xet still active); (2) sudo'd containers leave root-owned files in the mounted HF cache that later block host-side downloads with PermissionError on .locks — remedy `sudo chown -R $USER: ~/.cache/huggingface`.
>
> > **v4.12 (2026-08-05, LIVE WP1 FINDING — first real §1.5 execution):** the §2.9 "xet is broken on ARM64" lesson applies to ALL containerised HF downloads, not just Unsloth: the NGC vLLM container's weight download wedged silently ~26 min then failed with `CAS Client Error / error decoding response body` (xet backend). Fix baked in: `-e HF_HUB_DISABLE_XET=1` added to every HF-downloading docker run block (4 blocks); §3.c gains the failure signature; §1.5 now recommends host-side pre-download (`hf download`) so containers load from the mounted cache. Also validated live in this session: `vllm serve` entrypoint on 26.07-py3, fp8 KV auto-default, the CUDA forward-compat driver bridge on the 580.x hold, and the named-container `-it` habit after a Ctrl-C-orphaned container held port 8000.
>
> > **v4.11 (2026-08-05):** architecture figure redrawn for call-flow clarity — the SERVING stack is now layered (UI → retrieval services → generation → data) with the RAG call chain numbered 1–5 (question → embed → search → rerank → answer), the UPDATE pipeline lettered a–d strictly sequential ending in the Qdrant upsert, Spark-2's API call routed visibly to the answer LLM, and the internet pulls marked host-level. Same file name; the Word export embeds the new version.
>
> > **v4.10 (2026-08-05, per PoC-lead request):** §0.4 gains the one-picture **WP1 architecture figure** (`Project42_WP1_Architecture.png`, styled after the JEDI diagram): Spark-1's mode-exclusive SERVING/UPDATE stacks with ports, Qdrant spanning both modes, the mode-switch scripts, Spark-2's client role, and the internet sources that the enclave later replaces with Artifactory. md2docx extended to embed images in the Word export.
>
> > **v4.9 (2026-08-05, operator confusion resolved with a checked answer):** §1.5 Step 1 now *explains* what an image tag is (year.month monthly releases) and *answers* it concretely: newest NGC tag = `26.07-py3` (2026-07-27), previous `26.06-py3`; decision rule = pull newest → smoke test validates → fall back one tag on misbehaviour → pin what passes; NGC tag-list URL added for the day-of re-check; playbook launch form `vllm serve` re-confirmed 2026-08-05; §1.5 run block now uses the concrete tag instead of a placeholder.
>
> > **v4.8 (2026-08-05):** §1.5 Step 1 now carries the vLLM playbook links directly (build.nvidia.com/spark/vllm + GitHub mirror) instead of only pointing at §2.1 — per the v2.1 rule: an instruction to check something must include where.
>
> > **v4.7 (2026-08-05, operator-reported trap):** §0.8 now documents the **placeholder convention** (`<...>` = replace whole thing, never type the brackets — the shell reads them as redirection, hence the misleading `No such file or directory`); §1.5's entrypoint check now shows pull-then-inspect with a concrete real-tag example (`docker inspect` needs the image locally — it fails before the pull).
>
> > **v4.6 (2026-08-05, third external review triaged — 3 adopted, 2 adapted, 1 REJECTED with test evidence):** ADOPTED (High): §2.1.A example `--gpu-memory-utilization` corrected 0.70 → **0.55** (0.70 busts the runbook's own ≤0.75 co-resident budget — a real self-contradiction, reviewer right); §2.1.B gains the **strict sequential-execution mandate** for UPDATE-mode stages (one stage at a time, teardown + cache drop between — parallel VL+ColQwen can exceed the pool); `kb-mode-serve.sh` answer-LLM restore is now **engine-aware** (vllm-llm container → docker start; else llama-server.service → systemctl; else explicit operator note). ADAPTED: §1.5 gains the deterministic `docker inspect --format Entrypoint/Cmd` check before first launch (+ the classic `python3 -m vllm.entrypoints.openai.api_server` last-resort) — replaces try-and-see; §1.4 huggingface-cli claim scoped ("no longer works" = huggingface_hub 1.x, which is what this runbook installs; pre-1.0 installs still carry it — reviewer's counter-claim true only there). REJECTED: the §1.1 "word-splitting breaks multi-word commands" finding — demonstrably false: the loop deliberately relies on unquoted `$CMD` expansion, and the capture was tested end-to-end before adoption (v1.3) with multi-word commands (`date -u`, `cat /etc/os-release`, `head -n 20 /proc/meminfo`) executing correctly, arguments intact; the review's proposed `eval`-based rewrite adds risk (shell-injection surface) for no gain.
>
> > **v4.5 (2026-08-05, educational pass per PoC-lead direction):** full audit against the standing rule "every technical term explained in plain language at first use", document-wide. **71 inline fixes at first use, covering ~100 terms** (among them: token/tok-s, MoE vs dense, OOM, CUDA, quantisation and the format names, context window, KV cache, prefill vs decode, TTFT, acceptance rate, API/endpoint/port/localhost, chat template & tool calling, thinking mode, MCP forward-pointer at §2.2, harness/M42, agent, WP/gate/MVP/PoC/ladder, SKU/OEM/UEFI/Secure Boot, SHA-256, JSON/JSONL, REST, environment variable, Ray, llama.cpp RPC, pipeline parallelism, BM25/hybrid search/golden set, RRF context, CI, IDE/VSIX, SDK, CLI, cgroup, GPU-"kernels" disambiguated in §2.8.a, pp/tg, p95, YaRN, enclave/air-gap/Artifactory, upsert/payload/chunk, JupyterLab, SDPA/attention, xet, smoke test, repository senses, headless). New **Annex B — AI & serving concepts: plain-language glossary** (79 entries) added after Annex A and cross-referenced from §0.8 (read A for commands, B for concepts). §0.8-discipline sweep: one fix — §1.0's dongle-usage CAUTION (the three anti-bricking rules) moved ABOVE the steps it protects (it sat after step 6); §0.8's migration note now includes Annex B. No command, pin, URL, flag, model name or warning content changed; changelog entries and STEP RECORDs left verbatim.
>
> **v4.4 (2026-08-05, V4-Flash-0731 drop adopted):** DeepSeek released **V4-Flash-0731** (2026-07-31; facts verified 2026-08-05): same architecture, but a retraining pass massively improved agentic capability (DeepSWE 7.3→54.4, Cybergym 38.7→76.7) — **0731 is now the target checkpoint** for every V4-Flash route. §2.8.a step 2 pins updated: the 1M-variant recipe moved to `tonyd2wild/DeepSeek-v4-Flash-0731-DSpark-1M-NVFP4-KV-2x-DGX-Spark`; `MiaAI-Lab/DeepSeek-v4-Flash-DSpark-2x-DGX-Spark` (0731 DSpark) added as an alternative recipe; the plain-TP=2 quality-first target (`tonyd2wild/deepseek-v4-flash-dgx-spark`) and the harden-the-pins rule are unchanged. Step 5 quality gate kept intact but re-keyed: the old DSpark quality flag was measured on the **pre-0731** checkpoint — **re-measure on 0731**, do not carry the flag forward blindly. §3.a: cluster-path V4-Flash row retargeted to 0731; **new llama.cpp GGUF row** — frontier-class on **ONE** Spark via the Unsloth 0731 GGUF (UD-IQ2_M ~85 GiB / UD-IQ3_XXS ~97 GiB): community-measured ~16–17 tok/s decode / ~400–450 tok/s prefill, ctx 131,072 booted, 6/6 tool-calling spot-check, but ~6.5-min model load (page-cache contention), no speculative-decode support in llama.cpp, and a 2–3-bit quant is borderline vs the quality-first policy ⇒ candidate, Part C first, P2. Sizing note: 0731 sources corroborate **284B total / 13B active** — the very figure an earlier external review claimed and we rejected; the rejection is **formally reversed** in Model Catalogue v0.8 §4.2 ("corroborated, verify on box"). Sources: https://dev.classmethod.jp/en/articles/dgx-spark-deepseek-v4-flash-0731-llama-cpp/ · https://dev.classmethod.jp/en/articles/dgx-spark-2node-deepseek-v4-flash-dspark/ · https://github.com/tonyd2wild/DeepSeek-v4-Flash-0731-DSpark-1M-NVFP4-KV-2x-DGX-Spark · https://github.com/MiaAI-Lab/DeepSeek-v4-Flash-DSpark-2x-DGX-Spark
>
> **v4.3 (2026-08-04, reviewer challenge to the v4.2 spec-decode rejection — upheld in part, rejection revised):** the "gated default" reframing is adopted: v4.2 conflated *default* with *unvalidated*. New **§0.6 speculative-decoding policy**: spec-decode is the required target profile for every §3.a primary interactive model; mandatory per-model Part C gate (drafter repo-pinned + quantisation-matched; acceptance ≥ 60 % AND net decode speedup AND clean §3.a.1 template smoke test with drafter active) → pass = drafter in the recorded baseline flag set, fail/not-yet-run = non-speculative serving, deviation logged. Part C spec-decode row upgraded to MANDATORY; §4 exit checklist gains the per-model gate item; §2.1.A note aligned. Retained guardrails: the gate lives in Part C (the §1.5 smoke test stays minimal), and the gate is dual-criterion (acceptance alone can mask a TTFT regression). Conceded: properly-implemented speculative decoding is lossless (output distribution preserved) — the risk is implementation bugs, hence the template-smoke-test criterion.
>
> > **v4.2 (2026-08-04, second external review triaged — 2 adopted, 2 adapted, 1 already done, 1 rejected):** ADOPTED: `--kv-cache-dtype fp8` as standing default for all vLLM launches (§2.1.A, Part-C quality spot-check gate; llama.cpp keeps its ≥q8_0 KV rule); vLLM `/metrics` Prometheus endpoint as the §1.7 early-warning source (the review's `--dispatch-key prometheus` flag does not exist — metrics are on by default at `/metrics`). ADAPTED: RRF noted as the hybrid-fusion tuning knob, golden-set-validated (§2.1.A(d)); NemoClaw/OpenShell verified REAL (Apache-2.0, DGX Spark, sandbox+network-policy) but supports only OpenClaw/Hermes/LangChain agents — not our set — so §2.6 watchlist, re-check at G2. ALREADY DONE in v4.1: pgrep ingestion guard + readiness retry loop. REJECTED: speculative decoding by default in baseline recipes — contradicts the Part C method (drafters must be measured, acceptance-rate recorded; base drafters degrade; the review's `--speculative-model` flag form is also deprecated) — spec-decode enters a recipe only after its Part C validation.
>
> > **v4.1 (2026-08-04, independent review of the v4.0 KB baseline applied):** six reviewer fixes, no design change. (1) §1.5 Step 1 and §2.1.A(a) primary vLLM launch commands now use the NGC-standard **`vllm serve <model> <flags>` subcommand form**; the VERIFY note inverted accordingly (if the chosen tag's entrypoint already wraps vllm, the bare-flags `--model ...` form may be needed instead — record which works). (2) §2.1.A(d): plain-language caveat on `--add-host=host.docker.internal:host-gateway` — needs Docker v20.10+ (DGX OS ships newer, fine), can be blocked by restrictive iptables/ufw firewall configs; fallback = the Spark's LAN IP. (3) `kb-mode-serve.sh` now **detects foreground ingestion jobs** (`pgrep -f` on docling/colpali) before stopping containers, with an operator terminate/abort prompt — `docker stop` cannot see foreground terminal jobs. (4) `kb-mode-serve.sh` readiness: the fixed `sleep 10` replaced by a **retry loop** (probe `/v1/models` every 3 s, up to 30 tries ≈ 90 s — large 120B-class models can take 45–90 s to load), with the warning pointing at `docker logs vllm-llm` / the llama-server logs. (5) Both script-creation heredocs confirmed on the quoted `<<'EOF'` delimiter; the step text now spells out why the quotes matter (your shell must not expand `$variables` at write time — they expand later, when the script runs). (6) Master progress checklist § cells are now **links to their section anchors** (derived from the current headings per GitHub anchor rules; all 21 verified against the real headings).
>
> **v4.0 (2026-08-04, per PoC-lead decision — KB architecture change):** the KB (§2.1) baseline changes from the 2-Spark split (Spark-1 serving / Spark-2 ingestion) to a **single-Spark, mode-exclusive design on Spark-1**: the KB is always in exactly one of two modes — **SERVING** (answer LLM + BGE-M3 + reranker + Qdrant + Open WebUI; ~80 GB, comfortable) or **UPDATE** (KB offline in an announced maintenance window; answer LLM torn down; Docling + Qwen2.5-VL + ColQwen2.5 get the whole pool; Qdrant stays up in both modes). This removes bandwidth contention and co-residency OOM risk *by construction*, matches document-baseline configuration management (serving baseline N / updating to baseline N+1), and **frees Spark-2 for the client/benchmark/notebook/fine-tune tracks**. New in §2.1: "The two modes" intro table; **mandatory Qdrant snapshot before every update** (REST snapshot API, restore path documented); two commented mode-switch scripts **`/opt/p42/bin/kb-mode-update.sh`** and **`/opt/p42/bin/kb-mode-serve.sh`** (create, chmod +x, rehearse once in 2.1.C); 2.1.B retitled to "(Spark-1, UPDATE mode)" with vectors upserted to `localhost`. The old 2-Spark split stays documented as a fallback (topology confirmed at G2). Cross-reference sweep: §0.4 role-split table, master checklist row 2.1, §1.6 labels + port table, §3.b 8002 row (now "Spark-1 (UPDATE mode only)"), §1.7/§2.1 memory-budget wording. No command, pin, URL, flag, model name or warning dropped.
>
> **v3.4 (2026-08-04, found during execution):** §1.4 Step 3 now details obtaining the HF token (project account → Settings → Access Tokens → Read-type token, shown once, password store) and the gated-model licence-acceptance extra step.
>
> > **v3.3 (2026-08-04, found during execution):** §1.3 Step 4 — `/etc/docker/daemon.json` may legitimately not exist on current DGX OS (toolkit registers via CDI/defaults); check replaced with `docker info \| grep -iA3 runtime`, with the decision rule "Step 2 passed = stack proven regardless" and the `nvidia-ctk runtime configure` remedy only for the Step-2-failed case.
>
> > **v3.2 (2026-08-04, clarity gap found during execution):** §1.3 Step 1 now explains group-membership persistence — groups are read at login, so `usermod -aG docker` becomes permanent only after a full logout/login (SSH reconnect / desktop re-login), while `newgrp docker` is a current-shell-only stop-gap; other shells needing `sudo docker` until re-login is expected. Added `id -nG` verification. No command changed.
>
> > **v3.1 (2026-08-04, clarity gap found during execution):** §1.3 Step 2 now explains what `docker run` actually does before you run it — pull = a DOWNLOAD from NVIDIA's registry (nothing is uploaded), what the CUDA image contains (mini Ubuntu 24.04 + CUDA toolkit), that this container is a throwaway probe that runs one appended command (`nvidia-smi`) and exits leaving only the cached image, and what `-it`/`--gpus=all` mean. No command changed.
>
> > **v3.0 (2026-08-04, per PoC-lead direction):** **Part B (§2.1–§2.10) migrated to the §0.8 step anatomy** — every section is now numbered steps of the form Why → **Before you run it** (all pre-existing WARNING/CAUTION/IMPORTANT/NOTE/VERIFY content moved BEFORE the commands it concerns) → Run → Expect / If not; choices are explicit **DECISION** steps with the decision rule inline; each section's Teardown is now its final ☐ step. **New global rule, applied document-wide (Part A included):** every runnable command appears in its own standalone grey command box (fenced code block) — Part A's inline Run-line commands and other inline instruction sequences moved into fenced blocks accordingly. No technical content changed — no fact, URL, version pin, flag, model name or warning was added, dropped or altered.
>
> **v2.2 (2026-08-04, deep-dive on EC firmware status — user found no "safe list" on the forum; correct, none exists):** §1.2 Step 7's decision is now keyed to the **unit's own EC version** instead of a vague forum check: 0x02-series (`0x02004e18` = known-good) → never run `fwupdmgr upgrade` (0x0300-series `0x03000302` = confirmed-broken fan curve; newer `0x03000508` of 2026-07-15 has NO confirmed fix and no NVIDIA statement); already-0x0300 → idle baseline decides (healthy → keep+monitor; ≥45–50 °C → community-validated rollback to `0x02004e18`, exact fwupdmgr sequence given, logged as deviation). Added the distinct **failed-USB-Type-C-firmware twin** (hot idle right after an update; fix = 30-min full power-off) so it is not mistaken for the EC bug. Sources: forum threads #377069 (rollback), #376890 (0x03000508 release), #377044 (symptoms+NVIDIA escalation), #378028 (Type-C case).
>
> **v2.1 (2026-08-04, gap found during execution):** §1.2 Step 7's "check the forum's thermal threads" now carries the actual links (rollback-fix thread #377069 = the current-EC-status reference; symptom thread #377044; thermal-status thread #351345) plus the generic re-check recipe (search "EC firmware" in the DGX Spark / GB10 category, sort by latest). Format rule reinforced: an instruction to check something must include where.
>
> **v2.0 FORMAT OVERHAUL of Part A (2026-08-04, per PoC-lead feedback during execution):** the caution-after-commands layout failed in practice (the §1.2 kernel/module check sat *after* the commands that trigger the problem). Part A (§1.1–§1.7) rewritten to the **§0.8 step anatomy**: numbered steps, each = Why → **Before you run it** (ALL warnings and decision rules BEFORE the commands) → Run → Expect / If not (explicit per-failure actions); DECISION steps carry their decision rule inline (§1.2 Step 3 kernel/module check, §1.2 Step 7 firmware go/no-go, §1.3 Step 3 NGC-login fallback). **No prior knowledge assumed — every term now explained at first use** (kernel, driver, module, firmware, EC, UEFI, DKMS, container, venv, swap, page cache, OOM, PSI, port…). Content additions in the rewrite: §1.5 gains an explicit teardown step; §1.6 gains a DHCP caveat and the `ss -tlnp` diagnostic; §1.2 folds the v1.4 temperature TIP into the step flow (baseline BEFORE the firmware decision). §1.0/§1.2.a were already stepwise — unchanged. **Part B NOT yet migrated** (interim rule in §0.8: read Part B caution boxes in full before running its commands); migrate after Part A format is validated in use.
>
> **v1.5 addition (2026-08-04, per PoC-lead request — learning objective):** new **Annex A — Linux command primer**: every shell command and construct used anywhere in this runbook, explained in one plain-language line each, grouped as A.1 how-to-read-a-command-line (pipes, redirection, variables, `$(…)`, loops…), A.2 files & text, A.3 system inspection, A.4 software installation, A.5 processes & sessions, A.6 project-specific tools; closing TIP: `man`/`--help` + narrate-before-running habit. Reference only — no STEP RECORD, no checklist row.
>
> **v1.4 change (2026-08-04, gap found during execution):** §1.2 gains a **"How to verify idle temperature" TIP** — the firmware caution demanded the check but never said how. Procedure: true-idle preconditions → read all thermal zones (`/sys/class/thermal` one-liner, in °C) + the `nvidia-smi` GPU sensor (lm-sensors optional) → interpret against the baseline (GPU idle ≈ 30–35 °C healthy; CPU sensor ~10–15 °C hotter is normal; like-for-like comparison; ≥45–50 °C idle = STOP, check EC version) → record per-sensor values + EC/UEFI versions in the §1.2 STEP RECORD (= the §3.d thermal-baseline line).
>
> **v1.3 change (2026-08-04, per PoC-lead request during execution):** §1.1 box-state capture consolidated into a **single one-shot command** that runs all the individual checks (plus the VERIFY-box version records `docker version`/`nvidia-ctk --version` and the §1.0 `dmidecode` SKU/serial check), separates each output with a banner, and saves to `~/p42/boxstate-<hostname>-<date>.txt` per machine — the file is the birth certificate; its path goes in the §1.1 STEP RECORD. The per-command expectations moved into a reference table. Syntax of the one-liner tested before adoption.
>
> **v1.2 correction (2026-08-04, found during execution):** §1.0 step 2 recovery-image URL corrected — NVIDIA's User Guide "System Recovery" section now links to the public page **https://www.nvidia.com/en-us/drivers/dgx-spark-recovery-software/** (serves `dgx-spark-recovery-image-1.135.34.tar.gz`, ~5.5 GB, released 2026-05-31); the old developer.nvidia.com download path in earlier versions is superseded. §1.1 recovery WARNING now points at §1.0 step 2 instead of repeating a URL. Same fix applied to Golden-Image How-To (→ v0.4), which also had a stale version number (1.120.38). Everything else in §1.0 (scripts, ≥16 GB stick, Esc/Del → Boot Override procedure) re-checked against the official System Recovery page — matches.
>
> **v1.1 changes (from v1.0, 2026-08-04, per PoC-lead direction):** new **§1.2.a Workstation tools** — the runbook is now followed and FILLED on the Spark itself, so the on-box working environment is installed right after the OS update: **Google Chrome** (official ARM64 Linux build, new Q2 2026, forum-confirmed on Spark; official `.deb` + Google apt repo only), **Terminator + tmux** (split panes; SSH-surviving sessions for long pulls; kitty as alternative), **VS Code** (official Microsoft arm64 `.deb` — markdown preview for filling this runbook, and the future Cline host per §2.2), optional **glow** (Charm signed repo) for reading the runbook over SSH; plus the step that copies the runbook onto the box as `buildlog-<hostname>.md` and back-fills §1.0–§1.2. Enclave note added: Ubuntu-repo packages already mirrorable; Google/Microsoft/Charm repos would be new Mirror List rows if kept at G2 (VS Code = likely keeper). Master checklist gains the 1.2.a row.
>
> **v1.0 QA pass (2026-08-04, same day — no technical content changed):** final pre-run consistency sweep. Fixed stale ranges and labels (At-a-glance now §1.0–1.7 / §2.1–2.10; master checklist row 1.6 relabelled to what §1.6 actually is, row 2.3–2.7 now covers all remaining Part B tracks, KB row corrected to A–D); §1.1 day-one policy now points to §1.0 instead of repeating it (Secure-Boot *Custom*-mode nuance moved into §1.0 step 5); port story clarified everywhere (8000 = a single slot, one engine at a time; 8001 = the optional always-on llama-server service — now listed in both port tables); §3.a retagged v1.0 with an explicit division of labour vs the Model Catalogue v0.7 (incl. the Qwen3-Coder-Next gating note); §2.8 step 5 cross-references trap 5 (`launch-cluster.sh`, never hand-rolled launches); footer/version strings updated; companion-document list completed; cosmetic fence clean-up.
>
> **v1.0 EXECUTION EDITION (2026-08-04, pre-run refresh + format change):** (1) **Re-verified against the live forums before execution:** the 580.x driver hold is RE-CONFIRMED (NVIDIA staff, June-release thread: "590 drivers are not yet supported on DGX Spark"; a 595.x/CUDA 13.2 *beta* pipeline exists — beta, do not use); EC-firmware/thermal issues remain open upstream — §1.2 cautions stand; §3.c gains the community's new **power-state failure taxonomy** (30W PD safety mode = RMA · 100W thermal cap = cooling · 5W = stale-driver bug, with the one-line `nvidia-smi` detection command). (2) **Format: fillable execution edition** — master progress checklist up front; every executable section now ends with a **📋 STEP RECORD** (done/operator/date/machine/values) whose completed set constitutes the build log. (3) **New §1.0: create and TEST the recovery dongle** — the concrete steps folded in from the Golden-Image USB How-To v0.3 §2, now the first hands-on action of the run (also closes the pending WP1-exit pointer: §4 gains the reset-kit item).
>
> **v0.14 changes (from v0.13, 2026-07-23, per PoC-lead direction):** §2.2 client set restructured — **Cline confirmed as the interactive IDE client** (native MCP client → flagship consumer of the §2.10 `p42-kb` server; human-approval loop framed as a reviewability feature, not a defect; enclave provisioning via pinned VSIX from the `cline/cline` GitHub mirror); **pi coding agent added for WP1 evaluation** as a candidate M42 harness (MIT, npm, llama.cpp-first, headless JSON mode + JSONL session logs — benchmark-friendly instrumentation; no built-in MCP); §2.10 client-support list updated accordingly. Companions: Benchmark Strategy v0.5 (harness-candidate rules), Mirror List v0.13 (npm remote #17, cline/pi-mono GitHub allowlist).
>
> **v0.13 changes (from v0.12, 2026-07-23):** new **§2.10 KB↔agent bridge via MCP** (user-raised gap) — WP1 spike for a custom `p42-kb` MCP server wrapping our own hybrid retrieval (NOT raw Qdrant exposure), consumed natively by OpenHands and Open WebUI; aider has no native MCP client (context via conventions files); **M42 benchmark parity rule** (KB tools identically on/off across harnesses; baseline = OFF); security posture (no public-registry MCP servers; tool descriptions are a prompt-injection surface, project-controlled). Mirror List v0.12 adds `mcp`/`fastmcp` (+ `mcp-server-qdrant` reference-only) to the PyPI allowlist.
>
> **v0.12 changes (from v0.11) — Technical Review & Fact-Check Report adoptions (2026-07-22):** §2.1(a) gains an optional **systemd `ExecStartPre` drop-cache hook** for an always-on llama-server (automates the §1.7 habit; Docker containers keep the procedural pairing); §2.1.A(e) pandoc route now stages the **approved corporate Word template** at `/opt/p42/templates/airbus_corporate_template.docx` as a pinned artefact. The report's four "critical findings" match content already present since v0.11 (kernel/driver trap, EC 0x0300, silent-chatml fallback, V4-Flash cluster gotchas) — no changes needed there.
>
> **v0.11 changes (from v0.10) — robustness sweep (forums + issue trackers, verified 2026-07-22):** new **§3.a.1 chat-template & tool-calling known issues** — the Qwen-family template problem is systemic (minja can't parse the stock templates → **silent chatml fallback**; developer-role crash; thinking-mode tool-call interleaving; the llama-server arguments-as-object OpenAI-compat regression; DeepSeek DSML parser edge cases fixed by vLLM PR #41241) with per-model fixes and a **mandatory 3-turn template smoke test**; §1.2 gains the kernel-without-NVIDIA-module apt trap (no DKMS on ARM64) and the **EC 0x0300 fan-curve firmware regression** (do not blindly `fwupdmgr upgrade`; idle-temp health check); §2.1(a) llama.cpp build fallback `-DGGML_NATIVE=OFF` (#18425 class); §2.8 trap 5: the NCCL all-reduce deadlock is a launch-method problem — use `launch-cluster.sh`, never bare `--nnodes` (+ Ubuntu 25.10 unsupported); §3.c gains 4 new failure signatures (silent chatml fallback, FastAPI 500 after updates, garbled TP=2 on unpinned images, thermal power-off); §3.d gains template-smoke-test + thermal-baseline checks.
>
> **v0.10 changes (from v0.9):** new **§2.8.a** — source-rebuild route for the "Aiden-recipe"-class V4-Flash cluster serving (pinned `b12x` from PyPI + `tonyd2wild` recipe repos, hardened pins, reference numbers, quality gate; see Model Catalogue §3.2.a); new **Part C.2** — the community-comparable **llama-benchy** baseline is now a mandatory once-per-serving-config measurement with the forum-standard flag set, JSONs filed in the build log as the enclave acceptance reference (air-gap §10.3 compares against them).
>
> **v0.9 changes (from v0.8):** NGC access clarified (web-checked 2026-07-21): the `nvcr.io/nvidia/*` images used are NGC **free public tier** — no NVIDIA AI Enterprise entitlement or paid subscription; §1.3 gains a fallback `docker login nvcr.io` note (`$oauthtoken` + free NGC API key) in case a pull returns 401/403. Companion Mirror List v0.7 and Air-Gap Runbook v0.3 carry the Artifactory-side resolution.
>
> **v0.8 changes (from v0.7):** independent-review fixes (2026-07-16): Golden Rule cross-reference corrected (logging is Rule 5 since v0.4 renumbering); §1.1 now captures `/etc/apt/sources.list.d/` (the air-gap build needs it); §1.4 leads with the uv install route (bare `pip install` hits Ubuntu 24.04's externally-managed-environment block); colpali pin aligned to `>0.3.1`; Part C memory-measurement cell now uses Spark-aware tools per §1.7; §2.1.A(a) gains the **total vLLM memory budget rule** (all instances together ≤ ~0.75 co-resident) and an NGC-entrypoint VERIFY (`vllm serve` vs bare flags).
>
> **v0.7 changes (from v0.6):** §3.a gains the missing **two-Spark cluster path** model table (what the 256 GB pair is actually for): big open coding models for the software-development quality-ceiling assessment — Qwen3-Coder-480B-A35B (quantized, llama.cpp RPC), DeepSeek-V4-Flash (2-Spark spec-decode variant), GLM-4.7-Flash / MiniMax-M2.x-AWQ class (eugr-validated) — all Part-C/§2.8-gated candidates. §2.8 purpose sharpened: the cluster experiment now explicitly feeds the coding-benchmark ceiling config (does a ~480B-class coder write materially better new code than the single-box 30B?), which in turn feeds the 2027 hardware recommendation. Companion change: coding benchmark strategy v0.2 adds greenfield C and Python-tooling task families.
>
> **v0.6 changes (from v0.5):** §3.a upgraded from a model shopping list to a **model selection & download matrix**: every model carries its exact repo, quant format per engine, and a validation tag ([NV] NVIDIA verified matrix/playbook · [C] canonical GB10 community measurement · [P] arch-agnostic, validated in WP1); GGUF sources pinned (`ggml-org/gpt-oss-*-GGUF` — the repos behind the canonical benchmarks; `unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF` Q8_0); provenance rule added (nvidia/ and ggml-org/ preferred, no unpinned third-party quants); community-meta candidates (Nemotron-3-Nano-30B-A3B, Qwen3.6-35B-A3B+DFlash) listed as Part-C-first candidates; spec-decode drafters selected during Part C, never guessed.
>
> **v0.5 changes (from v0.4):** serving-engine policy formalised (§0.6) against the project's ordered criteria — **proven maturity (per community) > quality of outputs > performance**. Result: baseline = **NGC vLLM** (measured/concurrent/NVFP4) + **llama.cpp** (single-user GGUF); **Ollama removed from the box entirely** (fails quality: silent default-context truncation, auto-selected quants — and community-measured underperformance); **LM Studio evaluated and excluded from the baseline** (same llama.cpp engine under a closed-source GUI wrapper — adds accessibility, not capability; optional laptop-side only). §1.5 smoke test rewritten to run on the NGC vLLM container (one less install path); all Ollama references, ports and teardowns purged.
>
> **v0.4 changes (from v0.3):** community lessons baselined from `Project42_DGXSpark_Community_KnowHow.md` (forum + community-repo sweep, 2026-07-14): first-boot/recovery survival rules and SSH-first policy (§1.1); safe update path, no-generic-CUDA-repo warning and **driver hold at 580.x** (§1.2); new **§1.7 unified-memory discipline** (OOM = system hang, not an error) + Spark-aware monitoring; **Ollama demoted to smoke-test-only** — llama.cpp (121a build + flag set) is now the single-user serving route and NGC vLLM the measured/concurrent route (§1.5, §2.1); vLLM co-resident memory setting corrected 0.9 → **0.6–0.75** plus `--moe-backend marlin`, `--ipc=host`, ulimits, eager/fastsafetensors notes (§2.1); Part C gains canonical reference numbers, a speculative-decoding measurement and a concurrency sweep; §2.8 clustering gains the NCCL both-RoCE-halves rule, PyTorch 2.9.1 pin/eager workaround and TCP-is-slow-is-normal note; new **§2.9 Unsloth fine-tuning spike** (patched-container route). All sourced in the Know-How compendium.
>
> **v0.3 changes (from v0.2):** technical core re-verified against live official sources on 2026-07-10 (docs.nvidia.com, NGC, Hugging Face, vLLM/Qdrant/Open WebUI/Docling/Tabby/OpenHands docs). Corrections: `hf auth login`/`hf auth whoami` (not `hf login`/`hf whoami`; `huggingface-cli` no longer works); vLLM embeddings now use `--runner pooling` (`--task embed` deprecated); Qwen2.5-VL does not need `--trust-remote-code`; correct HF handles `nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-NVFP4` and `Qwen/Qwen3-Coder-Next` (no "Qwen3-Coder-80B"); `vllm/vllm-openai:latest` is now multi-arch (warning softened); Tabby has NO arm64 GPU image (confirmed, not just unverified) — HTTP-connector route promoted to mainline; OpenHands sandbox renamed to agent-server with arm64 published; Onyx stack is Postgres+OpenSearch (not Vespa) and its dev compose needs the base file; tok/s figures corrected to measured ranges (gpt-oss-120b ~35–60 depending on engine/tuning; the "89 tok/s MoE" figure was a speculative-decoding result); clustering can be *faster* with vLLM TP (the 47-vs-57 regression is llama.cpp-RPC-specific); DAC part and NCCL notes aligned to the official stacking doc. Also added §2.1.A(e): Office output rendering layer (pandoc / docxtpl / python-docx / python-pptx) so KB answers export into project Word/PowerPoint templates, with a matching end-to-end TEST item.
>
> **v0.2 changes (from v0.1):** retitled from "RSMA AI Pilot" to **Project 42** and aligned to the PoC plan — this runbook now executes **WP1 (3 Aug – 11 Sep)** and produces its deliverables; added §0.5 mapping of setup tracks to the MVP portfolio; added Golden Rule 4 (log everything); added **Part C — hardware benchmark protocol** (WP1.3 deliverable, feeds G1 scoring); added **Part D — familiarisation sessions & discipline sandboxes** (WP1.4); added §2.7 **data & log analysis** track (needed by FV/GNC/DB seed MVPs); clustering renumbered to §2.8; added WP1 exit checklist (§4). Technical commands unchanged from v0.1 except where marked.

</details>

---

*End of runbook — v4.29 EXECUTION EDITION (2026-08-08). Airbus — internal working draft; driver/forum baseline re-verified 2026-08-04; technical core re-verified against live official sources 2026-07-10; community lessons baselined 2026-07-14 (sources: `Project42_DGXSpark_Community_KnowHow.md`). Verify all flagged items on-box before the production rebuild. Companion to the Project 42 PoC Plan.*

---

# 2.2 Campaign 2 — the stack this runbook DOES NOT YET BUILD

> **v4.63 (2026-08-13). Read this before rebuilding a box from this runbook.**
>
> **A fresh box built from this runbook produces campaign 1.** Everything in §2.1 is correct and
> current for the campaign-1 stack, and campaign 2 replaced most of it. This runbook contains
> `ingest.py` **v2.7** writing `p42_text` via `kb-manifest.json`, and **zero** mentions of
> `ingest_v3`, `retrieve.py`, `ask_v2.py`, `anchor_sampler.py`, `audit_packet.py`, `gate4_check.py`,
> `corpus_closure.py`, `p42_text_v2` or `p42_text_v3`.
>
> This section is an **inventory, not a build procedure**. It records what exists, where, and at which
> version, so that the gap is visible rather than discovered. Embedding the campaign-2 heredocs is a
> separate, larger task and is **not done**.

## 2.2.1 What campaign 2 replaced

| campaign 1 (in this runbook) | campaign 2 (on the box only) |
|---|---|
| `ingest.py` v2.7 → `p42_text`, 23 documents, 6,226 points | `ingest_v3.py` **v3.3** → `p42_text_v3`, 88 documents, 22,134 points |
| retrieval inline in `ask.py` and the harness | `retrieve.py` — one routing module all clients import (requirement S4) |
| `ask.py` | `ask_v2.py` v2.0 |
| ledger `kb-manifest.json` | ledger **per collection**: `kb-manifest-<collection>.json` |

`p42_text` is **preserved and protected**: it is required by the P6 delivery gate and was built by an
ingest version that no longer exists. `ask.py` and `kb-bench/kb_bench.py` still point at it, correctly.

## 2.2.2 Campaign-2 artefact inventory (all under `~/p42/`)

| file | version | what it is |
|---|---|---|
| `ingest_v3.py` | **v3.3** | campaign-2 ingest. v3.2 added `cut` to the payload; v3.3 keyed the ledger to the target collection |
| `retrieve.py` | v1.0 | routing retrieval module — **the single source of truth**; `--evaluate` measures every query class in one run (standing rule 42) |
| `ask_v2.py` | v2.0 | answer path; defines no collection, resolves via `retrieve.py` |
| `gate4_check.py` | v2.0 | gate 4, ingestion quality |
| `corpus/corpus_closure.py` | v2.0 | typed normative closure, 428-edge graph |
| `anchor_sampler.py` | **v1.1** | anchor draw, 10 strata, 75 self-test assertions |
| `audit_packet.py` | v1.0 | builds and scores the human determinacy audit, 24 assertions |
| `compare_collections.py` | v1.0 | proves a re-ingest changed exactly one thing |
| `rebuild_index.py` | v1.0 | teardown with a protected list and an archived inventory |

**Docs** in `~/p42/docs/`: `P42_Design_Pipeline_and_Benchmark.md` v3.7 · `P42_Lessons_Learned.md` v1.11
· `P42_Anchor_Sampling_Preregistration.md` v1.11 · `P42_Anchor_Audit_Report.md` v1.0 ·
`P42_Index_Rebuild_Record.md` v1.0 · `project42_kb_benchmark.md` (state brief).

## 2.2.3 Rebuilding the campaign-2 index

Services needed: Qdrant `:6333` and BGE-M3 embeddings `:8080`. Captions are **off**, so the VL
container is not needed.

```bash
source ~/p42/ingest-venv/bin/activate
python ~/p42/ingest_v3.py --no-captions --collection p42_text_v3 /home/spark/p42/corpus/pdf
```

**`--no-captions` is not optional** — `kb-ingest-config-*.json` records `captions: false`, and omitting
it adds figure-caption units and changes chunks everywhere. Expect ~25 minutes and **22,134 points**.
Then:

```bash
P42_COLL=p42_text_v3 python ~/p42/gate4_check.py
```

All four checks reproduced their previous values exactly across a full rebuild — see
`P42_Index_Rebuild_Record.md` §4. A different number means the pipeline is not the one those gates
were measured on.

## 2.2.4 Two ingest defects fixed in v3.2 and v3.3 — do not reintroduce them

Both had the same failure mode: **they succeeded**.

1. **`cut` was computed and never written to the payload.** Any consumer keyed on it accepted
   everything silently. Standing rule 51.
2. **The ledger recorded the file, not the (file, collection) pair.** Ingesting an unchanged corpus
   into a *new* collection reported "ingested 0, skipped 88", exit 0, and left an empty index.

If the campaign-2 ingest is ever transcribed into this runbook as a heredoc, both fixes must come with
it, or the next paste reproduces them.

