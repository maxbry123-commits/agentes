// CODA persistence transformation policy for LuaN1aoAgent.
// This file is the allow/deny boundary for the transformed workflow link.

export const CODA_PERSISTENCE_ONLY = true;

export const ALLOWED_CONTROL_TOOLS = new Set([
  "planner_submit",
  "task_result_submit",
  "control_submit",
  "graph_delta_submit"
]);

export const PRESERVED_CONTROL_PLANE = new Set([
  "graph_store",
  "runtime_store",
  "execution_log",
  "planner_commands",
  "projection",
  "projector_coordinator",
  "operation_identity",
  "runtime_owner_lease",
  "epoch_budget_clock"
]);

export const DISABLED_RUNTIME_GROUPS = new Set([
  "connectivity",
  "host_egress",
  "network_sandbox",
  "executor_sandbox",
  "traffic_proxy",
  "browser_actions",
  "external_target_tools"
]);
