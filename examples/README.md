# SpaCCBench examples

This directory contains notebooks and the expected layout for harmonized method
outputs. Prepared scenario files must be available through
SPACCBENCH_DATA_DIR.

The single end-to-end notebook,
`evaluate_all_methods_CTX_THA.ipynb`, is the canonical workflow for all
available manuscript method outputs on THA and CTX.

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
  --out manuscript_outputs/spaccbench_results.csv
~~~

The command accepts --methods and --scenarios for selected subsets.
