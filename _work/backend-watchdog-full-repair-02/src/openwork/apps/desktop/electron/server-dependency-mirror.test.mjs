// Regression: server/dist/local-managed-mcp-url-guard.js failed to resolve undici in the packaged app (PR #3652).
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { describe, it } from "node:test";

const desktopPackage = JSON.parse(
  readFileSync(new URL("../package.json", import.meta.url), "utf8"),
);
const serverPackage = JSON.parse(
  readFileSync(new URL("../../server/package.json", import.meta.url), "utf8"),
);
const mcpSdkPackage = JSON.parse(
  readFileSync(new URL("../node_modules/@modelcontextprotocol/sdk/package.json", import.meta.url), "utf8"),
);

describe("server dependency mirror", () => {
  it("mirrors every server runtime dependency in the desktop package", () => {
    for (const [name, spec] of Object.entries(serverPackage.dependencies)) {
      assert.equal(
        desktopPackage.dependencies[name],
        spec,
        `Server runtime dependency "${name}" must be mirrored with the same version in apps/desktop/package.json because the packaged app imports server/dist from app.asar and electron-builder only packs node_modules declared by apps/desktop/package.json.`,
      );
    }
  });

  it("declares MCP validation dependencies that electron-builder must pack", () => {
    for (const name of ["ajv", "ajv-formats"]) {
      assert.equal(
        desktopPackage.dependencies[name],
        mcpSdkPackage.dependencies[name],
        `MCP SDK runtime dependency "${name}" must be declared directly in apps/desktop/package.json so it is available from app.asar.`,
      );
    }
  });
});
