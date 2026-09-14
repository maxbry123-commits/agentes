#!/usr/bin/env python3
from __future__ import annotations
import ast
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

SCRIPT = Path(__file__).with_name('yaiwes_internal_surgical_transform_v5.py')
spec = importlib.util.spec_from_file_location('yaiwes_internal_surgical_transform_v52_module', SCRIPT)
if spec is None or spec.loader is None:
    raise SystemExit('V52_IMPORT_FAILED')
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)
mod.VERSION = 'YAIWES-INTERNAL-PERSISTENCE-v5.2'

STRONG_SEGMENTS = {
    'attack','attacks','attackchain','exploit','exploits','recon','redteam','red_team','red-team',
    'scanner','scanners','scanning','payload','payloads','fuzzer','fuzz','phishing','post_exploit',
    'privesc','privilege_escalation','c2','metasploit','nmap','sqlmap','nuclei','masscan','shellcode',
    'bruteforce','brute_force','exfil','malware','ransom','injection','ssrf','vulnerability','vulnerabilities'
}
STRONG_LEAF_WORDS = {
    'exploit','attack','recon','scanner','scanning','payload','fuzz','fuzzer','phishing','privesc',
    'nmap','sqlmap','nuclei','metasploit','shellcode','bruteforce','exfil','malware','injection','ssrf',
    'vulnerability','vulnerabilities'
}
STRONG_LEAF_PHRASES = {
    'post_exploit','brute_force','run_code','command_exec','code_exec','reverse_shell','credential_dump',
    'privilege_escalation','red_team'
}
BENIGN_TOKENS = tuple(set(mod.BENIGN_TOKENS) | {
    'plan','planner','planning','loop','trace','report','orchestrat','multiagent','middleware','blackboard',
    'resource','reconnect','conversation','monitor','summar','graph_store','store','history','session',
    'context','event','dispatcher','profiler','aggregator','identifier','audit','registry','factory','provider'
})

def leaf_words(leaf: str):
    return {x for x in re.split(r'[^a-z0-9]+', leaf) if x}

def surgical_classify(rel: str, original: str, had_quarantine: bool):
    p = Path(rel)
    parts = [x.lower() for x in p.parts]
    leaf = p.stem.lower()
    words = leaf_words(leaf)
    low = original.lower()
    if words & STRONG_LEAF_WORDS or any(phrase in leaf for phrase in STRONG_LEAF_PHRASES):
        return 'BLOCK_OFFENSIVE', 'offensive functional leaf'
    if any(seg in STRONG_SEGMENTS for seg in parts[:-1]):
        return 'BLOCK_OFFENSIVE', 'offensive functional path segment'
    if any(tok in low for tok in mod.STRONG_CONTENT_RISK) and any(m in low for m in mod.EXEC_MARKERS):
        return 'BLOCK_OFFENSIVE', 'offensive content plus execution surface'
    low_path = rel.lower()
    if any(tok in low_path for tok in BENIGN_TOKENS):
        return 'RESTORE_BENIGN', 'benign planner/memory/orchestration/support semantics'
    if had_quarantine:
        return 'REVIEW_FAIL_CLOSED', 'previously effectful file without safe classification'
    return 'KEEP_UNCHANGED', 'audited; no transformation required'

mod.classify = surgical_classify

# Every classified/restored useful file is a persistence link. The component runtime
# records checkpoint/provenance for links; it never imports quarantined originals.
mod.RUNTIME = mod.RUNTIME.replace(
    'links = [x for x in manifest["files"] if x["decision"] in {"BLOCK_OFFENSIVE","REVIEW_FAIL_CLOSED"}]',
    'links = [x for x in manifest["files"] if x.get("link")]'
)

_base_transform = mod.transform_component

def _sha(s: str) -> str:
    return hashlib.sha256(s.encode('utf-8')).hexdigest()

