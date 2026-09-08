import { describe, expect, test } from "bun:test";

import { signedInRoute } from "../src/react-app/shell/den-signin-routing";

describe("signed-in routing", () => {
  test("sends organization members directly to chat", () => {
    expect(signedInRoute("org-returning")).toBe("/session");
    expect(signedInRoute("  org-returning  ")).toBe("/session");
  });

  test("reserves onboarding for users without an organization", () => {
    expect(signedInRoute(null)).toBe("/onboarding");
    expect(signedInRoute("  ")).toBe("/onboarding");
  });

  test("routes to onboarding while an org selection is deliberately pending", () => {
    expect(signedInRoute(null, { orgSelectionPending: true })).toBe("/onboarding");
    // Pending wins even if a background layer already wrote a default org id.
    expect(signedInRoute("org-default", { orgSelectionPending: true })).toBe("/onboarding");
    expect(signedInRoute("org-default", { orgSelectionPending: false })).toBe("/session");
  });
});
