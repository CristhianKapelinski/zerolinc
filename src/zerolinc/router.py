"""The end-user classification command: CSV of tickets in, categories out.

Two engines, selected by what the user has:

- ``zeroshot`` (day zero, no labeled data): GLiClass scores the ticket against
  the NIST category event hypotheses; fast default. ``zeroshot-max`` swaps in
  the stronger but slower NLI cross-encoder configuration.
- ``knn`` (a labeled reference file exists): similarity-weighted vote of the
  k nearest labeled tickets in embedding space; no training.
- ``auto``: knn when a memory file is given, with per-ticket fallback to the
  zero-shot engine whenever the nearest neighbor is farther than a similarity
  threshold (novel ticket types are not forced onto the memory).
"""

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .normalizer import Incident, load_incidents, normalize_text
from .memory_engine import vote, embed_texts
from .verbalizer import PROMPT_CONFIGS


ZEROSHOT_ENGINES: dict[str, tuple[str, str, str]] = {
    "zeroshot":     ("gliclass:knowledgator/gliclass-modern-base-v3.0", "en-event",   "full"),
    "zeroshot-max": ("nli:MoritzLaurer/deberta-v3-large-zeroshot-v2.0", "en-desc-kw", "subject"),
    "embed":        ("embed:Qwen/Qwen3-Embedding-0.6B",                 "en-event",   "full"),
    "rerank":       ("rerank:Qwen/Qwen3-Reranker-0.6B",                 "en-event",   "subject"),
}
EMBED_MODEL = "Qwen/Qwen3-Embedding-0.6B"
DEFAULT_K = 3
DEFAULT_SIM_THRESHOLD = 0.75


@dataclass(frozen=True)
class ToolPrediction:
    """One ticket's outcome: predicted category, its score, and which engine produced it.

    ``confidence`` is a cosine similarity for the knn engine and a normalized
    entailment/label score for the zero-shot engines; the two are not on the
    same scale. ``engine`` is one of the ``ZEROSHOT_ENGINES`` keys, ``"knn"``,
    or ``"zeroshot-fallback"`` for tickets the auto engine routed away from
    knn.
    """

    incident_id: str
    category: str
    confidence: float
    engine: str


def _load_texts(path: str | Path, text_column: str = "conteudo",
                id_column: str | None = None) -> list[Incident]:
    df = pd.read_csv(path)
    if text_column not in df.columns:
        raise ValueError(f"{path} has no column {text_column!r}")
    candidates = (id_column,) if id_column else ("incidente_id", "id")
    id_col = next((c for c in candidates if c in df.columns), None)
    if id_column and id_col is None:
        raise ValueError(f"{path} has no column {id_column!r}")
    return [
        Incident(
            incident_id=str(row[id_col]) if id_col else str(i),
            text=normalize_text(str(row[text_column])),
            label="",
        )
        for i, row in df.iterrows()
    ]


def _zeroshot(items: list[Incident], engine: str, batch_size: int) -> list[ToolPrediction]:
    from .zeroshot_engine import classify_any
    from .normalizer import subject_view

    spec, config_name, view = ZEROSHOT_ENGINES[engine]
    config = PROMPT_CONFIGS[config_name]
    # each engine uses the input view its configuration was selected with
    texts = [subject_view(i.text) if view == "subject" else i.text for i in items]
    result = classify_any(spec, texts, config, batch_size=batch_size)
    return [
        ToolPrediction(i.incident_id, p, round(s, 4), engine)
        for i, p, s in zip(items, result.predictions, result.top_scores)
    ]


def classify_tickets(
    input_path: str | Path,
    memory_path: str | Path | None = None,
    engine: str = "auto",
    k: int = DEFAULT_K,
    sim_threshold: float = DEFAULT_SIM_THRESHOLD,
    text_column: str = "conteudo",
    batch_size: int = 8,
    index_path: str | Path | None = None,
    id_column: str = "incidente_id",
    label_column: str = "categoria",
    embed_model: str = EMBED_MODEL,
) -> list[ToolPrediction]:
    """Classify a CSV of tickets, dispatching to the requested or auto-selected engine.

    Implements both headline classification paths: the ``knn`` engine votes
    over a reference set built by ``memory_engine`` (Claim #1), and the
    zero-shot engines score each ticket against the category hypotheses
    (Claim #2), with the default ``zeroshot`` engine also the one Claim #3
    times and meters for energy. Under ``engine="auto"``, a ticket falls back
    from knn to the zero-shot engine whenever its nearest reference is
    farther than ``sim_threshold``, so unfamiliar tickets are not forced onto
    the memory. Raises ``ValueError`` if ``engine="knn"`` is requested
    without a ``--memory`` file or a trained ``--model`` index.
    """
    items = _load_texts(input_path, text_column,
                        id_column if id_column != "incidente_id" else None)

    has_refs = bool(memory_path or index_path)
    if engine in ZEROSHOT_ENGINES or (engine == "auto" and not has_refs):
        return _zeroshot(items, engine if engine in ZEROSHOT_ENGINES else "zeroshot", batch_size)

    if not has_refs:
        raise ValueError("engine 'knn' requires --memory or a trained --model index")
    if index_path:
        from .memory_engine import load_index
        index = load_index(index_path)
        mem_labels = index["labels"]
        mem_emb = index["embeddings"]
        item_emb = embed_texts(index["model_id"], [i.text for i in items],
                               batch_size=batch_size)
    else:
        memory = load_incidents(memory_path, text_column=text_column,
                                id_column=id_column, label_column=label_column)
        mem_labels = [m.label for m in memory]
        emb_all = embed_texts(embed_model, [m.text for m in memory]
                              + [i.text for i in items], batch_size=batch_size)
        mem_emb, item_emb = emb_all[: len(memory)], emb_all[len(memory):]
    sims = item_emb @ mem_emb.T

    preds: list[ToolPrediction] = []
    fallback: list[int] = []
    n_mem = len(mem_labels)
    for row_i, item in enumerate(items):
        top_sim = float(sims[row_i].max())
        if engine == "auto" and top_sim < sim_threshold:
            fallback.append(row_i)
            preds.append(None)  # type: ignore[arg-type]
            continue
        label = vote(sims[row_i], mem_labels, list(range(n_mem)), k)
        preds.append(ToolPrediction(item.incident_id, label, round(top_sim, 4), "knn"))

    if fallback:
        zs = _zeroshot([items[j] for j in fallback], "zeroshot", batch_size)
        for j, p in zip(fallback, zs):
            preds[j] = ToolPrediction(p.incident_id, p.category, p.confidence,
                                      "zeroshot-fallback")
    return preds


def write_predictions(preds: list[ToolPrediction], out_path: str | Path) -> None:
    """Write predictions to ``out_path`` as CSV, one row per ``ToolPrediction`` field."""
    pd.DataFrame([p.__dict__ for p in preds]).to_csv(out_path, index=False)
