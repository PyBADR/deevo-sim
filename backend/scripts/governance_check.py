#!/usr/bin/env python3
"""
Impact Observatory — Governance Check CLI

Verifies that the canonical scenario registry is consistent with all
downstream components (bridge, catalog, normalize, MVOE config).

Exit codes:
    0  — all governance checks passed
    1  — one or more BLOCKER checks failed (deployment should be blocked)
    2  — unexpected error (module import failure, etc.)

Usage:
    # From project root:
    python backend/scripts/governance_check.py
    python backend/scripts/governance_check.py --json
    python backend/scripts/governance_check.py --strict   # fail on WARN too

CI integration:
    # Add to Procfile / railway.toml pre-deploy hook or GitHub Actions:
    python backend/scripts/governance_check.py || exit 1
"""

import argparse
import json
import pathlib
import sys

# Ensure backend package is importable regardless of CWD
BACKEND_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Impact Observatory governance consistency check",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON output (for CI artifact storage)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Also fail on WARN checks (not just FAIL)",
    )
    args = parser.parse_args()

    # Import governance module
    try:
        from app.governance.governor import run_governance_checks, CheckStatus
    except ImportError as e:
        msg = f"ERROR: Cannot import governance module: {e}\n"
        msg += "Ensure you are running from the project root or have set PYTHONPATH.\n"
        print(msg, file=sys.stderr)
        sys.exit(2)

    # Run checks
    try:
        result = run_governance_checks()
    except Exception as e:
        print(f"ERROR: Governance check raised an exception: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(2)

    # Output
    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(result.summary())

    # Exit code
    if not result.passed:
        sys.exit(1)

    if args.strict:
        warn_count = sum(
            1 for c in result.checks if c.status == CheckStatus.WARN
        )
        if warn_count > 0:
            if not args.json:
                print(f"  [--strict] Failing on {warn_count} WARN check(s).\n")
            sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
