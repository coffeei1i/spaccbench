"""Tests for packaged and externally supplied SpaCCBench resources."""
from spaccbench import load_lr_db
from spaccbench.resources import resolve_data_file


def test_packaged_lr_databases_have_expected_schema_and_size():
    expected = {"mouse": 8234, "human": 7056}
    for species, n_rows in expected.items():
        table = load_lr_db(species)
        assert len(table) == n_rows
        assert {"ligand", "receptor", "n_sources", "sources"}.issubset(
            table.columns
        )


def test_external_data_directory_overrides_packaged_resource(
    tmp_path, monkeypatch
):
    marker = tmp_path / "tha.h5ad"
    marker.write_bytes(b"external-scenario")
    monkeypatch.setenv("SPACCBENCH_DATA_DIR", str(tmp_path))
    assert resolve_data_file("tha.h5ad") == marker
