const SOURCE_ID = "b04daf7b55baa68a60abfbaaed41de3ee31c94041240809a5c724a0995c6f888";
function _yaiwesCheckpoint(step, payload = {}) { return {schema:'yaiwes.internal.persistence/v5', source_id:SOURCE_ID, step, payload, status:'CHECKPOINTED'}; }
export function yaiwesPersistenceStep(payload = {}) { return _yaiwesCheckpoint('yaiwesPersistenceStep', payload); }
export function FlowFilesAttachResourcesDialog(...args) { return _yaiwesCheckpoint("FlowFilesAttachResourcesDialog", {args_count: args.length}); }
export function FlowFilesAttachResourcesDialogBody(...args) { return _yaiwesCheckpoint("FlowFilesAttachResourcesDialogBody", {args_count: args.length}); }
export default yaiwesPersistenceStep;
