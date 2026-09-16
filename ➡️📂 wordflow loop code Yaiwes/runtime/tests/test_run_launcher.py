from pathlib import Path
import importlib.util, sys, tempfile, json
ROOT=Path(__file__).resolve().parents[1]
CORE=ROOT/"src"/"core"
sys.path.insert(0,str(CORE))
spec=importlib.util.spec_from_file_location("run_launcher",CORE/"run_launcher.py")
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)

def test_literal_instruction_creates_ready_run():
    with tempfile.TemporaryDirectory() as td:
        out=m.launch_run(instruction="Create frontend editor",project_id="ui-demo",profile="frontend",run_id="literal-001",authorized_root=Path(td),mutation_authorized=True)
        assert (out/"CRAZY-WALL.json").is_file()
        state=json.loads((out/"STATE.json").read_text())
        assert state["status"]=="READY"
        assert state["global_code_graph_30_of_30_untouched"] is True

def test_manifest_input_creates_backend_run():
    manifest={"project_id":"api-demo","profile":"backend","files":[
        {"source_id":"a","filename":"README.md","content":"# API demo\n## Routes","provenance":"upload:a"},
        {"source_id":"b","filename":"main.py","content":"def health():\n    return 'ok'\n","provenance":"upload:b"},
    ]}
    with tempfile.TemporaryDirectory() as td:
        out=m.launch_run(instruction="Build API",project_id="",profile="general",run_id="manifest-001",authorized_root=Path(td),manifest=manifest,mutation_authorized=True)
        contract=json.loads((out/"TASK-CONTRACT.json").read_text())
        assert contract["project_id"]=="api-demo"
        assert contract["profile"]=="backend"

def test_launcher_requires_mutation_authorization():
    with tempfile.TemporaryDirectory() as td:
        try:m.launch_run(instruction="x",project_id="safe",profile="general",run_id="no-write",authorized_root=Path(td),mutation_authorized=False)
        except PermissionError:pass
        else:raise AssertionError("write happened without authorization")
