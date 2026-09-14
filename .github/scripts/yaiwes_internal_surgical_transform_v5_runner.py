#!/usr/bin/env python3
from __future__ import annotations
import ast
import importlib.util
import sys
from pathlib import Path

SCRIPT = Path(__file__).with_name('yaiwes_internal_surgical_transform_v5.py')
spec = importlib.util.spec_from_file_location('yaiwes_internal_surgical_transform_v5_module', SCRIPT)
if spec is None or spec.loader is None:
    raise SystemExit('V5_IMPORT_FAILED')
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)
mod.VERSION = 'YAIWES-INTERNAL-PERSISTENCE-v5.1'

# A project/package brand such as "pentestgpt_agent" is not itself evidence that
# every file below it is offensive. V5.1 classifies functional leaf/segments.
STRONG_SEGMENTS = {
    'attack','attacks','attackchain','exploit','exploits','recon','redteam','red_team','red-team',
    'scanner','scanners','scanning','payload','payloads','fuzzer','fuzz','phishing','post_exploit',
    'privesc','privilege_escalation','c2','metasploit','nmap','sqlmap','nuclei','masscan','shellcode',
    'bruteforce','brute_force','exfil','malware','ransom','injection','ssrf','vulnerability','vulnerabilities'
}
STRONG_LEAF_TOKENS = (
    'exploit','attack','recon','scanner','payload','fuzz','phishing','post_exploit','privesc',
    'nmap','sqlmap','nuclei','metasploit','shellcode','bruteforce','brute_force','exfil','malware',
    'injection','ssrf','run_code','command_exec','code_exec','reverse_shell','credential_dump'
)
BENIGN_TOKENS = tuple(set(mod.BENIGN_TOKENS) | {
    'plan','planner','planning','loop','trace','report','orchestrat','multiagent','middleware','blackboard',
    'resource','reconnect','conversation','monitor','summar','graph_store','store','history','session',
    'context','event','dispatcher','profiler','aggregator','identifier','audit','registry','factory','provider'
})


def surgical_classify(rel: str, original: str, had_quarantine: bool):
    p = Path(rel)
    parts = [x.lower() for x in p.parts]
    leaf = p.stem.lower()
    low = original.lower()

    # Functional offensive leaf wins.
    if any(tok in leaf for tok in STRONG_LEAF_TOKENS):
        return 'BLOCK_OFFENSIVE', 'offensive functional leaf'
    # Exact operational attack/red-team segments win; brand namespaces such as
    # pentestgpt_agent are intentionally not included here.
    if any(seg in STRONG_SEGMENTS for seg in parts[:-1]):
        return 'BLOCK_OFFENSIVE', 'offensive functional path segment'
    # Strong dangerous behavior plus an execution surface is blocked even when
    # the filename is neutral.
    if any(tok in low for tok in mod.STRONG_CONTENT_RISK) and any(m in low for m in mod.EXEC_MARKERS):
        return 'BLOCK_OFFENSIVE', 'offensive content plus execution surface'
    # Preserve useful task/orchestration infrastructure from the quarantined
    # original. These files are not converted to generic stubs.
    low_path = rel.lower()
    if any(tok in low_path for tok in BENIGN_TOKENS):
        return 'RESTORE_BENIGN', 'benign planner/memory/orchestration/support semantics'
    # Ambiguous previously-effectful code remains disabled until independently
    # reviewed; do not silently restore it.
    if had_quarantine:
        return 'REVIEW_FAIL_CLOSED', 'previously effectful file without safe classification'
    return 'KEEP_UNCHANGED', 'no surgical transformation required'

mod.classify = surgical_classify

FORBIDDEN_ROOTS = {'subprocess','requests','httpx','aiohttp','socket'}
FORBIDDEN_NAMES = {'eval','exec'}
FORBIDDEN_ATTRS = {('os','system'),('os','popen')}


def call_name(node):
    if isinstance(node, ast.Name):
        return (node.id,)
    if isinstance(node, ast.Attribute):
        left = call_name(node.value)
        return left + (node.attr,) if left else (node.attr,)
    return ()


def python_forbidden_calls(text):
    tree = ast.parse(text)
    hits = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = call_name(node.func)
        if not name:
            continue
        if name[0] in FORBIDDEN_ROOTS or name[-1] in FORBIDDEN_NAMES or tuple(name[:2]) in FORBIDDEN_ATTRS:
            hits.append('.'.join(name))
    return hits