def transform_component_v52(comp: Path):
    manifest = _base_transform(comp)
    code = comp / 'code'
    by_path = {x['path']: x for x in manifest['files']}

    # Account for every active runtime source in the transformation scope, including
    # KEEP_UNCHANGED files, so the evidence is actually file-by-file.
    for active in list(mod.active_sources(code)):
        rel = active.relative_to(code).as_posix()
        if rel in by_path:
            continue
        original, q, had_q = mod.original_for(code, active)
        if original is None:
            continue
        decision, reason = mod.classify(rel, original, had_q)
        active_text = mod.read_text(active) or ''
        item = {
            'path': rel,
            'decision': decision,
            'reason': reason,
            'original_sha256': _sha(original),
            'active_sha256': _sha(active_text),
            'quarantine': str(q.relative_to(code)) if q else None,
            'link': decision != 'KEEP_UNCHANGED',
        }
        manifest['files'].append(item)
        by_path[rel] = item

    # Restored benign capabilities are links too; they preserve their exact source
    # while participating in checkpoint/provenance handoff.
    for item in manifest['files']:
        item['link'] = item['decision'] != 'KEEP_UNCHANGED'

    manifest['files'].sort(key=lambda x: x['path'])
    manifest['source_code_available'] = bool(manifest['files'])
    manifest['source_code_status'] = 'AVAILABLE' if manifest['files'] else 'SOURCE_CODE_UNAVAILABLE'
    manifest['counts'] = {
        'accounted': len(manifest['files']),
        'keep_unchanged': sum(x['decision'] == 'KEEP_UNCHANGED' for x in manifest['files']),
        'restored_benign': sum(x['decision'] == 'RESTORE_BENIGN' for x in manifest['files']),
        'blocked_offensive': sum(x['decision'] == 'BLOCK_OFFENSIVE' for x in manifest['files']),
        'review_fail_closed': sum(x['decision'] == 'REVIEW_FAIL_CLOSED' for x in manifest['files']),
        'links': sum(bool(x['link']) for x in manifest['files']),
    }
    (comp / 'INTERNAL-SURGICAL-MANIFEST-V5.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    c = manifest['counts']
    (comp / 'README-INTERNAL-V5.md').write_text(
        f"# {comp.name} — {mod.VERSION}\n\n## {mod.TEAM}\n\n"
        "`AUDIT ALL → CLASSIFY → KEEP | RESTORE_BENIGN | BLOCK_OFFENSIVE | REVIEW_FAIL_CLOSED → LINK → CHECKPOINT → VERIFY → RELEASE`\n\n"
        f"- Fuente interna: **{manifest['source_code_status']}**\n"
        f"- Archivos auditados: **{c['accounted']}**\n- Sin cambio: **{c['keep_unchanged']}**\n"
        f"- Restaurados benignos: **{c['restored_benign']}**\n- Bloqueados ofensivos: **{c['blocked_offensive']}**\n"
        f"- Revisión fail-closed: **{c['review_fail_closed']}**\n- Links internos: **{c['links']}**\n",
        encoding='utf-8'
    )
    return manifest

mod.transform_component = transform_component_v52

FORBIDDEN_ROOTS = {'subprocess','requests','httpx','aiohttp','socket'}
FORBIDDEN_NAMES = {'eval','exec'}
FORBIDDEN_ATTRS = {('os','system'),('os','popen')}

def call_name(node):
    if isinstance(node, ast.Name): return (node.id,)
    if isinstance(node, ast.Attribute):
        left = call_name(node.value)
        return left + (node.attr,) if left else (node.attr,)
    return ()

def python_forbidden_calls(text):
    tree = ast.parse(text); hits=[]
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call): continue
        name = call_name(node.func)
        if name and (name[0] in FORBIDDEN_ROOTS or name[-1] in FORBIDDEN_NAMES or tuple(name[:2]) in FORBIDDEN_ATTRS):
            hits.append('.'.join(name))
    return hits

MUST_RESTORE = {
    '🏈 12-PentestGPT': {
        'pentestgpt_agent/src/pentestgpt_agent/memory.py','pentestgpt_agent/src/pentestgpt_agent/plan.py',
        'pentestgpt_agent/src/pentestgpt_agent/loop.py','pentestgpt_agent/src/pentestgpt_agent/trace.py',
        'pentestgpt_legacy/llm/base.py','pentestgpt_legacy/llm/client.py','pentestgpt_legacy/llm/factory.py',
    },
    '🏈 06-PentAGI': {'frontend/src/features/resources/resources-rest.ts','backend/pkg/resources/resources.go'},
    '🏈 02-CyberStrikeAI': {'internal/multiagent/tool_pair_reconciler_middleware.go'},
}
MUST_BLOCK = {
    '🏈 04-AI-Pentest': {'backend/tools/network_scanner.py','backend/tools/post_exploit.py'},
    '🏈 10-Pentest-Swarm-AI': {'internal/agent/exploit/executor.go','internal/tools/nmap.go','internal/tools/sqlmap.go'},
    '🏈 22-PHANTOM': {'phantom/tools/fuzzer/fuzzer_actions.py'},
}

