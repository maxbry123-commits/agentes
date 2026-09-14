import { afterEach, describe, expect, test } from "bun:test";
import type { LookupAddress } from "node:dns";
import { createServer, type Server } from "node:http";
import type { LookupFunction } from "node:net";

import {
  assertLocalManagedMcpUrl,
  createLocalManagedMcpGuardedFetch,
  createLocalManagedMcpPublicLookup,
  isLocalManagedMcpPrivateAddress,
} from "./local-managed-mcp-url-guard.js";

const previousDevMode = process.env.OPENWORK_DEV_MODE;
const previousPrivateOverride = process.env.OPENWORK_ALLOW_PRIVATE_MCP_URLS;

afterEach(() => {
  if (previousDevMode === undefined) delete process.env.OPENWORK_DEV_MODE;
  else process.env.OPENWORK_DEV_MODE = previousDevMode;
  if (previousPrivateOverride === undefined) delete process.env.OPENWORK_ALLOW_PRIVATE_MCP_URLS;
  else process.env.OPENWORK_ALLOW_PRIVATE_MCP_URLS = previousPrivateOverride;
});

async function startRedirectServer(
  location: string,
  status = 302,
): Promise<{ server: Server; url: string; requests: () => number }> {
  let requestCount = 0;
  const server = createServer((_request, response) => {
    requestCount += 1;
    response.writeHead(status, { location });
    response.end();
  });
  await new Promise<void>((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", resolve);
  });
  const address = server.address();
  if (!address || typeof address === "string") throw new Error("Test redirect server did not bind a TCP port.");
  return {
    server,
    url: `http://127.0.0.1:${address.port}`,
    requests: () => requestCount,
  };
}

async function stopServer(server: Server): Promise<void> {
  await new Promise<void>((resolve, reject) => server.close((error) => error ? reject(error) : resolve()));
}

async function lookupAll(lookup: LookupFunction, hostname: string): Promise<LookupAddress[]> {
  return await new Promise<LookupAddress[]>((resolve, reject) => {
    lookup(hostname, { all: true }, (error, addresses) => {
      if (error) {
        reject(error);
        return;
      }
      if (!Array.isArray(addresses)) {
        reject(new Error("Expected an all-address DNS lookup result."));
        return;
      }
      resolve(addresses);
    });
  });
}

describe("local managed MCP outbound URL guard", () => {
  test("classifies private and reserved IPv4 and IPv6 ranges", () => {
    expect(isLocalManagedMcpPrivateAddress("127.0.0.1")).toBe(true);
    expect(isLocalManagedMcpPrivateAddress("169.254.169.254")).toBe(true);
    expect(isLocalManagedMcpPrivateAddress("192.168.1.10")).toBe(true);
    expect(isLocalManagedMcpPrivateAddress("::1")).toBe(true);
    expect(isLocalManagedMcpPrivateAddress("fc00::1")).toBe(true);
    expect(isLocalManagedMcpPrivateAddress("8.8.8.8")).toBe(false);
    expect(isLocalManagedMcpPrivateAddress("2606:4700:4700::1111")).toBe(false);
  });

  test("rejects IANA special-use IPv4 blocks that are unsafe for MCP egress", () => {
    for (const address of [
      "192.0.0.1",
      "192.0.0.9",
      "192.0.2.1",
      "192.88.99.1",
      "198.51.100.1",
      "203.0.113.1",
    ]) {
      expect(isLocalManagedMcpPrivateAddress(address)).toBe(true);
    }
    for (const address of ["192.0.1.1", "198.20.0.1", "203.0.114.1"]) {
      expect(isLocalManagedMcpPrivateAddress(address)).toBe(false);
    }
  });

  test("requires public HTTPS outside explicit local development", async () => {
    delete process.env.OPENWORK_DEV_MODE;
    delete process.env.OPENWORK_ALLOW_PRIVATE_MCP_URLS;
    await expect(assertLocalManagedMcpUrl("http://127.0.0.1:3978/mcp")).rejects.toThrow("HTTPS");
    await expect(assertLocalManagedMcpUrl("https://169.254.169.254/latest/meta-data")).rejects.toThrow("private or reserved");
    await expect(assertLocalManagedMcpUrl("https://192.0.0.1/mcp")).rejects.toThrow("private or reserved");
    await expect(assertLocalManagedMcpUrl("https://8.8.8.8/mcp")).resolves.toBeUndefined();
  });

  test("rejects a redirect to a non-web protocol before a second request", async () => {
    process.env.OPENWORK_DEV_MODE = "1";
    delete process.env.OPENWORK_ALLOW_PRIVATE_MCP_URLS;
    const fixture = await startRedirectServer("file:///tmp/private");
    try {
      await expect(createLocalManagedMcpGuardedFetch()(`${fixture.url}/mcp`)).rejects.toThrow("protocol");
      expect(fixture.requests()).toBe(1);
    } finally {
      await stopServer(fixture.server);
    }
  });

  test("blocks cross-origin redirects for credential-bearing request bodies", async () => {
    process.env.OPENWORK_DEV_MODE = "1";
    delete process.env.OPENWORK_ALLOW_PRIVATE_MCP_URLS;
    const fixture = await startRedirectServer("https://1.1.1.1/token", 307);
    try {
      await expect(createLocalManagedMcpGuardedFetch()(`${fixture.url}/token`, {
        method: "POST",
        headers: { authorization: "Bearer test" },
        body: "grant_type=refresh_token",
      })).rejects.toThrow("request body cannot be redirected");
      expect(fixture.requests()).toBe(1);
    } finally {
      await stopServer(fixture.server);
    }
  });

  test("binds the socket lookup to the validated public DNS answer", async () => {
    let resolverCalls = 0;
    const publicLookup = createLocalManagedMcpPublicLookup(async () => {
      resolverCalls += 1;
      return [{ address: "93.184.216.34", family: 4 }];
    });
    await expect(lookupAll(publicLookup, "mcp.example")).resolves.toEqual([
      { address: "93.184.216.34", family: 4 },
    ]);
    expect(resolverCalls).toBe(1);
  });

  test("rejects a private answer returned by the socket's own DNS lookup", async () => {
    const rebindingLookup = createLocalManagedMcpPublicLookup(async () => [
      { address: "169.254.169.254", family: 4 },
    ]);
    await expect(lookupAll(rebindingLookup, "mcp.example")).rejects.toThrow("private or reserved");
  });
});
