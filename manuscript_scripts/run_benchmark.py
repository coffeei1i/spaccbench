"""Evaluate harmonized manuscript-method outputs on THA and CTX.

Put method outputs under examples/method_outputs or pass --outputs, then run:

    python manuscript_scripts/run_benchmark.py --outputs examples/method_outputs \
        --require-all

The script passes each final cell-by-LR score matrix to spaccbench.evaluate.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import pandas as pd

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from spaccbench import BaseAdapter, compose_cohort, evaluate  # noqa: E402
from spaccbench.harmonization import harmonize_score_matrix  # noqa: E402

SCENARIO_SAMPLE = {
    "tha": "THA",
    "ctx": "CTX",
}

METHODS = [
    "LIANA",
    "COMMOT",
    "stLearn",
    "SPIDER",
    "Spacia",
    "StereoSiTE",
    "CellAgentChat",
    "stCASE",
    "LARIS",
    "SpaCcLink",
]


def _normalise_lr_columns(df: pd.DataFrame) -> pd.DataFrame:
    return harmonize_score_matrix(df)


def _read_indexed_csv(path: Path) -> pd.DataFrame:
    return _normalise_lr_columns(pd.read_csv(path, index_col=0))


def _read_stlearn(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    if "spot_id" in df.columns:
        df = df.set_index("spot_id")
    elif "Unnamed: 0" in df.columns:
        df = df.set_index("Unnamed: 0")
    else:
        df = pd.read_csv(path, index_col=0)
    return _normalise_lr_columns(df)


def _read_cellagentchat(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, sep=None, engine="python")
    for key in ("index", "spot_id", "Unnamed: 0", "cell"):
        if key in df.columns:
            df = df.set_index(key)
            break
    return _normalise_lr_columns(df)


def _first_existing(candidates: list[Path]) -> Path:
    for path in candidates:
        if path.exists():
            return path
    return candidates[0]


def _spider_path(root: Path, sample: str) -> Path:
    """Resolve the exact or suffix-matched SPIDER sample directory."""
    exact = root / "spider" / sample / f"{sample}.csv"
    if exact.exists():
        return exact

    spider_root = root / "spider"
    if spider_root.exists():
        sample_key = sample.lower()
        directories = sorted(
            (
                path
                for path in spider_root.iterdir()
                if path.is_dir()
                and (path.name.lower() == sample_key or path.name.lower().endswith(sample_key))
            ),
            key=lambda path: path.name.lower(),
        )
        for directory in directories:
            named = directory / f"{sample}.csv"
            if named.exists():
                return named
            csv_files = sorted(directory.rglob("*.csv"))
            if csv_files:
                return csv_files[0]
    return exact


@dataclass(frozen=True)
class MethodSpec:
    method: str
    path_builder: Callable[[Path, str], Path]
    reader: Callable[[Path], pd.DataFrame] = _read_indexed_csv


SPECS = {
    "LIANA": MethodSpec(
        "LIANA",
        lambda root, sample: root / "liana" / sample / f"{sample}_spotxLR.csv",
    ),
    "COMMOT": MethodSpec(
        "COMMOT",
        lambda root, sample: root / "commot" / sample / sample / f"{sample}.csv",
    ),
    "stLearn": MethodSpec(
        "stLearn",
        lambda root, sample: root / "stlearn" / sample / f"{sample}_SPOTxLR_lr_scores.csv",
        _read_stlearn,
    ),
    "SPIDER": MethodSpec(
        "SPIDER",
        _spider_path,
    ),
    "Spacia": MethodSpec(
        "Spacia",
        lambda root, sample: root / "spacia" / sample / f"{sample}_cellxLR_spacia.csv",
    ),
    "StereoSiTE": MethodSpec(
        "StereoSiTE",
        lambda root, sample: _first_existing(
            [
                root / "stereosite" / sample / sample / f"{sample}_LR_intensity_matrix.csv",
                root / "stereosite" / sample / f"{sample}_LR_intensity_matrix.csv",
            ]
        ),
    ),
    "CellAgentChat": MethodSpec(
        "CellAgentChat",
        lambda root, sample: (
            root / "cellagentchat" / sample / "out" / "cell_receiving_scores_FINAL.csv"
        ),
        _read_cellagentchat,
    ),
    "stCASE": MethodSpec(
        "stCASE",
        lambda root, sample: root / "stcase" / sample / f"{sample}.csv",
    ),
    "LARIS": MethodSpec(
        "LARIS",
        lambda root, sample: root / "laris" / sample / f"{sample}_prepare_CellByLR.csv",
    ),
    "SpaCcLink": MethodSpec(
        "SpaCcLink",
        lambda root, sample: _first_existing(
            [
                root / "spacclink" / sample / f"{sample}_ALL_LR_cellxLR.csv",
                root / "spacclink" / sample / f"{sample}_LR_scores.csv",
            ]
        ),
    ),
}


class MethodOutputAdapter(BaseAdapter):
    """Adapter for one method output file in the manuscript handoff format."""

    def __init__(
        self,
        name: str,
        path: Path,
        reader: Callable[[Path], pd.DataFrame],
    ):
        self.name = name
        self.path = path
        self.reader = reader

    def load_scores(self, scenario: str) -> pd.DataFrame:
        if not self.path.exists():
            raise FileNotFoundError(self.path)
        return self.reader(self.path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--outputs",
        type=Path,
        default=Path("examples/method_outputs"),
        help="Root containing method outputs in the examples/README.md layout.",
    )
    parser.add_argument(
        "--scenarios",
        nargs="+",
        default=["tha", "ctx"],
        choices=sorted(SCENARIO_SAMPLE),
        help="Scenarios to evaluate.",
    )
    parser.add_argument(
        "--methods",
        nargs="+",
        default=METHODS,
        choices=METHODS,
        help="Methods to evaluate; default is all ten manuscript methods.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("manuscript_outputs/spaccbench_results.csv"),
        help="CSV file for the long-format result table.",
    )
    parser.add_argument(
        "--require-all",
        action="store_true",
        help="Require every selected method output file to be present.",
    )
    parser.add_argument(
        "--n-perm",
        type=int,
        default=0,
        help="D4 permutations; 0 is fastest for examples.",
    )
    return parser.parse_args()


def summarise_result(result: dict) -> dict:
    row = {
        "method": result["method"],
        "scenario": result["scenario"],
    }
    if "d1" in result:
        row["d1_fraction"] = result["d1"]["fraction"]
    if "d2" in result:
        row["d2_pearson_r"] = result["d2"]["pearson_r"]
        row["d2_spearman"] = result["d2"]["spearman"]
        row["d2_cosine"] = result["d2"]["cosine"]
        row["d2_js"] = result["d2"]["js"]
    if "d3" in result:
        row["d3_morans_i"] = result["d3"]["morans_i"]
        row["d3_gearys_c"] = result["d3"]["gearys_c"]
    if "d4" in result:
        row["d4_mean_auc"] = result["d4"]["mean_auc"]
    return row


def main() -> int:
    args = parse_args()
    rows = []
    cohort_tables = []

    for scenario in args.scenarios:
        sample = SCENARIO_SAMPLE[scenario]
        scenario_results = []

        for method in args.methods:
            spec = SPECS[method]
            path = spec.path_builder(args.outputs, sample)
            if not path.exists():
                print(f"[PENDING] {method} {scenario}: add {path}")
                if args.require_all:
                    raise FileNotFoundError(path)
                continue

            adapter = MethodOutputAdapter(spec.method, path, spec.reader)
            result = evaluate(
                adapter,
                scenario=scenario,
                n_perm=args.n_perm,
                return_per_lr=False,
            )
            rows.append(summarise_result(result))
            scenario_results.append(result)
            print(f"[OK] {method} {scenario}: {path}")

        if scenario_results:
            cohort = compose_cohort(scenario_results).reset_index()
            cohort.insert(0, "scenario", scenario)
            cohort_tables.append(cohort)

    if rows:
        output = pd.DataFrame(rows)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        output.to_csv(args.out, index=False)
        print(f"[WROTE] {args.out}")

    if cohort_tables:
        cohort_out = args.out.with_name(args.out.stem + "_cohort.csv")
        pd.concat(cohort_tables, ignore_index=True).to_csv(
            cohort_out,
            index=False,
        )
        print(f"[WROTE] {cohort_out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
