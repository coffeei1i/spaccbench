# Manuscript reproduction entry point

run_benchmark.py applies the shared SpaCCBench D1-D4 calculations to harmonized
cell-by-LR matrices from the ten methods evaluated in the manuscript.

## Inputs

- Prepared THA or CTX scenario files exposed through SPACCBENCH_DATA_DIR.
- Method outputs arranged as described in examples/README.md.
- One score matrix per method and scenario.

## Run

~~~bash
python manuscript_scripts/run_benchmark.py \
  --outputs examples/method_outputs \
  --scenarios tha ctx \
  --out manuscript_outputs/spaccbench_results.csv
~~~

Use --require-all for a complete ten-method run. Without it, missing method
outputs are reported and available methods are evaluated.

## Outputs

- spaccbench_results.csv: raw D1-D4 metrics by method and scenario.
- spaccbench_results_cohort.csv: rank scores and geometric composites.

These tables are the lightweight figure-table inputs. Raw public datasets and
large cell-level method outputs remain outside the Git repository.
