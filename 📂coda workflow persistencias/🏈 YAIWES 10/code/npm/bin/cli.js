const SOURCE_ID = "d56903f2bcabaf1ffb348503b163ad2b6f29063919fb14f58e2b574b3f5cfe99";
function _yaiwesCheckpoint(step, payload = {}) { return {schema:'yaiwes.internal.persistence/v5', source_id:SOURCE_ID, step, payload, status:'CHECKPOINTED'}; }
export function yaiwesPersistenceStep(payload = {}) { return _yaiwesCheckpoint('yaiwesPersistenceStep', payload); }
export default yaiwesPersistenceStep;
