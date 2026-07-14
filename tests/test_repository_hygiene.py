"""Repository-level checks for public paths and documentation."""
from pathlib import Path


FORBIDDEN = (
    "/data3/",
    "Z:/",
    "Z:\\",
    "xyh_desktop",
    "benchmark_st_cellchat",
)


def test_public_text_files_do_not_expose_internal_paths():
    roots = [
        Path("README.md"),
        Path("docs"),
        Path("examples"),
        Path("manuscript_scripts"),
    ]
    files = [roots[0]]
    for root in roots[1:]:
        if root.exists():
            files.extend(
                path
                for path in root.rglob("*")
                if path.suffix in {".md", ".py"} and "superpowers" not in path.parts
            )
    for path in files:
        text = path.read_text(encoding="utf-8")
        assert not any(token in text for token in FORBIDDEN), path
