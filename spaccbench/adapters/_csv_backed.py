"""Shared implementation for adapters that read prepared CSV/parquet scores."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from spaccbench.adapters.base import BaseAdapter
from spaccbench.resources import resolve_data_file


class CsvBackedAdapter(BaseAdapter):
    """Adapter that loads prepared CSV/parquet scores.

    The default score path follows the convention:
        ``spaccbench/data/{method_name_lower}_{scenario}_scores.{csv|parquet}``

    Override the class attributes ``name`` and ``file_template`` in subclasses.
    """

    name: str = "CsvBacked"
    file_template: str = "{name_lower}_{scenario}_scores.parquet"

    def load_scores(self, scenario: str) -> pd.DataFrame:
        filename = self.file_template.format(
            name_lower=self.name.lower(), scenario=scenario
        )
        candidates = [filename, filename.rsplit(".", 1)[0] + ".csv"]
        for candidate in candidates:
            try:
                return self._read(resolve_data_file(candidate))
            except FileNotFoundError:
                continue

        raise FileNotFoundError(
            f"Prepare {self.name} scores as {filename!r} or CSV with "
            f"python tools/build_adapter_scores.py --method {self.name} "
            f"--scenario {scenario}."
        )

    @staticmethod
    def _read(path: Path) -> pd.DataFrame:
        if path.suffix.lower() == ".parquet":
            df = pd.read_parquet(path)
        else:
            df = pd.read_csv(path, index_col=0)
        df.columns = [str(c).strip().lower().replace("_", "-") for c in df.columns]
        return df
