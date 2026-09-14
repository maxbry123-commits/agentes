"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = 'ab35c0df37885bd8dcc51590768485118efe364fb8fa9e273106096add1c4163'
DECISION = 'REVIEW_FAIL_CLOSED'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

def _context(*args, **kwargs):
    return _yaiwes_checkpoint('_context', kwargs)

def _make_pyc(*args, **kwargs):
    return _yaiwes_checkpoint('_make_pyc', kwargs)

def test_repo_tree_flags_pyc_and_hidden_dirs(*args, **kwargs):
    return _yaiwes_checkpoint('test_repo_tree_flags_pyc_and_hidden_dirs', kwargs)

def test_repo_tree_normal_dirs_unflagged(*args, **kwargs):
    return _yaiwes_checkpoint('test_repo_tree_normal_dirs_unflagged', kwargs)

def test_venv_only_project_is_not_empty(*args, **kwargs):
    return _yaiwes_checkpoint('test_venv_only_project_is_not_empty', kwargs)

def test_pyc_only_project_is_not_empty(*args, **kwargs):
    return _yaiwes_checkpoint('test_pyc_only_project_is_not_empty', kwargs)

def test_git_only_project_is_empty(*args, **kwargs):
    return _yaiwes_checkpoint('test_git_only_project_is_empty', kwargs)

def test_pre_scan_warns_pyc_presence(*args, **kwargs):
    return _yaiwes_checkpoint('test_pre_scan_warns_pyc_presence', kwargs)

def test_pre_scan_flags_pyc_loader_pattern(*args, **kwargs):
    return _yaiwes_checkpoint('test_pre_scan_flags_pyc_loader_pattern', kwargs)

def test_pre_scan_scans_files_inside_flagged_dirs(*args, **kwargs):
    return _yaiwes_checkpoint('test_pre_scan_scans_files_inside_flagged_dirs', kwargs)

def test_pre_scan_flags_flagged_dir_reference(*args, **kwargs):
    return _yaiwes_checkpoint('test_pre_scan_flags_flagged_dir_reference', kwargs)

def test_pre_scan_clean_project_has_no_bytecode_warning(*args, **kwargs):
    return _yaiwes_checkpoint('test_pre_scan_clean_project_has_no_bytecode_warning', kwargs)

def test_dir_tree_flags_hidden_dirs_and_pyc(*args, **kwargs):
    return _yaiwes_checkpoint('test_dir_tree_flags_hidden_dirs_and_pyc', kwargs)
