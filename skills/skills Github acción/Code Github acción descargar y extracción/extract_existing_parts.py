import hashlib
import re
import shutil
import stat
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

LFS_POINTER_PREFIX = b"version https://git-lfs.github.com/spec/v1"
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


# Queue repair extension: preserves the extractor's hashing and ZIP guards.
import json
import os
import subprocess
import time
import urllib.request
import urllib.parse
import urllib.error


def git(*args):
    return subprocess.check_output(['git', *args], text=True).strip()


def http_bytes(url):
    headers = {'User-Agent': 'research-download-chain', 'Accept': 'application/vnd.github+json'}
    if url.startswith('https://api.github.com/') and os.environ.get('GH_TOKEN'):
        headers['Authorization'] = 'Bearer ' + os.environ['GH_TOKEN']
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=60) as response:
                return response.read()
        except urllib.error.HTTPError as exc:
            if exc.code not in (429, 500, 502, 503, 504) or attempt == 2:
                raise RuntimeError(f'HTTP_{exc.code}_GAP') from exc
            time.sleep(min(60, int(exc.headers.get('Retry-After', 5 * (attempt + 1)))))
        except (urllib.error.URLError, TimeoutError):
            if attempt == 2:
                raise
            time.sleep(5 * (attempt + 1))


def source_metadata(item):
    owner_repo = item['source_url'].removesuffix('.git').removeprefix('https://github.com/')
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', owner_repo):
        raise RuntimeError('INPUT_GAP: source_url')
    if not re.fullmatch(r'[a-f0-9]{40}', item['source_commit']):
        raise RuntimeError('INPUT_GAP: source_commit')
    url = f"https://api.github.com/repos/{owner_repo}/contents/{urllib.parse.quote(item['path'], safe='/')}?ref={item['source_commit']}"
    meta = json.loads(http_bytes(url))
    if meta.get('type') != 'file' or not re.fullmatch(r'[a-f0-9]{40}', meta.get('sha', '')):
        raise RuntimeError('SOURCE_TYPE_GAP')
    return meta, owner_repo


def check_payload(path, meta):
    size = path.stat().st_size
    if size >= GIT_BLOB_LIMIT:
        raise RuntimeError('GIT_BLOB_LIMIT_GAP')
    if is_lfs_pointer(path):
        raise RuntimeError('SOURCE_LFS_POINTER_GAP')
    blob = git('hash-object', '--no-filters', str(path))
    if blob != meta['sha'] or size != meta['size']:
        raise RuntimeError('SOURCE_HASH_MISMATCH')
    return blob


