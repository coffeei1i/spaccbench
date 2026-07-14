# Data access

All spatial transcriptomics datasets analyzed in the manuscript were obtained
from public repositories. Raw datasets are not duplicated in this Git
repository.

| Scenario | Public source |
|---|---|
| THA and CTX mouse adult-brain MERFISH | Allen Brain Cell Atlas, MERFISH-C57BL6J-638850: https://alleninstitute.github.io/abc_atlas_access/descriptions/MERFISH-C57BL6J-638850.html |
| Postnatal mouse brain Stereo-seq | CNGB accession CNP0003837: https://db.cngb.org/search/?q=CNP0003837 ; processed record: https://doi.org/10.12412/BSDC.1699433096.20001 |
| Mouse organogenesis Stereo-seq | MOSTA dataset in CNGB STOmics DB, associated with Chen et al. (2022) as cited in the manuscript |
| Mouse intracerebral haemorrhage Stereo-seq | CNGB STOmics DB accession STT0000047: https://db.cngb.org/stomics/stmich/ |
| Mouse 5XFAD 10x Visium | Gene Expression Omnibus accession GSE174321: https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE174321 |

## Prepared scenario files

For THA and CTX, tools/build_scenario.py produces the files expected by the
scenario registry:

- tha.h5ad or ctx.h5ad
- tha_top25.csv or ctx_top25.csv
- tha_gt_signal.parquet or ctx_gt_signal.parquet
- tha_pw_act.parquet or ctx_pw_act.parquet
- kegg_mouse.gmt

Store prepared files outside the repository and set SPACCBENCH_DATA_DIR to that
directory. The packaged kegg_mouse.gmt may be copied into the external scenario
directory when required by the scenario loader.

## Repository contents

The repository directly distributes the unified mouse and human LR tables and
the mouse KEGG gene-set file. Harmonized method outputs and figure-level
summary tables can be regenerated with manuscript_scripts/run_benchmark.py once
the public inputs and external-method outputs are available.
