# SpaCCBench

[![CI](https://github.com/coffeei1i/spaccbench/actions/workflows/ci.yml/badge.svg)](https://github.com/coffeei1i/spaccbench/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**A four-dimensional benchmark for spatial cell-cell communication (CCC) inference.**

SpaCCBench evaluates spatial CCC methods along four orthogonal axes — detection
accuracy (D1), expression fidelity (D2), spatial structure coherence (D3) and
downstream pathway activation (D4) — on a common per-sample top-25 ligand-receptor
list drawn from a unified, species-stratified LR database (8,234 mouse / 7,056
human pairs merged from the native resources of 10 contemporary methods).

## Quickstart

```bash
pip install git+https://github.com/coffeei1i/spaccbench.git
```

```python
from spaccbench import evaluate

result = evaluate(method="LIANA", scenario="tha")
print(f"D1 hit rate     : {result['d1']['fraction']:.2%}")
print(f"D2 Pearson r    : {result['d2']['pearson_r']:.3f}")
print(f"D3 Moran's I    : {result['d3']['morans_i']:.3f}")
print(f"D4 mean AUC     : {result['d4']['mean_auc']:.3f}  (p_perm={result['d4']['perm_p']:.3g})")
```

Or from the command line:
```bash
spaccbench list-methods
spaccbench list-scenarios
spaccbench evaluate --method LIANA --scenario tha
spaccbench evaluate --method LIANA --scenario tha --output result.json
```

## Evaluate your own method

Subclass `BaseAdapter` and return a cells × LR score matrix:

```python
import pandas as pd
from spaccbench import BaseAdapter, evaluate

class MyMethodAdapter(BaseAdapter):
    name = "MyMethod"
    def __init__(self, scores_path):
        self.scores_path = scores_path
    def load_scores(self, scenario):
        # Return DataFrame: rows = cell barcodes, cols = "ligand-receptor" lowercased.
        return pd.read_csv(self.scores_path, index_col=0)

result = evaluate(method=MyMethodAdapter("my_outputs/tha.csv"), scenario="tha")
print(result["composite_geo"])
```

See [`docs/extending.md`](docs/extending.md) for the full guide.

## Bundled scenarios

| Scenario | Platform | Cells | Species | Notes |
|---|---|---|---|---|
| `tha` | MERFISH | 9,773 | mouse | Hypothalamus |
| `ctx` | MERFISH | 9,943 | mouse | Cortico-striatal coronal section |

Pre-computed cell × LR matrices for **LIANA** and **COMMOT** ship with the
package. The remaining 8 methods evaluated in the paper (Spacia, StereoSiTE,
SPIDER, stLearn, LARIS, CellAgentChat, stCASE, SpaCcLink) appear as stub
adapters — pre-computed scores are available at the companion Zenodo deposit
(DOI to be added upon publication).

## Four-dimensional evaluation framework

| Dim | Metric | Question |
|---|---|---|
| D1 | n_hit / 25 | Does the method recover the top-25 candidate LR pairs with non-trivial per-cell scores? |
| D2 | Pearson / Spearman / cosine / JS | Do per-cell scores agree with the expression-derived reference signal E? |
| D3 | Moran's I, Geary's C | Are the scores spatially coherent (kNN-6 weight matrix)? |
| D4 | mean AUC + permutation null | Do detected interactions track KEGG pathway activity of receptor-associated pathways? |

A method is *globally strong* only if it performs consistently across all four
dimensions. The geometric-mean composite

```
Composite_geo(m) = exp( (1/4) Σ_d log s_d(m) )
```

(where s_d are rank-normalised scores per metric) penalises uneven performance.

## Standalone unified LR resource

The merged ligand-receptor database is available independently of the
evaluation pipeline:

```python
from spaccbench import load_lr_db

mouse_db = load_lr_db("mouse")  # 8,234 pairs
human_db = load_lr_db("human")  # 7,056 pairs
print(mouse_db.head())
```

Columns: `ligand`, `receptor`, `n_sources`, `sources`. Sources are derived
from the native resources of the 10 evaluated methods (see paper Methods §S1.3).

## Citation

```bibtex
@article{spaccbench2026,
  title  = {SpaCCBench enables four-dimensional benchmarking of spatial cell-cell communication inference across diverse biological scenarios},
  author = {Xie, Xiaolan and collaborators},
  year   = {2026},
  note   = {Manuscript in preparation},
}
```

## Development

```bash
git clone https://github.com/coffeei1i/spaccbench.git
cd spaccbench
pip install -e ".[dev]"
pytest tests/
```

## License

MIT. See [`LICENSE`](LICENSE).
