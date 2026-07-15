"""Shared score-matrix harmonization for adapters and manuscript workflows."""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd


def normalise_lr_name(value: object) -> str:
    """Return a lowercase ``ligand-receptor`` key.

    Common pair separators are accepted. For receptor complexes, the first
    receptor is retained to match the manuscript's cross-method convention.
    """
    name = str(value).strip().lower().replace(" ", "")
    for separator in ("::", "|", "^"):
        name = name.replace(separator, "-")

    if "-" in name:
        ligand, receptor = name.split("-", 1)
    elif "_" in name:
        ligand, receptor = name.split("_", 1)
    else:
        return name

    receptor = receptor.split("_", 1)[0].split("-", 1)[0]
    return f"{ligand}-{receptor}"


def harmonize_score_matrix(
    scores: pd.DataFrame,
    cell_index: Iterable[object] | None = None,
) -> pd.DataFrame:
    """Normalize LR columns, coerce numeric scores, merge duplicates, and fill zero.

    When ``cell_index`` is supplied, rows are aligned to that exact order.
    Missing cells and unavailable values are represented as ``0.0``.
    """
    out = scores.copy()
    out.index = out.index.astype(str)
    out.columns = [normalise_lr_name(column) for column in out.columns]
    out = out.apply(pd.to_numeric, errors="coerce")

    if out.columns.duplicated().any():
        ordered_names = list(dict.fromkeys(out.columns))
        out = pd.concat(
            [out.loc[:, out.columns == name].sum(axis=1, min_count=1) for name in ordered_names],
            axis=1,
        )
        out.columns = ordered_names

    if cell_index is not None:
        out = out.reindex(pd.Index([str(value) for value in cell_index]))
    return out.fillna(0.0)
