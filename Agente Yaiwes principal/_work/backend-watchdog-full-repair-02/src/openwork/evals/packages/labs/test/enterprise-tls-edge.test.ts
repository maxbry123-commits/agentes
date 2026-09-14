import assert from "node:assert/strict";
import { X509Certificate } from "node:crypto";
import { access, chmod, mkdtemp, readFile, rm, stat, symlink, writeFile } from "node:fs/promises";
import http from "node:http";
import https from "node:https";
import { tmpdir } from "node:os";
import path from "node:path";
import tls from "node:tls";
import { test } from "node:test";

import { stageTrustedEnterpriseTlsRoot, startEnterpriseTlsReverseEdge } from "../src/egress.ts";

function listen(server: http.Server): Promise<number> {
  return new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", () => {
      const address = server.address();
      if (!address || typeof address === "string") return reject(new Error("server did not bind"));
      resolve(address.port);
    });
  });
}

function close(server: http.Server): Promise<void> {
  return new Promise((resolve, reject) => server.close((error) => error ? reject(error) : resolve()));
}

function request(url: string, options: { ca?: string; method?: string; path?: string; body?: string } = {}): Promise<string> {
  return new Promise((resolve, reject) => {
    const target = new URL(url);
    const outgoing = https.request({
      hostname: target.hostname,
      port: target.port,
      ca: options.ca,
      method: options.method,
      path: options.path ?? `${target.pathname}${target.search}`,
    }, (response) => {
      const chunks: Buffer[] = [];
      response.on("data", (chunk) => chunks.push(Buffer.from(chunk)));
      response.on("end", () => resolve(Buffer.concat(chunks).toString("utf8")));
    });
    outgoing.on("error", reject);
    outgoing.end(options.body);
  });
}

function peerCertificatePem(url: string, ca: string): Promise<string> {
  const target = new URL(url);
  return new Promise((resolve, reject) => {
    const socket = tls.connect({ host: target.hostname, port: Number(target.port), ca, servername: "localhost" }, () => {
      const raw = socket.getPeerCertificate().raw;
      socket.end();
      if (!raw) reject(new Error("peer did not provide a certificate"));
      else resolve(new X509Certificate(raw).toString());
    });
    socket.on("error", reject);
  });
}

function manifest(rootPemPath: string): string {
  return `${JSON.stringify({
    pid: process.pid,
    candidateUrl: "https://localhost:8443",
    negativeUrl: "https://localhost:9443",
    adminUrl: "http://127.0.0.1:8445",
    rootPemPath,
  })}\n`;
}

test("enterprise TLS privileged trust material is validated and staged", async (t) => {
  const edge = await startEnterpriseTlsReverseEdge({ upstream: "http://127.0.0.1:1" });
  const dir = await mkdtemp(path.join(tmpdir(), "openwork-enterprise-tls-validation-test-"));
  const uid = typeof process.getuid === "function" ? process.getuid() : 0;
  try {
    await t.test("accepts an owned regular manifest and CA PEM", async () => {
      const rootPemPath = path.join(dir, "happy-root.pem");
      const manifestPath = path.join(dir, "happy-manifest.json");
      await writeFile(rootPemPath, edge.rootPem, { mode: 0o600 });
      await writeFile(manifestPath, manifest(rootPemPath), { mode: 0o600 });
      const staged = await stageTrustedEnterpriseTlsRoot(manifestPath, [uid]);
      try {
        assert.deepEqual(staged.rootPem, Buffer.from(edge.rootPem));
        assert.deepEqual(await readFile(staged.stagedRootPemPath), staged.rootPem);
        assert.notEqual(staged.stagedRootPemPath, rootPemPath);
        assert.equal((await stat(staged.stagedRootPemPath)).mode & 0o777, 0o600);
      } finally {
        await staged.cleanup();
      }
    });

    await t.test("rejects a symlinked manifest", async () => {
      const rootPemPath = path.join(dir, "manifest-link-root.pem");
      const targetPath = path.join(dir, "manifest-target.json");
      const manifestPath = path.join(dir, "manifest-link.json");
      await writeFile(rootPemPath, edge.rootPem, { mode: 0o600 });
      await writeFile(targetPath, manifest(rootPemPath), { mode: 0o600 });
      await symlink(targetPath, manifestPath);
      await assert.rejects(stageTrustedEnterpriseTlsRoot(manifestPath, [uid]), { name: "ENTERPRISE_TLS_MANIFEST_UNTRUSTED" });
    });

    await t.test("rejects a symlinked PEM", async () => {
      const targetPath = path.join(dir, "pem-target.pem");
      const rootPemPath = path.join(dir, "pem-link.pem");
      const manifestPath = path.join(dir, "pem-link-manifest.json");
      await writeFile(targetPath, edge.rootPem, { mode: 0o600 });
      await symlink(targetPath, rootPemPath);
      await writeFile(manifestPath, manifest(rootPemPath), { mode: 0o600 });
      await assert.rejects(stageTrustedEnterpriseTlsRoot(manifestPath, [uid]), { name: "ENTERPRISE_TLS_ROOT_PEM_UNTRUSTED" });
    });

    await t.test("rejects a world-writable PEM", async () => {
      const rootPemPath = path.join(dir, "writable-root.pem");
      const manifestPath = path.join(dir, "writable-manifest.json");
      await writeFile(rootPemPath, edge.rootPem, { mode: 0o600 });
      await chmod(rootPemPath, 0o666);
      await writeFile(manifestPath, manifest(rootPemPath), { mode: 0o600 });
      await assert.rejects(stageTrustedEnterpriseTlsRoot(manifestPath, [uid]), { name: "ENTERPRISE_TLS_ROOT_PEM_UNTRUSTED" });
    });

    await t.test("rejects non-CA and unparseable PEM files", async () => {
      const manifestPath = path.join(dir, "invalid-manifest.json");
      const rootPemPath = path.join(dir, "invalid-root.pem");
      await writeFile(manifestPath, manifest(rootPemPath), { mode: 0o600 });
      await writeFile(rootPemPath, await peerCertificatePem(edge.candidateUrl, edge.rootPem), { mode: 0o600 });
      await assert.rejects(stageTrustedEnterpriseTlsRoot(manifestPath, [uid]), /certificate is not a CA/u);
      await writeFile(rootPemPath, "not a certificate\n", { mode: 0o600 });
      await assert.rejects(stageTrustedEnterpriseTlsRoot(manifestPath, [uid]), { name: "ENTERPRISE_TLS_ROOT_PEM_UNTRUSTED" });
    });

    await t.test("rejects a relative rootPemPath", async () => {
      const manifestPath = path.join(dir, "relative-manifest.json");
      await writeFile(manifestPath, manifest("relative-root.pem"), { mode: 0o600 });
      await assert.rejects(stageTrustedEnterpriseTlsRoot(manifestPath, [uid]), /rootPemPath must be absolute/u);
    });

    await t.test("rejects an owner outside the explicit allowed uid set", async () => {
      const rootPemPath = path.join(dir, "owner-root.pem");
      const manifestPath = path.join(dir, "owner-manifest.json");
      await writeFile(rootPemPath, edge.rootPem, { mode: 0o600 });
      await writeFile(manifestPath, manifest(rootPemPath), { mode: 0o600 });
      await assert.rejects(stageTrustedEnterpriseTlsRoot(manifestPath, [uid + 1]), /owner uid .* is not allowed/u);
    });
  } finally {
    await edge.stop();
    await rm(dir, { recursive: true, force: true });
  }
});