def prepare_item(root, item, target):
    rel = PurePosixPath(item['component']) / item['path']
    if rel.is_absolute() or '..' in rel.parts or '\\' in str(rel):
        raise RuntimeError('UNSAFE_PATH')
    out = root / rel
    if out.is_symlink() or not out.resolve().is_relative_to(root.resolve()):
        raise RuntimeError('UNSAFE_DESTINATION')
    meta, owner_repo = source_metadata(item)
    if meta['size'] >= GIT_BLOB_LIMIT:
        raise RuntimeError('GIT_BLOB_LIMIT_GAP')
    if out.exists():
        if not out.is_file():
            raise RuntimeError('COLLISION_BLOCKED')
        check_payload(out, meta)
        return None, 'VERIFIED_EXISTING', meta
    chunks_dir = out.with_name(out.name + '.chunks')
    if chunks_dir.is_dir():
        if chunks_dir.is_symlink() or not chunks_dir.resolve().is_relative_to(root.resolve()):
            raise RuntimeError('UNSAFE_CHUNKS')
        parts = sorted(chunks_dir.glob(out.name + '.part-*'), key=natural_key)
        expected = [f'{out.name}.part-{n:04d}' for n in range(len(parts))]
        if not parts or [p.name for p in parts] != expected or any(p.is_symlink() for p in parts):
            raise RuntimeError('PART_SEQUENCE_GAP')
        with target.open('wb') as dest:
            for part in parts:
                with part.open('rb') as src:
                    shutil.copyfileobj(src, dest)
        operation = 'RECONSTRUCT_EXISTING'
    else:
        archives = sorted(root.glob(item['component'] + '_*.zip'), key=natural_key)
        if len(archives) != item['parts']:
            raise RuntimeError('PART_COUNT_GAP')
        found = False
        for archive in archives:
            with zipfile.ZipFile(archive) as zf:
                names = set()
                for info in zf.infolist():
                    safe = safe_member(info).as_posix()
                    if not info.is_dir() and safe in names:
                        raise RuntimeError('UNSAFE_ZIP: duplicate')
                    names.add(safe)
                    if safe == str(rel) and not info.is_dir():
                        if found or info.file_size >= GIT_BLOB_LIMIT:
                            raise RuntimeError('ARCHIVE_MEMBER_GAP')
                        # ZipExtFile checks CRC while the selected member is read.
                        with zf.open(info) as src, target.open('wb') as dest:
                            shutil.copyfileobj(src, dest)
                        found = True
        if found:
            operation = 'EXTRACT_ONLY'
        else:
            url = f"https://raw.githubusercontent.com/{owner_repo}/{item['source_commit']}/{urllib.parse.quote(item['path'], safe='/')}"
            target.write_bytes(http_bytes(url))
            operation = 'DOWNLOAD_MISSING_FILE'
    check_payload(target, meta)
    return target, operation, meta


def publish_batch(batch, plan, number, temp):
    evidence_path = f".github/nct-repair/{plan['task_id']}/batch-{number:03d}.json"
    evidence = temp / f'batch-{number:03d}.json'
    rows = [{k: v for k, v in row.items() if k != 'staged'} for row in batch]
    evidence.write_text(json.dumps({'task_id': plan['task_id'], 'run_id': os.getenv('GITHUB_RUN_ID'), 'files': rows}, indent=2) + '\n')
    candidates = [(row['destination'], Path(row['staged']), row['blob']) for row in batch]
    candidates.append((evidence_path, evidence, git('hash-object', '--no-filters', str(evidence))))
    for attempt in range(3):
        git('fetch', 'origin', 'main')
        git('reset', '--hard', 'origin/main')
        for path, src, expected in candidates:
            existing = subprocess.run(['git', 'rev-parse', f'HEAD:{path}'], capture_output=True, text=True)
            if existing.returncode == 0 and existing.stdout.strip() != expected:
                raise RuntimeError('COLLISION_BLOCKED: ' + path)
            if is_lfs_pointer(src) or src.stat().st_size >= GIT_BLOB_LIMIT:
                raise RuntimeError('STAGED_POINTER_OR_SIZE_GAP')
            actual = git('hash-object', '-w', '--no-filters', str(src))
            if actual != expected:
                raise RuntimeError('STAGED_HASH_GAP')
            git('update-index', '--add', '--cacheinfo', '100644', actual, path)
        if subprocess.run(['git', 'diff', '--cached', '--quiet']).returncode == 0:
            return git('rev-parse', 'HEAD')
        git('-c', 'core.hooksPath=/dev/null', 'commit', '-m', f"repair: {plan['task_id']} batch {number:03d}")
        commit = git('rev-parse', 'HEAD')
        result = subprocess.run(['git', '-c', 'core.hooksPath=/dev/null', 'push', 'origin', 'HEAD:main'], capture_output=True, text=True)
        git('fetch', 'origin', 'main')
        visible = subprocess.run(['git', 'merge-base', '--is-ancestor', commit, 'origin/main']).returncode == 0
        if visible:
            for path, src, expected in candidates:
                if git('rev-parse', f'origin/main:{path}') != expected:
                    raise RuntimeError('READ_BACK_CONTENT_MISMATCH')
            return commit
        message = result.stderr
        if any(x in message for x in ('GH008', 'GH001', 'GH013', 'Permission', 'permission', '403', 'protected')):
            raise RuntimeError('PUBLISH_NONRETRYABLE_GAP: ' + message[-500:])
        if attempt == 2:
            raise RuntimeError('PUBLISH_GAP: ' + message[-500:])
        time.sleep(5 * (attempt + 1))


