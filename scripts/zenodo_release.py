#!/usr/bin/env python3
"""Upload this dataset to Zenodo, as a new record or a new version of the existing one.

Run by .github/workflows/zenodo-release.yml when a GitHub release is published.
Zenodo never gets access to GitHub: this script pushes the files to Zenodo's
REST API with a Zenodo token that is stored as a secret in this repository only.

By default it leaves a DRAFT on Zenodo for you to check and publish yourself.
Publishing on Zenodo mints a DOI and cannot be undone (files can't be changed
afterwards, only replaced by a new version).

Environment:
  ZENODO_TOKEN      Zenodo personal access token, scopes deposit:write + deposit:actions
  ZENODO_URL        https://zenodo.org (default) or https://sandbox.zenodo.org for tests
  ZENODO_RECORD_ID  optional: id of the published record; new uploads become a new
                    version of it. If unset, the record is found by its title.
  ZENODO_PUBLISH    "true" to publish without review (default: leave a draft)

Usage:
  python scripts/zenodo_release.py --version 1.0.0 [--notes-file NOTES] [--dry-run] FILE...

Standard library only.
"""
import argparse
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class ZenodoError(Exception):
    pass


class Zenodo:
    def __init__(self, base_url, token):
        self.base = base_url.rstrip("/")
        self.token = token

    def request(self, method, url, body=None, raw=None, ok=(200, 201, 202, 204)):
        if not url.startswith("http"):
            url = self.base + url
        headers = {"Authorization": f"Bearer {self.token}", "Accept": "application/json"}
        data = None
        if raw is not None:
            data = raw
            headers["Content-Type"] = "application/octet-stream"
        elif body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                status, text = resp.status, resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            status, text = e.code, e.read().decode("utf-8", "replace")
        if status not in ok:
            raise ZenodoError(f"{method} {url.split('?')[0]} -> HTTP {status}: {text[:800]}")
        return json.loads(text) if text.strip() else None

    def depositions(self):
        """All of the token owner's depositions, drafts included (deduplicated)."""
        seen = {}
        for extra in ("", "&status=draft"):
            page = 1
            while True:
                batch = self.request(
                    "GET", f"/api/deposit/depositions?size=100&page={page}{extra}") or []
                for d in batch:
                    seen[d["id"]] = d
                if len(batch) < 100:
                    break
                page += 1
        return list(seen.values())


def trailing_id(url):
    tail = urllib.parse.urlparse(url).path.rstrip("/").rsplit("/", 1)[-1]
    return int(tail) if tail.isdigit() else None


def find_target(z, title, record_id):
    """Return (deposition, how) where how is 'draft' (reuse) or 'published' (new version)."""
    if record_id:
        dep = z.request("GET", f"/api/deposit/depositions/{record_id}")
        return dep, ("published" if dep.get("submitted") else "draft")
    mine = [d for d in z.depositions() if d.get("metadata", {}).get("title") == title]
    drafts = [d for d in mine if not d.get("submitted")]
    if drafts:
        return max(drafts, key=lambda d: d["id"]), "draft"
    published = [d for d in mine if d.get("submitted")]
    if published:
        return max(published, key=lambda d: d["id"]), "published"
    return None, "new"


def open_draft(z, title, record_id, log):
    dep, how = find_target(z, title, record_id)
    if how == "new":
        log("No existing record with this title: creating a new one.")
        return z.request("POST", "/api/deposit/depositions", body={})
    if how == "draft":
        log(f"Reusing the unpublished draft {dep['id']}.")
        return dep
    latest = trailing_id(dep.get("links", {}).get("latest", "")) or dep["id"]
    log(f"Creating a new version of record {latest}.")
    resp = z.request("POST", f"/api/deposit/depositions/{latest}/actions/newversion")
    if resp and not resp.get("submitted") and resp.get("id") != latest:
        return resp
    draft_url = (resp or {}).get("links", {}).get("latest_draft")
    if not draft_url:
        raise ZenodoError("Zenodo did not return the new version's draft.")
    return z.request("GET", draft_url)


def build_metadata(version, notes):
    meta = json.loads((ROOT / ".zenodo.json").read_text(encoding="utf-8"))
    meta["version"] = version
    meta["publication_date"] = dt.datetime.now(dt.timezone.utc).date().isoformat()
    if notes:
        meta["notes"] = notes
    return meta


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--version", required=True, help="version label, e.g. 1.0.0")
    ap.add_argument("--notes-file", help="release notes to store on the record")
    ap.add_argument("--dry-run", action="store_true", help="show what would be sent; no API calls")
    ap.add_argument("files", nargs="+", help="files to upload")
    args = ap.parse_args(argv)
    log = print

    version = args.version.strip()
    if version[:1] in "vV" and version[1:2].isdigit():
        version = version[1:]
    notes = ""
    if args.notes_file and Path(args.notes_file).exists():
        notes = Path(args.notes_file).read_text(encoding="utf-8").strip()
    meta = build_metadata(version, notes)

    files = [Path(f) for f in args.files]
    missing = [str(f) for f in files if not f.is_file()]
    if missing:
        raise ZenodoError("Missing files: " + ", ".join(missing))
    names = [f.name for f in files]
    dupes = sorted({n for n in names if names.count(n) > 1})
    if dupes:
        raise ZenodoError("Zenodo stores files without folders; these names clash: " + ", ".join(dupes))

    base = os.environ.get("ZENODO_URL", "https://zenodo.org").strip() or "https://zenodo.org"
    publish = os.environ.get("ZENODO_PUBLISH", "").strip().lower() == "true"
    record_id = os.environ.get("ZENODO_RECORD_ID", "").strip() or None

    log(f"Target: {base}  version: {version}  publish: {'yes' if publish else 'no (draft)'}")
    for f in files:
        log(f"  {f.name}  ({f.stat().st_size:,} bytes)")
    if args.dry_run:
        log("Dry run. Metadata that would be sent:")
        log(json.dumps(meta, indent=2, ensure_ascii=False))
        return 0

    token = os.environ.get("ZENODO_TOKEN", "").strip()
    if not token:
        raise ZenodoError("ZENODO_TOKEN is empty: add the Zenodo token as a repository secret.")
    z = Zenodo(base, token)

    draft = open_draft(z, meta["title"], record_id, log)
    api = draft["links"]["self"]

    existing = z.request("GET", f"{api}/files") or []
    for f in existing:
        z.request("DELETE", f["links"]["self"])
    if existing:
        log(f"Removed {len(existing)} file(s) carried over from the previous version.")

    bucket = draft["links"]["bucket"]
    for f in files:
        z.request("PUT", f"{bucket}/{urllib.parse.quote(f.name)}", raw=f.read_bytes())
        log(f"Uploaded {f.name}")

    draft = z.request("PUT", api, body={"metadata": meta})
    link = draft["links"].get("html", "")

    if publish:
        done = z.request("POST", f"{api}/actions/publish")
        doi = done.get("doi") or done.get("metadata", {}).get("doi", "")
        summary = f"Published version {version} on Zenodo: https://doi.org/{doi}"
    else:
        summary = (f"Draft of version {version} is ready on Zenodo: {link}\n"
                   "Check it there, then press Publish. Nothing is public until you do.")
    log(summary)
    out = os.environ.get("GITHUB_STEP_SUMMARY")
    if out:
        with open(out, "a", encoding="utf-8") as fh:
            fh.write(summary.replace("\n", "\n\n") + "\n")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ZenodoError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
