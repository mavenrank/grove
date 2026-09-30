"""CLI for `grove-ingest`: argument parsing and command dispatch.

Stage logic lives in pipeline.py; this module is the operator interface.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .pipeline import Pipeline


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="grove-ingest",
                                description="Grove content ingestion pipeline")
    sub = p.add_subparsers(dest="command", required=True)

    src = argparse.ArgumentParser(add_help=False)
    src.add_argument("--source", type=Path, required=True,
                     help="directory containing source documents")
    work = argparse.ArgumentParser(add_help=False)
    work.add_argument("--work", type=Path, required=True,
                      help="working directory for catalogs, drafts, and packs")

    run = sub.add_parser("run", parents=[src, work],
                         help="discover, extract, classify, normalize, validate, organize")
    run.add_argument("-v", "--verbose", action="store_true")

    pack = sub.add_parser("pack", parents=[src, work],
                          help="pack the validated catalog into a content pack")
    pack.add_argument("--version", required=True)
    pack.add_argument("--approve", action="store_true",
                      help="mark as human-approved (required for concepts to be included)")

    imp = sub.add_parser("import", parents=[work],
                         help="import an approved pack into the backend content store")
    imp.add_argument("--pack", type=Path, required=True)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "run":
        return Pipeline(args.source, args.work, verbose=args.verbose).run_all()
    if args.command == "pack":
        return Pipeline(args.source, args.work).run_pack(args.version, args.approve)
    if args.command == "import":
        payload = json.loads(Path(args.pack).read_text(encoding="utf-8"))
        release_id = payload.get("release_id", "grove-ingested")
        version = payload.get("version", "0.0.0")
        if not payload.get("approved"):
            print("refusing to import a pack that is not approved", file=sys.stderr)
            return 2

        from app.db import import_release  # backend store

        created = import_release(release_id, version, {"generated_at": payload.get("generated_at")}, payload)
        print(f"imported {release_id} v{version}: {'created' if created else 'already present (immutable)'}")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
