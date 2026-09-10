from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
POM = ROOT / 'pom.xml'
ZEEBE = ROOT / 'zeebe'


def source_probe() -> dict:
    required = [POM, ZEEBE]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise RuntimeError('upstream markers missing: ' + ','.join(missing))

    project = ET.parse(POM).getroot()
    artifact = next((el.text for el in project.iter() if el.tag.endswith('artifactId') and el.text), None)
    modules = [el.text for el in project.iter() if el.tag.endswith('module') and el.text]
    if artifact is None:
        raise RuntimeError('Camunda root artifactId missing')
    if not ZEEBE.is_dir():
        raise RuntimeError('Camunda Zeebe workflow engine tree missing')

    return {
        'ok': True,
        'component': 'Camunda',
        'classification': 'B',
        'root_artifact': artifact,
        'module_count': len(modules),
        'zeebe_root': str(ZEEBE.resolve()),
    }


def runtime_command() -> list[str]:
    source_probe()
    return [
        'mvn', '-q', '-N',
        'help:evaluate',
        '-Dexpression=project.artifactId',
        '-DforceStdout',
    ]


def runtime_cwd() -> str:
    return str(ROOT)
