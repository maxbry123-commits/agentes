#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import shutil
import stat
import tempfile
import zipfile

SCHEMA = "yaiwes.root-zip.v1"

ROOT_DIR = pathlib.Path(os.getenv("ROOT_DIR", "")).expanduser()
OUTPUT_ZIP = pathlib.Path(os.getenv("OUTPUT_ZIP", "")).expanduser()
MANIFEST_PATH = pathlib.Path(os.getenv("MANIFEST_PATH", "")).expanduser()
COLLISION_POLICY = os.getenv("COLLISION_POLICY", "fail").lower()


def sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_stream(stream) -> str:
    h = hashlib.sha256()
    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
        h.update(chunk)
    return h.hexdigest()


def is_inside(child: pathlib.Path, parent: pathlib.Path) -> bool:
    try:
        child.resolve(strict=False).relative_to(parent.resolve(strict=False))
        return True
    except ValueError:
        return False


def inventory(root: pathlib.Path):
    files = []
    dirs = []
    total_bytes = 0
    root = root.resolve()

    for current, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
        current_path = pathlib.Path(current)

        kept_dirs = []
        for name in sorted(dirnames):
            p = current_path / name
            rel = p.relative_to(root)
            if ".git" in rel.parts:
                continue
            if p.is_symlink():
                raise RuntimeError("UNSUPPORTED_SYMLINK:" + rel.as_posix())
            kept_dirs.append(name)
            dirs.append(rel.as_posix())
        dirnames[:] = kept_dirs

        for name in sorted(filenames):
            p = current_path / name
            rel = p.relative_to(root)
            if ".git" in rel.parts:
                continue
            mode = p.lstat().st_mode
            if stat.S_ISLNK(mode):
                raise RuntimeError("UNSUPPORTED_SYMLINK:" + rel.as_posix())
            if not stat.S_ISREG(mode):
                raise RuntimeError("UNSUPPORTED_SPECIAL_FILE:" + rel.as_posix())
            size = p.stat().st_size
            digest = sha256_file(p)
            files.append({
                "rel": rel.as_posix(),
                "bytes": size,
                "sha256": digest,
                "mode": stat.S_IMODE(mode),
            })
            total_bytes += size

    files.sort(key=lambda row: row["rel"])
    dirs = sorted(set(dirs))

    h = hashlib.sha256()
    for row in files:
        h.update(row["rel"].encode("utf-8"))
        h.update(b"\0")
        h.update(row["sha256"].encode("ascii"))
        h.update(b"\0")
        h.update(str(row["bytes"]).encode("ascii"))
        h.update(b"\n")

    return {
        "files": files,
        "dirs": dirs,
        "file_count": len(files),
        "dir_count": len(dirs),
        "bytes": total_bytes,
        "tree_sha256": h.hexdigest(),
    }


def add_dir(zf: zipfile.ZipFile, rel: str):
    name = rel.rstrip("/") + "/"
    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.create_system = 3
    info.compress_type = zipfile.ZIP_STORED
    info.external_attr = (0o755 & 0xFFFF) << 16
    zf.writestr(info, b"")


def add_file(zf: zipfile.ZipFile, source: pathlib.Path, rel: str, mode: int):
    info = zipfile.ZipInfo(rel, date_time=(1980, 1, 1, 0, 0, 0))
    info.create_system = 3
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = (mode & 0xFFFF) << 16
    with source.open("rb") as src, zf.open(info, "w", force_zip64=True) as dst:
        shutil.copyfileobj(src, dst, 1024 * 1024)


def build_zip(root: pathlib.Path, inv, tmp_zip: pathlib.Path):
    with zipfile.ZipFile(
        tmp_zip,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=6,
        allowZip64=True,
    ) as zf:
        for rel in inv["dirs"]:
            add_dir(zf, rel)
        for row in inv["files"]:
            add_file(zf, root / pathlib.PurePosixPath(row["rel"]), row["rel"], row["mode"])


