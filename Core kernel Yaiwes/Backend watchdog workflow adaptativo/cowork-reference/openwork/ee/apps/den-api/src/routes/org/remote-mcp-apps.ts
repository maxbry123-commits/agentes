import type { Context, Hono } from "hono"
import { describeRoute } from "hono-openapi"
import { z } from "zod"
import { jsonValidator, orgMemberRoute, paramValidator } from "../../middleware/index.js"
import { invalidRequestSchema, jsonResponse, notFoundSchema, unauthorizedSchema } from "../../openapi.js"
import { listTeamsForMember } from "../../orgs.js"
import {
  activateRemoteMcpAppRevision,
  getRemoteMcpApp,
  importRemoteMcpApp,
  loadRemoteMcpAppRevision,
  previewRemoteMcpApp,
  refreshRemoteMcpApp,
  RemoteMcpAppError,
  setRemoteMcpAppRetired,
} from "../../remote-mcp-apps.js"
import { PluginArchAuthorizationError, type PluginArchActorContext } from "./plugin-system/access.js"
import { PluginArchRouteFailure } from "./plugin-system/store.js"
import type { OrgRouteVariables } from "./shared.js"

const sourceSchema = z.object({ sourceUrl: z.string().trim().url().max(2048) })
const importSchema = sourceSchema.extend({
  activate: z.boolean().optional().default(true),
  pluginId: z.string().trim().min(1).max(160).optional(),
}).strict()
const refreshSchema = z.object({
  sourceUrl: z.string().trim().url().max(2048).optional(),
})
const appParamsSchema = z.object({ appId: z.string().trim().min(1).max(160) })
const revisionParamsSchema = appParamsSchema.extend({ versionId: z.string().trim().min(1).max(160) })
const activateSchema = z.object({ versionId: z.string().trim().min(1).max(160) })
const lifecycleSchema = z.object({ action: z.enum(["retire", "restore"]) })
const remoteAppResponseSchema = z.object({ item: z.unknown() })
const previewResponseSchema = z.object({ preview: z.unknown() })

type OrgContext = Context<{ Variables: OrgRouteVariables }>

async function actorContext(c: OrgContext): Promise<PluginArchActorContext> {
  const organizationContext = c.get("organizationContext")
  if (!organizationContext) throw new RemoteMcpAppError(404, "organization_not_found", "Organization context not found.")
  return {
    organizationContext,
    memberTeams: await listTeamsForMember({
      organizationId: organizationContext.organization.id,
      memberId: organizationContext.currentMember.id,
    }),
    session: c.get("session"),
  }
}

function errorResponse(c: OrgContext, error: unknown) {
  if (error instanceof RemoteMcpAppError) {
    return c.json({ error: error.code, message: error.message }, error.status)
  }
  if (error instanceof PluginArchAuthorizationError) {
    return c.json({ error: error.error, message: error.message, reason: error.reason }, error.status)
  }
  if (error instanceof PluginArchRouteFailure) {
    return c.json({ error: error.error, message: error.message }, error.status)
  }
  throw error
}

function safeDownloadName(name: string) {
  const normalized = name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 80)
  return `${normalized || "remote-mcp-app"}.html`
}

