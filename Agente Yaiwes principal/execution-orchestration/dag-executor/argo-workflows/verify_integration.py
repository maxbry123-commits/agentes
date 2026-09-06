import json
from pathlib import Path
from adapter import source_probe

root = Path(__file__).resolve().parent
probe = source_probe()
wiring = json.loads((root/'WIRING.json').read_text())
ficha = json.loads((root/'ficha.argo-workflows.v2.json').read_text())
assert wiring['fail_closed'] is True
assert wiring['direct_kernel_import'] is False
assert ficha['ejecucion']['llm_ratio'] == 0.0
assert ficha['contrato']['rol'] == 'dag_orchestrator'
assert probe['module'] == 'github.com/argoproj/argo-workflows/v4'
print('ARGO_STATIC_VERIFY_PASS')
