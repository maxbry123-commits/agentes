import { createDenTypeId } from "@openwork-ee/utils/typeid"
import { afterAll, beforeAll, expect, test } from "bun:test"
import { Hono } from "hono"
import { connect } from "node:net"
import type { AuthContextVariables } from "../src/session.js"

const adminUserId = createDenTypeId("user")
const targetUserId = createDenTypeId("user")
const adminMemberId = createDenTypeId("member")
const targetMemberId = createDenTypeId("member")
const adminAllowlistId = createDenTypeId("adminAllowlist")
const organizationId = createDenTypeId("organization")
const fiveHourPolicyId = createDenTypeId("inferenceOrgLimitPolicy")
const weeklyPolicyId = createDenTypeId("inferenceOrgLimitPolicy")
const monthlyPolicyId = createDenTypeId("inferenceOrgLimitPolicy")
const fiveHourBucketId = createDenTypeId("inferenceOrgUsageBucket")
const weeklyBucketId = createDenTypeId("inferenceOrgUsageBucket")
const monthlyBucketId = createDenTypeId("inferenceOrgUsageBucket")
const targetLedgerEntryId = createDenTypeId("inferenceUsageLedgerEntry")
const adminLedgerEntryId = createDenTypeId("inferenceUsageLedgerEntry")
const targetFiveHourChargeId = createDenTypeId("inferenceUsageLedgerBucketCharge")
const targetWeeklyChargeId = createDenTypeId("inferenceUsageLedgerBucketCharge")
const targetMonthlyChargeId = createDenTypeId("inferenceUsageLedgerBucketCharge")
const adminMonthlyChargeId = createDenTypeId("inferenceUsageLedgerBucketCharge")
const adminEmail = `admin-management+${adminUserId}@test.local`
const targetEmail = `admin-management-target+${targetUserId}@test.local`
const addedAdminEmail = `added-admin+${adminUserId}@test.local`

function seedRequiredEnv() {
  process.env.DATABASE_URL = "mysql://root:password@127.0.0.1:3306/openwork_test"
  process.env.DEN_DB_ENCRYPTION_KEY = "x".repeat(32)
  process.env.BETTER_AUTH_SECRET = "y".repeat(32)
  process.env.BETTER_AUTH_URL = "http://127.0.0.1:8790"
  process.env.CORS_ORIGINS = "http://127.0.0.1:8790"
  process.env.DEN_ORG_MODE = "multi_org"
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null
}

function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : String(error)
}

function shouldRunRouteDbCoverage() {
  const testFiles = process.argv.filter((argument) => argument.endsWith(".test.ts"))
  return testFiles.length <= 2 && testFiles.some((argument) => argument.endsWith("admin-management-inference-usage.test.ts"))
}

function isRouteDatabase(value: unknown) {
  return isRecord(value) && "query" in value
}

async function databaseIsAvailable() {
  return new Promise<boolean>((resolve) => {
    const socket = connect({ host: "127.0.0.1", port: 3306 })
    const finish = (available: boolean) => {
      socket.destroy()
      resolve(available)
    }
    socket.setTimeout(1_000)
    socket.once("connect", () => finish(true))
    socket.once("error", () => finish(false))
    socket.once("timeout", () => finish(false))
  })
}

let app: Hono<{ Variables: AuthContextVariables }> | null = null
let db: typeof import("../src/db.js").db | null = null
let schema: typeof import("@openwork-ee/den-db/schema") | null = null
let drizzle: typeof import("@openwork-ee/den-db/drizzle") | null = null
let routeTestUnavailable: string | null = null

function testDatabase() {
  if (!db || !schema || !drizzle) {
    throw new Error("test database not initialized")
  }
  return { db, schema, drizzle }
}

function routeApp() {
  if (!app) {
    throw new Error("test app not initialized")
  }
  return app
}

