import { afterEach, describe, expect, test } from "bun:test";

import {
  DESKTOP_SIGN_IN_INTENT_TTL_MS,
  clearOrgSelectionPending,
  hasActiveDesktopSignInIntent,
  isDesktopSignInIntentActive,
  markDesktopSignInInitiated,
  markOrgSelectionPending,
  readOrgSelectionPending,
  resolveHandoffOrgPlan,
} from "../src/app/lib/den-sign-in-intent";

const originalWindow = globalThis.window;

function memoryStorage(): Storage {
  const map = new Map<string, string>();
  return {
    get length() {
      return map.size;
    },
    clear() {
      map.clear();
    },
    getItem(key: string) {
      return map.get(key) ?? null;
    },
    key(index: number) {
      return Array.from(map.keys())[index] ?? null;
    },
    removeItem(key: string) {
      map.delete(key);
    },
    setItem(key: string, value: string) {
      map.set(key, value);
    },
  };
}

function stubWindow() {
  Object.defineProperty(globalThis, "window", {
    configurable: true,
    value: {
      localStorage: memoryStorage(),
      dispatchEvent: () => true,
    },
  });
}

afterEach(() => {
  Object.defineProperty(globalThis, "window", {
    configurable: true,
    value: originalWindow,
  });
});

describe("desktop sign-in intent marker", () => {
  test("is active within the TTL and expires after it", () => {
    stubWindow();
    markDesktopSignInInitiated(1_000);

    expect(hasActiveDesktopSignInIntent(1_000)).toBe(true);
    expect(hasActiveDesktopSignInIntent(1_000 + DESKTOP_SIGN_IN_INTENT_TTL_MS)).toBe(true);
    expect(hasActiveDesktopSignInIntent(1_000 + DESKTOP_SIGN_IN_INTENT_TTL_MS + 1)).toBe(false);
  });

  test("is inactive without a marker or with a malformed one", () => {
    expect(isDesktopSignInIntentActive(null, 1_000)).toBe(false);
    expect(isDesktopSignInIntentActive("not-a-number", 1_000)).toBe(false);
  });
});

describe("pending organization selection state", () => {
  test("round-trips the suggestion and clears completely", () => {
    stubWindow();
    markOrgSelectionPending({ id: "org_a", slug: "org-a", name: "Org A" });

    expect(readOrgSelectionPending()).toEqual({
      pending: true,
      suggestion: { id: "org_a", slug: "org-a", name: "Org A" },
    });

    clearOrgSelectionPending();
    expect(readOrgSelectionPending()).toEqual({ pending: false, suggestion: null });
  });

  test("stays pending without a usable suggestion", () => {
    stubWindow();
    markOrgSelectionPending(null);

    expect(readOrgSelectionPending()).toEqual({ pending: true, suggestion: null });
  });
});

describe("resolveHandoffOrgPlan", () => {
  const exchangeOrg = { id: "org_session", slug: "session-org", name: "Session Org" };

  test("an explicitly scoped org (install/invite/bootstrap) always commits", () => {
    expect(
      resolveHandoffOrgPlan({
        explicitActiveOrg: { id: "org_invite", slug: "invite-org", name: "Invite Org" },
        exchangeOrganization: exchangeOrg,
        desktopInitiated: true,
      }),
    ).toEqual({
      kind: "commit",
      organization: { id: "org_invite", slug: "invite-org", name: "Invite Org" },
    });
  });

  test("a desktop-initiated sign-in defers to the chooser with the exchange org as suggestion", () => {
    expect(
      resolveHandoffOrgPlan({
        explicitActiveOrg: null,
        exchangeOrganization: exchangeOrg,
        desktopInitiated: true,
      }),
    ).toEqual({ kind: "await-user-selection", suggestion: exchangeOrg });
    expect(
      resolveHandoffOrgPlan({
        explicitActiveOrg: null,
        exchangeOrganization: null,
        desktopInitiated: true,
      }),
    ).toEqual({ kind: "await-user-selection", suggestion: null });
  });

  test("a remotely-initiated handoff commits the session's organization", () => {
    expect(
      resolveHandoffOrgPlan({
        explicitActiveOrg: null,
        exchangeOrganization: exchangeOrg,
        desktopInitiated: false,
      }),
    ).toEqual({ kind: "commit", organization: exchangeOrg });
  });

  test("an explicit org with a blank id does not count as a remote selection", () => {
    expect(
      resolveHandoffOrgPlan({
        explicitActiveOrg: { id: "  ", slug: null, name: null },
        exchangeOrganization: exchangeOrg,
        desktopInitiated: true,
      }),
    ).toEqual({ kind: "await-user-selection", suggestion: exchangeOrg });
  });
});
