// Barrel export for the unified MemoryService. Consumers should import from
// here rather than reaching into submodules directly.

export { memoryService, type MemoryService } from './service.js';
export { hierarchicalRecall, storeWithAutoIndex } from './hierarchy.js';
export { autoIndex, classifyMemory, extractEntities, suggestTags, shouldLink } from './auto-index-pure.js';
export {
  computeHybridScores,
  deduplicateEntries,
  formatHierarchicalContext,
  reciprocalRankFusion,
  applyTemporalDecay,
  keywordOverlapScore,
  daysSince,
} from './hybrid-retrieval-pure.js';

export type {
  RecallParams, RecallResult,
  RememberParams,
  ForgetTarget,
  ImproveParams, ImproveResult,
  MemoryLayer, MemoryClass, MemoryEntry,
  HierarchicalRecallParams, HierarchicalRecallResult,
  LayerStats, AutoIndexResult,
} from './types.js';
