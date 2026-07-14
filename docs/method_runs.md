# Running external methods for SpaCCBench

The manuscript benchmark evaluates ten spatial cell-cell communication methods.
Each method is run with its official implementation and native model settings.
SpaCCBench begins after the method output has been converted to a cell-by-LR
score matrix.

## Method versions and handoff files

| Method | Official implementation | Manuscript version | Expected handoff |
|---|---|---:|---|
| LIANA | https://liana-py.readthedocs.io/ | 1.5.0 | sample_spotxLR.csv |
| COMMOT | https://commot.readthedocs.io/ | 0.0.3 | sample/sample.csv |
| stLearn | https://stlearn.readthedocs.io/ | 1.2.2 | sample_SPOTxLR_lr_scores.csv |
| SPIDER | spider-st package and tutorial | 0.2.5 | sample-level cells-by-LR CSV |
| Spacia | https://github.com/yunguan-wang/Spacia | commit 11809bb | sample_cellxLR_spacia.csv |
| StereoSiTE | official StereoSiTE release | 2.2.2 | sample_LR_intensity_matrix.csv |
| CellAgentChat | https://github.com/mcgilldinglab/CellAgentChat | 0.1.2 | out/cell_receiving_scores_FINAL.csv |
| stCASE | https://github.com/STCaser/STCase | 1.0.0 | sample/sample.csv |
| LARIS | official LARIS workflow | 0.9.3 | sample_prepare_CellByLR.csv |
| SpaCcLink | https://github.com/LiangYu-Xidian/SpaCcLink | commit bc80c22 | sample_ALL_LR_cellxLR.csv |

The version numbers above match the manuscript. For repositories without a
tagged release, the tested commit is recorded.

## 1. Prepare scenario data

Download the public datasets listed in data_access.md and prepare the scenario
files with tools/build_scenario.py. Keep these large files outside Git and set
SPACCBENCH_DATA_DIR to their directory.

~~~bash
export SPACCBENCH_DATA_DIR=/path/to/prepared_scenarios
~~~

## 2. Run each external method

Run the official workflow for each method against the same input sample.
Export the final receiving-cell or spot-level communication scores using the
handoff name above. The common matrix contract is described in
output_harmonization.md.

Method-specific installations remain separate because their dependency stacks
are mutually incompatible. SpaCCBench does not redistribute those packages.

## 3. Arrange harmonized outputs

Place the final matrices under examples/method_outputs using the layout in
examples/README.md. Large matrices are ignored by Git.

## 4. Run the shared D1-D4 layer

~~~bash
python manuscript_scripts/run_benchmark.py \
  --outputs examples/method_outputs \
  --scenarios tha ctx \
  --out manuscript_outputs/spaccbench_results.csv \
  --require-all
~~~

The command writes a raw D1-D4 table and a cohort table containing
rank-normalized metrics and the geometric composite.

## Reproducibility boundary

SpaCCBench provides the common LR resources, data contract, adapter interface,
and D1-D4 calculations. External methods remain governed by their own
repositories and licenses. Raw public datasets are referenced by accession
rather than copied into this repository.
