"""COMMOT reference adapter.

Loads pre-computed COMMOT cell × LR score matrices shipped with the package.
"""
from __future__ import annotations

from spaccbench.adapters._csv_backed import CsvBackedAdapter


class COMMOTAdapter(CsvBackedAdapter):
    name = "COMMOT"
    file_template = "commot_{scenario}_scores.parquet"
