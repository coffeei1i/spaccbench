"""LIANA score-file adapter.

Loads externally prepared LIANA cell × LR matrices by standardized filename.
"""

from __future__ import annotations

from spaccbench.adapters._csv_backed import CsvBackedAdapter


class LIANAAdapter(CsvBackedAdapter):
    name = "LIANA"
    file_template = "liana_{scenario}_scores.parquet"
