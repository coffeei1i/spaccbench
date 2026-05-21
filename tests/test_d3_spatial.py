"""Unit tests for D3 spatial autocorrelation."""
import numpy as np
import pandas as pd

from spaccbench.core import build_knn_weights, d3_spatial, gearys_c, morans_i


def _grid_coords(n_side: int = 20) -> np.ndarray:
    xs, ys = np.meshgrid(np.arange(n_side), np.arange(n_side))
    return np.column_stack([xs.ravel(), ys.ravel()])


def test_morans_i_high_for_smooth_gradient():
    coords = _grid_coords(20)
    W = build_knn_weights(coords, k=6)
    # Smooth horizontal gradient: each cell value = x coord.
    x = coords[:, 0].astype(float)
    I = morans_i(x, W)
    assert I > 0.9  # very high autocorrelation


def test_morans_i_near_zero_for_random():
    rng = np.random.default_rng(0)
    coords = rng.uniform(0, 100, size=(500, 2))
    W = build_knn_weights(coords, k=6)
    x = rng.normal(size=500)
    I = morans_i(x, W)
    assert abs(I) < 0.15


def test_gearys_c_low_for_smooth():
    coords = _grid_coords(20)
    W = build_knn_weights(coords, k=6)
    x = coords[:, 0].astype(float)
    C = gearys_c(x, W)
    assert C < 0.2  # very low C = high local similarity


def test_gearys_c_near_one_for_random():
    rng = np.random.default_rng(0)
    coords = rng.uniform(0, 100, size=(500, 2))
    W = build_knn_weights(coords, k=6)
    x = rng.normal(size=500)
    C = gearys_c(x, W)
    assert 0.7 < C < 1.3


def test_d3_full_pipeline():
    coords = _grid_coords(15)
    n = coords.shape[0]
    cells = [f"c{i}" for i in range(n)]
    # Two LR pairs: one smooth, one random.
    rng = np.random.default_rng(0)
    scores = pd.DataFrame(
        {
            "smooth-rec1": coords[:, 0].astype(float),
            "rand-rec2": rng.normal(size=n),
        },
        index=cells,
    )
    out = d3_spatial(scores, coords, top25_lr=["smooth-rec1", "rand-rec2"], k=6)
    assert out["n_lr"] == 2
    smooth_row = out["per_lr"].set_index("lr").loc["smooth-rec1"]
    rand_row = out["per_lr"].set_index("lr").loc["rand-rec2"]
    assert smooth_row["morans_i"] > rand_row["morans_i"]


def test_d3_skips_constant_lr():
    coords = _grid_coords(10)
    n = coords.shape[0]
    cells = [f"c{i}" for i in range(n)]
    scores = pd.DataFrame({"const-rec": np.zeros(n)}, index=cells)
    out = d3_spatial(scores, coords, top25_lr=["const-rec"], k=6)
    assert out["n_lr"] == 0
