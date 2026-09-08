#!/usr/bin/env python3
"""
Create the Zenodo DRAFT for the TimesFM-3 versus classical reproduction archive.

WHAT THIS DOES NOT DO
---------------------
It never publishes. The record is left as an unpublished DRAFT for you to review and press
Publish yourself. Publishing mints a permanent DOI that cannot be withdrawn, only superseded.
This matches the pattern used for the EDGE, EDGES and DeepGOF-1 deposits.

THE TOKEN
---------
Read from the environment. Never pass it on the command line (it would land in your shell
history) and never paste it into a chat.

    PowerShell :  $env:ZENODO_TOKEN = "<token>"
    bash       :  export ZENODO_TOKEN="<token>"

The token needs the deposit:write and deposit:actions scopes. Sandbox needs its OWN token from
sandbox.zenodo.org; tokens are not shared between the two sites.

USAGE
-----
    python code/99_deposit_zenodo.py --dry-run   # list what would go up, touch nothing
    python code/99_deposit_zenodo.py --sandbox   # rehearse on sandbox.zenodo.org
    python code/99_deposit_zenodo.py             # create the draft on the real Zenodo
    python code/99_deposit_zenodo.py --list      # list your depositions, create nothing
    python code/99_deposit_zenodo.py --new-version --of ID
                                                 # later: cut a new version of an existing record
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARCHIVE = ROOT / "release" / "timesfm-classical"
ZIP_NAME = "timesfm-classical.zip"
ZIP_TOP = "timesfm-classical"

# Front matter goes up as loose files so it is readable on the record page without
# downloading the zip. Zenodo's bucket key is FLAT -- a key containing "/" 404s -- so only
# root-level files can be uploaded individually.
ROOT_FILES = ["README.md", "LICENSE", "SPEC.md", "PREREGISTRATION.md", "DEVIATIONS.md"]


def archive_members():
    out = []
    for p in sorted(ARCHIVE.rglob("*")):
        if p.is_file():
            out.append((str(p.relative_to(ARCHIVE)).replace(os.sep, "/"), p))
    return out


def build_zip(members):
    dest = ROOT / "release" / ZIP_NAME
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for rel, full in members:
            z.write(full, f"{ZIP_TOP}/{rel}")
    return dest


def api(base, token, method, path, payload=None, raw=None):
    url = path if path.startswith("http") else base + path
    sep = "&" if "?" in url else "?"
    url = f"{url}{sep}access_token={token}"
    data, headers = None, {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    elif raw is not None:
        data = raw
        headers["Content-Type"] = "application/octet-stream"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as r:
            body = r.read().decode("utf-8")
            return json.loads(body) if body.strip() else {}
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:900]
        raise SystemExit(f"\nZenodo API error {e.code} on {method} {path}\n{detail}\n")
    except urllib.error.URLError as e:
        raise SystemExit(f"\nCould not reach Zenodo: {e.reason}\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sandbox", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--list", action="store_true",
                    help="list your depositions and exit; creates nothing")
    ap.add_argument("--new-version", action="store_true",
                    help="cut a new version of an existing published record")
    ap.add_argument("--of", metavar="ID", help="deposition id for --new-version")
    ap.add_argument("--use-draft", metavar="ID",
                    help="continue with an existing unpublished draft")
    args = ap.parse_args()

    if not ARCHIVE.is_dir():
        raise SystemExit(f"\n{ARCHIVE} does not exist.\n"
                         "Run:  python code/98_build_release.py  first.\n")

    meta_path = ARCHIVE / ".zenodo.json"
    if not meta_path.is_file():
        raise SystemExit(f"\n{meta_path} is missing; the build step should have copied it.\n")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))

    members = archive_members()
    total = sum(p.stat().st_size for _, p in members)
    roots = [(nm, ARCHIVE / nm) for nm in ROOT_FILES if (ARCHIVE / nm).is_file()]

    print(f"archive : {ARCHIVE}")
    print(f"contents: {len(members)} files ({total / 1e6:.1f} MB) "
          f"-> 1 zip + {len(roots)} loose root files")
    print(f"title   : {meta['title'][:72]}")
    print(f"authors : {', '.join(c['name'] for c in meta['creators'])}")
    print(f"licence : {meta.get('license')}   version: {meta.get('version', '(unset)')}")

    if args.dry_run:
        print("\n-- loose files at the record root --")
        for rel, full in roots:
            print(f"   {full.stat().st_size:>9d}  {rel}")
        print(f"\n-- inside {ZIP_NAME} (first 30 of {len(members)}) --")
        for rel, full in members[:30]:
            print(f"   {full.stat().st_size:>9d}  {rel}")
        if len(members) > 30:
            print(f"   ... and {len(members) - 30} more")
        print("\nDRY RUN: nothing was sent to Zenodo.")
        return

    token = os.environ.get("ZENODO_TOKEN", "").strip()
    if not token:
        raise SystemExit(
            "\nZENODO_TOKEN is not set.\n"
            '  PowerShell : $env:ZENODO_TOKEN = "<token>"\n'
            '  bash       : export ZENODO_TOKEN="<token>"\n'
            "Then re-run. The token is read from the environment and never echoed.\n")

    base = "https://sandbox.zenodo.org/api" if args.sandbox else "https://zenodo.org/api"
    print(f"site    : {base.replace('/api', '')}")
    print(f"token   : loaded from environment ({len(token)} chars, not shown)\n")

    if args.list:
        for d in api(base, token, "GET", "/deposit/depositions?size=100"):
            state = "published" if d.get("submitted") else "DRAFT"
            print(f"  [{str(d.get('id')):<10}] {state:<9} {(d.get('title') or '')[:66]}")
        return

    # 1. obtain a draft
    if args.use_draft:
        dep_id = str(args.use_draft)
        draft = api(base, token, "GET", f"/deposit/depositions/{dep_id}")
        if draft.get("submitted"):
            raise SystemExit(f"Deposition {dep_id} is already published; "
                             "pass it to --new-version --of instead.")
        print(f"continuing with existing draft {dep_id}")
    elif args.new_version:
        if not args.of:
            raise SystemExit("--new-version requires --of <deposition id>")
        nv = api(base, token, "POST",
                 f"/deposit/depositions/{args.of}/actions/newversion")
        draft = api(base, token, "GET", nv["links"]["latest_draft"])
        dep_id = draft["id"]
        print(f"opened new version of {args.of} -> draft {dep_id}")
    else:
        draft = api(base, token, "POST", "/deposit/depositions", payload={})
        dep_id = draft["id"]
        print(f"created new deposition draft {dep_id}")

    bucket = draft["links"]["bucket"]

    # 2. clear anything already on the draft, so a re-run is idempotent
    existing = draft.get("files", [])
    if existing:
        print(f"clearing {len(existing)} file(s) already on the draft ...")
        for f in existing:
            api(base, token, "DELETE", f"/deposit/depositions/{dep_id}/files/{f['id']}")

    # 3a. readable front matter as loose files
    print(f"uploading {len(roots)} root file(s) ...")
    for rel, full in roots:
        api(base, token, "PUT", f"{bucket}/{rel}", raw=full.read_bytes())
        print(f"   {rel}")

    # 3b. everything else in one zip
    print("building the archive zip ...")
    zpath = build_zip(members)
    print(f"   {len(members)} files -> {zpath.stat().st_size / 1e6:.1f} MB, uploading ...")
    api(base, token, "PUT", f"{bucket}/{ZIP_NAME}", raw=zpath.read_bytes())
    print(f"   {ZIP_NAME} uploaded")
    zpath.unlink()

    # 4. metadata
    md = dict(meta)
    md.setdefault("upload_type", "software")
    md.setdefault("access_right", "open")
    api(base, token, "PUT", f"/deposit/depositions/{dep_id}", payload={"metadata": md})
    print("metadata set")

    link = draft["links"].get("html") or f"https://zenodo.org/deposit/{dep_id}"
    print("\n" + "=" * 72)
    print("DRAFT CREATED AND NOT PUBLISHED.")
    print(f"  {link}")
    print("\nOpen it and check the title, the single author, the ORCID, the licence, the")
    print("version and the file list. Then press Publish yourself. Publishing mints a")
    print("permanent DOI that cannot be withdrawn, only superseded.")
    print("\nAfter publishing, put the concept DOI in the manuscript's data-availability")
    print("statement and add the record to ACADEMIC_TRACKER.md.")


if __name__ == "__main__":
    main()
