"""Method adapters.

Reference adapters with standardized score-file templates:
    - LIANA (LIANAAdapter)
    - COMMOT (COMMOTAdapter)

Companion-output adapters:
    - Spacia, StereoSiTE, SPIDER, stLearn, LARIS, CellAgentChat, stCASE, SpaCcLink

User-supplied adapters should subclass ``BaseAdapter``.
"""
from __future__ import annotations

from spaccbench.adapters._csv_backed import CsvBackedAdapter
from spaccbench.adapters._stubs import COMPANION_METHODS, make_companion_registry
from spaccbench.adapters.base import BaseAdapter
from spaccbench.adapters.commot import COMMOTAdapter
from spaccbench.adapters.liana import LIANAAdapter

# Public registry: method name (case-insensitive lookup at call site) -> adapter instance.
REFERENCE_ADAPTERS: dict[str, BaseAdapter] = {
    "LIANA": LIANAAdapter(),
    "COMMOT": COMMOTAdapter(),
}

ALL_ADAPTERS: dict[str, BaseAdapter] = {
    **REFERENCE_ADAPTERS,
    **make_companion_registry(),
}


def get_adapter(name: str) -> BaseAdapter:
    """Look up an adapter by case-insensitive name."""
    lower_map = {k.lower(): v for k, v in ALL_ADAPTERS.items()}
    key = name.strip().lower()
    if key not in lower_map:
        raise KeyError(
            f"Unknown method {name!r}. Available: {sorted(ALL_ADAPTERS)}"
        )
    return lower_map[key]


def list_methods() -> list[dict[str, str]]:
    """Return method metadata (name, status: reference/companion)."""
    rows = []
    for k in ALL_ADAPTERS:
        status = "reference" if k in REFERENCE_ADAPTERS else "companion"
        rows.append({"name": k, "status": status})
    return rows


__all__ = [
    "BaseAdapter",
    "CsvBackedAdapter",
    "LIANAAdapter",
    "COMMOTAdapter",
    "REFERENCE_ADAPTERS",
    "ALL_ADAPTERS",
    "COMPANION_METHODS",
    "get_adapter",
    "list_methods",
]
