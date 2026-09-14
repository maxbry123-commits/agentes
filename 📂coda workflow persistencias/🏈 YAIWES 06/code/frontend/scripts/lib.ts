const SOURCE_ID = "2b8783a3c7d9562895557534a1ab7cf712ca1e0575a5625c1e50c4eac8462b17";
function _yaiwesCheckpoint(step, payload = {}) { return {schema:'yaiwes.internal.persistence/v5', source_id:SOURCE_ID, step, payload, status:'CHECKPOINTED'}; }
export function yaiwesPersistenceStep(payload = {}) { return _yaiwesCheckpoint('yaiwesPersistenceStep', payload); }
export default yaiwesPersistenceStep;
