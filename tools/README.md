# tools/

One-time data-preparation scripts run on the server hosting the raw data.
The outputs of these scripts are committed to `spaccbench/data/` so that
end users can `pip install` and run `evaluate(...)` without re-running.

| Script | Purpose | Inputs | Outputs |
|---|---|---|---|
| `build_scenario.py` | Per-scenario adata, top-25 LR list, GT reference signal, pathway activity | raw `*.h5ad`, unified LR DB, KEGG GMT | `<scn>.h5ad`, `<scn>_top25.csv`, `<scn>_gt_signal.parquet`, `<scn>_pw_act.parquet` |
| `build_adapter_scores.py` | LIANA / COMMOT cell × LR score matrices | adapter raw outputs | `liana_<scn>_scores.parquet`, `commot_<scn>_scores.parquet` |

Typical workflow (server side):
```bash
# 1. Build the scenario bundle (slow: GSVA ~5-10 min per scenario)
python tools/build_scenario.py --scenario tha \
    --adata /path/to/raw/THA.h5ad \
    --lr-db ../sup/lrdb/unified_lr_db_mouse.csv \
    --kegg ../sup/pathway_db/kegg_mouse.gmt \
    --output-dir spaccbench/data/

python tools/build_scenario.py --scenario ctx \
    --adata /path/to/raw/CTX.h5ad \
    --lr-db ../sup/lrdb/unified_lr_db_mouse.csv \
    --kegg ../sup/pathway_db/kegg_mouse.gmt \
    --output-dir spaccbench/data/

# 2. Dump LIANA / COMMOT scores
python tools/build_adapter_scores.py --method LIANA --scenario tha \
    --raw /path/to/liana_result/THA/...
python tools/build_adapter_scores.py --method COMMOT --scenario tha \
    --raw /path/to/commot_result/THA/...
# ... repeat for ctx
```

After running, commit the resulting `spaccbench/data/*.{h5ad,csv,parquet,gmt}`
to the repo.
