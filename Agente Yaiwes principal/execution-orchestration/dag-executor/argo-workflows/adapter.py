from pathlib import Path

ROOT = Path(__file__).resolve().parent

def source_probe():
    required = [ROOT / 'go.mod', ROOT / 'workflow/controller/controller.go', ROOT / 'pkg/apis/workflow/v1alpha1']
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise RuntimeError({'missing': missing})
    return {'component': 'Argo-Workflows', 'classification': 'B', 'module': 'github.com/argoproj/argo-workflows/v4', 'controller': str((ROOT / 'workflow/controller/controller.go').resolve())}

def runtime_command():
    source_probe()
    return ['go', 'test', './workflow/validate', '-run', '^$']
