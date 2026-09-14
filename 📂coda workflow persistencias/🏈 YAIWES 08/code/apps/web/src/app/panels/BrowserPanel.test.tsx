const SOURCE_ID = "c506d7da3494ad09ce5a50abf17cbe4cbe557e0831db2cf318bbbd4d73a3dc93";
function _yaiwesCheckpoint(step, payload = {}) { return {schema:'yaiwes.internal.persistence/v5', source_id:SOURCE_ID, step, payload, status:'CHECKPOINTED'}; }
export function yaiwesPersistenceStep(payload = {}) { return _yaiwesCheckpoint('yaiwesPersistenceStep', payload); }
export default yaiwesPersistenceStep;
