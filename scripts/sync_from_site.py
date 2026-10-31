#!/usr/bin/env python3
"""Copy the published Microsoft 365 dataset from computecloud.co.uk into data/.

    python scripts/sync_from_site.py

This repository only ever mirrors the files already published on the website;
it never takes anything from elsewhere. The script downloads the three files,
checks they are complete and consistent, and only then replaces data/, writes
data/SHA256SUMS and sets the version in CITATION.cff.

Environment (optional):
  SITE_DATA_URL   where the files live (default: the live dataset folder)
  GITHUB_OUTPUT   set by GitHub Actions; receives changed=true|false and version=

Standard library only.
"""
import csv
import hashlib
import io
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
BASE = os.environ.get(
    "SITE_DATA_URL", "https://computecloud.co.uk/data/microsoft-365-plans/")
FILES = ["m365-features.json", "m365-features.csv", "m365-cells.csv"]
CELLS_HEADER = ["feature_id", "feature", "plan_id", "plan", "value", "addon",
                "limit", "note", "source_urls", "checked"]
VALUES = {"included", "not_included", "partial", "addon", "limit",
          "unclear", "unverified"}
# This dataset is ComputeCloud's own. The older data the site once used came from
# the M365 Maps matrix, which has no reuse licence, so nothing that mentions it may
# ever be copied into this repository.
FORBIDDEN = re.compile(rb"m365\s*maps|dinnage", re.IGNORECASE)


class SyncError(Exception):
    pass


def fetch(name):
    url = BASE.rstrip("/") + "/" + name
    req = urllib.request.Request(url, headers={"User-Agent": "computecloud-data-sync"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        if resp.status != 200:
            raise SyncError(f"{url} returned HTTP {resp.status}")
        return resp.read()


def rows(raw):
    return list(csv.reader(io.StringIO(raw.decode("utf-8-sig"), newline="")))


def check(files):
    """Raise SyncError unless the three files are complete and agree."""
    for name, body in files.items():
        hit = FORBIDDEN.search(body)
        if hit:
            raise SyncError(f"{name} mentions {hit.group().decode(errors='replace')!r}; "
                            "only ComputeCloud's own data may be copied here")
    try:
        data = json.loads(files["m365-features.json"])
    except ValueError as e:
        raise SyncError(f"m365-features.json is not valid JSON: {e}")
    meta = data.get("meta", {})
    version = meta.get("version", "")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", version):
        raise SyncError(f"meta.version {version!r} is not a YYYY-MM-DD date")
    if "creativecommons.org/licenses/by/4.0" not in json.dumps(meta.get("licence", "")):
        raise SyncError("meta.licence is not CC BY 4.0")
    counts = meta.get("counts", {})
    n_plans, n_features = len(data.get("plans", [])), len(data.get("features", []))
    if counts.get("plans") != n_plans or counts.get("features") != n_features:
        raise SyncError(f"meta.counts {counts} doesn't match {n_plans} plans / {n_features} features")
    if counts.get("cells") != n_plans * n_features:
        raise SyncError(f"meta.counts.cells {counts.get('cells')} != plans x features")

    feat = rows(files["m365-features.csv"])
    if feat[0][:3] != ["id", "feature", "microsoft_name"]:
        raise SyncError(f"m365-features.csv has an unexpected header: {feat[0][:3]}")
    if len(feat) - 1 != n_features:
        raise SyncError(f"m365-features.csv has {len(feat) - 1} rows, expected {n_features}")

    cells = rows(files["m365-cells.csv"])
    if cells[0] != CELLS_HEADER:
        raise SyncError(f"m365-cells.csv has an unexpected header: {cells[0]}")
    if len(cells) - 1 != counts["cells"]:
        raise SyncError(f"m365-cells.csv has {len(cells) - 1} rows, expected {counts['cells']}")
    bad = {r[4] for r in cells[1:] if r[4] not in VALUES}
    if bad:
        raise SyncError(f"m365-cells.csv has unknown values: {sorted(bad)}")
    return version, counts


def current_version():
    path = DATA / "m365-features.json"
    if not path.exists():
        return None
    return json.loads(path.read_bytes()).get("meta", {}).get("version")


def set_citation_version(version):
    path = ROOT / "CITATION.cff"
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"(?m)^version: .*$", f'version: "{version}"', text)
    text = re.sub(r"(?m)^date-released: .*$", f'date-released: "{version}"', text)
    path.write_text(text, encoding="utf-8", newline="\n")


def output(**kv):
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as fh:
            for k, v in kv.items():
                fh.write(f"{k}={v}\n")


def main():
    files = {name: fetch(name) for name in FILES}
    version, counts = check(files)
    print(f"Live dataset version {version}: {counts['plans']} plans, "
          f"{counts['features']} features, {counts['cells']} values.")

    unchanged = all((DATA / n).exists() and (DATA / n).read_bytes() == b
                    for n, b in files.items())
    if unchanged:
        print("data/ already matches the live files. Nothing to do.")
        output(changed="false", version=version)
        return 0

    old = current_version()
    if old and version < old:
        raise SyncError(f"The live version {version} is older than the copy here ({old}).")
    if old == version:
        print(f"WARNING: the live files changed but the version is still {version}. "
              "Zenodo needs a new version for a new release; bump it on the site first "
              "if this is more than a fix.")

    DATA.mkdir(exist_ok=True)
    sums = []
    for name, body in files.items():
        (DATA / name).write_bytes(body)
        sums.append(f"{hashlib.sha256(body).hexdigest()}  {name}")
        print(f"  {name}  {len(body):,} bytes")
    (DATA / "SHA256SUMS").write_text("\n".join(sums) + "\n", encoding="utf-8", newline="\n")
    set_citation_version(version)
    output(changed="true", version=version)
    print(f"data/ updated to version {version}.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (SyncError, OSError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