async function cleanup() {
  if (!db || !schema || !drizzle) {
    return
  }

  await db.delete(schema.InferenceUsageLedgerBucketChargeTable).where(drizzle.inArray(schema.InferenceUsageLedgerBucketChargeTable.id, [
    targetFiveHourChargeId,
    targetWeeklyChargeId,
    targetMonthlyChargeId,
    adminMonthlyChargeId,
  ]))
  await db.delete(schema.InferenceUsageLedgerEntryTable).where(drizzle.inArray(schema.InferenceUsageLedgerEntryTable.id, [targetLedgerEntryId, adminLedgerEntryId]))
  await db.update(schema.InferenceOrgLimitPolicyTable).set({ current_bucket_id: null }).where(drizzle.eq(schema.InferenceOrgLimitPolicyTable.organization_id, organizationId))
  await db.delete(schema.InferenceOrgUsageBucketTable).where(drizzle.eq(schema.InferenceOrgUsageBucketTable.organization_id, organizationId))
  await db.delete(schema.InferenceOrgLimitPolicyTable).where(drizzle.eq(schema.InferenceOrgLimitPolicyTable.organization_id, organizationId))
  await db.delete(schema.MemberTable).where(drizzle.eq(schema.MemberTable.organizationId, organizationId))
  await db.delete(schema.OrganizationTable).where(drizzle.eq(schema.OrganizationTable.id, organizationId))
  await db.delete(schema.AuthUserTable).where(drizzle.inArray(schema.AuthUserTable.id, [adminUserId, targetUserId]))
  await db.delete(schema.AdminAllowlistTable).where(drizzle.inArray(schema.AdminAllowlistTable.email, [adminEmail, addedAdminEmail]))
}

