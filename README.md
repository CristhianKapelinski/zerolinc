# ZeroLINC — Training-Free Local Classification of Security Incident Reports

ZeroLINC is an open-source classifier that assigns SOC/CSIRT incident tickets to the 12 NIST SP 800-61r3-derived categories locally, with no model training and no external API. Two engines behind one command: an **instance-memory engine** (similarity-weighted vote over previously labeled tickets) that reaches **90.8%** mean test accuracy with 89 labeled references, and a **zero-shot engine** (up to **70.9%**) for deployments with no labeled data. Classifying the whole evaluation corpus takes seconds and under 3 Wh on one GPU. This repository is the artifact of the paper *"ZeroLINC: Training-Free Local Classification of Security Incident Reports"* (SBSeg 2026, Salão de Ferramentas — Código Aberto).

# README structure

[Considered seals](#considered-seals) · [Basic information](#basic-information) · [Dependencies](#dependencies) · [Security concerns](#security-concerns) · [Installation](#installation) · [Minimal test](#minimal-test) · [Experiments](#experiments) (Claims #1–#3) · [LICENSE](#license). Layout: `src/zerolinc/` (one module per architecture component: `normalizer.py`, `verbalizer.py`, `zeroshot_engine.py`, `memory_engine.py`, `router.py`, `cli.py`), `examples/` (sample input), `docs/architecture.md` (data-flow, module, and sequence diagrams), `run_claim{1,2,3}.sh` (one script per paper claim), `tests/`. The measurement study behind the tool lives in the companion repository [zerolinc-benchmark](https://github.com/CristhianKapelinski/zerolinc-benchmark); the claim scripts fetch it automatically.

# Considered seals

Os selos considerados são: **Disponíveis (SeloD), Funcionais (SeloF), Sustentáveis (SeloS) e Reprodutíveis (SeloR)**.

# Basic information

| Component | Requirement |
|---|---|
| OS | Linux x86-64 |
| Runtime | Python ≥ 3.11, managed by `uv` |
| RAM | 16 GB |
| Disk | 15 GB free (model downloads) |
| GPU | optional but recommended: NVIDIA with ≥ 4 GB VRAM (CUDA 12.8 wheels). CPU-only works, slower |

Paper experiments ran on: AMD Ryzen 5 8600G (6 cores), 30 GB RAM, NVIDIA GeForce RTX 5060 Ti (16 GB VRAM), Linux kernel 6.17, Python 3.13, PyTorch 2.11 (cu128), Transformers 5.12.

# Dependencies

All Python dependencies are version-frozen in the committed `uv.lock` (PyTorch 2.11 cu128, Transformers 5.12, Sentence-Transformers 5.6, GLiClass 0.1.18, pandas). No system packages beyond `git`, `curl`, and `uv`. Model checkpoints download automatically from Hugging Face on first use (~2 GB for the default engines); set `HF_HUB_CACHE` to control where. The labeled evaluation corpus ships in the companion benchmark repository, fetched automatically by the claim scripts.

# Security concerns

Everything runs locally: no telemetry, no external API calls (only Hugging Face model downloads on first run), no credentials, no ports opened. Incident data never leaves the machine. The sample and evaluation data are anonymized (sensitive spans replaced by placeholder tags).

# Installation

```bash
git clone https://github.com/CristhianKapelinski/zerolinc
cd zerolinc
curl -LsSf https://astral.sh/uv/install.sh | sh   # if uv is not installed
uv sync                                            # ~3 min
```

# Minimal test

Offline unit tests, then one real zero-shot classification of the bundled sample (~2 min; first run downloads ~0.8 GB):

```bash
uv run pytest -q     # expected: "7 passed" (~10 s, no network)
uv run zerolinc classify --input examples/tickets_sample.csv --engine zeroshot
```

Expected final lines:

```
3 tickets classified -> predictions.csv
engines: {'zeroshot': 3}
categories: {...}
```

# Experiments

The paper makes three claims; each is one command that fetches the evaluation artifact automatically and ends with a result box containing `OK`. No manual steps.

## Claim #1 — Instance-memory engine reaches 90.8% mean test accuracy (main claim)

- **Description:** with 89 labeled reference tickets and no training, the engine reaches 90.8% mean accuracy over 5 validation/test splits (range 89.2–92.5%), McNemar p<0.001 in every split. Runs the full protocol live. GPU fp16 embedding introduces small run-to-run variation (per-seed ±1–2 p.p., mean ±0.5 p.p.); the assertion band 88–93% absorbs it.
- **Execution:** `./run_claim1.sh`
- **Expected time:** ~5 min on GPU (first run: +2 min clone/sync/model download); ~15 min CPU-only
- **Expected resources:** ~4 GB RAM, ~2 GB VRAM (GPU path), ~2 GB disk
- **Expected result:** a box ending in

```
  Mean test accuracy : 90.8%   (paper: 90.8%, range 89.2–92.5%)
  McNemar vs majority: p < 0.001 in all 5 seeds (max p = ...)
  Expected: mean between 88% and 93%, every p < 0.001  →  OK
```

## Claim #2 — Zero-shot engines reach up to 70.9% (protocol mean 68.8%)

- **Description:** recomputes every metric of the 292-run study from committed per-ticket predictions and re-runs the 5-seed selection protocol. No GPU.
- **Execution:** `./run_claim2.sh`
- **Expected time:** ~3 min, CPU only
- **Expected resources:** ~2 GB RAM, ~1 GB disk
- **Expected result (deterministic):** a box ending in

```
  Best single run     : 70.9%  (deberta-v3-large-zeroshot-v2.0__en-desc-kw__subject)
  NLI protocol mean   : 68.8%  (range 66.7–69.9%) over 5 splits
  Majority-class floor: 63.4%
  Expected: best 70.9%, NLI mean 68.8%  →  OK
```

## Claim #3 — The default zero-shot engine costs seconds and under 3 Wh

- **Description:** verifies the cost claim for the default engine over the 182-ticket corpus. Re-timed live when a GPU is present (`SKIP_LIVE=1 ./run_claim3.sh` forces the no-GPU path, which reads the committed run record). Wall-clock varies with hardware; the assertion is < 60 s and < 3 Wh.
- **Execution:** `./run_claim3.sh`
- **Expected time:** ~2 min on GPU; ~1 min no-GPU path
- **Expected resources:** ~4 GB RAM, ~1 GB VRAM (live path)
- **Expected result:** a box reporting wall-clock, Wh, VRAM, and accuracy, ending in `→  OK`

# LICENSE

[GNU AGPL-3.0](LICENSE).
