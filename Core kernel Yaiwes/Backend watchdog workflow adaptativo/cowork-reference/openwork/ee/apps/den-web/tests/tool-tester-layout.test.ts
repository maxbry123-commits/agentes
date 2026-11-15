import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { describe, expect, test } from "bun:test";

const screenPath = fileURLToPath(
  new URL("../app/(den)/dashboard/_components/tool-tester/tool-tester-screen.tsx", import.meta.url),
);
const inspectorPath = fileURLToPath(
  new URL("../app/(den)/dashboard/_components/tool-tester/tool-call-inspector.tsx", import.meta.url),
);

describe("Tool Tester layout", () => {
  test("keeps refresh and session-only history guidance visible", () => {
    const screen = readFileSync(screenPath, "utf8");

    expect(screen).toContain("Refresh tools");
    expect(screen).toContain("never stores run results");
  });

  test("keeps request inspection in the extracted inspector", () => {
    const inspector = readFileSync(inspectorPath, "utf8");

    expect(inspector).toContain("Outgoing request");
  });
});
