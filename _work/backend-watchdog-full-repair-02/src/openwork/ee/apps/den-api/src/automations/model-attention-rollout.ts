import { AUTOMATION_FREE_MODEL } from "@openwork/types/automations"

type ModelSelection = { providerId: string; modelId: string }
type ModelAccessFailure = {
  code: "owner_membership_lost" | "model_access_lost" | "provider_unavailable"
}

/**
 * The legacy free model was accepted by already-published desktop clients.
 * Den may turn its policy revocation into `needs_attention` only after the
 * caller or runner advertises support for that state. Other authority losses
 * remain fail-closed for every client generation.
 */
export function shouldApplyAutomationModelAccessFailure(input: {
  model: ModelSelection
  failure: ModelAccessFailure
  modelAttentionCapable: boolean
}): boolean {
  if (input.modelAttentionCapable) return true
  return input.failure.code !== "model_access_lost"
    || input.model.providerId !== AUTOMATION_FREE_MODEL.providerId
    || input.model.modelId !== AUTOMATION_FREE_MODEL.modelId
}
