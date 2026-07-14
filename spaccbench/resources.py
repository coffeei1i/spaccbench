"""Resolve small packaged resources and externally prepared scenario data."""
from __future__ import annotations

import os
from importlib.resources import as_file, files
from pathlib import Path


def resolve_data_file(filename: str) -> Path:
    """Return a data file from SPACCBENCH_DATA_DIR or package data.

    Large prepared scenario files can be kept outside the Git repository by
    setting SPACCBENCH_DATA_DIR. Small reusable resources remain bundled with
    the installed package.
    """
    external = os.environ.get("SPACCBENCH_DATA_DIR")
    if external:
        candidate = Path(external).expanduser().resolve() / filename
        if candidate.is_file():
            return candidate

    resource = files("spaccbench") / "data" / filename
    with as_file(resource) as path:
        candidate = Path(path)
        if candidate.is_file():
            return candidate

    locations = ["the packaged data directory"]
    if external:
        locations.insert(0, f"SPACCBENCH_DATA_DIR={external}")
    raise FileNotFoundError(
        f"SpaCCBench data file {filename!r} was not found in "
        + " or ".join(locations)
        + "."
    )
