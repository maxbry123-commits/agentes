import assert from "node:assert/strict";
import test from "node:test";

import {
  resolveOpenworkSentryAppVersion,
  resolveOpenworkSentryRelease,
} from "./sentry.mjs";

test("unpackaged Sentry release uses the desktop package version", () => {
  const appVersion = resolveOpenworkSentryAppVersion({
    app: { isPackaged: false, getVersion: () => "43.2.0" },
    packageMetadata: { version: "0.18.7" },
  });

  assert.equal(appVersion, "0.18.7");
  assert.equal(
    resolveOpenworkSentryRelease({ appVersion, environmentRelease: "" }),
    "openwork-desktop@0.18.7",
  );
});

test("packaged Sentry release uses Electron's stamped app version", () => {
  const appVersion = resolveOpenworkSentryAppVersion({
    app: { isPackaged: true, getVersion: () => "0.18.8" },
    packageMetadata: { version: "0.18.7" },
  });

  assert.equal(appVersion, "0.18.8");
  assert.equal(
    resolveOpenworkSentryRelease({ appVersion, environmentRelease: "" }),
    "openwork-desktop@0.18.8",
  );
});

test("Sentry release still honors an explicit build override", () => {
  assert.equal(
    resolveOpenworkSentryRelease({
      appVersion: "0.18.8",
      environmentRelease: "desktop-main@abcdef",
    }),
    "desktop-main@abcdef",
  );
});