def verify_zip(path: pathlib.Path, inv):
    expected_files = {row["rel"]: row for row in inv["files"]}
    expected_dirs = {d.rstrip("/") + "/" for d in inv["dirs"]}

    with zipfile.ZipFile(path, "r") as zf:
        bad = zf.testzip()
        if bad:
            raise RuntimeError("ZIP_CRC_FAIL:" + bad)

        names = [i.filename.replace("\\", "/") for i in zf.infolist()]
        if any(".git" in pathlib.PurePosixPath(name).parts for name in names):
            raise RuntimeError("GIT_HISTORY_LEAK")

        actual_dirs = {i.filename for i in zf.infolist() if i.is_dir()}
        actual_files = {i.filename for i in zf.infolist() if not i.is_dir()}

        if actual_dirs != expected_dirs:
            raise RuntimeError("ZIP_DIRECTORY_SET_MISMATCH")
        if actual_files != set(expected_files):
            raise RuntimeError("ZIP_FILE_SET_MISMATCH")

        for rel, row in expected_files.items():
            with zf.open(rel, "r") as stream:
                if sha256_stream(stream) != row["sha256"]:
                    raise RuntimeError("ZIP_FILE_HASH_MISMATCH:" + rel)


def write_manifest(inv, zip_sha256: str):
    manifest = {
        "schema": SCHEMA,
        "root": str(ROOT_DIR.resolve()),
        "output_zip": str(OUTPUT_ZIP.resolve(strict=False)),
        "exclude_git_history": True,
        "file_count": inv["file_count"],
        "dir_count": inv["dir_count"],
        "bytes": inv["bytes"],
        "tree_sha256": inv["tree_sha256"],
        "zip_sha256": zip_sha256,
        "files": inv["files"],
        "verdict": "VERIFIED_CLOSED",
    }
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = MANIFEST_PATH.with_name(MANIFEST_PATH.name + ".tmp")
    tmp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    os.replace(tmp, MANIFEST_PATH)
    return manifest


def main():
    if not str(ROOT_DIR) or not str(OUTPUT_ZIP) or not str(MANIFEST_PATH):
        raise SystemExit(json.dumps({
            "schema": SCHEMA,
            "verdict": "INPUT_GAP",
            "detail": "ROOT_DIR, OUTPUT_ZIP and MANIFEST_PATH are required",
        }))

    if COLLISION_POLICY not in {"fail", "replace"}:
        raise SystemExit(json.dumps({
            "schema": SCHEMA,
            "verdict": "INPUT_GAP",
            "detail": "COLLISION_POLICY must be fail|replace",
        }))

    if not ROOT_DIR.is_dir():
        raise SystemExit(json.dumps({
            "schema": SCHEMA,
            "verdict": "INPUT_GAP",
            "detail": "ROOT_DIR_NOT_FOUND",
        }))

    root = ROOT_DIR.resolve()
    output = OUTPUT_ZIP.resolve(strict=False)
    manifest_path = MANIFEST_PATH.resolve(strict=False)

    if is_inside(output, root) or is_inside(manifest_path, root):
        raise SystemExit(json.dumps({
            "schema": SCHEMA,
            "verdict": "INPUT_GAP",
            "detail": "OUTPUT_ZIP and MANIFEST_PATH must be outside ROOT_DIR",
        }))

    if output.exists() and COLLISION_POLICY == "fail":
        raise SystemExit(json.dumps({
            "schema": SCHEMA,
            "verdict": "INPUT_GAP",
            "detail": "OUTPUT_ZIP_EXISTS",
        }))

    inv = inventory(root)
    OUTPUT_ZIP.parent.mkdir(parents=True, exist_ok=True)

    fd, tmp_name = tempfile.mkstemp(prefix=OUTPUT_ZIP.name + ".", suffix=".partial", dir=str(OUTPUT_ZIP.parent))
    os.close(fd)
    tmp_zip = pathlib.Path(tmp_name)

    try:
        build_zip(root, inv, tmp_zip)
        verify_zip(tmp_zip, inv)
        zip_sha = sha256_file(tmp_zip)
        os.replace(tmp_zip, OUTPUT_ZIP)
        if sha256_file(OUTPUT_ZIP) != zip_sha:
            raise RuntimeError("ZIP_READBACK_HASH_MISMATCH")
        manifest = write_manifest(inv, zip_sha)
        print(json.dumps(manifest, ensure_ascii=False, sort_keys=True))
    finally:
        tmp_zip.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
