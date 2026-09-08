from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from . import __version__
from .inspector import inspect_policy


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="robot-skill", description="Create and validate portable robot-policy manifests.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)
    check = subparsers.add_parser("check", help="inspect a policy directory and report missing reproducibility evidence")
    check.add_argument("path", nargs="?", default=".", help="policy repository directory (default: current directory)")
    check.add_argument("--output", "-o", default="robot-skill.yaml", help="manifest output path, or '-' for stdout")
    check.add_argument("--format", choices=("text", "json"), default="text", help="diagnostic output format")
    check.add_argument("--no-write", action="store_true", help="inspect without writing a manifest")
    check.add_argument("--strict", action="store_true", help="return exit code 2 when required evidence is missing")
    validate = subparsers.add_parser("validate", help="validate an existing robot-skill YAML or JSON manifest")
    validate.add_argument("manifest", nargs="?", default="robot-skill.yaml")
    validate.add_argument("--format", choices=("text", "json"), default="text")
    return parser


def _write_manifest(manifest: dict, output: str) -> None:
    serialized = yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True)
    if output == "-":
        sys.stdout.write(serialized)
        return
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serialized, encoding="utf-8")


def _print_result(result, output_format: str) -> None:
    if output_format == "json":
        print(json.dumps(result.as_dict(), indent=2))
        return
    status = "PASS" if result.complete else "INCOMPLETE"
    print(f"{status}  {result.root}")
    print(f"Detected {len(result.detected_files)} evidence file(s); {len(result.errors)} error(s), {len(result.warnings)} warning(s).")
    for finding in result.findings:
        marker = "ERROR" if finding.severity == "error" else "WARN "
        print(f"{marker}  {finding.path}: {finding.message} [{finding.code}]")


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "validate":
            manifest_path = Path(args.manifest).expanduser().resolve()
            if not manifest_path.is_file():
                raise ValueError(f"manifest does not exist: {manifest_path}")
            from .inspector import _load_existing
            from .model import CheckResult
            from .schema import validate_manifest
            manifest = _load_existing(manifest_path)
            result = CheckResult(manifest_path.parent, manifest, validate_manifest(manifest), [manifest_path.name])
            _print_result(result, args.format)
            return 0 if result.complete else 2

        result = inspect_policy(Path(args.path))
        if not args.no_write and not any(item.code == "schema.invalid" for item in result.findings):
            _write_manifest(result.manifest, args.output)
        _print_result(result, args.format)
        return 2 if args.strict and not result.complete else 0
    except (OSError, ValueError) as exc:
        if getattr(args, "format", "text") == "json":
            print(json.dumps({"status": "error", "message": str(exc)}))
        else:
            print(f"ERROR  {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
