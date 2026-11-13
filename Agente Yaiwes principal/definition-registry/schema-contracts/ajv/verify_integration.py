from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
required=['lib/core.ts','package.json','tsconfig.json','adapter.py','yaiwes_bridge.js','WIRING.json','ficha.ajv.v2.json']
missing=[p for p in required if not (ROOT/p).exists()]
if missing: raise SystemExit('missing required files: '+', '.join(missing))
w=json.loads((ROOT/'WIRING.json').read_text()); f=json.loads((ROOT/'ficha.ajv.v2.json').read_text())
if w.get('artifact_id')!=f.get('artifact_id'): raise SystemExit('artifact_id mismatch')
if w.get('fail_closed') is not True: raise SystemExit('wiring must be fail_closed')
if f.get('ejecucion',{}).get('llm_ratio')!=0.0: raise SystemExit('Ajv must remain deterministic')
print('AJV_STATIC_VERIFY_PASS')
