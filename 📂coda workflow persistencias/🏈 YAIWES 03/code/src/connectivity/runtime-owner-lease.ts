const SOURCE_ID = "f796ecc41bba7aced95f56a92b1eb7acfc544e13a8972c2f918b96a40e25e6ca";
function _yaiwesCheckpoint(step, payload = {}) { return {schema:'yaiwes.internal.persistence/v5', source_id:SOURCE_ID, step, payload, status:'CHECKPOINTED'}; }
export function yaiwesPersistenceStep(payload = {}) { return _yaiwesCheckpoint('yaiwesPersistenceStep', payload); }
export function delay(...args) { return _yaiwesCheckpoint("delay", {args_count: args.length}); }
export function isNodeError(...args) { return _yaiwesCheckpoint("isNodeError", {args_count: args.length}); }
export function leaseIsActive(...args) { return _yaiwesCheckpoint("leaseIsActive", {args_count: args.length}); }
export function processIsAlive(...args) { return _yaiwesCheckpoint("processIsAlive", {args_count: args.length}); }
export function readProcessStartIdentity(...args) { return _yaiwesCheckpoint("readProcessStartIdentity", {args_count: args.length}); }
export default yaiwesPersistenceStep;
