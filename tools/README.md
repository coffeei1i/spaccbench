# Data preparation tools

These scripts create local SpaCCBench scenario bundles and harmonized method
score files. Large generated files are deliberately not packaged or committed
to Git.

| Script | Purpose | Inputs | Outputs |
|---|---|---|---|
| `build_scenario.py` | Per-scenario AnnData, candidate LR list, expression-derived reference signal, pathway activity | raw `*.h5ad`, unified LR DB, KEGG GMT | `<scn>.h5ad`, `<scn>_top25.csv`, `<scn>_gt_signal.parquet`, `<scn>_pw_act.parquet` |
| `build_adapter_scores.py` | Normalize a final cell-by-LR matrix | final CSV or parquet matrix | `<method>_<scn>_scores.parquet` |

`build_adapter_scores.py` accepts any method name when its input is already a
final cell-by-LR matrix. Its row index must already contain the correct cell or
spot barcodes; the tool does not infer barcodes from integer row numbers.
For LIANA and COMMOT, the generated filename is recognized by the built-in
file-backed adapters. For other method names, the parquet file is only a
standardized artifact; provide a custom adapter or place the corresponding CSV
in the manuscript handoff layout. This command does not register an adapter.

Install the preparation dependencies first:

```bash
pip install -e ".[data,pathway]"
```

The extras provide parquet output and the GSVA dependency used for D4.

Build scenario bundles in a local data directory:

```bash
# 1. Build the scenario bundle (slow: GSVA ~5-10 min per scenario)
python tools/build_scenario.py --scenario tha \
    --adata /path/to/raw/THA.h5ad \
    --lr-db spaccbench/data/unified_lr_db_mouse.csv \
    --kegg spaccbench/data/kegg_mouse.gmt \
    --output-dir /path/to/spaccbench_scenarios

python tools/build_scenario.py --scenario ctx \
    --adata /path/to/raw/CTX.h5ad \
    --lr-db spaccbench/data/unified_lr_db_mouse.csv \
    --kegg spaccbench/data/kegg_mouse.gmt \
    --output-dir /path/to/spaccbench_scenarios

# 2. Harmonize a final cell-by-LR score matrix
python tools/build_adapter_scores.py --method LIANA --scenario tha \
    --input-csv /path/to/THA_spotxLR.csv \
    --output-dir /path/to/spaccbench_scenarios
python tools/build_adapter_scores.py --method COMMOT --scenario tha \
    --input-csv /path/to/THA_commot.csv \
    --output-dir /path/to/spaccbench_scenarios
```

Set `SPACCBENCH_DATA_DIR` to the generated scenario directory before
evaluation. Keep generated `.h5ad`, parquet, method-output, and manuscript
output files outside Git; the repository ignores these large artifacts.
