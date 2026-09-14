#!/usr/bin/env node
// Layer 1 (unit) + Layer 2 (hang fuzz) for the runtime preflight. Feeds every check a mocked env that exercises happy path + every production failure mode (broken DNS, locked dir, garbage Get-MpComputerStatus output, OS=unknown, arch=mips64) and asserts the right verdict plus never-throws-past-the-wrapper. Layer 2 wires a never-resolving fake into network/spawn checks and asserts the wrapper times out within timeoutMs+200ms with status='warn' not 'fail'. Pure Node, no app deps, runs in under 1s.

'use strict';
const pf = require('../../electron/preflight');

let failed = 0;
function check(name, cond) { process.stdout.write(`  ${cond ? 'ok  ' : 'FAIL'}  ${name}\n`); if (!cond) failed++; }
async function asyncCheck(name, fn) { try { check(name, await fn()); } catch (e) { check(`${name} (threw: ${String((e && e.message) || e)})`, false); } }

// ---- mock env factory ----
function mkEnv(over = {}) {
  return {
    fs: {
      readFileSync: (p) => { if (over.fsReadFileSync) return over.fsReadFileSync(p); throw new Error('mock no-file'); },
      writeFileSync: (p, v) => { if (over.fsWrite) return over.fsWrite(p, v); },
      unlinkSync: () => {},
      mkdirSync: () => {},
      readdirSync: () => over.fsReaddir || [],
      statfsSync: over.statfsSync || (() => ({ bavail: BigInt(10_000_000), bsize: BigInt(4096) })),
    },
    child_process: { execFile: over.execFile || ((cmd, args, opts, cb) => setImmediate(() => cb(null, 'mock-stdout', ''))) },
    dns: { lookup: over.dnsLookup || ((host, opts, cb) => setImmediate(() => cb(null, '1.2.3.4'))) },
    http: require('http'),
    https: over.https || {
      get: () => ({ on: () => {}, setTimeout: (ms, cb) => setTimeout(cb, ms) }),
      request: () => ({ on: () => {}, setTimeout: (ms, cb) => setTimeout(cb, ms), end: () => {} }),
    },
    os: {
      release: over.osRelease || (() => '10.0.22000'),
      totalmem: over.totalmem || (() => 16 * 1024 ** 3),
      freemem: over.freemem || (() => 8 * 1024 ** 3),
      cpus: over.cpus || (() => Array(8).fill({})),
      homedir: () => '/tmp',
    },
    now: over.now || (() => Date.now()),
    platform: over.platform || 'linux',
    arch: over.arch || 'x64',
  };
}

