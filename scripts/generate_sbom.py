"""A software bill of materials for the release, in CycloneDX JSON.

    python scripts/generate_sbom.py --output dist/sbom.json

Every release says what is inside it. Without that, "is this affected by the
thing announced this morning?" is answered by reading a lock file from
whichever commit somebody guesses was the one that shipped - and the answer
arrives a day late.

CycloneDX rather than SPDX because GitHub, Dependency-Track and OpenSSF
Scorecard all read it, and this file is meant to be read by a machine that is
looking for a package name and a version.

No third-party dependency: the input is the lock file this repository already
commits, and the output is a small JSON document. A generator that has to be
installed first is a generator that gets skipped when the release is urgent.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tomllib
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
LOCK = ROOT / "requirements-dev.lock"
PIN = re.compile(r"^([A-Za-z0-9._-]+)==([A-Za-z0-9._+-]+)$")


def project_metadata() -> dict[str, str]:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        project = tomllib.load(handle).get("project", {})
    return {
        "name": str(project.get("name", ROOT.name)),
        "version": str(project.get("version", "0.0.0")),
        "description": str(project.get("description", "")),
    }


def source_revision() -> str:
    """The commit this bill of materials describes, or 'unknown'."""
    proc = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False)
    return proc.stdout.strip() if proc.returncode == 0 else "unknown"


def locked_packages() -> list[tuple[str, str]]:
    if not LOCK.is_file():
        raise SystemExit(f"no lock file at {LOCK}")
    packages: list[tuple[str, str]] = []
    for line in LOCK.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text or text.startswith("#"):
            continue
        match = PIN.match(text)
        if match:
            packages.append((match.group(1), match.group(2)))
    return packages


def component(name: str, version: str) -> dict[str, Any]:
    return {
        "type": "library",
        "name": name,
        "version": version,
        "purl": f"pkg:pypi/{name.lower()}@{version}",
        "scope": "required",
    }


def build_document() -> dict[str, Any]:
    metadata = project_metadata()
    packages = locked_packages()
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "serialNumber": f"urn:uuid:{uuid.uuid4()}",
        "version": 1,
        "metadata": {
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "tools": [{"vendor": "repo-quality-template", "name": "generate_sbom.py"}],
            "component": {
                "type": "application",
                "name": metadata["name"],
                "version": metadata["version"],
                "description": metadata["description"],
                "purl": f"pkg:pypi/{metadata['name']}@{metadata['version']}",
                "properties": [{"name": "vcs:revision", "value": source_revision()}],
            },
        },
        "components": [component(name, version) for name, version in packages],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--output", default="dist/sbom.json", help="where to write it")
    args = parser.parse_args()

    document = build_document()
    output = Path(args.output)
    if not output.is_absolute():
        output = ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)

    text = json.dumps(document, indent=2) + "\n"
    output.write_text(text, encoding="utf-8")
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()

    print(f"{output}: {len(document['components'])} components")
    print(f"sha256: {digest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
