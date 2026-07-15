# Extending SpaCCBench with your own method

This guide shows how to evaluate a new spatial CCC method with the SpaCCBench
framework. The adapter interface uses a single artefact: a cells x LR score
matrix wrapped in a minimal adapter class.

Set SPACCBENCH_DATA_DIR to the directory containing prepared scenario files before loading a registered scenario.

## 1. Generate your method scores

For a scenario such as `tha`, run your method on the scenario AnnData:

```python
import anndata as ad
from spaccbench.scenarios import load_scenario

scenario = load_scenario("tha")
adata = scenario.adata          # 9773 cells x 550 genes, with obsm['spatial']
candidate_lr = scenario.top25_lr  # expression-informed candidate LR strings

# Run your method workflow on adata and candidate_lr,
# producing a cells x LR pair score matrix.
```

The expected output is a `pandas.DataFrame`:

- **Index**: cell barcodes matching `scenario.adata.obs_names`.
- **Columns**: `"ligand-receptor"` strings, lowercased with `-` separator, such as `"agt-agtr1a"`.
- **Values**: per-cell scores as floats; `NaN` values follow the standard SpaCCBench alignment rules.

## 2. Write your adapter

```python
import pandas as pd
from spaccbench import BaseAdapter, evaluate

class MyMethodAdapter(BaseAdapter):
    name = "MyMethod"

    def __init__(self, scores_dir):
        self.scores_dir = scores_dir

    def load_scores(self, scenario: str) -> pd.DataFrame:
        return pd.read_csv(f"{self.scores_dir}/{scenario}.csv", index_col=0)

adapter = MyMethodAdapter(scores_dir="./my_outputs")
result = evaluate(method=adapter, scenario="tha")
print(result["composite_geo"])
```

Your method now produces D1-D4 numbers comparable to the ten methods in the
SpaCCBench paper.

## 3. Cohort-level ranking

To rank your method against the reference baselines:

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
scores (see paper Methods Section 2.2 / Eq. for `Composite_geo`).

## 4. Tips

### Column-name normalisation

Internally all LR strings are normalised to lowercase, hyphen-separated. The
adapter can standardize this during loading. For example, if your raw output
uses `"FN1_CD44"` or `"FN1|CD44"`, normalise at adapter load time or use the
helper in [`tools/build_adapter_scores.py`](../tools/build_adapter_scores.py).

### Cell alignment

`evaluate()` reindexes your score matrix to `scn.adata.obs_names`. The benchmark
alignment keeps cell ordering consistent across methods. Missing cells,
non-numeric values, and unavailable entries are represented as `0.0`.

### Reusing the four-dimensional machinery

If you want one dimension, the per-dimension functions are public:

```python
from spaccbench.core import d1_detection, d2_fidelity, d3_spatial, d4_pathway

d1_result = d1_detection(scores, top25_lr=scn.top25_lr)
d2_result = d2_fidelity(scores, reference=scn.gt_signal, top25_lr=scn.top25_lr)
d3_result = d3_spatial(scores, coords=scn.coords, top25_lr=scn.top25_lr, k=6)
d4_result = d4_pathway(scores, pw_act=scn.pw_act, top25_lr=scn.top25_lr,
                        kegg=scn.kegg, n_perm=200)
```

### Custom scenarios

The `Scenario` dataclass requires `adata`, `top25_lr`, `gt_signal`, `pw_act` and
`kegg`. For new data, use `tools/build_scenario.py` to derive `top25_lr`,
`gt_signal` and `pw_act` from an AnnData object, an LR database and a KEGG GMT,
then construct a `Scenario` and pass it directly to `evaluate`.
