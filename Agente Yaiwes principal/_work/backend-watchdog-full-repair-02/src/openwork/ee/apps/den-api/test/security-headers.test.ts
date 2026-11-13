import { beforeAll, describe, expect, test } from "bun:test"

function seedRequiredEnv() {
  process.env.DATABASE_URL = process.env.DATABASE_URL ?? "mysql://root:password@127.0.0.1:3306/openwork_test"
  process.env.DEN_DB_ENCRYPTION_KEY = process.env.DEN_DB_ENCRYPTION_KEY ?? "x".repeat(32)
  process.env.BETTER_AUTH_SECRET = process.env.BETTER_AUTH_SECRET ?? "y".repeat(32)
  process.env.BETTER_AUTH_URL = process.env.BETTER_AUTH_URL ?? "http://127.0.0.1:8790"
  process.env.DEN_API_PUBLIC_URL = process.env.DEN_API_PUBLIC_URL ?? "http://127.0.0.1:8790"
  process.env.CORS_ORIGINS = process.env.CORS_ORIGINS ?? "http://localhost:3005"
}

let app: typeof import("../src/app.js")["default"]

beforeAll(async () => {
  seedRequiredEnv()
  app = (await import("../src/app.js")).default
})

describe("security headers", () => {
  const hstsPolicy = "max-age=31536000; includeSubDomains"

  test("JSON responses disable MIME sniffing", async () => {
    const response = await app.request("/health")

    expect(response.status).toBe(200)
    expect(response.headers.get("x-content-type-options")).toBe("nosniff")
    expect(response.headers.get("strict-transport-security")).toBe(hstsPolicy)
  })

  test("middleware responses disable MIME sniffing", async () => {
    const response = await app.request("/v1/auth/desktop-handoff/exchange", {
      method: "OPTIONS",
      headers: {
        Origin: "https://8787-rotating.daytonaproxy01.net",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type,authorization",
      },
    })

    expect(response.status).toBe(204)
    expect(response.headers.get("x-content-type-options")).toBe("nosniff")
    expect(response.headers.get("strict-transport-security")).toBe(hstsPolicy)
  })

  test("not-found responses include transport security", async () => {
    const response = await app.request("/robots.txt")

    expect(response.status).toBe(404)
    expect(response.headers.get("x-content-type-options")).toBe("nosniff")
    expect(response.headers.get("strict-transport-security")).toBe(hstsPolicy)
  })
})
