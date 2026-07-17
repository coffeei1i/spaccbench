# Test suite

The automated suite validates SpaCCBench metric implementations, adapters,
resource packaging, metadata, and CLI behavior with compact synthetic inputs.
Complete ten-method comparisons use the prepared handoff matrices documented
in `docs/method_runs.md`.

| Test file | What it checks |
|---|---|
| `test_d1_detection.py` | Candidate-pair recovery, LR-name normalization, zero and missing-score handling |
| `test_d2_fidelity.py` | Pearson/Spearman fidelity, distribution distances, and degenerate inputs |
| `test_d3_spatial.py` | Moran's I, Geary's C, k-nearest-neighbor weights, and constant-score handling |
| `test_d4_pathway.py` | Receptor-pathway mapping, AUC calculation, permutations, and simple end-to-end cases |
| `test_composite.py` | Rank normalization and the four-dimensional geometric composite |
| `test_harmonization.py` | Shared LR normalization, duplicate merging, zero filling, and SPIDER path fallback |
| `test_adapters.py` | Registration and behavior of reference, companion-output, and custom adapters |
| `test_cli.py` | CLI help, method/scenario listing, version output, and user-facing errors |
| `test_resources.py` | Packaged human/mouse LR resources and external data-directory overrides |
| `test_metadata.py` | Public title, author list, and corresponding-author metadata |
| `test_tools.py` | Public script help commands, documented CLI options, and optional data dependencies |
| `test_repository_hygiene.py` | Absence of machine-specific internal paths in public text files |

Run the complete suite with:

```bash
pytest tests/
```

The manuscript-scale THA/CTX comparison is represented by the compact files in
`examples/results/`; metric recalculation uses the harmonized method outputs
and prepared scenario bundles described in the repository documentation.
