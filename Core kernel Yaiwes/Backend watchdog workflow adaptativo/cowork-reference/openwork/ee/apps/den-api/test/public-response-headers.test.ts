import { describe, expect, test } from "bun:test"
import { sanitizePublicResponseHeaders } from "../src/public-response-headers.js"

describe("public response headers", () => {
  test("strips internal and custom x-* headers from public responses", () => {
    const headers = new Headers({
      "access-control-expose-headers": "Content-Length, X-Request-Id, X-Origin-Host",
      "content-type": "application/json",
      "rndr-id": "render-request",
      "server": "internal-origin",
      "via": "internal-proxy",
      "x-cache-key": "cache:key",
      "x-content-type-options": "nosniff",
      "x-origin-host": "den-api.internal",
      "x-render-origin-server": "Render",
      "x-request-id": "req_internal",
    })

    sanitizePublicResponseHeaders(headers)

    expect(headers.get("access-control-expose-headers")).toBe("Content-Length")
    expect(headers.get("content-type")).toBe("application/json")
    expect(headers.get("x-content-type-options")).toBe("nosniff")
    for (const header of [
      "rndr-id",
      "server",
      "via",
      "x-cache-key",
      "x-origin-host",
      "x-render-origin-server",
      "x-request-id",
    ]) {
      expect(headers.get(header)).toBeNull()
    }
  })
})