MUST_RESTORE = {
    '🏈 12-PentestGPT': {
        'pentestgpt_agent/src/pentestgpt_agent/memory.py',
        'pentestgpt_agent/src/pentestgpt_agent/plan.py',
        'pentestgpt_agent/src/pentestgpt_agent/loop.py',
        'pentestgpt_agent/src/pentestgpt_agent/trace.py',
        'pentestgpt_legacy/llm/base.py',
        'pentestgpt_legacy/llm/client.py',
        'pentestgpt_legacy/llm/factory.py',
    },
    '🏈 06-PentAGI': {
        'frontend/src/features/resources/resources-rest.ts',
        'backend/pkg/resources/resources.go',
    },
    '🏈 02-CyberStrikeAI': {
        'internal/multiagent/tool_pair_reconciler_middleware.go',
    },
}
MUST_BLOCK = {
    '🏈 04-AI-Pentest': {
        'backend/tools/network_scanner.py',
        'backend/tools/post_exploit.py',
    },
    '🏈 10-Pentest-Swarm-AI': {
        'internal/agent/exploit/executor.go',
        'internal/tools/nmap.go',
        'internal/tools/sqlmap.go',
    },
    '🏈 22-PHANTOM': {
        'phantom/tools/fuzzer/fuzzer_actions.py',
    },
}


def validate(manifests):
    errors = []
    if len(manifests) != 24:
        errors.append(f'COMPONENT_COUNT:{len(manifests)}')
    by_component = {m['component']: m for m in manifests}
    for m in manifests:
        comp = mod.ROOT / m['component']
        code = comp / 'code'
        decisions = {x['path']: x['decision'] for x in m['files']}
        for x in m['files']:
            active = code / x['path']
            q = code / x['quarantine'] if x.get('quarantine') else None
            if not active.is_file():
                errors.append(f"MISSING_ACTIVE:{m['component']}:{x['path']}")
                continue
            at = mod.read_text(active)
            if at is None:
                continue
            if mod.sha256_text(at) != x['active_sha256']:
                errors.append(f"ACTIVE_SHA:{m['component']}:{x['path']}")
            if q and not q.is_file():
                errors.append(f"MISSING_QUARANTINE:{m['component']}:{x['path']}")
            if x['decision'] == 'RESTORE_BENIGN' and mod.sha256_text(at) != x['original_sha256']:
                errors.append(f"BENIGN_NOT_RESTORED:{m['component']}:{x['path']}")
            if x['decision'] in {'BLOCK_OFFENSIVE','REVIEW_FAIL_CLOSED'}:
                if active.suffix.lower() == '.py':
                    try:
                        hits = python_forbidden_calls(at)
                    except SyntaxError as e:
                        errors.append(f"PY_SYNTAX:{m['component']}:{x['path']}:{e.lineno}")
                        continue
                    if hits:
                        errors.append(f"PY_FORBIDDEN_CALL:{m['component']}:{x['path']}:{','.join(hits[:3])}")
                elif any(marker in at.lower() for marker in mod.EXEC_MARKERS):
                    errors.append(f"RESIDUAL_EXECUTION:{m['component']}:{x['path']}")
        for path in MUST_RESTORE.get(m['component'], set()):
            if decisions.get(path) != 'RESTORE_BENIGN':
                errors.append(f"REQUIRED_BENIGN_NOT_RESTORED:{m['component']}:{path}:{decisions.get(path)}")
        for path in MUST_BLOCK.get(m['component'], set()):
            if decisions.get(path) != 'BLOCK_OFFENSIVE':
                errors.append(f"REQUIRED_OFFENSIVE_NOT_BLOCKED:{m['component']}:{path}:{decisions.get(path)}")
        if not (code / 'yaiwes_internal' / 'persistence_runtime.py').is_file():
            errors.append(f"NO_RUNTIME:{m['component']}")
    for comp in set(MUST_RESTORE) | set(MUST_BLOCK):
        if comp not in by_component:
            errors.append(f'MISSING_COMPONENT_ASSERTION:{comp}')
    return errors

mod.validate = validate
mod.main()
