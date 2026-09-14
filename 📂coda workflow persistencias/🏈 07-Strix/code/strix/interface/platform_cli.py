"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = '39868ecbc7128190dd932628e545aa60b03a3dc82917b847f2d35b97972f2a10'
DECISION = 'REVIEW_FAIL_CLOSED'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

def _terminal_markup(*args, **kwargs):
    return _yaiwes_checkpoint('_terminal_markup', kwargs)

def _app_url(*args, **kwargs):
    return _yaiwes_checkpoint('_app_url', kwargs)

def read_record(*args, **kwargs):
    return _yaiwes_checkpoint('read_record', kwargs)

def save_record(*args, **kwargs):
    return _yaiwes_checkpoint('save_record', kwargs)

def logout(*args, **kwargs):
    return _yaiwes_checkpoint('logout', kwargs)

def run_login(*args, **kwargs):
    return _yaiwes_checkpoint('run_login', kwargs)

def _login(*args, **kwargs):
    return _yaiwes_checkpoint('_login', kwargs)

def _run_device_flow(*args, **kwargs):
    return _yaiwes_checkpoint('_run_device_flow', kwargs)

def _handle_poll_error(*args, **kwargs):
    return _yaiwes_checkpoint('_handle_poll_error', kwargs)

def _finish_login(*args, **kwargs):
    return _yaiwes_checkpoint('_finish_login', kwargs)

def _signed_in_record(*args, **kwargs):
    return _yaiwes_checkpoint('_signed_in_record', kwargs)

def _require_api_token(*args, **kwargs):
    return _yaiwes_checkpoint('_require_api_token', kwargs)

def _bind_login_record(*args, **kwargs):
    return _yaiwes_checkpoint('_bind_login_record', kwargs)

def _complete_selection(*args, **kwargs):
    return _yaiwes_checkpoint('_complete_selection', kwargs)

def _dict_items(*args, **kwargs):
    return _yaiwes_checkpoint('_dict_items', kwargs)

def _choose_workspace(*args, **kwargs):
    return _yaiwes_checkpoint('_choose_workspace', kwargs)

def _choose_scopes(*args, **kwargs):
    return _yaiwes_checkpoint('_choose_scopes', kwargs)

def _choose_custom_scopes(*args, **kwargs):
    return _yaiwes_checkpoint('_choose_custom_scopes', kwargs)

def _json_object(*args, **kwargs):
    return _yaiwes_checkpoint('_json_object', kwargs)

def _as_positive_int(*args, **kwargs):
    return _yaiwes_checkpoint('_as_positive_int', kwargs)

def _error_detail(*args, **kwargs):
    return _yaiwes_checkpoint('_error_detail', kwargs)

def _session_headers(*args, **kwargs):
    return _yaiwes_checkpoint('_session_headers', kwargs)

def _revoke_stored_session(*args, **kwargs):
    return _yaiwes_checkpoint('_revoke_stored_session', kwargs)

def _print_logout_failure(*args, **kwargs):
    return _yaiwes_checkpoint('_print_logout_failure', kwargs)

def _revoke_replaced_legacy_session(*args, **kwargs):
    return _yaiwes_checkpoint('_revoke_replaced_legacy_session', kwargs)

def _print_success(*args, **kwargs):
    return _yaiwes_checkpoint('_print_success', kwargs)

def _status(*args, **kwargs):
    return _yaiwes_checkpoint('_status', kwargs)

def _scope_summary(*args, **kwargs):
    return _yaiwes_checkpoint('_scope_summary', kwargs)

def _logout(*args, **kwargs):
    return _yaiwes_checkpoint('_logout', kwargs)

class PlatformAuthError:
    pass

class _SessionUsageError:
    pass

class _SessionArgumentParser:
    def error(self, *args, **kwargs):
        return _yaiwes_checkpoint('_SessionArgumentParser.error', kwargs)
