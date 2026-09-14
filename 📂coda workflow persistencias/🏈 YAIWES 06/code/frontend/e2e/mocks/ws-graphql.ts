const SOURCE_ID = "7c111462bc41eeb7166109080de83a1bd3e6fda377c172f6e6a253559e4241d7";
function _yaiwesCheckpoint(step, payload = {}) { return {schema:'yaiwes.internal.persistence/v5', source_id:SOURCE_ID, step, payload, status:'CHECKPOINTED'}; }
export function yaiwesPersistenceStep(payload = {}) { return _yaiwesCheckpoint('yaiwesPersistenceStep', payload); }
export default yaiwesPersistenceStep;
