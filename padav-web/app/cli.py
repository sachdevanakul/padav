"""Maintenance commands:  python -m app.cli import-content content/ssc-cgl-sample.json"""
import argparse
import sys
from pathlib import Path

from pydantic import ValidationError

from app.core.exceptions import DomainError
from app.database.session import SessionLocal
from app.services.content import ContentImporter


def import_content(path: Path) -> int:
    with SessionLocal() as db:
        try:
            report = ContentImporter(db).import_file(path)
        except ValidationError as error:
            print(f"Invalid content file:\n{error}", file=sys.stderr)
            return 1
        except DomainError as error:
            print(error.detail, file=sys.stderr)
            return 1
    print(f"Imported {report.created} test(s), skipped {report.skipped} existing.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    commands = parser.add_subparsers(dest="command", required=True)
    imp = commands.add_parser("import-content", help="Import tests/questions from a JSON file")
    imp.add_argument("path", type=Path)
    args = parser.parse_args(argv)
    return import_content(args.path)


if __name__ == "__main__":
    raise SystemExit(main())
