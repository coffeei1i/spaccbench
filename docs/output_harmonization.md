# Output harmonization

SpaCCBench compares methods after converting raw outputs into a common
cell-by-ligand-receptor score matrix. This document describes that common
format and how the manuscript scripts harmonized the ten evaluated methods.

## Common score matrix

Each evaluated method is represented as a `pandas.DataFrame`:

| Axis | Requirement |
|---|---|
| Rows | Cell or spot barcodes, aligned to `adata.obs_names` for the sample |
| Columns | Ligand-receptor pairs formatted as `Ligand-Receptor` |
| Values | Per-cell or per-spot communication scores; larger values mean stronger inferred communication |

For methods that naturally emit sender-receiver or cell-type-level outputs, the
manuscript wrappers extract or aggregate the receiver-side per-cell/spot score
used for the benchmark. Once a matrix has this shape, the same D1-D4 scoring
functions are used for every method.

## Normalization rules used in the manuscript scripts

The shared implementation is `spaccbench.harmonization.harmonize_score_matrix`.
Both the package adapters and `manuscript_scripts/run_benchmark.py` call this
function. The key rules are:

1. **Cell alignment.** Each raw matrix is reindexed to `adata.obs_names`.
   Rows are aligned to the benchmark cell index with `0.0` used for cells without an emitted score.
2. **Numeric coercion.** Numeric values are standardized and unavailable entries are represented as `0.0`.
3. **LR naming.** LR names are normalized to `Ligand-Receptor` by replacing
   separators such as `^`, `_`, or `::` where needed.
4. **Multi-receptor pairs.** For names such as `TGFB1-TGFBR1_TGFBR2`, the
   manuscript loaders keep the first receptor for cross-method matching
   (`TGFB1-TGFBR1`). Candidate matching also checks individual receptor
   variants where needed.
5. **Duplicate columns.** If LR names become duplicated after normalization,
   columns are summed.
6. **LR-pair coverage.** Pairs absent from a method output remain absent; each
   downstream metric records or skips them according to its documented rule.

These choices make all downstream metrics operate on the same matrix shape and keep comparisons focused on method signal rather than file-format differences.

## Method-specific raw files

The manuscript loaders read the following raw files.

| Method | Raw output pattern | Harmonization note |
|---|---|---|
| LIANA | `{sample}_spotxLR.csv` | Columns normalized with first-receptor matching. |
| LARIS | `{sample}_prepare_CellByLR.csv` | `Ligand::Receptor` columns are converted to `Ligand-Receptor`. |
| stLearn | `{sample}_SPOTxLR_lr_scores.csv` | Uses `spot_id` as index when present. |
| StereoSiTE | `{sample}/{sample}_LR_intensity_matrix.csv` or `{sample}_LR_intensity_matrix.csv` | Supports nested and flat layouts. |
| COMMOT | `{sample}/{sample}.csv` | Auto-detects index column. |
| SPIDER | `{sample}/{sample}.csv` or first CSV in matched sample directory | Supports exact and suffix-matched sample directories. |
| Spacia | `{sample}_cellxLR_spacia.csv` | Produced by aggregating Spacia per-interaction outputs. |
| CellAgentChat | `{sample}/out/cell_receiving_scores_FINAL.csv` | Numeric row indices are replaced by `adata.obs_names` when row counts match. |
| stCASE | `{sample}/{sample}.csv` | Auto-detects index column. |
| SpaCcLink | `{sample}_ALL_LR_cellxLR.csv` or `{sample}_LR_scores.csv` | Converts first `_` separator to `-` when no hyphen is present. |

## Public adapter contract

For the installable package, a method adapter only needs to implement:

```python
def load_scores(self, scenario: str) -> pandas.DataFrame:
    ...
```

The returned matrix should already follow the common score-matrix contract
above. See [`extending.md`](extending.md) for a minimal adapter example.

## How harmonized outputs enter D1-D4

After harmonization, SpaCCBench evaluates each method on the same per-sample
top-25 LR list:

- **D1 candidate-pair recovery:** whether each top-25 LR pair has a non-trivial
  score column.
- **D2 expression fidelity:** correlation between the per-cell method score and
  the receiver-centric expression-derived reference signal.
- **D3 spatial coherence:** Moran's I and Geary's C computed on the method
  score over the spatial graph.
- **D4 receptor-pathway concordance:** agreement between detected LR scores and
  receptor-associated KEGG pathway activity.

The composite score is calculated from rank-normalized D1-D4 scores, so the
benchmark summarizes cross-perspective consistency rather than a single
absolute accuracy value.
