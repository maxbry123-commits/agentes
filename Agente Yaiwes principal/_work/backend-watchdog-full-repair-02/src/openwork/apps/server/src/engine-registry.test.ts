import { spawn } from "node:child_process";
import { mkdtemp, rm, stat, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { describe, expect, test } from "bun:test";

import {
  buildEngineAuthProbeHeader,
  engineRegistryFilePath,
  readEngineRegistry,
  reapOrphanEngineInstances,
  registerEngineInstance,
  removeEngineInstance,
  updateEngineInstanceRole,
  type EngineInstanceRecord,
} from "./engine-registry.js";
import type { ServerConfig } from "./types.js";

type Fixture = {
  root: string;
  config: ServerConfig;
  cleanups: Array<() => void | Promise<void>>;
  restore: () => Promise<void>;
};

async function createFixture(): Promise<Fixture> {
  const root = await mkdtemp(join(tmpdir(), "openwork-engine-registry-"));
  const previousRuntimeDb = process.env.OPENWORK_RUNTIME_DB;
  process.env.OPENWORK_RUNTIME_DB = join(root, "runtime.sqlite");
  const config = { configPath: join(root, "server.json") } as unknown as ServerConfig;
  const cleanups: Array<() => void | Promise<void>> = [];
  return {
    root,
    config,
    cleanups,
    async restore() {
      for (const cleanup of cleanups.reverse()) {
        try {
          await cleanup();
        } catch {
          // Best-effort cleanup.
        }
      }
      if (previousRuntimeDb === undefined) delete process.env.OPENWORK_RUNTIME_DB;
      else process.env.OPENWORK_RUNTIME_DB = previousRuntimeDb;
      await rm(root, { recursive: true, force: true });
    },
  };
}

function processAlive(pid: number): boolean {
  try {
    process.kill(pid, 0);
    return true;
  } catch (error) {
    return (error as NodeJS.ErrnoException).code === "EPERM";
  }
}

async function waitForExit(pid: number, timeoutMs = 5000): Promise<boolean> {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (!processAlive(pid)) return true;
    await new Promise((resolve) => setTimeout(resolve, 50));
  }
  return !processAlive(pid);
}

/** Pid of a process that has already exited — a provably dead owner. */
async function deadPid(): Promise<number> {
  const child = spawn(process.execPath, ["-e", "process.exit(0)"], { stdio: "ignore" });
  const pid = child.pid;
  if (!pid) throw new Error("Failed to spawn short-lived process");
  await new Promise<void>((resolve) => child.once("exit", () => resolve()));
  return pid;
}

type FakeEngine = {
  pid: number;
  port: number;
  url: string;
  scriptPath: string;
  kill: () => void;
};

/**
 * A long-lived process that answers /global/health only with the expected
 * basic-auth header — the shape the reaper's identity probe relies on.
 */
async function spawnFakeEngine(fixture: Fixture, name: string, authHeader: string): Promise<FakeEngine> {
  const scriptPath = join(fixture.root, `${name}.mjs`);
  await writeFile(scriptPath, [
    "const expected = process.env.FAKE_ENGINE_AUTH ?? \"\";",
    "const server = Bun.serve({",
    "  hostname: \"127.0.0.1\",",
    "  port: 0,",
    "  fetch(request) {",
    "    const header = request.headers.get(\"authorization\") ?? \"\";",
    "    if (expected && header !== expected) return new Response(\"unauthorized\", { status: 401 });",
    "    return Response.json({ ok: true });",
    "  },",
    "});",
    "console.log(`listening ${server.port}`);",
    "process.on(\"SIGTERM\", () => process.exit(0));",
    "setInterval(() => undefined, 1000);",
  ].join("\n"));
  const child = spawn(process.execPath, [scriptPath], {
    env: { ...process.env, FAKE_ENGINE_AUTH: authHeader },
    stdio: ["ignore", "pipe", "ignore"],
  });
  const pid = child.pid;
  if (!pid) throw new Error("Failed to spawn fake engine");
  const kill = () => {
    try {
      child.kill("SIGKILL");
    } catch {
      // Already exited.
    }
  };
  fixture.cleanups.push(kill);
  const port = await new Promise<number>((resolve, reject) => {
    const timeout = setTimeout(() => reject(new Error("Fake engine did not report a port")), 10_000);
    let buffer = "";
    child.stdout?.on("data", (chunk) => {
      buffer += String(chunk);
      const match = buffer.match(/listening (\d+)/);
      if (match?.[1]) {
        clearTimeout(timeout);
        resolve(Number(match[1]));
      }
    });
    child.once("exit", () => {
      clearTimeout(timeout);
      reject(new Error("Fake engine exited before reporting a port"));
    });
  });
  child.unref();
  return { pid, port, url: `http://127.0.0.1:${port}`, scriptPath, kill };
}

