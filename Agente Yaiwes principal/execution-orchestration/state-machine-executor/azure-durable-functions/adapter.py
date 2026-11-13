from __future__ import annotations

from pathlib import Path
import json
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT / 'src/WebJobs.Extensions.DurableTask/WebJobs.Extensions.DurableTask.csproj'
ENTRY = ROOT / 'src/WebJobs.Extensions.DurableTask/DurableTaskExtension.cs'


def source_probe() -> dict:
    required = [
        ROOT / 'global.json',
        ROOT / 'Directory.Packages.props',
        PROJECT,
        ENTRY,
        ROOT / '.stylecop/GlobalSuppressions.cs',
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise RuntimeError({'missing': missing})

    sdk = json.loads((ROOT / 'global.json').read_text())['sdk']['version']
    project = ET.parse(PROJECT).getroot()
    frameworks = next((el.text for el in project.iter() if el.tag.endswith('TargetFrameworks')), '') or ''
    assembly = next((el.text for el in project.iter() if el.tag.endswith('AssemblyName')), '') or ''
    source = ENTRY.read_text(encoding='utf-8-sig')
    if 'class DurableTaskExtension' not in source or 'IExtensionConfigProvider' not in source:
        raise RuntimeError('DurableTaskExtension orchestration surface not found')
    if 'net8.0' not in frameworks or 'Microsoft.Azure.WebJobs.Extensions.DurableTask' not in assembly:
        raise RuntimeError('Durable Functions project metadata mismatch')

    return {
        'ok': True,
        'component': 'Azure-Durable-Functions',
        'classification': 'B',
        'sdk': sdk,
        'frameworks': frameworks,
        'assembly': assembly,
        'entry': str(ENTRY.resolve()),
    }


def runtime_command() -> list[str]:
    source_probe()
    return [
        'dotnet', 'msbuild',
        'src/WebJobs.Extensions.DurableTask/WebJobs.Extensions.DurableTask.csproj',
        '-getProperty:TargetFrameworks',
        '-getProperty:AssemblyName',
        '-verbosity:quiet',
    ]


def runtime_cwd() -> str:
    return str(ROOT)
