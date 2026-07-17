"""Build per-method adapter score matrices for SpaCCBench.

Reads a final cell-by-LR CSV or parquet input and
emits a clean cells x LR-pair parquet file consumable by
``spaccbench.adapters.CsvBackedAdapter``.
The tool standardizes a file; it does not register a method adapter. LIANA and
COMMOT have built-in file-backed adapters. Other methods still require a
custom adapter or the manuscript handoff layout.

Output format:
  - Path: ``<output_dir>/<method>_<scenario>_scores.parquet``
  - Index: cell barcodes (matching the scenario AnnData).
  - Columns: ``"ligand-receptor"`` (lowercase, hyphen-separated).
  - Values: numeric per-cell scores; unavailable values are written as 0.0.

Use ``--input-csv`` only when the method's final output already matches the
cells x LR format. Convert method-specific raw directories with the method's
own workflow before running this tool.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from spaccbench.harmonization import harmonize_score_matrix


def parse_args():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--method", required=True, help="Method name (e.g. LIANA, COMMOT)")
    p.add_argument("--scenario", required=True, help="Scenario name (e.g. tha, ctx)")
    p.add_argument(
        "--input-csv", type=Path, required=True, help="Path to a cells x LR-pairs CSV (or parquet)"
    )
    p.add_argument(
        "--output-dir", required=True, type=Path, help="Output dir (typically spaccbench/data/)"
    )
    p.add_argument(
        "--cell-index-col",
        default=None,
        help="Optional column name in the input that holds cell barcodes "
        "(default: use first column / DataFrame index)",
    )
    return p.parse_args()


def normalise_lr_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize names and values, merge duplicate LR pairs, and fill zero."""
    return harmonize_score_matrix(df)


def main():
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Load input.
    if args.input_csv.suffix.lower() == ".parquet":
        df = pd.read_parquet(args.input_csv)
    else:
        if args.cell_index_col:
            df = pd.read_csv(args.input_csv)
            df = df.set_index(args.cell_index_col)
        else:
            df = pd.read_csv(args.input_csv, index_col=0)

    df = normalise_lr_columns(df)
    print(f"[OK] loaded {args.input_csv} shape={df.shape}")

    method_lower = args.method.lower()
    out_path = args.output_dir / f"{method_lower}_{args.scenario}_scores.parquet"
    df.to_parquet(out_path)
    print(f"[WROTE] {out_path}")
    print(f"  cells     = {df.shape[0]}")
    print(f"  lr_pairs  = {df.shape[1]}")
    print(f"  non-null  = {df.notna().sum().sum()}")


if __name__ == "__main__":
    sys.exit(main())
