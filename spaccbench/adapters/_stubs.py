"""Companion-output adapters for manuscript methods.

These adapters keep the public method registry complete. For methods whose full
score matrices are provided through companion outputs or user-supplied files,
``load_scores`` points users to the shared adapter workflow.
"""
from __future__ import annotations

import pandas as pd

from spaccbench.adapters.base import BaseAdapter

_COMPANION_MESSAGE = (
    "Method {name!r} is supported through SpaCCBench's companion-output "
    "adapter workflow.\n\n"
    "To evaluate {name!r}:\n"
    "  1. Run {name!r} with its official workflow to produce a per-cell LR "
    "score matrix.\n"
    "  2. Provide that matrix through spaccbench.BaseAdapter.load_scores() "
    "or the examples/method_outputs layout.\n"
    "  3. Pass the adapter instance to spaccbench.evaluate(method=my_adapter, "
    "scenario=...).\n\n"
    "The examples directory documents the THA/CTX companion-output file layout "
    "used by the manuscript benchmark."
)


class _CompanionOutputAdapter(BaseAdapter):
    """Registry adapter for methods evaluated through companion score matrices."""

    def __init__(self, method_name: str):
        self.name = method_name

    def load_scores(self, scenario: str) -> pd.DataFrame:
        raise NotImplementedError(_COMPANION_MESSAGE.format(name=self.name))


COMPANION_METHODS: tuple[str, ...] = (
    "Spacia",
    "StereoSiTE",
    "SPIDER",
    "stLearn",
    "LARIS",
    "CellAgentChat",
    "stCase",
    "SpaCcLink",
)


def make_companion_registry() -> dict[str, _CompanionOutputAdapter]:
    """Return registry adapters for companion-output methods."""
    return {name: _CompanionOutputAdapter(name) for name in COMPANION_METHODS}
