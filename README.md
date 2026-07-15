# ZeroLINC

Training-free **local** classification of security incident reports (SOC/CSIRT tickets) into the 12 categories derived from NIST SP 800-61r3. No model training, no external API, no incident data leaving your machine.

Two engines, one command:

- **Zero-shot** (day zero, no labeled data): scores each ticket against natural-language category descriptions. Up to **70.9%** accuracy on the evaluation corpus.
- **Instance-memory** (you have labeled tickets): similarity-weighted vote over your own labeled examples. **90.5%** mean test accuracy with 89 labeled references, no training. Tickets dissimilar to every reference fall back to the zero-shot engine automatically.

Runs on a single GPU (under 4 GB VRAM; CPU-only also works, slower) and classifies hundreds of tickets per minute.

## Install

```bash
git clone https://github.com/CristhianKapelinski/zerolinc && cd zerolinc
uv sync
```

## Use

Day zero, no labeled data:

```bash
uv run zerolinc --input tickets.csv --engine zeroshot --output predictions.csv
```

With your labeled tickets as a reference set (recommended once you have a few dozen):

```bash
uv run zerolinc --input tickets.csv --memory labeled.csv --output predictions.csv
```

- `tickets.csv` needs a text column (default name `conteudo`; override with `--text-column`).
- `labeled.csv` needs `incidente_id`, `conteudo`, and `categoria` (CAT1..CAT12) columns.
- Output CSV: `incident_id, category, confidence, engine`.
- `--engine zeroshot-max` swaps the fast zero-shot model for the strongest (slower) one.

Models are downloaded from Hugging Face on first use; set `HF_HUB_CACHE` to control where.

## Architecture

One module per component, matching the paper: `normalizer.py` (tag compression, subject view), `verbalizer.py` (the 12 NIST categories in 8 verbalization sets), `zeroshot_engine.py` (NLI, GLiClass, embedding, and reranker backends behind one interface), `memory_engine.py` (embedding + k-NN vote), `router.py` (per-ticket engine selection with similarity fallback), `cli.py`. Data-flow, module, and sequence diagrams: [docs/architecture.md](docs/architecture.md).

## How it works and how well

The engines, verbalizations, and defaults were selected by a systematic measurement study on 182 expert-labeled CSIRT tickets (292 evaluation runs, validation/test protocol, McNemar significance tests). The full study, run records, and paper live in the companion repository: **[zerolinc-benchmark](https://github.com/CristhianKapelinski/zerolinc-benchmark)**.

## License

[GNU AGPL-3.0](LICENSE).
