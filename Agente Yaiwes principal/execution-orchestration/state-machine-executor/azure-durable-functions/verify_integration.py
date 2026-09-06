import json
from pathlib import Path
from adapter import source_probe

root = Path(__file__).resolve().parent
p = source_probe()
wiring = json.loads((root/'WIRING.json').read_text())
ficha = json.loads((root/'ficha.azure-durable-functions.v2.json').read_text())
csproj = (root/'src/WebJobs.Extensions.DurableTask/WebJobs.Extensions.DurableTask.csproj').read_text()
assert p['sdk'] == '10.0.302'
assert wiring['fail_closed'] is True and wiring['direct_kernel_import'] is False
assert ficha['ejecucion']['llm_ratio'] == 0.0
assert ficha['contrato']['rol'] == 'state_machine_orchestrator'
assert '<TargetFrameworks>net8.0;net10.0</TargetFrameworks>' in csproj
assert '<MajorVersion>3</MajorVersion>' in csproj and '<MinorVersion>15</MinorVersion>' in csproj
print('AZURE_DURABLE_STATIC_VERIFY_PASS')
