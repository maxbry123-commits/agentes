import { expect, test } from "bun:test"
import { createHash } from "node:crypto"

process.env.DEN_DB_ENCRYPTION_KEY ??= "x".repeat(32)
process.env.BETTER_AUTH_SECRET ??= "y".repeat(32)
process.env.BETTER_AUTH_URL ??= "http://127.0.0.1:3005"
process.env.OPENWORK_DEV_MODE ??= "1"
process.env.DATABASE_URL ??= "mysql://root:password@127.0.0.1:3306/openwork_den"

const {
  inspectRemoteMcpAppHtml,
  REMOTE_MCP_APP_MAX_BYTES,
  validateRemoteMcpAppContentType,
  validateRemoteMcpAppSourceUrl,
} = await import("../src/remote-mcp-apps.js")

function appHtml(extra = "") {
  return `<!doctype html><html><head><title>Project Explorer</title><meta name="description" content="Browse connected projects."><style>body{font:14px sans-serif}</style></head><body><main id="app"></main>${extra}<script>document.querySelector('#app').textContent='Ready'</script></body></html>`
}

test("accepts a self-contained HTML app without an OpenWork-specific manifest", () => {
  const html = appHtml()
  const inspected = inspectRemoteMcpAppHtml(html)
  expect(inspected.metadata).toMatchObject({
    name: "Project Explorer",
    description: "Browse connected projects.",
  })
  expect(inspected.metadata.version).toBe(inspected.digest.slice("sha256:".length, "sha256:".length + 12))
  expect(inspected.byteSize).toBe(Buffer.byteLength(html))
  expect(inspected.digest).toMatch(/^sha256:[a-f0-9]{64}$/)
})

test("derives a fallback name when the document omits a title", () => {
  const html = appHtml().replace("<title>Project Explorer</title>", "")
  expect(inspectRemoteMcpAppHtml(html).metadata.name).toBe("Cached MCP App")
})

test("decodes document metadata exactly once", () => {
  const html = appHtml()
    .replace("Project Explorer", "Project &amp;lt;Explorer&amp;gt;")
    .replace("Browse connected projects.", "Browse &amp;quot;connected&amp;quot; projects.")
  expect(inspectRemoteMcpAppHtml(html).metadata).toMatchObject({
    name: "Project &lt;Explorer&gt;",
    description: "Browse &quot;connected&quot; projects.",
  })
})

test("does not mistake bundled JavaScript strings for external CSS", () => {
  const html = appHtml('<script>const diagnostic = "CSS url() and @import \\\"theme.css\\\""</script>')
  expect(inspectRemoteMcpAppHtml(html).metadata.name).toBe("Project Explorer")
})

test("rejects runtime resource dependencies instead of caching a partially portable app", () => {
  expect(() => inspectRemoteMcpAppHtml(appHtml('<script src="https://cdn.example/app.js"></script>')))
    .toThrow("self-contained HTML file")
  expect(() => inspectRemoteMcpAppHtml(appHtml('<script\tsrc="https://cdn.example/app.js"></script\t\n ignored>')))
    .toThrow("self-contained HTML file")
  expect(() => inspectRemoteMcpAppHtml(appHtml('<link rel="stylesheet" href="./app.css">')))
    .toThrow("self-contained HTML file")
  expect(() => inspectRemoteMcpAppHtml(appHtml('<img src="/logo.png">')))
    .toThrow("self-contained HTML file")
  expect(() => inspectRemoteMcpAppHtml(appHtml('<iframe srcdoc="<p>nested</p>"></iframe>')))
    .toThrow("self-contained HTML file")
  expect(() => inspectRemoteMcpAppHtml(appHtml('<style>main{background:url("./background.png")}</style>')))
    .toThrow("self-contained HTML file")
  expect(() => inspectRemoteMcpAppHtml(appHtml('<main style="background:url(./background.png)"></main>')))
    .toThrow("self-contained HTML file")
})

test("uses the desktop MCP App host's exact resource byte ceiling", () => {
  expect(REMOTE_MCP_APP_MAX_BYTES).toBe(768 * 1024)
})

test("requires a credential-free HTTPS source outside explicit private development mode", () => {
  expect(validateRemoteMcpAppSourceUrl("https://apps.example/app/index.html")).toBe("https://apps.example/app/index.html")
  expect(() => validateRemoteMcpAppSourceUrl("http://apps.example/app/index.html")).toThrow("must use HTTPS")
  expect(() => validateRemoteMcpAppSourceUrl("file:///tmp/index.html")).toThrow("must use HTTPS")
  expect(() => validateRemoteMcpAppSourceUrl("https://token@apps.example/index.html")).toThrow("embedded credentials")
  expect(() => validateRemoteMcpAppSourceUrl("https://apps.example/index.html?access_token=secret")).toThrow("must not contain credentials")
  expect(validateRemoteMcpAppSourceUrl("http://127.0.0.1:8787/index.html", true)).toBe("http://127.0.0.1:8787/index.html")
})

test("accepts only UTF-8 HTML MIME types", () => {
  expect(validateRemoteMcpAppContentType("text/html; charset=UTF-8")).toBe("text/html")
  expect(validateRemoteMcpAppContentType("application/xhtml+xml; charset=\"utf-8\"")).toBe("application/xhtml+xml")
  expect(() => validateRemoteMcpAppContentType(null)).toThrow("must be served as text/html")
  expect(() => validateRemoteMcpAppContentType("text/plain")).toThrow("must be served as text/html")
  expect(() => validateRemoteMcpAppContentType("text/html; charset=iso-8859-1")).toThrow("must be UTF-8")
})

test("digests the exact stored UTF-8 document including a leading BOM", () => {
  const html = `\uFEFF${appHtml()}`
  const inspected = inspectRemoteMcpAppHtml(html)
  expect(inspected.byteSize).toBe(Buffer.byteLength(html, "utf8"))
  expect(inspected.digest).toBe(`sha256:${createHash("sha256").update(html).digest("hex")}`)
})
