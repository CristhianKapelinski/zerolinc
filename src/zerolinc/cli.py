"""ZeroLINC command line: classify a CSV of incident tickets into NIST categories."""

import argparse
from collections import Counter
from pathlib import Path

from .tool import classify_tickets, write_predictions


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="zerolinc",
        description="Training-free local classification of security incident "
                    "reports into the 12 NIST SP 800-61r3-derived categories.",
    )
    parser.add_argument("--input", type=Path, required=True, help="CSV with ticket texts")
    parser.add_argument("--memory", type=Path, default=None,
                        help="labeled CSV (columns incidente_id, conteudo, categoria) "
                             "used as the instance-memory reference set")
    parser.add_argument("--engine", choices=("auto", "zeroshot", "zeroshot-max", "knn"),
                        default="auto")
    parser.add_argument("--k", type=int, default=3)
    parser.add_argument("--sim-threshold", type=float, default=0.75)
    parser.add_argument("--text-column", default="conteudo")
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--output", type=Path, default=Path("predictions.csv"))
    args = parser.parse_args(argv)

    preds = classify_tickets(args.input, args.memory, args.engine, args.k,
                             args.sim_threshold, args.text_column, args.batch_size)
    write_predictions(preds, args.output)
    engines = Counter(p.engine for p in preds)
    cats = Counter(p.category for p in preds)
    print(f"{len(preds)} tickets classified -> {args.output}")
    print(f"engines: {dict(engines)}")
    print(f"categories: {dict(sorted(cats.items()))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
