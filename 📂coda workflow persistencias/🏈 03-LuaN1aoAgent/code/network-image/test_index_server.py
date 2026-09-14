"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = 'bcb12a8810236693895b8cba7d87c7e9e1c6d4f7f917e2c214a3f7748f20fcf3'
DECISION = 'REVIEW_FAIL_CLOSED'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

def framed_flow(*args, **kwargs):
    return _yaiwes_checkpoint('framed_flow', kwargs)

def indexed_record(*args, **kwargs):
    return _yaiwes_checkpoint('indexed_record', kwargs)

class FramedFlowReader:
    def __init__(self, *args, **kwargs):
        self._yaiwes_checkpoint = _yaiwes_checkpoint('FramedFlowReader.__init__', kwargs)
    def stream(self, *args, **kwargs):
        return _yaiwes_checkpoint('FramedFlowReader.stream', kwargs)

class FlowIndexTest:
    def setUp(self, *args, **kwargs):
        return _yaiwes_checkpoint('FlowIndexTest.setUp', kwargs)
    def tearDown(self, *args, **kwargs):
        return _yaiwes_checkpoint('FlowIndexTest.tearDown', kwargs)
    def test_reads_only_bytes_after_each_committed_record(self, *args, **kwargs):
        return _yaiwes_checkpoint('FlowIndexTest.test_reads_only_bytes_after_each_committed_record', kwargs)
    def test_partial_tail_is_retried_from_the_last_complete_record(self, *args, **kwargs):
        return _yaiwes_checkpoint('FlowIndexTest.test_partial_tail_is_retried_from_the_last_complete_record', kwargs)
    def test_rotation_preserves_inode_records_and_eviction_removes_them(self, *args, **kwargs):
        return _yaiwes_checkpoint('FlowIndexTest.test_rotation_preserves_inode_records_and_eviction_removes_them', kwargs)
    def test_restart_rebuilds_the_same_snapshot(self, *args, **kwargs):
        return _yaiwes_checkpoint('FlowIndexTest.test_restart_rebuilds_the_same_snapshot', kwargs)
    def test_concurrent_records_share_one_incremental_scan(self, *args, **kwargs):
        return _yaiwes_checkpoint('FlowIndexTest.test_concurrent_records_share_one_incremental_scan', kwargs)
    def test_reads_native_jsonl_and_retries_a_partial_tail(self, *args, **kwargs):
        return _yaiwes_checkpoint('FlowIndexTest.test_reads_native_jsonl_and_retries_a_partial_tail', kwargs)

class RouteProxyTest:
    def test_missing_readiness_file_is_not_ready(self, *args, **kwargs):
        return _yaiwes_checkpoint('RouteProxyTest.test_missing_readiness_file_is_not_ready', kwargs)
    def test_conntrack_accounting_configuration_fails_closed(self, *args, **kwargs):
        return _yaiwes_checkpoint('RouteProxyTest.test_conntrack_accounting_configuration_fails_closed', kwargs)
    def test_protocol_gateway_owns_transparent_capture_and_routing(self, *args, **kwargs):
        return _yaiwes_checkpoint('RouteProxyTest.test_protocol_gateway_owns_transparent_capture_and_routing', kwargs)
    def test_domain_scope_configures_nft_guard_and_gateway_admission(self, *args, **kwargs):
        return _yaiwes_checkpoint('RouteProxyTest.test_domain_scope_configures_nft_guard_and_gateway_admission', kwargs)
    def test_gateway_routes_all_task_tcp_to_one_protocol_gateway(self, *args, **kwargs):
        return _yaiwes_checkpoint('RouteProxyTest.test_gateway_routes_all_task_tcp_to_one_protocol_gateway', kwargs)
    def test_protocol_gateway_runs_unprivileged_as_capture_storage_owner(self, *args, **kwargs):
        return _yaiwes_checkpoint('RouteProxyTest.test_protocol_gateway_runs_unprivileged_as_capture_storage_owner', kwargs)
    def test_uid_routing_exists_only_for_the_trusted_replay_helper(self, *args, **kwargs):
        return _yaiwes_checkpoint('RouteProxyTest.test_uid_routing_exists_only_for_the_trusted_replay_helper', kwargs)
    def test_gateway_readiness_requires_every_data_plane_component(self, *args, **kwargs):
        return _yaiwes_checkpoint('RouteProxyTest.test_gateway_readiness_requires_every_data_plane_component', kwargs)
    def test_tun_ready_file_is_created_by_gateway_uid_without_chown_capability(self, *args, **kwargs):
        return _yaiwes_checkpoint('RouteProxyTest.test_tun_ready_file_is_created_by_gateway_uid_without_chown_capability', kwargs)
    def test_body_api_reports_response_truncated_by_requested_byte_limit(self, *args, **kwargs):
        return _yaiwes_checkpoint('RouteProxyTest.test_body_api_reports_response_truncated_by_requested_byte_limit', kwargs)
    def test_tcp_flow_record_exposes_directional_bounded_summaries(self, *args, **kwargs):
        return _yaiwes_checkpoint('RouteProxyTest.test_tcp_flow_record_exposes_directional_bounded_summaries', kwargs)
    def test_gateway_route_update_atomically_writes_normalized_longest_prefix_snapshot(self, *args, **kwargs):
        return _yaiwes_checkpoint('RouteProxyTest.test_gateway_route_update_atomically_writes_normalized_longest_prefix_snapshot', kwargs)
    def test_gateway_route_validation_keeps_previous_snapshot_on_failure(self, *args, **kwargs):
        return _yaiwes_checkpoint('RouteProxyTest.test_gateway_route_validation_keeps_previous_snapshot_on_failure', kwargs)
    def test_gateway_epoch_end_waits_for_zero_active_work_and_returns_fsynced_ack(self, *args, **kwargs):
        return _yaiwes_checkpoint('RouteProxyTest.test_gateway_epoch_end_waits_for_zero_active_work_and_returns_fsynced_ack', kwargs)
    def test_gateway_epoch_end_reconciles_stale_telemetry_after_kernel_drain(self, *args, **kwargs):
        return _yaiwes_checkpoint('RouteProxyTest.test_gateway_epoch_end_reconciles_stale_telemetry_after_kernel_drain', kwargs)
    def test_gateway_epoch_end_tolerates_conntrack_destroy_storm(self, *args, **kwargs):
        return _yaiwes_checkpoint('RouteProxyTest.test_gateway_epoch_end_tolerates_conntrack_destroy_storm', kwargs)
    def test_gateway_epoch_end_failure_keeps_epoch_active_for_retry(self, *args, **kwargs):
        return _yaiwes_checkpoint('RouteProxyTest.test_gateway_epoch_end_failure_keeps_epoch_active_for_retry', kwargs)
    def test_gateway_control_reads_fragmented_newline_delimited_request(self, *args, **kwargs):
        return _yaiwes_checkpoint('RouteProxyTest.test_gateway_control_reads_fragmented_newline_delimited_request', kwargs)
    def test_gateway_control_rejects_request_larger_than_one_mebibyte(self, *args, **kwargs):
        return _yaiwes_checkpoint('RouteProxyTest.test_gateway_control_rejects_request_larger_than_one_mebibyte', kwargs)
