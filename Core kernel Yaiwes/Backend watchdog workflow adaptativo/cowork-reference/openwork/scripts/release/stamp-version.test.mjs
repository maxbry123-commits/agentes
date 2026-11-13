import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";
import { STAMPED_PACKAGE_PATHS, normalizeStampVersion, stampVersion } from "./stamp-version.mjs";

function makeFakeRoot() {
  const root = mkdtempSync(join(tmpdir(), "stamp-version-"));
  for (const relativePath of STAMPED_PACKAGE_PATHS) {
    const packagePath = join(root, relativePath);
    mkdirSync(join(packagePath, ".."), { recursive: true });
    writeFileSync(packagePath, `${JSON.stringify({ name: relativePath, version: "0.0.0-dev" }, null, 2)}\n`);
  }
  return root;
}

test("stamps a stable version into all three package.json files", () => {
  const root = makeFakeRoot();
  const result = stampVersion("0.19.0", root);
  assert.equal(result.version, "0.19.0");
  for (const relativePath of STAMPED_PACKAGE_PATHS) {
    const json = JSON.parse(readFileSync(join(root, relativePath), "utf8"));
    assert.equal(json.version, "0.19.0");
  }
});

test("accepts v-prefixed tags and alpha prerelease versions", () => {
  assert.equal(normalizeStampVersion("v0.19.0"), "0.19.0");
  assert.equal(normalizeStampVersion("0.18.24-alpha.412+abc1234"), "0.18.24-alpha.412+abc1234");
});

test("rejects garbage versions", () => {
  for (const bad of ["", "dev", "v1.2", "0.19", "0..1"]) {
    assert.throws(() => normalizeStampVersion(bad), /Invalid version to stamp/, `expected ${JSON.stringify(bad)} to throw`);
  }
});
