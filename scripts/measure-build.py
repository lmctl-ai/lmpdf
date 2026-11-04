#!/usr/bin/env python3
"""Measure a build/binary and optional conformance fixture without dependencies."""
import argparse
import json
import os
import platform as platform_module
import shutil
import shlex
import sys
from datetime import datetime, timezone
import subprocess
import tempfile
import time
from pathlib import Path


def _command(value):
    return value if isinstance(value, list) else shlex.split(value)


def run_measured(command, cwd=None):
    started = time.monotonic()
    rss_kb = None
    if sys.platform.startswith("linux") and Path("/usr/bin/time").exists():
        result = subprocess.run(["/usr/bin/time", "-f", "%M", "--", *_command(command)], cwd=cwd,
                                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        lines = result.stderr.splitlines()
        if lines and lines[-1].isdigit():
            rss_kb = int(lines[-1])
            result.stderr = "\n".join(lines[:-1])
    else:
        result = subprocess.run(_command(command), cwd=cwd, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result, time.monotonic() - started, rss_kb


def stripped_size(binary):
    path = Path(binary)
    with tempfile.TemporaryDirectory(prefix="lmpdf-budget-") as tmp:
        copy = Path(tmp) / path.name
        shutil.copy2(path, copy)
        strip = shutil.which("strip")
        if not strip:
            return path.stat().st_size, False
        flags = ["-x"] if sys.platform == "darwin" else (["--strip-all"] if os.name != "nt" else [])
        if not flags:
            return path.stat().st_size, False
        result = subprocess.run([strip, *flags, str(copy)], stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True)
        if result.returncode:
            return path.stat().st_size, False
        return copy.stat().st_size, True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--platform", required=True, dest="target_platform")
    ap.add_argument("--binary", required=True)
    ap.add_argument("--output", default="build-metrics.json")
    ap.add_argument("--build-command", help="command to run before measuring the binary")
    ap.add_argument("--fixture-command", action="append", default=[],
                    help="fixture command; repeat for tagged/untagged measurements")
    ap.add_argument("--fixture-name", action="append", default=[])
    ap.add_argument("--ci-job", action="append", default=[],
                    help="measured CI job command, included in elapsed aggregation")
    args = ap.parse_args()
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    started_at = datetime.now(timezone.utc)
    metrics = {"version": 1, "platform": args.target_platform, "binary": args.binary,
               "host": platform_module.platform(), "jobs": [], "fixtures": {}}
    failure = 0
    if args.build_command:
        result, elapsed, rss = run_measured(args.build_command)
        metrics["jobs"].append({"name": "build", "elapsed_seconds": elapsed, "returncode": result.returncode})
        if result.returncode:
            print(result.stdout, end="", flush=True)
            print(result.stderr, end="", flush=True)
            failure = result.returncode
    binary = Path(args.binary)
    if not binary.is_file():
        message = f"binary does not exist: {binary}"
        metrics["ci_elapsed_seconds"] = sum(j["elapsed_seconds"] for j in metrics["jobs"])
        metrics["ci_elapsed_minutes"] = metrics["ci_elapsed_seconds"] / 60.0
        metrics["started_at_utc"] = started_at.isoformat()
        metrics["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
        metrics["success"] = False
        metrics["error"] = message
        Path(args.output).write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
        print(message)
        raise SystemExit(1)
    metrics["binary_size_bytes"] = binary.stat().st_size
    metrics["stripped_size_bytes"], metrics["stripped_supported"] = stripped_size(binary)
    for index, command in enumerate(args.fixture_command):
        name = args.fixture_name[index] if index < len(args.fixture_name) else f"fixture-{index + 1}"
        result, elapsed, rss = run_measured(command)
        metrics["fixtures"][name] = {"elapsed_seconds": elapsed, "rss_kb": rss,
                                      "returncode": result.returncode}
        if result.returncode:
            print(result.stdout, end="", flush=True)
            print(result.stderr, end="", flush=True)
            failure = failure or result.returncode
    for command in args.ci_job:
        result, elapsed, rss = run_measured(command)
        metrics["jobs"].append({"name": f"ci-{len(metrics['jobs'])}",
                                 "elapsed_seconds": elapsed, "rss_kb": rss,
                                 "returncode": result.returncode})
        if result.returncode:
            print(result.stdout, end="", flush=True)
            print(result.stderr, end="", flush=True)
            failure = failure or result.returncode
    metrics["ci_elapsed_seconds"] = sum(j["elapsed_seconds"] for j in metrics["jobs"])
    metrics["ci_elapsed_minutes"] = metrics["ci_elapsed_seconds"] / 60.0
    metrics["started_at_utc"] = started_at.isoformat()
    metrics["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    metrics["success"] = failure == 0
    Path(args.output).write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    raise SystemExit(failure)


if __name__ == "__main__":
    main()
