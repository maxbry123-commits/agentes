#!/usr/bin/env python3
"""
CI helper (NOT a motor, no checkout needed): performs a pure git-native
rename of the 4 remaining emoji-named root items in `agentes`, using the
GitHub Git Data API directly (trees/commits/refs). This is a metadata-only
operation -- it reuses the existing blob SHAs at new paths and never
downloads or re-uploads any file content, so it works regardless of how
large the folders are (no checkout, no disk space concerns, no motor
involved -- motor_3/motor_4 are for actually moving bytes between real
filesystem locations, which is not what a rename needs).

Runs with GITHUB_TOKEN (the default Actions token, which has push access
to this same repo) via `requests`.
"""
from __future__ import annotations
import os
import sys
import time
import requests

REPO = "maxbry123-commits/agentes"
API = "https://api.github.com"
TOKEN = os.environ["GITHUB_TOKEN"]
HEADERS = {
    "Authorization": "Bearer " + TOKEN,
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

# (old root path, new root path) -- old path is a DIRECTORY unless noted.
RENAME_PAIRS = [
    (u"\U0001f4c2 Bitácora stated JSON Craxy wall.json", u"Bitacora-stated-JSON-Craxy-wall.json"),
    (u"➡️\U0001f4c2 wordflow loop code Yaiwes", u"wordflow loop code Yaiwes"),
    (u"\U0001f4c2coda workflow persistencias", u"coda workflow persistencias"),
    (u"➡️\U0001f4c2motores de descarga extracción copiado movimiento archivos agentes", u"motores de descarga extraccion copiado movimiento archivos agentes"),
]


def gh(method, path, **kwargs):
    for attempt in range(5):
        r = requests.request(method, API + path, headers=HEADERS, timeout=120, **kwargs)
        if r.status_code == 403 and "rate limit" in r.text.lower():
            wait = int(r.headers.get("Retry-After", "10"))
            print("Rate limited, waiting " + str(wait) + "s...")
            time.sleep(wait)
            continue
        if r.status_code >= 400:
            print("ERROR " + method + " " + path + ": " + str(r.status_code) + " " + r.text[:2000])
            r.raise_for_status()
        return r.json() if r.text else {}
    raise RuntimeError("Failed after retries: " + method + " " + path)


def get_recursive_tree(tree_sha):
    data = gh("GET", "/repos/" + REPO + "/git/trees/" + tree_sha, params={"recursive": "1"})
    if data.get("truncated"):
        raise RuntimeError(
            "Tree " + tree_sha + " response truncated by GitHub API -- too large for a "
            "single recursive fetch. This folder needs per-subdirectory batches."
        )
    return data["tree"]


def main():
    print("=== Fetching current main branch state ===")
    ref = gh("GET", "/repos/" + REPO + "/git/ref/heads/main")
    base_commit_sha = ref["object"]["sha"]
    base_commit = gh("GET", "/repos/" + REPO + "/git/commits/" + base_commit_sha)
    base_tree_sha = base_commit["tree"]["sha"]
    print("base_commit=" + base_commit_sha + " base_tree=" + base_tree_sha)

    root_tree = gh("GET", "/repos/" + REPO + "/git/trees/" + base_tree_sha)["tree"]
    root_by_path = dict((e["path"], e) for e in root_tree)

    all_new_entries = []
    summary = []

    for old_root, new_root in RENAME_PAIRS:
        print("\n=== " + repr(old_root) + " -> " + repr(new_root) + " ===")
        root_entry = root_by_path.get(old_root)
        if root_entry is None:
            print("SKIP: not found at repo root (already renamed?)")
            summary.append("SKIP (not found): " + old_root)
            continue

        if root_entry["type"] == "blob":
            all_new_entries.append({
                "path": new_root, "mode": root_entry["mode"], "type": "blob", "sha": root_entry["sha"],
            })
            all_new_entries.append({
                "path": old_root, "mode": root_entry["mode"], "type": "blob", "sha": None,
            })
            print("OK (file): 1 add + 1 delete queued")
            summary.append("OK (file, " + str(root_entry.get("size", "?")) + " bytes): " + old_root + " -> " + new_root)
            continue

        try:
            subtree = get_recursive_tree(root_entry["sha"])
        except RuntimeError as e:
            print("ABORT for this item: " + str(e))
            summary.append("FAILED (tree too large to fetch in one call): " + old_root + " -- " + str(e))
            continue

        blobs = [e for e in subtree if e["type"] == "blob"]
        submodules = [e for e in subtree if e["type"] == "commit"]
        print("Found " + str(len(blobs)) + " files, " + str(len(submodules)) + " submodule references")

        for b in blobs:
            new_path = new_root + "/" + b["path"]
            old_path = old_root + "/" + b["path"]
            all_new_entries.append({"path": new_path, "mode": b["mode"], "type": "blob", "sha": b["sha"]})
            all_new_entries.append({"path": old_path, "mode": b["mode"], "type": "blob", "sha": None})

        for sm in submodules:
            new_path = new_root + "/" + sm["path"]
            old_path = old_root + "/" + sm["path"]
            all_new_entries.append({"path": new_path, "mode": sm["mode"], "type": "commit", "sha": sm["sha"]})
            all_new_entries.append({"path": old_path, "mode": sm["mode"], "type": "commit", "sha": None})
            print("  submodule ref preserved: " + old_path + " -> " + new_path)

        print("OK (dir): " + str(len(blobs)) + " file adds+deletes queued, " + str(len(submodules)) + " submodule adds+deletes queued")
        summary.append("OK (dir, " + str(len(blobs)) + " files, " + str(len(submodules)) + " submodules): " + old_root + " -> " + new_root)

    if not all_new_entries:
        print("\nNothing to do -- no renames queued.")
        return 0

    print("\n=== Creating new tree with " + str(len(all_new_entries)) + " entries ===")
    new_tree = gh("POST", "/repos/" + REPO + "/git/trees", json={"base_tree": base_tree_sha, "tree": all_new_entries})
    new_tree_sha = new_tree["sha"]
    print("new_tree=" + new_tree_sha)

    print("=== Creating commit ===")
    commit_message = (
        "rename: move content of 4 emoji-named root items to clean names "
        "(git-native tree rename, no content re-upload)\n\n" + "\n".join(summary)
    )
    new_commit = gh("POST", "/repos/" + REPO + "/git/commits", json={
        "message": commit_message, "tree": new_tree_sha, "parents": [base_commit_sha],
    })
    new_commit_sha = new_commit["sha"]
    print("new_commit=" + new_commit_sha)

    print("=== Updating main ref ===")
    gh("PATCH", "/repos/" + REPO + "/git/refs/heads/main", json={"sha": new_commit_sha, "force": False})
    print("main ref updated.")

    print("\n=== SUMMARY ===")
    for line in summary:
        print(" - " + line)

    return 0


if __name__ == "__main__":
    sys.exit(main())
