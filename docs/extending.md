# Extending SpaCCBench with your own method

This guide walks through evaluating a new spatial CCC method against the
SpaCCBench framework. You need to produce a single artefact — a cells × LR
score matrix — and wrap it in a minimal adapter class.

## 1. Generate your method's scores

For a scenario (e.g. `tha`), run your method on the bundled AnnData:

```python
import anndata as ad
from spaccbench.scenarios import load_scenario

scenario = load_scenario("tha")
adata = scenario.adata          # 9773 cells × 550 genes, with obsm['spatial']
top25_lr = scenario.top25_lr    # list of "ligand-receptor" strings (lowercased)

# ... run your method on adata, restricted to or pre-filtered to top25_lr,
# producing a cells × LR pair score matrix.
```

The expected output is a `pandas.DataFrame`:

- **Index**: cell barcodes (must match `scenario.adata.obs_names`)
- **Columns**: `"ligand-receptor"` strings, lowercased with `-` separator
  (e.g. `"agt-agtr1a"`)
- **Values**: per-cell scores (floats; `NaN` is allowed and means "no score
  emitted for this cell")

## 2. Write your adapter

```python
import pandas as pd
from spaccbench import BaseAdapter, evaluate

class MyMethodAdapter(BaseAdapter):
    name = "MyMethod"

    def __init__(self, scores_dir):
        self.scores_dir = scores_dir

    def load_scores(self, scenario: str) -> pd.DataFrame:
        # Just one method to implement.
        return pd.read_csv(f"{self.scores_dir}/{scenario}.csv", index_col=0)

adapter = MyMethodAdapter(scores_dir="./my_outputs")
result = evaluate(method=adapter, scenario="tha")
print(result["composite_geo"])
```

That's it. Your method now produces D1-D4 numbers comparable to the 10
methods in the SpaCCBench paper.

## 3. Cohort-level ranking

To rank your method against the bundled baselines:

```python
from spaccbench import compose_cohort, evaluate

methods = ["LIANA", "COMMOT"]
results = [evaluate(m, "tha") for m in methods]
results.append(evaluate(adapter, "tha"))

table = compose_cohort(results)
print(table[["d1_fraction", "d2_pearson_r", "d3_morans_i", "d4_mean_auc",
             "composite_geo"]].sort_values("composite_geo", ascending=False))
```

The `composite_geo` column is the geometric mean of the four rank-normalised
scores (see paper Methods §2.2 / Eq. for `Composite_geo`).

## 4. Tips

### Column-name normalisation

Internally all LR strings are normalised to lowercase, hyphen-separated. The
adapter base class doesn't enforce this — if your raw output uses
`"FN1_CD44"` or `"FN1|CD44"`, normalise at adapter load time or use the
helper `spaccbench.tools.normalise_lr_columns()` (see
[`tools/build_adapter_scores.py`](../tools/build_adapter_scores.py)).

### Cell alignment

`evaluate()` reindexes your score matrix to `scn.adata.obs_names`. Cells not
in your output get all-NaN rows; cells in your output but missing from the
AnnData are dropped. If your method skips cells (e.g. only emits scores for
the receiver cell-type), this is fine — D2-D4 are NaN-aware.

### Reusing the four-dim machinery

If you only need one dimension, the per-dimension functions are public:

```python
from spaccbench.core import d1_detection, d2_fidelity, d3_spatial, d4_pathway

d1_result = d1_detection(scores, top25_lr=scn.top25_lr)
d2_result = d2_fidelity(scores, reference=scn.gt_signal, top25_lr=scn.top25_lr)
d3_result = d3_spatial(scores, coords=scn.coords, top25_lr=scn.top25_lr, k=6)
d4_result = d4_pathway(scores, pw_act=scn.pw_act, top25_lr=scn.top25_lr,
                        kegg=scn.kegg, n_perm=200)
```

### Custom scenarios

The `Scenario` dataclass requires `adata`, `top25_lr`, `gt_signal`, `pw_act`
and `kegg`. If you have new data, use `tools/build_scenario.py` to derive
`top25_lr`, `gt_signal` and `pw_act` from an arbitrary AnnData + LR DB +
KEGG GMT, then construct a `Scenario` and pass it directly to `evaluate`.

## 5. Reporting back

If you adapt your method and want it included in the next release, open a
pull request adding:

- `spaccbench/adapters/<your_method>.py` — your adapter class
- a registration line in `spaccbench/adapters/__init__.py`
- pre-computed scores under `spaccbench/data/<method>_<scenario>_scores.parquet`
  (or a Zenodo URL if too large for the repo)
- a paragraph in the paper's Methods §S1.2 table
