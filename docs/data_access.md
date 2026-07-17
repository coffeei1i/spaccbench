# Data access

All spatial transcriptomics datasets analyzed in the manuscript were obtained
from public repositories. Raw datasets are not duplicated in this Git
repository.

| Scenario | Public source |
|---|---|
| THA and CTX mouse adult-brain MERFISH | Allen Brain Cell Atlas, MERFISH-C57BL6J-638850: https://alleninstitute.github.io/abc_atlas_access/descriptions/MERFISH-C57BL6J-638850.html |
| Postnatal mouse brain Stereo-seq | CNGB accession CNP0003837: https://db.cngb.org/search/?q=CNP0003837 ; processed record: https://doi.org/10.12412/BSDC.1699433096.20001 |
| Mouse organogenesis Stereo-seq | MOSTA, CNGB STOmics DB: processed dataset STDS0000058 (https://doi.org/10.26036/STDS0000058); raw Stereo-seq accession CNP0001543; portal: https://db.cngb.org/stomics/mosta/ |
| Mouse intracerebral haemorrhage Stereo-seq | CNGB STOmics DB accession STT0000047: https://db.cngb.org/stomics/stmich/ |
| Mouse 5XFAD 10x Visium | Gene Expression Omnibus accession GSE174321: https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE174321 |
The installable package currently registers only `tha` and `ctx`. The other
rows document dataset provenance for the broader manuscript analysis; they are
not runnable SpaCCBench scenario definitions in this repository.


## Prepared scenario files

For THA and CTX, `tools/build_scenario.py` produces four prepared files per
scenario:

- tha.h5ad or ctx.h5ad
- tha_top25.csv or ctx_top25.csv
- tha_gt_signal.parquet or ctx_gt_signal.parquet
- tha_pw_act.parquet or ctx_pw_act.parquet

Store them outside the repository and set `SPACCBENCH_DATA_DIR` to that
directory. The loader uses the packaged `kegg_mouse.gmt` unless an external
file with the same name is supplied.

## Repository contents

The repository distributes the unified mouse and human LR tables, the mouse
KEGG gene-set file, static manuscript summary tables, and the shared metric
implementation. Given prepared scenario files and final external-method
matrices, `manuscript_scripts/run_benchmark.py` recomputes metric and cohort
tables that can be used for independent plotting and method comparison.
