"""Core metric functions for SpaCCBench."""
from spaccbench.core.composite import (
    METRIC_DIRECTION,
    composite_geo,
    composite_table,
    rank_score,
)
from spaccbench.core.d1_detection import d1_detection
from spaccbench.core.d2_fidelity import d2_fidelity
from spaccbench.core.d3_spatial import (
    build_knn_weights,
    d3_spatial,
    gearys_c,
    morans_i,
)
from spaccbench.core.d4_pathway import (
    compute_auc,
    d4_pathway,
    load_gmt,
    receptor_to_pathways,
)

__all__ = [
    "d1_detection",
    "d2_fidelity",
    "d3_spatial",
    "d4_pathway",
    "rank_score",
    "composite_geo",
    "composite_table",
    "METRIC_DIRECTION",
    "build_knn_weights",
    "morans_i",
    "gearys_c",
    "compute_auc",
    "load_gmt",
    "receptor_to_pathways",
]
