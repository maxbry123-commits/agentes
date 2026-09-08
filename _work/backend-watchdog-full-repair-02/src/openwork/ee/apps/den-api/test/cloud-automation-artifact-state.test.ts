import assert from "node:assert/strict"
import test from "node:test"
import { cloudArtifactStateUpdate } from "../src/automations/cloud-artifact-state.js"

test("a failed cloud refresh preserves the last good artifact by leaving it untouched", () => {
  const failed = cloudArtifactStateUpdate({
    runId: "atr_failed",
    result: { ok: false, message: "The required capability was revoked." },
    now: 42,
  })
  assert.equal(failed.state, "needs_attention")
  assert.equal("latestSuccessfulRunId" in failed, false)
  assert.equal("latestSuccessfulResult" in failed, false)
})

test("a successful cloud run advances the exact last-good snapshot", () => {
  const succeeded = cloudArtifactStateUpdate({
    runId: "atr_success",
    result: { ok: true, value: { briefing: "ready" } },
    now: 42,
  })
  assert.deepEqual(succeeded, {
    kind: "succeeded",
    state: "active",
    needsAttentionReason: null,
    latestSuccessfulRunId: "atr_success",
    latestSuccessfulResult: { briefing: "ready" },
  })
})