def validate(manifests):
    errors=[]
    if len(manifests)!=24: errors.append(f'COMPONENT_COUNT:{len(manifests)}')
    for m in manifests:
        comp=mod.ROOT/m['component']; code=comp/'code'; decisions={x['path']:x['decision'] for x in m['files']}
        for x in m['files']:
            active=code/x['path']; q=code/x['quarantine'] if x.get('quarantine') else None
            if not active.is_file(): errors.append(f"MISSING_ACTIVE:{m['component']}:{x['path']}"); continue
            at=mod.read_text(active)
            if at is None: continue
            if _sha(at)!=x['active_sha256']: errors.append(f"ACTIVE_SHA:{m['component']}:{x['path']}")
            if q and not q.is_file(): errors.append(f"MISSING_QUARANTINE:{m['component']}:{x['path']}")
            if x['decision']=='RESTORE_BENIGN' and _sha(at)!=x['original_sha256']: errors.append(f"BENIGN_NOT_RESTORED:{m['component']}:{x['path']}")
            if x['decision'] in {'BLOCK_OFFENSIVE','REVIEW_FAIL_CLOSED'}:
                if active.suffix.lower()=='.py':
                    try: hits=python_forbidden_calls(at)
                    except SyntaxError as e: errors.append(f"PY_SYNTAX:{m['component']}:{x['path']}:{e.lineno}"); continue
                    if hits: errors.append(f"PY_FORBIDDEN_CALL:{m['component']}:{x['path']}:{','.join(hits[:3])}")
                elif any(marker in at.lower() for marker in mod.EXEC_MARKERS):
                    errors.append(f"RESIDUAL_EXECUTION:{m['component']}:{x['path']}")
        for path in MUST_RESTORE.get(m['component'],set()):
            if decisions.get(path)!='RESTORE_BENIGN': errors.append(f"REQUIRED_BENIGN_NOT_RESTORED:{m['component']}:{path}:{decisions.get(path)}")
        for path in MUST_BLOCK.get(m['component'],set()):
            if decisions.get(path)!='BLOCK_OFFENSIVE': errors.append(f"REQUIRED_OFFENSIVE_NOT_BLOCKED:{m['component']}:{path}:{decisions.get(path)}")
        if m['component']!='🏈 24-Security-AI-Agent' and m['counts']['links']<=0:
            errors.append(f"NO_INTERNAL_LINKS:{m['component']}")
        if m['component']=='🏈 24-Security-AI-Agent' and m['source_code_available']:
            errors.append('EXPECTED_PUBLIC_SOURCE_GAP_NOT_PRESENT:🏈 24-Security-AI-Agent')
        if not (code/'yaiwes_internal'/'persistence_runtime.py').is_file(): errors.append(f"NO_RUNTIME:{m['component']}")
    return errors

mod.validate = validate
mod.main()

# Make the unavoidable upstream source gap explicit in the global evidence.
report_path = mod.FIELD / 'YAIWES-INTERNAL-SURGICAL-REPORT-V5.json'
report = json.loads(report_path.read_text(encoding='utf-8'))
manifests = [json.loads((c/'INTERNAL-SURGICAL-MANIFEST-V5.json').read_text(encoding='utf-8')) for c in mod.components()]
report['version'] = mod.VERSION
report['keep_unchanged'] = sum(m['counts'].get('keep_unchanged',0) for m in manifests)
report['source_code_components'] = sum(bool(m.get('source_code_available')) for m in manifests)
report['source_code_unavailable'] = [m['component'] for m in manifests if not m.get('source_code_available')]
report['component_chain_count'] = 24
report['links'] = sum(m['counts']['links'] for m in manifests)
report['summary'] = [{'component':m['component'],'source_code_status':m['source_code_status'],**m['counts']} for m in manifests]
report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'version':mod.VERSION,'source_code_components':report['source_code_components'],'source_code_unavailable':report['source_code_unavailable'],'files_accounted':report['files_accounted'],'links':report['links']}, ensure_ascii=False))
