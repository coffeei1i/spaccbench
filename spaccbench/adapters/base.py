"""BaseAdapter contract for plugging methods into SpaCCBench."""
from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd


class BaseAdapter(ABC):
    """Abstract base class for spatial CCC method adapters.

    Subclass this to integrate a method into the SpaCCBench evaluation.
    The only required method is ``load_scores(scenario)``.

    Attributes
    ----------
    name : str
        Human-readable method name. Override in subclass.

    Examples
    --------
    >>> from spaccbench import BaseAdapter, evaluate
    >>> class MyAdapter(BaseAdapter):
    ...     name = "MyMethod"
    ...     def load_scores(self, scenario):
    ...         return pd.read_csv(f"my_outputs/{scenario}.csv", index_col=0)
    >>> result = evaluate(method=MyAdapter(), scenario="tha")
    """

    name: str = "BaseAdapter"

    @abstractmethod
    def load_scores(self, scenario: str) -> pd.DataFrame:
        """Return per-cell LR scores for the given scenario.

        Parameters
        ----------
        scenario : str
            Scenario name (e.g. ``"tha"``, ``"ctx"``).

        Returns
        -------
        pd.DataFrame
            Per-cell LR score matrix.

            - Index: cell barcodes (must match ``scenario.adata.obs_names``).
            - Columns: LR pair strings, formatted as lowercase
              ``"ligand-receptor"`` (e.g. ``"agt-agtr1a"``).
            - Values: floats. ``NaN`` is allowed and is interpreted as
              "no score emitted for this cell". All-zero or all-NaN columns
              are treated as ``not detected`` by D1.
        """
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name!r}>"