/** A long-lived process with no HTTP listener — a hung engine or a stranger. */
async function spawnIdleProcess(fixture: Fixture, name: string): Promise<{ pid: number; scriptPath: string; kill: () => void }> {
  const scriptPath = join(fixture.root, `${name}.mjs`);
  await writeFile(scriptPath, [
    "process.on(\"SIGTERM\", () => process.exit(0));",
    "setInterval(() => undefined, 1000);",
  ].join("\n"));
  const child = spawn(process.execPath, [scriptPath], { stdio: "ignore" });
  const pid = child.pid;
  if (!pid) throw new Error("Failed to spawn idle process");
  const kill = () => {
    try {
      child.kill("SIGKILL");
    } catch {
      // Already exited.
    }
  };
  fixture.cleanups.push(kill);
  child.unref();
  return { pid, scriptPath, kill };
}

function makeEntry(overrides: Partial<EngineInstanceRecord>): EngineInstanceRecord {
  return {
    id: overrides.id ?? `entry_${Math.random().toString(36).slice(2)}`,
    pid: overrides.pid ?? 1,
    port: overrides.port ?? 1024,
    url: overrides.url ?? "http://127.0.0.1:1024",
    startedAt: overrides.startedAt ?? Date.now(),
    role: overrides.role ?? "primary",
    serverRunId: overrides.serverRunId ?? "run",
    ownerPid: overrides.ownerPid ?? process.pid,
    authProbe: overrides.authProbe ?? "",
    bin: overrides.bin ?? "opencode",
  };
}

