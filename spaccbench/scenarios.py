"""Scenario registry and loader.

A scenario bundles everything needed to evaluate a method on a specific
dataset:

- AnnData (cells, genes, spatial coords, cell type metadata)
- Top-25 LR list (lowercased ``ligand-receptor`` strings)
- Expression-derived reference signal E (cells × top-25 LR)
- Pre-computed pathway activity matrix (cells × pathways)
- Species ("mouse" or "human")

Data files are shipped via ``importlib.resources`` from ``spaccbench/data/``.
"""
from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import as_file, files
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


SCENARIO_REGISTRY: dict[str, dict[str, Any]] = {
    "tha": {
        "name": "tha",
        "title": "Mouse hypothalamus (MERFISH)",
        "species": "mouse",
        "platform": "MERFISH",
        "n_cells_expected": 9773,
        "files": {
            "adata":     "tha.h5ad",
            "top25":     "tha_top25.csv",
            "gt":        "tha_gt_signal.parquet",
            "pw_act":    "tha_pw_act.parquet",
            "kegg":      "kegg_mouse.gmt",
        },
    },
    "ctx": {
        "name": "ctx",
        "title": "Mouse cortico-striatal coronal section (MERFISH)",
        "species": "mouse",
        "platform": "MERFISH",
        "n_cells_expected": 9943,
        "files": {
            "adata":     "ctx.h5ad",
            "top25":     "ctx_top25.csv",
            "gt":        "ctx_gt_signal.parquet",
            "pw_act":    "ctx_pw_act.parquet",
            "kegg":      "kegg_mouse.gmt",
        },
    },
}


@dataclass
class Scenario:
    """Container for everything an ``evaluate`` call needs."""
    name: str
    title: str
    species: str
    platform: str
    adata: Any                  # AnnData
    top25_lr: list[str]         # lowercased ligand-receptor strings
    top25_table: pd.DataFrame   # original top-25 CSV (with sender/receiver cell-type, scores, ...)
    gt_signal: pd.DataFrame     # cells × top-25 LR reference signal E
    pw_act: pd.DataFrame        # cells × pathways activity (GSVA)
    kegg: pd.DataFrame          # long-format pathway-gene table

    @property
    def coords(self) -> np.ndarray:
        """Return spatial coordinates from ``adata.obsm['spatial']``."""
        if "spatial" not in self.adata.obsm:
            raise KeyError(
                f"Scenario {self.name!r}: adata.obsm has no 'spatial' field."
            )
        return np.asarray(self.adata.obsm["spatial"], dtype=float)


# ----- Data resolution --------------------------------------------------------

def _resource_path(filename: str) -> Path:
    """Resolve a packaged data file. Raises FileNotFoundError if missing."""
    pkg_files = files("spaccbench") / "data"
    resource = pkg_files / filename
    try:
        with as_file(resource) as p:
            if not p.is_file():
                raise FileNotFoundError(p)
            return Path(p)
    except (FileNotFoundError, ModuleNotFoundError) as e:
        raise FileNotFoundError(
            f"Scenario data file {filename!r} is not bundled with this "
            f"installation. See README for data setup."
        ) from e


# ----- Public API -------------------------------------------------------------

def list_scenarios() -> list[dict[str, Any]]:
    """Return scenario metadata for all registered scenarios."""
    return [
        {
            "name": meta["name"],
            "title": meta["title"],
            "species": meta["species"],
            "platform": meta["platform"],
            "n_cells_expected": meta["n_cells_expected"],
        }
        for meta in SCENARIO_REGISTRY.values()
    ]


def load_scenario(name: str) -> Scenario:
    """Load a scenario by name.

    Parameters
    ----------
    name : str
        Scenario key (e.g. ``"tha"``, ``"ctx"``).

    Returns
    -------
    Scenario
        Container with adata, top25_lr, gt_signal, pw_act, kegg ready for
        ``evaluate``.

    Raises
    ------
    KeyError
        If ``name`` is not in the registry.
    FileNotFoundError
        If the bundled data files are missing.
    """
    if name not in SCENARIO_REGISTRY:
        raise KeyError(
            f"Unknown scenario {name!r}. Known: {sorted(SCENARIO_REGISTRY)}"
        )
    meta = SCENARIO_REGISTRY[name]

    # Lazy import: anndata is heavy.
    import anndata as ad

    adata_path = _resource_path(meta["files"]["adata"])
    top25_path = _resource_path(meta["files"]["top25"])
    gt_path = _resource_path(meta["files"]["gt"])
    pw_act_path = _resource_path(meta["files"]["pw_act"])
    kegg_path = _resource_path(meta["files"]["kegg"])

    adata = ad.read_h5ad(adata_path)
    top25_table = pd.read_csv(top25_path)

    if "lr" in top25_table.columns:
        top25_lr = [str(x).lower().strip() for x in top25_table["lr"].tolist()]
    elif {"ligand", "receptor"}.issubset(top25_table.columns):
        top25_lr = [
            f"{str(l).lower().strip()}-{str(r).lower().strip()}"
            for l, r in zip(top25_table["ligand"], top25_table["receptor"])
        ]
    else:
        raise ValueError(
            f"top25 table for {name!r} must contain either an 'lr' column or "
            f"both 'ligand' and 'receptor' columns. Got {list(top25_table.columns)}"
        )

    gt_signal = _read_table(gt_path)
    pw_act = _read_table(pw_act_path)

    from spaccbench.core.d4_pathway import load_gmt
    kegg = load_gmt(kegg_path)

    return Scenario(
        name=name,
        title=meta["title"],
        species=meta["species"],
        platform=meta["platform"],
        adata=adata,
        top25_lr=top25_lr,
        top25_table=top25_table,
        gt_signal=gt_signal,
        pw_act=pw_act,
        kegg=kegg,
    )


def _read_table(path: Path) -> pd.DataFrame:
    """Read CSV or parquet by suffix."""
    suffix = path.suffix.lower()
    if suffix == ".parquet":
        return pd.read_parquet(path)
    if suffix in {".csv", ".tsv"}:
        sep = "," if suffix == ".csv" else "\t"
        return pd.read_csv(path, sep=sep, index_col=0)
    raise ValueError(f"Unsupported table format: {path}")
