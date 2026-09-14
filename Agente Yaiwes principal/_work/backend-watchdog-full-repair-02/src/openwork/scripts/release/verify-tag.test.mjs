import assert from "node:assert/strict";
import { test } from "node:test";
import { verifyReleaseTag } from "./verify-tag.mjs";

const tags = ["v0.18.21", "v0.18.22", "v0.18.23", "v0.17.0", "alpha-macos-latest", "vffe6fee-dev"];

test("fresh tags must be strictly greater than every other stable tag", () => {
  const ok = verifyReleaseTag({ tag: "v0.18.24", mode: "fresh", tags });
  assert.equal(ok.ok, true);
  assert.equal(ok.version, "0.18.24");

  // The tag under verification is excluded from the comparison set: in CI the
  // clone already contains the tag this run just created, so the newest tag
  // verifies fresh against all the others.
  const newest = verifyReleaseTag({ tag: "v0.18.23", mode: "fresh", tags });
  assert.equal(newest.ok, true);

  const lower = verifyReleaseTag({ tag: "v0.18.22", mode: "fresh", tags });
  assert.equal(lower.ok, false);
  assert.match(lower.problems[0], /greater than the highest existing stable tag v0\.18\.23/);
});

test("a fresh tag not present in the tag list yet verifies against the rest", () => {
  const result = verifyReleaseTag({ tag: "v0.19.0", mode: "fresh", tags });
  assert.equal(result.ok, true);
});

test("recovery mode reruns an existing tag without monotonicity", () => {
  const result = verifyReleaseTag({ tag: "v0.18.22", mode: "recovery", tags });
  assert.equal(result.ok, true);
  assert.equal(result.version, "0.18.22");
});

test("non-stable tags are rejected in every mode", () => {
  for (const tag of ["v0.18.24-alpha.1", "0.18.24", "vffe6fee-dev", "", "v1.2"]) {
    const fresh = verifyReleaseTag({ tag, mode: "fresh", tags });
    assert.equal(fresh.ok, false, `expected ${tag} to fail`);
    const recovery = verifyReleaseTag({ tag, mode: "recovery", tags });
    assert.equal(recovery.ok, false, `expected ${tag} to fail`);
  }
});

test("unknown modes fail", () => {
  const result = verifyReleaseTag({ tag: "v0.19.0", mode: "yolo", tags });
  assert.equal(result.ok, false);
  assert.match(result.problems[0], /Unknown verify mode/);
});
