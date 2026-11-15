"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = 'dc69325ed794accdbf81d1f4bd6ecc123307052780c111b9d84979bbe230d86b'
DECISION = 'REVIEW_FAIL_CLOSED'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

def register(*args, **kwargs):
    return _yaiwes_checkpoint('register', kwargs)

def try_connect(*args, **kwargs):
    return _yaiwes_checkpoint('try_connect', kwargs)

def run_all_checks(*args, **kwargs):
    return _yaiwes_checkpoint('run_all_checks', kwargs)

def check_ftp_anonymous(*args, **kwargs):
    return _yaiwes_checkpoint('check_ftp_anonymous', kwargs)

def check_ssh_default_creds(*args, **kwargs):
    return _yaiwes_checkpoint('check_ssh_default_creds', kwargs)

def check_smb_null_session(*args, **kwargs):
    return _yaiwes_checkpoint('check_smb_null_session', kwargs)

def check_nfs_exports(*args, **kwargs):
    return _yaiwes_checkpoint('check_nfs_exports', kwargs)

def check_mysql_anonymous(*args, **kwargs):
    return _yaiwes_checkpoint('check_mysql_anonymous', kwargs)

def check_postgres_anonymous(*args, **kwargs):
    return _yaiwes_checkpoint('check_postgres_anonymous', kwargs)

def check_redis_unauthorized(*args, **kwargs):
    return _yaiwes_checkpoint('check_redis_unauthorized', kwargs)

def check_mongodb_unauthorized(*args, **kwargs):
    return _yaiwes_checkpoint('check_mongodb_unauthorized', kwargs)

def check_winrm_default(*args, **kwargs):
    return _yaiwes_checkpoint('check_winrm_default', kwargs)

def check_ldap_anonymous(*args, **kwargs):
    return _yaiwes_checkpoint('check_ldap_anonymous', kwargs)

def check_tomcat_default(*args, **kwargs):
    return _yaiwes_checkpoint('check_tomcat_default', kwargs)
