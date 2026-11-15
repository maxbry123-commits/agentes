import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { expect, test } from "bun:test";

const sessionPagePath = fileURLToPath(
  new URL("../src/react-app/domains/session/chat/session-page.tsx", import.meta.url),
);

test("hidden Cloud sign-in does not reserve header space", () => {
  const source = readFileSync(sessionPagePath, "utf8");

  expect(source).toContain("{showCloudSignIn ? (");
  expect(source).not.toContain('className={showCloudSignIn ? undefined : "invisible"}');
  expect(source).not.toContain("disabled={!showCloudSignIn}");
});
