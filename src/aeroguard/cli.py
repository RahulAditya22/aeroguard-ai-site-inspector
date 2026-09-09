"""Command-line interface for AeroGuard AI."""

import argparse
import json
import sys

from .config import settings
from .pipeline import InspectionPipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aeroguard",
        description="AI-assisted aerial site inspection and incident response.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect = subparsers.add_parser("inspect", help="Inspect one aerial/site image.")
    inspect.add_argument("image", help="Path to a JPG, PNG, or WEBP image.")

    batch = subparsers.add_parser("batch", help="Inspect every supported image in a directory.")
    batch.add_argument("directory", help="Directory containing aerial/site images.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        settings.validate(require_api_key=True)
        pipeline = InspectionPipeline(settings)
        if args.command == "inspect":
            record = pipeline.inspect_one(args.image)
            print(json.dumps(record.model_dump(mode="json"), indent=2))
        else:
            records = pipeline.inspect_directory(args.directory)
            print(json.dumps([r.model_dump(mode="json") for r in records], indent=2))
        return 0
    except Exception as exc:
        print(f"AeroGuard error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
