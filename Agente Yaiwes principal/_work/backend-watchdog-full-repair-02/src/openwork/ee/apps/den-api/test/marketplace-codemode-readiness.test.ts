import { beforeAll, expect, test } from "bun:test"

function seedRequiredEnv() {
  process.env.DATABASE_URL = process.env.DATABASE_URL ?? "mysql://root:password@127.0.0.1:3306/openwork_test_codemode_scripts"
  process.env.DEN_DB_ENCRYPTION_KEY = process.env.DEN_DB_ENCRYPTION_KEY ?? "x".repeat(32)
  process.env.BETTER_AUTH_SECRET = process.env.BETTER_AUTH_SECRET ?? "y".repeat(32)
  process.env.BETTER_AUTH_URL = process.env.BETTER_AUTH_URL ?? "http://127.0.0.1:8790"
}

let marketplaceConfigObjectExecutionMode: typeof import("../src/mcp/marketplace-capabilities.js")["marketplaceConfigObjectExecutionMode"]
let marketplaceConfigObjectReadyWhenSynced: typeof import("../src/mcp/marketplace-capabilities.js")["marketplaceConfigObjectReadyWhenSynced"]

beforeAll(async () => {
  seedRequiredEnv()
  const marketplaceCapabilities = await import("../src/mcp/marketplace-capabilities.js")
  marketplaceConfigObjectExecutionMode = marketplaceCapabilities.marketplaceConfigObjectExecutionMode
  marketplaceConfigObjectReadyWhenSynced = marketplaceCapabilities.marketplaceConfigObjectReadyWhenSynced
})

test("saved scripts execute in Code Mode and are cloud-ready once synced", () => {
  expect(marketplaceConfigObjectExecutionMode("script")).toBe("codemode")
  expect(marketplaceConfigObjectReadyWhenSynced("script")).toBe(true)
})

test("app config objects stay out of instructional marketplace projection", () => {
  expect(marketplaceConfigObjectExecutionMode("app")).toBe("desktop_only")
  expect(marketplaceConfigObjectReadyWhenSynced("app")).toBe(false)
})
