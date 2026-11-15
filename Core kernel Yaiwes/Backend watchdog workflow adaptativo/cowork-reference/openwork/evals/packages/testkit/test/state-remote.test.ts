import assert from "node:assert/strict";
import { mkdtemp, mkdir, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import test from "node:test";
import { electronProfilePaths } from "@openwork/hosts";
import { readConnectStateFile } from "../src/state.ts";
import type { CdpClient, Surface } from "@openwork/cdp";

const MISSING = "__OPENWORK_TESTKIT_MISSING__";

function surface(hostKind: string, profileDir?: string, sandboxId?: string): Surface {
  const client: CdpClient = {
    async send() {
      throw new Error("CDP must not be called.");
    },
    close() {},
  };
  return {
    handle: { name: "desktop", kind: "electron", hostKind, cdpUrl: "http://127.0.0.1:1", profileDir, sandboxId },
    client,
  };
}

test("readConnectStateFile reads Daytona candidates in order", async () => {
  const calls: Array<{ sandbox: string; script: string }> = [];
  const app = surface("daytona", "/workspace/profiles/desktop", "sandbox-1");
  const result = await readConnectStateFile(app, {
    exec: async (sandbox, script) => {
      calls.push({ sandbox, script });
      return calls.length === 1 ? MISSING : '{"connectEnabled":true}';
    },
  });

  assert.deepEqual(result, { status: "available", connectEnabled: true });
  assert.deepEqual(calls.map(({ sandbox }) => sandbox), ["sandbox-1", "sandbox-1"]);
  assert(calls[0]?.script.includes("/workspace/profiles/desktop/electron-userdata/openwork-dev-data/xdg/config/openwork/connect-state.json"));
  assert(calls[1]?.script.includes("/workspace/profiles/desktop/xdg-config/openwork/connect-state.json"));
  assert(calls.every(({ script }) => !script.includes("'")));
});

test("readConnectStateFile reports non-JSON Daytona content as invalid", async () => {
  const result = await readConnectStateFile(surface("daytona", "/workspace/profile", "sandbox"), { exec: async () => "not-json" });
  assert.deepEqual(result, { status: "invalid", connectEnabled: null });
});

test("readConnectStateFile reports missing when every Daytona candidate is absent", async () => {
  let calls = 0;
  const result = await readConnectStateFile(surface("daytona", "/workspace/profile", "sandbox"), {
    exec: async () => {
      calls += 1;
      return MISSING;
    },
  });
  assert.deepEqual(result, { status: "missing", connectEnabled: null });
  assert.equal(calls, 3);
});

test("readConnectStateFile requires a boolean connectEnabled", async () => {
  const result = await readConnectStateFile(surface("daytona", "/workspace/profile", "sandbox"), { exec: async () => "{}" });
  assert.deepEqual(result, { status: "invalid", connectEnabled: null });
});

test("readConnectStateFile rejects unsupported host kinds", async () => {
  await assert.rejects(readConnectStateFile(surface("attached", "/tmp/profile")), /supports local and daytona/);
});

test("readConnectStateFile requires a Daytona sandbox ID", async () => {
  await assert.rejects(readConnectStateFile(surface("daytona", "/workspace/profile")), /daytona app did not expose its sandbox ID/);
});

test("readConnectStateFile rejects unsafe Daytona profile paths without executing", async () => {
  let called = false;
  await assert.rejects(
    readConnectStateFile(surface("daytona", "/workspace/unsafe profile", "sandbox"), {
      exec: async () => {
        called = true;
        return MISSING;
      },
    }),
    /Unsafe connect-state path.*unsafe profile/,
  );
  assert.equal(called, false);
});

test("readConnectStateFile preserves local profile reads", async () => {
  const root = await mkdtemp(join(tmpdir(), "openwork-state-test-"));
  try {
    const paths = electronProfilePaths(root);
    const statePath = join(paths.configHome, "openwork", "connect-state.json");
    await mkdir(dirname(statePath), { recursive: true });
    await writeFile(statePath, '{"connectEnabled":false}', "utf8");
    assert.deepEqual(await readConnectStateFile(surface("local", root)), { status: "available", connectEnabled: false });
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});
