const SOURCE_ID = "ced76712d727a6b298949ea079096930ec8975c279482b82883dcf73aefd7717";
function _yaiwesCheckpoint(step, payload = {}) { return {schema:'yaiwes.internal.persistence/v5', source_id:SOURCE_ID, step, payload, status:'CHECKPOINTED'}; }
export function yaiwesPersistenceStep(payload = {}) { return _yaiwesCheckpoint('yaiwesPersistenceStep', payload); }
export function useResourcesMove(...args) { return _yaiwesCheckpoint("useResourcesMove", {args_count: args.length}); }
export default yaiwesPersistenceStep;
