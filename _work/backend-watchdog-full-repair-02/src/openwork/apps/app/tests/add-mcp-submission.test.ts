import { describe, expect, test } from "bun:test";

import type { McpDirectoryInfo } from "../src/app/constants";
import { conflictsWithOpenworkConnect } from "../src/react-app/domains/connections/mcp-connection-boundary";
import { submitMcpEntry } from "../src/react-app/domains/connections/modals/add-mcp-submission";

const entry: McpDirectoryInfo = {
  name: "BigQuery",
  description: "",
  type: "remote",
  url: "https://bigquery.googleapis.com/mcp",
  oauth: true,
  managedOAuth: true,
};

describe("local MCP submission feedback", () => {
  test("reserves the OpenWork Connect runtime name for its managed entry", () => {
    expect(conflictsWithOpenworkConnect({ name: "OpenWork Cloud" })).toBe(true);
    expect(conflictsWithOpenworkConnect({ name: "openwork-cloud" })).toBe(true);
    expect(conflictsWithOpenworkConnect({ id: "openwork-cloud", name: "Custom cloud" })).toBe(true);
    expect(conflictsWithOpenworkConnect({
      name: "OpenWork Cloud",
      serverName: "openwork-cloud",
      managedBy: "openwork-connect",
    })).toBe(false);
    expect(conflictsWithOpenworkConnect({ name: "BigQuery" })).toBe(false);
  });

  test("returns no error only after the connection succeeds", async () => {
    expect(await submitMcpEntry(async () => ({ ok: true }), entry, "Fallback")).toBeNull();
  });

  test("preserves the server error when the connection fails", async () => {
    expect(await submitMcpEntry(
      async () => ({ ok: false, error: "Secure storage is unavailable." }),
      entry,
      "Fallback",
    )).toBe("Secure storage is unavailable.");
  });

  test("turns a rejected connection into inline feedback", async () => {
    expect(await submitMcpEntry(
      async () => {
        throw new Error("Unexpected server error");
      },
      entry,
      "Fallback",
    )).toBe("Unexpected server error");
  });
});
