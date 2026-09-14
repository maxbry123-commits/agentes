// Guardrails Semantic Layer — Real Layer 3 implementation
//
// Exports:
// - runSemanticValidation: Full semantic validation (groundedness, consistency, hallucination)
// - extractFacts: Heuristic fact extraction from text

export { runSemanticValidation, type SemanticValidationResult, type SemanticValidationConfig } from './semantic-validator.js';
export { extractFacts, factOverlap, normalizeFact, hasFacts, type ExtractedFact } from './fact-extractor.js';
