# SpaCCBench: a scenario-aware four-dimensional benchmark for spatial cell-cell communication

[![CI](https://github.com/coffeei1i/spaccbench/actions/workflows/ci.yml/badge.svg)](https://github.com/coffeei1i/spaccbench/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

SpaCCBench evaluates spatial cell-cell communication inference methods along
four complementary dimensions: candidate-pair recovery (D1), expression
fidelity (D2), spatial coherence (D3), and receptor-pathway concordance (D4).
It provides a common adapter interface, species-stratified ligand-receptor
resources, and a reproducible workflow for harmonized cell-by-LR score
matrices.

## Installation

~~~bash
pip install git+https://github.com/coffeei1i/spaccbench.git
~~~

SpaCCBench requires Python 3.9 or newer.

## Quickstart

The unified ligand-receptor resources are packaged with the repository and work
without downloading a spatial dataset:

~~~python
from spaccbench import load_lr_db

mouse_lr = load_lr_db("mouse")
human_lr = load_lr_db("human")

print(mouse_lr.shape)  # (8234, 4)
print(human_lr.shape)  # (7056, 4)
print(mouse_lr.head())
~~~

Each table contains ligand, receptor, n_sources, and sources. The mouse resource
contains 8,234 pairs and is the resource used by the manuscript benchmark.

## Running a benchmark

Large prepared scenario files are intentionally kept outside Git. Put the
scenario files in one directory and set SPACCBENCH_DATA_DIR before evaluation:

~~~bash
export SPACCBENCH_DATA_DIR=/path/to/prepared_scenarios
spaccbench list-methods
spaccbench list-scenarios
spaccbench evaluate --method LIANA --scenario tha
~~~

On Windows PowerShell:

~~~powershell
$env:SPACCBENCH_DATA_DIR = "D:\path\to\prepared_scenarios"
spaccbench list-scenarios
~~~

The THA and CTX scenario definitions expect an AnnData file, an
expression-informed LR candidate table, an expression-derived reference
matrix, and a pathway-activity matrix. The benchmark uses 25 candidates per
sample as a fixed algorithmic setting. See docs/data_access.md for source
datasets and tools/build_scenario.py for preparation.

## Four-dimensional framework

| Dimension | Primary metric | Evaluation question |
|---|---|---|
| D1 | Candidate-pair recovery | Does a method emit non-trivial scores for the expression-informed candidates? |
| D2 | Pearson correlation | Do per-cell method scores agree with the expression-derived reference signal? |
| D3 | Moran's I | Are inferred communication scores spatially coherent? |
| D4 | Mean AUC | Do detected interactions track receptor-associated pathway activity? |

A cohort-level geometric composite summarizes rank-normalized D1-D4 scores
while penalizing uneven performance across dimensions.

## Evaluating another method

A method adapter returns a cells-by-LR pandas DataFrame:

~~~python
import pandas as pd
from spaccbench import BaseAdapter, evaluate


class MyMethodAdapter(BaseAdapter):
    name = "MyMethod"

    def __init__(self, scores_path):
        self.scores_path = scores_path

    def load_scores(self, scenario):
        return pd.read_csv(self.scores_path, index_col=0)


result = evaluate(
    method=MyMethodAdapter("my_outputs/tha.csv"),
    scenario="tha",
)
~~~

See docs/extending.md for the adapter contract and
docs/output_harmonization.md for the common score-matrix format.

## Reproducing the manuscript benchmark

The manuscript comparison starts from final cell-by-LR outputs produced by the
ten evaluated methods. The shared SpaCCBench layer then applies identical D1-D4
calculations to every method.

- docs/method_runs.md records method versions and expected output files.
- manuscript_scripts/run_benchmark.py evaluates harmonized outputs.
- examples/README.md gives the expected directory layout.
- docs/data_access.md maps scenarios to their public source datasets.

Raw public spatial-transcriptomics data and large method output matrices are not
duplicated in this Git repository.

## Citation

~~~bibtex
@article{spaccbench2026,
  title  = {SpaCCBench: a scenario-aware four-dimensional benchmark for spatial cell-cell communication},
  author = {Xu, Yiheng and Zhang, Zimu and Liu, Shuqi and Li, Xiao-Ming and Yu, Bin},
  year   = {2026},
  note   = {Submitted to BMC Bioinformatics}
}
~~~

## Development

~~~bash
git clone https://github.com/coffeei1i/spaccbench.git
cd spaccbench
pip install -e ".[dev]"
pytest tests/
~~~

## License

MIT. See LICENSE.
