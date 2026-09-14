import { describe, expect, test } from "bun:test";

import {
  EFFORT_LABELS,
  presetEffort,
} from "../app/(den)/dashboard/_components/connector-effort";

describe("connector effort", () => {
  test("maps preset authentication requirements to setup effort", () => {
    expect(presetEffort({ authType: "none" })).toBe("instant");
    expect(presetEffort({ authType: "apikey" })).toBe("api_key");
    expect(presetEffort({ authType: "oauth", requiresOAuthClient: true })).toBe("oauth_app");
    expect(presetEffort({ authType: "oauth" })).toBe("one_click");
  });

  test("provides a label for every effort level", () => {
    expect(EFFORT_LABELS).toEqual({
      guided: "Guided setup",
      one_click: "One-click",
      api_key: "API key",
      oauth_app: "OAuth app required",
      instant: "Instant — no sign-in",
    });
  });
});
