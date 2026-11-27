"""Command-line entry points for the rural-Florida scenario."""

import argparse
import hashlib
import json
from pathlib import Path

from .config import load_scenario
from .indoor import load_indoor_scenario, simulate_day
from .indoor_report import render_indoor_json, render_indoor_markdown
from .report import render_report


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="floridafarm",
        description=(
            "Rural-Florida agriculture planning fixtures. Labeled placeholder "
            "arithmetic only: never a measurement, design or performance claim."
        ),
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    rep = sub.add_parser("report", help="generate the Markdown scenario report")
    rep.add_argument("--config", default="config/scenario.json")
    rep.add_argument("--out", required=True)
    rep.add_argument("--title", default=None)

    val = sub.add_parser("validate", help="validate the scenario file")
    val.add_argument("--config", default="config/scenario.json")

    day = sub.add_parser(
        "simulate-day", help="run the bounded NON-OPERATIONAL indoor interval simulation"
    )
    day.add_argument("--config", default="config/indoor-simulation.json")
    day.add_argument("--json-out", required=True)
    day.add_argument("--markdown-out", required=True)
    day.add_argument("--water-handoff-out", type=Path,
                     help="Write reservoir capacity and the exact JSON report digest for water-budget replay")

    args = parser.parse_args(argv)
    if args.cmd == "simulate-day":
        if args.water_handoff_out is not None:
            paths = [Path(value).resolve() for value in
                     (args.config, args.json_out, args.markdown_out, args.water_handoff_out)]
            if len(set(paths)) != len(paths) or any(
                a.exists() and b.exists() and a.samefile(b)
                for i, a in enumerate(paths) for b in paths[:i]
            ):
                parser.error("config and the three output files must have distinct paths")
        indoor_cfg = load_indoor_scenario(args.config)
        result = simulate_day(indoor_cfg)
        report_bytes = render_indoor_json(result).encode("utf-8")
        Path(args.json_out).write_bytes(report_bytes)
        with open(args.markdown_out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(render_indoor_markdown(result))
        if args.water_handoff_out is not None:
            handoff = {
                "schema": "synthetic-farm-water-handoff/1",
                "report_sha256": hashlib.sha256(report_bytes).hexdigest(),
                "reservoir_capacity_l": indoor_cfg["water"]["capacity_l"],
            }
            args.water_handoff_out.write_bytes((json.dumps(handoff, indent=2) + "\n").encode("utf-8"))
        print("wrote", args.json_out, "and", args.markdown_out)
        return 0

    cfg = load_scenario(args.config)

    if args.cmd == "validate":
        print("scenario config valid:", cfg["scenario"]["name"])
        return 0

    markdown = render_report(cfg, title=args.title)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(markdown)
    print("wrote", args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
