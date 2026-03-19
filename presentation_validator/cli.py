import argparse
import sys
from urllib.parse import urlparse
from presentation_validator.web import create_app
from presentation_validator.validator import check_manifest, fetch_manifest
from bottle import run
from pathlib import Path

import json
import requests

def is_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in ("http", "https")

def load_input(source: str):
    warnings = []
    """Load JSON from a file path or URL."""
    if is_url(source):
        manifest, warnings = fetch_manifest(source, True, None)
        return manifest, warnings
    else:
        with open(source, "r", encoding="utf-8") as f:
            return json.load(f), warnings


def run_validate(args):
    try:
        data, warnings = load_input(args.source)
    except Exception as e:
        print(f"❌ Failed to load input: {e}", file=sys.stderr)
        sys.exit(1)

    version = args.version

    try:
        result = check_manifest(data, version, args.source, warnings)
    except Exception as e:
        print(f"❌ Validation error: {e}", file=sys.stderr)
        sys.exit(1)

    # Pretty print JSON result
    print(json.dumps(result, indent=2))

    # Optional: exit non-zero if invalid
    if isinstance(result, dict) and result.get("okay") is False:
        sys.exit(2)


def run_serve(args):
    app = create_app()

    run(
        app,
        host=args.host,
        port=args.port,
        debug=args.debug,
        reloader=args.reload,
    )

def run_validate_dir(args):
    # open up the directory
    base = Path(args.directory)

    if not base.exists() or not base.is_dir():
        print(f"Error: '{base}' is not a valid directory")
        return 1

    # find all files with the specified extension
    json_files = list(base.rglob(f"*{args.extension}"))

    print(f"Found {len(json_files)} files with extension '{args.extension}'\n")

    # validate each file
    total = 0
    passed = 0
    failed = 0

    for path in json_files:
        total += 1
        print(f"Validating: {path}")

        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)

            result = check_manifest(data, args.version)

            # print results
            if result.passed:
                passed += 1
                print("  ✓ OK\n")
            else:
                failed += 1
                if result.error:
                    print(f"  ✗ FAIL: {result.error}\n")
                else:
                    print("  ✗ FAIL\n")
                    for error in result.errorList:
                        print(str(error))

                for w in result.warnings:
                    print(f"    ⚠ {w}")

        except Exception as e:
            failed += 1
            print(f"  ✗ ERROR: {e}")

    # summary
    print("\n--- Summary ---")
    print(f"Total:  {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    return 0 if failed == 0 else 1

def main():
    parser = argparse.ArgumentParser(
        prog="iiif-validator",
        description="IIIF Presentation Validator",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # ---- validate ----
    validate_parser = subparsers.add_parser(
        "validate", help="Validate a IIIF manifest from file or URL"
    )
    validate_parser.add_argument(
        "source",
        help="Path or URL to IIIF manifest JSON",
    )
    validate_parser.add_argument(
        "--version",
        help="IIIF Presentation version (e.g. 2.1, 3.0)",
        default=None,
    )
    validate_parser.set_defaults(func=run_validate)

    # ---- serve ----
    serve_parser = subparsers.add_parser(
        "serve", help="Run the validator web server"
    )
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8080)
    serve_parser.add_argument("--debug", action="store_true")
    serve_parser.add_argument("--reload", action="store_true")
    serve_parser.set_defaults(func=run_serve)

    # --- validate dir --- 
    dir_parser = subparsers.add_parser(
        "validate-dir",
        help="Validate all JSON manifests in a directory (recursively)",
    )

    dir_parser.add_argument(
        "directory",
        help="Directory to search for JSON files",
    )

    dir_parser.add_argument(
        "--version",
        help="IIIF Presentation version (e.g. 2.1, 3.0)",
        default=None,
    )

    dir_parser.add_argument(
        "--extension",
        default=".json",
        help="File extension to look for (default: .json)",
    )

    dir_parser.set_defaults(func=run_validate_dir)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()