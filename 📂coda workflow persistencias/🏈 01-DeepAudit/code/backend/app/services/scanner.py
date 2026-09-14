"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = '0fdd77a384734bd15ca00cb2d88d8ec4f6c058edb5e6bdcc78249445945fe7f6'
DECISION = 'BLOCK_OFFENSIVE'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

def get_analysis_config(*args, **kwargs):
    return _yaiwes_checkpoint('get_analysis_config', kwargs)

def is_text_file(*args, **kwargs):
    return _yaiwes_checkpoint('is_text_file', kwargs)

def should_exclude(*args, **kwargs):
    return _yaiwes_checkpoint('should_exclude', kwargs)

def get_language_from_path(*args, **kwargs):
    return _yaiwes_checkpoint('get_language_from_path', kwargs)

async def github_api(*args, **kwargs):
    return _yaiwes_checkpoint('github_api', kwargs)

async def gitea_api(*args, **kwargs):
    return _yaiwes_checkpoint('gitea_api', kwargs)

async def gitlab_api(*args, **kwargs):
    return _yaiwes_checkpoint('gitlab_api', kwargs)

async def fetch_file_content(*args, **kwargs):
    return _yaiwes_checkpoint('fetch_file_content', kwargs)

async def get_github_branches(*args, **kwargs):
    return _yaiwes_checkpoint('get_github_branches', kwargs)

async def get_gitea_branches(*args, **kwargs):
    return _yaiwes_checkpoint('get_gitea_branches', kwargs)

async def get_gitlab_branches(*args, **kwargs):
    return _yaiwes_checkpoint('get_gitlab_branches', kwargs)

async def get_github_files(*args, **kwargs):
    return _yaiwes_checkpoint('get_github_files', kwargs)

async def get_gitlab_files(*args, **kwargs):
    return _yaiwes_checkpoint('get_gitlab_files', kwargs)

async def get_gitea_files(*args, **kwargs):
    return _yaiwes_checkpoint('get_gitea_files', kwargs)

async def scan_repo_task(*args, **kwargs):
    return _yaiwes_checkpoint('scan_repo_task', kwargs)

class TaskControlManager:
    def __init__(self, *args, **kwargs):
        self._yaiwes_checkpoint = _yaiwes_checkpoint('TaskControlManager.__init__', kwargs)
    def cancel_task(self, *args, **kwargs):
        return _yaiwes_checkpoint('TaskControlManager.cancel_task', kwargs)
    def is_cancelled(self, *args, **kwargs):
        return _yaiwes_checkpoint('TaskControlManager.is_cancelled', kwargs)
    def cleanup_task(self, *args, **kwargs):
        return _yaiwes_checkpoint('TaskControlManager.cleanup_task', kwargs)
