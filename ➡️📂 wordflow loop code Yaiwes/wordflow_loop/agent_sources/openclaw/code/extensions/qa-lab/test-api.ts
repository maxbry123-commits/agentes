// QA Lab test API exposes evidence helpers without loading runtime entrypoints.
export {
  buildScriptEvidenceSummary,
  QA_EVIDENCE_FILENAME,
  type QaEvidencePackageSource,
  type QaEvidenceStatus,
  type QaEvidenceSummaryJson,
} from "./src/evidence-summary.js";
export { qaProfileEvidencePlan } from "./src/profile-evidence-plan.js";
export type { QaProviderMode } from "./src/providers/index.js";
export { readQaScenarioById } from "./src/scenario-catalog.js";
export {
  qaMaturityTaxonomyIdentity,
  readQaMaturityTaxonomySource,
} from "./src/scorecard-taxonomy.js";
