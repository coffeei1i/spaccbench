"""Smoke tests for the adapter layer."""
import pandas as pd
import pytest

from spaccbench.adapters import (
    ALL_ADAPTERS,
    REFERENCE_ADAPTERS,
    BaseAdapter,
    COMMOTAdapter,
    LIANAAdapter,
    get_adapter,
    list_methods,
)
from spaccbench.adapters._stubs import COMPANION_METHODS


def test_reference_adapters_registered():
    assert "LIANA" in REFERENCE_ADAPTERS
    assert "COMMOT" in REFERENCE_ADAPTERS
    assert isinstance(REFERENCE_ADAPTERS["LIANA"], LIANAAdapter)
    assert isinstance(REFERENCE_ADAPTERS["COMMOT"], COMMOTAdapter)


def test_all_eight_companion_methods_registered():
    for m in COMPANION_METHODS:
        assert m in ALL_ADAPTERS


def test_list_methods_status_counts():
    rows = list_methods()
    bundled = [r for r in rows if r["status"] == "reference"]
    companion = [r for r in rows if r["status"] == "companion"]
    assert len(bundled) == 2
    assert len(companion) == len(COMPANION_METHODS)


def test_get_adapter_case_insensitive():
    a = get_adapter("liana")
    b = get_adapter("LIANA")
    assert isinstance(a, LIANAAdapter)
    assert a is b  # same instance from registry


def test_get_adapter_unknown_raises():
    with pytest.raises(KeyError):
        get_adapter("NotAMethod")


def test_companion_adapter_points_to_adapter_workflow():
    spacia = get_adapter("Spacia")
    with pytest.raises(NotImplementedError) as exc:
        spacia.load_scores("tha")
    assert "Spacia" in str(exc.value)
    assert "BaseAdapter" in str(exc.value)


def test_custom_adapter_subclass_works():
    class MyAdapter(BaseAdapter):
        name = "MyMethod"
        def load_scores(self, scenario):
            return pd.DataFrame({"lig1-rec1": [1.0]}, index=["c1"])

    a = MyAdapter()
    df = a.load_scores("tha")
    assert df.shape == (1, 1)


def test_baseadapter_cannot_be_instantiated_directly():
    with pytest.raises(TypeError):
        BaseAdapter()


def test_reference_adapter_guides_score_generation():
    """The reference adapter message points to the score-generation script."""
    adapter = LIANAAdapter()
    with pytest.raises(FileNotFoundError) as exc:
        adapter.load_scores("tha")
    msg = str(exc.value)
    assert "liana_tha_scores" in msg
    assert "tools/build_adapter_scores.py" in msg

def test_reference_adapter_loads_external_scores(tmp_path, monkeypatch):
    scores = pd.DataFrame(
        {"Lig1_Rec1": [1.0, 2.0]},
        index=["cell1", "cell2"],
    )
    scores.to_csv(tmp_path / "liana_tha_scores.csv")
    monkeypatch.setenv("SPACCBENCH_DATA_DIR", str(tmp_path))

    loaded = LIANAAdapter().load_scores("tha")

    assert list(loaded.columns) == ["lig1-rec1"]
    assert loaded.shape == (2, 1)
