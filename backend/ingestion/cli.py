"""CLI for `grove-ingest`: argument parsing and command dispatch.

Stage logic lives in pipeline.py; this module is the operator interface.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
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

    audit = sub.add_parser("audit", parents=[src, work],
                           help="read-only audit of all stored Learn topics against fresh source drafts")
    snapshot = audit.add_mutually_exclusive_group(required=True)
    snapshot.add_argument("--database", type=Path, help="existing SQLite store (opened read-only)")
    snapshot.add_argument("--release", type=Path, help="release JSON snapshot")
    audit.add_argument("--media", type=Path, help="published media directory to check (no writes)")

    visuals = sub.add_parser("visuals", parents=[src], help="read-only whole-slide rendering into a fresh inspection directory")
    visuals.add_argument("--catalog", type=Path, required=True)
    visuals.add_argument("--output", type=Path, required=True)
    visuals.add_argument("--deck", action="append", required=True, help="catalog deck ID; repeat for another deck")
    visuals.add_argument("--slide", type=int, action="append", help="original slide position; default all selected slides")
    visuals.add_argument("--width", type=int, default=1600)

    pack = sub.add_parser("pack", parents=[src, work],
                          help="pack the validated catalog into a content pack")
    pack.add_argument("--version", required=True)
    pack.add_argument("--approve", action="store_true",
                      help="mark as human-approved (required for concepts to be included)")

    imp = sub.add_parser("import", parents=[work],
                         help="revalidate an approved pack against reviewed work, install media and import")
    imp.add_argument("--pack", type=Path, required=True)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "visuals":
        from .visuals import run_visuals
        try:
            catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
            report = run_visuals(catalog, args.source, args.output, args.deck, args.slide, args.width)
        except (ValueError, OSError, KeyError, TypeError) as exc:
            print(f"visual inspection failed: {exc}", file=sys.stderr)
            return 2
        rendered = sum(d["status"] == "rendered" for d in report["decks"])
        print(f"visual report -> {args.output / 'visual-report.json'} ({rendered}/{len(report['decks'])} decks rendered)")
        print("inspection evidence only; no catalog edited or content approved/imported")
        return 0 if rendered == len(report["decks"]) else 1
    if args.command == "audit":
        from .bench import read_release, run_bench
        try:
            if args.database:
                payload, metadata = read_release(args.database)
                # The snapshot preserves stored payload; row timestamps are printed separately.
                print(f"stored release: {metadata['release_id']} v{metadata['version']} imported {metadata['imported_at']}")
            else:
                payload = json.loads(args.release.read_text(encoding="utf-8"))
            report = run_bench(payload, args.source, args.work, args.media)
        except (ValueError, OSError, sqlite3.Error) as exc:
            print(f"audit failed: {exc}", file=sys.stderr)
            return 2
        print(f"bench -> {args.work / 'bench-report.html'}")
        print(json.dumps(report["counts"], ensure_ascii=True))
        print("draft inspection only; no release approved/imported; answers and visual meaning remain unverified")
        return 0 if report["validation"]["ok"] and not report["skipped_sources"] else 1
    if args.command == "run":
        return Pipeline(args.source, args.work, verbose=args.verbose).run_all()
    if args.command == "pack":
        return Pipeline(args.source, args.work).run_pack(args.version, args.approve)
    if args.command == "import":
        from .importing import install_media, prepare_import
        try:
            payload = json.loads(Path(args.pack).read_text(encoding="utf-8"))
            media_source = prepare_import(payload, args.work)
            from app.config import settings
            install_media(payload["media_ids"], media_source, settings.media_dir)
            from app.db import import_release
            created = import_release(payload["release_id"], payload["version"],
                                     {"generated_at": payload["generated_at"], "content_sha256": payload["content_sha256"],
                                      "schema_version": payload["schema_version"]}, payload)
        except (ValueError, OSError, sqlite3.Error) as exc:
            print(f"import refused: {exc}", file=sys.stderr)
            return 2
        print(f"imported {payload['release_id']} v{payload['version']}: {'created' if created else 'already present (immutable)'}")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
