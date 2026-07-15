"""Similarity primitives for the instance-memory engine.

Each incoming ticket is embedded and compared against a reference set of
previously labeled tickets; the similarity-weighted majority label of the k
nearest references is the prediction. No training, no gradient updates.
"""

from collections import defaultdict


def embed_texts(model_id: str, texts: list[str], batch_size: int = 8,
                max_seq_length: int = 2048):
    import torch
    from sentence_transformers import SentenceTransformer

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = SentenceTransformer(
        model_id, device=device,
        model_kwargs={"torch_dtype": torch.float16} if device == "cuda" else None,
    )
    model.max_seq_length = min(getattr(model, "max_seq_length", max_seq_length),
                               max_seq_length)
    emb = model.encode(texts, normalize_embeddings=True, batch_size=batch_size,
                       show_progress_bar=False)
    del model
    if device == "cuda":
        torch.cuda.empty_cache()
    return emb


def vote(sims_row, labels: list[str], candidate_idx: list[int], k: int) -> str:
    """Similarity-weighted vote among the k most similar candidates."""
    top = sorted(candidate_idx, key=lambda j: -sims_row[j])[:k]
    weight: dict[str, float] = defaultdict(float)
    for j in top:
        weight[labels[j]] += float(sims_row[j])
    return max(sorted(weight), key=lambda lab: weight[lab])


def build_index(memory_path, model_id: str, out_path,
                text_column: str = "conteudo",
                id_column: str = "incidente_id",
                label_column: str = "categoria") -> dict:
    """``train``: embed a labeled CSV once and persist it as a reusable index.

    No gradient updates take place; training the tool means building the
    reference index (embeddings + labels) so later ``classify`` calls skip
    re-embedding the reference set.
    """
    import numpy as np

    from .normalizer import load_incidents

    memory = load_incidents(memory_path, text_column=text_column,
                            id_column=id_column, label_column=label_column)
    emb = embed_texts(model_id, [m.text for m in memory])
    np.savez_compressed(
        out_path,
        embeddings=emb.astype("float16"),
        labels=np.array([m.label for m in memory]),
        ids=np.array([m.incident_id for m in memory]),
        model_id=np.array([model_id]),
    )
    return {"n_references": len(memory), "model_id": model_id, "path": str(out_path)}


def load_index(path):
    """Load a persisted reference index built by build_index."""
    import numpy as np

    data = np.load(path, allow_pickle=False)
    return {
        "embeddings": data["embeddings"].astype("float32"),
        "labels": [str(x) for x in data["labels"]],
        "ids": [str(x) for x in data["ids"]],
        "model_id": str(data["model_id"][0]),
    }
