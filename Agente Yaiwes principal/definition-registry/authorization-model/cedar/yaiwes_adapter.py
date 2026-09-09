from pathlib import Path

ROOT = Path(__file__).resolve().parent

def source_probe():
    if not ROOT.exists():
        raise RuntimeError('component root missing')
    return {'component': 'Cedar', 'root': str(ROOT), 'exists': True}
