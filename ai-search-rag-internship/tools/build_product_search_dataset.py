"""Generate the deterministic product-search catalog and qrels."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from phase2_semantic_search.product_dataset import write_product_dataset


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        default="data/processed",
        help="Directory for the generated catalog, queries, qrels and manifest.",
    )
    parser.add_argument("--product-count", type=int, default=500)
    args = parser.parse_args()

    manifest = write_product_dataset(Path(args.output_dir), product_count=args.product_count)
    print(
        "generated dataset:",
        f"{manifest['product_count']} products,",
        f"{manifest['query_count']} queries,",
        f"{manifest['family_count']} families",
    )


if __name__ == "__main__":
    main()
