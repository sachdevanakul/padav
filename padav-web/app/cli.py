"""Maintenance commands:  python -m app.cli import-content content/ssc-cgl-sample.json"""
import argparse
import sys
from pathlib import Path

from pydantic import ValidationError

from app.core.exceptions import DomainError
from app.database.session import SessionLocal
from app.services.content import ContentImporter
from app.services.pia_content import PiaContentImporter


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


def import_pia(path: Path, activate: bool) -> int:
    with SessionLocal() as db:
        try:
            report = PiaContentImporter(db).import_file(path, activate=activate)
        except ValidationError as error:
            print(f"Invalid PIA content file:\n{error}", file=sys.stderr)
            return 1
        except DomainError as error:
            print(error.detail, file=sys.stderr)
            return 1
    print(f"Imported {report.items_created} item(s), skipped {report.items_skipped}; form: {report.form or 'none'}.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    commands = parser.add_subparsers(dest="command", required=True)
    imp = commands.add_parser("import-content", help="Import tests/questions from a JSON file")
    imp.add_argument("path", type=Path)
    pia = commands.add_parser("import-pia", help="Import PIA items and optionally a form from a JSON file")
    pia.add_argument("path", type=Path)
    pia.add_argument("--activate", action="store_true", help="Make the file's form the live form (needs a valid 50-item blueprint)")
    args = parser.parse_args(argv)
    if args.command == "import-pia":
        return import_pia(args.path, args.activate)
    return import_content(args.path)


if __name__ == "__main__":
    raise SystemExit(main())
