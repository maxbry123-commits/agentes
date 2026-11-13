import { beforeEach, expect, test } from "bun:test"
import {
  clearExternalToolsSearchCache,
  EXTERNAL_TOOLS_SEARCH_CACHE_MAX_ENTRIES,
  getExternalToolsSearchCache,
  setExternalToolsSearchCache,
  type ExternalToolsSearchCacheKey,
  type ExternalToolsSearchProbeResult,
} from "../src/mcp/external-tools-search-cache.js"

const updatedAt = new Date("2026-08-16T12:00:00.000Z")
const success: ExternalToolsSearchProbeResult = { outcome: "success", tools: [] }
const failure: ExternalToolsSearchProbeResult = { outcome: "failure", error: new Error("provider unavailable") }

function key(overrides: Partial<ExternalToolsSearchCacheKey> = {}): ExternalToolsSearchCacheKey {
  return {
    organizationId: "organization-one",
    connectionId: "connection-one",
    updatedAt,
    credentialMode: "shared",
    ...overrides,
  }
}

beforeEach(clearExternalToolsSearchCache)

test("keys per-member connections by organization membership", () => {
  const first = key({ credentialMode: "per_member", orgMembershipId: "member-one" })
  const second = key({ credentialMode: "per_member", orgMembershipId: "member-two" })
  setExternalToolsSearchCache(first, success)
  setExternalToolsSearchCache(second, failure)
  expect(getExternalToolsSearchCache(first)).toBe(success)
  expect(getExternalToolsSearchCache(second)).toBe(failure)
})

test("separates identical connection ids by organization", () => {
  const first = key({ organizationId: "organization-one" })
  const second = key({ organizationId: "organization-two" })
  setExternalToolsSearchCache(first, success)
  expect(getExternalToolsSearchCache(second)).toBeUndefined()
})

test("misses after the connection updatedAt changes", () => {
  setExternalToolsSearchCache(key(), success)
  expect(getExternalToolsSearchCache(key({ updatedAt: new Date(updatedAt.getTime() + 1) }))).toBeUndefined()
})

test("expires successful probes after ten minutes", () => {
  let now = 1_000
  const clock = () => now
  setExternalToolsSearchCache(key(), success, clock)
  now += 10 * 60_000 - 1
  expect(getExternalToolsSearchCache(key(), clock)).toBe(success)
  now += 1
  expect(getExternalToolsSearchCache(key(), clock)).toBeUndefined()
})

test("expires failures after one minute while successes persist", () => {
  let now = 1_000
  const clock = () => now
  const failureKey = key({ connectionId: "failure" })
  const successKey = key({ connectionId: "success" })
  setExternalToolsSearchCache(failureKey, failure, clock)
  setExternalToolsSearchCache(successKey, success, clock)
  now += 60_000
  expect(getExternalToolsSearchCache(failureKey, clock)).toBeUndefined()
  expect(getExternalToolsSearchCache(successKey, clock)).toBe(success)
})

test("evicts the oldest entry at the size cap", () => {
  const oldest = key({ connectionId: "connection-0" })
  for (let index = 0; index <= EXTERNAL_TOOLS_SEARCH_CACHE_MAX_ENTRIES; index += 1) {
    setExternalToolsSearchCache(key({ connectionId: `connection-${index}` }), success)
  }
  expect(getExternalToolsSearchCache(oldest)).toBeUndefined()
  expect(getExternalToolsSearchCache(key({ connectionId: `connection-${EXTERNAL_TOOLS_SEARCH_CACHE_MAX_ENTRIES}` }))).toBe(success)
})
