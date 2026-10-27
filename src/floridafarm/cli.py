"""Command-line entry points for the rural-Florida scenario."""

import argparse

from .config import load_scenario
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

    args = parser.parse_args(argv)
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