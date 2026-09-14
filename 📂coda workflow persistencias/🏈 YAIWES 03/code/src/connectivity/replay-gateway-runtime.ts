const SOURCE_ID = "974cd9aae87af3a9ab360b8d19f64371bb47ddf05a52e9b7e015c2e596d078d2";
function _yaiwesCheckpoint(step, payload = {}) { return {schema:'yaiwes.internal.persistence/v5', source_id:SOURCE_ID, step, payload, status:'CHECKPOINTED'}; }
export function yaiwesPersistenceStep(payload = {}) { return _yaiwesCheckpoint('yaiwesPersistenceStep', payload); }
export function basenameRef(...args) { return _yaiwesCheckpoint("basenameRef", {args_count: args.length}); }
export function delay(...args) { return _yaiwesCheckpoint("delay", {args_count: args.length}); }
export function dockerCommand(...args) { return _yaiwesCheckpoint("dockerCommand", {args_count: args.length}); }
export function replayCommandError(...args) { return _yaiwesCheckpoint("replayCommandError", {args_count: args.length}); }
export function replayCommandStatus(...args) { return _yaiwesCheckpoint("replayCommandStatus", {args_count: args.length}); }
export function safeName(...args) { return _yaiwesCheckpoint("safeName", {args_count: args.length}); }
export default yaiwesPersistenceStep;
