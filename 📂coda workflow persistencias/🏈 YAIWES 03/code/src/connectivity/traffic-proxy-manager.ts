const SOURCE_ID = "ba78ae33d2169d428c5c4402c82135233443bc70129caad62b0dafbf98e574b0";
function _yaiwesCheckpoint(step, payload = {}) { return {schema:'yaiwes.internal.persistence/v5', source_id:SOURCE_ID, step, payload, status:'CHECKPOINTED'}; }
export function yaiwesPersistenceStep(payload = {}) { return _yaiwesCheckpoint('yaiwesPersistenceStep', payload); }
export function pathExists(...args) { return _yaiwesCheckpoint("pathExists", {args_count: args.length}); }
export function readReadyLine(...args) { return _yaiwesCheckpoint("readReadyLine", {args_count: args.length}); }
export function waitForExit(...args) { return _yaiwesCheckpoint("waitForExit", {args_count: args.length}); }
export default yaiwesPersistenceStep;
