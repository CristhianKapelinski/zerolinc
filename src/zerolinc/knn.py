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


def _vote(sims_row, labels: list[str], candidate_idx: list[int], k: int) -> str:
    """Similarity-weighted vote among the k most similar candidates."""
    top = sorted(candidate_idx, key=lambda j: -sims_row[j])[:k]
    weight: dict[str, float] = defaultdict(float)
    for j in top:
        weight[labels[j]] += float(sims_row[j])
    return max(sorted(weight), key=lambda lab: weight[lab])
