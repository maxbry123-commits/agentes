import { describe, expect, test } from "bun:test"
import { isOrganizationSsoReady } from "../src/sso-readiness.js"

describe("isOrganizationSsoReady", () => {
  test("requires an enabled connection with a verified provider", () => {
    expect(isOrganizationSsoReady({ connection: null, provider: null })).toBe(false)
    expect(isOrganizationSsoReady({ connection: { status: "disabled" }, provider: { domainVerified: true } })).toBe(false)
    expect(isOrganizationSsoReady({ connection: { status: "enabled" }, provider: null })).toBe(false)
    expect(isOrganizationSsoReady({ connection: { status: "enabled" }, provider: { domainVerified: false } })).toBe(false)
    expect(isOrganizationSsoReady({ connection: { status: "enabled" }, provider: { domainVerified: true } })).toBe(true)
  })
})
