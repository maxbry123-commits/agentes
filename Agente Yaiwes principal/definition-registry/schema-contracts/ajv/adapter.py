from __future__ import annotations
import json, subprocess
from pathlib import Path
from typing import Any, Mapping
_ROOT=Path(__file__).resolve().parent
_BRIDGE=_ROOT/'yaiwes_bridge.js'
class AjvIntegrationError(RuntimeError): pass
def validate_json_schema(schema: Mapping[str,Any], data: Any, *, options: Mapping[str,Any]|None=None, timeout_s: float=10.0)->dict[str,Any]:
    if not isinstance(schema,Mapping): raise TypeError('schema must be a mapping')
    if timeout_s<=0: raise ValueError('timeout_s must be > 0')
    payload={'schema':dict(schema),'data':data,'options':dict(options or {})}
    try:
        p=subprocess.run(['node',str(_BRIDGE)],input=json.dumps(payload,separators=(',',':'),ensure_ascii=False),text=True,capture_output=True,cwd=_ROOT,timeout=timeout_s,check=False)
    except (OSError,subprocess.TimeoutExpired) as exc: raise AjvIntegrationError(f'Ajv bridge unavailable: {exc}') from exc
    if p.returncode!=0: raise AjvIntegrationError('Ajv bridge failed: '+(p.stderr.strip() or 'unknown bridge error'))
    try: result=json.loads(p.stdout)
    except json.JSONDecodeError as exc: raise AjvIntegrationError('Ajv bridge returned invalid JSON') from exc
    if not isinstance(result,dict) or not isinstance(result.get('valid'),bool): raise AjvIntegrationError('Ajv bridge returned an invalid contract')
    if result.get('errors') is not None and not isinstance(result['errors'],list): raise AjvIntegrationError('Ajv bridge errors must be list or null')
    return result
