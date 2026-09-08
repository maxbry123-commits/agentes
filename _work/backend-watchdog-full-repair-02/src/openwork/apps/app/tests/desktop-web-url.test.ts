import { describe, expect, test } from "bun:test";

import { assertDesktopWebUrl } from "../src/app/lib/desktop";

describe("desktop external web URLs", () => {
  test("allows HTTP and HTTPS browser destinations", () => {
    expect(assertDesktopWebUrl("https://accounts.example.com/authorize?state=test")).toBe(
      "https://accounts.example.com/authorize?state=test",
    );
    expect(assertDesktopWebUrl("http://127.0.0.1:4319/callback")).toBe(
      "http://127.0.0.1:4319/callback",
    );
  });

  test("rejects custom protocols before Electron openExternal", () => {
    expect(() => assertDesktopWebUrl("javascript:alert(1)")).toThrow("not allowed");
    expect(() => assertDesktopWebUrl("file:///tmp/provider-controlled")).toThrow("not allowed");
    expect(() => assertDesktopWebUrl("openwork://provider-controlled")).toThrow("not allowed");
  });
});
