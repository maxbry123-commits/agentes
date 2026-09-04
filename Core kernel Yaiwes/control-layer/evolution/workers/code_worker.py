"""CodeWorker · rellena adapter.py determinista + llm_hook."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

@dataclass
class WorkerResult:
    ok: bool
    adapter_path: str
    capabilities: list
    mode: str
    error: str = ""
    def to_dict(self): return asdict(self)

_BODIES = {
    "code.generate": "def handle_code_generate(payload):\n    spec=str(payload.get('spec') or payload.get('task') or '')\n    return {'ok': True, 'capability': 'code.generate', 'code': f'# {spec[:80]}\\ndef run():\\n    return True\\n', 'plugin': '{plugin_id}'}\n",
    "code.analyze": "def handle_code_analyze(payload):\n    src=str(payload.get('code') or '')\n    return {'ok': True, 'capability': 'code.analyze', 'lines': src.count(chr(10))+1, 'plugin': '{plugin_id}'}\n",
    "git.diff": "def handle_git_diff(payload):\n    return {'ok': True, 'capability': 'git.diff', 'diff': payload.get('diff') or '', 'plugin': '{plugin_id}'}\n",
}

class CodeWorker:
    def fill_adapter(self, package_path, *, plugin_id, capabilities, mode="deterministic"):
        package_path = Path(package_path)
        if not package_path.exists():
            return WorkerResult(False, str(package_path), capabilities, mode, "package_not_found")
        handlers_src, map_entries = [], []
        for cap in capabilities:
            body, fn_name, key = None, None, None
            for k, tmpl in _BODIES.items():
                if k in cap or cap.endswith(k):
                    body = tmpl.format(plugin_id=plugin_id); key = k; fn_name = f"handle_{k.replace('.', '_')}"; break
            if body is None:
                fn_name = "handle_" + cap.replace(".", "_").replace("-", "_")
                body = f"def {fn_name}(payload):\n    return {{'ok': True, 'capability': '{cap}', 'plugin': '{plugin_id}', 'payload_echo': dict(payload or {{}}), 'llm_hook': {str(mode=='llm_hook')}}}\n"
            handlers_src.append(body)
            map_entries.append(f'    "{cap}": {fn_name},')
        src = f'"""Adapter CodeWorker mode={mode} plugin={plugin_id}"""\nfrom typing import Any\nCAPABILITIES = {capabilities!r}\n\n' + "\n".join(handlers_src) + "\nHANDLERS = {\n" + "\n".join(map_entries) + "\n}\n\ndef handle(capability, payload=None):\n    h = HANDLERS.get(capability)\n    if h is None: return {{'ok': False, 'error': f'unknown:{{capability}}'}}\n    return h(dict(payload or {{}}))\n"
        (package_path / "adapter.py").write_text(src, encoding="utf-8")
        return WorkerResult(True, str(package_path / "adapter.py"), capabilities, mode)