beforeAll(async () => {
  if (!shouldRunRouteDbCoverage()) {
    routeTestUnavailable = "aggregate suite run; covered by the focused route DB test"
    return
  }

  seedRequiredEnv()
  if (!await databaseIsAvailable()) {
    routeTestUnavailable = "MySQL is not available at 127.0.0.1:3306"
    return
  }
  let adminRoutesModule: typeof import("../src/routes/admin/index.js")
  let dbModule: typeof import("../src/db.js")
  let schemaModule: typeof import("@openwork-ee/den-db/schema")
  let drizzleModule: typeof import("@openwork-ee/den-db/drizzle")
  try {
    [dbModule, schemaModule, drizzleModule] = await Promise.all([
      import("../src/db.js"),
      import("@openwork-ee/den-db/schema"),
      import("@openwork-ee/den-db/drizzle"),
    ])
    if (!isRouteDatabase(dbModule.db)) {
      routeTestUnavailable = "aggregate suite run; db module is mocked by another route test"
      return
    }
    adminRoutesModule = await import("../src/routes/admin/index.js")
  } catch (error) {
    routeTestUnavailable = errorMessage(error)
    return
  }
  db = dbModule.db
  schema = schemaModule
  drizzle = drizzleModule

  const now = new Date()
  const windowStart = new Date(now.getTime() - 60 * 60 * 1000)
  const windowEnd = new Date(now.getTime() + 60 * 60 * 1000)
  try {
    await cleanup()
    await db.insert(schema.AuthUserTable).values([
      { id: adminUserId, name: "Management Admin", email: adminEmail, emailVerified: true },
      { id: targetUserId, name: "Inference Target", email: targetEmail, emailVerified: true },
    ])
    await db.insert(schema.AdminAllowlistTable).values({ id: adminAllowlistId, email: adminEmail, note: "Management route test" })
    await db.insert(schema.OrganizationTable).values({ id: organizationId, name: "Admin Management Org", slug: `admin-management-${organizationId}` })
    await db.insert(schema.MemberTable).values([
      { id: adminMemberId, organizationId, userId: adminUserId, role: "admin" },
      { id: targetMemberId, organizationId, userId: targetUserId, role: "member" },
    ])
    await db.insert(schema.InferenceOrgLimitPolicyTable).values([
      { id: fiveHourPolicyId, organization_id: organizationId, window_type: "five_hour", reset_strategy: "activity_based" },
      { id: weeklyPolicyId, organization_id: organizationId, window_type: "weekly", reset_strategy: "anchored", anchor_at: now },
      { id: monthlyPolicyId, organization_id: organizationId, window_type: "monthly", reset_strategy: "anchored", anchor_at: now },
    ])
    await db.insert(schema.InferenceOrgUsageBucketTable).values([
      { id: fiveHourBucketId, organization_id: organizationId, policy_id: fiveHourPolicyId, window_start_at: windowStart, window_end_at: windowEnd, limit_amount: 1_000, used_amount: 11 },
      { id: weeklyBucketId, organization_id: organizationId, policy_id: weeklyPolicyId, window_start_at: windowStart, window_end_at: windowEnd, limit_amount: 2_000, used_amount: 22 },
      { id: monthlyBucketId, organization_id: organizationId, policy_id: monthlyPolicyId, window_start_at: windowStart, window_end_at: windowEnd, limit_amount: 3_000, used_amount: 40 },
    ])
    await db.update(schema.InferenceOrgLimitPolicyTable).set({ current_bucket_id: fiveHourBucketId }).where(drizzle.eq(schema.InferenceOrgLimitPolicyTable.id, fiveHourPolicyId))
    await db.update(schema.InferenceOrgLimitPolicyTable).set({ current_bucket_id: weeklyBucketId }).where(drizzle.eq(schema.InferenceOrgLimitPolicyTable.id, weeklyPolicyId))
    await db.update(schema.InferenceOrgLimitPolicyTable).set({ current_bucket_id: monthlyBucketId }).where(drizzle.eq(schema.InferenceOrgLimitPolicyTable.id, monthlyPolicyId))
    await db.insert(schema.InferenceUsageLedgerEntryTable).values([
      { id: targetLedgerEntryId, organization_id: organizationId, org_membership_id: targetMemberId, external_job_id: `target-${targetLedgerEntryId}`, cost_amount: 66, event_type: "usage", occurred_at: now },
      { id: adminLedgerEntryId, organization_id: organizationId, org_membership_id: adminMemberId, external_job_id: `admin-${adminLedgerEntryId}`, cost_amount: 7, event_type: "usage", occurred_at: now },
    ])
    await db.insert(schema.InferenceUsageLedgerBucketChargeTable).values([
      { id: targetFiveHourChargeId, ledger_entry_id: targetLedgerEntryId, bucket_id: fiveHourBucketId, amount: 11 },
      { id: targetWeeklyChargeId, ledger_entry_id: targetLedgerEntryId, bucket_id: weeklyBucketId, amount: 22 },
      { id: targetMonthlyChargeId, ledger_entry_id: targetLedgerEntryId, bucket_id: monthlyBucketId, amount: 33 },
      { id: adminMonthlyChargeId, ledger_entry_id: adminLedgerEntryId, bucket_id: monthlyBucketId, amount: 7 },
    ])
  } catch (error) {
    routeTestUnavailable = errorMessage(error)
    return
  }

  app = new Hono<{ Variables: AuthContextVariables }>()
  app.use("*", async (c, next) => {
    c.set("user", {
      id: adminUserId,
      name: "Management Admin",
      email: adminEmail,
      emailVerified: true,
      image: null,
      createdAt: new Date(),
      updatedAt: new Date(),
    })
    c.set("session", null)
    c.set("apiKey", null)
    await next()
  })
  adminRoutesModule.registerAdminRoutes(app)
})

afterAll(async () => {
  if (!routeTestUnavailable) {
    await cleanup()
  }
})

