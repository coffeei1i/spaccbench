"""LIANA reference adapter.

Loads pre-computed LIANA cell × LR score matrices shipped with the package.
"""
from __future__ import annotations

from spaccbench.adapters._csv_backed import CsvBackedAdapter


class LIANAAdapter(CsvBackedAdapter):
    name = "LIANA"
    file_template = "liana_{scenario}_scores.parquet"
