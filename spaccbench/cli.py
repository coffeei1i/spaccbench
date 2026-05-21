"""Command-line interface for SpaCCBench.

Usage:
    spaccbench evaluate --method LIANA --scenario tha
    spaccbench evaluate --method LIANA --scenario tha --output result.json
    spaccbench list-methods
    spaccbench list-scenarios
    spaccbench version
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

from spaccbench import __version__


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="spaccbench",
        description="SpaCCBench: four-dimensional benchmark for spatial CCC inference",
    )
    sub = p.add_subparsers(dest="command", required=True)

    # evaluate
    pe = sub.add_parser("evaluate", help="Run D1-D4 evaluation for a method on a scenario")
    pe.add_argument("--method", required=True, help="Method name (e.g. LIANA, COMMOT)")
    pe.add_argument("--scenario", required=True, help="Scenario name (e.g. tha, ctx)")
    pe.add_argument(
        "--dims",
        nargs="+",
        default=["d1", "d2", "d3", "d4"],
        choices=["d1", "d2", "d3", "d4"],
        help="Dimensions to compute (default: all four)",
    )
    pe.add_argument("--n-perm", type=int, default=200, help="D4 permutations (default 200)")
    pe.add_argument("--seed", type=int, default=0, help="Random seed (default 0)")
    pe.add_argument(
        "--output",
        type=Path,
        help="Path to write result as JSON. If omitted, prints summary to stdout.",
    )

    # list-methods
    sub.add_parser("list-methods", help="Print available methods and their bundle status")

    # list-scenarios
    sub.add_parser("list-scenarios", help="Print available scenarios with metadata")

    # info
    pi = sub.add_parser("info", help="Print scenario metadata")
    pi.add_argument("--scenario", required=True)

    # version
    sub.add_parser("version", help="Print package version")

    return p


def _summarise(result: dict) -> str:
    """One-line per-dimension summary string."""
    lines = [
        f"method   = {result['method']}",
        f"scenario = {result['scenario']}",
    ]
    if "d1" in result:
        d = result["d1"]
        lines.append(f"D1 (detection): n_hit={d['n_hit']}/{d['n_total']} ({d['fraction']:.2%})")
    if "d2" in result:
        d = result["d2"]
        lines.append(
            f"D2 (fidelity):  Pearson r={d['pearson_r']:.3f}  "
            f"Spearman={d['spearman']:.3f}  cosine={d['cosine']:.3f}  JS={d['js']:.3f}"
        )
    if "d3" in result:
        d = result["d3"]
        lines.append(
            f"D3 (spatial):   Moran's I={d['morans_i']:.3f}  Geary's C={d['gearys_c']:.3f}"
        )
    if "d4" in result:
        d = result["d4"]
        p_str = f"{d['perm_p']:.3g}" if d['perm_p'] == d['perm_p'] else "n/a"  # NaN check
        lines.append(
            f"D4 (pathway):   mean AUC={d['mean_auc']:.3f}  "
            f"perm_p={p_str}  n_sig_lr={d['n_sig_lr']}"
        )
    if result.get("composite_geo") is not None:
        lines.append(f"composite_geo = {result['composite_geo']:.3f}")
    return "\n".join(lines)


def _to_json_safe(result: dict) -> dict:
    """Strip non-JSON-serialisable fields (per_lr DataFrames) and convert NaN."""
    out: dict = {}
    for k, v in result.items():
        if isinstance(v, dict):
            inner = {}
            for kk, vv in v.items():
                if isinstance(vv, pd.DataFrame):
                    inner[kk] = vv.to_dict(orient="records")
                elif isinstance(vv, float) and vv != vv:  # NaN
                    inner[kk] = None
                else:
                    inner[kk] = vv
            out[k] = inner
        elif isinstance(v, float) and v != v:
            out[k] = None
        else:
            out[k] = v
    return out


def cmd_evaluate(args: argparse.Namespace) -> int:
    from spaccbench import evaluate
    result = evaluate(
        method=args.method,
        scenario=args.scenario,
        dimensions=args.dims,
        n_perm=args.n_perm,
        seed=args.seed,
    )
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(_to_json_safe(result), indent=2, default=str))
        print(f"Wrote {args.output}", file=sys.stderr)
    print(_summarise(result))
    return 0


def cmd_list_methods(args: argparse.Namespace) -> int:
    from spaccbench import list_methods
    rows = list_methods()
    width = max(len(r["name"]) for r in rows)
    for r in rows:
        marker = "✓" if r["status"] == "bundled" else "·"
        print(f"  {marker}  {r['name']:<{width}}  ({r['status']})")
    print(f"\n{sum(1 for r in rows if r['status'] == 'bundled')} bundled, "
          f"{sum(1 for r in rows if r['status'] == 'stub')} stub. "
          f"See docs/extending.md to add your own.")
    return 0


def cmd_list_scenarios(args: argparse.Namespace) -> int:
    from spaccbench import list_scenarios
    rows = list_scenarios()
    for r in rows:
        print(f"  {r['name']:<8}  {r['platform']:<10}  {r['n_cells_expected']:>6} cells  {r['title']}")
    return 0


def cmd_info(args: argparse.Namespace) -> int:
    from spaccbench.scenarios import SCENARIO_REGISTRY
    if args.scenario not in SCENARIO_REGISTRY:
        print(f"Unknown scenario {args.scenario!r}. Available: "
              f"{sorted(SCENARIO_REGISTRY)}", file=sys.stderr)
        return 1
    meta = SCENARIO_REGISTRY[args.scenario]
    for k, v in meta.items():
        if k == "files":
            print(f"  files:")
            for fk, fv in v.items():
                print(f"    {fk:<10} {fv}")
        else:
            print(f"  {k:<20} {v}")
    return 0


def cmd_version(args: argparse.Namespace) -> int:
    print(f"spaccbench {__version__}")
    return 0


COMMANDS = {
    "evaluate":       cmd_evaluate,
    "list-methods":   cmd_list_methods,
    "list-scenarios": cmd_list_scenarios,
    "info":           cmd_info,
    "version":        cmd_version,
}


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    handler = COMMANDS.get(args.command)
    if handler is None:
        parser.print_help()
        return 1
    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
