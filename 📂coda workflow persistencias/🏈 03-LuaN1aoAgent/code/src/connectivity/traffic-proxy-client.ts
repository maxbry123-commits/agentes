const SOURCE_ID = "68423bd7dd35f846252a26ce7dfd5ab2d86ec4b84b5963a8ea31ef839d42fe59";
function _yaiwesCheckpoint(step, payload = {}) { return {schema:'yaiwes.internal.persistence/v5', source_id:SOURCE_ID, step, payload, status:'CHECKPOINTED'}; }
export function yaiwesPersistenceStep(payload = {}) { return _yaiwesCheckpoint('yaiwesPersistenceStep', payload); }
export function managedHttpContext(...args) { return _yaiwesCheckpoint("managedHttpContext", {args_count: args.length}); }
export function requiredScopeRef(...args) { return _yaiwesCheckpoint("requiredScopeRef", {args_count: args.length}); }
export default yaiwesPersistenceStep;
