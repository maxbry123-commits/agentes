import assert from "node:assert/strict";
import { test } from "node:test";
import {
  buildRollbackBody,
  buildRollbackPlan,
  resolveRollback,
  runRollback,
  selectRollbackTarget,
} from "./rollback.mjs";

const release = (id, tag, options = {}) => ({
  id,
  tag_name: tag,
  draft: false,
  prerelease: false,
  body: `Notes for ${tag}`,
  assets: [{ name: "latest-mac.yml" }],
  ...options,
});

const releases = [
  release(1, "v1.2.5"),
  release(2, "v1.2.2"),
  release(3, "v1.2.1"),
  release(4, "v1.2.4", { draft: true }),
  release(5, "v1.2.3", { prerelease: true }),
  release(6, "alpha-macos-latest", { prerelease: true }),
];

function fakeGh(releaseList, latestTag) {
  const calls = [];
  const gh = (args) => {
    calls.push(args);
    if (args.includes("--paginate")) return JSON.stringify([releaseList]);
    if (args.join(" ") === "api repos/different-ai/openwork/releases/latest") {
      return JSON.stringify(releaseList.find((item) => item.tag_name === latestTag));
    }
    return "";
  };
  return { calls, gh };
}

test("selects the highest published stable semver below the bad release", () => {
  assert.equal(selectRollbackTarget(releases, "v1.2.5").tag_name, "v1.2.2");
});

test("validates an explicit target", () => {
  assert.equal(resolveRollback(releases, "v1.2.5", "v1.2.1").target.tag_name, "v1.2.1");
});

test("refuses targets that are not lower, stable, published releases", () => {
  assert.throws(
    () => resolveRollback(releases, "v1.2.5", "v1.2.5"),
    /must differ/,
  );
  assert.throws(
    () => resolveRollback(releases, "v1.2.5", "v1.2.4"),
    /draft/,
  );
  assert.throws(
    () => resolveRollback(releases, "v1.2.5", "v1.2.3"),
    /prerelease/,
  );
  assert.throws(
    () => resolveRollback(releases, "v1.2.5", "v9.9.9"),
    /Target release not found/,
  );
  assert.throws(
    () => resolveRollback(releases, "v1.2.2", "v1.2.5"),
    /must be lower/,
  );
});

test("dry-run builds the full plan without mutation", () => {
  const fake = fakeGh(releases, "v1.2.5");
  const originalLog = console.log;
  console.log = () => {};
  try {
    const result = runRollback([], {
      gh: fake.gh,
      now: new Date("2026-08-10T12:00:00Z"),
    });
    assert.equal(result.execute, false);
    assert.equal(result.plan.length, 3);
    assert.equal(fake.calls.length, 2);
  } finally {
    console.log = originalLog;
  }
});

test("execute runs the three mutating plan steps in order", () => {
  const fake = fakeGh(releases, "v1.2.5");
  const originalLog = console.log;
  console.log = () => {};
  try {
    runRollback(["--execute"], {
      gh: fake.gh,
      now: new Date("2026-08-10T12:00:00Z"),
    });
  } finally {
    console.log = originalLog;
  }

  assert.deepEqual(fake.calls.slice(2).map((args) => args.slice(0, 3)), [
    ["release", "edit", "v1.2.2"],
    ["release", "edit", "v1.2.5"],
    ["api", "--method", "PATCH"],
  ]);
});

test("idempotent plan skips completed steps", () => {
  const body = "> ⚠️ Rolled back on 2026-08-10. Do not install; use v1.2.4 instead.\n\nOld notes";
  const plan = buildRollbackPlan({
    bad: release(1, "v1.2.5", { prerelease: true, body }),
    target: release(2, "v1.2.4"),
    latestTag: "v1.2.4",
    now: new Date("2026-08-11T12:00:00Z"),
  });
  assert.deepEqual(plan.map((step) => step.skip), [true, true, true]);
});

test("keep-bad-listed skips only the demotion", () => {
  const plan = buildRollbackPlan({
    bad: release(1, "v1.2.5"),
    target: release(2, "v1.2.4"),
    latestTag: "v1.2.5",
    keepBadListed: true,
  });
  assert.deepEqual(plan.map((step) => step.skip), [false, true, false]);
});

test("prepends a dated banner while preserving the existing body", () => {
  assert.equal(
    buildRollbackBody("Existing notes", "v1.2.4", new Date("2026-08-10T12:00:00Z")),
    "> ⚠️ Rolled back on 2026-08-10. Do not install; use v1.2.4 instead.\n\nExisting notes",
  );
});
