import hashlib
import pathlib
import re
import sys

ROOT = pathlib.Path('Core kernel Yaiwes')
COMPONENTS = ['APScheduler','Workalendar','Celery','Redis','Hatchet','Dagu','PostgreSQL','pgvector','gVisor']
VERIFY = '--verify' in sys.argv

def sha256(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):
            h.update(chunk)
    return h.hexdigest()

def license_files(root):
    rows=[]
    for p in root.rglob('*'):
        if not p.is_file() or p.name.startswith('SOURCE_'):
            continue
        n=p.name.lower()
        if re.match(r'^(license|licence|copying|notice|copyright)(\.|$|[-_])', n):
            rows.append((p.relative_to(root).as_posix(),sha256(p)))
    return sorted(rows)

gaps=[]
for slug in COMPONENTS:
    d=ROOT/slug
    if not d.is_dir():
        gaps.append(f'{slug}:DESTINATION_MISSING'); continue
    for req in ('SOURCE_URL.txt','SOURCE_COMMIT.txt'):
        if not (d/req).is_file(): gaps.append(f'{slug}:TRACE_MISSING:{req}')
    evidence=license_files(d)
    trace=d/'SOURCE_LICENSE.txt'
    if VERIFY:
        if not trace.is_file(): gaps.append(f'{slug}:TRACE_MISSING:SOURCE_LICENSE.txt')
    else:
        if not evidence:
            gaps.append(f'{slug}:LICENSE_EVIDENCE_MISSING'); continue
        if not trace.exists():
            trace.write_text('SOURCE_LICENSE_FILES\n'+''.join(f'{digest}  {rel}\n' for rel,digest in evidence),encoding='utf-8')
        sums=[]
        for p in sorted(x for x in d.rglob('*') if x.is_file() and x.name!='SOURCE_SHA256SUMS.txt'):
            sums.append(f'{sha256(p)}  {p.relative_to(d).as_posix()}\n')
        (d/'SOURCE_SHA256SUMS.txt').write_text(''.join(sums),encoding='utf-8')
    sums=d/'SOURCE_SHA256SUMS.txt'
    if VERIFY and sums.is_file():
        for line in sums.read_text(encoding='utf-8').splitlines():
            if not line: continue
            try: digest,rel=line.split('  ',1)
            except ValueError:
                gaps.append(f'{slug}:SUM_FORMAT_GAP'); break
            p=d/rel
            if not p.is_file(): gaps.append(f'{slug}:READ_BACK_MISSING:{rel}'); break
            if sha256(p)!=digest: gaps.append(f'{slug}:READ_BACK_HASH_GAP:{rel}'); break
if gaps:
    print('\n'.join(gaps),file=sys.stderr)
    raise SystemExit(42)
print(('VERIFY' if VERIFY else 'REPAIR')+'_LICENSE_TRACE_PASS=9/9')
