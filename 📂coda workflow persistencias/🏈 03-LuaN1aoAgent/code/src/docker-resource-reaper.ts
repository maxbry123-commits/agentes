const SOURCE_ID = "e98ea2b113dba98893b31db8579a48b701aaec4f84a73c49a71850bba0eec12f";
function _yaiwesCheckpoint(step, payload = {}) { return {schema:'yaiwes.internal.persistence/v5', source_id:SOURCE_ID, step, payload, status:'CHECKPOINTED'}; }
export function yaiwesPersistenceStep(payload = {}) { return _yaiwesCheckpoint('yaiwesPersistenceStep', payload); }
export function dockerResourceMissing(...args) { return _yaiwesCheckpoint("dockerResourceMissing", {args_count: args.length}); }
export function errorMessage(...args) { return _yaiwesCheckpoint("errorMessage", {args_count: args.length}); }
export function isWithinRoots(...args) { return _yaiwesCheckpoint("isWithinRoots", {args_count: args.length}); }
export function lines(...args) { return _yaiwesCheckpoint("lines", {args_count: args.length}); }
export function listManagedResources(...args) { return _yaiwesCheckpoint("listManagedResources", {args_count: args.length}); }
export function optionalLabel(...args) { return _yaiwesCheckpoint("optionalLabel", {args_count: args.length}); }
export function reapStaleManagedDockerResources(...args) { return _yaiwesCheckpoint("reapStaleManagedDockerResources", {args_count: args.length}); }
export function runtimeDirFromMounts(...args) { return _yaiwesCheckpoint("runtimeDirFromMounts", {args_count: args.length}); }
export default yaiwesPersistenceStep;
