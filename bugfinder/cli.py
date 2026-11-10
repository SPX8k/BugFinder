import argparse
import sys
from pathlib import Path

from bugfinder.database import Database
from bugfinder.reporting import export_report
from bugfinder.rules import scan_project

def main(argv=None):
    parser = argparse.ArgumentParser(prog="bugfinder", description="Local-first code analyzer")
    sub = parser.add_subparsers(dest="command", required=True)
    scan = sub.add_parser("scan", help="Scan a project directory")
    scan.add_argument("path", type=Path)
    scan.add_argument("--format", choices=["json", "html", "sarif", "txt", "csv"], default="txt")
    scan.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        findings = scan_project(args.path)
        data = [f.to_dict() for f in findings]
        Database().save_scan(str(args.path.resolve()), data)
        output = args.output or Path(f"bugfinder-report.{args.format}")
        export_report(findings, output, args.format)
        print(f"Scan complete: {len(findings)} finding(s).")
        print(f"Report: {output.resolve()}")
        return 1 if any(f.severity in {"high", "medium"} for f in findings) else 0
    except (OSError, ValueError) as exc:
        print(f"BugFinder: {exc}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
