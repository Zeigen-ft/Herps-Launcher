"""Headless Step 1 commands. No Qt, JVM, network fetch, or game launch required."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from ..core import Launcher
from .adapter import PortPackAdapter, REQUIRES_PORTING

COMMANDS = ("check", "analyze-pack", "port", "export-report")


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="Herps Java mods: static analysis and local data-tier carry-over. No Java bridge or gameplay testing.")
    commands = root.add_subparsers(dest="command", required=True)
    for name in COMMANDS:
        command = commands.add_parser(name)
        command.add_argument("--support-dir", type=Path, help="Optional launcher support directory (defaults to the existing OS path helper)")
        command.add_argument("--profile", help="Existing launcher profile; uses saved selection by default")
        command.add_argument("--port-pack", type=Path, help="Trusted horizon-port-pack executable built from the pinned engine")
        command.add_argument("--timeout", type=float, default=120, help="Per-command timeout in seconds")
        if name == "export-report":
            command.add_argument("report", type=Path, help="A profile-local run's report.json")
            command.add_argument("output", type=Path)
            command.add_argument("--format", choices=("json", "text"), default="json")
        else:
            command.add_argument("source", type=Path, help="Java JAR for check; local JAR or pack/instance for port; pack/instance for analyze-pack")
            command.add_argument("--dependencies", type=Path, help="User-provided mod/instance directory; never downloads files")
            command.add_argument("--acknowledge-restricted-license", action="store_true",
                help="Acknowledge that check/port generates local data ports of ND/NC/restricted content. Review the licence first; this grants no redistribution rights.")
    return root


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    try:
        if not math.isfinite(args.timeout) or args.timeout <= 0:
            raise ValueError("Timeout must be positive")
        launcher = Launcher(args.support_dir)
        if args.profile:
            if args.profile not in launcher.config["profiles"]:
                raise ValueError("Select an existing launcher profile")
            # A command's explicit selection does not change GUI preferences.
            launcher.config["profile"] = args.profile
        adapter = PortPackAdapter(launcher, executable=args.port_pack, timeout=args.timeout)
        if args.command == "export-report":
            output = adapter.export_report(args.report, args.output, args.format)
            print(json.dumps({"exported": str(output), "format": args.format}))
            return 0
        operation = getattr(adapter, args.command.replace("-", "_"))
        result = operation(args.source, dependencies=args.dependencies,
                           acknowledge_restricted=args.acknowledge_restricted_license)
        print(json.dumps(result.to_dict(), indent=2))
        return 0 if result.status == REQUIRES_PORTING else 1
    except (OSError, ValueError) as error:
        print(json.dumps({"status": "Unsupported", "diagnostics": [
            {"code": "insufficient_evidence", "message": str(error)}],
            "test_execution": None, "java_bridge_available": False, "playable_verified": False}))
        return 1
