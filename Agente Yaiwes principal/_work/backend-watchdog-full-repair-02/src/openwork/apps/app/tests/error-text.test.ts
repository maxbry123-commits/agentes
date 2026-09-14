import { describe, expect, test } from "bun:test"

import { normalizeErrorText } from "../src/lib/error-text"

describe("normalizeErrorText", () => {
  test("summarizes and clamps a one-megabyte HTML error page", () => {
    const raw = `  <!DOCTYPE html><html><head><title>502 Bad Gateway</title></head><body>${"x".repeat(1_024 * 1_024)}</body></html>`
    const normalized = normalizeErrorText(raw)

    expect(normalized.originalLength).toBe(raw.length)
    expect(normalized.truncated).toBe(true)
    expect(normalized.display).toContain("Upstream returned an HTML error page (502 Bad Gateway)")
    expect(normalized.display).toContain("1.0 MB hidden")
    expect(normalized.display).toContain(`[Error text truncated; original size: ${raw.length.toLocaleString("en-US")} characters]`)
    expect(normalized.display.length).toBeLessThanOrEqual(4_096)
    expect(normalized.display.toLowerCase()).not.toContain("<!doctype")
  })

  test("uses the HTML title when no HTTP status phrase is present", () => {
    const normalized = normalizeErrorText("MCP error -32000: <html><head><title>Proxy temporarily unavailable</title></head><body>retry later</body></html>")

    expect(normalized.display).toContain("Upstream returned an HTML error page (“Proxy temporarily unavailable”)")
    expect(normalized.display).toContain("[Error text truncated; original size:")
  })

  test("preserves an embedded JSON diagnostic object intact while clamping", () => {
    const diagnostic = JSON.stringify({
      error: "connection_failed",
      diagnostic: { code: "MCP_HTTP_504", httpStatus: 504 },
    })
    const raw = `MCP error: ${diagnostic}\n${"provider detail ".repeat(1_000)}`
    const normalized = normalizeErrorText(raw, { cap: 512 })

    expect(normalized.display).toContain(diagnostic)
    expect(normalized.display).toContain("[Error text truncated; original size:")
    expect(normalized.display.length).toBeLessThanOrEqual(512)
  })

  test("leaves a small plain error unchanged", () => {
    expect(normalizeErrorText("The tool failed.")).toEqual({
      display: "The tool failed.",
      truncated: false,
      originalLength: 16,
    })
  })

  test("leaves JSON-only errors unchanged when they are under the cap", () => {
    const raw = JSON.stringify({ diagnostic: { category: "provider_policy", providerStatus: 403 } })
    expect(normalizeErrorText(raw)).toEqual({ display: raw, truncated: false, originalLength: raw.length })
  })
})
