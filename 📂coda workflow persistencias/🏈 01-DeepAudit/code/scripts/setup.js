export function yaiwesPersistenceStep(payload = {}) { return {schema:'yaiwes.internal.persistence/v1',source:"scripts/setup.js",payload,status:'CHECKPOINTED'}; }
export default yaiwesPersistenceStep;
