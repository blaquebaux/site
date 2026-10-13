#!/usr/bin/env python3
"""Create a machine-readable release manifest for a preview or deployment artifact."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "release-manifest.json"
ARTIFACTS = ["research-registry.json", "analysis/data.json", "bumble/feed.json", "bumble/briefings.json", "tracker/performance.json", "tracker/macro.json", "tracker/options.json"]


def timestamp(path: Path) -> str | None:
    try:
        payload = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    for key in ("generated_at", "asof", "updated_at", "updatedAt", "published_at"):
        if payload.get(key):
            return str(payload[key])
    articles = payload.get("articles")
    if isinstance(articles, list):
        published = [str(item["published_at"]) for item in articles if item.get("published_at")]
        if published:
            return max(published)
    return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    commit = os.environ.get("GITHUB_SHA") or subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    registry = json.loads((ROOT / "research-registry.json").read_text())
    manifest = {
        "schema_version": 1,
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "site_commit": commit,
        "registry": {"schema_version": registry["schema_version"], "generated_at": registry["generated_at"], "entries": len(registry["entries"])},
        "data_artifacts": {name: {"timestamp": timestamp(ROOT / name)} for name in ARTIFACTS},
        "performance_note": "Published research and simulated artifacts are not verified actual performance.",
    }
    args.output.write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
