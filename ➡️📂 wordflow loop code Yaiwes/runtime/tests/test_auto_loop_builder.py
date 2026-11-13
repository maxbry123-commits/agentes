from pathlib import Path
import importlib.util, sys, tempfile, json
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"src"/"core"/"auto_loop_builder.py"
spec=importlib.util.spec_from_file_location("auto_loop_builder",P)
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)

def intake(profile="frontend"):
    return {
      "schema":"yaiwes.project-intake/v1","project_id":"demo","profile":profile,
      "destination":"➡️📂 Wordflow LOOP Yaiwes/workspace/code/demo","file_count":2,
      "files":[{"filename":"README.md","sha256":"a"*64}],
      "architecture":{"project_id":"demo"},"requirements":[
        {"statement":"render editor","source_id":"a"},
        {"statement":"persist state","source_id":"b"}],
      "risks":[],"execution_authorized":False,"code_generation_authorized":False
    }

def test_builds_all_run_documents_without_global_mutation():
    docs=m.build_loop_documents(intake=intake(),instruction="Build and verify UI",run_id="run-001")
    assert set(docs)=={"TASK-CONTRACT.json","DAG.json","CRAZY-WALL.json","STATE.json","CHECKPOINT.json","BITACORA.md","ARCHITECTURE.json","SOURCE.json"}
    state=json.loads(docs["STATE.json"])
    assert state["global_code_graph_30_of_30_untouched"] is True
    dag=json.loads(docs["DAG.json"])
    assert any(n["id"]=="REQ-001" for n in dag["nodes"])
    contract=json.loads(docs["TASK-CONTRACT.json"])
    assert "MOBILE_TOUCH" in contract["frontend_policy"]

def test_persist_requires_authorization_and_readback():
    docs=m.build_loop_documents(intake=intake("backend"),instruction="Build API",run_id="run-002")
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        try:m.persist_run_documents(authorized_root=root,run_id="run-002",documents=docs,mutation_authorized=False)
        except PermissionError:pass
        else:raise AssertionError("authorization required")
        out=m.persist_run_documents(authorized_root=root,run_id="run-002",documents=docs,mutation_authorized=True)
        assert (out/"STATE.json").is_file()
        try:m.persist_run_documents(authorized_root=root,run_id="run-002",documents=docs,mutation_authorized=True)
        except m.AutoLoopError as e:assert str(e)=="RUN_ID_ALREADY_EXISTS"
        else:raise AssertionError("duplicate run accepted")

def test_invalid_run_id_fails():
    try:m.build_loop_documents(intake=intake(),instruction="x",run_id="../bad")
    except m.AutoLoopError as e:assert str(e)=="RUN_ID_INVALID"
    else:raise AssertionError("bad run accepted")
