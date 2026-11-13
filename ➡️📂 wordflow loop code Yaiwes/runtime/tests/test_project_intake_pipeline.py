from pathlib import Path
import importlib.util, sys

ROOT=Path(__file__).resolve().parents[1]
CORE=ROOT/"src"/"core"
sys.path.insert(0,str(CORE))
spec=importlib.util.spec_from_file_location("project_intake_pipeline",CORE/"project_intake_pipeline.py")
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)

def test_two_files_infer_project_and_architecture():
    files=[
        m.InputFile("a","package.json",'{"name":"demo-ui","dependencies":{"x":"1"}}',"upload:a"),
        m.InputFile("b","README.md","# demo-ui\n## UI\nBrowser mobile frontend","upload:b"),
    ]
    r=m.analyze_project(files,profile="frontend")
    assert r.project_id=="demo-ui"
    assert r.file_count==2
    assert r.destination.endswith("/workspace/code/demo-ui")
    assert r.execution_authorized is False and r.code_generation_authorized is False
    assert "markdown" in r.architecture["formats"]

def test_accepts_exactly_100_files_with_hint():
    files=[m.InputFile(f"id{i}",f"f{i}.txt",f"value {i}",f"upload:{i}") for i in range(100)]
    r=m.analyze_project(files,profile="general",project_hint="bulk-100")
    assert r.file_count==100

def test_rejects_more_than_100():
    files=[m.InputFile(f"id{i}",f"f{i}.txt","x",f"upload:{i}") for i in range(101)]
    try:m.analyze_project(files,profile="general",project_hint="too-many")
    except m.ProjectIntakeError as e: assert str(e)=="FILE_COUNT_MUST_BE_1_TO_100"
    else: raise AssertionError("expected limit")

def test_rejects_unsafe_path():
    try:m.analyze_project([m.InputFile("x","../x.py","print(1)","upload")],profile="backend",project_hint="x")
    except m.ProjectIntakeError as e: assert str(e)=="UNSAFE_INPUT_FILENAME"
    else: raise AssertionError("unsafe path accepted")

def test_ambiguous_project_fails_closed():
    files=[
        m.InputFile("a","project.json",'{"project_id":"one"}',"upload"),
        m.InputFile("b","README.md","# two","upload"),
    ]
    try:m.analyze_project(files,profile="general")
    except m.ProjectIntakeError as e: assert str(e).startswith("PROJECT_ID_AMBIGUOUS:")
    else: raise AssertionError("ambiguity accepted")
