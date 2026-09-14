import { beforeAll, expect, test } from "bun:test"

function seedRequiredEnv() {
  process.env.DATABASE_URL = process.env.DATABASE_URL ?? "mysql://root:password@127.0.0.1:3306/openwork_test"
  process.env.DEN_DB_ENCRYPTION_KEY = process.env.DEN_DB_ENCRYPTION_KEY ?? "x".repeat(32)
  process.env.BETTER_AUTH_SECRET = process.env.BETTER_AUTH_SECRET ?? "y".repeat(32)
  process.env.BETTER_AUTH_URL = process.env.BETTER_AUTH_URL ?? "http://127.0.0.1:8790"
}

let bootstrap: typeof import("../src/initial-admin-bootstrap.js")
beforeAll(async () => {
  seedRequiredEnv()
  bootstrap = await import("../src/initial-admin-bootstrap.js")
})

test("initial admin bootstrap normalizes emails like auth login", () => {
  expect(bootstrap.normalizeInitialAdminBootstrapEmail(" Initial.Admin@Example.COM ")).toBe("initial.admin@example.com")
})

test("initial admin bootstrap compares one-time setup code strings", () => {
  const code = "operator supplied one-time code"
  expect(bootstrap.compareInitialAdminBootstrapCode(code, code)).toBe(true)
  expect(bootstrap.compareInitialAdminBootstrapCode(`${code}!`, code)).toBe(false)
  expect(bootstrap.compareInitialAdminBootstrapCode(code.toUpperCase(), code)).toBe(false)
})

test("initial admin bootstrap grant format is single-purpose", () => {
  expect(bootstrap.isInitialAdminBootstrapGrantFormat(`${bootstrap.INITIAL_ADMIN_BOOTSTRAP_GRANT_PREFIX}abc123`)).toBe(true)
  expect(bootstrap.isInitialAdminBootstrapGrantFormat(bootstrap.INITIAL_ADMIN_BOOTSTRAP_GRANT_PREFIX)).toBe(false)
  expect(bootstrap.isInitialAdminBootstrapGrantFormat("regular-session-token")).toBe(false)
})