export function registerRemoteMcpAppRoutes<T extends { Variables: OrgRouteVariables }>(app: Hono<T>) {
  app.post(
    "/v1/remote-mcp-apps/preview",
    describeRoute({
      tags: ["Remote MCP Apps"],
      summary: "Download and inspect a portable MCP App without storing it",
      responses: {
        200: jsonResponse("Remote MCP App preview returned.", previewResponseSchema),
        400: jsonResponse("Invalid request.", invalidRequestSchema),
        401: jsonResponse("Sign-in required.", unauthorizedSchema),
      },
    }),
    orgMemberRoute(),
    jsonValidator(sourceSchema),
    async (c) => {
      try {
        return c.json({ preview: await previewRemoteMcpApp(c.req.valid("json").sourceUrl) })
      } catch (error) {
        return errorResponse(c as unknown as OrgContext, error)
      }
    },
  )

  app.post(
    "/v1/remote-mcp-apps",
    describeRoute({
      tags: ["Remote MCP Apps"],
      summary: "Import and cache a portable MCP App",
      responses: {
        201: jsonResponse("Remote MCP App imported.", remoteAppResponseSchema),
        400: jsonResponse("Invalid request.", invalidRequestSchema),
        401: jsonResponse("Sign-in required.", unauthorizedSchema),
      },
    }),
    orgMemberRoute(),
    jsonValidator(importSchema),
    async (c) => {
      try {
        const body = c.req.valid("json")
        const item = await importRemoteMcpApp({ context: await actorContext(c as unknown as OrgContext), ...body })
        return c.json({ item }, 201)
      } catch (error) {
        return errorResponse(c as unknown as OrgContext, error)
      }
    },
  )

  app.get(
    "/v1/remote-mcp-apps/:appId",
    describeRoute({
      tags: ["Remote MCP Apps"],
      summary: "Get a Remote MCP App installation",
      responses: {
        200: jsonResponse("Remote MCP App returned.", remoteAppResponseSchema),
        404: jsonResponse("Remote MCP App not found.", notFoundSchema),
      },
    }),
    orgMemberRoute(),
    paramValidator(appParamsSchema),
    async (c) => {
      try {
        return c.json({ item: await getRemoteMcpApp({
          context: await actorContext(c as unknown as OrgContext),
          configObjectId: c.req.valid("param").appId,
        }) })
      } catch (error) {
        return errorResponse(c as unknown as OrgContext, error)
      }
    },
  )

  app.post(
    "/v1/remote-mcp-apps/:appId/refresh",
    describeRoute({
      tags: ["Remote MCP Apps"],
      summary: "Cache a new immutable draft revision from the source URL",
      responses: { 200: jsonResponse("Remote MCP App refreshed.", remoteAppResponseSchema) },
    }),
    orgMemberRoute(),
    paramValidator(appParamsSchema),
    jsonValidator(refreshSchema),
    async (c) => {
      try {
        return c.json({ item: await refreshRemoteMcpApp({
          context: await actorContext(c as unknown as OrgContext),
          configObjectId: c.req.valid("param").appId,
          ...c.req.valid("json"),
        }) })
      } catch (error) {
        return errorResponse(c as unknown as OrgContext, error)
      }
    },
  )

  app.post(
    "/v1/remote-mcp-apps/:appId/activate",
    describeRoute({
      tags: ["Remote MCP Apps"],
      summary: "Activate or roll back to an immutable app revision",
      responses: { 200: jsonResponse("Remote MCP App revision activated.", remoteAppResponseSchema) },
    }),
    orgMemberRoute(),
    paramValidator(appParamsSchema),
    jsonValidator(activateSchema),
    async (c) => {
      try {
        return c.json({ item: await activateRemoteMcpAppRevision({
          context: await actorContext(c as unknown as OrgContext),
          configObjectId: c.req.valid("param").appId,
          versionId: c.req.valid("json").versionId,
        }) })
      } catch (error) {
        return errorResponse(c as unknown as OrgContext, error)
      }
    },
  )

  app.post(
    "/v1/remote-mcp-apps/:appId/lifecycle",
    describeRoute({
      tags: ["Remote MCP Apps"],
      summary: "Retire or restore a Remote MCP App",
      responses: { 200: jsonResponse("Remote MCP App lifecycle updated.", remoteAppResponseSchema) },
    }),
    orgMemberRoute(),
    paramValidator(appParamsSchema),
    jsonValidator(lifecycleSchema),
    async (c) => {
      try {
        return c.json({ item: await setRemoteMcpAppRetired({
          context: await actorContext(c as unknown as OrgContext),
          configObjectId: c.req.valid("param").appId,
          retired: c.req.valid("json").action === "retire",
        }) })
      } catch (error) {
        return errorResponse(c as unknown as OrgContext, error)
      }
    },
  )

  app.get(
    "/v1/remote-mcp-apps/:appId/revisions/:versionId/download",
    describeRoute({
      tags: ["Remote MCP Apps"],
      summary: "Download an exact cached Remote MCP App revision",
      responses: { 200: { description: "Cached self-contained HTML returned." }, 404: jsonResponse("Revision not found.", notFoundSchema) },
    }),
    orgMemberRoute(),
    paramValidator(revisionParamsSchema),
    async (c) => {
      try {
        const params = c.req.valid("param")
        const loaded = await loadRemoteMcpAppRevision({
          context: await actorContext(c as unknown as OrgContext),
          configObjectId: params.appId,
          versionId: params.versionId,
        })
        return new Response(loaded.html, {
          headers: {
            "content-type": "text/html; charset=utf-8",
            "content-disposition": `attachment; filename="${safeDownloadName(loaded.payload.metadata.name)}"`,
            "content-length": String(Buffer.byteLength(loaded.html, "utf8")),
            etag: `"${loaded.payload.resource.digest}"`,
            "x-content-type-options": "nosniff",
          },
        })
      } catch (error) {
        return errorResponse(c as unknown as OrgContext, error)
      }
    },
  )
}
