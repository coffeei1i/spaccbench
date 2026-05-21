"""Shared implementation for adapters that read a pre-computed CSV/parquet."""
from __future__ import annotations

from importlib.resources import as_file, files
from pathlib import Path

import pandas as pd

from spaccbench.adapters.base import BaseAdapter


class CsvBackedAdapter(BaseAdapter):
    """Adapter that loads scores from a packaged CSV/parquet file.

    The bundled file path follows the convention:
        ``spaccbench/data/{method_name_lower}_{scenario}_scores.{csv|parquet}``

    Override the class attributes ``name`` and ``file_template`` in subclasses.
    """

    name: str = "CsvBacked"
    file_template: str = "{name_lower}_{scenario}_scores.parquet"

    def load_scores(self, scenario: str) -> pd.DataFrame:
        filename = self.file_template.format(
            name_lower=self.name.lower(), scenario=scenario
        )
        pkg_files = files("spaccbench") / "data"
        resource = pkg_files / filename

        try:
            with as_file(resource) as p:
                path = Path(p)
                if not path.is_file():
                    raise FileNotFoundError(path)
                return self._read(path)
        except (FileNotFoundError, ModuleNotFoundError):
            # Fall back to a co-bundled csv with the same stem, in case the
            # build pipeline emitted csv instead of parquet.
            alt = filename.rsplit(".", 1)[0] + ".csv"
            alt_resource = pkg_files / alt
            try:
                with as_file(alt_resource) as p:
                    path = Path(p)
                    if path.is_file():
                        return self._read(path)
            except (FileNotFoundError, ModuleNotFoundError):
                pass
            raise FileNotFoundError(
                f"{self.name} scores file {filename!r} (or .csv fallback) is "
                f"not bundled. Run `python tools/build_adapter_scores.py "
                f"--method {self.name} --scenario {scenario}` to generate it."
            )

    @staticmethod
    def _read(path: Path) -> pd.DataFrame:
        if path.suffix.lower() == ".parquet":
            df = pd.read_parquet(path)
        else:
            df = pd.read_csv(path, index_col=0)
        # Normalise column names to lowercase ligand-receptor.
        df.columns = [str(c).strip().lower().replace("_", "-") for c in df.columns]
        return df
