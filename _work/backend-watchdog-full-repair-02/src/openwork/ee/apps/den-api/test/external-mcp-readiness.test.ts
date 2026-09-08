import { expect, mock, test } from "bun:test"

process.env.DEN_DB_ENCRYPTION_KEY ??= "x".repeat(32)
process.env.BETTER_AUTH_SECRET ??= "y".repeat(32)
process.env.BETTER_AUTH_URL ??= "http://127.0.0.1:3005"
process.env.OPENWORK_DEV_MODE ??= "1"
process.env.DATABASE_URL ??= "mysql://root:password@127.0.0.1:3306/openwork_den"

type QueryRows = Record<string, unknown>[]
type FakeQuery = {
  from: (table: unknown) => FakeQuery
  where: (condition: unknown) => FakeQuery
  limit: (count: number) => FakeQuery
  for: (mode: string) => FakeQuery
  then: Promise<QueryRows>["then"]
}

function fakeQuery(rows: QueryRows): FakeQuery {
  const promise = Promise.resolve(rows)
  const query: FakeQuery = {
    from: () => query,
    where: () => query,
    limit: () => query,
    for: () => {
      throw new Error("Read-only external MCP checks must not lock rows")
    },
    then: promise.then.bind(promise),
  }
  return query
}

const connection = {
  id: "emc_01k28e8q8pf8r9sff9mhyqxved",
  organizationId: "org_01k28e8q8pf8r9sff9mhyqxved",
  name: "Fixture MCP",
  url: "https://mcp.example/sse",
  authType: "oauth",
  credentialMode: "per_member",
  kind: "external_mcp",
  nativeProviderKey: null,
  oauthConfiguration: null,
  toolPolicy: null,
  apiKey: null,
  accessToken: null,
  refreshToken: null,
  tokenType: null,
  scope: null,
  expiresAt: null,
  pendingCodeVerifier: null,
  credentialHealth: null,
  oauthIssuerReviewRequiredAt: null,
  connectedAt: null,
  createdByOrgMembershipId: "mem_owner",
  createdAt: new Date("2026-01-01T00:00:00Z"),
  updatedAt: new Date("2026-01-01T00:00:00Z"),
}
const account = {
  id: "ca_01k28e8q8pf8r9sff9mhyqxved",
  organizationId: connection.organizationId,
  orgMembershipId: "mem_01k28e8q8pf8r9sff9mhyqxved",
  providerId: connection.id,
  externalAccountId: null,
  scopes: null,
  accessToken: "member-token",
  refreshToken: null,
  tokenType: null,
  expiresAt: null,
  pendingCodeVerifier: null,
  createdAt: new Date("2026-01-01T00:00:00Z"),
  updatedAt: new Date("2026-01-01T00:00:00Z"),
}
const orgClient = {
  id: "ooc_01k28e8q8pf8r9sff9mhyqxved",
  organizationId: connection.organizationId,
  providerId: connection.id,
  clientId: "mcp-client-id",
  clientSecret: null,
  extra: null,
  createdByOrgMembershipId: connection.createdByOrgMembershipId,
  createdAt: new Date("2026-01-01T00:00:00Z"),
  updatedAt: new Date("2026-01-01T00:00:00Z"),
}
let selectResults: QueryRows[] = []
let transactionCalls = 0

function queueSelectResults(results: QueryRows[]): void {
  selectResults = results
  transactionCalls = 0
}

mock.module("../src/db.js", () => ({
  db: {
    select: () => fakeQuery(selectResults.shift() ?? []),
    transaction: () => {
      transactionCalls += 1
      throw new Error("Read-only external MCP checks must not open a transaction")
    },
  },
}))

const {
  readConnectedAccountForExternalMcpIdentity,
  readOrgOAuthClientForExternalMcpIdentity,
  readyExternalMcpConnectionsForMember,
} = await import("../src/capability-sources/external-mcp-connections.js")

test("per-member connection list readiness reads credentials without row locks", async () => {
  queueSelectResults([[connection], [account], [connection]])
  await expect(readyExternalMcpConnectionsForMember(
    [connection] as never,
    account.orgMembershipId as never,
  )).resolves.toEqual([connection])
  expect(transactionCalls).toBe(0)
  expect(selectResults).toHaveLength(0)
})

test("per-member connected account reads do not lock the shared connection row", async () => {
  queueSelectResults([[connection], [account], [connection]])
  await expect(readConnectedAccountForExternalMcpIdentity({
    connection: connection as never,
    orgMembershipId: account.orgMembershipId as never,
  })).resolves.toEqual({ current: true, value: account })
  expect(transactionCalls).toBe(0)
  expect(selectResults).toHaveLength(0)
})

test("org OAuth client reads do not lock the shared connection row", async () => {
  queueSelectResults([[connection], [orgClient], [connection]])
  await expect(readOrgOAuthClientForExternalMcpIdentity(connection as never)).resolves.toEqual({
    current: true,
    value: orgClient,
  })
  expect(transactionCalls).toBe(0)
  expect(selectResults).toHaveLength(0)
})