describe("engine registry", () => {
  test("registers, updates, and removes entries", async () => {
    const fixture = await createFixture();
    try {
      const first = makeEntry({ id: "first", pid: 111, role: "primary" });
      const second = makeEntry({ id: "second", pid: 222, role: "starting" });
      await registerEngineInstance(fixture.config, first);
      await registerEngineInstance(fixture.config, second);
      await updateEngineInstanceRole(fixture.config, "second", "draining");

      const entries = await readEngineRegistry(fixture.config);
      expect(entries).toHaveLength(2);
      expect(entries.find((entry) => entry.id === "second")?.role).toBe("draining");

      if (process.platform !== "win32") {
        const mode = (await stat(engineRegistryFilePath(fixture.config))).mode & 0o777;
        expect(mode).toBe(0o600);
      }

      await removeEngineInstance(fixture.config, "first");
      expect((await readEngineRegistry(fixture.config)).map((entry) => entry.id)).toEqual(["second"]);
    } finally {
      await fixture.restore();
    }
  });

  test("treats a corrupt registry file as empty and recovers on the next write", async () => {
    const fixture = await createFixture();
    try {
      await registerEngineInstance(fixture.config, makeEntry({ id: "kept", pid: 333 }));
      await writeFile(engineRegistryFilePath(fixture.config), "{not json");
      expect(await readEngineRegistry(fixture.config)).toEqual([]);
      await registerEngineInstance(fixture.config, makeEntry({ id: "recovered", pid: 444 }));
      expect((await readEngineRegistry(fixture.config)).map((entry) => entry.id)).toEqual(["recovered"]);
    } finally {
      await fixture.restore();
    }
  });

  test("spares an engine whose owning server is still alive", async () => {
    const fixture = await createFixture();
    try {
      const engine = await spawnFakeEngine(fixture, "owned-engine", buildEngineAuthProbeHeader("user", "pass"));
      await registerEngineInstance(fixture.config, makeEntry({
        id: "owned",
        pid: engine.pid,
        port: engine.port,
        url: engine.url,
        ownerPid: process.pid,
        authProbe: buildEngineAuthProbeHeader("user", "pass"),
        bin: engine.scriptPath,
      }));

      const result = await reapOrphanEngineInstances(fixture.config, { killWaitMs: 100 });

      expect(result.spared).toEqual([engine.pid]);
      expect(result.killed).toEqual([]);
      expect(processAlive(engine.pid)).toBe(true);
      expect((await readEngineRegistry(fixture.config)).map((entry) => entry.id)).toEqual(["owned"]);
    } finally {
      await fixture.restore();
    }
  });

  test("kills a provable orphan whose owner is gone", async () => {
    const fixture = await createFixture();
    try {
      const authProbe = buildEngineAuthProbeHeader("orphan-user", "orphan-pass");
      const engine = await spawnFakeEngine(fixture, "orphan-engine", authProbe);
      await registerEngineInstance(fixture.config, makeEntry({
        id: "orphan",
        pid: engine.pid,
        port: engine.port,
        url: engine.url,
        ownerPid: await deadPid(),
        authProbe,
        bin: engine.scriptPath,
      }));

      const result = await reapOrphanEngineInstances(fixture.config, { killWaitMs: 200 });

      expect(result.killed).toEqual([engine.pid]);
      expect(await waitForExit(engine.pid)).toBe(true);
      expect(await readEngineRegistry(fixture.config)).toEqual([]);
    } finally {
      await fixture.restore();
    }
  });

  test("kills a hung orphan that matches the recorded binary but no longer answers", async () => {
    const fixture = await createFixture();
    try {
      const hung = await spawnIdleProcess(fixture, "hung-engine");
      await registerEngineInstance(fixture.config, makeEntry({
        id: "hung",
        pid: hung.pid,
        // Nothing listens on this port, so the identity probe is unreachable;
        // the command match against the recorded script is the kill evidence.
        port: 1,
        url: "http://127.0.0.1:1",
        ownerPid: await deadPid(),
        authProbe: buildEngineAuthProbeHeader("hung-user", "hung-pass"),
        bin: hung.scriptPath,
      }));

      const result = await reapOrphanEngineInstances(fixture.config, { killWaitMs: 200, probeTimeoutMs: 250 });

      expect(result.killed).toEqual([hung.pid]);
      expect(await waitForExit(hung.pid)).toBe(true);
      expect(await readEngineRegistry(fixture.config)).toEqual([]);
    } finally {
      await fixture.restore();
    }
  });

  test("never kills a process whose port answers with different credentials", async () => {
    const fixture = await createFixture();
    try {
      const engine = await spawnFakeEngine(fixture, "stranger-engine", buildEngineAuthProbeHeader("real-user", "real-pass"));
      await registerEngineInstance(fixture.config, makeEntry({
        id: "stranger",
        pid: engine.pid,
        port: engine.port,
        url: engine.url,
        ownerPid: await deadPid(),
        // Recorded credentials no longer match what the port expects, so the
        // probe cannot prove the process is ours.
        authProbe: buildEngineAuthProbeHeader("stale-user", "stale-pass"),
        bin: engine.scriptPath,
      }));

      const result = await reapOrphanEngineInstances(fixture.config, { killWaitMs: 100 });

      expect(result.killed).toEqual([]);
      expect(result.dropped).toEqual([engine.pid]);
      expect(processAlive(engine.pid)).toBe(true);
      expect(await readEngineRegistry(fixture.config)).toEqual([]);
    } finally {
      await fixture.restore();
    }
  });

  test("drops entries whose pid was reused by an unrelated process", async () => {
    const fixture = await createFixture();
    try {
      const bystander = await spawnIdleProcess(fixture, "unrelated-process");
      await registerEngineInstance(fixture.config, makeEntry({
        id: "reused",
        pid: bystander.pid,
        port: 1,
        url: "http://127.0.0.1:1",
        ownerPid: await deadPid(),
        authProbe: buildEngineAuthProbeHeader("reused-user", "reused-pass"),
        // The recorded binary shares nothing with the bystander's command line.
        bin: "/opt/does-not-exist/managed-engine-bin",
      }));

      const result = await reapOrphanEngineInstances(fixture.config, { killWaitMs: 100, probeTimeoutMs: 250 });

      expect(result.killed).toEqual([]);
      expect(result.dropped).toEqual([bystander.pid]);
      expect(processAlive(bystander.pid)).toBe(true);
      expect(await readEngineRegistry(fixture.config)).toEqual([]);
    } finally {
      await fixture.restore();
    }
  });

  test("drops entries whose engine already exited without killing anything", async () => {
    const fixture = await createFixture();
    try {
      await registerEngineInstance(fixture.config, makeEntry({
        id: "gone",
        pid: await deadPid(),
        ownerPid: await deadPid(),
      }));

      const result = await reapOrphanEngineInstances(fixture.config, { killWaitMs: 100 });

      expect(result.killed).toEqual([]);
      expect(result.dropped).toHaveLength(1);
      expect(await readEngineRegistry(fixture.config)).toEqual([]);
    } finally {
      await fixture.restore();
    }
  });
});
