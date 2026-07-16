"""COMMOT score-file adapter.

Loads externally prepared COMMOT cell × LR matrices by standardized filename.
"""

from __future__ import annotations

from spaccbench.adapters._csv_backed import CsvBackedAdapter


class COMMOTAdapter(CsvBackedAdapter):
    name = "COMMOT"
    file_template = "commot_{scenario}_scores.parquet"