def repair_queue(plan_path):
    plan = json.loads(Path(plan_path).read_text())
    root = Path(plan['destination_root'])
    if root.is_absolute() or '..' in root.parts or root.is_symlink():
        raise RuntimeError('UNSAFE_ROOT')
    if not re.fullmatch(r'[a-z0-9-]+', plan['task_id']):
        raise RuntimeError('INPUT_GAP: task_id')
    if git('remote', 'get-url', 'origin').removesuffix('.git') != 'https://github.com/' + plan['destination_repository']:
        raise RuntimeError('DESTINATION_REPOSITORY_GAP')
    for key, value in [('filter.lfs.clean', 'cat'), ('filter.lfs.smudge', 'cat'), ('filter.lfs.process', ''), ('filter.lfs.required', 'false'), ('core.autocrlf', 'false'), ('user.name', 'github-actions[bot]'), ('user.email', '41898282+github-actions[bot]@users.noreply.github.com')]:
        git('config', '--local', key, value)
    report_path = Path(os.environ.get('RUNNER_TEMP', tempfile.gettempdir())) / (plan['task_id'] + '-checkpoint.json')
    report = {'task_id': plan['task_id'], 'run_id': os.getenv('GITHUB_RUN_ID'), 'expected_files': len(plan['items']), 'files': [], 'blocked': plan.get('blocked', []), 'batches': [], 'verdict': 'PENDING_INDEPENDENT_VERIFICATION'}
    seen = set()
    with tempfile.TemporaryDirectory(prefix='repair-payload-') as td:
        temp = Path(td)
        batch = []
        batch_bytes = 0
        try:
            for n, item in enumerate(plan['items']):
                destination = (root / item['component'] / item['path']).as_posix()
                if destination in seen:
                    raise RuntimeError('DUPLICATE_INPUT')
                seen.add(destination)
                try:
                    src, operation, meta = prepare_item(root, item, temp / str(n))
                    row = dict(item, destination=destination, operation=operation, blob=meta['sha'], bytes=meta['size'], status='VERIFIED_EXISTING' if src is None else 'PREPARED')
                    if src is not None:
                        row.update(staged=str(src), sha256=sha256(src))
                        if batch and batch_bytes + meta['size'] > 80 * 1024 * 1024:
                            commit = publish_batch(batch, plan, len(report['batches']) + 1, temp)
                            report['batches'].append(commit)
                            for previous in batch:
                                previous.update(status='PUBLISHED_READ_BACK', commit=commit)
                            batch, batch_bytes = [], 0
                        batch.append(row)
                        batch_bytes += meta['size']
                    report['files'].append(row)
                    print(f"{operation} {destination}", flush=True)
                except (RuntimeError, OSError, zipfile.BadZipFile, SystemExit) as exc:
                    if str(exc).startswith(('PUBLISH', 'STAGED', 'READ_BACK', 'COLLISION_BLOCKED:')):
                        raise
                    report['blocked'].append({'destination': destination, 'reason': str(exc)})
                    print(f'GAP {destination}: {exc}', flush=True)
            if batch:
                commit = publish_batch(batch, plan, len(report['batches']) + 1, temp)
                report['batches'].append(commit)
                for row in batch:
                    row.update(status='PUBLISHED_READ_BACK', commit=commit)
        finally:
            for row in report['files']:
                row.pop('staged', None)
            report['verdict'] = 'GAP' if report['blocked'] else 'PENDING_INDEPENDENT_VERIFICATION'
            report_path.write_text(json.dumps(report, indent=2) + '\n')
            print(f'CHECKPOINT={report_path}', flush=True)
    if report['blocked']:
        raise SystemExit(2)


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] != "--queue":
        die("usage: extract_existing_parts.py --queue PLAN.json")
    repair_queue(sys.argv[2])
