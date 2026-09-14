import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { describe, expect, test } from "bun:test";

const uiPath = (file: string) =>
  fileURLToPath(new URL(`../app/(den)/_components/ui/${file}`, import.meta.url));

describe("Den UI primitives", () => {
  test("include switch, segmented, and danger badge contracts", () => {
    const switchSource = readFileSync(uiPath("switch.tsx"), "utf8");
    const segmentedSource = readFileSync(uiPath("segmented.tsx"), "utf8");
    const badgeSource = readFileSync(uiPath("badge.tsx"), "utf8");

    expect(switchSource).toContain('role="switch"');
    expect(switchSource).toContain('"h-6 w-10"');
    expect(switchSource).toContain('"h-5 w-9"');
    expect(switchSource).toContain('"h-5 w-5"');
    expect(switchSource).toContain('"h-4 w-4"');
    expect(segmentedSource).toContain('role="radiogroup"');
    expect(badgeSource).toContain("danger");
  });
});
