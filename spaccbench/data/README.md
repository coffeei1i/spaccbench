# SpaCCBench packaged data

This directory contains the small reusable resources distributed with the
SpaCCBench Python package.

- unified_lr_db_mouse.csv: 8,234 mouse ligand-receptor pairs.
- unified_lr_db_human.csv: 7,056 human ligand-receptor pairs.
- kegg_mouse.gmt: mouse KEGG pathway gene sets used by the D4 workflow.
The human LR table is a standalone resource; its presence does not indicate
that a human evaluation scenario is registered in this package release.


The LR tables are versioned benchmark resources. Their `sources` column records
the contributing LR resources, and `n_sources` gives the corresponding source
count. The distributed tables therefore preserve the provenance used by the
benchmark. Columns are `ligand`, `receptor`, `n_sources`, and `sources`.

Large prepared scenario files are intentionally not versioned in Git. Put
tha.h5ad, ctx.h5ad, their candidate tables, expression-reference matrices,
and pathway-activity matrices in a local directory and set
SPACCBENCH_DATA_DIR to that directory. See docs/data_access.md and
tools/build_scenario.py.
