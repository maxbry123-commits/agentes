import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { describe, it } from "node:test";

const require = createRequire(import.meta.url);
const { normalizeAsarEntryPath } = require("../scripts/electron-after-pack.cjs");

describe("after-pack asar entry paths", () => {
  it("normalizes Windows separators", () => {
    assert.equal(
      normalizeAsarEntryPath("\\node_modules\\@hono\\node-server\\package.json", "\\"),
      "/node_modules/@hono/node-server/package.json",
    );
  });

  it("leaves POSIX separators unchanged", () => {
    assert.equal(
      normalizeAsarEntryPath("/node_modules/@hono/node-server/package.json", "/"),
      "/node_modules/@hono/node-server/package.json",
    );
  });

  it("normalizes nested node_modules paths", () => {
    assert.equal(
      normalizeAsarEntryPath("\\node_modules\\a\\node_modules\\b\\package.json", "\\"),
      "/node_modules/a/node_modules/b/package.json",
    );
  });
});