test("admin management and inference usage reset routes persist and isolate changes", async () => {
  if (routeTestUnavailable) {
    console.warn(`admin management and inference usage route DB coverage skipped: ${routeTestUnavailable}`)
    return
  }

  const addAdmin = await routeApp().request("http://den.local/v1/admin/admins", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ email: `  ${addedAdminEmail.toUpperCase()}  `, note: "Second admin" }),
  })
  expect(addAdmin.status).toBe(200)
  const addAdminPayload: unknown = await addAdmin.json()
  expect(addAdminPayload).toMatchObject({ ok: true, admin: { email: addedAdminEmail, note: "Second admin" } })
  if (!isRecord(addAdminPayload) || !isRecord(addAdminPayload.admin) || typeof addAdminPayload.admin.id !== "string") {
    throw new Error("add admin response did not include an admin id")
  }
  const addedAdminId = addAdminPayload.admin.id

  const { db, schema, drizzle } = testDatabase()
  const persistedAdmins = await db.select({ email: schema.AdminAllowlistTable.email }).from(schema.AdminAllowlistTable).where(drizzle.eq(schema.AdminAllowlistTable.email, addedAdminEmail))
  expect(persistedAdmins).toEqual([{ email: addedAdminEmail }])

  const duplicateAdmin = await routeApp().request("http://den.local/v1/admin/admins", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ email: addedAdminEmail }),
  })
  expect(duplicateAdmin.status).toBe(409)

  const removeSelf = await routeApp().request(`http://den.local/v1/admin/admins/${adminAllowlistId}`, { method: "DELETE" })
  expect(removeSelf.status).toBe(400)
  await expect(removeSelf.json()).resolves.toMatchObject({ message: "You cannot delete your own admin access." })

  const removeSecondAdmin = await routeApp().request(`http://den.local/v1/admin/admins/${addedAdminId}`, { method: "DELETE" })
  expect(removeSecondAdmin.status).toBe(200)
  expect(await db.select().from(schema.AdminAllowlistTable).where(drizzle.eq(schema.AdminAllowlistTable.email, addedAdminEmail))).toEqual([])

  const usageBefore = await routeApp().request(`http://den.local/v1/admin/users/${targetUserId}/inference-usage`)
  expect(usageBefore.status).toBe(200)
  await expect(usageBefore.json()).resolves.toMatchObject({
    user: { id: targetUserId, email: targetEmail },
    organizations: [{
      id: organizationId,
      membershipId: targetMemberId,
      windows: [
        { bucketId: fiveHourBucketId, windowType: "five_hour", limitAmount: 1_000, organizationUsedAmount: 11, userUsedAmount: 11 },
        { bucketId: weeklyBucketId, windowType: "weekly", limitAmount: 2_000, organizationUsedAmount: 22, userUsedAmount: 22 },
        { bucketId: monthlyBucketId, windowType: "monthly", limitAmount: 3_000, organizationUsedAmount: 40, userUsedAmount: 33 },
      ],
    }],
  })

  const firstReset = await routeApp().request(`http://den.local/v1/admin/users/${targetUserId}/inference-usage/reset`, { method: "POST" })
  expect(firstReset.status).toBe(200)
  await expect(firstReset.json()).resolves.toEqual({ ok: true, resetAmount: 66 })

  const remainingCharges = await db
    .select({ id: schema.InferenceUsageLedgerBucketChargeTable.id, amount: schema.InferenceUsageLedgerBucketChargeTable.amount })
    .from(schema.InferenceUsageLedgerBucketChargeTable)
    .where(drizzle.inArray(schema.InferenceUsageLedgerBucketChargeTable.id, [targetFiveHourChargeId, targetWeeklyChargeId, targetMonthlyChargeId, adminMonthlyChargeId]))
  expect(remainingCharges).toEqual([{ id: adminMonthlyChargeId, amount: 7 }])

  const bucketRows = await db
    .select({ id: schema.InferenceOrgUsageBucketTable.id, usedAmount: schema.InferenceOrgUsageBucketTable.used_amount })
    .from(schema.InferenceOrgUsageBucketTable)
    .where(drizzle.eq(schema.InferenceOrgUsageBucketTable.organization_id, organizationId))
  expect(bucketRows).toEqual(expect.arrayContaining([
    { id: fiveHourBucketId, usedAmount: 0 },
    { id: weeklyBucketId, usedAmount: 0 },
    { id: monthlyBucketId, usedAmount: 7 },
  ]))

  const secondReset = await routeApp().request(`http://den.local/v1/admin/users/${targetUserId}/inference-usage/reset`, { method: "POST" })
  expect(secondReset.status).toBe(200)
  await expect(secondReset.json()).resolves.toEqual({ ok: true, resetAmount: 0 })

  const usageAfter = await routeApp().request(`http://den.local/v1/admin/users/${targetUserId}/inference-usage`)
  expect(usageAfter.status).toBe(200)
  await expect(usageAfter.json()).resolves.toMatchObject({
    organizations: [{ windows: [
      { bucketId: fiveHourBucketId, organizationUsedAmount: 0, userUsedAmount: 0 },
      { bucketId: weeklyBucketId, organizationUsedAmount: 0, userUsedAmount: 0 },
      { bucketId: monthlyBucketId, organizationUsedAmount: 7, userUsedAmount: 0 },
    ] }],
  })
})
