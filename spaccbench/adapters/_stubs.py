"""Stub adapters for methods not bundled with this distribution.

Eight of the ten methods evaluated in the SpaCCBench paper are not shipped
with pre-computed scores in this package. Calling ``load_scores`` on a stub
raises a ``NotImplementedError`` with instructions for the user.
"""
from __future__ import annotations

import pandas as pd

from spaccbench.adapters.base import BaseAdapter

_STUB_MESSAGE = (
    "Method {name!r} was evaluated in the SpaCCBench paper but its adapter "
    "is not bundled with this distribution.\n\n"
    "To run the evaluation for {name!r}:\n"
    "  1. Run {name!r} on your dataset to produce a per-cell LR score matrix.\n"
    "  2. Subclass spaccbench.BaseAdapter and implement load_scores() to "
    "return that matrix (see docs/extending.md).\n"
    "  3. Pass your adapter instance to spaccbench.evaluate(method=my_adapter, "
    "scenario=...).\n\n"
    "Full pre-computed scores for all 10 methods on the four scenarios in the "
    "paper are deposited at <Zenodo DOI to be added upon publication>."
)


class _StubAdapter(BaseAdapter):
    """A stub adapter that raises NotImplementedError with a guidance message."""

    def __init__(self, method_name: str):
        self.name = method_name

    def load_scores(self, scenario: str) -> pd.DataFrame:
        raise NotImplementedError(_STUB_MESSAGE.format(name=self.name))


STUB_METHODS: tuple[str, ...] = (
    "Spacia",
    "StereoSiTE",
    "SPIDER",
    "stLearn",
    "LARIS",
    "CellAgentChat",
    "stCASE",
    "SpaCcLink",
)


def make_stub_registry() -> dict[str, _StubAdapter]:
    """Return ``{method_name: _StubAdapter(method_name)}`` for all stub methods."""
    return {name: _StubAdapter(name) for name in STUB_METHODS}
