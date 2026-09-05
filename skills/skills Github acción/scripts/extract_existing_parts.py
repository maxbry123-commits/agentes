import hashlib
import re
import shutil
import stat
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

LFS_POINTER_PREFIX = b"version https://git-lfs.github.com/spec/v1\n"
GIT_BLOB_LIMIT = 100 * 1024 * 1024


def die(msg: str) -> None:
    raise SystemExit(msg)


def natural_key(path: Path):
    return [int(x) if x.isdigit() else x.lower() for x in re.split(r"(\d+)", path.name)]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def is_lfs_pointer(path: Path) -> bool:
    if path.stat().st_size > 1024:
        return False
    with path.open("rb") as f:
        return f.read(1024).startswith(LFS_POINTER_PREFIX)


def safe_member(info: zipfile.ZipInfo) -> PurePosixPath:
    name = info.filename.replace("\\", "/")
    if not name or "\x00" in name or name.startswith("/") or re.match(r"^[A-Za-z]:", name):
        die(f"UNSAFE_ZIP: invalid path {info.filename!r}")
    p = PurePosixPath(name)
    if any(part in ("", ".", "..") for part in p.parts):
        die(f"UNSAFE_ZIP: traversal/ambiguous path {info.filename!r}")
    mode = (info.external_attr >> 16) & 0xFFFF
    if mode and (stat.S_ISLNK(mode) or stat.S_ISCHR(mode) or stat.S_ISBLK(mode) or stat.S_ISFIFO(mode) or stat.S_ISSOCK(mode)):
        die(f"UNSAFE_ZIP: special file {info.filename!r}")
    return p


def tree_hash(root: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(x for x in root.rglob("*") if x.is_file() and x.name != "SOURCE_SHA256SUMS.txt"):
        h.update(p.relative_to(root).as_posix().encode() + b"\0")
        h.update(bytes.fromhex(sha256(p)))
    return h.hexdigest()


def main() -> None:
    if len(sys.argv) not in (5, 6, 7):
        die("usage: extract_existing_parts.py ROOT COMPONENT SOURCE_URL SOURCE_COMMIT [LICENSE] [EXPECTED_PARTS]")
    root = Path(sys.argv[1]).resolve()
    component = sys.argv[2]
    source_url = sys.argv[3]
    source_commit = sys.argv[4]
    license_name = sys.argv[5] if len(sys.argv) >= 6 else "UNKNOWN"
    expected_parts = int(sys.argv[6]) if len(sys.argv) == 7 else None

    parts = sorted(root.glob(f"{component}_*.zip"), key=natural_key)
    if not parts:
        die(f"PART_MISSING_GAP: no {component}_*.zip in {root}")
    if expected_parts is not None and len(parts) != expected_parts:
        die(f"PART_COUNT_GAP: expected={expected_parts} actual={len(parts)}")

    part_hashes = []
    seen_files = set()
    with tempfile.TemporaryDirectory(prefix=f"extract-{component}-") as td:
        stage = Path(td) / "payload"
        stage.mkdir()
        for part in parts:
            try:
                with zipfile.ZipFile(part) as zf:
                    bad = zf.testzip()
                    if bad:
                        die(f"ZIP_CRC_GAP: {part.name}:{bad}")
                    for info in zf.infolist():
                        member = safe_member(info)
                        if info.is_dir():
                            continue
                        rel = member.as_posix()
                        if rel in seen_files:
                            die(f"COLLISION_BLOCKED: duplicate archive member {rel}")
                        seen_files.add(rel)
                    zf.extractall(stage)
            except zipfile.BadZipFile as exc:
                die(f"ZIP_INVALID_GAP: {part.name}: {exc}")
            part_hashes.append((part.name, sha256(part), part.stat().st_size))

        staged_component = stage / component
        if not staged_component.is_dir():
            die(f"DESTINATION_GAP: archive does not contain top-level {component}/")
        staged_files = sorted(p for p in staged_component.rglob("*") if p.is_file())
        if not staged_files:
            die(f"EMPTY_TREE_GAP: {component}")
        for src in staged_files:
            if src.stat().st_size >= GIT_BLOB_LIMIT:
                die(f"GIT_BLOB_LIMIT_GAP: {src.relative_to(staged_component)}={src.stat().st_size}")
            if is_lfs_pointer(src):
                die(f"SOURCE_LFS_POINTER_GAP: {src.relative_to(staged_component)}")

        destination = root / component
        if destination.exists():
            for src in staged_files:
                rel = src.relative_to(staged_component)
                dst = destination / rel
                if dst.exists() and (not dst.is_file() or sha256(src) != sha256(dst)):
                    die(f"COLLISION_BLOCKED: {dst}")
        destination.mkdir(parents=True, exist_ok=True)
        for src in staged_files:
            rel = src.relative_to(staged_component)
            dst = destination / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            if not dst.exists():
                shutil.copy2(src, dst)

    (destination / "SOURCE_URL.txt").write_text(source_url.rstrip("/") + "\n", encoding="utf-8")
    (destination / "SOURCE_COMMIT.txt").write_text(source_commit + "\n", encoding="utf-8")
    (destination / "SOURCE_LICENSE.txt").write_text(license_name + "\n", encoding="utf-8")
    (destination / "SOURCE_PARTS_SHA256.txt").write_text(
        "".join(f"{digest}  {name}  {size}\n" for name, digest, size in part_hashes), encoding="utf-8"
    )
    sums = []
    for p in sorted(x for x in destination.rglob("*") if x.is_file() and x.name != "SOURCE_SHA256SUMS.txt"):
        sums.append(f"{sha256(p)}  {p.relative_to(destination).as_posix()}\n")
    (destination / "SOURCE_SHA256SUMS.txt").write_text("".join(sums), encoding="utf-8")
    print(f"EXTRACTED_VERIFIED component={component} parts={len(parts)} files={len(sums)} tree_sha256={tree_hash(destination)}")


if __name__ == "__main__":
    main()
