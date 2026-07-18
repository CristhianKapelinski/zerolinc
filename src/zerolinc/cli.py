"""ZeroLINC command line: train a reference index and classify incident tickets."""

import argparse
from collections import Counter
from pathlib import Path

from .router import DEFAULT_K, DEFAULT_SIM_THRESHOLD, classify_tickets, write_predictions


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="zerolinc",
        description="Training-free local classification of security incident "
                    "reports into the 12 NIST SP 800-61r3-derived categories.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_train = sub.add_parser(
        "train", help="build a persistent reference index from labeled tickets "
                      "(embeddings only; no gradient training)")
    p_train.add_argument("--memory", type=Path, required=True,
                         help="labeled CSV (columns set by --id/text/label-column)")
    p_train.add_argument("--model-out", type=Path, default=Path("zerolinc_index.npz"))
    p_train.add_argument("--text-column", default="conteudo")
    p_train.add_argument("--id-column", default="incidente_id")
    p_train.add_argument("--label-column", default="categoria")
    p_train.add_argument("--embedding-model", default="Qwen/Qwen3-Embedding-0.6B")

    p_cls = sub.add_parser("classify", help="classify a CSV of tickets")
    p_cls.add_argument("--input", type=Path, required=True, help="CSV with ticket texts")
    p_cls.add_argument("--model", type=Path, default=None,
                       help="trained reference index (from 'zerolinc train')")
    p_cls.add_argument("--memory", type=Path, default=None,
                       help="labeled CSV used directly as reference set")
    p_cls.add_argument("--engine",
                       choices=("auto", "zeroshot", "zeroshot-max", "embed", "rerank", "knn"),
                       default="auto")
    p_cls.add_argument("--k", type=int, default=DEFAULT_K)
    p_cls.add_argument("--sim-threshold", type=float, default=DEFAULT_SIM_THRESHOLD)
    p_cls.add_argument("--text-column", default="conteudo",
                       help="text column of the input CSV (and of --memory)")
    p_cls.add_argument("--id-column", default="incidente_id",
                       help="id column of the input and reference CSVs")
    p_cls.add_argument("--label-column", default="categoria",
                       help="label column of the reference CSV")
    p_cls.add_argument("--batch-size", type=int, default=8)
    p_cls.add_argument("--output", type=Path, default=Path("predictions.csv"))
    p_cls.add_argument("--embedding-model", default="Qwen/Qwen3-Embedding-0.6B",
                       help="embedding checkpoint for --memory runs")

    args = parser.parse_args(argv)

    if args.command == "train":
        from .memory_engine import build_index
        info = build_index(args.memory, args.embedding_model, args.model_out,
                           text_column=args.text_column,
                           id_column=args.id_column,
                           label_column=args.label_column)
        print(f"index built: {info['n_references']} references "
              f"({info['model_id']}) -> {info['path']}")
        return 0

    preds = classify_tickets(args.input, args.memory, args.engine, args.k,
                             args.sim_threshold, args.text_column, args.batch_size,
                             index_path=args.model, id_column=args.id_column,
                             label_column=args.label_column,
                             embed_model=args.embedding_model)
    write_predictions(preds, args.output)
    engines = Counter(p.engine for p in preds)
    cats = Counter(p.category for p in preds)
    print(f"{len(preds)} tickets classified -> {args.output}")
    print(f"engines: {dict(engines)}")
    print(f"categories: {dict(sorted(cats.items()))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
