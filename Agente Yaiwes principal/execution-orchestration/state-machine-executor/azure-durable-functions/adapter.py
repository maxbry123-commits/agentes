from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent

def source_probe():
    required = [
        ROOT / 'global.json',
        ROOT / 'Directory.Packages.props',
        ROOT / 'src/WebJobs.Extensions.DurableTask/WebJobs.Extensions.DurableTask.csproj',
        ROOT / 'src/WebJobs.Extensions.DurableTask/DurableTaskExtension.cs',
        ROOT / '.stylecop/GlobalSuppressions.cs',
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise RuntimeError({'missing': missing})
    sdk = json.loads((ROOT / 'global.json').read_text())['sdk']['version']
    return {
        'component': 'Azure-Durable-Functions',
        'classification': 'B',
        'sdk': sdk,
        'entry': str((ROOT / 'src/WebJobs.Extensions.DurableTask/DurableTaskExtension.cs').resolve()),
    }

def runtime_command():
    source_probe()
    return ['dotnet', 'build', 'src/WebJobs.Extensions.DurableTask/WebJobs.Extensions.DurableTask.csproj', '-f', 'net10.0']
