import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { X509Certificate } from "node:crypto";
import { mkdtemp, readFile, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { test } from "node:test";

import { createSystemCaCertificateVerifyProc, mergeSystemCaChildEnv, resolveSystemCaEnv } from "./runtime.mjs";
import {
  dedupeCertificates,
  parseDarwinSecurityCertificates,
  parseWindowsPowerShellCertificates,
  resolveSystemCaBundle,
  summarizeSystemCaSources,
} from "./system-ca.mjs";

const CERT_ONE = "-----BEGIN CERTIFICATE-----\none\n-----END CERTIFICATE-----";
const CERT_TWO = "-----BEGIN CERTIFICATE-----\ntwo\n-----END CERTIFICATE-----";
const CERT_THREE = "-----BEGIN CERTIFICATE-----\nthree\n-----END CERTIFICATE-----";

function windowsPowerShellCertBlock(base64) {
  return `-----OPENWORK-CERTIFICATE-----\n${base64}\n-----END-OPENWORK-CERTIFICATE-----`;
}

function pemForBase64(base64) {
  const lines = [];
  for (let index = 0; index < base64.length; index += 64) {
    lines.push(base64.slice(index, index + 64));
  }
  return `-----BEGIN CERTIFICATE-----\n${lines.join("\n")}\n-----END CERTIFICATE-----`;
}

let certificateFixturePromise;

async function certificateFixture() {
  certificateFixturePromise ??= (async () => {
    const directory = await mkdtemp(path.join(tmpdir(), "openwork-runtime-cert-chain-"));
    const run = (...args) => execFileSync("openssl", args, { cwd: directory, stdio: "ignore" });
    run("req", "-x509", "-newkey", "rsa:2048", "-nodes", "-keyout", "root.key", "-out", "root.pem", "-subj", "/CN=OpenWork Test Root", "-days", "2", "-sha256");
    await writeFile(path.join(directory, "server.ext"), "extendedKeyUsage = serverAuth\nsubjectAltName = DNS:enterprise.test\n");
    run("req", "-newkey", "rsa:2048", "-nodes", "-keyout", "leaf.key", "-out", "leaf.csr", "-subj", "/CN=enterprise.test", "-sha256");
    run("x509", "-req", "-in", "leaf.csr", "-CA", "root.pem", "-CAkey", "root.key", "-set_serial", "2", "-out", "leaf.pem", "-days", "1", "-sha256", "-extfile", "server.ext");
    await writeFile(path.join(directory, "client.ext"), "extendedKeyUsage = clientAuth\nsubjectAltName = DNS:enterprise.test\n");
    run("req", "-newkey", "rsa:2048", "-nodes", "-keyout", "client.key", "-out", "client.csr", "-subj", "/CN=enterprise.test", "-sha256");
    run("x509", "-req", "-in", "client.csr", "-CA", "root.pem", "-CAkey", "root.key", "-set_serial", "3", "-out", "client.pem", "-days", "1", "-sha256", "-extfile", "client.ext");
    run("req", "-x509", "-newkey", "rsa:2048", "-nodes", "-keyout", "other.key", "-out", "other.pem", "-subj", "/CN=Unrelated Test Root", "-days", "2", "-sha256");
    return {
      clientLeaf: await readFile(path.join(directory, "client.pem"), "utf8"),
      leaf: await readFile(path.join(directory, "leaf.pem"), "utf8"),
      root: await readFile(path.join(directory, "root.pem"), "utf8"),
      otherRoot: await readFile(path.join(directory, "other.pem"), "utf8"),
    };
  })();
  return certificateFixturePromise;
}

function verifyCertificate(proc, request) {
  return new Promise((resolve) => proc(request, resolve));
}

test("Chromium certificate verification success delegates", async () => {
  const proc = createSystemCaCertificateVerifyProc([]);
  assert.equal(await verifyCertificate(proc, { verificationResult: "net::OK", errorCode: 0 }), -3);
});

test("authority-invalid chain anchored by configured CA is accepted", async () => {
  const fixture = await certificateFixture();
  const keyUsage = new X509Certificate(fixture.leaf).keyUsage;
  assert.ok(keyUsage?.some((usage) => usage === "1.3.6.1.5.5.7.3.1" || /server ?auth/i.test(usage)));
  const proc = createSystemCaCertificateVerifyProc([fixture.root]);
  assert.equal(await verifyCertificate(proc, {
    verificationResult: "net::ERR_CERT_AUTHORITY_INVALID",
    errorCode: -202,
    hostname: "enterprise.test",
    certificate: { data: fixture.leaf },
  }), 0);
});

test("authority-invalid chain with clientAuth-only leaf delegates", async () => {
  const fixture = await certificateFixture();
  const keyUsage = new X509Certificate(fixture.clientLeaf).keyUsage;
  assert.ok(keyUsage?.some((usage) => usage === "1.3.6.1.5.5.7.3.2" || /client ?auth/i.test(usage)));
  assert.ok(!keyUsage.some((usage) => usage === "1.3.6.1.5.5.7.3.1" || /server ?auth/i.test(usage)));
  const proc = createSystemCaCertificateVerifyProc([fixture.root]);
  assert.equal(await verifyCertificate(proc, {
    verificationResult: "net::ERR_CERT_AUTHORITY_INVALID",
    errorCode: -202,
    hostname: "enterprise.test",
    certificate: { data: fixture.clientLeaf },
  }), -3);
});

test("authority-invalid chain with an unrelated root delegates", async () => {
  const fixture = await certificateFixture();
  const proc = createSystemCaCertificateVerifyProc([fixture.otherRoot]);
  assert.equal(await verifyCertificate(proc, {
    verificationResult: "net::ERR_CERT_AUTHORITY_INVALID",
    errorCode: -202,
    hostname: "enterprise.test",
    certificate: { data: fixture.leaf },
  }), -3);
});

test("trusted authority-invalid chain with mismatched or missing hostname delegates", async () => {
  const fixture = await certificateFixture();
  const proc = createSystemCaCertificateVerifyProc([fixture.root]);
  const authorityError = { verificationResult: "net::ERR_CERT_AUTHORITY_INVALID", errorCode: -202 };
  assert.equal(await verifyCertificate(proc, {
    ...authorityError,
    hostname: "different.test",
    certificate: { data: fixture.leaf },
  }), -3);
  assert.equal(await verifyCertificate(proc, {
    ...authorityError,
    certificate: { data: fixture.leaf },
  }), -3);
});

test("non-authority certificate errors delegate to Chromium", async () => {
  const fixture = await certificateFixture();
  const proc = createSystemCaCertificateVerifyProc([fixture.root]);
  assert.equal(await verifyCertificate(proc, {
    verificationResult: "net::ERR_CERT_DATE_INVALID",
    errorCode: -201,
    certificate: { data: fixture.leaf },
  }), -3);
  assert.equal(await verifyCertificate(proc, {
    verificationResult: "net::ERR_CERT_AUTHORITY_INVALID",
    errorCode: -201,
    certificate: { data: fixture.leaf },
  }), -3);
});

test("malformed and cyclic certificate chains never accept", async () => {
  const fixture = await certificateFixture();
  const proc = createSystemCaCertificateVerifyProc([fixture.root]);
  const cyclic = { data: fixture.leaf };
  cyclic.issuerCert = cyclic;
  const authorityError = { verificationResult: "net::ERR_CERT_AUTHORITY_INVALID", errorCode: -202, hostname: "enterprise.test" };
  assert.equal(await verifyCertificate(proc, { ...authorityError, certificate: { data: "not a certificate" } }), -3);
  assert.equal(await verifyCertificate(proc, { ...authorityError, certificate: cyclic }), -3);
});

test("writes system CA bundle when certificates are available", async () => {
  const userDataDir = await mkdtemp(path.join(tmpdir(), "openwork-runtime-ca-"));
  const bundlePath = path.join(userDataDir, "system-ca-bundle.pem");

  const env = await resolveSystemCaEnv({
    tlsModule: {
      getCACertificates(scope) {
        assert.equal(scope, "system");
        return [CERT_ONE, CERT_TWO];
      },
    },
    userDataDir,
    parentEnv: {},
    logInfo: () => {},
    loadPlatformCertificates: async () => [],
  });

  assert.deepEqual(env, { NODE_EXTRA_CA_CERTS: bundlePath });
  assert.equal(await readFile(bundlePath, "utf8"), `${CERT_ONE}\n${CERT_TWO}\n`);
});

test("sets NODE_EXTRA_CA_CERTS for a child env merge", async () => {
  const userDataDir = await mkdtemp(path.join(tmpdir(), "openwork-runtime-ca-"));
  const caEnv = await resolveSystemCaEnv({
    tlsModule: { getCACertificates: () => [CERT_ONE] },
    userDataDir,
    parentEnv: {},
    logInfo: () => {},
    loadPlatformCertificates: async () => [],
  });
  /** @type {NodeJS.ProcessEnv} */
  const childEnv = { PATH: "/bin", ...caEnv };

  assert.equal(childEnv.NODE_EXTRA_CA_CERTS, path.join(userDataDir, "system-ca-bundle.pem"));
});

test("keeps NODE_EXTRA_CA_CERTS from user env file over generated bundle", () => {
  const userEnvFile = { NODE_EXTRA_CA_CERTS: "/user/file-ca.pem" };
  const processEnv = {};
  const baseEnv = {
    ...userEnvFile,
    ...processEnv,
    BUN_CONFIG_DNS_RESULT_ORDER: "verbatim",
  };
  const childEnv = mergeSystemCaChildEnv(baseEnv, { NODE_EXTRA_CA_CERTS: "/generated/system-ca-bundle.pem" });

  assert.equal(childEnv.NODE_EXTRA_CA_CERTS, "/user/file-ca.pem");
});

test("respects user-set NODE_EXTRA_CA_CERTS", async () => {
  const userDataDir = await mkdtemp(path.join(tmpdir(), "openwork-runtime-ca-"));
  let called = false;
  let logged = false;

  const env = await resolveSystemCaEnv({
    tlsModule: {
      getCACertificates() {
        called = true;
        return [CERT_ONE];
      },
    },
    userDataDir,
    parentEnv: { NODE_EXTRA_CA_CERTS: "/custom/ca.pem" },
    logInfo(message) {
      logged = String(message).includes("NODE_EXTRA_CA_CERTS is already set");
    },
    loadPlatformCertificates: async () => {
      called = true;
      return [CERT_TWO];
    },
  });

  assert.deepEqual(env, {});
  assert.equal(called, false);
  assert.equal(logged, true);
});

test("no-ops when tls.getCACertificates is unavailable", async () => {
  const userDataDir = await mkdtemp(path.join(tmpdir(), "openwork-runtime-ca-"));

  const env = await resolveSystemCaEnv({
    tlsModule: {},
    userDataDir,
    parentEnv: {},
    logInfo: () => {},
    loadPlatformCertificates: async () => [],
  });

  assert.deepEqual(env, {});
  await assert.rejects(readFile(path.join(userDataDir, "system-ca-bundle.pem"), "utf8"));
});

test("incident case: macOS runtime returns no certs but platform keychains produce a bundle", async () => {
  const userDataDir = await mkdtemp(path.join(tmpdir(), "openwork-runtime-ca-"));
  const bundlePath = path.join(userDataDir, "system-ca-bundle.pem");
  const logs = [];
  const setDefaultCalls = [];

  const env = await resolveSystemCaEnv({
    tlsModule: {
      getCACertificates(scope) {
        if (scope === "default") return ["default-root"];
        assert.equal(scope, "system");
        return [];
      },
      setDefaultCACertificates(certs) {
        setDefaultCalls.push(certs);
      },
    },
    userDataDir,
    parentEnv: {},
    logInfo(message) {
      logs.push(String(message));
    },
    loadPlatformCertificates: async () => [CERT_ONE, CERT_TWO],
    platformSourceName: "macos-keychains",
  });

  assert.deepEqual(env, { NODE_EXTRA_CA_CERTS: bundlePath });
  assert.equal(await readFile(bundlePath, "utf8"), `${CERT_ONE}\n${CERT_TWO}\n`);
  assert.deepEqual(setDefaultCalls, [["default-root", CERT_ONE, CERT_TWO]]);
  assert.ok(logs.some((line) => line.includes("runtime=0 macos-keychains=2")));
});

test("dedupes certificates across runtime and platform sources", async () => {
  const userDataDir = await mkdtemp(path.join(tmpdir(), "openwork-runtime-ca-"));
  const bundlePath = path.join(userDataDir, "system-ca-bundle.pem");

  const env = await resolveSystemCaEnv({
    tlsModule: { getCACertificates: () => [CERT_ONE, CERT_TWO] },
    userDataDir,
    parentEnv: {},
    logInfo: () => {},
    loadPlatformCertificates: async () => [CERT_TWO, CERT_THREE, CERT_ONE],
    platformSourceName: "windows-cert-stores",
  });

  assert.deepEqual(env, { NODE_EXTRA_CA_CERTS: bundlePath });
  assert.equal(await readFile(bundlePath, "utf8"), `${CERT_ONE}\n${CERT_TWO}\n${CERT_THREE}\n`);
});

test("does not set main-process defaults when no additions are available", async () => {
  const userDataDir = await mkdtemp(path.join(tmpdir(), "openwork-runtime-ca-"));
  let setDefaultCalled = false;

  const env = await resolveSystemCaEnv({
    tlsModule: {
      getCACertificates: () => [],
      setDefaultCACertificates() {
        setDefaultCalled = true;
      },
    },
    userDataDir,
    parentEnv: {},
    logInfo: () => {},
    loadPlatformCertificates: async () => [],
  });

  assert.deepEqual(env, {});
  assert.equal(setDefaultCalled, false);
});

test("main-process default extension is optional", async () => {
  const userDataDir = await mkdtemp(path.join(tmpdir(), "openwork-runtime-ca-"));
  const bundlePath = path.join(userDataDir, "system-ca-bundle.pem");

  const env = await resolveSystemCaEnv({
    tlsModule: { getCACertificates: () => [CERT_ONE] },
    userDataDir,
    parentEnv: {},
    logInfo: () => {},
    loadPlatformCertificates: async () => [],
  });

  assert.deepEqual(env, { NODE_EXTRA_CA_CERTS: bundlePath });
});

test("system CA bundle resolver keeps platform sources additive and reports counts", async () => {
  const bundle = await resolveSystemCaBundle({
    runtime: () => [CERT_ONE],
    platform: { name: "macos-keychains", load: async () => [CERT_ONE, CERT_TWO] },
  });

  assert.deepEqual(bundle.certificates, [CERT_ONE, CERT_TWO]);
  assert.equal(summarizeSystemCaSources(bundle.sources), "runtime=1 macos-keychains=2");
});

test("system CA bundle resolver keeps other sources when platform enumeration fails", async () => {
  const bundle = await resolveSystemCaBundle({
    runtime: () => [CERT_ONE],
    platform: {
      name: "windows-cert-stores",
      load: async () => {
        throw new Error("powershell blocked by policy");
      },
    },
  });

  assert.deepEqual(bundle.certificates, [CERT_ONE]);
  assert.equal(summarizeSystemCaSources(bundle.sources), "runtime=1 windows-cert-stores=0");
});

test("parses and dedupes windows PowerShell certificate output", () => {
  const first = Buffer.from("first certificate with enough bytes to require PEM wrapping across more than one output line").toString("base64");
  const second = Buffer.from("second certificate").toString("base64");
  const output = [
    windowsPowerShellCertBlock(first),
    "noise",
    windowsPowerShellCertBlock(second),
    windowsPowerShellCertBlock("not-valid-base64"),
    windowsPowerShellCertBlock(first),
  ].join("\n");

  assert.deepEqual(parseWindowsPowerShellCertificates(output), [pemForBase64(first), pemForBase64(second)]);
});

test("parses darwin security PEM output", () => {
  const output = `noise\n${CERT_ONE}\nmore noise\n${CERT_TWO}\n${CERT_ONE}\n`;

  assert.deepEqual(parseDarwinSecurityCertificates(output), [CERT_ONE, CERT_TWO]);
});

test("ignores garbage certificate command output", () => {
  assert.deepEqual(parseDarwinSecurityCertificates("not certificate output"), []);
  assert.deepEqual(parseWindowsPowerShellCertificates("not certificate output"), []);
  assert.deepEqual(dedupeCertificates(["", "  ", CERT_ONE, CERT_ONE]), [CERT_ONE]);
});
