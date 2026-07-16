# Shared manuscript-metric entry point

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
  --out manuscript_outputs/spaccbench_results.csv \
  --require-all
~~~

The complete THA/CTX command uses `--require-all` so a missing method matrix
cannot silently produce a partial comparison. Omit it only for an explicitly
incomplete exploratory run.

## Outputs

- spaccbench_results.csv: raw D1-D4 metrics by method and scenario.
- spaccbench_results_cohort.csv: rank scores and geometric composites.

These are metric and cohort tables, not finished manuscript figures. This
script does not download datasets, run external methods, or apply final figure
formatting. Raw public datasets and large cell-level method outputs remain
outside the Git repository.
