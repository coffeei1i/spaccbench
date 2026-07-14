# SpaCCBench packaged data

This directory contains the small reusable resources distributed with the
SpaCCBench Python package.

- unified_lr_db_mouse.csv: 8,234 mouse ligand-receptor pairs.
- unified_lr_db_human.csv: 7,056 human ligand-receptor pairs.
- kegg_mouse.gmt: mouse KEGG pathway gene sets used by the D4 workflow.

The LR tables were produced by the repository's unified-database construction
workflow from the eligible native LR resources of the evaluated methods.
Columns are ligand, receptor, n_sources, and sources.

Large prepared scenario files are intentionally not versioned in Git. Put
tha.h5ad, ctx.h5ad, their candidate tables, expression-reference matrices,
and pathway-activity matrices in a local directory and set
SPACCBENCH_DATA_DIR to that directory. See docs/data_access.md and
tools/build_scenario.py.
