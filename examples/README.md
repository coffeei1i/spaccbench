# SpaCCBench examples

This directory contains notebooks and the expected layout for harmonized method
outputs. Prepared scenario files must be available through
SPACCBENCH_DATA_DIR.
`examples/method_outputs/` is intentionally absent from a fresh clone and is
ignored by Git; users must populate it with final external-method matrices.


The shared evaluation notebook, `evaluate_all_methods_CTX_THA.ipynb`, applies
the D1-D4 framework to prepared THA and CTX scenario bundles and harmonized
cell-by-LR outputs from the evaluated methods. It validates that every required
input is available before producing the complete ten-method comparison, so
missing inputs are reported as errors rather than silently omitted.

## Output layout

~~~text
examples/method_outputs/
  liana/THA/THA_spotxLR.csv
  liana/CTX/CTX_spotxLR.csv
  commot/THA/THA/THA.csv
  commot/CTX/CTX/CTX.csv
  stlearn/THA/THA_SPOTxLR_lr_scores.csv
  stlearn/CTX/CTX_SPOTxLR_lr_scores.csv
  spider/THA/THA.csv
  spider/CTX/CTX.csv
  spacia/THA/THA_cellxLR_spacia.csv
  spacia/CTX/CTX_cellxLR_spacia.csv
  stereosite/THA/THA_LR_intensity_matrix.csv
  stereosite/CTX/CTX_LR_intensity_matrix.csv
  cellagentchat/THA/out/cell_receiving_scores_FINAL.csv
  cellagentchat/CTX/out/cell_receiving_scores_FINAL.csv
  stcase/THA/THA.csv
  stcase/CTX/CTX.csv
  laris/THA/THA_prepare_CellByLR.csv
  laris/CTX/CTX_prepare_CellByLR.csv
  spacclink/THA/THA_ALL_LR_cellxLR.csv
  spacclink/CTX/CTX_ALL_LR_cellxLR.csv
~~~

## Run all available methods

~~~bash
python manuscript_scripts/run_benchmark.py \
  --outputs examples/method_outputs \
  --scenarios tha ctx \
  --out manuscript_outputs/spaccbench_results.csv \
  --require-all
~~~

Use `--methods` or `--scenarios` only when an intentionally incomplete
subset is required. Such output is not the complete ten-method THA/CTX
comparison.
