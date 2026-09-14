const SOURCE_ID = "78e23ff94934cc1d403e04f7ca158f02e14ce8bb0e9dfe18823f429a1a08cee5";
function _yaiwesCheckpoint(step, payload = {}) { return {schema:'yaiwes.internal.persistence/v5', source_id:SOURCE_ID, step, payload, status:'CHECKPOINTED'}; }
export function yaiwesPersistenceStep(payload = {}) { return _yaiwesCheckpoint('yaiwesPersistenceStep', payload); }
export function ResourcesMoveDialog(...args) { return _yaiwesCheckpoint("ResourcesMoveDialog", {args_count: args.length}); }
export function ResourcesMoveDialogForm(...args) { return _yaiwesCheckpoint("ResourcesMoveDialogForm", {args_count: args.length}); }
export default yaiwesPersistenceStep;
