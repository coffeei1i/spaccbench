"""Unified ligand-receptor database accessor.

Provides the merged LR resource (10 methods, species-stratified) as a
standalone community resource. See Methods §S1.3 of the SpaCCBench paper.
"""
from __future__ import annotations

from importlib.resources import as_file, files
from pathlib import Path

import pandas as pd


def load_lr_db(species: str) -> pd.DataFrame:
    """Load the unified ligand-receptor database.

    Parameters
    ----------
    species : {"mouse", "human"}
        Species. Mouse pool: 8234 pairs; human pool: 7056 pairs.

    Returns
    -------
    pd.DataFrame
        Columns: ``ligand``, ``receptor``, ``n_sources``, ``sources``.

        - ``ligand`` / ``receptor``: lowercase gene symbols.
        - ``n_sources``: number of source databases containing the pair.
        - ``sources``: semicolon-joined source DB names.

    Notes
    -----
    The pool is the union of native LR resources from the 10 evaluated
    methods. Pairs present in multiple databases get a higher ``n_sources``
    weight in the top-25 selection (see ``spaccbench.lr_selection``), which
    may over-represent well-studied interactions.
    """
    species_lower = species.strip().lower()
    if species_lower not in {"mouse", "human"}:
        raise ValueError(
            f"species must be 'mouse' or 'human', got {species!r}"
        )

    filename = f"unified_lr_db_{species_lower}.csv"
    pkg_files = files("spaccbench") / "data"
    resource = pkg_files / filename
    try:
        with as_file(resource) as p:
            path = Path(p)
            if not path.is_file():
                raise FileNotFoundError(path)
            return pd.read_csv(path)
    except (FileNotFoundError, ModuleNotFoundError) as e:
        raise FileNotFoundError(
            f"Unified LR database for {species!r} ({filename!r}) is not "
            f"bundled. See README for data setup."
        ) from e
