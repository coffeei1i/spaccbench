"""SpaCCBench: four-dimensional benchmark for spatial cell-cell communication inference.

Public API:

    >>> from spaccbench import evaluate, load_scenario, BaseAdapter
    >>> result = evaluate(method="LIANA", scenario="tha")
    >>> print(result["d2"]["pearson_r"])

See https://github.com/coffeei1i/spaccbench for documentation.
"""
from __future__ import annotations

from spaccbench._version import __version__
from spaccbench.adapters import (
    ALL_ADAPTERS,
    REFERENCE_ADAPTERS,
    BaseAdapter,
    COMMOTAdapter,
    LIANAAdapter,
    get_adapter,
    list_methods,
)
from spaccbench.core import (
    d1_detection,
    d2_fidelity,
    d3_spatial,
    d4_pathway,
    composite_geo,
    composite_table,
    rank_score,
)
from spaccbench.evaluate import compose_cohort, evaluate
from spaccbench.lr_db import load_lr_db
from spaccbench.scenarios import Scenario, list_scenarios, load_scenario

__all__ = [
    "__version__",
    # Top-level API
    "evaluate",
    "compose_cohort",
    "load_scenario",
    "list_scenarios",
    "load_lr_db",
    # Dimension functions
    "d1_detection",
    "d2_fidelity",
    "d3_spatial",
    "d4_pathway",
    # Composite helpers
    "rank_score",
    "composite_geo",
    "composite_table",
    # Adapter API
    "BaseAdapter",
    "LIANAAdapter",
    "COMMOTAdapter",
    "get_adapter",
    "list_methods",
    "REFERENCE_ADAPTERS",
    "ALL_ADAPTERS",
    # Types
    "Scenario",
]
