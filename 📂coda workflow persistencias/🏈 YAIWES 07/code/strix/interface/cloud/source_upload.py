"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = '0b20c9ec224a522e08847a648ec15d8efd1d1248815191d3b89fe5cf0ea2dea8'
DECISION = 'REVIEW_FAIL_CLOSED'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

def prepare_source(*args, **kwargs):
    return _yaiwes_checkpoint('prepare_source', kwargs)

def _format_mib(*args, **kwargs):
    return _yaiwes_checkpoint('_format_mib', kwargs)

def _archive_too_large_error(*args, **kwargs):
    return _yaiwes_checkpoint('_archive_too_large_error', kwargs)

def select_source(*args, **kwargs):
    return _yaiwes_checkpoint('select_source', kwargs)

def remove_bundle(*args, **kwargs):
    return _yaiwes_checkpoint('remove_bundle', kwargs)

def _candidate_paths(*args, **kwargs):
    return _yaiwes_checkpoint('_candidate_paths', kwargs)

def _git_candidate_paths(*args, **kwargs):
    return _yaiwes_checkpoint('_git_candidate_paths', kwargs)

def _git_relative_path(*args, **kwargs):
    return _yaiwes_checkpoint('_git_relative_path', kwargs)

def _walk_candidate_paths(*args, **kwargs):
    return _yaiwes_checkpoint('_walk_candidate_paths', kwargs)

def _pruned_directory_reason(*args, **kwargs):
    return _yaiwes_checkpoint('_pruned_directory_reason', kwargs)

def _check_candidate_limit(*args, **kwargs):
    return _yaiwes_checkpoint('_check_candidate_limit', kwargs)

def _git_root(*args, **kwargs):
    return _yaiwes_checkpoint('_git_root', kwargs)

def _exclusion_reason(*args, **kwargs):
    return _yaiwes_checkpoint('_exclusion_reason', kwargs)

def _matches_user_pattern(*args, **kwargs):
    return _yaiwes_checkpoint('_matches_user_pattern', kwargs)

def _write_archive(*args, **kwargs):
    return _yaiwes_checkpoint('_write_archive', kwargs)

def _sha256(*args, **kwargs):
    return _yaiwes_checkpoint('_sha256', kwargs)

def _has_archive_magic(*args, **kwargs):
    return _yaiwes_checkpoint('_has_archive_magic', kwargs)

def _load_ignore_patterns(*args, **kwargs):
    return _yaiwes_checkpoint('_load_ignore_patterns', kwargs)

def _read_ignore_file(*args, **kwargs):
    return _yaiwes_checkpoint('_read_ignore_file', kwargs)

def _validate_patterns(*args, **kwargs):
    return _yaiwes_checkpoint('_validate_patterns', kwargs)

class SelectedFile:
    pass

class SourceManifest:
    def total_bytes(self, *args, **kwargs):
        return _yaiwes_checkpoint('SourceManifest.total_bytes', kwargs)
    def as_dict(self, *args, **kwargs):
        return _yaiwes_checkpoint('SourceManifest.as_dict', kwargs)

class SourceBundle:
    def summary(self, *args, **kwargs):
        return _yaiwes_checkpoint('SourceBundle.summary', kwargs)