async function main() {
  // ===== Layer 1: branch coverage on each check =====
  process.stdout.write('Layer 1 - checkOs branches:\n');
  await asyncCheck('linux/x64 -> ok', async () => (await pf.checkOs(mkEnv())).status === 'ok');
  await asyncCheck('darwin/arm64 -> ok', async () => (await pf.checkOs(mkEnv({ platform: 'darwin', arch: 'arm64', osRelease: () => '23.4.0' }))).status === 'ok');
  await asyncCheck('darwin old (12) -> warn', async () => (await pf.checkOs(mkEnv({ platform: 'darwin', osRelease: () => '21.0.0' }))).status === 'warn');
  await asyncCheck('windows < 10 -> fail', async () => (await pf.checkOs(mkEnv({ platform: 'win32', osRelease: () => '6.1.7601' }))).status === 'fail');
  await asyncCheck('unknown platform -> fail', async () => (await pf.checkOs(mkEnv({ platform: 'sunos' }))).status === 'fail');
  await asyncCheck('mips64 arch -> fail', async () => (await pf.checkOs(mkEnv({ arch: 'mips64' }))).status === 'fail');

  process.stdout.write('\nLayer 1 - checkResources branches:\n');
  await asyncCheck('healthy 16GB/8cpu -> ok', async () => (await pf.checkResources(mkEnv())).status === 'ok');
  await asyncCheck('< 4GB ram -> warn', async () => (await pf.checkResources(mkEnv({ totalmem: () => 2 * 1024 ** 3 }))).status === 'warn');
  await asyncCheck('1 cpu -> warn', async () => (await pf.checkResources(mkEnv({ cpus: () => [{}] }))).status === 'warn');
  await asyncCheck('statfs throws -> warn', async () => (await pf.checkResources(mkEnv({ statfsSync: () => { throw new Error('boom'); } }))).status === 'warn');
  await asyncCheck('os api throws -> warn', async () => (await pf.checkResources(mkEnv({ totalmem: () => { throw new Error('boom'); } }))).status === 'warn');
  await asyncCheck('low disk -> warn', async () => (await pf.checkResources(mkEnv({ statfsSync: () => ({ bavail: BigInt(1000), bsize: BigInt(4096) }) }))).status === 'warn');

  process.stdout.write('\nLayer 1 - checkAppdataWritable branches:\n');
  await asyncCheck('happy path -> ok', async () => (await pf.checkAppdataWritable(mkEnv(), '/tmp/x')).status === 'ok');
  await asyncCheck('no dataDir -> warn', async () => (await pf.checkAppdataWritable(mkEnv(), null)).status === 'warn');
  await asyncCheck('write throws -> fail', async () => (await pf.checkAppdataWritable(mkEnv({ fsWrite: () => { throw new Error('EACCES'); } }), '/locked')).status === 'fail');

  process.stdout.write('\nLayer 1 - checkSecurityBlock branches:\n');
  await asyncCheck('darwin clean -> ok', async () => (await pf.checkSecurityBlock(mkEnv({ platform: 'darwin' }))).status === 'ok');
  await asyncCheck('darwin quarantined -> warn', async () => {
    const env = mkEnv({ platform: 'darwin', execFile: (cmd, args, opts, cb) => setImmediate(() => cb(null, 'com.apple.quarantine:0083;...', '')) });
    return (await pf.checkSecurityBlock(env)).status === 'warn';
  });
  await asyncCheck('darwin xattr fails -> warn', async () => {
    const env = mkEnv({ platform: 'darwin', execFile: (cmd, args, opts, cb) => setImmediate(() => cb(new Error('not found'), '', '')) });
    return (await pf.checkSecurityBlock(env)).status === 'warn';
  });
  await asyncCheck('win pwsh works -> ok', async () => (await pf.checkSecurityBlock(mkEnv({ platform: 'win32' }))).status === 'ok');
  await asyncCheck('win pwsh fails -> warn', async () => {
    const env = mkEnv({ platform: 'win32', execFile: (cmd, args, opts, cb) => setImmediate(() => cb(new Error('access denied'), '', '')) });
    return (await pf.checkSecurityBlock(env)).status === 'warn';
  });
  await asyncCheck('win pwsh localized garbage -> still ok (we just record the value)', async () => {
    const env = mkEnv({ platform: 'win32', execFile: (cmd, args, opts, cb) => setImmediate(() => cb(null, 'Zugriff verweigert', '')) });
    return (await pf.checkSecurityBlock(env)).status === 'ok';
  });
  await asyncCheck('linux -> ok (no os gate)', async () => (await pf.checkSecurityBlock(mkEnv())).status === 'ok');

  process.stdout.write('\nLayer 1 - checkDualStack branches:\n');
  await asyncCheck('both v4 and v6 resolve -> ok', async () => {
    const env = mkEnv({ dnsLookup: (host, opts, cb) => setImmediate(() => cb(null, opts.family === 4 ? '1.2.3.4' : '::1')) });
    return (await pf.checkDualStack(env)).status === 'ok';
  });
  await asyncCheck('only v4 resolves -> ok', async () => {
    const env = mkEnv({ dnsLookup: (host, opts, cb) => setImmediate(() => cb(opts.family === 6 ? new Error('nxdomain') : null, opts.family === 4 ? '1.2.3.4' : null)) });
    return (await pf.checkDualStack(env)).status === 'ok';
  });
  await asyncCheck('neither resolves -> warn', async () => {
    const env = mkEnv({ dnsLookup: (host, opts, cb) => setImmediate(() => cb(new Error('nxdomain'), null)) });
    return (await pf.checkDualStack(env)).status === 'warn';
  });
  await asyncCheck('dns module throws -> warn (caught by per-lookup try)', async () => {
    const env = mkEnv({ dnsLookup: () => { throw new Error('boom'); } });
    return (await pf.checkDualStack(env)).status === 'warn';
  });

  // ===== Layer 2: hang fuzz =====
  process.stdout.write('\nLayer 2 - hang fuzz (never-resolving deps must timeout to warn, not fail):\n');
  const hangingHttps = { get: () => ({ on: () => {}, setTimeout: () => {} }), request: () => ({ on: () => {}, setTimeout: () => {}, end: () => {} }) };
  await asyncCheck('checkNetwork w/ hung https -> warn within 350ms', async () => {
    const t0 = Date.now();
    const env = mkEnv({ https: hangingHttps });
    const w = await pf.withTimeout('network', () => pf.checkNetwork(env, { timeoutMs: 50_000 }), 200);
    const dt = Date.now() - t0;
    return w.status === 'warn' && dt < 350;
  });
  await asyncCheck('checkClock w/ hung https -> warn within 350ms', async () => {
    const t0 = Date.now();
    const env = mkEnv({ https: hangingHttps });
    const w = await pf.withTimeout('clock', () => pf.checkClock(env, { timeoutMs: 50_000 }), 200);
    return w.status === 'warn' && (Date.now() - t0) < 350;
  });
  await asyncCheck('checkSecurityBlock w/ hung execFile -> warn within 350ms', async () => {
    const t0 = Date.now();
    const env = mkEnv({ platform: 'win32', execFile: () => { /* never calls cb */ } });
    const w = await pf.withTimeout('security', () => pf.checkSecurityBlock(env), 200);
    return w.status === 'warn' && (Date.now() - t0) < 350;
  });
  await asyncCheck('checkDualStack w/ hung dns -> warn within 350ms', async () => {
    const t0 = Date.now();
    const env = mkEnv({ dnsLookup: () => { /* never resolves */ } });
    const w = await pf.withTimeout('dual-stack', () => pf.checkDualStack(env, { timeoutMs: 50_000 }), 200);
    return w.status === 'warn' && (Date.now() - t0) < 350;
  });
  await asyncCheck('withTimeout: a sync throw inside the fn becomes warn, not crash', async () => {
    const w = await pf.withTimeout('explode', async () => { throw new Error('synthetic'); }, 500);
    return w.status === 'warn' && /threw|synthetic/.test(w.reason);
  });
  await asyncCheck('withTimeout: a returned null becomes warn (never undefined)', async () => {
    const w = await pf.withTimeout('null-result', async () => null, 500);
    return w.status === 'warn';
  });

  // ===== Layer 1 - cache =====
  process.stdout.write('\nLayer 1 - cache + prune branches:\n');
  await asyncCheck('readCache returns null on no file', async () => pf.readCache(mkEnv(), '/tmp', '1.0.0') === null);
  await asyncCheck('readCache returns null on version mismatch', async () => {
    const env = mkEnv({ fsReadFileSync: () => JSON.stringify({ appVersion: '0.9.0', verdict: 'ok' }) });
    return pf.readCache(env, '/tmp', '1.0.0') === null;
  });
  await asyncCheck('readCache returns null on verdict != ok', async () => {
    const env = mkEnv({ fsReadFileSync: () => JSON.stringify({ appVersion: '1.0.0', verdict: 'fail' }) });
    return pf.readCache(env, '/tmp', '1.0.0') === null;
  });
  await asyncCheck('readCache returns payload on match', async () => {
    const env = mkEnv({ fsReadFileSync: () => JSON.stringify({ appVersion: '1.0.0', verdict: 'ok' }) });
    const got = pf.readCache(env, '/tmp', '1.0.0');
    return got && got.verdict === 'ok';
  });
  await asyncCheck('pruneOldCaches deletes off-version files', async () => {
    let deleted = [];
    const env = mkEnv({ fsReaddir: ['preflight-1.0.0.json', 'preflight-0.9.0.json', 'other.json'] });
    env.fs.unlinkSync = (p) => deleted.push(p);
    pf.pruneOldCaches(env, '/tmp', '1.0.0');
    return deleted.length === 1 && /0\.9\.0/.test(deleted[0]);
  });

  process.stdout.write(failed
    ? `\nPREFLIGHT SELFTEST FAIL: ${failed} assertion(s) failed.\n`
    : '\nPREFLIGHT SELFTEST PASS: every check discriminates and every hang resolves to warn within budget.\n');
  process.exit(failed ? 1 : 0);
}

main().catch((e) => { process.stderr.write(`\nPREFLIGHT SELFTEST FAIL: ${e && e.stack || e}\n`); process.exit(1); });
