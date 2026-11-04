#!/usr/bin/env python3
"""Enforce release binary/RSS budgets and require scoped notes for >10% growth."""
import argparse
import json
from pathlib import Path


def note_approves(notes_dir, platform_name, baseline, target, new_bytes):
    for path in sorted(Path(notes_dir).glob("*.json")):
        try:
            note = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if (note.get("approved") is True and note.get("platform") == platform_name
                and note.get("baseline_bytes") == baseline
                and note.get("target_bytes") == target
                and note.get("new_bytes") == new_bytes
                and isinstance(note.get("reason"), str) and note["reason"].strip()):
            return path
    return None


def check(metrics, budget, notes_dir, size_only=False):
    platform_name = metrics.get("platform")
    if platform_name not in budget["platforms"]:
        return [f"unknown platform: {platform_name}"], {}
    limits = budget["platforms"][platform_name]
    errors, report = [], {"platform": platform_name, "checks": []}
    if platform_name.startswith("linux-") and not size_only:
        for required in ("table-200-untagged", "table-200-tagged"):
            if required not in metrics.get("fixtures", {}):
                errors.append(f"missing required conformance fixture: {required}")
    stripped = metrics.get("stripped_size_bytes")
    baseline = limits["baseline_stripped_bytes"]
    maximum = limits["max_stripped_bytes"]
    if stripped is None:
        errors.append("missing stripped_size_bytes")
    else:
        report["checks"].append({"name": "stripped_size", "bytes": stripped, "max": maximum})
        if stripped > maximum:
            errors.append(f"stripped binary {stripped} exceeds max {maximum}")
        growth_limit = baseline * 1.10
        if stripped > growth_limit:
            new_bytes = stripped - baseline
            note = note_approves(notes_dir, platform_name, baseline, stripped, new_bytes)
            if not note:
                errors.append(f"stripped binary growth {stripped} > 110% of baseline {baseline}; approved scoped note required")
            else:
                report["approved_growth_note"] = str(note)
    for name, fixture in ([] if size_only else metrics.get("fixtures", {}).items()):
        rss_kb = fixture.get("rss_kb")
        if rss_kb is None:
            errors.append(f"fixture {name} missing Linux RSS (rss_kb)")
            continue
        rss_bytes = rss_kb * 1024
        rss_limits = limits.get("max_rss_bytes", {})
        if isinstance(rss_limits, dict):
            max_rss = rss_limits.get(name)
            if max_rss is None:
                errors.append(f"fixture {name} has no RSS budget")
                continue
        else:
            max_rss = rss_limits
        report["checks"].append({"name": f"rss:{name}", "bytes": rss_bytes, "max": max_rss})
        if rss_bytes > max_rss:
            errors.append(f"fixture {name} RSS {rss_bytes} exceeds max {max_rss}")
    report["ci_elapsed_seconds"] = metrics.get("ci_elapsed_seconds", 0)
    report["ci_elapsed_minutes"] = metrics.get("ci_elapsed_minutes", report["ci_elapsed_seconds"] / 60.0)
    return errors, report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--platform", required=True)
    ap.add_argument("--size-only", action="store_true", help="Build-stage size gate; conformance job separately requires both RSS fixtures")
    ap.add_argument("--binary", required=True)
    ap.add_argument("--metrics", required=True)
    ap.add_argument("--budgets", default="release/budgets.json")
    args = ap.parse_args()
    metrics = json.loads(Path(args.metrics).read_text(encoding="utf-8"))
    if metrics.get("platform") != args.platform or metrics.get("binary") != args.binary:
        raise SystemExit("metrics platform/binary does not match command line")
    budget_path = Path(args.budgets)
    budget = json.loads(budget_path.read_text(encoding="utf-8"))
    notes_dir = Path(budget.get("notes_directory", "release/budget-notes"))
    if not notes_dir.is_absolute():
        notes_dir = budget_path.parent / notes_dir
    errors, report = check(metrics, budget, notes_dir, size_only=args.size_only)
    print(json.dumps(report, indent=2))
    if errors:
        for error in errors:
            print(f"budget failure: {error}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