test("enterprise TLS edge pins its upstream and exposes selective trust", async () => {
  const upstreamRequests: { method: string; url: string; body: string }[] = [];
  const upstream = http.createServer(async (incoming, response) => {
    const chunks: Buffer[] = [];
    for await (const chunk of incoming) chunks.push(Buffer.from(chunk));
    upstreamRequests.push({ method: incoming.method ?? "GET", url: incoming.url ?? "/", body: Buffer.concat(chunks).toString("utf8") });
    response.end("from-pinned-upstream");
  });
  const attackerHits: string[] = [];
  const attacker = http.createServer((incoming, response) => {
    attackerHits.push(incoming.url ?? "/");
    response.end("attacker");
  });
  const upstreamPort = await listen(upstream);
  const attackerPort = await listen(attacker);
  const edge = await startEnterpriseTlsReverseEdge({ upstream: `http://127.0.0.1:${upstreamPort}` });
  const rootPath = edge.rootPemPath;
  try {
    await assert.rejects(request(`${edge.candidateUrl}/default-trust`));
    assert.equal(await request(`${edge.candidateUrl}/v1/me?full=1`, { ca: edge.rootPem, method: "POST", body: "payload" }), "from-pinned-upstream");
    await assert.rejects(request(`${edge.negativeUrl}/negative`, { ca: edge.rootPem }));

    const absoluteTarget = `http://127.0.0.1:${attackerPort}/stolen?token=yes`;
    assert.equal(await request(edge.candidateUrl, { ca: edge.rootPem, path: absoluteTarget }), "from-pinned-upstream");
    assert.deepEqual(attackerHits, []);
    assert.deepEqual(upstreamRequests, [
      { method: "POST", url: "/v1/me?full=1", body: "payload" },
      { method: "GET", url: "/stolen?token=yes", body: "" },
    ]);
    assert.deepEqual(edge.requests.map(({ endpoint, method, path, body }) => ({ endpoint, method, path, body })), [
      { endpoint: "trusted-candidate", method: "POST", path: "/v1/me?full=1", body: "payload" },
      { endpoint: "trusted-candidate", method: "GET", path: "/stolen?token=yes", body: "" },
    ]);
    assert.equal(edge.linuxTrust.restartApplication, true);
    assert.equal(edge.linuxTrust.install()[1]?.file, "/usr/sbin/update-ca-certificates");
    assert.equal(edge.linuxTrust.prerequisiteFailures.root, "ENTERPRISE_TLS_LINUX_ROOT_REQUIRED");
    const prerequisites = await edge.linuxTrust.checkPrerequisites();
    if (!prerequisites.ok) {
      assert.ok([
        "ENTERPRISE_TLS_LINUX_ROOT_REQUIRED",
        "ENTERPRISE_TLS_UPDATE_CA_CERTIFICATES_REQUIRED",
      ].includes(prerequisites.failure));
    }
  } finally {
    await edge.stop();
    await Promise.all([close(upstream), close(attacker)]);
  }
  await assert.rejects(access(rootPath));
  await assert.rejects(request(edge.candidateUrl, { ca: edge.rootPem }));
});
