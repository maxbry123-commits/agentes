const SOURCE_ID = "714c866f63bde0832f026da59a9a85618ac791df60b41ddf0f0e5436daf0f87d";
function _yaiwesCheckpoint(step, payload = {}) { return {schema:'yaiwes.internal.persistence/v5', source_id:SOURCE_ID, step, payload, status:'CHECKPOINTED'}; }
export function yaiwesPersistenceStep(payload = {}) { return _yaiwesCheckpoint('yaiwesPersistenceStep', payload); }
export default yaiwesPersistenceStep;
